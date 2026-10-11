"""Opt-in Frank/CA evidence spool and independent GitHub publisher.

Never modifies the Frank ledger, alert, policy or live Git checkout.
Uses gh authenticated CLI; content is sent on stdin and verified after upload.
No provider key, local paths, email, credential, quote or RPC URLs are exported.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.parse import urlsplit, urlunsplit

REPO = "lxxlx2/ChatGPT_mission_record"
BRANCH = "evidence/frank-ca-local"
PREFIX = "crypto-300-profit-mission/meme/local-evidence"
PUBKEY = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
SAFE_ID = re.compile(r"^[a-f0-9]{16,64}$")
BANNED = re.compile(r"secret|password|passphrase|private|seed|bearer|authorization|cookie|credential|webhook|rpc_url|endpoint_url|gmail|email|local_path|home_dir|api[_-]?key|access_token|refresh_token|auth_token|^key$|_token$", re.I)
SENSITIVE_INLINE = re.compile(r"(?i)(bearer\s+[a-z0-9._~+/-]+|(?:api[_-]?key|token|password|secret)\s*[:=]\s*[^\s&,;]+)")
CA_FIELDS = ("schema_version", "mint", "source", "observed_at", "supply_raw", "decimals",
             "token_profile", "market", "assessment", "holders", "metrics",
             "confirmed_relation_groups", "probable_control_clusters",
             "probable_execution_clusters", "shared_infrastructure_exclusions",
             "unresolved_relation_edges", "edges", "funding_evidence",
             "consolidation_evidence", "trade_evidence", "transaction_errors",
             "coverage", "limitations")
MAX_CA_BYTES = 250_000
MAX_RECURSION = 14
MAX_ARRAY = 200000
MAX_TEXT = 3000
MAX_REMOTE_BYTES = 650_000


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe(value: object, level: int = 0) -> object:
    """Whitelist/scrub recursive data, never sending arbitrary source logs."""
    if level > MAX_RECURSION:
        return "[DEPTH_LIMIT]"
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if -1e308 < value < 1e308 else None
    if isinstance(value, str):
        if re.search(r"(?i)(?:^|[\\s=])/(?:Users|home)/[^\\s]+", value):
            return "[LOCAL_PATH_REDACTED]"
        if SENSITIVE_INLINE.search(value):
            return "[REDACTED]"
        if len(value) > MAX_TEXT:
            return "[TEXT_OVER_LIMIT]"
        if value.startswith(("https://", "http://")):
            try:
                u = urlsplit(value)
                if u.username or u.password or u.query or u.fragment:
                    return urlunsplit((u.scheme, u.hostname or "", u.path, "", ""))
            except ValueError:
                return "[URL_INVALID]"
        return value
    if isinstance(value, list):
        if len(value) > MAX_ARRAY:
            raise ValueError("SAFE_ARRAY_EXCEEDS_LIMIT")
        return [safe(x, level + 1) for x in value]
    if isinstance(value, dict):
        return {str(k): safe(v, level + 1) for k, v in value.items()
                if isinstance(k, str) and not BANNED.search(k) and len(k) <= 90}
    return "[TYPE_REDACTED]"


def atomic_new(path: Path, data: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError("EVENT_ID_COLLISION_DIFFERENT_CONTENT")
        return False
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return True


class EvidenceSpool:
    def __init__(self, root: Path):
        self.root = Path(root) / "git-evidence-spool"
        self.pending = self.root / "pending"
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def ca_done(self, *, mint: str, job_id: str, report: dict) -> Path:
        if not PUBKEY.fullmatch(mint) or not SAFE_ID.fullmatch(job_id):
            raise ValueError("INVALID_CA_OR_JOB_ID")
        if not isinstance(report, dict) or report.get("mint") != mint:
            raise ValueError("CA_REPORT_IDENTITY_MISMATCH")
        limited = {k: report[k] for k in CA_FIELDS if k in report}
        filtered = safe(limited)
        filtered_bytes = canonical(filtered)
        if len(filtered_bytes) > 8_000_000:
            raise ValueError("CA_SANITIZED_REPORT_OVER_8MB")
        exported = {
            "schema_version": 2, "kind": "ca", "job_id": job_id, "mint": mint,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "local_job_status": "DONE", "chain_completeness_verified": False,
            "coverage_provenance": "BOUNDED_OR_PARTIAL_UNLESS_INDEPENDENTLY_AUDITED",
            "selected_source_fields": list(limited),
            "sanitized_evidence_sha256": digest(filtered_bytes),
            "full_local_report_sha256": digest(canonical(report)),
        }
        if len(filtered_bytes) + 3000 < MAX_CA_BYTES:
            exported["data"] = filtered
            exported["data_chunks"] = []
            exported["export_completeness"] = "ALL_SELECTED_FIELDS_REDACTED"
        else:
            # Preserve *all* allowed sanitized research evidence, split into
            # stable, independently verifiable GitHub-readable JSON chunks.
            # A concise manifest remains human-readable in Git.
            included = ("schema_version", "mint", "source", "observed_at",
                        "supply_raw", "decimals", "assessment", "metrics", "coverage")
            exported["data"] = safe({k: limited[k] for k in included if k in limited})
            exported["data_chunks"] = []
            exported["export_completeness"] = "ALL_SELECTED_FIELDS_IN_CHUNKS"
            for i, offset in enumerate(range(0, len(filtered_bytes), 120_000)):
                payload = filtered_bytes[offset: offset + 120_000]
                filename = f"part-{i:04d}.json"
                segment = {
                    "schema_version": 1, "job_id": job_id,
                    "part_index": i, "part_sha256": digest(payload),
                    "payload_b64": base64.b64encode(payload).decode("ascii"),
                }
                dest = self.pending / "ca-parts" / job_id / filename
                atomic_new(dest, canonical(segment))
                exported["data_chunks"].append({
                    "file": filename, "part_index": i, "sha256": digest(payload),
                    "payload_bytes": len(payload),
                })
        raw = canonical(exported)
        if len(raw) > MAX_CA_BYTES:
            raise ValueError("CA_MANIFEST_OVER_LIMIT")
        dest = self.pending / "ca" / f"{job_id}.json"
        atomic_new(dest, raw)
        return dest

    def frank_history(self, report: dict) -> Path:
        """Queue a complete locally recognized historical trade report once.

        Each versioned snapshot is content-addressed and reconstructable. The
        sanitized normalizer is explicitly separate from chain completeness.
        """
        if (not isinstance(report, dict) or
            report.get("source_scope") != "COMPLETE_LOCAL_RECOGNIZED_TRADES_NOT_FULL_CHAIN" or
            report.get("person_id") != "frank" or
            not isinstance(report.get("records"), list)):
            raise ValueError("HISTORY_REPORT_SCHEMA_INVALID")
        cleaned = safe(report)
        blob = canonical(cleaned)
        if len(blob) > 8_000_000:
            raise ValueError("FRANK_HISTORY_OVER_8MB")
        if cleaned.get("record_count") != len(cleaned["records"]):
            raise ValueError("FRANK_HISTORY_RECORDS_WOULD_BE_TRUNCATED")
        history_id = digest(blob)
        parts = []
        for i, offset in enumerate(range(0, len(blob), 120_000)):
            section = blob[offset: offset + 120_000]
            name = f"part-{i:04d}.json"
            packet = {
                "schema_version": 1, "snapshot_id": history_id,
                "part_index": i, "part_sha256": digest(section),
                "payload_b64": base64.b64encode(section).decode("ascii"),
            }
            target = self.pending / "frank-history-parts" / history_id / name
            atomic_new(target, canonical(packet))
            parts.append({"file": name, "part_index": i,
                          "sha256": digest(section), "bytes": len(section)})
        manifest = {
            "schema_version": 1, "kind": "frank-history",
            "snapshot_id": history_id,
            "sanitized_content_sha256": history_id,
            "record_count": cleaned["record_count"],
            "source_scope": cleaned["source_scope"],
            "parts": parts,
            "chain_completeness_verified": False,
            "net_pnl_verified": False,
        }
        target = self.pending / "frank-history" / (history_id + ".json")
        atomic_new(target, canonical(manifest))
        return target

    def frank_scan(self, *, poll_count: int, health: dict, coverage: dict | None = None,
                   recent_trades: list[dict] | None = None,
                   signal_candidates: list[dict] | None = None,
                   observed_watchlist: dict | None = None) -> Path:
        if type(poll_count) is not int or poll_count < 0:
            raise ValueError("FRANK_POLL_COUNT_INVALID")
        if not isinstance(health, dict):
            raise ValueError("FRANK_HEALTH_INVALID")
        # Never export full health: can contain local paths and provider errors.
        allowed = ("status", "last_successful_poll", "last_model_successful_eval",
                   "last_chain_signature", "last_processed_signature",
                   "last_processed_slot", "new_signatures", "lag_seconds",
                   "model_unprocessed", "raw_pending", "local_pending",
                   "consecutive_errors", "policy_hash", "source_drift")
        h = {k: health.get(k) for k in allowed}
        cov = coverage or {}
        observed = str(health.get("last_poll_at") or health.get("last_successful_poll") or "")
        if not observed:
            raise ValueError("FRANK_POLL_TIMESTAMP_MISSING")
        # Use explicit, public-chain-safe fields only. Do not publish raw SQL
        # bodies, local credentials, full policies or provider exceptions.
        trade_fields = ("signature", "mint", "side", "block_time",
                        "observed_quote_asset", "observed_quote_quantity",
                        "token_quantity", "verified_fill_price_usdc",
                        "position_after_token")
        signal_fields = ("mint", "pattern", "source_signal_id",
                         "source_signal_type", "position_state", "latest_side",
                         "latest_signature", "latest_at", "buy_count", "sell_count")
        recent = [safe({k: row.get(k) for k in trade_fields})
                  for row in (recent_trades or [])[:40] if isinstance(row, dict)]
        signals = [safe({k: row.get(k) for k in signal_fields})
                   for row in (signal_candidates or [])[:60] if isinstance(row, dict)]
        raw_watch = observed_watchlist if isinstance(observed_watchlist, dict) else {}
        watch_rows = raw_watch.get("rows") if isinstance(raw_watch.get("rows"), list) else []
        public_watch_keys = (
            "mint", "watch_state", "inventory_evidence", "local_model_state",
            "local_current_raw", "local_recognized_buys", "local_recognized_sells",
            "last_event_time", "last_event_signature", "last_event_side",
            "origin_scope", "signature_activity_count", "passive_receipt_events",
            "signature_received_events", "signature_sent_events", "signature_zero_events",
            "last_signature_activity_time", "last_signature_activity_signature",
            "signature_observed_in_raw", "signature_observed_out_raw",
            "signature_token_amount_decimals", "transfer_counterparty_verified",
            "current_chain_balance_verified", "pnl_usd",
        )
        observed_rows = [
            safe({k: row.get(k) for k in public_watch_keys})
            for row in watch_rows[:300] if isinstance(row, dict)
        ]
        watch_meta = {
            "scope": "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
            "total_observed": (raw_watch.get("summary") or {}).get("total_observed"),
            "original_trade_or_model_observed": (raw_watch.get("summary") or {}).get("original_trade_or_model_observed"),
            "passive_receipt_only": (raw_watch.get("summary") or {}).get("passive_receipt_only"),
            "other_account_activity_only": (raw_watch.get("summary") or {}).get("other_account_activity_only"),
            "signature_activity_provenance": safe(raw_watch.get("signature_activity_provenance") or {}),
            "exported_count": len(observed_rows),
            "truncated": len(watch_rows) > 300,
            "rows": observed_rows,
        }
        envelope = {
            "schema_version": 1, "kind": "frank",
            "poll_count": poll_count, "captured_at_utc": observed,
            "source_status": "LOCAL_WRITER_HEALTH_READ_ONLY",
            "chain_completeness_verified": False,
            "health": safe(h),
            "coverage": safe({k: cov.get(k) for k in ("status", "scope", "windows",
                          "earliest_indexed_block_time", "latest_indexed_block_time",
                          "indexed_signatures_all_time")}),
            "recent_recognized_trades_sample": recent,
            "signal_eligible_candidates_sample": signals,
            "observed_watchlist": watch_meta,
            "trade_sample_scope": "LATEST_40_LOCALLY_CLASSIFIED_NOT_FULL_HISTORY",
        }
        stamp = observed
        try:
            dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)
        bucket = f"{dt:%Y-%m-%d}/{dt.hour:02d}{(dt.minute//15)*15:02d}"
        envelope["bucket_utc"] = bucket
        raw = canonical(envelope)
        identity = digest(canonical({"poll_count": poll_count, "checkpoint": h.get("last_processed_signature"),
                                     "success": h.get("last_successful_poll")}))[:20]
        dest = self.pending / "frank" / f"{poll_count:012d}-{identity}.json"
        if dest.is_file():
            return dest  # stable first capture for this verified writer poll
        atomic_new(dest, raw)
        return dest


class GitEvidencePublisher:
    def __init__(self, spool: EvidenceSpool, *, clock=time.time, gh="gh"):
        self.spool, self.clock, self.gh = spool, clock, gh

    def _gh(self, method: str, remote: str, payload: dict | None = None) -> dict | None:
        if not remote.startswith(PREFIX + "/") or ".." in remote.split("/"):
            raise ValueError("REMOTE_PATH_FORBIDDEN")
        api = "repos/" + REPO + "/contents/" + remote
        cmd = [self.gh, "api", "--method", method, "-H",
               "Accept: application/vnd.github+json", api]
        if method == "GET":
            cmd[-1] += "?ref=" + BRANCH
        if payload is not None:
            cmd += ["--input", "-"]
        try:
            result = subprocess.run(cmd, input=canonical(payload) if payload is not None else None,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=25, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("GH_TRANSPORT_UNAVAILABLE") from exc
        if result.returncode:
            # Never include subprocess stderr because it may contain secrets.
            if method == "GET" and b"HTTP 404" in result.stderr:
                return None
            raise RuntimeError("GH_API_" + method + "_FAILED")
        try:
            return json.loads(result.stdout)
        except (ValueError, UnicodeError) as exc:
            raise RuntimeError("GH_API_INVALID_RESPONSE") from exc

    def _remote(self, remote: str) -> tuple[bytes | None, str | None]:
        existing = self._gh("GET", remote)
        if existing is None:
            return None, None
        if existing.get("encoding") != "base64":
            raise RuntimeError("GH_CONTENT_ENCODING_UNSUPPORTED")
        try:
            content = base64.b64decode(existing["content"], validate=False)
        except (KeyError, ValueError) as exc:
            raise RuntimeError("GH_CONTENT_INVALID") from exc
        return content, existing["sha"]

    def _upload(self, remote: str, blob: bytes):
        if len(blob) > MAX_REMOTE_BYTES:
            raise ValueError("GIT_EVIDENCE_SIZE_LIMIT")
        for attempt in range(3):
            prior, sha = self._remote(remote)
            if prior == blob:
                return
            # The 15-minute Frank poll bucket is intentionally append/update
            # material. All other evidence URLs are immutable observations.
            # A divergent remote content-addressed file is a collision and
            # must never be overwritten, even with a valid GitHub blob SHA.
            mutable_frank_bucket = bool(re.fullmatch(
                re.escape(PREFIX) + r"/frank/\\d{4}-\\d{2}-\\d{2}/\\d{4}\\.json",
                remote,
            ))
            if sha and not mutable_frank_bucket:
                raise ValueError("IMMUTABLE_GIT_EVIDENCE_COLLISION")
            args = {"message": "evidence: update " + remote.removeprefix(PREFIX + "/"),
                    "content": base64.b64encode(blob).decode("ascii"), "branch": BRANCH}
            if sha:
                args["sha"] = sha
            try:
                self._gh("PUT", remote, args)
            except RuntimeError:
                if attempt == 2:
                    raise
                time.sleep(min(2 ** attempt, 4))
                continue
            received, _ = self._remote(remote)
            if received == blob:
                return
            if attempt == 2:
                raise RuntimeError("GH_READBACK_HASH_MISMATCH")
        raise RuntimeError("GH_READBACK_HASH_MISMATCH")

    def sync(self, *, force: bool = False) -> dict:
        self.spool.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = self.spool.root / "sync.lock"
        with lock_path.open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return {"status": "SYNC_BUSY", "uploaded": 0}
            sent = 0
            errors = []
            for p in sorted((self.spool.pending / "ca").glob("*.json")):
                try:
                    data = json.loads(p.read_text())
                    if p.stem != data["job_id"] or not SAFE_ID.fullmatch(p.stem):
                        raise ValueError("CA_SPOOL_IDENTITY_INVALID")
                    if not PUBKEY.fullmatch(str(data["mint"])):
                        raise ValueError("CA_MINT_INVALID")
                    parts = []
                    for chunk in data.get("data_chunks") or []:
                        name = chunk["file"]
                        if not re.fullmatch(r"part-\d{4}\.json", name):
                            raise ValueError("CA_PART_FILENAME_INVALID")
                        local = self.spool.pending / "ca-parts" / p.stem / name
                        encoded = json.loads(local.read_text())
                        payload = base64.b64decode(encoded["payload_b64"], validate=True)
                        if digest(payload) != chunk["sha256"]:
                            raise ValueError("CA_PART_HASH_INVALID")
                        parts.append((local, name))
                    for local, name in parts:
                        self._upload(f"{PREFIX}/ca/{data['mint']}/{p.stem}/{name}", local.read_bytes())
                    remote = f"{PREFIX}/ca/{data['mint']}/{p.name}"
                    # Manifest is the commit barrier: readers see its presence
                    # only after all associated part blobs were read-back verified.
                    self._upload(remote, p.read_bytes())
                    for local, _ in parts:
                        local.unlink()
                    p.unlink()
                    sent += 1
                except (ValueError, OSError, RuntimeError, KeyError) as exc:
                    errors.append({"kind": "ca", "event": p.name, "reason": type(exc).__name__})
            for p in sorted((self.spool.pending / "frank-history").glob("*.json")):
                try:
                    manifest = json.loads(p.read_text())
                    history_id = manifest.get("snapshot_id")
                    if not isinstance(history_id, str) or not SAFE_ID.fullmatch(history_id) or history_id != p.stem:
                        raise ValueError("FRANK_HISTORY_ID_INVALID")
                    part_files = []
                    for rec in manifest.get("parts") or []:
                        name = rec["file"]
                        if not re.fullmatch(r"part-\d{4}\.json", name):
                            raise ValueError("FRANK_HISTORY_PART_NAME_INVALID")
                        local = self.spool.pending / "frank-history-parts" / history_id / name
                        chunk = json.loads(local.read_text())
                        payload = base64.b64decode(chunk["payload_b64"], validate=True)
                        if digest(payload) != rec["sha256"]:
                            raise ValueError("FRANK_HISTORY_CHUNK_MISMATCH")
                        part_files.append((local, name))
                    for local, name in part_files:
                        self._upload(f"{PREFIX}/frank-history/{history_id}/{name}", local.read_bytes())
                    self._upload(f"{PREFIX}/frank-history/{p.name}", p.read_bytes())
                    for local, _ in part_files:
                        local.unlink()
                    p.unlink()
                    sent += 1
                except (ValueError, OSError, RuntimeError, KeyError) as exc:
                    errors.append({"kind": "frank-history", "event": p.name, "reason": type(exc).__name__})
            # Do not sync an open 15-minute bucket unless explicitly forced.
            current_bucket_start = int(self.clock() // 900) * 900
            groups: dict[str, list[tuple[Path, dict]]] = {}
            for p in sorted((self.spool.pending / "frank").glob("*.json")):
                try:
                    item = json.loads(p.read_text())
                    bucket = str(item["bucket_utc"])
                    dt = datetime.strptime(bucket, "%Y-%m-%d/%H%M").replace(tzinfo=timezone.utc)
                    if dt.timestamp() >= current_bucket_start and not force:
                        continue
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}/\d{4}", bucket):
                        raise ValueError("BAD_BUCKET")
                    groups.setdefault(bucket, []).append((p, item))
                except (KeyError, ValueError, OSError) as exc:
                    errors.append({"kind": "frank", "event": p.name, "reason": type(exc).__name__})
            for bucket, rows in sorted(groups.items()):
                remote = f"{PREFIX}/frank/{bucket}.json"
                try:
                    old, _ = self._remote(remote)
                    existing = json.loads(old)["events"] if old is not None else []
                    by_id = {str(z["poll_count"]): z for z in existing}
                    for _, row in rows:
                        key = str(row["poll_count"])
                        if key in by_id and by_id[key] != row:
                            raise ValueError("POLL_ID_DIFFERENT_EVIDENCE")
                        by_id[key] = row
                    events = sorted(by_id.values(), key=lambda x: x["poll_count"])
                    packet = {"schema_version": 1, "bucket_utc": bucket,
                              "record_count": len(events), "events": events}
                    self._upload(remote, canonical(packet))
                    for p, _ in rows:
                        p.unlink()
                        sent += 1
                except (KeyError, ValueError, OSError, RuntimeError) as exc:
                    errors.append({"kind": "frank", "bucket": bucket, "reason": type(exc).__name__})
            pending_ca = len(list((self.spool.pending / "ca").glob("*.json")))
            pending_frank = len(list((self.spool.pending / "frank").glob("*.json")))
            pending_history = len(list((self.spool.pending / "frank-history").glob("*.json")))
            status = ("SYNC_PARTIAL" if errors else
                      "SYNC_PENDING_WINDOW" if pending_ca or pending_frank or pending_history else "SYNC_OK")
            return {"status": status, "uploaded": sent, "errors": errors,
                    "pending_ca": pending_ca, "pending_frank": pending_frank,
                    "pending_history": pending_history,
                    "remote_branch": BRANCH}
