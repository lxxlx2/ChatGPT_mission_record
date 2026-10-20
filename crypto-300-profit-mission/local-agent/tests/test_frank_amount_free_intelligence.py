"""P2 research-only amount-independent intelligence and dated historical evidence.

No live providers: tests load archived evidence files and pure candidate inputs.
"""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mission_agent.mission_control.intelligence import analyze_candidate


ARCHIVE = Path(__file__).resolve().parents[2] / "meme" / "evidence"
BKK = ZoneInfo("Asia/Bangkok")
MINT = "4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta"


def _reference_candidate(**overrides):
    base = {
        "mint": MINT, "pattern": "MULTIPLE",
        "source_signal_id": "confirmed-v1-source",
        "source_signal_at": 1000, "latest_at": 1010, "latest_buy_at": 1000,
        "latest_signature": "source-root-signed-swap",
        "latest_side": "BUY", "position_state": "OPEN",
        "buy_count": 2, "sell_count": 0,
        "latest_buy_price_usdc": "0.010",
        "latest_buy_price_status": "USDC_DIRECT",
    }
    base.update(overrides)
    return base


def _mark(**overrides):
    data = {
        "mint": MINT, "chain": "solana", "source": "PROVENANCE_TEST_POOL",
        "observed_at": 1200, "price_usdc_per_token": "0.012",
    }
    data.update(overrides)
    return data


def _analysis(candidate=None, market=None, **kwargs):
    return analyze_candidate(
        candidate or _reference_candidate(), as_of=1300,
        market=market, max_market_age_seconds=300, **kwargs,
    )


def test_valid_provenance_reference_reports_difference_not_trade_advice():
    x = _analysis(market=_mark())
    assert x["price"]["status"] == "COMPARABLE_REFERENCE_CHANGE"
    assert x["price"]["change_pct_vs_last_verified_buy"] == "20.0000"
    assert x["price"]["basis"] == "REFERENCE_PRICE_ONLY_NOT_EXECUTABLE_QUOTE_OR_PNL"
    assert "PRICE_ABOVE_VERIFIED_FRANK_BUY_REFERENCE" in x["facts"]
    assert x["execution_assessment"] == "NOT_ASSESSED_NO_USER_AMOUNT"
    assert x["order_amount_usdc"] is None
    assert x["user_order_authorized"] is False
    assert x["alert_delivery_authorized"] is False
    assert "BUY" not in x["suggested_action"]


def test_multiple_source_facts_and_sell_warning_survive_without_market():
    x = _analysis(candidate=_reference_candidate(
        latest_side="SELL", sell_count=1,
    ))
    assert "V1_SOURCE_MULTIPLE" in x["facts"]
    assert "FRANK_LATEST_ACTION_SELL" in x["facts"]
    assert "FRANK_SELL_OBSERVED_REVIEW_RISK" in x["facts"]
    assert "MARKET_REFERENCE_MISSING" in x["missing"]
    assert x["price"]["change_pct_vs_last_verified_buy"] is None


@pytest.mark.parametrize("market,expected", [
    (None, "PRICE_UNAVAILABLE"),
    (_mark(mint="different-mint"), "PRICE_SOURCE_MISMATCH"),
    (_mark(chain="ethereum"), "PRICE_SOURCE_MISMATCH"),
    (_mark(observed_at=1600), "PRICE_FROM_FUTURE"),
    (_mark(observed_at=999), "PRICE_STALE"),
    (_mark(price_usdc_per_token="NaN"), "PRICE_SOURCE_UNVERIFIED"),
    (_mark(price_usdc_per_token="0"), "PRICE_SOURCE_UNVERIFIED"),
    (_mark(source=""), "PRICE_SOURCE_UNVERIFIED"),
])
def test_missing_stale_future_or_wrong_market_never_generates_price_pct(market, expected):
    x = _analysis(market=market)
    assert x["price"]["status"] == expected
    assert x["price"]["change_pct_vs_last_verified_buy"] is None
    assert not any(s.startswith("PRICE_ABOVE") for s in x["facts"])


