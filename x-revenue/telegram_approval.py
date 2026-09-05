#!/usr/bin/env python3
"""Telegram approval delivery, callback polling, and state binding."""

from __future__ import annotations

import base64
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

from config import get_telegram_token, load_config

MAX_CALLBACK_DATA_LEN = 64
TELEGRAM_API_BASE = "https://api.telegram.org"


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def encode_callback_data(action: str, candidate_sha256: str) -> str:
    """Encode action and 256-bit hash into <= 64 char urlsafe base64 string."""
    if action not in ("A", "R"):
        raise ValueError(f"Invalid action: {action}")
    raw_bytes = bytes.fromhex(candidate_sha256)
    b64 = base64.urlsafe_b64encode(raw_bytes).decode("ascii").rstrip("=")
    encoded = f"{action}:{b64}"
    if len(encoded) > MAX_CALLBACK_DATA_LEN:
        raise ValueError(f"Encoded callback data exceeds {MAX_CALLBACK_DATA_LEN} bytes")
    return encoded


def decode_callback_data(data: str) -> tuple[str, str]:
    """Decode and validate callback data string to (action, sha256_hex)."""
    match = re.fullmatch(r"([AR]):([A-Za-z0-9_-]{43})", data)
    if not match:
        raise ValueError("MALFORMED_CALLBACK")
    action = match.group(1)
    b64_part = match.group(2)
    # 43 chars urlsafe base64 needs 1 '=' padding to decode 32 bytes (256 bits)
    padded = b64_part + "="
    try:
        raw_bytes = base64.urlsafe_b64decode(padded)
    except Exception:
        raise ValueError("MALFORMED_CALLBACK")
    if len(raw_bytes) != 32:
        raise ValueError("MALFORMED_CALLBACK")
    sha_hex = raw_bytes.hex()
    if encode_callback_data(action, sha_hex) != data:
        raise ValueError("MALFORMED_CALLBACK")
    return action, sha_hex


