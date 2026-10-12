#!/usr/bin/env python3
"""Monster Stage59: source-locked 166 event venue evidence ledger.

Only documentary/historical venue evidence, no predictor, trading cost or fixed
order size. Alpha listings were announced before signal; continuing liquidity
and actual fills AT signal are not demonstrated by an old announcement.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SPOT=E/"monster_stage57_all166_exact_symbol_spot_asof_source_SHA.jsonl"
OLD=E/"monster_stage58_exposed_spot_only_cap5_counterfactual_summary.json"
SHA={SPOT.name:"561b5a7dd5b894565d01b24671aa6d96d921bda8",
     OLD.name:"a0f377027ec49e8ec572fba53a2c8cf8872b3180"}
SPOT_YES="EXACT_SYMBOL_SPOT_15M_SOURCE_COMPLETE_WITH_TRADES"
S="MONSTER_STAGE59_EXPOSED_166_VENUE_AT_SIGNAL_DOCUMENTARY_EVIDENCE_V1"
# Binance original English publisher announcements; these are primary
# time-prior exchange announcements, NOT proof of an Alpha fill at signal.
ALPHA={
 ("2025-08-01","MYXUSDT"):{
  "project":"MYX Finance",
  "publisher":"Binance",
  "source_url":"https://www.binance.com/en-IN/support/announcement/detail/9801625522154e098d73b8245ad70646",
  "original_published_UTC":"2025-06-18T09:51:00Z",
  "alpha_open_UTC":None,
  "alpha_assertion":"ALREADY_LISTED_AS_OF_OFFICIAL_ANNOUNCEMENT",
  "scope":"Binance Alpha, separate from Binance Spot",
 },
 ("2025-10-02","AIAUSDT"):{
  "project":"DeAgent AI",
  "publisher":"Binance",
  "source_url":"https://www.binance.com/en/support/announcement/detail/aadbfbfee34c404c896f93957a0c08c7",
  "original_published_UTC":"2025-09-16T11:00:00Z",
  "alpha_open_UTC":"2025-09-18T08:00:00Z",
  "alpha_assertion":"SCHEDULED_ALPHA_OPEN_UTC_BEFORE_SIGNAL",
  "scope":"Binance Alpha, separate from Binance Spot",
 },
 ("2025-10-02","COAIUSDT"):{
  "project":"ChainOpera AI",
  "publisher":"Binance",
  "source_url":"https://www.binance.com/en/support/announcement/detail/89921e2281204d32a5fead5b711f6770",
  "original_published_UTC":"2025-09-23T08:45:00Z",
  "alpha_open_UTC":"2025-09-25T07:00:00Z",
  "alpha_assertion":"SCHEDULED_ALPHA_OPEN_UTC_BEFORE_SIGNAL",
  "scope":"Binance Alpha, separate from Binance Spot",
 },
}

def sha_git(p):
    blob=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()

def time(s):
    d=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.utcoffset()!=dt.timedelta(0):raise ValueError("STAGE59_TIMEZONE_UNKNOWN")
    return d

def inputs():
    for p in (SPOT, OLD):
        if SHA[p.name].startswith("a_PLACEHOLDER"):
            raise ValueError("STAGE59_NEEDS_PRECISE_STAGE58_BLOB_LOCK")
        if sha_git(p)!=SHA[p.name]:
            raise ValueError("STAGE59_EVIDENCE_SOURCE_CHANGED "+p.name)
    rows=[json.loads(s) for s in SPOT.read_text(encoding="utf-8").splitlines() if s]
    old=json.loads(OLD.read_text(encoding="utf-8"))
    if (len(rows),old["input_usdm_all_166"],old["confirmed_exact_symbol_spot_subcohort"])!=(166,166,76):
        raise ValueError("STAGE59_NOT_FULL_ORIGINAL166")
    if len({(x["date"],x["futures_symbol"]) for x in rows})!=166:
        raise ValueError("STAGE59_DUPLICATE_ORIGINAL_SYMBOL")
    return rows,old

def assess(rows,old):
    observed={}
    for x in rows:
        key=(x["date"],x["futures_symbol"])
        name=x["futures_symbol"]
        alpha=ALPHA.get(key)
        spot=x["spot_result"]==SPOT_YES
        if alpha:
            t=time(x["eligible_timestamp_UTC"])
            if not time(alpha["original_published_UTC"])<t:
                raise ValueError("STAGE59_ALPHA_ANNOUNCEMENT_AFTER_SIGNAL")
            if alpha["alpha_open_UTC"] and not time(alpha["alpha_open_UTC"])<t:
                raise ValueError("STAGE59_ALPHA_OPEN_NOT_BEFORE_SIGNAL")
            if spot:
                raise ValueError("STAGE59_CONFLICT_ALPHA_POSITIVE_SPOT_ALREADY_KNOWN")
        if spot:
            status="HISTORIC_BINANCE_SPOT_REAL_TRADES_SHA_VERIFIED"
        elif alpha:
            status="BINANCE_ALPHA_ANNOUNCED_BEFORE_SIGNAL_NO_FILL_VERIFICATION"
        else:
            status="UNKNOWN_ALTERNATIVE_VENUE_NOT_CHECKED"
        result={
          "date":key[0],"futures_symbol":name,"eligible_timestamp_UTC":x["eligible_timestamp_UTC"],
          "historical_USDM_futures_1m_confirmed":True,
          "historical_exact_symbol_spot_trades_SHA_verified":spot,
          "historical_spot_quote15_USDT_if_confirmed":x["spot_quote_15m_USDT_observed_in_available_source"] if spot else None,
          "historical_spot_trades15_if_confirmed":x["spot_trades_15m_observed_in_available_source"] if spot else None,
          "venue_evidence_status":status,"official_prior_alpha_announcement":alpha,
          "execution_at_signal_confirmed":False,
          "order_notional_user_selected":None,
          "notional_status":"UNSPECIFIED_NO_FIXED_AMOUNT",
          "historical_limit_orderbook_available":False,
          "historical_dex_liquidity_confirmed":False,
          "net_profit_or_slippage_verified":False,
          "posthoc_label_for_evaluation_ONLY":x["posthoc_label_EVALUATION_ONLY"],
          "original_priority_research_delivered":x["futures_research_delivered"],
        }
        observed[key]=result
    if set(ALPHA).difference(observed):
        raise ValueError("STAGE59_ALPHA_CASE_MISSING_FROM_ORIGINAL166")
    hist=old["high5x10x_exposed_original_source_cases"]
    if len(hist)!=3:
        raise ValueError("STAGE59_ORIGINAL_BIG_WINNERS_NOT_3")
    critical=[]
    for h in hist:
        key=h["date"],h["symbol"]
        row=observed[key]
        if row["venue_evidence_status"]!="BINANCE_ALPHA_ANNOUNCED_BEFORE_SIGNAL_NO_FILL_VERIFICATION":
            raise ValueError("STAGE59_HIGH_MULTIPLE_ALPHA_PRIOR_PROOF_NOT_PRESENT")
        critical.append({"date":key[0],"symbol":key[1],
                         "historical_future_high_gt5x":True,
                         "historical_future_high_gt10x":bool(h["actual_GT10_HISTORIC"]),
                         "venue_announcement_pre_signal":True,
                         "executability_at_signal_UNVERIFIED":True,
                         "publisher":row["official_prior_alpha_announcement"]["source_url"]})
    by_label={}
    labels=("FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN","FUTURE_2X_BUT_CANDIDATE_LATE",
            "ORDINARY_NOT_CALENDAR_2X")
    for k in labels:
        xs=[v for v in observed.values() if v["posthoc_label_for_evaluation_ONLY"]==k]
        by_label[k]={"n":len(xs),"venue_evidence_counts":dict(sorted(collections.Counter(v["venue_evidence_status"] for v in xs).items()))}
    counts=collections.Counter(v["venue_evidence_status"] for v in observed.values())
    if (counts["HISTORIC_BINANCE_SPOT_REAL_TRADES_SHA_VERIFIED"],
        counts["BINANCE_ALPHA_ANNOUNCED_BEFORE_SIGNAL_NO_FILL_VERIFICATION"],
        counts["UNKNOWN_ALTERNATIVE_VENUE_NOT_CHECKED"])!=(76,3,87):
        raise ValueError("STAGE59_COUNTS_DO_NOT_MATCH_DOCUMENTARY_SCOPE")
    return sorted(observed.values(),key=lambda x:(x["date"],x["futures_symbol"])),{
      "schema":S,"source_pin_git_blobs":SHA,"all_original_usdm_candidates":166,
      "venue_evidence_counts":dict(sorted(counts.items())),
      "by_posthoc_label_for_descriptive_analysis_only":by_label,
      "historical_5x_10x_critical_events":critical,
      "UNKNOWN_IS_NOT_PROOF_UNTRADABLE":True,
      "ALPHA_ANNOUNCEMENT_IS_NOT_EXECUTABLE_FILL":True,
      "NO_ASSUMED_NOTIONAL":True,
      "NEW_STRATEGY_OR_PRIORITY_CHANGE":False,
      "P1_V03":"REJECTED","MONSTER_DEPLOY":"NO_GO",
      "GMAIL":"OFF","FRANK":"UNCHANGED","AUTOTRADE":"NO_GO",
      "OTHER_AI_REVIEW":"NOT_DONE",
    }

def selftest():
    assert time("2025-09-18T08:00:00Z")<time("2025-10-02T14:03:00Z")
    assert time("2025-09-25T07:00:00Z")<time("2025-10-02T07:03:00Z")
    for record in ALPHA.values():
        assert record["source_url"].startswith("https://www.binance.com/")
    print("STAGE59_ANNOUNCEMENT_ASOF_NO_NOTIONAL_NO_FILL_SELFTEST_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--out",type=Path)
    a=parser.parse_args()
    if a.selftest:selftest();return
    if a.out is None:parser.error("--out required")
    rows,old=inputs()
    output,summary=assess(rows,old)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage59_all166_cross_venue_evidence_matrix.jsonl").write_text(
      "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in output),encoding="utf-8")
    (a.out/"monster_stage59_all166_venue_evidence_coverage_summary.json").write_text(
      json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE59_FULL166_UNSPECIFIED_NOTIONAL_VENUE_EVIDENCE_LEDGER "+
          json.dumps(summary["venue_evidence_counts"],sort_keys=True))

if __name__=="__main__":
    main()
