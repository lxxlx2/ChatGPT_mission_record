"""Focused tests for native RPC historical wallet-account evidence only."""
from __future__ import annotations

import sqlite3

import pytest

from scripts import audit_frank_native_owner_coverage as audit


W=audit.WALLET
MINT="HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
ATA="7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG"
SIG="4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S"
EXTRA="31eUPZfB1QGmZqfmLsjzByy2eqkLy9vX3Ds5rtbDfAcfJKWqt9FkvD56vVBmQnQ3gE88NARUYaS7KWdQr6ZxUmLU"


def balance(idx,mint,owner,raw):
    return {"accountIndex":idx,"mint":mint,"owner":owner,
            "uiTokenAmount":{"amount":str(raw),"decimals":6}}


def tx(slot=454400785,root_signed=True,changed=True):
    keys=[
        {"pubkey":"AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51","signer":root_signed},
        {"pubkey":W,"signer":root_signed},
        {"pubkey":ATA,"signer":False},
        {"pubkey":"6HEFmhrdC8KxY4e4C5eg4nmaQNRGyMAcwuMEeMpJTGV7","signer":False},
    ]
    pre=[balance(2,MINT,W,0),balance(3,audit.USDC,W,100000000)]
    post=[balance(2,MINT,W,10000 if changed else 0),
          balance(3,audit.USDC,W,95000000 if changed else 100000000)]
    return {"slot":slot,"blockTime":1791423976,
            "transaction":{"message":{"accountKeys":keys,"instructions":[
                {"programId":next(iter(sorted(audit.SOL_ROUTERS)))}
            ]}},
            "meta":{"err":None,"preTokenBalances":pre,
                    "postTokenBalances":post,"innerInstructions":[]}}


def test_historically_observed_token_account_is_discovered_and_paid_swap_is_only_candidate():
    original=tx()
    known=audit.owned_accounts(original,W)
    assert known=={ATA:MINT,"6HEFmhrdC8KxY4e4C5eg4nmaQNRGyMAcwuMEeMpJTGV7":audit.USDC}
    f=audit.flows(original,W)
    assert f["signed_by_root"]
    assert f["fomo_cosigned"]
    assert f["opposing_net_token_quote"]
    assert f["trade_confirmed"] is False


def test_token_account_only_no_owner_delta_is_not_synthetic_buy(monkeypatch):
    class FakeRPC:
        def call(self,method,params):
            assert method=="getTransaction" and params[0]==EXTRA
            return tx(slot=454400786,root_signed=False,changed=False)
    def signatures(_rpc,address,start,end):
        if address==ATA:
            return [{"signature":SIG,"slot":454400785,"blockTime":1791423976},
                    {"signature":EXTRA,"slot":454400786,"blockTime":1791423976}]
        return []
    monkeypatch.setattr(audit,"solana_signatures",signatures)
    counts,rows=audit.query_referenced_accounts(
        FakeRPC(),{ATA:MINT},audit.START,audit.END,{SIG},W)
    assert counts[ATA]==2
    assert len(rows)==1
    assert rows[0]["signature"]==EXTRA
    assert rows[0]["no_observed_token_net"]
    assert not rows[0]["opposing_net_token_quote"]
    assert rows[0]["review_reason"]=="NO_OWNER_TOKEN_DELTA"
    assert rows[0]["trade_confirmed"] is False


def test_local_read_is_read_only_and_uses_exact_closed_window(tmp_path):
    db=tmp_path/"forward.sqlite"
    con=sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE signatures (person_id TEXT,wallet TEXT,signature TEXT,block_time INTEGER);
        CREATE TABLE trades (wallet TEXT,signature TEXT,block_time INTEGER);
    """)
    con.execute("INSERT INTO signatures VALUES(?,?,?,?)",("frank",W,SIG,audit.START))
    con.execute("INSERT INTO trades VALUES(?,?,?)",(W,SIG,audit.START))
    con.commit()
    con.close()
    before=db.read_bytes()
    sigs,trades=audit.local_snapshot(db,W,audit.START,audit.END)
    assert sigs=={SIG}
    assert trades=={SIG}
    assert db.read_bytes()==before
    with pytest.raises(audit.EvidenceGap,match="LOCAL_LEDGER_NOT_FOUND"):
        audit.local_snapshot(tmp_path/"missing",W,audit.START,audit.END)
