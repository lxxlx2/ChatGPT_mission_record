"""Durable local notifications with stable OS identifiers and receipt recovery."""
import json,shutil,subprocess
from pathlib import Path
from ..hashing import digest
from ..frank.archive import publish
from .store import now
from .email import timestamp,label

JXA='''ObjC.import('AppKit');
function run(argv) {
  var center = $.NSUserNotificationCenter.defaultUserNotificationCenter;
  var items = center.deliveredNotifications;
  for (var i=0; i<items.count; i++) {
    if (ObjC.unwrap(items.objectAtIndex(i).identifier) === argv[0]) return 'ALREADY_PRESENT';
  }
  var notification = $.NSUserNotification.alloc.init;
  notification.identifier = argv[0];
  notification.title = argv[1];
  notification.informativeText = argv[2];
  center.deliverNotification(notification);
  return 'REQUEST_ACCEPTED';
}'''

class LocalNotifier:
    def __init__(self,run=subprocess.run,receipt_root=None):
        self.run=run;self.receipt_root=Path(receipt_root) if receipt_root else None
        if self.receipt_root:self.receipt_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    def __call__(self,signal):
        if signal.get('delivery_mode')=='DRY_RUN_AUDIT' and not signal.get('test_title','').startswith('[TEST]'):raise ValueError('HISTORICAL_DELIVERY_FORBIDDEN')
        content_hash=digest(signal);path=self.receipt_root/(digest({'signal_id':signal['signal_id'],'hash':content_hash})+'.json') if self.receipt_root else None
        if path and path.exists():
            old=json.loads(path.read_text())
            if old['signal_id']!=signal['signal_id'] or old['content_hash']!=content_hash:raise ValueError('LOCAL_RECEIPT_CONFLICT')
            return old
        title=signal.get('test_title') or ('Frank 多倍信号' if signal['signal_type']=='FRANK_MULTIPLE_SIGNAL' else 'Frank 建仓信号')
        p=signal['position'];mint=signal['mint'];cumulative='; '.join(f'{v} {label(k)}' for k,v in sorted(p['gross_quote_spent'].items()))
        message=f"{mint[:8]}…{mint[-6:]} | {signal['signal_type']} | buy_count={p['buy_count']} | latest={signal['latest_quote_amount']} {label(signal['quote_asset'])} | cumulative={cumulative} | {timestamp(signal['triggered_at'])}"
        binary=shutil.which('terminal-notifier')
        if binary:args=[binary,'-title',title,'-message',message,'-group',signal['signal_id']];mechanism='terminal-notifier-group'
        else:args=['/usr/bin/osascript','-l','JavaScript','-e',JXA,signal['signal_id'],title,message];mechanism='osascript-AppKit-identifier'
        result=self.run(args,capture_output=True,text=True,timeout=15)
        if result.returncode:raise RuntimeError('LOCAL_NOTIFICATION_COMMAND_FAILED')
        receipt={'signal_id':signal['signal_id'],'content_hash':content_hash,'accepted_at':now(),'mechanism':mechanism,'status':'COMMAND_ACCEPTED','os_response':result.stdout.strip()}
        if path:
            try:publish(path,json.dumps(receipt,sort_keys=True).encode())
            except FileExistsError:
                old=json.loads(path.read_text())
                if old['signal_id']!=signal['signal_id'] or old['content_hash']!=content_hash:raise ValueError('LOCAL_RECEIPT_CONFLICT')
                receipt=old
        return receipt

def drain(ledger,notifier=None):
    notifier=notifier or LocalNotifier();db=ledger.db
    # Recover accepted OS dispatch receipts after a parent crash before SQLite ack.
    rows=db.execute("SELECT o.*,s.body,s.content_hash FROM outbox o JOIN signals s USING(signal_id) WHERE o.status IN ('PENDING','RETRY_PENDING','CREDENTIAL_BLOCKED','IN_FLIGHT') ORDER BY CAST(s.created_at AS INTEGER),o.channel").fetchall()
    for row in rows:
        if row['channel']=='gmail':
            if json.loads(row['body']).get('policy_id')!='FRANK_LOCAL_SIGNAL_V1':
                db.execute("UPDATE outbox SET status='CREDENTIAL_BLOCKED',last_error='LEGACY_SIGNAL_NOT_V1_GMAIL_AUTHORITY' WHERE signal_id=? AND channel='gmail'",(row['signal_id'],))
            continue
        signal=json.loads(row['body']);db.execute("UPDATE outbox SET status='IN_FLIGHT',attempts=attempts+1 WHERE signal_id=? AND channel='local'",(row['signal_id'],))
        try:receipt=notifier(signal)
        except Exception as exc:
            db.execute("UPDATE outbox SET status='RETRY_PENDING',last_error=? WHERE signal_id=? AND channel='local'",(type(exc).__name__,row['signal_id']));continue
        receipt.update(content_hash=row['content_hash']);db.execute("UPDATE outbox SET status='COMMAND_ACCEPTED',receipt=?,last_error=NULL WHERE signal_id=? AND channel='local'",(json.dumps(receipt),row['signal_id']))
    # Independent Gmail worker; local notifications and scanner never await mail API.
    from .gmail import kick
    kick(ledger)
    return [dict(r) for r in db.execute('SELECT * FROM outbox')]
