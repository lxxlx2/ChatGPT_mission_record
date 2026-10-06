"""Evidence-only replay for Mission Meme follow thresholds.

Consumes durable follow_observations from mission-control.sqlite. It does not
change policy. Results with fewer than --min-samples are explicitly insufficient.
"""
from __future__ import annotations

import argparse,json,statistics
from decimal import Decimal,InvalidOperation
from pathlib import Path

from mission_agent.mission_control.db import open_control_ro


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


def nearest(rows,target,tolerance=180):
    candidates=[r for r in rows if target<=r['bucket_start']<=target+tolerance and D(r['execution_price_usdc']) is not None]
    return min(candidates,key=lambda r:r['bucket_start']) if candidates else None


def episode_samples(db):
    rows=[dict(r) for r in db.execute('SELECT * FROM follow_observations ORDER BY entity_key,bucket_start')]
    grouped={}
    for row in rows:grouped.setdefault(row['entity_key'],[]).append(row)
    samples=[]
    for entity,items in grouped.items():
        initial=next((r for r in items if r['runtime_status']=='LIVE' and r['route_exists']==1 and D(r['execution_price_usdc']) is not None and D(r['price_deviation_pct']) is not None and D(r['price_impact_pct']) is not None),None)
        if not initial:continue
        p15=nearest(items,initial['bucket_start']+15*60);p60=nearest(items,initial['bucket_start']+60*60)
        samples.append({'entity_key':entity,'person_id':initial['person_id'],'mint':initial['mint'],'episode_id':initial['episode_id'],'pattern':initial['pattern'],'at':initial['bucket_start'],'execution_price_usdc':initial['execution_price_usdc'],'price_deviation_pct':initial['price_deviation_pct'],'price_impact_pct':initial['price_impact_pct'],'return_15m_pct':pct_return(initial['execution_price_usdc'],p15['execution_price_usdc']) if p15 else None,'return_60m_pct':pct_return(initial['execution_price_usdc'],p60['execution_price_usdc']) if p60 else None})
    return samples


def classify(sample,buy_dev,buy_impact,small_dev,small_impact):
    dev=D(sample['price_deviation_pct']);impact=D(sample['price_impact_pct']);pattern=sample['pattern']
    if dev is None or impact is None:return 'WAIT'
    if pattern=='MULTIPLE' and dev<=D(buy_dev) and impact<=D(buy_impact):return 'BUY'
    if pattern in {'MULTIPLE','ACCUMULATION'} and dev<=D(small_dev) and impact<=D(small_impact):return 'SMALL_BUY'
    return 'WAIT'


def metrics(samples,decision,min_samples):
    selected=[s for s in samples if s['candidate_decision']==decision];r15=[s['return_15m_pct'] for s in selected if s['return_15m_pct'] is not None];r60=[s['return_60m_pct'] for s in selected if s['return_60m_pct'] is not None]
    return {'decision':decision,'sample_count':len(selected),'return_15m_count':len(r15),'return_60m_count':len(r60),'median_return_15m_pct':median(r15),'median_return_60m_pct':median(r60),'positive_15m_rate':sum(v>0 for v in r15)/len(r15) if r15 else None,'positive_60m_rate':sum(v>0 for v in r60)/len(r60) if r60 else None,'worst_60m_pct':min(r60) if r60 else None,'status':'EVALUABLE' if len(r60)>=min_samples else 'INSUFFICIENT_SAMPLE'}


def replay(path:Path,min_samples=10):
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
    return {'schema_version':1,'source':str(path),'sample_count':len(samples),'min_samples':min_samples,'samples':samples,'grid':grid,'automatic_policy_change':False,'production_trading':'NO_GO'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--min-samples',type=int,default=10);a=p.parse_args();result=replay(a.db,a.min_samples);a.out.write_text(json.dumps(result,indent=2,sort_keys=True));print(json.dumps({'sample_count':result['sample_count'],'grid_count':len(result['grid'])},sort_keys=True))

if __name__=='__main__':main()
