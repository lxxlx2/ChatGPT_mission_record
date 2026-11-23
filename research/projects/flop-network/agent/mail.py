"""Independent FLOP Gmail delivery: local immutable outbox and Gmail Sent readback.

Uses the existing Mission OAuth Gmail provider. Never provisions Gmail credentials,
logs tokens or assumes send returned SUCCESS without a matching Sent receipt.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.message import EmailMessage
from email import policy
import email
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

MISSION = Path(__file__).resolve().parents[3] / 'crypto-300-profit-mission' / 'local-agent'
if str(MISSION) not in sys.path:
    sys.path.insert(0, str(MISSION))
from mission_agent.signals.gmail_api import OAuthGmail
from mission_agent.signals.gmail import CredentialBlocked, RetryableError, PermanentError, AmbiguousSend


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _hash(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def init(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS flop_mail (
      mail_key TEXT PRIMARY KEY, subject TEXT NOT NULL, body TEXT NOT NULL,
      content_sha TEXT NOT NULL, wire_id TEXT NOT NULL,
      status TEXT NOT NULL, created_at TEXT NOT NULL, last_attempt TEXT,
      gmail_id TEXT, error_code TEXT, sent_verified_at TEXT
    );
    """)
    conn.commit()


def enqueue(conn, key, subject, body):
    """Immutable notification identities, fixed per launch/test/digest/error key."""
    if not re.fullmatch(r'[a-zA-Z0-9_.:-]{4,150}', key):
        raise ValueError('BAD_MAIL_KEY')
    if not subject.startswith('[FLOP]') or not body.strip():
        raise ValueError('BAD_MAIL_CONTENT')
    payload_hash = _hash(subject + '\n' + body)
    wire_id = '<flop.' + _hash(key) + '@local.invalid>'
    conn.execute("""
      INSERT OR IGNORE INTO flop_mail
      (mail_key,subject,body,content_sha,wire_id,status,created_at)
      VALUES (?,?,?,?,?,'PENDING',?)
    """, (key,subject,body,payload_hash,wire_id,_utc()))
    row = conn.execute('SELECT content_sha FROM flop_mail WHERE mail_key=?',(key,)).fetchone()
    if row[0] != payload_hash:
        raise ValueError('NOTIFICATION_CONTENT_IMMUTABLE_CONFLICT')
    conn.commit()


def provider_from_local():
    """Reuse configured authorized OAuth; user stores the path ONLY on Mac."""
    path = os.environ.get('FLOP_GMAIL_EXISTING_OAUTH_FILE') or os.environ.get('FRANK_GMAIL_EXISTING_OAUTH_FILE')
    receiver = os.environ.get('FLOP_GMAIL_RECIPIENT') or os.environ.get('FRANK_GMAIL_RECIPIENT')
    if not path or not Path(path).is_file():
        return None
    return OAuthGmail(path, recipient=receiver)


def message_bytes(row, recipient):
    if not re.fullmatch(r'[^\s<>@,;]+@[^\s<>@,;]+',recipient or ''):
        raise CredentialBlocked('FLOP_RECIPIENT_UNAVAILABLE')
    msg = EmailMessage()
    msg['To'] = recipient
    msg['From'] = recipient
    msg['Subject'] = row['subject']
    msg['Message-ID'] = row['wire_id']
    msg['X-Flop-Notification-Key'] = row['mail_key']
    msg['X-Flop-Content-SHA256'] = row['content_sha']
    msg.set_content(row['body'] + '\n\nFLOP-Notification-Key: ' + row['mail_key'] +
                    '\nFLOP-Content-SHA256: ' + row['content_sha'] + '\n')
    return msg.as_bytes()


def matches_sent(row, payload):
    if not payload.get('id') or 'SENT' not in payload.get('labelIds',[]):
        return False
    try:
        wire=base64.urlsafe_b64decode(payload['raw']+'===')
        msg=email.message_from_bytes(wire, policy=policy.default)
        body=msg.get_content().replace('\r\n','\n')
        return (str(msg['Subject'])==row['subject']
                and str(msg['X-Flop-Notification-Key'])==row['mail_key']
                and str(msg['X-Flop-Content-SHA256'])==row['content_sha']
                and body==row['body']+'\n\nFLOP-Notification-Key: '+row['mail_key']+
                     '\nFLOP-Content-SHA256: '+row['content_sha']+'\n')
    except (KeyError,ValueError,TypeError):
        return False


