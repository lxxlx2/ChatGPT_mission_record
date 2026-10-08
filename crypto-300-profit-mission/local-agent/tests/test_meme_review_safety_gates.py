"""Isolated behavioral checks for replay safety and installer policy authority."""
import json
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import frank_v1_replay


def test_frank_v1_replay_report_rejects_null_outbox_at_runtime(tmp_path):
    db=sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE signatures(body TEXT);
        CREATE TABLE signals(signal_id TEXT,created_at TEXT,body TEXT);
        CREATE TABLE v1_evaluations(id INTEGER);
        CREATE TABLE outbox(status TEXT);
        INSERT INTO outbox VALUES(NULL);
    """)
    engine=SimpleNamespace(db=db,summary=lambda:{})
    destination=tmp_path/"report.json"
    with pytest.raises(ValueError,match="HISTORICAL_DELIVERY_MUST_BE_DISABLED"):
        frank_v1_replay.report(engine,destination)
    assert not destination.exists()
    db.execute("DELETE FROM outbox")
    db.execute("INSERT INTO outbox VALUES('DRY_RUN_AUDIT')")
    frank_v1_replay.report(engine,destination)
    assert json.loads(destination.read_text())["notifications_sent"]==0
    db.close()



def run_installer_isolated(tmp_path, *, status="FROZEN_APPROVED",
                           live=True, retention=5184000,
                           hash_mismatch=False, no_approval=False,
                           confirm=True):
    """Execute real installer/Python policy gate, mock all external side effects.

    Existing on-disk approved files are fingerprinted before the run. Any
    rejection must leave them intact (including RPC secret and runners).
    """
    import hashlib, subprocess
    installer=Path(__file__).parents[1]/"scripts"/"install_mission_meme_launchd.sh"
    home=tmp_path/"home";home.mkdir()
    worktree=tmp_path/"worktree";worktree.mkdir()
    (worktree/".git").mkdir()
    # Import real policy authorization; this is NOT a fake policy gate.
    local=Path(__file__).parents[1]
    prod=tmp_path/"prod";prod.mkdir()
    (prod/"forward.sqlite").write_bytes(b"synthetic-never-opened")
    (prod/"health.json").write_text('{"status":"RUNNING"}')
    venv=tmp_path/"venv";(venv/"bin").mkdir(parents=True)
    py=venv/"bin"/"python"
    py.write_text(chr(10).join([
        "#!"+sys.executable,
        "import sys",
        "script=sys.stdin.read()",
        "if 'POLICY_GATE: PASS' in script:",
        "    sys.argv=['-',*sys.argv[2:]]",
        "    exec(compile(script,'<real-policy-gate>','exec'))",
        "else:",
        "    print('GMAIL_PREFLIGHT: ISOLATED_MOCK')",
        "",
    ]))
    py.chmod(0o700)
    control=tmp_path/"control";control.mkdir()
    pointer=tmp_path/"pointer";pointer.write_text(str(control))
    candidate=tmp_path/"candidate-policy.json"
    candidate.write_text(json.dumps({
        "schema_version":1,"policy_id":"FOLLOW_POLICY_REVIEW",
        "status":status,"live_delivery_approved":live,
        "decision":{"observation_retention_seconds":retention}
    },sort_keys=True))
    approved=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if hash_mismatch:approved="0"*64 if approved!="0"*64 else "1"*64
    fakebin=tmp_path/"fakebin";fakebin.mkdir()
    log=tmp_path/"launchctl.log"
    fake=(fakebin/"launchctl")
    fake.write_text(chr(10).join([
        "#!/bin/sh",'echo "$*" >> "$FAKE_LAUNCH_LOG"',"",
    ]))
    fake.chmod(0o700)
    for exe,contents in [("sleep",["#!/bin/sh","exit 0",""]),
                         ("curl",["#!/bin/sh","echo 200",""])]:
        p=fakebin/exe;p.write_text(chr(10).join(contents));p.chmod(0o700)
    # Seed the old approved state to prove rejected requests cause NO mutations.
    app=home/"Library"/"Application Support"/"FrankMeme";app.mkdir(parents=True)
    baseline_files={
        "follow_policy_v1.approved.json":b"PREVIOUS_APPROVED_POLICY",
        "approved_policy_sha256":b"PREVIOUS_APPROVED_DIGEST",
        "solana_rpc_urls":b"https://old.example.invalid/?api-key=PREVIOUS_SECRET",
        "dashboard_port":b"8766\\n",
        "mission-loop.sh":b"PREVIOUS_RUNNER",
        "dashboard.sh":b"PREVIOUS_DASHBOARD",
    }
    for name,data in baseline_files.items():(app/name).write_bytes(data)
    before={name:(app/name).read_bytes() for name in baseline_files}
    env={**os.environ,"HOME":str(home),"WORKTREE":str(worktree),
         "LOCAL_AGENT":str(local),"PROD":str(prod),"VENV":str(venv),
         "CONTROL_POINTER":str(pointer),"POLICY":str(candidate),
         "SOLANA_RPC_URLS":"https://new.example.invalid/?api-key=NEW_SECRET",
         "PATH":str(fakebin)+os.pathsep+os.environ["PATH"],
         "FAKE_LAUNCH_LOG":str(log)}
    if confirm:env["CONFIRM_MISSION_LOOP_RESTART"]="1"
    else:env.pop("CONFIRM_MISSION_LOOP_RESTART",None)
    if not no_approval:env["APPROVED_POLICY_SHA256"]=approved
    else:env.pop("APPROVED_POLICY_SHA256",None)
    result=subprocess.run(["bash",str(installer)],env=env,
                          capture_output=True,text=True,timeout=20)
    after={name:(app/name).read_bytes() for name in baseline_files}
    return result,before,after,log,app,approved


@pytest.mark.parametrize("overrides",[
    {"status":"REVIEW_ONLY"},
    {"live":False},
    {"retention":1},
    {"hash_mismatch":True},
    {"no_approval":True},
    {"confirm":False},
])
def test_installer_denies_each_policy_authority_violation_without_any_mutations(tmp_path,overrides):
    result,before,after,log,app,approved=run_installer_isolated(tmp_path,**overrides)
    assert result.returncode!=0
    assert before==after
    assert not log.exists()
    assert "NEW_SECRET" not in result.stdout+result.stderr
    if overrides.get("hash_mismatch") or overrides.get("status") or (
        overrides.get("live") is False) or overrides.get("retention")==1:
        assert "POLICY_NOT_AUTHORIZED" in result.stderr
    elif overrides.get("no_approval"):
        assert "EXTERNAL_POLICY_APPROVAL_REQUIRED" in result.stderr
    else:
        assert "MISSION_LOOP_RESTART_NOT_AUTHORIZED" in result.stderr


def test_installer_valid_externally_pinned_policy_runs_real_gate_before_mocked_oauth_and_launchd(tmp_path):
    result,before,after,log,app,approved=run_installer_isolated(tmp_path)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert "POLICY_GATE: PASS" in result.stdout
    assert log.exists()
    assert "bootstrap" in log.read_text() and "kickstart" in log.read_text()
    assert (app/"approved_policy_sha256").read_text().strip()==approved
    assert (app/"solana_rpc_urls").stat().st_mode & 0o077==0
    assert (app/"follow_policy_v1.approved.json").read_bytes()!=before["follow_policy_v1.approved.json"]
    assert "NEW_SECRET" not in result.stdout+result.stderr


def test_frank_v1_replay_outbox_rejects_pending_and_missing_table(tmp_path):
    import subprocess
    db=sqlite3.connect(":memory:")
    db.executescript("CREATE TABLE signatures(body TEXT); CREATE TABLE signals(signal_id TEXT,created_at TEXT,body TEXT); CREATE TABLE v1_evaluations(id INTEGER); CREATE TABLE outbox(status TEXT);")
    engine=SimpleNamespace(db=db,summary=lambda:{})
    db.execute("INSERT INTO outbox VALUES('PENDING_SEND')")
    with pytest.raises(ValueError,match="HISTORICAL_DELIVERY_MUST_BE_DISABLED"):
        frank_v1_replay.report(engine,tmp_path/"report.json")
    db.execute("DROP TABLE outbox")
    with pytest.raises(sqlite3.OperationalError):
        frank_v1_replay.report(engine,tmp_path/"report.json")
    db.close()
