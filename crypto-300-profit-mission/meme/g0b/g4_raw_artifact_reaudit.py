"""Independent OFFLINE replay of already-saved Frank G4 raw OHLCV artifact.

The original (2026-10-28) receipt is intentionally IMMUTABLE. Original rules
are replayed for lineage, but corrected primary results reject all candle-close
lookahead at the precommitted exit anchor. Secondary pre-anchor bar analysis is
a RETROSPECTIVE SENSITIVITY, not the original pre-registered primary analysis.

No provider/network access, no import of G4 strategy or old price helpers.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

MANIFEST_SHA256 = "5407db116ce0b755e0b38b1ce67331e6ac4b87a875e60665f63f75e351fe38ed"
EXPECTED_IDS = ("M2", "M3", "M4", "A2", "A3", "C3")
LAGS = (30, 120, 300, 900, 3600)
CANDLE_SECONDS = 60
MAX_STALENESS_SECONDS = 180


def decode_bars(doc):
    source = (((doc or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    out = {}
    for record in source:
        if not isinstance(record, list) or len(record) < 6:
            continue
        try:
            t, price, volume = int(record[0]), float(record[4]), float(record[5])
        except (ValueError, OverflowError, TypeError):
            continue
        if (t not in out and math.isfinite(price) and price > 0
                and math.isfinite(volume) and volume >= 0):
            out[t] = (t, price, volume)
    return sorted(out.values())


def old_next_close(bars, target):
    eligible = [b for b in bars if target <= b[0] <= target + 180 and b[2] > 0]
    return eligible[0] if eligible else None


def preanchor_close(bars, anchor):
    """Nearest nonzero-volume fully completed 1m close STRICTLY BEFORE anchor.

    Retrospective sensitivity only; this rule was not pre-registered.
    Reject stale bars beyond 180s rather than treat old prints as current.
    """
    eligible = [b for b in bars if b[2] > 0 and
                0 < anchor - (b[0] + CANDLE_SECONDS) <= MAX_STALENESS_SECONDS]
    return eligible[-1] if eligible else None


def rate(entry, exiting):
    ratio = exiting[1] / entry[1]
    return round((ratio - 1) * 100, 6) if math.isfinite(ratio) and ratio > 0 else None


def replay(receipt):
    assert receipt["status"] == "ALL_FROZEN_CASES_VISITED", "unexpected receipt status"
    assert receipt["manifest_sha256"] == MANIFEST_SHA256, "original manifest changed"
    ledger = receipt["http_attempts"]
    assert len(ledger) == 18 and all(x["status"] == 200 for x in ledger), "unexpected provider ledger"
    cases, raw = receipt["cases"], receipt["raw_provider_responses"]
    assert tuple(x["id"] for x in cases) == EXPECTED_IDS, "case identity/order drift"
    assert tuple(x["id"] for x in raw) == EXPECTED_IDS, "raw identity/order drift"
    records = []
    for case, source in zip(cases, raw):
        entry = decode_bars(source["entry_ohlcv_raw"])
        exit_bars = decode_bars(source["exit_ohlcv_raw"])
        assert len(entry) == case["entry_bars"] and len(exit_bars) == case["exit_bars"], "bar count drift"
        anchor = int(case["exit_target"])
        original_exit = old_next_close(exit_bars, anchor)
        alternative_exit = preanchor_close(exit_bars, anchor)
        assert set(case["lags"]) == set(map(str, LAGS)), "lag set drift"
        for lag in LAGS:
            key = str(lag)
            target = int(case["entry_time"]) + lag
            old_entry = old_next_close(entry, target) if target < anchor else None

            if target >= anchor:
                expected_old = "ENTRY_AT_OR_AFTER_EXIT"
            elif old_entry is None or original_exit is None:
                expected_old = "MISSING_NONZERO_VOLUME_CANDLE"
            elif old_entry[0] + CANDLE_SECONDS >= anchor:
                expected_old = "ENTRY_CANDLE_KNOWN_AT_OR_AFTER_EXIT"
            else:
                expected_old = "CANDLE_PROXY_ONLY_NOT_EXECUTABLE"
            observed = case["lags"][key]
            assert observed["status"] == expected_old, f"old status not reproducible {case['id']}+{lag}"
            old_rate = rate(old_entry, original_exit) if expected_old == "CANDLE_PROXY_ONLY_NOT_EXECUTABLE" else None
            if old_rate is not None:
                assert observed["gross_candle_close_proxy_pct"] is not None
                assert abs(observed["gross_candle_close_proxy_pct"] - old_rate) < 1e-6, "old gross % drift"
            else:
                assert observed["gross_candle_close_proxy_pct"] is None, "old missing drift"

            # PRIMARY: preserve every original entry/exit query and strict prereg.
            # The next candle at/after exit anchor is NOT known before it.
            if target >= anchor:
                strict_status = "ENTRY_AT_OR_AFTER_EXIT"
            elif old_entry is None or original_exit is None:
                strict_status = "MISSING_NONZERO_VOLUME_CANDLE"
            elif old_entry[0] + CANDLE_SECONDS >= anchor:
                strict_status = "ENTRY_CANDLE_KNOWN_AT_OR_AFTER_EXIT"
            elif original_exit[0] + CANDLE_SECONDS >= anchor:
                strict_status = "EXIT_CANDLE_KNOWN_AFTER_EXIT"
            else:
                strict_status = "CANDLE_PROXY_ONLY_NOT_EXECUTABLE"
            strict_rate = rate(old_entry, original_exit) if strict_status == "CANDLE_PROXY_ONLY_NOT_EXECUTABLE" else None

            # SECONDARY: a pre-anchor completed close (<=180s stale) is a
            # separately labelled retrospective price proxy, never a fill.
            if target >= anchor:
                alt_status = "ENTRY_AT_OR_AFTER_EXIT"
            elif old_entry is None or alternative_exit is None:
                alt_status = "MISSING_EITHER_ENTRY_OR_PREANCHOR_EXIT_BAR"
            elif old_entry[0] + CANDLE_SECONDS >= anchor:
                alt_status = "ENTRY_CANDLE_KNOWN_AT_OR_AFTER_EXIT"
            else:
                alt_status = "RETROSPECTIVE_PREANCHOR_CLOSE_SENSITIVITY_ONLY"
            alt_rate = rate(old_entry, alternative_exit) if alt_status == "RETROSPECTIVE_PREANCHOR_CLOSE_SENSITIVITY_ONLY" else None

            result = {
                "id": case["id"], "lag_seconds": lag,
                "anchor_epoch": anchor,
                "original_logged_status": observed["status"],
                "original_gross_pct": observed["gross_candle_close_proxy_pct"],
                "primary_strict_status": strict_status, "primary_strict_gross_pct": strict_rate,
                "secondary_status": alt_status, "secondary_gross_pct": alt_rate,
                "entry_candle_start_epoch": old_entry[0] if old_entry else None,
                "entry_minute_volume_usd": old_entry[2] if old_entry else None,
                "original_exit_candle_start_epoch": original_exit[0] if original_exit else None,
                "original_exit_known_epoch": original_exit[0] + CANDLE_SECONDS if original_exit else None,
                "secondary_exit_candle_start_epoch": alternative_exit[0] if alternative_exit else None,
                "secondary_exit_known_epoch": alternative_exit[0] + CANDLE_SECONDS if alternative_exit else None,
                "secondary_exit_bar_staleness_seconds": anchor - (alternative_exit[0] + CANDLE_SECONDS) if alternative_exit else None,
                "secondary_exit_minute_volume_usd": alternative_exit[2] if alternative_exit else None,
            }
            records.append(result)
            print("G4_CAUSAL_CORRECTION_ROW_JSON", json.dumps(result, sort_keys=True))
    assert len(records) == 30
    originally_priced = [r for r in records if r["original_logged_status"] == "CANDLE_PROXY_ONLY_NOT_EXECUTABLE"]
    causal_rejected = [r for r in originally_priced if r["primary_strict_status"] == "EXIT_CANDLE_KNOWN_AFTER_EXIT"]
    primary_priced = [r for r in records if r["primary_strict_gross_pct"] is not None]
    secondary_priced = [r for r in records if r["secondary_gross_pct"] is not None]
    assert len(originally_priced) == 16 and len(causal_rejected) == 16, "unexpected causal counterexample count"
    assert len(primary_priced) == 0, "old premature exit prices leaked to strict result"
    assert all(r["secondary_exit_known_epoch"] < r["anchor_epoch"] for r in secondary_priced)
    assert all(r["secondary_exit_bar_staleness_seconds"] <= MAX_STALENESS_SECONDS for r in secondary_priced)
    summary = {
        "status": "STRICT_EXIT_CAUSAL_CORRECTION_PASS",
        "historical_artifact_cases": 6, "total_lag_rows": 30,
        "original_priced_rows": len(originally_priced),
        "original_priced_rows_rejected_by_exit_lookahead": len(causal_rejected),
        "strict_preregistered_valid_price_rows": len(primary_priced),
        "secondary_preanchor_sensitivity_rows": len(secondary_priced),
        "new_geckoterminal_get_attempts": 0, "new_solana_rpc_attempts": 0,
        "verified_executable_follower_quotes": 0, "strategy_verdict": "NEED_MORE_DATA",
    }
    print("G4_CAUSAL_CORRECTION_SUMMARY_JSON", json.dumps(summary, sort_keys=True))
    return {"summary": summary, "rows": records}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", required=True)
    p.add_argument("--out", required=True)
    opts = p.parse_args()
    raw = json.loads(Path(opts.receipt).read_text(encoding="utf-8"))
    result = replay(raw)
    Path(opts.out).write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
