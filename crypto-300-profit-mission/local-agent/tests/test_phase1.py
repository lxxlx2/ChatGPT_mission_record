import copy
import gzip
import hashlib
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from threading import Barrier

import pytest

from mission_agent.clock import FakeClock,parse_utc,stamp
from mission_agent.config import Config
from mission_agent.hashing import canonical,digest,loads,seal,verify
from mission_agent.models import Event,EVENT_TYPES,DELIVERY_STATES
from mission_agent.db.connection import connect,transaction
from mission_agent.db.migrations import migrate
from mission_agent.db.repository import Repository
from mission_agent.queue.batch import build_batch,publish
from mission_agent.queue.reconciliation import reconcile
from mission_agent.decision.fixture_consumer import consume
from mission_agent.transport.local_file import LocalTransport
from mission_agent.delivery.mock_gmail import MockGmail,MODES
from mission_agent.delivery.state_machine import DeliveryEngine
from mission_agent.health.model import snapshot,SOURCE_FIELDS
from mission_agent.health.evaluator import evaluate
from mission_agent.retention import compress_terminal
from mission_agent.synthetic import run


def event(i=0,decision='IGNORE',priority=0,padding=0):
    return Event.synthetic('RAW_PRICE_CANDIDATE','SYNTH','2026-09-30T00:00:00Z',priority,
                           {'fixture_decision':decision,'padding':'x'*padding},str(i))


def decide(repo,config,label='ACTIONABLE_RISK'):
    value=event(decision=label);repo.ingest(value)
    batch=build_batch(repo,config);receipt=consume(batch,repo.clock)
    assert reconcile(repo,receipt)
    return value.event_id,batch,receipt


# U-03/04: vectors independently specified as bytes, not implementation snapshots.
def test_canonical_known_vector():
    value={'z':[True,None,3],'a':'e\u0301'}
    expected=b'{"a":"\xc3\xa9","z":[true,null,3]}'
    assert canonical(value)==expected
    assert digest(value)==hashlib.sha256(expected).hexdigest()
    assert digest({'a':'é','z':[True,None,3]})==digest(value)


@pytest.mark.parametrize('raw',['{"a":1,"a":2}','{"é":1,"e\u0301":2}','{"a":NaN}','{"x":1.1}','{bad'])
def test_canonical_rejects_ambiguous_or_corrupt(raw):
    with pytest.raises(ValueError):loads(raw)


@pytest.mark.parametrize('value',[float('inf'),1.2,{1:'bad'},{'é':1,'e\u0301':2}])
def test_canonical_rejects_non_contract_types(value):
    with pytest.raises(ValueError):canonical(value)


def test_batch_hash_covers_all_metadata():
    original=seal({'schema_version':1,'batch_id':'one','generated_at':'t','valid_until':'u','item_count':0,'items':[]})
    for key in ('batch_id','generated_at','valid_until','item_count','items'):
        value=copy.deepcopy(original);value[key]='altered'
        with pytest.raises(ValueError):verify(value)
    verify(original)


@pytest.mark.parametrize('kind',sorted(EVENT_TYPES))
def test_ids_stable_and_different_canonical_events(kind):
    a=Event.synthetic(kind,'SYNTH','2026-09-30T07:00:00+07:00',0,{'b':2,'a':1},'seed')
    b=Event.synthetic(kind,'SYNTH','2026-09-30T00:00:00Z',0,{'a':1,'b':2},'seed')
    assert a==b
    assert a.event_id!=Event.synthetic(kind,'OTHER','2026-09-30T00:00:00Z',0,{'a':1,'b':2},'seed').event_id


@pytest.mark.parametrize('field,value',[('event_type','BUY'),('priority',True),('priority',2),('payload',[]),('observed_at','2026-09-30')])
def test_invalid_synthetic_input(field,value):
    data={'event_type':'RAW_NFT_CANDIDATE','asset':None,'observed_at':'2026-09-30T00:00:00Z','priority':0,'payload':{}}
    data[field]=value
    with pytest.raises(ValueError):Event.synthetic(**data)


