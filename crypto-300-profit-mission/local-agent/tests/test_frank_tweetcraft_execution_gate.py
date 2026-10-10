"""Synthetic, strictly offline Meteora DLMM swap2 semantics regression cases."""

import pytest

from mission_agent.meme.fomo_crosschain import FOMO_COSIGNER, USDC
from scripts import audit_frank_native_resume as audit
from scripts import audit_frank_tweetcraft_instruction_offline as base
from scripts import audit_frank_tweetcraft_execution_gate as gate

ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ROOT=audit.WALLET


def b58encode(data):
    value=int.from_bytes(data,"big")
    chars=""
    while value:
        value,i=divmod(value,58)
        chars=ALPHABET[i]+chars
    return "1"*(len(data)-len(data.lstrip(bytes([0]))))+chars


def balance(idx,mint,owner,amount):
    return {"accountIndex":idx,"mint":mint,"owner":owner,
            "uiTokenAmount":{"amount":str(amount),"decimals":6}}


def transfer(program,source,dest,authority,amount,mint=None):
    info={"source":source,"destination":dest,"authority":authority}
    if mint is None:
        info["amount"]=str(amount)
        ix="transfer"
    else:
        info["mint"]=mint
        info["tokenAmount"]={"amount":str(amount),"decimals":6}
        ix="transferChecked"
    return {"programId":program,"parsed":{"type":ix,"info":info}}


def fixture():
    keys=[
        {"pubkey":FOMO_COSIGNER,"signer":True},
        {"pubkey":ROOT,"signer":True},
        {"pubkey":gate.ROOT_USDC_ATA,"signer":False},
        {"pubkey":gate.ROOT_TWEET_ATA,"signer":False},
        {"pubkey":gate.DFLOW,"signer":False},
        {"pubkey":gate.DLMM,"signer":False},
        {"pubkey":gate.BISONFI,"signer":False},
    ]
    raw=gate.SWAP2_DISCRIMINATOR+bytes(16)
    logs=[
        f"Program {gate.DFLOW} invoke [1]",
        "Program log: Instruction: Swap",
        f"Program {gate.BISONFI} invoke [2]",
        "Program log: Instruction: Buy",
        f"Program {gate.BISONFI} success",
        f"Program {gate.DLMM} invoke [2]",
        "Program log: Instruction: Swap2",
        f"Program {gate.DLMM} success",
        f"Program {gate.DFLOW} success",
    ]
    spl="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    token="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
    rows=[
        transfer(spl,gate.ROOT_USDC_ATA,"RECEIVER1",ROOT,15110402,USDC),
        transfer(spl,gate.ROOT_USDC_ATA,"RECEIVER2",ROOT,12088322,USDC),
        transfer(spl,gate.ROOT_USDC_ATA,"RECEIVER3",ROOT,2006560),
        transfer(spl,gate.ROOT_USDC_ATA,"ROUTEPOOL",ROOT,6686529208),
        transfer(token,"POOL1",gate.ROOT_TWEET_ATA,"POOLAUTH1",3508980043008,base.TWEETCRAFT_MINT),
        transfer(token,"POOL2",gate.ROOT_TWEET_ATA,"POOLAUTH2",1223240673406,base.TWEETCRAFT_MINT),
        {"programId":gate.DLMM,"data":b58encode(raw)},
    ]
    return {
        "slot":454400785,"blockTime":1791423976,
        "transaction":{"message":{"accountKeys":keys,
            "instructions":[{"programId":gate.DFLOW}]}},
        "meta":{"err":None,"logMessages":logs,
            "innerInstructions":[{"index":0,"instructions":rows}],
            "preTokenBalances":[
                balance(2,USDC,ROOT,7000000000),
                balance(3,base.TWEETCRAFT_MINT,ROOT,0),
            ],
            "postTokenBalances":[
                balance(2,USDC,ROOT,284265508),
                balance(3,base.TWEETCRAFT_MINT,ROOT,4732220716414),
            ]}
    }


def test_confirmed_onchain_buy_requires_exact_instruction_and_full_flow_match():
    tx=fixture()
    result=gate.gate(tx)
    assert result["status"]=="CONFIRMED_ROOT_AUTHORIZED_DEX_BUY_EVIDENCE"
    assert result["onchain_buy_evidence_confirmed"] is True
    assert result["buy_log_bound_to_program"] is True
    assert result["meteora_swap2_log_bound"] is True
    assert result["dlmm_discriminator"]["swap2_discriminator_matched"] is True
    assert result["log_program_bindings"]["status"]=="VALID"
    assert result["usdc_outbound_raw_total"]=="6715734492"
    assert result["other_outbound_usdc_raw"]=="29205284"
    assert result["target_inbound_raw_total"]=="4732220716414"
    assert result["execution_buy_not_person_pattern"] is True
    assert result["rpc_attempts"]==0
    assert result["signals_changed"] is False
    assert result["emails_sent"]==0


@pytest.mark.parametrize("mut",["wrong_discriminator","wrong_program","missing_swap2_log",
                                "wrong_ata_amount","invalid_stack","no_logs"])
def test_unverified_execution_never_upgrades(mut):
    tx=fixture()
    if mut=="wrong_discriminator":
        tx["meta"]["innerInstructions"][0]["instructions"][-1]["data"]="111111111"
    elif mut=="wrong_program":
        tx["meta"]["innerInstructions"][0]["instructions"][-1]["programId"]=gate.BISONFI
    elif mut=="missing_swap2_log":
        tx["meta"]["logMessages"]=[x for x in tx["meta"]["logMessages"]
                                      if x!="Program log: Instruction: Swap2"]
    elif mut=="wrong_ata_amount":
        tx["meta"]["innerInstructions"][0]["instructions"][1]["parsed"]["info"]["tokenAmount"]["amount"]="12088323"
    elif mut=="invalid_stack":
        tx["meta"]["logMessages"][5]=f"Program {gate.DLMM} invoke [3]"
    elif mut=="no_logs":
        tx["meta"]["logMessages"]=[]
    result=gate.gate(tx)
    assert result["status"]=="EXECUTION_BINDING_INCOMPLETE"
    assert result["onchain_buy_evidence_confirmed"] is False
    assert result["rpc_attempts"]==0


def test_prior_balance_or_signer_mismatch_fails_closed():
    tx=fixture()
    tx["transaction"]["message"]["accountKeys"][1]["signer"]=False
    with pytest.raises(audit.ScanBlocked,match="BUY_TX_EVIDENCE_DIFFERS_FROM_PRIOR_ROOT_AUDIT"):
        gate.gate(tx)
