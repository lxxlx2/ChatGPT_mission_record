"""Isolated, explicitly authorized historical delivery acceptance; no live DB writes."""
import argparse,base64,fcntl,gzip,json,os,re,sqlite3,subprocess
from decimal import Decimal
from pathlib import Path
from mission_agent.hashing import digest
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy,POLICY_SHA256,USDC
from mission_agent.signals.store import Ledger,quantity,now
from mission_agent.signals.gmail import GmailOutbox
from mission_agent.signals.gmail_api import OAuthGmail
from mission_agent.signals.delivery import JXA
from mission_agent.signals.email import timestamp
from mission_agent.gmail_setup.__main__ import save_private

MINT='6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx'
EVIDENCE=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003')
ROOT=EVIDENCE/'historical-delivery-e2e-v1'
POLICY=Path(__file__).resolve().parents[1]/'config/frank_local_signal_v1.json'

def readonly(path):
    db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;return db

def hash_tx(tx):return __import__('hashlib').sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def prepare(root=ROOT):
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    source=readonly(EVIDENCE/'v1-history-replay-final.sqlite')
    allsignals=[json.loads(r[0]) for r in source.execute('select body from signals where mint=?',(MINT,))]
    multiples=sorted([s for s in allsignals if s['signal_type']=='FRANK_MULTIPLE_SIGNAL'],key=lambda s:(s['triggered_at'],s['signal_id']))
    if not multiples:raise ValueError('NO_SUITABLE_HISTORICAL_MULTIPLE_FIXTURE')
    multiple=multiples[0];acc=next(s for s in allsignals if s['episode_id']==multiple['episode_id'] and s['signal_type']=='FRANK_ACCUMULATION_SIGNAL')
    summary=json.loads((EVIDENCE/'v1-history-replay-final.json').read_text())
    for s in allsignals:
        if s not in summary['signals']:raise ValueError('HISTORICAL_EVIDENCE_MISMATCH')
    rows=source.execute("select * from signatures where json_extract(body,'$.trade.mint')=? order by block_time,slot,signature",(MINT,)).fetchall()
    for row in rows:
        raw=json.loads(gzip.decompress(Path(row['raw_reference']).read_bytes()))
        tx=raw['transaction'] if 'status' in raw and 'signature' in raw else raw
        if hash_tx(tx)!=row['raw_hash']:raise ValueError('HISTORICAL_EVIDENCE_MISMATCH:RAW_HASH')
    path=root/'reconstruction.sqlite'
    if path.exists():raise ValueError('RECONSTRUCTION_EXISTS_USE_EXISTING_SELECTION')
    ledger=Ledger(path);engine=Engine(ledger,load_policy(POLICY),dry_run=True);chronology=[]
    for row in rows:
        ledger.db.execute('insert into signatures values('+','.join('?' for _ in row)+')',tuple(row))
        prior=engine._state(row['person_id'],MINT)
        before='MULTIPLE' if prior and prior['multiple_emitted'] else 'ACCUMULATION' if prior and prior['accumulation_emitted'] else 'NONE'
        result=engine.process(ledger.db.execute('select * from signatures where signature=?',(row['signature'],)).fetchone())
        state=engine._state(row['person_id'],MINT)
        if state and state['episode_id']==multiple['episode_id'] and result:
            t=json.loads(row['body'])['trade'];buys=[e for e in state['events'] if e['direction']=='BUY']
            cumulative={}
            for e in buys:cumulative[e['quote_asset']]=str(Decimal(cumulative.get(e['quote_asset'],'0'))+Decimal(e['quote_quantity']))
            after='MULTIPLE' if state['multiple_emitted'] else 'ACCUMULATION' if state['accumulation_emitted'] else 'NONE'
            chronology.append(dict(at=row['block_time'],timestamp_bangkok=timestamp(row['block_time']),signature=row['signature'],direction=t['direction'],side=('BUY #'+str(len(buys)) if t['direction']=='BUY' else 'SELL #'+str(sum(e['direction']=='SELL' for e in state['events']))),quote_asset=t['quote_asset'],quote_quantity=quantity(t['quote_amount_raw'],t['quote_decimals']),cumulative_buy=cumulative,buy_count=len(buys),inventory_raw=state['current_raw'],inventory_quantity=quantity(state['current_raw'],t['token_decimals']) if state['current_raw'] is not None else None,inventory_state=state['state'],stage_before=before,stage_after=after,predicates=result['predicates']))
    generated=[json.loads(r[0]) for r in ledger.db.execute('select body from signals where mint=?',(MINT,))]
    if sorted(generated,key=lambda s:s['signal_id'])!=sorted(allsignals,key=lambda s:s['signal_id']):raise ValueError('HISTORICAL_EVIDENCE_MISMATCH:DETERMINISTIC_SIGNALS')
    episodes=[]
    for ep in source.execute('select distinct episode_id from v1_evaluations where mint=?',(MINT,)):
        active=[json.loads(r[0]) for r in source.execute("select body from v1_evaluations where episode_id=? and json_extract(body,'$.kind')='ACTIVE_TRADE' order by at",(ep[0],))]
        ep_signals=[s for s in allsignals if s['episode_id']==ep[0]]
        episodes.append(dict(episode_id=ep[0],first_active_buy=min(r['at'] for r in source.execute("select at from v1_evaluations where episode_id=? and json_extract(body,'$.kind')='ACTIVE_TRADE'",(ep[0],))),signal_records=ep_signals,final_observed_buy_count=active[-1]['buy_count'],final_known_usdc=active[-1]['known_episode_usdc']))
    selection=dict(token='STONK',mint=MINT,stonk_accumulation=True,stonk_multiple=True,why_selected='User preferred token; chronologically first real frozen V1 MULTIPLE; no PnL selection',multiple=multiple,accumulation=acc,episodes=episodes,chronology=chronology,reconstruction='PASS',raw_hash_verified_count=len(rows),policy_hash=POLICY_SHA256)
    save_private(root/'selection.json',selection);ledger.db.close();source.close();print(json.dumps(dict(selected_token='STONK',episode_id=multiple['episode_id'],signal_id=multiple['signal_id'],chronology_rows=len(chronology),deterministic_reconstruction='PASS')))
    return selection

