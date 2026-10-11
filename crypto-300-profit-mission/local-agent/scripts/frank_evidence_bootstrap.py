#!/usr/bin/env python3
"""One-shot read-only Mac Frank/CA packet; optional verified Git sync.

This does not install, launch, stop, update or reconfigure a monitoring service.
It exports sanitized scan/CA artifacts plus an explicit D0 local coverage audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import zipfile

from mission_agent.mission_control.evidence_sync import EvidenceSpool, GitEvidencePublisher
from scripts.meme_evidence_sync import capture_frank
from scripts.frank_wallet_d0_snapshot import report as d0_report
from mission_agent.mission_control.wallet_history import export_history
from mission_agent.mission_control.wallet_watch import from_seed
from mission_agent.mission_control.wallet_inventory import InventoryEvidenceError, reconcile_watchlist
from mission_agent.mission_control.wallet_reconciliation import analyze as analyze_frank_gap
from mission_agent.mission_control.wallet_transfers import export_signature_evidence
from mission_agent.mission_control.transfer_archive import queue_transfer_history, sync_transfer_history


def refresh_zip_summary(packet: Path, status: dict) -> None:
    """Atomically reflect final Git upload state inside the portable ZIP."""
    tmp = packet.with_name(packet.name + ".summary-tmp")
    try:
        with zipfile.ZipFile(packet, "r") as source, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dest:
            for item in source.infolist():
                if item.filename != "summary.json":
                    dest.writestr(item, source.read(item.filename))
            dest.writestr("summary.json", json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
        os.replace(tmp, packet)
    finally:
        tmp.unlink(missing_ok=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--production-root", required=True, type=Path)
    p.add_argument("--control-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--sync", action="store_true", help="Attempt GitHub upload via existing authenticated gh CLI")
    p.add_argument("--inventory-evidence", type=Path, default=None,
                   help="Optional dated finalized RPC JSON; read-only research join, NOT live inventory")
    args = p.parse_args(argv)
    spool = EvidenceSpool(args.control_root)
    status = {"status": "READONLY_BOOTSTRAP", "frank": "NOT_STARTED",
              "ca_queued": 0, "ca_errors": [], "git_sync": "NOT_REQUESTED"}
    data = {}
    try:
        data["frank_capture"] = capture_frank(spool, args.production_root)
        status["frank"] = "QUEUED"
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        status["frank"] = "UNAVAILABLE_" + type(exc).__name__
    try:
        data["d0_local_audit"] = d0_report(args.production_root / "forward.sqlite", int(time.time()))
    except (OSError, ValueError) as exc:
        status["d0_audit"] = "UNAVAILABLE_" + type(exc).__name__
    try:
        data["frank_full_local_history"] = export_history(args.production_root / "forward.sqlite")
        spool.frank_history(data["frank_full_local_history"])
        status["frank_history"] = "QUEUED_LOCALLY"
        status["frank_history_records"] = data["frank_full_local_history"]["record_count"]
    except (OSError, ValueError, sqlite3.Error) as exc:
        status["frank_history"] = "UNAVAILABLE_" + type(exc).__name__
    try:
        transfer_report = export_signature_evidence(args.production_root / "forward.sqlite")
        queue_transfer_history(spool, transfer_report)
        status["frank_transfer_history"] = "QUEUED_LOCALLY"
        status["frank_transfer_signature_records"] = transfer_report["record_count"]
    except (OSError, ValueError, sqlite3.Error, TypeError) as exc:
        status["frank_transfer_history"] = "UNAVAILABLE_" + type(exc).__name__
    if args.inventory_evidence is not None:
        try:
            if "d0_local_audit" not in data:
                raise InventoryEvidenceError("FRANK_WATCH_SOURCE_MISSING")
            proof = json.loads(args.inventory_evidence.read_text(encoding="utf-8"))
            model = from_seed(data["d0_local_audit"]["watch_seed"])
            data["inventory_reconciliation"] = reconcile_watchlist(model, proof)
            if "frank_full_local_history" in data:
                data["local_trade_inventory_gap_audit"] = analyze_frank_gap(
                    data["frank_full_local_history"], proof)
                status["local_trade_inventory_gap_audit"] = "LOCALLY_ANALYZED_NO_PNL"
            status["inventory_reconciliation"] = "DATED_POINT_IN_TIME_NOT_LIVE"
            status["inventory_mints_checked"] = data["inventory_reconciliation"]["snapshot_reconciliation"]["matched_mints"]
        except (OSError, ValueError, InventoryEvidenceError, TypeError) as exc:
            status["inventory_reconciliation"] = "UNAVAILABLE_" + type(exc).__name__
    reports = args.control_root / "cluster-reports"
    if reports.is_dir():
        for filename in sorted(reports.glob("*/latest.json")):
            mint = filename.parent.name
            try:
                raw = filename.read_bytes()
                job_id = hashlib.sha256(mint.encode() + b"\x00" + raw).hexdigest()
                payload = json.loads(raw)
                spool.ca_done(mint=mint, job_id=job_id, report=payload)
                status["ca_queued"] += 1
            except (OSError, ValueError, KeyError) as exc:
                # No private path or source exception message is written.
                status["ca_errors"].append({"mint": mint if len(mint) < 46 else "[INVALID]",
                                            "error_type": type(exc).__name__})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Create the portable packet *before* syncing, since confirmed uploads
    # correctly remove their corresponding local pending files.
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("summary.json", json.dumps(status, indent=2, sort_keys=True))
        if "d0_local_audit" in data:
            archive.writestr("frank-d0-local-index.json",
                             json.dumps(data["d0_local_audit"], ensure_ascii=False, indent=2))
        if "inventory_reconciliation" in data:
            archive.writestr("frank-inventory-dated-reconciliation.json",
                             json.dumps(data["inventory_reconciliation"], ensure_ascii=False, indent=2))
        if "local_trade_inventory_gap_audit" in data:
            archive.writestr("frank-local-trade-inventory-gap-audit.json",
                             json.dumps(data["local_trade_inventory_gap_audit"],
                                        ensure_ascii=False, indent=2))
        for folder in ("ca", "ca-parts", "frank", "frank-history", "frank-history-parts", "frank-transfer-history", "frank-transfer-history-parts"):
            for source in sorted((spool.pending / folder).rglob("*.json")):
                archive.write(source, "sanitized-pending/" + source.relative_to(spool.pending).as_posix())
    if args.sync:
        if not shutil.which("gh"):
            status["git_sync"] = "GH_CLI_MISSING_PENDING_RETAINED"
        else:
            try:
                authenticated = subprocess.run(["gh", "auth", "status"],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                               timeout=10, check=False).returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                authenticated = False
            if authenticated:
                try:
                    publisher = GitEvidencePublisher(spool)
                    data["git_sync_result"] = publisher.sync(force=True)
                    transfer_result = sync_transfer_history(spool, publisher)
                    status["transfer_git_sync"] = transfer_result["status"]
                    status["transfer_remote_uploaded"] = transfer_result["uploaded"]
                    status["transfer_pending"] = transfer_result["pending"]
                    status["git_sync"] = (
                        "SYNC_OK" if data["git_sync_result"]["status"] == "SYNC_OK"
                        and transfer_result["status"] == "SYNC_OK"
                        and status.get("frank_transfer_history") == "QUEUED_LOCALLY"
                        and status.get("frank_history") == "QUEUED_LOCALLY"
                        and status.get("frank") == "QUEUED"
                        and not status.get("ca_errors")
                        and not str(status.get("d0_audit", "")).startswith("UNAVAILABLE_")
                        and (args.inventory_evidence is None
                             or status.get("inventory_reconciliation") == "DATED_POINT_IN_TIME_NOT_LIVE")
                        else "SYNC_PARTIAL"
                    )
                except (OSError, ValueError, RuntimeError):
                    status["git_sync"] = "GIT_SYNC_FAILED_PENDING_RETAINED"
            else:
                status["git_sync"] = "GH_AUTH_UNAVAILABLE_PENDING_RETAINED"
    refresh_zip_summary(args.output, status)
    receipt = args.output.with_suffix(".status.json")
    receipt.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"packet": str(args.output), "status_file": str(receipt),
                      "state": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "BOOTSTRAP_FAILED", "error_class": type(exc).__name__}),
              file=sys.stderr)
        sys.exit(2)
