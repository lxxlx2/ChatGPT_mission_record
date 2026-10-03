"""Crash-safe Gmail delivery metadata; historical state/identities remain immutable.

Gmail has no transactional idempotent send. Ambiguous acceptance never blindly
resends: reconcile stable RFC822/visible markers in Sent, or remain unverified.
"""
import base64,email,json,os,re,threading,fcntl
from email.message import EmailMessage
from email import policy as mime_policy
from pathlib import Path
from ..hashing import digest
from ..db.connection import transaction
from .store import now
from .email import content

TEST_SUBJECT='[TEST] Frank MULTIPLE Gmail Delivery'
class CredentialBlocked(Exception):pass
class RetryableError(Exception):pass
class PermanentError(Exception):pass
class AmbiguousSend(Exception):pass

class GmailOutbox:
    def __init__(self,ledger):
        self.ledger,self.db=ledger,ledger.db
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS gmail_delivery(
        signal_id TEXT PRIMARY KEY,message_type TEXT NOT NULL,delivery_mode TEXT NOT NULL,
        delivery_forbidden INTEGER NOT NULL CHECK(delivery_forbidden IN (0,1)),
        subject TEXT NOT NULL,body TEXT NOT NULL,body_hash TEXT NOT NULL,content_hash TEXT NOT NULL,
        status TEXT NOT NULL,attempt_count INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,
        last_attempt_at TEXT,sent_at TEXT,gmail_message_id TEXT,gmail_thread_id TEXT,
        readback_verified INTEGER NOT NULL DEFAULT 0,wire_message_id TEXT NOT NULL UNIQUE,
        last_error TEXT,receipt TEXT);
        ''')
    def sync(self):
        rows=self.db.execute("SELECT s.body FROM signals s JOIN outbox o USING(signal_id) WHERE o.channel='gmail' AND json_extract(s.body,'$.policy_id')='FRANK_LOCAL_SIGNAL_V1'").fetchall()
        for row in rows:
            signal=json.loads(row[0]);mail=content(signal);mode=signal.get('delivery_mode','DRY_RUN_AUDIT');forbidden=mode!='LIVE' or bool(signal.get('delivery_forbidden'))
            self.enqueue(mail,mode=mode,forbidden=forbidden,created_at=str(signal['triggered_at']))
    def enqueue(self,mail,*,mode,forbidden=False,created_at=None):
        sid=mail['signal_id']
        if mode=='TEST':
            if not sid.startswith('test-') or mail['subject']!=TEST_SUBJECT or not all(x in mail['body'] for x in ('THIS IS A DELIVERY TEST','NOT A LIVE INVESTMENT SIGNAL')):raise ValueError('TEST_IDENTITY_REQUIRED')
        elif mode=='LIVE' and (sid.startswith('test-') or mail['subject'].startswith('[TEST]')):raise ValueError('TEST_CANNOT_BE_LIVE')
        forbidden=forbidden or mode not in ('LIVE','TEST');body_hash=digest(mail['body']);ch=digest({'subject':mail['subject'],'body':mail['body']})
        wire_id='<frank.'+digest({'signal_id':sid,'mode':mode})+'@local.invalid>'
        self.db.execute('INSERT OR IGNORE INTO gmail_delivery(signal_id,message_type,delivery_mode,delivery_forbidden,subject,body,body_hash,content_hash,status,created_at,wire_message_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(sid,'FRANK_MULTIPLE_SIGNAL' if mode!='TEST' else 'TEST_GMAIL_DELIVERY',mode,int(forbidden),mail['subject'],mail['body'],body_hash,ch,'DRY_RUN_AUDIT' if forbidden else 'PENDING',created_at or now(),wire_id))
        old=self.row(sid)
        if old['content_hash']!=ch or old['delivery_mode']!=mode or old['delivery_forbidden']!=int(forbidden):raise ValueError('IMMUTABLE_GMAIL_IDENTITY_CONFLICT')
    def row(self,sid):return dict(self.db.execute('SELECT * FROM gmail_delivery WHERE signal_id=?',(sid,)).fetchone())
    def wire_body(self,r):return r['body']+'\n\nFrank-Delivery-Identity: '+r['signal_id']+'\nFrank-Content-SHA256: '+r['content_hash']+'\nFrank-Delivery-Mode: '+r['delivery_mode']+'\n'
    def wire(self,r,recipient):
        if not re.fullmatch(r'[^\s<>@,;]+@[^\s<>@,;]+',recipient):raise CredentialBlocked('RECIPIENT_NOT_CONFIGURED')
        msg=EmailMessage();msg['To']=recipient;msg['Subject']=r['subject'];msg['Message-ID']=r['wire_message_id'];msg['X-Frank-Signal-ID']=r['signal_id'];msg['X-Frank-Content-Hash']=r['content_hash'];msg['X-Frank-Delivery-Mode']=r['delivery_mode'];msg.set_content(self.wire_body(r));return msg.as_bytes()
    def verify(self,r,message):
        if not message.get('id') or 'SENT' not in message.get('labelIds',[]):raise PermanentError('NOT_A_SENT_RECEIPT')
        try:
            raw=base64.urlsafe_b64decode(message['raw']+'===' );msg=email.message_from_bytes(raw,policy=mime_policy.default);body=msg.get_content()
            checks=[str(msg['Subject'])==r['subject'],str(msg['Message-ID'])==r['wire_message_id'],str(msg['X-Frank-Signal-ID'])==r['signal_id'],str(msg['X-Frank-Content-Hash'])==r['content_hash'],str(msg['X-Frank-Delivery-Mode'])==r['delivery_mode'],body.replace('\r\n','\n')==self.wire_body(r)]
        except (KeyError,ValueError,TypeError):raise PermanentError('INVALID_SENT_RECEIPT') from None
        if not all(checks):raise PermanentError('SENT_IDENTITY_OR_CONTENT_MISMATCH')
        sent_at=now()
        if message.get('internalDate'):sent_at=__import__('datetime').datetime.fromtimestamp(int(message['internalDate'])/1000,__import__('datetime').timezone.utc).isoformat()
        receipt={'signal_id':r['signal_id'],'subject':r['subject'],'body_hash':r['body_hash'],'content_hash':r['content_hash'],'gmail_message_id':message['id'],'gmail_thread_id':message.get('threadId'),'sent_at':sent_at,'readback_verified':True}
        with transaction(self.db):
            self.db.execute("UPDATE gmail_delivery SET status='SENT_VERIFIED',sent_at=?,gmail_message_id=?,gmail_thread_id=?,readback_verified=1,last_error=NULL,receipt=? WHERE signal_id=?",(sent_at,message['id'],message.get('threadId'),json.dumps(receipt),r['signal_id']))
            self.db.execute("UPDATE outbox SET status='SENT_VERIFIED',receipt=?,last_error=NULL WHERE signal_id=? AND channel='gmail'",(json.dumps(receipt),r['signal_id']))
    def update(self,sid,status,error=None):
        with transaction(self.db):
            self.db.execute('UPDATE gmail_delivery SET status=?,last_error=? WHERE signal_id=?',(status,error,sid));self.db.execute("UPDATE outbox SET status=?,last_error=? WHERE signal_id=? AND channel='gmail'",(status,error,sid))
    def drain(self,provider=None,*,allow_test=False):
        self.sync();rows=self.db.execute("SELECT * FROM gmail_delivery WHERE delivery_forbidden=0 AND status NOT IN ('SENT_VERIFIED','PERMANENT_ERROR','DRY_RUN_AUDIT') ORDER BY created_at,signal_id").fetchall()
        for row in rows:
            r=dict(row);sid=r['signal_id']
            if r['delivery_mode']=='TEST' and not allow_test:continue
            if provider is None:self.update(sid,'CREDENTIAL_BLOCKED','NO_LOCAL_GMAIL_CREDENTIAL');continue
            uncertain=r['status'] in ('SENDING','SENT_UNVERIFIED') or bool(r['gmail_message_id'])
            try:
                provider.ready()
                # Recorded receipt ID is read first. Search also covers crash before its commit.
                candidates=[]
                if r['gmail_message_id']:
                    candidates.append(provider.get(r['gmail_message_id']))
                else:
                    candidates=[provider.get(mid) for mid in provider.find_sent(r['wire_message_id'],sid)]
                if len(candidates)>1:raise PermanentError('MULTIPLE_SENT_IDENTITIES_REQUIRE_REVIEW')
                if candidates:self.verify(r,candidates[0]);continue
                if uncertain:self.update(sid,'SENT_UNVERIFIED','SEND_OUTCOME_UNCERTAIN_WAITING_SENT');continue
                raw=self.wire(r,provider.recipient)
                with transaction(self.db):
                    self.db.execute("UPDATE gmail_delivery SET status='SENDING',attempt_count=attempt_count+1,last_attempt_at=?,last_error=NULL WHERE signal_id=?",(now(),sid));self.db.execute("UPDATE outbox SET status='SENDING',attempts=attempts+1,last_error=NULL WHERE signal_id=? AND channel='gmail'",(sid,))
                response=provider.send(raw)
                if not response.get('id'):raise AmbiguousSend('SEND_RETURNED_NO_MESSAGE_ID')
                with transaction(self.db):
                    self.db.execute("UPDATE gmail_delivery SET status='SENT_UNVERIFIED',gmail_message_id=?,gmail_thread_id=?,sent_at=? WHERE signal_id=?",(response['id'],response.get('threadId'),now(),sid));self.db.execute("UPDATE outbox SET status='SENT_UNVERIFIED' WHERE signal_id=? AND channel='gmail'",(sid,))
                self.verify(self.row(sid),provider.get(response['id']))
            except CredentialBlocked:
                # Never erase evidence of ambiguous/accepted send during credential failure.
                self.update(sid,'SENT_UNVERIFIED' if uncertain or self.row(sid)['status'] in ('SENDING','SENT_UNVERIFIED') else 'CREDENTIAL_BLOCKED','LOCAL_GMAIL_CREDENTIAL_UNAVAILABLE')
            except (AmbiguousSend,RetryableError,OSError,TimeoutError):
                uncertain=uncertain or self.row(sid)['status'] in ('SENDING','SENT_UNVERIFIED');self.update(sid,'SENT_UNVERIFIED' if uncertain else 'RETRYABLE_ERROR','GMAIL_DELIVERY_OR_READBACK_RETRY_PENDING')
            except PermanentError as exc:self.update(sid,'PERMANENT_ERROR',str(exc))
        return self.summary()
    def summary(self):
        rows=self.db.execute('SELECT status,count(*) FROM gmail_delivery WHERE delivery_forbidden=0 AND delivery_mode=\'LIVE\' GROUP BY status').fetchall();counts=dict(rows)
        return {'pending':sum(counts.get(s,0) for s in ('PENDING','SENDING','RETRYABLE_ERROR')),'sent_verified':counts.get('SENT_VERIFIED',0),'sent_unverified':counts.get('SENT_UNVERIFIED',0),'blocked':counts.get('CREDENTIAL_BLOCKED',0),'failed':counts.get('PERMANENT_ERROR',0),'historical_forbidden':self.db.execute('SELECT count(*) FROM gmail_delivery WHERE delivery_forbidden=1').fetchone()[0]}

_worker_lock=threading.Lock()
def kick(ledger):
    """No Gmail network call blocks scanner. Worker uses a separate SQLite connection."""
    from .gmail_api import existing_provider
    outbox=GmailOutbox(ledger);outbox.sync();provider=existing_provider(Path(ledger.db.execute('PRAGMA database_list').fetchone()[2]).parent/'gmail-existing-source.json')
    if provider is None:outbox.drain();return outbox.summary()
    if not _worker_lock.acquire(blocking=False):return outbox.summary()
    database=Path(ledger.db.execute('PRAGMA database_list').fetchone()[2])
    def work():
        from .store import Ledger
        db=None
        try:
            with database.with_suffix('.gmail-delivery.lock').open('a') as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:return
                db=Ledger(database);GmailOutbox(db).drain(provider)
        finally:
            if db:db.db.close()
            _worker_lock.release()
    threading.Thread(target=work,name='frank-gmail-delivery',daemon=True).start();return outbox.summary()
