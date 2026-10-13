#!/usr/bin/env python3
"""Aggregate Stage111 all519 24 official replay shards without masking censoring."""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
from statistics import median

try:
    import monster_v4_stage111_full519_replay_official as replay
except ImportError:
    from scripts import monster_v4_stage111_full519_replay_official as replay

old = replay.old
SCHEMA = "MONSTER_STAGE111_ALL519_SEVENDAY_CAUSAL_ECONOMIC_DECISION_V1"


def aggregate(packets):
    original, _ = replay.frozen()
    expected = {(r["date"], r["symbol"]) for r in original}
    original_by_key = {(r["date"], r["symbol"]): r for r in original}
    received = set()
    rows = []
    if len(packets) != 24:
        raise ValueError("STAGE111_EXACT_24_SHARDS_REQUIRED")
    for x in packets:
        key = (x["date"], x["shard"])
        if key in received or x["schema"] != replay.SCHEMA:
            raise ValueError("STAGE111_DUPLICATE_SHARD_OR_SCHEMA")
        if (x["source_stage83_git_blob"] != replay.src.PIN83
                or x["source_stage110_git_blob"] != replay.src.PIN110
                or x["source_input_population"] != 519
                or x["source_original_D1_population"] != 305):
            raise ValueError("STAGE111_PRE_REGISTERED_POPULATION_DRIFT")
        received.add(key)
        shard_source = old.shard_rows(x["date"], x["shard"], original)
        if {(z["date"], z["symbol"]) for z in shard_source} != {
                (z["date"], z["symbol"]) for z in x["rows"]}:
            raise ValueError("STAGE111_SHARD_CASE_LOSS")
        rows.extend(x["rows"])
    if received != {(d,s) for d in old.DATES for s in range(4)}:
        raise ValueError("STAGE111_DATE_SHARD_LOSS")
    actual = {(r["date"], r["symbol"]) for r in rows}
    if len(rows) != 519 or actual != expected:
        raise ValueError("STAGE111_ALL519_CASES_NOT_PRESENT")

    groups = Counter()
    economic = []
    source_states = Counter()
    missed = []
    recovered = []
    unknown = []
    original_major = []
    repeat = Counter()
    for z in rows:
        k = (z["date"], z["symbol"])
        oldrow = original_by_key[k]
        if (z["D0_FIRST_UTC"] != oldrow["D0_FIRST_UTC"]
                or z["original_D1_FIRST_UTC"] != oldrow["D1_FIRST_UTC"]
                or z["identity"] != oldrow["identity"]):
            raise ValueError("STAGE111_D0_IDENTITY_DRIFT")
        state = z["causal_state"]
        source_states[state["source_status"]] += 1
        priority_events = [e for e in state["events"] if e["state"] == "PRIORITY"]
        if len(priority_events) != state["priority_count"]:
            raise ValueError("STAGE111_PRIORITY_EVENT_COUNT_DRIFT")
        repeat[len(priority_events)] += 1
        for evt in priority_events:
            stamp = evt["observable_ms"]
            start = old.utc_ms(z["date"] + "T06:00:00Z")
            bucket = (stamp - start) // 86_400_000
            if bucket < 0 or bucket >= 7:
                raise ValueError("STAGE111_PRIORITY_OUTSIDE_FROZEN_ANCHOR")
            groups[(z["date"], bucket)] += 1
        for item in z["price_only_24h"]:
            if item["status"] == "PRICE_ONLY_PROXY_COMPLETE":
                economic.append(Decimal(item["gross_24h_price_pct"]))
        if oldrow["D0_at_least_5m_before_2x"]:
            original_major.append(k)
            if z["new_first_priority_early5_2x"]:
                recovered.append({"date":k[0], "symbol":k[1],
                                  "first_new_priority_ms":z["new_first_priority_visible_ms"]})
            else:
                t = old.utc_ms(z["original_first_2x_HIGH_EVAL_ONLY"])
                # If the verified minute prefix ends before the first 2x
                # crossing, non-observation cannot prove a model miss.
                last = state["last_observed_minute_open_ms"]
                if last is None or last + 60_000 < t:
                    unknown.append({"date":k[0], "symbol":k[1],
                                    "reason":"SOURCE_CENSORED_BEFORE_GT2"})
                else:
                    missed.append({"date":k[0], "symbol":k[1],
                                   "reason":"NO_PRIORITY_AT_LEAST_5M_BEFORE_GT2"})
    if len(original_major) != 28 or len(recovered)+len(missed)+len(unknown) != 28:
        raise ValueError("STAGE111_ORIGINAL_28_MISRECONCILED")
    daycounts = [{"date":d, "day_index":i, "priority_count":groups[(d,i)]}
                 for d in old.DATES for i in range(7)]
    burden = [z["priority_count"] for z in daycounts]
    values = sorted(economic)
    gross = str(median(values)) if values else None
    avg = str(Decimal(sum(burden)) / Decimal(42))
    any_censored = source_states["SOURCE_CENSORED"] > 0
    researched = {
        "G2_28_historical_original_D0_early5_retain":{
            "D0_early5_total":28, "new_early5_observed":len(recovered),
            "no_early5_with_known_complete_pre_GT_source":len(missed),
            "censored_before_GT2":len(unknown),
            "lower_bound_retention":str(Decimal(len(recovered))/Decimal(28)),
            "passed_80pct":len(recovered)*5 >= 28*4 if not unknown else "UNDETERMINED_SOURCE_CENSORED"},
        "G3_all_42_attention_days":{
            "counts": daycounts,"total_priority_events":sum(burden),
            "average_observed_per_day":avg,"maximum_observed_per_day":max(burden),
            "observed_average_and_peak_under_limits":
                (sum(burden)<=210 and max(burden)<=12),
            "source_complete_enough_for_firm_pass":not any_censored},
        "G4_price_only_only":{
            "complete_24h_price_proxy_count":len(values),
            "price_only_median_gross_pct":gross,
            "positive":sum(x>0 for x in values),
            "loss_at_least_20pct":sum(x<=-20 for x in values),
            "no_orderbook_broker_fee_notional_or_real_net":True,
            "real_executable_net":"UNKNOWN"}
    }
    status = "HISTORICAL_EXPOSED_EVALUATION_SOURCE_INCOMPLETE" if any_censored else (
        "HISTORICAL_EXPOSED_ONLY_NEEDS_OOS_AND_REVIEW")
    return {
        "schema": SCHEMA, "original_D0_total":519,"original_D1_total":305,
        "source_stages":"PINNED_STAGE83_STAGE110",
        "cases_by_source_status":dict(source_states),
        "cases_with_exact_anchor_window_1m_complete":source_states["EXPIRED"],
        "cases_not_seven_day_continuous":source_states["SOURCE_CENSORED"],
        "number_of_repeated_priorities_per_case":{str(k):v for k,v in sorted(repeat.items())},
        "historical_28_2x_early_preserved":recovered,
        "historical_28_2x_early_missed":missed,
        "historical_28_2x_source_unknown":unknown,
        "preregistered_gates":researched,
        "research_decision":status,
        "not_independent_OOS":True,"new_other_AI_review":"NOT_DONE",
        "real_executable_net":"UNKNOWN","monster_deployment":"NO_GO",
        "frank":"UNCHANGED","new_automation":"NONE",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    files = sorted(args.artifact_dir.glob("monster-stage111-*.json"))
    packets = [json.loads(p.read_text()) for p in files]
    result = aggregate(packets)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("STAGE111_FULL519_SOURCE_AWARE_GATE_RESULT " + json.dumps(
        {k:v for k,v in result.items() if k not in (
           "historical_28_2x_early_preserved",
           "historical_28_2x_early_missed",
           "historical_28_2x_source_unknown")}, sort_keys=True))


if __name__ == "__main__":
    main()
