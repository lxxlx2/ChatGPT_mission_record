from decimal import Decimal
from statistics import median, quantiles
FIELDS='episode_id person_id mint contributing_wallets first_market_buy_time first_market_buy_signature first_buy_price first_buy_usd second_buy_time second_buy_usd accumulation_start accumulation_end buy_count sell_count gross_buy_usd gross_sell_usd net_cost_basis_usd average_entry peak_net_exposure_usd current_net_exposure_usd position_growth_ratio time_to_2x_initial_position time_to_3x_initial_position median_inter_buy_gap p25_inter_buy_gap p75_inter_buy_gap first_sell_time full_exit_time realized_pnl_usd realized_roi unrealized_pnl_usd holding_duration mfe mae full_exit entry_market_cap entry_liquidity entry_volume token_age_seconds holder_concentration reconstruction_status source_signatures boundary_reason'.split()
def build_episodes(events,person_id,dust='0',history_complete=False):
    active={}; output=[]; counts={}; state={}
    for e in sorted(events,key=lambda e:(e['block_time'],e.get('slot',0),e['event_id'])):
        mint=e.get('mint'); kind=e['event_type']
        if not mint: continue
        if kind=='INTERNAL_TRANSFER': continue
        if kind not in {'MARKET_BUY','MARKET_SELL'}:
            if kind not in {'FEE','ATA_CREATE','PLATFORM_INFRA'} and mint in active: active[mint]['reconstruction_status']='QUALIFICATION_BLOCKED'
            continue
        qty=Decimal(str(e['token_delta'])); usd=e.get('usd_notional'); usd=Decimal(str(usd)) if usd is not None else None
        s=state.setdefault(mint,{'qty':Decimal(0),'cost':Decimal(0),'known':True})
        if mint not in active:
            if kind!='MARKET_BUY' or qty<=Decimal(dust): continue
            counts[mint]=counts.get(mint,0)+1
            ep={k:None for k in FIELDS};ep.update(episode_id=f'{person_id}:{mint}:{counts[mint]}',person_id=person_id,mint=mint,contributing_wallets=[],source_signatures=[],buy_count=0,sell_count=0,gross_buy_usd=0.0,gross_sell_usd=0.0,realized_pnl_usd=0.0,full_exit=False,first_market_buy_time=e['block_time'],first_market_buy_signature=e['signature'],first_buy_usd=float(usd) if usd is not None else None,first_buy_price=float(usd/qty) if usd is not None else None,boundary_reason='MARKET_BUY_FROM_ZERO_OR_DUST',reconstruction_status='PARTIAL_HISTORY',accumulation_start=e['block_time'],peak_net_exposure_usd=0.0)
            active[mint]=ep;s.update(qty=Decimal(0),cost=Decimal(0),known=True);ep['_buys']=[];ep['_initial']=qty
        ep=active[mint]
        if e.get('wallet') not in ep['contributing_wallets']: ep['contributing_wallets'].append(e.get('wallet'))
        ep['source_signatures'].append(e['signature'])
        if usd is None: s['known']=False
        if kind=='MARKET_BUY':
            s['qty']+=qty
            if usd is not None: s['cost']+=usd
            ep['buy_count']+=1;ep['_buys'].append(e['block_time']);ep['accumulation_end']=e['block_time']
            ep['gross_buy_usd']=ep['gross_buy_usd']+float(usd) if usd is not None and ep['gross_buy_usd'] is not None else None
            if ep['buy_count']==2: ep['second_buy_time']=e['block_time'];ep['second_buy_usd']=float(usd) if usd is not None else None
        else:
            sold=-qty
            if sold>s['qty'] or s['qty']<=0: s['known']=False
            removed=s['cost']*min(sold/s['qty'],Decimal(1)) if s['qty']>0 else Decimal(0)
            s['cost']-=removed;s['qty']+=qty;ep['sell_count']+=1
            ep['first_sell_time']=ep['first_sell_time'] or e['block_time']
            ep['gross_sell_usd']=ep['gross_sell_usd']+float(usd) if usd is not None and ep['gross_sell_usd'] is not None else None
            if usd is not None and ep['realized_pnl_usd'] is not None: ep['realized_pnl_usd']+=float(usd-removed)
        ep['net_cost_basis_usd']=float(s['cost']) if s['known'] else None
        ep['current_net_exposure_usd']=ep['net_cost_basis_usd']
        ep['average_entry']=float(s['cost']/s['qty']) if s['known'] and s['qty']>0 else None
        ep['position_growth_ratio']=float(s['qty']/ep['_initial'])
        for multiple in (2,3):
            key=f'time_to_{multiple}x_initial_position'
            if ep[key] is None and s['qty']>=multiple*ep['_initial']: ep[key]=e['block_time']-ep['first_market_buy_time']
        if s['known']: ep['peak_net_exposure_usd']=max(ep['peak_net_exposure_usd'] or 0,float(s['cost']))
        else: ep['realized_pnl_usd']=None;ep['peak_net_exposure_usd']=None
        ep['holding_duration']=e['block_time']-ep['first_market_buy_time']
        if s['qty']<=Decimal(dust):
            ep['full_exit']=True;ep['full_exit_time']=e['block_time'];ep['boundary_reason']+=';CONFIRMED_ZERO_OR_DUST_EXIT'
            if history_complete and s['known'] and ep['reconstruction_status']!='QUALIFICATION_BLOCKED': ep['reconstruction_status']='RECONSTRUCTED_PENDING_BALANCE_RECONCILIATION'
            output.append(ep);del active[mint]
    output.extend(active.values())
    for ep in output:
        times=ep.pop('_buys');ep.pop('_initial'); gaps=[b-a for a,b in zip(times,times[1:])]
        if gaps:
            ep['median_inter_buy_gap']=median(gaps)
            if len(gaps)>1: qs=quantiles(gaps,n=4,method='inclusive');ep['p25_inter_buy_gap']=qs[0];ep['p75_inter_buy_gap']=qs[2]
        ep['realized_roi']=ep['realized_pnl_usd']/ep['gross_buy_usd'] if ep['full_exit'] and ep['realized_pnl_usd'] is not None and ep['gross_buy_usd'] else None
    return output
