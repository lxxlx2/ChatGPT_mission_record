"""No live Mac launchd, Gmail provider or production database I/O in these tests."""
import importlib.util
from pathlib import Path
import sqlite3
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/frank_loop_only_rollout_20261012.py"
SPEC = importlib.util.spec_from_file_location("frank_loop_only_rollout_ops", SCRIPT)
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)


def test_loop_runner_exact_agent_replacement_and_export_explicit_off(tmp_path):
    original = """#!/bin/bash
set -euo pipefail
LOCAL_AGENT="/old/crypto-300-profit-mission/local-agent"
PROD="/live/data"
RPC_FILE="/home/rpc"
exec env PYTHONPATH=. "/venv/python" scripts/mission_meme_v1.py loop --live-delivery
"""
    old = Path("/old/crypto-300-profit-mission/local-agent")
    new = Path("/release/crypto-300-profit-mission/local-agent")
    changed = ops.runner_with_new_agent(original, old, new)
    assert changed.count('LOCAL_AGENT="' + str(new) + '"') == 1
    assert changed.count('export MISSION_EVIDENCE_EXPORT_ENABLED=0') == 1
    assert 'RPC_FILE="/home/rpc"' in changed
    assert 'PROD="/live/data"' in changed
    assert "--live-delivery" in changed
    assert changed.replace("export MISSION_EVIDENCE_EXPORT_ENABLED=0\n", "", 1).replace(
        'LOCAL_AGENT="' + str(new) + '"', 'LOCAL_AGENT="' + str(old) + '"', 1) == original


def test_existing_export_override_fails_closed():
    original = (
        'LOCAL_AGENT="/old"\n'
        'export MISSION_EVIDENCE_EXPORT_ENABLED=1\n'
        'exec env PYTHONPATH=. x\n'
    )
    with pytest.raises(RuntimeError, match="NO_EXISTING_EXPORT_OVERRIDE"):
        ops.runner_with_new_agent(original, Path("/old"), Path("/new"))


def test_missing_or_duplicate_local_agent_binding_never_rewritten():
    for source in (
        'PROD="/p"\nexec env PYTHONPATH=. x',
        'LOCAL_AGENT="/old"\nLOCAL_AGENT="/old"\nexec env PYTHONPATH=. x',
    ):
        with pytest.raises(RuntimeError):
            ops.runner_with_new_agent(source, Path("/old"), Path("/new"))


def test_legacy_receipts_unchanged_allows_new_decision_rows():
    original = {
        "gmail_delivery": {"legacy-a": "MANUAL_REVIEW", "legacy-b": "SENT_VERIFIED"},
        "local_delivery": {"legacy-a": "COMMAND_ACCEPTED"},
    }
    after = {
        "gmail_delivery": dict(original["gmail_delivery"], **{"brand-new": "PENDING"}),
        "local_delivery": dict(original["local_delivery"], **{"brand-new": "PENDING"}),
    }
    ops.assert_legacy_receipts_unchanged(original, after)


@pytest.mark.parametrize("channel", ["gmail_delivery", "local_delivery"])
def test_legacy_receipt_state_change_or_deletion_hard_blocks(channel):
    original = {
        "gmail_delivery": {"legacy-a": "MANUAL_REVIEW"},
        "local_delivery": {"legacy-b": "COMMAND_ACCEPTED"},
    }
    changed = {k: dict(v) for k, v in original.items()}
    key = next(iter(changed[channel]))
    changed[channel][key] = "PENDING"
    with pytest.raises(RuntimeError, match="LEGACY_TERMINAL_REGRESSED"):
        ops.assert_legacy_receipts_unchanged(original, changed)
    del changed[channel][key]
    with pytest.raises(RuntimeError, match="LEGACY_DELIVERY_ROW_MISSING"):
        ops.assert_legacy_receipts_unchanged(original, changed)


