#!/usr/bin/env python3
"""D1 offline audit/recovery. NEVER retries unknown requests or opens network."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import re

from f0_rpc_adapter import block_candidates, hexb

SHA256 = re.compile(r"[0-9a-f]{64}\Z")
RAWFILE = re.compile(r"[0-9]{3}\.body\Z")


def _no_duplicate_fields(items):
    result = {}
    for key, value in items:
        check(key not in result, "D1_RECOVERY_ANCHOR_DUPLICATE_JSON_FIELD")
        result[key] = value
    return result


def _anchored_block(raw, rid, height):
    """Validate an archived same-source full block and its RPC identity.

    This is stronger than merely hashing a caller-owned journal, but remains
    SAME-SOURCE proof only; never canonical/finalized chain attestation.
    """
    try:
        rpc = json.loads(raw, object_pairs_hook=_no_duplicate_fields)
        check(type(rpc) is dict and type(rpc.get("id")) is int
              and rpc["id"] == rid, "D1_RECOVERY_ANCHORED_RPC_ID_INVALID")
        parsed = block_candidates(rpc, set(), set())
        check(parsed["block_number"] == height,
              "D1_RECOVERY_ANCHORED_HEIGHT_INVALID")
        parent = hexb(rpc["result"]["parentHash"], 32)
        return parsed["block_hash"], parent
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
        raise ValueError("D1_RECOVERY_ANCHORED_RAW_INVALID:" + str(exc)) from exc


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
    failed_requests=set()
    raw_hashes={}
    last_id=0
    # FIRST_BLOCK_RESERVATION is the local baseline when a journal lacks a
    # successfully archived INITIAL_HEAD (e.g. old isolated test fixtures).
    # Where an initial HEAD exists, anchor additionally to its verified raw
    # JSON-RPC value. Never infer the first committed height from COMMIT rows:
    # that would silently forgive deletion of the initial commit event.
    first_reserved_block_height=None
    initial_head_height=None
    anchor_id=None
    anchor_height=None
    anchor_hash=None
    anchored_block_headers={}
    verified_first_parent=0
    verified_internal_links=0
    last_anchored_commit_hash=None
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
            check(row.get("category") in ("CHAIN","HEAD","INITIAL_HEAD","ANCHOR","BLOCK")
                  and row.get("method") in
                  ("eth_chainId","eth_blockNumber","eth_getBlockByNumber"),
                  "D1_RECOVERY_RESERVE_CATEGORY_INVALID")
            if row["category"]=="BLOCK":
                check(row["method"]=="eth_getBlockByNumber"
                      and type(row.get("height")) is int and row["height"]>0,
                      "D1_RECOVERY_RESERVED_HEIGHT_INVALID")
                if first_reserved_block_height is None:
                    first_reserved_block_height=row["height"]
                else:
                    # The single coordinator reserves each successive BLOCK
                    # exactly once even when returns arrive out of order.
                    previous_block_height=max(
                        item["height"] for item in reserved.values()
                        if item["category"]=="BLOCK")
                    check(row["height"]==previous_block_height+1,
                          "D1_RECOVERY_BLOCK_RESERVATION_GAP")
            elif row["category"]=="ANCHOR":
                check(anchor_id is None and type(row.get("height")) is int
                      and row["height"] > 0
                      and row["method"]=="eth_getBlockByNumber"
                      and initial_head_height is not None
                      and row["height"]==initial_head_height
                      and first_reserved_block_height is None,
                      "D1_RECOVERY_ANCHOR_RESERVATION_INVALID")
                anchor_id=rid
                anchor_height=row["height"]
            elif row["category"] in ("INITIAL_HEAD","HEAD"):
                check(row["method"]=="eth_blockNumber",
                      "D1_RECOVERY_RESERVE_CATEGORY_INVALID")
            elif row["category"]=="CHAIN":
                check(row["method"]=="eth_chainId",
                      "D1_RECOVERY_RESERVE_CATEGORY_INVALID")
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
                if (reserved[rid]["category"] in ("ANCHOR","BLOCK")
                        and anchor_id is not None
                        and row["state"]=="RPC_RESPONSE"):
                    block_hash,parent_hash=_anchored_block(
                        path.read_bytes(),rid,reserved[rid]["height"])
                    if reserved[rid]["category"]=="ANCHOR":
                        check(rid==anchor_id and
                              anchor_hash is None and
                              reserved[rid]["height"]==initial_head_height,
                              "D1_RECOVERY_ANCHOR_SETTLEMENT_INVALID")
                        anchor_hash=block_hash
                    else:
                        anchored_block_headers[rid]=(block_hash,parent_hash)
                if (reserved[rid]["category"]=="INITIAL_HEAD"
                        and row["state"]=="RPC_RESPONSE"):
                    check(initial_head_height is None,
                          "D1_RECOVERY_DUPLICATE_INITIAL_HEAD")
                    try:
                        head_rpc=json.loads(path.read_bytes())
                        quantity=head_rpc["result"]
                        valid=(type(head_rpc) is dict and
                               head_rpc.get("jsonrpc")=="2.0" and
                               type(head_rpc.get("id")) is int and
                               head_rpc["id"]==rid and
                               type(quantity) is str and
                               quantity.startswith("0x") and
                               len(quantity)>2 and
                               all(x in "0123456789abcdef" for x in quantity[2:]))
                        check(valid,"D1_RECOVERY_INITIAL_HEAD_INVALID")
                        initial_head_height=int(quantity,16)
                    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
                        raise ValueError(
                            "D1_RECOVERY_INITIAL_HEAD_INVALID") from exc
            elif row["state"]=="RPC_RESPONSE":
                raise ValueError("D1_RECOVERY_SUCCESS_WITHOUT_RAW_FRAME")
            settled.add(rid)
            if row["state"] != "RPC_RESPONSE":
                failed_requests.add(rid)
            if row["category"]=="BLOCK" and row["state"]=="RPC_RESPONSE":
                rpc_parsed.add(rid)
        elif kind=="COMMIT_CONTIGUOUS":
            check(type(rid) is int and rid in settled and rid in rpc_parsed
                  and reserved[rid]["category"]=="BLOCK" and
                  type(row.get("height")) is int and
                  row["height"]==reserved[rid]["height"],
                  "D1_RECOVERY_COMMIT_WITHOUT_SOURCE")
            if not commits:
                check(first_reserved_block_height is not None and
                      row["height"]==first_reserved_block_height,
                      "D1_RECOVERY_FIRST_COMMIT_START_GAP")
                if initial_head_height is not None:
                    check(first_reserved_block_height==initial_head_height+1,
                          "D1_RECOVERY_INITIAL_HEAD_START_MISMATCH")
            else:
                check(row["height"]==commits[-1][0]+1,
                      "D1_RECOVERY_NONCONTIGUOUS_COMMIT")
            check(all(x[1]!=rid for x in commits),
                  "D1_RECOVERY_DUPLICATE_COMMIT")
            if anchor_id is not None:
                # A fake coordinator may have committed a block but this
                # independent recovery audit MUST verify the saved RAW chain.
                check(anchor_hash is not None and anchor_id in settled
                      and anchor_height==initial_head_height
                      and rid in anchored_block_headers,
                      "D1_RECOVERY_UNVERIFIED_ANCHOR_COMMIT")
                block_hash,parent_hash=anchored_block_headers[rid]
                expected_parent=(anchor_hash if not commits
                                 else last_anchored_commit_hash)
                check(parent_hash==expected_parent,
                      "D1_RECOVERY_ANCHORED_PARENT_MISMATCH")
                if not commits:
                    verified_first_parent=1
                else:
                    verified_internal_links+=1
                last_anchored_commit_hash=block_hash
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
    # Correlate the actual INITIAL_HEAD even when no COMMIT event survives.
    # A missing first or all commit rows must never turn a completed positive
    # BLOCK response into a clean performance-accounted result.
    if first_reserved_block_height is not None and initial_head_height is not None:
        check(first_reserved_block_height==initial_head_height+1,
              "D1_RECOVERY_INITIAL_HEAD_START_MISMATCH")
    head_gap=(first_reserved_block_height is None or
              (bool(rpc_parsed) and not commits)
              or (anchor_id is not None and (
                  anchor_hash is None or
                  len(commits)!=len(rpc_parsed))))
    # No automated recovery. Even if every request settled, a fault invalidates
    # the performance sample; do not infer sustainable source speed.
    return {
        "audit_status":("INVALID_FOR_PERFORMANCE_CLAIM"
                        if pending or invalid or failed_requests or head_gap
                        else "OFFLINE_ACCOUNTED_NOT_LIVE"),
        "network_retries":0,
        "automatic_recovery_permitted":False,
        "reserved":len(reserved), "settled":len(settled),
        "unknown_request_ids":pending,
        "failed_request_ids":sorted(failed_requests),
        "parsed_full_block_responses":len(rpc_parsed),
        "contiguous_commits":len(commits),
        "expected_first_block_height":first_reserved_block_height,
        "verified_initial_head_height":initial_head_height,
        "first_commit_missing":bool(rpc_parsed) and not commits,
        "first_parent_independently_anchored":False,
        "initial_anchor_attempts":int(anchor_id is not None),
        "initial_anchor_raw_verified":anchor_hash is not None,
        "initial_anchor_height":anchor_height,
        "verified_initial_parent_links":verified_first_parent,
        "verified_internal_parent_links":verified_internal_links,
        "first_parent_same_source_anchored":bool(verified_first_parent),
        "invalid_parent_heights":sorted(invalid),
        "raw_frames_sha256":raw_hashes,
    }
