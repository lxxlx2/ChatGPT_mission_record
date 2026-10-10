#!/usr/bin/env python3
"""Read-only research full-universe event/signal burden study, NOT production model."""
import argparse,csv,gzip,hashlib,io,json,statistics,time,zipfile
from collections import Counter,defaultdict,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path

H=3600000
EPOCHS={
 'TRAIN_2021_2023':(1609459200000,1704067200000),
 'VALIDATION_2024':(1704067200000,1735689600000),
 'EXPOSED_2025_2026':(1735689600000,1790812800000)}
SPECIAL={'UNIDOWNUSDT','PAXUSDT','ADADOWNUSDT','XLMUPUSDT','UNIUPUSDT','XLMDOWNUSDT'}
POLICIES=('EARLY_WATCH','VOLUME_1H8','BREAKOUT24','MOMENTUM4','NEW_NO_BASE','ANY_STRONG')

def checksum(p):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def moment(ms):
 return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat().replace('+00:00','Z')

def read_events(packet):
 with zipfile.ZipFile(packet) as z:
  if z.testzip() is not None:raise ValueError('PACKET_BAD_CRC')
  rows=[]
  for period,name in [('TRAIN_2021_2023','train-instrument-events.json'),('VALIDATION_2024','validation-instrument-events.json'),('EXPOSED_2025_2026','ground-truth-events-v1.json')]:
   for e in json.loads(z.read('events/'+name)):
    if e['max7d']<2 or e['crossings']['2'] is None:raise ValueError('BAD_GT_EVENT')
    rows.append({'period':period,'event':e,'first':{p:None for p in POLICIES}})
 if len(rows)!=3904:raise ValueError('EXPECTED_ALL_3904_EVENTS')
 by=defaultdict(list)
 for e in rows:by[e['period'],e['event']['venue'],e['event']['symbol']].append(e)
 return rows,by

def iter_sources(home):
 fm3=home/'crypto-monitor-fm3-evidence-20261001/monster'
 fm2=home/'crypto-monitor-fm2-evidence-20260930/monster'
 f1=fm3/'expanded-coverage.json'
 f2=fm2/'universe-current-merged-v1.json'
 if not f1.is_file() or not f2.is_file():raise ValueError('REQUIRED_FM2_FM3_SOURCE_MANIFEST_MISSING')
 old=json.loads(f1.read_text())
 new=json.loads(f2.read_text())
 if not isinstance(old,list) or not isinstance(new,list):raise ValueError('SOURCE_MANIFEST_NOT_LIST')
 for r in old:
  if int(r.get('bars',0))>0:
   yield 'historical_2021_2024',r['venue'],r['symbol'],Path(r['bars_path'])
 for r in new:
  yield 'historical_2025_2026',r['venue'],r['symbol'],fm2/'bars'/r['venue']/(r['symbol']+'.json.gz')

def signal_info(b,past,first):
 old=list(past)
 prev=old[-1] if old else None
 ret1=b[4]/prev[4]-1 if prev and prev[4]>0 else None
 good24=len(old)==24 and all(old[i+1][0]-old[i][0]==H for i in range(23))
 med=statistics.median(x[6] for x in old) if good24 else None
 ratio=b[6]/med if med and med>0 else None
 ret4=b[4]/old[-4][4]-1 if good24 and old[-4][4]>0 else None
 breakout=b[4]/max(x[2] for x in old)-1 if good24 else None
 watch=ret1 is not None and ret1>=.05 and b[6]>=10000 and ratio is not None and ratio>=2
 vol=ret1 is not None and ret1>=.08 and b[6]>=50000 and ratio is not None and ratio>=3
 br=breakout is not None and breakout>=.03 and b[6]>=100000 and ratio is not None and ratio>=2.5
 mom=ret4 is not None and ret4>=.20 and b[6]>=100000 and ratio is not None and ratio>=3
 age=(b[0]-first)//H
 new=ret1 is not None and ret1>=.10 and b[6]>=100000 and 0<=age<24
 return {'EARLY_WATCH':watch,'VOLUME_1H8':vol,'BREAKOUT24':br,'MOMENTUM4':mom,'NEW_NO_BASE':new,'ANY_STRONG':vol or br or mom or new},ratio

