"""Full exposed-price reconstruction, evidence export and fixed counterfactual diagnostics."""
import hashlib
from copy import deepcopy
from collections import Counter
from decimal import Decimal as D
from datetime import datetime,timezone
from ..bar import MINUTE,dec
from ..calibration.contract import Partition,read_winner,immutable_json,MODULE
from ..calibration.episodes import PriceFeatures,GroundTruth
from ..calibration.signals import projection
from ..calibration.evaluate import aggregate
from ...hashing import canonical,digest
from .policies import POLICIES,expanded,masks,pick,DiagnosticGT,CandidatePolicy,serial_active
from .metrics import eligible,valid_events,policy_score,stability,family_metrics,suspicious,matches,classify,wilson


def timestamp(value):return int(datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()*1000)

MISSES=[timestamp('2026-08-22T'+t+':00Z') for t in ('05:14','05:16','05:20','05:24','08:38')]
WINDOWS={f'miss-{i+1}':[t-30*MINUTE,t+30*MINUTE] for i,t in enumerate(MISSES)}
WINDOWS.update({'early-merged':[timestamp('2026-08-22T04:45:00Z'),timestamp('2026-08-22T06:00:00Z')],
                'late-merged':[timestamp('2026-08-22T08:00:00Z'),timestamp('2026-08-22T09:15:00Z')]})


def needed(t):return any(start<=t<=end for start,end in WINDOWS.values())


