#!/usr/bin/env python3
"""Frozen original 8E6B token4 external native transfer exclusivity audit."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-8e6b-token4-19external-precommit-2026-10-15.json","d93d67e5e5c3af951eea9eafbdb56a714291faea"),("bsc-meme-address-model-v1-p4c-8e6b-token4-19external-part1-2026-10-15.json","275fa8ee1711b4cc170eacefaa254056a16e25fe"),("bsc-meme-address-model-v1-p4c-8e6b-token4-19external-part2-2026-10-15.json","bfa8072cb0d98d6f1d90820ceb13aa44ef35a495"),("bsc-meme-address-model-v1-p4c-8e6b-token4-19external-part3-2026-10-15.json","11abc4d11f57e9da94fbf895f7418b10f8689b08"),("bsc-meme-address-model-v1-p4c-8e6b-token4-19external-part4-2026-10-15.json","90cc9ead57670a0e21dab1613fc151909a0bad6e"),("bsc-meme-address-model-v1-p4c-8e6b-token4-two-settled-source-audit-2026-10-15.json","1d085883201da6bbbf47185df60898c0ec8eead1"))
SCOPE="All 19 frozen original 8E6B token4 EOA signed owner swap blocks have independently confirmed exactly the one selected sender native external transfer, zero other externally originated incoming native BNB and zero pagination pending. This rules out external native block coactivity only. Internal traces, unrelated internal native credits or original 1/5/15min observer followability still not verified. Do not infer pool route fee beneficiary."
def require(v,s):
    if not v:raise ValueError(s)
def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    data=[]
    for filename,sha in PINS:
        raw=(root/filename).read_bytes()
        require(blob(raw)==sha,"original source SHA changed "+filename)
        data.append(json.loads(raw))
    return data
def build(data):
    require(len(data)==6,"19-block external audit requires precommit, four raw source parts, original prior economic source")
    pre,*sources,owner=data
    require(pre["schema"]=="BSC_P4C_8E6B_TOKEN4_ALL19_ORIGINAL_OWNER_EXTERNAL_BLOCK_EXCLUSIVITY_PRECOMMIT"
            and pre["network"]=="bnb-mainnet"
            and len(pre["rows"])==19
            and owner["schema"]=="BSC_P4C_8E6B_TOKEN4_TWO_SETTLED_OWNER_NATIVE_ROUNDS_19TX_FIVE_SPOT"
            and len(owner["original_transactions"])==19
            and [x["part"] for x in sources]==[1,2,3,4]
            and all(x["precommit_sha"]==PINS[0][1] for x in sources)
            and all(x.get("production",x.get("summary",{}).get("production"))=="NO_GO" for x in data),
            "original 19 token4 selected external native scope or source pins changed")
    raw=[row for s in sources for row in s["rows"]]
    require(len(raw)==19 and len({r["block"] for r in raw})==19,"missing or duplicated original owner block")
    output=[]
    for orig in pre["rows"]:
        rows=[r for r in raw if r["hash"]==orig["hash"]]
        economic=[r for r in owner["original_transactions"] if r["hash"]==orig["hash"]]
        require(len(rows)==len(economic)==1
                and rows[0]["block"]==economic[0]["block"]==orig["block"]
                and economic[0]["p2_index"]==orig["p2_index"]
                and economic[0]["original_signed_success"],
                "original owner EOA tx/block identity mismatched")
        d=rows[0]["directions"]
        require(len(d)==2 and [q["direction"] for q in d]==["OUT","IN"],
                "missing both original directions")
        out,incoming=d
        require(all(x["status"]=="COMPLETE" and x["page_key_present"] is False for x in d)
                and len(out["transfers"])==1 and len(incoming["transfers"])==0,
                "extra native original owner external activity or uncompleted pagination")
        tx=out["transfers"][0]
        require(tx["hash"].lower()==orig["hash"].lower()
                and tx["from"].lower()==pre["owner"].lower()
                and tx["asset"]=="BNB",
                "wrong original owner external transaction or BNB network asset")
        output.append({
            "hash":orig["hash"],"block":orig["block"],"p2_index":orig["p2_index"],
            "signed_owner_external_txs_in_block":1,
            "unrelated_external_native_outgoing":0,
            "other_external_native_deposits":0,
            "both_direction_read_complete":True,
            "original_source_owner_native_delta_wei":economic[0]["original_native_delta_wei"]
        })
    return {
      "schema":"BSC_P4C_8E6B_TOKEN4_ALL19_EXTERNAL_NATIVE_EOA_EXCLUSIVITY_VERIFIED",
      "scope":SCOPE,
      "source_manifest":[{"path":PREFIX+name,"git_blob_sha":blob} for name,blob in PINS],
      "summary":{"original_selected_tx_blocks":19,"all_original_owner_external_tx_block_proven":19,
          "owner_blocks_with_other_external_native_sender":0,
          "owner_blocks_with_external_native_inbound":0,
          "provider_truncated_or_pagekey":0,
          "internal_native_trace_status":"UNRESOLVED",
          "public_executable_U":"UNRESOLVED",
          "followable_signals":0,"production":"NO_GO"},
      "rows":output
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
