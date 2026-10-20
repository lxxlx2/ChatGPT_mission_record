#!/usr/bin/env python3
"""Bounded, completely offline L1 full-block / ordinary-Router control ledger.

Consumes injected saved RPC responses and observation clocks, never networks or
wall-clock. Actual BSC first-seen, wallet EOA eligibility, E1/E2/E3, quotes and
independent completeness CANNOT be inferred from this file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from f0_offline_collector import _hash32
from f0_rpc_adapter import address, block_candidates, digest, hexb

SCHEMA = "bsc-f0-l1-contiguous-window-offline-v1"
COHORT_SCHEMA = "bsc-forward-f0-preparation-cohort-v1"
FROZEN_PR116_MANIFEST_PATH = "crypto-300-profit-mission/bsc-forward-follow-model/f0/F0_COHORT_PRESELECTION.json"
FROZEN_PR116_COMMIT = "cf88cd9f6568502f5c052ae3befc9cc16cbab98b"
FROZEN_PR116_BLOB = "fcd0029314353313867e565190cd4f2882089f11"
FROZEN_ROUTER_REGISTRY_BLOB = "dc425f85a3f89dd0eb2f73ee6583ad88549a00f2"
DOCUMENTED_ROUTER_MODE = "OFFICIAL_DOCUMENTED_ADDRESS_ONLY_NOT_CAUSAL_CONTROL"
ARCHITECTURE_SHA = "9134fcd41df49ef836b81c8a040974ad89c1fde1"
MAX_WINDOW = 512


def require(flag: bool, code: str) -> None:
    if not flag:
        raise ValueError(code)


def integer(value: object, code: str, lo: int = 0) -> int:
    require(type(value) is int and value >= lo, code)
    return value


def utc_ms(value: object) -> int:
    require(isinstance(value, str) and value.endswith("Z"), "UTC_REQUIRED")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
        return int(dt.timestamp() * 1000)
    except (ValueError, OverflowError) as exc:
        raise ValueError("UTC_INVALID") from exc


def git_blob_sha1(raw: bytes) -> str:
    """Identity of exact Git blob bytes, not JSON serialization or an RPC proof."""
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def load_frozen_cohort(raw: bytes) -> dict:
    """Only the exact PR #116 signed-off manifest can bind real cohort addresses.

    This works in a detached `git archive` too: cryptographically matches the
    exact Git blob identified in the PR #116 approved commit. It never fetches.
    """
    require(git_blob_sha1(raw) == FROZEN_PR116_BLOB,
            "FROZEN_COHORT_GIT_BLOB_MISMATCH")
    try:
        cohort = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_FROZEN_MANIFEST_JSON") from exc
    require(cohort.get("selection_seed") == ARCHITECTURE_SHA and
            cohort.get("reviewed_architecture_commit") == ARCHITECTURE_SHA,
            "FROZEN_MANIFEST_SEED_MISMATCH")
    return cohort


def cohort_watchlist(cohort: dict) -> tuple[set[str], dict]:
    """Accept PRIMARY addresses ONLY; never use historical PnL or backups."""
    require(cohort.get("schema") == COHORT_SCHEMA and cohort.get("chain_id") == 56 and
            cohort.get("reviewed_architecture_commit") == ARCHITECTURE_SHA and
            cohort.get("selection_seed") == ARCHITECTURE_SHA,
            "WRONG_FROZEN_COHORT_IDENTITY")
    entries = cohort.get("preliminary_wallets")
    require(isinstance(entries, list) and len(entries) == 30, "COHORT_NOT_20_PLUS_10")
    forbid = ("pnl", "profit", "win_rate", "score", "return", "independently_closed")
    require(not any(any(term in key.lower() for term in forbid for key in entry)
                    for entry in entries), "OUTCOME_FIELDS_FORBIDDEN")
    counts = {"PR40_23": {"PRIMARY": 0, "BACKUP": 0},
              "PR97_449_BSC_SIGNED": {"PRIMARY": 0, "BACKUP": 0}}
    seen: set[str] = set()
    for e in entries:
        w = address(e["wallet"])
        require(w not in seen and e.get("role") in ("PRIMARY", "BACKUP") and
                e.get("source") in counts and e.get("watch_runtime_enabled") is False,
                "INVALID_COHORT_ENTRY")
        seen.add(w)
        counts[e["source"]][e["role"]] += 1
    require(counts == {"PR40_23": {"PRIMARY": 10, "BACKUP": 5},
                       "PR97_449_BSC_SIGNED": {"PRIMARY": 10, "BACKUP": 5}},
            "COHORT_10_PRIMARY_5_BACKUP_EACH_STRATUM_REQUIRED")
    primary = {address(e["wallet"]) for e in entries if e["role"] == "PRIMARY"}
    return primary, {"primary_count": len(primary),
                     "technical_eoa_eligibility": "UNVERIFIED",
                     "cohort_binding": "INPUT_SCHEMA_ONLY_NOT_GIT_BLOB_ATTESTED",
                     "input_sha256": digest(cohort),
                     "watch_runtime_enabled": False}


def offline_window(fixture: dict, cohort: dict,
                   cohort_raw_bytes: bytes | None = None,
                   router_registry_raw: bytes | None = None) -> dict:
    require(isinstance(fixture, dict) and fixture.get("schema") == SCHEMA and
            fixture.get("mode") == "SYNTHETIC_SAVED_RPC_ONLY" and
            fixture.get("trial") is True and fixture.get("chain_id") == 56,
            "OFFLINE_ONLY")
    source_kind = fixture.get("cohort_source_kind")
    require(source_kind in ("SYNTHETIC_FIXTURE_ONLY", "FROZEN_PR116_GIT_BLOB"),
            "EXPLICIT_COHORT_SOURCE_REQUIRED")
    if source_kind == "FROZEN_PR116_GIT_BLOB":
        require(cohort_raw_bytes is not None, "FROZEN_COHORT_RAW_BYTES_REQUIRED")
        require(load_frozen_cohort(cohort_raw_bytes) == cohort,
                "FROZEN_COHORT_OBJECT_MISMATCH")
    else:
        require(cohort_raw_bytes is None and cohort.get("synthetic_fixture_only") is True,
                "SYNTHETIC_COHORT_MUST_BE_EXPLICIT")
    watched, cohort_meta = cohort_watchlist(cohort)
    cohort_meta["cohort_binding"] = (
        "VERIFIED_PR116_GIT_BLOB_OFFLINE_ONLY"
        if source_kind == "FROZEN_PR116_GIT_BLOB"
        else "SYNTHETIC_FIXTURE_NOT_REAL_COHORT"
    )
    cohort_meta["frozen_manifest_blob_sha1"] = (
        FROZEN_PR116_BLOB if source_kind == "FROZEN_PR116_GIT_BLOB" else None
    )
    cohort_meta["control_seed_source"] = "COHORT_SELECTION_SEED"
    start = integer(fixture.get("start_height"), "INVALID_START_HEIGHT", 1)
    end = integer(fixture.get("end_height"), "INVALID_END_HEIGHT", start)
    require(end - start + 1 <= MAX_WINDOW, "WINDOW_EXCEEDS_OFFLINE_CAP")
    cap = integer(fixture.get("max_rpc_calls"), "MISSING_RPC_CAP", 1)
    discovery_cap = integer(fixture.get("max_control_discovery_calls"),
                            "MISSING_CONTROL_DISCOVERY_CAP", 1)
    require("control_seed" not in fixture, "FIXTURE_CONTROL_SEED_OVERRIDE_FORBIDDEN")
    seed = cohort["selection_seed"]
    mod = integer(fixture.get("control_modulo"), "INVALID_CONTROL_MODULO", 1)
    require(isinstance(seed, str) and seed == ARCHITECTURE_SHA,
            "MISSING_FROZEN_CONTROL_SEED")
    router_mode = fixture.get("router_allowlist_kind")
    if router_mode == DOCUMENTED_ROUTER_MODE:
        # The registry pins *documented* addresses, not verified swap routes.
        # Reuse its reviewed validator; keep actual control eligibility false.
        require(source_kind == "FROZEN_PR116_GIT_BLOB" and
                isinstance(router_registry_raw, bytes) and
                git_blob_sha1(router_registry_raw) == FROZEN_ROUTER_REGISTRY_BLOB and
                "synthetic_routers" not in fixture, "FROZEN_ROUTER_REGISTRY_REQUIRED")
        from f0_l1_preflight import official_router_addresses
        registry = json.loads(router_registry_raw)
        routers = set(official_router_addresses(registry))
        router_provenance = "OFFICIAL_DOCUMENTED_ONLY_NO_SWAP_CAUSALITY"
    else:
        require(router_registry_raw is None and router_mode == "SYNTHETIC_ONLY",
                "NO_VERIFIED_ROUTER_ALLOWLIST")
        routers = {address(x) for x in fixture.get("synthetic_routers", [])}
        router_provenance = "SYNTHETIC_ROUTER_FIXTURE_ONLY"
    require(bool(routers), "NO_ROUTER_CANDIDATES")
    records = fixture.get("block_attempts")
    require(isinstance(records, list), "MISSING_OFFLINE_REQUEST_RECORDS")
    require(len(records) <= cap and len(records) <= discovery_cap,
            "OFFLINE_RPC_OR_CONTROL_BUDGET_EXCEEDED")
    by_height: dict[int, dict] = {}
    last_request_monotonic = -1
    for item in records:
        h = integer(item.get("height"), "INVALID_RECORDED_HEIGHT", start)
        require(h <= end and h not in by_height, "OUT_OF_RANGE_OR_DUPLICATE_HEIGHT")
        request_ms = utc_ms(item.get("request_utc"))
        response_ms = utc_ms(item.get("response_utc"))
        first_ms = utc_ms(item.get("first_received_utc"))
        request_mono = integer(item.get("request_monotonic_ms"), "INVALID_REQUEST_MONOTONIC")
        response_mono = integer(item.get("response_monotonic_ms"), "INVALID_RESPONSE_MONOTONIC")
        received_mono = integer(item.get("first_received_monotonic_ms"), "INVALID_FIRST_MONOTONIC")
        require(request_ms <= response_ms <= first_ms and
                last_request_monotonic <= request_mono <= response_mono <= received_mono,
                "INCONSISTENT_OBSERVATION_CLOCKS")
        # Requests may overlap when BSC produces blocks faster than network RTT.
        last_request_monotonic = request_mono
        path = item.get("ingest_path")
        require(path in ("POLL", "WS", "BACKFILL"), "INVALID_INGEST_PATH")
        ok = item.get("result")
        require(ok in ("RECEIVED", "FAILED"), "INVALID_BLOCK_ATTEMPT_RESULT")
        if ok == "RECEIVED":
            require(isinstance(item.get("rpc"), dict) and "error_code" not in item,
                    "BLOCK_RESPONSE_REQUIRED")
        else:
            require("rpc" not in item and isinstance(item.get("error_code"), str) and
                    bool(item["error_code"]), "FAILED_CALL_MUST_HAVE_ERROR_NOT_FAKE_RPC")
        by_height[h] = item
    rows, candidates, watches, controls = [], [], 0, 0
    previous = None
    for height in range(start, end + 1):
        item = by_height.get(height)
        if item is None:
            rows.append({"height": height, "state": "MISSING_NOT_ATTEMPTED",
                         "ingest_path": "UNKNOWN", "attempted_calls": 0})
            previous = None
            continue
        common = {"height": height, "ingest_path": item["ingest_path"],
                  "attempted_calls": 1, "request_utc": item["request_utc"],
                  "response_utc": item["response_utc"],
                  "first_received_utc": item["first_received_utc"],
                  "request_monotonic_ms": item["request_monotonic_ms"],
                  "response_monotonic_ms": item["response_monotonic_ms"],
                  "first_received_monotonic_ms": item["first_received_monotonic_ms"]}
        if item["result"] == "FAILED":
            rows.append({**common, "state": "FAILED", "error_code": item["error_code"]})
            previous = None
            continue
        parsed = block_candidates(item["rpc"], watched, routers)
        require(parsed["block_number"] == height, "RECEIVED_BLOCK_HEIGHT_MISMATCH")
        block = item["rpc"]["result"]
        parent = hexb(block["parentHash"], 32)
        require(previous is None or parent == previous,
                "CONTIGUOUS_PARENT_HASH_MISMATCH")
        previous = parsed["block_hash"]
        counts = {"watch_signed": 0, "control_candidates": 0, "control_selected": 0}
        for tx in parsed["candidates"]:
            if tx["group"] == "WATCHLIST":
                group, selected = "WATCHLIST_PRESELECTED", False
                counts["watch_signed"] += 1
                watches += 1
            else:
                group = "CONTROL_CANDIDATE"
                selected = _hash32(f"{seed}|{tx['wallet']}|{tx['tx_hash']}") % mod == 0
                counts["control_candidates"] += 1
                controls += 1
                if selected:
                    counts["control_selected"] += 1
            candidates.append({"height": height, "wallet": tx["wallet"],
                               "tx_hash": tx["tx_hash"], "group": group,
                               "router_eligible": tx["router_eligible"],
                               "router_address_match_only": tx["router_eligible"],
                               "control_eligible": False,
                               "control_selected_offline": selected,
                               "ingest_path": item["ingest_path"],
                               "first_received_utc": item["first_received_utc"],
                               "first_received_monotonic_ms": item["first_received_monotonic_ms"],
                               "source_rpc_sha256": parsed["raw_rpc_sha256"],
                               "side": "UNKNOWN", "ca": None,
                               "evidence": "TX_OBJECT_ONLY_NO_EOA_OR_SWAP_ATTESTATION",
                               "actual_e3": False})
        rows.append({**common, "state": "RECEIVED", "block_hash": parsed["block_hash"],
                     "parent_hash": parent, "source_rpc_sha256": parsed["raw_rpc_sha256"],
                     "full_block_tx_count": parsed["full_block_tx_count"], **counts})
    metrics = {"blocks_expected_window": end-start+1,
               "blocks_received": sum(r["state"] == "RECEIVED" for r in rows),
               "blocks_failed": sum(r["state"] == "FAILED" for r in rows),
               "missing_heights": [r["height"] for r in rows if r["state"] != "RECEIVED"],
               "backfill_received_blocks": sum(r["state"] == "RECEIVED" and r["ingest_path"] == "BACKFILL" for r in rows),
               "watch_signer_tx_in_received_blocks": watches,
               "router_control_candidates_in_received_blocks": controls,
               "preselected_control_offline": sum(x["control_selected_offline"] for x in candidates),
               "attempted_full_block_rpc_calls_offline": len(records),
               "attempted_control_discovery_rpc_calls_offline": len(records)}
    require(metrics["blocks_received"] + metrics["blocks_failed"] +
            len([r for r in rows if r["state"] == "MISSING_NOT_ATTEMPTED"]) ==
            metrics["blocks_expected_window"], "DENOMINATOR_INCONSISTENT")
    return {"schema": SCHEMA, "mode": "OFFLINE_ONLY_NOT_LIVE_L1",
            "clock_source": "INJECTED_SYNTHETIC_TIMESTAMPS_NOT_REAL_FIRST_SEEN",
            "cohort": cohort_meta,
            "control_selection": "OFFLINE_PRESELECTION_ONLY_ROUTER_AND_EOA_UNVERIFIED",
            "router_registry_provenance": router_provenance,
            "router_control_eligible": False,
            "start_height": start, "end_height": end,
            "block_rows": rows, "candidate_rows": candidates, "metrics": metrics,
            "actual_rpc_calls": 0, "live_control_coverage": "NOT_MEASURED",
            "independent_denominator": "NOT_MEASURED",
            "first_actionable_latency": "NOT_MEASURED",
            "e1_finality": "UNRESOLVED_F1_POLICY", "e2_attested": False,
            "e3_actual_count": 0, "quoted_actual_count": 0,
            "paper_profit_labels": 0,
            "stop_state": "NO_RUN", "safety": ["NO_NETWORK", "NO_TRADE", "NO_AUTOMATION", "NO_LIVE_E3"]}


def main() -> None:
    p = argparse.ArgumentParser(description="BSC F0 offline contiguous L1 ledger; NO RPC")
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--cohort", type=Path, required=True)
    p.add_argument("--router-registry", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    raw = args.fixture.read_bytes()
    manifest = args.cohort.read_bytes()
    fixture = json.loads(raw)
    router_raw = args.router_registry.read_bytes() if args.router_registry else None
    if fixture.get("cohort_source_kind") == "FROZEN_PR116_GIT_BLOB":
        cohort = load_frozen_cohort(manifest)
        report = offline_window(fixture, cohort, cohort_raw_bytes=manifest,
                                router_registry_raw=router_raw)
    else:
        report = offline_window(fixture, json.loads(manifest),
                                router_registry_raw=router_raw)
    report["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    report["cohort_file_sha256"] = hashlib.sha256(manifest).hexdigest()
    out = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(out, encoding="utf-8")
    else:
        print(out, end="")


if __name__ == "__main__":
    main()
