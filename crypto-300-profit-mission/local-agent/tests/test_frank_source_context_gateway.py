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
        body = response.read()
        try:
            doc = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            doc = {"non_json_error_page": True}
        return response.status, dict(response.getheaders()), doc
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
        assert read(dashboard.server_port, "/api/research/current-follow-context?mint=not-allowed")[0] == 400
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


def test_gateway_rejects_own_ephemeral_dashboard_port_before_connect(monkeypatch):
    """Bounded native HTTP probe: previously one bad port recursively dialed itself."""
    import time
    from mission_agent.mission_control import server as dashboard_module
    real_factory = dashboard_module.HTTPConnection
    attempted = []

    def counting_connection(*args, **kwargs):
        attempted.append(args)
        return real_factory(*args, **kwargs)

    monkeypatch.setattr(dashboard_module, "HTTPConnection", counting_connection)
    with serving(DashboardHandler) as dashboard:
        listen_port = dashboard.server_port
        assert 1024 <= listen_port <= 65535
        monkeypatch.setenv("FRANK_SOURCE_CONTEXT_PORT", str(listen_port))
        start = time.monotonic()
        code, headers, body = read(listen_port)
        elapsed = time.monotonic() - start
    assert code == 503 and body["status"] == "RESEARCH_SOURCE_NOT_CONNECTED"
    assert headers["Cache-Control"] == "no-store"
    assert attempted == [], "self-port must fail before any outbound HTTPConnection"
    assert elapsed < 1.5, "same port must not wait for the old 2.5s connection timeout"


def test_real_dashboard_follow_route_uses_reviewed_f01_partition(monkeypatch):
    """The actual /api/follow-opportunities route must exist before joint merges.

    No HTTP fake for the endpoint: real DashboardState policy and partition,
    with only the candidate list and runtime supplied as synthetic read inputs.
    """
    from types import SimpleNamespace
    from mission_agent.mission_control.server import DashboardState

    actual = object.__new__(DashboardState)
    actual.candidates = lambda: []
    actual.frank = SimpleNamespace(runtime=lambda: {"status": "LIVE"})
    computed = actual.follow_opportunities()
    assert computed["schema_version"] == 1
    assert computed["scope"] == "FRANK_FROZEN_DECISIONS_PRESENTATION_ONLY"
    assert computed["status"] == "OK"
    assert computed["eligible_count"] == 0 and computed["eligible"] == []
    assert computed["as_of_epoch"] > 0
    assert computed.get("read_only_policy_hash")

    class FakeState:
        def follow_opportunities(self):
            return actual.follow_opportunities()

    prior = DashboardHandler.state
    try:
        DashboardHandler.state = FakeState()
        with serving(DashboardHandler) as dashboard:
            status, headers, response = read(dashboard.server_port, "/api/follow-opportunities")
        assert status == 200
        assert headers["Cache-Control"] == "no-store"
        assert response["scope"] == "FRANK_FROZEN_DECISIONS_PRESENTATION_ONLY"
        assert response["status"] == "OK"
        assert response["eligible"] == []
    finally:
        DashboardHandler.state = prior


def test_native_dashboard_f01_positive_buy_and_wait_retains_exact_quote_provenance():
    """Real approved F01 partition + real Handler GET; only source rows are synthetic."""
    from types import SimpleNamespace
    import time
    from mission_agent.mission_control.server import DashboardState

    now = time.time() - 1
    first = "So11111111111111111111111111111111111111112"
    second = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    buy = {
        "person_id": "frank", "mint": first, "source_signal_id": "signal-live-1",
        "decision": "BUY", "position_state": "OPEN", "latest_side": "BUY",
        "pattern": "MULTIPLE", "current_raw": "100000",
        "latest_buy_at": now, "decision_created_at": now,
        "quote_observed_at": now,
        "decision_quote": {
            "status": "OK", "route_exists": True,
            "execution_price_usdc": "0.0125000",
            "price_impact_pct": "0.50",
        },
        "metrics": {
            "execution_price_usdc": "0.0125000",
            "price_impact_pct": "0.500",
        },
    }
    wait = {
        "person_id": "frank", "mint": second, "source_signal_id": "signal-wait",
        "decision": "WAIT", "position_state": "OPEN", "latest_side": "BUY",
        "pattern": "MULTIPLE", "current_raw": "100",
        "latest_buy_at": now, "decision_created_at": now,
        "quote_observed_at": now,
        "decision_quote": dict(buy["decision_quote"]),
        "metrics": dict(buy["metrics"]),
    }
    actual = object.__new__(DashboardState)
    actual.candidates = lambda: [buy, wait]
    actual.frank = SimpleNamespace(runtime=lambda: {"status": "LIVE"})
    computed = actual.follow_opportunities()
    assert computed["status"] == "OK"
    assert computed["eligible_count"] == 1
    assert len(computed["not_followed"]) == 1
    assert computed["not_followed"][0]["decision"] == "WAIT"
    eligible = computed["eligible"][0]
    assert eligible["mint"] == first
    assert eligible["source_signal_id"] == "signal-live-1"
    assert eligible["quote_observed_at"] == now
    assert eligible["validated_follow_quote"] == {
        "execution_price_usdc": "0.0125000",
        "price_impact_pct": "0.50",
    }

    class ActualReadOnlyState:
        def follow_opportunities(self):
            return actual.follow_opportunities()

    original = DashboardHandler.state
    try:
        DashboardHandler.state = ActualReadOnlyState()
        with serving(DashboardHandler) as dashboard:
            status, headers, payload = read(dashboard.server_port, "/api/follow-opportunities")
        assert status == 200
        assert headers["Cache-Control"] == "no-store"
        assert payload["eligible_count"] == 1
        assert payload["eligible"][0]["source_signal_id"] == "signal-live-1"
        assert payload["eligible"][0]["validated_follow_quote"] == eligible["validated_follow_quote"]
        assert payload["eligible"][0]["quote_observed_at"] == now
        assert payload["excluded_count"] == 1
    finally:
        DashboardHandler.state = original
