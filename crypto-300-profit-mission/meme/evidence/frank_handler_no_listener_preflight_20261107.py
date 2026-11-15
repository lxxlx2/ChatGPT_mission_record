"""Exercise actual GET Handler without constructing a socket or listener."""
import hashlib
from http.client import HTTPMessage
import io
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True
os.environ['MISSION_EVIDENCE_EXPORT_ENABLED'] = '0'
os.environ['SOLANA_RPC_URLS'] = 'https://offline.invalid/rpc'
source, production, control = map(Path, sys.argv[1:4])
network_attempts = 0
socket_operations = 0


def audit(event, args):
    global network_attempts, socket_operations
    if event.startswith('socket.'):
        socket_operations += 1
        if event in {'socket.connect', 'socket.getaddrinfo'}:
            network_attempts += 1
        raise RuntimeError('IN_PROCESS_HANDLER_NO_SOCKET_ALLOWED')


sys.addaudithook(audit)
sys.path.insert(0, str(source))
from mission_agent.mission_control import server

state = server.DashboardState(production, control)


def get(route, headers=None):
    # No BaseHTTPRequestHandler constructor, socket or server instance: retain
    # the actual do_GET/_json/_file/send_response/send_header/end_headers code.
    handler = server.Handler.__new__(server.Handler)
    handler.state = state
    handler.static_root = source / 'mission_agent/mission_control/static'
    handler.path = route
    handler.command = 'GET'
    handler.requestline = 'GET ' + route + ' HTTP/1.1'
    handler.request_version = 'HTTP/1.1'
    handler.client_address = ('127.0.0.1', 0)
    handler.headers = HTTPMessage()
    handler.headers['Host'] = '127.0.0.1:8766'
    for key, value in (headers or {}).items():
        handler.headers[key] = value
    handler.rfile = io.BytesIO()
    handler.wfile = io.BytesIO()
    handler.close_connection = True
    handler.do_GET()
    raw = handler.wfile.getvalue()
    head, body = raw.split(b'\r\n\r\n', 1)
    status = int(head.split(b' ', 2)[1])
    assert status == 200
    return body


def js(route, headers=None):
    return json.loads(get(route, headers))


try:
    static = source / 'mission_agent/mission_control/static'
    assert get('/') == (static / 'index.html').read_bytes()
    assert get('/static/app.js') == (static / 'app.js').read_bytes()
    css_files = sorted(static.rglob('*.css'))
    assert css_files
    for css in css_files:
        assert get('/static/' + str(css.relative_to(static))) == css.read_bytes()
    runtime = js('/api/runtime')
    assert runtime['status'] == 'LIVE' and not runtime['source_drift'] and runtime['consecutive_errors'] == 0
    f = js('/api/follow-opportunities')
    assert f['schema_version'] == 2 and f['status'] == 'SOURCE_ONLY' and f['eligible'] == []
    assert not f['current_balance_verified']
    saved = 0
    for path in sorted((control / 'cluster-reports/_jobs').glob('*.json')):
        if path.name.endswith('.done.json'):
            continue
        report = json.loads(path.read_bytes())
        job, mint = report['ca_job_id'], report['mint']
        assert js('/api/cluster-analysis?' + urllib.parse.urlencode({'job_id': job}))['status'] == 'DONE'
        exact = js('/api/cluster-latest?' + urllib.parse.urlencode({'mint': mint, 'job_id': job}))
        assert exact == report
        saved += 1
    assert saved >= 2
    d1 = js('/api/frank-signed-activity?days=1')
    assert d1['status'] == 'INDEXED_LOCAL_ONLY'
    d2 = js('/api/frank-d2-at-slot', {'X-Frank-D2-Read': '1', 'Origin': 'http://127.0.0.1:8766'})
    assert d2['status'] == 'BALANCE_AT_OBSERVED_FINALIZED_SLOTS_NOT_LIVE'
    assert network_attempts == socket_operations == 0
    print(json.dumps({'status': 'PASS', 'mode': 'IN_PROCESS_HANDLER_NO_LISTENER',
                      'actual_Handler_GET': True, 'actual_response_serialization': True,
                      'html_js_match': True, 'css_match': True, 'css_assets_checked': len(css_files), 'exact_saved_jobs_read': saved,
                      'runtime_status': runtime['status'], 'scanner_pid': runtime['pid'], 'scanner_code_commit': runtime['code_commit'],
                      'source_recent_count': f['source_recent_count'], 'history_count': len(f['not_followed']),
                      'eligible_count': 0, 'D1_status': d1['status'], 'D2_status': d2['status'],
                      'external_network_attempts': network_attempts, 'socket_operations': socket_operations,
                      'listeners_started': 0, 'POSTs': 0, 'clean_exit': True}))
finally:
    state.cluster_jobs.executor.shutdown(wait=True)
    if state.cluster_jobs.evidence_executor:
        state.cluster_jobs.evidence_executor.shutdown(wait=True)
