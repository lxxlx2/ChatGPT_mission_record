"""Forensic flags/statistics; never revise the frozen validation denominator."""
from collections import Counter
from decimal import Decimal as D
from math import sqrt
from ..bar import MINUTE
from ..calibration.evaluate import stats,aggregate,nearest


def eligible(episodes,start,end):return [e for e in episodes if start<e['first_material_time']<=end]

def valid_events(events,start,end):return [e for e in events if start<e['time']<=end and start<e.get('episode_start',e['time'])<=end]


def matches(event,episode):
    directions=episode.get('onset_directions',[episode['direction']])
    return event['direction'] in directions and episode['first_material_time']-15*MINUTE<=event['time']<=episode['first_material_time']


def suspicious(episodes):
    edges=[];previous={}
    for index,ep in enumerate(episodes):
        direction=ep['direction']
        if direction=='ENVELOPE':continue
        if direction in previous:
            prior_index,prior=previous[direction];between=episodes[prior_index+1:index]
            gap=ep['first_material_time']-prior['end_time']
            opposites=[e for e in between if e['direction']!=direction]
            if 0<=gap<=10*MINUTE and opposites and all(e['end_time']-e['first_material_time']<=5*MINUTE for e in opposites):
                edges.append({'from':prior['episode_id'],'to':ep['episode_id'],'gap_seconds':gap//1000,
                              'opposite_episodes':[e['episode_id'] for e in opposites],
                              'opposite_durations_seconds':[(e['end_time']-e['first_material_time'])//1000 for e in opposites]})
        previous[direction]=(index,ep)
    return edges


def stability(episodes,start,end):
    episodes=eligible(episodes,start,end);durations=[(e['end_time']-e['first_material_time'])//1000 for e in episodes]
    reentries={5:0,10:0,30:0};previous={};flips=0
    for i,ep in enumerate(episodes):
        direction=ep['direction']
        if direction=='ENVELOPE':continue
        if i and direction!=episodes[i-1]['direction']:flips+=1
        if direction in previous:
            gap=ep['first_material_time']-previous[direction]['end_time']
            for n in reentries:
                if 0<=gap<=n*MINUTE:reentries[n]+=1
        previous[direction]=ep
    ordered=sorted(durations)
    median=(ordered[(len(ordered)-1)//2]+ordered[len(ordered)//2])/2 if ordered else None
    edges=suspicious(episodes)
    envelope=bool(episodes and episodes[0]['direction']=='ENVELOPE')
    return {'episodes':len(episodes),'median_duration_seconds':str(median) if median is not None else None,
            'p95_duration_seconds':nearest(durations,95),'episodes_under_5min':sum(x<300 for x in durations),
            'episodes_under_10min':sum(x<600 for x in durations),'direction_flips':None if envelope else flips,
            'direction_flips_hour':None if envelope else str(D(flips)*3600000/D(end-start)),
            'same_direction_reentry':{str(k):v for k,v in reentries.items()},
            'fragmentation_ratio':None if envelope else str(D(reentries[30])/len(episodes)) if episodes else None,
            'suspicious_fragmentation_count':len(edges),'suspicious_edges':edges}


def policy_score(events,episodes,start,end):
    if episodes and any(e['direction']=='ENVELOPE' for e in episodes):
        # Feed a causal onset direction only; never future directional union.
        # Base statistics are rebuilt with one selected matching onset direction per envelope.
        converted=[]
        for ep in episodes:
            ep=dict(ep);hit=next((e for e in events if matches(e,ep)),None)
            ep['direction']=hit['direction'] if hit else ep['onset_directions'][0]
            converted.append(ep)
        return stats(events,converted,start,end,0)
    return stats(events,episodes,start,end,0)


def family_metrics(episodes,events,conflict_ids,start,end):
    episodes=eligible(episodes,start,end);events=valid_events(events,start,end);result={}
    for family in ('FAST_MOVE','MEDIUM_MOVE','REVERSAL','BREAKOUT','VOL_EXPANSION'):
        group=[e for e in episodes if family in e['episode_type_set']]
        hit=sum(any(matches(v,e) for v in events) for e in group)
        result[family]={'episodes':len(group),'hits':hit,'misses':len(group)-hit,'recall':str(D(hit)/len(group)) if group else None}
    fast=[e for e in episodes if 'FAST_MOVE' in e['episode_type_set']];exact=prior=other=miss=0
    onset_active=0
    for ep in fast:
        onset_active+='FAST_MOVE' in ep.get('onset_families',[])
        matched=[e for e in events if matches(e,ep)]
        exact+=any('R2' in e['rule_ids'] and e['time']==ep['first_material_time'] for e in matched)
        prior+=any('R2' in e['rule_ids'] and e['time']<ep['first_material_time'] for e in matched)
        other+=bool(matched) and not any('R2' in e['rule_ids'] for e in matched)
        miss+=not bool(matched)
    return {'families':result,'single_family_episodes':sum(len(e['episode_type_set'])==1 for e in episodes),
            'multi_family_episodes':sum(len(e['episode_type_set'])>1 for e in episodes),
            'conflict_family_episodes':sum(e['episode_id'] in conflict_ids for e in episodes),
            'r2_fast_overlap':{'fast_episodes':len(fast),'fast_active_at_onset':onset_active,'r2_exact_onset_hits':exact,
                               'r2_pre_onset_hits':prior,'only_other_rule_hits':other,'fast_misses':miss}}


def wilson(hits,total):
    z=1.959963984540054;p=hits/total;denom=1+z*z/total
    center=(p+z*z/(2*total))/denom;half=z*sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return {'hits':hits,'episodes':total,'recall':str(D(hits)/total),'wilson95':[str(center-half),str(center+half)],
            'maximum_misses_at_90pct':total-(9*total+9)//10,
            'one_more_miss':str(D(hits-1)/total),'two_more_misses':str(D(hits-2)/total),
            'one_resolved_miss':str(D(hits+1)/total),'two_resolved_misses':str(D(hits+2)/total),
            'one_miss_percentage_points':str(D(100)/total)}


def classify(evidence):
    flags=[]
    predicates=[('G_IMPLEMENTATION_BUG','implementation_bug'),('B_GT_DIRECTION_CONFLICT_FRAGMENTATION','fragmentation'),
                ('C_CANDIDATE_DIRECTION_CONFLICT','candidate_conflict'),('D_LIFECYCLE_HYSTERESIS_MISMATCH','lifecycle'),
                ('E_HIT_WINDOW_TIMING','late'),('A_TRUE_THRESHOLD_GAP','threshold_gap'),
                ('F_GT_EPISODE_MODEL_ARTIFACT','model_artifact')]
    flags=[name for name,key in predicates if evidence.get(key)]
    if not flags:
        if not evidence.get('other_explanation'):raise ValueError('MISS_UNEXPLAINED')
        flags=['H_OTHER']
    return {'primary':flags[0],'secondary':flags[1:],'evidence':evidence}
