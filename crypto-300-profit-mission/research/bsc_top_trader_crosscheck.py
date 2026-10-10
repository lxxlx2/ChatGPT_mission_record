#!/usr/bin/env python3
"""Read-only BSC Meme ranking collector and recency crosscheck.

Manual research only. No private keys, trades, production signals or scheduling.
A provider-reported positive PnL is NEVER a verified on-chain PnL.
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import sys

import bsc_meme_top_traders_readonly as collector


def parse_timestamp(value):
    try:
        ts = float(value)
        if ts >= 1e11:
            ts /= 1000
        if ts < 1e9 or ts >= 5e9:
            return None
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def read_csv(path):
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path, records, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def review(root, window_days=30):
    target = pathlib.Path(root) / "analysis"
    positions = read_csv(target / "token_trader_samples.csv")
    wallets = read_csv(target / "cross_token_wallets.csv")
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=window_days)
    position_by_wallet = {}
    for record in positions:
        wallet = record.get("wallet", "").lower()
        if wallet:
            position_by_wallet.setdefault(wallet, []).append(record)

    reviews = []
    for row in wallets:
        wallet = row.get("wallet", "").lower()
        sample = position_by_wallet.get(wallet, [])
        n_positive = sum(r.get("provisional_realized_winner") == "True" for r in sample)
        n_2026 = sum(
            r.get("provisional_realized_winner") == "True" and
            r.get("year") == "2026" for r in sample
        )
        dates = [parse_timestamp(p.get("last_token_activity_utc")) for p in sample]
        recent = [d for d in dates if d and d >= cutoff]
        latest = max((d for d in dates if d is not None), default=None)
        insufficient_cost = any(
            "TRANSFER_IN_COST_UNVERIFIED" in p.get("flags", "") or
            "NO_DIRECT_BUY" in p.get("flags", "") for p in sample
        )
        reviews.append({
            "wallet": wallet,
            "distinct_sampled_tokens": len({p["token"] for p in sample}),
            "provisional_positive_tokens": n_positive,
            "provisional_positive_2026_tokens": n_2026,
            "last_vendor_token_activity_utc": latest.isoformat() if latest else "",
            "vendor_token_activity_in_last_30d": bool(recent),
            "direct_30d_meme_swap_confirmed": False,
            "all_history_winning_rate_confirmed": False,
            "all_history_realized_pnl_confirmed": False,
            "transfer_in_or_no_buy_warning": insufficient_cost,
            "wallet_control_cluster_confirmed": False,
            "delay_replay_5min_15min_30min_confirmed": False,
            "research_status": "OBSERVE_ONLY",
        })
    reviews.sort(key=lambda r: (
        -int(r["provisional_positive_2026_tokens"]),
        -int(r["vendor_token_activity_in_last_30d"]),
        -int(r["provisional_positive_tokens"]),
        -int(r["distinct_sampled_tokens"]),
    ))
    columns = [
        "wallet", "distinct_sampled_tokens", "provisional_positive_tokens",
        "provisional_positive_2026_tokens", "last_vendor_token_activity_utc",
        "vendor_token_activity_in_last_30d", "direct_30d_meme_swap_confirmed",
        "all_history_winning_rate_confirmed", "all_history_realized_pnl_confirmed",
        "transfer_in_or_no_buy_warning", "wallet_control_cluster_confirmed",
        "delay_replay_5min_15min_30min_confirmed", "research_status"
    ]
    write_csv(target / "active_candidate_review.csv", reviews, columns)
    summary = {
        "generated_utc": now.isoformat(),
        "universe_size": len(collector.TOKENS),
        "vendor_sampled_wallets": len(reviews),
        "vendor_sampled_multi_token_wallets": sum(
            r["distinct_sampled_tokens"] >= 2 for r in reviews),
        "vendor_provisional_two_profitable_tokens": sum(
            r["provisional_positive_tokens"] >= 2 for r in reviews),
        "vendor_provisional_2026_multi_profit": sum(
            r["provisional_positive_2026_tokens"] >= 2 for r in reviews),
        "vendor_activity_within_30d_but_not_proven_swap": sum(
            r["vendor_token_activity_in_last_30d"] for r in reviews),
        "onchain_30d_swap_verified": 0,
        "all_dex_alltime_top100_verified": False,
        "all_wallet_pnl_confirmed": False,
        "production_trading": "NO_GO",
        "research_status": "OBSERVE_ONLY",
        "limitations": [
            "GMGN PnL and recent activity are provider supplied, not on-chain audited",
            "ERC20 receiving address may be router, user aggregator, custodian or transfer recipient",
            "Activity timestamp alone does not establish a signed swap",
            "Ranking samples can omit wallets and unrelated losing tokens",
            "Original swaps, quote-asset receipts, linked funds and delay-replay remain unverified",
        ]
    }
    target.joinpath("review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if reviews else 3


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("both", "collect", "analyze"),
                   default="both")
    p.add_argument("--root", type=pathlib.Path,
                   default=pathlib.Path("bsc_meme_top100"))
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--window-days", type=int, default=30)
    args = p.parse_args()
    if args.window_days <= 0 or args.window_days > 365:
        p.error("--window-days must be from 1 to 365")
    rc = 0
    if args.mode in ("both", "collect"):
        try:
            rc = collector.collect(args.root, args.refresh)
        except (RuntimeError, OSError, ValueError) as exc:
            print("COLLECTION_FAILED: " + str(exc), file=sys.stderr)
            return 2
    if args.mode in ("both", "analyze"):
        analysis_rc = collector.analyze(args.root)
        review_rc = review(args.root, args.window_days)
        rc = rc or analysis_rc or review_rc
    return rc


if __name__ == "__main__":
    sys.exit(main())
