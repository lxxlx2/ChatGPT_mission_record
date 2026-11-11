"""Private browser notes are bounded claims, never mutations or source reads."""
import hashlib
from http.client import HTTPMessage
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
from types import SimpleNamespace
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
import urllib.request

import pytest

from mission_agent.mission_control.narrative_supplement import MAX_BYTES, read_narrative_supplement
from mission_agent.mission_control.server import ClusterJobManager, Handler

JOB = 'a' * 32
MINT = 'So11111111111111111111111111111111111111112'
OTHER_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
URL = 'https://x.com/matthewabides/status/2106506213458341960'
NOW = time.time()


def utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace('+00:00', 'Z')


@pytest.fixture
def saved(tmp_path):
    control = tmp_path / 'control'
    manager = ClusterJobManager(control)
    report = {'schema_version': 2, 'source': 'SOLANA_FINALIZED_JSON_RPC', 'ca_job_id': JOB,
              'mint': MINT, 'observed_at': NOW - 60, 'coverage': {}, 'holders': [],
              'metrics': {}, 'assessment': {}, 'token_profile': {}, 'limitations': [],
              'narrative': {'evidence': [{'source_url': URL}]},
              'execution_quote_30_usdc': {'legacy_fixture': True}}
    folder = control / 'cluster-reports/_jobs'
    folder.mkdir(parents=True)
    raw = json.dumps(report, sort_keys=True).encode()
    digest = hashlib.sha256(raw).hexdigest()
    (folder / (JOB + '.json')).write_bytes(raw)
    (folder / (JOB + '.done.json')).write_text(json.dumps({
        'version': 1, 'status': 'DONE', 'ca_job_id': JOB, 'mint': MINT, 'report_sha256': digest,
    }))
    record = {'version': 1, 'job_id': JOB, 'mint': MINT, 'report_sha256': digest,
              'source_url': URL, 'author_handle': '@matthewabides',
              'published_at_utc': utc(NOW - 1000), 'captured_at_utc': utc(NOW - 10),
              'summary': '该账号自述：爬虫读取加密网页，以采集文本训练模型并计划开放权重。',
              'source_text_sha256': 'b' * 64}
    note = control / 'cluster-source-notes' / JOB / 'narrative.json'
    yield SimpleNamespace(control=control, manager=manager, report=report,
                          digest=digest, record=record, note=note, folder=folder)
    manager.executor.shutdown(wait=True)
    if manager.evidence_executor:
        manager.evidence_executor.shutdown(wait=True)


def write_note(saved, record=None):
    saved.note.parent.mkdir(parents=True, exist_ok=True)
    saved.note.write_text(json.dumps(saved.record if record is None else record, ensure_ascii=True))


def read_note(saved):
    return read_narrative_supplement(saved.control, saved.report, saved.digest, now=NOW)


def request(saved, query=None):
    handler = Handler.__new__(Handler)
    handler.state = SimpleNamespace(cluster_jobs=saved.manager)
    handler.path = '/api/cluster-narrative-supplement?' + (
        urlencode({'mint': MINT, 'job_id': JOB}) if query is None else query)
    handler.command = 'GET'
    handler.requestline = 'GET ' + handler.path + ' HTTP/1.1'
    handler.request_version = 'HTTP/1.1'
    handler.client_address = ('127.0.0.1', 0)
    handler.headers = HTTPMessage()
    handler.headers['Host'] = '127.0.0.1:8766'
    handler.rfile = io.BytesIO()
    handler.wfile = io.BytesIO()
    handler.close_connection = True
    handler.do_GET()
    head, body = handler.wfile.getvalue().split(b'\r\n\r\n', 1)
    return int(head.split(b' ', 2)[1]), json.loads(body)


def test_recorded_claim_has_exact_fixed_scope_and_original_raw_digest(saved):
    write_note(saved)
    result = read_note(saved)
    assert len(result) == 15
    assert result['status'] == 'BROWSER_OBSERVED_ACCOUNT_CLAIM'
    assert result['capture_method'] == 'MANUAL_BROWSER_READ'
    for key in ('official_recognition', 'interaction_status', 'earliest_origin'):
        assert result[key] == 'UNVERIFIED'
    assert result['report_sha256'] == saved.digest
    assert 'execution_quote_30_usdc' not in saved.manager._saved_job_report(JOB)
    assert saved.manager._saved_job_report_with_digest(JOB)[1] == saved.digest
    assert request(saved) == (200, result)


