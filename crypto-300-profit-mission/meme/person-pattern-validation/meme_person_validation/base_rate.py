"""Matched launch-age/liquidity base-universe outcomes. Never infer controls from winners."""
from statistics import mean
def compare(signal_outcomes,universe,age_bucket,liquidity_bucket):
    controls=[r for r in universe if r.get('age_bucket')==age_bucket and r.get('liquidity_bucket')==liquidity_bucket and r.get('canonical_executable_replay') is True and r.get('return') is not None]
    predictions=[r for r in signal_outcomes if r.get('canonical_executable_replay') is True and r.get('return') is not None]
    if not controls or not predictions: return {'status':'UNAVAILABLE','false_positive_rate':None,'base_win_rate':None,'incremental_mean_return':None,'reason':'MATCHED_EXECUTABLE_BASE_UNIVERSE_MISSING'}
    negatives=[r for r in controls if r['return']<=0];selected={r['sample_id'] for r in predictions}
    return {'status':'EVALUATED','sample_count':len(predictions),'control_count':len(controls),'false_positive_rate':sum(r['sample_id'] in selected for r in negatives)/len(negatives) if negatives else None,'signal_loss_fraction':sum(r['return']<=0 for r in predictions)/len(predictions),'base_win_rate':sum(r['return']>0 for r in controls)/len(controls),'incremental_mean_return':mean(r['return'] for r in predictions)-mean(r['return'] for r in controls)}
def profitability(results,policy):
    """No default performance cutoffs. Policy must be preregistered before evaluation."""
    if not policy or not policy.get('preregistered') or not policy.get('evidence_id'): return {'status':'UNAVAILABLE','reason':'PREREGISTERED_POLICY_REQUIRED'}
    limits=policy.get('minimums',{});ceilings=policy.get('maximums',{})
    if not limits and not ceilings: return {'status':'UNAVAILABLE','reason':'EMPTY_POLICY'}
    if any(results.get(k) is None for k in set(limits)|set(ceilings)): return {'status':'UNAVAILABLE','reason':'REQUIRED_METRIC_MISSING'}
    passed=all(results[k]>=v for k,v in limits.items()) and all(results[k]<=v for k,v in ceilings.items())
    return {'status':'PASS' if passed else 'FAIL','policy_evidence_id':policy['evidence_id']}
