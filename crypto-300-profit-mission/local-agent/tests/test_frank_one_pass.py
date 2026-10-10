"""Offline tests for one-pass Frank token-account research."""
import pytest

from scripts import audit_frank_one_pass as module
from scripts import audit_frank_native_resume as scan


def fake_sig(n):
    return "1" * 85 + ("1" if n == 0 else "2" if n == 1 else "3")


def row(n,ts):
    return {"signature":fake_sig(n),"slot":4550000+n,"blockTime":ts}


def state():
    return {"context":"abc","account":module.ATA,
            "buy_signature":module.fixed.BUY_SIGNATURE,
            "status":"PENDING","before":None,"pages":0,"signatures":[]}


def test_single_page_complete_cross_buy_timestamp():
    recent=module.BUY_TIME+60
    current=module.advance(state(),[row(0,recent),
                                    row(1,module.BUY_TIME+5),
                                    row(2,module.BUY_TIME-5)])
    assert current["status"]=="COMPLETE"
    assert current["pages"]==1
    assert len(current["signatures"])==2


def test_duplicate_or_reverse_time_fails_closed():
    s=state()
    s["status"]="ACTIVE"
    s["pages"]=1
    s["before"]=fake_sig(0)
    s["signatures"]=[row(0,module.BUY_TIME+20)]
    s["last_page_oldest_block_time"]=module.BUY_TIME+20
    with pytest.raises(scan.ScanBlocked,match="LIFECYCLE_DUPLICATE_SIGNATURE"):
        module.advance(s,[row(0,module.BUY_TIME+20)])
    with pytest.raises(scan.ScanBlocked,match="LIFECYCLE_PAGE_TIME_REVERSED"):
        module.advance(s,[row(1,module.BUY_TIME+50)])


def test_checkpoint_reads_original_without_api(tmp_path):
    context={"mode":"test","account":module.ATA}
    store=scan.Checkpoints(tmp_path/"ckpt",context,create=True)
    original=module.initial_state(store)
    store._write(store.root/"history.json",original)
    assert module.initial_state(store)==original
    assert original["status"]=="PENDING"


def _exit_case():
    return {"signature":"5wqKv5YuurRKUaJAK5fZtFrNg6GocVZuTTiAPWYrYDaswyUArwAZurpbZFU6WBjHp5z5Bt5bPCkLNKVQHfS6yigx",
            "block_time":1791509207,
            "token_delta_raw":"-4732220716414",
            "usdc_delta_raw":"7031556770",
            "frank_signed":True,"fomo_cosigned":True}


def test_conditional_lot_round_trip_matches_actual_reported_amounts():
    evidence=module.conditional_roundtrip(
        [{"token_delta_raw":"0"},{ "token_delta_raw":"0"},_exit_case()],True)
    assert evidence["status"]=="CONDITIONAL_MATCHED_TOKEN_ROUNDTRIP"
    assert evidence["hold_seconds"]==85231
    assert evidence["indicative_profit_usdc"]=="315.822278"
    assert evidence["indicative_return_pct"]=="4.702721"
    assert evidence["sale_instruction_verified"] is False
    assert evidence["gas_and_multiwallet_pnl_complete"] is False


def test_round_trip_rejects_other_token_movements_and_incomplete_windows():
    base=[{"token_delta_raw":"0"},_exit_case()]
    assert module.conditional_roundtrip(base,False)["status"]=="UNVERIFIED_INCOMPLETE_ACCOUNT"
    assert module.conditional_roundtrip([{"token_delta_raw":"12"},_exit_case()],True)["status"]=="UNVERIFIED_OTHER_TARGET_TOKEN_MOVEMENTS"
    x=dict(_exit_case())
    x["frank_signed"]=False
    assert module.conditional_roundtrip([x],True)["status"]=="UNVERIFIED_NOT_MATCHED_ROOT_AUTHORIZED_EXIT"
    x=dict(_exit_case())
    x["usdc_delta_raw"]="0"
    assert module.conditional_roundtrip([x],True)["status"]=="UNVERIFIED_NOT_MATCHED_ROOT_AUTHORIZED_EXIT"
