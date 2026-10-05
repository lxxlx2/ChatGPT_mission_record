"""Network-free replay and frozen objective evaluation."""
import hashlib
from collections import Counter,deque
from datetime import datetime,timezone
from decimal import Decimal
from .features import Features
from .candidate import candidate
from .rules import hits,ground_truth,VERSION
from ..hashing import canonical

def execute(data,starts,incremental=False,store=None):
 engines={asset:Features() for asset in data};btc={};features_hash={a:hashlib.sha256() for a in data};ids={a:[] for a in data}
 metrics={a:{'candidates':[],'daily':Counter(),'rules':Counter(),'overlap':Counter(),'ground_truth_count':0,'ground_truth_hit':0,'ground_truth_exact_hit':0,'misses':[],'leads':[],'label_counts':Counter(),'label_hits':Counter(),'unavailable_samples':0,'candidate_runs':[],'noise_samples':[]} for a in data}
 recent={a:deque() for a in data};run={a:0 for a in data};previous={a:None for a in data}
 def step(asset,bar):
  if incremental:
   from dataclasses import replace
   assert engines[asset].push(replace(bar,is_closed=False)) is None
  f=engines[asset].push(bar,btc.get(bar.open_time_utc) if asset!='BTC' else None)
  if asset=='BTC':btc[bar.open_time_utc]=f
  features_hash[asset].update(canonical({'t':bar.open_time_utc,'features':f,'hits':hits(f,asset)}))
  if bar.open_time_utc<starts[asset]:return
  m=metrics[asset];c=candidate(bar,f)
  if store:store.feature(asset,bar.close_time_utc,f)
  if c:
   ids[asset].append(c['event_id']);m['candidates'].append({'time':bar.open_time_utc,'event_id':c['event_id'],'rules':c['rule_ids'],'features':f})
   day=datetime.fromtimestamp(bar.open_time_utc//1000,timezone.utc).date().isoformat();m['daily'][day]+=1
   for rule in c['rule_ids']:m['rules'][rule]+=1
   for a in c['rule_ids']:
    for b in c['rule_ids']:m['overlap'][a+':'+b]+=1
   recent[asset].append(bar.open_time_utc);run[asset]=run[asset]+1 if previous[asset]==bar.open_time_utc-60000 else 1;previous[asset]=bar.open_time_utc
   if store:store.candidate(c)
  elif run[asset]:m['candidate_runs'].append(run[asset]);run[asset]=0
  while recent[asset] and recent[asset][0]<bar.open_time_utc-15*60000:recent[asset].popleft()
  if f['missing_data']:m['unavailable_samples']+=1;return
  labels=ground_truth(f)
  if labels:
   m['ground_truth_count']+=1;m['ground_truth_hit']+=bool(recent[asset]);m['ground_truth_exact_hit']+=bool(c)
   for label in labels:m['label_counts'][label]+=1;m['label_hits'][label]+=bool(recent[asset])
   if recent[asset]:m['leads'].append((bar.open_time_utc-recent[asset][0])//1000)
   elif len(m['misses'])<30:m['misses'].append({'open_time':bar.open_time_utc,'labels':labels,'features':f})
 if incremental:
  timeline=sorted((b.open_time_utc,0 if a=='BTC' else 1,a,b) for a,bars in data.items() for b in bars)
  for _,__,a,b in timeline:step(a,b)
 else:
  for a in sorted(data,key=lambda a:a!='BTC'):
   for b in data[a]:step(a,b)
 result={}
 for a,m in metrics.items():
  if run[a]:m['candidate_runs'].append(run[a])
  start,end=starts[a],data[a][-1].close_time_utc
  # UTC dates wholly contained in evaluation interval, including zero-candidate days.
  first=(start+86400000-1)//86400000;last=end//86400000
  daily=[m['daily'].get(datetime.fromtimestamp(d*86400,timezone.utc).date().isoformat(),0) for d in range(first,last)]
  ordered=sorted(daily);median=(ordered[(len(ordered)-1)//2]+ordered[len(ordered)//2])/2 if ordered else None
  p95=ordered[max(0,(95*len(ordered)+99)//100-1)] if ordered else None
  count=m['ground_truth_count'];recall=m['ground_truth_hit']/count if count else None
  flags=[]
  if count>=10 and recall<.90:flags.append('RECALL_BELOW_FROZEN_GATE')
  if median is not None and median>60:flags.append('MEDIAN_DAY_NOISE')
  if p95 is not None and p95>180:flags.append('P95_DAY_NOISE')
  selected=[];seen=set()
  for c in m['candidates']:
   for r in c['rules']:
    if r not in seen:seen.add(r);selected.append(c)
   if len(selected)>=9:break
  if m['candidates'] and daily:
   max_date=max(m['daily'],key=lambda day:(m['daily'][day],day))
   extreme=next(c for c in m['candidates'] if datetime.fromtimestamp(c['time']//1000,timezone.utc).date().isoformat()==max_date)
   if extreme not in selected:selected.append(extreme)
  result[a]={'candidate_count':len(ids[a]),'candidates_per_day':len(ids[a])/((end-start)/86400000), 'daily_counts':dict(m['daily']), 'complete_day_count':len(daily),'median_day':median,'p95_day':p95,'max_day':max(daily,default=0),'rule_hits':{r:m['rules'][r] for r in ['R'+str(i) for i in range(1,10)]},'overlap':dict(m['overlap']),'ground_truth_count':count,'ground_truth_hit':m['ground_truth_hit'],'ground_truth_miss':count-m['ground_truth_hit'],'recall':recall,'exact_sample_recall':m['ground_truth_exact_hit']/count if count else None,'label_counts':dict(m['label_counts']),'label_hits':dict(m['label_hits']),'first_candidate_lead_seconds_median':sorted(m['leads'])[len(m['leads'])//2] if m['leads'] else None,'misses':m['misses'],'noise_samples':selected,'unavailable_samples':m['unavailable_samples'],'max_consecutive_candidate_run':max(m['candidate_runs'],default=0),'clustering_runs':len(m['candidate_runs']),'feature_hash':features_hash[a].hexdigest(),'candidate_identity_hash':hashlib.sha256(canonical(ids[a])).hexdigest(),'evaluation_flags':flags,'rule_status':'NEEDS_CALIBRATION' if flags else 'NO_FROZEN_GATE_FAILURE_OBSERVED'}
 # Combined gate uses common full UTC days of the four full-history assets.
 # HYPE contributes known available candidates; unavailable history is never inferred.
 full=[a for a in data if a!='HYPE'] or list(data)
 first=max((starts[a]+86400000-1)//86400000 for a in full)
 last=min(data[a][-1].close_time_utc//86400000 for a in full)
 combined=max((sum(metrics[a]['daily'].get(datetime.fromtimestamp(d*86400,timezone.utc).date().isoformat(),0) for a in data) for d in range(first,last)),default=0)
 if combined>960:
  for value in result.values():
   value['evaluation_flags'].append('COMBINED_DAY_CAPACITY');value['rule_status']='NEEDS_CALIBRATION'
 for value in result.values():value['combined_complete_day_max']=combined
 return result
