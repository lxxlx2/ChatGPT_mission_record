#!/usr/bin/env python3
"""Original February 445 source-complete list, 28 SHA-bound offline minute shards.

Historical research only: source collection is NOT model or profitable-strategy
validation. No schedule, email, exchange orders, real SQLite, or Frank access.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from datetime import date
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

import monster_v4_shared_spot_d0_d1_original_core as shared
import monster_v4_stage26_continuous168h as stage26

SCHEMA = "MONSTER_FEB2026_SOURCE_COMPLETE_445_28_OFFICIAL_MINUTE_SHARDS_V1"
DAY = date(2026, 2, 4)
SHARD_SIZE = 16
SHARD_COUNT = 28
POPULATION = 445
SOURCE_DAYS = 10
MINUTE_ROWS = 12960
MAX_MEMBER_BYTES = 2_500_000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def roster():
    full, dates = shared.original_source_freeze()
    source_complete = tuple(sorted(dates[DAY.isoformat()]["complete_symbols"]))
    if (len(full) != 758 or len(source_complete) != POPULATION
            or len(full)-len(source_complete) != 313
            or not set(source_complete).issubset(full)):
        raise ValueError("SHARED_445_SOURCE_ROSTER_IDENTITY_OR_COUNT_DRIFT")
    return source_complete


def members(shard):
    if type(shard) is not int or shard < 0 or shard >= SHARD_COUNT:
        raise ValueError("SHARED_445_INVALID_FROZEN_SHARD_INDEX")
    source_complete = roster()
    expected_count = 13 if shard == 27 else 16
    selected = source_complete[shard*SHARD_SIZE:(shard+1)*SHARD_SIZE]
    if len(selected) != expected_count:
        raise ValueError("SHARED_445_SHARD_INCOMPLETE")
    return selected


def encode_bars(bars):
    # Stable JSON representation of exact Decimal strings; never float-cast.
    return json.dumps(
        [[r[0], *(str(v) for v in r[1:6]), r[6]] for r in bars],
        separators=(",", ":"), ensure_ascii=True).encode()


def decode_bars(raw):
    if len(raw) > MAX_MEMBER_BYTES:
        raise ValueError("SHARED_445_SHARD_MEMBER_OVERSIZE")
    obj = json.loads(raw)
    if not isinstance(obj, list) or len(obj) != MINUTE_ROWS:
        raise ValueError("SHARED_445_SHARD_MEMBER_SOURCE_ROWS_INVALID")
    bars = []
    for x in obj:
        if not isinstance(x, list) or len(x) != 7:
            raise ValueError("SHARED_445_SHARD_MEMBER_BAD_ROW_SHAPE")
        if type(x[0]) is not int or type(x[6]) is not int:
            raise ValueError("SHARED_445_SHARD_MEMBER_BAD_TYPES")
        try:
            values = [Decimal(v) for v in x[1:6]]
        except (TypeError, ValueError, ArithmeticError) as exc:
            raise ValueError("SHARED_445_SHARD_MEMBER_BAD_DECIMAL") from exc
        if any(not v.is_finite() for v in values):
            raise ValueError("SHARED_445_SHARD_MEMBER_NONFINITE")
        bars.append((x[0], *values, x[6]))
    return bars


def verify_one(symbol, bars, receipts):
    # Only derive features in private isolated SQLite, not the production DB.
    if len(receipts) != SOURCE_DAYS:
        raise ValueError("SHARED_445_SHARD_TEN_PUBLISHER_SHAS_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="monster_shared445_verify_") as td:
        with shared.setup_cache(Path(td)/"source_validation.sqlite") as db:
            verified=[dict(r, verified_published_sha256=True,
                           verified_by="ORIGINAL_STAGE26_PUBLISHER_DOWNLOADER")
                      for r in receipts]
            result=shared.prepare_symbol(db,symbol,DAY,bars,verified)
    if result["poll_rows"] != 3360 or result["closed_5m"] != 2592:
        raise ValueError("SHARED_445_SHARD_DERIVED_MINUTES_DIFFER")
    return result


def collect(shard, output, provenance, *, fetch=None, max_workers=2):
    selected=members(shard)
    if type(max_workers) is not int or not 1 <= max_workers <= 2:
        raise ValueError("SHARED_445_OFFICIAL_CONCURRENT_DOWNLOADS_LIMIT_TWO")
    for dest in (Path(output),Path(provenance)):
        if dest.exists() or dest.is_symlink():
            raise ValueError("SHARED_445_SOURCE_OUTPUT_ALREADY_EXISTS")
    downloader=stage26.read_complete_216h if fetch is None else fetch
    trusted_reader=fetch is None

    def one(sym):
        bars, receipts=downloader(sym,DAY)
        validated=verify_one(sym,bars,receipts)
        raw=encode_bars(bars)
        if len(raw) > MAX_MEMBER_BYTES:
            raise ValueError("SHARED_445_SHARD_MEMBER_OVERSIZE")
        return sym,raw,receipts,validated

    outcomes={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures={pool.submit(one,s):s for s in selected}
        for future in concurrent.futures.as_completed(futures):
            symbol=futures[future]
            outcomes[symbol]=future.result()
    payload=[]
    manifest={
      "schema":SCHEMA,"day":DAY.isoformat(),"shard":shard,
      "shard_size":SHARD_SIZE,"shard_count":SHARD_COUNT,
      "original_denominator":758,"source_complete_denominator":445,
      "historical_original_censored":313,
      "source_roster_sha256":shared.SECONDARY_ROSTER_SHA256,
      "production_model_blob":shared.ORIGINAL_SHADOW_BLOB,
      "source_reader":("ORIGINAL_STAGE26_OFFICIAL_SPOT1M_ZIP_AND_SAME_HOST_CHECKSUM"
                       if trusted_reader else "INJECTED_SYNTHETIC_UNVERIFIED"),
      "source_origin_verified_at_collection":trusted_reader,
      "original_SHA_precommitted_before_first_stage26_download":False,
      "trigger_commit_sha":os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED"),
      "selection":"FROZEN_445_LEXICOGRAPHIC_SHARD_NOT_WATCH_RANKED",
      "symbols":list(selected),"members":[]
    }
    for symbol in selected:
        _, raw, receipts, validated=outcomes[symbol]
        name=symbol+".json"
        payload.append((name,raw))
        manifest["members"].append({
         "symbol":symbol,"name":name,"source_json_sha256":sha(raw),
         "source_json_bytes":len(raw),"rows":MINUTE_ROWS,
         "publisher_days":[{"day":r["date"],"sha256":r["sha256"]}
                          for r in receipts],
         "poll_rows":validated["poll_rows"],
         "closed5m":validated["closed_5m"]
        })
    metadata=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    # No write when a publisher source or member validation fails.
    with zipfile.ZipFile(output,mode="x",compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as z:
        z.writestr("manifest.json",metadata)
        for name,raw in payload:
            z.writestr(name,raw)
    archive=Path(output).read_bytes()
    proof={
      "schema":"MONSTER_FEB2026_445_OFFICIAL_SHARD_ARTIFACT_PROOF_V1",
      "shard":shard,
      "source_schema":SCHEMA,
      "sha256_zip":sha(archive),
      "sha256_inner_manifest":sha(metadata),
      "archive_bytes":len(archive),
      "source_symbol_count":len(selected),
      "original_denominator":758,
      "source_complete_denominator":445,
      "historical_original_censored":313,
      "source_origin_verified_at_collection":trusted_reader,
      "trigger_commit_sha":manifest["trigger_commit_sha"],
      "symbols":list(selected),
      "source_sha256_by_symbol":[
       {"symbol":x["symbol"],"raw_sha256":x["source_json_sha256"],
        "publisher_days":x["publisher_days"]}
       for x in manifest["members"]],
      "research_only_no_445_replay":True,
      "G4":"UNKNOWN","G6":"NO_GO"
    }
    with Path(provenance).open("x",encoding="utf-8") as f:
        json.dump(proof,f,sort_keys=True,indent=2)
        f.write("\n")
    return proof


def read_archive(source_path, proof=None, expected_shard=None):
    # Explicit source path is research artifact, NEVER a production SQLite.
    path=Path(source_path)
    data=path.read_bytes()
    if proof is not None and sha(data) != proof["sha256_zip"]:
        raise ValueError("SHARED_445_SHARD_ZIP_SHA_MISMATCH")
    with zipfile.ZipFile(path) as z:
        members=z.namelist()
        if not members or members[0]!="manifest.json":
            raise ValueError("SHARED_445_SHARD_MANIFEST_MISSING")
        raw_manifest=z.read("manifest.json")
        if (proof is not None and
                sha(raw_manifest)!=proof["sha256_inner_manifest"]):
            raise ValueError("SHARED_445_SHARD_MANIFEST_SHA_MISMATCH")
        meta=json.loads(raw_manifest)
        idx=meta.get("shard")
        if (meta.get("schema")!=SCHEMA or type(idx) is not int
                or (expected_shard is not None and idx!=expected_shard)):
            raise ValueError("SHARED_445_SHARD_SCHEMA_OR_ID_DRIFT")
        selected=members_for_shard=globals()["members"](idx)
        if (meta.get("symbols")!=list(selected)
                or meta.get("original_denominator")!=758
                or meta.get("source_complete_denominator")!=445
                or meta.get("historical_original_censored")!=313
                or meta.get("source_roster_sha256")!=shared.SECONDARY_ROSTER_SHA256
                or meta.get("production_model_blob")!=shared.ORIGINAL_SHADOW_BLOB):
            raise ValueError("SHARED_445_SHARD_ORIGINAL_IDENTITY_DRIFT")
        archive_members=meta.get("members")
        if (not isinstance(archive_members,list)
                or [x.get("symbol") for x in archive_members]!=list(selected)
                or members!=["manifest.json"]+[s+".json" for s in selected]):
            raise ValueError("SHARED_445_SHARD_MEMBERS_OR_DUPLICATES")
        if proof is not None:
            if (proof.get("shard")!=idx or proof.get("symbols")!=list(selected)
                    or proof.get("source_origin_verified_at_collection") !=
                    meta.get("source_origin_verified_at_collection")):
                raise ValueError("SHARED_445_SHARD_PROVENANCE_MISMATCH")
        for m in archive_members:
            if (m.get("name")!=m["symbol"]+".json" or
                    m.get("rows")!=MINUTE_ROWS or
                    len(m.get("publisher_days",[]))!=SOURCE_DAYS):
                raise ValueError("SHARED_445_SHARD_MEMBER_METADATA_INVALID")
            info=z.getinfo(m["name"])
            if info.file_size>MAX_MEMBER_BYTES:
                raise ValueError("SHARED_445_SHARD_MEMBER_OVERSIZE")
            row_data=z.read(m["name"])
            if (sha(row_data)!=m.get("source_json_sha256")
                    or len(row_data)!=m.get("source_json_bytes")):
                raise ValueError("SHARED_445_SHARD_SOURCE_SHA_MISMATCH")
            bars=decode_bars(row_data)
            yield m["symbol"],bars,m["publisher_days"],meta


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--shard",type=int,required=True)
    ap.add_argument("--out-archive",required=True,type=Path)
    ap.add_argument("--out-proof",required=True,type=Path)
    ap.add_argument("--workers",type=int,default=2)
    args=ap.parse_args()
    proof=collect(args.shard,args.out_archive,args.out_proof,max_workers=args.workers)
    print("MONSTER_445_SHA_LOCKED_OFFICIAL_MINUTE_SHARD "+
          json.dumps({key:proof[key] for key in (
           "shard","sha256_zip","source_symbol_count","original_denominator",
           "source_origin_verified_at_collection","trigger_commit_sha")},
           sort_keys=True))


if __name__=="__main__":
    main()
