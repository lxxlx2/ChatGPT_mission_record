import importlib.util
import json
import sqlite3
from collections import Counter
from pathlib import Path

SCRIPT=Path(__file__).parents[1]/'scripts'/'frank_sol_usd_shadow_replay.py'
spec=importlib.util.spec_from_file_location('frank_sol_usd_shadow_replay',SCRIPT)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def memory_db():
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row;mod._ensure_reference_table(db);return db


class SequenceClient:
    def __init__(self,values):self.values=list(values);self.calls=0
    def reference(self,block_time):
        self.calls+=1
        return self.values[min(self.calls-1,len(self.values)-1)]


def verified(price='100',block_time=1000):
    epoch=mod.reference_epoch(block_time)
    value={
        'status':'VERIFIED','retryable':False,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC',
        'symbol':'SOLUSDC','interval':'1m','selection_rule':'PREVIOUS_CLOSED_1M_CLOSE',
        'reference_epoch':epoch,'candle_open_ms':epoch*1000,'candle_close_ms':epoch*1000+59999,
        'open':price,'high':price,'low':price,'close':price,'sol_usdc':price,'observed_at':123.0,
    }
    value['evidence_sha256']=mod._evidence_hash(value)
    return value


def missing_kline(block_time=1000):
    epoch=mod.reference_epoch(block_time)
    return {
        'status':'UNAVAILABLE','reason':'BINANCE_KLINE_NOT_FOUND','retryable':False,
        'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','symbol':'SOLUSDC','interval':'1m',
        'selection_rule':'PREVIOUS_CLOSED_1M_CLOSE','reference_epoch':epoch,'observed_at':123.0,
    }