def test_ingest_duplicate_conflict_and_corrupt(repo):
    e=event()
    assert repo.ingest(e)=='CREATED'
    assert [repo.ingest(e) for _ in range(3)]==['DUPLICATE']*3
    assert repo.ingest(replace(e,payload={'different':True}))=='QUARANTINED'
    assert repo.ingest_json('{corrupt')=='QUARANTINED'
    assert repo.counts()['candidates']==repo.counts()['outbox']==repo.counts()['deliveries']==1
    assert repo.counts()['quarantine']==2


@pytest.mark.parametrize('where',['candidate','outbox'])
def test_transaction_failure_no_partial_state(repo,where):
    with pytest.raises(RuntimeError):repo.ingest(event(),fail_at=where)
    assert repo.counts()['candidates']==repo.counts()['outbox']==repo.counts()['deliveries']==0


def test_migration_wal_reopen_and_backup(repo,tmp_path,clock):
    repo.ingest(event())
    assert repo.db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
    assert repo.db.execute('PRAGMA synchronous').fetchone()[0]==2
    assert repo.db.execute('SELECT version FROM schema_migrations').fetchone()[0]==1
    repo.backup(tmp_path/'backup.sqlite')
    other=Repository(tmp_path/'backup.sqlite',clock)
    try:assert other.counts()==repo.counts()
    finally:other.close()
    second=Repository(repo.path,clock)
    try:
        assert second.counts()==repo.counts()
        assert second.db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0]==1
    finally:second.close()


@pytest.mark.parametrize('point',[0,3,9])
def test_migration_failure_is_atomic(tmp_path,clock,point):
    db=connect(tmp_path/'broken.sqlite')
    try:
        with pytest.raises(RuntimeError):migrate(db,stamp(clock.now()),fail_after=point)
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()==[]
        migrate(db,stamp(clock.now()))
        assert db.execute('SELECT version FROM schema_migrations').fetchone()[0]==1
    finally:db.close()


@pytest.mark.parametrize('mutation',["UPDATE schema_migrations SET version=2","UPDATE schema_migrations SET checksum='tamper'"])
def test_newer_or_tampered_migration_rejected(repo,clock,mutation):
    repo.db.execute(mutation)
    with pytest.raises(ValueError):Repository(repo.path,clock)


def test_batch_limits_and_backlog_no_drop(repo,config):
    ids=set()
    for i in range(140):
        e=event(i,priority=int(i<30),padding=1400);ids.add(e.event_id);repo.ingest(e)
    first=build_batch(repo,config)
    assert sum(i['priority']==1 for i in first['items'])==8
    assert sum(i['priority']==0 for i in first['items'])==40
    assert all(i['priority']==1 for i in first['items'][:8])
    assert repo.db.execute("SELECT COUNT(*) FROM outbox WHERE state='PENDING'").fetchone()[0]==92
    batches=[first]
    while (b:=build_batch(repo,config)):batches.append(b)
    emitted=[i['event_id'] for b in batches for i in b['items']]
    assert set(emitted)==ids and len(emitted)==len(ids)
    assert all(len(canonical(b))<=100000 for b in batches)
    assert all(sum(i['priority']==0 for i in b['items'])<=40 for b in batches)
    assert all(sum(i['priority']==1 for i in b['items'])<=8 for b in batches)


def test_byte_limit_boundary_and_oversize_accounting(repo,config):
    repo.ingest(event(0));repo.ingest(event(1));repo.ingest(event(2,padding=3000))
    config=replace(config,max_batch_bytes=1100)
    one=build_batch(repo,config)
    assert len(canonical(one))<=1100
    assert repo.counts()['candidates']==3
    assert repo.db.execute("SELECT COUNT(*) FROM outbox WHERE state='QUARANTINED'").fetchone()[0]==1
    assert repo.counts()['quarantine']==1
    assert repo.db.execute("SELECT COUNT(*) FROM outbox WHERE state='PENDING'").fetchone()[0]>=1


