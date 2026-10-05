"""Single local Meme scanner, reusing the proven Frank durable state; no GPT or Gmail calls."""
import argparse,fcntl,gzip,hashlib,json,os,signal,threading,time
from pathlib import Path
from mission_agent.db.repository import Repository
from mission_agent.db.connection import transaction
from mission_agent.frank.collector import FrankCollector
from mission_agent.frank.parser import normalize
from mission_agent.frank.rpc import WALLET
from mission_agent.frank.store import FrankStore
from mission_agent.hashing import canonical,loads,seal,digest
from mission_agent.meme.registry import Registry
from mission_agent.meme.schema import fact,run_bundle,validate_run,epoch
from mission_agent.meme.state import SignalStore,DDL
from mission_agent.meme.collector import WalletCollector
from mission_agent.meme.transport import MemeTransport
from scripts.frank_shadow_service import ObservedRPC,atomic_json,utc,snapshot_health,history_loop,transport_once
IDENTIFIER='com.jerson.crypto-monitor-meme-shadow'

def drain(source,main,registry,policy,wallet,root):
    store=SignalStore(main.db,registry,policy)
    rows=source.db.execute('SELECT t.evidence_json,o.signature,o.detected_at,o.normalized_at FROM frank_observations o JOIN frank_transactions t USING(signature) LEFT JOIN meme_source_observations m ON m.wallet=? AND m.signature=o.signature WHERE m.signature IS NULL ORDER BY t.slot,o.signature LIMIT 256',(wallet,)) if source is main else source.db.execute('SELECT t.evidence_json,o.signature,o.detected_at,o.normalized_at FROM frank_observations o JOIN frank_transactions t USING(signature) ORDER BY t.slot,o.signature')
    if source is main:rows=rows.fetchall()
    processed=0
    for row in rows:
        if processed>=256:break
        if main.db.execute('SELECT 1 FROM meme_source_observations WHERE wallet=? AND signature=?',(wallet,row['signature'])).fetchone():continue
        e=loads(row['evidence_json']);prior=[loads(x[0]) for x in source.db.execute('SELECT evidence_json FROM frank_transactions WHERE block_time<? ORDER BY block_time DESC LIMIT 500',(e['block_time'],))]
        # Immutable fact creation time is persisted in the same transaction as source acknowledgement.
        values=[];created=utc()
        for mint in sorted({d['mint'] for d in e['token_balance_deltas'] if d['wallet_owned']}):
            f=fact(e,dict(row),created,registry,mint,prior=prior)
            if f:values.append(f)
        store.stage(values,created,observation=(wallet,row['signature']));processed+=1
    store.stage([],utc())

def validate_forward(run,repo,registry,root,source_roots):
    validate_run(run,namespace='LIVE')
    for c in run['candidates']:
        for f in c['facts']:
            registry.person('solana',f['wallet']);stored=repo.db.execute('SELECT body FROM meme_facts WHERE event_id=?',(f['event_id'],)).fetchone()
            if stored is None or canonical(loads(stored[0]))!=canonical(f):raise ValueError('DURABLE_REAL_FACT_REQUIRED')
            ack=repo.db.execute('SELECT state FROM meme_source_observations WHERE wallet=? AND signature=?',(f['wallet'],f['signature'])).fetchone()
            if ack is None or ack[0]!='PROCESSED':raise ValueError('OLD_HISTORY_CANNOT_REPLAY')
            srcroot=source_roots[f['wallet']];src=Repository(srcroot/'forward.sqlite')
            try:
                row=src.db.execute('SELECT t.evidence_json FROM frank_transactions t JOIN frank_observations o USING(signature) WHERE signature=?',(f['signature'],)).fetchone()
                if row is None:raise ValueError('REAL_FORWARD_OBSERVATION_REQUIRED')
                e=loads(row[0]);raw=srcroot/'raw'/(f['signature']+'.json.gz')
                if normalize(f['signature'],json.loads(gzip.decompress(raw.read_bytes())),f['wallet'])!=e:raise ValueError('REAL_RAW_HASH_BINDING')
                if e['mechanical_classification']!='ACTIVE_SWAP_LIKE' or e['evidence_sha256']!=f['source_evidence_hash']:raise ValueError('REAL_ACTIVE_BINDING')
                total=sum(int(d['delta']) for d in e['token_balance_deltas'] if d['wallet_owned'] and d['mint']==f['mint'])
                if str(total)!=f['buy_amount']['raw'] or total<=0:raise ValueError('BUY_AMOUNT_BINDING')
            finally:src.close()

def transport_cycle(root,registry,source_roots):
    repo=Repository(root/'forward.sqlite')
    try:
        row=repo.db.execute("SELECT rowid AS sequence,* FROM meme_runs WHERE state='READY' ORDER BY rowid LIMIT 1").fetchone()
        if row is None:return None
        run=loads(row['body']);t=MemeTransport('LIVE',live_validator=lambda r:validate_forward(r,repo,registry,root,source_roots));before=t.api.commits;result=t.publish_run(run,row['sequence']);after=t.api.commits;t.publish_run(run,row['sequence'])
        if t.api.commits!=after:raise ValueError('IDENTICAL_REPUBLISH_WROTE')
        result.update(identical_republish_writes=0,remote_write_commits=after-before)
        with transaction(repo.db):
            repo.db.execute('INSERT OR IGNORE INTO meme_transport VALUES(?,?)',(run['run_id'],canonical(result).decode()));repo.db.execute("UPDATE meme_runs SET state='PUBLISHED' WHERE run_id=?",(run['run_id'],))
        return result
    finally:repo.close()

