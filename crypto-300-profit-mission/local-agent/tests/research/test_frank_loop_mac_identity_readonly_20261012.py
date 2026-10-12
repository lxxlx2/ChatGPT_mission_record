"""Synthetic tests of secret-free, non-mutating Mac Loop identity audit."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "scripts/frank_loop_mac_identity_readonly_20261012.py"
spec = importlib.util.spec_from_file_location("frank_loop_readonly_identity", SOURCE)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


def put(root, path, body):
    dst = root / path
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(body, encoding="utf-8")
    return dst


def test_diff_includes_store_wallet_delivery_and_cli(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    for root in (old, new):
        put(root, "mission_agent/signals/store.py", "original")
        put(root, "mission_agent/mission_control/delivery.py", "original")
        put(root, "mission_agent/mission_control/wallet_watch.py", "original")
        put(root, "scripts/mission_meme_v1.py", "original")
    assert ops.changed_modules(ops.source_digests(old), ops.source_digests(new)) == []
    put(new, "mission_agent/signals/store.py", "changed")
    put(new, "mission_agent/mission_control/wallet_watch.py", "changed")
    put(new, "scripts/mission_meme_v1.py", "changed")
    put(new, "mission_agent/new_module.py", "new")
    assert ops.changed_modules(ops.source_digests(old), ops.source_digests(new)) == [
        "mission_agent/mission_control/wallet_watch.py", "mission_agent/new_module.py",
        "mission_agent/signals/store.py", "scripts/mission_meme_v1.py"]


def test_deleted_module_is_also_a_decision_change(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    put(old, "mission_agent/signals/engine.py", "present")
    put(new, "mission_agent/__init__.py", "")
    assert ops.changed_modules(ops.source_digests(old), ops.source_digests(new)) == [
        "mission_agent/__init__.py", "mission_agent/signals/engine.py"]


def test_config_field_parser_rejects_duplicates_and_unquoted():
    assert ops.field('LOCAL_AGENT=/tmp/a\n', "LOCAL_AGENT") is None
    assert ops.field('LOCAL_AGENT="/tmp/a"\nLOCAL_AGENT="/tmp/b"\n',
                     "LOCAL_AGENT") is None
    assert ops.field('LOCAL_AGENT="/tmp/old"\n', "LOCAL_AGENT") == Path("/tmp/old")


def test_process_identity_never_prints_raw_arguments_or_paths(monkeypatch, tmp_path, capsys):
    secret = "/fake/private/api-key-in-dir"
    old = tmp_path / "private-source"
    old.mkdir()
    def fake_execute(argv, *, seconds=12):
        if argv[0] == "/bin/ps":
            return SimpleNamespace(
                returncode=0,
                stdout="python scripts/mission_meme_v1.py loop --live-delivery --token=SECRET_NO_PRINT\n")
        return SimpleNamespace(returncode=0, stdout="p123\nn" + str(old) + "\n")
    monkeypatch.setattr(ops, "execute", fake_execute)
    result = ops.process_identity(123, old)
    assert result == {
        "process_args_match_loop": True,
        "process_cwd_matches_runner": True,
        "cwd_checked": True,
    }
    assert not capsys.readouterr().out
    assert "SECRET_NO_PRINT" not in str(result)
    assert secret not in str(result)


def test_lsof_cwd_unavailable_must_not_claim_running_version(monkeypatch, tmp_path):
    monkeypatch.setattr(ops, "execute", lambda cmd, seconds=12: SimpleNamespace(
        returncode=1, stdout="", stderr=""))
    result = ops.process_identity(123, tmp_path)
    assert result["process_cwd_matches_runner"] is False
    assert result["cwd_checked"] is False
    assert result["process_args_match_loop"] is False


def test_missing_source_sha_cannot_be_invented(monkeypatch, tmp_path):
    monkeypatch.setattr(ops, "execute", lambda cmd, seconds=12: SimpleNamespace(
        returncode=1, stdout="", stderr=""))
    assert ops.git_head(tmp_path) is None


def test_identical_delivery_code_is_only_conditional_rollback_gate(tmp_path, monkeypatch):
    old, new = tmp_path / "old", tmp_path / "new"
    for root in (old, new):
        put(root, "mission_agent/mission_control/delivery.py", "same")
        put(root, "scripts/mission_meme_v1.py", "same")
    monkeypatch.setattr(ops, "git_head", lambda p: "1"*40 if p == old else ops.PIN)
    monkeypatch.setattr(ops, "checks", {})
    monkeypatch.setattr(ops, "details", {})
    loop_text = f'LOCAL_AGENT="{old}"\n'
    dash_text = f'LOCAL_AGENT="{new}"\n'
    ops.metadata_of_runtime(loop_text, dash_text)
    assert ops.details["legacy_delivery_identical"] is True
    assert ops.details["automatic_rollback_still_requires_fresh_delivery_state_check"]
    assert ops.details["changed_code_files"] == []
    put(new, "mission_agent/mission_control/delivery.py", "different")
    monkeypatch.setattr(ops, "details", {})
    ops.metadata_of_runtime(loop_text, dash_text)
    assert ops.details["legacy_delivery_identical"] is False
    assert "mission_agent/mission_control/delivery.py" in ops.details["changed_code_files"]


def test_diagnostic_source_has_no_live_write_or_gmail_actions():
    src = SOURCE.read_text(encoding="utf-8")
    for prohibited in ("kickstart", "sqlite3.connect(", "GmailDelivery(", "send_message(",
                       "write_bytes(", "unlink(", "os.replace(", "policy_path.write_text",
                       "requests.", "urllib.request"):
        assert prohibited not in src
    assert "production_database_modified" in src
    assert "running_python_code_bytes_proven" in src



def test_shared_venv_and_pinned_version_are_readonly(monkeypatch, tmp_path):
    venv = tmp_path / "venv"
    put(venv, "bin/python", "nonexecuted-fixture")
    runner = f'VENV="{venv}"\n'
    called = []
    def fake_execute(cmd, *, seconds=12):
        called.append(cmd)
        return SimpleNamespace(returncode=0, stdout="3 12 15.0.1\n", stderr="")
    monkeypatch.setattr(ops, "execute", fake_execute)
    monkeypatch.setattr(ops, "checks", {})
    monkeypatch.setattr(ops, "details", {})
    ops.dependency_identity(runner, runner)
    assert all(v == "PASS" for v in ops.checks.values())
    assert ops.details["websockets_version"] == "15.0.1"
    assert called[0][1:3] == ["-B", "-c"]
    assert "mission_agent" not in called[0][3]
    assert "send" not in called[0][3]


def test_mismatched_venv_blocks_without_running_python(monkeypatch, tmp_path):
    a = put(tmp_path / "a", "bin/python", "fake-a")
    b = put(tmp_path / "b", "bin/python", "fake-b")
    monkeypatch.setattr(ops, "execute", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout="3 12 15.0.1\n"))
    monkeypatch.setattr(ops, "checks", {})
    monkeypatch.setattr(ops, "details", {})
    ops.dependency_identity(f'VENV="{a.parent.parent}"\n',
                            f'VENV="{b.parent.parent}"\n')
    assert ops.checks["SHARED_VENV_PATH_IDENTICAL"] == "FAIL"


def test_wrong_websockets_version_never_accepted(monkeypatch, tmp_path):
    venv = tmp_path / "venv"
    put(venv, "bin/python", "fake")
    monkeypatch.setattr(ops, "execute", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout="3 12 14.0.0\n"))
    monkeypatch.setattr(ops, "checks", {})
    monkeypatch.setattr(ops, "details", {})
    runner = f'VENV="{venv}"\n'
    ops.dependency_identity(runner, runner)
    assert ops.checks["RELEASE_WEBSOCKETS_DEPENDENCY_PIN"] == "FAIL"
