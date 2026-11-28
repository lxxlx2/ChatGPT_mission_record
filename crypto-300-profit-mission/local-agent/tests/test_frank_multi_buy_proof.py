"""Direct market legs are proven independently; a routing aggregate is not."""
import copy

import pytest

from mission_agent.meme.holder_ranks import _b58
from mission_agent.signals.classifier import classify
from mission_agent.signals.multi_buy_proof import PROGRAM, SPL, SWAP_INPUT, SWAP_OUTPUT
from mission_agent.signals.policy import USDC
from mission_agent.signals.store import Ledger

ADDRESS = lambda n: _b58(bytes((n,))*32)
WALLET, AUTH, SOURCE, TARGET_A, TARGET_B = (ADDRESS(n) for n in range(10,15))
SIGNATURE = _b58(bytes((23,))*64)


def tx():
    names = [WALLET, AUTH, SOURCE, TARGET_A, TARGET_B, USDC, SPL] + [ADDRESS(i) for i in range(25,37)]
    q1,q2,t1,t2,d1,d2,p1,p2,c1,c2,o1,o2 = names[7:]
    def bal(addr,mint,owner,n):
        return {"accountIndex":names.index(addr),"mint":mint,"owner":owner,"programId":SPL,
                "uiTokenAmount":{"amount":str(n),"decimals":6}}
    block = [(SOURCE,USDC,WALLET,100,65),(q1,USDC,AUTH,0,10),(q2,USDC,AUTH,0,25),
             (t1,TARGET_A,AUTH,555,548),(t2,TARGET_B,AUTH,444,443),
             (d1,TARGET_A,WALLET,0,7),(d2,TARGET_B,WALLET,0,1)]
    def cpi(src,dst,mint,authority,amount):
        return {"programId":SPL,"stackHeight":2,"parsed":{"type":"transferChecked",
                "info":{"source":src,"destination":dst,"mint":mint,"authority":authority,
                        "tokenAmount":{"amount":str(amount),"decimals":6}}}}
    plans = [(TARGET_A,p1,c1,o1,q1,t1,d1,10,7,SWAP_INPUT,10,6),
             (TARGET_B,p2,c2,o2,q2,t2,d2,25,1,SWAP_OUTPUT,26,1)]
    outer, inner = [], []
    for i,(target,pool,config,obs,q,t,d,paid,got,tag,lim1,lim2) in enumerate(plans):
        outer.append({"programId":PROGRAM,"data":_b58(tag+lim1.to_bytes(8,"little")+lim2.to_bytes(8,"little")),
                      "accounts":[WALLET,AUTH,config,pool,SOURCE,d,q,t,SPL,SPL,USDC,target,obs]})
        inner.append({"index":i,"instructions":[cpi(SOURCE,q,USDC,WALLET,paid),cpi(t,d,target,AUTH,got)]})
    return {"slot":12,"blockTime":1790760000,"version":0,
            "transaction":{"signatures":[SIGNATURE],"message":{
                "accountKeys":[{"pubkey":key,"signer":i==0} for i,key in enumerate(names)],"instructions":outer}},
            "meta":{"err":None,"fee":5000,"preBalances":[10000]+[1]*(len(names)-1),
                    "postBalances":[5000]+[1]*(len(names)-1),
                    "preTokenBalances":[bal(*row[:4]) for row in block],
                    "postTokenBalances":[bal(*row[:3],row[4]) for row in block],"innerInstructions":inner,
                    "logMessages":[]}}


def legs(raw, signature=SIGNATURE):
    return classify(signature,raw,WALLET).get("classification_details",{}).get("independent_buy_legs",[])


def test_two_independent_swaps_bind_each_debit_and_credit_without_logs(tmp_path):
    raw = tx()
    result = classify(SIGNATURE,raw,WALLET)
    assert result["trade"] is None
    found = legs(raw)
    assert [(r["mint"],r["quote_raw"],r["token_raw"],r["outer_index"]) for r in found]==[
        (TARGET_A,"10","7",0),(TARGET_B,"25","1",1)]
    assert len({r["leg_id"] for r in found})==2
    assert legs(copy.deepcopy(raw))==found
    ledger=Ledger(tmp_path/"ledger.sqlite")
    assert ledger.put("frank",result,result["evidence"]["raw_transaction_sha256"],"synthetic")
    assert ledger.db.execute("SELECT count(*) FROM signatures").fetchone()[0]==1
    for table in ("trades","signals","outbox"):
        assert ledger.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]==0


@pytest.mark.parametrize("case", ["router","extra_instruction","missing_cpi","same_inner_index","spoofed_vault",
                                  "other_transfer_owner","amount_bound","account_balance","duplicate_balance",
                                  "token_2022","missing_stack_height","no_wallet_signature","fee_rent","tx_failed"])
def test_does_not_split_unbound_or_nonmatching_flows(case):
    raw=tx()
    meta=raw["meta"]
    message=raw["transaction"]["message"]
    outer=message["instructions"]
    first=meta["innerInstructions"][0]["instructions"][0]
    if case=="router":
        outer[0]["programId"]="JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
    elif case=="extra_instruction":
        outer.append(copy.deepcopy(first))
    elif case=="missing_cpi":
        meta["innerInstructions"][0]["instructions"].pop()
    elif case=="same_inner_index":
        meta["innerInstructions"][1]["index"]=0
    elif case=="spoofed_vault":
        first["parsed"]["info"]["destination"]=ADDRESS(26)
    elif case=="other_transfer_owner":
        first["parsed"]["info"]["authority"]=AUTH
    elif case=="amount_bound":
        outer[0]["data"]=_b58(SWAP_INPUT+(11).to_bytes(8,"little")+(6).to_bytes(8,"little"))
    elif case=="account_balance":
        meta["postTokenBalances"][2]["uiTokenAmount"]["amount"]="24"
    elif case=="duplicate_balance":
        meta["postTokenBalances"].append(copy.deepcopy(meta["postTokenBalances"][0]))
    elif case=="token_2022":
        outer[0]["accounts"][8]="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
    elif case=="missing_stack_height":
        first.pop("stackHeight")
    elif case=="no_wallet_signature":
        message["accountKeys"][0]["signer"]=False
    elif case=="fee_rent":
        meta["postBalances"][0]=4900
    elif case=="tx_failed":
        meta["err"]={"InstructionError":[0,"Custom"]}
    assert legs(raw)==[]


def test_given_signature_must_match_raw_transaction():
    assert legs(tx(),_b58(bytes((24,))*64))==[]
