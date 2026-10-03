"""Durable local delivery; missing Gmail credentials are explicitly blocked."""
import json,shutil,subprocess
from .store import now

class LocalNotifier:
    def __init__(self,run=subprocess.run):self.run=run
    def __call__(self,signal):
        title='Frank 多倍信号' if signal['signal_type']=='FRANK_MULTIPLE_SIGNAL' else 'Frank 建仓信号'
        p=signal['position'];mint=signal['mint']
        message=f"{mint[:8]}…{mint[-6:]} | {signal['signal_type']} | buy_count={p['buy_count']} | latest={signal['latest_quote_amount']} {signal['quote_asset']} | cumulative={json.dumps(p['gross_quote_spent'])} | time={signal['triggered_at']}"
        binary=shutil.which('terminal-notifier')
        if binary:args=[binary,'-title',title,'-message',message,'-group',signal['signal_id']]
        else:
            script='on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run'
            args=['/usr/bin/osascript','-e',script,title,message]
        result=self.run(args,capture_output=True,text=True,timeout=15)
        if result.returncode:raise RuntimeError('LOCAL_NOTIFICATION_COMMAND_FAILED')
        return {'signal_id':signal['signal_id'],'accepted_at':now(),'mechanism':'terminal-notifier' if binary else 'osascript','status':'COMMAND_ACCEPTED'}

def drain(ledger,notifier=None):
    notifier=notifier or LocalNotifier();db=ledger.db
    rows=db.execute("SELECT o.*,s.body,s.content_hash FROM outbox o JOIN signals s USING(signal_id) WHERE o.status IN ('PENDING','RETRY_PENDING','CREDENTIAL_BLOCKED') ORDER BY s.created_at,o.channel").fetchall()
    for row in rows:
        if row['channel']=='gmail':
            db.execute("UPDATE outbox SET status='CREDENTIAL_BLOCKED',last_error='NO_LOCAL_GMAIL_CREDENTIAL' WHERE signal_id=? AND channel='gmail'",(row['signal_id'],));continue
        signal=json.loads(row['body'])
        # A crash during a non-idempotent OS notification is ambiguous. Do not falsely mark sent.
        db.execute("UPDATE outbox SET status='IN_FLIGHT',attempts=attempts+1 WHERE signal_id=? AND channel='local'",(row['signal_id'],))
        try:receipt=notifier(signal)
        except Exception as exc:
            db.execute("UPDATE outbox SET status='RETRY_PENDING',last_error=? WHERE signal_id=? AND channel='local'",(type(exc).__name__,row['signal_id']));continue
        receipt.update(content_hash=row['content_hash'])
        db.execute("UPDATE outbox SET status='COMMAND_ACCEPTED',receipt=?,last_error=NULL WHERE signal_id=? AND channel='local'",(json.dumps(receipt),row['signal_id']))
    return [dict(r) for r in db.execute('SELECT * FROM outbox')]
