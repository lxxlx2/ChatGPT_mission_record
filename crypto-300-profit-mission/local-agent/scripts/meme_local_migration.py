"""Mac-local transactional scanner rename. Restore known-good agent on any failed gate."""
import argparse,hashlib,json,os,plistlib,re,shutil,sqlite3,subprocess,time
from pathlib import Path
from scripts.frank_shadow_service import ForwardTransport,atomic_json,utc
from scripts.frank_shadow_launchagent import IDENTIFIER as OLD
from scripts.meme_shadow_service import IDENTIFIER as NEW
from mission_agent.db.repository import Repository
from mission_agent.db.connection import transaction
from mission_agent.frank.rpc import WALLET
from mission_agent.hashing import canonical,loads
from mission_agent.meme.registry import Registry
from mission_agent.meme.schema import run_bundle
from mission_agent.meme.state import migrate

DOMAIN='gui/'+str(os.getuid())

def command(*args,check=True):return subprocess.run(args,capture_output=True,text=True,check=check)
def scanner_processes():
    result=[]
    for line in command('ps','-axo','pid=,ppid=,command=').stdout.splitlines():
        parts=line.split(None,2)
        if len(parts)!=3:continue
        words=parts[2].split()
        if not words or not Path(words[0]).name.lower().startswith('python'):continue
        if '-m' in words and words[words.index('-m')+1] in ('scripts.frank_shadow_service','scripts.meme_shadow_service'):
            result.append({'pid':int(parts[0]),'parent':int(parts[1]),'module':words[words.index('-m')+1]})
    return result

def history_processes():
    return [line for line in command('ps','-axo','pid=,command=').stdout.splitlines() if '-m scripts.frank_backfill --snapshot ' in line and Path(line.split(None,1)[1].split()[0]).name.lower().startswith('python')]

def state(root,*,remote=True):
    h=json.loads((root/'health.json').read_text());db=sqlite3.connect(f'file:{root / "forward.sqlite"}?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('BEGIN')
    cursor=dict(db.execute("SELECT * FROM frank_cursor WHERE name='latest'").fetchone())
    counts={name:db.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ['frank_transactions','frank_observations','candidates','batches']}
    ids=[r[0] for r in db.execute('SELECT event_id FROM candidates ORDER BY event_id')]
    integrity=db.execute('PRAGMA integrity_check').fetchone()[0];db.rollback();db.close()
    value={'at':utc(),'health':h,'cursor':cursor,'counts':counts,'candidate_ids':ids,'sqlite_path':str(root/'forward.sqlite'),'sqlite_integrity':integrity,'scanners':scanner_processes(),'launchagents':sorted(p.name for p in (Path.home()/'Library/LaunchAgents').glob('*.plist')),'private_manifest':None,'meme_manifest':None}
    if remote:
        t=ForwardTransport(h['run_id']);x=t.read(t.branch,t.namespace+'/ingest/current.json');value['private_manifest']={'path':x.path,'blob_sha':x.blob_sha,'batch_id':x.value['batch_id'],'payload_sha256':x.value['payload_sha256']}
        from mission_agent.meme.transport import MemeTransport
        mt=MemeTransport('LIVE');x=mt._optional(mt.branch,mt.namespace+'/manifest/current.json')
        if x:value['meme_manifest']={'blob_sha':x.blob_sha,**x.value}
    return value

def snapshot(root,out,old_plist,registry,policy):
    out.mkdir(mode=0o700);db=sqlite3.connect(root/'forward.sqlite');target=sqlite3.connect(out/'forward.sqlite');db.backup(target);assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok';target.close();db.close();(out/'forward.sqlite').chmod(0o600)
    names={'health.json','initial-boundary.json','active-e2e-independent-readback.json','post-active-restart-before.json','post-active-restart-after.json','first-real-forward-unknown-receipt.json'}
    names.update(p.name for pattern in ['transport-*.json','restart-*.json'] for p in root.glob(pattern))
    for name in sorted(names):
        if (root/name).exists():shutil.copyfile(root/name,out/name);(out/name).chmod(0o600)
    for name in ['raw','detections']:
        if (root/name).exists():shutil.copytree(root/name,out/name)
    for src in [old_plist,registry,policy]:shutil.copyfile(src,out/src.name);(out/src.name).chmod(0o600)
    hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()};atomic_json(out/'snapshot-hashes.json',hashes)
    return hashes

