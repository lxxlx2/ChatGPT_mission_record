import copy
from decimal import Decimal

from scripts.frank_trade_coverage_historical_replay import (
    USDC, USDT, WSOL, groups, pick_causal_candle, reconstruct, valued_trade)


class Prices:
    def get(self,asset,at):
        price={USDC:'1','SOL':'120',WSOL:'120',USDT:'.9995'}.get(asset)
        return {'price':price,'source':'ISOLATED_TEST_PRICE','price_observed_through':at-1} if price else None


def record(flows,at=10000,native=0):
    return {'signature':'one-user-swap','block_time':at,'classification':'UNKNOWN_NEEDS_REVIEW',
            'classification_reason':'AMBIGUOUS_USER_EXCHANGE_ASSETS','frank_is_signer':True,
            'evidence':{'tx_err':None,'program_ids':['recognized-dex'],
                        'fee_adjusted_SOL_delta_lamports':str(native),
                        'classification_evidence':{'dex_program_interaction':True,'swap_instruction_evidence':True},
                        'token_balance_deltas':[{'mint':m,'wallet_owned':True,'delta':str(v),'pre_amount':str(max(-v,0)),
                                                 'post_amount':str(max(v,0)),'decimals':d} for m,v,d in flows],
                        'decoded_transient_token_flows':[]}}


def test_causal_previous_completed_minute_excludes_future_close():
    rows=[[9960,100,150,110,140,1],[9900,99,110,100,105,1]]
    assert pick_causal_candle(rows,10000)['price']=='105'
    assert pick_causal_candle(rows,10020)['price']=='140'
    assert pick_causal_candle(rows,10020)['price_observed_through']==10020
    assert pick_causal_candle(rows,10080) is None


def test_zero_owned_net_and_pool_assets_do_not_create_quote():
    e=record([('target',100,6),(USDT,0,6)])['evidence']
    e['token_balance_deltas'].append({'mint':USDT,'wallet_owned':False,'delta':'-3000000','pre_amount':'3000000','post_amount':'0','decimals':6})
    assert set(groups(e))=={'target'}


def test_true_usdt_quote_uses_historical_deviation_not_one_dollar():
    r=record([('target',100,6),(USDT,-3000000000,6)])
    t,a=reconstruct(r,Prices())
    assert a['category']=='RECONSTRUCTABLE_USER_SWAP' and t['direction']=='BUY'
    assert Decimal(t['quote_amount_raw'])/Decimal(10)**t['quote_decimals']==Decimal('2998.5000')
    assert a['quote_legs'][0]['price']['price']=='.9995'


def test_sol_refund_preserved_in_single_target_net_quote():
    r=record([('target',100,6),(USDC,-2500000000,6),(WSOL,250000000,9)],native=250000000)
    t,a=reconstruct(r,Prices(),allow_complex=True)
    assert a['category']=='RECONSTRUCTABLE_USER_SWAP'
    assert Decimal(t['quote_amount_raw'])/Decimal(10)**t['quote_decimals']==Decimal('2470')
    assert len(a['quote_legs'])==2


def test_nonzero_one_raw_secondary_target_never_discarded():
    r=record([('target',100,6),('other',1,9),(USDC,-2500000000,6)])
    t,a=reconstruct(r,Prices(),allow_complex=True)
    assert t is None and a['category']=='TRUE_MULTI_ASSET_ACTION'


def test_multiple_cpi_and_accounts_still_one_user_trade():
    r=record([('target',30,6),('target',70,6),(USDC,-2500000000,6)])
    r['evidence']['cpi_hops']=10
    t,a=reconstruct(r,Prices(),allow_complex=True)
    assert t['token_amount_raw']=='100' and a['category']=='RECONSTRUCTABLE_USER_SWAP'


def test_sol_rent_native_difference_fails_closed():
    r=record([('target',100,6),(USDC,-2500000000,6)],native=252039280)
    r['evidence']['decoded_transient_token_flows']=[{'mint':WSOL,'decimals':9,'net_transfer_raw':'250000000'}]
    t,a=reconstruct(r,Prices(),allow_complex=True)
    assert t is None and a['reason']=='WSOL_NET_NATIVE_RECONCILIATION_NOT_EXACT'


