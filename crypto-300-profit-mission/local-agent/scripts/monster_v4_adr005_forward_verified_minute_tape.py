#!/usr/bin/env python3
"""November ADR005 Spot 1m -> original D0 and preregistered D1 input bridge.

OFFLINE RETROSPECTIVE INPUTS ONLY. The public CLI revalidates raw T0 ZIP and
issuer daily ZIP/CHECKSUM via the previously approved score-admission run().
A fully closed historical issuer day was NOT necessarily available at the
original minute. This never claims historical live ticker/PIT, runs a
watch engine, scores GT2x, sends an alert or trades.

This module deliberately DOES NOT import the old hard-coded Oct Spot511 tape:
the three November windows get their own independent original T0 cohort.
"""
import argparse
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path
import zipfile

import monster_v4_adr005_forward_spot_score_admission as admission
import monster_v4_adr005_forward_spot_t0_gate as t0
import monster_v4_adr005_forward_spot_daily_gate as daily
import monster_v4_stage166_spot511_official_1m_intake as publisher

SCHEMA="MONSTER_ADR005_NOV_SPOT_SOURCE_VERIFIED_D0_RBTC_D1_INPUT_TAPE_V1"
TICK_MS=180_000
MIN_MS=60_000
FIVE_MS=300_000
WINDOW_MS=t0.WINDOW_MS
BASELINE_MIN=1440
OBS_MIN=7*1440
TOTAL_MIN=BASELINE_MIN+OBS_MIN
BAR_FIELDS=(1,2,3,4,5,7)
BTC="BTCUSDT"


def _verified_minute_grid(root,symbol,start_utc,*,asof_utc):
    """Re-open and validate all eight relevant original issuer source days."""
    start_ms=t0.frozen_window(start_utc)//1000
    first=t0.EPOCH+timedelta(milliseconds=start_ms)-timedelta(days=1)
    asof_us=t0.parse_us(asof_utc)
    result=[]
    checks={}
    for index in range(8):
        day=(first+timedelta(days=index)).date()
        day_end_us=t0.parse_us((first+timedelta(days=index+1)).isoformat().replace("+00:00","Z"))
        if day_end_us>asof_us:
            raise ValueError("ADR005_MINUTE_TAPE_UNCLOSED_ISSUER_DAY")
        zip_path, checksum_path=publisher.daily_paths(root,symbol,day)
        if (not zip_path.is_file() or not checksum_path.is_file()
            or zip_path.is_symlink() or checksum_path.is_symlink()):
            raise ValueError("ADR005_MINUTE_TAPE_MISSING_OR_SYMLINK_ISSUER_SOURCE")
        proof=publisher.validate_daily_zip(zip_path,checksum_path,symbol,day)
        checks[day.isoformat()]=proof["zip_sha256"]
        with zipfile.ZipFile(zip_path) as archive:
            member=f"{symbol}-1m-{day.isoformat()}.csv"
            with archive.open(member) as handle:
                rdr=csv.reader(io.TextIOWrapper(handle,encoding="utf-8",newline=""))
                try:
                    for line in rdr:
                        result.append(tuple(Decimal(line[col]) for col in BAR_FIELDS))
                except (InvalidOperation,ValueError,IndexError) as exc:
                    raise ValueError("ADR005_MINUTE_TAPE_PUBLISHER_ROW_INVALID") from exc
    if len(result)!=TOTAL_MIN or any(
        not all(v.is_finite() for v in row) or min(row[0],row[1],row[2],row[3])<=0
        for row in result
    ):
        raise ValueError("ADR005_MINUTE_TAPE_EIGHT_DAY_GRID_DRIFT")
    return result,checks