def scan_bars(group,venue,symbol,bars,by,stats,alerts,daily):
 if not bars:return
 period='EXPOSED_2025_2026' if group=='historical_2025_2026' else None
 past=deque(maxlen=24);previous=None;first=bars[0][0]
 states={p:False for p in ('EARLY_WATCH','ANY_STRONG')}
 failures={p:0 for p in states}
 last_emit={p:-10**18 for p in states}
 bound={k:(EPOCHS[k][0],EPOCHS[k][1]) for k in EPOCHS}
 window_events={p:by.get((p,venue,symbol),[]) for p in EPOCHS}
 observed=[];source_gaps=0;processed=0
 for i,b in enumerate(bars):
  t=int(b[0]+H)
  if previous is not None and b[0]<=previous[0]:raise ValueError('NON_INCREASING_BAR_CLOCK:'+symbol)
  if previous is not None and b[0]-previous[0]!=H:
   past.clear();source_gaps+=1
   for p in states:states[p]=False;failures[p]=0
  previous=b
  sig,ratio=signal_info(b,past,first)
  past.append(b)
  current=period or ('TRAIN_2021_2023' if t<bound['TRAIN_2021_2023'][1] else 'VALIDATION_2024')
  lo,hi=bound[current]
  if not lo<=t<hi:continue
  processed+=1;day=moment(t)[:10]
  daily[(current,'observed',day)]+=1
  if any(sig.values()):stats['raw_trigger_hours']+=1
  for s,hit in sig.items():
   if hit:
    stats['raw_'+s]+=1
    for ev in window_events[current]:
     e=ev['event']
     if ev['first'][s] is None and e['anchor_time']<=t<e['crossings']['2']:
      ev['first'][s]=t
  for s in states:
   if sig[s]:
    failures[s]=0
    if not states[s] and t-last_emit[s]>=24*H:
     states[s]=True;last_emit[s]=t
     daily[(current,s,day)]+=1
     observed.append((current,s,venue,symbol,t,i,ratio,','.join(p for p in POLICIES if sig[p])))
   else:
    failures[s]+=1
    if failures[s]>=3:states[s]=False
 for current,s,venue,symbol,t,i,ratio,paths in observed:
  entry=bars[i+1][1] if i+1<len(bars) and bars[i+1][0]==bars[i][0]+H else None
  after24=bars[i+24] if i+24<len(bars) and bars[i+24][0]-bars[i][0]==24*H else None
  within24=[x for x in bars[i+1:i+25] if 0<x[0]-bars[i][0]<=24*H]
  full24=len(within24)==24 and all(within24[k][0]==bars[i][0]+(k+1)*H for k in range(24))
  alerts.append({'period':current,'channel':s,'venue':venue,'symbol':symbol,'first_utc':moment(t),'paths':paths,'quote_ratio24':round(ratio,5) if ratio is not None else None,'reference_next_open':round(entry,10) if entry else None,'next24h_close_multiple':round(after24[4]/entry,6) if full24 and after24 and entry else None,'next24h_min_low_multiple':round(min(x[3] for x in within24)/entry,6) if full24 and entry else None,'next24h_max_close_multiple':round(max(x[4] for x in within24)/entry,6) if full24 and entry else None,'window_24h_complete':full24,'special_product':symbol in SPECIAL})
 stats['scanned_hourly_bars']+=processed
 stats['missing_hour_gaps']+=source_gaps
 stats['symbols_scanned']+=1

def summarize(events,alerts,daily,stats,missing,elapsed):
 out={'status':'RESEARCH_ONLY_NO_LIVE_OPERATION','all_historical_event_count':len(events),'historical_sources_missing':missing[:80],'missing_count':len(missing),'time_seconds':round(elapsed,2),'stats':dict(stats),'periods':{},'policy_notes':'Future labels never enter signal creation. All triggers use completed hourly bars only. No orderbook, 1m/5m, fills, fees or executable ROI.'}
 for period,(lo,hi) in EPOCHS.items():
  start=datetime.fromtimestamp(lo/1000,timezone.utc).date()
  stop=datetime.fromtimestamp(hi/1000,timezone.utc).date()
  dates=[(start+timedelta(days=i)).isoformat() for i in range((stop-start).days)]
  d={'alerting_symbols':len({(a['venue'],a['symbol']) for a in alerts if a['period']==period}),'scanned_hourly_bar_counts':sum(daily[period,'observed',x] for x in dates),'ground_truth_events':sum(e['period']==period for e in events),'signals':{}}
  for p in ('EARLY_WATCH','ANY_STRONG'):
   xs=sorted(daily[period,p,x] for x in dates)
   ev=[e for e in events if e['period']==period]
   rows=[a for a in alerts if a['period']==period and a['channel']==p]
   known=[a for a in rows if a['window_24h_complete'] and a['next24h_close_multiple'] is not None]
   d['signals'][p]={'emitted_episodes':len(rows),'days':len(dates),'median_episodes_per_day':statistics.median(xs),'p95_episodes_per_day':xs[min(len(xs)-1,int(.95*len(xs)+.999999)-1)],'5x_gt_event_prehit':sum(e['first'][p] is not None and e['event']['max7d']>=5 for e in ev),'gt_5x_events':sum(e['event']['max7d']>=5 for e in ev),'all_2x_gt_event_prehit':sum(e['first'][p] is not None for e in ev),'gt_2x_events':len(ev),'has_24h_outcome':len(known),'24h_close_positive_20pct':sum(a['next24h_close_multiple']>=1.2 for a in known),'24h_close_median_multiple':round(statistics.median(a['next24h_close_multiple'] for a in known),5) if known else None}
  out['periods'][period]=d
 return out

