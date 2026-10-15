"""Real localhost F01/C02 GETs and native isolated F02 HTTP, no live RPC."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

from scripts import frank_joint_readonly_http as joint
from scripts.frank_f02_manual_refresh import refresh_session
from scripts.frank_f02_readonly_positions_api import make_handler as f02_handler
from scripts.frank_reconcile_frozen32_offline import load_frozen_roster, ROSTER
from test_frank_f02_manual_refresh import reader, WALLET


@contextmanager
def serving(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def control_handler(data):
    class Control(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            data["requests"].append(self.path)
            if self.path == "/api/follow-opportunities":
                doc = dict(data["f01"])
                if doc.get("as_of_epoch") == "CURRENT_TEST_TIME":
                    doc["as_of_epoch"] = time.time()
            elif self.path.startswith("/api/cluster-latest?mint="):
                doc = data["c02"]
            else:
                self.send_error(404)
                return
            if doc is None:
                self.send_response(404)
                self.end_headers()
                return
            raw = json.dumps(doc).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            data["requests"].append("POST:" + self.path)
            self.send_error(405)

    return Control


def sources():
    mint = load_frozen_roster(ROSTER, WALLET)["records"][0]["mint"]
    other = load_frozen_roster(ROSTER, WALLET)["records"][1]["mint"]
    data = {
        "requests": [],
        "f01": {
            "schema_version": 1,
            "scope": "FRANK_FROZEN_DECISIONS_PRESENTATION_ONLY",
            "status": "OK", "as_of_epoch": "CURRENT_TEST_TIME",
            "eligible_count": 1, "excluded_count": 0,
            "not_followed": [],
            "eligible": [{"mint": mint, "person_id": "frank",
                          "decision": "BUY", "source_signal_id": "approved-1"}],
        },
        "c02": {
            "mint": mint, "chain": "solana",
            "token_identity": {
                "identity_status": "VERIFIED",
                "conflict_status": "NO_CONFLICT_OBSERVED",
                "display_label": "Verified Contract Label",
            },
            "assessment": {"narrative_status": "UNVERIFIED"},
        },
    }
    return mint, other, data


def make_f02(tmp_path):
    wire, calls = reader()
    summary, service = refresh_session(session_root=tmp_path / "isolated",
                                       read_raw=wire)
    assert summary["status"] == "VERIFIED_MANUAL_RESEARCH_SESSION"
    assert len(calls) == 2
    return summary, service


def test_real_http_bridge_existing_get_sources_and_zero_identity(tmp_path):
    mint, other, data = sources()
    summary, service = make_f02(tmp_path)
    before = Path(summary["sidecar"]).read_bytes()
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        bridge = joint.JointReadOnly(control_port=ctrl.server_port,
                                     f02_port=f02.server_port)
        with serving(joint.make_handler(bridge)) as front:
            conn = HTTPConnection("127.0.0.1", front.server_port, timeout=3)
            conn.request("GET", "/api/research/alignment?mint=" + mint)
            res = conn.getresponse()
            doc = json.loads(res.read())
            assert res.status == 200
            assert res.getheader("Cache-Control") == "no-store, max-age=0"
            assert res.getheader("Access-Control-Allow-Origin") is None
            assert doc["status"] == "EXISTING_ARCHIVED_SOURCES_ONLY"
            assert doc["upstream"] == {
                "f01": "SOURCE_READ", "c02": "ARCHIVED_REPORT_READ",
                "f02": "SOURCE_READ"}
            view = doc["alignment"]
            assert view["f01"]["status"] == "F01_ELIGIBLE"
            assert view["f01"]["frozen_decision"] == "BUY"
            assert view["f02"]["state"] == "OPEN_ACCOUNT_NONZERO"
            assert view["f02"]["observed_quantity"] == "123.000000"
            assert view["c02"]["status"] == "CA_EXACT_MINT_IDENTITY_VERIFIED"
            assert view["c02"]["narrative_status"] == "UNVERIFIED"
            assert doc["combined_trade_permission"] is False
            assert doc["ca_query_executed"] is False
            assert doc["initiated_solana_rpc"] is False
            assert doc["writes_production_sqlite"] is False

            conn.request("GET", "/api/research/alignment?mint=" + other)
            res = conn.getresponse()
            alt = json.loads(res.read())["alignment"]
            assert alt["f01"]["status"] == "F01_NOT_ELIGIBLE"
            assert alt["f02"]["state"] == "OPEN_ACCOUNT_ZERO"
            assert alt["f02"]["observed_quantity"] == "0.000000"
            assert alt["c02"]["status"] == "CA_MINT_MISMATCH"

            conn.request("POST", "/api/research/alignment?mint=" + mint,
                         body="{}", headers={"Content-Type": "application/json"})
            res = conn.getresponse()
            assert res.status == 405
            res.read()
            conn.request("GET", "/api/research/alignment?mint=NotSolanaCA")
            res = conn.getresponse()
            assert res.status == 400
            res.read()
            conn.request("GET", "/api/research/alignment?mint=" + mint,
                         headers={"Host": "evil.example.com"})
            res = conn.getresponse()
            assert res.status == 421
            res.read()
            conn.close()
    assert Path(summary["sidecar"]).read_bytes() == before
    assert data["requests"] == [
        "/api/follow-opportunities",
        "/api/cluster-latest?mint=" + mint,
        "/api/follow-opportunities",
        "/api/cluster-latest?mint=" + other,
    ]
    assert not any("POST:" in path for path in data["requests"])


def test_unqueried_ca_is_not_analysed_or_auto_posted(tmp_path):
    mint, _, data = sources()
    data["c02"] = None
    _, service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        result = joint.JointReadOnly(control_port=ctrl.server_port,
                                     f02_port=f02.server_port).query(mint)
    assert result["status"] == "CA_NOT_QUERIED"
    assert result["upstream"]["c02"] == "NOT_QUERIED"
    assert result["alignment"]["c02"]["status"] == "CA_NOT_QUERIED"
    assert result["alignment"]["f02"]["state"] == "OPEN_ACCOUNT_NONZERO"
    assert not any(path.startswith("POST") for path in data["requests"])


def test_unavailable_F01_never_masquerades_as_explicit_no_buy(tmp_path):
    mint, _, data = sources()
    data["f01"]["as_of_epoch"] = time.time() - 600
    _, service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        out = joint.JointReadOnly(control_port=ctrl.server_port,
                                  f02_port=f02.server_port).query(mint)
    assert out["status"] == "PARTIAL_SOURCES"
    assert out["alignment"]["f01"]["status"] == "F01_SOURCE_UNAVAILABLE"
    assert out["alignment"]["f01"]["frozen_decision"] is None
    assert out["alignment"]["c02"]["status"] == "CA_EXACT_MINT_IDENTITY_VERIFIED"
    assert out["combined_trade_permission"] is False


def test_stale_native_f02_service_cannot_resurrect_old_quantity(tmp_path):
    mint, _, data = sources()
    _, service = make_f02(tmp_path)
    observed = datetime.fromisoformat(service.positions()["capture_observed_at_utc"])
    original = service.positions
    service.positions = lambda: original(
        as_of_utc=observed + timedelta(seconds=301))
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        out = joint.JointReadOnly(control_port=ctrl.server_port,
                                  f02_port=f02.server_port).query(mint)
    assert out["upstream"]["f02"] == "SOURCE_READ"
    assert out["alignment"]["f02"]["state"] == "SOURCE_UNAVAILABLE"
    assert out["alignment"]["f02"]["observed_quantity"] is None
    assert out["alignment"]["f01"]["status"] == "F01_ELIGIBLE"
    assert out["combined_trade_permission"] is False


def test_refused_local_port_and_no_default_network(tmp_path, capsys):
    mint, _, _ = sources()
    _, service = make_f02(tmp_path)
    with serving(f02_handler(service)) as f02:
        out = joint.JointReadOnly(control_port=9,
                                  f02_port=f02.server_port).query(mint)
        assert out["status"] == "PARTIAL_SOURCES"
        assert out["upstream"]["f01"] == "SOURCE_UNAVAILABLE"
        assert out["upstream"]["c02"] == "SOURCE_UNAVAILABLE"
        assert out["alignment"]["f01"]["status"] == "F01_SOURCE_UNAVAILABLE"
        assert out["alignment"]["c02"]["status"] == "CA_SOURCE_UNAVAILABLE"
        assert out["alignment"]["f02"]["observed_quantity"] == "123.000000"
    assert joint.main([]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["status"] == "PLAN_ONLY"
    assert plan["network_invoked"] is False
    assert joint.valid_solana_mint(mint)
    assert not joint.valid_solana_mint(mint + "0")
    assert not joint.valid_solana_mint(mint[:-1] + "0")
    assert not joint.valid_solana_mint("So11111111111111111111111111111111111111112" * 2)
