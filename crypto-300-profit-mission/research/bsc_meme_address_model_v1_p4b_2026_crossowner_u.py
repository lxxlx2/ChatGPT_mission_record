#!/usr/bin/env python3
"""Bounded 2026 five-wallet opportunity-U readiness from pinned research sources."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = (
 ("bsc-meme-address-model-v1-p4-p2p3-readiness-matrix-2026-10-13.json", "3252e05c3ef1a4de14a5e10aed3e5ba80566154f"),
 ("bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json", "f88ed9abfcb0f321ec31e98a029303aca48a8623"),
 ("bsc-meme-address-model-v1-p4b-19ca-unified-early-market-buy-evidence-2026-10-14.json", "c42ad01e896f30262f89f7852f927fc84fb3ea18"),
 ("bsc-meme-address-model-v1-p4c-23x19-five-native-rounds-mixed239e-2026-10-15.json", "7ef825b5e56071687dadbf24d3b4327724e0d831"),
)
CASES = (
 ("DDAC", "0xddac928a240bdace3994c2cc0783d4e29a002127", "龙虾"),
 ("239E", "0x239e74bfbd02d71cdc70fecc2d505dc13acfb337", "龙虾"),
 ("877AF", "0x877af245c61289b24f0c619a4346cdbc68f1aaac", "MARSCOIN"),
 ("2ADF", "0x2adf961b40951736bcff3b36b7fb1cd5775475ba", "牛来"),
 ("A83B", "0xa83b73f5644cde337b61da79589f10ea15548811", "牛来"),
)
def check(ok, message):
    if not ok:
        raise ValueError(message)

def parse_utc(value):
    check(isinstance(value,str), "timestamp required in UTC")
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise ValueError("invalid recent-swap UTC timestamp") from exc
    check(dt.tzinfo is not None and dt.utcoffset().total_seconds()==0,
          "recent-swap timestamps must be UTC")
    return dt.astimezone(timezone.utc)

def load(root=ROOT):
    out=[]
    for name, sha in SOURCES:
        raw=(root/name).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        check(actual==sha, "pinned source drift: "+name)
        out.append(json.loads(raw))
    return out

def build(docs, cases=CASES):
    check(len(docs)==4 and len(cases)==5, "frozen five cases required")
    activity, early, market, economic=docs
    check((activity["summary"]["wallets"], early["summary"]["implicit_wallet_CA_cells"],
           market["summary"]["frozen_major_exact_CAs"], economic["summary"]["total_wallet_CA_cells"]) ==
          (23,437,19,437), "frozen denominator drift")
    check(all(x["summary"]["production"]=="NO_GO" for x in docs), "unexpected production state")
    check((early["summary"]["market_U_qualified"],
           market["summary"]["global_actual_U_and_sell_capacity_fully_qualified"],
           economic["summary"]["public_observer_follower_qualified_signals"]) == (0,0,0),
          "unverified public U was promoted")
    frozen_window=activity["frozen_19CA_snapshot_window"]
    check(isinstance(frozen_window,dict) and
          set(frozen_window)=={"start","end"}, "missing original frozen 19-CA window")
    window_start=parse_utc(frozen_window["start"])
    window_end=parse_utc(frozen_window["end"])
    check(window_start<window_end, "invalid source time window")
    check((activity["summary"]["strict19CA_30day_owner_swap_verified_wallets"],
           activity["summary"]["recent_swap_unknown_wallets"])==(7,16),
          "frozen P3 recent owner evidence denominator changed")
    # The 19-CA scope is material evidence, so make the actual exact-CA
    # universe available in the output rather than only stating its size.
    frozen_exact_CAs=[m["ca"] for m in early["markets"]]
    check(len(frozen_exact_CAs)==len(set(frozen_exact_CAs))==19 and
          set(frozen_exact_CAs)=={m["exact_CA"] for m in market["rows"]},
          "source P3/P4B 19 exact CA universe mismatch")
    check(len({w for _,w,_ in cases})==5, "duplicate wallet in cross-owner cohort")
    rows=[]
    for label,wallet,token in cases:
        owner=next((w for w in activity["wallets"] if w["wallet"]==wallet),None)
        entry=next((w for w in early["wallets"] if w["wallet"]==wallet),None)
        m=next((m for m in market["rows"] if m["token"]==token),None)
        check(owner is not None and entry is not None and m is not None, "cohort identity missing")
        idx=next((x["i"] for x in early["markets"] if x["ca"]==m["exact_CA"]),None)
        check(idx is not None and len(entry["early_owner_trade_statuses"])==19,
              "not in original exact CA cohort")
        rounds=[r for r in economic["verified_economic_rounds"]
                if r["wallet"]==wallet and r["exact_CA"]==m["exact_CA"]]
        check(m["actual_global_observer_market_U"]=="UNRESOLVED" and
              m["following_at_1_5_15min"]=="UNRESOLVED" and
              m["V2_WBNB_original_mathematical_buy_quote_complete"],
              "archived router quote mistaken for executable U")
        if label=="239E":
            check(len(rounds)==2 and sum(int(r["net_wei"])>0 for r in rounds)==1
                  and sum(int(r["net_wei"])<0 for r in rounds)==1,
                  "mixed original win/loss must remain together")
        if label=="DDAC":
            check(m["selected_early_buy_signer"]==wallet, "owner early buy witness missing")
        # P3 is a 30-day / 19-CA *wallet-level* evidence search, not this row's CA.
        # A false "verified" flag means NO VERIFIED WITNESS in the frozen
        # investigation, never CONFIRMED_INACTIVE or a token-specific negative.
        found=owner["p3_verified_recent_19CA_swap"]
        evidence_grade=owner["p4_research_qualification"]
        time=owner["p3_latest_verified_swap_UTC"]
        tx_hash=owner["p3_latest_verified_swap_hash"]
        check(type(found) is bool, "recent 19-CA evidence flag must be boolean")
        if found:
            check(evidence_grade!="RECENT_SIGNED_SWAP_UNRESOLVED"
                  and isinstance(tx_hash,str) and len(tx_hash)==66
                  and tx_hash.startswith("0x") and time is not None,
                  "confirmed P3 witness requires an actual signed tx hash and UTC")
            check(window_start<=parse_utc(time)<=window_end,
                  "confirmed P3 witness lies outside frozen 30-day window")
            state="CONFIRMED_ACTIVE"
        else:
            check(evidence_grade=="RECENT_SIGNED_SWAP_UNRESOLVED"
                  and time is None and tx_hash is None,
                  "no witness is UNKNOWN, not proof of inactivity")
            state="UNRESOLVED"
        rows.append({
            "wallet": wallet, "wallet_label": label, "token": token,
            "exact_CA": m["exact_CA"],
            "recent_signed_swap_state": state,
            "verified_recent_19CA_swap_found": found,
            "recent_swap_scope": "WALLET_LEVEL_FROZEN_19_EXACT_CAS_NOT_DISPLAYED_ROW_CA",
            "recent_swap_frozen_window_UTC": dict(frozen_window),
            "recent_swap_source_qualification": evidence_grade,
            "recent_swap_tx_hash": tx_hash,
            "recent_swap_utc": time,
            "recent_swap_row_CA_attribution": "NOT_CLAIMED_WALLET_UNIVERSE_ONLY",
            "P2_selected_positive_not_settled_PnL": owner["p2_selected_positive_episodes"],
            "P2_selected_negative_not_settled_PnL": owner["p2_selected_negative_episodes"],
            "early_owner_action": entry["early_owner_trade_statuses"][idx],
            "early_market_signed_buy_evidence": m["earlier_actual_signed_purchase_evidence"],
            "early_sampled_buy_signer": m["selected_early_buy_signer"],
            "scoped_first_Pancake_liquidity_block": m["first_scoped_Pancake_positive_liquidity_block"],
            "scoped_router_quote": "MATH_ONLY_NOT_ACTUAL_FILL",
            "source_signed_native_rounds": len(rounds),
            "source_signed_native_positive": sum(int(r["net_wei"])>0 for r in rounds),
            "source_signed_native_negative": sum(int(r["net_wei"])<0 for r in rounds),
            "first_observer_visible_executable_buy_and_sell_U": "UNRESOLVED",
            "funds_tax_gas_capacity_at_U": "UNRESOLVED",
            "follower_1_5_15min_PnL": "UNRESOLVED",
            "eligible_miss": "UNRESOLVED",
        })
    check(len({r["exact_CA"] for r in rows})==3, "frozen three-token cohort drift")
    return {
        "schema":"BSC_P4B_2026_FIVE_CROSSOWNER_U_READINESS",
        "selection":"SOURCE_REUSE_PRE_NEXT_RPC_NOT_RANDOM_OR_UNTOUCHED_HOLDOUT",
        "source_manifest":[{"path":"crypto-300-profit-mission/research/"+n,"git_blob_sha":sha} for n,sha in SOURCES],
        "recent_swap_frozen_19_exact_CAs": frozen_exact_CAs,
        "summary":{"full_wallet_CA_denominator":437,"selected_wallets":5,"selected_major_CAs":3,
                   "qualified_observer_executable_U":0,"qualified_follow_PnL":0,
                   "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO"},
        "cases":rows
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
