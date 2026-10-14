#!/usr/bin/env python3
"""Stage112 original519 Stage111 source-locked repeated-ignition attribution.

Offline analytical tool. Reads *existing* Stage111 CI shard artifacts and
immutable repo evidence. NO source retrieval, live polling, orders, email,
threshold changes, scheduling or deployment.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
from hashlib import sha1
import json
from pathlib import Path
from statistics import median

try:
    import monster_v4_stage111_full519_aggregate as prior
except ImportError:
    from scripts import monster_v4_stage111_full519_aggregate as prior

SCHEMA = "MONSTER_STAGE112_ORIGINAL519_REPEATED_PRIORITIES_DESCRIPTIVE_V1"
E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
SOURCE_AGG = E / "monster_stage111_real519_persistent_15m_v1_actual_results.json"
PIN_AGG_BLOB = "9473443f407deb5e4c9e7e14d64685b2e8e49cea"
MS_DAY = 86_400_000
MS_MIN = 60_000
SOURCE_WORKFLOW_COMMIT = "760b3605a2d1673a9765d7daeee8ffea62558507"


def git_blob(data: bytes) -> str:
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def frozen_aggregate() -> dict:
    raw = SOURCE_AGG.read_bytes()
    if git_blob(raw) != PIN_AGG_BLOB:
        raise ValueError("STAGE112_PINNED_STAGE111_AGGREGATE_BLOB_CHANGED")
    src = json.loads(raw)
    if (src["original_D0_total"] != 519 or src["original_D1_total"] != 305
            or src["preregistered_gates"]["G3_all_42_attention_days"]["total_priority_events"] != 740
            or src["preregistered_gates"]["G2_28_historical_original_D0_early5_retain"]["new_early5_observed"] != 19):
        raise ValueError("STAGE112_BASELINE_COUNTER_DRIFT")
    return src


def dist(vals: list[Decimal]) -> dict:
    seq = sorted(vals)
    return {
        "complete_price_proxy_n": len(seq),
        "positive_count": sum(z > 0 for z in seq),
        "nonpositive_count": sum(z <= 0 for z in seq),
        "negative_20pct_or_worse": sum(z <= -20 for z in seq),
        "gross_median_pct": str(median(seq)) if seq else None,
        "gross_min_pct": str(seq[0]) if seq else None,
        "gross_max_pct": str(seq[-1]) if seq else None,
        "fee_20bps_each_side_median_pct": (
            str(median([((Decimal(1) + z / 100) *
                (Decimal("0.998") / Decimal("1.002")) - 1) * 100
                for z in seq])) if seq else None),
        "not_real_executable_net": True,
    }


def diagnostic(packets: list[dict], reference: dict) -> dict:
    # Re-run immutable original519 accounting and all 42 historic day bins.
    check = prior.aggregate(packets)
    actual_gates = check["preregistered_gates"]
    ref_gates = reference["preregistered_gates"]
    g2 = "G2_28_historical_original_D0_early5_retain"
    g3 = "G3_all_42_attention_days"
    g4 = "G4_price_only_only"
    for key, fields in (
        (g2, ["D0_early5_total", "new_early5_observed", "censored_before_GT2"]),
        (g3, ["total_priority_events", "counts", "average_observed_per_day",
              "maximum_observed_per_day"]),
        (g4, ["complete_24h_price_proxy_count", "positive",
              "loss_at_least_20pct", "price_only_median_gross_pct"]),
    ):
        for field in fields:
            if actual_gates[key][field] != ref_gates[key][field]:
                raise ValueError("STAGE112_STAGE111_ORIGINAL_GATES_DO_NOT_REPRODUCE: " + field)
    if check["cases_by_source_status"] != reference["cases_by_source_status"]:
        raise ValueError("STAGE112_HISTORICAL_SOURCE_STATUS_DRIFT")

    rows = [case for pack in packets for case in pack["rows"]]
    if len(rows) != 519 or len({(z["date"], z["symbol"]) for z in rows}) != 519:
        raise ValueError("STAGE112_LOST_OR_DUPLICATE_ORIGINAL_CASES")

    first, repeats, censored_first, censored_repeats = [], [], 0, 0
    identities = Counter()
    percase_counts = Counter()
    d1_group = defaultdict(lambda: {"cases": 0, "priorities": 0,
                                     "with_priority": 0, "complete_price": 0})
    first_or_repeat = {"FIRST": Counter(), "REPEAT": Counter()}
    all_raw_ids = defaultdict(set)
    local_unique_events = set()
    case_medians = []
    paired_first_repeated = []
    case_summary = []
    right_tail = []
    by_date = defaultdict(lambda: {"cases": 0, "priority": 0, "repeat": 0})
    first_early5 = any_early5 = 0
    major_missing_first = []
    for z in sorted(rows, key=lambda q: (q["date"], q["symbol"])):
        date, symbol = z["date"], z["symbol"]
        case_id = date + ":" + symbol
        by_date[date]["cases"] += 1
        identity = z["identity"]
        identities[identity] += 1
        key = "OLD_D1" if z["original_D1_FIRST_UTC"] is not None else "D0_ONLY"
        d1_group[key]["cases"] += 1
        state = z["causal_state"]
        events = state["events"]
        priority = [e for e in events if e["state"] == "PRIORITY"]
        for evt in events:
            # Original Stage111 hash only includes D0 timestamp, decision time,
            # state and ordinal. It does NOT include the symbol. Detect raw
            # cross-case ID collisions but retain original evidence unchanged.
            eid = evt["event_id"]
            if (case_id, eid) in local_unique_events:
                raise ValueError("STAGE112_DUPLICATE_EVENT_ID_WITHIN_CASE")
            local_unique_events.add((case_id, eid))
            all_raw_ids[eid].add(case_id)
        ordered = sorted(priority, key=lambda e: e["observable_ms"])
        if ordered != priority:
            raise ValueError("STAGE112_PRIORITY_NOT_CHRONOLOGICAL")
        if len({x["observable_ms"] for x in ordered}) != len(ordered):
            raise ValueError("STAGE112_DUPLICATE_PRIORITY_CLOCK")
        if state["priority_count"] != len(ordered):
            raise ValueError("STAGE112_PRIORITY_COUNT_DRIFT")
        d0 = state["D0_first_ms"]
        end = state["anchor_end_ms"]
        if d0 >= end:
            raise ValueError("STAGE112_INVALID_FIXED_ANCHOR_TIME")
        for evt in ordered:
            t = evt["observable_ms"]
            if not d0 < t < end or evt["next_1m_open_ms"] != t:
                raise ValueError("STAGE112_PRIORITY_BAD_ASOF_TIMESTAMP_OR_ENTRY")
        # The source archive stores one price proxy per PRIORITY event in
        # decision-time order. The primary join key is the as-of event time.
        economics = z["price_only_24h"]
        if len(economics) != len(ordered):
            raise ValueError("STAGE112_PRIORITY_PRICE_JOIN_ROW_LOSS")
        price_map = {}
        for item in economics:
            t = item["priority_visible_ms"]
            if t in price_map:
                raise ValueError("STAGE112_DUPLICATE_HISTORIC_PRICE_JOIN")
            if item["next_open_ms"] != t:
                raise ValueError("STAGE112_HISTORIC_PRICE_NOT_NEXT_OPEN")
            price_map[t] = item
        if set(price_map) != {e["observable_ms"] for e in ordered}:
            raise ValueError("STAGE112_EVENT_TO_PRICE_JOIN_DRIFT")
        d1_group[key]["priorities"] += len(ordered)
        d1_group[key]["with_priority"] += bool(ordered)
        by_date[date]["priority"] += len(ordered)
        by_date[date]["repeat"] += max(0, len(ordered) - 1)
        percase_counts[len(ordered)] += 1
        case_repeats = []
        first_price = None
        for i, evt in enumerate(ordered):
            mode = "FIRST" if i == 0 else "REPEAT"
            item = price_map[evt["observable_ms"]]
            bucket = first_or_repeat[mode]
            bucket["events"] += 1
            if item["status"] == "PRICE_ONLY_PROXY_COMPLETE":
                ret = Decimal(item["gross_24h_price_pct"])
                if not ret.is_finite():
                    raise ValueError("STAGE112_NONFINITE_REAL_PRICE_PROXY")
                if mode == "FIRST":
                    first.append(ret)
                    first_price = ret
                else:
                    repeats.append(ret)
                    case_repeats.append(ret)
                d1_group[key]["complete_price"] += 1
                bucket["complete_prices"] += 1
            else:
                if item["gross_24h_price_pct"] is not None:
                    raise ValueError("STAGE112_CENSORED_WITH_FAKE_RETURN")
                if mode == "FIRST":
                    censored_first += 1
                else:
                    censored_repeats += 1
                bucket["censored"] += 1
        if case_repeats:
            case_medians.append(median(case_repeats))
            if first_price is not None:
                paired_first_repeated.append((first_price,median(case_repeats)))
        crossed = z["original_first_2x_HIGH_EVAL_ONLY"]
        if z["original_D0_early5_2x_EVAL_ONLY"]:
            if crossed is None:
                raise ValueError("STAGE112_HISTORIC_MAJOR_GROUND_TRUTH_MISSING")
            cross = prior.old.utc_ms(crossed)
            lead_minutes = ((cross - ordered[0]["observable_ms"]) // MS_MIN
                            if ordered else None)
            if lead_minutes is None:
                timing_class="NO_PRIORITY"
            elif lead_minutes >= 5:
                timing_class="EARLY_AT_LEAST_5MIN"
            elif lead_minutes > 0:
                timing_class="BEFORE_2X_UNDER_5MIN"
            elif lead_minutes == 0:
                timing_class="SAME_2X_MINUTE"
            else:
                timing_class="LATE_AFTER_2X"
            first_fired = bool(ordered and ordered[0]["observable_ms"] <= cross - 5*MS_MIN)
            any_fired = any(e["observable_ms"] <= cross - 5*MS_MIN for e in ordered)
            first_early5 += int(first_fired)
            any_early5 += int(any_fired)
            if not first_fired:
                major_missing_first.append({"date": date, "symbol": symbol,
                                            "priorities":len(ordered)})
            right_tail.append({"date":date, "symbol":symbol,
                               "first_early_2x":first_fired,
                               "any_early_2x":any_fired,
                               "first_priority_vs_2x_timing":timing_class,
                               "first_priority_lead_min":lead_minutes,
                               "total_priorities":len(ordered)})
        case_summary.append({
            "date":date, "symbol":symbol, "identity":identity,
            "original_D1":key, "priorities":len(ordered),
            "first_priority_utc_ms":ordered[0]["observable_ms"] if ordered else None,
            "last_priority_utc_ms":ordered[-1]["observable_ms"] if ordered else None,
            "first_priority_gross24_price_pct":str(first_price) if first_price is not None else None,
            "complete_repeat_24h_proxy_count":len(case_repeats),
            "repeat_24h_gross_median_pct":str(median(case_repeats)) if case_repeats else None,
            "original_D0_early2x5m_EVAL_ONLY":z["original_D0_early5_2x_EVAL_ONLY"],
            "source_state":state["source_status"],
        })

    if len(right_tail) != 28 or first_early5 != 19 or any_early5 != 19:
        # The existing model judges any priority before 2x, never a stale
        # signal after 2x. Original 19 early winners should exactly match.
        raise ValueError("STAGE112_GT2_28_RIGHT_TAIL_RECOMPUTE_MISMATCH")
    if sum(n*count for n,count in percase_counts.items()) != 740:
        raise ValueError("STAGE112_ORIGINAL740_PRIORITY_COUNT_DRIFT")
    if len(first) + len(repeats) != 598:
        raise ValueError("STAGE112_ORIGINAL598_COMPLETE_PRICE_PROXY_DRIFT")
    if len(first) + len(repeats) + censored_first + censored_repeats != 740:
        raise ValueError("STAGE112_ORIGINAL740_PRICE_COVERAGE_DRIFT")
    if len(first) + censored_first != 277 or len(repeats) + censored_repeats != 463:
        raise ValueError("STAGE112_ORIGINAL_FIRST_REPEAT_EVENT_COUNT_DRIFT")

    paired_diff=sorted([repeat-first for first,repeat in paired_first_repeated])
    paired_first=sorted([first for first,repeat in paired_first_repeated])
    paired_repeat=sorted([repeat for first,repeat in paired_first_repeated])
    right_tail_timing=Counter(z["first_priority_vs_2x_timing"] for z in right_tail)
    collisions = {raw:sorted(scoped) for raw,scoped in all_raw_ids.items()
                  if len(scoped) > 1}
    return {
        "schema":SCHEMA,
        "source_locked_stage111_aggregate_git_blob":PIN_AGG_BLOB,
        "source_locked_original_workflow_head_sha":SOURCE_WORKFLOW_COMMIT,
        "source_exposed_historical_not_OOS":True,
        "original519":len(rows),
        "original_D0_only_and_prior_D1":dict(d1_group),
        "identity_not_confirmed_tradeable":dict(identities),
        "original_priorities_740":sum(n*k for n,k in percase_counts.items()),
        "priority_event_count_by_original_case":{str(k):v for k,v in sorted(percase_counts.items())},
        "original_cases_with_no_priority":percase_counts[0],
        "original_cases_with_one_priority":percase_counts[1],
        "original_cases_with_repeats":sum(v for k,v in percase_counts.items() if k>=2),
        "events_from_repeated_cases":sum(k*v for k,v in percase_counts.items() if k>=2),
        "first_priority_event_count":sum(v for k,v in percase_counts.items() if k>=1),
        "repeat_priority_event_count":sum((k-1)*v for k,v in percase_counts.items() if k>=2),
        "first_priority_price_economics":dist(first),
        "repeat_priority_price_economics_event_weighted":dist(repeats),
        "case_weighted_repeat_median_of_complete_prices":dist(case_medians),
        "paired_same_case_first_vs_repeat_complete_prices":{
            "paired_cases":len(paired_diff),
            "first_24h_gross_median_pct":str(median(paired_first)) if paired_first else None,
            "repeat_case_median_24h_gross_median_pct":str(median(paired_repeat)) if paired_repeat else None,
            "median_of_within_case_repeat_minus_first_pct_points":str(median(paired_diff)) if paired_diff else None,
            "repeat_case_median_better_than_first":sum(v>0 for v in paired_diff),
            "repeat_case_median_worse_than_first":sum(v<0 for v in paired_diff),
            "exposed_descriptive_paired_not_causal":True,
        },
        "first_event_censored_n":censored_first,
        "repeat_event_censored_n":censored_repeats,
        "source_complete_price_proxies_total":len(first)+len(repeats),
        "by_original_anchor_date":dict(sorted(by_date.items())),
        "historical_original28_first_priority_timing_class":dict(sorted(right_tail_timing.items())),
        "historical_original28_first_priority_early5_2x":first_early5,
        "historical_original28_any_priority_early5_2x":any_early5,
        "historical_original28_major_early5_all":sorted(right_tail, key=lambda x:(x["date"],x["symbol"])),
        "historical_original28_major_early5_missed":sorted(major_missing_first,key=lambda x:(x["date"],x["symbol"])),
        "unscoped_original_event_id_collisions_across_cases":len(collisions),
        "unscoped_original_event_id_collision_examples":[{"event_id":k,"case_ids":v}
            for k,v in list(sorted(collisions.items()))[:10]],
        "event_id_scope_caveat":"Stage111 raw event_id omits venue/symbol; use date:symbol:event_id as research case scope; no production outbox may assume raw globally unique",
        "case_rows":case_summary,
        "real_executable_net_pnl":"UNKNOWN",
        "new_strategy_backtested":"NO",
        "independent_OOS":"NOT_DONE",
        "other_AI_review":"NOT_DONE",
        "monster_deployment":"NO_GO",
    }


def load_artifacts(root: Path) -> list[dict]:
    candidates = sorted(root.rglob("monster-stage111-*.json"))
    # Only individual six-date four-shard source outputs are permitted.
    packets = []
    for path in candidates:
        data = json.loads(path.read_text())
        if data.get("schema") == prior.replay.SCHEMA:
            packets.append(data)
    if len(packets) != 24:
        raise ValueError(f"STAGE112_REQUIRE_EXACT_24_REAL_SOURCE_SHARDS_GOT_{len(packets)}")
    return packets


def selftest():
    assert git_blob(b"test") == "30d74d258442c7c65512eafab474568dd706c430"
    assert dist([Decimal("-25"), Decimal("5"), Decimal("12")])["negative_20pct_or_worse"] == 1
    assert dist([])["gross_median_pct"] is None
    assert dist([Decimal("-10"), Decimal("10")])["gross_median_pct"] == "0"
    if str((Decimal("100") / Decimal("100") - 1) * 100) != "0":
        raise ValueError("STAGE112_PRICE_PROXY_BASIC_ARITHMETIC")
    print("STAGE112_DESC_DIAGNOSTIC_CAUSAL_AND_FEE_SELFTEST_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--artifact-dir", type=Path)
    ap.add_argument("--out", type=Path)
    args=ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.artifact_dir is None or args.out is None:
        ap.error("--artifact-dir and --out required")
    result=diagnostic(load_artifacts(args.artifact_dir),frozen_aggregate())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print("STAGE112_DIAGNOSTIC_REPRODUCED_ORIGINAL519 "+
          json.dumps({k:v for k,v in result.items() if k not in
            ("case_rows","historical_original28_major_early5_all",
             "historical_original28_major_early5_missed",
             "unscoped_original_event_id_collision_examples")},sort_keys=True))


if __name__=="__main__":
    main()