class VerifiedForwardSpotMinuteTape:
    """Per-symbol 8-day verified minute source for exact November 3m/5m inputs.

    Admission to this *pure* object does not itself authenticate prior source
    collection. The CLI builds it only after re-reading original HTTP/ZIPs.
    All data are retrospectively validated, not proof of a real-time tick feed.
    """
    def __init__(self,root,symbol,start_utc,asof_utc,admission_row):
        start=t0.frozen_window(start_utc)//1000
        if (not isinstance(symbol,str) or not t0.SYMBOL.fullmatch(symbol)
            or not symbol.endswith("USDT")
            or not isinstance(admission_row,dict)
            or admission_row.get("symbol")!=symbol
            or not admission_row.get("baseline_24h_source_verified")
            or not admission_row.get("candidate_own_observation_7d_source_verified")):
            raise ValueError("ADR005_MINUTE_TAPE_CANDIDATE_D0_SOURCE_ADMISSION_REQUIRED")
        self.start_ms=start
        self.end_ms=start+WINDOW_MS
        self.symbol=symbol
        self.asof_utc=asof_utc
        self.rows,self.publisher_sha=_verified_minute_grid(
            Path(root),symbol,start_utc,asof_utc=asof_utc)
        self.quote_prefix=[Decimal(0)]
        for row in self.rows:
            self.quote_prefix.append(self.quote_prefix[-1]+row[5])
        self.previous_day_and_observation_issuer_source_verified=True
        self.original_tick_quote_or_listing_PIT_proven=False

    def _index(self,tick_ms):
        if (type(tick_ms) is not int
            or not self.start_ms<=tick_ms<self.end_ms
            or tick_ms%TICK_MS):
            raise ValueError("ADR005_TAPE_TICK_OUTSIDE_FROZEN_UTC3M_WINDOW")
        right=BASELINE_MIN+(tick_ms-self.start_ms)//MIN_MS
        if right<BASELINE_MIN or right>TOTAL_MIN:
            raise RuntimeError("ADR005_TAPE_GRID_INDEX_DRIFT")
        return right

    def original_d0_context(self,tick_ms):
        """Exactly [T-24h,T) quote turnover and T-1m close, no future minute."""
        right=self._index(tick_ms)
        last=self.rows[right-1]
        return {
            "symbol":self.symbol,
            "lastPrice":str(last[3]),
            "quoteVolume":str(self.quote_prefix[right]-self.quote_prefix[right-BASELINE_MIN]),
        }

    def six_closed_5m(self,tick_ms):
        """Six contiguous exact UTC 5m closes expected by unchanged D1 core."""
        right=self._index(tick_ms)
        last_end=(tick_ms//FIVE_MS)*FIVE_MS
        end=BASELINE_MIN+(last_end-self.start_ms)//MIN_MS
        if (end>right or end<30 or end>TOTAL_MIN):
            raise ValueError("ADR005_TAPE_D1_SIX_CLOSED_5M_INVALID")
        bars=[]
        base_ms=self.start_ms-BASELINE_MIN*MIN_MS
        for index in range(end-30,end,5):
            segment=self.rows[index:index+5]
            if len(segment)!=5:
                raise ValueError("ADR005_TAPE_D1_MISSING_5M_SEGMENT")
            op=segment[0][0]
            hi=max(x[1] for x in segment)
            lo=min(x[2] for x in segment)
            close=segment[-1][3]
            vol=sum((x[4] for x in segment),Decimal(0))
            quote=sum((x[5] for x in segment),Decimal(0))
            open_ms=base_ms+index*MIN_MS
            close_ms=open_ms+FIVE_MS-1
            if close_ms>=tick_ms or open_ms%FIVE_MS:
                raise ValueError("ADR005_TAPE_D1_FUTURE_OR_MISALIGNED_BAR")
            bars.append([open_ms,str(op),str(hi),str(lo),str(close),
                         str(vol),close_ms,str(quote)])
        if len(bars)!=6:
            raise ValueError("ADR005_TAPE_D1_EXACT_SIX_BARS_REQUIRED")
        return bars

    def original_d1_fetch(self,venue,symbol,tick_ms):
        if venue!="spot" or symbol!=self.symbol:
            raise ValueError("ADR005_TAPE_ORIGINAL_D1_VENUE_OR_IDENTITY_MISMATCH")
        return self.six_closed_5m(tick_ms)


def from_score_admission(report,root,symbol,*,asof_utc):
    """Only for input generation; direct synthetic reports are NOT evidence."""
    if (not isinstance(report,dict) or report.get("schema")!=admission.SCHEMA
        or report.get("replay_engine_executed") is not False
        or report.get("metrics_from_future_labels_computed") is not False
        or report.get("original_market_census_venue")!="BINANCE_SPOT"):
        raise ValueError("ADR005_TAPE_SCORE_SOURCE_ADMISSION_REQUIRED")
    by_symbol={r["symbol"]:r for r in report["symbols"]}
    if len(by_symbol)!=len(report["symbols"]) or symbol not in by_symbol or symbol==BTC:
        raise ValueError("ADR005_TAPE_NON_BTC_TARGET_IN_ORIGINAL_T0_REQUIRED")
    row=by_symbol[symbol]
    own=VerifiedForwardSpotMinuteTape(
        root,symbol,report["window_start_utc"],asof_utc,row)
    btc=None
    if row["technically_eligible_for_offline_rbtc_d1_source_replay"]:
        if BTC not in by_symbol:
            raise ValueError("ADR005_TAPE_BTC_SOURCE_IN_ORIGINAL_T0_REQUIRED")
        btc=VerifiedForwardSpotMinuteTape(
            root,BTC,report["window_start_utc"],asof_utc,by_symbol[BTC])
    return own,btc


def run(start,asof,source_zip,receipts,publisher_root,symbol,tick_ms):
    """Actual executable CLI: re-check T0 and issuer SHA before any tape read."""
    report=admission.run(
        start,asof,source_zip,receipts,publisher_root)
    own,btc=from_score_admission(report,publisher_root,symbol,asof_utc=asof)
    original_context=own.original_d0_context(tick_ms)
    coin_closed5=own.six_closed_5m(tick_ms)
    btc_closed5=btc.six_closed_5m(tick_ms) if btc is not None else None
    return {
        "schema":SCHEMA,
        "window_start_utc":start,"symbol":symbol,
        "original_market_symbols_total":report["original_t0_symbols_total"],
        "tick_ms_retrospective":tick_ms,
        "original_d0_input_context":original_context,
        "original_D1_six_closed5_inputs":coin_closed5,
        "RBTC_D1_six_closed5_btc_inputs":btc_closed5,
        "original_d0_24h_quote_is_reconstructed_proxy_not_live_ticker":True,
        "research_btc_source_ready":btc is not None,
        "publisher_raw_zip_sha256_coin":own.publisher_sha,
        "publisher_raw_zip_sha256_btc":btc.publisher_sha if btc else None,
        "point_in_time_exchange_quote_availability":"UNPROVEN",
        "original_d0_core_executed":False,
        "original_d1_core_executed":False,
        "research_d1_core_executed":False,
        "actual_original_watch_event_id":None,
        "research_setup_event_id":None,
        "real_gt2x_label_evaluated":False,
        "G0":"PARTIAL","G1":"NOT_SCORABLE","G2":"UNKNOWN",
        "G3":"NOT_SCORABLE","G4":"UNKNOWN",
        "G5":"INDEPENDENT_REVIEW_PENDING","G6":"NO_GO",
        "NO_DEPLOY":True,"NO_AUTOMATIONS":True,"NO_GMAIL":True,"NO_TRADES":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--window-start-utc",required=True,choices=t0.WINDOWS)
    p.add_argument("--asof-utc",required=True)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--source-receipts",required=True,type=Path)
    p.add_argument("--publisher-root",required=True,type=Path)
    p.add_argument("--symbol",required=True)
    p.add_argument("--tick-ms",required=True,type=int)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    doc=run(a.window_start_utc,a.asof_utc,a.source_zip,a.source_receipts,
            a.publisher_root,a.symbol,a.tick_ms)
    if a.out is not None:
        if a.out.exists() or a.out.is_symlink():
            raise ValueError("ADR005_TAPE_REFUSE_OVERWRITE")
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with a.out.open("x",encoding="utf-8") as handle:
            json.dump(doc,handle,indent=2,sort_keys=True)
            handle.write("\n")
    print("ADR005_SPOT_EIGHT_DAY_VERIFIED_MINUTE_TAPE",
          json.dumps({k:v for k,v in doc.items() if k not in
                      ("original_D1_six_closed5_inputs","RBTC_D1_six_closed5_btc_inputs")},
                     sort_keys=True))


if __name__=="__main__":
    main()