def test_local_transport_immutable_roles_and_retry(repo,config,tmp_path):
    repo.ingest(event());batch=build_batch(repo,config);t=LocalTransport(tmp_path/'files')
    publish(repo,t,batch['batch_id']);original=(t.root/'mac-data/ingest/current-batch.json').read_bytes()
    publish(repo,t,batch['batch_id']);assert original==(t.root/'mac-data/ingest/current-batch.json').read_bytes()
    assert t.read_batch(batch['batch_id'])==batch
    receipt=consume(batch,repo.clock);t.publish_receipt(receipt)
    assert t.read_receipt(batch['batch_id'])==receipt
    assert not (t.root/'mac-data/decisions').exists()
    changed=copy.deepcopy(receipt);changed['decision_count']=0
    with pytest.raises(ValueError):t.publish_receipt(changed)


def test_publish_failure_preserves_outbox_and_retries(repo,config,tmp_path):
    repo.ingest(event());batch=build_batch(repo,config)
    class Broken:
        def publish_batch(self,batch):raise OSError('synthetic disk failure')
    with pytest.raises(OSError):publish(repo,Broken(),batch['batch_id'])
    row=repo.db.execute('SELECT * FROM outbox').fetchone()
    assert row['state']=='BATCHED' and row['attempt_count']==1
    publish(repo,LocalTransport(tmp_path/'files'),batch['batch_id'])
    assert repo.db.execute('SELECT state FROM outbox').fetchone()[0]=='PUBLISHED'


@pytest.mark.parametrize('mutation',['hash','unknown_batch','unknown_event','missing','extra','duplicate','count','decision_count','item_hash','bad_decision','bad_schema','bool_schema','future_time','old_time'])
def test_receipt_rejects_whole_batch(repo,config,mutation):
    for i in range(3):repo.ingest(event(i))
    batch=build_batch(repo,config);r=consume(batch,repo.clock)
    if mutation=='hash':r['input_payload_sha256']='x'*64
    elif mutation=='unknown_batch':r['input_batch_id']='not-found'
    elif mutation=='unknown_event':r['decisions'][0]['event_id']='unknown'
    elif mutation=='missing':r['decisions'].pop()
    elif mutation=='extra':r['decisions'].append({**r['decisions'][0],'event_id':'extra'})
    elif mutation=='duplicate':r['decisions'][1]=r['decisions'][0]
    elif mutation=='count':r['consumed_item_count']=False
    elif mutation=='decision_count':r['decision_count']=1
    elif mutation=='item_hash':r['decisions'][-1]['item_payload_sha256']='0'*64
    elif mutation=='bad_decision':r['decisions'][-1]['decision']='BUY'
    elif mutation=='bad_schema':r['schema_version']=2
    elif mutation=='bool_schema':r['schema_version']=True
    elif mutation=='future_time':r['decision_timestamp']='2030-01-01T00:00:00Z'
    elif mutation=='old_time':r['decision_timestamp']='2020-01-01T00:00:00Z'
    assert reconcile(repo,r) is False
    assert repo.counts()['decisions']==0
    assert repo.db.execute("SELECT COUNT(*) FROM candidates WHERE status='PENDING_DECISION'").fetchone()[0]==3
    assert repo.db.execute("SELECT COUNT(*) FROM outbox WHERE state='CONSUMED'").fetchone()[0]==0


def test_receipt_transaction_replay_and_failure(repo,config):
    for i in range(3):repo.ingest(event(i))
    b=build_batch(repo,config);r=consume(b,repo.clock)
    with pytest.raises(RuntimeError):reconcile(repo,r,fail_after=1)
    assert repo.counts()['decisions']==0
    assert reconcile(repo,r) and reconcile(repo,r)
    assert repo.counts()['decisions']==3


def test_stale_batch_requeue_no_loss(repo,config,clock):
    for i in range(50):repo.ingest(event(i))
    b=build_batch(repo,config);clock.advance(config.batch_ttl_seconds+1)
    with pytest.raises(ValueError):consume(b,clock)
    repo.expire_batch(b['batch_id'])
    assert repo.db.execute("SELECT COUNT(*) FROM outbox WHERE state='PENDING'").fetchone()[0]==50
    next_batch=build_batch(repo,config)
    assert next_batch['batch_id']!=b['batch_id']
    assert reconcile(repo,consume(next_batch,clock))


