"""Evidence-only replay for Mission Meme follow thresholds.

Consumes durable follow_observations from mission-control.sqlite. It does not
change policy. Results with fewer than --min-samples are explicitly insufficient.
Returns are BUY-side executable-quote mark-to-market comparisons; they exclude
sell-side slippage, fees and taxes and therefore are not realized-PnL estimates.
"""
from __future__ import annotations

import argparse,json,statistics
from decimal import Decimal,InvalidOperation
from pathlib import Path

from mission_agent.mission_control.db import open_control_ro

RETURN_BASIS='BUY_SIDE_EXECUTABLE_QUOTE_MARK_TO_MARK_EXCLUDES_SELL_SLIPPAGE_AND_FEES'


def D(value):
    try:return Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError):return None


def pct_return(start,end):
    a,b=D(start),D(end)
    if a is None or b is None or a<=0:return None
    return float((b/a-Decimal(1))*Decimal(100))


def median(values):
    values=[v for v in values if v is not None]
    return statistics.median(values) if values else None


def outcome(rows,target,tolerance=180):
    window=[r for r in rows if target<=r['bucket_start']<=target+tolerance]
    valid=[r for r in window if r['route_exists']==1 and D(r['execution_price_usdc']) is not None]
    if valid:
        return {'status':'OBSERVED','row':min(valid,key=lambda r:r['bucket_start'])}
    if any(r['route_exists']==0 for r in window):return {'status':'NO_ROUTE','row':None}
    if window:return {'status':'PRICE_UNAVAILABLE','row':None}
    return {'status':'NO_OBSERVATION','row':None}


def episode_samples(db):
    rows=[dict(r) for r in db.execute('SELECT * FROM follow_observations ORDER BY entity_key,bucket_start')]
    grouped={}
    for row in rows:grouped.setdefault(row['entity_key'],[]).append(row)
    samples=[]
    for entity,items in grouped.items():
        initial=next((r for r in items if r['runtime_status']=='LIVE' and r['route_exists']==1 and D(r['execution_price_usdc']) is not None and D(r['price_deviation_pct']) is not None and D(r['price_impact_pct']) is not None),None)
        if not initial:continue
        o15=outcome(items,initial['bucket_start']+15*60);o60=outcome(items,initial['bucket_start']+60*60)
        p15=o15['row'];p60=o60['row']
        samples.append({'entity_key':entity,'person_id':initial['person_id'],'mint':initial['mint'],'episode_id':initial['episode_id'],'pattern':initial['pattern'],'at':initial['bucket_start'],'execution_price_usdc':initial['execution_price_usdc'],'price_deviation_pct':initial['price_deviation_pct'],'price_impact_pct':initial['price_impact_pct'],'return_15m_pct':pct_return(initial['execution_price_usdc'],p15['execution_price_usdc']) if p15 else None,'return_60m_pct':pct_return(initial['execution_price_usdc'],p60['execution_price_usdc']) if p60 else None,'outcome_15m_status':o15['status'],'outcome_60m_status':o60['status']})
    return samples


def classify(sample,buy_dev,buy_impact,small_dev,small_impact):
    dev=D(sample['price_deviation_pct']);impact=D(sample['price_impact_pct']);pattern=sample['pattern']
    if dev is None or impact is None:return 'WAIT'
    if pattern=='MULTIPLE' and dev<=D(buy_dev) and impact<=D(buy_impact):return 'BUY'
    if pattern in {'MULTIPLE','ACCUMULATION'} and dev<=D(small_dev) and impact<=D(small_impact):return 'SMALL_BUY'
    return 'WAIT'


def metrics(samples,decision,min_samples):
    selected=[s for s in samples if s['candidate_decision']==decision]
    r15=[s['return_15m_pct'] for s in selected if s['return_15m_pct'] is not None]
    r60=[s['return_60m_pct'] for s in selected if s['return_60m_pct'] is not None]
    censored15=[s for s in selected if s['return_15m_pct'] is None]
    censored60=[s for s in selected if s['return_60m_pct'] is None]
    pessimistic15=r15+[-100.0]*len(censored15)
    pessimistic60=r60+[-100.0]*len(censored60)
    if len(selected)<min_samples:status='INSUFFICIENT_SAMPLE'
    elif censored60:status='EVALUABLE_WITH_CENSORING'
    else:status='EVALUABLE'
    return {
        'decision':decision,
        'sample_count':len(selected),
        'return_15m_count':len(r15),
        'return_60m_count':len(r60),
        'censored_15m_count':len(censored15),
        'censored_60m_count':len(censored60),
        'no_route_60m_count':sum(s['outcome_60m_status']=='NO_ROUTE' for s in selected),
        'price_unavailable_60m_count':sum(s['outcome_60m_status']=='PRICE_UNAVAILABLE' for s in selected),
        'no_observation_60m_count':sum(s['outcome_60m_status']=='NO_OBSERVATION' for s in selected),
        'median_return_15m_pct':median(r15),
        'median_return_60m_pct':median(r60),
        'positive_15m_rate':sum(v>0 for v in r15)/len(r15) if r15 else None,
        'positive_60m_rate':sum(v>0 for v in r60)/len(r60) if r60 else None,
        'worst_60m_pct':min(r60) if r60 else None,
        'pessimistic_median_15m_pct':median(pessimistic15),
        'pessimistic_median_60m_pct':median(pessimistic60),
        'pessimistic_positive_60m_rate':sum(v>0 for v in pessimistic60)/len(pessimistic60) if pessimistic60 else None,
        'pessimistic_worst_60m_pct':min(pessimistic60) if pessimistic60 else None,
        'status':status,
    }


def replay(path:Path,min_samples=30):
    db=open_control_ro(path)
    try:samples=episode_samples(db)
    finally:db.close()
    grid=[]
    for buy_dev in (5,8,10,12,15):
        for buy_impact in (0.5,1,1.5,2):
            for small_dev in (15,20,25):
                for small_impact in (2,3,5):
                    if small_dev<buy_dev or small_impact<buy_impact:continue
                    marked=[{**s,'candidate_decision':classify(s,buy_dev,buy_impact,small_dev,small_impact)} for s in samples]
                    grid.append({'thresholds':{'buy_deviation_pct':buy_dev,'buy_impact_pct':buy_impact,'small_deviation_pct':small_dev,'small_impact_pct':small_impact},'buy':metrics(marked,'BUY',min_samples),'small_buy':metrics(marked,'SMALL_BUY',min_samples)})
    return {'schema_version':2,'source':str(path),'sample_count':len(samples),'min_samples':min_samples,'return_basis':RETURN_BASIS,'censoring_policy':'MISSING_15M_OR_60M_EXECUTABLE_PRICE_REPORTED_EXPLICITLY; PESSIMISTIC_BOUND_TREATS_CENSORED_AS_-100_PERCENT','selection_warning':'EXPLORATORY_GRID_ONLY_NO_AUTOMATIC_WINNER_MULTIPLE_TESTING_AND_OVERFITTING_RISK','samples':samples,'grid':grid,'automatic_policy_change':False,'production_trading':'NO_GO'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--min-samples',type=int,default=30);a=p.parse_args();result=replay(a.db,a.min_samples);a.out.write_text(json.dumps(result,indent=2,sort_keys=True));print(json.dumps({'sample_count':result['sample_count'],'grid_count':len(result['grid'])},sort_keys=True))

if __name__=='__main__':main()
