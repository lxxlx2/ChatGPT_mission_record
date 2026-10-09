"""Read-only three-sample FOMO settlement trace: no blind RPC or signals."""
import pytest

from scripts import audit_frank_native_resume as scan
from scripts import audit_frank_partial_trace as trace

ACCOUNT=trace.DEFAULT_ACCOUNT
ROOT=scan.WALLET
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
OTHER="6HEFmhrdC8KxY4e4C5eg4nmaQNRGyMAcwuMEeMpJTGV7"
BASE58="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def sig(n):
    out=""
    n+=1
    while n:
        n,r=divmod(n,58)
        out=BASE58[r]+out
    return "1"*(88-len(out))+out


def context():
    return {"version":scan.VERSION,"wallet":ROOT,
            "start":scan.START,"end":scan.END,
            "source_sha256":"a"*64,"root_tx_sha256":"b"*64,
            "root_count":173,"commitment":"finalized",
            "page_size":scan.PAGE_SIZE,
            "max_signatures":scan.MAX_SOL_TRANSACTIONS_PER_WALLET,
            "max_pages":scan.MAX_SOL_PAGES,
            "max_extra_decode":scan.MAX_ADDITIONAL_TRANSACTIONS,
            "inventory":{ACCOUNT:USDC}}


def balance(index,owner,raw):
    return {"accountIndex":index,"mint":USDC,"owner":owner,
            "uiTokenAmount":{"amount":str(raw),"decimals":6}}


def transaction(row):
    return {
        "slot":row["slot"],"blockTime":row["blockTime"],
        "transaction":{"message":{
            "accountKeys":[
                {"pubkey":OTHER,"signer":True},
                {"pubkey":ACCOUNT,"signer":False},
                {"pubkey":"7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG","signer":False},
                {"pubkey":scan.flows.__globals__["FOMO_COSIGNER"],"signer":True},
                {"pubkey":"DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH","signer":False},
            ],
            "instructions":[
                {"programId":"DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH"},
                {"programId":"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                 "parsed":{"type":"transferChecked","info":{
                    "source":OTHER,"destination":ACCOUNT,
                    "authority":OTHER,"mint":USDC,
                    "tokenAmount":{"amount":"475000","decimals":6}}}},
            ]}},
        "meta":{"err":None,
            "preTokenBalances":[balance(1,ROOT,0),balance(0,OTHER,1000000)],
            "postTokenBalances":[balance(1,ROOT,475000),balance(0,OTHER,525000)],
            "innerInstructions":[]},
    }


def fixture_store(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    rows=[{"signature":sig(i),"slot":454440000+i,
           "blockTime":scan.START+5000-i} for i in range(5)]
    state=store.account(ACCOUNT)
    state.update({"status":"ACTIVE","pages":1,
                  "before":rows[-1]["signature"],"rows":rows})
    store.save_account(state)
    samples=scan.partial_decode_sample(store,set(),ACCOUNT)
    for row in samples:
        tx=transaction(row)
        store.save_receipt(row["signature"],tx,scan.decode_tx(row,lambda *a:tx)[1])
    return store,rows,samples


def test_three_saved_receipts_retraced_exactly_then_reused_at_zero_rpc(tmp_path,monkeypatch):
    store,rows,samples=fixture_store(tmp_path)
    source={x["signature"]:transaction(x) for x in samples}
    calls=[]
    def fake_rpc(_endpoint,method,params):
        calls.append(params[0])
        assert method=="getTransaction"
        return source[params[0]]
    monkeypatch.setattr(trace.audit,"one_rpc",fake_rpc)
    result=trace.trace(store,set(),ACCOUNT,"https://example.invalid",3)
    assert result["status"]=="TRACE_REVIEW_ONLY"
    assert result["rpc_attempts"]==3
    assert result["sample_candidates"]==3
    assert result["all_sample_traces_complete"] is True
    assert result["trade_confirmed"] is False
    assert result["production_db_writes"]==0
    assert len(calls)==3
    item=result["traces"][0]
    assert item["frank_root_in_account_keys"] is False
    assert item["frank_root_signed"] is False
    assert item["fomo_cosigned"] is True
    assert "DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH" in item["program_ids"]
    assert item["fee_payer"]==OTHER
    assert item["instruction_count"]==2
    assert item["tx_succeeded"] is True
    frank=[x for x in item["token_balance_changes"] if x["owner_is_frank"]]
    assert len(frank)==1 and frank[0]["change_raw"]=="475000"
    others=[x for x in item["token_balance_changes"] if not x["owner_is_frank"]]
    assert len(others)==1 and others[0]["change_raw"]=="-475000"
    assert store.account(ACCOUNT)["rows"]==rows
    reopened=scan.Checkpoints(store.root,context(),create=False)
    monkeypatch.setattr(trace.audit,"one_rpc",lambda *a:pytest.fail("NETWORK CALLED"))
    reused=trace.trace(reopened,set(),ACCOUNT,"https://example.invalid",3)
    assert reused["rpc_attempts"]==0
    assert reused["traces"]==result["traces"]


def test_trace_requires_prior_hash_bound_receipt(tmp_path,monkeypatch):
    store,rows,samples=fixture_store(tmp_path)
    target=store.root/("receipt-"+samples[0]["signature"]+".json")
    target.unlink()
    monkeypatch.setattr(trace.audit,"one_rpc",lambda *a:pytest.fail("NETWORK CALLED"))
    with pytest.raises(scan.ScanBlocked,match="TRACE_REQUIRES_EXISTING_DECODE_RECEIPT"):
        trace.trace(store,set(),ACCOUNT,"https://example.invalid",3)


def test_trace_rejects_same_slot_modified_transaction_and_writes_no_trace(tmp_path,monkeypatch):
    store,rows,samples=fixture_store(tmp_path)
    tx=transaction(samples[0])
    tx["meta"]["postTokenBalances"][0]["uiTokenAmount"]["amount"]="475001"
    monkeypatch.setattr(trace.audit,"one_rpc",lambda *a:tx)
    with pytest.raises(scan.ScanBlocked,match="TRACE_TRANSACTION_HASH_MISMATCH"):
        trace.trace(store,set(),ACCOUNT,"https://example.invalid",3)
    assert not list(store.root.glob("trace-*.json"))