def test_reads_only_complete_receipt_states_with_synthetic_db(tmp_path):
    db_path = tmp_path / "control.sqlite"
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE gmail_delivery (decision_id TEXT, status TEXT)")
        db.execute("CREATE TABLE local_delivery (decision_id TEXT, status TEXT)")
        db.execute("INSERT INTO gmail_delivery VALUES('a','MANUAL_REVIEW')")
        db.execute("INSERT INTO local_delivery VALUES('b','COMMAND_ACCEPTED')")
    result = ops.delivery_state(db_path)
    assert result == {
        "gmail_delivery": {"a": "MANUAL_REVIEW"},
        "local_delivery": {"b": "COMMAND_ACCEPTED"}
    }
    with sqlite3.connect(db_path) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_atomic_runner_is_no_old_path_leak_and_preserves_mode(tmp_path):
    target = tmp_path / "mission-loop.sh"
    target.write_bytes(b"old")
    ops.atomic_runner(target, b"new", 0o700)
    assert target.read_bytes() == b"new"
    assert target.stat().st_mode & 0o777 == 0o700


def test_actual_restart_requires_both_explicit_switch_and_alert_acknowledgment():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"--apply-loop"' in source
    assert '"--approve-fresh-alerts"' in source
    assert "not args.apply_loop or args.approve_fresh_alerts" in source
    assert "FRESH_LOOP_PREFLIGHT=PASS" in source
    assert 'loop_restart()' in source
    assert "GMAIL_SEND_INITIATED=NO" in source
    assert "LEGITIMATE_NEW_ALERTS=ALLOWED_BY_EXISTING_APPROVED_POLICY" in source
    assert "MISSION_EVIDENCE_EXPORT_ENABLED=0" in source
    assert '"kickstart", "-k", LOOP_LABEL' in source
    assert '"kickstart", "-k", DASH_LABEL' not in source
    assert "sqlite_backup(" in source
    assert "old_control = " not in source


def test_invalid_preflight_blob_hard_blocks_before_any_execution(tmp_path, monkeypatch):
    p = tmp_path / "preflight.py"
    p.write_text("raise SystemExit('should not execute')", encoding="utf-8")
    monkeypatch.setattr(ops, "CHECK_BLOB", "0" * 40)
    with patch.object(ops.subprocess, "run") as run:
        with pytest.raises(RuntimeError, match="PREFLIGHT_EXACT_GIT_BLOB"):
            ops.run_strict_preflight(p, Path("/usr/bin/python3"))
        run.assert_not_called()



def test_forward_progress_accepted_in_real_delivery_states(capsys):
    original = {
        "gmail_delivery": {"g1": "PENDING", "g2": "SENDING", "g3": "MANUAL_REVIEW"},
        "local_delivery": {"l1": "RETRY_PENDING", "l2": "COMMAND_ACCEPTED"},
    }
    after = {
        "gmail_delivery": {"g1": "SENT_VERIFIED", "g2": "SENT_UNVERIFIED", "g3": "MANUAL_REVIEW"},
        "local_delivery": {"l1": "COMMAND_ACCEPTED", "l2": "COMMAND_ACCEPTED"},
    }
    ops.assert_legacy_receipts_unchanged(original, after)
    assert "LEGACY_DELIVERY_PROGRESS_OBSERVED=3" in capsys.readouterr().out


