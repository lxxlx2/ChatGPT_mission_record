#!/usr/bin/env python3
"""P4-C owner signature provenance for frozen 239E Dragon + 877AF MARSCOIN.

Strictly owner-signed original 2026 tx evidence; BLOCK-SCOPE only, not PnL.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PINS=(
 ("bsc-meme-address-model-v1-p4c-next239e877af-balanced-four-rounds-precommit-2026-10-15.json","d3c22d013c5815a11839ef179abae575cc4c161a"),
 ("bsc-meme-address-model-v1-p4c-next239e877af-original-tx-part1-2026-10-15.json","ab999acb1540dfe67c7cdfac67e1ef92a4fe3860"),
 ("bsc-meme-address-model-v1-p4c-next239e877af-original-tx-part2-2026-10-15.json","284f63c722f66b6f83b95f42f440b4e1cf49ae33")
)
PREFIX="crypto-300-profit-mission/research/"
def require(x,msg):
    if not x:raise ValueError(msg)
def blob_sha(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def load(root=ROOT):
    a=[]
    for name,sha in PINS:
        b=(root/name).read_bytes()
        require(blob_sha(b)==sha,"immutable source changed: "+name)
        a.append(json.loads(b))
    return a
def build(d):
    require(len(d)==3,"source proof must include original precommit + 2 original tx readbacks")
    pre,first,second=d
    require(pre["schema"]=="BSC_P4C_P2_CROSSWALLET_NEXT_FOUR_ORIGINAL_BALANCED_CYCLE_PRECOMMIT_V1"
            and pre["summary"]["frozen_original_23_wallets"]==23
            and pre["summary"]["frozen_exact_CA_count"]==19
            and pre["summary"]["source_preselected_original_owner_tx_count"]==11
            and len(pre["rounds"])==4 and
            pre["summary"]["native_scope_positive_controls"]==2 and
            pre["summary"]["native_scope_negative_controls"]==2
            and first["part"]==1 and second["part"]==2
            and first["precommit_git_blob_sha"]==second["precommit_git_blob_sha"]==PINS[0][1]
            and pre["summary"]["production"]==first["production"]==second["production"]=="NO_GO",
            "precommitted 2026 original signed P2 balanced cohort invalid")
    raw=first["rows"]+second["rows"]
    require(len(raw)==11,"all selected 11 owner signatures must be accounted for")
    rounds=[]
    for v in pre["rounds"]:
        selected=v["original_preselected_signed_txs"]
        require(v["source_grade"]=="SIGNED_NATIVE_BLOCK_SCOPE" and
                v["independent_cashflow_status"]=="UNVERIFIED_QUOTE_AND_GAS"
                and v["origin_visible_U"]=="UNRESOLVED" and len(selected) in (2,3),
                "only source-native-scope selected rounds allowed")
        tx=[]
        for row in selected:
            matches=[x for x in raw if x["precommitted"]["hash"]==row["hash"]]
            require(len(matches)==1,"missing or duplicated precommitted signer transaction")
            source=matches[0]
            rpc=source["rpc"]
            require(source["status"]=="OWNER_SIGNED_CHAIN56"
                    and source["precommitted"]["round"]==v["token"]+"/"+str(v["original_episode_number"])
                    and source["precommitted"]["block"]==row["block"]
                    and source["precommitted"]["owner"]==v["owner"]
                    and source["precommitted"]["ca"]==v["exact_ca"]
                    and rpc["hash"]==row["hash"]
                    and rpc["from"]==v["owner"]
                    and int(rpc["blockNumber"],16)==row["block"]
                    and int(rpc["chainId"],16)==56,
                    "original signer/chain/tx identity not proven")
            tx.append({"hash":row["hash"],"block":row["block"],"chain_id":56,"EOA_from":v["owner"],
                       "signed_value_wei":str(int(rpc["value"],16)),"rpc_signed_original_complete":True})
        rounds.append({"P2_ledger_index":v["p2_ledger_index"],"owner":v["owner"],"token":v["token"],
                       "exact_ca":v["exact_ca"],"episode":v["original_episode_number"],
                       "original_signed_transactions":tx,"all_signed_hash_identity_confirmed":True,
                       "net_native_block_scope_wei":v["source_native_block_scope_wei"],
                       "native_block_scope_sign":v["source_native_block_scope_sign"],
                       "actual_original_quote_Gas_full_PnL":"UNRESOLVED",
                       "follower_1_5_15_min":"UNRESOLVED"})
    require([v["P2_ledger_index"] for v in rounds]==[29,30,37,38]
            and len({x["owner"] for x in rounds})==2
            and len({x["exact_ca"] for x in rounds})==2
            and sum(r["native_block_scope_sign"]=="POSITIVE_NATIVE_SCOPE" for r in rounds)==2
            and sum(r["native_block_scope_sign"]=="NEGATIVE_NATIVE_SCOPE" for r in rounds)==2,
            "fixed 2026 owner/token positive-negative challenge balance changed")
    return {"schema":"BSC_P4C_BALANCED_239E_877AF_FOUR_ORIGINAL_ROUNDS_SIGNER_READBACK",
            "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
            "summary":{"wallets":2,"tokens":2,"rounds":4,"original_signed_txs":11,
                       "owner_verified_bnb_chain56_txs":11,"original_native_block_scope_positive":2,
                       "original_native_block_scope_negative":2,"profit_rounds_newly_source_qualified":0,
                       "observer_followable_opportunity_U":"UNRESOLVED","production":"NO_GO"},
            "rounds":rounds}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
