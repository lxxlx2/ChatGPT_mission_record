"""Independent PR33 H-5/H-6/M-8/M-9 prevention with real SQLite and actual UI routine."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from mission_agent.mission_control.db import ControlDB
from mission_agent.mission_control.server import DashboardState
from test_delivery_review_integration import seed

AGENT = Path(__file__).resolve().parents[2]


def import_script(path, name):
    spec = importlib.util.spec_from_file_location(name, AGENT / "scripts" / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def store(tmp_path):
    ctl = tmp_path / "ctl"
    ctl.mkdir()
    prod = tmp_path / "prod"
    prod.mkdir()
    db = ControlDB(ctl / "mission-control.sqlite")
    (ctl / "mission-control-health.json").write_text(json.dumps({"status": "OK"}))
    yield ctl, db, DashboardState(prod, ctl)
    db.close()


def test_real_sqlite_old_pending_reaches_server_probe_and_deployer(store):
    ctl, db, dashboard = store
    seed(db, "PENDING", channel="gmail", attempts=0, error=None)
    seed(db, "PENDING", channel="local", attempts=0, error=None)
    before = list(db.db.execute(
        "SELECT channel,status,attempts FROM decision_outbox ORDER BY channel"))
    deploy = import_script("deploy_frank_dashboard_review_badge.py", "deploy_pending_test")
    probe = import_script("frank_dashboard_readonly_acceptance.py", "probe_pending_test")
    via_http = dashboard.mission_control_health()
    via_deploy = deploy.actual_delivery_counts(ctl)
    via_probe = probe.summary_from_database(ctl)
    for src in (via_http, via_deploy, via_probe):
        assert src["manual_review_queued_count"] == 2
        assert src["manual_review_queued_gmail_count"] == 1
        assert src["manual_review_queued_local_count"] == 1
        assert src["manual_review_visible_total_count"] == 2
        assert src["manual_review_total_count"] == 0
    assert via_probe["dashboard_hidden_nonsuccess_rows"] == 0
    assert list(db.db.execute(
        "SELECT channel,status,attempts FROM decision_outbox ORDER BY channel")) == before


def test_local_command_accepted_is_safe_in_both_independent_oracles(store):
    ctl, db, dashboard = store
    seed(db, "COMMAND_ACCEPTED", channel="local", attempts=1)
    deploy = import_script("deploy_frank_dashboard_review_badge.py", "deploy_local_ok")
    probe = import_script("frank_dashboard_readonly_acceptance.py", "probe_local_ok")
    assert deploy.actual_delivery_counts(ctl)["manual_review_visible_total_count"] == 0
    assert probe.summary_from_database(ctl)["dashboard_hidden_nonsuccess_rows"] == 0
    assert dashboard.mission_control_health()["manual_review_visible_total_count"] == 0


@pytest.mark.parametrize("channel,status", [
    ("gmail", "COMMAND_ACCEPTED"),
    ("local", "SENT_VERIFIED"),
    ("gmail", "UNEXPECTED_TERMINAL"),
    ("local", "UNEXPECTED_TERMINAL"),
])
def test_channel_status_mismatch_blocks_deploy_even_when_server_displays(
        store, channel, status):
    ctl, db, dashboard = store
    seed(db, status, channel=channel, attempts=1)
    probe = import_script("frank_dashboard_readonly_acceptance.py", "probe_invalid_pair")
    deploy = import_script("deploy_frank_dashboard_review_badge.py", "deploy_invalid_pair")
    assert dashboard.mission_control_health()["manual_review_visible_total_count"] == 1
    assert probe.summary_from_database(ctl)["dashboard_hidden_nonsuccess_rows"] == 1
    with pytest.raises(RuntimeError, match="UNCLASSIFIED_OUTBOX_STATUS"):
        deploy.actual_delivery_counts(ctl)


@pytest.mark.skipif(shutil.which("node") is None, reason="JS runtime unavailable")
def test_actual_dashboard_runtime_dom_renderer_handles_legacy_and_pending():
    src = AGENT / "mission_agent" / "mission_control" / "static" / "app.js"
    js = r"""
const fs=require('fs'),vm=require('vm');
const code=fs.readFileSync(process.argv[1],'utf8');
const start=code.indexOf('function renderRuntime(');
const end=code.indexOf('function renderStats(',start);
if (start<0||end<start) throw new Error('RUNTIME_RENDERER_NOT_FOUND');
const node={innerHTML:'',className:''};
const scope={
  $:()=>node,
  runtimeLabel:{},
  translated:()=> 'OK',
  badge:()=> '[STATUS]',
  esc:(v)=>String(v)
};
vm.createContext(scope);
vm.runInContext(code.slice(start,end),scope);
scope.renderRuntime({status:'OK',heartbeat_age_seconds:0},{
  status:'OK',manual_review_total_count:15,manual_review_gmail_count:15});
if (!node.innerHTML.includes('通知分类暂不可用') ||
    node.innerHTML.includes('通知异常待复核 15')) throw new Error('M9_LEGACY_FALSE_ACTIONABLE');
scope.renderRuntime({status:'OK'},{status:'OK',
  manual_review_breakdown_available:true,
  manual_review_actionable_count:0,
  manual_review_pending_count:0,
  manual_review_blocked_count:0,
  manual_review_queued_count:2,
  manual_review_queued_gmail_count:1,
  manual_review_queued_local_count:1,
  manual_review_queued_other_count:0,
  manual_review_expired_unsent_count:0,
  manual_review_visible_total_count:2
});
if (!node.innerHTML.includes('待发送未完成 2')) throw new Error('H6_QUEUED_INVISIBLE');
scope.renderRuntime({status:'OK'},{
  status:'OK',manual_review_breakdown_available:true,
  manual_review_expired_unsent_count:15,
  manual_review_actionable_count:0,
  manual_review_pending_count:0,
  manual_review_blocked_count:0,
  manual_review_visible_total_count:15
});
if (!node.innerHTML.includes('接口版本不匹配') ||
    node.innerHTML.includes('通知异常待复核 15')) throw new Error('M9_MIXED_VERSION');
process.stdout.write('PR33_ACTUAL_RUNTIME_RENDERER=PASS\\n');
"""
    result = subprocess.run(["node", "-e", js, str(src)], capture_output=True,
                            text=True, timeout=10, check=True)
    assert "PR33_ACTUAL_RUNTIME_RENDERER=PASS" in result.stdout
