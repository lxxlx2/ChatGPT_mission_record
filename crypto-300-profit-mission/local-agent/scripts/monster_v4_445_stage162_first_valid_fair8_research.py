#!/usr/bin/env python3
"""Stage162: isolated actual-445 fair-8 D1 experiment, not production or BUY.

Immutable D0 and genuine experimental V2 D1 remain the only model code.
Temporarily mask nonselected eligible SQLite IDs to change only D1 selection.
All durable masks are restored and source/event identities are checked.
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
import monster_v4_shared_spot_d0_d1_original_core as shared

REFERENCE_SHA = "370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf"
BASELINE_TRACE_SHA = "8d7ac8d9a0a78a0daa1164d0aee7783b0a51f29ef099437590b103bad0bab76d"
SCHEMA = "MONSTER445_STAGE162_FIRST_VALID_5M_ONCE_PRIORITY_8_RESEARCH_V1"
CAPACITY = 8
PEAK_MS = 1770338160000
MIN = 60_000
FIVE = 5 * MIN


def check_sha_file(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("MONSTER162_FROZEN_SOURCE_SHA_DRIFT")
    return json.loads(data)


def first_valid_post_watch_closed_bar(now_ms, first_seen_ms):
    """Same clock convention as frozen shared verified_closed_5m callback.

    Only clock/queue state, never subsequent prices, candles or future status.
    """
    latest_closed_bar_end = (now_ms // FIVE) * FIVE - 1
    return latest_closed_bar_end + 1 > first_seen_ms


def plan_eligible_eight(eligible_rows, now_ms, capacity=CAPACITY):
    if capacity != CAPACITY:
        raise ValueError("MONSTER162_CAPACITY_CHANGED")
    ids = [q["id"] for q in eligible_rows]
    if len(set(ids)) != len(ids):
        raise ValueError("MONSTER162_DUPLICATE_QUEUE_ID")
    for q in eligible_rows:
        if (q["status"] != "PENDING" or q["retry_after_ms"] > now_ms
                or type(q["deadline_ms"]) is not int
                or type(q["first_seen_ms"]) is not int):
            raise ValueError("MONSTER162_NOT_A_REAL_NOW_ELIGIBLE_QUEUE")
    oldest = sorted(eligible_rows, key=lambda q:(q["first_seen_ms"],q["id"]))
    fresh = [q for q in oldest
             if q["last_evaluated_bar_ms"] is None
             and now_ms <= q["deadline_ms"]
             and first_valid_post_watch_closed_bar(now_ms,q["first_seen_ms"])]
    selected = fresh[:capacity]
    used = {q["id"] for q in selected}
    selected += [q for q in oldest if q["id"] not in used][:capacity-len(selected)]
    if len(selected)!=min(len(oldest),CAPACITY):
        raise RuntimeError("MONSTER162_SELECTED_CAPACITY_OR_ID_DRIFT")
    return selected


class FairEightObserver:
    def __init__(self):
        self.real_original_handler=zeroq.experimental_queue_handler
        self.ticks=0
        self.slots=[]
        self.busy_ticks=[]
        self.first_selected={}
        self.first_evaluated={}
        self.by_id=Counter()
        self.selected_total=0
        self.selected_when_valid_mature=0
        self.repeats_advanced=0
        self.repeats_no_progress=0

    def instrument(self, store, now_ms, original_fetch, source_db, *,
                   limit, original_queue, stats):
        if limit!=CAPACITY or type(now_ms) is not int or store.in_transaction:
            raise RuntimeError("MONSTER162_FROZEN_HANDLER_CONTRACT_DRIFT")
        before={q["id"]:dict(q) for q in
                store.execute("SELECT * FROM candidate_queue ORDER BY id")}
        eligible=[q for q in before.values()
                  if q["status"]=="PENDING" and q["retry_after_ms"]<=now_ms]
        chosen=plan_eligible_eight(eligible, now_ms, limit)
        chosen_ids={q["id"] for q in chosen}
        if len(chosen_ids)!=len(chosen):
            raise RuntimeError("MONSTER162_SELECTED_ID_DUPLICATE")
        suppressed=[(q["id"],q["retry_after_ms"]) for q in eligible
                    if q["id"] not in chosen_ids]
        if suppressed:
            with store:
                for ident,_ in suppressed:
                    store.execute("UPDATE candidate_queue SET retry_after_ms=? WHERE id=?",
                                  (now_ms+1,ident))
        try:
            actual=self.real_original_handler(
                store,now_ms,original_fetch,source_db,limit=CAPACITY,
                original_queue=original_queue,stats=stats)
        finally:
            try:
                if store.in_transaction:
                    store.rollback()
                if suppressed:
                    with store:
                        for ident,retry in suppressed:
                            store.execute("UPDATE candidate_queue SET retry_after_ms=? WHERE id=?",
                                          (retry,ident))
                    got={q["id"]:q["retry_after_ms"] for q in store.execute(
                        "SELECT id,retry_after_ms FROM candidate_queue WHERE id IN ("+
                        ",".join("?" for _ in suppressed)+")",
                        tuple(i for i,_ in suppressed))}
                    if got!=dict(suppressed):
                        raise RuntimeError("MONSTER162_MASK_RESTORE_READBACK_MISMATCH")
            except Exception as exc:
                raise RuntimeError("MONSTER162_MASK_RESTORE_FAILED") from exc
        after={q["id"]:dict(q) for q in
               store.execute("SELECT * FROM candidate_queue ORDER BY id")}
        if (actual["selected"]!=len(chosen)
                or set(before)!=set(after)):
            raise RuntimeError("MONSTER162_ACTUAL_SELECTION_OR_QUEUE_SET_DRIFT")
        for ident,old in before.items():
            if ident not in chosen_ids and old!=after[ident]:
                raise RuntimeError("MONSTER162_NONSELECTED_DURABLE_ROW_MUTATED")
            if ident in chosen_ids and old==after[ident]:
                raise RuntimeError("MONSTER162_PHANTOM_SELECTED_CANDIDATE")
        self.ticks+=1
        self.selected_total+=len(chosen)
        if chosen:
            self.busy_ticks.append({
                "tick_ms":now_ms,
                "eligible":len(eligible),
                "selected_ids":[q["id"] for q in chosen],
                "first_mature_fair_priority":sum(
                    q["last_evaluated_bar_ms"] is None and
                    now_ms<=q["deadline_ms"] and
                    first_valid_post_watch_closed_bar(now_ms,q["first_seen_ms"])
                    for q in chosen),
                "completed":actual["completed"],"deferred":actual["deferred"],
                "late":actual["late"],
            })
        for q in chosen:
            ident=q["id"]
            v=after[ident]
            advanced=(v["last_evaluated_bar_ms"] is not None
                      and (q["last_evaluated_bar_ms"] is None
                           or v["last_evaluated_bar_ms"]>q["last_evaluated_bar_ms"]))
            first=ident not in self.first_selected
            if first:
                self.first_selected[ident]=now_ms
            if advanced and ident not in self.first_evaluated:
                self.first_evaluated[ident]=now_ms
            if not first:
                if advanced:
                    self.repeats_advanced+=1
                else:
                    self.repeats_no_progress+=1
            self.by_id[ident]+=1
            self.slots.append({
                "tick_ms":now_ms,"id":ident,"symbol":q["symbol"],
                "first_seen_ms":q["first_seen_ms"],
                "deadline_ms":q["deadline_ms"],"first_selection":first,
                "mature_before_selection":first_valid_post_watch_closed_bar(
                    now_ms,q["first_seen_ms"]),
                "valid_5m_evaluation_marker_advanced":advanced,
                "status_after":v["status"],"last_error_after":v["last_error"],
                "last_evaluated_bar_ms_before":q["last_evaluated_bar_ms"],
                "last_evaluated_bar_ms_after":v["last_evaluated_bar_ms"],
            })
        return actual


def delay_stats(candidates, field):
    values=sorted((q[field]-q["first_seen_ms"])/MIN
                  for q in candidates if q[field] is not None)
    if not values:
        return {"n":0,"p50":None,"p90":None,"p99":None}
    def nearest(p):
        return values[max(0, min(len(values)-1,
                     (len(values)*p+99)//100-1))]
    return {"n":len(values),"p50":nearest(50),"p90":nearest(90),
            "p99":nearest(99)}


def build_report(candidate_model, observer, ref, baseline):
    def contract(condition, key):
        if not condition:
            raise RuntimeError("MONSTER162_REAL_DATA_"+key)
    contract(ref.get("actually_complete_symbols")==445,"BASELINE_COHORT_DRIFT")
    contract(candidate_model.get("actually_complete_symbols")==445,"COHORT_DRIFT")
    contract(candidate_model["execution_counts"]["polls"]==3360,"POLL_DRIFT")
    contract(observer.ticks==3360,"HANDLER_TICKS_DRIFT")
    old_watch={e["event_id"]:e for e in ref["events"]
               if e["event_type"]=="WATCH_EARLY"}
    new_watch={e["event_id"]:e for e in candidate_model["events"]
               if e["event_type"]=="WATCH_EARLY"}
    contract(old_watch==new_watch and len(old_watch)==269,
             "D0_WATCH_IDENTITY_OR_EVENT_DRIFT")
    old_rows={q["id"]:q for q in ref["queue_rows"]}
    new_rows={q["id"]:q for q in candidate_model["queue_rows"]}
    contract(len(old_rows)==len(new_rows)==269,"QUEUE_269_ID_DRIFT")
    contract(all((q["venue"],q["symbol"],q["first_seen_ms"],
                  q["deadline_ms"])==
                 tuple(new_rows[i][k] for k in
                    ("venue","symbol","first_seen_ms","deadline_ms"))
                 for i,q in old_rows.items()),
             "D0_CANDIDATE_ANCHOR_DRIFT")
    contract(set(old_rows)==set(new_rows),"QUEUE_KEY_DRIFT")
    contract(observer.selected_total==len(observer.slots)
             and observer.selected_total==candidate_model[
                 "execution_counts"]["D1_selected"],"SLOT_ACCOUNT_DRIFT")
    contract(all(len(t["selected_ids"])<=CAPACITY for t in observer.busy_ticks)
             and sum(len(t["selected_ids"]) for t in observer.busy_ticks)
                 ==observer.selected_total,"TICK_CAPACITY_DRIFT")
    contract(baseline["D1_global_selected_slots"]==753
             and baseline["D1_first_selection_slots"]==269
             and baseline["D1_repeated_selection_slots"]==484,
             "BASELINE_TRACE_DRIFT")
    contract(baseline["original_V2_every_event_and_queue_byte_semantics_equal"]
             is True and baseline["frozen_original_full_json_sha256"]
             ==REFERENCE_SHA,"BASELINE_SOURCE_IDENTITY_DRIFT")
    contract(set(q["id"] for q in baseline["candidate_first_service"]) ==
             set(old_rows),"BASELINE_CANDIDATES_DRIFT")
    old_setups={e["event_id"]:e for e in ref["events"]
                if e["event_type"]=="SETUP_ACTIVE"}
    new_setups={e["event_id"]:e for e in candidate_model["events"]
                if e["event_type"]=="SETUP_ACTIVE"}
    contract(len(old_setups)==120 and len(new_setups)==len(set(new_setups)),
             "SETUP_BASELINE_OR_DUPLICATE_DRIFT")
    old_to_q={q["id"]:q for q in baseline["candidate_first_service"]}
    data=[]
    for ident,old in old_rows.items():
        now=new_rows[ident]
        item={
            "id":ident,"symbol":old["symbol"],
            "first_seen_ms":old["first_seen_ms"],
            "deadline_ms":old["deadline_ms"],
            "cohort":"PEAK_98" if old["first_seen_ms"]==PEAK_MS else "OTHER_171",
            "baseline_status":old["status"],"alternative_status":now["status"],
            "baseline_first_selected_ms":old_to_q[ident]["first_selected_ms"],
            "baseline_first_evaluation_ms":old_to_q[ident]["first_evaluation_ms"],
            "alternative_first_selected_ms":observer.first_selected.get(ident),
            "alternative_first_evaluation_ms":observer.first_evaluated.get(ident),
            "alternative_selected_slots":observer.by_id[ident],
        }
        data.append(item)
    cohorts={}
    for label,expected in (("PEAK_98",98),("OTHER_171",171)):
        cohort=[q for q in data if q["cohort"]==label]
        contract(len(cohort)==expected,"COHORT_GROUPING_DRIFT")
        baseline_evals=[dict(first_seen_ms=x["first_seen_ms"],
                             at=x["baseline_first_evaluation_ms"]) for x in cohort]
        alternative_evals=[dict(first_seen_ms=x["first_seen_ms"],
                                at=x["alternative_first_evaluation_ms"]) for x in cohort]
        cohorts[label]={
            "watch":len(cohort),
            "baseline_evaluated_with_valid_closed_5m":
                sum(x["at"] is not None for x in baseline_evals),
            "alternative_evaluated_with_valid_closed_5m":
                sum(x["at"] is not None for x in alternative_evals),
            "baseline_late":sum(x["baseline_status"]=="LATE" for x in cohort),
            "alternative_late":sum(x["alternative_status"]=="LATE" for x in cohort),
            "baseline_queue_status":dict(sorted(
                Counter(x["baseline_status"] for x in cohort).items())),
            "alternative_queue_status":dict(sorted(
                Counter(x["alternative_status"] for x in cohort).items())),
            "baseline_first_valid_eval_delay_minutes":
                delay_stats([dict(first_seen_ms=x["first_seen_ms"],
                                 first_eval=x["baseline_first_evaluation_ms"])
                             for x in cohort],"first_eval"),
            "alternative_first_valid_eval_delay_minutes":
                delay_stats([dict(first_seen_ms=x["first_seen_ms"],
                                 first_eval=x["alternative_first_evaluation_ms"])
                             for x in cohort],"first_eval"),
            "first_selected_before_actual_deadline_baseline":
                sum(x["baseline_first_selected_ms"] is not None and
                    x["baseline_first_selected_ms"]<=x["deadline_ms"] for x in cohort),
            "first_selected_before_actual_deadline_alternative":
                sum(x["alternative_first_selected_ms"] is not None and
                    x["alternative_first_selected_ms"]<=x["deadline_ms"] for x in cohort),
        }
    lost=set(old_setups)-set(new_setups)
    gained=set(new_setups)-set(old_setups)
    retained=set(old_setups)&set(new_setups)
    cohort_of=lambda e: ("PEAK_98" if next(
        (q["first_seen_ms"] for q in old_rows.values()
         if q["symbol"]==e["symbol"]),-1)==PEAK_MS else "OTHER_171")
    for label in cohorts:
        cohorts[label]["baseline_setups"]=sum(cohort_of(e)==label for e in old_setups.values())
        cohorts[label]["alternative_setups"]=sum(cohort_of(e)==label for e in new_setups.values())
        cohorts[label]["lost_setups"]=sum(cohort_of(old_setups[x])==label for x in lost)
        cohorts[label]["new_setups"]=sum(cohort_of(new_setups[x])==label for x in gained)
    return {
        "schema":SCHEMA,
        "baseline_original_full_sha256":REFERENCE_SHA,
        "baseline_first_service_trace_sha256":BASELINE_TRACE_SHA,
        "date":candidate_model["date"],
        "population":"HISTORICAL_POSTHOC_445_OF_758_313_CENSORED",
        "D0_watch_269_event_and_queue_identity_exact":True,
        "real_3360_shared_poll_ticks":observer.ticks,
        "capacity_per_tick":CAPACITY,
        "research_variant_selection_only_not_original_production_D1":True,
        "baseline_d1_selections":baseline["D1_global_selected_slots"],
        "alternative_d1_selections":observer.selected_total,
        "alternative_first_selected":len(observer.first_selected),
        "alternative_reselected":observer.selected_total-len(observer.first_selected),
        "alternative_repeated_5m_evaluation_progress":observer.repeats_advanced,
        "alternative_repeated_5m_no_evaluation_progress":observer.repeats_no_progress,
        "cohort_comparison":cohorts,
        "setup_event_id_baseline":len(old_setups),
        "setup_event_id_alternative":len(new_setups),
        "setup_retained_ids":len(retained),
        "setup_lost_ids":len(lost),
        "setup_new_ids":len(gained),
        "setup_lost_event_ids":sorted(lost),
        "setup_new_event_ids":sorted(gained),
        "setup_guardrail":"PASS_NO_LOSS" if not lost else "NO_GO_LOST_EXISTING_SETUPS",
        "candidate_outcomes":data,
        "selected_slot_trace":observer.slots,
        "busy_tick_trace":observer.busy_ticks,
        "raw_alternative_events":candidate_model["events"],
        "raw_alternative_queue":candidate_model["queue_rows"],
        "raw_alternative_execution_counts":candidate_model["execution_counts"],
        "raw_alternative_event_type_counts":candidate_model["event_type_counts"],
        "raw_alternative_queue_status_counts":candidate_model["queue_status_counts"],
        "historical_research_only_not_PIT_listing":True,
        "not_independent_OOS":True,"actual_executable_net_profit":"UNVERIFIED",
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True,
    }


def run(source_dir, baseline_full, baseline_trace):
    ref=check_sha_file(baseline_full,REFERENCE_SHA)
    trace=check_sha_file(baseline_trace,BASELINE_TRACE_SHA)
    observer=FairEightObserver()
    orig_v2=zeroq.run_v2
    def wrapped_v2(source_db, day, symbols, *, market_coverage_label):
        with patch.object(zeroq,"experimental_queue_handler",
                          side_effect=observer.instrument):
            return orig_v2(source_db,day,symbols,
                           market_coverage_label=market_coverage_label)
    with patch.object(zeroq,"run_v2",side_effect=wrapped_v2):
        candidate=assembler.run_all(source_dir,research_zeroquote_v2=True)
    return build_report(candidate,observer,ref,trace)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dir",type=Path,required=True)
    ap.add_argument("--baseline-full",type=Path,required=True)
    ap.add_argument("--baseline-trace",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("MONSTER162_OUTPUT_EXISTS_NO_OVERWRITE")
    report=run(args.source_dir,args.baseline_full,args.baseline_trace)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as dst:
        json.dump(report,dst,sort_keys=True,ensure_ascii=False,indent=2)
        dst.write("\n")
    print("MONSTER162_REAL445_FAIR8_RESEARCH_ONLY",
          json.dumps({key:report[key] for key in (
              "setup_event_id_baseline","setup_event_id_alternative",
              "setup_lost_ids","setup_new_ids","setup_guardrail",
              "alternative_d1_selections","cohort_comparison")},
              sort_keys=True),flush=True)


if __name__=="__main__":
    main()
