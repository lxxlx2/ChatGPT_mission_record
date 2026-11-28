"""One Frank-only local signal authority; scanner/model/notifier never depend on GPT."""
import argparse,fcntl,hashlib,json,os,signal,sqlite3,stat,subprocess,time
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit
from mission_agent.signals.registry import load
from mission_agent.signals.policy import load_policy,POLICY_SHA256
from mission_agent.signals.store import Ledger
from mission_agent.signals.engine import Engine
from mission_agent.signals.buy_admission import BuyDeliveryGate, MEME_SCOPE_BLOCKED
from mission_agent.signals.auto_buy_category import AutoBuyCategory
from mission_agent.signals.scanner import Scanner,WalletRPC
from mission_agent.signals.delivery import LocalNotifier,drain
from mission_agent.signals.runtime_io import atomic_json,utc
from mission_agent.signals.gmail import summary_from_db
from mission_agent.signals.gmail_health import health_from_summary

IDENTIFIER='com.jerson.crypto-monitor-frank-local'

def configured_scanner_rpc(path=None):
    """Read the first endpoint from the existing private configuration format."""
    if path is None:
        path = Path.home() / 'Library/Application Support/FrankMeme/solana_rpc_urls'
    try:
        # Check the opened object so a replaced pathname cannot bypass the checks.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            mode = os.fstat(fd).st_mode
            if not stat.S_ISREG(mode) or mode & 0o077:
                raise ValueError('unsafe RPC config file')
            with os.fdopen(fd, encoding='utf-8', closefd=False) as config:
                endpoint = config.read().partition(',')[0].strip()
        finally:
            os.close(fd)
        if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in endpoint):
            raise ValueError('invalid RPC endpoint')
        parsed = urlsplit(endpoint)
        # Validate numeric port syntax and range before starting transport.
        parsed.port
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or '#' in endpoint):
            raise ValueError('invalid RPC endpoint')
        return endpoint
    except (OSError, ValueError):
        raise RuntimeError('FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID') from None

def source_hash():
    root=Path(__file__).resolve().parents[1];h=hashlib.sha256()
    files=sorted((root/'mission_agent/signals').glob('*.py'))+[Path(__file__).resolve(),root/'mission_agent/frank/parser.py',root/'mission_agent/frank/rpc.py']
    for p in files:h.update(p.name.encode());h.update(p.read_bytes())
    return h.hexdigest()

def check_snapshot(path, wallets):
    """Check a standalone SQLite backup without running ledger migrations."""
    if path.is_symlink() or not path.is_file():
        raise ValueError('SCANNER_SNAPSHOT_REQUIRED')
    wal=path.with_name(path.name+'-wal')
    if wal.exists() or wal.is_symlink():
        raise ValueError('SCANNER_SNAPSHOT_WAL_NOT_INCLUDED')
    for suffix in ('-shm', '-journal'):
        sidecar=path.with_name(path.name+suffix)
        if sidecar.exists() or sidecar.is_symlink():
            raise ValueError('SCANNER_SNAPSHOT_SIDECAR_PRESENT')
    uri=path.resolve().as_uri()+'?mode=ro&immutable=1'
    with closing(sqlite3.connect(uri,uri=True)) as db:
        db.row_factory=sqlite3.Row
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('SQLITE_INTEGRITY_FAILURE')
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('SQLITE_FOREIGN_KEY_FAILURE')
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'cursors','signatures'}<=tables:
            raise ValueError('SCANNER_SNAPSHOT_SCHEMA_UNSUPPORTED')
        cursors=[]
        for wallet in wallets:
            row=db.execute('SELECT wallet,signature,slot,updated_at FROM cursors WHERE wallet=?',(wallet,)).fetchone()
            if row is None or not row['signature'] or type(row['slot']) is not int or row['slot']<0:
                raise ValueError('CHECKPOINT_REQUIRED_NO_INITIAL_CURSOR_RESET')
            cursors.append(dict(row))
        if 'v1_meta' in tables:
            old=db.execute("SELECT value FROM v1_meta WHERE key='policy_hash'").fetchone()
            if old and old[0]!=POLICY_SHA256:raise ValueError('MODEL_POLICY_HASH_DRIFT')
        query=('SELECT count(*) FROM signatures s LEFT JOIN v1_seen v USING(wallet,signature) WHERE v.signature IS NULL'
               if 'v1_seen' in tables else 'SELECT count(*) FROM signatures')
        pending=db.execute(query).fetchone()[0]
    return {'status':'PREFLIGHT_PASS','policy_hash':POLICY_SHA256,'cursor':cursors,
            'pending_unprocessed_signatures':pending}

