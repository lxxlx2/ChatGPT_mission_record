"""One Frank-only local signal authority; scanner/model/notifier never depend on GPT."""
import argparse,fcntl,hashlib,json,os,signal,subprocess,time
from pathlib import Path
from mission_agent.signals.registry import load
from mission_agent.signals.policy import load_policy,POLICY_SHA256
from mission_agent.signals.store import Ledger
from mission_agent.signals.engine import Engine
from mission_agent.signals.scanner import Scanner
from mission_agent.signals.delivery import LocalNotifier,drain
from mission_agent.signals.runtime_io import atomic_json,utc
from mission_agent.signals.gmail import summary_from_db
from mission_agent.signals.gmail_health import health_from_summary

IDENTIFIER='com.jerson.crypto-monitor-frank-local'

def source_hash():
    root=Path(__file__).resolve().parents[1];h=hashlib.sha256()
    files=sorted((root/'mission_agent/signals').glob('*.py'))+[Path(__file__).resolve(),root/'mission_agent/frank/parser.py',root/'mission_agent/frank/rpc.py']
    for p in files:h.update(p.name.encode());h.update(p.read_bytes())
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--registry',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--authority-lock',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    policy=load_policy(a.policy);_,wallets=load(a.registry)
    ledger=Ledger(a.root/'forward.sqlite');engine=Engine(ledger,policy,dry_run=False)
    if any(ledger.cursor(w) is None for w in wallets):raise ValueError('CHECKPOINT_REQUIRED_NO_INITIAL_CURSOR_RESET')
    if ledger.db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLITE_INTEGRITY_FAILURE')
    if ledger.db.execute('PRAGMA foreign_key_check').fetchone() is not None:raise ValueError('SQLITE_FOREIGN_KEY_FAILURE')
    if a.check:
        print(json.dumps({'status':'PREFLIGHT_PASS','policy_hash':POLICY_SHA256,'cursor':[ledger.cursor(w) for w in wallets],'pending_unprocessed_signatures':ledger.db.execute('SELECT count(*) FROM signatures s LEFT JOIN v1_seen v USING(wallet,signature) WHERE v.signature IS NULL').fetchone()[0]}));ledger.db.close();return
    # Legacy and new scanners share this flock: even a mistaken double launch fails closed.
    authority=a.authority_lock.open('a');fcntl.flock(authority,fcntl.LOCK_EX|fcntl.LOCK_NB)
    own=(a.root/'service.lock').open('a');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stopped=False
    def stop(*_):
        nonlocal stopped
        stopped=True
    for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,stop)
    scanner=Scanner(ledger,wallets,a.root/'raw',mode='LIVE');notifier=LocalNotifier(receipt_root=a.root/'local-receipts')
    path=a.root/'health.json';old=json.loads(path.read_text()) if path.exists() else {};before={w:ledger.cursor(w) for w in wallets};first=True
    git_root=Path(__file__).resolve().parents[3];commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=git_root,text=True).strip();source=source_hash()
    health={'system':'FRANK_ONLY','policy':'FRANK_LOCAL_SIGNAL_V1','policy_hash':POLICY_SHA256,'identifier':IDENTIFIER,'pid':os.getpid(),'started_at':utc(),'first_started_at':old.get('first_started_at',utc()),'restart_count':old.get('restart_count',-1)+1,'code_commit':commit,'loaded_source_sha256':source,'poll_count':old.get('poll_count',0),'consecutive_errors':0,'poll_interval_seconds':30,'delivery_authority':'LOCAL_DETERMINISTIC_SIGNAL','gpt_in_critical_path':False,'production_trading':'NO_GO','other_persons':'DEFERRED','new_automation':False,'status':'STARTING'}
    health.update(health_from_summary(summary_from_db(ledger.db)))
    atomic_json(path,health)
    while not stopped:
        started=time.monotonic();health['last_poll_at']=utc();health['poll_count']+=1
        cycles=[]
        try:
            # Clock is read before the address scan. No time-stage processing can leap over an RPC gap.
            clocks={w:scanner.rpcs[w].finalized_clock() for w in wallets}
            for wallet in wallets:cycles.append(scanner.cycle(wallet))
            engine.drain(until=min(c['block_time'] for c in clocks.values()))
            deliveries=drain(ledger,notifier)
            current={w:ledger.cursor(w) for w in wallets}
            health.update(status='RUNNING',last_successful_poll=utc(),last_model_successful_eval=utc(),last_chain_signature=cycles[0]['last_chain_signature'],last_processed_signature=current[next(iter(wallets))]['signature'],last_processed_slot=current[next(iter(wallets))]['slot'],lag_seconds=cycles[0]['lag_seconds'],consecutive_errors=0,new_signatures=sum(c['new_signatures'] for c in cycles),model=engine.summary(),local_pending=sum(r['channel']=='local' and r['status']!='COMMAND_ACCEPTED' and r['status']!='DRY_RUN_AUDIT' for r in deliveries),raw_pending=ledger.db.execute("SELECT count(*) FROM signature_detections WHERE state='RAW_PENDING'").fetchone()[0],model_unprocessed=ledger.db.execute('SELECT count(*) FROM signatures s LEFT JOIN v1_seen v USING(wallet,signature) WHERE v.signature IS NULL').fetchone()[0])
            health.update(health_from_summary(summary_from_db(ledger.db)))
            if first:
                atomic_json(a.root/'first-cycle.json',{'status':'PASS','cursor_before':before,'cursor_after':current,'catchup_signatures':sum(c['new_signatures'] for c in cycles),'gap':sum(c['lag_seconds']!=0 for c in cycles),'at':utc()});first=False
        except Exception as exc:
            health.update(status='RETRY_PENDING',last_error=type(exc).__name__+':'+str(exc),consecutive_errors=health['consecutive_errors']+1)
        health['source_drift']=source_hash()!=source;health['uptime_seconds']=str(time.time()-__import__('datetime').datetime.fromisoformat(health['started_at']).timestamp());atomic_json(path,health)
        deadline=time.monotonic()+max(0,30-(time.monotonic()-started))
        while not stopped and time.monotonic()<deadline:time.sleep(min(.5,deadline-time.monotonic()))
    health.update(status='STOPPED',stopped_at=utc());atomic_json(path,health);ledger.db.close()
if __name__=='__main__':main()
