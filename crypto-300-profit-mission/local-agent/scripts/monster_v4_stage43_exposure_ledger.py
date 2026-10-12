#!/usr/bin/env python3
"""Stage43 pre-validation exposure ledger, pinned to frozen Stage42 git commit.

Read text (not prices) from historical Monster docs, protocols, workflows and
research Python scripts. Freeze historical-start-date candidate windows before
fetching any new official Binance archives. A date previously present in a file
is considered *potentially exposed* even if not proven a research-window anchor:
conservative false exclusions are acceptable; false 'OOS' claims are not.
A candidate must NOT overlap any known 7-day exposed window.
"""
from __future__ import annotations
import argparse,collections,datetime as dt,hashlib,json,re,subprocess
from pathlib import Path

PIN="2c6d9c1b3f4a9f99a236b015603f517c22afff69"
SCHEMA="MONSTER_STAGE43_STAGE42_PINNED_GIT_EXPOSURE_LEDGER_V1"
DATE=re.compile(r"(?<!\d)(20(?:2[1-6]))-(0[1-9]|1[0-2])-([0-2]\d|3[01])(?!\d)")
START=dt.date(2025,1,1)
LAST=dt.date(2026,9,30)
SEED=b"MONSTER_STAGE43_HISTORICAL_SEVEN_DAY_NO_OVERLAP_V1"

def git(*args):
    p=subprocess.run(["git",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return p.stdout

def included(path):
    if path.startswith("crypto-300-profit-mission/monster/") and path.endswith(".md"):
        return True
    if path.startswith("crypto-300-profit-mission/monster/evidence/") and path.endswith(".json"):
        name=path.rsplit("/",1)[-1].lower()
        return any(k in name for k in ("prereg","protocol","frozen","proof","stage36_official_usdm_archive"))
    if path.startswith(".github/workflows/monster") and (path.endswith(".yml") or path.endswith(".yaml")):
        return True
    if path.startswith("crypto-300-profit-mission/local-agent/scripts/monster_") and path.endswith(".py"):
        return True
    return False

def exposure(source):
    matches=set()
    for yy,mm,dd in DATE.findall(source):
        try:d=dt.date(int(yy),int(mm),int(dd))
        except ValueError:continue
        if START<=d<=LAST:matches.add(d)
    return matches

def inspect_source():
    head=git("rev-parse",PIN).decode().strip()
    if head!=PIN:raise RuntimeError("STAGE43_HISTORICAL_PIN_NOT_PRESENT")
    tracked=git("ls-tree","-r","--name-only",PIN).decode("utf-8","replace").splitlines()
    paths=sorted(x for x in tracked if included(x))
    if len(paths)<45:raise RuntimeError("STAGE43_UNEXPECTEDLY_FEW_ORIGINAL_HISTORY_DOCS")
    exposed=collections.defaultdict(set)
    receipts=[]
    for path in paths:
        raw=git("show",PIN+":"+path)
        # These files are historical docs/code/protocols, not original market ZIPs.
        if len(raw)>2_000_000:raise RuntimeError("STAGE43_SOURCE_TOO_LARGE "+path)
        days=exposure(raw.decode("utf-8","replace"))
        receipts.append({"path":path,"git_blob_SHA256":hashlib.sha256(raw).hexdigest(),
                         "historical_ISO_date_count":len(days)})
        for day in days:exposed[day.isoformat()].add(path)
    if not exposed:raise RuntimeError("STAGE43_MISSING_SOURCE_DATE_EXPOSURE")
    return exposed,receipts

def selection(exposed):
    known=sorted(dt.date.fromisoformat(x) for x in exposed)
    # Distinct pinned-source ISO date may be an event date, an experiment start,
    # or ordinary descriptive date. Treat all as potential 7d exposures.
    eligible=[]
    blocked=[]
    candidate=START
    while candidate<=LAST-dt.timedelta(days=7):
        conflicts=[a for a in known if abs((candidate-a).days)<7]
        if conflicts:
            blocked.append(candidate)
        else:
            eligible.append(candidate)
        candidate+=dt.timedelta(days=1)
    byhash=sorted(eligible,key=lambda d:hashlib.sha256(SEED+d.isoformat().encode()).hexdigest())
    chosen=[]
    for day in byhash:
        if all(abs((day-prev).days)>=21 for prev in chosen):
            chosen.append(day)
        if len(chosen)==6:break
    return {
      "covered_range_utc":[START.isoformat(),LAST.isoformat()],
      "historical_seven_day_window_possible_start_days":len(eligible)+len(blocked),
      "no_overlap_start_dates_all_recorded_source_dates":len(eligible),
      "blocked_by_any_research_or_example_date":len(blocked),
      "holdout_selected_blind_by_hashed_date_only":sorted(d.isoformat() for d in chosen),
      "holdout_rule":"SEED_SHA256(date), no 7d intersection with any 2025-2026 historical ISO date in pinned Monster docs/code/protocols; 21d minimum spacing between chosen starts",
      "selection_status":"FROZEN_CANDIDATE_UNDER_DATE_AUDIT" if len(chosen)>=4 else "INSUFFICIENT_STRICT_DISJOINT_DATES_NO_OOS_CLAIM",
      "no_future_prices_or_labels_read_to_choose_dates":True
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    exposures,receipts=inspect_source()
    if len(exposures)<25:raise RuntimeError("STAGE43_TOO_FEW_EXPOSURES")
    output={
       "schema":SCHEMA,"frozen_git_sha":PIN,
       "audit_includes":"monster reports, preregistered JSON, GitHub workflows and source scripts only",
       "not_includes":"binary official price files and event-labelled JSONL; NOT complete historical point-in-time exchange listings",
       "date_mentions_conservatively_exposed_NOT_proven_prior_7d_anchor":True,
       "audited_source_documents":len(receipts),
       "source_SHA256_receipts":receipts,
       "historical_exposed_or_potentially_exposed_ISO_dates":{
         day:{"files":sorted(paths)[:12],"file_count":len(paths)}
         for day,paths in sorted(exposures.items())
       },
       "selection":selection(exposures),
       "market_data_queried_in_this_run":False,
       "strategy_p1_v01":"REJECTED_15_OF_48_FROM_STAGE42",
       "other_AI_review":"NOT_DONE","deployment":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED"
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE43_PINNED_HISTORY_AUDIT_PASS "+json.dumps({
       "source_docs":len(receipts),"exposure_dates":len(exposures),
       "strict_start_candidates":output["selection"]["no_overlap_start_dates_all_recorded_source_dates"],
       "blind_dates":output["selection"]["holdout_selected_blind_by_hashed_date_only"],
       "status":output["selection"]["selection_status"]},sort_keys=True))

if __name__=="__main__":main()
