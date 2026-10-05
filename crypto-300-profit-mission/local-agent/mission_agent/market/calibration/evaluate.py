"""Only this module matches independently built GT with price activations."""
from collections import Counter
from fractions import Fraction
from datetime import datetime,timezone
from decimal import Decimal as D
from ..bar import MINUTE

DAY=86400000

def day(t):return datetime.fromtimestamp(t//1000,timezone.utc).date().isoformat()

def nearest(values,percent):
    values=sorted(values)
    return values[max(0,(percent*len(values)+99)//100-1)] if values else None


def stats(events,episodes,start,end,candidate_episodes):
    events=[e for e in events if start<e['time']<=end and start<e.get('episode_start',e['time'])<=end]
    episodes=[e for e in episodes if start<e['first_material_time']<=end]
    used=set();hit=exact=prior=late=0;leads=[];misses=[]
    for ep in episodes:
        onset=ep['first_material_time']
        matched=[e for e in events if e['direction']==ep['direction'] and onset-15*MINUTE<=e['time']<=onset]
        if matched:
            hit+=1;exact+=any(e['time']==onset for e in matched);prior+=any(e['time']<onset for e in matched)
            used.update(e['event_id'] for e in matched);leads.append((onset-min(e['time'] for e in matched))//1000)
        else:
            misses.append(ep['episode_id'])
            late+=any(e['direction']==ep['direction'] and onset<e['time']<=onset+5*MINUTE for e in events)
    counts=Counter(day(e['time']-MINUTE) for e in events)
    first=(start+DAY-1)//DAY;last=end//DAY
    full=[counts.get(day(t*DAY),0) for t in range(first,last)]
    sorted_full=sorted(full);median=(sorted_full[(len(full)-1)//2]+sorted_full[len(full)//2])/2 if full else None
    activation=Counter(r for e in events for r in e['rule_ids']);clusters=Counter(e['episode_id'] for e in events)
    count=len(episodes)
    return {'episode_count':count,'episode_hit':hit,'episode_miss':count-hit,'episode_recall':str(D(hit)/D(count)) if count else None,
            'exact_onset_hit':exact,'pre_onset_hit':prior,'late_5m_diagnostic':late,
            'median_lead_seconds':nearest(leads,50),'p25_lead_seconds':nearest(leads,25),'p75_lead_seconds':nearest(leads,75),
            'candidate_episode_count':len(clusters),'candidate_events':len(events),'candidate_events_day':str(D(len(events))*DAY/D(end-start)),
            'median_day':str(median) if median is not None else None,'p95_day':nearest(full,95),'max_day':max(full,default=0),
            'daily_counts':dict(counts),'complete_days':len(full),'unmatched_candidate_count':len(events)-len(used),
            'unmatched_candidate_rate':str(D(len(events)-len(used))/D(len(events))) if events else None,
            'rule_activation_distribution':dict(activation),'candidate_cluster_distribution':{str(k):v for k,v in Counter(clusters.values()).items()},
            'misses':misses,'sample_status':'ENOUGH_EPISODES' if count>=10 else 'INSUFFICIENT_EPISODES',
            'event_ids_hash':__import__('hashlib').sha256(('\n'.join(e['event_id'] for e in events)).encode()).hexdigest()}


def aggregate(metrics,start,end):
    first=(start+DAY-1)//DAY;last=end//DAY
    combined=[sum(m['daily_counts'].get(day(t*DAY),0) for m in metrics.values()) for t in range(first,last)]
    count=sum(m['episode_count'] for m in metrics.values());hit=sum(m['episode_hit'] for m in metrics.values())
    return {'episode_count':count,'episode_hit':hit,'episode_miss':count-hit,
            'episode_recall':str(D(hit)/D(count)) if count else None,'combined_p95_day':nearest(combined,95),
            'total_candidate_episodes':sum(m['candidate_episode_count'] for m in metrics.values()),
            'total_candidate_events':sum(m['candidate_events'] for m in metrics.values())}


def gates(metrics,total):
    flags=[]
    if not total['episode_count'] or Fraction(total['episode_hit'],total['episode_count'])<Fraction(9,10):flags.append('AGGREGATE_RECALL')
    for asset,m in metrics.items():
        if m['episode_count']>=10 and Fraction(m['episode_hit'],m['episode_count'])<Fraction(9,10):flags.append(asset+'_RECALL')
        if m['median_day'] is None or D(m['median_day'])>5:flags.append(asset+'_MEDIAN_LOAD')
        if m['p95_day'] is None or m['p95_day']>15:flags.append(asset+'_P95_LOAD')
        if m['max_day']>30:flags.append(asset+'_MAX_LOAD')
    if total['combined_p95_day'] is None or total['combined_p95_day']>40:flags.append('COMBINED_P95_LOAD')
    return flags


def rank(row,order):
    qualified=[Fraction(m['episode_hit'],m['episode_count']) for m in row['metrics'].values() if m['episode_count']>=10]
    total=row['aggregate']
    return (min(qualified,default=Fraction(0)),Fraction(total['episode_hit'],total['episode_count']),
            -total['combined_p95_day'],-total['total_candidate_episodes'],*(D(row['thresholds'][k]) for k in order))
