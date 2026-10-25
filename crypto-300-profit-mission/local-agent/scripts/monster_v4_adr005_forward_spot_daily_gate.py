#!/usr/bin/env python3
"""ADR-005 frozen future Spot official 1m daily source census, offline only.

Reuse Stage166's publisher ZIP/CHECKSUM + 1440 genuine microsecond minute
validator. Include 24h lead-in, 7d observation, and 7d later 2x label horizon;
a later-download archive cannot prove it was known at the historical event.
No HTTP, trading, re-optimization, background tasks, Gmail or Mac deployment.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path

import monster_v4_adr005_forward_spot_t0_gate as t0
import monster_v4_stage166_spot511_official_1m_intake as publisher

SCHEMA="MONSTER_ADR005_FROZEN_NOVEMBER_SPOT_PUBLISHER_15DAY_CENSUS_V1"
DAY=timedelta(days=1)
SEGMENTS=("BASELINE_24H", "D0_D1_OBSERVATION_7D", "FUTURE_2X_LABEL_7D")


def source_calendar(window_start_utc):
    epoch=t0.frozen_window(window_start_utc)
    start=datetime.fromtimestamp(epoch/1_000_000,timezone.utc)
    if start.time()!=datetime.min.time():
        raise ValueError("ADR005_DAILY_WINDOW_NOT_UTC_MIDNIGHT")
    days=[]
    for offset in range(-1,14):
        day=(start+offset*DAY).date()
        category=("BASELINE_24H" if offset==-1 else
                  "D0_D1_OBSERVATION_7D" if offset<7 else
                  "FUTURE_2X_LABEL_7D")
        days.append({"utc_day":day.isoformat(),"segment":category})
    if len(days)!=15 or [sum(x["segment"]==c for x in days) for c in SEGMENTS]!=[1,7,7]:
        raise RuntimeError("ADR005_DAILY_FROZEN_CALENDAR_DRIFT")
    return days


def _asof(asof_utc):
    stamp=t0.parse_us(asof_utc)
    return datetime.fromtimestamp(stamp/1_000_000,timezone.utc)


def planned_source_readiness(window_start_utc,asof_utc):
    """No T0: report only calendar expectations, never synthesize a market."""
    calendar=source_calendar(window_start_utc)
    current=_asof(asof_utc)
    result=[]
    for entry in calendar:
        day=datetime.fromisoformat(entry["utc_day"]).replace(tzinfo=timezone.utc)
        code=("UTC_DAY_NOT_YET_ENDED"
              if day+DAY>current else "T0_POPULATION_MISSING_CANNOT_SCORE")
        result.append({**entry,"source_status":code})
    return {
        "schema":SCHEMA,"window_start_utc":window_start_utc,
        "asof_utc_supplied":asof_utc,"calendar":result,
        "calendar_days":15,"missing_t0":True,
        "source_census":"NO_T0_POPULATION_NO_VALID_SYMBOL_DENOMINATOR",
        "source_verified_full_15d":False,
        "G0":"POPULATION_UNKNOWN","G1":"NOT_SCORABLE",
        "G2":"UNKNOWN","G3":"NOT_SCORABLE","G4":"UNKNOWN",
        "G6":"NO_GO","NO_AUTOMATIONS":True,"NO_TRADES":True,
    }


def census(admitted_t0,root,asof_utc):
    """Only a preflight-admitted fixed T0 cohort can define the source census.

    A caller-crafted dict cannot establish that T0 is authentic. Production
    CLI performs the raw-ZIP/receipt verification before calling this function.
    """
    if (not isinstance(admitted_t0,dict)
        or admitted_t0.get("schema")!=t0.SCHEMA
        or admitted_t0.get("source_ready_state")!="T0_ARCHIVE_STRUCTURALLY_ADMITTED_ORIGIN_UNVERIFIED"
        or admitted_t0.get("captured_within_15m_and_completed_before_window") is not True
        or admitted_t0.get("source_authenticity")!="SELF_REPORTED_HTTP_RECEIPTS_NOT_EXCHANGE_SIGNED"):
        raise ValueError("ADR005_DAILY_REAL_T0_ADMISSION_REQUIRED")
    start=admitted_t0["window_start_utc"]
    calendar=source_calendar(start)
    asof=_asof(asof_utc)
    ids=admitted_t0.get("t0_spot_usdt_symbol_ids")
    if (not isinstance(ids,list) or not ids or ids!=sorted(set(ids))
        or len(ids)!=admitted_t0.get("t0_spot_usdt_candidates")
        or any(not isinstance(x,str) or not t0.SYMBOL.fullmatch(x) or not x.endswith("USDT")
               for x in ids)):
        raise ValueError("ADR005_DAILY_T0_CANDIDATE_ROSTER_CORRUPT")
    root=Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("ADR005_DAILY_ARCHIVE_ROOT_MISSING_OR_SYMLINK")
    counts=Counter()
    rows=[]
    for sym in ids:
        for entry in calendar:
            day=datetime.fromisoformat(entry["utc_day"]).date()
            midnight=datetime.combine(day,datetime.min.time(),timezone.utc)
            archive,checksum=publisher.daily_paths(root,sym,day)
            if midnight+DAY>asof:
                state="UTC_DAY_NOT_YET_ENDED"
                evidence=None
            elif archive.is_symlink() or checksum.is_symlink():
                state="SOURCE_REJECTED_OR_INCOMPLETE"
                evidence="ARCHIVE_OR_CHECKSUM_SYMLINK_REFUSED"
            elif not archive.is_file() and not checksum.is_file():
                state="SOURCE_NOT_SUPPLIED"
                evidence=None
            elif not archive.is_file() or not checksum.is_file():
                state="SOURCE_REJECTED_OR_INCOMPLETE"
                evidence="ZIP_AND_PUBLISHER_CHECKSUM_REQUIRED"
            else:
                try:
                    evidence=publisher.validate_daily_zip(archive,checksum,sym,day)
                    state="VERIFIED_1440_OFFICIAL_1M"
                except (OSError,ValueError,UnicodeError,RuntimeError) as exc:
                    state="SOURCE_REJECTED_OR_INCOMPLETE"
                    evidence=str(exc)
                # A damaged ZIP may surface as zipfile.BadZipFile, an OSError-like
                # domain exception NOT inherited from OSError; handle below.
                except Exception as exc:
                    import zipfile
                    if not isinstance(exc,zipfile.BadZipFile):
                        raise
                    state="SOURCE_REJECTED_OR_INCOMPLETE"
                    evidence="PUBLISHER_ZIP_BAD_ARCHIVE"
            counts[state]+=1
            rows.append({"symbol":sym,"utc_day":day.isoformat(),
                         "segment":entry["segment"],"source_status":state,
                         "publisher_source_evidence":evidence})
    total=len(ids)*15
    if len(rows)!=total or sum(counts.values())!=total:
        raise RuntimeError("ADR005_DAILY_SOURCE_DENOMINATOR_LOSS")
    full=counts["VERIFIED_1440_OFFICIAL_1M"]==total
    by_segment={}
    for part in SEGMENTS:
        subset=[r for r in rows if r["segment"]==part]
        by_segment[part]=dict(sorted(Counter(r["source_status"] for r in subset).items()))
    return {
        "schema":SCHEMA,"window_start_utc":start,
        "asof_utc_supplied":asof_utc,
        "t0_archive_sha256":admitted_t0["archive_sha256"],
        "t0_source_capture_origin":"NOT_CRYPTOGRAPHICALLY_ATTESTED",
        "dynamic_listing_changes_during_window":"UNKNOWN",
        "baseline_symbol_population":len(ids),
        "days_per_original_symbol":15,
        "expected_official_zip_checksum_pairs":total,
        "actual_status_counts":dict(sorted(counts.items())),
        "segment_source_status_counts":by_segment,
        "verified_complete_all_15days":full,
        "source_publisher_archive_available_at_event_time":"UNKNOWN",
        "historical_price_replay_done":False,
        "G0":"PARTIAL_DYNAMIC_LISTING_UNKNOWN",
        "G1":"NOT_SCORABLE" if not full else "SOURCE_READY_ONLY_NOT_SCORED",
        "G2":"UNKNOWN","G3":"NOT_SCORABLE","G4":"UNKNOWN",
        "G6":"NO_GO","NO_AUTOMATIONS":True,"NO_TRADES":True,
        "source_attempts":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--window-start-utc",required=True,choices=t0.WINDOWS)
    p.add_argument("--asof-utc",required=True)
    p.add_argument("--source-root",type=Path)
    p.add_argument("--t0-zip",type=Path)
    p.add_argument("--t0-receipts",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.t0_zip is None and args.t0_receipts is None:
        if args.source_root is not None:
            p.error("--source-root requires a verified original T0 ZIP and receipt")
        report=planned_source_readiness(args.window_start_utc,args.asof_utc)
    else:
        if None in (args.t0_zip,args.t0_receipts,args.source_root):
            p.error("admitted raw T0 ZIP, receipts and source-root required together")
        admission=t0.preflight(args.window_start_utc,args.asof_utc,
                               args.t0_zip,args.t0_receipts)
        report=census(admission,args.source_root,args.asof_utc)
    if args.out:
        if args.out.exists() or args.out.is_symlink():
            raise ValueError("ADR005_DAILY_CENSUS_REFUSE_OVERWRITE")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open("x",encoding="utf-8") as f:
            json.dump(report,f,sort_keys=True,indent=2,ensure_ascii=False)
            f.write("\n")
    print("ADR005_OFFLINE_PUBLISHER_DAILY_FORWARD_CENSUS",
          json.dumps({k:v for k,v in report.items() if k not in ("calendar","source_attempts")},
                     sort_keys=True))


if __name__=="__main__":
    main()