def test_missing_note_is_unrecorded_without_creating_directories(saved):
    status, result = request(saved)
    assert status == 200
    assert result == {'version': 1, 'status': 'NOT_RECORDED', 'job_id': JOB,
                      'mint': MINT, 'report_sha256': saved.digest}
    assert not (saved.control / 'cluster-source-notes').exists()


@pytest.mark.parametrize('field,value', [
    ('version', True), ('version', 1.0), ('job_id', 'c' * 32), ('mint', OTHER_MINT),
    ('report_sha256', 'd' * 64), ('source_text_sha256', 'not-a-hash'),
    ('summary', ''), ('summary', '   '), ('summary', 'x' * 801),
    ('summary', 'claim\x00hidden'), ('summary', 'claim\u202ehidden'),
    ('summary', 'claim\nsecond line'), ('summary', '\ud800'),
    ('author_handle', '@elonmusk'), ('author_handle', 'matthewabides'),
    ('source_url', 'https://x.com/elonmusk/status/123'),
    ('source_url', URL + '?tracking=1'), ('source_url', URL + '#claim'),
    ('source_url', URL + '?'), ('source_url', URL + '#'),
    ('source_url', URL.replace('https://', 'http://')),
    ('source_url', URL.replace('x.com', 'x.com.evil.example')),
    ('source_url', URL.replace('x.com', 'private@x.com')),
    ('source_url', URL.replace('x.com', 'x.com:444')),
    ('source_url', URL.replace('x.com', 'X.COM')),
    ('source_url', URL.replace('x.com', 'x.com.')),
    ('published_at_utc', '2026-10-03T22:06:32'),
    ('published_at_utc', '2026-10-03T22:06:32+01:00'),
    ('published_at_utc', '2026-10-03T22:06:32-00:00'),
    ('published_at_utc', utc(NOW + 100)),
    ('captured_at_utc', utc(NOW + 61)), ('captured_at_utc', utc(NOW - 1001)),
])
def test_invalid_record_withholds_claim_instead_of_echoing_data(saved, field, value):
    record = dict(saved.record)
    record[field] = value
    write_note(saved, record)
    result = read_note(saved)
    assert result == {'version': 1, 'status': 'UNVERIFIED', 'job_id': JOB,
                      'mint': MINT, 'report_sha256': saved.digest,
                      'reason': 'SUPPLEMENT_NOT_VERIFIED'}


@pytest.mark.parametrize('field', ['official_verified', 'official_recognition', 'interaction_status', 'capture_method'])
def test_producer_cannot_add_verification_or_scope_flags(saved, field):
    record = dict(saved.record, **{field: 'VERIFIED'})
    write_note(saved, record)
    assert read_note(saved)['status'] == 'UNVERIFIED'


@pytest.mark.parametrize('url', [
    URL.replace('x.com', 'twitter.com'), URL.replace('x.com', 'www.x.com'),
    URL.replace('x.com', 'www.twitter.com'), URL.replace('x.com', 'x.com:443'), URL + '/',
])
def test_allowed_url_shape_still_requires_exact_report_source_membership(saved, url):
    record = dict(saved.record, source_url=url, author_handle='@MatthewAbides')
    write_note(saved, record)
    assert read_note(saved)['status'] == 'UNVERIFIED'
    saved.report['narrative']['evidence'][0]['source_url'] = url
    assert read_note(saved)['status'] == 'BROWSER_OBSERVED_ACCOUNT_CLAIM'


@pytest.mark.parametrize('kind', ['oversized', 'utf8', 'duplicate_key', 'not_object'])
def test_invalid_private_file_has_only_fixed_error(saved, kind):
    write_note(saved)
    if kind == 'oversized':
        saved.note.write_bytes(b' ' * (MAX_BYTES + 1))
    elif kind == 'utf8':
        saved.note.write_bytes(b'\xff')
    elif kind == 'duplicate_key':
        saved.note.write_text(saved.note.read_text().replace('"version": 1', '"version": 1, "version": 1'))
    else:
        saved.note.write_text('[]')
    status, result = request(saved)
    assert status == 200 and result['status'] == 'UNVERIFIED'
    assert result['reason'] == 'SUPPLEMENT_NOT_VERIFIED'
    assert str(saved.control) not in json.dumps(result)


