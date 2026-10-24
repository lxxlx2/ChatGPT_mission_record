#!/usr/bin/env python3
"""Real eight signed Dragon sells, five-sale full exit, actual USDT receipts and BNB fees.

P4-B research only. This proves a genuine wallet liquidation after 239E exit,
not a profitable 1,000 USDT standalone position or a causal follow signal.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCES={
    "buy":("bsc-meme-address-model-v1-p4b-239e-r2-external-5e60-real-usdt-debit-gas-and-dragon-readback-2026-10-18.json","4288f9819f2815cb4d899c93116b23e19e6fe0ba"),
    "out":("bsc-meme-address-model-v1-p4b-5e60-eight-real-post-239e-exit-dragon-outbound-transfers-2026-10-18.json","b08b3cf9d7cbd81829281d7fec6cba65258db23a"),
    "sells":("bsc-meme-address-model-v1-p4b-5e60-eight-real-signed-usdt-sells-and-five-full-exit-2026-10-18.json","902871db18ac42d98647ce43d61438e8e32b7947"),
    "fees":("bsc-meme-address-model-v1-p4b-5e60-eight-real-sell-success-receipts-and-gas-readback-2026-10-18.json","97ea488293a5d031837086a5dfe122f89e83cad8"),
    "censored":("bsc-meme-address-model-v1-p4b-5e60-earlier-ten-inbound-dragon-cost-basis-censored-2026-10-18.json","cee0c1be380f9509d5c30b73cc64d1350ad66c87"),
}
def require(ok,code):
    if not ok:
        raise ValueError("P4B_5E60_FIRST_CLOSED_LIQUIDATION_"+code)

def load(root=ROOT):
    docs={}
    for k,(name,pin) in SOURCES.items():
        buf=(root/name).read_bytes()
        sha=hashlib.sha1(b"blob "+str(len(buf)).encode()+b"\0"+buf).hexdigest()
        require(sha==pin,"SOURCE_GIT_BLOB_"+k)
        docs[k]=json.loads(buf)
    return docs

def build(d):
    buy,out,sales,fees,censored=(d[k] for k in ("buy","out","sells","fees","censored"))
    owner="0x5e600e259e3cff0757e3736223685958665866c6"
    Dragon="0xeccbb861c0dda7efd964010085488b69317e4444"
    WBNB="0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
    USDT="0x55d398326f99059ff775485246999027b3197955"
    PAIR="0x22af7297243c4eef12e2d5a4f888b92e56bf127c"
    ROUTER="0x10ed43c718714eb63d5aa57b78b54704e256024e"
    require(out["source_prefreeze"]["git_blob"]=="7bbd14b61b0c28c86886ccb4738854bd6ac8e5e9" and
            out["source_owner_239e_signed_exit_block"]==85961371 and
            len(out["transfers"])==8 and
            out["response_total_returned"]==8 and
            out["has_page_key"] is False and
            sales["precommit_sha"]=="5410e8219be426037edf25376a3872b608c4b1ba" and
            sales["bounded_calls"]=={"max":13,"actual":13,"retries":0} and
            len(sales["rows"])==len(fees["rows"])==8 and
            fees["actual_queries"]==8 and fees["retries"]==0,
            "FROZEN_SOURCE_QUERY_SCOPE")
    require(buy["signer"]==owner and
            buy["signed_Router_decoded"]["amountIn_USDT_raw"]=="1000000000000000000000" and
            buy["receipt"]["computed_buy_fee_wei"]=="78316000000000" and
            buy["external_wallet_dragon_state"]["before_buy_raw"]==
                 "335173813691889308361853" and
            buy["external_wallet_dragon_state"]["at_original_239e_final_sell_raw"]==
                 "383628517870200760487354",
            "REAL_PREEXISTING_DRAGON_AND_1000_USDT_BUY")
    require(censored["returned_count"]==10 and
            len(censored["rows"])==10 and
            censored["pageKey_exists"] is True and
            censored["complete_full_window"] is False and
            len(censored["page_key_preserved"])>0,
            "COST_BASIS_INCOMPLETE_MUST_NOT_BE_PROFIT")
    sale_summary=[]
    for i,(transfer,sell,fee) in enumerate(zip(out["transfers"],sales["rows"],fees["rows"])):
        require(sell["rank"]==fee["rank"]==transfer["selected_order"]==i+1 and
                sell["tx"]==fee["tx"]==transfer["hash"] and
                sell["block"]==fee["block"]==transfer["block_dec"] and
                sell["block"]>85961371 and
                sell["signer"]==owner and sell["signed_router"]==ROUTER and
                transfer["from"]==owner and transfer["to"]==PAIR and
                sell["signed_router_selector"]=="0x5c11d795" and
                sell["signed_router_method"]=="swapExactTokensForTokensSupportingFeeOnTransferTokens" and
                sell["signed_router_path"]==[Dragon,WBNB,USDT] and
                sell["original_tx_fully_parseable"] is True and
                sell["original_tx_legacy_type0"] is True,
                "ALL_EIGHT_SAME_REAL_SIGNED_ROUTER_SELL_PATH")
        amount=int(sell["actual_signed_Dragon_sold_raw"])
        usdt=int(sell["actual_USDT_received_raw"])
        gas=int(fee["gasUsed_units"])
        price=int(sell["signed_gasPrice_wei"])
        require(amount>0 and usdt>0 and
                amount==int(transfer["raw_uint256"]) and
                amount==int(transfer["raw_hex"],16) and
                fee["status"]=="0x1" and
                fee["receipt_full_JSON_parseable"] is True and
                fee["effectiveGasPrice_wei"]==sell["signed_gasPrice_wei"]=="500000000" and
                fee["gasUsed_units"]==str(int(fee["gasUsed_hex"],16)) and
                fee["realized_sell_Gas_fee_wei"]==str(gas*price),
                "ACTUAL_TRANSACTION_SUCCESS_GAS_AND_ERC20_SELL_QUANTITY")
        payment=sell["selected_full_USDT_Transfer"]
        require(payment["transactionHash"]==sell["tx"] and
                payment["blockNumber"]==hex(sell["block"]) and
                payment["transactionIndex"]==fee["transactionIndex"] and
                payment["address"]==USDT and
                payment["topic_to"]=="0x"+"0"*24+owner[2:] and
                int(payment["data"],16)==usdt,
                "SAME_SIGNED_SELL_REAL_USDT_CREDIT_NOT_ROUTER_MIN_OUT")
        sale_summary.append({"sell_number":i+1,"block":sell["block"],
              "hash":sell["tx"],"sold_Dragon_raw":str(amount),
              "real_USDT_receipt_raw":str(usdt),
              "actual_gas_used":str(gas),"actual_BNB_gas_fee_wei":str(gas*price)})
    check=sales["checkpoints"]
    require(set(check)=={"before_first_sell_Dragon_raw","after_fifth_sell_Dragon_raw",
        "after_eighth_sell_Dragon_raw","before_first_sell_USDT_raw","after_fifth_sell_USDT_raw"},
        "FIVE_EXACT_HISTORY_CHECKPOINTS")
    require(all(isinstance(v,str) and v.isdigit() for v in check.values()),
        "FIVE_CHECKPOINTS_NONNEGATIVE_RAW_UINT256")
    starting=int(check["before_first_sell_Dragon_raw"])
    final=int(check["after_fifth_sell_Dragon_raw"])
    actual_out=sum(int(x["sold_Dragon_raw"]) for x in sale_summary[:5])
    received=sum(int(x["real_USDT_receipt_raw"]) for x in sale_summary[:5])
    actual_balance_diff=(int(check["after_fifth_sell_USDT_raw"])-
                         int(check["before_first_sell_USDT_raw"]))
    require(starting==actual_out==383628517870200760487354 and final==0 and
            check["after_eighth_sell_Dragon_raw"]=="0" and
            actual_balance_diff==received==8399620126582833083485 and
            sales["first_five"]["Dragon_sold_raw"]==str(actual_out) and
            sales["first_five"]["USDT_received_raw"]==
                 sales["first_five"]["wallet_USDT_actual_increase_raw"]==
                 str(received),
            "FIRST_FIVE_FULL_REAL_LIQUIDATION_AND_USDT_WALLET_CREDIT")
    firstfee=sum(int(x["actual_BNB_gas_fee_wei"]) for x in sale_summary[:5])
    laterfee=sum(int(x["actual_BNB_gas_fee_wei"]) for x in sale_summary[5:])
    require(firstfee==370354000000000 and
            laterfee==229642000000000 and
            fees["first_five"]["total_fee_wei"]==str(firstfee) and
            fees["later_three"]["total_fee_wei"]==str(laterfee) and
            sales["second_three"]["USDT_received_raw"]==
                 str(sum(int(x["real_USDT_receipt_raw"]) for x in sale_summary[5:]))==
                 "13540757456188781829802",
            "EIGHT_FEES_AND_SEPARATE_LATER_ROUND_ACCOUNTING")
    require(buy["verification"]["actual_follower_net_return"]=="UNRESOLVED" and
            fees["limitations"][2].startswith("First five sell original wallet-held") and
            sales["gates"]["P5"]==fees["gates"]["P5"]=="BLOCKED",
            "NO_FALSE_CAUSAL_1000USDT_PROFIT")
    return {
      "schema":"BSC_P4B_2026_REAL_EXTERNAL_FIVE_TRADE_LIQUIDATION_USDT_CASHIN_AND_COST_BASIS_UNKNOWN",
      "pinned_blobs":{k:v[1] for k,v in SOURCES.items()},
      "signer":owner,"original_owner_239e_last_signed_sell_block":85961371,
      "first_five_real_signed_sales":sale_summary[:5],
      "first_five_all_Dragon_sold_raw":str(actual_out),
      "first_five_actual_USDT_received_raw":str(received),
      "first_five_independent_USDT_wallet_balance_increase_raw":str(actual_balance_diff),
      "first_five_realized_USDT_cash_in_not_profit":True,
      "first_five_true_zero_Dragon_wallet_balance_after_fifth":True,
      "first_five_actual_BNB_sell_gas_fee_wei":str(firstfee),
      "earlier_real_buy_USDT_input_raw":"1000000000000000000000",
      "earlier_real_buy_BNB_gas_wei":"78316000000000",
      "legacy_335173_Dragon_purchase_cost_basis":"UNRESOLVED_PAGINATED_PRIOR_10_OR_MORE_RECEIPTS",
      "later_three_signed_USDT_sales":sale_summary[5:],
      "later_three_actual_USDT_received_raw":"13540757456188781829802",
      "later_three_realized_USDT_PNL":"UNRESOLVED_COST_BASIS",
      "public_observer_causality":"UNRESOLVED",
      "fixed_delay_1_5_15min_follower_return":"UNRESOLVED",
      "PUBLIC_EXECUTABLE_U":"UNRESOLVED",
      "P4_B":"PARTIAL","P5":"BLOCKED","PRODUCTION":"NO_GO"
    }

if __name__=="__main__":
    print(json.dumps(build(load()),indent=2,sort_keys=True))
