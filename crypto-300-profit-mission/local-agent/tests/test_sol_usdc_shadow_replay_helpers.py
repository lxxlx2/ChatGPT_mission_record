import importlib.util
import sqlite3
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


def verified(price='100'):
    return {'status':'VERIFIED','retryable':False,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':960,'sol_usdc':price,'evidence_sha256':'v'}


def test_transient_failure_is_not_persisted_and_later_call_can_recover():
    db=memory_db();client=SequenceClient([
        {'status':'UNAVAILABLE','reason':'BINANCE_HTTP_429','retryable':True,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':960},
        {'status':'UNAVAILABLE','reason':'BINANCE_HTTP_429','retryable':True,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':960},
        {'status':'UNAVAILABLE','reason':'BINANCE_HTTP_429','retryable':True,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':960},
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


def test_deterministic_missing_kline_is_cacheable():
    db=memory_db();client=SequenceClient([{'status':'UNAVAILABLE','reason':'BINANCE_KLINE_NOT_FOUND','retryable':False,'source':'BINANCE_OFFICIAL_SPOT_SOLUSDC','reference_epoch':960}])
    mod._reference(db,client,1000,sleep=lambda _:None);mod._reference(db,client,1019,sleep=lambda _:None)
    assert client.calls==1
    assert db.execute('select count(*) from sol_usdc_references').fetchone()[0]==1


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
