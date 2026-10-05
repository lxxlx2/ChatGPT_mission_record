from mission_agent.mission_control.policy import evaluate, should_notify

POLICY={"decision":{"max_quote_age_seconds":30,"hard_no_buy_position_states":["CLOSED","INVENTORY_UNDETERMINED"],"buy":{"max_price_deviation_pct":"8","max_price_impact_pct":"1.5"},"small_buy":{"allowed_patterns":["MULTIPLE","ACCUMULATION"],"max_price_deviation_pct":"20","max_price_impact_pct":"3"}}}

def candidate(**overrides):
    base={"runtime_status":"LIVE","position_state":"OPEN","current_raw":"100","pattern":"MULTIPLE","latest_side":"BUY","latest_buy_price_usdc":"1"};base.update(overrides);return base

def quote(**overrides):
    base={"status":"OK","observed_at":1000,"route_exists":True,"execution_price_usdc":"1.05","price_impact_pct":"0.8","input_usdc":"30"};base.update(overrides);return base

def test_multiple_close_to_frank_is_buy(): assert evaluate(candidate(),quote(),POLICY,now=1005)["decision"]=="BUY"
def test_accumulation_is_small_buy_not_full_buy(): assert evaluate(candidate(pattern="ACCUMULATION"),quote(),POLICY,now=1005)["decision"]=="SMALL_BUY"
def test_price_chase_becomes_wait(): assert evaluate(candidate(),quote(execution_price_usdc="1.25"),POLICY,now=1005)["decision"]=="WAIT"
def test_high_impact_becomes_wait(): assert evaluate(candidate(),quote(price_impact_pct="4"),POLICY,now=1005)["decision"]=="WAIT"
def test_latest_sell_blocks_follow(): assert evaluate(candidate(latest_side="SELL"),quote(),POLICY,now=1005)["decision"]=="WAIT"
def test_closed_and_unknown_inventory_are_no_buy():
    assert evaluate(candidate(position_state="CLOSED",current_raw="0"),quote(),POLICY,now=1005)["decision"]=="NO_BUY"
    assert evaluate(candidate(position_state="INVENTORY_UNDETERMINED",current_raw=None),quote(),POLICY,now=1005)["decision"]=="NO_BUY"
def test_offline_runtime_fails_closed_without_market_dependency(): assert evaluate(candidate(runtime_status="OFFLINE"),{"status":"SKIPPED"},POLICY,now=1005)["decision"]=="WAIT"
def test_stale_quote_never_buy(): assert evaluate(candidate(),quote(observed_at=900),POLICY,now=1005)["decision"]=="WAIT"
def test_no_route_is_no_buy(): assert evaluate(candidate(),quote(route_exists=False),POLICY,now=1005)["decision"]=="NO_BUY"
def test_notification_transition_rules():
    assert should_notify(None,"BUY") is True
    assert should_notify(None,"WAIT") is True
    assert should_notify("BUY","BUY") is False
    assert should_notify("BUY","WAIT") is True
    assert should_notify("WAIT","NO_BUY") is True
