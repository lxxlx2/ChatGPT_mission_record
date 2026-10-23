"""Zero-network adversarial Frank D2 source projection tests. No live data."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import unittest

from mission_agent.mission_control.wallet_owner_at_slot import (
    FRANK_WALLET, PROGRAMS, AtSlotSourceError, _fingerprint,
    project_replayed_owner, render_offline_html,
)

MINT_A = "2" * 32
MINT_B = "3" * 32
MINT_C = "4" * 32
MINT_ABSENT = "5" * 32
ACCOUNTS = ("6" * 32, "7" * 32, "8" * 32, "9" * 32)


def row(token_account, mint, program, slot, raw, decimals=6):
    return {
        "token_account": token_account, "mint": mint, "program_id": program,
        "raw_amount": str(raw), "decimals": decimals, "state": "initialized",
        "owner": FRANK_WALLET, "slot": slot,
    }


def source():
    observed = datetime(2026, 10, 23, 14, 46, 32, tzinfo=timezone.utc).isoformat()
    p1, p2 = PROGRAMS
    slots = (460482174, 460482176)
    a = row(ACCOUNTS[0], MINT_A, p1, slots[0], 5000000)
    b = row(ACCOUNTS[1], MINT_A, p1, slots[0], 7000000)
    c = row(ACCOUNTS[2], MINT_B, p1, slots[0], 0)
    d = row(ACCOUNTS[3], MINT_C, p2, slots[1], 1000000000, 9)
    mints = [
        {"mint": MINT_A, "raw_amount_observed_sum": "12000000",
         "decimals": 6, "token_accounts": [a,b],
         "slot_min": slots[0], "slot_max": slots[0]},
        {"mint": MINT_B, "raw_amount_observed_sum": "0",
         "decimals": 6, "token_accounts": [c],
         "slot_min": slots[0], "slot_max": slots[0]},
        {"mint": MINT_C, "raw_amount_observed_sum": "1000000000",
         "decimals": 9, "token_accounts": [d],
         "slot_min": slots[1], "slot_max": slots[1]},
    ]
    doc = {
        "schema_version": 1, "network": "solana-mainnet",
        "wallet": FRANK_WALLET, "status": "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC",
        "observed_at_utc": observed,
        "program_coverage": [
            {"wallet": FRANK_WALLET, "program_id": p1,
             "slot": slots[0], "commitment": "finalized", "account_count": 3,
             "accounts": [a,b,c], "source": "SOLANA_GET_TOKEN_ACCOUNTS_BY_OWNER"},
            {"wallet": FRANK_WALLET, "program_id": p2,
             "slot": slots[1], "commitment": "finalized", "account_count": 1,
             "accounts": [d], "source": "SOLANA_GET_TOKEN_ACCOUNTS_BY_OWNER"},
        ],
        "missing": [], "account_count": 4, "mint_count_observed": 3,
        "mints": mints, "slot_min": slots[0], "slot_max": slots[1],
        "both_programs_observed": True, "same_slot_atomic": False,
        "all_history_complete": False,
        "person_beneficial_ownership_verified": False,
        "wallet_total_balance_verified": False,
        "wallet_nav_usd": None, "realized_pnl_usd": None,
    }
    doc["capture_sha256"] = _fingerprint(doc)
    return doc


WATCH = {"rows": [
    {"mint": MINT_A, "local_model_state": "CLOSED", "last_event_side": "SELL"},
    {"mint": MINT_B, "local_model_state": "OPEN", "last_event_side": "BUY"},
    {"mint": MINT_ABSENT, "local_model_state": "UNKNOWN"},
]}
AS_OF = datetime(2026,10,23,15,0,tzinfo=timezone.utc)


def projected(doc=None, watch=None, targets=(MINT_A,MINT_B,MINT_C,MINT_ABSENT), **options):
    return project_replayed_owner(doc if doc is not None else source(),
                                  watch if watch is not None else WATCH,
                                  target_mints=targets, as_of=options.pop('as_of', AS_OF), **options)


def changed(mutator):
    doc = source()
    mutator(doc)
    doc["capture_sha256"] = _fingerprint(doc)
    return doc


class D2AtSlotSourceTests(unittest.TestCase):
    def test_multiple_accounts_one_mint_exact_int_and_model_distinct(self):
        out=projected()
        rows={z["mint"]:z for z in out["preview_rows"]}
        self.assertEqual(rows[MINT_A]["raw_amount"],"12000000")
        self.assertEqual(rows[MINT_A]["token_quantity_at_slots"],"12")
        self.assertEqual(rows[MINT_A]["token_account_count"],2)
        self.assertEqual(rows[MINT_A]["at_slot_state"],"NONZERO_AT_SLOT")
        self.assertEqual(rows[MINT_A]["model_state"],"CLOSED")
        self.assertEqual(rows[MINT_A]["last_signed_side"],"SELL")
        self.assertFalse(rows[MINT_A]["current_chain_balance_verified"])
        self.assertIsNone(rows[MINT_A]["usd_value"])
        self.assertIsNone(rows[MINT_A]["pnl_usd"])
        self.assertEqual(out["account_count"],4)
        self.assertEqual(out["mint_count"],3)
        self.assertEqual(out["outside_watchlist_mints"],1)

    def test_zero_account_is_not_absent_account(self):
        rows={z["mint"]:z for z in projected()["preview_rows"]}
        self.assertEqual(rows[MINT_B]["at_slot_state"],"ZERO_AT_SLOT")
        self.assertEqual(rows[MINT_B]["raw_amount"],"0")
        self.assertEqual(rows[MINT_ABSENT]["at_slot_state"],
                         "NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS")
        self.assertIsNone(rows[MINT_ABSENT]["raw_amount"])
        self.assertEqual(rows[MINT_ABSENT]["token_account_count"],0)
        self.assertEqual(rows[MINT_C]["token_quantity_at_slots"],"1")
        self.assertEqual(rows[MINT_C]["program_ids"],[PROGRAMS[1]])

    def test_slots_timestamps_non_atomic_even_if_equal(self):
        out=projected()
        self.assertEqual(out["program_coverage"][0]["slot"],460482174)
        self.assertEqual(out["program_coverage"][1]["slot"],460482176)
        self.assertFalse(out["same_slot_atomic"])
        self.assertEqual(out["observed_at_bangkok"][:16],"2026-10-23T21:46")
        same=changed(lambda d: (
            d["program_coverage"][1].update(slot=460482174),
            d["program_coverage"][1]["accounts"][0].update(slot=460482174),
            d["mints"][2].update(slot_min=460482174,slot_max=460482174),
            d.update(slot_max=460482174)))
        out=projected(same)
        self.assertFalse(out["same_slot_atomic"])

    def test_stale_age_labeled_not_perpetually_current(self):
        out=projected(as_of=AS_OF + timedelta(days=4))
        self.assertGreater(out["age_seconds_at_render"],4*86400)
        self.assertFalse(out["current_chain_balance_verified"])
        with self.assertRaisesRegex(AtSlotSourceError,"SOURCE_TIMESTAMP_IN_FUTURE"):
            projected(as_of=AS_OF - timedelta(days=30))

    def test_missing_second_program_and_wrong_owner_and_program_fail_closed(self):
        for change in (
            lambda d:d["program_coverage"].pop(),
            lambda d:d["program_coverage"][0].update(wallet=MINT_A),
            lambda d:d["program_coverage"][1].update(program_id=PROGRAMS[0]),
            lambda d:d.update(status="PARTIAL_SOURCE"),
            lambda d:d.update(missing=[{"program_id":PROGRAMS[1]}]),
        ):
            with self.subTest(case=change):
                with self.assertRaises(AtSlotSourceError):
                    projected(changed(change))

    def test_fingerprint_tamper_refused(self):
        doc=source()
        doc["program_coverage"][0]["accounts"][0]["raw_amount"]="1"
        with self.assertRaisesRegex(AtSlotSourceError,"REPLAY_CAPTURE_FINGERPRINT_MISMATCH"):
            projected(doc)

    def test_duplicate_account_and_inconsistent_decimals_refused(self):
        def duplicate(d):
            d["program_coverage"][0]["accounts"][1]["token_account"]=ACCOUNTS[0]
        def decimals(d):
            d["program_coverage"][0]["accounts"][1]["decimals"]=9
        for action in (duplicate,decimals):
            with self.subTest(case=action):
                with self.assertRaises(AtSlotSourceError):
                    projected(changed(action))

    def test_declared_mint_sum_mismatch_rejected(self):
        doc=changed(lambda d:d["mints"][0].update(raw_amount_observed_sum="13000000"))
        with self.assertRaisesRegex(AtSlotSourceError,"MINT_SOURCE_RECONCILIATION_FAILED"):
            projected(doc)

    def test_outside_watchlist_retained_in_aggregate_without_full_account_dump(self):
        out=projected()
        self.assertEqual(out["outside_watchlist_mints"],1)
        html=render_offline_html(out)
        self.assertIn(MINT_C,html)
        self.assertNotIn(ACCOUNTS[0],html)
        self.assertIn("余额证据",html)
        self.assertIn("无网络",html)
        self.assertNotIn("https://",html)

    def test_watchlist_duplicate_mint_rejected(self):
        with self.assertRaisesRegex(AtSlotSourceError,"WATCHLIST_MINT_DUPLICATED"):
            projected(watch={"rows":WATCH["rows"]+[WATCH["rows"][0]]})

    def test_visible_bound_and_search_priority(self):
        doc=source()
        # Give the watchlist enough distinct valid-base58 synthetics.
        others=[{"mint":("Z"*(31-len(str(i)))) + str(i).replace("0","A") + "9",
                 "local_model_state":"UNKNOWN"} for i in range(100)]
        watch={"rows":WATCH["rows"]+others}
        result=projected(watch=watch,max_visible=60,outsider_reserve=10)
        self.assertLessEqual(len(result["preview_rows"]),60)
        self.assertTrue({MINT_A,MINT_B,MINT_C,MINT_ABSENT}.issubset(
            {x["mint"] for x in result["preview_rows"]}))
        self.assertEqual(result["preview_limit"],60)

    def test_html_escapes_hostile_watchlist_source(self):
        watch=deepcopy(WATCH)
        watch["rows"][0]["local_model_state"]='<img src=x onerror=alert(1)>'
        html=render_offline_html(projected(watch=watch))
        self.assertIn("&lt;img",html)
        self.assertNotIn("<img src=x",html)

    def test_raw_not_numeric_or_negative_rejected(self):
        for raw in ("-1","1e3",1,False):
            with self.subTest(raw=raw):
                d=changed(lambda doc:doc["program_coverage"][0]["accounts"][0].update(raw_amount=raw))
                with self.assertRaises(AtSlotSourceError):
                    projected(d)


if __name__=="__main__":
    unittest.main()
