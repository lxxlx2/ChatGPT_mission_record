"""Pure mock-only safety tests: do not connect to or restart any Mac service."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "rollout_frank_combined_dashboard_only_20261012.py"
SPEC = importlib.util.spec_from_file_location("frank_ops_rollout_legacy_preflight", SCRIPT)
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)


def fake_existing(port, path, attempts=1):
    if path == "/":
        return b'<!doctype html><html lang="zh-CN"><title>Meme Frank console</title></html>'
    raise OSError("legacy 404: /api/frank-observed-watchlist")


def test_legacy_api_absent_does_not_block_valid_identified_running_dashboard():
    with patch.object(ops.shutil, "which", return_value="/usr/sbin/lsof"), \
         patch.object(ops, "run", return_value=SimpleNamespace(stdout="p14077")), \
         patch.object(ops, "get", side_effect=fake_existing):
        result = ops.existing_dashboard_baseline(8766, 14077)
    assert result["existing_watchlist_api"] == "LEGACY_UNAVAILABLE"
    assert result["identified_dashboard_pid"] == 14077
    assert result["existing_root_html"] == "VERIFIED"


def test_live_new_api_is_read_back_and_counted():
    def request(port, path, attempts=1):
        if path == "/":
            return b"<html>Frank</html>"
        return b'{"rows":[{}, {}, {}]}'
    with patch.object(ops.shutil, "which", return_value="/usr/sbin/lsof"), \
         patch.object(ops, "run", return_value=SimpleNamespace(stdout="p32071")), \
         patch.object(ops, "get", side_effect=request):
        result = ops.existing_dashboard_baseline(8766, 32071)
    assert result["existing_watchlist_count"] == 3
    assert result["existing_watchlist_api"] == "AVAILABLE"


def test_unrelated_port_listener_blocks_before_any_network_query():
    with patch.object(ops.shutil, "which", return_value="/usr/sbin/lsof"), \
         patch.object(ops, "run", return_value=SimpleNamespace(stdout="p81777")), \
         patch.object(ops, "get") as fetch:
        with pytest.raises(RuntimeError, match="CONFIGURED_PORT_OWNED_BY_DASHBOARD=BLOCKED"):
            ops.existing_dashboard_baseline(8766, 14077)
        fetch.assert_not_called()


def test_bad_root_html_blocks_even_if_listener_matches():
    with patch.object(ops.shutil, "which", return_value="/usr/sbin/lsof"), \
         patch.object(ops, "run", return_value=SimpleNamespace(stdout="p14077")), \
         patch.object(ops, "get", return_value=b"unrelated service") as fetch:
        with pytest.raises(RuntimeError, match="EXISTING_DASHBOARD_HTML=BLOCKED"):
            ops.existing_dashboard_baseline(8766, 14077)
        assert fetch.call_count == 1


def test_missing_lsof_blocks_before_any_network_query():
    with patch.object(ops.shutil, "which", return_value=None), \
         patch.object(ops, "run") as execute, \
         patch.object(ops, "get") as fetch:
        with pytest.raises(RuntimeError, match="LSOF_AVAILABLE=BLOCKED"):
            ops.existing_dashboard_baseline(8766, 14077)
        execute.assert_not_called()
        fetch.assert_not_called()