def assert_transition(before,after):
    assert after['sqlite_integrity']=='ok','SQLITE_INTEGRITY'
    assert len(after['scanners'])==1 and after['scanners'][0]['module']=='scripts.meme_shadow_service','EXACT_ONE_SCANNER'
    assert after['health']['status']=='RUNNING','MEME_NOT_RUNNING'
    assert after['health']['gap_count']==after['health']['unresolved_gap_count']==after['health']['candidate_duplicate_count']==0,'GAP_OR_DUPLICATE'
    assert after['cursor']['slot']>=before['cursor']['slot'],'CURSOR_BACKWARD'
    assert all(after['counts'][k]>=v for k,v in before['counts'].items()),'STATE_RESET'
    assert set(before['candidate_ids'])<=set(after['candidate_ids']),'OLD_CANDIDATE_LOST'
    assert after['health']['poll_count']>before['health']['poll_count'],'POLL_COUNTER_STALLED'
    assert after['health']['active_e2e_status']=='FRANK_ACTIVE_E2E_PASS','E2E_NOT_PRESERVED'
    if before['meme_manifest']:
        assert after['meme_manifest'] and after['meme_manifest']['sequence']>=before['meme_manifest']['sequence'],'MANIFEST_BACKWARD'
        if after['meme_manifest']['sequence']==before['meme_manifest']['sequence']:assert after['meme_manifest']['blob_sha']==before['meme_manifest']['blob_sha'],'IMMUTABLE_POINTER_CHANGED'


def wait_running(root,old_poll,timeout=60):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        h=json.loads((root/'health.json').read_text())
        if h['identifier']==NEW and h['status']=='RUNNING' and h['poll_count']>old_poll:return
        time.sleep(1)
    raise RuntimeError('LOCAL_POLL_ACCEPTANCE_TIMEOUT')

def wait_handoff(root,timeout=120):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        path=root/'meme-transport-health.json'
        if path.exists() and json.loads(path.read_text()).get('status')=='PASS_EXACT_GPT_HANDOFF':return
        time.sleep(1)
    raise RuntimeError('EXACT_PRIVATE_HANDOFF_TIMEOUT')

