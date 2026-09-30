from decimal import Decimal as D
from dataclasses import replace
import gzip,json,urllib.error
import pytest
from mission_agent.market.bar import Bar,MINUTE
from mission_agent.market.features import Features
from mission_agent.market.rules import hits
from mission_agent.market.store import PriceStore
from mission_agent.market.candidate import candidate
from mission_agent.market.replay import execute
from mission_agent.market.cache import save,load
from mission_agent.db.price_migrations import migrate_price
from mission_agent.market.sources.official import Official,parse_ws,parse_rest
from mission_agent.clock import stamp


def bar(i,price='100',asset='BTC',closed=True):
 return Bar(asset,'hyperliquid_perp' if asset=='HYPE' else 'binance_spot',asset if asset=='HYPE' else asset+'USDT',i*MINUTE,price,price,price,price,'1',is_closed=closed)

@pytest.mark.parametrize('rule,key,threshold',[('R1','return_15m','.03'),('R2','return_1h','.05'),('R3','return_4h','.08'),('R4','return_24h','.12'),('R5','reversal_15m','.04'),('R8','relative_return_vs_btc_1h','.04'),('R9','relative_return_vs_btc_4h','.06')])
@pytest.mark.parametrize('offset,expected',[('-0.00000000000000000001',False),('0',True),('0.00000000000000000001',True)])
@pytest.mark.parametrize('sign',[1,-1])
def test_exact_rule_thresholds(rule,key,threshold,offset,expected,sign):
 if rule=='R5' and sign==-1:return
 value=(D(threshold)+D(offset))*sign
 assert (rule in hits({key:str(value)},'ETH'))==expected

@pytest.mark.parametrize('move,expected',[('.01999999999999999999',False),('.02',True),('.02000000000000000001',True)])
def test_r7_move_boundary(move,expected):
 assert ('R7' in hits({'realized_vol_5m':'.3','trailing_24h_vol_median':'.1','return_5m':move},'BTC'))==expected

@pytest.mark.parametrize('vol,expected',[('.29999999999999999999',False),('.3',True),('.30000000000000000001',True)])
def test_r7_vol_boundary(vol,expected):
 assert ('R7' in hits({'realized_vol_5m':vol,'trailing_24h_vol_median':'.1','return_5m':'.02'},'BTC'))==expected


def test_features_returns_warmup_and_provisional():
 e=Features()
 for i in range(1446):f=e.push(bar(i))
 assert not f['missing_data'] and f['return_24h']=='0'
 assert e.push(bar(1446,'103',closed=False)) is None
 f=e.push(bar(1446,'103'));assert D(f['return_15m'])==D('.03')
 assert D(f['realized_vol_5m'])>0


def test_r6_prior_extrema_excludes_current_and_requires_two():
 e=Features()
 for i in range(1441):e.push(bar(i))
 first=e.push(bar(1441,'101'));assert first['high_24h']=='100' and not first['breakout_two']
 second=e.push(bar(1442,'102.01'));assert second['high_24h']=='101' and second['breakout_two']
 # Future high cannot alter already-computed result.
 assert 'R6' in hits(second,'BTC')
 third=e.push(bar(1443,'200'));assert second['high_24h']=='101'


def test_gap_resets_features_and_old_input_rejected():
 e=Features()
 for i in range(1500):e.push(bar(i))
 assert e.push(bar(1501))['missing_data']
 with pytest.raises(ValueError):e.push(bar(1500))


def test_decimal_and_ohlc_validation():
 with pytest.raises(ValueError):replace(bar(0),high='99')
 with pytest.raises(ValueError):replace(bar(0),close='NaN')
 from mission_agent.market.bar import dec
 with pytest.raises(ValueError):dec(.1)


def test_store_dedup_order_gap_repair_and_restart(repo,clock):
 s=PriceStore(repo);s.put(bar(0));s.put(bar(2));assert s.gaps('BTC')==[MINUTE]
 s.put(bar(1));assert s.gaps('BTC')==[]
 assert s.put(bar(2))=='DUPLICATE'
 cursor=s.db.execute("SELECT last_closed_bar_time FROM price_source_state WHERE asset='BTC'").fetchone()[0]
 path=repo.path;repo.close()
 from mission_agent.db.repository import Repository
 reopened=Repository(path,clock);r=PriceStore(reopened)
 assert r.db.execute("SELECT last_closed_bar_time FROM price_source_state WHERE asset='BTC'").fetchone()[0]==cursor
 assert len(list(r.bars('BTC')))==3
 assert r.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';reopened.close()


def test_closed_bar_cannot_regress_to_provisional(repo):
 s=PriceStore(repo);s.put(bar(0));assert s.put(bar(0,'101',closed=False))=='IGNORED_PROVISIONAL'
 assert list(s.bars('BTC'))[0].close=='100'

@pytest.mark.parametrize('point',[0,2,5])
def test_price_migration_atomic_failure(repo,point):
 with pytest.raises(RuntimeError):migrate_price(repo.db,stamp(repo.clock.now()),point)
 assert not repo.db.execute("SELECT name FROM sqlite_master WHERE name='price_bars_1m'").fetchall()
 migrate_price(repo.db,stamp(repo.clock.now()))
 assert repo.db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0]==1


def test_cache_immutable_corruption_hash_and_count(tmp_path):
 p=tmp_path/'bars.gz';save(p,[{'t':1}],{'source':'fixture'})
 assert load(p)[0]==[{'t':1}]
 with pytest.raises(ValueError):save(p,[{'t':2}],{'source':'fixture'})
 p.write_bytes(b'corrupt')
 with pytest.raises(ValueError,match='HASH'):load(p)


def test_batch_incremental_equivalence_and_candidate_dedup(repo):
 data={'BTC':[bar(i,'103' if i>1500 else '100') for i in range(1520)],'ETH':[bar(i,'106' if i>1500 else '100','ETH') for i in range(1520)]}
 starts={a:0 for a in data};a=execute(data,starts);b=execute(data,starts,True)
 assert a==b
 e=Features()
 for item in data['BTC'][:1502]:f=e.push(item)
 c=candidate(data['BTC'][1501],f);assert c['event_type']=='RAW_PRICE_CANDIDATE'
 s=PriceStore(repo);assert s.candidate(c)=='INSERTED';assert s.candidate(c)=='DUPLICATE'
 assert repo.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0]==1
 assert not any(word in c for word in ('decision','recommendation'))

@pytest.mark.parametrize('error',[TimeoutError(),urllib.error.HTTPError('u',429,'rate limit',{'Retry-After':'0'},None)])
def test_rest_fault_retry_bounded_no_network(error):
 calls=[]
 def failure(*args,**kwargs):calls.append(1);raise error
 api=Official(failure,lambda _:None)
 with pytest.raises(type(error)):api.history('BTC',0,MINUTE)
 assert len(calls)==3


def test_partial_historical_response_not_fabricated():
 class Response:
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def read(self):return b'[]'
 api=Official(lambda *a,**k:Response(),lambda _:None)
 assert api.history('BTC',0,MINUTE)==[]


def test_hype_ws_never_closed_from_clock():
 frame={'channel':'candle','data':{'s':'HYPE','t':0,'T':59999,'o':'100','h':'100','l':'100','c':'100','v':'1','n':1}}
 assert not parse_ws(frame,120000)[0].is_closed
 assert parse_rest('HYPE',frame['data'],120000).is_closed


def test_decimal_serialization_preserves_precision_outside_context():
 from mission_agent.market.bar import dec
 assert dec('1.123456789012345678901234567890123')=='1.123456789012345678901234567890123'
