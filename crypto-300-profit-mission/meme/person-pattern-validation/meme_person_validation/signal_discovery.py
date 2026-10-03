"""Candidate families from TRAIN distributions; thresholds never use control snapshots."""
from statistics import median
FORBIDDEN={'final_buy_count','final_pnl','future_peak_position','full_exit','realized_pnl_usd'}
FAMILIES={
 'probe_to_conviction':['position_growth_ratio','gross_buy_15m'],
 'accumulation_velocity':['buy_velocity','buy_velocity_acceleration'],
 'profitable_pyramid':['position_growth_ratio','price_change_since_first_buy','unrealized_pnl_before_add'],
 'trend_confirmed_accumulation':['buys_15m','price_change_since_first_buy','liquidity_change','volume_expansion_ratio','holder_growth'],
 'dip_accumulation':['position_growth_ratio','price_change_since_first_buy'],
}
def discover(train_snapshots):
    candidates=[]
    for family,features in FAMILIES.items():
        complete=[s for s in train_snapshots if all(s.get(k) is not None for k in features)]
        if not complete: continue
        thresholds={k:median(s[k] for s in complete) for k in features}
        candidates.append({'pattern_id':'train_median_'+family,'family':family,'thresholds':thresholds,'features':features,'status':'RESEARCH_ONLY','training_sample_count':len(complete),'version':1})
    return candidates
def trigger(pattern,features):
    thresholds=pattern.get('thresholds',{pattern.get('feature'):pattern.get('threshold')})
    if any(k in FORBIDDEN for k in thresholds): raise ValueError('LOOKAHEAD_FEATURE')
    if any(features.get(k) is None for k in thresholds): return False
    if pattern.get('family')=='dip_accumulation':
        return features['price_change_since_first_buy']<0 and features['position_growth_ratio']>=thresholds['position_growth_ratio']
    if pattern.get('family') in {'profitable_pyramid','trend_confirmed_accumulation'}:
        if features['price_change_since_first_buy']<=0: return False
        if pattern['family']=='profitable_pyramid' and features['unrealized_pnl_before_add']<=0: return False
    return all(features[k]>=v for k,v in thresholds.items())
def signal(pattern,features,episode):
    return {'signal_id':episode['episode_id']+':'+pattern['pattern_id']+':'+str(features['as_of']),'episode_id':episode['episode_id'],'person_id':episode['person_id'],'mint':episode['mint'],'T_signal':features['as_of'],'trigger_version':pattern,'feature_snapshot':dict(features)}
