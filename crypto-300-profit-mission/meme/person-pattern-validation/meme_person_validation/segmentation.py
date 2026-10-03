"""TRAIN-only gap inspection. A gap alone never splits an open position."""
import math
from statistics import median
def infer_dormant_gap(train_events):
    by_mint={}
    for e in sorted(train_events,key=lambda e:e['block_time']): by_mint.setdefault(e['mint'],[]).append(e['block_time'])
    gaps=sorted(b-a for ts in by_mint.values() for a,b in zip(ts,ts[1:]) if b>a)
    if len(gaps)<4: return {'status':'INSUFFICIENT_SAMPLE','threshold_seconds':None,'sample_count':len(gaps)}
    logs=[math.log(g) for g in gaps];diffs=[b-a for a,b in zip(logs,logs[1:])];i=max(range(len(diffs)),key=diffs.__getitem__)
    if diffs[i]<=median(diffs): return {'status':'NO_SEPARATE_REGIME','threshold_seconds':None,'sample_count':len(gaps)}
    return {'status':'TRAIN_DISTRIBUTION_CANDIDATE_NOT_ACCEPTED','threshold_seconds':math.sqrt(gaps[i]*gaps[i+1]),'sample_count':len(gaps),'position_reset_required':True}
