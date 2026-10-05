"""One-time credential/readback probe executed inside the existing daemon worker."""
import json,os
from pathlib import Path
from mission_agent.signals.gmail import GmailOutbox
from mission_agent.signals.store import Ledger,now
from .__main__ import save_private

def probe(provider, runtime, config):
    target=runtime/'gmail-daemon-capability.json'
    if target.exists(): return json.loads(target.read_text()).get('status')=='PASS'
    ledger=None
    try:
        provider.ready()
        root=Path.home()/'.config/frank-local-gmail'
        receipt=json.loads((root/'test-receipt.json').read_text())
        if any(receipt.get(k)!='PASS' for k in ('test_send','test_sent_readback','test_dedupe')):raise ValueError('TEST_GATE_NOT_PASS')
        ledger=Ledger(root/'setup-state.sqlite');box=GmailOutbox(ledger);row=box.row(receipt['signal_id'])
        ids=provider.find_sent(row['wire_message_id'],row['signal_id'])
        if ids!=[receipt['test_message_id']]:raise ValueError('SENT_IDENTITY_NOT_UNIQUE')
        box.verify(row,provider.get(ids[0]))
        save_private(target,dict(status='PASS',pid=os.getpid(),uid=os.getuid(),verified_at=now(),account_email=provider.recipient,test_message_id=ids[0],credential_backend='LOCAL_FILE',api=provider.last_api_result))
        return True
    except Exception as exc:
        save_private(target,dict(status='BLOCKED',pid=os.getpid(),verified_at=now(),exception_class=type(exc).__name__,api=provider.last_api_result))
        return False
    finally:
        if ledger:ledger.db.close()
