"""No-network regression tests for FOMO cross-chain evidence attribution."""
import json
import runpy
from pathlib import Path

import pytest

from mission_agent.meme import fomo_crosschain as fc


def b58encode(value):
    number=int.from_bytes(value,"big")
    text=""
    while number:
        number,remainder=divmod(number,58)
        text=fc._BASE58[remainder]+text
    return "1"*(len(value)-len(value.lstrip(b"\0")))+text


def topic(wallet):
    return "0x"+"0"*24+wallet.lower().removeprefix("0x")


def data_words(*words):
    return "0x"+"".join(format(x,"064x") if isinstance(x,int)
                          else x.lower().removeprefix("0x").rjust(64,"0") for x in words)


def log(index, address, topics, data="0x"):
    return {"logIndex":hex(index),"blockNumber":"0x10","address":address,
            "topics":topics,"data":data,"transactionHash":"0x"+"9"*64}


def balances(wallet, before, after, mint=fc.USDC):
    a={"accountIndex":2,"mint":mint,"owner":wallet,
       "uiTokenAmount":{"amount":str(before),"decimals":6}}
    b={"accountIndex":2,"mint":mint,"owner":wallet,
       "uiTokenAmount":{"amount":str(after),"decimals":6}}
    return [a],[b]


def sol_tx(wallet, *, signed=True, cosigned=True, solver=False, before=5_000_000,
           after=0, instructions=()):
    pre,post=balances(wallet,before,after)
    return {"slot":1212,"blockTime":1791472000,
            "transaction":{"message":{"accountKeys":[
                {"pubkey":wallet,"signer":signed},
                {"pubkey":fc.FOMO_COSIGNER,"signer":cosigned},
                {"pubkey":fc.USDC,"signer":False},
                {"pubkey":fc.SOL_RELAY_SOLVER,"signer":solver},
            ],"instructions":list(instructions)}},
            "meta":{"err":None,"preTokenBalances":pre,"postTokenBalances":post,
                    "innerInstructions":[]}}


def test_solana_relay_cash_payment_requires_wallet_signature_and_exact_instruction():
    oid="0x"+"1"*64
    payload=fc.DEPOSIT_DISCRIMINATOR+(5_000_000).to_bytes(8,"little")+bytes.fromhex(oid[2:])
    ix={"programId":fc.SOL_RELAY_DEPOSIT,"data":b58encode(payload)}
    rows=fc.solana_events("sig1",sol_tx(fc.SOL_CASH_WALLET,instructions=[ix]),fc.SOL_CASH_WALLET)
    assert len(rows)==1
    assert rows[0]["kind"]=="RELAY_PAY" and rows[0]["order_id"]==oid
    assert rows[0]["amount_raw"]=="5000000"
    assert rows[0]["signal_eligible"] is False
    unsigned=sol_tx(fc.SOL_CASH_WALLET,signed=False,instructions=[ix])
    assert fc.solana_events("sig2",unsigned,fc.SOL_CASH_WALLET)==[]
    invalid={"programId":fc.SOL_RELAY_DEPOSIT,"data":"xxx"}
    assert fc.solana_events("sig3",sol_tx(fc.SOL_CASH_WALLET,instructions=[invalid]),fc.SOL_CASH_WALLET)==[]


def test_relay_payout_signed_by_solver_and_memo_is_not_a_buy():
    oid="0x"+"2"*64
    ix={"programId":"MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr","parsed":oid}
    tx=sol_tx(fc.SOL_CASH_WALLET,signed=False,cosigned=False,solver=True,
              before=100,after=50_000_100,instructions=[ix])
    rows=fc.solana_events("payout",tx,fc.SOL_CASH_WALLET)
    assert len(rows)==1 and rows[0]["kind"]=="RELAY_PAYOUT"
    assert rows[0]["order_id"]==oid and rows[0]["amount_raw"]=="50000000"
    assert rows[0]["signal_eligible"] is False


def test_unsigned_fomo_cosigner_receipt_is_not_a_market_buy():
    tx=sol_tx(fc.SOL_CASH_WALLET,signed=False,cosigned=True,
              before=0,after=1000000)
    assert fc.solana_events("other",tx,fc.SOL_CASH_WALLET)==[]


def test_solana_samechain_candidate_not_final_trade():
    wallet=fc.SOL_CANDIDATE_WALLET
    tx=sol_tx(wallet,before=5_000_000,after=0,
              instructions=[{"programId":"DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH"}])
    tx["meta"]["postTokenBalances"].append({
        "accountIndex":3,"mint":"TokenABC","owner":wallet,
        "uiTokenAmount":{"amount":"100000000","decimals":9},
    })
    rows=fc.solana_events("swap_candidate",tx,wallet)
    assert len(rows)==1 and rows[0]["kind"]=="SWAP_CANDIDATE"
    assert rows[0]["signal_eligible"] is False


def test_evm_fill_requires_router_and_executor_transfer():
    wallet=fc.RH_CANDIDATE_WALLET
    oid="0x"+"3"*64
    token="0x"+"a"*40
    receipt={"transactionHash":"0x"+"f"*64,"status":"0x1",
        "logs":[log(1,token,[fc.TOPIC_TRANSFER,topic(fc.RH_RELAY_EXECUTOR),topic(wallet)],
                    data_words(123456))]}
    tx={"to":fc.RH_RELAY_ROUTER,"input":"0xabcdef"+oid[2:],"hash":"0x"+"f"*64}
    rows=fc.robinhood_buy_fills(tx,receipt,wallet)
    assert len(rows)==1 and rows[0]["kind"]=="BUY_FILL"
    assert rows[0]["amount_raw"]=="123456" and rows[0]["order_id"]==oid
    assert rows[0]["signal_eligible"] is False
    assert fc.robinhood_buy_fills({**tx,"to":"0x"+"b"*40},receipt,wallet)==[]