def _telegram_api_call(token: str, method: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    url = f"{TELEGRAM_API_BASE}/bot{token}/{method}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(1_000_000)
            parsed = json.loads(data.decode("utf-8"))
            if not parsed.get("ok"):
                desc = parsed.get("description", "Unknown Telegram error")
                raise RuntimeError(f"TELEGRAM_API_ERROR: {desc}")
            return parsed.get("result", {})
    except urllib.error.HTTPError as err:
        err_msg = err.read(4096).decode("utf-8", errors="replace")
        raise RuntimeError(f"TELEGRAM_HTTP_ERROR_{err.code}: {err_msg}")


def send_approval_message(
    artifact_dir: Path,
    candidate_text: str,
    trigger_summary: str,
    source_timestamp: str,
    candidate_sha256: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Send approval request message with Approve/Reject inline keyboard to Telegram."""
    token = get_telegram_token()
    chat_id = config.get("telegram_chat_id")
    if not token or not chat_id:
        return {
            "sent": False,
            "delivery_state": "CREDENTIALS_MISSING",
            "reason": "Telegram bot token or chat ID is not configured",
        }

    approve_cb = encode_callback_data("A", candidate_sha256)
    reject_cb = encode_callback_data("R", candidate_sha256)

    text = (
        "X candidate (approval only; publishing OFF)\n\n"
        f"{candidate_text}\n\n"
        f"Trigger: {trigger_summary}\n"
        f"Session: {source_timestamp}\n"
        f"SHA256: {candidate_sha256}"
    )

    markup = {
        "inline_keyboard": [
            [
                {"text": "Approve", "callback_data": approve_cb},
                {"text": "Reject", "callback_data": reject_cb},
            ]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": markup,
    }

    try:
        result = _telegram_api_call(token, "sendMessage", payload)
        message_id = result.get("message_id")
        return {
            "sent": True,
            "delivery_state": "SENT",
            "telegram_message_id": message_id,
            "telegram_chat_id": str(chat_id),
        }
    except Exception as exc:
        return {
            "sent": False,
            "delivery_state": "FAILED",
            "reason": f"Telegram delivery failed: {type(exc).__name__}",
        }


def find_artifact_by_sha256(artifacts_root: Path, sha256_hex: str) -> Path | None:
    """Find the artifact folder corresponding to the candidate SHA-256."""
    if not artifacts_root.is_dir():
        return None
    for child in artifacts_root.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            app_file = child / "approval.json"
            if app_file.is_file():
                try:
                    data = json.loads(app_file.read_text(encoding="utf-8"))
                    if data.get("candidate_sha256") == sha256_hex:
                        return child
                except Exception:
                    continue
    return None


def handle_single_callback(
    query: dict[str, Any],
    artifacts_root: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate and apply a callback query to the candidate approval state machine."""
    query_id = query.get("id")
    data = query.get("data", "")
    from_user = query.get("from", {})
    message = query.get("message", {})
    chat = message.get("chat", {})

    # 1. Parse and validate format
    try:
        action, sha256_hex = decode_callback_data(data)
    except ValueError:
        return {"status": "REJECTED", "reason": "MALFORMED_CALLBACK", "query_id": query_id}

    # 2. Match candidate
    artifact_dir = find_artifact_by_sha256(artifacts_root, sha256_hex)
    if not artifact_dir:
        return {"status": "REJECTED", "reason": "UNKNOWN_CANDIDATE", "query_id": query_id}

    # 3. Verify candidate digest match
    candidate_file = artifact_dir / "candidate.txt"
    if not candidate_file.is_file():
        return {"status": "REJECTED", "reason": "CANDIDATE_MISSING", "query_id": query_id}
    raw_candidate = candidate_file.read_bytes().rstrip(b"\n")
    actual_hash = hashlib.sha256(raw_candidate).hexdigest()
    if actual_hash != sha256_hex:
        return {"status": "REJECTED", "reason": "CANDIDATE_DIGEST_MISMATCH", "query_id": query_id}

    # 4. Authorization & binding check
    configured_chat = config.get("telegram_chat_id")
    if configured_chat and str(chat.get("id")) != str(configured_chat):
        return {"status": "REJECTED", "reason": "CALLBACK_BINDING_REJECTED", "query_id": query_id}

    allowed_users = config.get("telegram_allowed_user_ids", [])
    user_id_str = str(from_user.get("id", ""))
    if allowed_users and user_id_str not in [str(u) for u in allowed_users]:
        return {"status": "REJECTED", "reason": "CALLBACK_BINDING_REJECTED", "query_id": query_id}

    # 5. Acquire lock on approval.json and verify state
    approval_file = artifact_dir / "approval.json"
    lock_file = artifact_dir / "approval.lock"

    with lock_file.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "REJECTED", "reason": "CONCURRENT_DECISION_ACTIVE", "query_id": query_id}

        try:
            approval = json.loads(approval_file.read_text(encoding="utf-8"))
        except Exception:
            return {"status": "REJECTED", "reason": "CORRUPT_APPROVAL_STATE", "query_id": query_id}

        # Check replay / already decided
        if approval.get("status") not in ("PENDING", "PENDING_HUMAN_APPROVAL"):
            return {"status": "REJECTED", "reason": "ALREADY_FINALIZED", "query_id": query_id}

        # Check expiration
        expires_at_raw = approval.get("expires_at")
        now = dt.datetime.now(dt.timezone.utc)
        if expires_at_raw:
            try:
                exp_dt = dt.datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
                if now >= exp_dt:
                    approval.update({
                        "status": "EXPIRED",
                        "decision": "EXPIRED",
                        "decided_at": utc_now_iso(),
                        "actor": f"telegram:{user_id_str}",
                        "external_publish_allowed": False,
                    })
                    _atomic_write_json(approval_file, approval)
                    return {"status": "REJECTED", "reason": "STALE_CALLBACK", "query_id": query_id}
            except Exception:
                pass

        # Apply decision
        decision = "APPROVED" if action == "A" else "REJECTED"
        actor_name = from_user.get("username") or user_id_str
        approval.update({
            "status": decision,
            "decision": decision,
            "decided_at": utc_now_iso(),
            "actor": f"telegram:{actor_name}",
            "note": f"Decided via Telegram inline callback query {query_id}",
            "external_publish_allowed": False,
        })
        _atomic_write_json(approval_file, approval)

    return {
        "status": "DECIDED",
        "decision": decision,
        "artifact": str(artifact_dir),
        "candidate_sha256": sha256_hex,
        "actor": f"telegram:{actor_name}",
        "query_id": query_id,
        "message_id": message.get("message_id"),
        "chat_id": chat.get("id"),
    }


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def poll_and_process_callbacks(
    artifacts_root: Path,
    state_dir: Path,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Poll Telegram Bot getUpdates for inline callbacks and process them."""
    token = get_telegram_token()
    if not token:
        return []

    state_dir.mkdir(parents=True, exist_ok=True)
    offset_file = state_dir / "telegram-offset.json"
    offset = 0
    if offset_file.is_file():
        try:
            offset = json.loads(offset_file.read_text(encoding="utf-8")).get("offset", 0)
        except Exception:
            offset = 0

    try:
        updates = _telegram_api_call(
            token,
            "getUpdates",
            {"offset": offset, "limit": 100, "timeout": 0, "allowed_updates": ["callback_query"]},
        )
    except Exception:
        return []

    results: list[dict[str, Any]] = []
    if not isinstance(updates, list):
        return results

    for update in updates:
        update_id = update.get("update_id", 0)
        query = update.get("callback_query")
        if query:
            res = handle_single_callback(query, artifacts_root, config)
            results.append(res)
            # Answer callback query to stop loading spinner on client
            query_id = query.get("id")
            if query_id:
                if res.get("status") == "DECIDED":
                    answer_text = f"Candidate {res['decision']}; publishing remains OFF."
                else:
                    answer_text = f"Rejected: {res.get('reason', 'INVALID')}"
                try:
                    _telegram_api_call(
                        token,
                        "answerCallbackQuery",
                        {"callback_query_id": query_id, "text": answer_text},
                    )
                except Exception:
                    pass

        offset = max(offset, update_id + 1)
        _atomic_write_json(offset_file, {"offset": offset})

    return results
