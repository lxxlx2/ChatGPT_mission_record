"""Content-addressed Frank passive-transfer research archive (opt-in only).

Works alongside the existing CA/Frank publisher without changing it. No
production writer or signal path access. Only sanitized public evidence goes
to the preexisting dedicated evidence Git branch.
"""
from __future__ import annotations

import base64
import fcntl
import json
from pathlib import Path
import re

from .evidence_sync import (
    EvidenceSpool, GitEvidencePublisher, PREFIX, atomic_new, canonical, digest, safe
)
from .wallet_transfers import SOURCE_SCOPE

ID = re.compile(r"^[0-9a-f]{64}$")
PART = re.compile(r"^part-([0-9]{4})[.]json$")
PART_BYTES = 120_000
MAX_RECORDS = 200_000
MAX_BYTES = 8_000_000
KIND = "frank-transfer-history"


def queue_transfer_history(spool: EvidenceSpool, report: dict) -> Path:
    if (not isinstance(report, dict) or report.get("source_scope") != SOURCE_SCOPE
            or report.get("person_id") != "frank"
            or not isinstance(report.get("records"), list)
            or type(report.get("record_count")) is not int
            or report["record_count"] != len(report["records"])
            or report["record_count"] > MAX_RECORDS):
        raise ValueError("TRANSFER_HISTORY_SOURCE_OR_COUNT_INVALID")
    cleaned = safe(report)
    if not isinstance(cleaned, dict) or len(cleaned.get("records", [])) != report["record_count"]:
        raise ValueError("TRANSFER_HISTORY_SANITIZER_LOST_RECORDS")
    source = canonical(cleaned)
    if len(source) > MAX_BYTES:
        raise ValueError("TRANSFER_HISTORY_TOO_LARGE_FAIL_CLOSED")
    history_id = digest(source)
    parts = []
    for index, start in enumerate(range(0, len(source), PART_BYTES)):
        piece = source[start:start + PART_BYTES]
        name = f"part-{index:04d}.json"
        packed = {
            "schema_version": 1, "snapshot_id": history_id,
            "part_index": index, "part_sha256": digest(piece),
            "payload_b64": base64.b64encode(piece).decode("ascii"),
        }
        atomic_new(spool.pending / (KIND + "-parts") / history_id / name,
                   canonical(packed))
        parts.append({"file": name, "part_index": index,
                      "sha256": digest(piece), "bytes": len(piece)})
    manifest = {
        "schema_version": 1, "kind": KIND, "snapshot_id": history_id,
        "source_scope": SOURCE_SCOPE, "record_count": report["record_count"],
        "sanitized_content_sha256": history_id, "parts": parts,
        "chain_history_complete": False, "cost_basis_verified": False,
        "net_pnl_verified": False,
    }
    destination = spool.pending / KIND / (history_id + ".json")
    atomic_new(destination, canonical(manifest))
    return destination


