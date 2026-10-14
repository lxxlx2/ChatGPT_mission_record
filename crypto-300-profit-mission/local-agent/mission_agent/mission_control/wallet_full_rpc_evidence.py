"""A05 isolated full-wire-byte finalized owner RPC evidence and deterministic replay.

Unlike the ChatGPT connector's truncated display this module only accepts a
COMPLETE bounded network response. No private RPC URL, secret, market buy,
trade, pricing, Gmail or protected SQLite appears in an evidence manifest.
It never calls the network itself; the CLI supplies an explicit byte reader.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid

from .person_registry import _solana_pubkey_32_bytes
from .wallet_chain_capture import (
    ChainCaptureError, PROGRAMS, capture_owner, normalize_owner_program,
    _fingerprint,
)

MAX_RAW_RPC_BYTES = 12_000_000
FILES = ("spl-token.json", "token-2022.json")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_exclusive(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _load_verified_reply(raw: bytes, expected_id: int, wallet: str,
                         program: str) -> tuple[dict, dict]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_RAW_RPC_BYTES:
        raise ValueError("OWNER_RPC_FULL_BYTES_REQUIRED")
    try:
        reply = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("OWNER_RPC_INCOMPLETE_JSON") from exc
    if (not isinstance(reply, dict) or type(reply.get("id")) is not int
            or reply["id"] != expected_id or "error" in reply
            or "result" not in reply):
        raise ValueError("OWNER_RPC_ENVELOPE_INVALID")
    # Completeness is established by a complete, parsed JSON-RPC value array,
    # not by the server's HTTP 200 or by a truncated snippet.
    observation = normalize_owner_program(wallet, program, reply)
    return reply, observation


def _assert_directory(path: Path) -> Path:
    original = Path(path).expanduser()
    if original.is_symlink() or any(x.is_symlink() for x in (original, *original.parents)):
        raise ValueError("OWNER_EVIDENCE_SYMLINK_FORBIDDEN")
    # Full original wallet RPC bytes are local research data, never a file
    # inside the public Mission checkout where they could be git committed.
    result = original.resolve()
    repository_root = Path(__file__).resolve().parents[4]
    if result == repository_root or repository_root in result.parents:
        raise ValueError("OWNER_EVIDENCE_INSIDE_GIT_CHECKOUT_FORBIDDEN")
    return result


def collect_owner_full_receipts(*, wallet: str, evidence_root: Path,
                                read_raw, min_context_slot: int | None = None,
                                observed_at_utc: str | None = None) -> dict:
    """Make exactly two explicit finalized token-program owner RPC calls.

    read_raw(method,params,expected_id) -> raw HTTPS response body bytes.
    The resulting manifest is saved even if a program fails, in which case
    'complete' is false and importing economic holdings is forbidden.
    """
    if not isinstance(wallet, str) or not _solana_pubkey_32_bytes(wallet):
        raise ValueError("RESEARCH_WALLET_INVALID")
    if min_context_slot is not None and (type(min_context_slot) is not int
                                        or min_context_slot < 0):
        raise ValueError("MIN_CONTEXT_SLOT_INVALID")
    observed = observed_at_utc or datetime.now(timezone.utc).isoformat()
    if not isinstance(observed, str):
        raise ValueError("OWNER_EVIDENCE_TIME_INVALID")
    try:
        date = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("OWNER_EVIDENCE_TIME_INVALID")
    except (ValueError, TypeError) as exc:
        raise ValueError("OWNER_EVIDENCE_TIME_INVALID") from exc
    root = _assert_directory(evidence_root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    bundle = root / ("owner-" + uuid.uuid4().hex)
    bundle.mkdir(mode=0o700)
    receipts, missing, reply_by_program = [], [], {}
    lower_bound = min_context_slot
    for index, (program, filename) in enumerate(zip(PROGRAMS, FILES), 1):
        config = {"encoding": "jsonParsed", "commitment": "finalized"}
        if lower_bound is not None:
            config["minContextSlot"] = lower_bound
        params = [wallet, {"programId": program}, config]
        try:
            wire = read_raw("getTokenAccountsByOwner", params, index)
            reply, normalized = _load_verified_reply(wire, index, wallet, program)
            if lower_bound is not None and normalized["slot"] < lower_bound:
                raise ValueError("OWNER_RPC_CONTEXT_BELOW_REQUIRED_MIN")
        except (OSError, RuntimeError, TimeoutError, ValueError, TypeError,
                KeyError, ChainCaptureError) as exc:
            missing.append({
                "program_id": program,
                "reason": "COMPLETE_OWNER_RPC_RESPONSE_UNAVAILABLE",
                "error_type": type(exc).__name__,
            })
            continue
        _write_exclusive(bundle / filename, wire)
        receipts.append({
            "program_id": program,
            "file": filename,
            "bytes": len(wire),
            "sha256": _digest(wire),
            "slot": normalized["slot"],
            "account_count": normalized["account_count"],
        })
        reply_by_program[program] = reply
        lower_bound = max(lower_bound or 0, normalized["slot"])
    complete = len(receipts) == len(PROGRAMS)
    capture = None
    if complete:
        # Replay through the *existing* already-reviewed A05 normalization:
        # a request error cannot masquerade as an empty account list.
        def request(method, params):
            return reply_by_program[params[1]["programId"]]
        capture = capture_owner(wallet, request,
                                min_context_slot=min_context_slot)
        capture["observed_at_utc"] = observed
        capture["capture_sha256"] = _fingerprint({
            k: v for k, v in capture.items() if k != "capture_sha256"
        })
    manifest = {
        "schema_version": 1,
        "kind": "SOLANA_OWNER_FULL_RPC_WIRE_EVIDENCE_V1",
        "wallet": wallet,
        "network": "solana-mainnet",
        "observed_at_utc": observed,
        "commitment": "finalized",
        "encoding": "jsonParsed",
        "min_context_slot": min_context_slot,
        "complete": complete,
        "both_programs_observed_non_atomic": complete,
        "same_slot_atomic": False,
        "receipts": receipts,
        "missing": missing,
        "capture_sha256": capture["capture_sha256"] if capture else None,
        "slot_min": capture["slot_min"] if capture else None,
        "slot_max": capture["slot_max"] if capture else None,
        "full_32_mint_roster_verified": False,
        "history_complete": False,
    }
    _write_exclusive(bundle / "manifest.json",
                     json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")).encode("utf-8"))
    return {"bundle": str(bundle), "manifest": manifest, "snapshot": capture}


def replay_owner_full_receipts(bundle_dir: Path, *, expected_wallet: str) -> dict:
    """Verify every *original wire byte* and rebuild same immutable snapshot.

    A partial manifest never creates a fake complete owner snapshot.
    No SQLite writes or network calls happen here.
    """
    bundle = _assert_directory(bundle_dir)
    manifest_path = bundle / "manifest.json"
    raw = manifest_path.read_bytes()
    if len(raw) > 64_000:
        raise ValueError("OWNER_MANIFEST_TOO_LARGE")
    manifest = json.loads(raw)
    if (not isinstance(manifest, dict)
            or manifest.get("schema_version") != 1
            or manifest.get("kind") != "SOLANA_OWNER_FULL_RPC_WIRE_EVIDENCE_V1"
            or manifest.get("wallet") != expected_wallet
            or manifest.get("network") != "solana-mainnet"
            or manifest.get("commitment") != "finalized"
            or manifest.get("encoding") != "jsonParsed"
            or manifest.get("complete") is not True
            or manifest.get("both_programs_observed_non_atomic") is not True
            or manifest.get("same_slot_atomic") is not False
            or manifest.get("missing") != []
            or not isinstance(manifest.get("receipts"), list)
            or len(manifest["receipts"]) != 2):
        raise ValueError("OWNER_SOURCE_NOT_FULLY_VERIFIED")
    stamp = manifest.get("observed_at_utc")
    if not isinstance(stamp, str):
        raise ValueError("OWNER_EVIDENCE_TIME_INVALID")
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("OWNER_EVIDENCE_TIME_INVALID")
    except ValueError as exc:
        raise ValueError("OWNER_EVIDENCE_TIME_INVALID") from exc
    replies = {}
    lower_bound = manifest.get("min_context_slot")
    if lower_bound is not None and (type(lower_bound) is not int
                                    or lower_bound < 0):
        raise ValueError("OWNER_RECEIPT_SOURCE_METADATA_MISMATCH")
    for index, (program, filename) in enumerate(zip(PROGRAMS, FILES), 1):
        item = manifest["receipts"][index - 1]
        if (not isinstance(item, dict) or item.get("program_id") != program
                or item.get("file") != filename
                or type(item.get("bytes")) is not int
                or type(item.get("slot")) is not int
                or type(item.get("account_count")) is not int):
            raise ValueError("OWNER_RECEIPT_SOURCE_IDENTITY_INVALID")
        wire = (bundle / filename).read_bytes()
        if len(wire) != item["bytes"] or _digest(wire) != item.get("sha256"):
            raise ValueError("OWNER_RAW_RPC_BYTES_SHA_MISMATCH")
        reply, normalized = _load_verified_reply(
            wire, index, expected_wallet, program)
        if (normalized["slot"] != item["slot"]
                or normalized["account_count"] != item["account_count"]
                or (lower_bound is not None
                    and normalized["slot"] < lower_bound)):
            raise ValueError("OWNER_RECEIPT_SOURCE_METADATA_MISMATCH")
        replies[program] = reply
        lower_bound = max(lower_bound or 0, normalized["slot"])
    def request(method, params):
        return replies[params[1]["programId"]]
    result = capture_owner(expected_wallet, request,
                           min_context_slot=manifest.get("min_context_slot"))
    result["observed_at_utc"] = stamp
    result["capture_sha256"] = _fingerprint({
        k: v for k, v in result.items() if k != "capture_sha256"
    })
    if (result["both_programs_observed"] is not True
            or result["capture_sha256"] != manifest.get("capture_sha256")
            or result["slot_min"] != manifest.get("slot_min")
            or result["slot_max"] != manifest.get("slot_max")):
        raise ValueError("OWNER_REPLAY_SNAPSHOT_CONFLICT")
    return result
