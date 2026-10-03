"""Read-only post-selection outcome audit; never an online feature input."""
import bisect,json,resource
from pathlib import Path
import numpy as np
from scripts.monster_v3_replay import dump,health,load_bars,HOUR

def audit(root,source,stage):
 meta=json.loads((source/'feature-manifest.json').read_text());events=json.loads(((source if stage=='train' else root)/(stage+'-instrument-events.json')).read_text());rows=json.loads((root/(stage+'-audit-candidates.json')).read_text());group={}
 for r in rows:group.setdefault(r['instrument_index'],[]).append(r)
 counts={'complete':0,'censored':0,'non2x_count':0};primary={};fail={};quality={'EXTREME_INTRAHOUR_RANGE':{'events':0,'prehit':0},'LOW_ANCHOR_LIQUIDITY':{'events':0,'prehit':0},'UNFLAGGED':{'events':0,'prehit':0}};first=np.load(root/(stage+'-audit-first-triggers.npz'))['instrument'][0]
 for i,e in enumerate(events):
  if e['max7d']<5:continue
  flags=[k for k in quality if k in e['quality_flags']] or ['UNFLAGGED'];hit=first[i]>=0 and first[i]<=e['crossings']['2']
  for flag in flags:quality[flag]['events']+=1;quality[flag]['prehit']+=int(hit)
 for i,candidates in group.items():
  bars=load_bars(meta[i]);times=[b[0]+HOUR for b in bars]
  for c in candidates:
   j=bisect.bisect_left(times,c['at']);assert j<len(bars) and times[j]==c['at'];window=bars[j+1:j+169];complete=len(window)==168 and all(b[0]==bars[j][0]+(k+1)*HOUR for k,b in enumerate(window));counts['complete' if complete else 'censored']+=1
   if complete:counts['non2x_count']+=int(max(b[2] for b in window)/bars[j][4]<2)
   primary[c['primary_path']]=primary.get(c['primary_path'],0)+1
   for k,v in c['confirmations'].items():fail[k+':'+v]=fail.get(k+':'+v,0)+1
  health()
 counts['non2x_rate']=counts['non2x_count']/counts['complete'] if counts['complete'] else None;result={'stage':stage,'candidate_count':len(rows),'complete168h_forward_high_outcome':counts,'primary_path_candidate_counts':primary,'confirmation_status_counts':fail,'gt_high_tier_quality_flags':quality,'scope':'Instrument activation outcomes, not unique-entity investment false-positive probability. No executable return claim.','peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss};dump(root/(stage+'-outcome-audit.json'),result);print(json.dumps(result))
if __name__=='__main__':
 import sys
 audit(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3])