@pytest.mark.parametrize('label,state',[('IGNORE','DECIDED_IGNORE'),('WATCH','DECIDED_WATCH'),('ACTIONABLE_RISK','DELIVERY_PENDING'),('ACTIONABLE_OPPORTUNITY','DELIVERY_PENDING')])
def test_decision_states_no_ignore_watch_send(repo,config,tmp_path,label,state):
    id,_,_=decide(repo,config,label)
    provider=MockGmail(tmp_path/'mock.sqlite',repo.clock)
    try:
        engine=DeliveryEngine(repo,provider,config)
        assert engine.state(id)['state']==state
        actual=engine.run(id)
        assert actual==('DELIVERED' if state=='DELIVERY_PENDING' else state)
        assert provider.count(id)==int(state=='DELIVERY_PENDING')
    finally:provider.close()


@pytest.mark.parametrize('mode',sorted(MODES))
def test_mock_failure_modes_and_cooldown(repo,config,tmp_path,clock,mode):
    id,_,_=decide(repo,config)
    provider=MockGmail(tmp_path/'mock.sqlite',clock);engine=DeliveryEngine(repo,provider,config)
    try:
        first=engine.run(id,mode)
        expected='DELIVERED' if mode=='SUCCESS' else 'FAILED_MANUAL_REVIEW' if mode=='DUPLICATE_SENT_RESULT' else 'DELIVERY_UNCERTAIN'
        assert first==expected
        for _ in range(3):engine.run(id)
        assert provider.calls(id)==1
        clock.advance(180)
        second=engine.run(id)
        assert second==('DELIVERY_UNCERTAIN' if mode=='TIMEOUT_BEFORE_SEND' else 'FAILED_MANUAL_REVIEW' if mode=='DUPLICATE_SENT_RESULT' else 'DELIVERED')
        assert provider.calls(id)==1
        assert provider.count(id)==(0 if mode=='TIMEOUT_BEFORE_SEND' else 2 if mode=='DUPLICATE_SENT_RESULT' else 1)
        if second=='DELIVERED':assert engine.state(id)['provider_message_id'] is not None
    finally:provider.close()


def test_sent_search_delay_and_independent_store_reopen(repo,config,tmp_path,clock):
    id,_,_=decide(repo,config);path=tmp_path/'mock.sqlite'
    provider=MockGmail(path,clock);engine=DeliveryEngine(repo,provider,config)
    assert engine.run(id,search_delay=180)=='DELIVERY_UNCERTAIN'
    assert provider.search_sent(id)==[] and provider.count(id)==1
    provider.close();provider=MockGmail(path,clock);engine=DeliveryEngine(repo,provider,config)
    try:
        clock.advance(61);assert engine.run(id)=='DELIVERY_UNCERTAIN'
        clock.advance(120);assert engine.run(id)=='DELIVERED'
        assert provider.calls(id)==1
    finally:provider.close()


@pytest.mark.parametrize('at',['before_send','after_send'])
def test_cold_restart_sending_intent_uncertain(repo,config,tmp_path,clock,at):
    id,_,_=decide(repo,config);provider=MockGmail(tmp_path/'mock.sqlite',clock)
    try:
        engine=DeliveryEngine(repo,provider,config)
        with pytest.raises(SystemExit):engine.run(id,crash_at=at)
        assert engine.state(id)['state']=='DELIVERY_SENDING'
        other=Repository(repo.path,clock)
        try:
            restarted=DeliveryEngine(other,provider,config)
            clock.advance(121);assert restarted.run(id)=='DELIVERY_UNCERTAIN'
            clock.advance(61)
            assert restarted.run(id)==('DELIVERED' if at=='after_send' else 'DELIVERY_UNCERTAIN')
            assert provider.calls(id)==int(at=='after_send')
        finally:other.close()
    finally:provider.close()


def test_two_concurrent_consumers_single_send(repo,config,tmp_path,clock):
    id,_,_=decide(repo,config);barrier=Barrier(2)
    provider=MockGmail(tmp_path/'mock.sqlite',clock);provider.close()
    def worker():
        r=Repository(repo.path,clock);p=MockGmail(tmp_path/'mock.sqlite',clock)
        try:barrier.wait();return DeliveryEngine(r,p,config).run(id)
        finally:p.close();r.close()
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:worker(),range(2)))
    provider=MockGmail(tmp_path/'mock.sqlite',clock)
    try:
        assert provider.count(id)==provider.calls(id)==1
        assert tuple(repo.db.execute('SELECT state,fence FROM deliveries WHERE event_id=?',(id,)).fetchone())==('DELIVERED',1)
    finally:provider.close()