def restore_agent(old_path,new_path,old_data,domain=DOMAIN):
    command('launchctl','bootout',domain+'/'+NEW,check=False)
    end=time.monotonic()+30
    while scanner_processes() and time.monotonic()<end:time.sleep(1)
    if scanner_processes():raise RuntimeError('ROLLBACK_SCANNER_STILL_RUNNING')
    if new_path.exists():new_path.unlink()
    old_path.write_bytes(old_data);old_path.chmod(0o600)
    command('launchctl','enable',domain+'/'+OLD);command('launchctl','bootstrap',domain,str(old_path))

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();module=Path(__file__).resolve().parents[1];registry_path=module/'config/meme_person_registry.json';policy_path=module/'config/meme_shadow_policy.json';registry=Registry(json.loads(registry_path.read_text()));registry.person('solana',WALLET)
    a.evidence.mkdir(parents=True,exist_ok=False,mode=0o700);before=state(a.root);atomic_json(a.evidence/'pre-migration-state.json',before)
    assert before['sqlite_integrity']=='ok' and before['health']['status']=='RUNNING','PREFLIGHT_STATE'
    assert before['health']['gap_count']==before['health']['unresolved_gap_count']==0,'PREFLIGHT_GAP'
    assert len(before['scanners'])==1 and before['scanners'][0]['module']=='scripts.frank_shadow_service','OLD_SCANNER_COUNT'
    old_path=Path.home()/'Library/LaunchAgents'/(OLD+'.plist');new_path=old_path.with_name(NEW+'.plist');old_data=old_path.read_bytes();assert not new_path.exists(),'SECOND_SCANNER_PLIST'
    config=plistlib.loads(old_data);assert config['Label']==OLD and config['WorkingDirectory']==str(module),'LOCAL_CONFIG_BINDING'
    args=config['ProgramArguments'];assert args[args.index('--root')+1]==str(a.root),'DURABLE_ROOT_BINDING'
    assert before['health']['pid']==before['scanners'][0]['pid'],'HEALTH_PID_BINDING'
    assert set(config.get('EnvironmentVariables',{}))<= {'PATH','PYTHONUNBUFFERED'},'DO_NOT_SNAPSHOT_SECRETS'
    snapshot(a.root,a.evidence/'snapshot',old_path,registry_path,policy_path)
    stopped=False
    try:
        command('launchctl','bootout',DOMAIN+'/'+OLD);stopped=True
        deadline=time.monotonic()+40
        while (scanner_processes() or history_processes()) and time.monotonic()<deadline:time.sleep(1)
        assert not scanner_processes() and not history_processes(),'OLD_WORKER_RESIDUAL'
        stopped_state=state(a.root);atomic_json(a.evidence/'migration-before.json',stopped_state)
        snapshot(a.root,a.evidence/'stopped-snapshot',old_path,registry_path,policy_path)
        repo=Repository(a.root/'forward.sqlite');cutoff=utc();migrate(repo.db,cutoff,registry,legacy_wallet=WALLET)
        # A real LIVE empty bundle proves the current contract without replaying the FM3 ACTIVE.
        empty=run_bundle([],'LIVE')
        with transaction(repo.db):repo.db.execute('INSERT OR IGNORE INTO meme_runs VALUES(?,?,?,?)',(empty['run_id'],cutoff,canonical(empty).decode(),'READY'))
        repo.close();atomic_json(a.evidence/'migration-cutoff.json',{'cutoff':cutoff,'old_candidates_excluded':stopped_state['counts']['frank_observations']})
        config['Label']=NEW;args=config['ProgramArguments'];args[args.index('scripts.frank_shadow_service')]='scripts.meme_shadow_service';args+=['--registry',str(registry_path),'--policy',str(policy_path)];config['StandardOutPath']=str(a.root/'meme.stdout.log');config['StandardErrorPath']=str(a.root/'meme.stderr.log')
        new_path.write_bytes(plistlib.dumps(config));new_path.chmod(0o600);command('plutil','-lint',str(new_path));old_path.unlink();command('launchctl','disable',DOMAIN+'/'+OLD);command('launchctl','enable',DOMAIN+'/'+NEW);command('launchctl','bootstrap',DOMAIN,str(new_path));wait_running(a.root,before['health']['poll_count']);time.sleep(31)
        wait_handoff(a.root);after=state(a.root);assert_transition(before,after)
        assert after['meme_manifest'] is not None,'PRIVATE_HANDOFF_MISSING'
        db=sqlite3.connect(a.root/'forward.sqlite')
        assert db.execute("SELECT COUNT(*) FROM meme_source_observations WHERE state='BASELINE_EXCLUDED'").fetchone()[0]>=stopped_state['counts']['frank_observations'],'BASELINE_REPLAY'
        assert db.execute("SELECT COUNT(*) FROM meme_signals s JOIN meme_facts f ON json_extract(s.body,'$.facts[0].event_id')=f.event_id JOIN meme_source_observations o ON o.signature=json_extract(f.body,'$.signature') AND o.wallet=json_extract(f.body,'$.wallet') WHERE o.state='BASELINE_EXCLUDED'").fetchone()[0]==0,'OLD_CANDIDATE_REPLAY';db.close()
        atomic_json(a.evidence/'migration-after.json',after);command('launchctl','kickstart','-k',DOMAIN+'/'+NEW);wait_running(a.root,after['health']['poll_count']);time.sleep(31);restarted=state(a.root);assert_transition(after,restarted);atomic_json(a.evidence/'restart-after.json',restarted);atomic_json(a.evidence/'migration-result.json',{'status':'MIGRATION_PASS','scanners':1,'sqlite_integrity':'ok','cursor_monotonic':True,'old_candidate_replay':0,'controlled_restart':'PASS','rollback_snapshot_usable':True});print('MIGRATION_PASS',flush=True)
    except BaseException as e:
        if stopped:restore_agent(old_path,new_path,old_data)
        atomic_json(a.evidence/'migration-result.json',{'status':'MIGRATION_ROLLED_BACK' if stopped else 'PREFLIGHT_BLOCKED','error':type(e).__name__})
        raise
if __name__=='__main__':main()
