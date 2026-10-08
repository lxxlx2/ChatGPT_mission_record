"""Pure deterministic V1 predicates over verified observed active chronology."""
from decimal import Decimal
from .policy import USDC

D=Decimal

KNOWN_USDC_PREDICATES=frozenset({'USDC_DIRECT_NUMERIC','SOL_EVENT_TIME_USDC_VERIFIED'})

def known_usdc_event(event):
    predicate=event.get('amount_predicate')
    # Legacy direct-USDC rows predate explicit provenance. Preserve only that
    # narrow compatibility case; all explicit UNKNOWN/UNDETERMINED provenance
    # remains non-authoritative.
    if predicate is None:
        return event.get('quote_asset')==USDC and not event.get('amount_predicate_reason')
    return predicate in KNOWN_USDC_PREDICATES and event.get('quote_asset')==USDC

def amount(events):
    known=sum((D(e['quote_quantity']) for e in events if known_usdc_event(e)),D(0))
    unknown=any(not known_usdc_event(e) for e in events)
    return known,unknown

def amount_gate(events,minimum):
    known,unknown=amount(events)
    return 'PASS' if known>=D(minimum) else 'UNDETERMINED' if unknown else 'FAIL'

def watch_tick(at):return (int(at)-1740)//3600*3600+1740

def evaluate(state,at,policy):
    """Never mutates input; same state/clock/policy yields identical predicates/reasons."""
    a=policy['mapping']['FRANK_ACCUMULATION_SIGNAL'];m=policy['mapping']['FRANK_MULTIPLE_SIGNAL']
    events=state['events'];buys=[e for e in events if e['direction']=='BUY']
    recent=[e for e in buys if at-a['window_seconds']<=e['at']<=at]
    gates={'accumulation_buy_count':'PASS' if len(recent)>=a['count_min'] else 'FAIL','accumulation_amount':amount_gate(recent,a['quote_quantity_min'])}
    open_known=state['current_raw'] is not None and int(state['current_raw'])>0 and state['state']=='OPEN'
    accumulation=all(gates[k]=='PASS' for k in ['accumulation_buy_count','accumulation_amount']) and open_known
    prior=state.get('accumulation_emitted',False) or accumulation
    span=(buys[-1]['at']-buys[0]['at']) if buys else 0
    prior_watch=state.get('watch_at')==watch_tick(at)-3600
    path_b=len(buys)>=m['persistence']['B']['buy_count_min'] and span>=m['persistence']['B']['buy_span_seconds_min']
    recent_trades=[e for e in events if at-m['net_buy_window_seconds']<=e['at']<=at]
    net=sum((int(e['token_amount_raw'])*(1 if e['direction']=='BUY' else -1) for e in recent_trades),0)
    current=D(state['current_raw']) if state['current_raw'] is not None else None;peak=D(state['peak_raw'])
    retained=current is not None and peak>0 and current/peak>=D(m['retention_ratio_min'])
    # Include the inventory carried into the rolling window; no future peak is used.
    points=state['inventory_points'];cutoff=at-m['distribution_window_seconds'];inside=[p for p in points if cutoff<=p['at']<=at];before=[p for p in points if p['at']<cutoff]
    if before:inside.insert(0,before[-1])
    rolling_peak=max((D(p['raw']) for p in inside if p['raw'] is not None),default=D(0))
    drop=(rolling_peak-current)/rolling_peak if current is not None and rolling_peak>0 else None
    sells=[e for e in recent_trades if e['direction']=='SELL'];fresh_reaccumulation=bool(sells and buys and buys[-1]['at']>sells[-1]['at'])
    distribution=drop is not None and drop>D(m['distribution_drop_ratio_gt']) and not fresh_reaccumulation
    t0=state.get('t0');fresh_buy=bool(buys and at-buys[-1]['at']<=m['fresh_buy_window_seconds'])
    stale=t0 is not None and at-t0>m['stale_after_seconds']
    gates.update(prior_accumulation='PASS' if prior else 'FAIL',t0='PASS' if t0 is not None else state.get('t0_amount_status','FAIL'),
                 cumulative_amount=amount_gate(buys,m['cumulative_amount_min']),persistence='PASS' if prior_watch or path_b else 'FAIL',
                 inventory='PASS' if open_known and (retained or net>0) else 'UNDETERMINED' if current is None else 'FAIL',
                 distribution='UNDETERMINED' if current is None else 'FAIL' if distribution else 'PASS',
                 hft='FAIL' if state.get('hft',False) else 'PASS',freshness='PASS' if not stale or (fresh_buy and open_known) else 'FAIL')
    multiple=all(gates[k]=='PASS' for k in ['prior_accumulation','t0','cumulative_amount','persistence','inventory','distribution','hft','freshness'])
    stages=[]
    if accumulation:stages.append({'signal_type':'FRANK_ACCUMULATION_SIGNAL','stage':'PRECONFIRM','reason_codes':['PATH_C_REPEATED_ACTIVE_BUYS_GE_2','ROLLING_60M_USDC_QUOTE_GE_25000','PATH_C_SINGLE_LARGE_BUY_NOT_ACCUMULATION']})
    if multiple:stages.append({'signal_type':'FRANK_MULTIPLE_SIGNAL','stage':'SUSPECTED_CONVICTION','reason_codes':['ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED','MEANINGFUL_ACCUMULATION_T0_ESTABLISHED','EPISODE_USDC_QUOTE_GE_10000','PERSISTENCE_PATH_A_PRIOR_HOURLY_WATCH' if prior_watch else 'PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M','OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING','NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION','NO_CONFIRMED_HFT_EXECUTION','FRESHNESS_BEHAVIOR_PASSED','NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT']})
    return {'stages':stages,'predicates':gates,'known_rolling_usdc':str(amount(recent)[0]),'known_episode_usdc':str(amount(buys)[0]),'buy_count':len(buys),'buy_span_seconds':span,'inventory_scope':'OBSERVED_ACTIVE_SEQUENCE','lifetime_position':'LIFETIME_POSITION_UNKNOWN','sequence':'CURRENT_ACCUMULATION_SEQUENCE_KNOWN','usd_estimate':'unavailable'}

def watch_eligible(state,at,policy):
    m=policy['mapping']['FRANK_MULTIPLE_SIGNAL'];recent=[e for e in state['events'] if at-3600<=e['at']<=at]
    buys=[e for e in recent if e['direction']=='BUY'];sells=[e for e in recent if e['direction']=='SELL']
    buy,bu=amount(buys);sell,su=amount(sells)
    return len(buys)>=2 and not bu and not su and buy>sell and state['current_raw'] is not None and int(state['current_raw'])>0 and not state.get('hft',False)

def establish_t0(state,policy):
    if state.get('t0') is not None:return
    m=policy['mapping']['FRANK_MULTIPLE_SIGNAL'];buys=[e for e in state['events'] if e['direction']=='BUY']
    if not buys:return
    last=buys[-1];recent=[e for e in buys if last['at']-m['t0_window_seconds']<=e['at']<=last['at']]
    repeat=len(recent)>=m['t0_repeated_buy_count'] and amount_gate(recent,m['t0_repeated_amount_min'])=='PASS'
    large=any(known_usdc_event(e) and D(e['quote_quantity'])>=D(m['t0_large_buy_min']) for e in recent[:-1])
    state['t0_amount_status']='UNDETERMINED' if any(not known_usdc_event(e) for e in recent) and not (repeat or large) else 'FAIL'
    if repeat or large:state['t0']=last['at'];state['t0_amount_status']='PASS'
