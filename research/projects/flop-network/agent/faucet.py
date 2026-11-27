"""Pinned Testnet D10 grant using reviewed official CLI releases.
Persist the nonce before signing. Reconcile only that nonce. Never create a
second grant until an independent finalized spend/eligibility verifier exists.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from agent import DATA, utc
from mail import enqueue

IDENTITY=DATA/'agent-identity.json'
GENESIS='0x918abd58fb16306b30ef3886514cfaebffecb4de43e82b6f8ec4795c43cfd800'
RECHECK_SECONDS=900
# Official 0.9.1 release uses SDK 0.12.1 and admits runtime 1014039.
# https://github.com/flop-labs/network/commit/942db04ae9cf3fed442190d824f4f8da6508a751
REVIEWED_CLI_VERSIONS=frozenset(('0.9.0','0.9.1','0.10.3'))


def funding_observation(conn, *, fetch, cli_status, runner=subprocess.run, chain_reader=None):
    """Read-only observations, never infer a grant from balance alone."""
    def save(k,v):
        conn.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',(k,str(v)))
    for k in ('faucet_pool_flop','faucet_daily_remaining_flop','faucet_pending_grants',
              'faucet_grant_flop','faucet_limits_asof','wallet_free_flop','wallet_reserved_flop',
              'wallet_balance_at','wallet_balance_source','wallet_balance_error','wallet_balance_height','wallet_address','faucet_signer','faucet_lane_status','faucet_claim_path','faucet_rollover_requires_spend'):
        save(k,'UNVERIFIED')
    save('funding_observed_at',utc())
    save('wallet_funding_state','UNVERIFIED')
    save('faucet_claim_status','NOT_ATTEMPTED_OR_NOT_RECORDED')
    for k in ('faucet_claim_at','faucet_claim_nonce','faucet_claim_tx','faucet_claim_reason','faucet_claim_retry_at'):
        save(k,'UNVERIFIED')
    try:
        obj=json.loads(IDENTITY.read_text())
        address=obj.get('address')
        if not isinstance(address,str) or not re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{42,55}',address):
            raise ValueError('INVALID_ADDRESS')
        save('wallet_address',address)
        key=active_claim_key(conn,address)
        row=conn.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
        if row:
            claim=json.loads(row[0])
            for field,k in (('status','faucet_claim_status'),('at','faucet_claim_at'),
                            ('nonce','faucet_claim_nonce'),('tx_hash','faucet_claim_tx'),
                            ('reason','faucet_claim_reason'),('retry_at','faucet_claim_retry_at')):
                save(k,claim.get(field,'UNVERIFIED'))
    except (OSError,ValueError,TypeError,AttributeError):
        address=None
    try:
        chain=json.loads(fetch('https://faucet.flop.network/chain'))
        limits=json.loads(fetch('https://faucet.flop.network/limits'))
        if chain.get('network')!='testnet' or chain.get('genesisHash')!=GENESIS or limits.get('network')!='testnet' or limits.get('stale') is not False:
            raise ValueError('FAUCET_IDENTITY_OR_FRESHNESS')
        f=limits['faucet']
        save('faucet_lane_status',f.get('status','UNVERIFIED'))
        save('faucet_claim_path',f.get('agent',{}).get('claimPath','UNVERIFIED'))
        save('faucet_rollover_requires_spend',str(f.get('agent',{}).get('rolloverRequiresSpend')).lower())
        signer=f.get('signer')
        if isinstance(signer,str) and re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{42,55}',signer):
            save('faucet_signer',signer)
        for k,v in (('faucet_pool_flop',f.get('balanceFlop')),
                    ('faucet_daily_remaining_flop',f.get('dailyCap',{}).get('remainingFlop')),
                    ('faucet_pending_grants',f.get('pendingGrants')),
                    ('faucet_grant_flop',f.get('agent',{}).get('grantFlop'))):
            if re.fullmatch(r'[0-9]{1,30}',str(v)):
                save(k,v)
        if isinstance(limits.get('asOf'),str):
            save('faucet_limits_asof',limits['asOf'][:40])
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        pass
    if address and cli_status.get('observed_genesis')==GENESIS and cli_status.get('rpc_genesis_matches_expected') is True:
        try:
            cli=shutil.which('flop')
            if not cli:
                raise ValueError('NO_CLI')
            source='CLI'
            try:
                cp=runner([cli,'--network','testnet','balance',address,'--json'],capture_output=True,text=True,timeout=35,check=False)
                if cp.returncode:
                    raise ValueError('RUNTIME_INCOMPATIBLE' if 'RUNTIME_INCOMPATIBLE' in (cp.stdout+cp.stderr) else 'CLI_BALANCE_FAILED')
                bal=json.loads(cp.stdout)
            except (OSError,ValueError,TypeError,subprocess.SubprocessError) as exc:
                code=str(exc)
                code=code if code in ('RUNTIME_INCOMPATIBLE','CLI_BALANCE_FAILED') else 'CLI_BALANCE_UNAVAILABLE'
                save('wallet_balance_error',code)
                if chain_reader is None:
                    from cycle import chain_check
                    reader=chain_check
                else:
                    reader=chain_reader
                bal=reader('balance',{'wallet':address})
                if not bal.get('ok') or bal.get('finalized') is not True or bal.get('genesis')!=GENESIS:
                    save('wallet_balance_error',code+' / '+str(bal.get('code','FINALIZED_BALANCE_UNVERIFIED'))[:80])
                    raise ValueError('FINALIZED_BALANCE_UNVERIFIED')
                source='FINALIZED_RPC'
                save('wallet_balance_height',bal.get('height','UNVERIFIED'))
            # CLI reports chain base units, 18 decimals. No heuristic unit conversion.
            if not isinstance(bal,dict) or bal.get('address')!=address:
                raise ValueError('BALANCE_SCHEMA_OR_ADDRESS_MISMATCH')
            from decimal import Decimal
            for field in ('free','reserved'):
                if type(bal.get(field)) not in (int,str) or not re.fullmatch(r'[0-9]{1,40}',str(bal[field])):
                    raise ValueError('BALANCE_UNITS_UNVERIFIED')
            free=Decimal(str(bal['free']))/Decimal(10**18)
            reserved=Decimal(str(bal['reserved']))/Decimal(10**18)
            save('wallet_free_flop',format(free,'f'))
            save('wallet_reserved_flop',format(reserved,'f'))
            stamp=utc()
            save('wallet_balance_at',stamp)
            save('wallet_balance_source',source)
            save('wallet_last_known_free_flop',format(free,'f'))
            save('wallet_last_known_at',stamp)
            save('wallet_funding_state','POSITIVE_BALANCE_OBSERVED' if free>0 else 'ZERO_FREE_BALANCE_OBSERVED')
            if free>0 and conn.execute("SELECT 1 FROM sqlite_master WHERE name='flop_mail'").fetchone():
                mailkey='first-funded-wallet-'+hashlib.sha256((GENESIS+':'+address).encode()).hexdigest()[:24]
                if not conn.execute('SELECT 1 FROM flop_mail WHERE mail_key=?',(mailkey,)).fetchone():
                    enqueue(conn,mailkey,'[FLOP] 首次检测到钱包测试币余额',
                            '钱包：'+address+'\n实际可用余额：'+format(free,'f')+
                            ' Test FLOP\n已读链上余额；领取交易来源和最终确认需另行核验。尚不代表空投积分。')
        except (OSError,ValueError,TypeError,subprocess.SubprocessError):
            pass
    conn.commit()


def base_claim_key(address):
    return 'initial-faucet-'+hashlib.sha256((GENESIS+':'+address).encode()).hexdigest()[:24]

def active_claim_key(conn,address):
    base=base_claim_key(address)
    row=conn.execute("SELECT value FROM kv WHERE key='cycle_active_claim_key'").fetchone()
    if row:
        key=row[0]
        if key!=base and not re.fullmatch(re.escape(base)+r'-cycle-[1-9][0-9]{0,9}',key):
            raise ValueError('ACTIVE_CLAIM_KEY_WRONG_WALLET')
        return key
    return base

def request_initial(conn, confirmed_genesis, *, cli_runner=subprocess.run, clock=time.time, recheck_reported=False):
    if confirmed_genesis!=GENESIS:
        return {'status':'BLOCKED_NETWORK_GENESIS_NOT_VERIFIED'}
    keyfile=IDENTITY.parent/'agent-key.json'
    pwfile=IDENTITY.parent/'agent-password'
    if any(not p.is_file() or p.stat().st_mode & 0o077 for p in (IDENTITY,keyfile,pwfile)):
        return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
    try:
        obj=json.loads(IDENTITY.read_text())
        address=obj.get('address')
        if not isinstance(address,str) or not re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{42,55}',address):
            return {'status':'BLOCKED_AGENT_ADDRESS_INVALID'}
        if obj.get('purpose')!='FLOP_TESTNET_ONLY' or json.loads(keyfile.read_text()).get('address')!=address:
            return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
        password=pwfile.read_text().strip()
        if not password:
            return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
    except (OSError,ValueError,TypeError,AttributeError):
        return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
    key=active_claim_key(conn,address)
    old=conn.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
    now=int(clock())
    if old:
        attempt=json.loads(old[0])
        if not attempt.get('nonce'):
            return {'status':'BLOCKED_LEGACY_ATTEMPT'}
        if attempt.get('status') in ('CHAIN_FINALIZED','REFUSED_NO_AUTO_RETRY') or (attempt.get('status')=='CLI_FINALIZED_REPORTED' and (attempt.get('tx_hash') or not recheck_reported)):
            return {'status':attempt['status'],'receipt':attempt}
        if now < attempt.get('retry_at',0):
            return {'status':'SAME_NONCE_BACKOFF'}
    else:
        attempt={'status':'OUTCOME_UNKNOWN_PRECOMMITTED','at':utc(),
                 'network':'testnet','genesis':confirmed_genesis,'address':address,
                 'nonce':str(int(clock()*1000))}
    cli=shutil.which('flop')
    if not cli:
        return {'status':'BLOCKED_CLI_NOT_INSTALLED'}
    try:
        version=cli_runner([cli,'--version'],capture_output=True,text=True,timeout=20,check=False)
        if version.returncode or version.stdout.strip() not in REVIEWED_CLI_VERSIONS:
            return {'status':'BLOCKED_CLI_VERSION_REVIEW_REQUIRED'}
    except (OSError,subprocess.TimeoutExpired):
        return {'status':'BLOCKED_CLI_VERSION_REVIEW_REQUIRED'}
    signer=conn.execute("SELECT value FROM kv WHERE key='faucet_signer'").fetchone()
    if signer and re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{42,55}',signer[0]):
        attempt.setdefault('faucet_signer',signer[0])
    attempt.update(status='OUTCOME_UNKNOWN_PRECOMMITTED',retry_at=now+RECHECK_SECONDS)
    conn.execute('INSERT OR REPLACE INTO kv(key,value) VALUES (?,?)',(key,json.dumps(attempt)))
    conn.commit()
    env=dict(os.environ,FLOP_KEY_PASSWORD=password)
    try:
        cp=cli_runner([cli,'--network','testnet','--keystore',str(keyfile),
                       '--password-env','FLOP_KEY_PASSWORD','faucet','request',
                       '--json','--nonce',attempt['nonce']],env=env,capture_output=True,text=True,
                       timeout=150,check=False)
        attempt['return_code']=cp.returncode
        attempt['output_sha256']=hashlib.sha256(cp.stdout.encode()).hexdigest()
        attempt['stderr_sha256']=hashlib.sha256(cp.stderr.encode()).hexdigest()
        response={}
        for raw in (cp.stdout,cp.stderr):
            try:
                parsed=json.loads(raw)
                if isinstance(parsed,dict):
                    response=parsed
                    break
            except (ValueError,TypeError):
                pass
        # Only named response wrappers; never infer tx identity from random hex.
        for name in ('result','data','receipt','grant'):
            inner=response.get(name)
            if isinstance(inner,dict):
                response={**response,**inner}
        reason=response.get('reason') or response.get('code')
        if isinstance(reason,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}',reason):
            attempt['reason']=reason
        reported=response.get('status') or response.get('outcome')
        if isinstance(reported,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}',reported):
            attempt['reported_status']=reported
        tx=response.get('tx_hash') or response.get('txHash')
        if isinstance(tx,str) and re.fullmatch(r'0x[0-9a-fA-F]{64}',tx):
            attempt['tx_hash']=tx
        for field in ('blockHash','block_hash','finalizedBlockHash'):
            value=response.get(field)
            if isinstance(value,str) and re.fullmatch(r'0x[0-9a-fA-F]{64}',value):
                attempt['block_hash']=value
                break
        for field in ('blockNumber','block_number','blockHeight','block_height'):
            value=response.get(field)
            if type(value) in (str,int) and re.fullmatch(r'[0-9]{1,12}',str(value)):
                attempt['block_number']=int(value)
                break
        if cp.returncode==0 and (response.get('finalized') is True or response.get('status')=='finalized') and attempt.get('tx_hash'):
            attempt['status']='CLI_FINALIZED_REPORTED'
        elif response.get('action') in ('fix_request','report_to_operator'):
            attempt['status']='REFUSED_NO_AUTO_RETRY'
        else:
            attempt['status']='SAME_NONCE_RECONCILIATION_PENDING'
            delay=response.get('retryAfterSeconds')
            if type(delay) is int and delay>0:
                attempt['retry_at']=now+max(RECHECK_SECONDS,delay)
    except (OSError,subprocess.TimeoutExpired) as exc:
        attempt['status']='SAME_NONCE_RECONCILIATION_PENDING'
        attempt['reason']=type(exc).__name__
    finally:
        env.pop('FLOP_KEY_PASSWORD',None)
        password=''
    conn.execute('UPDATE kv SET value=? WHERE key=?',(json.dumps(attempt),key))
    conn.commit()
    if attempt['status']=='CLI_FINALIZED_REPORTED' and not conn.execute('SELECT 1 FROM flop_mail WHERE mail_key=?',('faucet-finalized-'+hashlib.sha256(key.encode()).hexdigest()[:15],)).fetchone():
        enqueue(conn,'faucet-finalized-'+hashlib.sha256(key.encode()).hexdigest()[:15],
                '[FLOP] 首次 Testnet Faucet 返回 finalized',
                'CLI reported finalized; independent chain verification still required. '
                'Testnet grant is not voucher credit. Transaction: '+attempt['tx_hash'])
    elif attempt.get('tx_hash') and not conn.execute('SELECT 1 FROM flop_mail WHERE mail_key=?',('faucet-tx-'+hashlib.sha256(key.encode()).hexdigest()[:15],)).fetchone():
        enqueue(conn,'faucet-tx-'+hashlib.sha256(key.encode()).hexdigest()[:15],
                '[FLOP] 首次 Faucet 已返回交易｜等待最终核验',
                '交易哈希：'+attempt['tx_hash']+'\n尚未确认最终到账；不会另起 nonce。')
    return attempt
