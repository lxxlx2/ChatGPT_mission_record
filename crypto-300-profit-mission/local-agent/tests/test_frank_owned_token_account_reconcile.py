"""Targeted regression for Frank root vs owned mint-account historical coverage."""
from __future__ import annotations

from scripts import reconcile_frank_owned_token_account as audit


ROOT=audit.ROOT
MINT=audit.MINT
ACCOUNT="7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG"


def balance(idx,mint,owner,amount):
    return {
        "accountIndex":idx,"mint":mint,"owner":owner,
        "uiTokenAmount":{"amount":str(amount),"decimals":6},
    }


def transaction(sig,delta,quote_delta,root_reference):
    keys=[{"pubkey":ACCOUNT,"signer":False},{"pubkey":"FEE","signer":True}]
    if root_reference:
        keys.append({"pubkey":ROOT,"signer":True})
    target=balance(0,MINT,ROOT,1000)
    quote=balance(1,list(audit.QUOTE_MINTS)[0],ROOT,30000)
    result={
        "slot":123 if sig=="root" else 124 if sig=="extra" else 125,
        "blockTime":1791423976,
        "transaction":{"message":{"accountKeys":keys,"instructions":[]}},
        "meta":{"err":None,"preTokenBalances":[target,quote],
                "postTokenBalances":[balance(0,MINT,ROOT,1000+delta),
                                     balance(1,quote["mint"],ROOT,30000+quote_delta)]},
    }
    return result


class FakeRPC:
    def call(self,method,params):
        if method=="getTokenAccountsByOwner":
            return {"value":[{"pubkey":ACCOUNT,"account":{"data":{"parsed":{"info":{
                "mint":MINT,"owner":ROOT,
            }}}}}]}
        if method=="getTransaction":
            sig=params[0]
            return {
                "root":transaction(sig,100,-20,True),
                "extra":transaction(sig,250,0,False),
                "noop":transaction(sig,0,0,False),
            }[sig]
        raise AssertionError(method)


def test_token_account_only_signatures_are_reported_not_automatically_buys(monkeypatch):
    def signatures(rpc, address, since, until):
        if address==ROOT:return [{"signature":"root","slot":123,"blockTime":1791423976}]
        if address==ACCOUNT:return [
            {"signature":"root","slot":123,"blockTime":1791423976},
            {"signature":"extra","slot":124,"blockTime":1791423976},
            {"signature":"noop","slot":125,"blockTime":1791423976},
        ]
        raise AssertionError(address)
    monkeypatch.setattr(audit,"solana_signatures",signatures)
    result=audit.audit(FakeRPC(),ROOT,MINT,1791386454,1791472854)
    assert result["root_signatures_in_window"]==1
    assert result["mint_account_unique_signatures"]==3
    assert result["mint_account_signatures_not_in_root_index"]==2
    assert result["candidate_extra_sigs"]==["extra","noop"]
    assert result["historical_closed_accounts_covered"] is False
    assert result["confirmed_frank_buy_count"] is None
    rows={x["signature"]:x for x in result["mint_account_transactions"]}
    assert rows["root"]["review_status"]=="OPPOSING_FLOWS_REVIEW_REQUIRED"
    assert rows["extra"]["root_referenced"] is False
    assert rows["extra"]["review_status"]=="TOKEN_CHANGE_WITHOUT_OWNED_QUOTE"
    assert rows["noop"]["review_status"]=="NO_OWNER_MINT_DELTA"
    assert all(not row["trade_confirmed"] for row in rows.values())
    assert result["production_db_writes"]==0
    assert result["gmail_sent"]==0


def test_delegated_quote_change_without_root_signer_remains_review_only():
    tx=transaction("extra",100,-5,False)
    event=audit.delta_evidence(tx,ROOT,MINT,"extra",False,[ACCOUNT])
    assert event["root_signed"] is False
    assert event["opposing_owned_asset_flows"] is True
    assert event["trade_confirmed"] is False


def test_current_mint_account_identity_requires_same_root_owner():
    class Other(FakeRPC):
        def call(self,method,params):
            if method=="getTokenAccountsByOwner":
                return {"value":[{"pubkey":ACCOUNT,"account":{"data":{"parsed":{"info":{
                    "mint":MINT,"owner":"someone_else",
                }}}}}]}
            return super().call(method,params)
    assert audit.discover_current_token_accounts(Other(),ROOT,MINT)==[]
