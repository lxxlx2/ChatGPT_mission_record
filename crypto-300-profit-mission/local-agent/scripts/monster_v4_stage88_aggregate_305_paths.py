#!/usr/bin/env python3
"""Fail-closed aggregate original 305 D1 gross-only 24h / 72h path evidence."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path

try:
    import monster_v4_stage88_d1_24h72h_official_paths as src
    from monster_v4_stage80_dual_entry_core import decimal
except ImportError:
    from scripts import monster_v4_stage88_d1_24h72h_official_paths as src
    from scripts.monster_v4_stage80_dual_entry_core import decimal

SCHEMA="MONSTER_STAGE88_ALL305_D1_GROSS_24H_72H_EVIDENCE_SUMMARY_V1"
METRICS=("fixed_exit_gross_return_pct","max_favorable_HIGH_pct_not_realized",
         "max_adverse_LOW_pct_not_realized","max_close_to_close_drawdown_pct")


def all_rows(folder:Path):
    shards=sorted(folder.glob("monster-stage88-*.json"))
    if len(shards)!=24:
        raise ValueError("STAGE88_REQUIRE_ALL24_SHARDS_"+str(len(shards)))
    original,prev=src.frozen()
    identities={(x["date"],x["symbol"]) for x in original}
    expected_shards={(d,i) for d in src.DATES for i in range(4)}
    obtained_shards=set()
    rows=[]
    for f in shards:
        batch=json.loads(f.read_text())
        if batch.get("schema")!=src.SCHEMA:
            raise ValueError("STAGE88_WRONG_SHARD_SCHEMA")
        ident=(batch["date"],batch["shard"])
        if ident not in expected_shards or ident in obtained_shards:
            raise ValueError("STAGE88_DUPLICATE_OR_OUT_OF_SCOPE_SHARD")
        obtained_shards.add(ident)
        candidates=src.shard_rows(*ident,source=original)
        exp={(x["date"],x["symbol"]) for x in candidates}
        got={(x["date"],x["symbol"]) for x in batch["rows"]}
        if exp!=got or batch["expected"]!=len(exp) or len(batch["rows"])!=len(exp):
            raise ValueError("STAGE88_ORIGINAL_FROZEN_COINS_MISSING")
        if (batch["valid24"]!=sum(x["h24"]["status"]==src.COMPLETE for x in batch["rows"])
           or batch["valid72"]!=sum(x["h72"]["status"]==src.COMPLETE for x in batch["rows"])):
            raise ValueError("STAGE88_SHARD_VALID_COUNTS_NOT_TRUSTWORTHY")
        rows.extend(batch["rows"])
    if obtained_shards!=expected_shards or len(rows)!=305 or {
        (x["date"],x["symbol"]) for x in rows} != identities:
        raise ValueError("STAGE88_NOT_ALL305_ORIGINAL_D1")
    index={(x["date"],x["symbol"]):x for x in original}
    for x in rows:
        old=index[(x["date"],x["symbol"])]
        if (x["D1_FIRST_UTC"]!=old["D1_FIRST_UTC"] or x["D0_FIRST_UTC"]!=old["D0_FIRST_UTC"]
             or x["D1_PATH"]!=old["D1_PATH"]
             or x["identity"]!=old["identity"]):
            raise ValueError("STAGE88_HISTORY_EDITED_DURING_AGGREGATION")
        if x["h24"]["status"] not in (src.COMPLETE,src.CENSORED,src.NO_BAR) or \
                x["h72"]["status"] not in (src.COMPLETE,src.CENSORED,src.NO_BAR):
            raise ValueError("STAGE88_UNKNOWN_OUTCOME_STATUS")
        if x["h72"]["status"]==src.COMPLETE and x["h24"]["status"]!=src.COMPLETE:
            raise ValueError("STAGE88_LONG_HORIZON_CANNOT_COMPLETE_IF_SHORT_UNKNOWN")
    return sorted(rows,key=lambda x:(x["date"],x["symbol"]))


def median(values):
    if not values:return None
    seq=sorted(decimal(x) for x in values)
    n=len(seq)
    return str(seq[n//2]) if n%2 else str((seq[n//2-1]+seq[n//2])/2)


def summarize(rows,scope):
    response={"original_coin_dates":len(rows)}
    for tag in ("h24","h72"):
        valid=[x[tag] for x in rows if x[tag]["status"]==src.COMPLETE]
        profits=[decimal(x["fixed_exit_gross_return_pct"]) for x in valid]
        response[tag]={
            "source_scored":len(valid),"source_censored_or_untraded":len(rows)-len(valid),
            "fixed_exit_positive_gross_count":sum(x>0 for x in profits),
            "fixed_exit_positive_gross_fraction":(
                str(Decimal(sum(x>0 for x in profits))/len(valid)) if valid else None),
            "fixed_exit_negative_gross_count":sum(x<0 for x in profits),
            "fixed_exit_zero_gross_count":sum(x==0 for x in profits),
            "fixed_exit_gross_median_pct":median([x["fixed_exit_gross_return_pct"] for x in valid]),
            "fixed_exit_gross_sum_not_a_portfolio_return_pct":str(sum(profits)) if valid else None,
            "fixed_exit_20pct_or_more_loss_count":sum(x<=-20 for x in profits),
            "fixed_exit_50pct_or_more_loss_count":sum(x<=-50 for x in profits),
            "mfe_high_median_pct_unrealizable_max":median([
                x["max_favorable_HIGH_pct_not_realized"] for x in valid]),
            "mae_low_median_pct_risk_proxy":median([
                x["max_adverse_LOW_pct_not_realized"] for x in valid]),
            "max_close_drawdown_median_pct":median([
                x["max_close_to_close_drawdown_pct"] for x in valid]),
        }
    response["group_label"]=scope
    return response


def aggregate(rows):
    groups={"full_mixed_USDM_all305":rows}
    for d in src.DATES:
        groups["date_"+d]=[x for x in rows if x["date"]==d]
    for path in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
        groups["entry_"+path]=[x for x in rows if x["D1_PATH"]==path]
    for label in (True,False):
        groups["seven_day_anchor_2x_"+str(label).lower()]=[
            x for x in rows if x["historical_anchor_2x_EVALUATION_ONLY"]==label]
    identities=Counter(x["identity"] for x in rows)
    status={
       horizon:dict(Counter(x[horizon]["status"] for x in rows))
       for horizon in ("h24","h72")
    }
    summary={
        "schema":SCHEMA,
        "frozen_stage85_git_blob":src.PIN85,
        "frozen_stage83_git_blob":src.PIN83,
        "original_first_D1_census":len(rows),
        "official_source_status_counts":status,
        "actual_entry_bar_supported":sum(
            x["entry_delayed_1m"]["status"]=="BAR_HAS_TRADES_PRICE_ONLY" for x in rows),
        "identity_status_counts":dict(identities),
        "five_day_price_window_cut_after_7day_anchor":True,
        "groups":{key:summarize(value,key) for key,value in groups.items()},
        "absolute_gross_returns_not_trade_returns":True,
        "price_only_futures_historical_no_real_entry_or_exit":True,
        "survivorship_selection_only_D1_not_all_D0":True,
        "user_order_notional":"UNSPECIFIED",
        "fee_slippage_depth":"UNKNOWN",
        "real_executable_net_pnl":"UNKNOWN",
        "new_oos":"NOT_DONE",
        "historical_exposure":"EXPOSED_SIX_WINDOWS_ONLY",
        "independent_other_ai_review":"NOT_DONE",
        "deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"
    }
    total=summary["groups"]["full_mixed_USDM_all305"]
    for key in ("h24","h72"):
        if (total[key]["source_scored"]+total[key]["source_censored_or_untraded"])!=305:
            raise ValueError("STAGE88_305_DENOMINATOR_LOST")
    if sum(identities.values())!=305:
        raise ValueError("STAGE88_SCOPE_NOT_ALL305")
    return summary,rows


def selftest():
    assert median(["1","3"])=="2"
    assert median(["-3","1","2"])=="1"
    assert src.frozen()[0] and len(src.frozen()[0])==305
    assert len(src.DATES)==6
    print("STAGE88_FULL305_COHORT_GROSS_PATH_AGGREGATION_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--artifact-dir",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.artifact_dir or not a.out:p.error("--artifact-dir, --out required")
    rows=all_rows(a.artifact_dir)
    result,detail=aggregate(rows)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage88_all305_D1_post_signal_24h72h_price_paths.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in detail))
    (a.out/"monster_stage88_all305_D1_24h72h_price_only_summary.json").write_text(
        json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE88_FROZEN305_GROSS_ONLY "+json.dumps({
        "n":result["original_first_D1_census"],
        "valid24":result["groups"]["full_mixed_USDM_all305"]["h24"]["source_scored"],
        "valid72":result["groups"]["full_mixed_USDM_all305"]["h72"]["source_scored"],
        "h24":result["groups"]["full_mixed_USDM_all305"]["h24"]["fixed_exit_gross_median_pct"],
        "h72":result["groups"]["full_mixed_USDM_all305"]["h72"]["fixed_exit_gross_median_pct"]},
        sort_keys=True))


if __name__=="__main__":
    main()
