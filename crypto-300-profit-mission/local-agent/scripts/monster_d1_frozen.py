#!/usr/bin/env python3
"""Objective full-universe discovery and causal frozen 48-grid shadow replay."""
import argparse,bisect,collections,datetime,gzip,hashlib,itertools,json,math,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mission_agent.monster.ground_truth import discover,HOUR,START,END,SPLITS
import numpy as np
from mission_agent.monster.evaluation import noise_audit,attach_prices

ATTEMPT='v1'
def dump(path,value):
 if ATTEMPT!='v1':path=path.with_name(path.stem+'-'+ATTEMPT+path.suffix)
 raw=json.dumps(value,indent=2,allow_nan=False,sort_keys=True).encode()
 if path.exists():
  if path.read_bytes()==raw:return
  raise ValueError('IMMUTABLE_EVIDENCE_CONFLICT:'+str(path))
 with path.open('xb') as f:f.write(raw)
 path.chmod(0o600)
def percentile(a):
 out=np.full(a.shape,np.nan,dtype=np.float32)
 for t in range(a.shape[1]):
  col=a[:,t];valid=np.flatnonzero(np.isfinite(col));n=len(valid)
  if n<20:continue
  ix=valid[np.argsort(col[valid],kind='stable')];vals=col[ix];lo=np.searchsorted(vals,vals,'left');hi=np.searchsorted(vals,vals,'right');out[ix,t]=(lo+hi)/(2*n)
 return out