def scan_wallet_batch(scanner, wallets):
    """Keep successful raw capture independent of another wallet's transport failure."""
    clocks, cycles, failures = {}, {}, {}
    for wallet in wallets:
        try:
            clocks[wallet] = scanner.rpcs[wallet].finalized_clock()
        except Exception as exc:
            scanner.record_failure(wallet, exc)
            failures[wallet] = type(exc).__name__
    for wallet in clocks:
        try:
            cycles[wallet] = scanner.cycle(wallet)
        except Exception as exc:
            failures[wallet] = type(exc).__name__
    return clocks, cycles, failures


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--registry',type=Path,required=True)
    p.add_argument('--policy',type=Path,required=True)
    p.add_argument('--authority-lock',type=Path,required=True)
    p.add_argument('--rpc-config',type=Path,help='Private RPC config file. Defaults to the existing macOS FrankMeme file.')
    p.add_argument('--buy-qualifications',type=Path,help='Existing local Meme qualification file; overrides FRANK_BUY_QUALIFICATIONS_PATH.')
    p.add_argument('--buy-category-evidence',type=Path,help='Explicit, local opt-in category receipt file; no source fetch.')
    p.add_argument('--auto-buy-categories', action='store_true',
                   help='Qualify indexed unknown Mints through the existing CoinGecko Demo key.')
    p.add_argument('--check',action='store_true',help='Check a standalone SQLite backup without opening a writer.')
    a=p.parse_args()
    if not a.check or a.rpc_config is not None:
        try:
            endpoint=configured_scanner_rpc(a.rpc_config)
        except RuntimeError as exc:
            p.exit(2, f'{exc}\n')
    policy=load_policy(a.policy);_,wallets=load(a.registry)
    if a.check:
        try:
            result=check_snapshot(a.root/'forward.sqlite',wallets)
        except ValueError as exc:
            p.exit(2,f'{exc}\n')
        except (OSError,sqlite3.Error):
            p.exit(2,'SCANNER_SNAPSHOT_READ_FAILED\n')
        print(json.dumps(result))
        return
    # Claim both exclusions before initializing or migrating the ledger.
    authority=a.authority_lock.open('a');fcntl.flock(authority,fcntl.LOCK_EX|fcntl.LOCK_NB)
    own=(a.root/'service.lock').open('a');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
    delivery_gate=BuyDeliveryGate(a.buy_qualifications, category_evidence_path=a.buy_category_evidence)
    ledger=Ledger(a.root/'forward.sqlite');engine=Engine(ledger,policy,dry_run=False,delivery_gate=delivery_gate)
    if any(ledger.cursor(w) is None for w in wallets):raise ValueError('CHECKPOINT_REQUIRED_NO_INITIAL_CURSOR_RESET')
    if ledger.db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLITE_INTEGRITY_FAILURE')
    if ledger.db.execute('PRAGMA foreign_key_check').fetchone() is not None:raise ValueError('SQLITE_FOREIGN_KEY_FAILURE')
    category_key = os.environ.get('COINGECKO_DEMO_API_KEY') if a.auto_buy_categories else None
    categories = AutoBuyCategory(ledger.db, api_key=category_key, manual_path=delivery_gate.path,
                                 receipt_path=a.buy_category_evidence) if category_key else None
    stopped=False
    def stop(*_):
        nonlocal stopped
        stopped=True
    for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,stop)
    scanner=Scanner(ledger,wallets,a.root/'raw',rpcs={w:WalletRPC(w,endpoint=endpoint) for w in wallets},mode='LIVE');notifier=LocalNotifier(receipt_root=a.root/'local-receipts')
    path=a.root/'health.json';old=json.loads(path.read_text()) if path.exists() else {};before={w:ledger.cursor(w) for w in wallets};first=True
    git_root=Path(__file__).resolve().parents[3];commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=git_root,text=True).strip();source=source_hash()
    health={'system':'FRANK_ONLY','policy':'FRANK_LOCAL_SIGNAL_V1','policy_hash':POLICY_SHA256,'identifier':IDENTIFIER,'pid':os.getpid(),'started_at':utc(),'first_started_at':old.get('first_started_at',utc()),'restart_count':old.get('restart_count',-1)+1,'code_commit':commit,'loaded_source_sha256':source,'poll_count':old.get('poll_count',0),'consecutive_errors':0,'poll_interval_seconds':30,'delivery_authority':'LOCAL_DETERMINISTIC_SIGNAL','gpt_in_critical_path':False,'production_trading':'NO_GO','other_persons':'DEFERRED','new_automation':False,'status':'STARTING'}
    health.update(health_from_summary(summary_from_db(ledger.db)))
    health['buy_category_capture'] = {'status': (
        'WAITING_FOR_SCAN' if categories else 'SOURCE_NOT_CONFIGURED' if a.auto_buy_categories else 'NOT_ENABLED'
    )}
    atomic_json(path,health)
    while not stopped:
        started=time.monotonic();health['last_poll_at']=utc();health['poll_count']+=1
        try:
            clocks, wallet_cycles, wallet_failures = scan_wallet_batch(scanner, wallets)
            cycles = list(wallet_cycles.values())
            health['wallet_scan_failures'] = len(wallet_failures)
            health['new_signatures'] = sum(c['new_signatures'] for c in cycles)
            if categories and cycles:
                try:
                    health['buy_category_capture'] = categories.refresh()
                except (OSError, ValueError, sqlite3.Error) as exc:
                    health['buy_category_capture'] = {'status': 'CATEGORY_SYNC_UNAVAILABLE',
                                                       'error_type': type(exc).__name__}
            # V1 can aggregate wallets for Frank, so pending chain facts must
            # stay ahead of any scheduled model stages or new deliveries.
            if wallet_failures:
                raise RuntimeError('WALLET_BATCH_INCOMPLETE')
            engine.drain(until=min(c['block_time'] for c in clocks.values()))
            deliveries=drain(ledger,notifier,delivery_gate=delivery_gate)
            current={w:ledger.cursor(w) for w in wallets}
            health.update(status='RUNNING',last_successful_poll=utc(),last_model_successful_eval=utc(),last_chain_signature=cycles[0]['last_chain_signature'],last_processed_signature=current[next(iter(wallets))]['signature'],last_processed_slot=current[next(iter(wallets))]['slot'],lag_seconds=cycles[0]['lag_seconds'],consecutive_errors=0,new_signatures=sum(c['new_signatures'] for c in cycles),model=engine.summary(),local_pending=sum(r['channel']=='local' and r['status'] not in ('COMMAND_ACCEPTED','DRY_RUN_AUDIT',MEME_SCOPE_BLOCKED,'SENT_UNVERIFIED') for r in deliveries),raw_pending=ledger.db.execute("SELECT count(*) FROM signature_detections WHERE state='RAW_PENDING'").fetchone()[0],model_unprocessed=ledger.db.execute('SELECT count(*) FROM signatures s LEFT JOIN v1_seen v USING(wallet,signature) WHERE v.signature IS NULL').fetchone()[0])
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