def reconstruct(root,role,thresholds):
    partition=Partition(root,role);btc={};out={};trace=[]
    for asset in partition.config['assets']:
        feature=PriceFeatures();source=hashlib.sha256();fh=hashlib.sha256();state_hash=hashlib.sha256()
        gt={p:GroundTruth(asset) if p=='P0' else DiagnosticGT(asset,p) for p in POLICIES}
        candidates={p:CandidatePolicy(asset,p) for p in POLICIES}
        counters=Counter();annotation={};conflict_ids=set();signature=None;previous_time=None;previous_conflict=False
        begin=partition.start-partition.config['warmup_bars']*MINUTE
        for bar in partition.bars(asset):
            source.update(canonical(bar.value()))
            point=feature.push(bar,btc.get(bar.open_time_utc) if asset!='BTC' else None,source.hexdigest(),begin)
            if asset=='BTC':btc[bar.open_time_utc]={key:point.features[key] for key in ('return_1h','return_4h')}
            fh.update(canonical({'time':point.time,'features':point.features,'drawup':point.drawup,'drawdown':point.drawdown}))
            raw_gt,rules=expanded(point,thresholds);active=[s for s in raw_gt if s['active']]
            gdirs={s['direction'] for s in active};conflict=len(gdirs)>1
            current_signature=projection(point,partition.config)
            if signature is not None and current_signature!=signature:
                state_hash.update(canonical({'time':previous_time,'state':candidates['P0'].engine.state()}))
            signature=current_signature;previous_time=point.time
            relevant=partition.start<point.time<=partition.end
            trace_this=role=='VALIDATION' and asset=='SOL' and needed(point.time)
            gbefore=serial_active(gt['P0'].active) if trace_this else None
            gbefore_id=gt['P0'].active['episode_id'] if gt['P0'].active else None
            gbefore_direction=gt['P0'].active['direction'] if gt['P0'].active else None
            finished_before=len(gt['P0'].episodes)
            selected_gt,gt_reason=pick('P0',raw_gt,gbefore_direction)
            policy_data={}
            for policy in POLICIES:
                if policy=='P0':gt[policy].step(point)
                else:gt[policy].step(point,raw_gt)
                result=candidates[policy].step(point.time,rules)
                if trace_this:
                    policy_data[policy]={'gt_active':serial_active(gt[policy].active),'candidate':result}
            current=gt['P0'].active;after_id=current['episode_id'] if current else None
            gswitch=bool(gbefore_direction and current and gbefore_direction!=current['direction'])
            gstart=bool(current and after_id!=gbefore_id)
            if gstart:annotation[after_id]={'onset_families':[s['name'] for s in active if s['direction']==selected_gt],
                                         'onset_family_reason':gt_reason,'conflict_at_onset':conflict,'preceding_conflict':previous_conflict}
            if conflict:
                if gbefore_id:conflict_ids.add(gbefore_id)
                if after_id:conflict_ids.add(after_id)
            p0_result=policy_data['P0']['candidate'] if trace_this else None
            # State snapshots are cheap and needed for population direction arbitration effects.
            engine=candidates['P0'].engine
            # Generated events are exactly engine events whose time is this sample.
            generated=[e for e in engine.events[-1:] if e['time']==point.time]
            selected_candidate,_=pick('P0',rules)
            up,down=masks(rules)
            if relevant:
                counters['minutes']+=1;counters['eligible_minutes']+=not point.features['missing_data']
                counters['gt_conflict_minutes']+=conflict;counters['gt_direction_switches']+=gswitch
                counters['gt_switch_at_conflict']+=gswitch and conflict
                counters['gt_switch_after_conflict']+=gswitch and previous_conflict
                counters['gt_starts_at_conflict']+=gstart and conflict
                counters['gt_starts_after_conflict']+=gstart and previous_conflict
                counters['candidate_conflict_minutes']+=bool(up and down)
                if generated:
                    event=generated[0];counters['candidate_'+event['activation_reason']]+=1
                    counters['candidate_direction_switches']+=event['activation_reason']=='REVERSAL'
                    if event['activation_reason']=='REVERSAL':
                        opposite=any(r['active'] and r['direction']!=event['direction'] for r in rules)
                        counters['candidate_switch_lower_rule']+=opposite
                lowest=next((r for r in rules if r['active']),None)
                if lowest and lowest['name'] in ('R1','R2') and any(r['active'] and int(r['name'][1:])>=3 and r['direction']!=lowest['direction'] for r in rules):
                    counters['R1_R2_override_opposite_R3_R9_minutes']+=1
            if trace_this:
                ended=gt['P0'].episodes[finished_before:]
                trace.append({'time':point.time,'time_utc':datetime.fromtimestamp(point.time/1000,timezone.utc).isoformat(),
                              'bar':bar.value(),'features':point.features,'drawup_15m':point.drawup,'drawdown_15m':point.drawdown,
                              'gt_families':raw_gt,'raw_material_directions':sorted(gdirs),'selected_GT_direction':selected_gt,
                              'selected_GT_family_reason':gt_reason,'conflict_yes_no':conflict,
                              'GT_before':gbefore,'GT_after':serial_active(current),'episode_start':gstart,
                              'episode_finish':bool(ended),'finished_episode_ids':[e['episode_id'] for e in ended],
                              'finish_reason':'opposite_material' if gswitch else 'inactive_reset' if ended else None,
                              'candidate_rules':rules,'candidate':p0_result,'policies':policy_data})
            previous_conflict=conflict
        state_hash.update(canonical({'time':previous_time,'state':candidates['P0'].engine.state()}))
        metrics={};episodes={};events={};stable={}
        for policy in POLICIES:
            gt[policy].finish(partition.end,True)
            episodes[policy]=eligible(gt[policy].episodes,partition.start,partition.end)
            events[policy]=valid_events(candidates[policy].events,partition.start,partition.end)
            metrics[policy]=policy_score(candidates[policy].events,gt[policy].episodes,partition.start,partition.end)
            stable[policy]=stability(gt[policy].episodes,partition.start,partition.end)
            if policy=='P4':stable[policy]['directional_subsignal_transitions']=gt[policy].subsignal_transitions
        for ep in episodes['P0']:ep.update(annotation.get(ep['episode_id'],{}))
        denom=counters['eligible_minutes']
        counters=dict(counters);counters['gt_conflict_rate']=str(D(counters.get('gt_conflict_minutes',0))/denom) if denom else None
        counters['candidate_conflict_rate']=str(D(counters.get('candidate_conflict_minutes',0))/denom) if denom else None
        out[asset]={'metrics':metrics,'stability':stable,'episodes':episodes,'events':events,'conflicts':counters,
                    'family_metrics':family_metrics(episodes['P0'],events['P0'],conflict_ids,partition.start,partition.end),
                    'feature_hash':fh.hexdigest(),'state_hash':state_hash.hexdigest(),'input_hash':source.hexdigest()}
        print(f'forensic {role} {asset}: P0 episodes={len(episodes["P0"])} candidate_events={len(events["P0"])}',flush=True)
    total={p:aggregate({a:v['metrics'][p] for a,v in out.items()},partition.start,partition.end) for p in POLICIES}
    return {'role':role,'range':[partition.start,partition.end],'partition_hash':partition.receipt['payload_sha256'],
            'assets':out,'aggregate':total},trace