def worker(root,registry,source_roots,stop):
    while not stop.is_set():
        try:
            # Preserve legacy FM3 real ACTIVE path and receipts; never reinterpret its old candidates.
            transport_once(root,json.loads((root/'health.json').read_text())['run_id'])
            result=transport_cycle(root,registry,source_roots)
            if result:atomic_json(root/'meme-transport-health.json',{'status':'PASS_EXACT_GPT_HANDOFF',**result})
        except Exception as e:atomic_json(root/'meme-transport-health.json',{'status':'RETRY_PENDING','error':type(e).__name__,'at':utc()})
        stop.wait(10)

def main():
    p=argparse.ArgumentParser()
    for key in ['root','manual','raw','processed','registry','policy']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();registry=Registry(json.loads(a.registry.read_text()));policy=json.loads(a.policy.read_text());lock=(a.root/'service.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stop=threading.Event()
    for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,lambda *_:stop.set())
    old=json.loads((a.root/'health.json').read_text());h={**old,'identifier':IDENTIFIER,'system':'Meme','started_at':utc(),'pid':os.getpid(),'status':'STARTING','restart_count':old['restart_count']+1,'service_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'registry_sha256':registry.sha256,'gmail':0,'app_alert':0,'automation_mutations':0,'production_trading':False,'meme_live_handoff_writes':'AUTHORIZED_FM4_SHADOW_FACTS_ONLY'}
    repo=Repository(a.root/'forward.sqlite')
    if not repo.db.execute("SELECT value FROM meme_meta WHERE key='migration_cutoff'").fetchone():raise ValueError('MIGRATION_PREFLIGHT_REQUIRED')
    if repo.db.execute("SELECT value FROM meme_meta WHERE key='schema_hash'").fetchone()[0]!=digest(list(DDL)):raise ValueError('MEME_SQLITE_SCHEMA_DRIFT')
    rpc=ObservedRPC();collector=FrankCollector(repo,a.root/'raw',{k:str(getattr(a,k)) for k in ['manual','raw','processed']},rpc,durable_detection=True,history_limit=500)
    if collector.store.cursor() is None:raise ValueError('DURABLE_CURSOR_REQUIRED_NO_RESET')
    sources={WALLET:a.root};extra=[]
    for (chain,wallet),(person,verified) in registry.wallets.items():
        if not verified:continue
        if wallet==WALLET:continue
        path=a.root/'meme-wallets'/hashlib.sha256(wallet.encode()).hexdigest()[:24];sub=Repository(path/'forward.sqlite');extra.append((wallet,sub,WalletCollector(sub,path,wallet)));sources[wallet]=path
    atomic_json(a.root/'health.json',h)
    threads=[threading.Thread(target=worker,args=(a.root,registry,sources,stop),daemon=True),threading.Thread(target=history_loop,args=(a.root,stop),daemon=True)]
    for t in threads:t.start()
    base={k:old.get(k,0) for k in ['request_count','rpc_429_count','rpc_error_count','timeouts','retry']};before=collector.store.cursor()
    first=True
    while not stop.is_set():
        started=time.monotonic();h['last_poll_at']=utc();h['poll_count']+=1
        try:
            cycle=collector.cycle()
            # Poll all verified wallet sources before lower-priority signal/transport work.
            for wallet,sub,c in extra:c.cycle()
            h.update(status='RUNNING',last_successful_poll=utc(),gap_count=cycle['cursor_gap'])
            drain(repo,repo,registry,policy,WALLET,a.root)
            for wallet,sub,c in extra:drain(sub,repo,registry,policy,wallet,c.root)
            h['candidate_duplicate_count']+=cycle['duplicates']
            if first:atomic_json(a.root/('meme-restart-'+str(h['restart_count'])+'.json'),{'status':'PASS','cursor_before':before,'cursor_after':collector.store.cursor(),'gap':cycle['cursor_gap'],'duplicates':cycle['duplicates']});first=False
        except Exception as e:
            h.update(status='RETRY_PENDING',last_error=type(e).__name__)
            if str(e)=='FRANK_CURSOR_GAP_UNRESOLVED':h.update(status='CURSOR_GAP_BLOCKED',gap_count=1,unresolved_gap_count=h.get('unresolved_gap_count',0)+1)
        h.update(request_count=base['request_count']+rpc.calls,rpc_429_count=base['rpc_429_count']+rpc.rate_limits,rpc_error_count=base['rpc_error_count']+rpc.errors,timeouts=base['timeouts']+rpc.timeouts,retry=base['retry']+rpc.retries,last_rpc_success_at=rpc.success_at)
        snapshot_health(repo,h);h['meme_candidate_count']=repo.db.execute('SELECT count(*) FROM meme_signals').fetchone()[0];h['real_token_consensus_count']=repo.db.execute("SELECT count(*) FROM meme_signals WHERE json_extract(body,'$.signal_family_candidate')='TOKEN_CONSENSUS'").fetchone()[0];h['meme_run_count']=repo.db.execute('SELECT count(*) FROM meme_runs').fetchone()[0];h['poll_seconds']=str(time.monotonic()-started);h['uptime_seconds']=str(time.time()-epoch(h['started_at']));atomic_json(a.root/'health.json',h);stop.wait(max(0,30-(time.monotonic()-started)))
    h.update(status='STOPPED',stopped_at=utc());atomic_json(a.root/'health.json',h)
    for t in threads:t.join(timeout=3)
    for wallet,sub,c in extra:sub.close()
    repo.close()
if __name__=='__main__':main()
