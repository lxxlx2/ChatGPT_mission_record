import base64,json,sqlite3,threading,time
from pathlib import Path
import pytest
from mission_agent.signals.gmail import GmailOutbox,TEST_SUBJECT,CredentialBlocked,RetryableError,AmbiguousSend,PermanentError
from mission_agent.signals.email import content
from test_frank_v1 import fixture_multiple,signals,buy

class Provider:
    recipient='owner@example.invalid'
    def __init__(self):self.messages={};self.sent=[];self.actions=[];self.read_failures=0;self.crash=False;self.ready_blocked=False
    def ready(self):
        self.actions.append('ready')
        if self.ready_blocked:raise CredentialBlocked()
    def find_sent(self,wire_id,sid):self.actions.append('find');return list(self.messages)
    def get(self,mid):
        self.actions.append('get')
        if self.read_failures:self.read_failures-=1;raise RetryableError()
        return self.messages[mid]
    def send(self,raw):
        self.actions.append('send');self.sent.append(raw);mid='gmail-'+str(len(self.sent));self.messages[mid]={'id':mid,'threadId':'thread-'+mid,'labelIds':['SENT'],'raw':base64.urlsafe_b64encode(raw).decode(),'internalDate':'1791049000000'}
        if self.crash:raise SystemExit('post-acceptance crash before local receipt')
        return {'id':mid,'threadId':'thread-'+mid}

def setup(tmp_path,dry=False):
    l,e=fixture_multiple(tmp_path,dry);o=GmailOutbox(l);o.sync();sid=signals(l)[-1]['signal_id'];return l,e,o,sid

def test_multiple_creates_exactly_one_email_outbox(tmp_path):
    l,e,o,sid=setup(tmp_path);o.sync();assert l.db.execute('select count(*) from gmail_delivery').fetchone()[0]==1
    assert l.db.execute("select count(*) from outbox where channel='gmail'").fetchone()[0]==1

def test_accumulation_never_creates_email(tmp_path):
    l,e,o,sid=setup(tmp_path);acc=signals(l)[0]['signal_id'];assert not l.db.execute('select 1 from gmail_delivery where signal_id=?',(acc,)).fetchone()

def test_email_outbox_unique_by_signal_id(tmp_path):
    l,e,o,sid=setup(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):l.db.execute('insert into gmail_delivery select * from gmail_delivery')

def test_gmail_send_records_message_id_and_sent_readback_verifies_signal_id(tmp_path):
    l,e,o,sid=setup(tmp_path);p=Provider();o.drain(p);r=o.row(sid);assert r['status']=='SENT_VERIFIED' and r['gmail_message_id']=='gmail-1' and r['gmail_thread_id']=='thread-gmail-1' and r['readback_verified']==1
    assert json.loads(r['receipt'])['signal_id']==sid;assert p.actions==['ready','find','send','get'];o.drain(p);assert len(p.sent)==1

def test_gmail_send_success_local_crash_does_not_duplicate(tmp_path):
    l,e,o,sid=setup(tmp_path);p=Provider();p.crash=True
    with pytest.raises(SystemExit):o.drain(p)
    assert o.row(sid)['status']=='SENDING' and o.row(sid)['gmail_message_id'] is None;l.db.close()
    from mission_agent.signals.store import Ledger
    l=Ledger(tmp_path/'db');o=GmailOutbox(l);p.crash=False;o.drain(p);assert len(p.sent)==1 and o.row(sid)['status']=='SENT_VERIFIED'

def test_sent_unverified_retries_readback_before_resend(tmp_path):
    l,e,o,sid=setup(tmp_path);p=Provider();p.read_failures=1;o.drain(p);assert o.row(sid)['status']=='SENT_UNVERIFIED';p.actions=[];o.drain(p);assert p.actions==['ready','get'] and len(p.sent)==1 and o.row(sid)['status']=='SENT_VERIFIED'

def test_delayed_sent_index_after_crash_never_blindly_resends(tmp_path):
    l,e,o,sid=setup(tmp_path);p=Provider();p.crash=True
    with pytest.raises(SystemExit):o.drain(p)
    saved=p.messages;p.messages={};p.crash=False;o.drain(p);assert len(p.sent)==1 and o.row(sid)['status']=='SENT_UNVERIFIED';p.messages=saved;o.drain(p);assert len(p.sent)==1 and o.row(sid)['status']=='SENT_VERIFIED'

def test_credential_blocked_keeps_outbox(tmp_path):
    l,e,o,sid=setup(tmp_path);o.drain();assert o.row(sid)['status']=='CREDENTIAL_BLOCKED' and o.row(sid)['attempt_count']==0
    assert l.db.execute("select status from outbox where channel='gmail'").fetchone()[0]=='CREDENTIAL_BLOCKED'

def test_credential_recovery_processes_pending_live_only(tmp_path):
    l,e,o,sid=setup(tmp_path);o.drain();p=Provider();o.drain(p);assert len(p.sent)==1
    other=tmp_path/'history';hl,he,ho,hsid=setup(other,True);ho.drain(p);assert len(p.sent)==1 and ho.row(hsid)['delivery_forbidden']==1

@pytest.mark.parametrize('mode',['DRY_RUN_AUDIT','HISTORICAL_REPLAY','UNSPECIFIED'])
def test_historical_and_dry_run_signal_never_email(tmp_path,mode):
    l,e,o,sid=setup(tmp_path,True);r=o.row(sid);p=Provider();o.drain(p);assert p.sent==[] and r['delivery_forbidden']==1
    mail={'signal_id':'history-'+mode,'subject':'historical','body':'never deliver'};o.enqueue(mail,mode=mode);o.drain(p);assert p.sent==[] and o.row(mail['signal_id'])['delivery_forbidden']==1