def test_transient_failure_is_not_persisted_and_later_call_can_recover():
    db=memory_db();client=SequenceClient([
        {'status':'UNAVAILABLE','reason':'BINANCE_HTTP_429','retryable':True,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':900},
        {'status':'UNAVAILABLE','reason':'BINANCE_HTTP_429','retryable':True,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':900},
        {'status':'UNAVAILABLE','reason':'BINANCE_HTTP_429','retryable':True,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':900},
        verified(),
    ])
    first=mod._reference(db,client,1000,attempts=3,sleep=lambda _:None)
    assert first['status']=='UNAVAILABLE'
    assert db.execute('select count(*) from sol_usdc_references').fetchone()[0]==0
    second=mod._reference(db,client,1019,attempts=3,sleep=lambda _:None)
    assert second['status']=='VERIFIED'
    assert client.calls==4
    assert db.execute('select count(*) from sol_usdc_references').fetchone()[0]==1


def test_verified_reference_is_shared_by_candle_not_trade_timestamp():
    db=memory_db();client=SequenceClient([verified()])
    one=mod._reference(db,client,1000,sleep=lambda _:None)
    two=mod._reference(db,client,1019,sleep=lambda _:None)
    assert one==two
    assert 'block_time' not in one
    assert client.calls==1


def test_deterministic_missing_kline_is_cacheable_only_in_replay_target():
    target=memory_db();cache=memory_db();client=SequenceClient([missing_kline()])
    one=mod._reference(target,client,1000,sleep=lambda _:None,cache_db=cache)
    two=mod._reference(target,client,1019,sleep=lambda _:None,cache_db=cache)
    assert one['reason']=='BINANCE_KLINE_NOT_FOUND' and two['reason']=='BINANCE_KLINE_NOT_FOUND'
    assert client.calls==1
    assert target.execute('select count(*) from sol_usdc_references').fetchone()[0]==1
    assert cache.execute('select count(*) from sol_usdc_references').fetchone()[0]==0


def test_external_reference_cache_reuses_verified_candle_and_copies_it_into_new_target():
    cache=memory_db();first_target=memory_db();client=SequenceClient([verified('123')])
    first=mod._reference(first_target,client,1000,sleep=lambda _:None,cache_db=cache)
    assert first['sol_usdc']=='123' and client.calls==1
    assert cache.execute('select count(*) from sol_usdc_references').fetchone()[0]==1

    second_target=memory_db();offline=SequenceClient([{'status':'UNAVAILABLE','reason':'SHOULD_NOT_CALL','retryable':False}])
    stats=Counter()
    second=mod._reference(second_target,offline,1019,sleep=lambda _:None,cache_db=cache,cache_stats=stats)
    assert second['sol_usdc']=='123'
    assert offline.calls==0
    assert stats['hits']==1 and stats['rejected']==0
    assert second_target.execute('select count(*) from sol_usdc_references').fetchone()[0]==1


def test_tampered_reusable_cache_is_rejected_and_refetched():
    cache=memory_db();target=memory_db()
    bad=verified('1')
    bad['evidence_sha256']='tampered'
    mod._store_reference(cache,mod.reference_key(1000),1000,bad)
    cache.commit()
    client=SequenceClient([verified('123')]);stats=Counter()
    value=mod._reference(target,client,1000,sleep=lambda _:None,cache_db=cache,cache_stats=stats)
    assert client.calls==1
    assert stats['rejected']==1
    assert value['sol_usdc']=='123'
    stored=cache.execute('select body from sol_usdc_references').fetchone()[0]
    assert '"sol_usdc":"123"' in stored


def test_reusable_cache_rejects_body_when_database_content_hash_no_longer_matches():
    cache=memory_db();target=memory_db()
    good=verified('10')
    mod._store_reference(cache,mod.reference_key(1000),1000,good)
    body=json.loads(cache.execute('select body from sol_usdc_references').fetchone()[0])
    body['sol_usdc']='999'
    cache.execute('update sol_usdc_references set body=?',(json.dumps(body,sort_keys=True,separators=(',',':')),))
    cache.commit()
    client=SequenceClient([verified('77')]);stats=Counter()
    value=mod._reference(target,client,1000,sleep=lambda _:None,cache_db=cache,cache_stats=stats)
    assert client.calls==1 and value['sol_usdc']=='77'
    assert stats['rejected']==1


def test_reusable_cache_rejects_wrong_candle_metadata_even_with_matching_hashes():
    cache=memory_db();target=memory_db()
    bad=verified('1')
    bad['candle_open_ms']=bad['candle_open_ms']+60000
    bad['evidence_sha256']=mod._evidence_hash(bad)
    mod._store_reference(cache,mod.reference_key(1000),1000,bad)
    client=SequenceClient([verified('88')]);stats=Counter()
    value=mod._reference(target,client,1000,sleep=lambda _:None,cache_db=cache,cache_stats=stats)
    assert client.calls==1 and value['sol_usdc']=='88'
    assert stats['rejected']==1


def test_reusable_cache_rejects_self_consistent_hashes_when_close_disagrees_with_selected_price():
    cache=memory_db();target=memory_db()
    bad=verified('150')
    bad['sol_usdc']='1'
    bad['evidence_sha256']=mod._evidence_hash(bad)
    mod._store_reference(cache,mod.reference_key(1000),1000,bad)
    client=SequenceClient([verified('77')]);stats=Counter()
    value=mod._reference(target,client,1000,sleep=lambda _:None,cache_db=cache,cache_stats=stats)
    assert client.calls==1 and value['sol_usdc']=='77'
    assert stats['rejected']==1


def test_reusable_cache_rejects_close_outside_low_high_even_with_recomputed_hashes():
    cache=memory_db();target=memory_db()
    bad=verified('150')
    bad['high']='100';bad['low']='90';bad['open']='95'
    bad['evidence_sha256']=mod._evidence_hash(bad)
    mod._store_reference(cache,mod.reference_key(1000),1000,bad)
    client=SequenceClient([verified('66')]);stats=Counter()
    value=mod._reference(target,client,1000,sleep=lambda _:None,cache_db=cache,cache_stats=stats)
    assert client.calls==1 and value['sol_usdc']=='66'
    assert stats['rejected']==1


def test_cleanup_sqlite_removes_target_and_sidecars(tmp_path):
    target=tmp_path/'shadow.sqlite'
    for suffix in ('','-wal','-shm','-journal'):
        Path(str(target)+suffix).write_text('x')
    mod._cleanup_sqlite(target)
    assert not any(Path(str(target)+suffix).exists() for suffix in ('','-wal','-shm','-journal'))


def test_missing_quote_decimals_is_input_failure_not_reference_failure():
    assert mod._input_failure_reason({'quote_asset':'SOL','quote_amount_raw':'1','quote_decimals':None})=='QUOTE_DECIMALS_MISSING'
    assert mod._input_failure_reason({'quote_asset':'SOL','quote_amount_raw':None,'quote_decimals':9})=='QUOTE_AMOUNT_MISSING'


def sig(mint='A',trigger='u1'):
    return {'person_id':'frank','mint':mint,'episode_id':'e','signal_type':'FRANK_ACCUMULATION_SIGNAL','stage':'PRECONFIRM','triggering_signature':trigger}


def test_strict_regression_does_not_exclude_mixed_sol_usdc_mints():
    source=[sig('MIXED','usdc-trigger')]
    result=mod.compare_signals_strict(source,[])
    assert result['pass'] is False
    assert result['missing']==source


def test_strict_regression_passes_when_all_old_signals_survive_and_allows_additions():
    source=[sig('MIXED','old')];shadow=[sig('MIXED','old'),sig('SOLONLY','new')]
    result=mod.compare_signals_strict(source,shadow)
    assert result['pass'] is True
    assert result['missing']==[]
    assert result['added']==[shadow[1]]


def test_fatal_binance_access_reasons_are_explicit_and_bounded():
    assert {'BINANCE_HTTP_403','BINANCE_HTTP_418','BINANCE_HTTP_451'} <= mod.FATAL_ACCESS_REASONS
    assert mod.FATAL_ACCESS_STREAK_LIMIT==3