def test_three_replays_delivered_event_no_resend(repo,config,tmp_path):
    id,b,r=decide(repo,config);provider=MockGmail(tmp_path/'mock.sqlite',repo.clock)
    try:
        engine=DeliveryEngine(repo,provider,config)
        assert engine.run(id)=='DELIVERED'
        for _ in range(3):assert reconcile(repo,r);assert engine.run(id)=='DELIVERED'
        assert provider.count(id)==provider.calls(id)==1
    finally:provider.close()


@pytest.mark.parametrize('policy',['at_least_once','at_most_once'])
def test_policies_do_not_blind_resend(repo,config,tmp_path,clock,policy):
    id,_,_=decide(repo,config);repo.db.execute('UPDATE deliveries SET policy=?',(policy,))
    provider=MockGmail(tmp_path/'mock.sqlite',clock)
    try:
        engine=DeliveryEngine(repo,provider,replace(config,delivery_policy=policy))
        engine.run(id,'TIMEOUT_AFTER_SEND');clock.advance(120)
        assert engine.run(id)=='DELIVERED' and provider.calls(id)==1
    finally:provider.close()


def test_health_unknown_real_fields_and_persistent_seq(repo,config,clock):
    a=snapshot(repo,config);b=snapshot(repo,config)
    assert b['seq']==a['seq']+1
    assert b['overall']=='UNKNOWN'
    assert all(b[k]=='UNKNOWN' for k in SOURCE_FIELDS)
    assert b['sleep_gap_detected']=='UNKNOWN' and b['restart_count_24h']=='UNKNOWN'
    assert b['sqlite_writable'] is True and b['disk_free_bytes']>0
    r=Repository(repo.path,clock)
    try:assert snapshot(r,config)['seq']==b['seq']+1
    finally:r.close()


def test_stale_healthy_external_override(repo,config,clock):
    s=snapshot(repo,config);s['overall']='HEALTHY'
    for key in SOURCE_FIELDS:s[key]=0
    clock.advance(1201)
    assert evaluate(s,clock.now(),config.disk_budget_bytes)=={'overall':'UNHEALTHY','reason':'UNHEALTHY_STALE_HOST'}


@pytest.mark.parametrize('used,status',[(4_000_000_000,'UNKNOWN'),(4_000_000_001,'DEGRADED'),(4_750_000_000,'DEGRADED'),(4_750_000_001,'UNHEALTHY')])
def test_disk_budget_boundaries(repo,config,used,status):
    s=snapshot(repo,config);s['storage_used_bytes']=used
    assert evaluate(s,repo.clock.now(),config.disk_budget_bytes)['overall']==status


def test_monotonic_independent_of_wall_jump(clock):
    clock.advance(5);elapsed=clock.monotonic();clock.value-=timedelta(hours=1)
    assert clock.monotonic()==elapsed
    with pytest.raises(ValueError):parse_utc('2026-09-30T00:00:00')


def test_real_process_crash_uncommitted_and_committed_survive(repo,clock):
    e=event();repo.ingest(e)
    script="""from mission_agent.db.repository import Repository
from mission_agent.models import Event
import os,sys
r=Repository(sys.argv[1]);r.db.execute('BEGIN IMMEDIATE')
r.db.execute("UPDATE candidates SET status='LOST'")
os._exit(53)
"""
    result=subprocess.run([sys.executable,'-c',script,str(repo.path)],timeout=20)
    assert result.returncode==53
    reopened=Repository(repo.path,clock)
    try:
        assert reopened.counts()['candidates']==1
        assert reopened.db.execute('SELECT status FROM candidates').fetchone()[0]=='PENDING_DECISION'
        assert reopened.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    finally:reopened.close()


