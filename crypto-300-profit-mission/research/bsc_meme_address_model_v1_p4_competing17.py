#!/usr/bin/env python3
"""P4: reproduce all 17 frozen historically-active competing pool first active moments.

No hindsight wallet alpha, sellability, tax, route capacity, first whole-market venue,
or permission for production. All numbers are immutable source-pinned onchain evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

from bsc_meme_address_model_v1_p4_competing_first4 import build as build_four, load as load_four

ROOT = Path(__file__).resolve().parent
PREFIX = "crypto-300-profit-mission/research/"
PINS = (
    ("bsc-meme-address-model-v1-p4-priority4-competing-first-active-2026-10-14.json",
     "256c942d65a200b22533b402d7f6145606c94ba1"),
    ("bsc-meme-address-model-v1-p4-competing13-exact-creation-events-2026-10-14.json",
     "64847abe3207794defdf10dcc42f89939fc27339"),
    ("bsc-meme-address-model-v1-p4-competing13-creation-state-part1-2026-10-14.json",
     "c02d002d4ebf30eea9ced2daa5088954652a2fbe"),
    ("bsc-meme-address-model-v1-p4-competing13-creation-state-part2-2026-10-14.json",
     "cee6181d4b58d5062c9eb6d8e04da4837e18b807"),
    ("bsc-meme-address-model-v1-p4-competing13-creation-state-part3-2026-10-14.json",
     "65f03a0480cb4b99b79cef62942dbeb49a552e91"),
    ("bsc-meme-address-model-v1-p4-bulla-v3-usdt-10000-delayed-active-proof-2026-10-14.json",
     "41366fc5959d4bd227826aec8101229eb02e1bd1"),
    ("bsc-meme-address-model-v1-p4-niulai-v3-10000-delayed-active-proof-2026-10-14.json",
     "7a5e74b5fa653b7e2a51f1f86e2200510c8a5c88"),
)
FACTORY_V2 = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
FACTORY_V3 = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
V2_SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
V2_MINT = "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
V3_INIT = "0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"
V3_MINT = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
V3_PANCAKE_SWAP = "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83"
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
USDT = "0x55d398326f99059ff775485246999027b3197955"

def check(test, why):
    if not test:
        raise ValueError(why)

def git_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def load(root=ROOT):
    records = []
    for name, sha in PINS:
        raw = (root / name).read_bytes()
        check(git_sha(raw) == sha, "source blob drift: " + name)
        records.append(json.loads(raw))
    return records

def word(data, index):
    check(isinstance(data, str) and data.startswith("0x") and len(data) >= 2 + 64*(index+1),
          "truncated onchain uint word")
    return int(data[2+64*index:2+64*(index+1)], 16)

def verify_factory(log, row):
    check(log["address"].lower() == row["original_factory_event"]["address"].lower(),
          "creation factory identity mismatch")
    check(log["topics"][0] == (FACTORY_V2 if row["protocol"] == "V2" else FACTORY_V3),
          "incorrect factory event type")
    check(int(log["blockNumber"], 16) == row["creation_block"],
          "wrong creation block")
    check(log["transactionHash"].lower() == row["factory_creation_tx"].lower(),
          "wrong factory transaction")
    quote = USDT if row["quote"] == "USDT" else WBNB
    ordered = sorted((row["CA"].lower(), quote.lower()))
    check([t[-40:].lower() for t in log["topics"][1:3]] ==
          [x[2:] for x in ordered], "different CA / quote")
    check(("0x" + log["data"][26:66] if row["protocol"] == "V2"
          else "0x" + log["data"][-40:]).lower() == row["pool"].lower(),
          "factory event pool mismatch")
    if row["protocol"] == "V3":
        check(int(log["topics"][3], 16) == row["fee_pips"],
              "V3 fee mismatch")

def verify_bulla(doc, row):
    b = row["creation_block"]
    check(doc["schema"] == "BSC_P4_BULLA_V3_USDT_10000_FIRST_ACTIVE_LIQUIDITY_PROOF"
          and doc["source_creation_part3_git_blob_sha"] == PINS[4][1]
          and doc["source_creation_events_git_blob_sha"] == PINS[1][1]
          and doc["pool"] == row["pool"] and doc["creation_block"] == b
          and doc["first_active_block"] == b + 10 and doc["delay_blocks"] == 10
          and doc["production"] == "NO_GO", "BULLA delayed source scope mismatch")
    win = doc["full_unfiltered_event_window"]
    events = win["events"]
    check(win["result_complete"] is True and win["from"] == b+1 and win["to"] == b+10
          and win["pool"] == row["pool"] and len(events) == 1
          and events[0] == doc["first_active_event"]
          and int(events[0]["blockNumber"], 16) == b+10
          and events[0]["address"].lower() == row["pool"]
          and events[0]["topics"][0] == V3_PANCAKE_SWAP,
          "BULLA first event must be genuine Pancake V3 Swap, not Mint")
    states = doc["liquidity_raw_states"]
    check([s["block"] for s in states] == [b, b+9, b+10]
          and int(states[0]["result"], 16) == int(states[1]["result"], 16) == 0
          and int(states[2]["result"], 16) > 0
          and word(events[0]["data"], 3) == int(states[2]["result"], 16)
          and str(word(events[0]["data"], 3)) == doc["first_active_Swap_post_trade_liquidity_raw"],
          "BULLA delayed activity historical state not closed")
    return b+10, "V3_FIRST_ACTIVE_ON_PANCAKE_SWAP_AFTER_10_BLOCKS"

def verify_niulai(doc, row):
    b = row["pool_creation_block"]
    check(doc["pool"] == row["pool"] and doc["pool_creation_block"] == b
          and doc["first_active_block"] == b+17 and doc["production"] == "NO_GO",
          "NIULAI delayed origin mismatch")
    windows = doc["windows"]
    check(len(windows) == 10 and all(w["state"] == "COMPLETE" for w in windows),
          "NIULAI historical windows incomplete")
    observed = []
    for i,w in enumerate(windows):
        check(w["lo"] == b+1+10*i and w["hi"] == b+10+10*i, "NIULAI window gap")
        observed.extend(w["logs"])
    check(bool(observed) and observed[0] == doc["first_mint_event"]
          and int(observed[0]["blockNumber"],16) == b+17
          and observed[0]["topics"][0] == V3_PANCAKE_SWAP
          and all(x["topics"][0] == V3_PANCAKE_SWAP for x in observed),
          "NIULAI source is Pancake V3 SWAP, not Mint")
    states = doc["historical_state"]
    check([x["block"] for x in states] == [b,b+16,b+17]
          and int(states[0]["liquidity_raw"],16) == int(states[1]["liquidity_raw"],16) == 0
          and int(states[2]["liquidity_raw"],16)>0,
          "NIULAI first positive historical state missing")
    return b+17, "V3_FIRST_ACTIVE_ON_PANCAKE_SWAP_AFTER_17_BLOCKS"

def build(data, root=ROOT):
    check(len(data) == len(PINS), "missing pinned inputs")
    four, events13, p1, p2, p3, bulla, niulai = data
    check(four["summary"]["first_active_block_evidence"] == 4
          and four["summary"]["production"] == "NO_GO"
          and four == build_four(load_four(root)), "prior 4-pool replay drift")
    check(events13["schema"] == "BSC_P4_COMPETING_REMAINING13_INDEXED_FACTORY_CREATION_EVENTS"
          and len(events13["events"]) == 13 and events13["production"] == "NO_GO",
          "13 factory evidence source drift")
    source_rows = p1["records"] + p2["records"] + p3["records"]
    check(len(source_rows) == 13 and len({x["pool"] for x in source_rows}) == 13,
          "13 raw pool states incomplete/duplicate")
    check([x["index"] for x in source_rows] == list(range(12)) + [16],
          "13 frozen pools changed")
    for src,part,span in ((p1,1,[0,4]),(p2,2,[5,8]),(p3,3,[9,12])):
        check(src["source_creation_event_git_blob_sha"] == PINS[1][1]
              and src["part"] == part and src["range"] == span
              and src["production"] == "NO_GO", "creation batch provenance drift")
    result = []
    for item, entry in zip(source_rows, events13["events"]):
        check(item["pool"] == entry["pool"] and item["index"] == entry["index"]
              and item["creation_block"] == entry["creation_block"]
              and item["token"] == entry["token"]
              and item["factory_creation_tx"] == entry["original_factory_event"]["transactionHash"]
              and item["protocol"] == entry["protocol"], "13 pool source identity mismatch")
        ref = dict(item)
        if "CA" not in ref:
            ref["CA"] = entry["CA"]
            ref["quote"] = entry["quote"]
            ref["fee_pips"] = entry["fee_pips"]
            ref["original_factory_event"] = entry["original_factory_event"]
        check(ref["CA"] == entry["CA"] and ref["quote"] == entry["quote"]
              and ref["fee_pips"] == entry["fee_pips"], "exact token or route modified")
        verify_factory(entry["original_factory_event"],ref)
        logs = (item.get("original_same_creation_tx_events")
                or item.get("filtered_original_creation_events") or [])
        check(bool(logs)
              and all(int(e["blockNumber"],16) == item["creation_block"]
                      and e["address"].lower() == item["pool"].lower()
                      for e in logs), "creation log wrong block or pool")
        # End-of-block records may also contain later distinct same-block swaps/Sync.
        # The creation liquidity proof must only consume events from the factory tx.
        logs = [e for e in logs
                if e["transactionHash"] == item["factory_creation_tx"]]
        check(bool(logs), "creation transaction contains no original pool event")
        if "code_absent_before_creation" in item:
            check(item["code_absent_before_creation"] is True
                  and item["code_previous_block"] == "0x" and item["rpc_complete"] is True,
                  "pre-creation code or RPC incomplete")
        if item["protocol"] == "V3":
            init = [e for e in logs if e["topics"][0] == V3_INIT]
            mint = [e for e in logs if e["topics"][0] == V3_MINT]
            check(len(init) == len(mint) == 1
                  and int(init[0]["logIndex"],16) < int(mint[0]["logIndex"],16),
                  "missing/or misordered creation Initialize Mint")
            active = int(item["state_hex_at_creation"],16)
            check(active >= 0 and active == int(item.get("active_liquidity_raw",str(active))),
                  "V3 raw historical state mismatch")
            first = item["creation_block"] if active > 0 else None
            kind = "V3_CREATION_TX_INITIALIZE_MINT_IN_RANGE_ACTIVE_END_BLOCK"
            if not active:
                check(item["pool"] == bulla["pool"] and item["index"] == 11,
                      "unexpected V3 zero active without bounded proof")
                first,kind = verify_bulla(bulla,ref)
        else:
            sync = [e for e in logs if e["topics"][0] == V2_SYNC]
            mint = [e for e in logs if e["topics"][0] == V2_MINT]
            check(len(sync) >= 1 and len(mint) == 1
                  and int(sync[0]["logIndex"],16) < int(mint[0]["logIndex"],16)
                  and sync[0]["data"] == mint[0]["data"]
                  and word(sync[0]["data"],0) > 0 and word(sync[0]["data"],1) > 0,
                  "creation V2 Sync Mint not positive bilateral")
            check(word(item["state_hex_at_creation"],0) > 0
                  and word(item["state_hex_at_creation"],1) > 0,
                  "V2 creation reserves not positive")
            first = item["creation_block"]
            kind = "V2_CREATION_TX_SYNC_MINT_POSITIVE_END_BLOCK"
        check(item.get("positive_at_end",item.get("positive_at_creation_block_end"))
              == (first == item["creation_block"]), "positive creation label tampered")
        result.append({
            "index":item["index"],"token":ref["token"],"exact_CA":ref["CA"],
            "pool":ref["pool"],"protocol":ref["protocol"],"quote":ref["quote"],
            "fee_pips":ref["fee_pips"],"creation_block":item["creation_block"],
            "creation_UTC":entry["creation_UTC"],"first_active_block":first,
            "delay_blocks":first-item["creation_block"],"activation_event_kind":kind,
            "first_global_trade":"UNRESOLVED","sellability_tax_impact":"UNRESOLVED",
            "wallet_qualified_miss":"UNRESOLVED","follower_profit":"UNRESOLVED"
        })
    check(len(four["rows"]) == 4, "four base rows lost")
    for idx,row in enumerate(four["rows"],12):
        first,kind = row["first_active_liquidity_block"],row["source_event_kind"]
        if row["at_creation_active"]:
            check(first == row["pool_creation_block"], "four active-at-creation violated")
        else:
            check(row["pool"] == niulai["pool"], "wrong four-pool delayed member")
            first,kind = verify_niulai(niulai,row)
        result.append({
            "index":idx,"token":row["token"],"exact_CA":row["CA"],
            "pool":row["pool"],"protocol":row["protocol"],"quote":row["quote"],
            "fee_pips":row["fee_pips"],"creation_block":row["pool_creation_block"],
            "creation_UTC":row["creation_UTC"],"first_active_block":first,
            "delay_blocks":first-row["pool_creation_block"],"activation_event_kind":kind,
            "first_global_trade":"UNRESOLVED","sellability_tax_impact":"UNRESOLVED",
            "wallet_qualified_miss":"UNRESOLVED","follower_profit":"UNRESOLVED"
        })
    result.sort(key=lambda r:r["index"])
    check(len(result) == 17 and [r["index"] for r in result] == list(range(17))
          and len({r["pool"] for r in result}) == 17,
          "17 original active competitor identities incomplete")
    check(sum(r["delay_blocks"]==0 for r in result)==15
          and sorted(r["delay_blocks"] for r in result if r["delay_blocks"]>0)==[10,17],
          "15 at creation and two delayed first-active negatives expected")
    return {
       "schema":"BSC_P4_17_COMPETITOR_SCOPED_FIRST_ACTIVE_LIQUIDITY",
       "scope":"17 frozen active-at-V2-reference Pancake V2/V3 WBNB/USDT competitors, excludes five inactive at reference but does not dismiss their earlier history or other launch venues",
       "source_manifest":[{"path":PREFIX+name,"git_blob_sha":sha} for name,sha in PINS],
       "summary":{"competitor_first_active_proven":17,"creation_block_active":15,
                  "delayed_first_active":2,"delayed_blocks":[10,17],
                  "other_inactive_at_reference_still_unresolved":5,
                  "first_global_buy_sell_proven":0,"eligible_wallet_misses":0,
                  "follower_pnl_proven":0,"production":"NO_GO"},
       "rows":result
    }

def main():
    p=argparse.ArgumentParser(description="P4 17 pool first active offline source replay")
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    args.output.write_text(json.dumps(build(load(args.source_dir),args.source_dir),
        ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
