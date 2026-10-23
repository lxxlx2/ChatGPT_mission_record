#!/usr/bin/env python3
"""D1 offline audit/recovery. NEVER retries unknown requests or opens network."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import re

SHA256 = re.compile(r"[0-9a-f]{64}\Z")
RAWFILE = re.compile(r"[0-9]{3}\.body\Z")

def check(condition, reason):
    if not condition:
        raise ValueError(reason)

def reconcile_saved_attempts(root):
    """Read an offline journal and raw frames, return immutable audit verdict.

    A crashed run with one or more UNKNOWN reservations is INVALID and never
    resumed. It cannot consume a new or previously issued permission.
    """
    check(isinstance(root, Path) and root.is_absolute() and root.is_dir()
          and not root.is_symlink() and root.stat().st_mode & 0o077 == 0,
          "D1_RECOVERY_ROOT_NOT_PRIVATE")
    log = root/"attempts.jsonl"
    rawdir=root/"raw_responses"
    check(log.is_file() and not log.is_symlink() and
          log.stat().st_mode & 0o077 == 0
          and rawdir.is_dir() and not rawdir.is_symlink() and
          rawdir.stat().st_mode & 0o077 == 0,
          "D1_RECOVERY_FILES_NOT_PRIVATE")
    content=log.read_bytes()
    check(content.endswith(b"\n") or not content,
          "D1_RECOVERY_TRUNCATED_LOG")
    check(len(content) <= 4_000_000,"D1_RECOVERY_LOG_TOO_LARGE")
    reserved={}
    settled=set()
    commits=[]
    invalid=set()
    rpc_parsed=set()
    raw_hashes={}
    last_id=0
    for line_no,line in enumerate(content.splitlines(),1):
        try:
            row=json.loads(line)
        except (ValueError,UnicodeError) as exc:
            raise ValueError("D1_RECOVERY_CORRUPT_JSONL") from exc
        check(type(row) is dict and type(row.get("event")) is str,
              "D1_RECOVERY_EVENT_INVALID")
        kind=row["event"]
        rid=row.get("id")
        if kind=="RESERVE_UNKNOWN":
            check(type(rid) is int and rid == last_id+1,
                  "D1_RECOVERY_NONMONOTONIC_ID")
            last_id=rid
            check(row.get("category") in ("CHAIN","HEAD","INITIAL_HEAD","BLOCK")
                  and row.get("method") in
                  ("eth_chainId","eth_blockNumber","eth_getBlockByNumber"),
                  "D1_RECOVERY_RESERVE_CATEGORY_INVALID")
            if row["category"]=="BLOCK":
                check(type(row.get("height")) is int and row["height"]>0,
                      "D1_RECOVERY_RESERVED_HEIGHT_INVALID")
            reserved[rid]=row
        elif kind=="SETTLE":
            check(type(rid) is int and rid in reserved and rid not in settled,
                  "D1_RECOVERY_DUPLICATE_OR_ORPHAN_SETTLE")
            check(row.get("category")==reserved[rid]["category"] and
                  row.get("height")==reserved[rid].get("height") and
                  row.get("state") in ("RPC_RESPONSE","FAILED","UNKNOWN"),
                  "D1_RECOVERY_SETTLEMENT_MISMATCH")
            filename=row.get("raw_name")
            if filename is not None:
                check(type(filename) is str and RAWFILE.fullmatch(filename)
                      and filename=="%03d.body"%rid and
                      type(row.get("raw_sha256")) is str and
                      bool(SHA256.fullmatch(row["raw_sha256"])),
                      "D1_RECOVERY_RAW_MANIFEST_INVALID")
                path=rawdir/filename
                check(path.is_file() and not path.is_symlink() and
                      path.stat().st_mode & 0o077 == 0,
                      "D1_RECOVERY_RAW_NOT_PRIVATE")
                check(path.stat().st_size<=2_000_000 and
                      sha256(path.read_bytes()).hexdigest()==row["raw_sha256"],
                      "D1_RECOVERY_RAW_HASH_MISMATCH")
                raw_hashes[filename]=row["raw_sha256"]
            elif row["state"]=="RPC_RESPONSE":
                raise ValueError("D1_RECOVERY_SUCCESS_WITHOUT_RAW_FRAME")
            settled.add(rid)
            if row["category"]=="BLOCK" and row["state"]=="RPC_RESPONSE":
                rpc_parsed.add(rid)
        elif kind=="COMMIT_CONTIGUOUS":
            check(type(rid) is int and rid in settled and rid in rpc_parsed
                  and reserved[rid]["category"]=="BLOCK" and
                  type(row.get("height")) is int and
                  row["height"]==reserved[rid]["height"],
                  "D1_RECOVERY_COMMIT_WITHOUT_SOURCE")
            if commits:
                check(row["height"]==commits[-1][0]+1,
                      "D1_RECOVERY_NONCONTIGUOUS_COMMIT")
            check(all(x[1]!=rid for x in commits),
                  "D1_RECOVERY_DUPLICATE_COMMIT")
            commits.append((row["height"],rid))
        elif kind=="CHAIN_INTEGRITY_FAULT":
            check(type(rid) is int and rid in rpc_parsed and
                  reserved[rid]["category"]=="BLOCK" and
                  row.get("height")==reserved[rid]["height"] and
                  row.get("height") not in invalid,
                  "D1_RECOVERY_WRONG_FAULT_OWNER_OR_DUPLICATE")
            invalid.add(row["height"])
        else:
            raise ValueError("D1_RECOVERY_UNKNOWN_EVENT")
    if invalid and commits:
        check(all(x[0] < min(invalid) for x in commits),
              "D1_RECOVERY_COMMIT_ACROSS_BAD_PARENT")
    pending=sorted(set(reserved)-settled)
    # No automated recovery. Even if every request settled, a fault invalidates
    # the performance sample; do not infer sustainable source speed.
    integrity_ok=not pending and not invalid and all(
        row.get("state")=="RPC_RESPONSE" for row in [])
    return {
        "audit_status":("INVALID_FOR_PERFORMANCE_CLAIM"
                        if pending or invalid else "OFFLINE_ACCOUNTED_NOT_LIVE"),
        "network_retries":0,
        "automatic_recovery_permitted":False,
        "reserved":len(reserved), "settled":len(settled),
        "unknown_request_ids":pending,
        "parsed_full_block_responses":len(rpc_parsed),
        "contiguous_commits":len(commits),
        "first_parent_independently_anchored":False,
        "invalid_parent_heights":sorted(invalid),
        "raw_frames_sha256":raw_hashes,
    }
