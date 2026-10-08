import gzip
import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from mission_agent.signals.classifier import classify
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import USDC, load_policy
from mission_agent.signals.store import Ledger
from mission_agent.frank.rpc import WALLET
from test_frank_fm import tx


SCRIPT=Path(__file__).parents[1]/"scripts"/"frank_classifier_candidate_replay.py"
SPEC=importlib.util.spec_from_file_location("frank_classifier_candidate_replay_under_test",SCRIPT)
replay=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)
POLICY=Path(__file__).parents[1]/"config"/"frank_local_signal_v1.json"


def raw_hash(value):
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    ).hexdigest()


def make_source(tmp_path):
    prod=tmp_path/"prod";prod.mkdir()
    raw_root=prod/"raw";raw_root.mkdir()
    source=prod/"forward.sqlite"
    value=tx()
    for field in ("preTokenBalances","postTokenBalances"):
        value["meta"][field][1]["mint"]=USDC
    sig="source-sig"
    raw_path=raw_root/(sig+".json.gz")
    raw_path.write_bytes(gzip.compress(json.dumps(value,sort_keys=True).encode(),mtime=0))
    classified=classify(sig,value,WALLET)
    ledger=Ledger(source)
    ledger.put("frank",classified,raw_hash(value),str(raw_path),dry_run=True)
    engine=Engine(ledger,load_policy(POLICY),dry_run=True)
    engine.drain(until=int(value["blockTime"])+3600)
    ledger.db.close()
    return source,raw_path


def make_hourly_source(tmp_path):
    prod=tmp_path/"prod-hourly";prod.mkdir()
    raw_root=prod/"raw";raw_root.mkdir()
    source=prod/"forward.sqlite"
    ledger=Ledger(source)
    for index,(sig,at) in enumerate((("first",3600),("second",4200))):
        value=tx();value["slot"]=100+index;value["blockTime"]=at
        for field in ("preTokenBalances","postTokenBalances"):
            value["meta"][field][1]["mint"]=USDC
        value["meta"]["preTokenBalances"][1]["uiTokenAmount"]["amount"]="13000000000"
        value["meta"]["postTokenBalances"][1]["uiTokenAmount"]["amount"]="0"
        raw_path=raw_root/(sig+".json.gz")
        raw_path.write_bytes(gzip.compress(json.dumps(value,sort_keys=True).encode(),mtime=0))
        classified=classify(sig,value,WALLET)
        ledger.put("frank",classified,raw_hash(value),str(raw_path),dry_run=True)
    engine=Engine(ledger,load_policy(POLICY),dry_run=True)
    engine.drain(until=8940)
    ledger.db.close()
    return source


def run_main(monkeypatch,*args):
    monkeypatch.setattr(sys,"argv",[str(SCRIPT),*map(str,args)])
    replay.main()


def test_replay_requires_report_inside_new_isolated_workspace_before_any_write(tmp_path,monkeypatch):
    source,_=make_source(tmp_path)
    before=source.read_bytes()
    work=tmp_path/"replay-new"
    with pytest.raises(ValueError,match="OUTPUT_MUST_BE_INSIDE_WORKSPACE"):
        run_main(
            monkeypatch,
            "--source",source,"--policy",POLICY,
            "--work",work,"--output",source,
        )
    assert source.read_bytes()==before
    assert not work.exists()


def test_replay_rejects_workspace_inside_production_source_directory(tmp_path):
    source,_=make_source(tmp_path)
    with pytest.raises(ValueError,match="WORKSPACE_INSIDE_SOURCE_DIRECTORY"):
        replay._new_workspace(source.parent/"candidate-replay",source.resolve())


def test_replay_rejects_existing_symlink_or_hardlink_output_alias(tmp_path):
    source,_=make_source(tmp_path)
    work=tmp_path/"manual-work";work.mkdir()
    symlink=work/"symlink-report.json"
    symlink.symlink_to(source)
    with pytest.raises(ValueError,match="OUTPUT_MUST_NOT_EXIST"):
        replay._output_in_workspace(symlink,work)

    hardlink=work/"hardlink-report.json"
    hardlink.hardlink_to(source)
    with pytest.raises(ValueError,match="OUTPUT_MUST_NOT_EXIST"):
        replay._output_in_workspace(hardlink,work)


def test_replay_rejects_reserved_database_output_name(tmp_path):
    source,_=make_source(tmp_path)
    work=replay._new_workspace(tmp_path/"audit-work",source.resolve())
    with pytest.raises(ValueError,match="OUTPUT_PATH_RESERVED"):
        replay._output_in_workspace(work/"baseline.sqlite",work)


