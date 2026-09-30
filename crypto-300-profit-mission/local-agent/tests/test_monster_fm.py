import json,urllib.error
import pytest
from mission_agent.monster.source import BinanceSource,universe
from mission_agent.fm.health import disk_state,snapshot

def test_current_and_new_symbols_not_dropped_for_short_history():
    rows=universe({'symbols':[{'symbol':'NEWUSDT','status':'TRADING','baseAsset':'NEW','quoteAsset':'USDT'},{'symbol':'OLDUSDT','status':'BREAK','baseAsset':'OLD','quoteAsset':'USDT'}]},'spot')
    assert len(rows)==2 and rows[0]['new_symbol_history_status']=='UNKNOWN_UNTIL_HISTORY_PROBE'

@pytest.mark.parametrize('value',[{}, {'symbols':None},{'symbols':[{'symbol':'BAD'}]}])
def test_partial_universe_rejected(value):
    with pytest.raises(ValueError):universe(value,'spot')

def test_duplicate_symbol_rejected():
    s={'symbol':'S','status':'TRADING','baseAsset':'S','quoteAsset':'USDT'}
    with pytest.raises(ValueError,match='DUPLICATE'):universe({'symbols':[s,s]},'spot')

class Response:
    def __init__(self,value):self.value=value
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps(self.value).encode()

def test_429_backoff_and_allowlist():
    calls=[];sleep=[]
    def req(request,timeout):
        calls.append(request.full_url)
        if len(calls)==1:raise urllib.error.HTTPError(request.full_url,429,'limited',{'Retry-After':'2'},None)
        return Response({'symbols':[]})
    s=BinanceSource(req,sleep.append);assert s.get('spot_universe')=={'symbols':[]};assert s.retries==1 and sleep==[2.0]
    with pytest.raises(ValueError,match='ALLOWLIST'):s.get('order')

@pytest.mark.parametrize('failure',[TimeoutError(),urllib.error.URLError('offline')])
def test_timeout_bounded_retry(failure):
    calls=[]
    def req(*a,**k):calls.append(1);raise failure
    with pytest.raises(type(failure)):BinanceSource(req,lambda x:None).get('spot_universe')
    assert len(calls)==3

def test_derivatives_unavailable_not_zero():
    def req(r,timeout):raise urllib.error.HTTPError(r.full_url,404,'missing',{},None)
    with pytest.raises(urllib.error.HTTPError):BinanceSource(req,lambda x:None).get('oi',{'symbol':'OLDUSDT'})

def test_application_error_not_success():
    with pytest.raises(ValueError,match='APPLICATION'):BinanceSource(lambda *a,**k:Response({'code':-1121}),lambda x:None).get('spot_universe')

@pytest.mark.parametrize('used,expected',[(0,'HEALTHY_DISK'),(4_000_000_000,'DEGRADED_DISK'),(4_750_000_000,'UNHEALTHY_DISK')])
def test_disk_thresholds(used,expected):assert disk_state(used)==expected

def test_health_unknown_cursor_not_false_zero():
    h=snapshot();assert h['frank']['cursor_gap'] is None and h['monster']['symbols_failed'] is None