def path_sanity(rows,start,end):
    rows=[r for r in rows if start<=r['time']<=end]
    prices=[D(r['bar']['close']) for r in rows];base=prices[0]
    return {'start':start,'end':end,'samples':len(rows),'first_close':dec(base),'last_close':dec(prices[-1]),
            'min_close':dec(min(prices)),'max_close':dec(max(prices)),'net_return':dec(prices[-1]/base-1),
            'max_forward_excursion':dec(max(prices)/base-1),'max_reverse_excursion':dec(min(prices)/base-1),
            'range_return':dec(max(prices)/min(prices)-1)}


def miss_causes(validation,trace):
    sol=validation['assets']['SOL'];episodes=sol['episodes']['P0'];events=sol['events']['P0'];rows={r['time']:r for r in trace}
    edges=suspicious(episodes);by_id={ep['episode_id']:ep for ep in episodes};result=[]
    for onset in MISSES:
        ep=next(e for e in episodes if e['first_material_time']==onset);direction=ep['direction'];row=rows[onset]
        window=[r for r in trace if onset-15*MINUTE<=r['time']<=onset]
        raw_same=[{'time':r['time'],'rules':[x['name'] for x in r['candidate_rules'] if x['active'] and x['direction']==direction],
                   'selected_direction':r['candidate']['selected_direction'],'event':r['candidate']['events']} for r in window
                  if any(x['active'] and x['direction']==direction for x in r['candidate_rules'])]
        conflict=[r for r in raw_same if r['selected_direction']!=direction and (r['time']==onset or r['event'])]
        latched=[r for r in raw_same if r['selected_direction']==direction and not r['event']]
        late=next((e for e in events if e['direction']==direction and onset<e['time']<=onset+5*MINUTE),None)
        links=[edge for edge in edges if edge['to']==ep['episode_id']]
        family_substitution=any(by_id[other].get('onset_family_reason')!=ep.get('onset_family_reason') for edge in links for other in edge['opposite_episodes'])
        evidence={'implementation_bug':False,'fragmentation':bool(links) and family_substitution,
                  'candidate_conflict':bool(conflict),'lifecycle':bool(latched),'late':bool(late),
                  'threshold_gap':not bool(raw_same),'model_artifact':False,'raw_same_direction_samples':raw_same,
                  'conflict_samples':conflict,'lifecycle_samples':latched,'suspicious_edges':[e for e in edges if e['to']==ep['episode_id']],
                  'onset_candidate_before':row['candidate']['before'],'onset_candidate_after':row['candidate']['after'],
                  'onset_gt_families':row['gt_families'],'onset_rules':row['candidate_rules']}
        classified=classify(evidence)
        if late:
            later=rows[late['time']]
            classified['late_detection']={'candidate':late,'delay_seconds':(late['time']-onset)//1000,
                                          'onset_rules':row['candidate_rules'],'event_rules':later['candidate_rules'],
                                          'onset_state':row['candidate']['after'],'event_state_before':later['candidate']['before'],
                                          'onset_features':row['features'],'event_features':later['features']}
        mappings={}
        for policy in POLICIES:
            group=sol['episodes'][policy];ev=sol['events'][policy]
            selected=next((e for e in group if e['first_material_time']==onset and (e['direction']==direction or policy=='P4')),None)
            contained=next((e for e in group if e['first_material_time']<=onset<=e['end_time'] and (e['direction']==direction or policy=='P4')),None)
            target=selected or contained
            original_time_hit=any(e['direction']==direction and onset-15*MINUTE<=e['time']<=onset for e in ev)
            mappings[policy]={'mapping':'RETAINED_ONSET' if selected else 'MERGED_NO_NEW_ONSET' if contained else 'DIRECTION_CHANGED_OR_ABSENT',
                              'episode_id':target['episode_id'] if target else None,'mapped_episode_hit':any(matches(e,target) for e in ev) if target else None,
                              'original_timestamp_direction_hit':original_time_hit}
        classified.update({'episode_id':ep['episode_id'],'onset':onset,'direction':direction,'counterfactual_mapping':mappings})
        result.append(classified)
    # Connected forensic groups through suspicious edges, including opposite episodes.
    groups={e['episode_id']:e['episode_id'] for e in episodes}
    def root(key):
        while groups[key]!=key:key=groups[key]
        return key
    for edge in edges:
        keys=[edge['from'],edge['to']]+edge['opposite_episodes'];first=root(keys[0])
        for key in keys[1:]:groups[root(key)]=first
    grouped=Counter(root(e['episode_id']) for e in result)
    return result,{'raw_miss_episodes':len(result),'forensic_grouped_sequences':len(grouped),'group_sizes':dict(grouped)}
