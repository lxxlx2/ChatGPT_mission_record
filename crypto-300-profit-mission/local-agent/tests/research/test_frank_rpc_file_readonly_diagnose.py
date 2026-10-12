"""No credential reads or real launchctl invocation. Test only synthetic fixtures."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/frank_rpc_file_readonly_diagnose_20261012.py"
SPEC = importlib.util.spec_from_file_location("frank_rpc_file_readonly_diagnose", SCRIPT)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_nonmatching_paths_diagnostic_does_not_print_rpc_secret(tmp_path, monkeypatch, capsys):
    app = tmp_path / "Application Support" / "FrankMeme"
    app.mkdir(parents=True)
    a = app / "old-rpc"
    a.write_text("https://private.invalid/SECRET_ENDPOINT_SHOULD_NOT_APPEAR")
    a.chmod(0o600)
    (app / "mission-loop.sh").write_text(f'RPC_FILE="{tmp_path / "gone-rpc"}"\nPROD="{tmp_path}"\n')
    (app / "dashboard.sh").write_text(f'RPC_FILE="{a}"\n')
    pointer = tmp_path / "control-pointer"
    pointer.write_text(str(tmp_path / "control"))
    monkeypatch.setattr(m, "SUPPORT", app)
    monkeypatch.setattr(m, "LOOP", app / "mission-loop.sh")
    monkeypatch.setattr(m, "DASH", app / "dashboard.sh")
    monkeypatch.setattr(m, "POINTER", pointer)
    monkeypatch.setattr(m, "launch_pid", lambda name: {"loop": 1234, "dashboard": 5678}[name])
    monkeypatch.setattr(m, "RESULT", {})
    monkeypatch.setattr(m, "STATES", {})
    m.main()
    printed = capsys.readouterr().out
    assert m.STATES["LOOP_RPC_FILE_EXISTS"] == "FAIL"
    assert m.STATES["DASHBOARD_RPC_FILE_EXISTS"] == "PASS"
    assert m.STATES["LOOP_DASHBOARD_RPC_PATHS_MATCH"] == "FAIL"
    assert m.RESULT["classification"]["LOOP_PATH_DIFFERS_FROM_DASHBOARD"] is True
    assert m.RESULT["classification"]["DASHBOARD_HAS_PRIVATE_RPC_CANDIDATE"] is True
    assert "SECRET_ENDPOINT_SHOULD_NOT_APPEAR" not in printed
    assert "private.invalid" not in printed
    assert str(tmp_path) not in printed
    assert a.read_text().endswith("SECRET_ENDPOINT_SHOULD_NOT_APPEAR")


def test_matching_missing_paths_do_not_imply_source_exists(tmp_path, monkeypatch):
    p = tmp_path / "gone"
    app = tmp_path / "support"
    app.mkdir()
    (app / "mission-loop.sh").write_text(f'RPC_FILE="{p}"\n')
    (app / "dashboard.sh").write_text(f'RPC_FILE="{p}"\n')
    monkeypatch.setattr(m, "SUPPORT", app)
    monkeypatch.setattr(m, "LOOP", app / "mission-loop.sh")
    monkeypatch.setattr(m, "DASH", app / "dashboard.sh")
    monkeypatch.setattr(m, "POINTER", tmp_path / "no-pointer")
    monkeypatch.setattr(m, "launch_pid", lambda kind: 1)
    monkeypatch.setattr(m, "RESULT", {})
    monkeypatch.setattr(m, "STATES", {})
    m.main()
    assert m.STATES["LOOP_DASHBOARD_RPC_PATHS_MATCH"] == "PASS"
    assert m.STATES["LOOP_RPC_FILE_EXISTS"] == "FAIL"
    assert m.STATES["DASHBOARD_RPC_FILE_EXISTS"] == "FAIL"


def test_unquoted_and_duplicate_rpc_field_is_not_trusted():
    assert m.field('RPC_FILE=/tmp/a\n', 'RPC_FILE') is None
    assert m.field('RPC_FILE="/tmp/a"\nRPC_FILE="/tmp/b"\n', 'RPC_FILE') is None
    assert m.field('RPC_FILE="/tmp/valid"\n', 'RPC_FILE') == Path("/tmp/valid")


def test_symlink_and_world_readable_privacy_flags(tmp_path):
    secret = tmp_path / "rpc-private"
    secret.write_text("DO_NOT_PRINT")
    secret.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(secret)
    x = m.inspect(link)
    assert x["regular_file"] is True and x["symlink"] is True
    assert x["owner_only_permissions"] is True
    secret.chmod(0o644)
    assert m.inspect(link)["owner_only_permissions"] is False


def test_no_external_mutating_operations_are_used():
    script = SCRIPT.read_text()
    assert 'kickstart' not in script
    assert '.write_text(' not in script
    assert '.read_bytes(' not in script
    assert 'urlopen(' not in script
    assert 'rpc_values_read": False' in script
