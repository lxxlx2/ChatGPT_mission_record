"""Isolated SQLite acceptance for the PR39 read-only release gate."""
import json
import sqlite3
from pathlib import Path

import pytest

from scripts import frank_pr39_predeploy_readonly as audit


def db_fixture(tmp_path, *, gmail_status="SENT_VERIFIED", local_status="COMMAND_ACCEPTED"):
    control = tmp_path / "control.sqlite"
    db = sqlite3.connect(control)
    db.executescript("""
      CREATE TABLE decision_events(decision_id TEXT PRIMARY KEY);
      CREATE TABLE decision_outbox(channel TEXT,status TEXT);
      CREATE TABLE gmail_delivery(delivery_mode TEXT,status TEXT);
      CREATE TABLE local_delivery(status TEXT);
    """)
    db.execute("INSERT INTO decision_events VALUES('old')")
    db.execute("INSERT INTO gmail_delivery VALUES('LIVE',?)",(gmail_status,))
    db.execute("INSERT INTO local_delivery VALUES(?)",(local_status,))
    db.execute("INSERT INTO decision_outbox VALUES('gmail',?)",(gmail_status,))
    db.execute("INSERT INTO decision_outbox VALUES('local',?)",(local_status,))
    db.commit();db.close()
    prod = tmp_path / "prod.sqlite"
    db = sqlite3.connect(prod)
    db.execute("CREATE TABLE v1_states(person_id TEXT, body TEXT)")
    return control, prod, db


def write_state(db, events):
    db.execute(
        "INSERT INTO v1_states VALUES(?,?)",
        ("frank", json.dumps({"events":events})),
    )
    db.commit()


def buy(**kw):
    return {
        "direction": "BUY", "quote_asset": audit.USDC,
        "quote_quantity": "15000", **kw,
    }


def test_historical_verified_gmail_is_not_classified_as_inflight(tmp_path):
    control, prod, db = db_fixture(tmp_path)
    write_state(db,[buy(amount_predicate="USDC_DIRECT_NUMERIC")]);db.close()
    control_result=audit.control_audit(control)
    assert control_result["historical_live_gmail_count"]==1
    assert control_result["live_gmail_in_flight"]==0
    assert control_result["local_unresolved"]==0
    assert control_result["presentation_table"]=="NOT_YET_CREATED"
    stats=audit.frank_payment_coverage(prod)
    assert stats["latest_buy_direct_usdc_verified"]==1
    assert stats["latest_buy_predicate_missing"]==0


@pytest.mark.parametrize("status", ["PENDING","RETRYABLE_ERROR","CREDENTIAL_BLOCKED","SENDING","SENT_UNVERIFIED"])
def test_unsafe_live_gmail_status_blocks_predeployment(status,tmp_path,monkeypatch,capsys):
    control, prod, db=db_fixture(tmp_path,gmail_status=status)
    write_state(db,[buy(amount_predicate="USDC_DIRECT_NUMERIC")]);db.close()
    monkeypatch.setattr(audit,"approved_source_check",lambda _ : {"reviewed_product_unchanged":True})
    status_code=audit.main(["--source-root",str(tmp_path),
                            "--control-db",str(control),"--frank-db",str(prod)])
    out=json.loads(capsys.readouterr().out)
    assert status_code==3
    assert out["gate"]=="BLOCKED_ACTIVE_DELIVERY_QUEUE"
    assert out["control"]["live_gmail_in_flight"]==1
    assert out["mutated_production"] is False


def test_legacy_direct_usdc_without_predicate_requires_review(tmp_path,monkeypatch,capsys):
    control, prod, db=db_fixture(tmp_path)
    write_state(db,[buy()]);db.close()
    monkeypatch.setattr(audit,"approved_source_check",lambda _ : {"reviewed_product_unchanged":True})
    before=prod.read_bytes()
    status_code=audit.main(["--source-root",str(tmp_path),
                            "--control-db",str(control),"--frank-db",str(prod)])
    out=json.loads(capsys.readouterr().out)
    assert status_code==4
    assert out["gate"]=="REVIEW_REQUIRED_LEGACY_BUY_PREDICATES"
    assert out["frank_amount_coverage"]["legacy_usdc_quote_predicate_missing"]==1
    assert out["frank_amount_coverage"]["latest_buy_predicate_missing"]==1
    assert before==prod.read_bytes()


def test_success_gate_with_explicit_legacy_history_preserved(tmp_path,monkeypatch,capsys):
    control, prod, db=db_fixture(tmp_path)
    write_state(db,[buy(amount_predicate="USDC_DIRECT_NUMERIC")]);db.close()
    monkeypatch.setattr(audit,"approved_source_check",lambda _ : {"reviewed_product_unchanged":True})
    code=audit.main(["--source-root",str(tmp_path),
                     "--control-db",str(control),"--frank-db",str(prod)])
    out=json.loads(capsys.readouterr().out)
    assert code==0
    assert out["gate"]=="PASS_READ_ONLY_PREDEPLOY"
    assert out["control"]["historical_live_gmail_count"]==1


def test_present_schema_mismatch_fails_closed(tmp_path):
    control, prod, db=db_fixture(tmp_path)
    write_state(db,[buy(amount_predicate="USDC_DIRECT_NUMERIC")]);db.close()
    con=sqlite3.connect(control)
    con.execute("CREATE TABLE local_delivery_presentation(wrong TEXT)")
    con.commit();con.close()
    with pytest.raises(ValueError,match="LOCAL_PRESENTATION_SCHEMA_UNEXPECTED"):
        audit.control_audit(control)


def test_missing_database_does_not_create_file(tmp_path):
    missing=tmp_path/"missing.sqlite"
    with pytest.raises(ValueError,match="DATABASE_FILE_UNAVAILABLE"):
        audit.readonly_connect(missing)
    assert not missing.exists()


def test_last_buy_only_and_uncertain_fields(tmp_path):
    _, prod, db=db_fixture(tmp_path)
    write_state(db,[
        buy(amount_predicate="USDC_DIRECT_NUMERIC"),
        {"direction":"SELL","quote_asset":audit.USDC},
        buy(amount_predicate="UNDETERMINED",amount_predicate_reason="COMPOSITE_QUOTE_LEGS"),
        {"direction":"SELL"},
    ])
    db.close()
    stats=audit.frank_payment_coverage(prod)
    assert stats["states_with_buy"]==1
    assert stats["latest_buy_explicitly_uncertain"]==1
    assert stats["latest_buy_direct_usdc_verified"]==0
