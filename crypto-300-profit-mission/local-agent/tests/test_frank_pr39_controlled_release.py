"""Isolated temp SQLite/files; fake launchd/HTTP. No production/provider access."""
import copy
import json
import multiprocessing
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import frank_pr39_controlled_release as r
from mission_agent.mission_control.db import ControlDB, utc
from mission_agent.mission_control.delivery import GmailDelivery, LocalDelivery
from mission_agent.mission_control.service import MissionMemeService
from mission_agent.hashing import digest


def payload(decision='BUY'):
    return {'person_id':'frank', 'mint':'TEST_ONLY', 'episode_id':'fixture',
            'source_signal_type':'FRANK_MULTIPLE_SIGNAL', 'decision':decision,
            'created_at':utc(), 'inputs':{'buy_count':3,'pattern':'MULTIPLE'}, 'metrics':{},
            'reasons':[], 'missing':[], 'invalidation':[]}


@pytest.fixture
def dbfile(tmp_path):
    path = tmp_path / 'control.sqlite'; db = ControlDB(path)
    event = db.record(payload(), 'P', 'H')['event']
    GmailDelivery(db).enqueue(event, mode='DRY_RUN_AUDIT', forbidden=True)
    LocalDelivery(db).enqueue(event, forbidden=True)
    db.db.execute('DROP TABLE local_delivery_presentation'); db.close()
    return path


def test_additive_migration_preserves_legacy_and_old_reader(dbfile):
    before = r.ledger(dbfile); r.migrate(dbfile); r.migrate(dbfile)
    r.assert_preserved(before, r.ledger(dbfile), exact=True)
    with sqlite3.connect(dbfile) as db:
        assert db.execute('SELECT COUNT(*) FROM gmail_delivery').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM local_delivery_presentation').fetchone()[0] == 0
        db.execute('PRAGMA foreign_keys=ON')
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO local_delivery_presentation VALUES('missing','t','s','h')")


@pytest.mark.parametrize('status', ['PENDING','RETRYABLE_ERROR','CREDENTIAL_BLOCKED','SENDING','SENT_UNVERIFIED','UNKNOWN'])
def test_gmail_unfinished_blocks(dbfile,status):
    with sqlite3.connect(dbfile) as db: db.execute('UPDATE gmail_delivery SET status=?',(status,))
    with pytest.raises(RuntimeError,match='ACTIVE_OR_UNKNOWN'): r.ledger(dbfile)


@pytest.mark.parametrize('status', ['PENDING','RETRY_PENDING','UNKNOWN'])
def test_old_local_pending_blocks(dbfile,status):
    with sqlite3.connect(dbfile) as db: db.execute('UPDATE local_delivery SET status=?',(status,))
    with pytest.raises(RuntimeError,match='ACTIVE_OR_UNKNOWN'): r.ledger(dbfile)


def test_pending_outbox_blocks(dbfile):
    with sqlite3.connect(dbfile) as db: db.execute("UPDATE decision_outbox SET status='PENDING'")
    with pytest.raises(RuntimeError,match='ACTIVE_OR_UNKNOWN'): r.ledger(dbfile)


@pytest.mark.parametrize('column,value',[('body','tamper'),('subject','tamper'),('wire_message_id','tamper'),('attempt_count',7),('receipt','tamper'),('content_hash','tamper')])
def test_immutable_identity_guard(dbfile,column,value):
    before = r.ledger(dbfile)
    with sqlite3.connect(dbfile) as db: db.execute('UPDATE gmail_delivery SET '+column+'=?',(value,))
    with pytest.raises(RuntimeError): r.assert_preserved(before,r.ledger(dbfile))


def test_manual_reasons_redacted_not_inferred(dbfile):
    with sqlite3.connect(dbfile) as db:
        db.execute("UPDATE gmail_delivery SET delivery_mode='LIVE',status='MANUAL_REVIEW',last_error='secret@example.com'")
        decision_id=db.execute('SELECT decision_id FROM gmail_delivery').fetchone()[0]
        wire='<mission.'+digest({'decision_id':decision_id,'mode':'LIVE'})+'@local.invalid>'
        db.execute('UPDATE gmail_delivery SET wire_message_id=?',(wire,))
        db.execute("UPDATE decision_outbox SET status='MANUAL_REVIEW' WHERE channel='gmail'")
    facts = r.review_reasons(r.ledger(dbfile))
    assert facts['requires_private_review'] == 1
    assert facts['reason_counts'] == {'UNVERIFIED_OTHER_REASON':1}
    assert 'secret' not in json.dumps(facts)


