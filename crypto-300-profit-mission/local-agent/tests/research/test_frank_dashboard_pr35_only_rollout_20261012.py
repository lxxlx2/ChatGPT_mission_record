"""Static/behavioral PR35 Dashboard-only rollout gates: no live Mac side effects."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/frank_dashboard_pr35_only_rollout_20261012.py"
spec = importlib.util.spec_from_file_location("dashboard_pr35_only", SCRIPT)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


def test_exact_source_pins_and_pr35_layout():
    assert ops.PIN == "62697bf98606c19c5709c27006a6a40d9408db97"
    assert ops.PRIOR_DASH_PIN == "6a5b7e8a533f99c871e31f9674329fcb4f929cc2"
    markup = (ROOT / "mission_agent/mission_control/static/index.html").read_text()
    assert ops.layout_order_valid(markup)
    assert 'id="follow-opportunities"' in markup


def test_reordering_or_lost_section_fails_without_reading_external_state():
    markup = (ROOT / "mission_agent/mission_control/static/index.html").read_text()
    assert not ops.layout_order_valid(markup.replace(
        'id="follow-opportunities"', 'id="missing-follow-opportunities"'))
    assert not ops.layout_order_valid(markup.replace(
        'id="frank-watch-panel"', 'id="follow-opportunities"'))


def test_live_response_must_show_new_layout_before_deployment_success(monkeypatch):
    from json import dumps
    markup = (ROOT / "mission_agent/mission_control/static/index.html").read_text()
    fake = {
        "/": markup.encode("utf-8"),
        "/api/frank-observed-watchlist": dumps({
            "rows": [
                {"mint":ops.J7, "ata_outside_index_window_signatures": 0,
                 "ata_inside_index_window_signatures":2, "pnl_usd":None},
                {"mint":ops.BPXX, "ata_outside_index_window_signatures": 63,
                 "ata_inside_index_window_signatures":3, "pnl_usd":None}
            ],
            "ata_gap_source_status": "DATED_ATA_INDEX_SCOPE_V2"
        }).encode("utf-8"),
        "/static/app.js": "数据库无发送尝试记录 窗口前".encode("utf-8"),
        "/api/control-health": b'{}',
    }
    monkeypatch.setattr(ops, "get", lambda port, path, attempts=1: fake[path])
    assert ops.verify_api(8766, strict=True)["watchlist_count"] == 2
    fake["/"] = markup.replace('id="follow-opportunities"', 'id="lost-section"').encode()
    with pytest.raises(RuntimeError, match="LIVE_PR35_OPPORTUNITY_FIRST"):
        ops.verify_api(8766, strict=True)


def test_existing_loop_is_never_launchctl_kickstarted_or_runner_overwritten():
    code = SCRIPT.read_text()
    assert "dashboard_restart()" in code
    assert '["/bin/launchctl", "kickstart", "-k", DASH_LABEL]' in code
    assert '["/bin/launchctl", "kickstart", "-k", LOOP_LABEL]' not in code
    assert "atomic_runner(LOOP_RUNNER" not in code
    assert "sha(LOOP_RUNNER) == loop_sha_before" in code
    assert "launch_pid(LOOP_LABEL) == live_loop_pid_before" in code
    assert "--apply-dashboard" in code
    assert "sqlite_backup" in code
    assert "ISOLATED_PREFLIGHT=PASS" in code
    assert "DASHBOARD_PR35_LAYOUT=SUCCESS" in code


def test_existing_runner_parser_rejects_duplicate_agent_and_not_mutate(tmp_path):
    raw = 'LOCAL_AGENT="/tmp/a"\nPROD="/tmp/p"\nVENV="/tmp/v"\nCONTROL_POINTER="/tmp/c"\n'
    assert set(ops.runner_vars(raw)) == {"LOCAL_AGENT","PROD","VENV","CONTROL_POINTER"}
    with pytest.raises(RuntimeError, match="RUNNER_MISSING_OR_DUPLICATE_LOCAL_AGENT"):
        ops.runner_vars(raw + 'LOCAL_AGENT="/tmp/b"\n')


def test_atomic_runner_keeps_exact_bytes_and_file_mode(tmp_path):
    runner = tmp_path / "dashboard.sh"
    runner.write_bytes(b"prior")
    ops.atomic_runner(runner,b"follow-first",0o700)
    assert runner.read_bytes()==b"follow-first"
    assert runner.stat().st_mode & 0o777 == 0o700


def test_runner_upgrade_changes_only_agent_binding():
    old = '/home/a/old'
    target = '/home/a/new'
    raw = f'LOCAL_AGENT="{old}"\nRPC_FILE="/secret/not-to-be-printed"\n'
    updated = raw.replace('LOCAL_AGENT="' + old + '"','LOCAL_AGENT="' + target + '"',1)
    assert updated.replace('LOCAL_AGENT="' + target + '"',
                           'LOCAL_AGENT="' + old + '"',1) == raw
    assert 'RPC_FILE="/secret/not-to-be-printed"' in updated
