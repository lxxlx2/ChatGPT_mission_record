"""Existing tick's Testnet-only funding -> compute -> finalized spend -> rollover.
No new wallet, scheduler, Devnet or mainnet. Unknown results stop new payments.
Discovery schemas are conservative; missing fields never mean zero or ready.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
from urllib.parse import urlparse
import faucet
from agent import utc
from mail import enqueue

GENESIS=faucet.GENESIS
EXPLORER='https://testnet.flopscan.io'
GUIDE='https://flop.network/llms.txt'
UNIT=10**18
# Conservative pilot ceiling; not a claim about official pricing or eligibility.
SESSION_CAP=Decimal('0.1')
FEE_RESERVE=Decimal('0.2')
HASH=re.compile(r'0x[0-9a-fA-F]{64}')
ADDRESS=re.compile(r'[1-9A-HJ-NP-Za-km-z]{42,55}')
COOLDOWN=86400

def get(c,k,default=None):
    row=c.execute('SELECT value FROM kv WHERE key=?',(k,)).fetchone()
    return row[0] if row else default
def put(c,k,v):
    c.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',(k,str(v)))
    c.commit()
def emit(c,key,subject,body):
    if not c.execute('SELECT 1 FROM flop_mail WHERE mail_key=?',(key,)).fetchone():
        enqueue(c,key,subject,body)
def status(c,value):
    put(c,'cycle_status',value)
    put(c,'execution_mode',value)
    return value
def read_json(fetch,url):
    result=json.loads(fetch(url))
    if not isinstance(result,(dict,list)):raise ValueError('BAD_JSON')
    return result
def rows(obj):
    if isinstance(obj,list):return obj
    if isinstance(obj,dict) and isinstance(obj.get('data'),list):return obj['data']
    if isinstance(obj,dict) and isinstance(obj.get('models'),list):return obj['models']
    raise ValueError('UNKNOWN_LIST_SCHEMA')
def decimal(v):
    try:
        a=Decimal(str(v))
        if not a.is_finite() or a<0:raise ValueError('BAD_AMOUNT')
        return a
    except InvalidOperation as e:raise ValueError('BAD_AMOUNT') from e
def valid_hash(v):
    return isinstance(v,str) and HASH.fullmatch(v) is not None
def integer(v):
    if type(v) not in (int,str) or not re.fullmatch(r'[0-9]{1,16}',str(v)):return None
    return int(v)
def score_state(text,height):
    # No optimistic inference from the runtime number or vague roadmap.
    if re.search(r'no block or date is announced|no activation block|future upgrade|inference does not work yet',text,re.I):
        return 'UNSCORED_OR_NOT_ANNOUNCED'
    matches=re.findall(r'voucher earning (?:starts|started|begins|began) at (?:the )?(?:finalized )?block ([0-9,]+)',text,re.I)
    if len(set(matches))==1:
        block=int(matches[0].replace(',',''))
        return ('SCORED_AT_FINALIZED_BLOCK_' if height>=block else 'WAITING_ACTIVATION_BLOCK_')+str(block)
    return 'UNVERIFIED'

def claim_eligible(grant, settlement, at):
    if not grant or grant.get('status')!='CHAIN_FINALIZED' or not settlement:
        return False
    return (settlement.get('finalized') is True
            and settlement.get('genesis')==GENESIS and settlement.get('wallet')==grant.get('address')
            and settlement.get('grant_key')==grant.get('key')
            and integer(settlement.get('block_number')) is not None
            and integer(grant.get('block_number')) is not None
            and int(settlement['block_number'])>int(grant['block_number'])
            and valid_hash(settlement.get('tx_hash'))
            and decimal(settlement.get('spent_raw','0'))>0
            and integer(grant.get('timestamp_ms')) is not None
            and at>=int(grant['timestamp_ms'])/1000+COOLDOWN)

def chain_check(kind, data, *, runner=subprocess.run):
    cli=shutil.which('flop');node=shutil.which('node')
    if not cli or not node:return {'ok':False,'code':'CHAIN_TOOL_MISSING'}
    try:
        cp=runner([node,str(Path(__file__).with_name('chain_verify.cjs'))],
            input=json.dumps({'kind':kind,'genesis':GENESIS,'cli':cli,**data}),capture_output=True,text=True,timeout=50,check=False)
        # polkadot/api may print diagnostics before its single JSON result.
        for line in reversed(cp.stdout.splitlines()):
            try:
                obj=json.loads(line)
                if isinstance(obj,dict) and 'ok' in obj:
                    return obj if cp.returncode==0 and obj['ok'] is True else {'ok':False,'code':obj.get('code','CHAIN_ADAPTER_UNAVAILABLE')}
            except ValueError:pass
    except (OSError,subprocess.SubprocessError,ValueError):pass
    return {'ok':False,'code':'CHAIN_ADAPTER_UNAVAILABLE'}

def locate(fetch,tx,record):
    if not valid_hash(tx):return None
    hint=integer(record.get('block_number'))
    h=record.get('block_hash')
    if hint is not None:
        return {'block_number':hint,**({'block_hash':h} if valid_hash(h) else {})}
    try:
        obj=read_json(fetch,EXPLORER+'/api/transactions/'+tx)
        if isinstance(obj,dict) and isinstance(obj.get('data'),dict):obj=obj['data']
        if not isinstance(obj,dict):return None
        for k in ('blockNumber','block_number','blockHeight','block_height'):
            n=integer(obj.get(k))
            if n is not None:
                h=obj.get('blockHash') or obj.get('block_hash')
                return {'block_number':n,**({'block_hash':h} if valid_hash(h) else {})}
        block=obj.get('block')
        if isinstance(block,dict):
            n=integer(block.get('number') or block.get('height'))
            h=block.get('hash')
            if n is not None:return {'block_number':n,**({'block_hash':h} if valid_hash(h) else {})}
    except (OSError,ValueError,TypeError,AttributeError):pass
    return None

def public_https(url):
    if not isinstance(url,str):return False
    try:
        p=urlparse(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.port not in (443,None):
            return False
        if p.hostname.endswith('.local') or 'devnet' in p.hostname.lower():return False
        ips={x[4][0] for x in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)}
        return bool(ips) and all(ipaddress.ip_address(x).is_global for x in ips)
    except (OSError,ValueError):return False

def candidates(offers, models, height, wallet, free, *, endpoint_ok=public_https):
    """Only independently advertised verified venue + matching registry identity.
    Explicit raw or FLOP price units required; ambiguous minEscrow is rejected.
    """
    model_map={}
    for m in models:
        if not isinstance(m,dict):continue
        h=m.get('modelHash') or m.get('hash')
        slug=m.get('canonical_slug') or m.get('canonicalSlug') or m.get('slug')
        if valid_hash(h) and isinstance(slug,str) and re.fullmatch(r'[A-Za-z0-9._/-]{5,125}',slug):
            model_map.setdefault(h.lower(),set()).add(slug)
    result=[]
    for offer in offers:
        if not isinstance(offer,dict) or offer.get('venueVerified') is not True:continue
        venue=offer.get('venue')
        endpoint=venue if isinstance(venue,str) else (venue.get('endpoint') or venue.get('url') if isinstance(venue,dict) else None)
        miner=offer.get('miner') or offer.get('minerAddress')
        h=offer.get('modelHash')
        expiry=integer(offer.get('expiryBlock') or offer.get('expiry'))
        if not isinstance(miner,str) or not ADDRESS.fullmatch(miner) or miner==wallet or not valid_hash(h) or expiry is None or expiry<=height+30:continue
        slugs=model_map.get(h.lower(),set())
        if len(slugs)!=1 or not endpoint_ok(endpoint):continue
        try:
            if 'minEscrowRaw' in offer: price=decimal(offer['minEscrowRaw'])/UNIT
            elif 'minEscrowPlancks' in offer:price=decimal(offer['minEscrowPlancks'])/UNIT
            elif 'minEscrowFlop' in offer:price=decimal(offer['minEscrowFlop'])
            else:continue
            # First and recurring trials capped at 0.1 test FLOP, with reserve
            # for fees. Never increase escrow merely to spend faucet tokens.
            if price<=0 or price>SESSION_CAP or free<price+FEE_RESERVE:continue
            if price*UNIT!=(price*UNIT).to_integral_value():continue
        except ValueError:continue
        result.append({'miner':miner,'model':next(iter(slugs)),'endpoint':endpoint,
                       'max_flop':format(price,'f'),'expiry':expiry})
    return sorted(result,key=lambda x:(Decimal(x['max_flop']),-x['expiry'],x['miner']))

def discovery(c,fetch,height,wallet,free,*,runner=subprocess.run):
    put(c,'discovery_status','UNVERIFIED')
    put(c,'offer_count','UNVERIFIED');put(c,'eligible_offer_count','UNVERIFIED')
    try:
        offers=rows(read_json(fetch,EXPLORER+'/api/session-offers?limit=100'))
        put(c,'offer_count',len(offers))
        if not offers:
            put(c,'eligible_offer_count',0);put(c,'discovery_status','NO_LISTED_OFFERS')
            return []
        cli=shutil.which('flop')
        if not cli:raise ValueError('NO_CLI')
        cp=runner([cli,'--network','testnet','model','list','--json'],capture_output=True,text=True,timeout=35,check=False)
        if cp.returncode:raise ValueError('MODEL_LIST_FAILED')
        models=rows(json.loads(cp.stdout))
        result=candidates(offers,models,height,wallet,free)
        put(c,'eligible_offer_count',len(result));put(c,'discovery_status','CANDIDATES_FOUND' if result else 'NO_VERIFIED_AFFORDABLE_VENUE')
        return result
    except (OSError,ValueError,TypeError,subprocess.SubprocessError):
        put(c,'discovery_status','DISCOVERY_INTERFACE_UNVERIFIED')
        return []

def submit(c,key,grant,candidate,height,*,runner=subprocess.run):
    cli=shutil.which('flop')
    if not cli:return status(c,'CLI_UNAVAILABLE')
    # Existing encrypted identity only; no new keystore and no secrets on CLI args.
    ident=faucet.IDENTITY; keyfile=ident.parent/'agent-key.json';pwfile=ident.parent/'agent-password'
    try:
        if any(not p.is_file() or p.stat().st_mode & 0o077 for p in (ident,keyfile,pwfile)):raise ValueError()
        obj=json.loads(ident.read_text());wallet=obj['address']
        if obj.get('purpose')!='FLOP_TESTNET_ONLY' or wallet!=grant['address'] or json.loads(keyfile.read_text()).get('address')!=wallet:raise ValueError()
        password=pwfile.read_text().strip()
        if not password:raise ValueError()
        version=runner([cli,'--version'],capture_output=True,text=True,timeout=20,check=False)
        if version.returncode or version.stdout.strip()!='0.9.0':return status(c,'CLI_VERSION_REVIEW_REQUIRED')
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError):
        return status(c,'IDENTITY_OR_CLI_UNVERIFIED')
    aid='cycle-'+hashlib.sha256(key.encode()).hexdigest()[:24]
    rec={'grant_key':key,'start_height':height}
    c.execute("""INSERT INTO session_attempts
      (attempt_id,phase,started_utc,wallet,expected_genesis,miner,max_flop,cli_result)
      VALUES (?,?,?,?,?,?,?,?)""",(aid,'RESERVED_UNKNOWN_MAY_SUBMIT',utc(),wallet,GENESIS,candidate['miner'],candidate['max_flop'],json.dumps(rec)))
    c.commit()
    status(c,'TESTNET_SESSION_SUBMITTING')
    env=dict(os.environ,FLOP_KEY_PASSWORD=password,FLOP_INDEXER_URL=EXPLORER)
    try:
        cp=runner([cli,'--network','testnet','--keystore',str(keyfile),'--password-env','FLOP_KEY_PASSWORD',
          'session','run','--miner',candidate['miner'],'--model',candidate['model'],'--prompt',
          'Give one short explanation of why finalized inference settlement matters.',
          '--max-flop',candidate['max_flop'],'--via','offer','--endpoint',candidate['endpoint'],'--json'],
          env=env,capture_output=True,text=True,timeout=750,check=False)
        rec['return_code']=cp.returncode
        rec['stdout_sha256']=hashlib.sha256(cp.stdout.encode()).hexdigest()
        rec['stderr_sha256']=hashlib.sha256(cp.stderr.encode()).hexdigest()
        obj={}
        for raw in (cp.stdout,cp.stderr):
            try:
                x=json.loads(raw)
                if isinstance(x,dict):obj=x;break
            except ValueError:pass
        for k in ('result','data'):
            if isinstance(obj.get(k),dict):obj={**obj,**obj[k]}
        settle=obj.get('settlement') if isinstance(obj.get('settlement'),dict) else {}
        channel=obj.get('channelId') or obj.get('channel_id') or obj.get('channel')
        if isinstance(channel,dict):channel=channel.get('id') or channel.get('channelId')
        tx=obj.get('settlementTx') or obj.get('settlement_tx') or obj.get('settlementTxHash') or settle.get('txHash') or settle.get('tx_hash')
        if isinstance(tx,dict):tx=tx.get('hash') or tx.get('txHash')
        if valid_hash(channel):rec['channel']=channel
        if valid_hash(tx):rec['tx_hash']=tx
        for v in (settle.get('blockNumber'),obj.get('settlementBlockNumber')):
            n=integer(v)
            if n is not None:rec['block_number']=n;break
        phase='CLI_RESULT_NEEDS_CHAIN_FINALITY' if rec.get('channel') and rec.get('tx_hash') else 'UNKNOWN_MAY_HAVE_SUBMITTED'
    except (OSError,subprocess.SubprocessError) as e:
        phase='UNKNOWN_MAY_HAVE_SUBMITTED';rec['error']=type(e).__name__
    finally:
        env.pop('FLOP_KEY_PASSWORD',None);password=''
    c.execute('UPDATE session_attempts SET phase=?,ended_utc=?,cli_result=?,last_error=? WHERE attempt_id=?',
              (phase,utc(),json.dumps(rec),None if phase=='CLI_RESULT_NEEDS_CHAIN_FINALITY' else 'RECONCILIATION_REQUIRED',aid))
    c.commit()
    return status(c,'WAITING_FOR_FINALIZED_SETTLEMENT')

def run_tick(c,fetch,*,clock=time.time,verifier=chain_check,runner=subprocess.run):
    """Run from the existing locked runtime tick only."""
    if get(c,'rpc_genesis_matches_expected')!='true' or get(c,'observed_genesis')!=GENESIS or get(c,'rpc_reachable')!='true' or get(c,'profile_status')!='live':
        return status(c,'WAITING_PINNED_TESTNET')
    # Read a separate finalized head even during faucet downtime.
    height=integer(get(c,'finalized_height'))
    if not height:return status(c,'WAITING_CHAIN_FINALITY')
    try:
        guide=fetch(GUIDE)
        scoring=score_state(guide,height)
    except (OSError,ValueError,TypeError):scoring='UNVERIFIED'
    old_score=get(c,'cycle_scoring','UNVERIFIED')
    put(c,'cycle_scoring',scoring)
    if scoring.startswith('SCORED_AT_FINALIZED_BLOCK_') and scoring!=old_score:
        emit(c,'scoring-'+scoring,'[FLOP] 官方计分区块已达到',scoring+'；有效积分仍须独立核验。')
    wallet=get(c,'wallet_address')
    if not isinstance(wallet,str) or not ADDRESS.fullmatch(wallet):return status(c,'WAITING_EXISTING_WALLET')
    key=faucet.active_claim_key(c,wallet)
    grant_raw=get(c,key)
    grant=json.loads(grant_raw) if grant_raw else None
    ready=(get(c,'faucet_ready')=='true' and get(c,'faucet_matches_rpc')=='true'
           and get(c,'faucet_grant_flop')=='10' and integer(get(c,'faucet_daily_remaining_flop')) is not None
           and int(get(c,'faucet_daily_remaining_flop'))>=10)
    # A grant's balance is not a receipt. Recheck the same nonce on the existing
    # ledger until a transaction can be independently verified.
    if not grant or grant.get('status')!='CHAIN_FINALIZED':
        if grant and valid_hash(grant.get('tx_hash')):
            signer=grant.get('faucet_signer') or get(c,'faucet_signer')
            loc=locate(fetch,grant['tx_hash'],grant)
            if loc and isinstance(signer,str) and ADDRESS.fullmatch(signer):
                ev=verifier('grant',{'tx_hash':grant['tx_hash'],'wallet':wallet,'signer':signer,'amount_raw':str(10*UNIT),**loc})
                if ev.get('ok') and ev.get('finalized') is True and ev.get('wallet')==wallet and ev.get('genesis')==GENESIS and ev.get('amount_raw')==str(10*UNIT) and ev.get('tx_hash')==grant['tx_hash'].lower() and integer(ev.get('timestamp_ms')) is not None:
                    grant.update(ev,status='CHAIN_FINALIZED',key=key)
                    put(c,key,json.dumps(grant));put(c,'faucet_claim_status','CHAIN_FINALIZED')
                    emit(c,'grant-chain-'+hashlib.sha256(key.encode()).hexdigest()[:24],
                         '[FLOP] 测试币领取已链上最终确认','到账 10 Test FLOP\n钱包：'+wallet+'\n交易：'+grant['tx_hash']+'\n不代表空投积分。')
                    return status(c,'GRANT_FINALIZED_READY_FOR_DISCOVERY')
                put(c,'cycle_verify_reason',ev.get('code','GRANT_EVIDENCE_MISMATCH'))
        if ready and (not grant or grant.get('status') not in ('CLI_FINALIZED_REPORTED','REFUSED_NO_AUTO_RETRY')):
            outcome=faucet.request_initial(c,GENESIS)
            put(c,'faucet_claim_status',outcome.get('status','UNVERIFIED'))
            return status(c,'WAITING_GRANT_FINALITY')
        return status(c,'WAITING_GRANT_FINALITY_OR_FAUCET')
    if grant.get('address')!=wallet or grant.get('genesis')!=GENESIS:return status(c,'GRANT_WALLET_OR_GENESIS_MISMATCH')
    grant['key']=key
    aid='cycle-'+hashlib.sha256(key.encode()).hexdigest()[:24]
    # Unknown legacy or parallel sessions prevent any new payment.
    prior=c.execute('SELECT attempt_id FROM session_attempts WHERE chain_verified=0 AND attempt_id<>? LIMIT 1',(aid,)).fetchone()
    if prior:return status(c,'BLOCKED_OTHER_UNRECONCILED_SESSION')
    row=c.execute('SELECT * FROM session_attempts WHERE attempt_id=?',(aid,)).fetchone()
    if row:
        rec=json.loads(row['cli_result'] or '{}')
        if not row['chain_verified']:
            loc=locate(fetch,rec.get('tx_hash'),rec)
            if not loc or not valid_hash(rec.get('channel')):return status(c,'SESSION_OUTCOME_UNKNOWN_NO_NEW_PAYMENT')
            ev=verifier('settlement',{'tx_hash':rec['tx_hash'],'channel':rec['channel'],'wallet':wallet,
                'miner':row['miner'],'grant_height':grant['block_number'],'start_height':rec['start_height'],
                'max_raw':str(int(Decimal(row['max_flop'])*UNIT)),**loc})
            if (not ev.get('ok') or ev.get('finalized') is not True or ev.get('wallet')!=wallet or ev.get('miner')!=row['miner']
                    or ev.get('genesis')!=GENESIS or ev.get('channel')!=rec['channel'] or ev.get('tx_hash')!=rec['tx_hash'].lower()
                    or decimal(ev.get('spent_raw','0'))<=0 or decimal(ev.get('spent_raw','0'))>Decimal(row['max_flop'])*UNIT):
                put(c,'cycle_verify_reason',ev.get('code','SETTLEMENT_EVIDENCE_MISMATCH'))
                return status(c,'WAITING_FINALIZED_SETTLEMENT')
            ev['grant_key']=key
            if int(ev['block_number'])<=int(grant['block_number']):return status(c,'SETTLEMENT_BEFORE_GRANT')
            rec['chain_evidence']=ev
            c.execute("UPDATE session_attempts SET chain_verified=1,phase='DIRECT_CHAIN_VERIFIED',final_spent_flop=?,chain_tx=?,last_error=NULL,cli_result=? WHERE attempt_id=?",
              (format(Decimal(ev['spent_raw'])/UNIT,'f'),ev['tx_hash'],json.dumps(rec),aid))
            c.commit();put(c,'last_verified_session_utc',utc())
            emit(c,'session-chain-'+aid,'[FLOP] 推理支付已链上最终确认','已核验自有钱包向独立 Miner 的结算：'+format(Decimal(ev['spent_raw'])/UNIT,'f')+' Test FLOP\n交易：'+ev['tx_hash']+'\n计分状态：'+scoring+'；积分归属仍以官方为准。')
            return status(c,'SETTLEMENT_FINALIZED_WAIT_COOLDOWN')
        ev=rec.get('chain_evidence')
        if not claim_eligible(grant,ev,clock()):
            if integer(grant.get('timestamp_ms')) is not None:
                put(c,'next_claim_eligible_after_utc_epoch',int(grant['timestamp_ms'])//1000+COOLDOWN)
            return status(c,'WAITING_24H_OR_QUALIFYING_SPEND')
        if not ready:return status(c,'ROLLOVER_WAITING_FAUCET')
        # Atomic advance of ledger identity; old grant and settlement retained.
        number=integer(get(c,'cycle_number','0'))
        if number is None:raise ValueError('BAD_CYCLE_NUMBER')
        newkey=faucet.base_claim_key(wallet)+'-cycle-'+str(number+1)
        if get(c,newkey):return status(c,'ROLLOVER_KEY_ALREADY_EXISTS')
        c.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',('cycle_active_claim_key',newkey))
        c.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',('cycle_number',str(number+1)))
        c.commit()
        return status(c,'ROLLOVER_ELIGIBLE_NEXT_TICK')
    try:free=decimal(get(c,'wallet_free_flop','UNVERIFIED'))
    except ValueError:return status(c,'WAITING_WALLET_BALANCE')
    offers=discovery(c,fetch,height,wallet,free,runner=runner)
    if not offers:return status(c,'WAITING_VERIFIED_TESTNET_MINER_MODEL')
    # Verify our independent adapter can actually decode current runtime before
    # permitting first payment; future schemas still fail closed.
    probe=verifier('probe',{})
    if not probe.get('ok') or probe.get('genesis')!=GENESIS:return status(c,'CHAIN_VERIFIER_UNAVAILABLE_NO_PAYMENT')
    return submit(c,key,grant,offers[0],height,runner=runner)