def test_unsigned_failed_missing_swap_do_not_reconstruct():
    for field in ('signer','failed','swap'):
        r=record([('target',100,6),(USDT,-3000000000,6)])
        if field=='signer':r['frank_is_signer']=False
        elif field=='failed':r['evidence']['tx_err']={'failed':True}
        else:r['evidence']['classification_evidence']['swap_instruction_evidence']=False
        assert reconstruct(r,Prices())[0] is None


def test_missing_price_stays_unresolved():
    class NoPrice:
        def get(self,*args):return None
    r=record([('target',100,6),(USDT,-3000000000,6)])
    t,a=reconstruct(r,NoPrice())
    assert t is None and a['category']=='INSUFFICIENT_EVIDENCE'


def test_sol_valuation_is_isolated_and_sensitivity_not_target_quantity():
    trade={'quote_asset':'SOL','quote_amount_raw':'25000000000','quote_decimals':9,'token_amount_raw':'100','mint':'target','direction':'BUY'}
    original=copy.deepcopy(trade)
    values=[valued_trade(trade,10000,Prices(),f)[0] for f in (Decimal('.98'),Decimal(1),Decimal('1.02'))]
    assert trade==original
    assert [Decimal(v['quote_amount_raw'])/Decimal(10)**12 for v in values]==[Decimal('2940'),Decimal('3000'),Decimal('3060')]
    assert all(v['token_amount_raw']=='100' for v in values)


def test_research_program_requires_own_invocation_swap_log_and_never_mutates_original():
    from scripts.frank_trade_coverage_historical_replay import research_market_record, RESEARCH_MARKETS, market_proven
    program=next(iter(RESEARCH_MARKETS));r=record([('target',100,6),(USDC,-5000000000,6)])
    r['evidence']['classification_evidence'].update(dex_program_interaction=False,swap_instruction_evidence=False)
    original=copy.deepcopy(r)
    tx={'meta':{'logMessages':[f'Program {program} invoke [1]', 'Program log: Instruction: SwapV2',f'Program {program} success']}}
    assert market_proven(research_market_record(r,tx))
    unrelated={'meta':{'logMessages':[f'Program {program} invoke [1]', 'Program unrelated invoke [2]', 'Program log: Instruction: SwapV2', 'Program unrelated success',f'Program {program} success']}}
    assert not market_proven(research_market_record(r,unrelated))
    assert r==original


def test_quote_only_swap_not_invented_as_meme_position():
    r=record([(USDC,-5000000000,6),(WSOL,40000000000,9)])
    t,a=reconstruct(r,Prices(),allow_complex=True)
    assert t is None and a['category']=='LP_ROUTING_INVENTORY_OPERATION'


def test_restored_real_trades_can_reduce_multiple_with_original_sticky_hft(tmp_path):
    import json
    from pathlib import Path
    from mission_agent.signals.store import Ledger
    from mission_agent.signals.engine import Engine
    from mission_agent.signals.policy import load_policy
    from test_frank_local_signals import active,put
    counts=[]
    for name,times in [('current',[100000,101200,102800]),('restored',[100000,100010,100020,101200,102800])]:
        ledger=Ledger(tmp_path/(name+'.sqlite'))
        engine=Engine(ledger,load_policy(Path(__file__).parents[2]/'config/frank_local_signal_v1.json'))
        for at in times:
            event=active('real-'+str(at),100,13000);event['block_time']=at;event['slot']=at
            event['trade'].update(quote_asset=USDC,quote_amount_raw='13000000000',quote_decimals=6)
            put(ledger,event);engine.drain()
        counts.append(engine.summary()['multiple_trigger_count'])
        assert not ledger.db.execute("select 1 from outbox where status!='DRY_RUN_AUDIT'").fetchone()
    assert counts==[1,0]