class HistoricalOutbox(GmailOutbox):
    def enqueue_historical(self,mail):
        sid=mail['signal_id']
        if not re.fullmatch(r'historical-test:[0-9a-f]{64}:delivery-e2e-v1',sid):raise ValueError('HISTORICAL_NAMESPACE_REQUIRED')
        if not mail['subject'].startswith('[HISTORICAL TEST][Frank 多倍信号] ') or not all(x in mail['body'] for x in ('HISTORICAL REPLAY / DELIVERY E2E TEST','这不是 Frank 当前实时交易。','不得作为新的实时买入信号解读。')):raise ValueError('HISTORICAL_LABEL_REQUIRED')
        bh=digest(mail['body']);ch=digest({'subject':mail['subject'],'body':mail['body']});wire='<frank.'+digest({'signal_id':sid,'mode':'HISTORICAL_TEST'})+'@local.invalid>'
        self.db.execute('INSERT OR IGNORE INTO gmail_delivery(signal_id,message_type,delivery_mode,delivery_forbidden,subject,body,body_hash,content_hash,status,created_at,wire_message_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(sid,'HISTORICAL_TEST_MULTIPLE','HISTORICAL_TEST',0,mail['subject'],mail['body'],bh,ch,'PENDING',now(),wire))
        r=self.row(sid)
        if r['content_hash']!=ch or r['delivery_mode']!='HISTORICAL_TEST':raise ValueError('IMMUTABLE_HISTORICAL_IDENTITY_CONFLICT')

class Counter(OAuthGmail):
    def __init__(self):super().__init__(Path.home()/'.config/frank-local-gmail/authorized-user.json');self.send_count=0
    def send(self,raw):self.send_count+=1;return super().send(raw)

def mail_for(selection):
    m=selection['multiple'];a=selection['accumulation'];p=m['position'];sid='historical-test:'+m['signal_id']+':delivery-e2e-v1'
    body='HISTORICAL REPLAY / DELIVERY E2E TEST\n\n这不是 Frank 当前实时交易。\n这是使用已确认历史链上数据进行的投递验收。\n不得作为新的实时买入信号解读。\n\n'
    fields=[('Token','STONK'),('CA / Mint',MINT),('Original signal time',timestamp(m['triggered_at'])),('Original accumulation time',timestamp(a['triggered_at'])),('Original multiple time',timestamp(m['triggered_at'])),('Episode ID',m['episode_id']),('Historical signal ID',m['signal_id']),('Historical delivery identity',sid),('首次 ACTIVE BUY',timestamp(p['first_buy_at'])),('最新触发 BUY',timestamp(p['last_buy_at'])),('buy_count',p['buy_count']),('sell_count',p['sell_count']),('累计 raw quote','; '.join(v+' '+('USDC' if k==USDC else k) for k,v in p['gross_quote_spent'].items())),('当前 replay inventory state',p['current_token_quantity']+' STONK / OBSERVED_ACTIVE_SEQUENCE / LIFETIME_POSITION_UNKNOWN'),('MULTIPLE reason codes','\n'+'\n'.join(m['reason_codes'])),('Triggering signature',m['triggering_signature']),('Triggering tx','https://solscan.io/tx/'+m['triggering_signature'])]
    body+='\n\n'.join(str(k)+': '+str(v) for k,v in fields)+'\n'
    return dict(signal_id=sid,subject='[HISTORICAL TEST][Frank 多倍信号] STONK | MULTIPLE | '+timestamp(m['triggered_at']),body=body)

def local_test(root,signal,stage):
    sid='historical-test:'+signal['signal_id']+':local-e2e-v1';path=root/('local-'+stage.lower()+'.json')
    title='[HISTORICAL TEST] Frank '+stage+' | STONK'
    message='Historical replay delivery test\nNOT A LIVE FRANK TRADE\nToken: STONK\nCA: '+MINT+'\nOriginal trigger time: '+timestamp(signal['triggered_at'])+'\nOriginal stage: '+signal['stage']+'\nOriginal signal_id: '+signal['signal_id']+'\nTriggering signature: '+signal['triggering_signature']
    ch=digest({'title':title,'body':message})
    if path.exists():
        receipt=json.loads(path.read_text())
        if receipt['content_hash']!=ch:raise ValueError('LOCAL_IDENTITY_CONFLICT')
        return receipt
    # Persist dispatch intent first. Unknown outcome must not silently redispatch.
    intent=root/('local-'+stage.lower()+'-intent.json')
    if intent.exists():raise ValueError('LOCAL_DISPATCH_OUTCOME_REQUIRES_REVIEW')
    save_private(intent,dict(signal_id=sid,content_hash=ch,title=title,body=message,at=now()))
    result=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',JXA,sid,title,message],capture_output=True,text=True,timeout=15)
    if result.returncode or result.stdout.strip() not in ('REQUEST_ACCEPTED','ALREADY_PRESENT'):raise ValueError('LOCAL_NOTIFICATION_NOT_ACCEPTED')
    receipt=dict(signal_id=sid,content_hash=ch,status='COMMAND_ACCEPTED',os_response=result.stdout.strip(),accepted_at=now(),title=title,body=message)
    save_private(path,receipt);return receipt

def deliver(root=ROOT):
    selection=json.loads((root/'selection.json').read_text())
    if selection.get('reconstruction')!='PASS':raise ValueError('REPLAY_GATE_REQUIRED')
    if not (root/'targeted-chain-readback.json').exists():raise ValueError('TARGETED_READBACK_REQUIRED')
    readback=json.loads((root/'targeted-chain-readback.json').read_text())
    if readback['status']!='PASS':raise ValueError('HISTORICAL_EVIDENCE_MISMATCH')
    locals=[local_test(root,selection['accumulation'],'ACCUMULATION'),local_test(root,selection['multiple'],'MULTIPLE')]
    ledger=Ledger(root/'delivery.sqlite');box=HistoricalOutbox(ledger);mail=mail_for(selection);box.enqueue_historical(mail)
    provider=Counter();provider.ready();box.drain(provider)
    row=box.row(mail['signal_id'])
    if row['status']!='SENT_VERIFIED':raise ValueError('HISTORICAL_GMAIL_'+row['status']+':'+str(row['last_error']))
    ids=provider.find_sent(row['wire_message_id'],row['signal_id'])
    if ids!=[row['gmail_message_id']]:raise ValueError('SENT_IDENTITY_NOT_UNIQUE')
    box.verify(row,provider.get(ids[0]));receipt=json.loads(box.row(row['signal_id'])['receipt']);save_private(root/'original-gmail-receipt.json',receipt)
    second=Counter();box.drain(second)
    if second.send_count:raise ValueError('DEDUPE_FAILED')
    ledger.db.execute("UPDATE gmail_delivery SET status='SENDING',gmail_message_id=NULL,gmail_thread_id=NULL,receipt=NULL,readback_verified=0 WHERE signal_id=?",(row['signal_id'],));ledger.db.commit();ledger.db.close()
    ledger=Ledger(root/'delivery.sqlite');box=HistoricalOutbox(ledger);recovery=Counter();box.drain(recovery)
    restored=box.row(row['signal_id'])
    if recovery.send_count or restored['status']!='SENT_VERIFIED' or restored['gmail_message_id']!=ids[0]:raise ValueError('CRASH_RECOVERY_FAILED')
    final=dict(historical_gmail='PASS',local_notifications=locals,first_execution_send_count=provider.send_count,total_delivery_attempt_count=restored['attempt_count'],second_execution_send_count=second.send_count,test_dedupe='PASS',crash_recovery='PASS',recovery_additional_sends=recovery.send_count,gmail_receipt=json.loads(restored['receipt']),gmail_api=provider.last_api_result,live_outbox_writes=0,delivery_mode=restored['delivery_mode'],at=now())
    previous=json.loads((root/'delivery-verification.json').read_text()) if (root/'delivery-verification.json').exists() else None
    executions=previous.get('executions',[{'send_count':previous['first_execution_send_count'],'at':previous['at']}]) if previous else []
    final['executions']=executions+[{'send_count':provider.send_count,'at':final['at']}]
    if previous:final['first_execution_send_count']=previous['first_execution_send_count']
    save_private(root/'delivery-verification.json',final);ledger.db.close();print(json.dumps({k:v for k,v in final.items() if k not in ('local_notifications','gmail_receipt')},ensure_ascii=False));print('GMAIL_MESSAGE_ID='+ids[0])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--deliver',action='store_true');a=p.parse_args()
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (ROOT/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.prepare:prepare()
        elif a.deliver:deliver()
        else:p.error('explicit --prepare or --deliver required')
