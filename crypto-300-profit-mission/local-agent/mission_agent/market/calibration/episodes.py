"""Independent causal GT and candidate lifecycles. No file or output readers."""
from dataclasses import dataclass
from functools import wraps
from decimal import Decimal as D, localcontext, ROUND_HALF_EVEN
from collections import deque
from ..features import Features
from ..bar import dec, MINUTE

def decimal34(function):
    @wraps(function)
    def wrapped(*args,**kwargs):
        with localcontext() as context:
            context.prec=34;context.rounding=ROUND_HALF_EVEN
            return function(*args,**kwargs)
    return wrapped

RESET = 30 * MINUTE
GT_ORDER = ('FAST_MOVE','MEDIUM_MOVE','REVERSAL','BREAKOUT','VOL_EXPANSION')

@dataclass(frozen=True)
class PricePoint:
    asset: str
    time: int
    close: str
    features: dict
    drawup: str
    drawdown: str
    breakout_side: int
    input_hash: str
    input_start: int


class PriceFeatures:
    def __init__(self):
        self.engine = Features()
        self.local = deque(maxlen=15)
        self.last = None

    def push(self, bar, btc=None, input_hash='', input_start=0):
        if not bar.is_closed: return None
        if self.last is not None and bar.open_time_utc != self.last + MINUTE:
            self.local.clear()
        self.last = bar.open_time_utc
        f = self.engine.push(bar, btc)
        self.local.append(bar)
        with localcontext() as ctx:
            ctx.prec=34; ctx.rounding=ROUND_HALF_EVEN
            high=max(D(b.high) for b in self.local); low=min(D(b.low) for b in self.local); close=D(bar.close)
            up=(close-low)/low; down=(high-close)/high
            side=1 if f['distance_from_24h_high'] is not None and D(f['distance_from_24h_high'])>=D('.01') else -1 if f['distance_from_24h_low'] is not None and D(f['distance_from_24h_low'])<=D('-.01') else 0
            return PricePoint(bar.asset,bar.close_time_utc,bar.close,f,dec(up),dec(down),side,input_hash,input_start)


@decimal34
def material(point):
    if type(point) is not PricePoint: raise TypeError('GT_REQUIRES_CANONICAL_PRICE_POINT')
    f=point.features
    if f['missing_data']: return []
    out=[]
    def add(name,value,threshold):
        if value is not None and abs(D(value))>=D(threshold):
            out.append((name,1 if D(value)>=0 else -1,abs(D(value))))
    add('FAST_MOVE',f['return_1h'],'.04');add('MEDIUM_MOVE',f['return_4h'],'.07')
    reversal=max(D(point.drawup),D(point.drawdown))
    if reversal>=D('.05'):
        out.append(('REVERSAL',1 if D(point.drawup)>=D(point.drawdown) else -1,reversal))
    if f['gt_breakout_three']:
        side=point.breakout_side
        magnitude=abs(D(f['distance_from_24h_high'] if side==1 else f['distance_from_24h_low']))
        out.append(('BREAKOUT',side,magnitude))
    median=D(f['trailing_24h_vol_median'])
    if median>0 and D(f['realized_vol_5m'])>=median*4 and abs(D(f['return_5m']))>=D('.025'):
        out.append(('VOL_EXPANSION',1 if D(f['return_5m'])>=0 else -1,abs(D(f['return_5m']))))
    return out


