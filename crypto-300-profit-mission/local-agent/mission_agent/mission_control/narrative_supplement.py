"""Read one report-bound browser claim without collecting or changing evidence."""
from contextlib import ExitStack
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import re
import stat
import time
import unicodedata
from urllib.parse import urlsplit

MAX_BYTES = 16 * 1024
FIELDS = frozenset({
    'version', 'job_id', 'mint', 'report_sha256', 'source_url', 'author_handle',
    'published_at_utc', 'captured_at_utc', 'summary', 'source_text_sha256',
})
HOSTS = frozenset({'x.com', 'www.x.com', 'twitter.com', 'www.twitter.com'})
UTC_TIME = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)')
HEX64 = re.compile(r'[0-9a-f]{64}')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_FIELD')
        result[key] = value
    return result


def _read_record(control_root: Path, job_id: str):
    # Directory descriptors prevent a note path from following a replaced link.
    # Nonblocking open also rejects a FIFO before an ordinary read could hang.
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        folder = os.open(control_root, directory_flags)
        stack.callback(os.close, folder)
        for name in ('cluster-source-notes', job_id):
            folder = os.open(name, directory_flags, dir_fd=folder)
            stack.callback(os.close, folder)
        source = os.open('narrative.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
        stack.callback(os.close, source)
        info = os.fstat(source)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise ValueError('NOTE_FILE_INVALID')
        raw = bytearray()
        while len(raw) <= MAX_BYTES:
            part = os.read(source, MAX_BYTES + 1 - len(raw))
            if not part:
                break
            raw.extend(part)
        if len(raw) > MAX_BYTES:
            raise ValueError('NOTE_FILE_LIMIT')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object)


def _utc_timestamp(value):
    if not isinstance(value, str) or UTC_TIME.fullmatch(value) is None:
        raise ValueError('NOTE_TIME_INVALID')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError('NOTE_TIME_INVALID')
    return parsed.timestamp()


def _validate(record, report, report_sha256, now):
    if not isinstance(record, dict) or set(record) != FIELDS or type(record['version']) is not int or record['version'] != 1:
        raise ValueError('NOTE_SCHEMA_INVALID')
    for field, expected in (('job_id', report['ca_job_id']), ('mint', report['mint']), ('report_sha256', report_sha256)):
        if not isinstance(record[field], str) or record[field] != expected:
            raise ValueError('NOTE_IDENTITY_INVALID')
    if HEX64.fullmatch(record['report_sha256']) is None or not isinstance(record['source_text_sha256'], str) or HEX64.fullmatch(record['source_text_sha256']) is None:
        raise ValueError('NOTE_HASH_INVALID')
    summary = record['summary']
    if (not isinstance(summary, str) or not 1 <= len(summary) <= 800 or not summary.strip()
            or any(unicodedata.category(char) in {'Cc', 'Cf', 'Cs'} for char in summary)):
        raise ValueError('NOTE_SUMMARY_INVALID')
    url = record['source_url']
    if (not isinstance(url, str) or not url.startswith('https://') or len(url) > 2048
            or any(ord(char) < 33 or char == '\\' for char in url) or '?' in url or '#' in url):
        raise ValueError('NOTE_SOURCE_INVALID')
    parsed = urlsplit(url)
    host = parsed.hostname
    if (parsed.scheme != 'https' or host not in HOSTS or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443) or parsed.netloc not in {host, host + ':443'}):
        raise ValueError('NOTE_SOURCE_INVALID')
    post = re.fullmatch(r'/([A-Za-z0-9_]{1,15})/status/([0-9]{1,25})/?', parsed.path)
    handle = record['author_handle']
    if (post is None or not isinstance(handle, str) or re.fullmatch(r'@[A-Za-z0-9_]{1,15}', handle) is None
            or handle[1:].lower() != post[1].lower()):
        raise ValueError('NOTE_AUTHOR_INVALID')
    narrative = report.get('narrative')
    rows = narrative.get('evidence') if isinstance(narrative, dict) else None
    allowed = {row.get('source_url') for row in rows if isinstance(row, dict) and isinstance(row.get('source_url'), str)} if isinstance(rows, list) else set()
    if url not in allowed:
        raise ValueError('NOTE_SOURCE_NOT_IN_REPORT')
    # A real browser read may precede or follow the chain report. Exact report
    # hash/source binding is independent of publication -> capture chronology.
    published = _utc_timestamp(record['published_at_utc'])
    captured = _utc_timestamp(record['captured_at_utc'])
    if (isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now)
            or not published <= captured <= now + 60):
        raise ValueError('NOTE_TIME_ORDER_INVALID')


def read_narrative_supplement(control_root: Path, report: dict, report_sha256: str, *, now=None):
    """Return a bounded local claim, never an official/interaction verification."""
    base = {'version': 1, 'status': 'NOT_RECORDED', 'job_id': report['ca_job_id'],
            'mint': report['mint'], 'report_sha256': report_sha256}
    try:
        record = _read_record(control_root, report['ca_job_id'])
        _validate(record, report, report_sha256, time.time() if now is None else now)
    except FileNotFoundError:
        return base
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return {**base, 'status': 'UNVERIFIED', 'reason': 'SUPPLEMENT_NOT_VERIFIED'}
    return {**record, 'status': 'BROWSER_OBSERVED_ACCOUNT_CLAIM', 'capture_method': 'MANUAL_BROWSER_READ',
            'official_recognition': 'UNVERIFIED', 'interaction_status': 'UNVERIFIED', 'earliest_origin': 'UNVERIFIED'}
