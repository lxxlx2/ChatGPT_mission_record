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
    with pytest.raises(RuntimeError, match="LEGACY_DELIVERY_STATUS_CHANGED"):
        ops.assert_legacy_receipts_unchanged(original, changed)
    del changed[channel][key]
    with pytest.raises(RuntimeError, match="LEGACY_DELIVERY_STATUS_CHANGED"):
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
