#!/usr/bin/env python3
"""Independent review only: no production strategy edits, notification or trade.
Schedules are independently implemented here; upstream raw-market replay is
explicitly a reproducibility check of the frozen implementation, not a second
independent implementation of V4. --official checks EVERY 2700 source attempt.
"""
import argparse, collections, concurrent.futures, hashlib, json, sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPTS))
E=SCRIPTS.parents[1]/'monster'/'evidence'
BASELINE='2cfaea7064012869ae264a16d776b2cb7e6b52a9'

def read(name):
    return [json.loads(x) for x in (E/name).read_text().splitlines() if x]

def minute(s):
    return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()//60)

def independent_raw_events(bars,day):
    """Separate scalar D0 and P1 implementation; no production/P1 evaluator call.
    Mirrors only the frozen three-minute polling contract for source comparison.
    """
    watches=[];samples=[];last_watch=None;watch_price=None;invalid=False
    quote=collections.deque();quote_sum=Decimal(0)
    # Original runner first polls at active minute 3, with no pre-active snapshots.
    for i,b in enumerate(bars):
        quote.append(b[5]);quote_sum+=b[5]
        if len(quote)>1440:quote_sum-=quote.popleft()
        if i<1442 or (i-1442)%3:continue
        at=b[0]+60000;price=b[4]
        if last_watch is not None and not invalid and price<=watch_price*Decimal('.85'):invalid=True
        returns=[]
        if samples and price/samples[-1][1]-1>=Decimal('.05'):returns.append(True)
        for lag,tolerance,threshold in ((15,3,Decimal('.08')),(60,6,Decimal('.15'))):
            target=at-lag*60000
            # Regular 3m grid: nearest eligible prior tick, including startup tolerance.
            k=max(0,len(samples)-lag//3)
            if samples and abs(samples[k][0]-target)<=tolerance*60000 and price/samples[k][1]-1>=threshold:returns.append(True)
        samples.append((at,price))
        if not returns or quote_sum<100000:continue
        if last_watch is not None and not invalid and at-last_watch<6*3600000:continue
        watches.append(at);last_watch=at;watch_price=price;invalid=False
    p1=None
    if watches:
        first=watches[0];first_i=(first-bars[0][0])//60000-1;first_price=bars[first_i][4]
        end=minute(day+'T06:00:00Z')*60000+168*3600000
        for t in range(first,end,180000):
            i=(t-bars[0][0])//60000-1
            price=bars[i][4];q15=sum((b[5] for b in bars[i-14:i+1]),Decimal(0));q45=sum((b[5] for b in bars[i-59:i-14]),Decimal(0))
            ratio=3*q15/q45 if q45 else None;ret60=(price/bars[i-60][4]-1)*100;retfirst=(price/first_price-1)*100
            if ratio is not None and ratio>=Decimal('1.5') and ((t==first and ret60>=14 and q15>=3000000) or (t>first and retfirst>=15 and ret60>=8 and q15>=2000000)):
                p1=t;break
    baseline=bars[1440][1]
    high=next((b[0] for b in bars[1440:] if b[2]>=baseline*2),None)
    def stamp(t):return datetime.fromtimestamp(t/1000,__import__('datetime').timezone.utc).isoformat().replace('+00:00','Z') if t is not None else None
    return dict(WATCH_UTC=[stamp(t) for t in watches],P1=stamp(p1),first_2x=stamp(high))

def five_oracle(out):
    import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    rows=read('monster_stage66_full2700_originalV4_D0_and_P1v03_source_SHA.jsonl')
    cases=[]
    for r in rows:
        if r['minute_source_status']!='COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4' or not r['hourly_gt2x_EVALUATION_ONLY']:continue
        bars,proof=src.minute_source(r['symbol'],r['date']);actual=independent_raw_events(bars,r['date'])
        assert proof==r['source_9_daily_minute_publisher_SHA']
        assert actual['WATCH_UTC']==r['original_D0_all_WATCH_UTC'],r['symbol']+' INDEPENDENT_D0_DRIFT'
        assert actual['P1']==r['P1v03_original_unbudgeted_candidate']['at_UTC']
        assert actual['first_2x']==r['original_GT2x_first_real_1m_HIGH_UTC']
        cases.append(dict(date=r['date'],symbol=r['symbol'],**actual,official_daily_sha=proof))
        print('INDEPENDENT_RAW_FIVE_ORACLE_PASS',r['symbol'],flush=True)
    (out/'monster_stage71_five_official_raw_independent_oracle.json').write_text(json.dumps(dict(baseline=BASELINE,cases=cases),indent=2,sort_keys=True)+'\n')

def recalculate(rows):
    """No Stage68 summary, event ledger, old fates or allocator used as input."""
    events=[]
    for r in rows:
        if r['minute_source_status']!='COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4':continue
        if r['original_D0_first_UTC']:
            events.append(dict(date=r['date'],symbol=r['symbol'],kind='FIRST_D0_WATCH',at=r['original_D0_first_UTC'],quote=r['D0_first_quote15_USDM_asof']))
        p=r['P1v03_original_unbudgeted_candidate']
        if p:events.append(dict(date=r['date'],symbol=r['symbol'],kind='P1_FIRST_ASOF_ELIGIBLE',at=p['at_UTC'],quote=p['features']['quote15_USDT']))
    events.sort(key=lambda e:(minute(e['at']),e['kind']!='FIRST_D0_WATCH',-Decimal(e['quote']),e['symbol']))
    used_old=collections.Counter();used_new=collections.Counter();early=collections.Counter()
    old={};new={};watch={};ledger=[]
    for e in events:
        elapsed=minute(e['at'])-minute(e['date']+'T06:00:00Z')
        assert 0<=elapsed<10080 and elapsed%3==0
        slot=e['date'],elapsed//1440
        key=e['date'],e['symbol']
        if e['kind']=='FIRST_D0_WATCH':
            assert key not in watch
            watch[key]=e['at'];continue
        assert key in watch and minute(watch[key])<=minute(e['at']) and key not in old
        o=used_old[slot]<5
        n=used_new[slot]<5 and (elapsed%1440>=720 or early[slot]<2)
        old[key]=o;new[key]=n
        used_old[slot]+=o;used_new[slot]+=n
        if elapsed%1440<720:early[slot]+=n
        ledger.append(dict(**e,slot=slot[1],old_urgent=o,new_urgent=n))
    cases=[]
    for r in rows:
        if r['minute_source_status']!='COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4' or not r['hourly_gt2x_EVALUATION_ONLY']:continue
        key=r['date'],r['symbol'];p=r['P1v03_original_unbudgeted_candidate'];high=r['original_GT2x_first_real_1m_HIGH_UTC']
        lead=minute(high)-minute(p['at_UTC']) if p else None
        cases.append(dict(date=r['date'],symbol=r['symbol'],D0=watch.get(key),P1=p['at_UTC'] if p else None,first_2x=high,P1_lead_min=lead,old_urgent=old.get(key,False),new_urgent=new.get(key,False),old_early=bool(old.get(key) and lead>=5),new_early=bool(new.get(key) and lead>=5)))
    return dict(baseline=BASELINE,population=len(rows),statuses=dict(collections.Counter(r['minute_source_status'] for r in rows)),watch=len(watch),p1=len(old),old_urgent=sum(old.values()),new_urgent=sum(new.values()),old_early=sum(c['old_early'] for c in cases),new_early=sum(c['new_early'] for c in cases),cases=cases,slots=[dict(date=k[0],slot=k[1],old=used_old[k],new=used_new[k],first_half=early[k]) for k in sorted(set(used_old)|set(used_new))],allocation=ledger)

def official(out,workers):
    import monster_v4_stage65_new3_full900_official_hourly_SHA as s65
    import monster_v4_stage66_new3_original_1m_D0_first5_vs_P1v03 as s66
    import monster_v4_stage38_usdm_original_v4_1m_pilot as s38
    # verify upstream guards before replay; additional dependency gap tested separately
    s65.frozen();s66.frozen()
    hour=read('monster_stage65_new3_full2700_hourly_official_source_SHA.jsonl')
    prior={(r['date'],r['symbol']):r for r in read('monster_stage66_full2700_originalV4_D0_and_P1v03_source_SHA.jsonl')}
    out.mkdir(parents=True,exist_ok=True)
    records=[];proofs=[]
    def job(h):
        key=h['date'],h['symbol']
        fresh=s65.orig44.eval_coin(h['symbol'],h['date'])
        assert fresh==h, 'OFFICIAL_HOURLY_DRIFT '+str(key)
        raw=s66.process(fresh)
        assert raw==prior[key], 'OFFICIAL_MINUTE_OR_REPLAY_DRIFT '+str(key)
        return raw
    # Ordinary and unavailable symbols are not discarded; winners are not used
    # to choose tasks. All 900 archived symbols on all three dates are attempted.
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(job,h):h for h in hour}
        with (out/'monster_stage71_official2700_replay_receipts.jsonl').open('w') as log:
            for f in concurrent.futures.as_completed(jobs):
                h=jobs[f]
                try:
                    r=f.result();records.append(r)
                    p=dict(date=r['date'],symbol=r['symbol'],status=r['minute_source_status'],exact_prior_row_parity=True)
                except Exception as err:
                    p=dict(date=h['date'],symbol=h['symbol'],error=type(err).__name__+':'+str(err),exact_prior_row_parity=False)
                proofs.append(p);log.write(json.dumps(p,sort_keys=True)+'\n');log.flush()
                if len(proofs)%50==0:print('OFFICIAL_PROGRESS',len(proofs),'errors',sum(not p['exact_prior_row_parity'] for p in proofs),flush=True)
    report=dict(baseline=BASELINE,attempted=len(proofs),exact_prior_parity=len(records),errors=[p for p in proofs if not p['exact_prior_row_parity']],official_source='https://data.binance.vision/data/futures/um/',all_source_attempts_retained=True)
    if len(records)==2700:report['fresh_recalculation']=recalculate(sorted(records,key=lambda r:(r['date'],r['symbol'])))
    (out/'monster_stage71_official2700_replay_summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    assert len(records)==2700, 'OFFICIAL_REPLAY_HAS_UNRESOLVED_ERRORS'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--official',action='store_true');ap.add_argument('--five-oracle',action='store_true');ap.add_argument('--workers',type=int,default=8)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    r=recalculate(read('monster_stage66_full2700_originalV4_D0_and_P1v03_source_SHA.jsonl'))
    (a.out/'monster_stage71_independent2700_scheduler_recalculation.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('allocation','slots')},sort_keys=True),flush=True)
    if a.official:official(a.out,a.workers)
    if a.five_oracle:five_oracle(a.out)
if __name__=='__main__':main()
