#!/usr/bin/env python3
"""Stage76: cross-check pre-D0 Binance Alpha official documentary evidence.

The official page contents were separately researched; this offline check
validates immutable source identities, timestamps and categories, NOT live
Alpha executability, historical minute trades or chain-verified liquidity.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlparse

BASE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
MANIFEST=BASE/"monster_stage76_four_futures_GT2x_2025_pre_D0_official_alpha_announcement_venue_mapping.json"
OLD=BASE/"monster_stage74_original196_exact_asof_spot_prior_trades_source_SHA.jsonl"
FOUR_QUOTES=BASE/"monster_stage75_original95_all380_spot_four_quote_SHA_asof_rows.jsonl"
GT2X=("HUSDT","PIPPINUSDT","TANSSIUSDT","TRADOORUSDT")


def timestamp(t):
    v=datetime.datetime.fromisoformat(t.replace("Z","+00:00"))
    if v.tzinfo is None or v.utcoffset()!=datetime.timedelta(0):
        raise ValueError("STAGE76_TIME_NOT_UTC")
    return v


def audit():
    v=json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows=v["rows"]
    old=[json.loads(x) for x in OLD.read_text(encoding="utf-8").splitlines() if x]
    noUSDT=[json.loads(x) for x in FOUR_QUOTES.read_text(encoding="utf-8").splitlines() if x]
    if len(old)!=196 or len(noUSDT)!=95 or len(rows)!=4:
        raise ValueError("STAGE76_MISSING_FULL_COHORT_OR_ALPHA_RECORDS")
    reference={(x["date"],x["symbol"]):x for x in old}
    alt={(x["original_window_date"],x["original_futures_symbol"]):x for x in noUSDT}
    if {x["symbol"] for x in rows}!=set(GT2X):
        raise ValueError("STAGE76_NOT_ALL_FOUR_FIXED_DOCUMENTED_CASES")
    if len({(x["date"],x["symbol"]) for x in rows})!=4:
        raise ValueError("STAGE76_DUPLICATED_ID")
    findings=[]
    for x in rows:
        key=(x["date"],x["symbol"])
        former=reference[key];quotes=alt[key]
        signal=timestamp(x["first_D0_UTC"])
        if (former["original_usdm_first_D0_UTC"]!=x["first_D0_UTC"] or
            quotes["original_futures_first_D0_UTC"]!=x["first_D0_UTC"]):
            raise ValueError("STAGE76_CHANGED_ORIGINAL_WATCH_SIGNAL")
        if former["spot_historical_evidence_status"]=="SPOT_PRIOR_MINUTE_TRADES_VERIFIED":
            raise ValueError("STAGE76_ALREADY_DIRECT_SPOT_TRADABLE_SIGNAL")
        if quotes["any_alternative_quote_spot_prior_closed_minute_trades_verified"]:
            raise ValueError("STAGE76_ALT_QUOTE_TRADE_AVAILABLE_DRIFT")
        if not timestamp(x["official_document_published_UTC"])<signal:
            raise ValueError("STAGE76_ALPHA_ANNOUNCEMENT_NOT_PRIOR_TO_WATCH")
        clock=x["official_alpha_event_UTC"]
        if clock.startswith("UNKNOWN_ALREADY_LISTED"):
            if not x["proof_type"].startswith("OFFICIAL_CONFIRMED_ALREADY_ALPHA_LISTED"):
                raise ValueError("STAGE76_UNKNOWN_LISTING_DATE_CLAIMED_KNOWN")
        elif not timestamp(clock)<signal:
            raise ValueError("STAGE76_ALPHA_LAUNCH_NOT_BEFORE_FIRST_D0")
        u=urlparse(x["official_link"])
        if u.scheme!="https" or u.netloc!="www.binance.com" or not u.path.startswith("/en/support/announcement/detail/"):
            raise ValueError("STAGE76_NOT_OFFICIAL_ENGLISH_BINANCE_SOURCE")
        contract=x["official_chain_CA"]
        if x["symbol"]=="PIPPINUSDT":
            if x["official_chain"]!="Solana" or contract!="Dfh5DzRgSvvCFDoYc2ciTkMrbDfRKybA4SoFbPmApump":
                raise ValueError("STAGE76_SOLANA_MINT_NOT_VERIFIED_OR_DIFFERENT")
        if x["symbol"]=="TRADOORUSDT":
            if x["official_chain"]!="BNB Smart Chain" or contract.lower()!="0x9123400446a56176eb1b6be9ee5cf703e409f492":
                raise ValueError("STAGE76_BSC_CONTRACT_NOT_FROM_OFFICIAL_FUTURES_ANNOUNCEMENT")
            if not re.fullmatch(r"0x[a-fA-F0-9]{40}",contract):
                raise ValueError("STAGE76_INVALID_EVM_CONTRACT")
        if x["symbol"] in ("HUSDT","TANSSIUSDT") and contract!="UNKNOWN_NOT_STATED_IN_THIS_ANNOUNCEMENT":
            raise ValueError("STAGE76_UNPROVEN_CA_INVENTED")
        findings.append({
            "original_futures":x["symbol"],"original_D0_UTC":x["first_D0_UTC"],
            "official_alpha_document_date":x["official_document_published_UTC"],
            "alpha_statement_before_our_D0":True,
            "official_source":x["official_link"],
            "t_exact_historic_alpha_trades_or_liquidity":"UNVERIFIED",
        })
    print("STAGE76_OFFICIAL_HISTORIC_ALPHA_DOCUMENTARY_FOUR_OF_FOUR_PRIOR_TO_D0_SOURCE_IDENTITIES_PASS "+
          json.dumps(findings,sort_keys=True))


if __name__=="__main__":
    audit()
