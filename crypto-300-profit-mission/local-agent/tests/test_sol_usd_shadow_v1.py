import json
from pathlib import Path

from mission_agent.market.sol_usd import normalize_classification
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger
from test_frank_local_signals import active

POLICY=Path(__file__).parents[1]/'config/frank_local_signal_v1.json'


def put_sol(ledger,engine,signature,at,sol_amount,sol_usdc='100'):
    event=active(signature,100,20)
    event['block_time']=at;event['slot']=at
    event['trade']['quote_asset']='SOL'
    event['trade']['quote_amount_raw']=str(int(sol_amount*1_000_000_000))
    event['trade']['quote_decimals']=9
    event['trade']['amount_predicate']='UNDETERMINED'
    event['trade']['amount_predicate_reason']='NON_USDC_QUOTE'
    event['trade']['quote_legs']=[{'asset':'SOL','raw_delta':str(-int(sol_amount*1_000_000_000)),'decimals':9}]
    event['trade']['route_intermediate_assets']=[]
    event['trade']['route_amount_semantics']='DIRECT_OR_SINGLE_TARGET_QUOTE'
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','selection_rule':'PREVIOUS_CLOSED_1M_CLOSE','sol_usdc':sol_usdc,'evidence_sha256':'fixture'}
    normalized=normalize_classification(event,ref,for_model=True)
    ledger.put('frank',normalized,signature,'fixture',dry_run=True)
    engine.drain()


def signals(ledger):
    return [json.loads(r[0]) for r in ledger.db.execute('select body from signals order by created_at,signal_type')]


def test_verified_sol_usdc_shadow_recovers_same_accumulation_and_multiple_shape(tmp_path):
    ledger=Ledger(tmp_path/'shadow.sqlite');engine=Engine(ledger,load_policy(POLICY),dry_run=True)
    put_sol(ledger,engine,'first',100000,130)
    put_sol(ledger,engine,'second',101200,130)
    put_sol(ledger,engine,'third',102700,50)
    assert [s['signal_type'] for s in signals(ledger)]==['FRANK_ACCUMULATION_SIGNAL','FRANK_MULTIPLE_SIGNAL']
    state=json.loads(ledger.db.execute('select body from v1_states').fetchone()[0])
    assert all(e['quote_asset']=='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' for e in state['events'])
    assert all(e['original_quote']['quote_asset']=='SOL' for e in state['events'])
    assert all(e['quote_usdc_status']=='SOL_EVENT_TIME_USDC_VERIFIED' for e in state['events'])


def test_unresolved_sol_reference_remains_fail_closed(tmp_path):
    ledger=Ledger(tmp_path/'shadow.sqlite');engine=Engine(ledger,load_policy(POLICY),dry_run=True)
    event=active('one',100,20);event['block_time']=100000;event['slot']=100000
    event['trade']['quote_asset']='SOL';event['trade']['quote_amount_raw']=str(130*1_000_000_000);event['trade']['quote_decimals']=9
    event['trade']['amount_predicate']='UNDETERMINED';event['trade']['amount_predicate_reason']='NON_USDC_QUOTE'
    event['trade']['quote_legs']=[{'asset':'SOL','raw_delta':str(-130*1_000_000_000),'decimals':9}]
    event['trade']['route_intermediate_assets']=[];event['trade']['route_amount_semantics']='DIRECT_OR_SINGLE_TARGET_QUOTE'
    normalized=normalize_classification(event,{'status':'UNAVAILABLE','reason':'fixture'},for_model=True)
    ledger.put('frank',normalized,'one','fixture',dry_run=True);engine.drain()
    assert signals(ledger)==[]
    evaluation=json.loads(ledger.db.execute('select body from v1_evaluations order by at desc limit 1').fetchone()[0])
    assert evaluation['predicates']['accumulation_amount']=='UNDETERMINED'