@pytest.mark.parametrize("bad_status,bad_price", [
    ("SOL_EVENT_TIME_USDC_UNAVAILABLE", "0.010"),
    ("QUOTE_PRICE_UNAVAILABLE", "0.010"),
    ("COMPOSITE_QUOTE_PRICE_UNAVAILABLE", "0.010"),
    ("USDC_DIRECT", "Infinity"),
    ("USDC_DIRECT", "-1"),
    ("USDC_DIRECT", None),
])
def test_noncomparable_frank_purchase_price_never_creates_a_return(bad_status,bad_price):
    x = _analysis(candidate=_reference_candidate(
        latest_buy_price_status=bad_status,
        latest_buy_price_usdc=bad_price,
    ), market=_mark())
    assert x["price"]["status"] == "VERIFIED_BUY_REFERENCE_MISSING"
    assert x["price"]["change_pct_vs_last_verified_buy"] is None
    assert "VERIFIED_COMPARABLE_FRANK_BUY_PRICE_UNAVAILABLE" in x["missing"]


def test_future_buy_or_source_signal_is_not_available_in_prior_replay():
    x = _analysis(
        candidate=_reference_candidate(
            latest_at=1400,latest_buy_at=1400,
            source_signal_at=1400,latest_side="SELL",
        ),
        market=_mark(),
    )
    assert x["latest_signature"] is None
    assert x["source_signal_id"] is None
    assert "CANDIDATE_EVENT_AFTER_AS_OF" in x["missing"]
    assert x["price"]["change_pct_vs_last_verified_buy"] is None
    assert not any(s=="FRANK_SELL_OBSERVED_REVIEW_RISK" for s in x["facts"])


@pytest.mark.parametrize("invalid_age", [0,-1,True,1.5,"600",None])
def test_market_freshness_limit_must_be_explicit_positive_integer(invalid_age):
    with pytest.raises(ValueError,match="MARKET_FRESHNESS_LIMIT_REQUIRED"):
        analyze_candidate(
            _reference_candidate(),as_of=1300,
            market=_mark(),max_market_age_seconds=invalid_age,
        )


def test_reentry_does_not_promote_into_frozen_accumulation_signal():
    x=_analysis(candidate=_reference_candidate(
        pattern="REENTRY_WATCH",source_signal_id=None,
        source_signal_at=1010,
    ))
    assert "REENTRY_OBSERVE_ONLY" in x["facts"]
    assert not any(k.startswith("V1_SOURCE_") for k in x["facts"])


def test_archived_six_lot_results_are_outcomes_not_trigger_time_facts():
    evidence = json.loads((ARCHIVE / "frank-six-observed-roundtrips-2026-10-10.json").read_text())
    assert evidence["sampling"].startswith("PURPOSIVE_NONRANDOM")
    assert len(evidence["case_results"]) == 6
    seen = set()
    for idx, lot in enumerate(evidence["case_results"]):
        assert lot["mint"] not in seen
        seen.add(lot["mint"])
        at = datetime.strptime(lot["signal_trigger_bkk"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=BKK).timestamp()
        last_exit = datetime.strptime(lot["exit_last_bkk"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=BKK).timestamp()
        assert at < last_exit
        # Only source facts available at trigger: archived lot's eventual exit
        # and observed quote-net profit are deliberately NOT supplied to P2.
        x = analyze_candidate(
            {"mint":lot["mint"],"pattern":"UNKNOWN",
             "latest_side":"UNKNOWN","latest_at":at},
            as_of=at,market=None,max_market_age_seconds=300,
        )
        assert x["mint"] == lot["mint"]
        assert x["price"]["change_pct_vs_last_verified_buy"] is None
        assert x["latest_side"] == "UNVERIFIED"
        assert x["execution_assessment"] == "NOT_ASSESSED_NO_USER_AMOUNT"
        assert x["latest_signature"] is None
    assert len(seen) == 6


def test_archived_six_finalized_balances_never_imply_new_buy_or_current_usd_value():
    evidence = json.loads((ARCHIVE / "frank-d0-six-mint-finalized-2026-10-11.json").read_text())
    assert evidence["total_checked"] == 6
    assert evidence["nonzero_count"] == 2
    assert len(evidence["records"]) == 6
    seen=set()
    for rec in evidence["records"]:
        assert rec["mint"] not in seen
        seen.add(rec["mint"])
        x = analyze_candidate(
            {"mint":rec["mint"],"current_raw":rec["raw_balance"],
             "position_state":"UNKNOWN"},
            as_of=1791676800,market=None,max_market_age_seconds=300,
        )
        assert "LATEST_ACTION_NOT_PROVEN" in x["missing"]
        assert x["latest_signature"] is None
        assert x["price"]["change_pct_vs_last_verified_buy"] is None
        assert x["price"]["market_price_usdc"] is None
        assert "FRANK_LATEST_ACTION_BUY" not in x["facts"]
        assert rec["executable_usd_value_status"] == "PRICE_UNAVAILABLE_NOT_ASSUMED_ZERO"
    assert len(seen)==6
