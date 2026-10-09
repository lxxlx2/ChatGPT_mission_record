"""Targeted tests for rate-limit-safe, strictly offline Frank cache audit."""
from __future__ import annotations

import json
import sqlite3

import pytest

from scripts import audit_frank_root_offline as offline


W = offline.WALLET
M = "HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
TOKEN_ACCOUNT = "7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG"
USDC_ACCOUNT = "6HEFmhrdC8KxY4e4C5eg4nmaQNRGyMAcwuMEeMpJTGV7"
S1="4"*88
S2="5"*88


def tx(sig, block_time, swap):
    keys = [
        {"pubkey":W,"signer":True},
        {"pubkey":TOKEN_ACCOUNT,"signer":False},
        {"pubkey":USDC_ACCOUNT,"signer":False},
    ]
    def bal(idx,mint,amount):
        return {"accountIndex":idx,"mint":mint,"owner":W,
                "uiTokenAmount":{"amount":str(amount),"decimals":6}}
    pre=[bal(1,M,0),bal(2,offline.USDC,10000000)]
    post=[bal(1,M,10000 if swap else 0),
          bal(2,offline.USDC,5000000 if swap else 10000000)]
    return {"slot":100 if sig==S1 else 101,"blockTime":block_time,
            "transaction":{"message":{"accountKeys":keys,"instructions":[]}},
            "meta":{"err":None,"preTokenBalances":pre,
                    "postTokenBalances":post,"innerInstructions":[]}}


def fixtures(tmp_path):
    cache=tmp_path/"cache"
    directory=cache/W
    directory.mkdir(parents=True)
    for sig,delta,at in ((S1,True,offline.START+20),(S2,False,offline.START+30)):
        obj=tx(sig,at,delta)
        file=directory/(sig+".json")
        file.write_text(json.dumps({"signature":sig,"slot":obj["slot"],"tx":obj}))
        file.chmod(0o600)
    db=tmp_path/"live.sqlite"
    con=sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE signatures (person_id TEXT,wallet TEXT,signature TEXT,block_time INTEGER);
        CREATE TABLE trades (wallet TEXT,signature TEXT,block_time INTEGER);
    """)
    for sig,at in ((S1,offline.START+20),(S2,offline.START+30)):
        con.execute("INSERT INTO signatures VALUES(?,?,?,?)",("frank",W,sig,at))
    con.execute("INSERT INTO trades VALUES(?,?,?)",(W,S1,offline.START+20))
    con.commit()
    con.close()
    return cache,db


def test_offline_only_two_root_transactions_produce_bounded_candidates(monkeypatch,tmp_path):
    cache,db=fixtures(tmp_path)
    monkeypatch.setattr(offline,"read_report",lambda *args:(2,"verified-source-sha"))
    original_db=db.read_bytes()
    report=offline.build_offline_report(tmp_path/"original.json",cache,db,offline.START,offline.END)
    assert db.read_bytes()==original_db
    assert report["status"]=="OFFLINE_ROOT_CACHE_RECONCILED_SCOPE_LIMITED"
    assert report["cached_root_transaction_count"]==2
    assert report["local_classified_signature_count"]==1
    assert report["root_opposing_flow_candidate_count"]==1
    assert report["root_opposing_flow_candidates"][0]["signature"]==S1
    assert report["root_opposing_flow_candidates"][0]["already_classified_by_mission"]
    assert report["root_opposing_flow_candidates"][0]["trade_confirmed"] is False
    assert report["owned_accounts_observed_in_cached_root"]==2
    assert report["token_account_signature_coverage_checked"] is False
    assert report["can_conclude_complete_frank_trades"] is False
    assert report["rpc_requests"]==0
    assert report["external_indexer_requests"]==0
    assert report["production_db_writes"]==0


def test_offline_cache_count_mismatch_is_blocking(tmp_path):
    cache,_=fixtures(tmp_path)
    with pytest.raises(offline.EvidenceGap,match="ROOT_CACHE_WINDOW_COUNT_MISMATCH"):
        offline.cached_root(cache,W,offline.START,offline.END,3)


def test_offline_cache_identity_must_match_filename(tmp_path):
    cache,_=fixtures(tmp_path)
    one=cache/W/(S1+".json")
    data=json.loads(one.read_text())
    data["signature"]=S2
    one.write_text(json.dumps(data))
    with pytest.raises(offline.EvidenceGap,match="ROOT_CACHE_IDENTITY_MISMATCH"):
        offline.cached_root(cache,W,offline.START,offline.END,2)


def test_offline_cache_symlinks_rejected(tmp_path):
    cache,_=fixtures(tmp_path)
    original=cache/W/(S1+".json")
    original.unlink()
    original.symlink_to(cache/W/(S2+".json"))
    with pytest.raises(offline.EvidenceGap,match="ROOT_CACHE_ENTRY_UNSAFE"):
        offline.cached_root(cache,W,offline.START,offline.END,2)


def test_offline_mismatched_ledger_is_not_silent_success(monkeypatch,tmp_path):
    cache,db=fixtures(tmp_path)
    monkeypatch.setattr(offline,"read_report",lambda *args:(2,"verified-source-sha"))
    con=sqlite3.connect(db)
    con.execute("DELETE FROM signatures WHERE signature=?",(S2,))
    con.commit()
    con.close()
    report=offline.build_offline_report(tmp_path/"source",cache,db,offline.START,offline.END)
    assert report["cached_root_not_in_local_ledger"]==[S2]
    assert report["can_conclude_complete_frank_trades"] is False
