import io,json
from decimal import Decimal

from mission_agent.market.sol_usd import BinanceSolUsdHistoryClient,USDC,normalize_classification,reference_key


class Response(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,*args):self.close();return False


def test_binance_reference_uses_previous_closed_minute_only():
    block_time=180
    # event is at 00:03:00; reference must be fully closed 00:02 candle.
    body=[[120000,'100','102','99','101','1',179999,'0',1,'0','0','0']]
    seen=[]
    def open_url(request,timeout=8):seen.append(request.full_url);return Response(json.dumps(body).encode())
    result=BinanceSolUsdHistoryClient(open_url=open_url).reference(block_time)
    assert result['status']=='VERIFIED'
    assert result['sol_usd']=='101'
    assert result['candle_close_ms']<block_time*1000
    assert 'startTime=120000' in seen[0]
    assert reference_key(block_time).endswith(':120')


def test_invalid_future_or_wrong_candle_fails_closed():
    body=[[180000,'100','102','99','101','1',239999,'0',1,'0','0','0']]
    client=BinanceSolUsdHistoryClient(open_url=lambda *a,**k:Response(json.dumps(body).encode()))
    result=client.reference(180)
    assert result['status']=='UNAVAILABLE'
    assert result['reason']=='BINANCE_HISTORY_RESPONSE_INVALID'


def _classified():
    return {'classification':'ACTIVE_TRADE','signature':'x','wallet':'w','slot':1,'block_time':180,'trade':{'mint':'Token','direction':'BUY','token_amount_raw':'1000000','token_decimals':6,'quote_asset':'SOL','quote_amount_raw':'2500000000','quote_decimals':9}}


def test_shadow_model_conversion_preserves_original_quote_and_uses_usdc_equivalent():
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDT','sol_usd':'100','evidence_sha256':'h'}
    result=normalize_classification(_classified(),ref,for_model=True)
    trade=result['trade']
    assert trade['quote_asset']==USDC
    assert trade['quote_decimals']==6
    assert Decimal(trade['quote_amount_raw'])/Decimal(10**6)==Decimal('250')
    assert trade['quote_normalization']=='SOL_TO_USD_SHADOW_EQUIVALENT'
    assert trade['original_quote']['quote_asset']=='SOL'
    assert trade['original_quote']['quote_quantity']=='2.5'
    assert trade['quote_usd_status']=='SOL_EVENT_TIME_VERIFIED'


def test_missing_reference_never_converts_sol_to_usdc():
    result=normalize_classification(_classified(),{'status':'UNAVAILABLE','reason':'x'},for_model=True)
    assert result['trade']['quote_asset']=='SOL'
    assert result['trade']['quote_usd_status']=='UNDETERMINED'
    assert 'quote_normalization' not in result['trade']