def csv_text(rows,headers):
 b=io.StringIO();w=csv.DictWriter(b,fieldnames=headers);w.writeheader();w.writerows(rows);return b.getvalue()

def run(home,packet,output,limit_symbols=0):
 start=time.monotonic();events,by=read_events(packet)
 stats=Counter();daily=Counter();alerts=[];missing=[];seen=set()
 for idx,(group,venue,symbol,source) in enumerate(iter_sources(home)):
  if venue not in ('spot','futures') or not symbol.endswith('USDT'):continue
  key=(group,venue,symbol)
  if key in seen:raise ValueError('DUPLICATE_INVENTORY:'+str(key))
  seen.add(key)
  if not source.is_file():
   missing.append(f'{group}/{venue}/{symbol}:MISSING_BARS')
   continue
  try:
   with gzip.open(source,'rt',encoding='utf-8') as stream:bars=json.load(stream)
   if not isinstance(bars,list):raise ValueError('BAD_BAR_JSON')
   scan_bars(group,venue,symbol,bars,by,stats,alerts,daily)
  except (OSError,ValueError,TypeError,KeyError) as exc:
   missing.append(f'{group}/{venue}/{symbol}:{type(exc).__name__}')
  if idx and idx%50==0:print('READ_ONLY_RESEARCH_SCANNED',idx,flush=True)
  if limit_symbols and idx+1>=limit_symbols:break
 if stats['symbols_scanned']==0:raise ValueError('NO_HISTORICAL_SYMBOLS_SCANNED')
 summary=summarize(events,alerts,daily,stats,missing,time.monotonic()-start)
 summary['dataset_file_sha256']=checksum(packet)
 summary['symbols_in_inventory']=len(seen)
 summary['limit_symbols']=limit_symbols
 evrows=[]
 for e in events:
  x=e['event']
  r={'period':e['period'],'venue':x['venue'],'symbol':x['symbol'],'event_id':x['event_id'],'anchor_utc':moment(x['anchor_time']),'gt_maxhigh_7d':round(x['max7d'],6),'gt_first2x_utc':moment(x['crossings']['2']),'is_5x_gt':x['max7d']>=5,'is_special_product':x['symbol'] in SPECIAL}
  for p in POLICIES:r[p+'_first_pre2_utc']=moment(e['first'][p]) if e['first'][p] is not None else ''
  evrows.append(r)
 sample=alerts[0] if alerts else {'period':'','channel':'','venue':'','symbol':'','first_utc':'','paths':'','quote_ratio24':None,'reference_next_open':None,'next24h_close_multiple':None,'next24h_min_low_multiple':None,'next24h_max_close_multiple':None,'window_24h_complete':False,'special_product':False}
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  out.writestr('summary.json',json.dumps(summary,indent=2,ensure_ascii=False))
  out.writestr('all_gt_event_signal_coverage.csv',csv_text(evrows,list(evrows[0])))
  out.writestr('all_market_signal_episodes.csv',csv_text(alerts,list(sample)))
  out.writestr('README.txt','Read-only research: 1h closed-bar alerts and next-open price proxies, no actual executions. GT is offline-only. Exposed historical samples are not independent holdout.\n')
 return summary

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--home',type=Path,default=Path.home()/'Documents/ChatGPT')
 ap.add_argument('--packet',type=Path)
 ap.add_argument('--out',type=Path)
 ap.add_argument('--limit-symbols',type=int,default=0)
 a=ap.parse_args()
 packet=a.packet or a.home/'monster-backtest-packet-20261010.zip'
 output=a.out or a.home/'monster-full-universe-hourly-research-20261010.zip'
 result=run(a.home,packet,output,a.limit_symbols)
 print('RESEARCH_MODE=READ_ONLY_NO_SIGNALS_SENT')
 print('SYMBOLS_SCANNED='+str(result['stats'].get('symbols_scanned',0)))
 print('SCANNED_HOURLY_BARS='+str(result['stats'].get('scanned_hourly_bars',0)))
 print('MISSING_SYMBOLS='+str(result['missing_count']))
 print('RESULT_FILE='+str(output))
 print('RESULT_SHA256='+checksum(output))

if __name__=='__main__':main()
