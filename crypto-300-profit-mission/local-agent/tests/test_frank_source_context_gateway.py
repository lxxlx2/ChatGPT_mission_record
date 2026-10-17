"""Explicit opt-in same-origin Dashboard gateway to already running research bridge.

All three localhost sources below are synthetic test fixtures: no production
DashboardState, private sidecar, real Solana RPC, Gmail, or trade requests.
"""
import json
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler

from mission_agent.mission_control.server import Handler as DashboardHandler
from test_frank_joint_readonly_http import (
    serving, sources, control_handler, make_f02
)
from scripts.frank_f02_readonly_positions_api import make_handler as f02_handler
from scripts.frank_joint_readonly_http import JointReadOnly, make_handler as joint_handler


def read(port, path="/api/research/current-follow-context", host=None):
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        headers = {} if host is None else {"Host": host}
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), json.loads(response.read())
    finally:
        conn.close()


def test_gateway_disabled_by_default_is_unavailable_without_network(monkeypatch):
    monkeypatch.delenv("FRANK_SOURCE_CONTEXT_PORT", raising=False)
    with serving(DashboardHandler) as dashboard:
        status, headers, doc = read(dashboard.server_port)
        assert status == 503
        assert doc["status"] == "RESEARCH_SOURCE_NOT_CONNECTED"
        assert "Access-Control-Allow-Origin" not in headers
        assert headers["Cache-Control"] == "no-store"
        assert read(dashboard.server_port, "?mint=not-allowed")[0] == 400
        assert read(dashboard.server_port, host="remote.example")[0] == 421


def test_gateway_only_accepts_explicit_loopback_port(monkeypatch):
    for bad in ("", "-1", "0", "65536", "0xF00", " 17777 ", "1" * 200):
        monkeypatch.setenv("FRANK_SOURCE_CONTEXT_PORT", bad)
        with serving(DashboardHandler) as dashboard:
            assert read(dashboard.server_port)[0] == 503


def test_native_three_upstream_http_bridge_to_existing_f01_page(monkeypatch, tmp_path):
    first, second, data = sources()
    data["f01"]["eligible"][0]["mint"] = second
    _, f02_service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, \
         serving(f02_handler(f02_service)) as f02:
        research = JointReadOnly(control_port=ctrl.server_port,
                                 f02_port=f02.server_port)
        with serving(joint_handler(research)) as bridge:
            monkeypatch.setenv("FRANK_SOURCE_CONTEXT_PORT", str(bridge.server_port))
            with serving(DashboardHandler) as dashboard:
                status, headers, doc = read(dashboard.server_port)
    assert status == 200
    assert headers["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in headers
    assert doc["candidate_count"] == 1
    assert doc["candidates"][0]["mint"] == second
    assert doc["candidates"][0]["f01_decision"] == "BUY"
    assert doc["candidates"][0]["observed_quantity"] == "0.000000"
    assert doc["candidates"][0]["review_required_reason"] == (
        "F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW")
    assert doc["combined_trade_permission"] is False
    assert doc["ca_query_executed"] is False
    assert doc["initiated_solana_rpc"] is False
    assert data["requests"] == ["/api/follow-opportunities"]
    assert first != second


def test_gateway_refuses_forged_combined_trade_permission(monkeypatch):
    class Forged(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            body = json.dumps({
                "schema_version": 1,
                "kind": "FRANK_CURRENT_F01_WITH_A05_RESEARCH_CONTEXT",
                "candidate_count": 0, "candidates": [],
                "combined_trade_permission": True,
                "archive_is_live_wallet_portfolio": False
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    with serving(Forged) as forged:
        monkeypatch.setenv("FRANK_SOURCE_CONTEXT_PORT", str(forged.server_port))
        with serving(DashboardHandler) as dashboard:
            code, _, out = read(dashboard.server_port)
    assert code == 503
    assert out["status"] == "RESEARCH_SOURCE_NOT_CONNECTED"
