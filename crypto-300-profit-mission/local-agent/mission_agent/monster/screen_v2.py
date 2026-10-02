"""Frozen V2 independent causal paths and entity-safe lifecycle."""
import itertools,re
import numpy as np
PATHS=('MOMENTUM_BREAKOUT','VOLUME_IGNITION','OLD_SHELL_REACTIVATION','NEW_LISTING_IGNITION','RELATIVE_STRENGTH_ACCELERATION')
FIELDS=('r1','r4','r6','r24','volume_acc','trade_acc','range_acc','rel1','rel4','rel24','rel_acc','high7_distance','old_shell','age_hours','quote','close')

def midrank(values,minimum=20):
 values=np.asarray(values,dtype=float);out=np.full(values.shape,np.nan);valid=np.isfinite(values);x=values[valid]
 if len(x)<minimum:return out
 order=np.sort(x);out[valid]=(np.searchsorted(order,x,'left')+np.searchsorted(order,x,'right'))/(2*len(x));return out

def activations(f,ranks,config):
 """Array rows are instruments at the same finalized timestamp. No future columns."""
 q=f[:,14]>=10000;r1=f[:,0];rel4=f[:,8]
 a=q & (np.fmax(ranks[:,0],ranks[:,1])>=config[0]) & ((f[:,2]>0)|(f[:,11]>=0))
 b=q & (f[:,4]>=config[1]) & (f[:,5]>=1.5) & (f[:,6]>=1.2) & (r1>0)
 c=q & (f[:,12]==1) & (f[:,13]>=2160) & (f[:,4]>=config[2]) & (f[:,6]>=1.5) & (rel4>0)
 d=q & (f[:,13]>=0) & (f[:,13]<168) & (r1>0) & (ranks[:,0]>=config[3]) & (f[:,6]>=1.2)
 e=q & (np.fmax.reduce(ranks[:,2:5],axis=1)>=config[4]) & (f[:,10]>0)
 return np.stack([a,b,c,d,e],axis=1)

def configurations():
 return list(itertools.product((.90,.95,.98),(2,3,5),(3,5,8),(.80,.90,.95),(.90,.95,.98)))

def entity_id(venue,symbol,base_asset=None,identity_verified=False,ambiguous=False):
 scaled=bool(re.match(r'^\d+',base_asset or symbol));leveraged=bool(re.search(r'(UP|DOWN|BULL|BEAR)USDT$',symbol))
 if not identity_verified or not base_asset or ambiguous or scaled or leveraged:return f'ENTITY_AMBIGUOUS:{venue}:{symbol}'
 return 'BINANCE_BASE:'+base_asset

class Lifecycle:
 def __init__(self,n):self.active=np.zeros((n,5),bool);self.fail=np.zeros((n,5),np.int8);self.last=None
 def step(self,t,active,eligible):
  recovery=self.last is not None and t-self.last!=3600000
  if recovery:self.active[:]=False;self.fail[:]=0
  # Per-instrument missing bar resets state rather than carrying an old activation across a gap.
  self.active[~eligible]=False;self.fail[~eligible]=0
  added=active & ~self.active;existing=self.active.any(axis=1)
  self.fail=np.where(active,0,np.minimum(self.fail+1,3));self.active |= active;self.active[self.fail>=3]=False;self.last=t
  return [(int(i),'PATH_ADDED' if existing[i] else 'PATH_ACTIVATED',[PATHS[k] for k in np.flatnonzero(added[i])],recovery) for i in np.flatnonzero(added.any(axis=1))]