def test_rollback_gate_blocks_old_expired_pending_but_not_fresh(tmp_path):
    from datetime import datetime, timedelta, timezone
    path = tmp_path / "delivery.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
          CREATE TABLE decision_events(decision_id TEXT, created_at TEXT);
          CREATE TABLE gmail_delivery(decision_id TEXT, status TEXT);
          CREATE TABLE local_delivery(decision_id TEXT, status TEXT);
        """)
        now = datetime.now(timezone.utc)
        old = (now - timedelta(seconds=800)).isoformat()
        recent = (now - timedelta(seconds=40)).isoformat()
        db.executemany("INSERT INTO decision_events VALUES(?,?)",
                       (("old", old), ("fresh", recent), ("uncertain", old),
                        ("l_old", old), ("l_fresh", recent)))
        db.executemany("INSERT INTO gmail_delivery VALUES(?,?)",
                       (("old", "PENDING"), ("fresh", "PENDING"),
                        ("uncertain", "SENDING")))
        db.executemany("INSERT INTO local_delivery VALUES(?,?)",
                       (("l_old", "RETRY_PENDING"), ("l_fresh", "PENDING")))
    assert ops.legacy_stale_sendable_count(path) == 2
    with pytest.raises(RuntimeError, match="LEGACY_ROLLBACK_STALE_GATE"):
        ops.confirm_rollback_safe(path)


def test_rollback_gate_fails_closed_on_missing_or_unreadable_db(tmp_path, capsys):
    absent = tmp_path / "absent.sqlite"
    with pytest.raises(RuntimeError, match="ROLLBACK_LEGACY_STATE_UNREADABLE"):
        ops.confirm_rollback_safe(absent)
    assert "OLD_LOOP_ROLLBACK=BLOCKED_UNREADABLE_DELIVERY_STATE" in capsys.readouterr().out


def test_rollback_gate_missing_invalid_or_future_time_is_unsafe(tmp_path):
    path = tmp_path / "delivery.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
          CREATE TABLE decision_events(decision_id TEXT, created_at TEXT);
          CREATE TABLE gmail_delivery(decision_id TEXT, status TEXT);
          CREATE TABLE local_delivery(decision_id TEXT, status TEXT);
        """)
        db.executemany("INSERT INTO decision_events VALUES(?,?)",
                       (("unparsed","no-date"),("future","2099-01-01T00:00:00Z"),
                        ("naive","2026-10-12T01:02:03")))
        db.executemany("INSERT INTO gmail_delivery VALUES(?,?)",
                       (("unparsed","RETRYABLE_ERROR"),("future","CREDENTIAL_BLOCKED")))
        db.execute("INSERT INTO local_delivery VALUES('naive','RETRY_PENDING')")
    assert ops.legacy_stale_sendable_count(path) == 3


def test_live_old_loop_blocks_new_pid_success(monkeypatch):
    monkeypatch.setattr(ops, "WAIT_SECONDS", 2)
    monkeypatch.setattr(ops, "launch_pid", lambda label: 2222)
    monkeypatch.setattr(ops, "process_alive", lambda pid: pid == 1111)
    monkeypatch.setattr(ops.time, "sleep", lambda _: None)
    with pytest.raises(RuntimeError, match="OLD_LOOP_PROCESS_STILL_ALIVE"):
        ops.wait_for_new_loop(1111, Path("/fake-control"), 123.0)


def test_stale_heartbeat_never_proves_new_pid_health(monkeypatch):
    monkeypatch.setattr(ops, "WAIT_SECONDS", 3)
    monkeypatch.setattr(ops, "launch_pid", lambda label: 2222)
    monkeypatch.setattr(ops, "process_alive", lambda pid: False)
    monkeypatch.setattr(ops.time, "sleep", lambda _: None)
    seen = []
    def stale_hb(control, *, since=None):
        seen.append(since)
        raise RuntimeError("HEARTBEAT_AFTER_NEW_LOOP_START=BLOCKED")
    monkeypatch.setattr(ops, "heartbeat", stale_hb)
    with pytest.raises(RuntimeError, match="NEW_LOOP_ALIVE_HEARTBEAT_NOT_OBSERVED"):
        ops.wait_for_new_loop(1111, Path("/fake-control"), 123.0)
    assert len(seen) == 3
    assert len(set(seen)) == 1


