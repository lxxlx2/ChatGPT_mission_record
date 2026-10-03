import json
import pytest
from scripts.frank_historical_delivery_e2e import HistoricalOutbox
from mission_agent.signals.store import Ledger
from test_frank_gmail_delivery import Provider

def historical_mail():
    return dict(signal_id='historical-test:'+'a'*64+':delivery-e2e-v1',subject='[HISTORICAL TEST][Frank 多倍信号] TOKEN | MULTIPLE | original date',body='HISTORICAL REPLAY / DELIVERY E2E TEST\n这不是 Frank 当前实时交易。\n不得作为新的实时买入信号解读。')

def test_historical_namespace_and_content_are_required(tmp_path):
    box=HistoricalOutbox(Ledger(tmp_path/'db'));mail=historical_mail()
    with pytest.raises(ValueError,match='HISTORICAL_NAMESPACE'):box.enqueue_historical({**mail,'signal_id':'live-id'})
    with pytest.raises(ValueError,match='HISTORICAL_LABEL'):box.enqueue_historical({**mail,'subject':'Frank live signal'})
    box.enqueue_historical(mail)
    with pytest.raises(ValueError,match='IMMUTABLE'):box.enqueue_historical({**mail,'body':mail['body']+' changed'})

def test_isolated_historical_send_and_reopened_recovery_do_not_touch_live_outbox(tmp_path):
    ledger=Ledger(tmp_path/'db');box=HistoricalOutbox(ledger);mail=historical_mail();box.enqueue_historical(mail);p=Provider();box.drain(p)
    assert len(p.sent)==1 and box.row(mail['signal_id'])['delivery_mode']=='HISTORICAL_TEST'
    box.drain(p);assert len(p.sent)==1
    ledger.db.execute("update gmail_delivery set status='SENDING',gmail_message_id=NULL,receipt=NULL,readback_verified=0")
    ledger.db.close();ledger=Ledger(tmp_path/'db');box=HistoricalOutbox(ledger);box.drain(p)
    assert len(p.sent)==1 and box.row(mail['signal_id'])['status']=='SENT_VERIFIED'
    assert ledger.db.execute('select count(*) from outbox').fetchone()[0]==0
    assert ledger.db.execute('select count(*) from signals').fetchone()[0]==0
