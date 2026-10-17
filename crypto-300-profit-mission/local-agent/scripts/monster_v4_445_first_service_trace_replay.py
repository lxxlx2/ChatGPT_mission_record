#!/usr/bin/env python3
"""Observe the ACTUAL frozen research V2 D1 selection on all 445 real sources.

No original market/queue code changes, no additional candidate selection,
no order execution, no notification. Never infer first service from attempts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import monster_v4_shared_445_one_db_from_shards as assembler
import monster_v4_shared_d1_zeroquote_research_v2 as zeroq

SOURCE_SHA = "370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf"
TRACE_SCHEMA = "MONSTER445_FIRST_SELECTED_ACTUAL_D1_EIGHT_SLOTS_RESEARCH_V1"
PEAK_MS = 1770338160000
SLOT_LIMIT = 8
MIN = 60000


def eligible_and_pending(store, now_ms):
    pending = store.execute("""
        SELECT id,venue,symbol,first_seen_ms,deadline_ms,status,
               retry_after_ms,attempts,last_error,last_evaluated_bar_ms
        FROM candidate_queue WHERE status='PENDING'
        ORDER BY first_seen_ms,id
    """).fetchall()
    eligible=[dict(x) for x in pending if x["retry_after_ms"]<=now_ms]
    return eligible,[dict(x) for x in pending]


class FirstServiceObserver:
    def __init__(self):
        self.ticks=0
        self.slots=[]
        self.busy_ticks=[]
        self.first_selected={}
        self.first_evaluated={}
        self.slots_by_id=Counter()
        self.selected_count=0
        self.no_candidate_ticks=0
        self.peak_first_service_ticks={}
        self.original_handler=zeroq.experimental_queue_handler

    def instrument(self, store, now_ms, original_fetch, source_db, *,
                   limit, original_queue, stats):
        if limit != SLOT_LIMIT or type(now_ms) is not int:
            raise RuntimeError("MONSTER445_TRACE_original_eight_slots_changed")
        eligible,pending=eligible_and_pending(store,now_ms)
        original_first8=eligible[:SLOT_LIMIT]
        select_ids=[r["id"] for r in original_first8]
        # The trace observes reads only. Original V2 remains sole writer.
        outcome=self.original_handler(
            store,now_ms,original_fetch,source_db,
            limit=limit,original_queue=original_queue,stats=stats)
        if outcome["selected"] != len(original_first8):
            raise RuntimeError("MONSTER445_TRACE_actual_d1_selection_changed")
        self.ticks+=1
        if not select_ids:
            self.no_candidate_ticks+=1
        else:
            self.busy_ticks.append({
                "tick_ms":now_ms,"pending":len(pending),
                "eligible_before":len(eligible),"selected":len(select_ids),
                "unselected_eligible":max(0,len(eligible)-len(select_ids)),
                "selected_ids":select_ids,
                "original_completed":outcome["completed"],
                "original_deferred":outcome["deferred"],
                "original_late":outcome["late"],
            })
        for before in original_first8:
            ident=before["id"]
            after=store.execute("""
                SELECT id,venue,symbol,first_seen_ms,deadline_ms,status,
                       retry_after_ms,attempts,last_error,last_evaluated_bar_ms
                FROM candidate_queue WHERE id=?""",(ident,)).fetchone()
            if after is None or after["symbol"]!=before["symbol"]:
                raise RuntimeError("MONSTER445_TRACE_candidate_identity_drift")
            after=dict(after)
            if ident not in self.first_selected:
                self.first_selected[ident]=now_ms
            self.slots_by_id[ident]+=1
            if (after["last_evaluated_bar_ms"] is not None and
                    (before["last_evaluated_bar_ms"] is None or
                     after["last_evaluated_bar_ms"]>before["last_evaluated_bar_ms"])
                    and ident not in self.first_evaluated):
                self.first_evaluated[ident]=now_ms
            self.slots.append({
                "tick_ms":now_ms,
                "id":ident,
                "symbol":before["symbol"],
                "first_seen_ms":before["first_seen_ms"],
                "deadline_ms":before["deadline_ms"],
                "slot_class":("FIRST_SELECTION"
                              if self.slots_by_id[ident]==1
                              else "REPEATED_SELECTION"),
                "status_after":after["status"],
                "last_error_after":after["last_error"],
                "last_evaluated_bar_ms_before":before["last_evaluated_bar_ms"],
                "last_evaluated_bar_ms_after":after["last_evaluated_bar_ms"],
                "retry_after_ms_before":before["retry_after_ms"],
                "retry_after_ms_after":after["retry_after_ms"],
                "attempts_before":before["attempts"],
                "attempts_after":after["attempts"],
            })
            if before["first_seen_ms"]==PEAK_MS and ident not in self.peak_first_service_ticks:
                self.peak_first_service_ticks[ident]=now_ms
        self.selected_count+=len(original_first8)
        return outcome


def summarize_original_trace(model, frozen, trace):
    for key in ("execution_counts","queue_status_counts","event_type_counts",
                "queue_rows","events"):
        if model.get(key)!=frozen.get(key):
            raise RuntimeError("MONSTER445_TRACE_original_445_V2_model_drift_"+key)
    counts=frozen["execution_counts"]
    if (trace.ticks!=3360 or trace.selected_count!=counts["D1_selected"]
            or len(trace.slots)!=trace.selected_count
            or counts["D0_watch_new"]!=269 or len(model["queue_rows"])!=269
            or frozen.get("actually_complete_symbols")!=445
            or model.get("D1_model_semantics")!=
                "RESEARCH_V2_SOURCE_UNSUPPORTED_ZEROQUOTE"):
        raise RuntimeError("MONSTER445_TRACE_original_global_counters_drift")
    rows=model["queue_rows"]
    ids=[q["id"] for q in rows]
    if len(set(ids))!=269:
        raise RuntimeError("MONSTER445_TRACE_queue_id_duplicates")
    per_candidate=[]
    selected_lags=[]; evaluated_lags=[]
    for q in rows:
        ident=q["id"]; seen=q["first_seen_ms"]
        first=trace.first_selected.get(ident)
        first_eval=trace.first_evaluated.get(ident)
        if (first is not None and first<seen) or (
                first_eval is not None and (first is None or first_eval<first)):
            raise RuntimeError("MONSTER445_TRACE_negative_first_service")
        if first is not None:
            selected_lags.append((first-seen)//MIN)
        if first_eval is not None:
            evaluated_lags.append((first_eval-seen)//MIN)
        per_candidate.append({
            "id":ident,"symbol":q["symbol"],"first_seen_ms":seen,
            "cohort":("PEAK_98" if seen==PEAK_MS else "OTHER_171"),
            "final_status":q["status"],
            "first_selected_ms":first,
            "first_selected_delay_minutes":(
                (first-seen)//MIN if first is not None else None),
            "first_evaluation_ms":first_eval,
            "first_evaluation_delay_minutes":(
                (first_eval-seen)//MIN if first_eval is not None else None),
            "total_selected_slots":trace.slots_by_id[ident],
            "repeated_selected_slots":max(0,trace.slots_by_id[ident]-1),
            "ever_selected":first is not None,
            "ever_valid_D1_evaluation":first_eval is not None,
        })
    by_cohort={}
    for label,expected in (("PEAK_98",98),("OTHER_171",171)):
        cohort=[q for q in per_candidate if q["cohort"]==label]
        if len(cohort)!=expected:
            raise RuntimeError("MONSTER445_TRACE_cohort_size_drift")
        by_cohort[label]={
            "WATCH":len(cohort),
            "final_status":dict(sorted(Counter(x["final_status"] for x in cohort).items())),
            "ever_selected":sum(x["ever_selected"] for x in cohort),
            "never_selected":sum(not x["ever_selected"] for x in cohort),
            "ever_valid_D1_evaluation":sum(x["ever_valid_D1_evaluation"] for x in cohort),
            "first_selection_lag_minutes_counts":dict(sorted(Counter(
                str(x["first_selected_delay_minutes"]) if x["ever_selected"]
                else "NOT_SELECTED" for x in cohort).items())),
            "total_selected_slots":sum(x["total_selected_slots"] for x in cohort),
            "repeated_selected_slots":sum(x["repeated_selected_slots"] for x in cohort),
            "LATE_never_selected":sum(x["final_status"]=="LATE" and not x["ever_selected"] for x in cohort),
            "LATE_selected_before_deadline":sum(
                x["final_status"]=="LATE" and x["first_selected_ms"] is not None
                and x["first_selected_ms"]<=x["first_seen_ms"]+15*MIN
                for x in cohort),
        }
    if (sum(x["total_selected_slots"] for x in per_candidate)!=trace.selected_count
            or sum(x["repeated_selected_slots"] for x in per_candidate)!=
               trace.selected_count-len(trace.first_selected)
            or sum(len(x["selected_ids"]) for x in trace.busy_ticks)!=
               trace.selected_count
            or any(x["selected"]>8 for x in trace.busy_ticks)
            or len(trace.peak_first_service_ticks)!=by_cohort["PEAK_98"]["ever_selected"]):
        raise RuntimeError("MONSTER445_TRACE_slot_accounting_drift")
    return {
        "schema":TRACE_SCHEMA,
        "research_only":True,
        "frozen_original_full_json_sha256":SOURCE_SHA,
        "original_758_censored":313,
        "actual_one_sqlite_445_symbols":True,
        "actual_3360_shared_polls":trace.ticks,
        "original_V2_every_event_and_queue_byte_semantics_equal":True,
        "original_model_core_unchanged":True,
        "D1_global_selected_slots":trace.selected_count,
        "D1_first_selection_slots":len(trace.first_selected),
        "D1_repeated_selection_slots":trace.selected_count-len(trace.first_selected),
        "D1_busy_ticks":len(trace.busy_ticks),
        "D1_no_eligible_candidate_ticks":trace.no_candidate_ticks,
        "D1_baseline_limit_per_tick":8,
        "cohort_comparison":by_cohort,
        "candidate_first_service":per_candidate,
        "slot_trace":trace.slots,
        "busy_tick_trace":trace.busy_ticks,
        "not_independent_OOS":True,
        "not_real_PIT_listing":True,
        "not_a_counterfactual_scheduler":True,
        "actual_profit_or_lost_profitable_opportunities":"UNVERIFIED",
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True
    }


def run_trace(source_dir:Path, reference_json:Path):
    original_raw=reference_json.read_bytes()
    if hashlib.sha256(original_raw).hexdigest()!=SOURCE_SHA:
        raise RuntimeError("MONSTER445_TRACE_original_raw_full_SHA_drift")
    frozen=json.loads(original_raw)
    tracer=FirstServiceObserver()
    # Assemble and run via assembler's ORIGINAL explicit V2 mode, preserving
    # its research-only schema and source-complete statements. Instrument only
    # the real handler with read-only pre/post SQL around ONE actual call.
    real_v2=zeroq.run_v2
    def traced_engine(db, day, roster, *, market_coverage_label):
        with patch.object(zeroq,"experimental_queue_handler",
                          side_effect=tracer.instrument):
            return real_v2(db,day,roster,market_coverage_label=market_coverage_label)
    with patch.object(zeroq,"run_v2",side_effect=traced_engine):
        model=assembler.run_all(source_dir,research_zeroquote_v2=True)
    return summarize_original_trace(model,frozen,tracer)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--reference-full",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("MONSTER445_TRACE_OUTPUT_ALREADY_EXISTS")
    report=run_trace(args.source_dir,args.reference_full)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as out:
        json.dump(report,out,indent=2,sort_keys=True)
        out.write("\n")
    print("MONSTER445_REAL_SOURCE_FIRST_SERVICE_TRACE",
          json.dumps({k:report[k] for k in (
              "actual_3360_shared_polls","D1_global_selected_slots",
              "D1_first_selection_slots","D1_repeated_selection_slots",
              "D1_busy_ticks","G6")},sort_keys=True),
          flush=True)


if __name__=="__main__":
    main()
