import pytest
from mission_agent.signals.gmail_health import health_from_summary
from mission_agent.signals.gmail import GmailOutbox
from mission_agent.signals.store import Ledger
from test_frank_v1 import fixture_multiple,signals

BASE=dict(pending=0,sent_verified=0,sent_unverified=0,blocked=0,failed=0,historical_forbidden=0)

@pytest.mark.parametrize('counts,status',[
    ({},'LIVE'),({'sent_verified':3},'LIVE'),({'pending':1},'PENDING'),
    ({'blocked':1,'pending':1},'BLOCKED'),
    ({'sent_unverified':1,'blocked':1,'pending':1},'SENT_UNVERIFIED'),
    ({'failed':1,'sent_unverified':1,'blocked':1,'pending':1},'FAILED'),
])
def test_local_health_priority_and_counts(counts,status):
    summary={**BASE,**counts};h=health_from_summary(summary)
    assert h['email_delivery_status']==status
    for key in ('pending','sent_verified','sent_unverified','blocked','failed'):assert h['gmail_'+key]==summary[key]

def test_pending_counts_all_inflight_retry_states_and_excludes_history(tmp_path):
    l=Ledger(tmp_path/'db');o=GmailOutbox(l)
    for i,status in enumerate(['PENDING','SENDING','RETRYABLE_ERROR','SENT_UNVERIFIED','SENT_VERIFIED','CREDENTIAL_BLOCKED','PERMANENT_ERROR']):
        sid='fixture-'+str(i);o.enqueue(dict(signal_id=sid,subject='fixture',body='fixture'),mode='LIVE');o.update(sid,status)
    o.enqueue(dict(signal_id='history',subject='fixture',body='fixture'),mode='DRY_RUN_AUDIT')
    before=[tuple(r) for r in l.db.execute('select * from gmail_delivery')]
    summary=o.summary();h=health_from_summary(summary)
    assert h==dict(email_delivery_status='FAILED',gmail_pending=3,gmail_sent_verified=1,gmail_sent_unverified=1,gmail_blocked=1,gmail_failed=1)
    assert [tuple(r) for r in l.db.execute('select * from gmail_delivery')]==before

def test_missing_frozen_live_content_reports_failed_without_network(tmp_path,monkeypatch):
    import socket
    monkeypatch.setattr(socket,'socket',lambda *a,**k:pytest.fail('telemetry performed network'))
    l,e=fixture_multiple(tmp_path,False);l.db.execute('delete from email_content');o=GmailOutbox(l);o.sync()
    assert health_from_summary(o.summary())['email_delivery_status']=='FAILED'
    assert o.summary()['failed']==1

def test_missing_historical_content_is_not_live_failure(tmp_path):
    l,e=fixture_multiple(tmp_path);l.db.execute('delete from email_content');o=GmailOutbox(l);o.sync()
    assert o.summary()['failed']==0
    assert l.db.execute("select status from outbox where channel='gmail'").fetchone()[0]=='DRY_RUN_AUDIT'

def test_telemetry_does_not_create_delivery_schema_when_absent(tmp_path):
    from mission_agent.signals.gmail import summary_from_db
    ledger=Ledger(tmp_path/'db');before=[tuple(r) for r in ledger.db.execute('select * from sqlite_master')]
    assert health_from_summary(summary_from_db(ledger.db))['email_delivery_status']=='LIVE'
    assert [tuple(r) for r in ledger.db.execute('select * from sqlite_master')]==before
