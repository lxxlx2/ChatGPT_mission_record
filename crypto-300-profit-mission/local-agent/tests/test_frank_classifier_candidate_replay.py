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
    database=sqlite3.connect(":memory:")
    database.execute("CREATE TABLE outbox(status TEXT)")
    database.execute("INSERT INTO outbox VALUES('DRY_RUN_AUDIT')")
    replay.verify_dry_run_outbox(database)
    database.execute("INSERT INTO outbox VALUES('PENDING_SEND')")
    with pytest.raises(RuntimeError,match="NON_DRY_RUN_OUTBOX"):
        replay.verify_dry_run_outbox(database)
    database.execute("DELETE FROM outbox")
    database.execute("INSERT INTO outbox VALUES(NULL)")
    with pytest.raises(RuntimeError,match="NON_DRY_RUN_OUTBOX"):
        replay.verify_dry_run_outbox(database)
    database.close()


def test_acceptance_integrity_snapshot_allows_normal_live_heartbeats_and_appends(tmp_path):
    import subprocess
    module_path=Path(__file__).parents[1]/"scripts"/"meme_acceptance_integrity.py"
    prod=tmp_path/"fake-prod";prod.mkdir()
    db=prod/"forward.sqlite"
    con=sqlite3.connect(db)
    con.execute("CREATE TABLE signatures(wallet TEXT,signature TEXT,person_id TEXT,slot INTEGER,block_time INTEGER,raw_hash TEXT,raw_reference TEXT)")
    con.execute("INSERT INTO signatures VALUES(?,?,?,?,?,?,?)",("w","first","frank",1,100,"oldhash","raw1"))
    con.commit();con.close()
    health=prod/"health.json"
    health.write_text(json.dumps({"last_successful_poll":100,"lag_seconds":4,"status":"RUNNING","policy_hash":"immutable"}))
    loop=tmp_path/"loop.plist";loop.write_text("<plist>loop</plist>")
    dash=tmp_path/"dashboard.plist";dash.write_text("<plist>dash</plist>")
    def command(op,*more):
        return [sys.executable,str(module_path),op,"--prod",str(prod),
                "--loop-plist",str(loop),"--dash-plist",str(dash),*more]
    before=json.loads(subprocess.check_output(command("capture"),text=True))
    before_path=tmp_path/"before.json"
    before_path.write_text(json.dumps(before))
    health.write_text(json.dumps({"last_successful_poll":101,"lag_seconds":0,"status":"RUNNING",
                                  "last_chain_signature":"second","policy_hash":"immutable"}))
    con=sqlite3.connect(db)
    con.execute("INSERT INTO signatures VALUES(?,?,?,?,?,?,?)",("w","second","frank",2,110,"newhash","raw2"))
    con.commit();con.close()
    out=json.loads(subprocess.check_output(command("verify","--before",str(before_path)),text=True))
    assert out["status"]=="PASS" and out["new_live_rows_allowed"]
    # Real historical mutation must fail, even though live appends are permitted.
    con=sqlite3.connect(db)
    con.execute("UPDATE signatures SET raw_hash='TAMPERED' WHERE signature='first'")
    con.commit();con.close()
    bad=subprocess.run(command("verify","--before",str(before_path)),capture_output=True,text=True)
    assert bad.returncode!=0
    assert "IMMUTABLE_LEDGER_OR_STABLE_HEALTH_OR_PLIST_CHANGED" in bad.stderr


