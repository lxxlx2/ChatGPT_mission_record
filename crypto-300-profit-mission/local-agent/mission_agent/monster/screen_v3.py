"""Frozen causal second-stage confirmations; imports no GT/outcome evaluator."""
import itertools,json
from pathlib import Path
import numpy as np
from .screen_v2 import activations,PATHS

def search():return json.loads((Path(__file__).resolve().parents[2]/'config/monster_d1_v3_search.json').read_text())
def configurations(spec=None):
 s=spec or search();g=s['grid'];return list(itertools.product(*(g[k] for k in ['persistence_hours','quote_mean_min','confirmation_mode','max_return1','conditional_dual'])))

def supplemental(bars):
 """range/close, close location, trades, prior168 quote percentile; no future input."""
 x=np.asarray(bars,float);out=np.full((len(x),4),np.nan,np.float32)
 if not len(x):return out
 out[:,0]=(x[:,2]-x[:,3])/x[:,4];out[:,1]=np.divide(x[:,4]-x[:,3],x[:,2]-x[:,3],out=np.ones(len(x)),where=x[:,2]>x[:,3]);out[:,2]=x[:,7]
 edges=np.r_[0,np.flatnonzero(np.diff(x[:,0])!=3600000)+1,len(x)]
 for lo,hi in zip(edges[:-1],edges[1:]):
  q=x[lo:hi,6]
  if len(q)<=168:continue
  views=np.lib.stride_tricks.sliding_window_view(q,169)
  for i in range(0,len(views),256):
   v=views[i:i+256];rank=((v[:,:-1]<v[:,-1,None]).sum(axis=1)+.5*(v[:,:-1]==v[:,-1,None]).sum(axis=1))/168;out[lo+168+i:lo+168+i+len(v),3]=rank
 return out

def dual_confirmation(f,entity_indices,venues):
 """Only preverified entity mapping and actual same-time candles participate."""
 n=len(f);applies=np.zeros(n,bool);passed=np.zeros(n,bool)
 groups={}
 for i,e in enumerate(entity_indices):groups.setdefault(int(e),[]).append(i)
 for indices in groups.values():
  if len(indices)<2:continue
  for i in indices:
   other=[j for j in indices if venues[j]!=venues[i] and np.isfinite(f[j,15])]
   applies[i]=bool(other)
   passed[i]=bool(other) and f[i,0]>0 and f[i,1]>0 and any(f[j,0]>0 and f[j,1]>0 and f[j,14]>=10000 for j in other)
 return applies,passed

class Confirmations:
 def __init__(self,n,spec=None,configs=None):
  self.spec=spec or search();self.configs=configs or configurations(self.spec);self.streak=np.zeros(n,np.int32);self.anchor=np.full(n,np.nan);self.buffer=[]
 def step(self,f,ranks,aux,entity_indices,venues):
  s=self.spec;paths=activations(f,ranks,s['stage1_v2_parameters']);eligible=np.isfinite(f[:,15]);broad=paths.any(axis=1)&eligible&(f[:,14]>=s['stage0_quote_min'])
  new=broad&(self.streak==0);self.anchor[new]=f[new,15];self.streak=np.where(broad,self.streak+1,0);self.anchor[~broad]=np.nan
  self.buffer.append((f.copy(),aux.copy()));self.buffer=self.buffer[-3:]
  applies,dual=dual_confirmation(f,entity_indices,venues);alt=np.full(len(f),np.nan)
  for v in set(venues):
   ix=np.array([i for i,x in enumerate(venues) if x==v]);good=np.isfinite(f[ix,1])
   if good.sum()>=20:alt[ix]=f[ix,1]-np.median(f[ix[good],1])
  young=np.isfinite(f[:,13])&(f[:,13]>=0)&(f[:,13]<s['young_age_hours']);retained=f[:,15]>=self.anchor*s['close_retention_min'];families={};qualified=[]
  for hours,quote,mode,maxret,conditional in self.configs:
   if hours not in families:
    if len(self.buffer)<hours:
     quality=np.zeros(len(f),bool);rs=quality.copy()
    else:
     fs=np.array([x[0] for x in self.buffer[-hours:]]);xs=np.array([x[1] for x in self.buffer[-hours:]])
     quality_base=(np.mean(xs[:,:,2],axis=0)>=s['quality_trade_mean_min'])&(np.mean(fs[:,:,4],axis=0)>=s['quality_volume_acc_mean_min'])&((aux[:,3]>=s['quality_prior7d_percentile_min'])|young)
     rs=(f[:,8]>s['relative4_min'])&(f[:,9]>s['relative24_min'])&(alt>s['relative_to_broad_alt4_min'])&np.all(fs[:,:,8]>0,axis=0)
     quality=(np.mean(fs[:,:,14],axis=0),quality_base)
    families[hours]=(quality,rs)
   quality,rs=families[hours];limit=np.where(young,quote*s['young_quote_multiplier'],quote)
   quality=((quality[0]>=limit)&quality[1]&(f[:,14]>=limit*.5)) if isinstance(quality,tuple) else quality
   confirm=(quality|rs) if mode=='QUALITY_OR_RS' else quality if mode=='QUALITY' else quality&(rs|dual)
   ok=broad&(self.streak>=hours)&retained&(f[:,0]<=maxret)&(f[:,1]<s['max_return4'])&confirm
   if conditional:ok&=(~applies|dual)
   qualified.append(ok)
  return np.array(qualified),{'paths':paths,'streak':self.streak.copy(),'retained':retained,'families':families,'dual_applicable':applies,'dual_pass':dual,'young':young,'alt_relative4':alt}

def daily_stats(counts):
 x=sorted(int(v) for v in counts)
 if not x:raise ValueError('NO_CALENDAR_DAYS')
 n=len(x);return {'median':(x[(n-1)//2]+x[n//2])/2,'p95':float(x[int(np.ceil(.95*n))-1])}

def winner(reports):
 eligible=[r for r in reports if r['ceiling_pass']]
 def key(r):
  e=r['entity'];years=[v['entity']['5']['recall'] for v in r['years'].values() if v['entity']['5']['events']];lead=e['5']['lead_hours']['2']
  return (-(e['5']['recall'] or 0),-(e['5']['strict_before2'] or 0),-(e['10']['recall'] or 0),-(lead if lead is not None else -1e30),r['median_entities_day'],r['p95_entities_day'],-min(years,default=0),r['config_id'])
 return min(eligible,key=key) if eligible else None

def validation_status(r,spec=None):
 s=(spec or search())['validation'];e=r['entity']
 if e['5']['events']<s['min_5x_events']:return 'INSUFFICIENT_DATA'
 ok=r['ceiling_pass'] and e['5']['recall']>=s['recall5_min']
 if e['10']['events']>=s['min_10x_events']:ok&=e['10']['recall']>=s['recall10_min'] and e['10']['strict_before2']>=s['strict_before2_10_min']
 if e['20']['events']>=s['min_20x_events']:ok&=e['20']['recall']>=s['recall20_min']
 return 'MONSTER_D1_V3_VALIDATION_PASS' if ok else 'MONSTER_D1_V3_FAIL_VALIDATION'