@pytest.mark.parametrize('component', ['file', 'job_directory', 'notes_directory', 'control_directory'])
def test_note_path_does_not_follow_symlinks(saved, tmp_path, component):
    write_note(saved)
    target = tmp_path / 'moved'
    if component == 'file':
        saved.note.rename(target)
        saved.note.symlink_to(target)
        result = read_note(saved)
    elif component == 'job_directory':
        saved.note.parent.rename(target)
        saved.note.parent.symlink_to(target, target_is_directory=True)
        result = read_note(saved)
    elif component == 'notes_directory':
        directory = saved.control / 'cluster-source-notes'
        directory.rename(target)
        directory.symlink_to(target, target_is_directory=True)
        result = read_note(saved)
    else:
        alias = tmp_path / 'control-link'
        alias.symlink_to(saved.control, target_is_directory=True)
        result = read_narrative_supplement(alias, saved.report, saved.digest, now=NOW)
    assert result['status'] == 'UNVERIFIED'


def test_nonregular_note_is_rejected_without_waiting_for_a_writer(saved):
    saved.note.parent.mkdir(parents=True)
    os.mkfifo(saved.note)
    assert read_note(saved)['status'] == 'UNVERIFIED'


@pytest.mark.parametrize('query', [
    '', 'mint=' + MINT, 'job_id=' + JOB,
    urlencode({'mint': MINT, 'job_id': JOB}) + '&other=1',
    'mint=' + MINT + '&mint=' + MINT + '&job_id=' + JOB,
    'mint=' + MINT + '&job_id=' + JOB + '&job_id=' + JOB,
    'mint=&job_id=' + JOB, 'mint=' + MINT + '&job_id=',
    'mint=bad&job_id=' + JOB, 'mint=' + MINT + '&job_id=../private',
])
def test_query_requires_exact_single_valid_job_and_mint(saved, query):
    assert request(saved, query) == (400, {'error': 'INVALID_NARRATIVE_SUPPLEMENT_QUERY'})


@pytest.mark.parametrize('case', ['other_mint', 'other_job', 'missing_done', 'bad_digest', 'changed_report'])
def test_only_valid_exact_done_report_can_bind_a_note(saved, case):
    write_note(saved)
    query = None
    if case == 'other_mint':
        query = urlencode({'mint': OTHER_MINT, 'job_id': JOB})
    elif case == 'other_job':
        query = urlencode({'mint': MINT, 'job_id': 'e' * 32})
    elif case == 'missing_done':
        (saved.folder / (JOB + '.done.json')).unlink()
    elif case == 'bad_digest':
        marker = saved.folder / (JOB + '.done.json')
        value = json.loads(marker.read_text());value['report_sha256'] = 'f' * 64
        marker.write_text(json.dumps(value))
    else:
        (saved.folder / (JOB + '.json')).write_text('{}')
    assert request(saved, query) == (404, {'error': 'CA_REPORT_NOT_FOUND'})


def test_actual_get_handler_performs_no_collection_db_access_or_file_writes(saved, monkeypatch):
    write_note(saved)
    before = {str(p.relative_to(saved.control)): p.read_bytes() for p in saved.control.rglob('*') if p.is_file()}
    def denied(*args, **kwargs):
        raise AssertionError('NO_COLLECTION_OR_MUTATION')
    for name in ('submit', 'resume', 'get', 'latest'):
        monkeypatch.setattr(saved.manager, name, denied)
    monkeypatch.setattr(socket, 'socket', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(urllib.request, 'urlopen', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr(Path, 'write_text', denied)
    monkeypatch.setattr(Path, 'write_bytes', denied)
    monkeypatch.setattr(Path, 'mkdir', denied)
    original_open = os.open
    def readonly_open(path, flags, *args, **kwargs):
        assert flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND) == 0
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(os, 'open', readonly_open)
    assert request(saved)[0] == 200
    after = {str(p.relative_to(saved.control)): p.read_bytes() for p in saved.control.rglob('*') if p.is_file()}
    assert before == after


@pytest.mark.parametrize('seconds_before_report', [1, 300, 86400])
def test_true_browser_read_before_report_remains_bound_and_preserves_time(saved, seconds_before_report):
    captured = saved.report['observed_at'] - seconds_before_report
    record = dict(saved.record, published_at_utc=utc(captured - 60), captured_at_utc=utc(captured))
    write_note(saved, record)
    before = (saved.folder / (JOB + '.json')).read_bytes()
    status, result = request(saved)
    assert status == 200 and result['status'] == 'BROWSER_OBSERVED_ACCOUNT_CLAIM'
    assert result['captured_at_utc'] == record['captured_at_utc']
    assert result['report_sha256'] == saved.digest
    assert result['official_recognition'] == result['interaction_status'] == result['earliest_origin'] == 'UNVERIFIED'
    assert (saved.folder / (JOB + '.json')).read_bytes() == before
