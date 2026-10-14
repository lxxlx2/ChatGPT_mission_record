#!/usr/bin/env python3
"""P4-B: deterministic historical PancakeSwap V2 direct Swap evidence, 19 exact CAs.

Only an observed pool action within a fixed 10-block or 1-block window.
Not earliest whole-market tradability, public-wallet trade/PnL or sellability.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = "crypto-300-profit-mission/research/"
PINS = (
    ("bsc-meme-address-model-v1-p4b-v2-first10-swap-precommit-2026-10-14.json", "7a18d9ecf7c9f6d7f7e3c586f9de5155c7aba718"),
    ("bsc-meme-address-model-v1-p4b-v2-first10-swaps-part1-2026-10-14.json", "65c15652731e36d8ff7786643ef21cdc7e449ed6"),
    ("bsc-meme-address-model-v1-p4b-v2-first10-swaps-part2-2026-10-14.json", "692d0b5eb8ae4e5944c1cf313f37bc34b00593cc"),
    ("bsc-meme-address-model-v1-p4b-v2-first10-swaps-part3-2026-10-14.json", "84ae3dbad84cbe379a4b564590432f301ba771df"),
    ("bsc-meme-address-model-v1-p4b-v2-first10-swaps-part4-2026-10-14.json", "3de1f0069609a71c3c9dffefc920f611a70d55ca"),
    ("bsc-meme-address-model-v1-p4b-v2-truncation-oneblock-fallback-precommit-2026-10-14.json", "7a18d9ecf7c9f6d7f7e3c586f9de5155c7aba718"),
    ("bsc-meme-address-model-v1-p4b-v2-oneblock-fallback-part1-2026-10-14.json", "c1e4f73b2bac842f9eb9bf7885ff18e0db3c23f0"),
    ("bsc-meme-address-model-v1-p4b-v2-oneblock-fallback-part2-2026-10-14.json", "c1e4f73b2bac842f9eb9bf7885ff18e0db3c23f0"),
)
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"


def check(ok, message):
    if not ok:
        raise ValueError(message)


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load(root=ROOT):
    result = []
    for name, sha in PINS:
        raw = (root / name).read_bytes()
        check(git_blob(raw) == sha, "source blob mismatch: " + name)
        result.append(json.loads(raw))
    return result


def build(docs):
    pre, *rest = docs
    check(len(docs) == len(PINS) and pre["schema"] ==
          "BSC_P4B_FROZEN19_V2_WBNB_FIRST10_BLOCK_SWAP_WITNESS_PRECOMMIT"
          and pre["production"] == "NO_GO" and len(pre["rows"]) == 19,
          "precommitted 19 CA scope invalid")
    ten_parts = docs[1:5]
    fb_pre = docs[5]
    fb_parts = docs[6:8]
    ten = [r for p in ten_parts for r in p["rows"]]
    fallback = [r for p in fb_parts for r in p["rows"]]
    check(len(ten) == 19 and [r["index"] for r in ten] == list(range(19)),
          "truncated original cohort")
    check(len(fallback) == 8 and
          [r["index"] for r in fallback] == [0, 4, 5, 10, 12, 13, 14, 17],
          "fallback pool selection altered")
    check(fb_pre["schema"] == "BSC_P4B_V2_FIRST10_RPC_TRUNCATION_FALLBACK_PRECOMMIT"
          and fb_pre["production"] == "NO_GO"
          and [x["index"] for x in fb_pre["targets"]] ==
          [r["index"] for r in fallback],
          "fallback missing original frozen selection")
    check(fb_pre["source_part_blob_sha"] ==
          [{"part": i+1, "sha": PINS[i+1][1]} for i in range(4)],
          "fallback was not precommitted from original completed attempts")
    for k,p in enumerate(ten_parts, 1):
        check(p["schema"] == "BSC_P4B_V2_FIRST10_ORIGINAL_POOL_SWAP_LOGS"
              and p["part"] == k and p["precommit_git_blob_sha"] == PINS[0][1]
              and p["production"] == "NO_GO", "ten-block provenance broken")
    for k,p in enumerate(fb_parts, 1):
        check(p["schema"] == "BSC_P4B_V2_FIRST_BLOCK_FALLBACK_POOL_SWAP_LOGS"
              and p["part"] == k and p["precommit_git_blob_sha"] == PINS[5][1]
              and p["production"] == "NO_GO", "fallback source mismatch")
    fallback_map = {x["index"]: x for x in fallback}
    rows = []
    for idx, (selection, attempt) in enumerate(zip(pre["rows"], ten)):
        check(selection["index"] == attempt["index"] == idx
              and selection["pool"] == attempt["pool"]
              and selection["token"] == attempt["token"]
              and attempt["from_block"] == selection["from_block"]
              and attempt["to_block"] == selection["to_block"]
              and selection["to_block"] == selection["from_block"] + 9
              and selection["expected_swap_topic0"] == SWAP
              and selection["quote"] == "WBNB", "original pool/window changed")
        was_truncated = attempt["query_status"] != "COMPLETE"
        check(attempt["query_status"] in ("COMPLETE", "FAILED_OR_TRUNCATED"),
              "unknown original fetch result")
        if was_truncated:
            fb = fallback_map.get(idx)
            check(fb is not None and fb["query_status"] == "COMPLETE"
                  and fb["block"] == selection["from_block"]
                  and fb["pool"] == selection["pool"]
                  and fb["token"] == selection["token"], "fallback not one block exactly")
            logs = fb["logs"]
        else:
            check(idx not in fallback_map, "fallback data silently overrides complete window")
            logs = attempt["logs"]
        check(isinstance(logs, list) and
              (not was_truncated or idx in fallback_map), "missing raw events")
        from_block = selection["from_block"]
        to_block = from_block if was_truncated else selection["to_block"]
        pool = selection["pool"].lower()
        token = selection["exact_CA"].lower()
        token_is_zero = min(token, WBNB) == token
        buys = sells = other = 0
        events = []
        for log in logs:
            check(log["address"].lower() == pool and log["topics"][0] == SWAP
                  and log.get("removed") is not True
                  and from_block <= int(log["blockNumber"], 16) <= to_block,
                  "Swap log outside verified query scope")
            data = log["data"]
            check(isinstance(data, str) and data.startswith("0x")
                  and len(data) == 2+64*4, "malformed V2 Swap data")
            amt = [int(data[2+64*k:2+64*(k+1)], 16) for k in range(4)]
            a0i, a1i, a0o, a1o = amt
            tin, tout = (a0i, a0o) if token_is_zero else (a1i, a1o)
            qin, qout = (a1i, a1o) if token_is_zero else (a0i, a0o)
            if tin == 0 and tout > 0 and qin > 0 and qout == 0:
                typ = "POOL_SWAP_BUY_TOKEN_WBNB_IN"
                buys += 1
            elif tin > 0 and tout == 0 and qin == 0 and qout > 0:
                typ = "POOL_SWAP_SELL_TOKEN_WBNB_OUT"
                sells += 1
            else:
                typ = "COMPLEX_OR_NOT_SIMPLE"
                other += 1
            events.append({
                "block": int(log["blockNumber"], 16),
                "txhash": log["transactionHash"],
                "log_index": int(log["logIndex"], 16),
                "swap_type": typ,
                "token_in_raw": str(tin), "token_out_raw": str(tout),
                "wbnb_in_wei": str(qin), "wbnb_out_wei": str(qout),
            })
        events.sort(key=lambda x: (x["block"], x["log_index"]))
        check(len({(x["txhash"], x["log_index"]) for x in events}) == len(events),
              "duplicate onchain log counted")
        check(buys+sells+other == len(events), "Swap decode count mismatch")
        rows.append({
            "index": idx, "token": selection["token"],
            "exact_CA": selection["exact_CA"], "pool": selection["pool"],
            "source_first_liquidity_block": selection["first_positive_liquidity_block"],
            "verified_swap_window_start": from_block,
            "verified_swap_window_end": to_block,
            "scan_coverage": "FIRST_BLOCK_ONLY_TEN_BLOCK_SOURCE_TRUNCATED" if was_truncated else "FULL_FIRST_TEN_BLOCKS",
            "swap_event_count": len(events), "pool_buy_token_events": buys,
            "pool_sell_token_events": sells, "complex_swap_events": other,
            "first_observed_swap_block": events[0]["block"] if events else None,
            "event_witnesses": events,
            "pool_directional_trades_are_not_owner_pnl": True,
            "qualified_major_opportunity": "UNRESOLVED",
            "tax_and_sellability": "UNRESOLVED", "follower_pnl": "UNRESOLVED",
        })
    summary = {
        "exact_CAs": 19, "v2_wbnb_pools": 19,
        "complete_ten_block_windows": sum(r["scan_coverage"]=="FULL_FIRST_TEN_BLOCKS" for r in rows),
        "first_block_only_fallbacks": sum(r["scan_coverage"]=="FIRST_BLOCK_ONLY_TEN_BLOCK_SOURCE_TRUNCATED" for r in rows),
        "observed_v2_swap_events_in_verified_windows": sum(r["swap_event_count"] for r in rows),
        "pools_with_observed_swap": sum(r["swap_event_count"]>0 for r in rows),
        "pools_with_observed_token_buy": sum(r["pool_buy_token_events"]>0 for r in rows),
        "pools_with_observed_token_sell": sum(r["pool_sell_token_events"]>0 for r in rows),
        "fully_qualified_U": 0, "production": "NO_GO",
    }
    check(summary["complete_ten_block_windows"] == 11
          and summary["first_block_only_fallbacks"] == 8
          and summary["observed_v2_swap_events_in_verified_windows"] == 24,
          "actual bounded observation tally changed")
    return {
        "schema": "BSC_P4B_FROZEN19_V2_FIRST10_SWAP_OBSERVATION_MATRIX",
        "scope": "Only Pancake V2 WBNB direct pool Swap witness at 19 frozen first liquidity blocks, 11 full ten-block windows and 8 one-block fallbacks; not full launch market or sellability/pnl",
        "source_manifest": [{"path": PREFIX+name,"git_blob_sha":sha} for name,sha in PINS],
        "summary": summary, "rows": rows,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dir",type=Path,default=ROOT)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.write_text(json.dumps(build(load(args.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