def test_retention_compresses_only_acknowledged_and_readback(repo,config,tmp_path,clock):
    e=event();repo.ingest(e);b=build_batch(repo,config);t=LocalTransport(tmp_path/'files')
    publish(repo,t,b['batch_id'])
    assert compress_terminal(repo,t,0)==[]
    r=consume(b,clock);t.publish_receipt(r);assert reconcile(repo,r)
    paths=compress_terminal(repo,t,0)
    assert len(paths)==2
    for rel in paths:assert loads(gzip.decompress((t.root/(rel+'.gz')).read_bytes()))
    assert repo.counts()['candidates']==repo.counts()['decisions']==1
    assert t.read_batch(b['batch_id'])==b
    assert t.read_receipt(b['batch_id'])==r


def test_synthetic_e2e_metrics(tmp_path):
    result=run(Config(tmp_path),60,1729)
    assert result['gate_pass'] is True
    assert result['synthetic_events_created']==result['fixture_decisions']==60
    assert result['input_candidate_bytes']>100000
    assert result['mock_sent_count']==result['mock_delivered']==30
    assert result['max_batch_bytes']<=100000
    assert result['normal_max_per_batch']<=40 and result['urgent_max_per_batch']<=8
    assert result['health_overall']=='UNKNOWN'
    for key in ('silent_event_loss','duplicate_candidate','accepted_receipt_mismatch','unknown_receipt_accepted','hash_mismatch_accepted',
                'restart_event_loss','over_100kb_batch_emitted','unprocessed_backlog_silently_removed','uncertain_blind_resend','stale_batch_accepted'):
        assert result[key]==0


def test_cli_synthetic_and_cycle(tmp_path):
    base=[sys.executable,'-m','mission_agent.cli','--runtime-root',str(tmp_path)]
    result=subprocess.run(base+['synthetic-event','--event-type','TEST_ACTION_CANDIDATE','--observed-time','2026-09-30T00:00:00Z',
                                '--payload','{"fixture_decision":"ACTIONABLE_OPPORTUNITY"}','--seed','abc'],capture_output=True,text=True,timeout=20)
    assert result.returncode==0 and loads(result.stdout)['result']=='CREATED'
    duplicate=subprocess.run(base+['synthetic-event','--event-type','TEST_ACTION_CANDIDATE','--observed-time','2026-09-30T00:00:00Z',
                                   '--payload','{"fixture_decision":"ACTIONABLE_OPPORTUNITY"}','--seed','abc'],capture_output=True,text=True,timeout=20)
    assert loads(duplicate.stdout)['result']=='DUPLICATE'
    cycle=subprocess.run(base+['cycle'],capture_output=True,text=True,timeout=20)
    assert cycle.returncode==0,cycle.stderr
    assert loads(cycle.stdout)['decisions']==1


def test_config_no_real_adapters(config):
    assert config.real_send_enabled is False and config.transport_mode=='LOCAL_FILE'
    assert config.runtime_repo=='lxxlx2/crypto-monitor-runtime' and config.disk_budget_bytes==5_000_000_000
    with pytest.raises(ValueError):replace(config,max_batch_bytes=100001)


