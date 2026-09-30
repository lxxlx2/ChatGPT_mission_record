"""Same deterministic incremental pure data engine is used by live and replay."""
from decimal import Decimal as D,localcontext,ROUND_HALF_EVEN
from collections import deque
from bisect import insort,bisect_left
from .bar import MINUTE,dec

class Features:
 def __init__(self):self.reset()
 def reset(self):
  self.bars=deque(maxlen=1447);self.closes={};self.squares=deque(maxlen=5)
  self.vols=deque();self.sorted_vol=[];self.highs=deque();self.lows=deque();self.previous_side=0;self.gt_sides=deque(maxlen=3)
 def push(self,bar,btc=None):
  if not bar.is_closed:return None
  t=bar.open_time_utc
  if self.bars and t<=self.bars[-1].open_time_utc:raise ValueError('nonchronological engine input; replay corrected canonical sequence')
  if self.bars and t!=self.bars[-1].open_time_utc+MINUTE:self.reset()
  with localcontext() as ctx:
   ctx.prec=34;ctx.rounding=ROUND_HALF_EVEN
   c=D(bar.close);previous=D(self.bars[-1].close) if self.bars else None
   f={}
   for label,n in [('5m',5),('15m',15),('1h',60),('4h',240),('24h',1440)]:
    prior=self.closes.get(t-n*MINUTE);f['return_'+label]=dec(c/prior-1) if prior else None
   while self.highs and self.highs[0][0]<t-1440*MINUTE:self.highs.popleft()
   while self.lows and self.lows[0][0]<t-1440*MINUTE:self.lows.popleft()
   warmed=len(self.bars)>=1440
   hi=self.highs[0][1] if warmed else None;lo=self.lows[0][1] if warmed else None
   f.update({'high_24h':dec(hi) if hi else None,'low_24h':dec(lo) if lo else None,
             'distance_from_24h_high':dec(c/hi-1) if hi else None,'distance_from_24h_low':dec(c/lo-1) if lo else None})
   local=list(self.bars)[-14:]+[bar]
   if len(local)==15:
    lh=max(D(b.high) for b in local);ll=min(D(b.low) for b in local)
    f['reversal_15m']=dec(max((lh-c)/lh,(c-ll)/ll))
   else:f['reversal_15m']=None
   vol=None
   if previous:
    self.squares.append((c/previous).ln()**2)
    if len(self.squares)==5:vol=sum(self.squares,D(0)).sqrt()
   f['realized_vol_5m']=dec(vol) if vol is not None else None
   f['trailing_24h_vol_median']=dec((self.sorted_vol[719]+self.sorted_vol[720])/2) if len(self.sorted_vol)==1440 else None
   side=1 if hi and c>=hi*D('1.01') else -1 if lo and c<=lo*D('.99') else 0
   f['breakout_two']=bool(side and self.previous_side==side);self.previous_side=side
   gt=1 if hi and c>=hi*D('1.015') else -1 if lo and c<=lo*D('.985') else 0
   self.gt_sides.append(gt);f['gt_breakout_three']=len(self.gt_sides)==3 and gt!=0 and len(set(self.gt_sides))==1
   for n in ('1h','4h'):
    f['relative_return_vs_btc_'+n]=dec(D(f['return_'+n])-D(btc['return_'+n])) if btc and f['return_'+n] is not None and btc.get('return_'+n) is not None else None
   f['reference_btc_returns']={n:btc.get('return_'+n) if btc else None for n in ('1h','4h')}
   f['missing_data']=not (f['return_24h'] is not None and f['trailing_24h_vol_median'] is not None)
   if bar.asset!='BTC' and any(f['relative_return_vs_btc_'+n] is None for n in ('1h','4h')):f['missing_data']=True
   self.bars.append(bar);self.closes[t]=c
   for old in list(self.closes):
    if old<t-1440*MINUTE:del self.closes[old]
   h,l=D(bar.high),D(bar.low)
   while self.highs and self.highs[-1][1]<=h:self.highs.pop()
   while self.lows and self.lows[-1][1]>=l:self.lows.pop()
   self.highs.append((t,h));self.lows.append((t,l))
   if vol is not None:
    self.vols.append(vol);insort(self.sorted_vol,vol)
    if len(self.vols)>1440:self.sorted_vol.pop(bisect_left(self.sorted_vol,self.vols.popleft()))
   return f
