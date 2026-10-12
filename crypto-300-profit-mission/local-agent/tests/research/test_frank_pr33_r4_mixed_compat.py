"""R4: real legacy module vs new Dashboard HTTP; state-label accuracy.

Tests use local SQLite, an ephemeral live loopback server, and the actual
JavaScript renderRuntime function. No production Mac, Gmail or wallet access.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import threading
import urllib.request

import pytest

from mission_agent.mission_control.db import ControlDB
from mission_agent.mission_control import server as server_module
from mission_agent.mission_control.server import DashboardState, Handler, ThreadingHTTPServer
from test_delivery_review_integration import seed

RESEARCH = Path(__file__).resolve().parent
STATIC_JS = RESEARCH.parents[1] / "mission_agent/mission_control/static/app.js"
LEGACY = RESEARCH / "fixtures/frank_delivery_review_legacy_dbd2dae5.py"


@pytest.fixture
def db_and_dashboard(tmp_path):
    prod = tmp_path / "prod"
    prod.mkdir()
    control = tmp_path / "control"
    control.mkdir()
    db = ControlDB(control / "mission-control.sqlite")
    (control / "mission-control-health.json").write_text(json.dumps({
        "status": "OK", "manual_review_total_count": 15,
        "manual_review_gmail_count": 15
    }))
    yield db, DashboardState(prod, control)
    db.close()


def legacy_classifier():
    spec = importlib.util.spec_from_file_location("legacy_delivery_review_dbd2dae5", LEGACY)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    return original.summarize_manual_reviews


def test_real_legacy_module_new_backend_returns_explicit_noncrashing_error(
        db_and_dashboard, monkeypatch):
    db, dashboard = db_and_dashboard
    for _ in range(15):
        seed(db)
    monkeypatch.setattr(server_module, "summarize_manual_reviews", legacy_classifier())
    before = list(db.db.execute(
        "SELECT decision_id,status FROM decision_outbox ORDER BY decision_id"))
    got = dashboard.mission_control_health()
    assert got["status"] == "OK"
    assert got["manual_review_breakdown_available"] is False
    assert got["manual_review_breakdown_error"] == "DELIVERY_REVIEW_CONTRACT_MISMATCH"
    assert got["manual_review_counts_stale"] is True
    assert "manual_review_queued_count" not in got
    assert list(db.db.execute(
        "SELECT decision_id,status FROM decision_outbox ORDER BY decision_id")) == before


def test_real_legacy_module_new_backend_http_is_200_with_explicit_block(
        db_and_dashboard, monkeypatch):
    db, dashboard = db_and_dashboard
    seed(db, "PENDING", error=None)
    monkeypatch.setattr(server_module, "summarize_manual_reviews", legacy_classifier())
    monkeypatch.setattr(Handler, "state", dashboard)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{server.server_port}/api/control-health",
                timeout=4) as response:
            assert response.status == 200
            body = json.load(response)
        assert body["manual_review_breakdown_available"] is False
        assert body["manual_review_breakdown_error"] == "DELIVERY_REVIEW_CONTRACT_MISMATCH"
        assert body["manual_review_counts_stale"] is True
    finally:
        server.shutdown()
        worker.join(timeout=4)
        server.server_close()


@pytest.mark.parametrize("malformed", [
    {"manual_review_breakdown_available": True},
    {"manual_review_breakdown_available": True, "manual_review_queued_count": False},
])
def test_malformed_classifier_cannot_advertise_available_counts(
        db_and_dashboard, monkeypatch, malformed):
    db, dashboard = db_and_dashboard
    seed(db)
    monkeypatch.setattr(server_module, "summarize_manual_reviews", lambda rows: malformed)
    result = dashboard.mission_control_health()
    assert result["manual_review_breakdown_available"] is False
    assert result["manual_review_breakdown_error"] == "DELIVERY_REVIEW_CONTRACT_MISMATCH"


def test_current_classifier_retains_real_counts(db_and_dashboard):
    db, dashboard = db_and_dashboard
    seed(db, "PENDING", error=None)
    seed(db, "MANUAL_REVIEW")
    got = dashboard.mission_control_health()
    assert got["manual_review_queued_count"] == 1
    assert got["manual_review_expired_unsent_count"] == 1
    assert got["manual_review_visible_total_count"] == 2
    assert got["manual_review_breakdown_available"] is True


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_real_js_renders_unknown_as_status_anomaly_not_auto_retry():
    assert STATIC_JS.is_file()
    js = r"""
const fs=require('fs'),vm=require('vm');
const src=fs.readFileSync(process.argv[1],'utf8');
const start=src.indexOf('function renderRuntime(');
const end=src.indexOf('function renderStats(',start);
if(start<0||end<start)throw new Error('RENDER_FN_MISSING');
const dom={innerHTML:'',className:''};
const scope={$:()=>dom,runtimeLabel:{},translated:()=> 'OK',
             badge:()=> '[OK]',esc:(x)=>String(x)};
vm.createContext(scope);
vm.runInContext(src.slice(start,end),scope);
function display(control){scope.renderRuntime({status:'OK'},control);return dom.innerHTML;}
const expected={status:'OK',manual_review_breakdown_available:true,
 manual_review_actionable_count:0,manual_review_pending_count:0,
 manual_review_blocked_count:1,manual_review_blocked_gmail_count:1,
 manual_review_blocked_local_count:0,manual_review_blocked_other_count:0,
 manual_review_queued_count:0,manual_review_expired_unsent_count:0,
 manual_review_visible_total_count:1};
const warning=display(expected);
if(!warning.includes('运行阻塞或状态异常待核查 1'))throw new Error('UNKNOWN_STATE_LABEL_HIDDEN');
if(!warning.includes('未知或跨渠道错配状态'))throw new Error('UNKNOWN_STATE_TOOLTIP_MISSING');
if(warning.includes('正在自动重试'))throw new Error('UI_CLAIMS_AUTO_RETRY');
const stale=display({status:'OK',manual_review_total_count:15,
  manual_review_breakdown_available:false,
  manual_review_breakdown_error:'DELIVERY_REVIEW_CONTRACT_MISMATCH'});
if(!stale.includes('通知分类暂不可用'))throw new Error('STALE_WARNING_MISSING');
if(stale.includes('下列历史总数')||stale.includes('通知异常待复核 15'))
  throw new Error('STALE_FALSE_CLAIM_OR_COUNT');
process.stdout.write('M11_M12_L9_REAL_RENDERER=PASS');
"""
    proc = subprocess.run(["node", "-e", js, str(STATIC_JS)],
                          capture_output=True, text=True, timeout=8)
    assert proc.returncode == 0, proc.stderr
    assert "M11_M12_L9_REAL_RENDERER=PASS" in proc.stdout