def test_receipt_file_recovered_after_client_crash(tmp_path,config):
    # Persist fixture receipt, leave local batch unconsumed, then execute the real CLI recovery.
    r=Repository(tmp_path/'mission.sqlite')
    try:
        r.ingest(event());b=build_batch(r,config);t=LocalTransport(tmp_path/'runtime-local')
        publish(r,t,b['batch_id']);receipt=consume(b,r.clock);t.publish_receipt(receipt)
        first=(t.root/'gpt-data/decisions/current.json').read_bytes()
    finally:r.close()
    result=subprocess.run([sys.executable,'-m','mission_agent.cli','--runtime-root',str(tmp_path),'cycle'],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert loads(result.stdout)['decisions']==1
    assert (t.root/'gpt-data/decisions/current.json').read_bytes()==first


def test_corrupt_payload_and_transport_over_100kb_rejected(repo,config,tmp_path):
    repo.ingest(event());b=build_batch(repo,config)
    changed={k:v for k,v in b.items() if k!='payload_sha256'}
    changed['items'][0]['payload']['padding']='tampered'
    changed=seal(changed)
    with pytest.raises(ValueError):consume(changed,repo.clock)
    large=seal({'schema_version':1,'batch_id':'oversize','generated_at':stamp(repo.clock.now()),
                'valid_until':stamp(repo.clock.now()+timedelta(hours=1)),'item_count':1,'items':[{'data':'x'*100000}]})
    assert len(canonical(large))>100000
    t=LocalTransport(tmp_path/'files')
    with pytest.raises(ValueError):t.publish_batch(large)
    assert not (t.root/'mac-data/ingest/current-batch.json').exists()


def test_unknown_receipt_cannot_partially_consume_known_events(repo,config):
    for i in range(3):repo.ingest(event(i))
    b=build_batch(repo,config);receipt=consume(b,repo.clock)
    receipt['decisions'][-1]['event_id']='unknown-at-end'
    assert reconcile(repo,receipt) is False
    assert repo.counts()['decisions']==0
    assert repo.db.execute("SELECT COUNT(*) FROM deliveries WHERE state='PENDING_DECISION'").fetchone()[0]==3


def test_receipt_positive_received_late_after_ttl(repo,config,clock):
    repo.ingest(event());b=build_batch(repo,config);r=consume(b,clock)
    clock.advance(config.batch_ttl_seconds+1)
    # Decision was made while valid; late reconciliation is safe if no expiry/requeue occurred.
    assert reconcile(repo,r)


def test_unprocessed_backlog_survives_reopen(repo,config,clock):
    expected=set()
    for i in range(100):
        e=event(i,priority=int(i<20));expected.add(e.event_id);repo.ingest(e)
    b=build_batch(repo,config);assert reconcile(repo,consume(b,clock))
    second=Repository(repo.path,clock)
    try:
        pending={r[0] for r in second.db.execute("SELECT event_id FROM outbox WHERE state='PENDING'")}
        done={r[0] for r in second.db.execute('SELECT event_id FROM decisions')}
        assert expected==pending|done and not pending&done
        assert len(pending)==52
    finally:second.close()


def test_clock_schema_and_entire_delivery_state_set(repo,config):
    assert DELIVERY_STATES=={'PENDING_DECISION','DECIDED_IGNORE','DECIDED_WATCH','DELIVERY_PENDING','DELIVERY_SENDING',
                            'DELIVERY_UNCERTAIN','DELIVERED','FAILED_MANUAL_REVIEW'}
    assert repo.db.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
    required={'schema_migrations','meta','candidates','outbox','batches','decisions','deliveries','health'}
    names={r[0] for r in repo.db.execute('SELECT name FROM sqlite_master WHERE type="table"')}
    assert required<=names


def test_budget_guard_preserves_accepted_work(repo,config,tmp_path):
    from mission_agent.storage import DiskBudgetExceeded
    e=event();repo.ingest(e)
    tiny=replace(config,disk_budget_bytes=1)
    with pytest.raises(DiskBudgetExceeded):build_batch(repo,tiny)
    repo.disk_budget_bytes=1
    with pytest.raises(DiskBudgetExceeded):repo.ingest(event(1))
    assert repo.counts()['candidates']==1
    assert repo.db.execute('SELECT state FROM outbox').fetchone()[0]=='PENDING'


def test_compressed_receipt_remains_immutable(repo,config,tmp_path):
    id,b,r=decide(repo,config,'IGNORE');t=LocalTransport(tmp_path/'files')
    t.publish_batch(b);t.publish_receipt(r);compress_terminal(repo,t,0)
    changed=copy.deepcopy(r);changed['decision_count']=0
    with pytest.raises(ValueError):t.publish_receipt(changed)
    assert t.read_receipt(b['batch_id'])==r


def test_duplicate_at_disk_limit_does_not_need_new_admission(repo):
    e=event();repo.ingest(e);repo.disk_budget_bytes=1
    assert repo.ingest(e)=='DUPLICATE'


def test_health_retention_preserves_monotonic_sequence(repo,config):
    repo.db.execute("UPDATE meta SET value='1001' WHERE key='health_seq'")
    repo.db.execute("INSERT INTO health VALUES(1,'old','old','UNKNOWN','{}')")
    current=snapshot(repo,config)
    assert current['seq']==1002
    assert repo.db.execute('SELECT COUNT(*) FROM health WHERE seq=1').fetchone()[0]==0
    assert repo.db.execute('SELECT MAX(seq) FROM health').fetchone()[0]==1002
