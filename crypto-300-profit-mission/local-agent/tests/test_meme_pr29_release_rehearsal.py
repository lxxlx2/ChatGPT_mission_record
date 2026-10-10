"""No-deploy rehearsal using the *real* PR #29 release/restore helpers.

All paths and SQLite databases live under pytest tmp_path. launchctl and process
probes are monkeypatched; no Mac service, network or email may be touched.
"""
import ast
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
H3 = "6cb432e1b99571e6bf551aa684f5cf76686c4978"
FRANK = "crypto-300-profit-mission/local-agent/mission_agent/mission_control/frank.py"
DEPLOY = HERE / "scripts/deploy_mission_meme_pr29.py"
spec = importlib.util.spec_from_file_location("pr29_deploy_tested", DEPLOY)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def _node(tree, name):
    for item in tree.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name:
            return item
        if isinstance(item, ast.ClassDef) and item.name == "FrankReader":
            for method in item.body:
                if isinstance(method, ast.FunctionDef) and method.name == name:
                    return method
    raise AssertionError("FUNCTION_ABSENT:" + name)


@pytest.mark.parametrize("function", [
    "_event_price_usdc", "_quote_display", "candidates",
])
def test_frank_h3_decision_source_is_ast_identical_to_current_head(function):
    """Prove this PR did not modify the decision adapter compared with H3."""
    old = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", H3 + ":" + FRANK], text=True
    )
    current = (ROOT / FRANK).read_text()
    left = ast.dump(_node(ast.parse(old), function), include_attributes=False)
    right = ast.dump(_node(ast.parse(current), function), include_attributes=False)
    assert left == right, (
        f"H3_{function}_CHANGED_REQUIRES_HISTORICAL_DECISION_REPLAY"
    )


def _sqlite(path):
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(
        "CREATE TABLE IF NOT EXISTS gmail_delivery "
        "(decision_id TEXT PRIMARY KEY,status TEXT,receipt TEXT)"
    )
    con.execute("INSERT OR IGNORE INTO gmail_delivery VALUES (?,?,?)",
                ("original-mail", "SENT_VERIFIED", "old-message-id"))
    con.commit()
    return con


def _read_mail(path):
    with sqlite3.connect(path) as con:
        return dict(con.execute(
            "SELECT decision_id,status FROM gmail_delivery ORDER BY decision_id"
        ).fetchall())


