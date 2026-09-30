"""Bounded official Binance market-data access; no orders or account endpoints."""
import json,time,urllib.request,urllib.error,urllib.parse
from decimal import Decimal

ENDPOINTS={
    'spot_universe':'https://data-api.binance.vision/api/v3/exchangeInfo',
    'spot_ticker':'https://data-api.binance.vision/api/v3/ticker/24hr',
    'spot_klines':'https://data-api.binance.vision/api/v3/klines',
    'futures_universe':'https://fapi.binance.com/fapi/v1/exchangeInfo',
    'futures_klines':'https://fapi.binance.com/fapi/v1/klines',
    'alpha_tokens':'https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list',
    'alpha_universe':'https://www.binance.com/bapi/defi/v1/public/alpha-trade/get-exchange-info',
    'oi':'https://fapi.binance.com/fapi/v1/openInterest',
    'oi_history':'https://fapi.binance.com/futures/data/openInterestHist',
    'funding':'https://fapi.binance.com/fapi/v1/fundingRate',
    'basis_mark':'https://fapi.binance.com/fapi/v1/premiumIndex',
    'taker':'https://fapi.binance.com/futures/data/takerlongshortRatio',
    'top_longshort':'https://fapi.binance.com/futures/data/topLongShortPositionRatio',
    'global_longshort':'https://fapi.binance.com/futures/data/globalLongShortAccountRatio',
}

class BinanceSource:
    def __init__(self,request=urllib.request.urlopen,sleep=time.sleep):
        self.request=request;self.sleep=sleep;self.calls=0;self.retries=0
    def get(self,kind,params=None):
        if kind not in ENDPOINTS:raise ValueError('MONSTER_SOURCE_ALLOWLIST')
        url=ENDPOINTS[kind]+('?' + urllib.parse.urlencode(params) if params else '')
        for attempt in range(3):
            self.calls+=1
            try:
                with self.request(urllib.request.Request(url,headers={'User-Agent':'crypto-monitor-official-data/1','Accept':'application/json'}),timeout=20) as response:
                    value=json.loads(response.read(),parse_float=str)
                if isinstance(value,dict) and value.get('code') not in (None,'000000',0):raise ValueError('BINANCE_APPLICATION_ERROR')
                return value
            except urllib.error.HTTPError as e:
                if e.code not in (429,500,502,503,504) or attempt==2:raise
                delay=float(e.headers.get('Retry-After','1'))
                if delay>30:raise
            except (TimeoutError,urllib.error.URLError):
                if attempt==2:raise
                delay=0
            self.retries+=1;self.sleep(max(delay,2**attempt))


def universe(value,venue):
    body=value.get('data',value)
    if not isinstance(body,dict) or not isinstance(body.get('symbols'),list):raise ValueError('UNIVERSE_RESPONSE_INCOMPLETE')
    result=[];seen=set()
    for s in body['symbols']:
        if not all(k in s for k in ('symbol','status','baseAsset','quoteAsset')):raise ValueError('PARTIAL_SYMBOL_RESPONSE')
        symbol=s['symbol']
        if symbol in seen:raise ValueError('DUPLICATE_UNIVERSE_SYMBOL')
        seen.add(symbol)
        result.append({'symbol':symbol,'venue':venue,'status':s['status'],'base_asset':s['baseAsset'],'quote_asset':s['quoteAsset'],'onboard_date':s.get('onboardDate'),'delivery_date':s.get('deliveryDate'),'contract_type':s.get('contractType'),'new_symbol_history_status':'UNKNOWN_UNTIL_HISTORY_PROBE'})
    return result
