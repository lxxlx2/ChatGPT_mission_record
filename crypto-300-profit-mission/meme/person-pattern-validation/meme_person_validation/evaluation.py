"""Evaluate frozen candidate signals, with delayed quotes and explicit missing-data gates."""
from .signal_discovery import trigger,signal
from .replay import replay
from .negative_controls import evaluate_family
from statistics import mean,median
def run(episodes,features,patterns,quote_provider,policy,fixture_rows):
    by_id={e['episode_id']:e for e in episodes};signals=[];replays=[];results=[]
    for pattern in patterns:
        selected=[]
        for ep in episodes:
            causal=sorted([f for f in features if f['episode_id']==ep['episode_id']],key=lambda f:f['as_of'])
            match=next((f for f in causal if trigger(pattern,f)),None)
            if match is not None: selected.append(signal(pattern,match,ep))
        signals.extend(selected)
        samples=[replay(s,d,quote_provider,policy,by_id[s['episode_id']]) for s in selected for d in policy['canonical_horizons']+policy['high_resolution']+policy['auxiliary']]
        for row in samples:
            row['delay_group']='canonical' if row['delay'] in policy['canonical_horizons'] else 'high_resolution' if row['delay'] in policy['high_resolution'] else 'auxiliary'
            row['pattern_id']=pattern['pattern_id']
        replays.extend(samples)
        canonical=[r for r in samples if r['delay_group']=='canonical']
        outcomes=[r['fixed_horizon_returns']['86400'] for r in canonical if r['fixed_horizon_returns']['86400'] is not None]
        negative=evaluate_family(pattern['features'],fixture_rows)
        results.append({'pattern_id':pattern['pattern_id'],'signal_count':len(selected),'sample_count':len(canonical),'followable_rate':sum(r['followable'] for r in canonical)/len(canonical) if canonical else None,'replay_complete':bool(canonical) and all(r['status']=='COMPLETE' for r in canonical),'mean_return':mean(outcomes) if outcomes else None,'median_return':median(outcomes) if outcomes else None,'false_positive_rate':None,'base_rate_status':'UNAVAILABLE_UNIVERSE_NOT_PROVIDED','negative_controls':negative,'status':'REJECTED_BASELINE' if negative['status']=='FAIL' else 'UNVALIDATED'})
    return signals,replays,results