def _validated_parts(spool: EvidenceSpool, path: Path):
    """Fail before ANY PUT unless the complete source can be reconstructed."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    history_id = path.stem
    if (not ID.fullmatch(history_id) or manifest.get("snapshot_id") != history_id
            or manifest.get("sanitized_content_sha256") != history_id
            or manifest.get("source_scope") != SOURCE_SCOPE
            or manifest.get("kind") != KIND or
            type(manifest.get("record_count")) is not int):
        raise ValueError("TRANSFER_ARCHIVE_MANIFEST_INVALID")
    infos = manifest.get("parts")
    if not isinstance(infos, list) or not infos or len(infos) > 100:
        raise ValueError("TRANSFER_ARCHIVE_PARTS_INVALID")
    payloads = []
    for idx, item in enumerate(infos):
        if not isinstance(item, dict):
            raise ValueError("TRANSFER_ARCHIVE_PART_ENTRY_INVALID")
        name = item.get("file")
        if (not isinstance(name, str) or not PART.fullmatch(name)
                or name != f"part-{idx:04d}.json" or item.get("part_index") != idx):
            raise ValueError("TRANSFER_ARCHIVE_PART_SEQUENCE_INVALID")
        part_path = spool.pending / (KIND + "-parts") / history_id / name
        chunk = json.loads(part_path.read_text(encoding="utf-8"))
        encoded = chunk.get("payload_b64")
        if (not isinstance(encoded, str) or chunk.get("snapshot_id") != history_id
                or chunk.get("part_index") != idx):
            raise ValueError("TRANSFER_ARCHIVE_PART_ID_INVALID")
        raw = base64.b64decode(encoded, validate=True)
        if (digest(raw) != item.get("sha256") or
            digest(raw) != chunk.get("part_sha256") or
            len(raw) != item.get("bytes") or len(raw) > PART_BYTES):
            raise ValueError("TRANSFER_ARCHIVE_CHUNK_INVALID")
        payloads.append((part_path, name, raw))
    reconstructed = b"".join(x[2] for x in payloads)
    if digest(reconstructed) != history_id:
        raise ValueError("TRANSFER_ARCHIVE_FULL_HASH_MISMATCH")
    decoded = json.loads(reconstructed)
    if (decoded.get("source_scope") != SOURCE_SCOPE or
        decoded.get("record_count") != len(decoded.get("records", [])) or
        decoded["record_count"] != manifest["record_count"]):
        raise ValueError("TRANSFER_ARCHIVE_RECORD_COUNT_INVALID")
    return manifest, payloads


def sync_transfer_history(spool: EvidenceSpool, publisher: GitEvidencePublisher) -> dict:
    """Independent flock, exact Git GET-after-PUT, durable retry on any failure."""
    spool.root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = spool.root / "transfer-sync.lock"
    with lock.open("a+") as file_lock:
        try:
            fcntl.flock(file_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "SYNC_BUSY", "uploaded": 0, "pending": -1}
        uploaded, errors = 0, []
        for path in sorted((spool.pending / KIND).glob("*.json")):
            try:
                manifest, chunks = _validated_parts(spool, path)
                ident = manifest["snapshot_id"]
                for part_path, name, _ in chunks:
                    publisher._upload(
                        f"{PREFIX}/{KIND}/{ident}/{name}", part_path.read_bytes())
                # Immutable manifest becomes visible only after all parts passed GET.
                publisher._upload(f"{PREFIX}/{KIND}/{path.name}", path.read_bytes())
                for part_path, _, _ in chunks:
                    part_path.unlink()
                path.unlink()
                uploaded += 1
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
                errors.append({"event": path.name, "error_type": type(exc).__name__})
        pending = len(list((spool.pending / KIND).glob("*.json")))
        return {"status": "SYNC_PARTIAL" if errors else
                "SYNC_PENDING" if pending else "SYNC_OK",
                "uploaded": uploaded, "pending": pending, "errors": errors}


def publish_evidence_batch(
    spool: EvidenceSpool, publisher: GitEvidencePublisher,
    frank_database: Path, capture_transfer: bool,
) -> dict:
    """Called exclusively on existing Mission Control background worker.

    A transfer-source error must not block original CA/Frank Git sync. The
    writer, original signals and Gmail never call this from their hot path.
    """
    capture = "NOT_REQUESTED"
    if capture_transfer:
        from .wallet_transfers import export_signature_evidence
        try:
            report = export_signature_evidence(frank_database)
            queue_transfer_history(spool, report)
            capture = "QUEUED_CONTENT_ADDRESSED"
        except (OSError, ValueError, RuntimeError, TypeError) as exc:
            capture = "SOURCE_UNAVAILABLE_" + type(exc).__name__
    try:
        core = publisher.sync()
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        core = {"status": "SYNC_PARTIAL", "error_type": type(exc).__name__}
    try:
        transfer = sync_transfer_history(spool, publisher)
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        transfer = {"status": "SYNC_PARTIAL", "error_type": type(exc).__name__}
    return {"capture": capture, "original": core, "transfer": transfer,
            "fully_synced": (core["status"] == "SYNC_OK"
                             and transfer["status"] == "SYNC_OK"
                             and (not capture_transfer or
                                  capture == "QUEUED_CONTENT_ADDRESSED"))}