def _setup(tmp_path, monkeypatch):
    home = tmp_path / "home"
    app = home / "Library/Application Support/FrankMeme"
    plists = home / "Library/LaunchAgents"
    control = tmp_path / "control"
    prod = home / "Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1"
    old_agent = home / "Documents/ChatGPT/frank-meme-main/crypto-300-profit-mission/local-agent"
    venv = tmp_path / "venv"
    for dir_ in (app, plists, control, prod, old_agent, venv):
        dir_.mkdir(parents=True, exist_ok=True)
    (venv / "bin").mkdir()
    (venv / "bin/python").write_text("isolated-python-fixture")
    (prod / "forward.sqlite").write_bytes(b"PRODUCTION_WRITER_LEDGER_UNTOUCHED")
    (prod / "health.json").write_text('{"status":"RUNNING"}')
    (home / ".frank_meme_control_root").write_text(str(control))
    (app / "dashboard_port").write_text("8766")
    approved = json.dumps({
        "status": "FROZEN_APPROVED", "live_delivery_approved": True,
        "decision": {"observation_retention_seconds": 5184000}
    }, sort_keys=True)
    (app / "follow_policy_v1.approved.json").write_text(approved)
    (app / "approved_policy_sha256").write_text(
        hashlib.sha256(approved.encode()).hexdigest()
    )
    (app / "solana_rpc_urls").write_text("private-placeholder-do-not-log")
    names = ("dashboard.sh", "mission-loop.sh")
    original = {}
    for name in names:
        content = "\n".join([
            "#!/bin/sh",
            f'LOCAL_AGENT="{old_agent}"',
            f'VENV="{venv}"',
            f'CONTROL_POINTER="{home / ".frank_meme_control_root"}"',
            "exec echo --live-delivery" if name == "mission-loop.sh" else "exec echo dashboard",
            "",
        ])
        (app / name).write_text(content)
        original[name] = (app / name).read_bytes()
    writer_plist = plists / "com.audit.crypto-monitor-frank-local.plist"
    writer_plist.write_text("unchanged-writer-fixture")
    conn = _sqlite(control / "mission-control.sqlite")
    conn.close()

    monkeypatch.setenv("USER", "audit")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(deploy, "ensure_git_release", lambda agent, sha: ROOT)
    monkeypatch.setattr(deploy, "preflight_import", lambda agent,venv: None)
    monkeypatch.setattr(deploy, "loaded_job", lambda name: 10 if name.endswith(".loop") else 20)
    monkeypatch.setattr(deploy, "cwd_for_pid", lambda pid: old_agent)
    monkeypatch.setattr(deploy, "http_json", lambda port,url:
                        {"delivery_allowed": True, "updated_at":"2026-10-10T00:00:00Z"})
    monkeypatch.setattr(deploy, "check_frank_stable",
                        lambda *args: (SimpleNamespace(verify=lambda *x: None),{}))
    # A successful restore must pass actual integration_health entrypoint.
    # Fake only provider process/HTTP internals, never actual Mac services.
    monkeypatch.setattr(deploy,"integration_health",
                        lambda port,loop,dash,agent,previous_updated=None:
                        {"dashboard_routes":7,"runtime_status":"LIVE","control_status":"OK"})
    restarts=[]
    monkeypatch.setattr(deploy, "restart", lambda label: restarts.append(label))
    return {
        "home":home,"app":app,"control":control,"prod":prod,"old_agent":old_agent,
        "original":original,"names":names,"writer_plist":writer_plist,"restarts":restarts,
    }


def _invoke(monkeypatch, args):
    monkeypatch.setattr("sys.argv", [str(DEPLOY), *args])
    deploy.main()


def test_apply_failure_uses_real_backup_restore_and_keeps_append_only_receipts(tmp_path,monkeypatch):
    state=_setup(tmp_path,monkeypatch)
    app=state["app"]
    before_policy=(app/"follow_policy_v1.approved.json").read_bytes()
    before_secret=(app/"solana_rpc_urls").read_bytes()
    before_writer=state["writer_plist"].read_bytes()
    before_prod=(state["prod"]/"forward.sqlite").read_bytes()
    expected_head="a"*40

    def inject_post_restart_failure(port,loop_label,dash_label,agent,previous_updated=None):
        if agent != state["old_agent"]:
            # Simulate a failed new-code boot after both mocked restarts.
            assert all('LOCAL_AGENT="' + str(HERE) + '"' in
                       (app/name).read_text() for name in state["names"])
            with sqlite3.connect(state["control"]/"mission-control.sqlite") as conn:
                conn.execute("INSERT INTO gmail_delivery VALUES (?,?,?)",
                             ("new-mail", "SENT_VERIFIED", "new-message-id"))
            raise RuntimeError("SIMULATED_NEW_RELEASE_HEALTH_FAILURE")
        # The restored old runner should be validated separately and healthy.
        assert all('LOCAL_AGENT="' + str(state["old_agent"]) + '"' in
                   (app/name).read_text() for name in state["names"])
        return {"dashboard_routes":7,"control_status":"OK","runtime_status":"LIVE"}

    monkeypatch.setattr(deploy,"integration_health",inject_post_restart_failure)
    with pytest.raises(RuntimeError, match="SIMULATED_NEW_RELEASE_HEALTH_FAILURE"):
        _invoke(monkeypatch,[
            "--apply", "--expected-head", expected_head, "--confirm",deploy.CONFIRM
        ])
    assert {name:(app/name).read_bytes() for name in state["names"]}==state["original"]
    assert state["restarts"]==[
        "com.audit.frank-meme.dashboard","com.audit.frank-meme.loop",
        "com.audit.frank-meme.dashboard","com.audit.frank-meme.loop"
    ]
    backups=list((app/"deploy-backups").glob("pr29-*"))
    assert len(backups)==1
    backup=backups[0]
    assert {name:(backup/name).read_bytes() for name in state["names"]}==state["original"]
    # WAL-safe backup taken before simulated new receipt, never restored onto
    # live state during fallback. Prior + new delivery identity survive exactly.
    assert _read_mail(backup/"mission-control.sqlite")=={"original-mail":"SENT_VERIFIED"}
    assert _read_mail(state["control"]/"mission-control.sqlite")=={
        "original-mail":"SENT_VERIFIED","new-mail":"SENT_VERIFIED"
    }
    assert (app/"follow_policy_v1.approved.json").read_bytes()==before_policy
    assert (app/"solana_rpc_urls").read_bytes()==before_secret
    assert state["writer_plist"].read_bytes()==before_writer
    assert (state["prod"]/"forward.sqlite").read_bytes()==before_prod
    assert sqlite3.connect(backup/"mission-control.sqlite").execute(
        "PRAGMA quick_check"
    ).fetchone()[0]=="ok"


