"""Offline-only independent bar/volume arithmetic check of the 2026-10-28 G4 artifact.

Input is a previously downloaded GitHub Actions JSON artifact.
No network/GeckoTerminal/RPC, no trading or monitored service imports.
"""
import argparse
import json
import math
from pathlib import Path

MANIFEST_SHA256 = "5407db116ce0b755e0b38b1ce67331e6ac4b87a875e60665f63f75e351fe38ed"
EXPECTED_IDS = ("M2", "M3", "M4", "A2", "A3", "C3")


def decode_bars(doc):
    source = (((doc or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    out = {}
    for row in source:
        if not isinstance(row, list) or len(row) < 6:
            continue
        try:
            timestamp, close, minute_volume = int(row[0]), float(row[4]), float(row[5])
        except (TypeError, ValueError, OverflowError):
            continue
        if timestamp not in out and math.isfinite(close) and close > 0 and math.isfinite(minute_volume) and minute_volume >= 0:
            out[timestamp] = (timestamp, close, minute_volume)
    return sorted(out.values())


def choose(bars, target):
    matches = [x for x in bars if target <= x[0] <= target + 180 and x[2] > 0]
    return matches[0] if matches else None


def recompute(receipt):
    assert receipt["status"] == "ALL_FROZEN_CASES_VISITED", "not a full recorded pilot"
    assert receipt["manifest_sha256"] == MANIFEST_SHA256, "manifest drift"
    attempts = receipt["http_attempts"]
    assert len(attempts) == 18 and all(x["status"] == 200 for x in attempts), "bad source attempt ledger"
    cases = receipt["cases"]
    raw = receipt["raw_provider_responses"]
    assert [x["id"] for x in cases] == list(EXPECTED_IDS)
    assert [x["id"] for x in raw] == list(EXPECTED_IDS)
    rows = []
    for case, origin in zip(cases, raw):
        entry = decode_bars(origin["entry_ohlcv_raw"])
        exiting = decode_bars(origin["exit_ohlcv_raw"])
        assert case["entry_bars"] == len(entry) and case["exit_bars"] == len(exiting), "raw bar count mismatch"
        exit_at = int(case["exit_target"])
        exit_bar = choose(exiting, exit_at)
        assert set(case["lags"]) == {"30", "120", "300", "900", "3600"}, "lag lattice drift"
        for key in sorted(case["lags"], key=int):
            lag = int(key)
            target = int(case["entry_time"]) + lag
            input_bar = choose(entry, target) if target < exit_at else None
            if target >= exit_at:
                expected_status = "ENTRY_AT_OR_AFTER_EXIT"
            elif input_bar is None or exit_bar is None:
                expected_status = "MISSING_NONZERO_VOLUME_CANDLE"
            elif input_bar[0] + 60 >= exit_at:
                expected_status = "ENTRY_CANDLE_KNOWN_AT_OR_AFTER_EXIT"
            else:
                expected_status = "CANDLE_PROXY_ONLY_NOT_EXECUTABLE"
            stored = case["lags"][key]
            assert stored["status"] == expected_status, f"status mismatch {case['id']} {lag}"
            value = None
            if expected_status == "CANDLE_PROXY_ONLY_NOT_EXECUTABLE":
                value = round((exit_bar[1] / input_bar[1] - 1) * 100, 6)
                assert abs(value - stored["gross_candle_close_proxy_pct"]) < 1e-6, f"price mismatch {case['id']} {lag}"
            else:
                assert stored["gross_candle_close_proxy_pct"] is None, "unknown promoted to zero"
            result = {
                "id": case["id"], "lag_seconds": lag, "status": expected_status,
                "gross_candle_close_proxy_pct": value,
                "entry_candle_start_epoch": input_bar[0] if input_bar else None,
                "entry_minute_volume_usd": input_bar[2] if input_bar else None,
                "exit_candle_start_epoch": exit_bar[0] if exit_bar else None,
                "exit_minute_volume_usd": exit_bar[2] if exit_bar else None,
            }
            rows.append(result)
            print("G4_RAW_AUDIT_LAG_JSON", json.dumps(result, sort_keys=True))
    assert len(rows) == 30
    good = [x for x in rows if x["status"] == "CANDLE_PROXY_ONLY_NOT_EXECUTABLE"]
    assert len(good) == 16
    below10 = [x for x in good if min(x["entry_minute_volume_usd"], x["exit_minute_volume_usd"]) < 10]
    summary = {
        "status": "RAW_OFFLINE_RECOMPUTE_PASS", "case_count": 6,
        "total_lags": len(rows), "price_proxy_lags": len(good),
        "minute_volume_under_10_usd_lags": len(below10),
        "new_provider_get_attempts": 0,
        "verified_executable_follower_quotes": 0,
        "strategy_verdict": "NEED_MORE_DATA",
    }
    print("G4_RAW_AUDIT_SUMMARY_JSON", json.dumps(summary, sort_keys=True))
    return {"summary": summary, "rows": rows}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    original = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    checked = recompute(original)
    Path(args.out).write_text(json.dumps(checked, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
