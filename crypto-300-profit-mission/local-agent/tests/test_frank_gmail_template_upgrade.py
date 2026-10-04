import base64,email,json,re
from email import policy as mime_policy
import pytest
from mission_agent.hashing import digest
from mission_agent.signals import email as renderer
from mission_agent.signals.engine import Engine
from mission_agent.signals.gmail import GmailOutbox,PermanentError
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger
from test_frank_v1 import fixture_multiple,signals,POLICY
from test_frank_local_signals import active,put
from test_frank_gmail_delivery import Provider

def template(version):
    def render(s):
        subject='[Frank 多倍信号] '+version+' fixture'
        body=version+' frozen body\n'+s['signal_id']
        return dict(signal_id=s['signal_id'],subject=subject,body=body,content_hash=digest({'subject':subject,'body':body}))
    return render

class IdentityProvider(Provider):
    def find_sent(self,wire_id,sid):
        self.actions.append('find')
        return [mid for mid,m in self.messages.items() if str(email.message_from_bytes(base64.urlsafe_b64decode(m['raw']),policy=mime_policy.default)['X-Frank-Signal-ID']).strip()==sid]

def setup_old(tmp_path,monkeypatch,dry=False):
    monkeypatch.setattr(renderer,'content',template('OLD'))
    l,e=fixture_multiple(tmp_path,dry);o=GmailOutbox(l);o.sync();sid=signals(l)[-1]['signal_id']
    return l,e,o,sid

def add_new(l,e):
    e.dry_run=False
    for sig,at,quote in [('new-first',200000,13000),('new-second',201200,13000),('new-third',202700,5000)]:
        event=active(sig,100,quote);event['trade']['mint']='mint2';event['trade']['quote_amount_raw']=str(quote*10**6);event['trade']['quote_decimals']=6;event['block_time']=at;event['slot']=at
        put(l,event);e.drain()
    return next(s['signal_id'] for s in signals(l) if s['mint']=='mint2' and s['signal_type']=='FRANK_MULTIPLE_SIGNAL')

@pytest.mark.parametrize('status',['PENDING','SENDING','SENT_UNVERIFIED','SENT_VERIFIED','CREDENTIAL_BLOCKED','RETRYABLE_ERROR','PERMANENT_ERROR'])
def test_all_existing_delivery_states_survive_template_upgrade_without_render(tmp_path,monkeypatch,status):
    l,e,o,sid=setup_old(tmp_path,monkeypatch)
    l.db.execute('update gmail_delivery set status=? where signal_id=?',(status,sid));before=o.row(sid)
    monkeypatch.setattr(renderer,'content',lambda _:pytest.fail('old delivery re-rendered'))
    o.sync();assert o.row(sid)==before

def test_old_sent_verified_is_unchanged_and_not_resent(tmp_path,monkeypatch):
    l,e,o,sid=setup_old(tmp_path,monkeypatch);p=IdentityProvider();o.drain(p);before=o.row(sid)
    monkeypatch.setattr(renderer,'content',template('NEW'));o.sync();count=len(p.sent);o.drain(p)
    assert len(p.sent)-count==0 and o.row(sid)==before and before['status']=='SENT_VERIFIED'

def test_old_pending_sends_frozen_old_body_after_upgrade(tmp_path,monkeypatch):
    l,e,o,sid=setup_old(tmp_path,monkeypatch);before=o.row(sid)
    monkeypatch.setattr(renderer,'content',template('NEW'));o.sync();p=IdentityProvider();o.drain(p)
    msg=email.message_from_bytes(p.sent[0],policy=mime_policy.default)
    assert str(msg['Subject'])==before['subject'] and msg.get_content()==o.wire_body(before)
    for key in ('subject','body','content_hash','wire_message_id'):assert o.row(sid)[key]==before[key]

@pytest.mark.parametrize('status',['SENDING','SENT_UNVERIFIED'])
def test_uncertain_old_send_recovers_frozen_body_without_resend(tmp_path,monkeypatch,status):
    l,e,o,sid=setup_old(tmp_path,monkeypatch);p=IdentityProvider();o.drain(p);old=o.row(sid)
    l.db.execute('update gmail_delivery set status=?,gmail_message_id=NULL,receipt=NULL,readback_verified=0 where signal_id=?',(status,sid))
    monkeypatch.setattr(renderer,'content',template('NEW'));o.sync();count=len(p.sent);o.drain(p)
    assert len(p.sent)-count==0 and o.row(sid)['status']=='SENT_VERIFIED'
    assert o.row(sid)['gmail_message_id']==old['gmail_message_id'] and o.row(sid)['body']==old['body']

@pytest.mark.parametrize('old_dry',[False,True])
def test_old_and_new_actual_signals_coexist_and_worker_is_not_blocked(tmp_path,monkeypatch,old_dry):
    l,e,o,old_sid=setup_old(tmp_path,monkeypatch,old_dry);before=o.row(old_sid)
    monkeypatch.setattr(renderer,'content',template('NEW'));new_sid=add_new(l,e);o.sync()
    assert o.row(old_sid)==before and o.row(old_sid)['body'].startswith('OLD')
    assert o.row(new_sid)['body'].startswith('NEW')
    frozen=l.db.execute('select body,content_hash from email_content where signal_id=?',(new_sid,)).fetchone()
    assert frozen['body']==o.row(new_sid)['body'] and frozen['content_hash']==o.row(new_sid)['content_hash']
    p=IdentityProvider();o.drain(p)
    assert o.row(new_sid)['status']=='SENT_VERIFIED' and len(p.sent)==(1 if old_dry else 2)
    if old_dry:assert o.row(old_sid)['delivery_forbidden']==1 and o.row(old_sid)['status']=='DRY_RUN_AUDIT'

