"""Opt-in connected-Gmail canary orchestration, no OAuth/SMTP/browser adapter.

Provider action is executed by the currently connected Codex Gmail capability.
This module persists intent/invocation/results and validates full MIME readbacks.
No ordinary test/CLI calls that capability. Budget is one fixed grant per SQLite.
"""
import hashlib
import os
from datetime import timedelta
from email.utils import getaddresses
from ..clock import stamp, parse_utc
from ..hashing import canonical, loads, digest
from ..db.connection import transaction

SCHEMA = '''
CREATE TABLE IF NOT EXISTS canary_results(event_id TEXT PRIMARY KEY,classification TEXT NOT NULL,provider_id TEXT,observed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS canary_budget(id INTEGER PRIMARY KEY CHECK(id=1),run_id TEXT NOT NULL,authorized INTEGER NOT NULL CHECK(authorized=3));
CREATE TABLE IF NOT EXISTS canary_intents(event_id TEXT PRIMARY KEY REFERENCES deliveries(event_id),run_id TEXT NOT NULL,
 recipient_hash TEXT NOT NULL,subject_marker TEXT NOT NULL,delivery_policy TEXT NOT NULL,slot INTEGER UNIQUE NOT NULL CHECK(slot BETWEEN 1 AND 3),
 created_at TEXT NOT NULL,invoked_at TEXT,provider_result_class TEXT NOT NULL,provider_message_id TEXT,verified_at TEXT,recovery_state TEXT NOT NULL);
'''


def recipient_hash(email):
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def subject(event_id):
    return f'[MISSION:{event_id}] [TEST ONLY] Crypto Monitor Phase 2B'


def body(event_id, run_id, scenario, sent_at):
    return ('Crypto Monitor Phase 2B integration canary.\n\nTEST ONLY.\n'
            'No investment action is required.\n\n'
            f'event_id: {event_id}\nrun_id: {run_id}\nscenario: {scenario}\nsent_at_utc: {sent_at}\n')


def text_parts(payload):
    values = []
    if payload.get('mime_type', '').lower() == 'text/plain':
        content = (payload.get('body') or {}).get('content')
        if isinstance(content, str): values.append(content)
    for part in payload.get('parts') or []: values.extend(text_parts(part))
    return values


def verify_message(message, event_id, expected_recipient_hash, earliest, returned_id=None):
    if 'SENT' not in (message.get('label_ids') or []): raise ValueError('NOT_SENT_LABEL')
    if not isinstance(message.get('id'), str) or not message['id']: raise ValueError('MISSING_PROVIDER_ID')
    if returned_id and message['id'] != returned_id: raise ValueError('PROVIDER_ID_CONFLICT')
    headers = message['payload']['headers']
    def header(name):
        matches = [h['value'] for h in headers if h['name'].lower() == name.lower()]
        if len(matches) != 1: raise ValueError('MISSING_OR_DUPLICATE_HEADER')
        return matches[0]
    if header('Subject') != subject(event_id): raise ValueError('SUBJECT_MARKER_MISMATCH')
    recipients = getaddresses([header('To')]); senders = getaddresses([header('From')])
    if len(recipients) != 1 or recipient_hash(recipients[0][1]) != expected_recipient_hash:
        raise ValueError('UNEXPECTED_RECIPIENT')
    if len(senders) != 1 or recipient_hash(senders[0][1]) != expected_recipient_hash:
        raise ValueError('SENDER_IDENTITY_CONFLICT')
    if any(h['name'].lower() in ('cc', 'bcc') and h['value'].strip() for h in headers):
        raise ValueError('UNEXPECTED_RECIPIENT')
    text = '\n'.join(text_parts(message['payload'])).replace('\r\n', '\n')
    if text.splitlines().count('event_id: ' + event_id) != 1: raise ValueError('BODY_EVENT_MISMATCH')
    if 'TEST ONLY.' not in text or 'No investment action is required.' not in text:
        raise ValueError('MISSING_TEST_NOTICE')
    from datetime import datetime, timezone
    when = datetime.fromtimestamp(int(message['internal_date']) / 1000, timezone.utc)
    if when < parse_utc(earliest) - timedelta(minutes=5) or when > parse_utc(earliest) + timedelta(minutes=15):
        raise ValueError('TIMESTAMP_MISMATCH')
    return {'id': message['id'], 'sent_at': stamp(when)}


