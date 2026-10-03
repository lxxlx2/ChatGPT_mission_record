"""Point-in-time features; no terminal episode columns accepted."""
WINDOWS={'5m':300,'15m':900,'30m':1800,'1h':3600,'6h':21600,'24h':86400}
def snapshot(events,t,market=()):
    past=sorted([e for e in events if e['block_time']<=t],key=lambda e:(e['block_time'],e.get('slot',0),e['event_id']))
    trades=[e for e in past if e['event_type'] in {'MARKET_BUY','MARKET_SELL'}]; buys=[e for e in trades if e['event_type']=='MARKET_BUY']
    f={'as_of':t,'time_since_first_buy':t-buys[0]['block_time'] if buys else None,'time_since_prev_buy':t-buys[-2]['block_time'] if len(buys)>1 else None}
    for label,w in WINDOWS.items():
        rows=[e for e in trades if t-w<=e['block_time']<=t];b=[e for e in rows if e['event_type']=='MARKET_BUY']
        f['buys_'+label]=len(b)
        f['gross_buy_'+label]=sum(e['usd_notional'] for e in b) if all(e.get('usd_notional') is not None for e in b) else None
        f['net_buy_'+label]=sum(e['usd_notional']*(1 if e['event_type']=='MARKET_BUY' else -1) for e in rows) if all(e.get('usd_notional') is not None for e in rows) else None
    f['buy_velocity']=f['buys_5m']/300
    previous=sum(1 for e in buys if t-600<=e['block_time']<t-300)/300
    f['buy_velocity_acceleration']=f['buy_velocity']-previous
    qty=sum(float(e['token_delta']) for e in trades); initial=float(buys[0]['token_delta']) if buys else None
    f['position_growth_ratio']=qty/initial if initial else None
    f['sell_during_accumulation']=any(e['event_type']=='MARKET_SELL' for e in trades)
    f['partial_sell_ratio']=sum(-float(e['token_delta']) for e in trades if e['event_type']=='MARKET_SELL')/sum(float(e['token_delta']) for e in buys) if buys else None
    points=sorted([m for m in market if m['timestamp']<=t and m.get('available_at',m['timestamp'])<=t],key=lambda m:m['timestamp'])
    latest=points[-1] if points else {}
    for k in ['market_cap','liquidity','volume_5m','volume_15m','volume_1h','holder_count','token_age']: f[k]=latest.get(k)
    first_price=buys[0].get('price_usd') if buys else None; prev_price=buys[-2].get('price_usd') if len(buys)>1 else None;price=latest.get('price_usd')
    f['price_change_since_first_buy']=price/first_price-1 if price is not None and first_price else None
    f['price_change_since_prev_buy']=price/prev_price-1 if price is not None and prev_price else None
    cost=0.0;position=0.0;green=0;red=0;known=True;pre_add_pnl=None
    for e in trades:
        delta=float(e['token_delta']); value=e.get('usd_notional'); ep=e.get('price_usd')
        if e['event_type']=='MARKET_BUY':
            if position>0 and ep is not None and known:
                pnl=position*ep-cost
                if e['block_time']==t: pre_add_pnl=pnl
                green+=pnl>0;red+=pnl<0
            position+=delta
            if value is None: known=False
            else: cost+=value
        else:
            if position<=0 or -delta>position: known=False
            elif known: cost*=1+delta/position
            position+=delta
    f['unrealized_pnl_before_add']=pre_add_pnl
    f['adds_on_green_count']=green if known else None;f['adds_on_drawdown_count']=red if known else None
    first_points=[m for m in points if buys and m['timestamp']<=buys[0]['block_time']]
    first=first_points[-1] if first_points else {}
    for source,target in [('market_cap','market_cap_change'),('liquidity','liquidity_change'),('holder_count','holder_growth')]:
        f[target]=latest[source]/first[source]-1 if latest.get(source) is not None and first.get(source) else None
    f['volume_expansion_ratio']=latest['volume_5m']/latest['volume_1h']*12 if latest.get('volume_5m') is not None and latest.get('volume_1h') else None
    f['internal_transfer_ratio']=sum(e['event_type']=='INTERNAL_TRANSFER' for e in past)/len(past) if past else None
    return f
