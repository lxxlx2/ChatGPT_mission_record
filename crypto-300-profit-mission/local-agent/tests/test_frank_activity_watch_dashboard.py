"""Frank Option 3 D2: signed-activity research independent of current candidates.

Synthetic inputs only. No RPC, Gmail, trading, default amount, DB writes or
production Mac actions. P4 owner Mac results remain separate from this CI.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

from mission_agent.mission_control import server
from mission_agent.mission_control.frank_activity_watch import summarize_activity


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MINT_ACTIVE = "B" * 43
MINT_OLD = "C" * 43


def sample_trades():
    rows = []
    for i in range(100):
        side = ("BUY" if i < 41 else
                "SELL_POSITION_UNRESOLVED" if i < 66 else
                "EXIT")
        is_sell = i >= 41
        mint = MINT_ACTIVE if i < 54 else MINT_OLD
        rows.append({
            "signature": "A" * 62 + ALPHABET[i // len(ALPHABET)]
                         + ALPHABET[i % len(ALPHABET)],
            "mint": mint,
            "side": side,
            "block_time": 1_792_493_000 + i,
            "body": {"direction": "SELL" if is_sell else "BUY"},
        })
    return rows


def test_100_local_rows_preserve_46_sales_outside_current_candidate_set():
    rows = sample_trades()
    observed = summarize_activity(
        rows, [{"mint": MINT_ACTIVE}], as_of=1_792_494_000
    )
    assert observed["displayed_transactions"] == 100
    assert observed["counts"]["buy_category"] == 41
    assert observed["counts"]["sell_category"] == 59
    assert observed["counts"]["sell_outside_current_candidate_mint_set"] == 46
    assert observed["counts"]["sell_position_unresolved"] == 25
    assert observed["rows"][0]["source_side"] == "EXIT"
    assert observed["rows"][0]["in_current_candidate_mint_set"] is False
    assert all(not x["send_allowed"] for x in observed["rows"])
    assert all(x["position_status"] == "CURRENT_BALANCE_NOT_VERIFIED"
               for x in observed["rows"])
    assert all(x["linked_prior_v1_signal"] == "NOT_VERIFIED"
               for x in observed["rows"])
    assert all(x["order_amount_usdc"] is None for x in observed["rows"])
    assert observed["notification_authorized"] is False
    assert observed["chain_completeness_verified"] is False


def test_no_future_events_duplicate_or_direction_conflicts_are_counted_as_trades():
    trade = sample_trades()[0]
    rows = [trade, dict(trade),
            dict(sample_trades()[1], block_time=1_792_494_001),
            dict(sample_trades()[2], body={"direction": "SELL"})]
    observed = summarize_activity(rows, [], as_of=1_792_494_000)
    assert observed["displayed_transactions"] == 1
    assert observed["counts"]["excluded"]["DUPLICATE_SIGNATURE"] == 1
    assert observed["counts"]["excluded"]["SOURCE_FIELDS_NOT_VERIFIED"] == 1
    assert observed["counts"]["excluded"]["SOURCE_DIRECTION_CONFLICT"] == 1
    with pytest.raises(ValueError, match="CONFLICTING_SAME_SIGNATURE_FACTS"):
        summarize_activity([trade, dict(trade, side="ADD")], [], as_of=1_792_494_000)
    with pytest.raises(ValueError, match="INVALID_BOUNDED_TRADE_SOURCE"):
        summarize_activity(sample_trades() + [trade], [], as_of=1_792_494_000)


def test_dashboard_readonly_state_and_failure_do_not_create_false_zero(monkeypatch):
    monkeypatch.setattr(server.time, "time", lambda: 1_792_494_000.0)
    state = server.DashboardState.__new__(server.DashboardState)
    events = []
    state.frank = SimpleNamespace(
        recent_trades=lambda limit: (events.append(("trades", limit)), sample_trades())[1],
        candidates=lambda: (events.append(("candidates",)), [{"mint": MINT_ACTIVE}])[1]
    )
    result = state.frank_activity_watch()
    assert events == [("trades",100),("candidates",)]
    assert result["status"] == "LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY"
    assert result["counts"]["sell_category"] == 59
    assert result["notification_authorized"] is False
    assert not hasattr(state, "mailer")

    state.frank = SimpleNamespace(
        recent_trades=lambda limit: (_ for _ in ()).throw(OSError("offline")),
        candidates=lambda: [{"mint": MINT_ACTIVE}],
    )
    failed = state.frank_activity_watch()
    assert failed["status"] == "SOURCE_UNAVAILABLE"
    assert failed["reason"] == "LOCAL_FRANK_ACTIVITY_SOURCE_UNAVAILABLE"
    assert "counts" not in failed


def test_queryless_local_route_and_native_dashboard_filters():
    handler = server.Handler.__new__(server.Handler)
    handler._allowed_host = lambda: True
    handler._json = lambda payload, status=200: (payload, status)
    handler.state = SimpleNamespace(
        frank_activity_watch=lambda: {"status":"LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY"}
    )
    handler.path = "/api/frank-activity-watch"
    assert handler.do_GET() == ({"status":"LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY"}, 200)
    handler.path = "/api/frank-activity-watch?include=markets"
    assert handler.do_GET() == ({"error":"UNSUPPORTED_ACTIVITY_QUERY"}, 400)
    handler._allowed_host = lambda: False
    handler.send_error = lambda code, reason: (code, reason)
    handler.path = "/api/frank-activity-watch"
    assert handler.do_GET()[0] == 421

    static = Path(server.__file__).parent / "static"
    html = (static/"index.html").read_text()
    js = (static/"app.js").read_text()
    assert 'id="frank-activity-panel"' in html
    assert 'id="frank-activity-type"' in html
    assert "get('/api/frank-activity-watch')" in js
    assert "renderFrankActivity(" in js
    assert "setInterval(refreshFrankActivity,60000)" in js
    assert "get('/api/frank-intelligence')" in js
    assert "get('/api/candidates')" in js
