#!/usr/bin/env python3
"""Compact verifiable Stage114 all519 CI output; never recompute/alter model."""
from __future__ import annotations

import argparse
from hashlib import sha1
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[2] / "monster" / "evidence"
SOURCE = EVIDENCE / "monster_stage114_real519_d0_d1_priority_paired_entry_actual.json"
PIN_SOURCE = "de64a09ff4f8b35009fd1ff71a284542fd5de5ac"
SCHEMA = "MONSTER_STAGE114_SOURCE_LOCKED_FULL519_COMPACT_REPORT_V1"


def sha_blob(raw: bytes) -> str:
    return sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    raw=SOURCE.read_bytes()
    if sha_blob(raw)!=PIN_SOURCE:
        raise ValueError("STAGE114_FULL519_ACTUAL_RESULT_GIT_BLOB_CHANGED")
    item=json.loads(raw)
    if (item["original_D0_cases"]!=519
        or item["original_D1_count"]!=305
        or item["cases_with_first_priority"]!=277
        or item["major_D0_early5_2x"]!=28
        or item["major_first_priority_early5_2x"]!=19
        or len(item["all_519_original_cases"])!=519):
        raise ValueError("STAGE114_FULL519_SOURCE_ORIGINAL_POPULATION_CHANGED")
    result={k:v for k,v in item.items() if k!="all_519_original_cases"}
    result["schema"]=SCHEMA
    result["source_full_results_git_blob"]=PIN_SOURCE
    result["source_full_results_bytes"]=len(raw)
    result["case_level_evidence_kept_in_pinned_large_source"]=True
    result["research_not_independent_OOS"]=True
    result["real_executable_net"]="UNKNOWN"
    result["monster_deployment"]="NO_GO"
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("STAGE114_PINNED_ALL519_COMPACT_SOURCE_RECHECK "+
          json.dumps({k:v for k,v in result.items()
                      if k in ("source_full_results_git_blob","original_D0_cases",
                               "original_D1_count","cases_with_first_priority",
                               "major_first_priority_early5_2x","real_executable_net")},
                     sort_keys=True))


if __name__=="__main__":
    main()
