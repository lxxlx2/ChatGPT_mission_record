"""One-instrument causal features with bounded rolling buffers; no future labels."""
import numpy as np
from .screen_v2 import FIELDS
HOUR=3600000

def rolling(x,w,kind):
 out=np.full(len(x),np.nan)
 if len(x)<w:return out
 views=np.lib.stride_tricks.sliding_window_view(x,w)
 fn={'median':np.median,'max':np.max,'min':np.min}[kind]
 for i in range(0,len(views),256):out[w-1+i:w-1+min(i+256,len(views))]=fn(views[i:i+256],axis=1)
 return out

def features(bars,btc,verified_first=None):
 b=np.asarray(bars,dtype=float);out=np.full((len(b),len(FIELDS)),np.nan,dtype=np.float32)
 if not len(b):return out
 edges=np.r_[0,np.flatnonzero(np.diff(b[:,0])!=HOUR)+1,len(b)]
 for start,end in zip(edges[:-1],edges[1:]):
  x=b[start:end];n=len(x);f=out[start:end];close=x[:,4];q=x[:,6];tr=x[:,7];rng=(x[:,2]-x[:,3])/close
  for col,lag in enumerate((1,4,6,24)):
   if n>lag:f[lag:,col]=close[lag:]/close[:-lag]-1
  for col,v in [(4,q),(5,tr),(6,rng)]:
   med=rolling(v,24,'median');prior=np.r_[np.nan,med[:-1]];f[:,col]=np.divide(v,prior,out=np.full(n,np.nan),where=prior>0)
  ref=np.array([btc.get(int(t),np.nan) for t in x[:,0]])
  for col,lag,retcol in [(7,1,0),(8,4,1),(9,24,3)]:
   if n>lag:
    contiguous=np.convolve(np.isfinite(ref).astype(np.int8),np.ones(lag+1,np.int8),mode='valid')==lag+1
    f[lag:,col]=np.where(contiguous,f[lag:,retcol]-(ref[lag:]/ref[:-lag]-1),np.nan)
  if n>4:f[4:,10]=f[4:,8]-f[:-4,8]
  high=rolling(x[:,2],168,'max');prior=np.r_[np.nan,high[:-1]];f[:,11]=close/prior-1
  median=rolling(q,720,'median');hi=rolling(close,720,'max');lo=rolling(close,720,'min')
  f[:,12]=np.where(np.isfinite(median),(median<10000)&(hi/lo<2),np.nan)
  if verified_first is not None:f[:,13]=(x[:,0]-verified_first)/HOUR
  else:
   lower_bound=(x[:,0]-b[0,0])/HOUR
   f[:,13]=np.where(lower_bound>=2160,lower_bound,np.nan)
  f[:,14]=q;f[:,15]=close
 return out