def test_frozen_content_without_delivery_does_not_use_current_renderer(tmp_path,monkeypatch):
    monkeypatch.setattr(renderer,'content',template('OLD'));l,e=fixture_multiple(tmp_path,False);sid=signals(l)[-1]['signal_id']
    monkeypatch.setattr(renderer,'content',lambda _:pytest.fail('frozen content re-rendered'))
    o=GmailOutbox(l);o.sync();assert o.row(sid)['body'].startswith('OLD')

@pytest.mark.parametrize('missing_table',[False,True])
def test_missing_frozen_content_fails_closed_but_does_not_block_new_signal(tmp_path,monkeypatch,missing_table):
    monkeypatch.setattr(renderer,'content',template('OLD'));l,e=fixture_multiple(tmp_path,False);old_sid=signals(l)[-1]['signal_id']
    l.db.execute('drop table email_content' if missing_table else 'delete from email_content')
    o=GmailOutbox(l);o.sync()
    assert not l.db.execute('select 1 from gmail_delivery where signal_id=?',(old_sid,)).fetchone()
    assert l.db.execute("select last_error from outbox where signal_id=? and channel='gmail'",(old_sid,)).fetchone()[0]=='MISSING_FROZEN_EMAIL_CONTENT'
    e=Engine(l,load_policy(POLICY),dry_run=False);assert l.db.execute('select count(*) from email_content').fetchone()[0]==0
    monkeypatch.setattr(renderer,'content',template('NEW'));new_sid=add_new(l,e);o.sync();p=IdentityProvider();o.drain(p)
    assert o.row(new_sid)['status']=='SENT_VERIFIED' and len(p.sent)==1

def test_restart_recovers_missing_content_only_from_existing_frozen_delivery(tmp_path,monkeypatch):
    l,e,o,sid=setup_old(tmp_path,monkeypatch);old=o.row(sid);l.db.execute('delete from email_content')
    monkeypatch.setattr(renderer,'content',lambda _:pytest.fail('migration re-rendered'))
    Engine(l,load_policy(POLICY),dry_run=False)
    restored=l.db.execute('select subject,body,content_hash from email_content where signal_id=?',(sid,)).fetchone()
    assert dict(restored)=={k:old[k] for k in ('subject','body','content_hash')} and o.row(sid)==old

def test_corrupt_frozen_hash_is_not_enqueued(tmp_path,monkeypatch):
    monkeypatch.setattr(renderer,'content',template('OLD'));l,e=fixture_multiple(tmp_path,False);sid=signals(l)[-1]['signal_id'];l.db.execute("update email_content set content_hash='corrupt'")
    o=GmailOutbox(l);o.sync();assert not l.db.execute('select 1 from gmail_delivery').fetchone()
    assert l.db.execute("select last_error from outbox where channel='gmail'").fetchone()[0]=='INVALID_FROZEN_EMAIL_CONTENT'

@pytest.mark.parametrize('mode',['LIVE','TEST','HISTORICAL_TEST'])
def test_folded_outer_header_whitespace_roundtrip_preserves_exact_values(tmp_path,monkeypatch,mode):
    l,e,o,sid=setup_old(tmp_path,monkeypatch);r=o.row(sid)
    # Verification accepts any saved delivery mode; send gates are not changed by this test.
    r={**r,'delivery_mode':mode};raw=o.wire(r,'fixture@example.invalid')
    for header,key in [('X-Frank-Signal-ID','signal_id'),('X-Frank-Content-Hash','content_hash'),('X-Frank-Delivery-Mode','delivery_mode')]:
        raw=re.sub(rb'(?m)^'+header.encode()+rb':[^\r\n]*(?:\r?\n[ \t][^\r\n]*)*',header.encode()+b':\n \t'+r[key].encode()+b' \t',raw)
    msg=dict(id='fake-folded',labelIds=['SENT'],raw=base64.urlsafe_b64encode(raw).decode())
    o.verify(r,msg);assert o.row(sid)['readback_verified']==1
    changed=raw.replace(r['content_hash'].encode(),r['content_hash'][:20].encode()+b' '+r['content_hash'][20:].encode());msg['raw']=base64.urlsafe_b64encode(changed).decode()
    with pytest.raises(PermanentError,match='SENT_IDENTITY_OR_CONTENT_MISMATCH'):o.verify(r,msg)

def test_background_worker_processes_new_signal_after_old_template_upgrade(tmp_path,monkeypatch):
    import time
    from mission_agent.signals.gmail import kick,_worker_lock
    from mission_agent.signals import gmail_api
    l,e,o,old_sid=setup_old(tmp_path,monkeypatch);old=o.row(old_sid)
    monkeypatch.setattr(renderer,'content',template('NEW'));new_sid=add_new(l,e)
    p=IdentityProvider();monkeypatch.setattr(gmail_api,'existing_provider',lambda *args:p)
    kick(l)
    for _ in range(200):
        if not _worker_lock.locked():break
        time.sleep(.01)
    assert not _worker_lock.locked()
    assert o.row(old_sid)['body']==old['body'] and o.row(old_sid)['status']=='SENT_VERIFIED'
    assert o.row(new_sid)['status']=='SENT_VERIFIED' and len(p.sent)==2