def test_test_email_cannot_be_confused_with_live_signal(tmp_path):
    l,e,o,sid=setup(tmp_path,True);mail={'signal_id':'test-frank-delivery-once','subject':TEST_SUBJECT,'body':'THIS IS A DELIVERY TEST\nNOT A LIVE INVESTMENT SIGNAL'};o.enqueue(mail,mode='TEST');p=Provider();o.drain(p);assert not p.sent;o.drain(p,allow_test=True);o.drain(p,allow_test=True);assert len(p.sent)==1 and o.row(mail['signal_id'])['status']=='SENT_VERIFIED'
    with pytest.raises(ValueError,match='TEST_CANNOT_BE_LIVE'):o.enqueue(mail,mode='LIVE')

def test_email_template_has_all_required_fields_and_raw_quote(tmp_path):
    l,e,o,sid=setup(tmp_path);s=signals(l)[-1];m=content(s)
    for x in ('Signal ID:','触发时间:','Token:','CA / Mint:','Stage:','Episode ID:','首次主动买入时间:','最新主动买入时间:','当前 buy_count:','当前 sell_count:','本次 BUY:','累计 BUY:','当前观察库存:','触发规则:','最新触发交易:'):assert x in m['body']
    assert m['subject'].endswith('1970-01-02 11:31');s['quote_asset']='SOL';s['latest_quote_amount']='7.123';assert '7.123 SOL' in content(s)['body']

def test_wrong_sent_subject_or_marker_or_content_cannot_verify(tmp_path):
    l,e,o,sid=setup(tmp_path);p=Provider();o.drain(p);r=o.row(sid);message=dict(p.messages['gmail-1']);raw=base64.urlsafe_b64decode(message['raw']).replace(b'X-Frank-Signal-ID:',b'X-Wrong-Signal-ID:');message['raw']=base64.urlsafe_b64encode(raw).decode()
    with pytest.raises(PermanentError):o.verify(r,message)

def test_gmail_failure_does_not_prevent_local_notification_or_next_scanner_cycle(tmp_path):
    from mission_agent.signals.delivery import drain
    l,e,o,sid=setup(tmp_path);seen=[];drain(l,lambda s:(seen.append(s['signal_id']) or {'status':'COMMAND_ACCEPTED'}));assert len(seen)==2
    p=Provider();p.ready_blocked=True;o.drain(p);buy(l,e,'new',105500,13000);assert l.db.execute('select 1 from v1_seen where signature=\'new\'').fetchone();assert o.row(sid)['status']=='CREDENTIAL_BLOCKED'

def test_gmail_network_worker_does_not_block_scanner_thread(tmp_path,monkeypatch):
    from mission_agent.signals.gmail import kick,_worker_lock
    from mission_agent.signals import gmail_api
    l,e,o,sid=setup(tmp_path);entered=threading.Event();release=threading.Event();p=Provider()
    def blocked_ready():entered.set();release.wait(3)
    p.ready=blocked_ready;monkeypatch.setattr(gmail_api,'existing_provider',lambda *args:p)
    started=time.monotonic();kick(l);assert time.monotonic()-started<.5;assert entered.wait(1)
    buy(l,e,'while-mail-blocked',105500,13000);assert l.db.execute("select 1 from v1_seen where signature='while-mail-blocked'").fetchone();release.set()
    for _ in range(100):
        if not _worker_lock.locked():break
        time.sleep(.01)
    assert not _worker_lock.locked()

def test_gpt_consumer_not_required_for_local_signal(tmp_path,monkeypatch):
    from mission_agent.signals.delivery import drain
    l,e,o,sid=setup(tmp_path);monkeypatch.setattr('urllib.request.urlopen',lambda *a,**k:pytest.fail('unexpected network in blocked delivery'));drain(l,lambda s:{'status':'COMMAND_ACCEPTED'});assert len(signals(l))==2

def test_delivery_never_changes_frozen_model_or_signal_identity(tmp_path):
    l,e,o,sid=setup(tmp_path);before=[tuple(r) for r in l.db.execute('select * from signals')];o.drain(Provider());assert before==[tuple(r) for r in l.db.execute('select * from signals')]


def test_legacy_manifest_cannot_become_frank_authority(tmp_path,monkeypatch):
    from mission_agent.meme.transport import MemeTransport
    monkeypatch.setattr(MemeTransport,'read',lambda *args:pytest.fail('legacy manifest consumed'))
    l,e,o,sid=setup(tmp_path);o.drain(Provider());assert o.row(sid)['status']=='SENT_VERIFIED'

def test_legacy_non_v1_signal_cannot_enter_new_gmail_authority(tmp_path):
    from mission_agent.signals.store import Ledger
    from test_frank_local_signals import put,active,MULTIPLE
    l=Ledger(tmp_path/'legacy');put(l,active(),stages=[MULTIPLE],dry_run=False);p=Provider();GmailOutbox(l).drain(p);assert not p.sent and l.db.execute('select count(*) from gmail_delivery').fetchone()[0]==0


def test_all_historical_signals_have_explicit_forbidden_delivery_flag_without_identity_change(tmp_path):
    from scripts.frank_gmail_delivery import delivery_flags
    l,e,o,sid=setup(tmp_path,True);before=[tuple(r) for r in l.db.execute('select * from signals')];delivery_flags(l)
    rows=l.db.execute('select * from signal_delivery_flags').fetchall();assert len(rows)==2 and all(r['delivery_forbidden']==1 for r in rows)
    assert before==[tuple(r) for r in l.db.execute('select * from signals')]
