"""Hermetic local GET-only direct-vs-proxy fault attribution (no Mac data)."""
from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
from pathlib import Path
import sys
import threading
import zipfile

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
diag = importlib.import_module("frank_decisions_readonly_diagnostic")


@contextmanager
def serve(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class LocalSource(BaseHTTPRequestHandler):
    status = 200
    payload = b"[]"
    requests = []

    def do_GET(self):
        type(self).requests.append((self.command, self.path))
        if self.path != "/api/decisions":
            self.send_error(404)
            return
        payload = type(self).payload
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        raise AssertionError("Unexpected POST to local source")

    def log_message(self, *_):
        pass


def test_direct_and_actual_qa_proxy_can_both_be_200():
    class Source(LocalSource):
        requests = []
        status = 200
        payload = b'[{"sample":"small"}]'
    with serve(Source) as source:
        report = diag.run_diagnostic(source.server_port, samples=2, spacing=0)
    assert report["summary"]["verdict"] == "NOT_REPRODUCED"
    assert report["summary"]["sample_count"] == 2
    assert len(Source.requests) == 4
    assert set(Source.requests) == {("GET", "/api/decisions")}
    assert [x["order"] for x in report["requests"]] == [
        ["direct", "proxy"], ["proxy", "direct"],
    ]
    assert all(x["direct"]["status"] == 200 and x["proxy"]["status"] == 200
               for x in report["requests"])
    assert all("body" not in x for x in report["requests"])
    assert report["body_or_decisions_recorded"] is False
    assert report["new_rpc"] is False


def test_oversize_direct_200_proxy_503_detected_using_real_proxy():
    class Large(LocalSource):
        requests = []
        status = 200
        payload = b'{"data":"' + b'x' * (diag.PROXY_CAP + 100) + b'"}'
    with serve(Large) as source:
        report = diag.run_diagnostic(source.server_port, samples=1, spacing=0)
    s = report["requests"][0]
    assert s["direct"]["status"] == 200
    assert s["direct"]["read_cap_reached"]
    assert s["proxy"]["status"] == 503
    assert report["summary"]["verdict"] == "PROXY_4MB_LIMIT_PROBABLE"
    assert report["summary"]["oversize_suspected_count"] == 1
    assert Large.requests == [("GET", "/api/decisions"), ("GET", "/api/decisions")]


def test_real_source_503_stays_distinct_from_proxy_failure():
    class Unavailable(LocalSource):
        requests = []
        status = 503
        payload = b'{"error":"source temporarily unavailable"}'
    with serve(Unavailable) as source:
        report = diag.run_diagnostic(source.server_port, samples=1, spacing=0)
    assert report["requests"][0]["direct"]["status"] == 503
    assert report["requests"][0]["proxy"]["status"] == 503
    assert report["summary"]["verdict"] == "DIRECT_SOURCE_ERROR_OBSERVED"


def test_source_vs_proxy_transient_classification():
    base = {
        "direct": {"status": 200, "elapsed_ms": 50, "bytes_read": 55, "declared_bytes": 55},
        "proxy": {"status": 503, "elapsed_ms": 61},
    }
    assert diag.classify_samples([base])["verdict"] == "PROXY_OR_INTERMITTENT_ERROR_UNRESOLVED"
    slow = {**base, "direct": {**base["direct"], "elapsed_ms": 3400}}
    assert diag.classify_samples([slow])["verdict"] == "PROXY_3S_TIMEOUT_POSSIBLE"
    assert diag.classify_samples([])["verdict"] == "NO_SAMPLES"


def test_private_zip_only_contains_metadata_and_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(diag, "uuid4", lambda: type("U", (), {"hex": "e" * 32})())
    sha = "a" * 40
    report = {
        "kind": "FRANK_DECISIONS_503_READONLY_DIRECT_VS_QA_PROXY",
        "requests": [{"direct":{"status":200, "bytes_read":145},
                      "proxy":{"status":503, "error_class":"TimeoutError"}}],
        "body_or_decisions_recorded": False,
    }
    out = diag.save_evidence(tmp_path, report, sha)
    original = out.read_bytes()
    with zipfile.ZipFile(out) as z:
        assert z.namelist() == ["diagnostic.json"]
        assert json.loads(z.read("diagnostic.json")) == report
    with pytest.raises(FileExistsError):
        diag.save_evidence(tmp_path, report, sha)
    assert out.read_bytes() == original


def test_sampling_limit_fails_closed():
    with pytest.raises(ValueError, match="INVALID_SAMPLING_LIMITS"):
        diag.run_diagnostic(8765, samples=0)
    with pytest.raises(ValueError, match="INVALID_SAMPLING_LIMITS"):
        diag.run_diagnostic(8765, samples=21)