def test_failed_preflight_does_not_switch_runner_or_restart(tmp_path,monkeypatch):
    state=_setup(tmp_path,monkeypatch)
    monkeypatch.setattr(deploy,"preflight_import",lambda *args:deploy.abort("ISOLATED_PREFLIGHT_REJECT"))
    with pytest.raises(RuntimeError,match="ISOLATED_PREFLIGHT_REJECT"):
        _invoke(monkeypatch,[
            "--apply","--expected-head","b"*40,"--confirm",deploy.CONFIRM
        ])
    assert {name:(state["app"]/name).read_bytes() for name in state["names"]}==state["original"]
    assert state["restarts"]==[]
    assert _read_mail(state["control"]/"mission-control.sqlite")=={"original-mail":"SENT_VERIFIED"}


def test_explicit_rollback_only_restores_runners_not_database(tmp_path,monkeypatch):
    state=_setup(tmp_path,monkeypatch)
    app=state["app"]
    backup=(app/"deploy-backups"/"pr29-rehearsal")
    backup.mkdir(parents=True)
    for name,data in state["original"].items():
        (backup/name).write_bytes(data)
        (app/name).write_text(f'LOCAL_AGENT="{HERE}"\n')
    with sqlite3.connect(state["control"]/"mission-control.sqlite") as conn:
        conn.execute("INSERT INTO gmail_delivery VALUES (?,?,?)",
                     ("new-mail","SENT_VERIFIED","new-message"))
    _invoke(monkeypatch,["--rollback","--backup",str(backup),"--confirm",deploy.CONFIRM])
    assert {name:(app/name).read_bytes() for name in state["names"]}==state["original"]
    assert _read_mail(state["control"]/"mission-control.sqlite")=={
        "original-mail":"SENT_VERIFIED","new-mail":"SENT_VERIFIED"
    }
    assert state["restarts"]==[
        "com.audit.frank-meme.dashboard","com.audit.frank-meme.loop"
    ]


def test_no_confirm_cannot_mutate_isolated_services(tmp_path,monkeypatch):
    state=_setup(tmp_path,monkeypatch)
    with pytest.raises(RuntimeError,match="USAGE_REQUIRES_EXPLICIT_APPLY_OR_ROLLBACK_CONFIRMATION"):
        _invoke(monkeypatch,["--apply","--expected-head","c"*40])
    assert state["restarts"]==[]
    assert {name:(state["app"]/name).read_bytes() for name in state["names"]}==state["original"]