def test_stale_manual_requires_zero_attempts(dbfile):
    with sqlite3.connect(dbfile) as db:
        db.execute("UPDATE gmail_delivery SET delivery_mode='LIVE',status='MANUAL_REVIEW',last_error='GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND'")
        decision_id=db.execute('SELECT decision_id FROM gmail_delivery').fetchone()[0]
        wire='<mission.'+digest({'decision_id':decision_id,'mode':'LIVE'})+'@local.invalid>'
        db.execute('UPDATE gmail_delivery SET wire_message_id=?',(wire,))
        db.execute("UPDATE decision_outbox SET status='MANUAL_REVIEW' WHERE channel='gmail'")
    assert r.review_reasons(r.ledger(dbfile))['expired_before_any_send'] == 1
    with sqlite3.connect(dbfile) as db: db.execute('UPDATE gmail_delivery SET attempt_count=1')
    assert r.review_reasons(r.ledger(dbfile))['requires_private_review'] == 1


def test_n4_hash_change_does_not_create_sendable_event(dbfile):
    db = ControlDB(dbfile); old = dict(db.db.execute('SELECT * FROM decision_events').fetchone())
    new = payload(); new['inputs'] = MissionMemeService._decision_inputs(
        {'person_id':'frank','latest_buy_amount_predicate':'USDC_DIRECT_NUMERIC',
         'latest_buy_amount_predicate_reason':'fixture'}, {})
    assert digest(new['inputs']) != digest(json.loads(old['body'])['inputs'])
    before = r.ledger(dbfile); db.upsert_latest(new,'P','H'); result = db.record(new,'P','H')
    assert result['changed'] is False and result['event']['decision_id'] == old['decision_id']
    r.assert_preserved(before,r.ledger(dbfile),exact=True); db.close()


def test_backup_wal_consistency_private_and_timeout(dbfile,tmp_path):
    c=sqlite3.connect(dbfile); c.execute('CREATE TABLE test_committed(x)'); c.commit()
    c.execute('INSERT INTO test_committed VALUES(4)'); c.commit()
    dest=tmp_path/'backup.sqlite'; r.backup(dbfile,dest)
    assert dest.stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(dest) as db: assert db.execute('SELECT x FROM test_committed').fetchone()[0] == 4
    c.close()
    with pytest.raises(RuntimeError,match='BACKUP_LOCK_OR_TIMEOUT'):
        r.backup(dbfile,tmp_path/'expired.sqlite',deadline=-1)


def test_database_lock_blocks_migration(dbfile):
    lock=sqlite3.connect(dbfile); lock.execute('BEGIN IMMEDIATE')
    try:
        with pytest.raises(sqlite3.OperationalError,match='locked'): r.migrate(dbfile)
    finally: lock.rollback(); lock.close()


def test_low_disk_readonly(dbfile,tmp_path,monkeypatch):
    monkeypatch.setattr(r.shutil,'disk_usage',lambda _:SimpleNamespace(free=0))
    before=r.sha(dbfile)
    with pytest.raises(RuntimeError,match='DISK_SPACE'): r.disk_gate(tmp_path,[dbfile])
    assert r.sha(dbfile)==before


def test_mixed_and_extra_source_blocked(tmp_path):
    root=tmp_path/'repo'; root.mkdir(); (root/'mission_agent').mkdir(); (root/'config').mkdir()
    source=root/'mission_agent/a.py'; source.write_text('x=1\n')
    subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@local.invalid','commit','-qm','fixture'],check=True)
    r.source_manifest(root); source.write_text('x=2\n')
    with pytest.raises(RuntimeError,match='SOURCE_MIXED_BYTES'): r.source_manifest(root)
    source.write_text('x=1\n'); (root/'mission_agent/extra.py').write_text('x=2')
    with pytest.raises(RuntimeError,match='SOURCE_EXTRA_FILE'): r.source_manifest(root)


def test_runner_preserves_config_disables_export(tmp_path):
    old,new=tmp_path/'old',tmp_path/'new'
    text='#!/bin/bash\nLOCAL_AGENT="'+str(old)+'"\nexec env PYTHONPATH=. python x\n'
    changed=r.replace_source(text,new)
    assert changed.replace(str(new),str(old)).replace('export MISSION_EVIDENCE_EXPORT_ENABLED=0\n','')==text
    with pytest.raises(RuntimeError): r.replace_source(text,Path('/tmp/$(unsafe)'))


