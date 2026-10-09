"""Synthetic no-network tests for exact Frank TWEETCRAFT instruction audit."""
import copy

import pytest

from mission_agent.meme.fomo_crosschain import FOMO_COSIGNER, SOL_ROUTERS, USDC
from scripts import audit_frank_native_resume as audit
from scripts import audit_frank_tweetcraft_instruction_offline as focus


def bal(index,mint,owner,amount):
    return {"accountIndex":index,"mint":mint,"owner":owner,
            "uiTokenAmount":{"amount":str(amount),"decimals":6}}


def fake_swap():
    wallet=audit.WALLET
    program=next(iter(SOL_ROUTERS))
    return {
        "slot":454400785,"blockTime":1791423976,
        "transaction":{"message":{"accountKeys":[
            {"pubkey":FOMO_COSIGNER,"signer":True},
            {"pubkey":wallet,"signer":True},
            {"pubkey":"6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF","signer":False},
            {"pubkey":"7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG","signer":False},
        ],"instructions":[
            {"programId":program},
            {"programId":"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
             "parsed":{"type":"transferChecked","info":{
                 "source":"6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF",
                 "mint":USDC,"amount":"6715734492"}}},
        ]}},
        "meta":{"err":None,"logMessages":["Program log: Instruction: Swap"],
                "innerInstructions":[],
                "preTokenBalances":[
                    bal(2,USDC,wallet,8000000000),
                    bal(3,focus.TWEETCRAFT_MINT,wallet,0),
                ],
                "postTokenBalances":[
                    bal(2,USDC,wallet,1284265508),
                    bal(3,focus.TWEETCRAFT_MINT,wallet,4732220716414),
                ]},
    }


def test_exact_root_signed_tweetcraft_candidate_stays_unconfirmed():
    tx=fake_swap()
    r=focus.summarize(tx)
    assert r["status"]=="ROOT_SIGNED_TWEETCRAFT_BUY_CANDIDATE_INSTRUCTION_REVIEW"
    assert r["signature"]==focus.BUY_SIGNATURE
    assert r["mint"]==focus.TWEETCRAFT_MINT
    assert r["usdc_out_raw"]=="-6715734492"
    assert r["tweetcraft_in_raw"]=="4732220716414"
    assert r["frank_signed"] is True
    assert r["fomo_cosigned"] is True
    assert r["routers_detected"]
    assert r["instruction_count"]==2
    assert len(r["log_matches_sample"])==1
    assert r["executable_buy_confirmed"] is False
    assert r["rpc_attempts"]==0
    assert r["production_db_writes"]==0
    assert r["signals_changed"] is False
    assert r["emails_sent"]==0
    assert r["transaction_sha256"]==audit.digest(tx)


@pytest.mark.parametrize("kind",["wrong_slot_time","wrong_amount","unsigned","not_fomo","failed","wrong_sig"])
def test_tweetcraft_evidence_regressions_fail_closed(kind):
    tx=fake_swap()
    sig=focus.BUY_SIGNATURE
    if kind=="wrong_slot_time":
        tx["blockTime"]=audit.END+1
    elif kind=="wrong_amount":
        tx["meta"]["postTokenBalances"][1]["uiTokenAmount"]["amount"]="4732220716413"
    elif kind=="unsigned":
        tx["transaction"]["message"]["accountKeys"][1]["signer"]=False
    elif kind=="not_fomo":
        tx["transaction"]["message"]["accountKeys"][0]["signer"]=False
    elif kind=="failed":
        tx["meta"]["err"]={"InstructionError":[0,"Custom"]}
    elif kind=="wrong_sig":
        sig="NotTheApprovedSignature"
    with pytest.raises((audit.ScanBlocked,ValueError)):
        focus.summarize(tx,signature=sig)
