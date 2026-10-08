"""Behavioral regression for acceptance under both legitimate Frank writer schemas.

All data are isolated fixtures. This does not run the live production writer.
"""
import json
import sqlite3
from pathlib import Path

import pytest

from mission_agent.signals.store import Ledger
from scripts.meme_acceptance_integrity import capture, verify, STABLE_HEALTH_KEYS


LEDGER_STABLE = {
    "system": "FRANK_ONLY",
    "policy": "FRANK_LOCAL_SIGNAL_V1",
    "policy_hash": "83ebab1fbb8ec7e03950626137c5597a38b81b8a4085d9150610018cc78cedab",
    "identifier": "com.jerson.crypto-monitor-frank-local",
    "code_commit": "b" * 40,
    "loaded_source_sha256": "c" * 64,
    "delivery_authority": "LOCAL_DETERMINISTIC_SIGNAL",
    "gpt_in_critical_path": False,
    "production_trading": "NO_GO",
    "other_persons": "DEFERRED",
    "new_automation": False,
    "poll_interval_seconds": 30,
    "source_drift": False,
}


def _prod(tmp_path):
    prod = tmp_path / "fake-prod"
    prod.mkdir()
    ledger = Ledger(prod / "forward.sqlite")
    # Engine initializes v1_states when the real Ledger writer runs.
    ledger.db.execute("CREATE TABLE IF NOT EXISTS v1_states(person_id TEXT,mint TEXT,body TEXT,PRIMARY KEY(person_id,mint))")
    ledger.db.execute(
        """INSERT INTO signatures (
             wallet,signature,person_id,slot,block_time,seen_at,classified_at,
             raw_hash,raw_reference,body,alert_state,alert_reason
           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("wallet", "baseline", "frank", 10, 100, "t1", "t1",
         "hash", "raw1", "{}", "NO", "FIXTURE"),
    )
    ledger.db.commit()
    ledger.db.close()
    health = prod / "health.json"
    health.write_text(json.dumps({
        **LEDGER_STABLE,
        "status": "RUNNING", "last_poll_at": "t1", "poll_count": 1,
        "consecutive_errors": 0, "last_processed_signature": "baseline",
        "new_signatures": 1, "lag_seconds": 0, "model": {"active": 1},
    }))
    loop = tmp_path / "loop.plist"
    dash = tmp_path / "dashboard.plist"
    loop.write_text("loop")
    dash.write_text("dashboard")
    return prod, health, loop, dash


def test_real_ledger_health_contract_polling_and_append_does_not_false_fail(tmp_path):
    prod, health, loop, dash = _prod(tmp_path)
    assert set(LEDGER_STABLE) <= STABLE_HEALTH_KEYS
    baseline = capture(prod, loop, dash)
    # Seven running iterations with source-writer fields and new signatures.
    for i in range(2, 9):
        current = json.loads(health.read_text())
        current.update(
            status="RETRY_PENDING" if i == 5 else "RUNNING",
            last_poll_at=f"t{i}", poll_count=i, consecutive_errors=1 if i == 5 else 0,
            last_successful_poll=f"success-{i}",
            last_model_successful_eval=f"eval-{i}", source_drift=False,
            last_processed_signature=f"sig{i}", last_processed_slot=10 + i,
            new_signatures=i, lag_seconds=i % 3,
            model={"signal_count": i}, raw_pending=i,
            local_pending=i, model_unprocessed=i, uptime_seconds=str(i * 30),
        )
        health.write_text(json.dumps(current))
        with sqlite3.connect(prod / "forward.sqlite") as db:
            db.execute(
                """INSERT INTO signatures (
                     wallet,signature,person_id,slot,block_time,seen_at,classified_at,
                     raw_hash,raw_reference,body,alert_state,alert_reason
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("wallet", f"sig{i}", "frank", 10 + i, 100 + i, "t", "t",
                 f"hash-{i}", f"raw-{i}", "{}", "NO", "FIXTURE"),
            )
        assert verify(baseline, prod, loop, dash)["status"] == "PASS"


@pytest.mark.parametrize("key", (
    "policy_hash", "loaded_source_sha256", "code_commit",
    "production_trading", "identifier", "system",
))
def test_ledger_stable_security_config_changes_are_detected(tmp_path, key):
    prod, health, loop, dash = _prod(tmp_path)
    before = capture(prod, loop, dash)
    current = json.loads(health.read_text())
    current[key] = "TAMPERED"
    health.write_text(json.dumps(current))
    with pytest.raises((RuntimeError,ValueError),match="(HEALTH_|IMMUTABLE_LEDGER_OR_STABLE_HEALTH_OR_PLIST_CHANGED)"):
        verify(before, prod, loop, dash)


def test_shadow_writer_stable_fields_still_detected_without_poll_false_positive(tmp_path):
    prod, health, loop, dash = _prod(tmp_path)
    # Separate the synthetic Repository schema from Ledger-owned v1_states.
    with sqlite3.connect(prod / "forward.sqlite") as database:
        database.execute("DROP TABLE v1_states")
    shadow = {
        "identifier": "com.jerson.crypto-monitor-frank-shadow",
        "service_source_sha256": "a" * 64,
        "parser_version": "frank-v8",
        "historical_network_backfill": "BOUNDED300S_IDLE_WINDOW_ONLY",
        "gmail": 0, "app_alert": 0, "automation_mutations": 0,
        "production_writes": 0,
        "last_poll_at": "t1", "request_count": 1,
    }
    health.write_text(json.dumps(shadow))
    before = capture(prod, loop, dash)
    for n in range(2, 9):
        shadow.update(last_poll_at=f"t{n}", request_count=n,
                      poll_seconds=f"{n}.2", candidate_duplicate_count=n)
        health.write_text(json.dumps(shadow))
        assert verify(before, prod, loop, dash)["status"] == "PASS"
    shadow["production_writes"] = 1
    health.write_text(json.dumps(shadow))
    with pytest.raises((RuntimeError,ValueError),match="(HEALTH_|IMMUTABLE_LEDGER_OR_STABLE_HEALTH_OR_PLIST_CHANGED)"):
        verify(before, prod, loop, dash)


@pytest.mark.parametrize("remove_key", ["policy_hash","code_commit","loaded_source_sha256","source_drift","identifier"])
def test_ledger_missing_authority_field_is_denied_at_capture(tmp_path, remove_key):
    prod,health,loop,dash=_prod(tmp_path)
    value=json.loads(health.read_text())
    del value[remove_key]
    health.write_text(json.dumps(value))
    with pytest.raises(ValueError,match="HEALTH_"):
        capture(prod,loop,dash)


def test_ledger_profile_unknown_or_repository_mismatch_denied(tmp_path):
    prod,health,loop,dash=_prod(tmp_path)
    health.write_text(json.dumps({"status":"RUNNING","poll_count":10}))
    with pytest.raises(ValueError,match="HEALTH_WRITER_PROFILE_UNSUPPORTED"):
        capture(prod,loop,dash)
    health.write_text(json.dumps({"identifier":"com.jerson.crypto-monitor-frank-shadow",
                                  "status":"RUNNING"}))
    with pytest.raises(ValueError,match="HEALTH_REQUIRED_STABLE_FIELDS_MISSING"):
        capture(prod,loop,dash)


def test_ledger_source_drift_and_pre_capture_policy_mismatch_fail_closed(tmp_path):
    prod,health,loop,dash=_prod(tmp_path)
    original=json.loads(health.read_text())
    for key,value,code in (
        ("source_drift",True,"HEALTH_SOURCE_DRIFT"),
        ("policy_hash","a"*64,"HEALTH_FROZEN_POLICY_NOT_APPROVED"),
        ("production_trading","YES","HEALTH_PRODUCTION_TRADING_UNSAFE"),
    ):
        current=dict(original);current[key]=value
        health.write_text(json.dumps(current))
        with pytest.raises(ValueError,match=code):
            capture(prod,loop,dash)
    health.write_text(json.dumps(original))
    baseline=capture(prod,loop,dash)
    changed=dict(original);changed["source_drift"]=True
    health.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match="HEALTH_SOURCE_DRIFT"):
        verify(baseline,prod,loop,dash)


def test_complete_shadow_health_rejected_against_ledger_schema(tmp_path):
    prod,health,loop,dash=_prod(tmp_path)
    health.write_text(json.dumps({
        "identifier":"com.jerson.crypto-monitor-frank-shadow",
        "service_source_sha256":"a"*64,
        "parser_version":"frank-v8",
        "historical_network_backfill":"BOUNDED300S_IDLE_WINDOW_ONLY",
        "gmail":0,"app_alert":0,"automation_mutations":0,"production_writes":0,
    }))
    with pytest.raises(ValueError,match="DB_SCHEMA_WRITER_PROFILE_MISMATCH"):
        capture(prod,loop,dash)


def test_wrong_ledger_identifier_fails_at_capture_not_only_at_verify(tmp_path):
    prod,health,loop,dash=_prod(tmp_path)
    data=json.loads(health.read_text())
    data["identifier"]="com.not-approved-ledger"
    health.write_text(json.dumps(data))
    with pytest.raises(ValueError,match="HEALTH_WRITER_PROFILE_MISMATCH"):
        capture(prod,loop,dash)
