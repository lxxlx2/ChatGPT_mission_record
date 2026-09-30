"""Finite, price-only bit projection; search never reopens validation or GT output."""
from decimal import Decimal as D
from itertools import product
from .episodes import PricePoint, RuleSignal, decimal34
from ..rules import hits as v1_hits

DIMENSIONS=('R1','R2','R3','R4','R7_multiplier','R7_move')


def configs(contract):
    return [dict(zip(DIMENSIONS,values)) for values in product(*(contract['grid'][key] for key in DIMENSIONS))]


@decimal34
def projection(point,contract):
    if type(point) is not PricePoint:raise TypeError('CANDIDATE_REQUIRES_CANONICAL_PRICE_POINT')
    f=point.features
    if f['missing_data']:return 0,0,0,0
    up=down=0; index=0
    def put(active,direction):
        nonlocal up,down,index
        if active:
            if direction>=0:up|=1<<index
            else:down|=1<<index
        index+=1
    directions={}
    for rule,key in [('R1','return_15m'),('R2','return_1h'),('R3','return_4h'),('R4','return_24h')]:
        value=D(f[key]);directions[rule]=1 if value>=0 else -1
        for threshold in contract['grid'][rule]:put(abs(value)>=D(threshold),directions[rule])
    r5=1 if D(point.drawup)>=D(point.drawdown) else -1;directions['R5']=r5
    put(D(f['reversal_15m'])>=D('.04'),r5)
    directions['R6']=point.breakout_side;put(f['breakout_two'],point.breakout_side)
    move=D(f['return_5m']);median=D(f['trailing_24h_vol_median']);vol=D(f['realized_vol_5m']);directions['R7']=1 if move>=0 else -1
    for multiplier in contract['grid']['R7_multiplier']:
        for threshold in contract['grid']['R7_move']:
            put(median>0 and vol>=median*D(multiplier) and abs(move)>=D(threshold),directions['R7'])
    for rule,key,threshold in [('R8','relative_return_vs_btc_1h','.04'),('R9','relative_return_vs_btc_4h','.06')]:
        value=D(f[key]) if f[key] is not None else D(0)
        directions[rule]=1 if value>=0 else -1
        put(point.asset!='BTC' and abs(value)>=D(threshold),directions[rule])
    v1_up=v1_down=0
    for rule in v1_hits(f,point.asset):
        bit=1<<(int(rule[1:])-1)
        if directions[rule]>=0:v1_up|=bit
        else:v1_down|=bit
    return up,down,v1_up,v1_down


def selector(parameters,contract):
    indices=[];offset=0
    for rule in ('R1','R2','R3','R4'):
        indices.append(offset+contract['grid'][rule].index(parameters[rule]));offset+=len(contract['grid'][rule])
    indices.extend([12,13])
    indices.append(14+contract['grid']['R7_multiplier'].index(parameters['R7_multiplier'])*2+contract['grid']['R7_move'].index(parameters['R7_move']))
    indices.extend([18,19]);return indices


def signal(time,up,down,indices):
    a=b=0
    for rule,index in enumerate(indices):
        if up & (1<<index):a|=1<<rule
        if down & (1<<index):b|=1<<rule
    return RuleSignal(time,a,b)