class FakeMac:
    def __init__(self,tmp,context):
        self.runners={k:tmp/(k+'.sh') for k in ('loop','dashboard')}
        self.labels={k:k for k in self.runners}; self.context=context; self.calls=[]
        self.state_path=tmp/'fake-launchd.json'
        if not self.state_path.exists(): self.write({'loop':1,'dashboard':2})
    def write(self,state): self.state_path.write_text(json.dumps(state))
    def state(self): return json.loads(self.state_path.read_text())
    def runtime(self,key,text):
        result=copy.deepcopy(self.context['runtime'][key]); result['pid']=self.state()[key]
        if text==self.context['new_texts'][key]: result['source']=self.context['new_source']
        return result
    def stop(self,key):
        self.calls.append(('stop',key)); state=self.state(); state.pop(key,None); self.write(state)
    def start(self,key,plist):
        self.calls.append(('start',key)); state=self.state(); state[key]=11 if key=='loop' else 12; self.write(state)
    def launch(self,label):
        if label not in self.state(): raise subprocess.CalledProcessError(1,['fake'])
        return self.state()[label],''
    def worker_pids(self,context): return list(self.state().values())
    def wait_dead(self,pids): pass
    def absent(self,key): assert key not in self.state()


@pytest.fixture
def release(dbfile,tmp_path,monkeypatch):
    old,new=tmp_path/'old',tmp_path/'new'; old.mkdir(); new.mkdir()
    (old/'a.py').write_text('old'); (new/'a.py').write_text('new')
    protected=tmp_path/'frozen'; protected.write_text('FROZEN')
    runtime={k:{'pid':n,'agent':str(old),'source':{'a.py':r.sha(old/'a.py')},
                'plist':k,'plist_hash':'fixture','runner_hash':'fixture','started':1}
             for k,n in (('loop',1),('dashboard',2))}
    context={'runtime':runtime,'old_texts':{k:'old-'+k for k in runtime},
             'new_texts':{k:'new-'+k for k in runtime},'db':str(dbfile),'prod_db':str(dbfile),
             'before':r.ledger(dbfile),'control':str(tmp_path),'new_agent':str(new),
             'new_source':{'a.py':r.sha(new/'a.py')},'protected':{str(protected):r.sha(protected)},
             'expected':'fixture','scanner_label':'fixture','policy':'H'}
    mac=FakeMac(tmp_path,context)
    for k,text in context['old_texts'].items(): mac.runners[k].write_text(text)
    journal=tmp_path/'private/journal.json'; journal.parent.mkdir()
    monkeypatch.setattr(r,'scanner_check',lambda *a:None)
    monkeypatch.setattr(r,'http_check',lambda *a:None)
    monkeypatch.setattr(r,'fresh',lambda *a,**kw:{})
    monkeypatch.setattr(r,'source_manifest',lambda root:{'a.py':r.sha(Path(root)/'a.py')})
    return mac,context,journal


def test_complete_dual_service_release(release):
    mac,c,j=release; r.apply(mac,c,j)
    assert json.loads(j.read_text())['phase']=='SUCCESS'
    assert mac.calls==[('stop','loop'),('stop','dashboard'),('start','dashboard'),('start','loop')]
    assert (j.parent/'db.prestop.sqlite').exists() and (j.parent/'db.sqlite').exists()
    assert all(p.read_text().startswith('new-') for p in mac.runners.values())


@pytest.mark.parametrize('stage',['backup','stop_dashboard','migrate','partial_runner','dashboard_http','heartbeat','interrupt'])
def test_failure_rolls_back_code_preserves_data(release,monkeypatch,stage):
    mac,c,j=release; before=r.ledger(c['db'])
    def fail(*a,**kw): raise RuntimeError('INJECTED')
    if stage=='backup': monkeypatch.setattr(r,'backup',fail)
    elif stage=='stop_dashboard':
        original=mac.stop
        def stop(key):
            if key=='dashboard' and ('stop','dashboard') not in mac.calls:
                mac.calls.append(('stop','dashboard')); raise RuntimeError('INJECTED')
            original(key)
        mac.stop=stop
    elif stage=='migrate': monkeypatch.setattr(r,'migrate',fail)
    elif stage=='partial_runner':
        original=r.atomic; hits=[]
        def atomic(path,data,mode=0o700):
            if path==mac.runners['dashboard'] and data.startswith(b'new') and not hits:
                hits.append(1); raise RuntimeError('INJECTED')
            original(path,data,mode)
        monkeypatch.setattr(r,'atomic',atomic)
    elif stage=='dashboard_http': monkeypatch.setattr(r,'http_check',fail)
    elif stage=='heartbeat': monkeypatch.setattr(r,'fresh',fail)
    else:
        def interrupt(*a): raise KeyboardInterrupt()
        monkeypatch.setattr(r,'migrate',interrupt)
    monkeypatch.setattr(r,'wait_ready',lambda fn,sec:fn())
    with pytest.raises(BaseException): r.apply(mac,c,j)
    r.assert_preserved(before,r.ledger(c['db']),exact=True)
    assert all(p.read_text().startswith('old-') for p in mac.runners.values())
    assert json.loads(j.read_text())['phase']==('ABORTED_NO_MUTATION' if stage=='backup' else 'ROLLED_BACK')
    if stage=='backup': assert not mac.calls


