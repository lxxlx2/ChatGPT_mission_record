#!/usr/bin/env python3
"""Fail-closed forward recovery of the specific PR39 L30 macOS outage.

Default --plan is read-only; --apply requires all three explicit authorizations.
Never restarts the unverified legacy Loop, rewinds SQLite, or touches the Frank
scanner LaunchAgent. This is NOT the regular dual-service release flow.
"""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import getpass
import json
import os
from pathlib import Path
import plistlib
import re
import sqlite3
import subprocess
import sys
import time

import frank_pr39_controlled_release as rel

INCIDENT = "20261013T084832Z-legacy-55143"
TARGET = "52d43d18ee5a6d87408bc68d4832869fce8817a9"
ORIGINAL_RUNNERS = {
    "loop": "3e6ed819aab32f78d8d04462c24cdb02fcfd118dcc0986d4718f8be7e82750c7",
    "dashboard": "e0c38e6e4d0dd8177eb2f273a6292b0716f3e454f8c749af0de94d24954e4afc",
}
OLD_PIDS = {"loop": 79154, "dashboard": 25851}
SCANNER_PID = 52300
SCANNER_SOURCE = "599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce"
EXPECTED_SOURCE_FILE_COUNT = 148
PHASES = ["R00_VERIFIED_OFFLINE", "R10_BACKED_UP", "R20_MIGRATED",
          "R30_RUNNERS_SWITCHED", "R40_DASHBOARD_VERIFIED",
          "R50_LOOP_VERIFIED", "R60_SUCCESS"]
SCANNER_LABEL = lambda: f"gui/{os.getuid()}/com.jerson.crypto-monitor-frank-local"


def command(argv):
    return subprocess.run(argv, capture_output=True, text=True, timeout=15,
                          env={**os.environ, "LC_ALL": "C"})


def host_offline(mac):
    """No PID, orphan worker or KeepAlive restart path before the first write."""
    disabled = command(["/bin/launchctl", "print-disabled", f"gui/{os.getuid()}"])
    rel.require(disabled.returncode == 0, "DISABLED_REGISTRY_UNVERIFIED")
    for role in ("loop", "dashboard"):
        label = mac.labels[role]
        service = command(["/bin/launchctl", "print", label])
        rel.require(service.returncode != 0 and
                    ("Could not find service" in service.stderr or service.returncode == 113),
                    "AGENT_MAY_STILL_BE_LOADED")
        short = label.split("/")[-1]
        found = re.search(r'["\']?' + re.escape(short) +
                          r'["\']?\s*=>\s*disabled\b', disabled.stdout)
        rel.require(found is not None, "AGENT_NOT_DISABLED")
        plist = mac.home / "Library/LaunchAgents" / (short + ".plist")
        config = plistlib.loads(plist.read_bytes())
        rel.require(config.get("Label") == short and
                    config.get("ProgramArguments") == [str(mac.runners[role])] and
                    config.get("KeepAlive") is True and not config.get("EnvironmentVariables"),
                    "AGENT_PLIST_CHANGED")
        old = command(["/bin/ps", "-p", str(OLD_PIDS[role]), "-o", "pid="])
        rel.require(old.returncode != 0 or not old.stdout.strip(), "OLD_PID_PRESENT")
    processes = command(["/bin/ps", "-axo", "pid=,command="])
    rel.require(processes.returncode == 0, "PROCESS_INVENTORY_FAILED")
    workers = [line for line in processes.stdout.splitlines()
               if re.search(r"scripts/mission_meme_v1\.py\s+(?:loop|serve)\b", line)]
    rel.require(not workers, "MISSION_WORKER_PRESENT")
    return {"old_pids_absent": True, "no_worker": True,
            "both_launch_agents_disabled_and_unloaded": True}


