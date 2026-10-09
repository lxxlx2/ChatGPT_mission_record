"""Frank root signed purchase / relay payment retrospective: no RPC."""
from scripts import audit_frank_root_execution_focus as focus
from mission_agent.meme.fomo_crosschain import FOMO_COSIGNER, USDC, SOL_ROUTERS

ROOT="498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
TOKEN="7Xgc5RacHtGzfhw2HukUBk5V986yBbvshr7rrCoopump"
OTHER="6HEFmhrdC8KxY4e4C5eg4nmaQNRGyMAcwuMEeMpJTGV7"


def bal(idx,mint,owner,raw,decimals=6):
    return {"accountIndex":idx,"mint":mint,"owner":owner,
            "uiTokenAmount":{"amount":str(raw),"decimals":decimals}}


def txn(time,quote_from,quote_to,token_from,token_to,router=False):
    return {
        "slot":4400+time,"blockTime":time,
        "transaction":{"message":{
            "accountKeys":[
                {"pubkey":ROOT,"signer":True},
                {"pubkey":FOMO_COSIGNER,"signer":True},
                {"pubkey":OTHER,"signer":False},
            ],
            "instructions":[{
                "programId":next(iter(SOL_ROUTERS)) if router else
                            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            }],
        }},
        "meta":{"err":None,
            "preTokenBalances":[
                bal(0,USDC,ROOT,quote_from),
                bal(1,TOKEN,ROOT,token_from),
                bal(2,USDC,OTHER,0),
            ],
            "postTokenBalances":[
                bal(0,USDC,ROOT,quote_to),
                bal(1,TOKEN,ROOT,token_to),
                bal(2,USDC,OTHER,quote_from-quote_to),
            ],
            "innerInstructions":[]},
    }


def test_root_outflow_without_target_acquisition_never_invent_buy():
    tx=txn(1800000001,7000000000,2000000000,0,0,router=False)
    report=focus.summarize({"signature-paid":tx},ROOT)
    assert report["rpc_attempts"]==0
    assert report["candidate_count"]==1
    case=report["candidate_sample"][0]
    assert case["root_signed"] is True
    assert case["usdc_out_raw"]=="-5000000000"
    assert case["target_in_mints"]==[]
    assert case["trade_confirmed"] is False
    assert case["category"]=="TOKEN_MOVEMENT"
    assert report["trade_coverage_complete"] is False


def test_root_cosigned_router_swap_candidate_contains_exact_token_mint_but_unconfirmed():
    tx=txn(1800000002,8000000,5000000,0,100000,router=True)
    report=focus.summarize({"signature-buy":tx},ROOT)
    assert report["candidate_count"]==1
    r=report["candidate_sample"][0]
    assert r["category"]=="SWAP_CANDIDATE"
    assert r["root_signed"] is True
    assert r["fomo_cosigned"] is True
    assert r["usdc_out_raw"]=="-3000000"
    assert r["target_in_mints"]==[
        {"mint":TOKEN,"raw":"100000","decimals":6}]
    assert r["trade_confirmed"] is False
    assert report["emails_sent"]==0
    assert report["production_db_writes"]==0
    assert report["signals_changed"] is False


def test_unsigned_deposit_not_reported_as_person_trade():
    tx=txn(1800000003,0,10000,0,0,router=False)
    tx["transaction"]["message"]["accountKeys"][0]["signer"]=False
    result=focus.summarize({"signature-credit":tx},ROOT)
    assert result["candidate_count"]==0
    assert result["root_signed_count"]==0
    assert result["category_counts"]["TOKEN_MOVEMENT"]==1
