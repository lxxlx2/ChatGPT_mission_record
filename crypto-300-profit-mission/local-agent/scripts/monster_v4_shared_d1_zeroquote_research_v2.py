#!/usr/bin/env python3
"""Experimental D1 zero-quote *source unsupported* handling, NEVER production.

Runs the original full-market shared D0; preserves max eight FIFO D1 selection
slots/tick; invokes unchanged production.process_queue only on supported items.
Zero quote is not forged into a positive quote or a trading setup. This is a
new research semantic, NOT the fixed SHA-reviewed original D1 experiment.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import hashlib
from unittest.mock import patch

import monster_v4_shadow as production
import monster_v4_shared_spot_d0_d1_original_core as shared
import monster_v4_shared_445_first32_real_comparison as first

SCHEMA="MONSTER_FEB2026_REAL_ZERO_QUOTE_UNSUPPORTED_D1_RESEARCH_VARIANT_V2"
WAIT_ERROR="SOURCE_UNSUPPORTED_ZERO_QUOTE"
TERMINAL="SOURCE_UNSUPPORTED_D1_ZERO_QUOTE"


def source_zero_closed5m(source_db, symbol, tick_ms):
    """Return True iff actual *valid closed* 5m quote is exactly zero.

    If any OHLC, clock, shape, quote or volume is invalid, fail whole study.
    Never fill zero data; tests must distinguish real zero from bad HIGH=0.
    """
    data=source_db.execute("""
        SELECT candle_json FROM closed5m_source
        WHERE symbol=? AND end_ms<? ORDER BY end_ms DESC LIMIT 8
    """,(symbol,tick_ms)).fetchall()
    candles=[json.loads(v[0]) for v in reversed(data)]
    t0=(tick_ms//(5*shared.MIN))*(5*shared.MIN)-1
    expected=[t0-(7-i)*5*shared.MIN for i in range(8)]
    if len(candles)!=8:
        raise RuntimeError("ZEROQUOTE_RESEARCH_INVALID_D1_SOURCE_TOO_FEW")
    has_zero=False
    for i,c in enumerate(candles):
        try:
            if (not isinstance(c,list) or len(c)!=8
                or type(c[0]) is not int or type(c[6]) is not int
                or c[6]!=expected[i] or
                c[0]!=expected[i]-5*shared.MIN+1 or c[6]>=tick_ms):
                raise ValueError("BAD_CLOCK_OR_SHAPE")
            op,hi,lo,cl,volume,quote=[Decimal(str(c[k]))
                            for k in (1,2,3,4,5,7)]
            if (not all(x.is_finite()
                    for x in (op,hi,lo,cl,volume,quote))
                or min(op,hi,lo,cl)<=0 or
                not (lo<=op<=hi and lo<=cl<=hi) or
                volume<0 or quote<0):
                raise ValueError("BAD_OHLC_VOLUME_OR_QUOTE")
            if quote==0:
                has_zero=True
        except (ValueError,InvalidOperation,TypeError,IndexError,
                OverflowError,ArithmeticError) as exc:
            raise RuntimeError("ZEROQUOTE_RESEARCH_REAL_D1_SOURCE_CORRUPTED") from exc
    if not has_zero:
        # Frozen original evaluator remains the final authority on normal
        # supported candles. Any hidden data defect is fatal, not deferred.
        shared.verified_closed_5m_for_original_d1(
            source_db, shared.clean_roster((symbol,)),
            "spot",symbol,tick_ms)
    return has_zero


def experimental_queue_handler(store,now_ms,original_fetch,source_db,*,limit=8,
                               original_queue,stats):
    if limit!=8:
        raise ValueError("ZEROQUOTE_RESEARCH_MUST_KEEP_ORIGINAL_EIGHT_CAPACITY")
    selected=store.execute("""
        SELECT * FROM candidate_queue WHERE status='PENDING'
        AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?
    """,(now_ms,limit)).fetchall()
    out=dict(selected=0,completed=0,deferred=0,late=0)
    for item in selected:
        if item["venue"]!="spot":
            raise RuntimeError("ZEROQUOTE_RESEARCH_UNEXPECTED_FUTURES_IN_SPOT_COHORT")
        # Explicitly only alter source-contract uncertainty, NOT queue
        # capacity, signal ordering, price paths, or established stale policy.
        if (now_ms>item["deadline_ms"] and
                item["last_evaluated_bar_ms"] is None and
                item["last_error"]==WAIT_ERROR):
            with store:
                store.execute("""UPDATE candidate_queue SET status=?,last_error=?
                    WHERE id=?""",(TERMINAL,WAIT_ERROR,item["id"]))
            stats["terminal_unsupported"]+=1
            stats["by_symbol"][item["symbol"]]+=1
            out["selected"]+=1
            continue
        if now_ms>item["deadline_ms"]:
            normal=original_queue(store,now_ms,original_fetch,limit=1)
        else:
            unsupported=source_zero_closed5m(
                source_db,item["symbol"],now_ms)
            if unsupported:
                with store:
                    if now_ms>=item["deadline_ms"] and item["last_evaluated_bar_ms"] is None:
                        store.execute("""UPDATE candidate_queue
                            SET status=?,last_error=? WHERE id=?""",
                            (TERMINAL,WAIT_ERROR,item["id"]))
                        stats["terminal_unsupported"]+=1
                        stats["by_symbol"][item["symbol"]]+=1
                    else:
                        store.execute("""UPDATE candidate_queue SET
                            last_error=?,retry_after_ms=? WHERE id=?""",
                            (WAIT_ERROR,now_ms+shared.MIN,item["id"]))
                        out["deferred"]+=1
                    out["selected"]+=1
                stats["zero_quote_source_slots_consumed"]+=1
                continue
            normal=original_queue(store,now_ms,original_fetch,limit=1)
        if normal["selected"]!=1:
            raise RuntimeError("ZEROQUOTE_RESEARCH_FIFO_OR_SLOT_PARITY_BROKEN")
        for k in out:
            out[k]+=normal[k]
    if out["selected"]!=len(selected) or out["selected"]>8:
        raise RuntimeError("ZEROQUOTE_RESEARCH_GLOBAL_SELECTION_OVER_EIGHT")
    stats["max_slots_in_single_tick"]=max(
        stats["max_slots_in_single_tick"],out["selected"])
    return out


def run_v2(source_db,day,symbols,*,market_coverage_label):
    if market_coverage_label not in (
         "OFFICIAL_VERIFIED_SUBSET_ONLY","SYNTHETIC_TEST_ONLY"):
        raise ValueError("ZEROQUOTE_RESEARCH_NO_FULL_758_SELF_ATTESTATION")
    # Patch only inside this isolated experiment process. Never mutate
    # prod source or the old independently approved V4 replay implementation.
    original_queue=production.process_queue
    stats={"zero_quote_source_slots_consumed":0,
           "terminal_unsupported":0,"by_symbol":Counter(),
           "max_slots_in_single_tick":0}
    def variant(store,now_ms,fetch_candles,limit=8):
        return experimental_queue_handler(
          store,now_ms,fetch_candles,source_db,limit=limit,
          original_queue=original_queue,stats=stats)
    with patch.object(shared.production,"process_queue",side_effect=variant):
        result=shared.run_shared(source_db,day,symbols,
                                 market_coverage_label=market_coverage_label)
    # The approved original core reported True. REVOKE that statement for a
    # genuine change in queue semantics; profit/trading claims remain OFF.
    result["schema"]=SCHEMA
    result["only_original_production_D0_and_D1_called"]=False
    result["production_D0_unchanged"]=True
    result["production_D1_original_processor_called_for_supported_cases"]=True
    result["experimental_source_semantics_approved_for_trading"]=False
    result["D1_zero_quote_unsupported_attempt_slots"]=stats[
        "zero_quote_source_slots_consumed"]
    result["D1_zero_quote_terminal_candidates"]=stats["terminal_unsupported"]
    result["D1_zero_quote_terminal_by_symbol"]=dict(stats["by_symbol"])
    result["D1_max_selected_slots_one_tick"]=stats["max_slots_in_single_tick"]
    result["G4"]="UNKNOWN"
    result["G6"]="NO_GO"
    result["d1_zeroquote_research_sha256"]=hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest()
    return result


def analyze_frozen_first32(dirpath):
    # Reuses independently SHA-verifiable original 16+16 archives and old
    # Stage26 per-coin watch comparison, with clearly different D1 semantics.
    result=first.analyze_two(dirpath,shared_run=run_v2)
    if result["schema"]!=SCHEMA:
        raise RuntimeError("ZEROQUOTE_RESEARCH_SCHEMA_LOST_IN_FROZEN_COINS")
    result["pilot_schema"]="FIRST32_SOURCE_COMPLETE_NOT_FULL_445"
    result["not_independent_out_of_sample"]=True
    return result


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("ZEROQUOTE_RESEARCH_OUTPUT_EXISTS")
    result=analyze_frozen_first32(a.source_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as f:
        f.write(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("MONSTER_445_FIRST32_ZEROQUOTE_D1_EXPERIMENT "+
        json.dumps({"WATCH":result["execution_counts"]["D0_watch_new"],
          "same_source_32_old_D0_watch":result["original_per_symbol_old_watch_total"],
          "burst_0036":result["new_shared_D0_simultaneous_20260206_0036_UTC"],
          "D1":result["queue_status_counts"],
          "unsupported":result["D1_zero_quote_terminal_candidates"],
          "late":result["execution_counts"]["D1_late"],
          "no_trade":True},sort_keys=True))


if __name__=="__main__":
    main()
