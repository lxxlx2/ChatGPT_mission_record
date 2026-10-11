"""Stage27 real WATCH arrival shared queue and strict user-cash ledger tests."""
import sys
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).parents[1]/"scripts"
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import monster_v4_stage27_shared_queue_cash_ledger as m

DATE="2026-02-06T00:36:00Z"
def stamp(s):
    return m.previous.utc(s)
def case(symbol,when="2026-02-06T00:36:00Z",net=-25,valid=True):
    return {"date":"2026-02-04","symbol":symbol,"watch_utc":when,
       "proxy_status":"PRICE_PROXY_ONLY" if valid else "CENSORED_ZERO_VOLUME_EXIT",
       "net_pct":net if valid else None}

class Stage27(unittest.TestCase):
    def test_frozen_capacity_and_financed_denominator(self):
        cfg=m.frozen()
        self.assertEqual(cfg["shared_queue"]["process_queue_limit_per_poll"],8)
        self.assertEqual(cfg["ledger"]["full_lot_USDT"],30)
        self.assertEqual(cfg["all_watches"],1132)
    def test_ninety_eight_simultaneous_watches_cannot_all_be_served(self):
        t=stamp(DATE)
        arrivals=[(t,f"T{i:03d}USDT") for i in range(98)]
        result=m.shared_first_eval_queue(arrivals)
        self.assertEqual(result["arrivals"],98)
        self.assertEqual(result["per_poll_peak"],98)
        self.assertEqual(result["first_evaluated_before_deadline"],48)
        self.assertEqual(result["unserved_expired"],50)
        self.assertEqual(result["max_backlog_after_arrivals"],98)
        self.assertTrue(result["one_eval_model_optimistic"])
    def test_sparse_events_all_first_evaluated_with_zero_wait(self):
        t=stamp(DATE)
        arr=[(t+timedelta(minutes=i*30),f"X{i}USDT") for i in range(5)]
        out=m.shared_first_eval_queue(arr)
        self.assertEqual(out["first_evaluated_before_deadline"],5)
        self.assertEqual(out["unserved_expired"],0)
        self.assertEqual(out["max_wait_minutes"],0)
    def test_fixed_full_30u_no_overdraft_after_first_loss(self):
        arr=[case("AUSDT",DATE,-20),
             case("BUSDT","2026-02-07T01:00:00Z",20)]
        out=m.money_ledger(arr,30,1,"FIXED_30U",20,100)
        self.assertEqual(out["counts"]["selected"],1)
        self.assertEqual(out["counts"]["skip_insufficient_cash_30u"],1)
        self.assertEqual(out["final_cash_USDT"],24)
        self.assertFalse(out["cash_overdrawn"])
    def test_fractional_lot_reuses_remaining_cash_without_leverage(self):
        arr=[case("AUSDT",DATE,-20),
             case("BUSDT","2026-02-07T01:00:00Z",20)]
        out=m.money_ledger(arr,30,1,"UP_TO_30U_FRACTIONAL",20,100)
        self.assertEqual(out["counts"]["selected"],2)
        self.assertEqual(out["selected_cases"][1]["entry_USDT"],24)
        self.assertEqual(out["final_cash_USDT"],28.8)
    def test_censored_exits_two_bounds_not_claim_zero_historical_loss(self):
        arr=[case("AUSDT",valid=False),
             case("BUSDT",when="2026-02-07T02:00:00Z",net=10)]
        optimistic=m.money_ledger(arr,30,1,"FIXED_30U",20,100)
        stress=m.money_ledger(arr,30,1,"FIXED_30U",20,0)
        self.assertEqual(optimistic["counts"]["selected"],2)
        self.assertEqual(optimistic["final_cash_USDT"],33)
        self.assertEqual(stress["counts"]["selected"],1)
        self.assertEqual(stress["final_cash_USDT"],0)
        self.assertEqual(stress["counts"]["skip_insufficient_cash_30u"],1)
    def test_tied_same_minute_cash_deterministic_symbol_not_future_profit(self):
        a=case("ZZZUSDT",DATE,100)
        b=case("AAAUSDT",DATE,-10)
        sorted_entries=sorted([a,b],key=lambda x:(x["watch_utc"],x["date"],x["symbol"]))
        result=m.money_ledger(sorted_entries,30,1,"FIXED_30U",20,100)
        self.assertEqual(result["selected_cases"][0]["symbol"],"AAAUSDT")
        self.assertEqual(result["final_cash_USDT"],27)
    def test_unfunded_trade_does_not_create_new_cash(self):
        trades=[case(f"X{i}USDT",(stamp(DATE)+timedelta(hours=i*25)).strftime("%Y-%m-%dT%H:%M:%SZ"),-90) for i in range(5)]
        result=m.money_ledger(trades,30,1,"FIXED_30U",20,100)
        self.assertEqual(result["counts"]["selected"],1)
        self.assertEqual(result["final_cash_USDT"],3)
        self.assertEqual(result["counts"]["skip_insufficient_cash_30u"],4)

if __name__=="__main__": unittest.main()
