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
    counts,rows,blocked,deferred=audit.query_referenced_accounts(
        FakeRPC(),{ATA:MINT},audit.START,audit.END,{SIG},W)
    assert blocked=={}
    assert deferred=={}
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


def test_missing_report_exposes_stage_without_network(tmp_path,monkeypatch):
    def must_not_call(*args):
        raise AssertionError("RPC must not be called for missing inputs")
    monkeypatch.setattr(audit,"configured_solana_endpoints",must_not_call)
    with pytest.raises(audit.AuditStageError) as exc:
        audit.run(tmp_path/"missing.json",tmp_path, tmp_path/"db",
                  tmp_path/"rpc",audit.START,audit.END)
    assert exc.value.stage=="SOURCE_REPORT"
    assert exc.value.code=="SOURCE_REPORT_UNSAFE_OR_MISSING"


def test_missing_local_ledger_fails_before_rpc_calls(tmp_path,monkeypatch):
    monkeypatch.setattr(audit,"read_report",lambda *args:(173,"test-sha"))
    def must_not_call(*args):
        raise AssertionError("RPC must not be called for missing ledger")
    monkeypatch.setattr(audit,"configured_solana_endpoints",must_not_call)
    with pytest.raises(audit.AuditStageError) as exc:
        audit.run(tmp_path/"report",tmp_path,tmp_path/"missing.sqlite",
                  tmp_path/"rpc",audit.START,audit.END)
    assert exc.value.stage=="LOCAL_LEDGER"
    assert exc.value.code=="LOCAL_LEDGER_NOT_FOUND"


def test_root_rpc_failures_report_provider_code_without_key(tmp_path,monkeypatch):
    monkeypatch.setattr(audit,"read_report",lambda *args:(173,"test-sha"))
    monkeypatch.setattr(audit,"local_snapshot",lambda *args:({SIG},set()))
    monkeypatch.setattr(audit,"configured_solana_endpoints",
                        lambda *args:["https://private-rpc.example/v2/SECRET_TOKEN"])
    def fail_rpc(*args):
        raise audit.IncompleteWindow("SOL_MAX_PAGES_REACHED")
    monkeypatch.setattr(audit,"solana_signatures",fail_rpc)
    with pytest.raises(audit.AuditStageError) as exc:
        audit.run(tmp_path/"report",tmp_path,tmp_path/"db",
                  tmp_path/"rpc",audit.START,audit.END)
    assert exc.value.stage=="ROOT_SIGNATURES"
    assert exc.value.code=="SOL_MAX_PAGES_REACHED"
    assert exc.value.details["rpc_endpoints_attempted"]==1
    assert "SECRET_TOKEN" not in str(exc.value)


def test_high_volume_account_is_marked_incomplete_without_erasing_other_accounts(monkeypatch):
    # One known high-volume token account cannot invalidate a complete low-volume sibling.
    other="2shtxUKnoNBMSvnBUqSuVfCQdjB54GM6LgNE6W2fCRkX"
    assert len(other)==44
    calls=[]
    def fake_signatures(_rpc,address,start,end):
        calls.append(address)
        if address==ATA:
            raise audit.IncompleteWindow("SOL_WALLET_TRANSACTION_BUDGET_EXCEEDED")
        return [{"signature":SIG,"slot":454400785,"blockTime":1791423976}]
    monkeypatch.setattr(audit,"solana_signatures",fake_signatures)
    counts,rows,blocked,deferred=audit.query_referenced_accounts(
        object(),{ATA:MINT,other:audit.USDC},audit.START,audit.END,{SIG},W)
    assert set(calls)=={ATA,other}
    assert counts=={other:1}
    assert rows==[]
    assert deferred=={}
    assert blocked=={ATA:{
        "mint":MINT,
        "reason":"SOL_WALLET_TRANSACTION_BUDGET_EXCEEDED",
        "signature_count":None,
        "window_complete":False,
    }}


def test_unrelated_rpc_failure_remains_hard_failure(monkeypatch):
    def fail_rpc(*args):
        raise audit.IncompleteWindow("RPC_HTTP_429")
    monkeypatch.setattr(audit,"solana_signatures",fail_rpc)
    with pytest.raises(audit.AuditStageError) as exc:
        audit.query_referenced_accounts(object(),{ATA:MINT},audit.START,audit.END,set(),W)
    assert exc.value.stage=="TOKEN_ACCOUNT_SIGNATURES"
    assert exc.value.code=="RPC_HTTP_429"


def test_excess_additional_signatures_preserved_as_unverified_not_decoded(monkeypatch):
    other="2shtxUKnoNBMSvnBUqSuVfCQdjB54GM6LgNE6W2fCRkX"
    monkeypatch.setattr(audit,"MAX_ADDITIONAL_TRANSACTIONS",1)
    def signatures(_rpc,address,start,end):
        return [
            {"signature":SIG,"slot":454400785,"blockTime":1791423976},
            {"signature":EXTRA,"slot":454400786,"blockTime":1791423976},
        ]
    monkeypatch.setattr(audit,"solana_signatures",signatures)
    class FakeRPC:
        def call(self,method,params):
            assert params[0] in {SIG,EXTRA}
            return tx(slot=454400785 if params[0]==SIG else 454400786,
                      root_signed=False,changed=False)
    counts,rows,blocked,deferred=audit.query_referenced_accounts(
        FakeRPC(),{ATA:MINT,other:audit.USDC},audit.START,audit.END,set(),W)
    assert len(counts)==2
    assert len(rows)==1
    assert len(deferred)==1
    assert set(deferred).isdisjoint({r["signature"] for r in rows})
    assert blocked=={}


def test_raw_rpc_exception_message_is_never_exposed():
    code=audit.safe_failure_code(
        ValueError("https://solana-mainnet.g.alchemy.com/v2/SECRET_TOKEN")
    )
    assert code=="UNEXPECTED_VALUEERROR"
    assert "SECRET_TOKEN" not in code
