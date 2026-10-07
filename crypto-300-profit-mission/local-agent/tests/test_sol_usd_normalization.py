import io,json,urllib.error
from decimal import Decimal

from mission_agent.market.sol_usd import BinanceSolUsdcHistoryClient,USDC,normalize_classification,normalize_trade_event,reference_key
from mission_agent.mission_control.frank import _event_price_usdc,_quote_display


class Response(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,*args):self.close();return False


def test_binance_reference_uses_previous_closed_minute_only_and_has_no_trade_time():
    block_time=180
    body=[[120000,'100','102','99','101','1',179999,'0',1,'0','0','0']]
    seen=[]
    def open_url(request,timeout=8):seen.append(request.full_url);return Response(json.dumps(body).encode())
    result=BinanceSolUsdcHistoryClient(open_url=open_url).reference(block_time)
    assert result['status']=='VERIFIED'
    assert result['sol_usdc']=='101'
    assert result['symbol']=='SOLUSDC'
    assert result['candle_close_ms']<block_time*1000
    assert result['reference_epoch']==120
    assert 'block_time' not in result
    assert 'symbol=SOLUSDC' in seen[0]
    assert 'startTime=120000' in seen[0]
    assert reference_key(block_time).endswith(':120')


def test_empty_exact_candle_is_deterministic_not_found():
    client=BinanceSolUsdcHistoryClient(open_url=lambda *a,**k:Response(b'[]'))
    result=client.reference(180)
    assert result['status']=='UNAVAILABLE'
    assert result['reason']=='BINANCE_KLINE_NOT_FOUND'
    assert result['retryable'] is False


def test_invalid_or_future_candle_fails_closed_and_is_retryable():
    body=[[180000,'100','102','99','101','1',239999,'0',1,'0','0','0']]
    client=BinanceSolUsdcHistoryClient(open_url=lambda *a,**k:Response(json.dumps(body).encode()))
    result=client.reference(180)
    assert result['status']=='UNAVAILABLE'
    assert result['reason']=='BINANCE_HISTORY_RESPONSE_INVALID'
    assert result['retryable'] is True


def test_429_is_retryable():
    def limited(*a,**k):
        raise urllib.error.HTTPError('https://example',429,'rate limited',{},None)
    result=BinanceSolUsdcHistoryClient(open_url=limited).reference(180)
    assert result['reason']=='BINANCE_HTTP_429'
    assert result['retryable'] is True


def _classified(block_time=180):
    return {'classification':'ACTIVE_TRADE','signature':'x','wallet':'w','slot':1,'block_time':block_time,'trade':{'mint':'Token','direction':'BUY','token_amount_raw':'1000000','token_decimals':6,'quote_asset':'SOL','quote_amount_raw':'2500000000','quote_decimals':9,'amount_predicate':'UNDETERMINED','amount_predicate_reason':'NON_USDC_QUOTE'}}


def test_shadow_model_conversion_preserves_original_quote_and_uses_usdc_equivalent():
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','sol_usdc':'100','evidence_sha256':'h'}
    result=normalize_classification(_classified(),ref,for_model=True)
    trade=result['trade']
    assert trade['quote_asset']==USDC
    assert trade['quote_decimals']==6
    assert Decimal(trade['quote_amount_raw'])/Decimal(10**6)==Decimal('250')
    assert trade['quote_normalization']=='SOL_TO_USDC_SHADOW_EQUIVALENT'
    assert trade['original_quote']['quote_asset']=='SOL'
    assert trade['original_quote']['quote_quantity']=='2.5'
    assert trade['quote_usdc_status']=='SOL_EVENT_TIME_USDC_VERIFIED'
    assert trade['quote_usdc_equivalent']=='250.0'
    assert trade['amount_predicate']=='SOL_EVENT_TIME_USDC_VERIFIED'
    assert trade['quote_usdc_reference']['trade_block_time']==180
    assert trade['quote_usdc_reference']['reference'] is ref


def test_quote_display_never_presents_synthetic_usdc_as_frank_payment():
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','sol_usdc':'100','evidence_sha256':'h'}
    trade=normalize_classification(_classified(),ref,for_model=True)['trade']
    display=_quote_display(trade)
    assert display['asset']=='SOL'
    assert display['quantity']=='2.5'
    assert display['normalized'] is True
    assert display['usdc_equivalent']=='250.0'