class Canary:
    def __init__(self, repo, run_id, self_hash):
        if not run_id or not self_hash or len(self_hash) != 64: raise ValueError('invalid canary identity')
        self.repo, self.run_id, self.self_hash = repo, run_id, self_hash
        with transaction(repo.db):
            for statement in filter(str.strip, SCHEMA.split(';')): repo.db.execute(statement)
            repo.db.execute('INSERT OR IGNORE INTO canary_budget VALUES(1,?,3)', (run_id,))
            row = repo.db.execute('SELECT * FROM canary_budget').fetchone()
            if row['run_id'] != run_id or row['authorized'] != 3: raise ValueError('BUDGET_GRANT_MISMATCH')
            repo.db.execute("INSERT OR IGNORE INTO meta VALUES('canary_recipient_hash',?)",(self_hash,))
            if repo.db.execute("SELECT value FROM meta WHERE key='canary_recipient_hash'").fetchone()[0] != self_hash:
                raise ValueError('RECIPIENT_GRANT_MISMATCH')

    def _check_stop(self):
        if self.repo.db.execute("SELECT value FROM meta WHERE key='canary_abort_reason'").fetchone():
            raise ValueError('CANARY_ABORTED_NO_MORE_SENDS')

    def _abort(self, reason, event_id=None):
        with transaction(self.repo.db):
            self.repo.db.execute("INSERT INTO meta VALUES('canary_abort_reason',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(reason,))
            if event_id:
                self.repo.db.execute("UPDATE deliveries SET state='FAILED_MANUAL_REVIEW',last_error=? WHERE event_id=?",(reason,event_id))
                self.repo.db.execute("UPDATE canary_intents SET recovery_state='FAILED_MANUAL_REVIEW' WHERE event_id=?",(event_id,))

    def budget(self):
        used = self.repo.db.execute('SELECT COUNT(*) FROM canary_intents WHERE invoked_at IS NOT NULL').fetchone()[0]
        return {'authorized': 3, 'used': used, 'remaining': 3 - used}

    def intent(self, event_id):
        return self.repo.db.execute('SELECT * FROM canary_intents WHERE event_id=?', (event_id,)).fetchone()

    def prepare(self, event_id, recipient, exact_matches, private_verified, enabled=False, explicit=False):
        self._check_stop()
        if not enabled or not explicit: raise ValueError('REAL_SEND_DOUBLE_GATE_REQUIRED')
        if not private_verified: raise ValueError('RUNTIME_REPO_NOT_PRIVATE')
        if recipient != self.self_hash: raise ValueError('RECIPIENT_NOT_VERIFIED')
        if not event_id.startswith('phase2b:gmail:' + self.run_id + ':'): raise ValueError('NON_TEST_EVENT')
        if exact_matches: raise ValueError('PREEXISTING_SENT_MATCH')
        if self.intent(event_id): raise ValueError('EVENT_ALREADY_HAS_SEND_INTENT')
        with transaction(self.repo.db):
            row = self.repo.db.execute('SELECT * FROM deliveries WHERE event_id=?', (event_id,)).fetchone()
            if not row or row['state'] != 'DELIVERY_PENDING': raise ValueError('NOT_DELIVERY_PENDING')
            count = self.repo.db.execute('SELECT COUNT(*) FROM canary_intents').fetchone()[0]
            if count >= 3 or self.budget()['used'] >= 3: raise ValueError('SEND_BUDGET_EXHAUSTED')
            slot = count + 1; now = stamp(self.repo.clock.now())
            self.repo.db.execute('INSERT INTO canary_intents VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                (event_id,self.run_id,recipient,'[MISSION:'+event_id+']',row['policy'],slot,now,None,'NOT_INVOKED',None,None,'DELIVERY_SENDING'))
            self.repo.db.execute("UPDATE deliveries SET state='DELIVERY_SENDING',last_sent_attempt_at=?,updated_at=? WHERE event_id=?", (now,now,event_id))
        return slot

    def invoke(self, event_id, enabled=False, explicit=False, private_verified=False):
        self._check_stop()
        if not enabled or not explicit: raise ValueError('REAL_SEND_DOUBLE_GATE_REQUIRED')
        if not private_verified: raise ValueError('RUNTIME_REPO_NOT_PRIVATE')
        with transaction(self.repo.db):
            row = self.intent(event_id)
            state = self.repo.db.execute('SELECT state FROM deliveries WHERE event_id=?',(event_id,)).fetchone()
            if not row or row['invoked_at'] or not state or state[0] != 'DELIVERY_SENDING':
                raise ValueError('SEND_FORBIDDEN_USE_LOOKUP_RECOVERY')
            if self.budget()['used'] >= 3: raise ValueError('SEND_BUDGET_EXHAUSTED')
            now = stamp(self.repo.clock.now())
            self.repo.db.execute("UPDATE canary_intents SET invoked_at=?,provider_result_class='UNKNOWN' WHERE event_id=?",(now,event_id))
            # Invocation claim is irreversible even if action crashes or result is unknown.
            return {'slot':row['slot'],'invoked_at':now}

    def result(self, event_id, classification, provider_id=None, inject_failure=False):
        if classification not in ('SUCCESS','EXPLICIT_REJECT','TIMEOUT','AMBIGUOUS','UNKNOWN'):
            raise ValueError('invalid provider classification')
        row = self.intent(event_id)
        if not row or not row['invoked_at']: raise ValueError('provider never invoked')
        with transaction(self.repo.db):
            self.repo.db.execute("INSERT INTO canary_results VALUES(?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET classification=excluded.classification,provider_id=excluded.provider_id,observed_at=excluded.observed_at",(event_id,classification,provider_id,stamp(self.repo.clock.now())))
        if inject_failure:
            try:
                with transaction(self.repo.db):
                    self.repo.db.execute('UPDATE canary_intents SET provider_result_class=?,provider_message_id=? WHERE event_id=?', (classification,provider_id,event_id))
                    raise RuntimeError('INJECTED_POST_ACCEPTANCE_PERSISTENCE_FAILURE')
            except RuntimeError:
                self.uncertain(event_id, 'INJECTED_POST_ACCEPTANCE_PERSISTENCE_FAILURE')
                return
        with transaction(self.repo.db):
            self.repo.db.execute("UPDATE canary_intents SET provider_result_class=?,provider_message_id=?,recovery_state='DELIVERY_UNCERTAIN' WHERE event_id=?",(classification,provider_id,event_id))
            self.repo.db.execute("UPDATE deliveries SET state='DELIVERY_UNCERTAIN',provider_message_id=?,updated_at=? WHERE event_id=?",(provider_id,stamp(self.repo.clock.now()),event_id))

    def uncertain(self, event_id, reason):
        with transaction(self.repo.db):
            self.repo.db.execute("UPDATE canary_intents SET recovery_state='DELIVERY_UNCERTAIN' WHERE event_id=?",(event_id,))
            self.repo.db.execute("UPDATE deliveries SET state='DELIVERY_UNCERTAIN',last_error=?,updated_at=? WHERE event_id=?",(reason,stamp(self.repo.clock.now()),event_id))

    def recover(self, event_id, messages):
        row = self.intent(event_id)
        if not row or not row['invoked_at']: raise ValueError('no persisted invocation')
        observed = self.repo.db.execute('SELECT * FROM canary_results WHERE event_id=?',(event_id,)).fetchone()
        returned_id = row['provider_message_id'] or (observed['provider_id'] if observed else None)
        self._check_stop()
        try:
            verified = [verify_message(m,event_id,row['recipient_hash'],row['invoked_at']) for m in messages]
        except ValueError as error:
            self._abort(str(error),event_id)
            raise
        if len(verified) > 1:
            self._abort('MULTIPLE_SENT_MATCHES',event_id)
            with transaction(self.repo.db):
                self.repo.db.execute("UPDATE deliveries SET state='FAILED_MANUAL_REVIEW',last_error='MULTIPLE_SENT_MATCHES' WHERE event_id=?",(event_id,))
                self.repo.db.execute("UPDATE canary_intents SET recovery_state='FAILED_MANUAL_REVIEW' WHERE event_id=?",(event_id,))
            return 'FAILED_MANUAL_REVIEW'
        if not verified:
            self.uncertain(event_id,'SENT_NOT_YET_CONFIRMED');return 'DELIVERY_UNCERTAIN'
        proof = verified[0]
        if returned_id and proof['id'] != returned_id:
            self._abort('PROVIDER_ID_CONFLICT',event_id)
            raise ValueError('PROVIDER_ID_CONFLICT')
        with transaction(self.repo.db):
            now = stamp(self.repo.clock.now())
            self.repo.db.execute("UPDATE deliveries SET state='DELIVERED',provider_message_id=?,last_error=NULL,updated_at=? WHERE event_id=?",(proof['id'],now,event_id))
            self.repo.db.execute("UPDATE canary_intents SET provider_message_id=?,verified_at=COALESCE(verified_at,?),recovery_state='DELIVERED' WHERE event_id=?",(proof['id'],now,event_id))
        return 'DELIVERED'

    def receipt(self, event_id, decision, batch_id, batch_hash):
        row = self.intent(event_id)
        if not row or row['recovery_state'] != 'DELIVERED': raise ValueError('delivery not verified')
        observed = self.repo.db.execute('SELECT classification FROM canary_results WHERE event_id=?',(event_id,)).fetchone()
        value = {'schema_version':1,'run_id':self.run_id,'event_id':event_id,'decision':decision,
                 'delivery_policy':row['delivery_policy'],'delivery_state':row['recovery_state'],
                 'send_slot_number':row['slot'],'send_action_invoked':row['invoked_at'] is not None,
                 'provider_result_class':observed[0] if observed else row['provider_result_class'],
                 'provider_message_id_hash':hashlib.sha256(row['provider_message_id'].encode()).hexdigest(),
                 'sent_at':row['invoked_at'],'verified_at':row['verified_at'],'subject_marker':row['subject_marker'],
                 'recipient_hash':row['recipient_hash'],'input_batch_id':batch_id,'input_payload_sha256':batch_hash}
        return {**value,'receipt_sha256':digest(value)}
