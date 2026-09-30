"""Fixed P0–P4 diagnostic arbitration, independent of frozen V2 source."""
from copy import deepcopy
from collections import Counter
from decimal import Decimal as D
from ..bar import MINUTE,dec
from ..calibration.episodes import GroundTruth,Activations,RuleSignal,decimal34

POLICIES=('P0','P1','P2','P3','P4')
RESET=30*MINUTE

@decimal34
def expanded(point,thresholds):
    f=point.features;available=not f['missing_data']
    def detail(name,value,threshold,direction=None,eligible=True,score=None):
        magnitude=abs(D(value)) if value is not None else None
        if direction is None:direction=1 if value is not None and D(value)>=0 else -1
        norm=magnitude/D(threshold) if magnitude is not None else None
        if score is not None:norm=score
        return {'name':name,'active':bool(available and eligible and norm is not None and norm>=1),
                'direction':'UP' if direction==1 else 'DOWN','magnitude':dec(magnitude) if magnitude is not None else None,
                'threshold':str(threshold),'normalized_exceedance':dec(norm) if norm is not None else None}
    revdir=1 if D(point.drawup)>=D(point.drawdown) else -1
    rev=max(D(point.drawup),D(point.drawdown));side=point.breakout_side
    breakout=f['distance_from_24h_high'] if side==1 else f['distance_from_24h_low']
    median=D(f['trailing_24h_vol_median']) if f['trailing_24h_vol_median'] is not None else None
    vol=D(f['realized_vol_5m']) if f['realized_vol_5m'] is not None else None
    move=D(f['return_5m']) if f['return_5m'] is not None else None
    def volscore(mult,threshold):
        return min(vol/(median*D(mult)),abs(move)/D(threshold)) if median and median>0 and vol is not None and move is not None else None
    gt=[detail('FAST_MOVE',f['return_1h'],'.04'),detail('MEDIUM_MOVE',f['return_4h'],'.07'),
        detail('REVERSAL',rev,'.05',revdir),detail('BREAKOUT',breakout,'.015',side,f['gt_breakout_three']),
        detail('VOL_EXPANSION',f['return_5m'],'.025',eligible=bool(median and median>0),score=volscore('4','.025'))]
    # Zero median makes compound volatility unavailable, never zero-vs-zero active.
    if volscore('4','.025') is None:gt[-1]['active']=False;gt[-1]['normalized_exceedance']=None
    rules=[detail('R'+str(i),f[key],thresholds['R'+str(i)]) for i,key in enumerate(('return_15m','return_1h','return_4h','return_24h'),1)]
    rules += [detail('R5',rev,'.04',revdir),detail('R6',breakout,'.01',side,f['breakout_two']),
              detail('R7',f['return_5m'],thresholds['R7_move'],eligible=bool(median and median>0),score=volscore(thresholds['R7_multiplier'],thresholds['R7_move'])),
              detail('R8',f['relative_return_vs_btc_1h'],'.04',eligible=point.asset!='BTC'),
              detail('R9',f['relative_return_vs_btc_4h'],'.06',eligible=point.asset!='BTC')]
    if volscore(thresholds['R7_multiplier'],thresholds['R7_move']) is None:rules[6]['active']=False;rules[6]['normalized_exceedance']=None
    gt[-1]['vol_multiplier_threshold']='4';rules[6]['vol_multiplier_threshold']=thresholds['R7_multiplier']
    return gt,rules


def pick(policy,signals,previous=None):
    active=[s for s in signals if s['active']]
    if not active:return None,None
    if policy=='P0':return active[0]['direction'],active[0]['name']
    strongest=max(active,key=lambda s:D(s['normalized_exceedance'])) # stable original order breaks ties
    if policy=='P1':
        retained=next((s for s in active if s['direction']==previous),None)
        chosen=retained or active[0]
    elif policy=='P2':chosen=strongest
    elif policy=='P3':
        votes=Counter(s['direction'] for s in active)
        if votes['UP']==votes['DOWN']:
            chosen=next((s for s in active if s['direction']==previous),None) or strongest
        else:
            direction='UP' if votes['UP']>votes['DOWN'] else 'DOWN'
            chosen=next(s for s in active if s['direction']==direction)
    else:raise ValueError('P4_REQUIRES_CONCURRENT_ENVELOPE')
    return chosen['direction'],chosen['name']


def masks(rules):
    up=down=0
    for rule in rules:
        if rule['active']:
            bit=1<<(int(rule['name'][1:])-1)
            if rule['direction']=='UP':up|=bit
            else:down|=bit
    return up,down


def serial_active(value):
    if value is None:return None
    value=deepcopy(value)
    if isinstance(value.get('episode_type_set'),set):value['episode_type_set']=sorted(value['episode_type_set'])
    return value


