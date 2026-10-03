"""Historical executable quotes only. No candle or source-wallet fill fallback."""
class HistoricalQuoteProvider:
    def quote(self,mint,t,notional,side='BUY'): return None
class FileQuoteProvider(HistoricalQuoteProvider):
    def __init__(self,rows): self.rows=rows
    def quote(self,mint,t,notional,side='BUY'):
        rows=[q for q in self.rows if q['mint']==mint and q['timestamp']==t and q['notional_usd']==notional and q.get('side','BUY')==side and q.get('historical_pool_evidence')]
        if len(rows)>1: raise ValueError('AMBIGUOUS_HISTORICAL_QUOTE')
        return rows[0] if rows else None
def replay(signal,delay,provider,policy,episode=None):
    t=signal['T_signal']+delay; notional=policy['small_user_notional_usd'];q=provider.quote(signal['mint'],t,notional)
    row={**{k:signal[k] for k in ['signal_id','episode_id','person_id','mint','T_signal']},'delay':delay,'entry_time':t,'entry_notional':notional,'entry_price':None,'quantity':None,'route':None,'liquidity':None,'slippage':None,'price_impact':None,'fees':None,'followable':False,'post_signal_mfe':None,'post_signal_mae':None,'return_to_source_first_sell':None,'return_to_source_full_exit':None,'fixed_horizon_returns':{str(h):None for h in policy['canonical_horizons']},'max_drawdown':None,'status':'UNAVAILABLE','failure_reason':'HISTORICAL_PRICE_MISSING','censored':True}
    if q is None: return row
    if q['timestamp']!=t: raise ValueError('QUOTE_TIMESTAMP_MISMATCH')
    required=['price','quantity','route','liquidity','slippage','price_impact','fees','historical_pool_evidence']
    if any(q.get(k) is None for k in required): row['failure_reason']='EXECUTABLE_QUOTE_INCOMPLETE';return row
    if q['quantity']<=0 or q['price']<=0: row['failure_reason']='INVALID_EXECUTABLE_QUOTE';return row
    if not q.get('executable',False) or q['liquidity']<notional or (policy['max_price_impact'] is not None and q['price_impact']>policy['max_price_impact']): row.update(status='UNFOLLOWABLE',failure_reason='INSUFFICIENT_LIQUIDITY_OR_IMPACT');return row
    row.update(entry_price=q['price'],quantity=q['quantity'],route=q['route'],liquidity=q['liquidity'],slippage=q['slippage'],price_impact=q['price_impact'],fees=q['fees'],followable=True,status='ENTRY_ONLY',failure_reason='EXIT_QUOTES_OR_PATH_MISSING')
    for h in policy['canonical_horizons']:
        exitq=provider.quote(signal['mint'],t+h,notional,'SELL')
        if exitq and exitq.get('executable') and exitq.get('quantity')==q['quantity'] and exitq.get('proceeds_usd') is not None:
            row['fixed_horizon_returns'][str(h)]=exitq['proceeds_usd']/(notional+q['fees'])-1
    if all(v is not None for v in row['fixed_horizon_returns'].values()): row['status']='HORIZONS_COMPLETE_PATH_UNAVAILABLE'
    episode=episode or {}
    for source,target in [('first_sell_time','return_to_source_first_sell'),('full_exit_time','return_to_source_full_exit')]:
        when=episode.get(source)
        if when is not None and when>=t:
            exitq=provider.quote(signal['mint'],when,notional,'SELL')
            if exitq and exitq.get('executable') and exitq.get('quantity')==q['quantity'] and exitq.get('proceeds_usd') is not None: row[target]=exitq['proceeds_usd']/(notional+q['fees'])-1
    row['censored']=episode.get('full_exit_time') is None
    path=q.get('executable_exit_path',[])
    values=[]
    for point in path:
        if point.get('timestamp',0)>=t and point.get('historical_pool_evidence') and point.get('quantity')==q['quantity'] and point.get('executable') and point.get('proceeds_usd') is not None:
            values.append((point['timestamp'],point['proceeds_usd']/(notional+q['fees'])-1))
    if values and q.get('path_coverage_complete'):
        vals=[v for _,v in sorted(values)];row['post_signal_mfe']=max(vals);row['post_signal_mae']=min(vals)
        peak=1.0;drawdown=0.0
        for v in vals:
            peak=max(peak,1+v);drawdown=min(drawdown,(1+v)/peak-1)
        row['max_drawdown']=drawdown
        if all(v is not None for v in row['fixed_horizon_returns'].values()): row.update(status='COMPLETE',failure_reason=None)
    return row