def test_evm_sell_belongs_only_to_correct_4337_operation_in_shared_bundle():
    wallet=fc.RH_CANDIDATE_WALLET
    other="0x"+"b"*40
    token="0x"+"a"*40
    oid="0x"+"4"*64
    log_list=[
        log(1,token,[fc.TOPIC_TRANSFER,topic(other),topic(fc.RH_RELAY_DEPOSITORY)],data_words(111)),
        log(2,fc.RH_ENTRYPOINT,[fc.TOPIC_USEROP,"0x"+"0"*64,topic(other)],data_words(1,1,0,0)),
        log(3,token,[fc.TOPIC_TRANSFER,topic(wallet),topic(fc.RH_RELAY_DEPOSITORY)],data_words(100)),
        log(4,fc.RH_RELAY_DEPOSITORY,[fc.TOPIC_DEPOSIT],
            data_words(wallet,fc.RH_USDG,2500000,oid)),
        log(5,fc.RH_ENTRYPOINT,[fc.TOPIC_USEROP,"0x"+"0"*64,topic(wallet)],data_words(1,1,0,0)),
    ]
    receipt={"transactionHash":"0x"+"9"*64,"status":"0x1","logs":log_list}
    rows=fc.robinhood_user_operations(receipt,wallet)
    assert len(rows)==1
    assert rows[0]["kind"]=="SELL_EXECUTED"
    assert rows[0]["asset"]==token
    assert rows[0]["order_id"]==oid
    receipt["logs"][4]["data"]=data_words(1,0,0,0)
    assert fc.robinhood_user_operations(receipt,wallet)==[]


def test_multi_token_or_multi_order_not_wrongly_called_sell():
    wallet=fc.RH_CANDIDATE_WALLET
    logs=[
        log(1,"0x"+"a"*40,[fc.TOPIC_TRANSFER,topic(wallet),topic("0x"+"b"*40)],data_words(100)),
        log(2,"0x"+"c"*40,[fc.TOPIC_TRANSFER,topic(wallet),topic("0x"+"d"*40)],data_words(200)),
        log(3,fc.RH_ENTRYPOINT,[fc.TOPIC_USEROP,"0x"+"0"*64,topic(wallet)],data_words(1,1,0,0)),
    ]
    receipt={"transactionHash":"0x"+"9"*64,"logs":logs}
    rows=fc.robinhood_user_operations(receipt,wallet)
    assert len(rows)==1 and rows[0]["kind"]=="USEROP_AMBIGUOUS"


def test_cross_chain_relay_join_is_exact_unique_and_not_followable():
    oid="0x"+"f"*64
    pay={"kind":"RELAY_PAY","order_id":oid,"chain":"SOL","asset":fc.USDC,"tx_id":"sol1"}
    fill={"kind":"BUY_FILL","order_id":oid,"chain":"RH","asset":"0x"+"a"*40,"tx_id":"rh1"}
    other={"kind":"RELAY_PAY","order_id":"0x"+"e"*64,"chain":"SOL","asset":fc.USDC,"tx_id":"sol2"}
    joined=fc.pair_orders([pay,fill,other])
    assert len(joined)==2
    good=next(x for x in joined if x["order_id"]==oid)
    assert good["kind"]=="PAIRED_BUY_EVIDENCE"
    assert good["attribution"]=="THIRD_PARTY_UNVERIFIED"
    assert good["follow_signal_eligible"] is False
    dup=fc.pair_orders([pay,fill,{**fill,"tx_id":"rh2"}])
    assert dup[0]["kind"]=="INCOMPLETE_OR_AMBIGUOUS_ORDER"


def test_two_leg_sell_is_not_a_buy():
    oid="0x"+"f"*64
    joined=fc.pair_orders([
        {"kind":"SELL_EXECUTED","order_id":oid,"chain":"RH","asset":"token","tx_id":"evm"},
        {"kind":"RELAY_PAYOUT","order_id":oid,"chain":"SOL","asset":fc.USDC,"tx_id":"sol"},
    ])
    assert joined[0]["kind"]=="PAIRED_SELL_EVIDENCE"


def test_unrecognized_order_id_is_never_paired():
    assert fc.order_id("0x"+"0"*64) is None
    assert fc.order_id("broken") is None
    assert fc.pair_orders([{"kind":"RELAY_PAY","order_id":None}])==[]


def test_collector_requires_true_rpc_completeness(monkeypatch):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="module_unit_test")
    class NoPage:
        def call(self,method,params):
            if method=="getSignaturesForAddress":
                return [{"signature":"one","slot":10,"blockTime":999}]
            if method=="getTransaction":
                return None
            raise AssertionError(method)
    monkeypatch.setitem(audit["solana_signatures"].__globals__,"MAX_SOL_PAGES",1)
    with pytest.raises(audit["IncompleteWindow"]):
        audit["solana_signatures"](NoPage(),"wallet",10)
    assert audit["pad_evm_wallet"](fc.RH_CANDIDATE_WALLET).endswith(fc.RH_CANDIDATE_WALLET[2:])


def test_audit_never_exposes_unverified_identity_as_signal():
    assert fc.RH_CHAIN_ID==4663
    assert fc.FOMO_EIP7702_CODE.startswith("0xef0100")
    assert fc.RH_CANDIDATE_WALLET.lower()=="0x696d1265c8fc4f14797abebfae3c43ebfa9d8e28"
