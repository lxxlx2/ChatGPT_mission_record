"""F02-R2: real loopback HTTP browser page and independent static resources."""
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading

from scripts.frank_f02_readonly_positions_api import make_handler
import pytest
import test_frank_f02_r1_readonly_positions_api as upstream_fixtures


@pytest.fixture
def source(tmp_path):
    return upstream_fixtures.source.__wrapped__(tmp_path)


@pytest.fixture
def service(source):
    return upstream_fixtures.service.__wrapped__(source)


def get(port, path, host=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {} if host is None else {"Host": host}
    conn.request("GET", path, headers=headers)
    response = conn.getresponse()
    result = response.status, dict(response.getheaders()), response.read()
    conn.close()
    return result


def test_f02_actual_loopback_browser_resources_and_stale_source(service):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        port = httpd.server_port
        status, h, page = get(port, "/research/positions")
        assert status == 200
        assert h["Content-Type"] == "text/html; charset=utf-8"
        assert h["Cache-Control"] == "no-store"
        assert h["X-Frame-Options"] == "DENY"
        assert h["Referrer-Policy"] == "no-referrer"
        assert "default-src 'none'" in h["Content-Security-Policy"]
        assert "connect-src 'self'" in h["Content-Security-Policy"]
        assert "script-src 'self'" in h["Content-Security-Policy"]
        assert "Access-Control-Allow-Origin" not in h
        assert b'/research/positions.js' in page
        assert b'/research/positions.css' in page
        assert b'id="position-rows"' in page
        assert b'<script>' not in page

        status, h, js = get(port, "/research/positions.js")
        assert status == 200 and h["Cache-Control"] == "no-store"
        assert h["Content-Type"] == "text/javascript; charset=utf-8"
        assert b'window.FrankF02Contract' in js
        assert b'innerHTML' not in js
        assert b'document.createElement' in js
        assert b'fetch(API,' in js

        status, h, css = get(port, "/research/positions.css")
        assert status == 200 and b".stats" in css
        assert h["Content-Type"] == "text/css; charset=utf-8"

        status, h, data = get(port, "/api/research/positions")
        assert status == 200 and h["Cache-Control"] == "no-store"
        payload = json.loads(data)
        assert payload["target_mint_count"] == 32
        assert payload["readiness"] == "STALE_ARCHIVED_SOURCE"
        assert payload["state_counts"] == {"SOURCE_UNAVAILABLE": 32}
        assert all(m["observed_raw_amount"] is None for m in payload["mints"])
        assert b"9007199254741000" not in page
        assert b"9007199254741000" not in data
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_f02_host_and_fixed_route_scope(service):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        port = httpd.server_port
        for path in ("/research/other", "/api/candidates"):
            status, _, data = get(port, path)
            assert status == 404
            assert json.loads(data) == {"status": "NOT_FOUND"}
        for path in ("/research/positions", "/research/positions.js", "/api/research/positions"):
            status, _, data = get(port, path, host="untrusted.test")
            assert status == 403
            assert json.loads(data) == {"status": "LOCALHOST_ONLY"}
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_f02_browser_does_not_modify_isolated_sidecar(service, source):
    original = Path(source["sidecar"]).read_bytes()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        for path in ("/research/positions", "/research/positions.js",
                     "/research/positions.css", "/api/research/positions"):
            assert get(httpd.server_port, path)[0] == 200
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
    assert Path(source["sidecar"]).read_bytes() == original
