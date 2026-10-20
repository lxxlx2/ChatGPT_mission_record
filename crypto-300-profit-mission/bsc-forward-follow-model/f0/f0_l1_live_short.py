#!/usr/bin/env python3
"""Single-use BSC short-window HTTP L1. DO NOT RUN without independently reviewed permit.

Real network entrypoint is opt-in --execute-live only; injected trials have no
network and use local fake transport. Never interpret local response arrival as
global first-seen. No retries, WS, payment, signing or automation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
import urllib.error
import urllib.request

from f0_l1_code_probe import atomic_json, fsync_directory
from f0_l1_durable_journal import Journal
from f0_l1_http_wire import ENDPOINT, json_body, parse_http_response, plan_prospective_heights, _parse_quantity
from f0_l1_window import (SCHEMA as WINDOW_SCHEMA, DOCUMENTED_ROUTER_MODE,
                          FROZEN_ROUTER_REGISTRY_BLOB, git_blob_sha1,
                          load_frozen_cohort, cohort_watchlist, offline_window, utc_ms)
from f0_l1_preflight import official_router_addresses
from f0_rpc_adapter import block_candidates, digest

SCHEMA = "bsc-f0-l1-short-http-single-use-v1"
MAX_BLOCKS = 60
MAX_CALLS = 62
MAX_BODY = 2_000_000
DEPENDENCIES = (
    "f0_l1_http_wire.py", "f0_l1_durable_journal.py", "f0_l1_injected_capture.py", "f0_l1_window.py",
    "f0_l1_preflight.py", "f0_l1_code_probe.py", "f0_offline_collector.py",
    "f0_rpc_adapter.py", "f0_bounded_smoke.py", "F0_COHORT_PRESELECTION.json",
    "F0_ROUTER_SOURCE_CANDIDATES.json")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def require(ok, code):
    if not ok:
        raise ValueError(code)


def utcnow():
    return datetime.now(timezone.utc)


def iso(now):
    return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def timestamp(text):
    require(isinstance(text, str) and text.endswith("Z"), "UTC_REQUIRED")
    try:
        return datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("UTC_INVALID") from exc


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_permit(permit, now):
    require(isinstance(permit, dict) and permit.get("scope") == SCHEMA and
            permit.get("user_authorized") is True and
            permit.get("independent_review_required") is True and
            permit.get("endpoint") == ENDPOINT and
            permit.get("chain_id") == 56 and
            permit.get("methods") ==
            ["eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"] and
            permit.get("free_only") is True and permit.get("read_only") is True and
            permit.get("no_retries") is True and permit.get("no_ws") is True and
            permit.get("no_proxy") is True and permit.get("no_redirects") is True and
            permit.get("background") is False, "CAPTURE_AUTHORIZATION_INVALID")
    blocks = permit.get("max_block_reads")
    require(type(blocks) is int and 1 <= blocks <= MAX_BLOCKS and
            type(permit.get("max_total_attempts")) is int and
            permit["max_total_attempts"] == blocks + 2 and
            permit["max_total_attempts"] <= MAX_CALLS,
            "CAPTURE_REQUEST_CAP_INVALID")
    require(type(permit.get("min_interval_ms")) is int and
            250 <= permit["min_interval_ms"] <= 5000 and
            type(permit.get("future_block_pace_ms")) is int and
            500 <= permit["future_block_pace_ms"] <= 2000 and
            type(permit.get("max_response_bytes")) is int and
            0 < permit["max_response_bytes"] <= MAX_BODY and
            type(permit.get("timeout_ms")) is int and
            1000 <= permit["timeout_ms"] <= 8000 and
            permit.get("fail_streak_limit") == 3, "CAPTURE_RESOURCE_CAP_INVALID")
    start, end = timestamp(permit.get("window_start_utc")), timestamp(permit.get("window_end_utc"))
    require(timedelta(0) < end-start <= timedelta(minutes=10) and start <= now <= end,
            "CAPTURE_WINDOW_INVALID")
    require(isinstance(permit.get("approved_commit_sha"), str) and
            HEX40.fullmatch(permit["approved_commit_sha"]) and
            isinstance(permit.get("approved_script_sha256"), str) and
            HEX64.fullmatch(permit["approved_script_sha256"]) and
            isinstance(permit.get("run_nonce"), str) and
            HEX64.fullmatch(permit["run_nonce"]), "CAPTURE_SHA_OR_NONCE_INVALID")
    root = permit.get("storage_root")
    require(isinstance(root, str) and root.startswith("/tmp/") and
            ".." not in Path(root).parts and Path(root).is_dir() and
            not Path(root).is_symlink() and
            permit.get("archive_raw_public_rpc") is True,
            "CAPTURE_PRIVATE_STORAGE_INVALID")
    return Path(root), end, blocks


def verify_checkout(script, permit):
    proc = subprocess.run(["git", "-C", str(script.parent), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True, timeout=5)
    require(proc.stdout.strip() == permit["approved_commit_sha"],
            "CAPTURE_UNREVIEWED_HEAD")
    require(sha(script.read_bytes()) == permit["approved_script_sha256"],
            "CAPTURE_UNREVIEWED_SCRIPT")
    repo = Path(subprocess.run(["git", "-C", str(script.parent), "rev-parse",
                                "--show-toplevel"], capture_output=True,
                               text=True, check=True, timeout=5).stdout.strip())
    for name in DEPENDENCIES:
        path = (script.parent / name).resolve(strict=True)
        rel = path.relative_to(repo.resolve()).as_posix()
        reviewed = subprocess.run(["git", "-C", str(repo), "show", "HEAD:"+rel],
                                  capture_output=True, check=True, timeout=5).stdout
        require(path.read_bytes() == reviewed, "CAPTURE_UNREVIEWED_DEPENDENCY")
    return True


class DenyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("HTTP_REDIRECT_FORBIDDEN")


def live_https_post(url, body, timeout_s, cap):
    require(url == ENDPOINT and type(body) is bytes and 0 < len(body) <= 2000,
            "HTTP_ENDPOINT_OR_REQUEST_INVALID")
    context = ssl.create_default_context()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                        urllib.request.HTTPSHandler(context=context),
                                        DenyRedirect())
    request = urllib.request.Request(url, data=body, method="POST",
        headers={"Content-Type":"application/json", "Accept":"application/json",
                 "Accept-Encoding":"identity", "Connection":"close"})
    try:
        response = opener.open(request, timeout=timeout_s)
    except urllib.error.HTTPError as exc:
        # HTTP errors still contain returned evidence. Read under the same cap;
        # the parser will reject the status after Journal archives these bytes.
        response = exc
    with response:
        status = response.status
        headers = dict(response.headers.items())
        raw = response.read(cap + 1)
    require(len(raw) <= cap, "RESPONSE_TOO_LARGE")
    return status, headers, raw



def capture_once(permit, cohort_raw, router_raw, post, *,
                 clock=utcnow, mono=time.monotonic, sleep=time.sleep):
    root, deadline, nblocks = validate_permit(permit, clock())
    cohort = load_frozen_cohort(cohort_raw)
    watched, _ = cohort_watchlist(cohort)
    require(git_blob_sha1(router_raw) == FROZEN_ROUTER_REGISTRY_BLOB,
            "FROZEN_ROUTER_REGISTRY_REQUIRED")
    routers = set(official_router_addresses(json.loads(router_raw)))
    require(len(watched) == 20 and len(routers) == 2, "CAPTURE_FROZEN_INPUT_INVALID")
    journal_path, report_path = root/"journal.json", root/"report.json"
    require(not journal_path.exists() and not report_path.exists() and
            not journal_path.is_symlink() and not report_path.is_symlink(),
            "CAPTURE_OUTPUTS_NOT_FRESH")
    raw_dir = root/"raw_responses"
    require(not raw_dir.exists(), "CAPTURE_RAW_DIRECTORY_EXISTS")
    audit = Journal(journal_path, limit=permit["max_total_attempts"],
                    clock=clock, mono=mono, sleep=sleep,
                    interval_ms=permit["min_interval_ms"],
                    deadline=deadline, raw_dir=raw_dir)
    audit.timeout_seconds = permit["timeout_ms"]/1000
    audit.response_cap = permit["max_response_bytes"]

    stop = "CAPTURE_WINDOW_COMPLETED"
    records = []
    observed_head = None
    start_height = None
    try:
        chain, failure, _ = audit.request("eth_chainId", [], "CHAIN_ID", post)
        if failure is not None or chain is None:
            raise ValueError("CHAIN_ID_UNAVAILABLE")
        # Fail before spending the separate head-call budget on a wrong chain.
        _parse_quantity(chain, "eth_chainId", 1)
        head, failure, head_item = audit.request("eth_blockNumber", [], "HEAD", post)
        if failure is not None or head is None:
            raise ValueError("HEAD_UNAVAILABLE")
        plan = plan_prospective_heights(chain, head, chain_request_id=1,
                                         head_request_id=2,max_block_reads=nblocks)
        observed_head = plan["observed_head"]
        start_height = plan["start_height"]
        head_anchor = mono()
        failed_streak = 0
        for idx, height in enumerate(range(plan["start_height"], plan["end_height"]+1)):
            wait = (idx+1)*permit["future_block_pace_ms"]/1000 - (mono()-head_anchor)
            if wait > 0:
                sleep(wait)
            if clock() > deadline:
                stop = "CAPTURE_WINDOW_EXPIRED"
                break
            row, error, attempt = audit.request(
                "eth_getBlockByNumber", [hex(height), True], "FULL_BLOCK", post)
            valid = False
            if error is None and row is not None:
                try:
                    parsed = block_candidates(row, watched, routers)
                    valid = parsed["block_number"] == height
                except (ValueError, TypeError, KeyError):
                    valid = False
            if not valid:
                error = error or "BLOCK_UNAVAILABLE_OR_WRONG_HEIGHT"
                failed_streak += 1
                entry = {"height":height, "ingest_path":"POLL",
                         "request_utc":attempt["requested_utc"],
                         "response_utc":attempt["completed_utc"],
                         "first_received_utc":attempt["completed_utc"],
                         "request_monotonic_ms":attempt["requested_monotonic_ns"]//1000000,
                         "response_monotonic_ms":attempt["completed_monotonic_ns"]//1000000,
                         "first_received_monotonic_ms":attempt["completed_monotonic_ns"]//1000000,
                         "result":"FAILED","error_code":error}
            else:
                failed_streak=0
                entry={"height":height,"ingest_path":"POLL",
                       "request_utc":attempt["requested_utc"],
                       "response_utc":attempt["completed_utc"],
                       "first_received_utc":attempt["completed_utc"],
                       "request_monotonic_ms":attempt["requested_monotonic_ns"]//1000000,
                       "response_monotonic_ms":attempt["completed_monotonic_ns"]//1000000,
                       "first_received_monotonic_ms":attempt["completed_monotonic_ns"]//1000000,
                       "result":"RECEIVED", "rpc":row}
            records.append(entry)
            if failed_streak >= 3:
                stop="CAPTURE_THREE_SOURCE_FAILURES"
                break
    except ValueError as exc:
        stop="CAPTURE_SOURCE_BLOCKED"
        fault_code = str(exc) if str(exc) in (
            "CHAIN_ID_UNAVAILABLE","HEAD_UNAVAILABLE","HTTP_SOURCE_WRONG_CHAIN",
            "HTTP_SOURCE_IDENTITY_UNVERIFIED","HTTP_SOURCE_QUANTITY_INVALID") else "SOURCE_VALIDATION_FAILED"
    else:
        fault_code = None

    report={"schema":SCHEMA,"source":"USER_LOCAL_BSC_HTTP_RESPONSE_NOT_GLOBAL_FIRST_SEEN",
            "stop_state":stop,"error_code":fault_code,
            "observed_head":observed_head, "planned_block_reads":nblocks,
            "start_height":start_height,"attempted_total":len(audit.rows),
            "attempted_identity":sum(x["category"] in ("CHAIN_ID","HEAD") for x in audit.rows),
            "attempted_blocks":len(records),
            "failed_block_attempts":sum(x["result"]=="FAILED" for x in records),
            "unattempted_blocks":nblocks-len(records),
            "actual_rpc_calls":len(audit.rows),
            "provider_billed":"UNVERIFIED",
            "first_seen_source":"LOCAL_HTTP_RESPONSE_RECEIPT_ONLY",
            "raw_http_locally_archived":True,"raw_git_committed":False,
            "live_control_eligible":False,"e2_attested":False,"actual_e3":False,
            "quoted_actual_count":0}
    if start_height is not None:
        fixture={"schema":WINDOW_SCHEMA,"mode":"SYNTHETIC_SAVED_RPC_ONLY",
                 "trial":True,"chain_id":56,
                 "cohort_source_kind":"FROZEN_PR116_GIT_BLOB",
                 "router_allowlist_kind":DOCUMENTED_ROUTER_MODE,
                 "start_height":start_height,"end_height":start_height+nblocks-1,
                 "max_rpc_calls":nblocks,"max_control_discovery_calls":nblocks,
                 "control_modulo":2,"block_attempts":records}
        try:
            parsed=offline_window(fixture,cohort,cohort_raw_bytes=cohort_raw,
                                  router_registry_raw=router_raw)
            report["offline_block_analysis"]=parsed
        except (ValueError,KeyError,TypeError):
            report["parse_state"]="SAVED_BLOCK_PARSER_REJECTED"
    atomic_json(report_path, report)
    return report


def main():
    parser=argparse.ArgumentParser(description="Explicitly gated one-shot real BSC short L1")
    parser.add_argument("--execute-live",action="store_true")
    parser.add_argument("--permit",type=Path,required=True)
    parser.add_argument("--review-approval",type=Path,required=True)
    args=parser.parse_args()
    require(args.execute_live,"LIVE_REQUIRES_EXPLICIT_EXECUTE_FLAG")
    raw=args.permit.read_bytes()
    permit=json.loads(raw)
    root, _, _=validate_permit(permit, utcnow())
    require(args.permit.resolve().parent != root.resolve(),
            "PERMIT_MUST_BE_OUTSIDE_OUTPUT_DIRECTORY")
    # Approval text MUST originate from an independent human/agent review of
    # this exact permit, not from this script or a self-issued hash.
    expected="APPROVE_PERMIT "+sha(raw)
    require(args.review_approval.read_text().strip() == expected and
            args.review_approval.resolve() != args.permit.resolve(),
            "INDEPENDENT_PERMIT_APPROVAL_MISSING_OR_MISMATCHED")
    script=Path(__file__).resolve()
    verify_checkout(script,permit)
    nonce_hash=sha(permit["run_nonce"].encode("utf-8"))
    nonce_path=root/(".f0_short_nonce_"+nonce_hash+".json")
    with nonce_path.open("x") as mark:
        os.chmod(nonce_path,0o600)
        json.dump({"permit_sha256":sha(raw),"nonce_sha256":nonce_hash,
                   "consumed_at_utc":iso(utcnow())},mark)
        mark.flush()
        os.fsync(mark.fileno())
    fsync_directory(root)
    base=script.parent
    result=capture_once(permit,
                (base/"F0_COHORT_PRESELECTION.json").read_bytes(),
                (base/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes(),
                live_https_post)
    print(json.dumps({"stop_state":result["stop_state"],
          "actual_rpc_calls":result["actual_rpc_calls"],
          "attempted_blocks":result["attempted_blocks"],
          "report":str(root/"report.json"),"journal":str(root/"journal.json")}))
    if result["stop_state"]!="CAPTURE_WINDOW_COMPLETED":
        raise SystemExit(1)


if __name__=="__main__":
    main()