def test_new_heartbeat_after_old_exited_is_required(monkeypatch):
    monkeypatch.setattr(ops, "WAIT_SECONDS", 4)
    monkeypatch.setattr(ops, "launch_pid", lambda label: 2222)
    monkeypatch.setattr(ops, "process_alive", lambda pid: False)
    monkeypatch.setattr(ops.time, "sleep", lambda _: None)
    seen = []
    def fresh_hb(control, *, since=None):
        seen.append(since)
        if len(seen) < 2:
            raise RuntimeError("HEARTBEAT_NOT_YET_NEW")
        return {"status": "OK"}
    monkeypatch.setattr(ops, "heartbeat", fresh_hb)
    pid, state = ops.wait_for_new_loop(1111, Path("/fake-control"), 123.0)
    assert pid == 2222 and state["status"] == "OK"
    assert len(seen) == 2
    assert seen[0] == seen[1]


def test_sigterm_handler_raises_catchable_keyboard_interrupt():
    with pytest.raises(KeyboardInterrupt):
        ops.interrupted(15, None)


def test_signal_code_files_captured_by_expected_scope():
    assert "mission_agent/mission_control/policy.py" in ops.SIGNAL_FILES
    assert "mission_agent/signals/classifier.py" in ops.SIGNAL_FILES
    assert "mission_agent/signals/engine.py" in ops.SIGNAL_FILES
    assert "mission_agent/signals/evaluator.py" in ops.SIGNAL_FILES
    assert ops.WAIT_SECONDS >= 600
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"--approve-signal-code-change"' in source
    assert "SIGNAL_CODE_DELTA_EXPLICITLY_APPROVED" in source
    assert "except BaseException:" in source
    assert "signal.signal(signal.SIGTERM, previous_sigterm)" in source



