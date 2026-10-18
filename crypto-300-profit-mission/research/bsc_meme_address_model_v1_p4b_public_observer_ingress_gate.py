"""Read-only BSC Meme V1 observer evidence ingress: no RPC, wallet, trades or notifications.

This is an evidence validator, not a websocket client or strategy backtester.
An imported timestamp is self-asserted until independently attested; even a
well-formed public pending transaction is NOT a verified actionable token BUY.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FROZEN = "bsc-meme-address-model-v1-p4b-five-case-first-seen-u-prefreeze-2026-10-18.json"
FROZEN_BLOB = "22dff3f77fa4bc63d2bd80b76de458a826769306"
GRID = "bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json"
GRID_BLOB = "f88ed9abfcb0f321ec31e98a029303aca48a8623"
HASH = re.compile(r"0x[0-9a-fA-F]{64}\Z")
ADDR = re.compile(r"0x[0-9a-fA-F]{40}\Z")
DELAY_SECONDS = (60, 300, 900)
BLOCKED = {"PUBLIC_EXECUTABLE_U": "UNRESOLVED", "P5": "BLOCKED",
           "PRODUCTION": "NO_GO", "NO_TRADE": True, "NO_DEPLOY": True,
           "NO_MERGE": True, "NO_GMAIL": True}


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()


def source(root: Path, name: str, sha: str) -> dict:
    raw = (root / name).read_bytes()
    if blob_sha(raw) != sha:
        raise ValueError("PINNED_SOURCE_BLOB_SHA_DRIFT:" + name)
    return json.loads(raw)


def load_frozen(root: Path = ROOT) -> tuple[dict, dict]:
    pre = source(root, FROZEN, FROZEN_BLOB)
    grid = source(root, GRID, GRID_BLOB)
    wallets = [w["wallet"].lower() for w in grid["wallets"]]
    cas = [m["ca"].lower() for m in grid["markets"]]
    if (len(wallets), len(cas), len(set(wallets)), len(set(cas))) != (23, 19, 23, 19):
        raise ValueError("FROZEN_WALLET_CA_UNIVERSE_DRIFT")
    if (pre["fixed_observer_delays_seconds"] != list(DELAY_SECONDS)
            or len(pre["cases"]) != 5
            or any(c["first_public_observer_received_utc"] is not None for c in pre["cases"])):
        raise ValueError("HISTORICAL_FIRST_SEEN_PREFREEZE_DRIFT")
    return pre, grid


def utc(text: str) -> datetime:
    if not isinstance(text, str) or not text.endswith("Z"):
        raise ValueError("UTC_Z_REQUIRED")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_UTC_TIMESTAMP") from exc
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("UTC_OFFSET_NOT_ZERO")
    return parsed


def iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def historical_summary(pre: dict) -> dict:
    return {"schema": "BSC_P4B_FIRST_SEEN_EVIDENCE_GATE_V1",
            "mode": "FROZEN_HISTORICAL_EVIDENCE_STATUS",
            "cases": [
                {"case": c["case"], "token": c["token"],
                 "original_owner": c["original_owner"], "exact_ca": c["exact_ca"],
                 "first_public_observer_received_utc": None,
                 "state": "HISTORICAL_NO_ARCHIVED_PUBLIC_FIRST_SEEN",
                 "target_windows_utc": None,
                 "observer_60_300_900_real_fills": "UNRESOLVED",
                 "original_native_direction_not_follower_pnl": c["observed_native_direction"]}
                for c in pre["cases"]],
            "selected_cases": len(pre["cases"]),
            "usable_public_first_seen_records": 0,
            "strategy_win_rate": "UNRESOLVED_POSTHOC_EVIDENCE_CONTROLS",
            "gates": dict(BLOCKED)}


TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PENDING_KIND = "PUBLIC_PENDING_TRANSACTION_INGRESS"
CONFIRMED_LOG_KIND = "PUBLIC_CONFIRMED_ERC20_TRANSFER_LOG_INGRESS"


def _address_topic(address: str) -> str:
    return "0x" + "0" * 24 + address.lower()[2:]


def validate_confirmed_log(payload: dict, row: dict, wallet: str, ca: str, tx_hash: str, t: datetime, clock: dict) -> dict:
    """An immutable BNB mined ERC20 Transfer is NOT a signed EOA BUY signal."""
    if payload.get("removed") is True:
        raise ValueError("LOG_REMOVED_REORG_NOT_ACTIONABLE")
    if payload.get("removed") is not False:
        raise ValueError("LOG_REMOVAL_STATUS_NOT_PROVEN")
    topics = payload.get("topics")
    if (not isinstance(topics, list) or len(topics) != 3
            or str(topics[0]).lower() != TRANSFER_TOPIC
            or str(topics[2]).lower() != _address_topic(wallet)):
        raise ValueError("LOG_NOT_EXACT_ERC20_TRANSFER_TO_OWNER")
    if (str(payload.get("address", "")).lower() != ca
            or str(payload.get("transactionHash", "")).lower() != tx_hash):
        raise ValueError("LOG_CA_OR_TRANSACTION_HASH_MISMATCH")
    for topic in topics:
        if not isinstance(topic, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", topic):
            raise ValueError("INVALID_LOG_TOPIC")
    data = payload.get("data")
    if not isinstance(data, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", data) or int(data, 16) <= 0:
        raise ValueError("INVALID_LOG_TOKEN_AMOUNT")
    for key in ("blockNumber", "logIndex"):
        val = payload.get(key)
        if not isinstance(val, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", val):
            raise ValueError("LOG_MISSING_MINED_BLOCK_OR_INDEX")
    if int(payload["blockNumber"], 16) <= 0:
        raise ValueError("LOG_NOT_CONFIRMED_IN_BLOCK")
    if not isinstance(payload.get("blockHash"), str) or not HASH.fullmatch(payload["blockHash"]):
        raise ValueError("LOG_NO_BLOCK_HASH_PROOF")
    return {
        "state": "POST_BLOCK_TOKEN_RECEIPT_OBSERVER_CANDIDATE_UNATTESTED",
        "reason": "TOKEN_TRANSFER_INTO_WALLET_NOT_PROOF_ORIGINAL_SIGNED_BUY",
        "wallet": wallet, "exact_ca": ca, "tx_hash": tx_hash,
        "received_erc20_raw": str(int(data, 16)),
        "confirmed_block_number": int(payload["blockNumber"], 16),
        "confirmed_block_hash": payload["blockHash"].lower(),
        "log_index": int(payload["logIndex"], 16),
        "first_local_observer_received_utc_claim": iso(t),
        "first_public_observer_received_utc": None,
        "target_windows_utc": {str(delay): iso(t + timedelta(seconds=delay)) for delay in DELAY_SECONDS},
        "time_anchor": "FIRST_LOCAL_POST_BLOCK_LOG_INGRESS_CLAIM_NOT_MEMPOOL_FIRST_SEEN",
        "source_raw_sha256": row["raw_sha256"].lower(),
        "observer_clock_claim_source": clock["source"],
        "tx_original_signer": "UNRESOLVED_RECEIPT_AND_FROM_NOT_READ",
        "exact_ca_trade_buy_validation": "UNRESOLVED_TRANSFER_MAY_BE_PASSIVE",
        "trade_funding_and_execution": "UNRESOLVED",
        "follower_net_pnl": "UNRESOLVED",
    }


def _reject(reason: str) -> dict:
    return {"state": "REJECTED_EVIDENCE", "reason": reason,
            "first_public_observer_received_utc": None,
            "target_windows_utc": None,
            "follower_net_pnl": "UNRESOLVED"}


def validate_event(row: dict, wallets: set[str], cas: set[str], archived_txs: set[str]) -> dict:
    """Accept raw public pending tx evidence for research, never as signed token BUY.

    Source JSON must contain its actual raw pending event bytes encoded as b64.
    The later EVM receipt+token CA+route+cost audit is an independent separate gate.
    All event-level clocks, provenance and source URLs are claims by the importer.
    """
    try:
        if not isinstance(row, dict):
            raise ValueError("EXPECTED_JSON_OBJECT")
        if set(("event_id", "network", "wallet", "exact_ca", "tx_hash",
                "capture_kind", "raw_event_base64", "raw_sha256", "observer_received_utc",
                "capture_machine_id", "provider_id", "observer_monotonic_ns",
                "clock_sync")) - set(row):
            raise ValueError("REQUIRED_RAW_CAPTURE_FIELDS_MISSING")
        if row["network"] != "bnb-mainnet":
            raise ValueError("WRONG_NETWORK")
        wallet, ca, tx_hash = row["wallet"], row["exact_ca"], row["tx_hash"]
        if (not isinstance(wallet, str) or not ADDR.fullmatch(wallet)
                or wallet.lower() not in wallets
                or not isinstance(ca, str) or not ADDR.fullmatch(ca)
                or ca.lower() not in cas):
            raise ValueError("OUTSIDE_FROZEN_23X19")
        if not isinstance(tx_hash, str) or not HASH.fullmatch(tx_hash):
            raise ValueError("INVALID_TX_HASH")
        if tx_hash.lower() in archived_txs:
            raise ValueError("FROZEN_HISTORICAL_TX_CANNOT_BE_PROMOTED_TO_LIVE_CAPTURE")
        if row["capture_kind"] not in (PENDING_KIND, CONFIRMED_LOG_KIND):
            raise ValueError("HISTORICAL_OR_SIMULATED_CAPTURE_NOT_LIVE")
        if (not isinstance(row["event_id"], str) or not row["event_id"].strip()
                or not isinstance(row["capture_machine_id"], str) or not row["capture_machine_id"].strip()
                or not isinstance(row["provider_id"], str) or not row["provider_id"].strip()):
            raise ValueError("MISSING_CAPTURE_IDENTITY")
        mono = row["observer_monotonic_ns"]
        if isinstance(mono, bool) or not isinstance(mono, int) or mono < 0:
            raise ValueError("INVALID_MONOTONIC_CLOCK")
        clock = row["clock_sync"]
        if (not isinstance(clock, dict) or clock.get("sync_state") != "REPORTED_SYNCED"
                or not isinstance(clock.get("source"), str) or not clock["source"].strip()
                or not isinstance(clock.get("max_abs_offset_ms"), (int, float))
                or isinstance(clock["max_abs_offset_ms"], bool)
                or not 0 <= clock["max_abs_offset_ms"] < 10000):
            raise ValueError("CLOCK_SYNC_CLAIM_MISSING_OR_INVALID")
        t = utc(row["observer_received_utc"])
        if not isinstance(row["raw_sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", row["raw_sha256"]):
            raise ValueError("INVALID_RAW_SHA256")
        try:
            raw = base64.b64decode(row["raw_event_base64"], validate=True)
        except (ValueError, binascii.Error, TypeError) as exc:
            raise ValueError("RAW_EVENT_NOT_BASE64") from exc
        if len(raw) == 0 or len(raw) > 262144:
            raise ValueError("INVALID_RAW_EVENT_SIZE")
        if hashlib.sha256(raw).hexdigest() != row["raw_sha256"].lower():
            raise ValueError("RAW_EVENT_SHA256_MISMATCH")
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("RAW_EVENT_NOT_JSON") from exc
        if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
            candidate_payload = payload["params"].get("result")
        else:
            candidate_payload = payload
        if row["capture_kind"] == CONFIRMED_LOG_KIND:
            if not isinstance(candidate_payload, dict):
                raise ValueError("RAW_EVENT_NOT_A_LOG_OBJECT")
            return validate_confirmed_log(candidate_payload, row, wallet.lower(),
                                          ca.lower(), tx_hash.lower(), t, clock)
        # Support a JSON-RPC pending tx object or a direct pending transaction
        # object. A bare hash is NOT an authenticated original-signer event.
        if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
            payload = payload["params"].get("result")
        if not isinstance(payload, dict):
            raise ValueError("RAW_EVENT_LACKS_TX_FROM")
        if (str(payload.get("hash", "")).lower() != tx_hash.lower()
                or str(payload.get("from", "")).lower() != wallet.lower()):
            raise ValueError("RAW_EVENT_TX_HASH_OR_FROM_MISMATCH")
        if "blockNumber" in payload and payload["blockNumber"] not in (None, "pending"):
            raise ValueError("RAW_EVENT_IS_CONFIRMED_BLOCK_REPLAY")
        if payload.get("timestamp") == row["observer_received_utc"]:
            # Timestamp supplied by a historical API is not arrival proof.
            raise ValueError("RAW_EVENT_REUSES_HISTORICAL_TIMESTAMP")
        windows = {str(s): iso(t + timedelta(seconds=s)) for s in DELAY_SECONDS}
        return {"state": "PENDING_OWNER_TX_CAPTURE_CANDIDATE_UNATTESTED",
                "reason": "RAW_PUBLIC_FEED_EVENT_AND_SELF_REPORTED_LOCAL_CLOCK_ONLY",
                "wallet": wallet.lower(), "exact_ca": ca.lower(), "tx_hash": tx_hash.lower(),
                "first_local_observer_received_utc_claim": iso(t),
                "first_public_observer_received_utc": None,
                "target_windows_utc": windows,
                "observer_clock_claim_source": clock["source"],
                "source_raw_sha256": row["raw_sha256"].lower(),
                "pending_tx_origin_verification": "NOT_INDEPENDENTLY_RECHECKED_ON_CHAIN",
                "exact_ca_trade_buy_validation": "UNRESOLVED_ROUTER_AND_TOKEN_LOGS",
                "trade_funding_and_execution": "UNRESOLVED",
                "follower_net_pnl": "UNRESOLVED"}
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        return _reject(str(exc))


def ingest_document(doc: dict, grid: dict, pre: dict) -> dict:
    if not isinstance(doc, dict) or doc.get("schema") != "BSC_P4B_PUBLIC_OBSERVER_INGRESS_V1":
        raise ValueError("INGRESS_SCHEMA_INVALID")
    observations = doc.get("events")
    if not isinstance(observations, list) or len(observations) > 500:
        raise ValueError("INGRESS_EVENTS_NOT_BOUNDED")
    wallets = {w["wallet"].lower() for w in grid["wallets"]}
    cas = {m["ca"].lower() for m in grid["markets"]}
    archived_txs = {x[field].lower() for x in pre["cases"] for field in ("first_signed_buy_tx", "last_signed_exit_tx")}
    records, ids = [], set()
    for row in observations:
        event_id = row.get("event_id") if isinstance(row, dict) else None
        if not isinstance(event_id, str) or event_id in ids:
            result = _reject("DUPLICATE_OR_MISSING_EVENT_ID")
        else:
            ids.add(event_id)
            result = validate_event(row, wallets, cas, archived_txs)
        records.append({"event_id": event_id, **result})
    return {"schema": "BSC_P4B_FIRST_SEEN_EVIDENCE_GATE_V1",
            "mode": "OFFLINE_IMPORT_ONLY_NOT_AN_ACTIVE_MONITOR",
            "records": records,
            "counts": {"total": len(records),
                       "unattested_pending_tx_candidates": sum(x["state"] == "PENDING_OWNER_TX_CAPTURE_CANDIDATE_UNATTESTED" for x in records),
                       "unattested_post_block_transfer_candidates": sum(x["state"] == "POST_BLOCK_TOKEN_RECEIPT_OBSERVER_CANDIDATE_UNATTESTED" for x in records),
                       "rejected": sum(x["state"] == "REJECTED_EVIDENCE" for x in records),
                       "verified_public_executable_U": 0, "proven_net_profitable_follower": 0},
            "gates": dict(BLOCKED)}


def main() -> None:
    p = argparse.ArgumentParser(description="Offline BSC first-seen evidence quality gate; NO RPC/trade")
    p.add_argument("--input", type=Path, help="Existing local JSON document of raw ingress records")
    p.add_argument("--output", type=Path, help="Optional local output file; no network")
    a = p.parse_args()
    pre, grid = load_frozen()
    if a.input:
        output = ingest_document(json.loads(a.input.read_text(encoding="utf-8")), grid, pre)
    else:
        output = historical_summary(pre)
    encoded = json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if a.output:
        a.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
