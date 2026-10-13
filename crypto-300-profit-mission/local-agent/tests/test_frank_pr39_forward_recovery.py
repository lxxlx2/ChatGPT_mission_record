"""Recovery of verified PR39 L30 outage: forward-only, no Gmail, no old Loop."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import frank_pr39_forward_recovery as f
import frank_pr39_controlled_release as rel
import test_frank_pr39_legacy_cutover as legacy_fixture
from test_frank_pr39_legacy_cutover import build_world


def offline_world(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    monkeypatch.setattr(f, "rel", legacy_fixture.r)
    monkeypatch.setattr(f, "TARGET", world.sha)
    monkeypatch.setattr(f, "EXPECTED_SOURCE_FILE_COUNT", len(rel.source_manifest(world.ops)))
    monkeypatch.setattr(f, "OLD_PIDS", {"loop": world.loop_pid, "dashboard": world.dash_pid})
    monkeypatch.setattr(f, "ORIGINAL_RUNNERS", {k: rel.sha(v) for k, v in world.mac.runners.items()})
    monkeypatch.setattr(f, "SCANNER_PID", 5555)
    monkeypatch.setattr(f, "SCANNER_SOURCE", "L")
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(f, "host_offline", lambda mac: host_sim(mac))
    world.support = world.mac.support
    with sqlite3.connect(world.frank_db) as db:
        db.execute("CREATE TABLE cursors(wallet TEXT PRIMARY KEY, slot INTEGER, signature TEXT)")
        db.execute("INSERT INTO cursors VALUES('wallet', 100, 'sig100')")
    (world.prod / "health.json").write_text(json.dumps({
        "last_successful_poll": f.datetime.now(f.timezone.utc).isoformat(),
        "status": "RUNNING", "pid": 5555, "source_drift": False,
        "production_trading": "NO_GO", "loaded_source_sha256": "L", "policy_hash": "P"}))
    rel.stage_immutable_release(world.mac, world.ops, world.sha, rel.source_manifest(world.ops))
    incident = world.support / "pr39-releases" / f.INCIDENT
    incident.mkdir(parents=True)
    data = {"mode": "LEGACY_CUTOVER", "phase": "LEGACY_MANUAL_RECOVERY_REQUIRED",
            "expected": world.sha, "legacy_loop_pid": world.loop_pid,
            "dashboard_pid": world.dash_pid, "scanner_pid": 5555,
            "history": [{"phase": x} for x in
                        ["L00_RECHECKED","L10_STAGED","L20_PRESTOP_BACKED_UP",
                         "L25_FROZEN","L30_HOLDS_SET","LEGACY_MANUAL_RECOVERY_REQUIRED"]]}
    (incident / "journal.json").write_text(json.dumps(data))
    rel.backup(world.db, incident / "control-prestop.sqlite")
    rel.backup(world.frank_db, incident / "frank-prestop.sqlite")
    for key, filename in (("loop", "legacy-loop-runner.before.sh"),
                          ("dashboard", "legacy-dashboard-runner.before.sh")):
        (incident / filename).write_bytes(world.mac.runners[key].read_bytes())
    for k in ("loop", "dashboard"):
        world.mac.procs[world.loop_pid if k == "loop" else world.dash_pid]["state"] = "dead"
        world.mac.loaded[world.mac.labels[k]] = None
    world.mac.holds = {"loop", "dashboard"}
    return world, incident


def host_sim(mac):
    assert all(mac.loaded[mac.labels[k]] is None for k in ("loop", "dashboard"))
    assert mac.holds == {"loop", "dashboard"}
    assert all(v["state"] == "dead" for p,v in mac.procs.items() if p in (4242,4343))
    assert not mac.worker_pids({"new_agent": "not-running", "runtime": {
        "loop": {"agent": mac.legacy_agent}, "dashboard": {"agent": mac.dash_agent}}})
    return {"no_worker": True}


def test_recovery_plan_only_reads_live_state(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    before = {str(p): rel.sha(p) for p in tmp_path.rglob("*") if p.is_file()}
    report, state = f.read_only_plan(world.mac, world.ops, world.sha)
    assert report["gate"] == "FORWARD_RECOVERY_ELIGIBLE"
    assert report["old_workers_absent"] is True
    assert report["deployment_authorized"] is False
    assert report["target_sha"] == world.sha
    assert state["incident"] == incident
    assert before == {str(p): rel.sha(p) for p in tmp_path.rglob("*") if p.is_file()}
    assert world.mac.events == []


def test_forward_recovery_uses_immutable_new_loop_and_never_restarts_legacy(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    before = rel.ledger(world.db)
    result = f.forward_apply(world.mac, world.ops, world.sha)
    assert result["status"] == "FORWARD_RECOVERY_SUCCESS"
    assert result["phase"] == "R60_SUCCESS"
    assert world.mac.violations == []
    assert [e[1] for e in world.mac.events if e[0] == "start"] == ["dashboard", "loop"]
    assert world.mac.holds == set()
    for runner in world.mac.runners.values():
        assert "pr39-immutable-releases" in runner.read_text()
    con = sqlite3.connect(world.db)
    assert con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='local_delivery_presentation'").fetchone()[0] == 1
    con.close()
    rel.assert_preserved(before, rel.ledger(world.db), exact=True)
    assert (incident / "forward-recovery/control-recovery.sqlite").is_file()
    assert (incident / "forward-recovery/frank-recovery.sqlite").is_file()
    report = json.loads((incident / "forward-recovery/journal.json").read_text())
    assert report["history"] == f.PHASES
    assert json.loads((incident / "journal.json").read_text())["phase"] == "LEGACY_MANUAL_RECOVERY_REQUIRED"


def test_failed_new_dashboard_fails_stopped_without_db_restore(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    original = world.mac.start
    def broken(key, plist):
        if key == "dashboard":
            raise RuntimeError("TEST_DASHBOARD_BOOTSTRAP_FAILURE")
        original(key, plist)
    monkeypatch.setattr(world.mac, "start", broken)
    outcome = f.forward_apply(world.mac, world.ops, world.sha)
    assert outcome["status"] == "RECOVERY_BLOCKED"
    assert world.mac.holds == {"loop", "dashboard"}
    assert not any(e[0] == "start" and e[1] == "loop" for e in world.mac.events)
    assert world.mac.violations == []
    assert json.loads((incident / "forward-recovery/journal.json").read_text())["phase"] == "RECOVERY_MANUAL_INTERVENTION_REQUIRED"
    assert (incident / "control-prestop.sqlite").is_file()
    assert (incident / "forward-recovery/control-recovery.sqlite").is_file()


def test_loop_heartbeat_failure_after_dashboard_start_holds_both(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    world.mac.loop_heartbeats = False
    outcome = f.forward_apply(world.mac, world.ops, world.sha)
    assert outcome["status"] == "RECOVERY_BLOCKED"
    assert world.mac.holds == {"loop", "dashboard"}
    assert world.mac.violations == []
    assert all(world.mac.loaded[world.mac.labels[k]] is None for k in ("loop", "dashboard"))
    assert json.loads((incident / "forward-recovery/journal.json").read_text())["phase"] == "RECOVERY_MANUAL_INTERVENTION_REQUIRED"


def test_recovery_never_overwrites_existing_attempt_journal(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    recover = incident / "forward-recovery"
    recover.mkdir()
    (recover / "journal.json").write_text("persistent")
    with pytest.raises(RuntimeError, match="RECOVERY_ALREADY_ATTEMPTED"):
        f.read_only_plan(world.mac, world.ops, world.sha)
    assert (recover / "journal.json").read_text() == "persistent"


def test_changed_runner_blocks_before_any_database_or_runner_mutation(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    world.mac.runners["loop"].write_text("tampered")
    with pytest.raises(RuntimeError, match="ORIGINAL_RUNNER_CHANGED"):
        f.read_only_plan(world.mac, world.ops, world.sha)
    assert not (incident / "forward-recovery").exists()


def test_scanner_digest_drift_blocks_forward_recovery(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    monkeypatch.setattr(f, "SCANNER_SOURCE", "wrong")
    with pytest.raises(RuntimeError, match="SCANNER_IDENTITY_DRIFT"):
        f.read_only_plan(world.mac, world.ops, world.sha)
    assert not (incident / "forward-recovery").exists()


def test_original_control_backup_is_not_restore_source_after_drift(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    con = sqlite3.connect(world.db)
    con.execute("DELETE FROM decision_outbox")
    con.commit(); con.close()
    with pytest.raises(RuntimeError):
        f.read_only_plan(world.mac, world.ops, world.sha)
    assert not (incident / "forward-recovery").exists()


def test_missing_authorizations_cannot_apply(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    monkeypatch.setattr(f.rel, "Mac", lambda: world.mac)
    for flags in ([], ["--authorize-production-restart"],
                  ["--authorize-production-restart", "--authorize-future-real-notifications"]):
        with pytest.raises(RuntimeError, match="RECOVERY_AUTHORIZATION_REQUIRED"):
            f.main(["--expected-tool-sha", world.sha, "--apply", *flags])
    assert not (incident / "forward-recovery").exists()


def test_host_offline_checks_disabled_registry_and_no_old_pid(tmp_path, monkeypatch):
    world, _ = offline_world(tmp_path, monkeypatch)
    monkeypatch.undo()
    results = []
    short_labels = [v.split("/")[-1] for v in world.mac.labels.values()]
    disabled = "\n".join(f' "{label}" => disabled' for label in short_labels)
    def fake_command(argv):
        if argv[1] == "print-disabled": return SimpleNamespace(returncode=0, stdout=disabled, stderr="")
        if argv[1] == "print": return SimpleNamespace(returncode=113, stdout="", stderr="Could not find service")
        if argv[1] == "-p": return SimpleNamespace(returncode=1, stdout="", stderr="")
        if argv[1] == "-axo": return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(argv)
    monkeypatch.setattr(f, "command", fake_command)
    assert f.host_offline(world.mac)["no_worker"]
    monkeypatch.setattr(f, "command", lambda argv: SimpleNamespace(
        returncode=0, stdout="4242", stderr="") if argv[1] == "-p" else fake_command(argv))
    with pytest.raises(RuntimeError, match="OLD_PID_PRESENT"):
        f.host_offline(world.mac)

@pytest.mark.parametrize('fault', ['stale', 'future', 'status', 'source_drift', 'policy'])
def test_scanner_health_blocks_plan(tmp_path, monkeypatch, fault):
    world, incident = offline_world(tmp_path, monkeypatch)
    path = world.prod / 'health.json'
    body = json.loads(path.read_text())
    if fault in ('stale', 'future'):
        body['last_successful_poll'] = f.datetime.fromtimestamp(
            f.time.time() + (-121 if fault == 'stale' else 60), f.timezone.utc).isoformat()
    elif fault == 'status': body['status'] = 'ERROR'
    elif fault == 'source_drift': body['source_drift'] = True
    else: body['policy_hash'] = 'changed'
    path.write_text(json.dumps(body))
    with pytest.raises(RuntimeError, match='SCANNER_HEARTBEAT'):
        f.read_only_plan(world.mac, world.ops, world.sha)
    assert not (incident / 'forward-recovery').exists()

@pytest.mark.parametrize('sql,reason', [
    ("UPDATE cursors SET slot=99", 'CURSOR_REGRESSION'),
    ("UPDATE cursors SET signature='different'", 'CURSOR_IDENTITY_CHANGED'),
    ("DELETE FROM cursors", 'CURSOR_WALLET_CHANGED')])
def test_cursor_drift_after_backup_blocks_migration(tmp_path, monkeypatch, sql, reason):
    world, _ = offline_world(tmp_path, monkeypatch)
    original = f.rel.backup
    def backup(src, dest):
        original(src, dest)
        if dest.name == 'frank-recovery.sqlite':
            with sqlite3.connect(world.frank_db) as db: db.execute(sql)
    monkeypatch.setattr(f.rel, 'backup', backup)
    result = f.forward_apply(world.mac, world.ops, world.sha)
    assert result['reason'] == reason
    assert world.mac.holds == {'loop', 'dashboard'}


def test_loaded_service_without_pid_is_still_booted_out(tmp_path, monkeypatch):
    world, _ = offline_world(tmp_path, monkeypatch)
    def broken_start(key, plist):
        world.mac.holds.discard(key)
        raise RuntimeError('BOOTSTRAP_FAILED_NO_PID')
    monkeypatch.setattr(world.mac, 'start', broken_start)
    outcome = f.forward_apply(world.mac, world.ops, world.sha)
    assert outcome['status'] == 'RECOVERY_BLOCKED'
    assert {e[1] for e in world.mac.events if e[0] == 'stop'} == {'loop', 'dashboard'}
    assert outcome['residual_worker_pids'] == []


def test_cleanup_reports_orphan_even_after_bootout(tmp_path, monkeypatch):
    world, incident = offline_world(tmp_path, monkeypatch)
    original = world.mac.start
    def start(key, plist):
        original(key, plist)
        if key == 'dashboard':
            world.mac.procs[world.mac.loaded[world.mac.labels[key]]]['state'] = 'stopped'
            raise RuntimeError('DASHBOARD_FAILED')
    monkeypatch.setattr(world.mac, 'start', start)
    result = f.forward_apply(world.mac, world.ops, world.sha)
    assert result['residual_worker_pids'] == [6000]
    assert 'WORKER_EXIT_UNVERIFIED' in result['cleanup_errors']
    assert json.loads((incident / 'forward-recovery/journal.json').read_text())['residual_worker_pids'] == [6000]


def test_extra_loop_cannot_be_reported_as_success(tmp_path, monkeypatch):
    world, _ = offline_world(tmp_path, monkeypatch)
    original = world.mac.start
    def start(key, plist):
        original(key, plist)
        if key == 'loop':
            world.mac.add_proc(9999, 'python scripts/mission_meme_v1.py loop',
                               f.rel.field(world.mac.runners[key].read_text(), 'LOCAL_AGENT'), f.time.time())
    monkeypatch.setattr(world.mac, 'start', start)
    result = f.forward_apply(world.mac, world.ops, world.sha)
    assert result['reason'] == 'RECOVERY_WORKER_SET_MISMATCH'
    assert result['residual_worker_pids'] == [9999]


@pytest.mark.parametrize('phase', ['INIT', *f.PHASES,
    'MIGRATE_ONLY_PRESENTATION_TABLE', 'SWITCH_RUNNERS_WHILE_SERVICES_DISABLED',
    'START_AND_VERIFY_DASHBOARD', 'START_AND_VERIFY_NEW_LOOP'])
def test_sigkill_after_every_durable_checkpoint_blocks_reexecution(tmp_path, monkeypatch, phase):
    import signal
    world, incident = offline_world(tmp_path, monkeypatch)
    original = f.write_record
    def kill_after_write(path, body):
        original(path, body)
        if (body['phase'] == phase and body['intent'] is None) or body['intent'] == phase:
            os.kill(os.getpid(), signal.SIGKILL)
    child = os.fork()
    if child == 0:
        f.write_record = kill_after_write
        try: f.forward_apply(world.mac, world.ops, world.sha)
        finally: os._exit(10)
    _, status = os.waitpid(child, 0)
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL
    journal = incident / 'forward-recovery/journal.json'
    saved = journal.read_bytes()
    with pytest.raises(RuntimeError, match='RECOVERY_ALREADY_ATTEMPTED'):
        f.read_only_plan(world.mac, world.ops, world.sha)
    assert journal.read_bytes() == saved


def test_cursor_regression_after_observed_advance_is_blocked(tmp_path, monkeypatch):
    world, _ = offline_world(tmp_path, monkeypatch)
    guard = f.scanner_guard
    calls = 0
    def moving(mac, prod, baseline=None):
        nonlocal calls
        calls += 1
        if calls in (2, 3):
            with sqlite3.connect(prod) as db:
                db.execute("UPDATE cursors SET slot=?", (110 if calls == 2 else 105,))
        return guard(mac, prod, baseline)
    monkeypatch.setattr(f, 'scanner_guard', moving)
    result = f.forward_apply(world.mac, world.ops, world.sha)
    assert result['reason'] == 'CURSOR_REGRESSION'
    assert not any(e[0] == 'start' and e[1] == 'loop' for e in world.mac.events)