def test_old_release_mission_delivery_ignores_new_manual_review_rows(tmp_path):
    """Check real frozen legacy delivery selectors after an isolated fallback.

    This only proves MANUAL_REVIEW exclusion, NOT every possible old/new schema
    transition. No OAuth provider or platform notification is actually invoked.
    """
    import types
    from mission_agent.mission_control.db import ControlDB
    from mission_agent.mission_control.delivery import GmailDelivery, LocalDelivery
    from test_mission_control_delivery import event

    old_source = subprocess.check_output(
        ["git", "-C", str(ROOT), "show",
         "49d5d3b7122efa41dd74ba6ede0c5d225309988c:"
         "crypto-300-profit-mission/local-agent/mission_agent/mission_control/delivery.py"],
        text=True,
    )
    legacy=types.ModuleType("mission_agent.mission_control._legacy_delivery")
    legacy.__package__="mission_agent.mission_control"
    exec(compile(old_source,"<frozen-legacy-delivery>", "exec"),legacy.__dict__)

    control=ControlDB(tmp_path/"control.sqlite")
    e=event(control)
    LocalDelivery(control,run=lambda *a,**k:None).enqueue(e,forbidden=False)
    GmailDelivery(control).enqueue(e,mode="LIVE",forbidden=False)
    decision=e["decision_id"]
    control.db.execute(
        "UPDATE local_delivery SET status='MANUAL_REVIEW' WHERE decision_id=?",
        (decision,)
    )
    control.db.execute(
        "UPDATE gmail_delivery SET status='MANUAL_REVIEW' WHERE decision_id=?",
        (decision,)
    )
    control.db.execute(
        "UPDATE decision_outbox SET status='MANUAL_REVIEW' WHERE decision_id=?",
        (decision,)
    )

    class NoCalls:
        recipient="owner@example.invalid"
        def ready(self):raise AssertionError("legacy provider should not be called")
        def find_sent(self,*x):raise AssertionError("legacy provider should not be called")
        def get(self,*x):raise AssertionError("legacy provider should not be called")
        def send(self,*x):raise AssertionError("legacy provider must not send")
    legacy.LocalDelivery(control,run=lambda *a,**kw:
                         (_ for _ in ()).throw(AssertionError("must not show local alert"))).drain()
    legacy.GmailDelivery(control).drain(NoCalls())
    for table in ("gmail_delivery","local_delivery"):
        assert control.db.execute(f"SELECT status FROM {table} WHERE decision_id=?",
                                  (decision,)).fetchone()[0]=="MANUAL_REVIEW"
    assert set(x["status"] for x in control.db.execute(
        "SELECT status FROM decision_outbox WHERE decision_id=?",(decision,)
    ))=={"MANUAL_REVIEW"}
    control.close()



def test_rollback_runtime_health_failure_is_not_claimed_as_success(
    tmp_path,monkeypatch,capsys,
):
    """A successful kickstart is NOT enough to report rollback success."""
    state=_setup(tmp_path,monkeypatch)
    app=state["app"]
    backup=app/"deploy-backups"/"pr29-unhealthy"
    backup.mkdir(parents=True)
    for name,data in state["original"].items():
        (backup/name).write_bytes(data)
        (app/name).write_text(f'LOCAL_AGENT="{HERE}"\n')
    monkeypatch.setattr(
        deploy,"integration_health",
        lambda *args,**kwargs:deploy.abort("ROLLBACK_HEALTH_CHECK_FAILED"),
    )
    with pytest.raises(RuntimeError,match="ROLLBACK_HEALTH_CHECK_FAILED"):
        _invoke(monkeypatch,[
            "--rollback","--backup",str(backup),"--confirm",deploy.CONFIRM
        ])
    assert "RUNNERS_RESTORED=YES" not in capsys.readouterr().out
    assert {name:(app/name).read_bytes() for name in state["names"]}==state["original"]
    assert state["restarts"]==[
        "com.audit.frank-meme.dashboard","com.audit.frank-meme.loop"
    ]