def scanner_guard(mac, prod, baseline=None):
    """Identity alone cannot prove an alive, polling scanner or monotonic cursors."""
    snap = rel.legacy_scanner_snapshot(mac, SCANNER_LABEL(), prod)
    rel.require(snap["pid"] == SCANNER_PID and
                snap["loaded_source_sha256"] == SCANNER_SOURCE, "SCANNER_IDENTITY_DRIFT")
    if baseline is not None:
        rel.require(snap == baseline["identity"], "SCANNER_IDENTITY_CHANGED")
    rel.require(all(rel.sha(path) == value for path, value in snap["protected"].items()),
                "SCANNER_CONFIG_CHANGED")
    body = json.loads((Path(prod).parent / "health.json").read_text())
    stamp = datetime.fromisoformat(body["last_successful_poll"].replace("Z", "+00:00")).timestamp()
    rel.require(0 <= time.time() - stamp < 120 and body.get("status") == "RUNNING"
                and body.get("pid") == snap["pid"] and body.get("source_drift") is False
                and body.get("production_trading") == "NO_GO"
                and body.get("loaded_source_sha256") == snap["loaded_source_sha256"]
                and body.get("policy_hash") == snap["policy_hash"], "SCANNER_HEARTBEAT")
    with closing(rel.ro(prod)) as db:
        cursors = {r["wallet"]: dict(r) for r in db.execute("SELECT * FROM cursors")}
    rel.require(all(type(row["slot"]) is int for row in cursors.values()), "CURSOR_SLOT")
    if baseline is not None:
        old = baseline["cursors"]
        rel.require(cursors.keys() == old.keys(), "CURSOR_WALLET_CHANGED")
        for wallet, row in cursors.items():
            rel.require(row["slot"] >= old[wallet]["slot"], "CURSOR_REGRESSION")
            rel.require(row["slot"] != old[wallet]["slot"] or
                        row["signature"] == old[wallet]["signature"], "CURSOR_IDENTITY_CHANGED")
    return {"identity": snap, "cursors": cursors}


def worker_context(state):
    return {"new_agent": str(state["staged"]), "runtime": {
        key: {"agent": str(rel.field(text, "LOCAL_AGENT"))}
        for key, text in state["texts"].items()}}


def immutable_incident_backup(path):
    """Read stopped, completed SQLite backup without creating -shm/-wal sidecars.

    The journal's prestop backup was made using sqlite3.backup and integrity
    checked. Immutable opens are restricted to this sealed historical backup,
    NEVER the running control/Frank databases.
    """
    rel.require(Path(path).is_file(), "INCIDENT_BACKUP_MISSING")
    from urllib.parse import quote
    uri = "file:" + quote(str(Path(path).resolve()), safe="/") + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True, timeout=3)) as conn:
        conn.row_factory = sqlite3.Row
        rel.integrity(conn)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        result = {table: [dict(x) for x in
                          conn.execute("SELECT * FROM " + table + " ORDER BY rowid")]
                  for table in rel.TABLES}
        result["local_delivery_presentation"] = (
            [dict(x) for x in conn.execute(
                "SELECT * FROM local_delivery_presentation ORDER BY rowid")]
            if "local_delivery_presentation" in tables else [])
        return result


