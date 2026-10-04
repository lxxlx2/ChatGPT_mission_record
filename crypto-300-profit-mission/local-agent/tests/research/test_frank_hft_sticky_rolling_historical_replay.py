import copy
import json
from pathlib import Path

import pytest
from scripts.frank_hft_sticky_rolling_historical_replay import (
    HistoricalHFTEngine, fail_windows, rolling_fail)
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy, USDC
from mission_agent.signals.store import Ledger
from test_frank_local_signals import active, put

POLICY = Path(__file__).parents[2] / 'config/frank_local_signal_v1.json'


def replay(root, mode='CURRENT', recovery=0, original=False):
    ledger=Ledger(root/'research.sqlite');policy=load_policy(POLICY)
    engine=Engine(ledger,policy) if original else HistoricalHFTEngine(ledger,policy,mode=mode,recovery_seconds=recovery)
    for i,at in enumerate((100000,100020,100060,100200,102800,103000)):
        event=active('isolated-'+str(i),100,13000)
        event['block_time']=at;event['slot']=at
        event['trade'].update(quote_asset=USDC,quote_amount_raw='13000000000',quote_decimals=6)
        put(ledger,event);engine.drain()
    state=json.loads(ledger.db.execute('select body from v1_states').fetchone()[0])
    signals=[json.loads(r[0]) for r in ledger.db.execute('select body from signals order by signal_id')]
    assert not ledger.db.execute("select 1 from outbox where status!='DRY_RUN_AUDIT'").fetchone()
    return ledger,engine,state,signals


def test_current_sticky_survives_low_frequency_accumulation(tmp_path):
    ledger,engine,state,signals=replay(tmp_path)
    assert state['hft'] is True
    last=json.loads(ledger.db.execute('select body from v1_evaluations order by at desc limit 1').fetchone()[0])
    assert last['predicates']['hft']=='FAIL'
    assert all(last['predicates'][k]=='PASS' for k in ('prior_accumulation','t0','cumulative_amount','persistence','inventory','distribution','freshness'))
    assert [s['signal_type'] for s in signals]==['FRANK_ACCUMULATION_SIGNAL']


def test_current_subclass_exactly_matches_production(tmp_path):
    a,_,sa,aa=replay(tmp_path/'subclass');b,_,sb,ab=replay(tmp_path/'original',original=True)
    assert sa==sb and aa==ab
    assert [tuple(r) for r in a.db.execute('select * from v1_evaluations order by evaluation_id')]==[tuple(r) for r in b.db.execute('select * from v1_evaluations order by evaluation_id')]


@pytest.mark.parametrize('recovery',[0,300,900])
def test_shadow_only_recovers_hft_with_same_chronology_inventory_accumulation(tmp_path,recovery):
    _,_,a,sa=replay(tmp_path/'current');_,_,b,sb=replay(tmp_path/'shadow','ROLLING',recovery)
    for key in ('events','current_raw','peak_raw','inventory_points','t0','accumulation_emitted'):
        assert a[key]==b[key]
    assert b['hft'] is False
    assert sum(s['signal_type']=='FRANK_MULTIPLE_SIGNAL' for s in sb)==1
    assert [s for s in sa if s['signal_type']=='FRANK_ACCUMULATION_SIGNAL']==[s for s in sb if s['signal_type']=='FRANK_ACCUMULATION_SIGNAL']


def test_inclusive_60s_boundary_and_fixed_recovery():
    policy=load_policy(POLICY)
    state={'state':'OPEN','events':[{'at':at} for at in (100,120,160)]}
    assert fail_windows(state['events'])==[{'start':160,'end':160}]
    assert rolling_fail(state,160,policy)
    assert not rolling_fail(state,161,policy)
    assert rolling_fail(state,460,policy,300)
    assert not rolling_fail(state,461,policy,300)
    assert rolling_fail(state,1060,policy,900)
    assert not rolling_fail(state,1061,policy,900)
    assert fail_windows([{'at':at} for at in (100,120,161)])==[]


def test_repeated_bursts_reset_continuous_recovery_and_future_is_excluded():
    policy=load_policy(POLICY);state={'state':'OPEN','events':[{'at':at} for at in (100,110,120,200,210,220)]}
    assert fail_windows(state['events'])==[{'start':120,'end':160},{'start':220,'end':260}]
    assert rolling_fail(state,500,policy,300)
    assert not rolling_fail(state,561,policy,300)
    assert not rolling_fail(state,170,policy)


def test_rapid_complete_roundtrip_preserved_without_three_trade_burst():
    policy=load_policy(POLICY);state={'state':'CLOSED','events':[{'at':100},{'at':1000}]}
    assert rolling_fail(state,1100,policy)
    state['events'][-1]['at']=1301
    assert not rolling_fail(state,1301,policy)


def test_one_signature_not_cpi_hops():
    assert fail_windows([{'at':100,'signature':'one-user-swap','cpi_hops':12}])==[]


def test_rapid_close_stays_vetoed_after_later_sell_in_closed_episode():
    policy=load_policy(POLICY)
    state={'state':'CLOSED','events':[{'at':100},{'at':1000},{'at':5000}],
           'inventory_points':[{'at':100,'raw':'100'},{'at':1000,'raw':'0'},{'at':5000,'raw':None}]}
    assert rolling_fail(state,5000,policy)
