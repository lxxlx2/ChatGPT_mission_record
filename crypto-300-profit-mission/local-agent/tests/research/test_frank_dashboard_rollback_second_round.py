"""Independent deterministic interruption/rollback tests for PR33 research fix.

Never calls real launchctl, Gmail, RPC or production SQLite.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import signal

import pytest

MODFILE = Path(__file__).resolve().parents[2] / "scripts" / "deploy_frank_dashboard_review_badge.py"
spec = importlib.util.spec_from_file_location("review_deploy_rollback", MODFILE)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    folder = tmp_path / "source"
    (folder / "static").mkdir(parents=True)
    originals = {name: (b"old bytes " + name.encode()) for name in app.PATCHES}
    target = {name: (b"new bytes " + name.encode()) for name in app.PATCHES}
    for name, content in originals.items():
        (folder / name).write_bytes(content)
    monkeypatch.setattr(app.Path, "home", lambda: tmp_path)
    restart = []
    monkeypatch.setattr(app, "restart_dashboard", lambda: restart.append("restart"))
    def verify_rollback(root, saved):
        assert saved == originals
        for name, contents in originals.items():
            if (root / name).read_bytes() != contents:
                raise RuntimeError("ROLLBACK_MIXED_TEST_PROOF")
    monkeypatch.setattr(app, "verify_rollback", verify_rollback)
    return folder, originals, target, restart


def test_keyboard_interrupt_after_first_write_restores_every_source_byte(prepared, monkeypatch, capsys):
    folder, originals, target, restarts = prepared
    original = app._replace_bytes
    calls = []
    def interrupt_once(path, data):
        calls.append(path.name)
        if len(calls) == 2:
            raise KeyboardInterrupt()
        return original(path, data)
    monkeypatch.setattr(app, "_replace_bytes", interrupt_once)
    with pytest.raises(KeyboardInterrupt):
        app.install(folder, target)
    assert restarts == ["restart"]
    assert all((folder / k).read_bytes() == v for k, v in originals.items())
    out = capsys.readouterr().out
    assert "ROLLBACK=DASHBOARD_FILES_RESTORED" in out
    assert "BACKUP_NAME=" in out
    backups = list((Path.home() / "Library/Application Support/FrankMeme/dashboard-review-backups").glob("*"))
    assert len(backups) == 1
    for name in originals:
        assert (backups[0] / name).stat().st_mode & 0o777 == 0o600


def test_sigterm_during_install_can_trigger_rollback_without_real_os_signal(prepared, monkeypatch):
    folder, originals, target, restarts = prepared
    original = app._replace_bytes
    calls = 0
    def fake_signal(path, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        return original(path, data)
    monkeypatch.setattr(app, "_replace_bytes", fake_signal)
    with pytest.raises(InterruptedError, match="DASHBOARD_INSTALL_SIGNAL_INTERRUPTED"):
        app.install(folder, target)
    assert all((folder / k).read_bytes() == v for k, v in originals.items())
    assert restarts == ["restart"]


def test_failed_one_file_restore_reports_incomplete_but_attempts_others(prepared, monkeypatch, capsys):
    folder, originals, target, restarts = prepared
    original = app._replace_bytes
    def fail_restore_server(path, data):
        if path.name == "server.py" and data == originals["server.py"]:
            raise OSError(28, "ENOSPC simulated")
        return original(path, data)
    monkeypatch.setattr(app, "_replace_bytes", fail_restore_server)
    monkeypatch.setattr(app, "verify_dashboard",
                        lambda: (_ for _ in ()).throw(RuntimeError("HTTP_UNHEALTHY")))
    with pytest.raises(RuntimeError, match="DASHBOARD_ROLLBACK_INCOMPLETE"):
        app.install(folder, target)
    assert (folder / "server.py").read_bytes() == target["server.py"]
    assert all((folder / name).read_bytes() == originals[name]
               for name in ("static/app.js", "delivery_review.py"))
    assert len(restarts) == 2
    stderr = capsys.readouterr().err
    assert "ROLLBACK_INCOMPLETE=" in stderr
    assert "MANUAL_ACTION_REQUIRED BACKUP_NAME=" in stderr
    assert "restore:server.py:OSError" in stderr


def test_verify_dashboard_rechecks_database_on_each_retry(prepared, monkeypatch):
    folder, originals, target, restarts = prepared
    monkeypatch.setattr(app, "control_root", lambda: folder)
    monkeypatch.setattr(app, "health_endpoint", lambda control: "http://127.0.0.1/health")
    basic = {"manual_review_expired_unsent_count": 0,
             "manual_review_actionable_count": 0,
             "manual_review_pending_count": 0}
    first = {**basic, "manual_review_total_count": 4,
             "manual_review_visible_total_count": 4}
    second = {**basic, "manual_review_total_count": 5,
              "manual_review_visible_total_count": 5}
    count_calls = []
    def read_db(control):
        count_calls.append(True)
        return first if len(count_calls) == 1 else second
    monkeypatch.setattr(app, "actual_delivery_counts", read_db)
    monkeypatch.setattr(app.time, "sleep", lambda seconds: None)
    class Payload:
        def __enter__(self): return self
        def __exit__(self,*a): return None
        def read(self,*a): return json.dumps({
            "manual_review_breakdown_available": True,
            "manual_review_breakdown_error": None,
            **second
        }).encode()
    monkeypatch.setattr(app.urllib.request, "urlopen",
                        lambda url, timeout: Payload())
    app.verify_dashboard()
    assert len(count_calls) == 2


def test_second_deployer_cannot_acquire_existing_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(app.Path, "home", lambda: tmp_path)
    with app.deployment_mutex():
        with pytest.raises(RuntimeError, match="DASHBOARD_DEPLOY_ALREADY_RUNNING"):
            with app.deployment_mutex():
                pass


def test_original_product_source_pinned_as_real_git_commit():
    assert len(app.COMMIT) == 40
    assert all(len(item["target"]) == 40 for item in app.PATCHES.values())
