import json
from pathlib import Path

from mission_agent.market.sol_usd import SELECTION_RULE, SOURCE, reference_epoch
from mission_agent.mission_control.sol_mirror import SolNormalizedMirror, _evidence_hash, merge_candidates
from mission_agent.signals.store import Ledger


class RefClient:
    def reference(self,block_time):
        epoch=reference_epoch(block_time)
        value={
            "status":"VERIFIED","retryable":False,"source":SOURCE,"symbol":"SOLUSDC","interval":"1m",
            "selection_rule":SELECTION_RULE,"reference_epoch":epoch,
            "candle_open_ms":epoch*1000,"candle_close_ms":epoch*1000+59999,
            "open":"150","high":"151","low":"149","close":"150","sol_usdc":"150","observed_at":1.0,
        }
        value["evidence_sha256"]=_evidence_hash(value)
        return value


def body(sig,at):
    return {
        "signature":sig,"wallet":"wallet","slot":at,"block_time":at,
        "classification":"ACTIVE_TRADE","classification_reason":"SIGNED_DEX_SWAP_OPPOSING_OWNED_FLOWS",
        "frank_is_signer":True,"frank_is_authority":True,
        "evidence":{"tx_err":None,"classification_evidence":{"dex_program_interaction":True,"swap_instruction_evidence":True,"opposing_economic_flows":True}},
        "trade":{
            "mint":"MintSOL","direction":"BUY","token_amount_raw":"1000000","token_decimals":6,
            "quote_asset":"SOL","quote_amount_raw":"100000000000","quote_decimals":9,
            "amount_predicate":"UNDETERMINED","amount_predicate_reason":"NON_USDC_QUOTE",
            "referenced_pre_raw":"0","referenced_post_raw":"1000000",
        },
    }


def make_source(path):
    ledger=Ledger(path)
    for sig,at in [("s1",1000),("s2",1100)]:
        ledger.db.execute(
            "INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            ("wallet",sig,"frank",at,at,"seen","classified","raw-"+sig,"raw-ref",json.dumps(body(sig,at)),"NO","SOURCE")
        )
    ledger.db.commit();ledger.db.close()


def test_live_sol_mirror_reuses_frozen_engine_without_writing_source(tmp_path):
    source=tmp_path/"forward.sqlite";sidecar=tmp_path/"sol.sqlite";make_source(source)
    policy=Path(__file__).parents[1]/"config"/"frank_local_signal_v1.json"
    mirror=SolNormalizedMirror(source,sidecar,policy,client=RefClient())
    result=mirror.sync()
    assert result["status"]=="OK"
    assert result["sol_trades"]==2
    assert result["sol_resolved"]==2
    assert result["sol_unresolved"]==0
    assert result["added_signal_count"]==0
    # Causal price evidence is research-only; cannot promote SOL to V1 USDC gates.
    assert mirror.candidates()==[]
    normalized=json.loads(mirror.db.execute(
        "SELECT body FROM signatures WHERE signature='s1'").fetchone()[0])["trade"]
    assert normalized["quote_asset"]=="SOL"
    assert normalized["amount_predicate"]=="UNDETERMINED"
    assert normalized["quote_usdc_status"]=="SOL_EVENT_TIME_USDC_VERIFIED"
    assert normalized["quote_usdc_equivalent"]=="15000.0"
    mirror.close()
    source_ledger=Ledger(source)
    assert source_ledger.db.execute("select count(*) from signals").fetchone()[0]==0
    source_ledger.db.close()


def test_routed_sol_trade_stays_unresolved_in_mirror_even_with_verified_reference(tmp_path):
    source=tmp_path/"forward.sqlite";sidecar=tmp_path/"sol.sqlite"
    ledger=Ledger(source)
    value=body("routed",1000)
    value["trade"]["amount_predicate"]="UNDETERMINED"
    value["trade"]["amount_predicate_reason"]="ROUTED_RESIDUAL_ASSETS"
    value["trade"]["route_intermediate_assets"]=[{"mint":"Residual"}]
    value["trade"]["route_amount_semantics"]="GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST"
    ledger.db.execute(
        "INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("wallet","routed","frank",1000,1000,"seen","classified","raw-routed","raw-ref",json.dumps(value),"NO","SOURCE")
    )
    ledger.db.commit();ledger.db.close()
    policy=Path(__file__).parents[1]/"config"/"frank_local_signal_v1.json"
    mirror=SolNormalizedMirror(source,sidecar,policy,client=RefClient())
    result=mirror.sync()
    assert result["status"]=="OK"
    assert result["sol_trades"]==1
    assert result["sol_resolved"]==0
    assert result["sol_unresolved"]==1
    assert result["failures"]["SOL_QUOTE_PROVENANCE_INELIGIBLE"]==1
    stored=json.loads(mirror.db.execute("select body from signatures where signature='routed'").fetchone()[0])
    trade=stored["trade"]
    assert trade["quote_asset"]=="SOL"
    assert trade["amount_predicate"]=="UNDETERMINED"
    assert trade["quote_usdc_status"]=="UNDETERMINED"
    assert mirror.db.execute("select count(*) from signals").fetchone()[0]==0
    mirror.close()


def test_merge_prefers_stronger_or_verified_sol_overlay():
    base=[{"person_id":"frank","mint":"M","episode_id":"E","pattern":"ACCUMULATION","latest_at":1,"latest_buy_price_status":"QUOTE_PRICE_UNAVAILABLE"}]
    overlay=[{"person_id":"frank","mint":"M","episode_id":"E","pattern":"ACCUMULATION","latest_at":1,"latest_buy_price_status":"SOL_EVENT_TIME_USDC_VERIFIED"}]
    out=merge_candidates(base,overlay)
    assert out[0]["latest_buy_price_status"]=="SOL_EVENT_TIME_USDC_VERIFIED"


def test_sol_mirror_excludes_non_frank_person_history(tmp_path):
    source=tmp_path/"forward.sqlite";sidecar=tmp_path/"mirror.sqlite"
    make_source(source)
    ledger=Ledger(source)
    ledger.db.execute(
        "INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("wallet","other-person","other",1200,1200,"seen","classified",
         "hash","raw-ref",json.dumps(body("other-person",1200)),"NO","SOURCE")
    )
    ledger.db.commit();ledger.db.close()
    policy=Path(__file__).parents[1]/"config"/"frank_local_signal_v1.json"
    mirror=SolNormalizedMirror(source,sidecar,policy,client=RefClient())
    result=mirror.sync()
    assert result["status"]=="OK"
    assert result["copied"]==2
    assert mirror.db.execute(
        "select count(*) from signatures where person_id!='frank'").fetchone()[0]==0
    mirror.close()


def test_live_decision_service_never_merges_shadow_candidates():
    import mission_agent.mission_control.service as service
    source=Path(service.__file__).read_text()
    assert "candidates = base_candidates" in source
    assert "merge_candidates(base_candidates, overlay_candidates)" not in source
