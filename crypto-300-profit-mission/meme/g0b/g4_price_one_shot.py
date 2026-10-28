"""Frank G4: specifically authorized, one-shot, free public historical OHLCV probe.

This is a research-only, price-availability probe, NOT actual follower
executability, independent OOS, or a profit/return recommendation.
No network unless the CLI has --execute. Six frozen cases, at most 18
public GET attempts, no retries, no RPC, no private Mac inputs, no schedule.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re

from g0b_gecko_one_shot import (
    PINNED_BLOB_SHA1, STUDY, MIN_SPACING_SECONDS, PublicGet, StopPilot,
    load_manifest, select_pool, extract_bars, close_proxy, utc,
)

HERE = Path(__file__).resolve().parent
LOTS = HERE.parent / "evidence/frank-six-observed-roundtrips-2026-10-10.json"
PINNED_LOTS_BLOB = "b44cc2140927246f9a428c8c455a6793eb80b662"
MAX_HTTP = 18
LAGS = (30, 120, 300, 900, 3600)
BKK = timezone(timedelta(hours=7))
BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,50}$")
# Order and membership are source-committed before requesting the first bar.
CASES = (
    ("M2", "FORMAL_MULT", "MULT_PLUS_24H"),
    ("M3", "FORMAL_MULT", "MULT_PLUS_24H"),
    ("M4", "FORMAL_MULT", "MULT_PLUS_24H"),
    ("A2", "ACC", "FRANK_LAST_OBSERVED_EXIT"),
    ("A3", "ACC", "FRANK_LAST_OBSERVED_EXIT"),
    ("C3", "NO_SIGNAL_BUY_CONTROL", "BUY_PLUS_24H"),
)


def git_blob_sha1(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def get_manifest():
    baseline, baseline_sha = load_manifest()  # validates archived study git blob
    study = json.loads(STUDY.read_bytes())
    lots_raw = LOTS.read_bytes()
    if git_blob_sha1(lots_raw) != PINNED_LOTS_BLOB:
        raise ValueError("LOT_EVIDENCE_BLOB_DRIFT")
    root_lots = json.loads(lots_raw)["case_results"]
    by_id = {row["id"]: row for row in baseline}
    if len(by_id) != 12:
        raise ValueError("BASELINE_MANIFEST_DRIFT")
    signals = study["models"]["M3"]["signals"]
    if len(signals) != 32:
        raise ValueError("SIGNAL_ARCHIVE_DRIFT")
    manifest = []
    for item_id, entry_kind, exit_kind in CASES:
        item = by_id[item_id]
        mint, episode = item["mint"], item["episode_id"]
        related = [s for s in signals if s["episode_id"] == episode]
        if any(s["mint"] != mint for s in related):
            raise ValueError("EPISODE_MINT_MISMATCH")
        acc = [s for s in related if s["signal_type"] == "FRANK_ACCUMULATION_SIGNAL"]
        mult = [s for s in related if s["signal_type"] == "FRANK_MULTIPLE_SIGNAL"]
        if entry_kind == "FORMAL_MULT":
            if len(acc) != 1 or len(mult) != 1:
                raise ValueError("FORMAL_MULT_MISSING")
            t0 = int(mult[0]["triggered_at"])
            if t0 - int(acc[0]["triggered_at"]) <= 3600:
                raise ValueError("FORMAL_MULT_NOT_LATER_THAN_1H")
            if int(item["t0"]) != int(acc[0]["triggered_at"]):
                raise ValueError("OLD_PILOT_CLOCK_NOT_ACC")
            exit_target = t0 + 86400
        elif entry_kind == "ACC":
            if len(acc) != 1 or mult:
                raise ValueError("ACC_ONLY_STATUS_DRIFT")
            t0 = int(acc[0]["triggered_at"])
            if t0 != int(item["t0"]):
                raise ValueError("ACC_CLOCK_DRIFT")
            root = [row for row in root_lots if row["mint"] == mint]
            if len(root) != 1:
                raise ValueError("ROOT_LOT_EXIT_MISSING_OR_DUPLICATE")
            bkk = datetime.strptime(root[0]["exit_last_bkk"], "%Y-%m-%d %H:%M:%S")
            exit_target = int(bkk.replace(tzinfo=BKK).timestamp())
            if not t0 < exit_target < t0 + 86400:
                raise ValueError("ROOT_EXIT_NOT_EARLY_OR_BAD_TIMEZONE")
        elif entry_kind == "NO_SIGNAL_BUY_CONTROL":
            if related or any(s["mint"] == mint for s in signals):
                raise ValueError("CONTROL_HAS_FROZEN_SIGNAL")
            t0 = int(item["t0"])
            exit_target = t0 + 86400
        else:
            raise ValueError("UNKNOWN_CASE_KIND")
        manifest.append({
            "id": item_id,
            "mint": mint,
            "episode_id": episode,
            "kind": entry_kind,
            "entry_time": t0,
            "entry_utc": utc(t0),
            "exit_policy": exit_kind,
            "exit_target": exit_target,
            "exit_utc": utc(exit_target),
            "old_pilot_t0": item["t0"],
        })
    if len(manifest) != 6 or len({x["mint"] for x in manifest}) != 6:
        raise ValueError("DUPLICATE_OR_MISSING_STUDY_CASE")
    digest = hashlib.sha256(json.dumps(
        manifest, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    return manifest, digest, baseline_sha


def assess_lags(entry_bars, exit_bars, entry_time, exit_time):
    exit_px = close_proxy(exit_bars, exit_time)
    result = {}
    for lag in LAGS:
        target = entry_time + lag
        row = {"lag_seconds": lag, "entry_target_utc": utc(target),
               "entry": None, "exit": exit_px, "gross_candle_close_proxy_pct": None}
        if target >= exit_time:
            row["status"] = "ENTRY_AT_OR_AFTER_EXIT"
        else:
            row["entry"] = close_proxy(entry_bars, target)
            if row["entry"] is None or exit_px is None:
                row["status"] = "MISSING_NONZERO_VOLUME_CANDLE"
            elif row["entry"]["price_known_no_earlier_than"] >= exit_time:
                row["status"] = "ENTRY_CANDLE_KNOWN_AT_OR_AFTER_EXIT"
            else:
                ratio = exit_px["close_usd"] / row["entry"]["close_usd"]
                if not math.isfinite(ratio) or ratio <= 0:
                    row["status"] = "INVALID_PRICE_RATIO"
                else:
                    row["status"] = "CANDLE_PROXY_ONLY_NOT_EXECUTABLE"
                    row["gross_candle_close_proxy_pct"] = round((ratio - 1) * 100, 6)
        result[str(lag)] = row
    return result


def run(*, execute=False, max_http=MAX_HTTP, out_dir=None):
    if not 1 <= max_http <= MAX_HTTP:
        raise ValueError("MAX_HTTP_MUST_BE_WITHIN_1_TO_18")
    manifest, manifest_hash, old_manifest_hash = get_manifest()
    result = {
        "status": "OFFLINE_PREDECLARATION_ONLY",
        "research_scope": "SIX_EVENT_CLOCK_CASES_OHLCV_NOT_EXECUTABLE",
        "study_blob": PINNED_BLOB_SHA1,
        "lots_blob": PINNED_LOTS_BLOB,
        "old_pilot_manifest_sha256": old_manifest_hash,
        "manifest_sha256": manifest_hash,
        "cases_predeclared": manifest,
        "max_http": max_http,
        "min_spacing_seconds": MIN_SPACING_SECONDS,
        "http_attempts": [],
        "cases": [],
        "raw_provider_responses": [],
        "notes": [
            "Price is the next future-known one-minute CLOSE, not a fill at event time.",
            "First-page surviving pool selection is hindsight-biased.",
            "Minute pool volumes do not prove executable liquidity.",
            "Frank's original-lot exit timestamp is not a follower exit time.",
            "No user notional is specified; route, gas, impact, slippage, fills are absent.",
            "C3 is an outcome- and reconstruction-biased non-signal control.",
            "Missing prices or quotes remain null; not zero returns.",
            "No fresh RPC, wallet, notifications, scheduler or trading.",
        ],
        "verified_executable_follower_quotes": 0,
        "strategy_verdict": "NEED_MORE_DATA",
    }
    if not execute:
        result["summary"] = {"requests": 0, "cases_predeclared": len(manifest)}
        return result

    transport = PublicGet(max_calls=max_http)
    try:
        result["status"] = "REQUESTS_STARTED"
        for item in manifest:
            case = {**item, "pool": None, "state": "NO_POOL",
                    "lags": {}, "entry_bars": None, "exit_bars": None}
            result["cases"].append(case)
            raw_record = {"id": item["id"], "pool_discovery_raw": None,
                          "entry_ohlcv_raw": None, "exit_ohlcv_raw": None}
            result["raw_provider_responses"].append(raw_record)
            pool_doc = transport.get(
                "/networks/solana/tokens/" + item["mint"] + "/pools",
                {"page": 1}
            )
            raw_record["pool_discovery_raw"] = pool_doc
            if pool_doc is None:
                case["state"] = "POOL_DISCOVERY_HTTP_MISSING"
                continue
            pool = select_pool(pool_doc, item["mint"], item["entry_time"])
            if pool is None:
                case["state"] = "NO_PREEXISTING_POOL_IN_CURRENT_RANKED_FIRST_PAGE"
                continue
            if not BASE58.fullmatch(pool["address"]):
                raise StopPilot("UNSAFE_POOL_ADDRESS_FROM_PROVIDER")
            case["pool"] = pool
            path = "/networks/solana/pools/" + pool["address"] + "/ohlcv/minute"
            options = {"aggregate": 1, "currency": "usd",
                       "token": pool["side"], "include_empty_intervals": "false"}
            entry_doc = transport.get(path, {**options,
                "before_timestamp": item["entry_time"] + 75 * 60,
                "limit": 120})
            raw_record["entry_ohlcv_raw"] = entry_doc
            if entry_doc is None:
                case["state"] = "ENTRY_OHLCV_HTTP_MISSING"
                continue
            exit_doc = transport.get(path, {**options,
                "before_timestamp": item["exit_target"] + 6 * 60,
                "limit": 30})
            raw_record["exit_ohlcv_raw"] = exit_doc
            if exit_doc is None:
                case["state"] = "EXIT_OHLCV_HTTP_MISSING"
                continue
            entry_bars = extract_bars(entry_doc)
            exit_bars = extract_bars(exit_doc)
            case["entry_bars"] = len(entry_bars)
            case["exit_bars"] = len(exit_bars)
            case["lags"] = assess_lags(entry_bars, exit_bars,
                                       item["entry_time"], item["exit_target"])
            vals = list(case["lags"].values())
            case["state"] = (
                "FIVE_LAGS_CANDLE_PROXIES" if all(
                    x["status"] == "CANDLE_PROXY_ONLY_NOT_EXECUTABLE"
                    for x in vals
                ) else "PARTIAL_OR_MISSING_CANDLE_PROXIES"
            )
        result["status"] = "ALL_FROZEN_CASES_VISITED"
    except StopPilot as exc:
        result["status"] = "HALTED_PARTIAL"
        result["stop_reason"] = str(exc)
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        result["status"] = "HALTED_PARTIAL"
        result["stop_reason"] = "UNEXPECTED_PROVIDER_OR_SOURCE_SCHEMA"
        result["error_type"] = type(exc).__name__
    finally:
        result["http_attempts"] = transport.attempts
        if len(transport.attempts) > MAX_HTTP:
            raise AssertionError("EXCEEDED_18_HTTP_HARD_CAP")
        result["summary"] = {
            "predeclared_cases": len(manifest),
            "visited_cases": len(result["cases"]),
            "http_attempts": len(transport.attempts),
            "http_status_counts": dict(Counter(
                str(x["status"]) for x in transport.attempts
            )),
            "case_states": dict(Counter(
                x["state"] for x in result["cases"]
            )),
            "price_proxy_not_executable": True,
            "verified_executable_follower_quotes": 0,
            "strategy_verdict": "NEED_MORE_DATA",
        }
        if out_dir:
            directory = Path(out_dir)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "g4_price_once_receipts.json").write_text(
                json.dumps(result, sort_keys=True, indent=2, allow_nan=False),
                encoding="utf-8"
            )
        print("G4_ONE_SHOT_SUMMARY_JSON", json.dumps({
            "status": result["status"],
            "manifest_sha256": manifest_hash,
            "summary": result["summary"],
            "stop_reason": result.get("stop_reason"),
        }, sort_keys=True))
        for case in result["cases"]:
            print("G4_ONE_SHOT_CASE_JSON", json.dumps({
                "id": case["id"], "state": case["state"],
                "exit_policy": case["exit_policy"],
                "lag_status": {k: v["status"] for k, v in case["lags"].items()},
                "lag_candle_gross_pct": {
                    k: v["gross_candle_close_proxy_pct"]
                    for k, v in case["lags"].items()
                },
            }, sort_keys=True))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-http", type=int, default=MAX_HTTP)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    run(execute=args.execute, max_http=args.max_http, out_dir=args.out_dir)


if __name__ == "__main__":
    main()
