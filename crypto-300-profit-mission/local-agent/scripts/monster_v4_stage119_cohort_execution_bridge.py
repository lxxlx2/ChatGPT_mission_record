#!/usr/bin/env python3
"""Stage119: offline full519 D0/305 D1 to Stage90 D2 execution-readiness bridge.

No source auto-fetch, order, Gmail, watch, default notional or code deployment.
The old D0 / rejected D1 remain unchanged. A snapshot cost is NOT a fill/PnL.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha1, sha256
import json
from pathlib import Path

try:
    import monster_v4_stage90_d2_execution_proof as d2
except ImportError:
    from scripts import monster_v4_stage90_d2_execution_proof as d2

SCHEMA="MONSTER_STAGE119_ORIGINAL519_D0_D1_READONLY_EXECUTABILITY_V1"
CASE_SCHEMA="MONSTER_STAGE118_FROZEN_FIRST_D0_PRICE_OR_TAKER_FLOW_V1"
SOURCE_SHA="c1a84d8da79ca202567332f56042f359c73b4297"
D2_CODE_SHA="d71f46370e40748b7db90d8f18a0599df2522510"
STAGE118_SUMMARY_SHA="f469a4b2b50a6746cd3da295060754990cb6affe"
E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SOURCE=E/"monster_stage118_first_D0_flow_full519_actual_rows.jsonl"
PRIOR=E/"monster_stage118_first_D0_flow_full519_actual_summary.json"
LEGACY_CLASSES={
    "CRYPTO_IDENTITY_UNVERIFIED",
    "MULTIPLIER_MAPPING_UNVERIFIED",
    "CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE",
}
SIDE_PROOF_FIELDS=("identity","mapping","market_status","fees")
TICK=60_000


def git_blob(raw:bytes)->str:
    return sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()


def signal_ms(utc):
    if not isinstance(utc,str) or not utc.endswith("Z"):
        raise ValueError("STAGE119_SIGNAL_NOT_UTC")
    parsed=datetime.fromisoformat(utc[:-1]+"+00:00")
    if parsed.tzinfo!=timezone.utc or parsed.second!=0 or parsed.microsecond!=0:
        raise ValueError("STAGE119_SOURCE_CLOCK_NOT_CLOSED_MINUTE")
    ms=int(parsed.timestamp()*1000)
    if ms%(3*TICK)!=0:
        raise ValueError("STAGE119_ORIGINAL_V4_3MIN_POLL_CLOCK_DRIFT")
    return ms


def read_source():
    a=SOURCE.read_bytes()
    b=PRIOR.read_bytes()
    if git_blob(a)!=SOURCE_SHA or git_blob(b)!=STAGE118_SUMMARY_SHA:
        raise ValueError("STAGE119_STAGE118_ALL519_GIT_BLOB_CHANGED")
    if git_blob(Path(d2.__file__).read_bytes())!=D2_CODE_SHA:
        raise ValueError("STAGE119_EXISTING_D2_ENGINE_CODE_CHANGED")
    rows=[json.loads(line) for line in a.decode().splitlines() if line.strip()]
    info=json.loads(b)
    if (len(rows)!=519 or info["complete_original_D0"]!=519 or
            info["original_D1_pop"]!=305 or
            info["new_two_lane_first_D0_attention"]!=183 or
            info["new_D0_fast_early2x5m"]!=18 or
            info["research_decision"]!="REJECTED_HISTORICAL_EARLY_2X_RECALL"):
        raise ValueError("STAGE119_UPSTREAM_REJECTION_MUST_BE_PRESERVED")
    if len({(r["date"],r["symbol"]) for r in rows})!=519:
        raise ValueError("STAGE119_DUPLICATE_ORIGINAL_MARKET_CASES")
    return sorted(rows,key=lambda r:(r["date"],r["symbol"])),info


def scoped_event(*,anchor,symbol,venue,signal_type,observed_utc):
    if venue!="BINANCE_USDM" or signal_type not in ("ORIGINAL_D0","ORIGINAL_D1"):
        raise ValueError("STAGE119_INVALID_ORIGINAL_EVENT_TYPE")
    if not isinstance(symbol,str) or not symbol.endswith("USDT"):
        raise ValueError("STAGE119_USDM_EVENT_BAD_SYMBOL")
    t=signal_ms(observed_utc)
    start=int(datetime.fromisoformat(anchor+"T06:00:00+00:00").timestamp()*1000)
    if not start<=t<start+7*86_400_000:
        raise ValueError("STAGE119_EVENT_OUTSIDE_ORIGINAL_ANCHOR")
    key="MONSTER_STAGE119|"+venue+"|"+anchor+"|"+symbol+"|"+signal_type+"|"+observed_utc
    return {
        "venue":venue,"symbol":symbol,"observed_ms":t,
        "anchor_date":anchor,"event_type":signal_type,
        "event_id":sha256(key.encode("ascii")).hexdigest(),
        "idempotency_key":key,
        "original_event_timestamp_utc":observed_utc,
    }


def provenance_check(supplied, now):
    """Hash integrity is necessary, not sufficient for independent authenticity.

    No human-asserted "verified=True" is treated as independent API identity
    provenance. Never promote G0 on SHA syntax or a raw future book alone.
    """
    if not isinstance(supplied,dict):
        return "NONOBJECT_EXTERNAL_SOURCE_PROOF"
    for k in SIDE_PROOF_FIELDS:
        item=supplied.get(k)
        if not isinstance(item,dict):
            return "MISSING_RAW_"+k.upper()
        raw=item.get("raw_json")
        digest=item.get("raw_response_sha256")
        if not isinstance(raw,str) or sha256(raw.encode()).hexdigest()!=digest:
            return "RAW_SHA_MISSING_OR_BAD_"+k.upper()
        if not isinstance(item.get("capture_ms"),int) or isinstance(item["capture_ms"],bool):
            return "CAPTURE_TIME_MISSING_"+k.upper()
        if item["capture_ms"]>now and k!="fees":
            return "FUTURE_SOURCE_"+k.upper()
        if not isinstance(item.get("source_url"),str) or not item["source_url"].startswith("https://"):
            return "ORIGINAL_SOURCE_URL_MISSING_"+k.upper()
        if not item.get("external_authenticity_evidence"):
            return "EXTERNAL_AUTHENTICITY_UNKNOWN_"+k.upper()
    return None


def evaluate(event, *, identity_classification="CRYPTO_IDENTITY_UNVERIFIED",
             supplied_evidence=None, user_notional=None):
    """Return a typed G0/G4 research status; never output actionable BUY."""
    if identity_classification not in LEGACY_CLASSES:
        raise ValueError("STAGE119_UNSUPPORTED_LEGACY_IDENTITY_CLASS")
    if user_notional is not None:
        amt=d2.dec(user_notional)
        if amt<=0:raise ValueError("STAGE119_INVALID_EXPLICIT_NOTIONAL")
    candidate={k:event[k] for k in ("symbol","venue","observed_ms")}
    if supplied_evidence is None:
        proof={"identity":{"classification":identity_classification}}
        out=d2.evaluate(candidate,proof,notional_quote=user_notional)
        origin="ORIGINAL_CASE_ONLY_NO_ACTUAL_BOOK_CAPTURE"
        external="NOT_PRESENT"
    else:
        if not isinstance(supplied_evidence,dict):
            raise ValueError("STAGE119_EXTERNAL_EVIDENCE_NOT_OBJECT")
        identity=supplied_evidence.get("identity",{})
        if isinstance(identity,dict) and identity.get("classification")=="CONFIRMED_CRYPTO":
            blocker=provenance_check(supplied_evidence,event["observed_ms"])
            if blocker is not None:
                out=d2.result("SOURCE_PROVENANCE_UNVERIFIED",blocker)
                origin="RAW_ORIGIN_UNATTESTED"
                external="MISSING_OR_MISMATCHED"
            else:
                out=d2.evaluate(candidate,supplied_evidence,
                                notional_quote=user_notional)
                origin="RAW_BYTE_CONSISTENCY_ONLY_EXTERNAL_AUTH_MUST_BE_REVIEWED"
                external="CLAIM_PRESENT_IN_UNTRUSTED_ARCHIVE"
        else:
            out=d2.evaluate(candidate,supplied_evidence,
                            notional_quote=user_notional)
            origin="EXPLICIT_TYPED_INPUT_UNPROVEN"
            external="UNKNOWN"
    if out.get("real_buy_or_sell_fill")!="NOT_OBSERVED":
        raise ValueError("STAGE119_EXISTING_D2_ASSERTED_NONEXISTENT_EXECUTION")
    return {
        "schema":SCHEMA,"event_id":event["event_id"],
        "anchor_date":event["anchor_date"],"symbol":event["symbol"],
        "venue":event["venue"],"event_type":event["event_type"],
        "observed_ms":event["observed_ms"],
        "D2_status":out["status"],"D2_reason":out["reason"],
        "D2_returned_source_contract":out["schema"],
        "source_provenance_level":origin,
        "independent_external_source_authenticity":external,
        "notional_from_user":str(user_notional) if user_notional is not None else None,
        "market_entry_or_exit_actual_fill":"NOT_OBSERVED",
        "net_executable_profit":"UNKNOWN",
        "G0_crypto_scope":"NOT_ATTESTED",
        "G4_live_executable_profit":"NOT_SCORABLE",
        "research_only_no_trade":True,
        "Monster_deploy":"NO_GO",
    }


def audit_historic():
    rows,prior=read_source()
    all_events=[]
    seen=set()
    counts=Counter()
    per_day=defaultdict(Counter)
    identity_case=Counter()
    for r in rows:
        kind=r["original_crypto_identity_UNVERIFIED"]
        if kind not in LEGACY_CLASSES:
            raise ValueError("STAGE119_CASE_CRYPTO_CLASS_UNKNOWN")
        d=r["decision"]
        if (not d.get("raw_D0_watch_retained")
            or d.get("schema")!=CASE_SCHEMA
            or d.get("first_D0_UTC")!=r["original_D0_UTC"]
            or d["symbol"]!=r["symbol"] or d["venue"]!="USDM"
            or d["BUY"]!="NOT_AUTHORIZED"
            or d["fast_attention"] not in (True,False)):
            raise ValueError("STAGE119_ORIGINAL_D0_AND_SIGNAL_RULES_CHANGED")
        identity_case[kind]+=1
        for event_type,clock in (
            ("ORIGINAL_D0",r["original_D0_UTC"]),
            ("ORIGINAL_D1",r["original_stage83_first_D1_UTC"]),
        ):
            if clock is None: continue
            original=scoped_event(anchor=r["date"],symbol=r["symbol"],
                                  venue="BINANCE_USDM",signal_type=event_type,
                                  observed_utc=clock)
            if original["event_id"] in seen:
                raise ValueError("STAGE119_DUPLICATE_D0_D1_GLOBAL_EVENT_ID")
            seen.add(original["event_id"])
            if event_type=="ORIGINAL_D1":
                if original["observed_ms"]<signal_ms(r["original_D0_UTC"]):
                    raise ValueError("STAGE119_D1_BEFORE_ORIGINAL_D0")
            proof=evaluate(original,identity_classification=kind)
            all_events.append({
                "candidate":original,
                "original_identity":kind,
                "prior_Stage118_fast_attention":(
                    bool(d["fast_attention"]) if event_type=="ORIGINAL_D0" else None),
                "stage90_D2_readiness":proof,
                "original_5m_24h_price_only_NOT_EXECUTABLE":(
                    r["D0_5m_24h_gross_price_proxy_ONLY"]
                    if event_type=="ORIGINAL_D0" else None),
            })
            counts[event_type]+=1
            counts[event_type+"_"+proof["D2_status"]]+=1
            per_day[r["date"]][event_type]+=1
    if (counts["ORIGINAL_D0"]!=519 or counts["ORIGINAL_D1"]!=305
        or len(all_events)!=824 or len(seen)!=824):
        raise ValueError("STAGE119_ORIGINAL_519_D0_305_D1_COUNTS_DRIFT")
    if dict(identity_case)!={
        "CRYPTO_IDENTITY_UNVERIFIED":501,
        "MULTIPLIER_MAPPING_UNVERIFIED":15,
        "CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE":3}:
        raise ValueError("STAGE119_ORIGINAL_519_IDENTITY_CLASS_DRIFT")
    return {
        "schema":SCHEMA,
        "source_Stage118_actual_rows_git_blob":SOURCE_SHA,
        "source_Stage118_actual_summary_git_blob":STAGE118_SUMMARY_SHA,
        "source_Stage90_D2_pure_engine_git_blob":D2_CODE_SHA,
        "original_D0_519":519,"original_D1_305":305,"D2_event_count":824,
        "original_519_case_identity_class":dict(sorted(identity_case.items())),
        "D2_status_by_mode":dict(sorted(counts.items())),
        "source_date_D0_D1_counts":{k:dict(sorted(v.items()))
                                   for k,v in sorted(per_day.items())},
        "actual_signal_time_book_price_level_order_fills":"NOT_ARCHIVED",
        "actual_historical_user_notional":"UNSPECIFIED",
        "explicit_no_default_quote_notional":True,
        "historical_real_executable_profit":"UNKNOWN",
        "real_crypto_G0_certification":"NOT_DONE",
        "original_Stage118_18_28_G2":"REJECTED",
        "forward_OOS":"NOT_DONE",
        "review":"INDEPENDENT_OTHER_AI_NOT_DONE",
        "user_mac_Monster_install":"NO_GO",
        "autotrading":"NO_GO","Gmail":"OFF",
        "Frank":"UNCHANGED","Stage99_existing_authorized_one_shot":"UNCHANGED",
    }, all_events


def selftest():
    t="2026-10-14T06:03:00Z"
    x=scoped_event(anchor="2026-10-14",symbol="TESTUSDT",
                   venue="BINANCE_USDM",signal_type="ORIGINAL_D0",
                   observed_utc=t)
    y=scoped_event(anchor="2026-10-14",symbol="TESTUSDT",
                   venue="BINANCE_USDM",signal_type="ORIGINAL_D1",
                   observed_utc=t)
    assert x["event_id"]!=y["event_id"]
    assert evaluate(x)["D2_status"]=="IDENTITY_UNKNOWN"
    assert evaluate(x,identity_classification="MULTIPLIER_MAPPING_UNVERIFIED")[
        "D2_status"]=="MAPPING_UNKNOWN"
    assert evaluate(x,identity_classification="CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE")[
        "D2_status"]=="OUT_OF_SCOPE"
    a=d2.synthetic_fixture()
    # A non-public synthetic quote amount ONLY for a deterministic D2 unit
    # fixture; without independent source provenance it is not a real fill.
    fixture=a[1]
    reject=evaluate(x,supplied_evidence=fixture,user_notional="100")
    assert reject["D2_status"]=="SOURCE_PROVENANCE_UNVERIFIED"
    assert reject["net_executable_profit"]=="UNKNOWN"
    assert reject["market_entry_or_exit_actual_fill"]=="NOT_OBSERVED"
    assert reject["Monster_deploy"]=="NO_GO"
    assert git_blob(b"test")=="30d74d258442c7c65512eafab474568dd706c430"
    print("STAGE119_D0_D1_UNIQUE_ID_NO_DEFAULT_NOTIONAL_RAW_PROVENANCE_AND_D2_DENY_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    p.add_argument("--cases",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest()
        return
    if a.out is None or a.cases is None:
        p.error("--out --cases required for offline original519 D2 evidence audit")
    summary,records=audit_historic()
    for target in (a.out,a.cases):
        target.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    a.cases.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in records))
    print("STAGE119_FULL_ORIGINAL824_EXECUTION_READY_AUDIT "+
          json.dumps({k:v for k,v in summary.items() if k not in (
              "source_date_D0_D1_counts",)},sort_keys=True))


if __name__=="__main__":
    main()
