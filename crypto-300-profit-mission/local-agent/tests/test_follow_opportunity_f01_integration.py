"""F01 real local read-only source integration; no external notification calls."""
import json
import sqlite3
import time

from mission_agent.mission_control.server import DashboardState, Handler
from mission_agent.mission_control.service import MissionMemeService

from test_mission_control_service import make_prod, policy


def jupiter_quote(price):
    return {
        "status": "OK",
        "source": "JUPITER_OFFICIAL",
        "observed_at": time.time(),
        "input_usdc": "30",
        "execution_price_usdc": price,
        "price_impact_pct": "0.5",
        "route_exists": True,
    }


def test_current_display_is_derived_from_actual_cycle_without_changed_delivery(tmp_path):
    prod = tmp_path / "prod"
    control = tmp_path / "control"
    frozen = tmp_path / "frozen.json"
    make_prod(prod)
    policy(frozen)
    svc = MissionMemeService(production_root=prod, control_root=control,
                             policy_path=frozen)
    try:
        svc.jupiter.quote_usdc_to_token = lambda *a, **kw: jupiter_quote("1.02")
        cycle = svc.cycle()
        assert cycle["decision_events"][0]["decision"] == "BUY"
        before = [dict(row) for row in svc.control.db.execute(
            "SELECT * FROM decision_outbox ORDER BY rowid")]
        dashboard = DashboardState(prod, control)
        dashboard.frank.runtime = lambda: {"status": "LIVE"}
        source = dashboard.candidates()[0]
        assert source["decision"] == "BUY"
        assert source["quote_observed_at"] is not None
        result = dashboard.follow_opportunities()
        assert result["status"] == "OK"
        assert result["eligible_count"] == 1
        assert result["eligible"][0]["decision"] == "BUY"
        assert result["eligible"][0]["mint"] == source["mint"]
        after = [dict(row) for row in svc.control.db.execute(
            "SELECT * FROM decision_outbox ORDER BY rowid")]
        assert before == after
    finally:
        svc.close()


def test_real_legacy_source_with_latest_sell_must_leave_primary_panel(tmp_path):
    prod = tmp_path / "prod"
    control = tmp_path / "control"
    frozen = tmp_path / "frozen.json"
    make_prod(prod)
    policy(frozen)
    svc = MissionMemeService(production_root=prod, control_root=control,
                             policy_path=frozen)
    try:
        svc.jupiter.quote_usdc_to_token = lambda *a, **kw: jupiter_quote("1.02")
        svc.cycle()
        dashboard = DashboardState(prod, control)
        dashboard.frank.runtime = lambda: {"status": "LIVE"}
        old_read = dashboard.frank.candidates
        def after_sell():
            return [{**row, "latest_side": "SELL"} for row in old_read()]
        dashboard.frank.candidates = after_sell
        result = dashboard.follow_opportunities()
        assert result["eligible_count"] == 0
        assert result["not_followed"][0]["exclusion_reason"] == "LATEST_ACTION_NOT_BUY"
        assert result["not_followed"][0]["decision"] == "BUY"
    finally:
        svc.close()


def test_no_control_decision_cannot_create_fake_current_opportunity(tmp_path):
    prod = tmp_path / "prod"
    make_prod(prod)
    dashboard = DashboardState(prod, tmp_path / "no-control")
    dashboard.frank.runtime = lambda: {"status": "LIVE"}
    result = dashboard.follow_opportunities()
    assert result["eligible"] == []
    assert result["eligible_count"] == 0
    assert result["not_followed"][0]["decision"] == "UNASSESSED"


def test_server_ui_consumes_server_eligibility_and_keeps_exclusions_searchable():
    script = (Handler.static_root / "app.js").read_text(encoding="utf-8")
    html = (Handler.static_root / "index.html").read_text(encoding="utf-8")
    assert "get('/api/follow-opportunities')" in script
    assert "renderCandidates(activeCandidates,follow.status)" in script
    assert "renderNotFollowed(excludedCandidates,follow.status)" in script
    assert "id=\"not-followed-panel\"" in html
    assert "id=\"not-followed-count\"" in html
    assert "id=\"follow-opportunities\"" in html