def test_new_record_blocks_old_loop_restart_never_restores_db(release,monkeypatch):
    mac,c,j=release
    def new_record(*a,**kw):
        db=ControlDB(c['db']); db.record(payload('WAIT'),'P','H'); db.close()
        raise RuntimeError('POSTCHECK_FAILURE')
    monkeypatch.setattr(r,'fresh',new_record); monkeypatch.setattr(r,'wait_ready',lambda fn,sec:fn())
    with pytest.raises(RuntimeError): r.apply(mac,c,j)
    assert json.loads(j.read_text())['phase']=='BLOCKED_RECOVERY_REQUIRED'
    assert mac.state()=={} and len(r.ledger(c['db'])['decision_events'])==2
    assert all(p.read_text().startswith('old-') for p in mac.runners.values())


def test_sigkill_journal_and_recovery(release,monkeypatch):
    mac,c,j=release
    def die(*a): os.kill(os.getpid(),signal.SIGKILL)
    monkeypatch.setattr(r,'http_check',die)
    proc=multiprocessing.get_context('fork').Process(target=r.apply,args=(mac,c,j))
    proc.start(); proc.join(15)
    assert proc.exitcode==-signal.SIGKILL and json.loads(j.read_text())['phase']=='SWITCHED'
    monkeypatch.setattr(r,'http_check',lambda *a:None)
    r.rollback(mac,json.loads(j.read_text()),j)
    assert json.loads(j.read_text())['phase']=='ROLLED_BACK'
    r.assert_preserved(c['before'],r.ledger(c['db']),exact=True)


def test_locked_migration_rolls_back(release):
    mac,c,j=release; lock=sqlite3.connect(c['db']); lock.execute('BEGIN IMMEDIATE')
    try:
        with pytest.raises(sqlite3.OperationalError): r.apply(mac,c,j)
    finally: lock.rollback(); lock.close()
    assert json.loads(j.read_text())['phase']=='ROLLED_BACK'


def test_readonly_connection_rejects_writes(dbfile):
    conn=r.ro(dbfile)
    with pytest.raises(sqlite3.OperationalError): conn.execute('DELETE FROM decision_events')
    conn.close()


def test_partial_collection_redacts_errors(tmp_path,monkeypatch):
    mac=SimpleNamespace(home=tmp_path,runners={'loop':tmp_path/'missing'})
    monkeypatch.setattr(r,'prepare',lambda *a:(_ for _ in ()).throw(OSError('private secret')))
    report=r.collect_evidence(mac,tmp_path,'x','x')
    assert report['gate']=='UNVERIFIED_RELEASE_BLOCKED'
    assert str(tmp_path) not in json.dumps(report) and 'secret' not in json.dumps(report)


def test_orphan_worker_prevents_rollback_restart(release):
    mac,c,j=release
    mac.write({})
    mac.worker_pids=lambda context:[999999]
    mac.wait_dead=lambda pids:None
    with pytest.raises(RuntimeError,match='LINGERING_WORKERS'):
        r.rollback(mac,c,j)
    assert not mac.calls


def test_journal_roundtrip_context_types(release):
    mac,c,j=release
    r.save_journal(j,c,'PREPARED')
    loaded=json.loads(j.read_text())
    assert loaded==c
    assert isinstance(loaded['old_texts']['loop'],str)
    assert all(isinstance(k,str) and isinstance(v,str) for k,v in loaded['protected'].items())


def test_default_main_is_read_only_no_lock_or_backup(release,monkeypatch):
    mac,c,j=release
    monkeypatch.setattr(r.sys,'platform','darwin')
    monkeypatch.setattr(r,'Mac',lambda:mac)
    c['reasons']={}
    monkeypatch.setattr(r,'prepare',lambda *a:c)
    before={p:p.read_bytes() for p in j.parent.parent.rglob('*') if p.is_file()}
    assert r.main(['--expected-release-sha','a'*40])==0
    assert before=={p:p.read_bytes() for p in j.parent.parent.rglob('*') if p.is_file()}
    assert not mac.calls


@pytest.mark.parametrize('flags',[[],['--authorize-production-restart'],['--authorize-future-real-notifications']])
def test_apply_needs_both_explicit_authorizations(monkeypatch,flags):
    monkeypatch.setattr(r.sys,'platform','darwin')
    with pytest.raises(RuntimeError,match='EXPLICIT_AUTHORIZATION_REQUIRED'):
        r.main(['--expected-release-sha','a'*40,'--apply']+flags)
