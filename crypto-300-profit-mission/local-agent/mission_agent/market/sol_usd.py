"""Deterministic SOL->USDC event-time normalization for Frank trades.

Default source is Binance official public Spot market-data. No API key is
required. To avoid replay look-ahead, the reference price is the close of the
previous fully closed 1-minute SOLUSDC candle, never the current candle.

The network client is intentionally separate from the evaluator. Callers must
persist returned reference evidence before using it in a model replay.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

USDC='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
WSOL='So11111111111111111111111111111111111111112'
SOL_QUOTE_ASSETS=frozenset({'SOL',WSOL})
SOURCE='BINANCE_OFFICIAL_SPOT_SOLUSDC'
SELECTION_RULE='PREVIOUS_CLOSED_1M_CLOSE'
DEFAULT_ENDPOINT='https://data-api.binance.vision/api/v3/klines'


def _canonical(value)->bytes:
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def reference_key(block_time:int)->str:
    minute=(int(block_time)//60-1)*60
    return f'{SOURCE}:1m:{minute}'


class BinanceSolUsdcHistoryClient:
    def __init__(self,*,endpoint:str=DEFAULT_ENDPOINT,open_url=urllib.request.urlopen):
        self.endpoint=endpoint;self.open_url=open_url

    def reference(self,block_time:int)->dict:
        block_time=int(block_time)
        target_open=(block_time//60-1)*60
        start_ms=target_open*1000;end_ms=start_ms+59999
        params=urllib.parse.urlencode({'symbol':'SOLUSDC','interval':'1m','startTime':str(start_ms),'endTime':str(end_ms),'limit':'1'})
        request=urllib.request.Request(self.endpoint+'?'+params,headers={'User-Agent':'mission-meme-v1/sol-usdc-review'})
        try:
            with self.open_url(request,timeout=8) as response:body=json.load(response)
        except urllib.error.HTTPError as exc:
            return {'status':'UNAVAILABLE','reason':'BINANCE_HTTP_'+str(exc.code),'source':SOURCE,'selection_rule':SELECTION_RULE,'block_time':block_time,'observed_at':time.time()}
        except (urllib.error.URLError,TimeoutError,OSError,ValueError,TypeError):
            return {'status':'UNAVAILABLE','reason':'BINANCE_HISTORY_UNAVAILABLE','source':SOURCE,'selection_rule':SELECTION_RULE,'block_time':block_time,'observed_at':time.time()}
        try:
            if not isinstance(body,list) or len(body)!=1 or not isinstance(body[0],list) or len(body[0])<7:raise ValueError('BAD_KLINE')
            row=body[0];open_ms=int(row[0]);close_ms=int(row[6]);price=Decimal(str(row[4]))
            if open_ms!=start_ms or close_ms>block_time*1000 or price<=0:raise ValueError('INVALID_REFERENCE')
            evidence={'status':'VERIFIED','source':SOURCE,'symbol':'SOLUSDC','interval':'1m','selection_rule':SELECTION_RULE,'block_time':block_time,'candle_open_ms':open_ms,'candle_close_ms':close_ms,'open':str(row[1]),'high':str(row[2]),'low':str(row[3]),'close':str(row[4]),'sol_usdc':str(price),'observed_at':time.time()}
            evidence['evidence_sha256']=hashlib.sha256(_canonical({k:v for k,v in evidence.items() if k not in {'observed_at','evidence_sha256'}})).hexdigest()
            return evidence
        except (ValueError,TypeError,InvalidOperation,IndexError):
            return {'status':'UNAVAILABLE','reason':'BINANCE_HISTORY_RESPONSE_INVALID','source':SOURCE,'selection_rule':SELECTION_RULE,'block_time':block_time,'observed_at':time.time()}


def normalize_trade_event(event:dict,reference:dict|None)->dict:
    """Return a copy with deterministic USDC-equivalent evidence when possible."""
    value=dict(event);asset=value.get('quote_asset')
    try:quote=Decimal(str(value.get('quote_quantity')))
    except (InvalidOperation,ValueError,TypeError):quote=None
    if asset==USDC and quote is not None:
        value['quote_usdc_equivalent']=str(quote);value['quote_usdc_status']='USDC_DIRECT';value['quote_usdc_reference']={'source':'USDC_DIRECT','block_time':value.get('at')}
        return value
    if asset not in SOL_QUOTE_ASSETS:
        value['quote_usdc_status']='UNDETERMINED';return value
    if quote is None or not reference or reference.get('status')!='VERIFIED':
        value['quote_usdc_status']='UNDETERMINED';value['quote_usdc_reference']=reference or {'status':'UNAVAILABLE','reason':'SOL_USDC_REFERENCE_MISSING'};return value
    try:usdc=quote*Decimal(str(reference['sol_usdc']))
    except (InvalidOperation,ValueError,TypeError,KeyError):
        value['quote_usdc_status']='UNDETERMINED';value['quote_usdc_reference']=reference;return value
    value['quote_usdc_equivalent']=str(usdc);value['quote_usdc_status']='SOL_EVENT_TIME_USDC_VERIFIED';value['quote_usdc_reference']=reference
    return value


def normalize_classification(classified:dict,reference:dict|None,*,for_model:bool=False)->dict:
    """Normalize one ACTIVE_TRADE without mutating caller input.

    In ordinary audit mode the original SOL quote remains untouched and verified
    USDC-equivalent fields are appended. In shadow-model mode, a verified SOL quote
    is converted to synthetic USDC raw units so the frozen V1 evaluator can be
    replayed unchanged. Original quote fields and reference evidence are preserved.
    """
    value=dict(classified);trade=value.get('trade')
    if not trade or value.get('classification')!='ACTIVE_TRADE':return value
    t=dict(trade);asset=t.get('quote_asset')
    if asset not in SOL_QUOTE_ASSETS:return value
    if t.get('quote_decimals') is None:return value
    try:q=Decimal(str(t['quote_amount_raw']))/(Decimal(10)**int(t['quote_decimals']))
    except (InvalidOperation,ValueError,TypeError,KeyError):return value
    normalized=normalize_trade_event({'quote_asset':asset,'quote_quantity':str(q),'at':value.get('block_time')},reference)
    for key in ('quote_usdc_equivalent','quote_usdc_status','quote_usdc_reference'):
        if key in normalized:t[key]=normalized[key]
    if for_model and normalized.get('quote_usdc_status')=='SOL_EVENT_TIME_USDC_VERIFIED':
        original={'quote_asset':t.get('quote_asset'),'quote_amount_raw':t.get('quote_amount_raw'),'quote_decimals':t.get('quote_decimals'),'quote_quantity':str(q)}
        micro=(Decimal(normalized['quote_usdc_equivalent'])*Decimal(10**6)).quantize(Decimal('1'),rounding=ROUND_HALF_EVEN)
        t.update(original_quote=original,quote_asset=USDC,quote_amount_raw=str(int(micro)),quote_decimals=6,quote_normalization='SOL_TO_USDC_SHADOW_EQUIVALENT')
    value['trade']=t
    return value
