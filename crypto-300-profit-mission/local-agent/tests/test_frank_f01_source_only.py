"""F01 source-only, no quote/amount/API/network/production changes."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mission_agent.mission_control import server
from mission_agent.mission_control.f01_source_view import partition_source_only

NOW = 1_800_000_000.0
BASE = {
    "person_id": "frank", "mint": "7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump",
    "episode_id": "e1", "source_signal_id": "s1",
    "candidate_source": "FRANK_SOURCE", "pattern": "MULTIPLE",
    "position_state": "OPEN", "latest_side": "BUY",
    "latest_buy_at": NOW - 12, "latest_at": NOW - 12,
    "decision": "NO_BUY", "decision_created_at": NOW - 5,
}
def candidate(**kw):
    return {**BASE, **kw}


class F01SourceOnlyTests(unittest.TestCase):
    def view(self, rows, runtime="LIVE"):
        return partition_source_only(rows, now=NOW, runtime_status=runtime)

    def test_recent_source_buy_observed_regardless_of_quote_or_decision(self):
        result = self.view([candidate(decision="NO_BUY", decision_quote={})])
        self.assertEqual(result["status"], "SOURCE_ONLY")
        self.assertEqual(result["source_recent_count"], 1)
        self.assertEqual(result["source_recent"][0]["f01_source_state"], "RECENT_SOURCE_BUY_ONLY")
        self.assertFalse(result["current_balance_verified"])
        self.assertEqual(result["eligible"], [])
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["execution_eligibility"], "NOT_ASSESSED_USER_AMOUNT_MISSING")
        self.assertFalse(result["live_notification_authorized"])

    def test_exact_ten_minute_window_and_no_future(self):
        result = self.view([
            candidate(latest_buy_at=NOW - 600, latest_at=NOW - 600),
            candidate(latest_buy_at=NOW - 601),
            candidate(latest_at=NOW + 1),
        ])
        self.assertEqual(result["source_recent_count"], 1)
        self.assertEqual(result["excluded_count"], 2)

    def test_sell_exit_closed_and_unknown_stay_history(self):
        result = self.view([
            candidate(latest_side="SELL"),
            candidate(position_state="CLOSED"),
            candidate(position_state="INVENTORY_UNDETERMINED"),
            candidate(latest_side="UNKNOWN"),
        ])
        self.assertEqual(result["source_recent_count"], 0)
        self.assertEqual(result["excluded_count"], 4)
        self.assertEqual(result["not_followed"][0]["exclusion_reason"], "LATEST_ACTION_NOT_BUY")

    def test_no_overlay_cross_person_or_unverified_source(self):
        result = self.view([
            candidate(candidate_source="MISSION_CONTROL_OVERLAY"),
            candidate(person_id="another"),
            candidate(source_signal_id=None),
            candidate(pattern="REENTRY_WATCH"),
        ])
        self.assertEqual(result["source_recent_count"], 0)

    def test_runtime_not_live_blocks_current_even_if_fresh(self):
        for runtime in ("OFFLINE", "UNKNOWN", "RUNNING", None):
            with self.subTest(runtime=runtime):
                out = self.view([candidate()], runtime=runtime)
                self.assertEqual(out["status"], "RUNTIME_UNAVAILABLE")
                self.assertEqual(out["source_recent_count"], 0)
                self.assertEqual(out["eligible_count"], 0)

    def test_bad_time_and_row_rejected_or_excluded(self):
        for ts in (None, False, float("nan"), "2026-10-27T12:00:00", "garbage"):
            with self.subTest(ts=str(ts)):
                self.assertEqual(self.view([candidate(latest_buy_at=ts)])["source_recent_count"], 0)
        for rows in (None, {}, [None]):
            with self.assertRaises(ValueError):
                self.view(rows)

    def test_dashboard_state_uses_source_only_without_rpc(self):
        state = server.DashboardState.__new__(server.DashboardState)
        state.frank = SimpleNamespace(runtime=lambda: {"status": "LIVE"})
        state.candidates = lambda: [candidate()]
        with patch.object(server, "partition_source_only", wraps=partition_source_only) as gate:
            result = state.follow_opportunities()
        self.assertEqual(gate.call_count, 1)
        self.assertEqual(result["source_recent_count"], 0)  # NOW is a historical synthetic timestamp
        self.assertEqual(result["eligible_count"], 0)

    def test_dashboard_source_failure_is_unknown_not_empty_verified(self):
        state = server.DashboardState.__new__(server.DashboardState)
        state.frank = SimpleNamespace(runtime=lambda: {"status": "LIVE"})
        state.candidates = lambda: (_ for _ in ()).throw(OSError("offline"))
        out = state.follow_opportunities()
        self.assertEqual(out["status"], "SOURCE_UNAVAILABLE")
        self.assertIsNone(out["source_recent"])
        self.assertIsNone(out["source_recent_count"])

    def test_get_route_is_readonly_no_query(self):
        handler = server.Handler.__new__(server.Handler)
        handler._allowed_host = lambda: True
        handler._json = lambda payload, status=200: (payload, status)
        handler.state = SimpleNamespace(follow_opportunities=lambda: {"status": "SOURCE_ONLY"})
        handler.path = "/api/follow-opportunities"
        self.assertEqual(handler.do_GET(), ({"status":"SOURCE_ONLY"}, 200))
        handler.path = "/api/follow-opportunities?mint=abc"
        self.assertEqual(handler.do_GET()[1], 400)

    def test_source_only_contract_not_executable_at_any_amount(self):
        for decision in ("BUY", "SMALL_BUY", "WAIT", "NO_BUY", "UNASSESSED"):
            with self.subTest(decision=decision):
                result = self.view([candidate(decision=decision,
                    decision_quote={"status":"OK","route_exists":True,
                                    "execution_price_usdc":"1","price_impact_pct":"0"})])
                self.assertEqual(result["eligible_count"], 0)


if __name__ == "__main__":
    unittest.main()