def test_legacy_delivery_auto_rollback_requires_identical_version(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    rel = Path("mission_agent/mission_control/delivery.py")
    (old / rel).parent.mkdir(parents=True)
    (new / rel).parent.mkdir(parents=True)
    (old / rel).write_bytes(b"safe-stale-age-guard-fixture")
    (new / rel).write_bytes(b"safe-stale-age-guard-fixture")
    assert ops.legacy_delivery_code_verified(old, new) is True
    (old / rel).write_bytes(b"legacy-expired-mail-can-send")
    assert ops.legacy_delivery_code_verified(old, new) is False
    (old / rel).unlink()
    assert ops.legacy_delivery_code_verified(old, new) is False


def test_old_process_status_unavailable_never_proves_exit(monkeypatch):
    monkeypatch.setattr(ops.os, "kill", lambda pid, sig: None)
    with patch.object(ops.subprocess, "run", return_value=type(
        "Result", (), {"returncode": 1, "stdout": ""})()):
        with pytest.raises(RuntimeError, match="PROCESS_LIVENESS_UNVERIFIED"):
            ops.process_alive(1111)


def test_only_process_lookup_error_means_pid_is_absent(monkeypatch):
    def missing(pid, sig):
        raise ProcessLookupError()
    monkeypatch.setattr(ops.os, "kill", missing)
    assert ops.process_alive(1111) is False
    with pytest.raises(RuntimeError, match="PID_IDENTITY_UNVERIFIED"):
        ops.process_alive(-1)



def _fake_mac_rollout(tmp_path, monkeypatch, *, mode="success",
                      change_signal=False, legacy_safe=True, apply=True,
                      approve_signal=False):
    """Run real main/atomic-runner against fake HOME and fake launchd.

    The only SQLite backup writes fake fixture bytes. It never invokes a
    provider, network, real Mac LaunchAgent or live databases.
    """
    app = tmp_path / "Library" / "Application Support" / "FrankMeme"
    app.mkdir(parents=True)
    old_file = app / "mission-loop.sh"
    dash_file = app / "dashboard.sh"
    old_file.write_bytes(b"OLD_RUNNER_EXACT_BYTES\n")
    dash_file.write_bytes(b"DASHBOARD_PRESERVED\n")
    monkeypatch.setattr(ops, "SUPPORT", app)
    monkeypatch.setattr(ops, "BACKUPS", app / "release-backups")
    monkeypatch.setattr(ops, "LOOP_RUNNER", old_file)
    monkeypatch.setattr(ops, "DASH_RUNNER", dash_file)
    original_sha = ops.file_sha256(old_file)
    dash_sha = ops.file_sha256(dash_file)
    ctx = {
        "original": "OLD_RUNNER_EXACT_BYTES\n",
        "original_bytes": b"OLD_RUNNER_EXACT_BYTES\n",
        "candidate": "CANDIDATE_RUNNER\n",
        "old_sha": "1"*40,
        "changed_signal_files": ["mission_agent/mission_control/policy.py"]
            if change_signal else [],
        "legacy_delivery_verified": legacy_safe,
        "db": tmp_path / "private" / "control.sqlite",
        "prod": tmp_path / "private" / "forward.sqlite",
        "control": tmp_path / "private",
        "loop_pid": 111,
        "dashboard_pid": 444,
        "dashboard_sha": dash_sha,
        "runner_sha": original_sha,
        "mode": 0o700,
    }
    monkeypatch.setattr(ops, "prepare", lambda args: ctx)
    monkeypatch.setattr(ops, "sqlite_backup",
                        lambda src, dest: dest.write_bytes(b"CONSISTENT_FIXTURE_BACKUP"))
    monkeypatch.setattr(ops, "delivery_state", lambda path: {
        "gmail_delivery": {"one": "MANUAL_REVIEW"},
        "local_delivery": {"one": "COMMAND_ACCEPTED"},
    })
    monkeypatch.setattr(ops, "confirm_rollback_safe", lambda path: None)
    runtime = {"pid": 111, "restarts": 0, "wait_calls": []}
    def restart():
        runtime["restarts"] += 1
        runtime["pid"] = 222 if runtime["restarts"] == 1 else 333
        if mode in ("crash", "interrupt") and runtime["restarts"] == 1:
            runtime["pid"] = None
    monkeypatch.setattr(ops, "loop_restart", restart)
    def pid(label):
        if label == ops.DASH_LABEL:
            return 444
        if runtime["pid"] is None:
            raise RuntimeError("NO_RUNNING_LOOP")
        return runtime["pid"]
    monkeypatch.setattr(ops, "launch_pid", pid)
    monkeypatch.setattr(ops, "process_alive", lambda pid: (
        mode == "no-heartbeat" and pid == 222
    ))
    def wait(old_pid, control, started_at):
        runtime["wait_calls"].append(old_pid)
        if runtime["restarts"] == 1:
            if mode == "interrupt":
                raise KeyboardInterrupt("OPERATOR_CONTROL_C")
            if mode == "crash":
                raise RuntimeError("NEW_LOOP_NOT_RUNNING")
            if mode == "no-heartbeat":
                raise RuntimeError("NEW_LOOP_ALIVE_HEARTBEAT_NOT_OBSERVED")
            return (222, {"status": "OK"})
        return (333, {"status": "OK"})
    monkeypatch.setattr(ops, "wait_for_new_loop", wait)
    argv = [str(SCRIPT), "--preflight-script", str(tmp_path / "noop")]
    if apply:
        argv += ["--apply-loop", "--approve-fresh-alerts"]
    if approve_signal:
        argv += ["--approve-signal-code-change"]
    monkeypatch.setattr("sys.argv", argv)
    return old_file, dash_file, runtime


def test_end_to_end_prepare_never_restarts_or_rewrites_runner(tmp_path, monkeypatch, capsys):
    loop, dash, trace = _fake_mac_rollout(tmp_path, monkeypatch, apply=False)
    ops.main()
    assert trace["restarts"] == 0
    assert loop.read_bytes() == b"OLD_RUNNER_EXACT_BYTES\n"
    assert dash.read_bytes() == b"DASHBOARD_PRESERVED\n"
    assert "LOOP_SWITCH=NOT_ATTEMPTED_DRY_RUN" in capsys.readouterr().out


def test_end_to_end_success_switches_only_loop_runner(tmp_path, monkeypatch, capsys):
    loop, dash, trace = _fake_mac_rollout(tmp_path, monkeypatch)
    ops.main()
    assert trace["restarts"] == 1
    assert trace["wait_calls"] == [111]
    assert loop.read_bytes() == b"CANDIDATE_RUNNER\n"
    assert dash.read_bytes() == b"DASHBOARD_PRESERVED\n"
    assert "LOOP_RELEASE=SUCCESS_NEW_PID_VERIFIED" in capsys.readouterr().out


def test_end_to_end_existing_successor_without_heartbeat_never_rolls_back(tmp_path, monkeypatch, capsys):
    loop, dash, trace = _fake_mac_rollout(tmp_path, monkeypatch, mode="no-heartbeat")
    with pytest.raises(RuntimeError, match="NEW_LOOP_ALIVE_HEARTBEAT_NOT_OBSERVED"):
        ops.main()
    assert trace["restarts"] == 1
    assert loop.read_bytes() == b"CANDIDATE_RUNNER\n"
    assert dash.read_bytes() == b"DASHBOARD_PRESERVED\n"
    assert "ROLLBACK=MANUAL_NEW_LOOP_STILL_RUNNING" in capsys.readouterr().out


def test_end_to_end_crashed_new_loop_reverts_original_runner_exact_bytes(tmp_path, monkeypatch, capsys):
    loop, dash, trace = _fake_mac_rollout(tmp_path, monkeypatch, mode="crash")
    with pytest.raises(RuntimeError, match="NEW_LOOP_NOT_RUNNING"):
        ops.main()
    assert trace["restarts"] == 2
    assert trace["wait_calls"] == [111, 111]
    assert loop.read_bytes() == b"OLD_RUNNER_EXACT_BYTES\n"
    assert dash.read_bytes() == b"DASHBOARD_PRESERVED\n"
    assert "LOOP_ROLLBACK_SERVICE=RECOVERED" in capsys.readouterr().out


def test_end_to_end_keyboard_interrupt_recovers_old_loop_if_safe(tmp_path, monkeypatch, capsys):
    loop, dash, trace = _fake_mac_rollout(tmp_path, monkeypatch, mode="interrupt")
    with pytest.raises(KeyboardInterrupt):
        ops.main()
    assert trace["restarts"] == 2
    assert loop.read_bytes() == b"OLD_RUNNER_EXACT_BYTES\n"
    assert dash.read_bytes() == b"DASHBOARD_PRESERVED\n"
    assert "LOOP_ROLLBACK_SERVICE=RECOVERED" in capsys.readouterr().out


def test_end_to_end_unverified_old_delivery_code_never_automatic_rollback(tmp_path, monkeypatch, capsys):
    loop, dash, trace = _fake_mac_rollout(
        tmp_path, monkeypatch, mode="crash", legacy_safe=False)
    with pytest.raises(RuntimeError, match="NEW_LOOP_NOT_RUNNING"):
        ops.main()
    assert trace["restarts"] == 1
    assert loop.read_bytes() == b"CANDIDATE_RUNNER\n"
    assert dash.read_bytes() == b"DASHBOARD_PRESERVED\n"
    assert "ROLLBACK=MANUAL_OLD_DELIVERY_CODE_UNVERIFIED" in capsys.readouterr().out


def test_end_to_end_signal_delta_is_hard_apply_gate(tmp_path, monkeypatch):
    loop, _, trace = _fake_mac_rollout(
        tmp_path, monkeypatch, change_signal=True)
    with pytest.raises(RuntimeError, match="SIGNAL_CODE_DELTA_EXPLICITLY_APPROVED"):
        ops.main()
    assert trace["restarts"] == 0
    assert loop.read_bytes() == b"OLD_RUNNER_EXACT_BYTES\n"