def pump(conn, provider=None, *, max_items=12):
    """Never blindly resend uncertain Gmail sends; reconcile Sent first."""
    init(conn)
    if provider is None:
        provider = provider_from_local()
    rows = conn.execute("""SELECT * FROM flop_mail WHERE status IN
        ('PENDING','CREDENTIAL_BLOCKED','SENDING','SENT_UNVERIFIED','RETRYABLE')
        ORDER BY created_at LIMIT ?""", (max_items,)).fetchall()
    counters = {}
    for row in rows:
        key=row['mail_key']
        if not provider:
            conn.execute('UPDATE flop_mail SET status=?,error_code=? WHERE mail_key=?',
                         ('CREDENTIAL_BLOCKED','LOCAL_OAUTH_NOT_CONFIGURED',key))
            counters[key]='CREDENTIAL_BLOCKED'; continue
        uncertain=row['status'] in ('SENDING','SENT_UNVERIFIED') or bool(row['gmail_id'])
        try:
            provider.ready()
            ids=[row['gmail_id']] if row['gmail_id'] else provider.find_sent(row['wire_id'],key)
            ids=list(dict.fromkeys(x for x in ids if x))
            if len(ids)>1:
                raise PermanentError('MULTIPLE_SENT_IDENTITIES')
            if ids:
                item=provider.get(ids[0])
                if not matches_sent(row,item):
                    raise PermanentError('SENT_RECEIPT_MISMATCH')
                conn.execute('UPDATE flop_mail SET status=?,gmail_id=?,sent_verified_at=?,error_code=NULL WHERE mail_key=?',
                             ('SENT_VERIFIED',ids[0],_utc(),key))
                counters[key]='SENT_VERIFIED';continue
            if uncertain:
                conn.execute('UPDATE flop_mail SET status=?,error_code=? WHERE mail_key=?',
                             ('SENT_UNVERIFIED','UNKNOWN_SEND_OUTCOME_NO_RESEND',key))
                counters[key]='SENT_UNVERIFIED'; continue
            conn.execute('UPDATE flop_mail SET status=?,last_attempt=?,error_code=NULL WHERE mail_key=?',
                         ('SENDING',_utc(),key))
            conn.commit()
            raw=message_bytes(row,provider.recipient)
            result=provider.send(raw)
            if not result.get('id'):
                raise AmbiguousSend('SEND_RETURNED_NO_ID')
            conn.execute('UPDATE flop_mail SET status=?,gmail_id=? WHERE mail_key=?',
                         ('SENT_UNVERIFIED',result['id'],key))
            conn.commit()
            item=provider.get(result['id'])
            if not matches_sent(row,item):
                raise PermanentError('SENT_RECEIPT_MISMATCH')
            conn.execute('UPDATE flop_mail SET status=?,sent_verified_at=?,error_code=NULL WHERE mail_key=?',
                         ('SENT_VERIFIED',_utc(),key))
            counters[key]='SENT_VERIFIED'
        except (CredentialBlocked,) as exc:
            state='SENT_UNVERIFIED' if uncertain else 'CREDENTIAL_BLOCKED'
            conn.execute('UPDATE flop_mail SET status=?,error_code=? WHERE mail_key=?',
                         (state,type(exc).__name__,key))
            counters[key]=state
        except (AmbiguousSend, RetryableError, OSError, TimeoutError):
            conn.execute('UPDATE flop_mail SET status=?,error_code=? WHERE mail_key=?',
                         ('SENT_UNVERIFIED','GMAIL_SEND_OR_READBACK_AMBIGUOUS',key))
            counters[key]='SENT_UNVERIFIED'
        except PermanentError as exc:
            conn.execute('UPDATE flop_mail SET status=?,error_code=? WHERE mail_key=?',
                         ('PERMANENT_ERROR',str(exc),key))
            counters[key]='PERMANENT_ERROR'
        except Exception as exc:
            # Preserve evidence instead of claiming delivery, never leak exception text.
            state='SENT_UNVERIFIED' if row['status']=='SENDING' else 'CREDENTIAL_BLOCKED'
            conn.execute('UPDATE flop_mail SET status=?,error_code=? WHERE mail_key=?',
                         (state,type(exc).__name__,key))
            counters[key]=state
    conn.commit()
    return counters


def mail_status(conn):
    init(conn)
    counts = dict(conn.execute('SELECT status,COUNT(*) FROM flop_mail GROUP BY status').fetchall())
    return {'sent_verified':counts.get('SENT_VERIFIED',0),
            'unverified':counts.get('SENT_UNVERIFIED',0),
            'blocked':counts.get('CREDENTIAL_BLOCKED',0),
            'failed':counts.get('PERMANENT_ERROR',0),
            'pending':counts.get('PENDING',0)+counts.get('SENDING',0)+counts.get('RETRYABLE',0)}
