"""F01 source-only, no quote/amount/API/network/production changes."""
import unittest
from io import BytesIO
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
        with patch.object(server.time, "time", return_value=NOW), \
             patch.object(server, "partition_source_only", wraps=partition_source_only) as gate:
            result = state.follow_opportunities()
        self.assertEqual(gate.call_count, 1)
        self.assertEqual(result["source_recent_count"], 1)
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

    def test_event_age_and_remaining_window_are_chain_based_not_index_lag(self):
        out = self.view([
            candidate(latest_buy_at=NOW-12, latest_at=NOW-12),
            candidate(latest_buy_at=NOW-700, latest_at=NOW-700),
            candidate(latest_buy_at=None),
        ])
        self.assertEqual(out["event_time_basis"], "ONCHAIN_BLOCK_TIME_SECONDS")
        self.assertEqual(out["index_ingest_timestamp_status"],
                         "UNAVAILABLE_IN_EXISTING_CANDIDATE_SCHEMA")
        self.assertIsNone(out["index_ingest_latency_seconds"])
        self.assertEqual(out["source_recent"][0]["chain_buy_age_seconds_at_observation"], 12)
        self.assertEqual(out["source_recent"][0]["source_window_remaining_seconds"], 588)
        self.assertEqual(out["newest_indexed_buy_age_seconds"], 12)
        self.assertEqual(out["excluded_reason_counts"], {"SOURCE_BUY_STALE_OR_UNVERIFIED":2})
        self.assertEqual(out["eligible_count"], 0)

    def test_late_indexed_buy_does_not_get_falsely_marked_fresh(self):
        out = self.view([candidate(latest_buy_at=NOW-1000, latest_at=NOW-1000)])
        self.assertEqual(out["source_recent_count"], 0)
        self.assertEqual(out["newest_indexed_buy_age_seconds"], 1000)
        self.assertEqual(out["not_followed"][0]["exclusion_reason"],
                         "SOURCE_BUY_STALE_OR_UNVERIFIED")

    def test_ca_post_error_codes_are_safe_and_do_not_start_jobs(self):
        handler = server.Handler.__new__(server.Handler)
        handler._allowed_host = lambda: True
        handler._json = lambda payload, status=200: (payload, status)
        handler.path = "/api/cluster-analysis"
        handler.headers = {"Origin":"http://127.0.0.1:8765",
                           "Content-Type":"application/json",
                           "Content-Length":"38"}
        raw = b'{"mint":"not-a-ca","preset":"standard"}'
        handler.headers["Content-Length"] = str(len(raw))
        handler.rfile = BytesIO(raw)
        handler.state = SimpleNamespace(cluster_jobs=SimpleNamespace(
            submit=lambda *args: (_ for _ in ()).throw(ValueError("INVALID_SOLANA_CA"))))
        self.assertEqual(handler.do_POST(), ({"error":"INVALID_SOLANA_CA"},400))
        handler.rfile = BytesIO(raw)
        handler.state.cluster_jobs.submit = lambda *args: (
            _ for _ in ()).throw(ValueError("secret-rpc-query-api-key"))
        self.assertEqual(handler.do_POST(), ({"error":"INVALID_CLUSTER_REQUEST"},400))

    def test_source_api_never_serializes_stale_execution_quote_or_amount_metrics(self):
        from json import dumps
        input_row = candidate(
            metrics={"execution_price_usdc":"3.45", "price_impact_pct":"1.5",
                     "user_trade_amount_usdc":"custom_amount_should_not_leak"},
            decision_quote={"status":"OK", "execution_price_usdc":"3.45",
                            "route_exists":True, "internal_amount":"stale"},
            user_trade_amount_usdc="fake_runtime_amount",
            latest_buy_original_quote_asset="USDC",
            latest_buy_original_quote_quantity="5000",
            latest_buy_price_usdc="0.002"
        )
        for result_row in (
            self.view([input_row])["source_recent"][0],
            self.view([dict(input_row, latest_at=NOW-700,
                latest_buy_at=NOW-700)])["not_followed"][0]
        ):
            output = dumps(result_row, sort_keys=True)
            self.assertNotIn("decision_quote", output)
            self.assertNotIn("metrics", output)
            self.assertNotIn("execution_price_usdc", output)
            self.assertNotIn("price_impact_pct", output)
            self.assertNotIn("user_trade_amount_usdc", output)
            self.assertNotIn("fake_runtime_amount", output)
            self.assertNotIn("custom_amount_should_not_leak", output)
            self.assertEqual(result_row["latest_buy_original_quote_quantity"],"5000")
            self.assertEqual(result_row["latest_buy_price_usdc"],"0.002")
            self.assertEqual(result_row["decision"],"NO_BUY")
        self.assertEqual(self.view([input_row])["eligible_count"],0)

    def test_source_only_contract_not_executable_at_any_amount(self):
        for decision in ("BUY", "SMALL_BUY", "WAIT", "NO_BUY", "UNASSESSED"):
            with self.subTest(decision=decision):
                result = self.view([candidate(decision=decision,
                    decision_quote={"status":"OK","route_exists":True,
                                    "execution_price_usdc":"1","price_impact_pct":"0"})])
                self.assertEqual(result["eligible_count"], 0)


if __name__ == "__main__":
    unittest.main()
