import json
import os
import sqlite3
import time
from pathlib import Path

from mission_agent.mission_control.service import MissionMemeService


def make_prod(root: Path, *, latest_at=None):
    root.mkdir(parents=True)
    latest_at=int(time.time()) if latest_at is None else latest_at
    (root/"health.json").write_text(json.dumps({"status":"RUNNING","pid":os.getpid(),"last_successful_poll":__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),"poll_interval_seconds":30,"source_drift":False,"consecutive_errors":0}))
    db=sqlite3.connect(root/"forward.sqlite")
    db.executescript("""
    create table v1_states(person_id text,mint text,body text,primary key(person_id,mint));
    create table signals(signal_id text primary key,person_id text,mint text,episode_id text,signal_type text,stage text,created_at text,content_hash text,body text);
    create table trades(wallet text,signature text,mint text,episode_id text,block_time integer,side text,body text);
    """)
    event={"signature":"tx3","at":latest_at,"direction":"BUY","token_amount_raw":"1000000","token_decimals":6,"quote_asset":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v","quote_quantity":"1"}
    state={"episode_id":"ep1","state":"OPEN","current_raw":"3000000","events":[{**event,"signature":"tx1","at":latest_at-120},{**event,"signature":"tx2","at":latest_at-60},event]}
    db.execute("insert into v1_states values(?,?,?)",("frank","Mint111",json.dumps(state)))
    db.execute("insert into signals values(?,?,?,?,?,?,?,?,?)",("signal1","frank","Mint111","ep1","FRANK_MULTIPLE_SIGNAL","MULTIPLE",str(latest_at),"h",json.dumps({"signal_id":"signal1"})))
    db.commit();db.close()


def policy(path: Path):
    path.write_text(json.dumps({"schema_version":1,"policy_id":"P1","status":"REVIEW_ONLY","live_delivery_approved":False,"decision":{"quote_usdc_amount":"30","slippage_bps":100,"quote_cache_seconds":20,"max_quote_age_seconds":30,"initial_notification_max_age_seconds":600,"hard_no_buy_position_states":["CLOSED","INVENTORY_UNDETERMINED"],"buy":{"required_pattern":"MULTIPLE","max_price_deviation_pct":"8","max_price_impact_pct":"1.5"},"small_buy":{"allowed_patterns":["MULTIPLE","ACCUMULATION"],"max_price_deviation_pct":"20","max_price_impact_pct":"3"}}}))


def test_review_policy_never_allows_live_delivery_and_records_dry_outbox(tmp_path):
    prod=tmp_path/"prod";control=tmp_path/"control";p=tmp_path/"policy.json";make_prod(prod);policy(p)
    service=MissionMemeService(production_root=prod,control_root=control,policy_path=p,live_delivery=True)
    service.jupiter.quote_usdc_to_token=lambda *a,**k:{"status":"OK","source":"JUPITER_OFFICIAL","observed_at":time.time(),"input_usdc":"30","execution_price_usdc":"1.02","price_impact_pct":"0.5","route_exists":True,"route_plan":[{}]}
    result=service.cycle()
    assert result["delivery_allowed"] is False
    assert result["decision_events"][0]["decision"]=="BUY"
    assert service.control.db.execute("select status from gmail_delivery").fetchone()[0]=="DRY_RUN_AUDIT"
    assert service.control.db.execute("select status from local_delivery").fetchone()[0]=="DRY_RUN_AUDIT"
    service.close()


def test_bootstrap_old_historical_candidate_does_not_enqueue_notification(tmp_path):
    prod=tmp_path/"prod";control=tmp_path/"control";p=tmp_path/"policy.json";make_prod(prod,latest_at=int(time.time())-3600);policy(p)
    service=MissionMemeService(production_root=prod,control_root=control,policy_path=p)
    service.jupiter.quote_usdc_to_token=lambda *a,**k:{"status":"OK","source":"JUPITER_OFFICIAL","observed_at":time.time(),"input_usdc":"30","execution_price_usdc":"1.02","price_impact_pct":"0.5","route_exists":True,"route_plan":[{}]}
    result=service.cycle()
    assert result["decision_events"][0]["notification_enqueued"] is False
    assert service.control.db.execute("select count(*) from decision_outbox").fetchone()[0]==0
    service.close()
