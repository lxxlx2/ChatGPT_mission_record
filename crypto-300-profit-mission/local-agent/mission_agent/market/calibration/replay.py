"""Streaming one partition, compact all-grid transitions, independent episode labels."""
import hashlib
from dataclasses import asdict
from .episodes import PriceFeatures,GroundTruth,Activations,RuleSignal
from .signals import projection,selector,signal
from ..bar import MINUTE
from ...hashing import canonical,digest


def prepare(partition):
    btc={};out={}
    for asset in partition.config['assets']:
        feature=PriceFeatures();gt=GroundTruth(asset);source_hash=hashlib.sha256();fh=hashlib.sha256()
        rows=[];signature=None;begin=partition.start-partition.config['warmup_bars']*MINUTE
        v1=[];v1_runs=[];run=0;previous=None
        for bar in partition.bars(asset):
            source_hash.update(canonical(bar.value()))
            point=feature.push(bar,btc.get(bar.open_time_utc) if asset!='BTC' else None,source_hash.hexdigest(),begin)
            if asset=='BTC':btc[bar.open_time_utc]={key:point.features[key] for key in ('return_1h','return_4h')}
            fh.update(canonical({'time':point.time,'features':point.features,'drawup':point.drawup,'drawdown':point.drawdown}))
            gt.step(point)
            up,down,vup,vdown=projection(point,partition.config)
            current=(up,down,vup,vdown)
            if current!=signature:
                if rows:rows[-1]['end']=point.time-MINUTE
                rows.append({'time':point.time,'end':point.time,'up':up,'down':down,'v1up':vup,'v1down':vdown});signature=current
            else:rows[-1]['end']=point.time
            if partition.start<point.time<=partition.end and vup|vdown:
                first=(vup|vdown)&-(vup|vdown);direction='UP' if vup&first else 'DOWN'
                rules=['R'+str(i+1) for i in range(9) if (vup|vdown)&(1<<i)]
                v1.append({'event_id':f'v1:{asset}:{point.time}','time':point.time,'direction':direction,'rule_ids':rules,'episode_id':f'v1minute:{point.time}'})
                run=run+1 if previous==point.time-MINUTE else 1;previous=point.time
            elif run:v1_runs.append(run);run=0
        if run:v1_runs.append(run)
        gt.finish(partition.end,True)
        out[asset]={'transitions':rows,'episodes':gt.episodes,'feature_hash':fh.hexdigest(),'input_hash':source_hash.hexdigest(),
                    'gt_conflicts':gt.conflicts,'v1_events':v1,'v1_clusters':v1_runs,'range':[partition.start,partition.end]}
        print(f'prepared {partition.role} {asset}: {len(rows)} transitions / {len(gt.episodes)} GT episodes',flush=True)
    return out


def activate(asset,rows,parameters,contract,incremental=False):
    engine=Activations(asset);indices=selector(parameters,contract);state_hash=hashlib.sha256()
    for row in rows:
        signal_start=signal(row['time'],row['up'],row['down'],indices)
        if incremental:
            for t in range(row['time'],row['end']+MINUTE,MINUTE):
                engine.step(RuleSignal(t,signal_start.up,signal_start.down))
        else:
            engine.step(signal_start)
            if row['end']!=row['time']:
                both=signal_start.up|signal_start.down;first=both & -both
                current=signal_start.up if signal_start.up & first else signal_start.down
                for index in engine.rules:
                    if current & (1<<index):engine.rules[index]=row['end']
                if current:engine.last_true=row['end']
                engine.step(RuleSignal(row['end'],signal_start.up,signal_start.down))
        # Exact state hash at every all-grid state boundary, same in both paths.
        state_hash.update(canonical({'time':row['end'],'state':engine.state()}))
    return engine.events,state_hash.hexdigest(),engine.episode_count


def score(prepared,parameters,contract,incremental=False):
    from .evaluate import stats,aggregate,gates
    metrics={};hashes={};events={}
    for asset,value in prepared.items():
        output,state,count=activate(asset,value['transitions'],parameters,contract,incremental)
        start,end=value['range'];metrics[asset]=stats(output,value['episodes'],start,end,count);hashes[asset]=state;events[asset]=output
    start,end=next(iter(prepared.values()))['range'];total=aggregate(metrics,start,end)
    return {'thresholds':parameters,'metrics':metrics,'aggregate':total,'failures':gates(metrics,total),'state_hashes':hashes},events