def test_rollback_invalid_runner_backup_never_changes_any_active_file(
    tmp_path,monkeypatch,
):
    state=_setup(tmp_path,monkeypatch)
    app=state["app"]
    backup=app/"deploy-backups"/"pr29-invalid"
    backup.mkdir(parents=True)
    for name,data in state["original"].items():
        (backup/name).write_bytes(data)
    injected=(backup/"mission-loop.sh").read_text().replace(
        str(state["old_agent"]),"/tmp/unknown-agent/crypto-300-profit-mission/local-agent"
    )
    (backup/"mission-loop.sh").write_text(injected)
    with pytest.raises(RuntimeError,match="ROLLBACK_BACKUP_SOURCE_MISMATCH"):
        _invoke(monkeypatch,[
            "--rollback","--backup",str(backup),"--confirm",deploy.CONFIRM
        ])
    assert state["restarts"]==[]
    assert {name:(app/name).read_bytes() for name in state["names"]}==state["original"]


def test_rollback_validation_requires_heartbeat_advance_when_prior_exists(
    tmp_path,monkeypatch,
):
    state=_setup(tmp_path,monkeypatch)
    app=state["app"]
    backup=app/"deploy-backups"/"pr29-freshness"
    backup.mkdir(parents=True)
    for name,data in state["original"].items():
        (backup/name).write_bytes(data)
    checked=[]
    def probe(port,loop,dash,agent,previous_updated=None):
        checked.append((port,agent,previous_updated))
        if previous_updated is None:
            raise AssertionError("MUST_REQUIRE_HEARTBEAT_ADVANCE")
        return {"dashboard_routes":7}
    monkeypatch.setattr(deploy,"integration_health",probe)
    _invoke(monkeypatch,[
        "--rollback","--backup",str(backup),"--confirm",deploy.CONFIRM
    ])
    assert checked==[(8766,state["old_agent"],"2026-10-10T00:00:00Z")]



def test_real_integration_health_rejects_pre_rollback_heartbeat(
    tmp_path,monkeypatch,
):
    """Exercise the real integration_health predicate with mocked HTTP/jobs."""
    agent=tmp_path/"old-agent"
    agent.mkdir()
    monkeypatch.setattr(deploy,"TIMEOUT_SECONDS",0.02)
    monkeypatch.setattr(deploy.time,"sleep",lambda _:None)
    monkeypatch.setattr(deploy,"loaded_job",lambda label:1 if label.endswith(".loop") else 2)
    monkeypatch.setattr(deploy,"cwd_for_pid",lambda pid:agent)
    called=[]
    def http(port,path):
        called.append(path)
        if path=="/api/control-health":
            return {"status":"OK","delivery_allowed":True,"updated_at":"OLD_HEARTBEAT"}
        if path=="/api/runtime":
            return {"status":"LIVE"}
        if path=="/api/coverage":
            return {"scope":"LOCAL_INDEX_ONLY","status":"OK"}
        return []
    monkeypatch.setattr(deploy,"http_json",http)
    with pytest.raises(RuntimeError,match="INTEGRATION_CHECK_TIMEOUT"):
        deploy.integration_health(8766,"test.loop","test.dashboard",
                                  agent,previous_updated="OLD_HEARTBEAT")
    assert "/api/control-health" in called


def test_real_integration_health_accepts_new_healthy_old_loop(
    tmp_path,monkeypatch,
):
    agent=tmp_path/"old-agent"
    agent.mkdir()
    monkeypatch.setattr(deploy,"loaded_job",lambda label:1 if label.endswith(".loop") else 2)
    monkeypatch.setattr(deploy,"cwd_for_pid",lambda pid:agent)
    def http(port,path):
        if path=="/api/control-health":
            return {"status":"OK","delivery_allowed":True,"updated_at":"NEW_HEARTBEAT"}
        if path=="/api/runtime":
            return {"status":"LIVE"}
        if path=="/api/coverage":
            return {"scope":"LOCAL_INDEX_ONLY","status":"OK"}
        return []
    monkeypatch.setattr(deploy,"http_json",http)
    outcome=deploy.integration_health(8766,"test.loop","test.dashboard",
                                      agent,previous_updated="OLD_HEARTBEAT")
    assert outcome["dashboard_routes"]==7
    assert outcome["control_status"]=="OK"
    assert outcome["runtime_status"]=="LIVE"
