#!/usr/bin/env python3
"""Stage111 immutable all-519 historical original 7d official 1m source replay.
Source absence is censoring, never a losing trade. Read-only research only.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from collections import Counter
from datetime import date
from decimal import Decimal
import json
from pathlib import Path

try:
    import monster_v4_stage111_full519_source_census as src
    import monster_v4_stage111_persistent_recovery_core as core
    import monster_v4_stage110_d1_continuous_confirm as stage110
except ImportError:
    from scripts import monster_v4_stage111_full519_source_census as src
    from scripts import monster_v4_stage111_persistent_recovery_core as core
    from scripts import monster_v4_stage110_d1_continuous_confirm as stage110

old = stage110.old
MIN = core.MIN
SCHEMA = "MONSTER_STAGE111_REAL_FULL519_FROZEN_V1_OFFICIAL_1M_REPLAY"
DAYMS = 86_400_000


def official_case(x: dict, archived: dict | None, reader=None) -> dict:
    if reader is None:
        reader = old.publisher.verified_1m_day
    d0 = old.utc_ms(x["D0_FIRST_UTC"])
    end = old.utc_ms(x["date"] + "T06:00:00Z") + 7 * DAYMS
    if not d0 < end:
        raise ValueError("STAGE111_D0_AFTER_ANCHOR_END")
    d1 = old.utc_ms(x["D1_FIRST_UTC"]) if x["D1_FIRST_UTC"] else None
    needed = src.date_days(src.iso(x["D0_FIRST_UTC"]) + src.MINUTE,
                           src.iso(x["date"] + "T06:00:00Z") + 7 * src.DAY)
    known_1m = ({r["date"]: r["zip_sha256"]
                 for r in archived["source_days_real_official_sha"]}
                if archived else {})
    # Stage83 prior official ZIP receipts are 3m source, NOT 1m:
    # never try to SHA-match a 3m archive to a 1m archive.
    receipts = []
    lookup = {}
    missing_day = None
    missing_why = None
    for day in needed:
        try:
            bars, proof = reader(x["symbol"], date.fromisoformat(day))
        except Exception as exc:
            # No source means the case is censored/unavailable; never treat
            # retrieval failure as a zero return. Already pinned 1m receipts
            # failing download are explicitly identified for recheck.
            missing_day = day
            missing_why = ("PINNED_MINUTE_SOURCE_TEMPORARILY_UNAVAILABLE" if
                           day in known_1m else
                           "OFFICIAL_MINUTE_SOURCE_UNAVAILABLE")
            break
        if (proof.get("date") != day
                or proof.get("verified_official_publisher_SHA256") is not True
                or len(proof.get("zip_sha256", "")) != 64):
            raise ValueError("STAGE111_OFFICIAL_PUBLISHER_PROOF_INVALID")
        if day in known_1m and known_1m[day] != proof["zip_sha256"]:
            raise ValueError("STAGE111_PREVIOUS_STAGE110_1M_PUBLISHER_SHA_DRIFT")
        receipts.append({"date": day, "zip_sha256": proof["zip_sha256"],
                         "bars": len(bars),
                         "verified_official_publisher_SHA256": True})
        if len(bars) != 1440:
            missing_day, missing_why = day, "INCOMPLETE_OFFICIAL_ONE_MINUTE_DAY"
            break
        for bar in bars:
            if bar[0] in lookup:
                raise ValueError("STAGE111_DUPLICATE_SOURCE_MINUTE")
            lookup[bar[0]] = bar
    contiguous = []
    next_open = d0 + MIN
    while next_open < end:
        row = lookup.get(next_open)
        if row is None:
            break
        contiguous.append(row)
        next_open += MIN
    state = core.replay(d0, end, contiguous, d1)
    if missing_day is not None and state["source_status"] != "SOURCE_CENSORED":
        # A late missing date may start only after the anchor end; the
        # prefix is still complete. Otherwise a source absence is censoring.
        if next_open < end:
            raise ValueError("STAGE111_MISSING_SOURCE_MISCLASSIFIED_COMPLETE")
    major = x["true_first_2x_HIGH_UTC_EVALUATION_ONLY"]
    first_cross = old.utc_ms(major) if major else None
    priority = [e for e in state["events"] if e["state"] == "PRIORITY"]
    early = ([e for e in priority
              if first_cross is not None and
              first_cross - e["observable_ms"] >= 5 * MIN])
    economics = []
    for event in priority:
        t = event["next_1m_open_ms"]
        record = {"priority_visible_ms": event["observable_ms"],
                  "next_open_ms": t, "status": "CENSORED_OR_NO_TRADE",
                  "gross_24h_price_pct": None,
                  "real_executable_net_profit": "UNKNOWN"}
        if t + 1440 * MIN <= end:
            bars = [lookup.get(t + i * MIN) for i in range(1440)]
            if (all(z is not None for z in bars)
                    and bars[0][6] > 0 and bars[0][5] > 0
                    and bars[-1][6] > 0 and bars[-1][5] > 0
                    and bars[0][1] > 0):
                entry, exit_close = bars[0][1], bars[-1][4]
                gross = (exit_close / entry - 1) * 100
                low = min(z[3] for z in bars)
                record.update({
                    "status": "PRICE_ONLY_PROXY_COMPLETE",
                    "price_entry_next_1m_open": str(entry),
                    "price_exit_24h_final_1m_close": str(exit_close),
                    "gross_24h_price_pct": str(gross),
                    "low_minute_24h_drawdown_from_entry_pct":
                        str((low / entry - 1) * 100),
                    "synthetic_fee_20bps_each_side_pct":
                        str(((exit_close / entry) *
                             (Decimal("0.998") / Decimal("1.002")) - 1) * 100),
                    "real_executable_net_profit": "UNKNOWN",
                })
        economics.append(record)
    return {
        "date": x["date"], "symbol": x["symbol"],
        "identity": x["identity"],
        "D0_FIRST_UTC": x["D0_FIRST_UTC"],
        "original_D1_FIRST_UTC": x["D1_FIRST_UTC"],
        "original_D0_early5_2x_EVAL_ONLY": x["D0_at_least_5m_before_2x"],
        "original_D1_early5_2x_EVAL_ONLY": x["D1_at_least_5m_before_2x"],
        "original_first_2x_HIGH_EVAL_ONLY": major,
        "new_first_priority_early5_2x": bool(early),
        "new_first_priority_visible_ms": priority[0]["observable_ms"] if priority else None,
        "source_days_needed": len(needed),
        "source_days_downloaded_verified_1m": receipts,
        "source_first_unavailable_day": missing_day,
        "source_first_unavailable_reason": missing_why,
        "causal_state": state,
        "price_only_24h": economics,
        "full_7d_observation": state["complete_fixed_anchor_window"],
        "research_exposed_data_not_OOS": True,
        "actual_execution": "UNKNOWN",
    }


def frozen():
    items, prior = src.frozen()
    src.analyze(items, prior)
    by_prior = {(r["date"], r["symbol"]): r for r in prior["all_source_cases"]}
    return items, by_prior


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--shard", type=int)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if not args.date or args.shard is None or args.out is None:
        ap.error("--date --shard --out are required; historical read-only mode")
    if args.workers not in range(1, 5):
        raise ValueError("STAGE111_WORKER_COUNT")
    cases, prior = frozen()
    group = old.shard_rows(args.date, args.shard, cases)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(official_case, x, prior.get((x["date"], x["symbol"]))):x
                for x in group}
        for future in concurrent.futures.as_completed(jobs):
            x = jobs[future]
            try:
                y = future.result()
            except Exception as exc:
                raise RuntimeError("STAGE111_OFFICIAL_CASE_ERROR " + x["date"] +
                                   " " + x["symbol"] + " " + str(exc)) from exc
            results.append(y)
            print("STAGE111_REAL_1M_SOURCE " + x["date"] + " " + x["symbol"] +
                  " " + y["causal_state"]["source_status"], flush=True)
    if len(results) != len(group):
        raise ValueError("STAGE111_CASE_LOSS")
    packet = {"schema": SCHEMA, "date": args.date, "shard": args.shard,
              "source_stage83_git_blob": src.PIN83,
              "source_stage110_git_blob": src.PIN110,
              "source_input_population": 519,
              "source_original_D1_population": 305,
              "all_research_not_OOS": True,
              "real_executable_profit": "UNKNOWN",
              "monster_deployment": "NO_GO",
              "rows": sorted(results, key=lambda z: z["symbol"])}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    print("STAGE111_SHARD_RESEARCH_RESULT " + json.dumps({
        "date": args.date, "shard": args.shard,
        "cases": len(results),
        "source_window_complete":
            sum(z["full_7d_observation"] for z in results),
        "priorities": sum(z["causal_state"]["priority_count"] for z in results)}))


if __name__ == "__main__":
    main()
