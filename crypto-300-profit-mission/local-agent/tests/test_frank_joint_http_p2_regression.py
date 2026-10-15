"""P2 regressions from independent PR70 review: real localhost TCP/bridge.

Never call live Solana RPC. Native F02 handler uses only synthetic source
wire and temporary research Sidecar; no production SQLite or POST.
"""
from copy import deepcopy
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import time

import pytest

from scripts.frank_f02_readonly_positions_api import make_handler as f02_handler
from scripts.frank_joint_readonly_http import JointReadOnly, make_handler
from test_frank_joint_readonly_http import make_f02, serving, sources


def upstream_handler(data, *, damaged_route=None, framing="correct"):
    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            route = ("f01" if self.path == "/api/follow-opportunities" else
                     "c02" if self.path.startswith("/api/cluster-latest?mint=")
                     else "missing")
            if route == "missing":
                self.send_error(404)
                return
            doc = deepcopy(data[route])
            if route == "f01" and doc.get("as_of_epoch") == "CURRENT_TEST_TIME":
                doc["as_of_epoch"] = time.time()
            raw = json.dumps(doc).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            if route != damaged_route or framing != "no_length":
                declared = (str(len(raw) + 100)
                            if route == damaged_route and framing == "early_eof"
                            else "-1" if route == damaged_route and framing == "negative"
                            else "bogus" if route == damaged_route and framing == "nonnumeric"
                            else "+10" if route == damaged_route and framing == "signed"
                            else "999999999" if route == damaged_route and framing == "oversized"
                            else str(len(raw)))
                self.send_header("Content-Length", declared)
            self.end_headers()
            self.wfile.write(raw)
            self.wfile.flush()
            self.close_connection = True

    return Upstream


def bridge_request(front, mint):
    conn = HTTPConnection("127.0.0.1", front.server_port, timeout=4)
    try:
        conn.request("GET", "/api/research/alignment?mint=" + mint)
        result = conn.getresponse()
        body = json.loads(result.read())
        return result.status, body
    finally:
        conn.close()


@pytest.mark.parametrize("route,framing", [
    ("f01", "early_eof"),
    ("c02", "early_eof"),
    ("f01", "negative"),
    ("c02", "negative"),
    ("f01", "nonnumeric"),
    ("c02", "signed"),
    ("f01", "no_length"),
    ("c02", "oversized"),
])
def test_partial_or_invalid_real_tcp_http_framing_never_trusted(
        tmp_path, route, framing):
    mint, _, data = sources()
    summary, f02 = make_f02(tmp_path)
    before = Path(summary["sidecar"]).read_bytes()
    with serving(upstream_handler(data, damaged_route=route,
                                  framing=framing)) as ctrl:
        with serving(f02_handler(f02)) as f02_server:
            join = JointReadOnly(control_port=ctrl.server_port,
                                 f02_port=f02_server.server_port)
            with serving(make_handler(join)) as front:
                code, body = bridge_request(front, mint)
    assert code == 200
    assert body["status"] == "PARTIAL_SOURCES"
    assert body["upstream"][route] == "SOURCE_UNAVAILABLE"
    assert body["alignment"][route]["status"] == (
        "F01_SOURCE_UNAVAILABLE" if route == "f01"
        else "CA_SOURCE_UNAVAILABLE")
    if route == "f01":
        assert body["alignment"]["f01"]["frozen_decision"] is None
        assert body["alignment"]["c02"]["status"] == (
            "CA_EXACT_MINT_IDENTITY_VERIFIED")
    else:
        assert body["alignment"]["f01"]["status"] == "F01_ELIGIBLE"
        assert body["alignment"]["c02"]["exact_mint_label"] is None
    assert body["alignment"]["f02"]["observed_quantity"] == "123.000000"
    assert body["combined_trade_permission"] is False
    assert Path(summary["sidecar"]).read_bytes() == before


@pytest.mark.parametrize("mutation", [
    "missing_eligible", "eligible_wrong_type", "eligible_wrong_count",
    "missing_eligible_count", "missing_excluded", "excluded_wrong_count",
    "eligible_bad_record", "scope_mismatch",
])
def test_missing_or_invalid_current_f01_partition_not_explicit_no_buy(
        tmp_path, mutation):
    mint, _, data = sources()
    data["f01"]["eligible"] = []
    data["f01"]["eligible_count"] = 0
    doc = data["f01"]
    if mutation == "missing_eligible":
        doc.pop("eligible")
    elif mutation == "eligible_wrong_type":
        doc["eligible"] = {}
    elif mutation == "eligible_wrong_count":
        doc["eligible_count"] = 1
    elif mutation == "missing_eligible_count":
        doc.pop("eligible_count")
    elif mutation == "missing_excluded":
        doc.pop("not_followed")
    elif mutation == "excluded_wrong_count":
        doc["excluded_count"] = 1
    elif mutation == "eligible_bad_record":
        doc["eligible"] = ["not-a-candidate"]
        doc["eligible_count"] = 1
    else:
        doc["scope"] = "SOME_OTHER_ENDPOINT"

    summary, f02 = make_f02(tmp_path)
    before = Path(summary["sidecar"]).read_bytes()
    with serving(upstream_handler(data)) as ctrl:
        with serving(f02_handler(f02)) as f02_server:
            join = JointReadOnly(control_port=ctrl.server_port,
                                 f02_port=f02_server.server_port)
            with serving(make_handler(join)) as front:
                code, body = bridge_request(front, mint)
    assert code == 200
    assert body["upstream"]["f01"] == "SOURCE_UNAVAILABLE"
    assert body["alignment"]["f01"]["status"] == "F01_SOURCE_UNAVAILABLE"
    assert body["alignment"]["f01"]["frozen_decision"] is None
    assert body["status"] == "PARTIAL_SOURCES"
    assert body["alignment"]["c02"]["status"] == "CA_EXACT_MINT_IDENTITY_VERIFIED"
    assert body["combined_trade_permission"] is False
    assert Path(summary["sidecar"]).read_bytes() == before


def test_genuinely_empty_native_f01_eligible_list_is_not_eligible(tmp_path):
    mint, _, data = sources()
    data["f01"]["eligible"] = []
    data["f01"]["eligible_count"] = 0
    summary, f02 = make_f02(tmp_path)
    with serving(upstream_handler(data)) as ctrl:
        with serving(f02_handler(f02)) as f02_server:
            join = JointReadOnly(control_port=ctrl.server_port,
                                 f02_port=f02_server.server_port)
            with serving(make_handler(join)) as front:
                code, body = bridge_request(front, mint)
    assert code == 200
    assert body["status"] == "EXISTING_ARCHIVED_SOURCES_ONLY"
    assert body["upstream"]["f01"] == "SOURCE_READ"
    assert body["alignment"]["f01"]["status"] == "F01_NOT_ELIGIBLE"
    assert body["alignment"]["f01"]["frozen_decision"] is None
    assert body["combined_trade_permission"] is False
