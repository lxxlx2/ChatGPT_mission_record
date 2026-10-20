"""Option 3 P3/P4 only: source-only Dashboard integration and dated archive replay.

No RPC, market lookup, notification provider, production DB or macOS operations.
"""
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from mission_agent.mission_control import server
from mission_agent.mission_control.intelligence_preview import analyze_rows, render_html

ARCHIVE = Path(__file__).resolve().parents[2] / "meme" / "evidence"
BKK = ZoneInfo("Asia/Bangkok")
MINT = "4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta"
SIGNATURE = "5yJ2AbcfMNPqwxyz123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghi"


def _candidate():
    return {
        "mint": MINT, "pattern": "ACCUMULATION",
        "source_signal_id": "source-1", "source_signal_at": 1_600,
        "latest_side": "SELL", "latest_at": 1_850,
        "latest_signature": SIGNATURE, "latest_buy_at": 1_700,
        "latest_buy_price_usdc": "0.01",
        "latest_buy_price_status": "USDC_DIRECT",
        "buy_count": 2, "sell_count": 1, "position_state": "CLOSED",
    }


def test_integrated_state_reads_exact_existing_frank_facts_without_new_market_calls(monkeypatch):
    monkeypatch.setattr(server.time, "time", lambda: 2000.0)
    state = server.DashboardState.__new__(server.DashboardState)
    count = []
    state.frank = SimpleNamespace(candidates=lambda: (count.append("read"), [_candidate()])[1])
    result = state.frank_intelligence()
    assert count == ["read"]
    assert result["status"] == "LOCAL_SOURCE_RESEARCH_ONLY"
    assert result["market_reference"] == "NOT_REQUESTED"
    assert result["live_notification_authorized"] is False
    assert result["scope"] == "FRANK_INDEX_ONLY_NOT_COMPLETE_CHAIN_OR_CURRENT_BALANCE"
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert "FRANK_SELL_OBSERVED_REVIEW_RISK" in row["facts"]
    assert row["latest_side"] == "SELL"
    assert row["model_episode_position_state"] == "CLOSED"
    assert row["price"]["status"] == "PRICE_UNAVAILABLE"
    assert row["price"]["change_pct_vs_last_verified_buy"] is None
    assert row["order_amount_usdc"] is None
    assert row["alert_delivery_authorized"] is False


def test_source_failure_is_unavailable_and_cannot_become_zero_wallet_activity(monkeypatch):
    monkeypatch.setattr(server.time, "time", lambda: 2000.0)
    state = server.DashboardState.__new__(server.DashboardState)
    def inaccessible():
        raise OSError("offline")
    state.frank = SimpleNamespace(candidates=inaccessible)
    result = state.frank_intelligence()
    assert result["status"] == "SOURCE_UNAVAILABLE"
    assert result["reason"] == "LOCAL_FRANK_SOURCE_UNAVAILABLE"
    assert result["market_reference"] == "NOT_REQUESTED"


def test_invalid_candidate_fails_closed_rather_than_silently_skipping():
    state = server.DashboardState.__new__(server.DashboardState)
    state.frank = SimpleNamespace(candidates=lambda: [{"mint": ""}])
    result = state.frank_intelligence()
    assert result["status"] == "SOURCE_UNAVAILABLE"
    assert result["reason"] == "LOCAL_FRANK_SOURCE_UNAVAILABLE"


def test_new_route_is_restricted_to_read_only_queryless_local_source():
    handler = server.Handler.__new__(server.Handler)
    handler._allowed_host = lambda: True
    handler._json = lambda payload, status=200: (payload, status)
    handler.state = SimpleNamespace(frank_intelligence=lambda: {"status": "TEST_ONLY"})
    handler.path = "/api/frank-intelligence"
    assert handler.do_GET() == ({"status": "TEST_ONLY"}, 200)
    handler.path = "/api/frank-intelligence?market=live"
    assert handler.do_GET() == ({"error": "UNSUPPORTED_INTELLIGENCE_QUERY"}, 400)
    handler._allowed_host = lambda: False
    handler.send_error = lambda code, reason: (code, reason)
    handler.path = "/api/frank-intelligence"
    assert handler.do_GET()[0] == 421


def test_html_and_browser_bind_into_existing_dashboard_without_touching_old_senders():
    static = Path(server.__file__).parent / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    js = (static / "app.js").read_text(encoding="utf-8")
    assert 'id="frank-intelligence-panel"' in html
    assert 'id="frank-intelligence-cards"' in html
    assert "get('/api/frank-intelligence')" in js
    assert "refreshFrankIntelligence();" in js
    assert "setInterval(refreshFrankIntelligence,60000)" in js
    assert "get('/api/candidates')" in js
    assert "get('/api/frank-signed-activity?days='" in js
    assert "get('/api/frank-observed-watchlist')" in js


def test_twelve_genuine_archival_observations_render_with_no_future_outcomes():
    lots = json.loads((ARCHIVE / "frank-six-observed-roundtrips-2026-10-10.json").read_text())
    balances = json.loads((ARCHIVE / "frank-d0-six-mint-finalized-2026-10-11.json").read_text())
    assert len(lots["case_results"]) == len(balances["records"]) == 6
    assert len({x["mint"] for x in lots["case_results"]}) == 6

    # Six genuine dated trade-lot references at trigger time: the original
    # later exit outcome/net delta is intentionally never given to the engine.
    for lot in lots["case_results"]:
        at = datetime.strptime(lot["signal_trigger_bkk"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=BKK).timestamp()
        after = datetime.strptime(lot["exit_last_bkk"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=BKK).timestamp()
        assert at < after
        output = analyze_rows(
            [{"mint": lot["mint"], "pattern": "UNKNOWN", "latest_side": "UNKNOWN",
              "latest_at": at}],
            as_of=at, max_market_age_seconds=300,
        )[0]
        html = render_html([output], as_of=at, simulated_updates=[])
        assert lot["mint"] in html
        assert "MARKET_REFERENCE_MISSING" in html
        assert output["latest_signature"] is None
        assert "FRANK_SELL_OBSERVED_REVIEW_RISK" not in output["facts"]
        assert output["price"]["change_pct_vs_last_verified_buy"] is None
        assert lot["net_margin_usdc"] not in html

    # Six later real finalized balance observations: even a nonzero quantity
    # is neither a new signed buy nor a current price or full-wallet balance.
    for record in balances["records"]:
        output = analyze_rows(
            [{"mint": record["mint"], "current_raw": record["raw_balance"],
              "position_state": "UNKNOWN"}],
            as_of=1_791_691_200, max_market_age_seconds=300,
        )[0]
        html = render_html([output], as_of=1_791_691_200, simulated_updates=[])
        assert record["mint"] in html
        assert output["latest_side"] == "UNVERIFIED"
        assert "FRANK_LATEST_ACTION_BUY" not in output["facts"]
        assert output["price"]["market_price_usdc"] is None
        assert output["price"]["change_pct_vs_last_verified_buy"] is None
        assert record["executable_usd_value_status"] == "PRICE_UNAVAILABLE_NOT_ASSUMED_ZERO"
        assert "NOT executable return" not in html

    # Real evidence diversity, not independent returns or an operational SLA.
    assert sum(x["balance_status"] == "NONZERO_VERIFIED" for x in balances["records"]) == 2
    assert sum(x["balance_status"] == "ZERO_AT_SLOT_VERIFIED" for x in balances["records"]) == 4