def metrics(events,cands,split):
 es=[e for e in events if e['split']==split and e['split_future_complete']];by={}
 for v,s,t in cands:by.setdefault((v,s),[]).append(t)
 for x in by.values():x.sort()
 records=[]
 for e in es:
  ts=by.get((e['venue'],e['symbol']),[]);i=bisect.bisect_left(ts,e['anchor_time']-24*HOUR);t=ts[i] if i<len(ts) and ts[i]<=e['peak_time'] else None
  pre=t is not None and t<=e['crossings']['2'];strict=t is not None and t<e['crossings']['2']
  records.append({'event_id':e['event_id'],'max7d':e['max7d'],'tier':e['exact_tier'],'first_candidate_time':t,'prehit':pre,'strict_before2':strict,'lead_hours_to_2':(e['crossings']['2']-t)/HOUR if t else None,'lead_hours_by_threshold':{k:(ct-t)/HOUR if t is not None and ct is not None else None for k,ct in e['crossings'].items()},'lead_hours_to_peak':(e['peak_time']-t)/HOUR if t is not None else None,'venue':e['venue'],'symbol':e['symbol'],'current_active':e['current_active'],'current_inventory_present':e['current_inventory_present'],'new_listing':e['new_listing'],'old_shell':e['old_shell'],'age_status':e['age_status'],'before_thresholds':{k:(t<ct if t is not None and ct is not None else False if ct is not None else None) for k,ct in e['crossings'].items()},'late_hit':t is not None and not pre})
 cohorts={}
 for tier in (2,3,5,10,20):
  rr=[r for r in records if r['tier']>=tier];den=len(rr);cohorts[str(tier)]={'events':den,'prehit_count':sum(x['prehit'] for x in rr),'prehit_recall':sum(x['prehit'] for x in rr)/den if den else None,'strict_before2_fraction':sum(x['strict_before2'] for x in rr)/den if den else None,'before_thresholds':{k:{'crossing_events':sum(x['before_thresholds'][k] is not None for x in rr),'strict_before_count':sum(x['before_thresholds'][k] is True for x in rr),'fraction':sum(x['before_thresholds'][k] is True for x in rr)/sum(x['before_thresholds'][k] is not None for x in rr) if any(x['before_thresholds'][k] is not None for x in rr) else None} for k in ('1.25','1.5','2','3','5','10','20')},'median_lead_hours_to_peak':float(np.median([x['lead_hours_to_peak'] for x in rr if x['lead_hours_to_peak'] is not None])) if any(x['lead_hours_to_peak'] is not None for x in rr) else None,'median_lead_hours_by_threshold':{k:float(np.median([x['lead_hours_by_threshold'][k] for x in rr if x['lead_hours_by_threshold'][k] is not None])) if any(x['lead_hours_by_threshold'][k] is not None for x in rr) else None for k in ('1.25','1.5','2','3','5','10','20')},'median_lead_hours_to_2':float(np.median([x['lead_hours_to_2'] for x in rr if x['lead_hours_to_2'] is not None])) if any(x['lead_hours_to_2'] is not None for x in rr) else None}
 lo,hi=SPLITS[split];days={d:set() for d in range(lo//86400000,(hi-1)//86400000+1)};episodes={d:0 for d in days}
 for v,s,t in cands:
  if lo<=t<hi:days[t//86400000].add(s);episodes[t//86400000]+=1
 counts=sorted(map(len,days.values()));med=float(np.median(counts));p95=counts[math.ceil(.95*len(counts))-1];c5=cohorts['5'];c10=cohorts['10'];sample=c10['events']>=10
 gate=sample and c5['prehit_recall'] is not None and c5['prehit_recall']>=.85 and c10['prehit_recall']>=.90 and c10['strict_before2_fraction']>=.70 and med<=30 and p95<=60
 breakdowns={}
 for field in ('venue','current_active','current_inventory_present','new_listing','old_shell','age_status'):
  breakdowns[field]={}
  for value in {str(r[field]) for r in records}:
   subset=[r for r in records if str(r[field])==value];breakdowns[field][value]={str(t):{'events':sum(r['tier']>=t for r in subset),'prehit_count':sum(r['tier']>=t and r['prehit'] for r in subset)} for t in (2,3,5,10,20)}
 return {'cohorts':cohorts,'cohort_breakdowns':breakdowns,'median_unique_symbols_per_day':med,'p95_unique_symbols_per_day':p95,'max_per_day':max(counts),'median_episodes_per_day':float(np.median(list(episodes.values()))),'daily_counts':[{'utc_day_ms':d*86400000,'unique_symbols':len(days[d]),'episodes':episodes[d]} for d in sorted(days)],'days_including_zero':len(days),'sample_sufficient':sample,'gate_pass':gate,'noise_gate':med<=30 and p95<=60,'records':records,'largest_misses':sorted([r for r in records if not r['prehit']],key=lambda r:(-r['max7d'],r['event_id']))}

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--attempt',default='v1');p.add_argument('--coverage-name',default='stage-a-final-coverage.json');p.add_argument('--completed-day-cutoff-ms',type=int);a=p.parse_args();global ATTEMPT;ATTEMPT=a.attempt
 if not ATTEMPT.replace('-','').replace('_','').isalnum():raise ValueError('ATTEMPT_NAME_INVALID')
 root=Path(a.root)/'monster';freeze=json.loads((Path(a.root)/'monster-gt-freeze.json').read_text());doc=Path(__file__).resolve().parents[1]/'docs/MONSTER_GROUND_TRUTH_V1.md'
 if not freeze['remote_verified'] or freeze['search_configurations']!=48 or hashlib.sha256(doc.read_bytes()).hexdigest()!=freeze['document_sha256']:raise ValueError('GT_FREEZE_IDENTITY_INVALID')
 dump(root/'discovery-start-v1.json',{'freeze_commit':freeze['freeze_commit'],'document_sha256':freeze['document_sha256'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_urls':['https://github.com/binance/binance-public-data','https://data.binance.vision/'],'numpy_version':np.__version__,'python_version':sys.version,'python_executable':sys.executable,'code_sha256':{str(p.relative_to(Path(__file__).resolve().parents[1])):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(list((Path(__file__).resolve().parents[1]/'mission_agent/monster').glob('*.py'))+list((Path(__file__).resolve().parents[1]/'scripts').glob('monster*.py')))}})
 coverage=sorted(json.loads((root/a.coverage_name).read_text())+json.loads((root/'stage-a-contract-supplement-coverage.json').read_text())+json.loads((root/'stage-a-current-supplement-coverage.json').read_text()),key=lambda r:(r['venue'],r['symbol']));current_metadata={v:{s['symbol']:s for s in json.loads((root/f'{v}-current-fm2.json').read_text())['symbols']} for v in ('spot','futures')};events=[];audit=[];data={}
 dump(root/'dataset-manifest-v1.json',{'freeze_commit':freeze['freeze_commit'],'analysis_start_ms':START,'analysis_end_exclusive_ms':END,'coverage_source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (a.coverage_name,'stage-a-contract-supplement-coverage.json','stage-a-current-supplement-coverage.json','spot-current-fm2.json','futures-current-fm2.json')},'instruments':[{'venue':r['venue'],'symbol':r['symbol'],'bars':r['bars'],'archives':r['archive_receipts'],'conflicts':r['conflicting_timestamps']} for r in coverage]})
 for rec in coverage:
  v,s=rec['venue'],rec['symbol'];metadata=current_metadata[v].get(s);rec['current_inventory_present']=metadata is not None;rec['current_active']=bool(metadata and metadata['status']=='TRADING');rec['instrument_metadata']={k:metadata.get(k) for k in ('quoteAsset','contractType','onboardDate','deliveryDate','status')} if metadata else {'quoteAsset':'USDT_FROM_HISTORICAL_DIRECTORY_NAME','status':'HISTORICAL_NOT_CURRENT','ambiguity':rec.get('instrument_alias_ambiguity')};path=root/rec.get('final_bars_directory','bars')/v/f'{s}.json.gz'
  with gzip.open(path,'rt') as f:bars=json.load(f)
  completed_day_cutoff=a.completed_day_cutoff_ms or int(datetime.datetime.now(datetime.timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()*1000)
  bars=[b for b in bars if b[0]+HOUR<=completed_day_cutoff]
  ev,c=discover(bars,v,s,rec['earliest_archive_month'],rec['current_active'])
  for e in ev:e['instrument_alias_ambiguity']=rec.get('instrument_alias_ambiguity');e['current_inventory_present']=rec['current_inventory_present']
  events.extend(ev);audit.append({'venue':v,'symbol':s,**c,'bars':len(bars)});data[(v,s)]=np.asarray(bars,dtype=np.float64).reshape((-1,8))
 dump(root/'universe-current-merged-v1.json',[{k:r[k] for k in ('venue','symbol','current_active','current_inventory_present','instrument_metadata')} for r in coverage]);dump(root/'ground-truth-events-v1.json',events);dump(root/'ground-truth-coverage-v1.json',audit)
 status_counts=collections.Counter()
 missing_reasons=collections.defaultdict(list)
 for rec in coverage:
  for receipt in rec['archive_receipts']:
   st=receipt['status'];err=receipt.get('error','')
   category='VALID' if st=='VALID' else 'MISSING_404' if '404' in err else 'TIMEOUT' if 'timed out' in err.lower() or st=='TimeoutError' else 'CHECKSUM_FAILURE' if 'CHECKSUM' in err else 'INVALID_ZIP' if st=='BadZipFile' else 'PARSE_FAILURE' if st in ('ValueError','IndexError','UnicodeDecodeError') else st
   status_counts[category]+=1
  if not rec['bars']:
   reason='ENDED_BEFORE_ANALYSIS_WINDOW' if rec.get('latest_archive_month') and rec['latest_archive_month']<'2024-10' and not rec['current_active'] else 'UNRESOLVED_ARCHIVE_FAILURE' if any(r['status']!='VALID' for r in rec['archive_receipts']) else 'CURRENT_INSTRUMENT_ARCHIVE_UNAVAILABLE' if rec['current_active'] else 'NO_OFFICIAL_1H_ARCHIVE_IN_TARGET_PERIOD'
   missing_reasons[reason].append({'venue':rec['venue'],'symbol':rec['symbol']})
 dump(root/'archive-status-summary-v1.json',{'receipt_status_counts':dict(status_counts),'zero_bar_symbols_by_reason':dict(missing_reasons),'no_target_period_is_not_failed_download':True})
 print('GT_EVENTS',len(events),flush=True)
 configs=[(r,v,b,x,q) for r,v,b,x,q in itertools.product((.95,.98,.99),(.8,.95),(.8,.95),(1.5,2),(10000,50000))];all_candidates={i:[] for i in range(48)};all_recovery={i:[] for i in range(48)};warm=1727740800000;T=(END-warm)//HOUR;times=np.arange(warm+HOUR,END+HOUR,HOUR,dtype=np.int64)
 for venue in ('spot','futures'):
  symbols=sorted(s for v,s in data if v==venue and len(data[(v,s)]));N=len(symbols);close=np.full((N,T),np.nan);qvol=np.full_like(close,np.nan);ranges=np.full_like(close,np.nan)
  for i,s in enumerate(symbols):
   for t,o,h,l,c,v,q,tr in data[(venue,s)]:
    k=int((t-warm)//HOUR)
    if 0<=k<T:close[i,k]=c;qvol[i,k]=q;ranges[i,k]=(h-l)/c
  deltas={d:np.concatenate([np.full((N,d),np.nan),close[:,d:]/close[:,:-d]-1],axis=1) for d in (1,4,6,24)}
  # Gaps block the entire causal 24h lookback, including missing intermediate bars.
  valid=np.isfinite(close);continuous=np.zeros_like(valid);continuous[:,24:]=np.lib.stride_tricks.sliding_window_view(valid,25,axis=1).all(axis=2)
  btc=symbols.index('BTCUSDT') if 'BTCUSDT' in symbols else None
  if btc is None:raise ValueError('BTC_REFERENCE_ABSENT')
  volacc=np.full_like(close,np.nan);rangeexp=np.full_like(close,np.nan)
  for i in range(N):
   volacc[i,24:]=qvol[i,24:]/np.median(np.lib.stride_tricks.sliding_window_view(qvol[i],24)[:-1],axis=1)
   rangeexp[i,24:]=ranges[i,24:]/np.median(np.lib.stride_tricks.sliding_window_view(ranges[i],24)[:-1],axis=1)
  btc_ok=continuous[btc];mask=continuous & btc_ok[None,:]
  for d in deltas:deltas[d][~mask]=np.nan
  volacc[~mask]=np.nan;rangeexp[~mask]=np.nan;rel=deltas[4]-deltas[4][btc][None,:];r1=percentile(deltas[1]);r4=percentile(deltas[4]);vp=percentile(volacc);bp=percentile(rel)
  observed=np.maximum.accumulate(valid,axis=1);cross_section_coverage=[]
  for k,t in enumerate(times):
   if START<=t<END:
    seen=int(observed[:,k].sum());counts={'return1h':int(np.isfinite(deltas[1][:,k]).sum()),'return4h':int(np.isfinite(deltas[4][:,k]).sum()),'volume_acceleration':int(np.isfinite(volacc[:,k]).sum()),'BTC_relative4h':int(np.isfinite(rel[:,k]).sum())};cross_section_coverage.append({'observation_time':int(t),'causally_observed_universe':seen,'counts':counts,'missing_counts':{f:seen-n for f,n in counts.items()}})
  dump(root/f'd1-cross-section-coverage-{venue}-v1.json',cross_section_coverage)
  eligible=mask & np.isfinite(r1)&np.isfinite(r4)&np.isfinite(vp)&np.isfinite(bp)&np.isfinite(rangeexp)
  for ci,(rt,vt,bt,xt,qt) in enumerate(configs):
   activation=(np.maximum(r1,r4)>=rt)&((vp>=vt)|(bp>=bt))&(rangeexp>=xt)&(qvol>=qt)&eligible
   state=np.zeros(N,dtype=np.int8);failed=np.zeros(N,dtype=np.int8);previous=np.zeros(N,dtype=bool)
   for k,t in enumerate(times):
    good=eligible[:,k];recovery=good&~previous;state[~good]=0;failed[~good]=0
    emit=good&activation[:,k]&(state==0)&~recovery
    if START<=t<END:
     all_candidates[ci].extend((venue,symbols[i],int(t)) for i in np.flatnonzero(emit))
     all_recovery[ci].extend((venue,symbols[i],int(t)) for i in np.flatnonzero(recovery & activation[:,k]))
    state[good&activation[:,k]]=1;failed[good&activation[:,k]]=0;failed[good&~activation[:,k]]+=1;state[failed>=3]=0;failed[failed>=3]=3;previous=good
   print('GRID',venue,ci,'candidates',len(all_candidates[ci]),flush=True)
  del close,qvol,ranges,deltas,volacc,rangeexp,rel,r1,r4,vp,bp
 summaries=[];full={}
 for ci,config in enumerate(configs):
  train=metrics(events,all_candidates[ci],'TRAIN');train['recovery_context_activations']=sum(SPLITS['TRAIN'][0]<=t<SPLITS['TRAIN'][1] for v,s,t in all_recovery[ci]);full[ci]=train;summaries.append({'config_id':f'V1-{ci:02d}','parameters':config,'TRAIN':{k:v for k,v in train.items() if k not in ('records','largest_misses')}})
 passing=[i for i in range(48) if full[i]['gate_pass']];noise=[i for i in range(48) if full[i]['noise_gate']]
 def rec(i,t):return full[i]['cohorts'][t]['prehit_recall'] or 0
 if passing:winner=min(passing,key=lambda i:(full[i]['median_unique_symbols_per_day'],-rec(i,'10'),-rec(i,'5'),i))
 elif noise:winner=min(noise,key=lambda i:(-min(rec(i,'5')/.85,rec(i,'10')/.9),full[i]['median_unique_symbols_per_day'],i))
 else:winner=None
 report={'frozen_grid_size':48,'training_only_selection':True,'winner':f'V1-{winner:02d}' if winner is not None else None,'status':'MONSTER_D1_NEEDS_CALIBRATION','coverage_full_universe':len(coverage),'symbols_with_bars':sum(r['bars']>0 for r in coverage),'symbols_without_bars':sum(r['bars']==0 for r in coverage),'expected_no_target_monthly_period_archives':sum(r['status']=='NO_TARGET_PERIOD_ARCHIVE' for r in coverage),'coverage_venue_summary':{v:{'union_symbols':sum(r['venue']==v for r in coverage),'symbols_with_bars':sum(r['venue']==v and r['bars']>0 for r in coverage),'historical_not_current_symbols':sum(r['venue']==v and not r['current_active'] for r in coverage),'historical_not_current_with_bars':sum(r['venue']==v and not r['current_active'] and r['bars']>0 for r in coverage)} for v in ('spot','futures')},'not_current_inventory_symbols_with_bars':sum(r['bars']>0 and not r['current_inventory_present'] for r in coverage),'historical_not_current_symbols_with_bars':sum(r['bars']>0 and not r['current_active'] for r in coverage),'unavailable_or_failed_archive_receipts':sum(x['status']!='VALID' for r in coverage for x in r['archive_receipts']),'right_censored_anchors':sum(x['right_censored_anchors'] for x in audit),'split_boundary_censored_events':sum(not e['split_future_complete'] for e in events),'exact_tiers':{str(t):sum(e['exact_tier']==t for e in events) for t in (2,3,5,10,20)},'cumulative_tiers':{str(t):sum(e['exact_tier']>=t for e in events) for t in (2,3,5,10,20)},'archive_receipt_status_counts':dict(status_counts),'zero_bar_symbol_reasons':{k:len(v) for k,v in missing_reasons.items()},'ALPHA':'ALPHA_HISTORICAL_UNAVAILABLE','completed_UTC_day_cutoff_ms':completed_day_cutoff,'right_censoring_due_to_current_incomplete_day':True}
 if winner is not None:
  report['parameters']=configs[winner];report['accepted_candidate_activations']=len(all_candidates[winner]);report['recovery_context_activations']=len(all_recovery[winner]);report['primary_recall_and_noise_exclude_recovery_context']=True
  dump(root/'d1-recovery-context-v1.json',[{'venue':v,'symbol':s,'activation_time':t,'recovery_context':True,'primary_credit':False} for v,s,t in all_recovery[winner]]);report['TRAIN']=full[winner];report['VALIDATION']=metrics(events,all_candidates[winner],'VALIDATION');report['AUDIT']=metrics(events,all_candidates[winner],'AUDIT')
  for split in ('TRAIN','VALIDATION','AUDIT'):attach_prices(report[split],data)
  audit_rows,noise_summary,largest_noise=noise_audit(all_candidates[winner],data)
  dump(root/'d1-candidate-future-audit-v1.json',audit_rows);dump(root/'d1-largest-noise-v1.json',largest_noise);report['candidate_non2x_rates']=noise_summary
  report['status']='MONSTER_D1_PASS' if report['VALIDATION']['gate_pass'] and report['unavailable_or_failed_archive_receipts']==0 else 'MONSTER_D1_INSUFFICIENT_DATA' if not report['VALIDATION']['sample_sufficient'] else 'MONSTER_D1_NEEDS_CALIBRATION'
  dump(root/'d1-winner-candidates-v1.json',[{'venue':v,'symbol':s,'activation_time':t,'event_id':f'{v}:{s}:V1-{winner:02d}:{t}'} for v,s,t in all_candidates[winner]])
 validation_extreme=sum(e['split']=='VALIDATION' and e['split_future_complete'] and e['exact_tier']>=10 for e in events)
 report['validation_10x_sample_count']=validation_extreme;report['validation_10x_required_minimum']=10
 report['calibration_required']=winner is None or report.get('VALIDATION',{}).get('gate_pass') is not True
 if validation_extreme<10:report['status']='MONSTER_D1_INSUFFICIENT_DATA'
 if winner is None:
  # Reporting diagnostic only: choose strictly from TRAIN noise, never VALIDATION.
  diagnostic=min(range(48),key=lambda i:(full[i]['p95_unique_symbols_per_day'],full[i]['median_unique_symbols_per_day'],i))
  diagnostic_report={'config_id':f'V1-{diagnostic:02d}','parameters':configs[diagnostic],'selection_rule':'TRAIN_ONLY_MIN_P95_THEN_MEDIAN_THEN_CONFIG_ID','accepted_winner':False,'TRAIN':full[diagnostic],'VALIDATION':metrics(events,all_candidates[diagnostic],'VALIDATION'),'AUDIT':metrics(events,all_candidates[diagnostic],'AUDIT'),'recovery_context_activations':len(all_recovery[diagnostic])}
  for split in ('TRAIN','VALIDATION','AUDIT'):attach_prices(diagnostic_report[split],data)
  audit_rows,noise_summary,largest_noise=noise_audit(all_candidates[diagnostic],data)
  diagnostic_report['candidate_non2x_rates']=noise_summary;report['DIAGNOSTIC']=diagnostic_report
  dump(root/'d1-diagnostic-largest-noise-v1.json',largest_noise)
  dump(root/'d1-diagnostic-candidate-future-audit-v1.json',audit_rows)
  dump(root/'d1-diagnostic-candidates-v1.json',[{'venue':v,'symbol':s,'activation_time':t,'config_id':f'V1-{diagnostic:02d}','accepted_winner':False} for v,s,t in all_candidates[diagnostic]])
  dump(root/'d1-diagnostic-recovery-context-v1.json',[{'venue':v,'symbol':s,'activation_time':t,'recovery_context':True,'primary_credit':False} for v,s,t in all_recovery[diagnostic]])
 dump(root/'d1-grid-train-v1.json',summaries);dump(root/'d1-result-v1.json',report);print('D1_COMPLETE',report['status'],flush=True)
if __name__=='__main__':main()