class GroundTruth:
    def __init__(self,asset):
        self.asset=asset; self.active=None; self.episodes=[]; self.conflicts=0; self.last=None

    def finish(self,t,censored=False,input_hash=None):
        if self.active is None:return
        value=self.active;value['end_time']=t;value['right_censored']=censored
        value['episode_type_set']=sorted(value['episode_type_set'])
        value['source_window'][1]=t
        if input_hash:value['input_hash']=input_hash
        self.episodes.append(value);self.active=None

    def step(self,point):
        if type(point) is not PricePoint: raise TypeError('GT_REQUIRES_CANONICAL_PRICE_POINT')
        if point.asset!=self.asset:raise ValueError('wrong asset')
        if self.last is not None and point.time!=self.last+MINUTE:raise ValueError('GT_NONCONTIGUOUS_INPUT')
        self.last=point.time
        families=material(point)
        if len({x[1] for x in families})>1:self.conflicts+=1
        if families:
            direction=families[0][1]; families=[x for x in families if x[1]==direction]
            label='UP' if direction==1 else 'DOWN'
            if self.active and self.active['direction']!=label:self.finish(point.time,input_hash=point.input_hash)
            if self.active is None:
                self.active={'episode_id':f'gt2e:{self.asset}:{point.time}:{label}','asset':self.asset,'direction':label,
                             'start_time':point.time,'first_material_time':point.time,'end_time':None,
                             'last_material_time':point.time,'episode_type_set':set(),'peak_magnitude':'0','peak_time':point.time,
                             'max_drawup_or_drawdown':'0','onset_close':point.close,'source_window':[point.input_start,None],
                             'input_hash':point.input_hash,'right_censored':False}
            self.active['last_material_time']=point.time
            self.active['episode_type_set'].update(x[0] for x in families)
            magnitude=max(x[2] for x in families)
            if magnitude>D(self.active['peak_magnitude']):
                self.active['peak_magnitude']=dec(magnitude);self.active['peak_time']=point.time
        if self.active:
            with localcontext() as ctx:
                ctx.prec=34;ctx.rounding=ROUND_HALF_EVEN
                excursion=abs(D(point.close)/D(self.active['onset_close'])-1)
                if excursion>D(self.active['max_drawup_or_drawdown']):self.active['max_drawup_or_drawdown']=dec(excursion)
            self.active['input_hash']=point.input_hash
            if point.time-self.active['last_material_time']>=RESET:
                self.finish(point.time,input_hash=point.input_hash)


@dataclass(frozen=True)
class RuleSignal:
    time:int
    up:int
    down:int


class Activations:
    def __init__(self,asset):
        self.asset=asset;self.direction=None;self.onset=None;self.last_true=None
        self.rules={};self.events=[];self.episode_count=0;self.conflicts=0

    def step(self,signal):
        if type(signal) is not RuleSignal:raise TypeError('CANDIDATE_REQUIRES_PRICE_RULE_SIGNAL')
        t=signal.time; both=signal.up|signal.down
        first=both & -both
        chosen=signal.up if signal.up & first else signal.down
        for rule in list(self.rules):
            elapsed=t-self.rules[rule]
            if elapsed>RESET or (elapsed>=RESET and not chosen & (1<<rule)):del self.rules[rule]
        if self.onset is not None and (t-self.last_true>RESET or (t-self.last_true>=RESET and not both)):
            self.onset=None;self.direction=None;self.rules={}
        if not both:return None
        first=both & -both
        direction=1 if signal.up & first else -1
        if signal.up and signal.down:self.conflicts+=1
        current=signal.up if direction==1 else signal.down
        new_episode=self.onset is None or direction!=self.direction
        reason='ACTIVATION' if self.onset is None else 'REVERSAL' if direction!=self.direction else 'RULE_ADDED'
        if new_episode:
            self.rules={};self.onset=t;self.direction=direction;self.episode_count+=1
        self.last_true=t
        added=[]
        for index in range(9):
            bit=1<<index
            if current & bit:
                if index not in self.rules:added.append('R'+str(index+1))
                self.rules[index]=t
        if not added:return None
        label='UP' if direction==1 else 'DOWN'
        event={'event_id':f"price:{self.asset}:PRICE_RULE_V2:{t}:{reason}:"+','.join(added)+':'+label,
               'event_type':'RAW_PRICE_CANDIDATE','rule_version':'PRICE_RULE_V2','asset':self.asset,'time':t,'direction':label,
               'activation_reason':reason,'rule_ids':added,'episode_start':self.onset,'episode_id':f'price2e:{self.asset}:{self.onset}:{label}'}
        self.events.append(event);return event

    def state(self):
        return {'direction':self.direction,'onset':self.onset,'last_true':self.last_true,
                'rules':{str(k):v for k,v in sorted(self.rules.items())}}
