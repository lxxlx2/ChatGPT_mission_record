#!/usr/bin/env python3
"""Stage29b original Stage29 ZIP/JSON SHA, existing Stage27 cash-funded ledger.

POSTHOC: a descriptive 8+ cluster proved favorable on exposed historical prices.
This tests capital shortage, not new heldout profitable buy-signal efficacy.
"""
import argparse
import collections
import hashlib
import json
import zipfile
from pathlib import Path
try:
    import monster_v4_stage27_shared_queue_cash_ledger as money
    import monster_v4_stage29_watch_burst_price_research as diagnosis
except ImportError:
    from scripts import monster_v4_stage27_shared_queue_cash_ledger as money
    from scripts import monster_v4_stage29_watch_burst_price_research as diagnosis

PRE=money.EVIDENCE/"monster_stage29b_burst_cash_diagnostic_frozen_20261011.json"
MEMBER="monster_stage29_all1132_watch_burst_vs_price_proxy_regime.json"

def original(path):
    m=json.loads(PRE.read_text(encoding="utf-8"))
    if m["schema"]!="MONSTER_STAGE29B_POSTHOC_FUNDED_BURST_SENSITIVITY_FROZEN_V1":
        raise ValueError("STAGE29B_CONTRACT_INVALID")
    b=Path(path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=m["original_zip_sha256"]:
        raise ValueError("STAGE29B_SOURCE_ZIP_SHA_MISMATCH")
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=[MEMBER] or z.getinfo(MEMBER).file_size>1_000_000:
            raise ValueError("STAGE29B_SOURCE_MEMBER_MISMATCH")
        raw=z.read(MEMBER)
    if hashlib.sha256(raw).hexdigest()!=m["original_JSON_sha256"]:
        raise ValueError("STAGE29B_SOURCE_JSON_SHA_MISMATCH")
    data=json.loads(raw)
    if (data.get("schema")!="MONSTER_STAGE29_EXPOSED_ALL1132_WATCH_REAL_PRICE_PROXY_NO_STRATEGY_TUNING_V1"
        or data.get("watch_event_count")!=1132):
        raise ValueError("STAGE29B_UNEXPECTED_SOURCE_IDENTITY")
    cases=data["2026_02_06T0036_all_98_watch_event_audit"]
    if len(cases)!=98:raise ValueError("STAGE29B_WATCH_98_MISSING")
    return data,m

def funded(data,m,stage26_original_archives):
    if len(stage26_original_archives)!=36:
        raise ValueError("STAGE29B_ALL_ORIGINAL_36_REQUIRED")
    originals=money.original_cases(stage26_original_archives)
    if len(originals)!=2719:
        raise ValueError("STAGE29B_ORIGINAL_SOURCE_COMPLETE_COUNT_CHANGED")
    replayed=diagnosis.make_event_cases(originals)
    if len(replayed)!=1132:
        raise ValueError("STAGE29B_ORIGINAL_WATCH_COUNT_CHANGED")
    burst=[x for x in replayed if x["bucket"]=="BURST_8PLUS"]
    if len(burst)!=110 or {x["watch_utc"] for x in burst}!={"2026-02-06T00:36:00Z","2026-09-09T22:12:00Z"}:
        raise ValueError("STAGE29B_GENUINE_BURST_110_CHANGED")
    feb=data["2026_02_06T0036_all_98_watch_event_audit"]
    proof_feb=[x for x in burst if x["watch_utc"]=="2026-02-06T00:36:00Z"]
    if (len(proof_feb)!=98 or
        {x["symbol"] for x in proof_feb}!={x["symbol"] for x in feb}):
        raise ValueError("STAGE29B_PREVIOUS_VERIFIED_98_UNMATCHED")
    for x in proof_feb:
        previous=next(v for v in feb if v["symbol"]==x["symbol"])
        if x["cost_proxies"]!=previous["cost_proxies"]:
            raise ValueError("STAGE29B_EXISTING_98_PRICE_PROXIES_CHANGED")
    if sum(x["cost_proxies"]["20"]["status"]=="PRICE_PROXY_ONLY" for x in burst)!=64:
        raise ValueError("STAGE29B_ORIGINAL_64_EVALUABLE_CHANGED")
    groups={}
    for slip in (20,100):
        selected=[];ignored=[]
        for x in burst:
            t=x["cost_proxies"][str(slip)]
            if t["status"]=="SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED":
                ignored.append(x["symbol"])
                continue
            selected.append({"date":x["date"],"symbol":x["symbol"],
                "watch_utc":x["watch_utc"],"proxy_status":t["status"],
                "net_pct":t.get("net_pct")})
        selected.sort(key=lambda x:(x["watch_utc"],x["date"],x["symbol"]))
        if len(selected)!=109 or len(ignored)!=1:
            raise ValueError("STAGE29B_EVENT_PREEXISTING_CAPITAL_OVERLAP_CHANGED")
        groups[str(slip)]={"input_after_original_overlap":len(selected),
            "excluded_old_same_symbol_overlap":ignored,"scenarios":{}}
        for initial,slots in ((30,1),(300,10)):
            for lot in ("FIXED_30U","UP_TO_30U_FRACTIONAL"):
                for censored in (100,0):
                    value=money.money_ledger(selected,initial,slots,lot,slip,censored)
                    key=f"{initial}U_{slots}SLOT_{lot}_{slip}BPS_{censored}PCT_UNKNOWN_EXIT_RECOVERY"
                    groups[str(slip)]["scenarios"][key]=value
    return {
       "schema":"MONSTER_STAGE29B_POSTHOC_ALL_110_BURST_FUNDED_LEDGER_16_SCENARIOS_V1",
       "stage29_zip_JSON_SHA_and_stage26_all36_ZIP_JSON_verified":True,
       "posterior_market_regime_filter":True,
       "same_poll_historical_watches_replayed":len(burst),
       "two_same_poll_events":[{"utc":utc,"watch_count":sum(x["watch_utc"]==utc for x in burst)}
                    for utc in sorted({x["watch_utc"] for x in burst})],
       "original_price_evaluable_20bps":64,
       "funding_results_by_slippage_bps":groups,
       "no_real_orders_or_L2":True,"not_a_validated_profitable_buy_strategy":True,
       "independent_AI_review":"NOT_DONE","deployment":"NO_GO",
       "frank":"UNCHANGED","real_gmail":"OFF","trading":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage29-zip",required=True,type=Path)
    p.add_argument("--stage26-original-zips",nargs=36,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    mdata,manifest=original(a.stage29_zip)
    result=funded(mdata,manifest,a.stage26_original_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    abridged={}
    for slip,group in result["funding_results_by_slippage_bps"].items():
        abridged[slip]={key:{name:val for name,val in data.items() if name!="selected_cases"}
                         for key,data in group["scenarios"].items()}
    print("STAGE29B_FUNDED_JSON "+json.dumps(abridged,sort_keys=True),flush=True)

if __name__=="__main__": main()
