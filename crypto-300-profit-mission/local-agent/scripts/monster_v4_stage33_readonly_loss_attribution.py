#!/usr/bin/env python3
"""Stage33: audit-only loss attribution; do NOT modify Stage32 rules or tune a strategy.

Original 36 GitHub ZIP/JSON SHAs and official publisher source commitments are
revalidated by Stage32 verifier. Funded positions use exact frozen Stage27 ledger.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

try:
    import monster_v4_stage32_aggregate as stage32
    import monster_v4_stage27_shared_queue_cash_ledger as cash
except ImportError:
    from scripts import monster_v4_stage32_aggregate as stage32
    from scripts import monster_v4_stage27_shared_queue_cash_ledger as cash

SOURCE_FINAL_SHA256 = "33285d1030a17d09f35e74e6ed28349793af1506237859a8c32ea754634c0476"
SOURCE_FINAL_JSON = "monster_stage32_final_full_dual_1m3m_300U_sha_comparison.json"
SCHEMA = "MONSTER_STAGE33_READONLY_36_ORIGINAL_SHA_LOSS_ATTRIBUTION_V1"

def actual_reports(files):
    proof = json.loads(stage32.ARTIFACT_PROOF.read_text(encoding="utf-8"))
    lookup = {(v["date"], v["shard"]): v for v in proof["artifacts"]}
    if proof.get("source_ci_status") != "SUCCESS_ALL_36" or len(lookup) != 36 or len(files) != 36:
        raise ValueError("STAGE33_NOT_ALL_TRUE_STAGE32_ORIGINALS")
    reports = {}
    for path in files:
        with zipfile.ZipFile(path) as z:
            if len(z.namelist()) != 1:
                raise ValueError("STAGE33_UNKNOWN_ZIP_MEMBER")
            member = z.namelist()[0]
        if not member.startswith("monster_stage32_") or not member.endswith(".json"):
            raise ValueError("STAGE33_WRONG_ORIGINAL_ZIP")
        date, shard = member.removeprefix("monster_stage32_").removesuffix(".json").split("_shard")
        key = date, int(shard)
        if key not in lookup or int(shard) in reports.get(date, {}):
            raise ValueError("STAGE33_UNKNOWN_OR_DUPLICATE_SOURCE")
        reports.setdefault(date, {})[int(shard)] = stage32.verify_zip(path, lookup[key])
    stage32.original_cohort(reports)
    return reports

def load_frozen_final(path):
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_FINAL_SHA256:
        raise ValueError("STAGE33_ORIGINAL_FINAL_ZIP_SHA_CHANGED")
    with zipfile.ZipFile(path) as z:
        if z.namelist() != [SOURCE_FINAL_JSON]:
            raise ValueError("STAGE33_ORIGINAL_FINAL_JSON_MEMBER_CHANGED")
        result = json.loads(z.read(SOURCE_FINAL_JSON))
    if result.get("schema") != "MONSTER_STAGE32_FULL6_NEW_DATE_ORIGINAL36_SHA_PAIRED_1M_VS3M_V4_V1":
        raise ValueError("STAGE33_WRONG_FROZEN_FINAL_SCHEMA")
    return result

def split_funded(cases):
    selected = cases["selected_cases"]
    status = Counter(s["source_status"] for s in selected)
    by_date = {}
    for date in stage32.research.NEW_DAYS:
        d = [s for s in selected if s["date"] == date]
        by_date[date] = {
            "selected": len(d),
            "priced_winners": sum(s["source_status"] == "PRICE_PROXY_ONLY" and s["assumed_exit_USDT"] > s["entry_USDT"] for s in d),
            "priced_losers": sum(s["source_status"] == "PRICE_PROXY_ONLY" and s["assumed_exit_USDT"] < s["entry_USDT"] for s in d),
            "unverified_exit": sum(s["source_status"] != "PRICE_PROXY_ONLY" for s in d),
            "settled_proxy_PnL_USDT": round(sum(s["assumed_exit_USDT"]-s["entry_USDT"] for s in d),6),
        }
    losers = sorted((s for s in selected if s["assumed_exit_USDT"] < s["entry_USDT"]),
                    key=lambda s: s["assumed_exit_USDT"]-s["entry_USDT"])
    gross_loss = sum(s["entry_USDT"]-s["assumed_exit_USDT"] for s in losers)
    winners = [s for s in selected if s["assumed_exit_USDT"] > s["entry_USDT"]]
    gross_gain = sum(s["assumed_exit_USDT"]-s["entry_USDT"] for s in winners)
    top = [{
        "date": s["date"], "symbol": s["symbol"], "watch_utc": s["watch_utc"],
        "pnl_USDT": round(s["assumed_exit_USDT"]-s["entry_USDT"],6)
    } for s in losers[:10]]
    return {
        "selected_status_counts": dict(status), "by_date": by_date,
        "gross_selected_losses_USDT": round(gross_loss,6),
        "gross_selected_gains_USDT": round(gross_gain,6),
        "top10_gross_loss_fraction": round(sum(-v["pnl_USDT"] for v in top)/gross_loss,6) if gross_loss else None,
        "worst_10_funded": top,
    }

def inspect(rows, arm, cost):
    labels = Counter()
    known = []
    for r in rows:
        for t in r[arm]["trade_proxies"]:
            proxy = t["proxy_"+str(cost)+"bps"]
            if proxy is None:
                labels["SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"] += 1
            else:
                labels[proxy["status"]] += 1
                if proxy["status"] == "PRICE_PROXY_ONLY":
                    known.append(proxy)
    negatives = [p for p in known if p["net_pct"] < 0]
    return {
        "all_watch": sum(labels.values()), "status_counts": dict(labels),
        "evaluable": len(known), "winning": sum(p["net_pct"] > 0 for p in known),
        "losing": len(negatives),
        "losing_with_any_positive_high_during_hold": sum(p.get("max_high_excursion_pct",0)>0 for p in negatives),
        "losing_with_high_excursion_over_10pct": sum(p.get("max_high_excursion_pct",0)>10 for p in negatives),
        "warning": "The future intrahold HIGH is hindsight, not an executable limit fill or a model input."
    }

def analyze(files, final_zip):
    reports = actual_reports(files)
    original = load_frozen_final(final_zip)
    recalc = stage32.study(reports)
    if recalc != original:
        raise ValueError("STAGE33_FULL_ORIGINAL_STAGE32_AGGREGATE_DRIFT")
    rows = [r for r in stage32.original_cohort(reports) if r["status"] == "COMPLETE_BOTH_168H"]
    result = {
        "schema": SCHEMA, "full36_SHA_and_frozen_Stage32_profit_recomputed": True,
        "source_run_id": 38158924838, "source_aggregate_run_id": 38161283627,
        "universe_attempted": 4548, "paired_valid": len(rows),
        "research_only": True, "new_strategy_backtest": False,
        "independent_other_AI_review": "NOT_DONE",
        "trading": "NO_GO", "Monster_deployment": "NO_GO", "real_Gmail": "OFF", "Frank": "UNCHANGED",
        "arms": {}
    }
    for arm,key in (("V4_original3m","original3min"),("V4_candidate1m","candidate1min")):
        d = {}
        for cost in (20,100):
            desc = inspect(rows,arm,cost)
            entries, skipped = stage32.candidate_entries(rows,arm,cost)
            if skipped != desc["status_counts"].get("SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED",0):
                raise ValueError("STAGE33_OVERLAP_LOSS")
            original_case = original["economic_"+key][str(cost)]
            if desc["all_watch"] != original_case["all_watch"] or desc["evaluable"] != original_case["valid_trade_proxies"]:
                raise ValueError("STAGE33_WATCH_COUNT_DRIFT")
            desc["funded_300USDT_10fixed30USDT"] = {}
            for recovery in (100,0):
                funded = cash.money_ledger(entries,300,10,"FIXED_30U",cost,recovery)
                name = f"300U_10SLOT_{cost}BPS_CENSORED_{recovery}PCT"
                if {k:v for k,v in funded.items() if k!="selected_cases"} != original_case["cash_funded_no_overdraft"][name]:
                    raise ValueError("STAGE33_ORIGINAL_STAGE27_FUNDED_CASH_MISMATCH")
                desc["funded_300USDT_10fixed30USDT"][str(recovery)] = {
                    "final_cash_USDT": funded["final_cash_USDT"],
                    "profit_USDT": funded["realized_proxy_profit_USDT"],
                    "counts": funded["counts"],
                    **split_funded(funded)
                }
            d[str(cost)] = desc
        result["arms"][key] = d
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original-zips", required=True, nargs=36, type=Path)
    p.add_argument("--stage32-final", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    report = analyze(args.original_zips,args.stage32_final)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE33_VERIFIED_FUNDED_LOSS_DIAGNOSTIC "+json.dumps({
      a:{k:{"watch":v["all_watch"],"300U_optimistic_profit":v["funded_300USDT_10fixed30USDT"]["100"]["profit_USDT"]}
         for k,v in q.items()} for a,q in report["arms"].items()},sort_keys=True))

if __name__ == "__main__":
    main()
