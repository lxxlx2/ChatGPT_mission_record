#!/usr/bin/env python3
"""Stage119 read-only D0/D1 forward D2 audit for one frozen Stage116 window.

Accepts authenticated Stage97 capture and completed source Stage116 replay;
optional human-supplied per-event D2 evidence and optional explicitly supplied
notional. Never fetches, captures, trades, deploys, schedules or emails.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

try:
    import monster_v4_stage119_cohort_execution_bridge as bridge
    import monster_v4_stage116_forward_population_score as source
    import monster_v4_stage120_exchangeinfo_execution_rules as rules
except ImportError:
    from scripts import monster_v4_stage119_cohort_execution_bridge as bridge
    from scripts import monster_v4_stage116_forward_population_score as source
    from scripts import monster_v4_stage120_exchangeinfo_execution_rules as rules

SCHEMA="MONSTER_STAGE119_FROZEN_FORWARD_WINDOW_EXECUTION_EVIDENCE_V1"


def validate_bundle(path, event):
    if path is None:
        return None
    filename=path/(event["event_id"]+".json")
    if not filename.is_file():
        return None
    doc=json.loads(filename.read_text())
    if doc.get("schema")!="MONSTER_STAGE119_EXPLICIT_D2_EVENT_EVIDENCE_V1":
        raise ValueError("STAGE119_FORWARD_EVIDENCE_SCHEMA_UNKNOWN")
    if (doc.get("event_id")!=event["event_id"] or
        doc.get("venue")!=event["venue"] or
        doc.get("symbol")!=event["symbol"] or
        doc.get("observed_ms")!=event["observed_ms"]):
        raise ValueError("STAGE119_FORWARD_EVENT_PROVENANCE_MISMATCH")
    payload=doc.get("evidence")
    if not isinstance(payload,dict):
        raise ValueError("STAGE119_FORWARD_EMPTY_EXTERNAL_EVIDENCE_BUNDLE")
    return payload


def audit_rows(window,validated,source_sha,*,evidence_dir=None,user_notional=None,verified_market_metadata=None):
    """Consumes ONLY already-validated frozen full venue source rows."""
    if window not in source.WINDOWS:
        raise ValueError("STAGE119_FORBIDDEN_BACKDATED_WINDOW")
    expected_attempts=len(validated)
    if len({x["symbol"] for x in validated})!=expected_attempts:
        raise ValueError("STAGE119_FORWARD_DUPLICATE_ATTEMPTS")
    seen=set()
    all_evidence=[]
    counter=Counter()
    rejected_sources=Counter()
    for row in validated:
        if row["date"]!=window[:10] or row["venue"]!="BINANCE_USDM":
            raise ValueError("STAGE119_FORWARD_INVALID_SOURCE_DATE_OR_VENUE")
        status=row["source_status"]
        metadata=None
        if verified_market_metadata is not None:
            metadata=verified_market_metadata["per_symbol"].get(row["symbol"])
            if (metadata is None or metadata["exchangeInfo_original_raw_sha256"]!=source_sha):
                raise ValueError("STAGE120_INDEPENDENT_SNAPSHOT_MARKET_CONTEXT_MISSING")
            attached=row.get("stage120_original_asof_contract_metadata")
            if attached is not None and attached!=metadata:
                raise ValueError("STAGE120_FORWARD_MANIFEST_METADATA_NOT_SAME_VERIFIED_BYTES")
            counter["asof_full_original_market_metadata_covered"]+=1
            counter["asof_trade_filters_complete"]+=int(
                metadata["filter_rules_at_snapshot"]["status"]==
                "COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION")
        counter["original_full_market_symbols_attempted"]+=1
        if status!="COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY":
            counter["source_censored_or_incomplete"]+=1
            rejected_sources[status]+=1
            continue
        counter["original_complete_9day_publisher_source"]+=1
        if row.get("Crypto_identity") not in (
            "UNKNOWN_NEEDS_INDEPENDENT_ASOF_PROOF",
            "VERIFIED_CRYPTO_ASOF","CONFIRMED_NONCRYPTO_OUT_OF_SCOPE"):
            raise ValueError("STAGE119_UNKNOWN_USDM_MARKET_IDENTITY_ENUM")
        if row.get("Crypto_identity")=="VERIFIED_CRYPTO_ASOF":
            # No sidecar may claim confirmed identity without proven underlying
            # official/issuer mapping; inherited source is not a proof.
            counter["source_claims_verified_crypto_but_independent_proof_pending"]+=1
        clocks=(
            ("ORIGINAL_D0",row["D0_first_UTC"]),
            ("ORIGINAL_D1",row["D1_first_UTC"]),
        )
        if row["D1_first_UTC"] is not None and row["D0_first_UTC"] is None:
            raise ValueError("STAGE119_ORPHAN_D1")
        original=row.get("stage119_D0_D1_asof_execution_source_readiness")
        if original is not None and len(original)!=sum(clock is not None for _,clock in clocks):
            raise ValueError("STAGE119_LEGACY_REPLAY_BRIDGE_HAS_DIFFERENT_EVENT_COUNT")
        for i,(mode,clock) in enumerate((x for x in clocks if x[1] is not None)):
            event=bridge.scoped_event(
                anchor=window[:10],symbol=row["symbol"],
                venue="BINANCE_USDM",signal_type=mode,observed_utc=clock)
            if event["event_id"] in seen:
                raise ValueError("STAGE119_DUPLICATE_FORWARD_EVENT_ID")
            seen.add(event["event_id"])
            if original is not None:
                legacy=original[i]
                if (legacy["event_id"]!=event["event_id"] or
                    legacy["D2_status"]!="IDENTITY_UNKNOWN" or
                    legacy["net_executable_profit"]!="UNKNOWN"):
                    raise ValueError("STAGE119_STAGE116_ORIGINAL_NO_PROOF_D2_DRIFT")
            proof=validate_bundle(evidence_dir,event)
            read=bridge.evaluate(event,supplied_evidence=proof,
                                 user_notional=user_notional)
            # The Stage120 official exchangeInfo and quantity-rule preflight
            # is separate and never upgrades Stage90's identity/book source.
            if metadata is None:
                eligibility={"status":"SOURCE_METADATA_MISSING",
                    "actual_fill":"NOT_OBSERVED",
                    "net_executable_profit":"UNKNOWN"}
            else:
                eligibility=rules.market_preflight(
                    metadata,book=(proof.get("book") if proof else None),
                    notional_quote=user_notional,observed_ms=event["observed_ms"])
                at_time=rules.at_signal(metadata,event["observed_ms"])
                if at_time["venue_status_at_signal"]==(
                    "SNAPSHOT_TIME_ONLY_NO_INDEPENDENT_CRYPTO_ID"):
                    raise ValueError("STAGE120_SOURCE_SNAPSHOT_NOT_PROOF_OF_CRYPTO")
                eligibility["venue_status_at_signal"]=at_time["venue_status_at_signal"]
            if eligibility.get("net_executable_profit")!="UNKNOWN":
                raise ValueError("STAGE120_FALSE_EXECUTABLE_NET_AT_D0")
            counter["STAGE120_"+eligibility["status"]]+=1
            counter[mode]+=1
            counter[mode+"_"+read["D2_status"]]+=1
            all_evidence.append({
                "event":event,
                "forward_original_Stage118_frozen_attention_only":(
                    row.get("stage118_new_price_or_taker_buy_D0_candidate")
                    if mode=="ORIGINAL_D0" else None),
                "D2_evidence_gap":read,
                "Stage120_frozen_market_filter_and_book_preflight":eligibility,
                "original_forward_2x_high_LABEL_NOT_DECISION_FEATURE":None,
                "real_order_execution_or_fill":"NOT_OBSERVED",
            })
    if len(all_evidence)!=counter["ORIGINAL_D0"]+counter["ORIGINAL_D1"]:
        raise ValueError("STAGE119_FORWARD_SOURCE_EVENT_LOSS")
    summary={
        "schema":SCHEMA,
        "window":window,
        "original_frozen_market_capture_raw_sha256":source_sha,
        "all_original_symbol_attempts":counter["original_full_market_symbols_attempted"],
        "source_9day_complete":counter["original_complete_9day_publisher_source"],
        "source_incomplete":counter["source_censored_or_incomplete"],
        "source_censor_reasons":dict(sorted(rejected_sources.items())),
        "signal_evidence_counts":dict(sorted(counter.items())),
        "D0_D1_events_considered":len(all_evidence),
        "notional_from_user_only":str(user_notional) if user_notional is not None else None,
        "retained_all_raw_attempts_even_if_no_signal":True,
        "lookahead_GT2x_HIGH_used_in_signal_or_execution":False,
        "G0_independent_crypto_asof_proof":"NOT_ESTABLISHED",
        "G4_actual_executable_net":"UNKNOWN",
        "G1_G2_G3_crypto_OOS":"NOT_SCORABLE_FROM_D2_ONLY",
        "Stage118_original_historical_strategy":"REJECTED",
        "Monster_deployment":"NO_GO",
        "Frank":"UNCHANGED",
        "Stage99":"UNCHANGED",
        "Gmail":"OFF","real_trading":"NO_GO",
        "genuine_oos":"ONLY_IF_ALL_FROZEN_SOURCE_WINDOWS_VERIFIED_SEPARATELY",
    }
    return summary,all_evidence


def audit(snapshot,replay,*,evidence_dir=None,user_notional=None):
    window=replay.get("window_start_utc")
    universe=source.audited_capture(snapshot,window)
    rows=source.validate_replay(window,replay,universe)
    original=rules.catalog(snapshot,window)
    if original["raw_market_SHA"]!=universe["raw_sha256"]:
        raise ValueError("STAGE120_CROSS_MODULE_ORIGINAL_EXCHANGE_INFO_BYTES_DIFFER")
    return audit_rows(window,rows,universe["raw_sha256"],
                      evidence_dir=evidence_dir,user_notional=user_notional,
                      verified_market_metadata=original)


def selftest():
    window=source.WINDOWS[0]
    null=audit_rows(window,[{
       "date":window[:10],"venue":"BINANCE_USDM","symbol":"TESTUSDT",
       "source_status":"CENSORED_OR_UNAVAILABLE_OFFICIAL_DAILY_1M",
       "D0_first_UTC":None,"D1_first_UTC":None,
    }],"a"*64)[0]
    assert null["source_incomplete"]==1
    assert null["D0_D1_events_considered"]==0
    row={
       "date":window[:10],"venue":"BINANCE_USDM","symbol":"TESTUSDT",
       "source_status":"COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY",
       "D0_first_UTC":"2026-10-14T06:03:00Z",
       "D1_first_UTC":"2026-10-14T06:12:00Z",
       "Crypto_identity":"UNKNOWN_NEEDS_INDEPENDENT_ASOF_PROOF",
    }
    s,rr=audit_rows(window,[row],"a"*64)
    assert s["source_9day_complete"]==1 and s["D0_D1_events_considered"]==2
    assert len({r["event"]["event_id"] for r in rr})==2
    assert all(r["D2_evidence_gap"]["D2_status"]=="IDENTITY_UNKNOWN" for r in rr)
    assert s["notional_from_user_only"] is None
    assert s["G4_actual_executable_net"]=="UNKNOWN"
    assert all(r["Stage120_frozen_market_filter_and_book_preflight"]["status"]
        =="SOURCE_METADATA_MISSING" for r in rr)
    print("STAGE119_STAGE116_AUTHENTICATED_POPULATION_INTERFACE_SOURCE_CENSORED_AND_D2_CAUSAL_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--snapshot",type=Path)
    p.add_argument("--replay",type=Path)
    p.add_argument("--evidence-dir",type=Path)
    p.add_argument("--notional-quote")
    p.add_argument("--out",type=Path)
    p.add_argument("--rows",type=Path)
    args=p.parse_args()
    if args.selftest:
        selftest()
        return
    if None in (args.snapshot,args.replay,args.out,args.rows):
        p.error("--snapshot --replay --out --rows required, NO capture or live order")
    if args.notional_quote is not None:
        amount=bridge.d2.dec(args.notional_quote)
        if amount<=0:raise ValueError("STAGE119_NONPOSITIVE_EXPLICIT_TEST_NOTIONAL")
    snapshot=json.loads(args.snapshot.read_text())
    replay=json.loads(args.replay.read_text())
    summary,records=audit(snapshot,replay,
                          evidence_dir=args.evidence_dir,
                          user_notional=args.notional_quote)
    for target in (args.out,args.rows):
        target.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    args.rows.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in records))
    print("STAGE119_FORWARD_SOURCE_EXECUTION_READINESS "+
          json.dumps({k:v for k,v in summary.items() if k!="signal_evidence_counts"},sort_keys=True))


if __name__=="__main__":
    main()