def test_acceptance_bash_fake_prod_integrity_only(tmp_path):
    import os
    import subprocess
    sh=Path(__file__).parents[1]/"scripts"/"accept_meme_ca_v3.sh"
    module_path=Path(__file__).parents[1]/"scripts"/"meme_acceptance_integrity.py"
    prod=tmp_path/"fake-prod";prod.mkdir()
    db=sqlite3.connect(prod/"forward.sqlite")
    db.execute("CREATE TABLE signatures(wallet TEXT,signature TEXT,person_id TEXT,slot INTEGER,block_time INTEGER,raw_hash TEXT,raw_reference TEXT)")
    db.commit();db.close()
    (prod/"health.json").write_text('{"last_successful_poll":1,"status":"RUNNING"}')
    home=tmp_path/"home";home.mkdir()
    venv=tmp_path/"fake-venv";(venv/"bin").mkdir(parents=True)
    (venv/"bin"/"python").symlink_to(Path(sys.executable))
    worktree=Path(__file__).parents[3]
    control=tmp_path/"control"
    env={**os.environ,"INTEGRITY_SELF_TEST_ONLY":"1","PROD":str(prod),
         "WORKTREE":str(worktree),"LOCAL_AGENT":str(Path(__file__).parents[1]),
         "HOME":str(home),"VENV":str(venv),"CONTROL":str(control)}
    result=subprocess.run(["bash",str(sh)],env=env,capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert "REAL_CA_ACCEPTANCE: NOT_RUN" in result.stdout
    assert (control/"integrity-before.json").is_file()


def test_replay_transition_ignores_evidence_only_route_metadata():
    source={"classification":"ACTIVE_TRADE",
            "classification_reason":"SIGNED_DEX_SWAP_OPPOSING_OWNED_FLOWS",
            "trade":{"mint":"M","direction":"BUY","token_amount_raw":"100",
                     "quote_asset":"SOL","quote_amount_raw":"500"}}
    candidate=json.loads(json.dumps(source))
    candidate["trade"]["route_intermediate_evidence_status"]="NO_INTERMEDIATE_TRANSFER_OBSERVED"
    candidate["trade"]["route_intermediate_assets"]=[]
    assert source!=candidate
    assert replay.semantic_classification(source)==replay.semantic_classification(candidate)
    candidate["trade"]["quote_asset"]="USDT"
    assert replay.semantic_classification(source)!=replay.semantic_classification(candidate)


def test_acceptance_integrity_allows_real_writer_polling_but_not_stable_tamper(tmp_path):
    import importlib.util
    module_path=Path(__file__).parents[1]/"scripts"/"meme_acceptance_integrity.py"
    spec=importlib.util.spec_from_file_location("meme_acceptance_integrity_for_test",module_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    prod=tmp_path/"prod";prod.mkdir()
    db=sqlite3.connect(prod/"forward.sqlite")
    db.execute("CREATE TABLE signatures(wallet TEXT,signature TEXT,person_id TEXT,slot INTEGER,block_time INTEGER,raw_hash TEXT,raw_reference TEXT)")
    db.execute("INSERT INTO signatures VALUES(?,?,?,?,?,?,?)",("w","sig1","frank",1,100,"rawhash","ref"))
    db.commit();db.close()
    health_path=prod/"health.json"
    health={"service_source_sha256":"stable-script","parser_version":"frank-v8",
            "identifier":"frank","historical_network_backfill":"BOUNDED300S_IDLE_WINDOW_ONLY",
            "gmail":0,"app_alert":0,"automation_mutations":0,"production_writes":0,
            "last_poll_at":"time1","candidate_duplicate_count":0,
            "request_count":100,"rpc_429_count":0,"rpc_error_count":0,
            "timeouts":0,"retry":0,"last_rpc_success_at":"time1",
            "private_transport_status":"WAITING_REAL_ACTIVE_EVENT",
            "active_e2e_status":"FRANK_ACTIVE_E2E_WAITING_REAL_EVENT",
            "poll_seconds":"0.5","last_successful_poll":"time1"}
    health_path.write_text(json.dumps(health))
    loop=tmp_path/"loop.plist";loop.write_text("loop")
    dash=tmp_path/"dash.plist";dash.write_text("dash")
    before=module.capture(prod,loop,dash)
    assert before["db"]["identity_prefix_rows"]==1
    assert before["health_stable_sha256"]
    health.update(last_poll_at="time2",candidate_duplicate_count=1,
                  request_count=101,rpc_429_count=1,rpc_error_count=1,
                  timeouts=1,retry=1,last_rpc_success_at="time2",
                  private_transport_status="RPC_RETRY",
                  active_e2e_status="FRANK_ACTIVE_E2E_PASS",
                  poll_seconds="7.3",last_successful_poll="time2")
    health_path.write_text(json.dumps(health))
    assert module.verify(before,prod,loop,dash)["status"]=="PASS"
    health["production_writes"]=1
    health_path.write_text(json.dumps(health))
    with pytest.raises(RuntimeError,match="IMMUTABLE_LEDGER_OR_STABLE_HEALTH_OR_PLIST_CHANGED"):
        module.verify(before,prod,loop,dash)


def test_replay_transition_detects_sol_route_eligibility_flip():
    base={"classification":"ACTIVE_TRADE",
          "classification_reason":"SIGNED_DEX_SWAP_OPPOSING_OWNED_FLOWS",
          "trade":{"mint":"M","direction":"BUY","token_amount_raw":"200",
                   "quote_asset":"SOL","quote_amount_raw":"1000",
                   "amount_predicate":"UNDETERMINED",
                   "amount_predicate_reason":"NON_USDC_QUOTE"}}
    alt=json.loads(json.dumps(base))
    alt["trade"]["route_intermediate_evidence_status"]="UNVERIFIED"
    assert replay.semantic_classification(base)!=replay.semantic_classification(alt)
    both=json.loads(json.dumps(base))
    both["trade"]["route_intermediate_evidence_status"]="NO_INTERMEDIATE_TRANSFER_OBSERVED"
    both["trade"]["route_intermediate_assets"]=[]
    assert replay.semantic_classification(base)==replay.semantic_classification(both)


def test_replay_transition_ignores_nonsemantic_balance_reference_metadata():
    source={"classification":"ACTIVE_TRADE",
            "classification_reason":"SIGNED_DEX_SWAP_OPPOSING_OWNED_FLOWS",
            "trade":{"mint":"M","direction":"BUY","token_amount_raw":"100",
                     "quote_asset":USDC,"quote_amount_raw":"1000000",
                     "quote_decimals":6,"amount_predicate":"USDC_DIRECT_NUMERIC",
                     "referenced_pre_raw":"100","referenced_post_raw":"200"}}
    updated=json.loads(json.dumps(source))
    updated["trade"]["referenced_pre_raw"]="120"
    updated["trade"]["referenced_post_raw"]="220"
    assert updated!=source
    assert replay.semantic_classification(updated)==replay.semantic_classification(source)
    updated["trade"]["quote_amount_raw"]="500000"
    assert replay.semantic_classification(updated)!=replay.semantic_classification(source)