def test_composite_sol_quote_never_becomes_model_amount_or_follow_price():
    classified=_classified()
    classified['trade']['amount_predicate_reason']='COMPOSITE_QUOTE_LEGS'
    classified['trade']['quote_legs']=[
        {'asset':'SOL','raw_delta':'-2500000000','decimals':9},
        {'asset':USDC,'raw_delta':'1000000','decimals':6},
    ]
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','sol_usdc':'100','evidence_sha256':'h'}
    result=normalize_classification(classified,ref,for_model=True)
    trade=result['trade']
    assert trade['quote_asset']=='SOL'
    assert trade['amount_predicate']=='UNDETERMINED'
    assert trade['quote_usdc_status']=='UNDETERMINED'
    assert 'quote_normalization' not in trade
    assert _event_price_usdc(trade) is None


def test_routed_sol_quote_never_gains_usdc_amount_authority_or_follow_price():
    classified=_classified()
    classified['trade']['amount_predicate']='UNDETERMINED'
    classified['trade']['amount_predicate_reason']='ROUTED_RESIDUAL_ASSETS'
    classified['trade']['route_intermediate_assets']=[{'mint':'Residual'}]
    classified['trade']['route_amount_semantics']='GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST'
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','sol_usdc':'150','evidence_sha256':'h'}
    audit=normalize_classification(classified,ref,for_model=False)['trade']
    model=normalize_classification(classified,ref,for_model=True)['trade']
    for trade in (audit,model):
        assert trade['quote_asset']=='SOL'
        assert trade['amount_predicate']=='UNDETERMINED'
        assert trade['amount_predicate_reason']=='ROUTED_RESIDUAL_ASSETS'
        assert trade['quote_usdc_status']=='UNDETERMINED'
        assert trade.get('quote_usdc_equivalent') is None
        assert 'quote_normalization' not in trade
        event={**trade,'quote_quantity':'200','token_amount_raw':'1000000','token_decimals':6}
        assert _event_price_usdc(event) is None


def test_composite_usdc_event_is_not_labeled_direct_usdc_equivalent():
    event={'quote_asset':USDC,'quote_quantity':'2500','at':180,'amount_predicate':'UNDETERMINED','amount_predicate_reason':'COMPOSITE_QUOTE_LEGS'}
    normalized=normalize_trade_event(event,None)
    assert normalized['quote_usdc_status']=='UNDETERMINED'
    assert normalized.get('quote_usdc_equivalent') is None


def test_unauthorized_synthetic_sol_fields_do_not_create_follow_price_or_display_equivalent():
    event={
        'token_amount_raw':'1000000','token_decimals':6,
        'quote_asset':USDC,'quote_quantity':'30000',
        'quote_normalization':'SOL_TO_USDC_SHADOW_EQUIVALENT',
        'original_quote':{'quote_asset':'SOL','quote_quantity':'200'},
        'quote_usdc_equivalent':'30000','quote_usdc_status':'SOL_EVENT_TIME_USDC_VERIFIED',
        'amount_predicate':'UNDETERMINED','amount_predicate_reason':'ROUTED_RESIDUAL_ASSETS',
    }
    assert _event_price_usdc(event) is None
    display=_quote_display(event)
    assert display['asset']=='SOL'
    assert display['quantity']=='200'
    assert display['normalized'] is False
    assert display['usdc_equivalent'] is None


def test_same_candle_can_be_reused_without_reusing_first_trade_block_time():
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','sol_usdc':'100','reference_epoch':960,'evidence_sha256':'same-candle'}
    one=normalize_classification(_classified(1000),ref,for_model=False)['trade']
    two=normalize_classification(_classified(1019),ref,for_model=False)['trade']
    assert one['quote_usdc_reference']['reference']['evidence_sha256']=='same-candle'
    assert two['quote_usdc_reference']['reference']['evidence_sha256']=='same-candle'
    assert one['quote_usdc_reference']['trade_block_time']==1000
    assert two['quote_usdc_reference']['trade_block_time']==1019


def test_missing_reference_never_converts_sol_to_usdc():
    result=normalize_classification(_classified(),{'status':'UNAVAILABLE','reason':'x'},for_model=True)
    assert result['trade']['quote_asset']=='SOL'
    assert result['trade']['quote_usdc_status']=='UNDETERMINED'
    assert 'quote_normalization' not in result['trade']


def test_mission_control_uses_verified_sol_event_time_usdc_and_never_current_sol_price():
    event={'token_amount_raw':'1000000','token_decimals':6,'quote_asset':'SOL','quote_quantity':'2.5','at':180}
    ref={'status':'VERIFIED','source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','sol_usdc':'100'}
    normalized=normalize_trade_event(event,ref)
    assert _event_price_usdc(normalized)==Decimal('250')
    assert _event_price_usdc(event) is None
