#!/usr/bin/env python3
"""P4 fixed first-observed-swap BNB/quote capital and bounded funding evidence.

Read-only, source-blob pinned. A first observed *SELL* balance is never claimed
to be starting capital, profitability, pool liquidity or a qualified missed BUY.
No cross-EOA control attribution from a common sender and no zero-source claim
outside the explicitly queried Alchemy external transfer category/window.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIR = "crypto-300-profit-mission/research/"
FILE_SHA = {
    "bsc-meme-address-model-v1-p4-p2p3-readiness-matrix-2026-10-13.json": "3252e05c3ef1a4de14a5e10aed3e5ba80566154f",
    "bsc-meme-address-model-v1-p4-funding4-precommit-2026-10-13.json": "9b0a5f08a9009af016de7d8cbea9f6ad16c7165c",
    "bsc-meme-address-model-v1-p4-funding4-historical-balance-part1-2026-10-13.json": "7369d73af907079c04ed429dd71ba41ab9dcf5b6",
    "bsc-meme-address-model-v1-p4-funding4-historical-balance-part2-2026-10-13.json": "7959b852f82cce99490c3317f9daed07c9b4c278",
    "bsc-meme-address-model-v1-p4-funding4-historical-balance-part3-2026-10-13.json": "f72bc7a1b210a58de393935d83518775ad317539",
    "bsc-meme-address-model-v1-p4-funding4-historical-balance-part4-2026-10-13.json": "83fa4a44980f29448db3c96904bf28e9af2e5c59",
    "bsc-meme-address-model-v1-p4-funding4-external-native-inbound-2026-10-13.json": "c1d38406a7149a81dab58f3f96c4ada0aa639aab",
    "bsc-meme-address-model-v1-p4-funding4-wbnb-usdt-inbound-2026-10-13.json": "415cc5ede2d54c0f8d30397a763f0ec415852320",
    "bsc-meme-address-model-v1-p4-ddac-inbound-erc20-first25-partial-2026-10-13.json": "54e4f75be3771a30007d75884250794f409d1889",
}


def guard(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load(root: Path) -> dict:
    sources = {}
    for name, pin in FILE_SHA.items():
        b = (root / name).read_bytes()
        guard(git_blob(b) == pin, "SOURCE_BLOB_DRIFT: " + name)
        sources[name] = json.loads(b)
    return sources


def build(src: dict) -> dict:
    readiness, frozen = (src[k] for k in list(FILE_SHA)[:2])
    guard(len(readiness["wallets"]) == 23 and readiness["summary"]["wallets"] == 23
          and readiness["summary"]["sampled_two_plus_major_positive_with_recent_activity"] == 4,
          "P4 all-wallet denominator changed")
    selected = frozen["addresses"]
    guard(len(selected) == len({x["wallet"] for x in selected}) == 4
          and frozen["production"] == "NO_GO", "P4 fixed selection drift")
    source_parts = [src[n] for n in list(FILE_SHA)[2:6]]
    native, erc20, ddac = (src[n] for n in list(FILE_SHA)[6:])
    guard(len(source_parts) == 4 and len(native["wallets"]) == len(erc20["wallets"]) == 4
          and native["summary"]["fully_paginated"] == 4
          and native["summary"]["raw_count"] == 20, "inbound source incomplete")
    guard(erc20["summary"]["fully_paginated"] == 3 and erc20["summary"]["events"] == 3,
          "selected quote source coverage drift")
    guard(ddac["completed"] is False and ddac["next_page_key"] and len(ddac["pages"]) == 5
          and sum(len(page["events"]) for page in ddac["pages"]) == 25,
          "DDAC source must remain explicit PARTIAL, never complete")
    by_ready = {r["wallet"]: r for r in readiness["wallets"]}
    guard(len(by_ready) == 23, "duplicate baseline wallet")
    funding = {}
    for i, expected in enumerate(selected):
        row = source_parts[i]
        wallet = expected["wallet"]
        guard(row["source_precommit_sha"] == FILE_SHA[list(FILE_SHA)[1]]
              and row["sample_index"] == i + 1
              and row["wallet"] == wallet
              and row["first_swap_block"] == expected["first_swap_block"]
              and row["pre_swap_block"] == row["first_swap_block"]-1
              and row["tx"] == expected["first_confirmed_swap_tx"]
              and row["production"] == "NO_GO", "wrong first-swap funding probe")
        guard(by_ready[wallet]["p4_research_qualification"].startswith("PRIORITY_"),
              "snapshot wallet no longer priority under frozen P2/P3 basis")
        raw = {}
        for k in ("native_bnb_before", "native_bnb_swap_block", "nonce_before",
                  "wbnb_before", "usdt_before"):
            r = row["reads"][k]
            guard(r["state"] == "CONFIRMED"
                  and r["raw_hex"].startswith("0x")
                  and int(r["raw_integer"]) == int(r["raw_hex"], 16) >= 0,
                  "failed or mismatched historical onchain read: " + wallet + ":" + k)
            raw[k] = int(r["raw_integer"])
        inflow = next((r for r in native["wallets"] if r["wallet"] == wallet), None)
        quote = next((r for r in erc20["wallets"] if r["wallet"] == wallet), None)
        guard(inflow is not None and inflow["query_state"] == "COMPLETE_PROVIDER_RETURN"
              and inflow["pageKey"] is None
              and inflow["matched_rows"] == len(inflow["records"]), "external inflow not fully paginated")
        guard(quote is not None, "missing quote funding lookup")
        funding_events = inflow["records"]
        for event in funding_events:
            guard(event["to"] == wallet and event["asset"] == "BNB"
                  and int(event["native_value_hex"], 16) > 0
                  and frozen["frozen_start_block"] <= int(event["block_hex"], 16) <= row["pre_swap_block"],
                  "off-window incoming native asset")
        senders = sorted(set(x["from"] for x in funding_events))
        guard(quote["state"] in ("COMPLETE_PROVIDER_RETURN","UNRESOLVED_RPC"),
              "unknown selected quote scan state")
        if wallet == "0xddac928a240bdace3994c2cc0783d4e29a002127":
            guard(quote["state"] == "UNRESOLVED_RPC", "DDAC is a deliberately incomplete quote scan")
            quote_state, known_erc20, quote_senders = "PARTIAL_FIRST_25_EVENTS", 25, sorted(set(
                event["from"] for page in ddac["pages"] for event in page["events"]))
        else:
            guard(quote["state"] == "COMPLETE_PROVIDER_RETURN"
                  and quote["pageKey"] is None and quote["count"] == len(quote["records"]),
                  "non-DDAC quote source should be complete")
            quote_state, known_erc20, quote_senders = "COMPLETE_SELECTED_WBNB_USDT_ONLY", quote["count"], sorted(
                set(event["from"] for event in quote["records"]))
        guard(raw["nonce_before"] > 0, "no observed past signer nonce")
        funding[wallet] = {
            "wallet": wallet, "first_frozen_19CA_successful_swap_hash": row["tx"],
            "first_frozen_19CA_successful_swap_block": row["first_swap_block"],
            "observed_native_bnb_pre_swap_wei": str(raw["native_bnb_before"]),
            "observed_native_bnb_pre_swap_BNB": format(Decimal(raw["native_bnb_before"]) / Decimal(10**18), "f"),
            "observed_native_bnb_at_swap_wei": str(raw["native_bnb_swap_block"]),
            "observed_wbnb_pre_swap_raw_wei": str(raw["wbnb_before"]),
            "observed_usdt_pre_swap_raw_18_decimals": str(raw["usdt_before"]),
            "nonce_pre_swap": raw["nonce_before"],
            "window_external_BNB_inbound_count": len(funding_events),
            "window_external_BNB_inbound_wei": str(sum(int(e["native_value_hex"],16) for e in funding_events)),
            "observed_external_BNB_senders": senders,
            "selected_WBNB_USDT_inbound_state": quote_state,
            "selected_WBNB_USDT_inbound_events_known": known_erc20,
            "observed_selected_quote_senders": quote_senders,
            "historical_internal_native_transfers": "UNRESOLVED_PROVIDER_UNSUPPORTED",
            "original_funding_attribution": "UNRESOLVED",
            "common_controller": "UNRESOLVED",
            "first_eligible_buy_market": "UNRESOLVED",
            "qualified_missed_opportunity": "UNRESOLVED",
            "realized_PnL": "UNRESOLVED",
        }
    guard(set(funding) == {x["wallet"] for x in selected}, "wrong fixed wallet subset")
    rows = []
    for baseline in readiness["wallets"]:
        w = baseline["wallet"]
        rows.append(funding.get(w) or {
            "wallet": w, "research_priority": baseline["p4_research_qualification"],
            "historical_funding_probe": "UNRESOLVED_NO_SNAPSHOT",
            "common_controller": "UNRESOLVED",
            "first_eligible_buy_market": "UNRESOLVED",
            "qualified_missed_opportunity": "UNRESOLVED",
            "realized_PnL": "UNRESOLVED",
        })
    owner_to_wallets = {}
    for wallet, row in funding.items():
        for sender in row["observed_external_BNB_senders"]:
            owner_to_wallets.setdefault(sender, []).append(wallet)
    shared = {x:v for x,v in owner_to_wallets.items() if len(set(v)) > 1}
    guard(len(rows) == 23 and len(shared) == 0, "unexpected common external native funder within bounded scope")
    return {
        "schema": "BSC_MEME_ADDRESS_MODEL_V1_P4_BOUNDED_FIRST_SWAP_CAPITAL_EVIDENCE",
        "scope": "4 frozen research priorities at first verified P3 recent 19-CA Swap pre-block; all 23 wallets retained",
        "source_manifest": [{"path": DIR + name, "git_blob_sha": pin} for name,pin in FILE_SHA.items()],
        "summary": {"wallets": 23, "funding_probed_wallets": 4,
                    "other_wallets_unprobed": 19,
                    "historical_native_pre_swap_balance_verified": 4,
                    "native_external_inbound_windows_fully_paginated": 4,
                    "selected_quote_windows_fully_paginated": 3,
                    "selected_quote_windows_partial": 1,
                    "native_external_inbound_records": 20,
                    "known_selected_ERC20_inbound_records": 28,
                    "shared_external_native_sender_in_scope": 0,
                    "control_attribution_proven": 0,
                    "qualified_major_opportunity_misses": "UNRESOLVED",
                    "production": "NO_GO"},
        "interpretation": ("Prior BNB balance and historical nonce prove a snapshot, not funding source "
                           "of first BUY. Observed external native inflow omits internal and older "
                           "sources. DDAC quote inbound is first 25 records and remains partial. "
                           "No observed shared external BNB sender within this limited window "
                           "does not disprove related owners."),
        "wallets": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Pinned P4 capital snapshot model, no trading")
    p.add_argument("--source-dir", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = build(load(a.source_dir))
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
