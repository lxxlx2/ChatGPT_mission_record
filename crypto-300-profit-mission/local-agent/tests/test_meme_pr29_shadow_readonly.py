"""Offline contract tests for the Mac release read-only snapshot/parity gate."""
import importlib.util
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/accept_meme_pr29_shadow_readonly.py"
spec=importlib.util.spec_from_file_location("pr29_shadow_readonly",SCRIPT)
shadow=importlib.util.module_from_spec(spec)
spec.loader.exec_module(shadow)


def test_sqlite_online_backup_never_writes_source(tmp_path):
    source=tmp_path/"writer.sqlite"
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE ledger (id INTEGER PRIMARY KEY, status TEXT)")
        db.execute("INSERT INTO ledger VALUES(1,'SENT_VERIFIED')")
    original=source.read_bytes()
    out=tmp_path/"snapshot.sqlite"
    shadow.snapshot(source,out)
    assert out.is_file()
    assert source.read_bytes()==original
    assert out.stat().st_mode & 0o077==0
    with sqlite3.connect(out) as db:
        assert db.execute("SELECT status FROM ledger").fetchone()[0]=="SENT_VERIFIED"
        db.execute("INSERT INTO ledger(status) VALUES('MANUAL_REVIEW')")
    with sqlite3.connect(source) as db:
        assert db.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]==1
    with pytest.raises(ValueError,match="SQLITE_SOURCE_NOT_REGULAR"):
        shadow.snapshot(tmp_path/"nonexistent.sqlite",tmp_path/"should_not_exist.sqlite")
    assert not (tmp_path/"should_not_exist.sqlite").exists()


def test_readonly_shadow_comparison_reports_every_semantic_change():
    old={"rows":[
        {"identity_hash":"a","candidate_hash":"X","decision_hashes":["m","n"]},
        {"identity_hash":"b","candidate_hash":"Y","decision_hashes":["m","n"]},
        {"identity_hash":"c","candidate_hash":"Z","decision_hashes":["m","n"]},
    ]}
    new={"rows":[
        {"identity_hash":"a","candidate_hash":"X","decision_hashes":["m","n"]},
        {"identity_hash":"b","candidate_hash":"DIFFERENT","decision_hashes":["m","n"]},
        {"identity_hash":"d","candidate_hash":"Z","decision_hashes":["m","DIFFERENT"]},
    ]}
    result=shadow.compare(old,new)
    assert result["status"]=="REVIEW_DELTAS"
    assert result["identity_added"]==1
    assert result["identity_missing"]==1
    assert result["candidate_payload_differences"]==1
    assert result["decision_vector_differences"]==0
    # Different decision vector alone also fails, even with same candidate.
    new["rows"][1]["candidate_hash"]="Y"
    new["rows"][1]["decision_hashes"]=["m","changed"]
    changed=shadow.compare(old,new)
    assert changed["decision_vector_differences"]==1


def test_shadow_worker_real_synthetic_ledger_uses_only_pure_evaluate(tmp_path):
    from test_mission_control_service import make_prod,policy
    local=SCRIPT.parents[1]
    prod=tmp_path/"prod"
    make_prod(prod)
    approved=tmp_path/"review-policy.json"
    policy(approved)
    a=shadow._run_worker(local,prod,approved,1791580700.0)
    b=shadow._run_worker(local,prod,approved,1791580700.0)
    assert a==b
    assert a["candidate_count"]>=1
    assert all(len(item["decision_hashes"])==5 for item in a["rows"])
    assert shadow.compare(a,b)["status"]=="PASS"
    assert not (prod/"mission-control.sqlite").exists()
    assert not (prod/"sol-normalized-v1.sqlite").exists()


def test_script_has_explicit_no_live_provider_or_restart_paths():
    source=SCRIPT.read_text()
    for forbidden in (
        "MissionMemeService(", "GmailDelivery(", "LocalDelivery(",
        "launchctl", "kickstart", "provider.send(", "send_email(",
        "swap_transaction", "private_key", "os.system(",
    ):
        assert forbidden not in source
    assert "?mode=ro" in source
    assert "PR_RELEASE_NOT_DETACHED" in source
    assert "SYNTHETIC_PARITY_ONLY_NOT_A_JUPITER_QUOTE" in source
    assert '"network_quote_called":False' in source
    assert "DATA" not in shadow.compare({"rows":[]},{"rows":[]})["status"]