def read_only_plan(mac, root, tool_pin):
    """Live on-host inventory: no lock, staging, backup, journal or signal."""
    rel.require(sys.platform == "darwin", "ACTUAL_MAC_REQUIRED")
    rel.require(re.fullmatch("[a-f0-9]{40}", tool_pin or "") is not None, "TOOL_SHA_REQUIRED")
    repo = Path(rel.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"]))
    rel.require(rel.run(["git", "-C", str(repo), "rev-parse", "HEAD"]) == tool_pin, "TOOL_SHA_DRIFT")
    rel.require(not rel.run(["git", "-C", str(repo), "status", "--porcelain"]), "TOOL_WORKTREE_DIRTY")
    incident = mac.support / "pr39-releases" / INCIDENT
    path = incident / "journal.json"
    rel.require(path.is_file() and not path.is_symlink(), "INCIDENT_JOURNAL_MISSING")
    incident_doc = json.loads(path.read_text())
    rel.require(incident_doc.get("mode") == "LEGACY_CUTOVER"
                and incident_doc.get("expected") == TARGET
                and incident_doc.get("phase") == "LEGACY_MANUAL_RECOVERY_REQUIRED",
                "INCIDENT_IDENTITY_MISMATCH")
    done = [h.get("phase") for h in incident_doc.get("history", [])]
    rel.require(done == ["L00_RECHECKED", "L10_STAGED", "L20_PRESTOP_BACKED_UP",
                         "L25_FROZEN", "L30_HOLDS_SET",
                         "LEGACY_MANUAL_RECOVERY_REQUIRED"], "INCIDENT_PHASE_MISMATCH")
    rel.require(incident_doc.get("legacy_loop_pid") == OLD_PIDS["loop"]
                and incident_doc.get("dashboard_pid") == OLD_PIDS["dashboard"]
                and incident_doc.get("scanner_pid") == SCANNER_PID, "INCIDENT_PIDS_MISMATCH")
    recovery_dir = incident / "forward-recovery"
    rel.require(not (recovery_dir / "journal.json").exists(), "RECOVERY_ALREADY_ATTEMPTED")
    host = host_offline(mac)
    texts = {}
    for role in ("loop", "dashboard"):
        runner = mac.runners[role]
        saved = incident / ("legacy-loop-runner.before.sh" if role == "loop"
                            else "legacy-dashboard-runner.before.sh")
        rel.require(runner.is_file() and not runner.is_symlink()
                    and saved.is_file() and rel.sha(runner) == ORIGINAL_RUNNERS[role]
                    and runner.read_bytes() == saved.read_bytes(),
                    "ORIGINAL_RUNNER_CHANGED")
        texts[role] = runner.read_text(encoding="utf-8")
    staged = mac.support / "pr39-immutable-releases" / TARGET[:12]
    marker = staged / rel.RELEASE_MARKER
    rel.require(staged.is_dir() and not staged.is_symlink()
                and marker.is_file() and json.loads(marker.read_text()).get("expected") == TARGET,
                "IMMUTABLE_TARGET_IDENTITY")
    source = rel.release_manifest(staged)
    rel.require(len(source) == EXPECTED_SOURCE_FILE_COUNT and source == rel.source_manifest(root),
                "TARGET_PRODUCT_SOURCE_DIFFERENCE")
    rel.require(all(not (f.stat().st_mode & 0o222) for f in [staged, *staged.rglob("*")]),
                "IMMUTABLE_TARGET_WRITABLE")
    for key in ("PROD", "CONTROL_POINTER", "VENV", "RPC_FILE"):
        rel.require(rel.field(texts["loop"], key) == rel.field(texts["dashboard"], key),
                    "RUNNER_CONFIG_DIVERGENCE")
    policy = rel.field(texts["loop"], "POLICY")
    approved = rel.field(texts["loop"], "APPROVED_HASH_FILE")
    policy_sha = rel.sha(policy)
    rel.require(policy_sha == approved.read_text().strip()
                and policy_sha == rel.sha(staged / "config/follow_policy_v1.approved.json"),
                "POLICY_CHANGED")
    settings = json.loads(policy.read_text())
    rel.require(settings.get("status") == "FROZEN_APPROVED"
                and settings.get("live_delivery_approved") is True, "POLICY_NOT_APPROVED")
    control = Path(rel.field(texts["loop"], "CONTROL_POINTER").read_text().strip()).resolve()
    prod = rel.field(texts["loop"], "PROD") / "forward.sqlite"
    db = control / "mission-control.sqlite"
    rel.require(db.is_file() and prod.is_file() and db.resolve() != prod.resolve(),
                "DATABASE_BOUNDARY")
    with closing(rel.ro(prod)) as d:
        rel.integrity(d)
    before = rel.ledger(db)
    incident_backup = incident / "control-prestop.sqlite"
    from urllib.parse import quote
    saved_frank = (incident / "frank-prestop.sqlite").resolve()
    with closing(sqlite3.connect("file:" + quote(str(saved_frank), safe="/") +
                                 "?mode=ro&immutable=1", uri=True, timeout=3)) as d:
        rel.integrity(d)
    rel.assert_preserved(immutable_incident_backup(incident_backup), before, exact=True)
    rel.require(len(before["local_delivery_presentation"]) == 0, "UNEXPECTED_OLD_PRESENTATION_ROWS")
    reasons = rel.review_reasons(before)
    rel.require(reasons["requires_private_review"] == 0, "HISTORIC_SEND_UNRESOLVED")
    scanner_state = scanner_guard(mac, prod)
    scanner = scanner_state["identity"]
    rel.disk_gate(mac.support, (db, prod))
    port = int((control / "dashboard.port").read_text())
    rel.require(0 < port < 65536, "DASHBOARD_PORT")
    report = {"mode": "PR39_FORWARD_RECOVERY_PLAN", "gate": "FORWARD_RECOVERY_ELIGIBLE",
              "target_sha": TARGET, "verified_files": len(source),
              "old_workers_absent": host["no_worker"], "both_launch_agents_disabled": True,
              "scanner_pid": scanner["pid"],
              "queue_terminal": True, "manual_review_historical": reasons["manual_review_live"],
              "decision_events": len(before["decision_events"]),
              "gmail_delivery": len(before["gmail_delivery"]),
              "local_delivery": len(before["local_delivery"]),
              "deployment_authorized": False, "mutated_production": False}
    private = {"incident": incident, "recovery_dir": recovery_dir, "staged": staged,
               "source": source, "texts": texts, "control": control, "db": db, "prod": prod,
               "policy_sha": policy_sha, "scanner": scanner, "scanner_state": scanner_state, "queue": before, "port": port}
    return report, private


def write_record(path, body):
    rel.atomic(path, json.dumps(body, sort_keys=True).encode(), 0o600)


def forward_apply(mac, root, tool_pin):
    """Forward-only: old Loop never restarted; any failure leaves both disabled."""
    plan, state = read_only_plan(mac, root, tool_pin)
    folder = state["recovery_dir"]
    folder.mkdir(mode=0o700)
    journal = folder / "journal.json"
    doc = {"mode": "PR39_FORWARD_RECOVERY", "phase": "INIT",
           "target_sha": TARGET, "tool_sha": tool_pin, "history": [], "intent": None}
    write_record(journal, doc)
    def checkpoint(phase):
        rel.require(phase == PHASES[len(doc["history"])], "RECOVERY_PHASE_ORDER")
        doc["phase"] = phase
        doc["history"].append(phase)
        doc["intent"] = None
        write_record(journal, doc)
    def intent(action):
        doc["intent"] = action
        write_record(journal, doc)
    touched = False
    previous = rel.install_signal_handlers()
    try:
        checkpoint("R00_VERIFIED_OFFLINE")
        rel.backup(state["db"], folder / "control-recovery.sqlite")
        rel.backup(state["prod"], folder / "frank-recovery.sqlite")
        checkpoint("R10_BACKED_UP")
        rel.assert_preserved(state["queue"], rel.ledger(state["db"]), exact=True)
        state["scanner_state"] = scanner_guard(mac, state["prod"], state["scanner_state"])
        host_offline(mac)
        intent("MIGRATE_ONLY_PRESENTATION_TABLE")
        touched = True
        rel.migrate(state["db"])
        rel.assert_preserved(state["queue"], rel.ledger(state["db"]), exact=True)
        checkpoint("R20_MIGRATED")
        new_texts = {key: rel.replace_source(text, state["staged"])
                     for key, text in state["texts"].items()}
        intent("SWITCH_RUNNERS_WHILE_SERVICES_DISABLED")
        for key in ("dashboard", "loop"):
            rel.write_runner(mac.runners[key], new_texts[key])
        checkpoint("R30_RUNNERS_SWITCHED")
        rel.require(rel.release_manifest(state["staged"]) == state["source"],
                    "TARGET_CHANGED_PRE_START")
        host_offline(mac)
        intent("START_AND_VERIFY_DASHBOARD")
        mac.start("dashboard", str(mac.home / "Library/LaunchAgents" /
                                    (mac.labels["dashboard"].split("/")[-1] + ".plist")))
        dash = rel.wait_ready(lambda: mac.runtime("dashboard", new_texts["dashboard"]), 180)
        rel.require(dash["source"] == state["source"] and dash["pid"] != OLD_PIDS["dashboard"],
                    "NEW_DASHBOARD_SOURCE_UNVERIFIED")
        rel.wait_ready(lambda: rel.http_check({"port": state["port"],
                                                "new_agent": str(state["staged"])}, True), 60)
        checkpoint("R40_DASHBOARD_VERIFIED")
        state["scanner_state"] = scanner_guard(mac, state["prod"], state["scanner_state"])
        rel.require(rel.release_manifest(state["staged"]) == state["source"],
                    "TARGET_CHANGED_PRE_LOOP")
        rel.assert_preserved(state["queue"], rel.ledger(state["db"]), exact=True)
        mac.absent("loop")
        rel.require(set(mac.worker_pids(worker_context(state))) == {dash["pid"]},
                    "WORKER_PRESENT_BEFORE_LOOP_START")
        intent("START_AND_VERIFY_NEW_LOOP")
        start = time.time()
        mac.start("loop", str(mac.home / "Library/LaunchAgents" /
                              (mac.labels["loop"].split("/")[-1] + ".plist")))
        rel.wait_ready(lambda: rel.fresh(state["control"] / "mission-control-health.json",
                                          since=start, policy=state["policy_sha"]), 180)
        loop = rel.wait_ready(lambda: mac.runtime("loop", new_texts["loop"]), 60)
        rel.require(loop["source"] == state["source"] and loop["pid"] != OLD_PIDS["loop"],
                    "NEW_LOOP_SOURCE_UNVERIFIED")
        rel.assert_preserved(state["queue"], rel.ledger(state["db"]))
        state["scanner_state"] = scanner_guard(mac, state["prod"], state["scanner_state"])
        rel.require(set(mac.worker_pids(worker_context(state))) == {loop["pid"], dash["pid"]},
                    "RECOVERY_WORKER_SET_MISMATCH")
        rel.require(mac.runtime("dashboard", new_texts["dashboard"]) == dash and
                    mac.runtime("loop", new_texts["loop"]) == loop, "RECOVERY_RUNTIME_CHANGED")
        checkpoint("R50_LOOP_VERIFIED")
        checkpoint("R60_SUCCESS")
        return {"status": "FORWARD_RECOVERY_SUCCESS", "phase": doc["phase"],
                "loop_pid": loop["pid"], "dashboard_pid": dash["pid"],
                "scanner_pid": SCANNER_PID, "target_sha": TARGET}
    except BaseException as exc:
        # Prefer an outage to an unverified legacy restart or duplicate writer.
        errors = []
        for key in ("loop", "dashboard"):
            try:
                mac.hold(key)
            except BaseException:
                errors.append("HOLD_" + key.upper())
        # Loaded services can have no PID while KeepAlive is retrying. Always
        # attempt bootout, then independently prove absence and inspect workers.
        for key in ("loop", "dashboard"):
            try:
                mac.stop(key)
            except BaseException:
                pass
            try:
                mac.absent(key)
            except BaseException:
                errors.append("UNLOAD_" + key.upper())
        residual = None
        try:
            residual = mac.worker_pids(worker_context(state))
            mac.wait_dead(residual)
            residual = mac.worker_pids(worker_context(state))
            if residual:
                errors.append("RESIDUAL_WORKERS")
        except BaseException:
            errors.append("WORKER_EXIT_UNVERIFIED")
            try:
                residual = mac.worker_pids(worker_context(state))
            except BaseException:
                residual = None
        doc["phase"] = "RECOVERY_MANUAL_INTERVENTION_REQUIRED"
        doc["intent"] = None
        doc["error_kind"] = (str(exc) if isinstance(exc, RuntimeError) and
                             re.fullmatch("[A-Z_0-9]+", str(exc)) else type(exc).__name__)
        doc["cleanup_errors"] = errors
        doc["residual_worker_pids"] = residual
        doc["mutations_began"] = touched
        write_record(journal, doc)
        return {"status": "RECOVERY_BLOCKED", "phase": doc["phase"],
                "reason": doc["error_kind"], "cleanup_errors": errors,
                "residual_worker_pids": residual,
                "mutations_began": touched}
    finally:
        rel.restore_signal_handlers(previous)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-tool-sha", required=True)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--authorize-production-restart", action="store_true")
    ap.add_argument("--authorize-future-real-notifications", action="store_true")
    ap.add_argument("--authorize-legacy-unverified-loop-cutover", action="store_true")
    args = ap.parse_args(argv)
    rel.require(args.plan != args.apply, "EXACTLY_ONE_MODE_REQUIRED")
    if args.apply:
        rel.require(args.authorize_production_restart and args.authorize_future_real_notifications
                    and args.authorize_legacy_unverified_loop_cutover, "RECOVERY_AUTHORIZATION_REQUIRED")
    mac = rel.Mac()
    root = Path(__file__).resolve().parents[1]
    if args.plan:
        report, _ = read_only_plan(mac, root, args.expected_tool_sha)
        print(json.dumps(report, sort_keys=True))
        return 0
    base = mac.support / "pr39-releases"
    with (base / "release.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = forward_apply(mac, root, args.expected_tool_sha)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "FORWARD_RECOVERY_SUCCESS" else 6


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        reason = (str(exc) if isinstance(exc, RuntimeError) and
                  re.fullmatch("[A-Z_0-9]+", str(exc)) else type(exc).__name__)
        print(json.dumps({"gate": "RECOVERY_BLOCKED", "reason": reason}))
        sys.exit(3)
