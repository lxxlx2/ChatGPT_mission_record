"""Monster bounded 300U ledger: visible closed minutes and no hindsight admission."""
import importlib.util
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest

S=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(S))
spec=importlib.util.spec_from_file_location("monster_300u",S/"monster_v4_mainline_preclosed_300u_cash_ledger.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def minutes(n=1500,*,start=1770000000000):
    start -= start%60_000
    return [[start+i*60_000,"1","1","1","1","100",3] for i in range(n)]


def slot(symbol,at,status="PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE",return_pct="-10"):
    return {"symbol":symbol,"event_id":symbol+"-a","event_time_ms":at-180000,
            "entry_time_ms":at,
            "source_entry_status":"ENTRY_PREVIOUS_CLOSED_MINUTE_SOURCE_OK",
            "source_exit":{"status":status,
                "net_return_pct_fee10_slip20_per_side":return_pct} if status=="PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE"
                else {"status":status}}


class Monster300UPreclosedTests(unittest.TestCase):
    def test_entry_uses_only_prior_closed_minute_not_entry_minutes_future_volume(self):
        b=minutes()
        at=b[3][0]
        before=m.prior_closed_1m_eligible(b,at)
        self.assertEqual(before[0],"ENTRY_PREVIOUS_CLOSED_MINUTE_SOURCE_OK")
        b[3][5]="0"
        b[3][6]=0
        self.assertEqual(m.prior_closed_1m_eligible(b,at),before)

    def test_ineligible_previous_minute_does_not_admit_entry_even_if_next_is_liquid(self):
        b=minutes()
        at=b[3][0]
        b[2][5]="0"
        self.assertEqual(m.prior_closed_1m_eligible(b,at)[0],
                         "CENSORED_PRIOR_MINUTE_QUOTE_LT_30_OR_NO_TRADES")

    def test_exit_minute_volume_future_info_does_not_change_exit_admission(self):
        b=minutes()
        at=b[1443][0]
        expected=m.exit_only_preclosed_minute_source(b,at)
        self.assertEqual(expected[0],"PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE")
        b[1443][5]="0"
        b[1443][6]=0
        self.assertEqual(m.exit_only_preclosed_minute_source(b,at),expected)

    def test_exit_last_closed_minute_source_rejects_zero_volume(self):
        b=minutes()
        at=b[1443][0]
        b[1442][6]=0
        self.assertEqual(m.exit_only_preclosed_minute_source(b,at)[0],
                         "CENSORED_EXIT_PRIOR5_ZERO_VOLUME_OR_INVALID")

    def test_all_cash_limited_10_of_simultaneous_12_selected(self):
        at=minutes()[3][0]
        events=[slot(f"SYM{i:02d}USDT",at,return_pct="0") for i in range(12)]
        r=m.cash_simulation(events,symbol_order="SYMBOL_ASC",censored_principal_recovery=100)
        s=r["summary"]
        self.assertEqual(s["selected_count"],10)
        self.assertEqual(s["skipped_10_slots"],2)
        self.assertEqual(s["maximum_concurrent_lots"],10)
        self.assertEqual(s["initial_cash_usdt"],"300")
        self.assertEqual(s["gross_assumed_entry_spend_usdt"],"300")
        self.assertEqual(s["final_cash_after_all_assumed_24h_settlements_usdt"],"300")
        self.assertEqual(len(s["largest_98_watch_burst"]["selected_symbols"]),0)

    def test_cash_scenario_unknown_exit_remains_hypothetical(self):
        at=minutes()[3][0]
        events=[slot("AUSDT",at,status="CENSORED_EXIT_OPEN_NOT_ARCHIVED")]
        worst=m.cash_simulation(events,symbol_order="SYMBOL_ASC",censored_principal_recovery=0)
        best=m.cash_simulation(events,symbol_order="SYMBOL_ASC",censored_principal_recovery=100)
        self.assertEqual(worst["summary"]["final_cash_after_all_assumed_24h_settlements_usdt"],"270")
        self.assertEqual(best["summary"]["final_cash_after_all_assumed_24h_settlements_usdt"],"300")
        self.assertTrue(best["summary"]["unverified_recovery_not_a_bound_on_true_execution"])

    def test_future_exit_missing_does_not_free_up_cash_or_symbol_before_24h(self):
        at=minutes()[3][0]
        rows=[slot("AUSDT",at,status="CENSORED_EXIT_OPEN_NOT_ARCHIVED"),
              slot("AUSDT",at+360000,status="PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE")]
        rows[1]["event_id"]="AUSDT-b"
        r=m.cash_simulation(rows,symbol_order="SYMBOL_ASC",censored_principal_recovery=100)
        self.assertEqual(r["summary"]["selected_count"],1)
        self.assertEqual(r["summary"]["skipped_same_symbol"],1)

    def test_two_frozen_tie_orders_choose_different_symbols_with_no_future_ranking(self):
        at=minutes()[3][0]
        events=[slot(f"SYM{i:02d}USDT",at) for i in range(12)]
        asc=m.cash_simulation(events,symbol_order="SYMBOL_ASC",censored_principal_recovery=0)
        desc=m.cash_simulation(events,symbol_order="SYMBOL_DESC",censored_principal_recovery=0)
        a=[x["symbol"] for x in asc["event_decisions"] if x["selection_status"]=="SELECT_30_USDT"]
        b=[x["symbol"] for x in desc["event_decisions"] if x["selection_status"]=="SELECT_30_USDT"]
        self.assertEqual(len(a),10)
        self.assertEqual(len(b),10)
        self.assertNotEqual(set(a),set(b))

    def test_source_only_unfunded_signals_still_count_in_denominator(self):
        at=minutes()[3][0]
        ev=[slot("AUSDT",at),slot("BUSDT",at)]
        ev[1]["source_entry_status"]="CENSORED_PRIOR_MINUTE_QUOTE_LT_30_OR_NO_TRADES"
        ev[1]["source_exit"]=None
        r=m.cash_simulation(ev,symbol_order="SYMBOL_ASC",censored_principal_recovery=100)
        self.assertEqual(r["summary"]["selected_count"],1)
        self.assertEqual(r["summary"]["entry_source_rejected"],1)
        self.assertEqual(r["summary"]["total_signals"],2)

    def test_immutable_previous_source_blob_gate_rejects_untrusted_text(self):
        with tempfile.TemporaryDirectory() as d:
            e=Path(d)/"fake.json"
            ab=Path(d)/"ab.json"
            e.write_text("{}")
            ab.write_text("{}")
            with self.assertRaisesRegex(ValueError,"PREVIOUS_ECON_IMMUTABLE_BLOB_DRIFT"):
                m.original_inputs(ab,e)


if __name__=="__main__":
    unittest.main()
