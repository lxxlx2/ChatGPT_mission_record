#!/usr/bin/env python3
"""Original-owner WBNB event ledger; negative controls retained. No inferred PnL.

WBNB Deposit/Withdrawal events are emitted by wrapper/router, not guaranteed
wallet-level purchase cost or sell proceeds. Partial log response never zero.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
 "scope": ("bsc-meme-address-model-v1-p4c-postapprove4-wallets10-wbnb-event-query-scope-2026-10-16.json", "7576ae8dd73ae46169d7baa25b9073fa8042a2a7"),
 "a": ("bsc-meme-address-model-v1-p4c-postapprove-wbnb-events-partA-2026-10-16.json", "bc56999d827c130d4805863e208c08d65d31fedb"),
 "b": ("bsc-meme-address-model-v1-p4c-postapprove-wbnb-events-partB-2026-10-16.json", "947713ae87e1c73f82dd63062bc5d2be9b31af82"),
 "c": ("bsc-meme-address-model-v1-p4c-postapprove-wbnb-events-partC-2026-10-16.json", "286e72bc8e11780693fc2c8104180b6f7ff4e474"),
 "manifest": ("bsc-meme-address-model-v1-p4c-fiveowners-fourmajors-original14-pre-rpc-2026-10-16.json", "723de3bb9aad1fb916eb8b958173e633d8338796"),
 "bsource": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partB-2026-10-16.json", "94d8eca8b73a687f5a7e9dca424757c67fc8416e"),
 "csource": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partC-2026-10-16.json", "f1b8a739043de8e3763cfd96bc9025029ade63f4"),
 "ledger": ("bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json", "2a19dbd88c2971efff60a15894d952d0d05e64d9"),
}
OWNER_INDICES = [31, 38, 46, 44]
EXPECTED_COUNTS = [2, 3, 3, 2]
EXPECTED = {
 31: {"Deposit": 99000000000000000, "Withdrawal": 56494853670212508},
 38: {"Deposit": 1732500000000000000, "Withdrawal": 1694918377918343466},
 46: {"Deposit": 99000000000000000, "Withdrawal": None},
 44: {"Deposit": 0, "Withdrawal": 6078812899850782},
}

def ensure(cond, error):
    if not cond:
        raise ValueError(error)

def load(root=ROOT):
    docs={}
    for k,(n,sha) in PINS.items():
        raw=(Path(root)/n).read_bytes()
        digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        ensure(digest==sha,"GIT_SOURCE_BLOB_CHANGED:"+k)
        docs[k]=json.loads(raw)
    return docs

def classify(d):
    ensure(set(d)==set(PINS), "SOURCE_SET_MISSING")
    s=d["scope"]
    ensure(s["reviewed_parent_sha"]=="5ef6f7944cac0503ca0e5ccd7a5739edac6670c9"
           and "NOT a blind" in s["declared_query_scope"]
           and s["wBNB_ca"].lower()=="0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
           "EARLIER_PILOT_OR_WBNB_SCOPE_UNDISCLOSED")
    original=[e for e in d["manifest"]["cases"] if e["p2_index"] in OWNER_INDICES]
    ensure([e["p2_index"] for e in original]==OWNER_INDICES
           and [len(x["original_transactions"]) for x in original]==EXPECTED_COUNTS
           and [e["p2_index"] for e in s["original_txs"]]==OWNER_INDICES,
           "ORIGINAL_POSITIVE_NEGATIVE_COHORT_RESELECTED")
    ensure([d[x]["source_offsets"] for x in ("a","b","c")]==[[0,4],[4,8],[8,10]]
           and all(d[x]["source_scope_blob_sha"]==PINS["scope"][1] for x in ("a","b","c")),
           "ORIGINAL_10_QUERY_WINDOWS_NOT_COMPLETE")
    rows=d["a"]["cases"]+d["b"]["cases"]+d["c"]["cases"]
    need=s["original_txs"]
    original_rows=[(c,x) for c in need for x in c["original_txs"]]
    ensure(len(rows)==len(original_rows)==10,"ORIGINAL_10_QUERY_COUNT_CHANGED")
    extra_case=d["csource"]["cases"]
    extra_buy=next(x for x in extra_case if x["index"]==44 and x["block"]==121783426)
    ensure(extra_buy["tx_value_wei"]=="0" and extra_buy["tx_selector"]=="0x84da2c7b"
           and extra_buy["signer_match"],"ADFF_ZERO_NATIVE_INPUT_OR_UNKNOWN_ROUTE_FALSIFIED")
    result={}
    complete_requests=0
    partial_requests=0
    for idx in OWNER_INDICES:
        p2=d["ledger"]["episodes"][idx]
        scoped=next(x for x in need if x["p2_index"]==idx)
        ensure(scoped["owner"]==p2["wallet"] and scoped["exact_ca"]==p2["exact_ca"]
               and scoped["original_native_scope_sign"]==p2["net_classification"]
               and scoped["original_native_scope_wei"]==p2["net_native_BNB_wallet_event_blocks_wei"],
               "P2_ORIGINAL_OWNER_CA_OR_SOURCE_NATIVE_SIGN_CHANGED")
        result[idx]={"wallet":scoped["owner"],"token":p2["token"],"ca":p2["exact_ca"],
                     "original_native_scope_wei":p2["net_native_BNB_wallet_event_blocks_wei"],
                     "original_native_scope_sign":p2["net_classification"],
                     "wbnb_event_sums_wei":{"Deposit":0,"Withdrawal":0},
                     "full_per_event_type":{"Deposit":True,"Withdrawal":True}}
    for row,(case,orig) in zip(rows,original_rows):
        ensure(row["p2_index"]==case["p2_index"] and row["hash"]==orig["hash"]
               and row["block"]==orig["block"] and row["owner"]==case["owner"]
               and len(row["events"])==2
               and [e["type"] for e in row["events"]]==["Deposit","Withdrawal"],
               "ORIGINAL_SIGNER_EVENT_PAIR_SOURCE_CHANGED")
        for ev in row["events"]:
            kind=ev["type"]
            r=result[case["p2_index"]]
            if not ev["full_block_filter_reply"]:
                partial_requests+=1
                ensure(ev["selected_tx_events"] is None,"TRUNCATED_LOGS_MUST_NOT_GIVE_ZERO")
                r["full_per_event_type"][kind]=False
                continue
            complete_requests+=1
            ensure(isinstance(ev["selected_tx_events"],list),"SUCCESSFUL_LOG_QUERY_HAS_NULL")
            for item in ev["selected_tx_events"]:
                ensure(item["transactionHash"].lower()==row["hash"].lower()
                       and item["topics"][0].lower()==s["events"][kind].lower()
                       and int(item["data"],16)==int(item["amount_wei"])>=0,
                       "WRONG_TRANSACTION_TOPIC_OR_AMOUNT")
                r["wbnb_event_sums_wei"][kind]+=int(item["amount_wei"])
    ensure((complete_requests,partial_requests)==(19,1),"ALL_20_QUERY_COVERAGE_GRADE_DRIFT")
    ensure(result[46]["full_per_event_type"]=={"Deposit":True,"Withdrawal":False},
           "MISSING_2ADF_SECOND_EXIT_MUST_NOT_BE_CALLED_FULL")
    for idx in OWNER_INDICES:
        r=result[idx]
        for kind,v in EXPECTED[idx].items():
            if v is None:
                ensure(not r["full_per_event_type"][kind],"MISSING_WITHDRAWAL_FALSIFIED")
            else:
                ensure(r["wbnb_event_sums_wei"][kind]==v,"WBNB_ORIGINAL_GROSS_EVENT_SUM_DRIFT")
    ensure(result[44]["wbnb_event_sums_wei"]["Deposit"]==0
           and result[44]["original_native_scope_sign"]=="POSITIVE_NATIVE_SCOPE",
           "ADFF_ZERO_WRAP_ARRIVAL_CANNOT_IMPLY_ZERO_COST")
    return {"schema":"BSC_P4C_POSTAPPROVE_FOUR_OWNER_TEN_TX_WBNB_EVENT_SOURCE_REPLAY",
            "original_owners":4,"original_transactions":10,
            "positive_source_native_scope_owners":2,
            "negative_source_native_scope_owners":2,
            "complete_exact_block_event_queries":complete_requests,
            "truncated_exact_block_event_queries":partial_requests,
            "cases":{str(i):{**r, "wbnb_event_sums_wei":{
                k:str(v) if r["full_per_event_type"][k] else "UNRESOLVED_PARTIAL_LOG_QUERY"
                for k,v in r["wbnb_event_sums_wei"].items()},
                "quote_route_pnl":"UNRESOLVED"} for i,r in result.items()},
            "ADFF_positive_native_scope_quote_cost":"UNRESOLVED_ZERO_TX_MSG_VALUE_AND_NO_MATCHING_WBNB_DEPOSIT_DO_NOT_PROVE_FREE_BUY",
            "route_observation_grade":"WBNB_WRAPPER_EVENT_ONLY_NOT_WALLET_PNL",
            "repeat_trader_profitability":"UNRESOLVED",
            "public_executable_U":"UNRESOLVED","P4_C":"PARTIAL","P5":"BLOCKED",
            "PRODUCTION":"NO_GO"}

if __name__=="__main__":
    print(json.dumps(classify(load()),ensure_ascii=False,indent=2))