def test_replay_missing_or_invalid_raw_hash_is_not_verified(tmp_path):
    source,raw_path=make_source(tmp_path)
    row={"raw_hash":"","raw_reference":str(raw_path)}
    tx_value,error=replay.raw_transaction(row,source.resolve())
    assert tx_value is None and error=="RAW_HASH_MISSING_OR_INVALID"
    row["raw_hash"]="not-a-sha256"
    tx_value,error=replay.raw_transaction(row,source.resolve())
    assert tx_value is None and error=="RAW_HASH_MISSING_OR_INVALID"


def test_semantic_diffs_detect_event_provenance_and_signal_identity_changes():
    before={"frank|M":{"state":"OPEN","events":[{"signature":"s","amount_predicate":"USDC_DIRECT_NUMERIC"}],"watch_at":100}}
    after={"frank|M":{"state":"OPEN","events":[{"signature":"s","amount_predicate":"UNDETERMINED"}],"watch_at":200}}
    deltas=replay._mapping_deltas(before,after)
    fields={row["field"] for row in deltas[0]["field_diffs"]}
    assert "events[0].amount_predicate" in fields
    assert "watch_at" in fields

    one={"a":{"person_id":"frank","mint":"M","episode_id":"E1","signal_type":"X","stage":"S","triggered_at":1,"triggering_signature":"t","latest_buy_signature":"b"}}
    two={"b":{"person_id":"other","mint":"M","episode_id":"E2","signal_type":"X","stage":"S","triggered_at":2,"triggering_signature":"t","latest_buy_signature":"b"}}
    assert replay._signal_counter(one)!=replay._signal_counter(two)


def test_replay_reproduces_hourly_watch_and_terminal_clock_semantics(tmp_path,monkeypatch):
    source=make_hourly_source(tmp_path)
    work=tmp_path/"hourly-replay";output=work/"report.json"
    run_main(
        monkeypatch,
        "--source",source,"--policy",POLICY,
        "--work",work,"--output",output,
    )
    report=json.loads(output.read_text())
    assert report["timing_equivalence"]["terminal_clock"]==8940
    assert report["baseline_source_signal_identity_parity"] is True
    assert report["baseline_source_state_parity"] is True
    assert report["candidate_signal_identity_parity"] is True
    assert report["source_baseline_evaluation_deltas"]==[]


def test_replay_is_read_only_and_reproduces_source_state_with_terminal_clock(tmp_path,monkeypatch):
    source,_=make_source(tmp_path)
    before=source.read_bytes()
    work=tmp_path/"isolated-replay"
    output=work/"report.json"
    run_main(
        monkeypatch,
        "--source",source,"--policy",POLICY,
        "--work",work,"--output",output,
    )
    assert source.read_bytes()==before
    report=json.loads(output.read_text())
    assert report["source_open_mode"]=="READ_ONLY"
    assert report["unreclassified_count"]==0
    assert report["baseline_source_signal_identity_parity"] is True
    assert report["baseline_source_state_parity"] is True
    assert report["candidate_signal_identity_parity"] is True
    assert report["acceptance"]=="REVIEW_DELTAS"
    assert report["timing_equivalence"]["terminal_clock"] is not None
    assert (work/"baseline.sqlite").is_file()
    assert (work/"candidate.sqlite").is_file()


def test_replay_report_verifies_source_sha256(tmp_path,monkeypatch):
    source,_=make_source(tmp_path)
    extra=tmp_path/"health.json"
    extra.write_text('{"status":"OK"}')
    original=replay.sha256_file(source)
    work=tmp_path/"hash-work"
    output=work/"report.json"
    run_main(
        monkeypatch,"--source",source,"--policy",POLICY,
        "--work",work,"--output",output,"--integrity-file",extra,
    )
    report=json.loads(output.read_text())
    assert report["integrity_check"]=="PASS"
    assert report["integrity_verified_file_count"]==2
    assert report["verified_integrity_files_sha256"][str(source.resolve())]==original
    assert report["production_files_changed"]=="NOT_VERIFIED_FROM_SOURCE_COPY"


def test_replay_outbox_guard_is_not_python_assert():
    text=SCRIPT.read_text()
    assert 'raise RuntimeError("NON_DRY_RUN_OUTBOX")' in text
    assert "assert not ledger.db.execute" not in text
