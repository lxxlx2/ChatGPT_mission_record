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


def test_installer_real_policy_gate_rejects_unapproved_policy_before_external_calls(tmp_path):
    """The real inline POLICY_GATE executes; OAuth, curl and launchctl do not."""
    installer=Path(__file__).parents[1]/"scripts"/"install_mission_meme_launchd.sh"
    home=tmp_path/"home";home.mkdir()
    worktree=tmp_path/"worktree";worktree.mkdir()
    (worktree/".git").mkdir()
    local=worktree/"crypto-300-profit-mission"/"local-agent";local.mkdir(parents=True)
    prod=tmp_path/"prod";prod.mkdir()
    (prod/"forward.sqlite").write_bytes(b"synthetic-never-opened")
    (prod/"health.json").write_text('{"status":"RUNNING"}')
    venv=tmp_path/"venv";(venv/"bin").mkdir(parents=True)
    # Inline policy preflight runs actual Python logic. An OAuth preflight
    # attempt is actively blocked even if the policy guard is removed.
    mock_python=venv/"bin"/"python"
    mock_python.write_text(
        "#!"+sys.executable+"\n"
        "import sys\n"
        "code=sys.stdin.read()\n"
        "if 'POLICY_GATE: PASS' not in code:\n"
        "    raise SystemExit('EXTERNAL_OAUTH_PREFLIGHT_FORBIDDEN')\n"
        "sys.argv=['-',sys.argv[2],sys.argv[3]]\n"
        "exec(compile(code,'<policy-gate>','exec'))\n"
    )
    mock_python.chmod(0o700)
    control=tmp_path/"control";control.mkdir()
    pointer=tmp_path/"pointer";pointer.write_text(str(control))
    invalid=tmp_path/"unapproved-policy.json"
    invalid.write_text(json.dumps({
        "status":"REVIEW_ONLY",
        "live_delivery_approved":True,
        "decision":{"observation_retention_seconds":5184000}
    }))
    fakebin=tmp_path/"fake-bin";fakebin.mkdir()
    launch_log=tmp_path/"launchctl.log"
    launchctl=fakebin/"launchctl"
    launchctl.write_text('#!/bin/sh\nprintf "LAUNCHCALLED\\n" >> "$FAKE_LAUNCH_LOG"\n')
    launchctl.chmod(0o700)
    env={**os.environ,"HOME":str(home),"WORKTREE":str(worktree),
         "LOCAL_AGENT":str(local),"PROD":str(prod),"VENV":str(venv),
         "CONTROL_POINTER":str(pointer),"POLICY":str(invalid),
         "CONFIRM_MISSION_LOOP_RESTART":"1",
         "SOLANA_RPC_URLS":"https://rpc.example.invalid/?api-key=FAKE_ONLY",
         "PATH":str(fakebin)+os.pathsep+os.environ["PATH"],
         "FAKE_LAUNCH_LOG":str(launch_log)}
    result=__import__("subprocess").run(["bash",str(installer)],env=env,
                                         capture_output=True,text=True,timeout=15)
    assert result.returncode!=0
    assert "AssertionError" in result.stderr
    assert "POLICY_GATE: PASS" not in result.stdout
    assert "EXTERNAL_OAUTH_PREFLIGHT_FORBIDDEN" not in result.stderr
    assert not launch_log.exists()
    assert "FAKE_ONLY" not in result.stdout+result.stderr