class DiagnosticGT:
    """P1–P4 offline labels; does not write or replace PRICE_GT_V2."""
    def __init__(self,asset,policy):
        self.asset=asset;self.policy=policy;self.active=None;self.episodes=[];self.subsignal_transitions=0;self.last_dirs=set()

    def finish(self,t,censored=False,input_hash=None):
        if not self.active:return
        ep=self.active;ep['end_time']=t;ep['right_censored']=censored;ep['episode_type_set']=sorted(ep['episode_type_set'])
        ep['source_window'][1]=t
        if input_hash:ep['input_hash']=input_hash
        self.episodes.append(ep);self.active=None

    @decimal34
    def step(self,point,signals):
        active=[s for s in signals if s['active']];directions={s['direction'] for s in active}
        self.subsignal_transitions+=len(directions ^ self.last_dirs);self.last_dirs=directions
        previous=self.active['direction'] if self.active else None
        if self.policy=='P4':direction='ENVELOPE' if active else None;reason='ANY_MATERIAL'
        else:direction,reason=pick(self.policy,signals,previous)
        selected=active if self.policy=='P4' else [s for s in active if s['direction']==direction]
        if selected:
            if self.active and self.active['direction']!=direction:self.finish(point.time,input_hash=point.input_hash)
            if not self.active:
                self.active={'episode_id':f'diagnostic:{self.policy}:{self.asset}:{point.time}:{direction}',
                             'asset':self.asset,'direction':direction,'onset_directions':sorted(directions) if self.policy=='P4' else [direction],
                             'first_material_time':point.time,'start_time':point.time,'end_time':None,'last_material_time':point.time,
                             'episode_type_set':set(),'peak_magnitude':'0','peak_time':point.time,'max_drawup_or_drawdown':'0',
                             'onset_close':point.close,'source_window':[point.input_start,None],'input_hash':point.input_hash,'right_censored':False}
            ep=self.active;ep['last_material_time']=point.time;ep['episode_type_set'].update(s['name'] for s in selected)
            magnitude=max(D(s['magnitude']) for s in selected)
            if magnitude>D(ep['peak_magnitude']):ep['peak_magnitude']=dec(magnitude);ep['peak_time']=point.time
        if self.active:
            ep=self.active;excursion=abs(D(point.close)/D(ep['onset_close'])-1)
            if excursion>D(ep['max_drawup_or_drawdown']):ep['max_drawup_or_drawdown']=dec(excursion)
            ep['input_hash']=point.input_hash
            if point.time-ep['last_material_time']>=RESET:self.finish(point.time,input_hash=point.input_hash)
        return direction,reason


class CandidatePolicy:
    def __init__(self,asset,policy):
        self.asset=asset;self.policy=policy;self.engine=Activations(asset);self.down=Activations(asset) if policy=='P4' else None
        self.events=[];self.envelope_onset=None;self.last_any=None

    def state(self):
        if self.policy!='P4':return self.engine.state()
        return {'envelope_onset':self.envelope_onset,'up':self.engine.state(),'down':self.down.state()}

    def step(self,t,rules):
        up,down=masks(rules);before=self.state();generated=[]
        previous='UP' if before.get('direction')==1 else 'DOWN' if before.get('direction')==-1 else None
        if self.policy=='P4':
            both=up|down
            if self.envelope_onset is not None and (t-self.last_any>RESET or (t-self.last_any>=RESET and not both)):
                self.envelope_onset=None
            if both:
                if self.envelope_onset is None:self.envelope_onset=t
                self.last_any=t
            for engine,signal in [(self.engine,RuleSignal(t,up,0)),(self.down,RuleSignal(t,0,down))]:
                event=engine.step(signal)
                if event:
                    event=deepcopy(event);event['episode_id']=f'diagnostic:P4:{self.asset}:{self.envelope_onset}:ENVELOPE'
                    event['episode_start']=self.envelope_onset;generated.append(event)
            direction='BOTH' if up and down else 'UP' if up else 'DOWN' if down else None;reason='CONCURRENT'
        else:
            direction,reason=pick(self.policy,rules,previous)
            chosen_up=up if direction=='UP' else 0;chosen_down=down if direction=='DOWN' else 0
            # P0 must pass all raw opposing rules unchanged for exact frozen reproduction.
            event=self.engine.step(RuleSignal(t,up,down) if self.policy=='P0' else RuleSignal(t,chosen_up,chosen_down))
            if event:generated.append(deepcopy(event))
        self.events.extend(generated)
        return {'up_mask':up,'down_mask':down,'both_mask':up|down,'lowest_active_rule':next((r['name'] for r in rules if r['active']),None),
                'selected_direction':direction,'selected_reason':reason,'before':before,'after':self.state(),'events':generated}
