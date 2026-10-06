import json
import sqlite3

import pytest

from mission_agent.mission_control.db import ControlDB, open_production_ro, utc


def test_production_connection_is_query_only(tmp_path):
    path = tmp_path / "forward.sqlite"
    db = sqlite3.connect(path)
    db.execute("create table x(v integer)")
    db.execute("insert into x values(1)")
    db.commit(); db.close()
    ro = open_production_ro(path)
    assert ro.execute("select v from x").fetchone()[0] == 1
    with pytest.raises(sqlite3.OperationalError):
        ro.execute("insert into x values(2)")
    ro.close()


def payload(decision="BUY", input_nonce=1):
    return {
        "person_id":"frank", "mint":"Mint111", "episode_id":"ep1",
        "source_signal_id":"sig1", "source_signal_type":"FRANK_MULTIPLE_SIGNAL",
        "decision":decision, "created_at":utc(), "policy_id":"P1", "policy_hash":"h1",
        "inputs":{"nonce":input_nonce}, "metrics":{}, "reasons":[], "missing":[], "invalidation":[],
    }


def test_same_decision_does_not_grow_snapshots_or_events(tmp_path):
    db = ControlDB(tmp_path / "mission-control.sqlite")
    first = db.record(payload("BUY",1), "P1", "h1")
    for nonce in range(2,7):
        repeated = db.record(payload("BUY",nonce), "P1", "h1")
        assert repeated["changed"] is False
        assert repeated["snapshot_id"] == first["snapshot_id"]
    assert db.db.execute("select count(*) from decision_snapshots").fetchone()[0] == 1
    assert db.db.execute("select count(*) from decision_events").fetchone()[0] == 1


def test_decision_change_creates_new_event_with_previous_state(tmp_path):
    db = ControlDB(tmp_path / "mission-control.sqlite")
    db.record(payload("BUY",1), "P1", "h1")
    changed = db.record(payload("WAIT",2), "P1", "h1")
    assert changed["changed"] is True
    assert changed["event"]["previous_decision"] == "BUY"
    body = json.loads(changed["event"]["body"])
    assert body["previous_decision"] == "BUY"
    assert db.db.execute("select count(*) from decision_snapshots").fetchone()[0] == 2
    assert db.db.execute("select count(*) from decision_events").fetchone()[0] == 2
