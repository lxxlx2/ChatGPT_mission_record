"""Deterministic anomaly evidence strength, never investment probability."""
import numpy as np

def priority(active,features,entity_indices,entity_count,persistence):
 paths=np.zeros((entity_count,5),bool)
 for p in range(5):np.logical_or.at(paths[:,p],entity_indices,active[:,p])
 present=active.any(axis=1);quotes=np.zeros(entity_count);np.maximum.at(quotes,entity_indices,np.where(present,features[:,14],0))
 state=np.zeros(entity_count,bool);young=np.isfinite(features[:,13])&(features[:,13]>=0)&(features[:,13]<168)
 np.logical_or.at(state,entity_indices,present&((features[:,12]==1)|young))
 return np.minimum(paths.sum(axis=1)*20,40)+(persistence>=2)*15+(quotes>=100000)*15+state*15,paths

def choices():return [(threshold,hours) for threshold in (60,75,90) for hours in (1,2)]
