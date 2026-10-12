#!/usr/bin/env python3
"""BSC Meme address-model V1 / P1: deterministic, offline, read-only evidence census.

Input is the *immutable* V21 23-wallet x 19-exact-CA transfer overlay; this script
DOES NOT derive wallet trading PnL or trader rankings from ERC20 Transfer rows.

No network access, API keys, GMGN dependency, trading, delivery or deployment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "BSC_MEME_ADDRESS_MODEL_V1_P1_CROSS_WALLET_TRANSFER_EVIDENCE_BASELINE"
FREEZE_DATE = "2026-10-13"
SOURCE_BASENAME = "BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json"
PRIORITY_2026_MAJOR_NAMES = (
    "我踏马来了",
    "龙虾",
    "牛来",
    "MARSCOIN",
)
FULL_OBSERVED = "COMPLETE_OBSERVED"
FULL_ZERO = "COMPLETE_ZERO_ERC20"
UNKNOWN = "UNRESOLVED"


class SourceValidationError(ValueError):
    """Frozen evidence could not be validated without inventing missing facts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceValidationError(message)


def _address(value: object, label: str) -> str:
    _require(
        isinstance(value, str)
        and len(value) == 42
        and value.startswith("0x")
        and all(c in "0123456789abcdefABCDEF" for c in value[2:]),
        f"{label}: invalid 20-byte hex address",
    )
    return value.lower()


def _nonnegative_int(value: object, label: str) -> int:
    _require(type(value) is int and value >= 0, f"{label}: expected >=0 integer")
    return value


def build_baseline(
    source: dict,
    *,
    source_git_blob_sha: str,
    expected_wallets: int = 23,
    expected_tokens: int = 19,
    expected_observed: int = 148,
    priority_2026_names: tuple[str, ...] = PRIORITY_2026_MAJOR_NAMES,
) -> dict:
    """Pure transform: source transfer evidence -> *research priority*, never profit rank.

    Strict failure on wrong fixed-universe counts, inconsistent wallet/token identities,
    duplicated address/contract, or a missing/partial cursor. UNKNOWN remains UNKNOWN.
    For synthetic unit tests only, expected_wallets/tokens/observed may be overridden.
    """
    _require(isinstance(source, dict), "source must be object")
    _require(isinstance(source_git_blob_sha, str) and len(source_git_blob_sha) == 40
             and all(c in "0123456789abcdef" for c in source_git_blob_sha.lower()),
             "source blob sha must be a 40-character Git hex SHA")
    wallets = source.get("cells_by_wallet")
    summary = source.get("summary")
    _require(isinstance(summary, dict) and isinstance(wallets, list), "missing V21 matrix")
    _require(len(wallets) == expected_wallets, "wallet count differs from frozen universe")
    _require(summary.get("wallets") == expected_wallets, "source summary wallet count mismatch")
    _require(summary.get("token_cas") == expected_tokens, "source summary token count mismatch")
    _require(summary.get("cells") == expected_wallets * expected_tokens,
             "source summary matrix size mismatch")
    _require(summary.get("complete_cursor_cells") == expected_wallets * expected_tokens,
             "source has incomplete cursor coverage")
    _require(summary.get("observed_transfer_pairs") == expected_observed,
             "observed count mismatch")
    _require(summary.get("token_quantity_closed_pairs") == expected_observed,
             "frozen original raw-token quantity not fully verified")
    _require(summary.get("complete_zero_transfer_pairs")
             == expected_wallets * expected_tokens - expected_observed,
             "zero-transfer count mismatch")

    first = wallets[0].get("cells")
    _require(isinstance(first, list) and len(first) == expected_tokens,
             "first wallet lacks full token universe")
    token_universe: list[dict] = []
    token_by_name: dict[str, str] = {}
    for cell in first:
        name = cell.get("token")
        _require(isinstance(name, str) and bool(name), "token name missing")
        ca = _address(cell.get("ca"), f"token {name}")
        _require(name not in token_by_name, f"duplicate token name {name}")
        _require(ca not in token_by_name.values(), f"duplicated exact CA {ca}")
        token_universe.append({"token": name, "ca": ca})
        token_by_name[name] = ca

    _require(len(priority_2026_names) == len(set(priority_2026_names)),
             "duplicated 2026 major token names")
    for name in priority_2026_names:
        _require(name in token_by_name, f"priority 2026 name missing from exact universe: {name}")

    seen_wallets: set[str] = set()
    records: list[dict] = []
    all_cells: list[dict] = []
    observed_total = 0
    for src in wallets:
        wallet = _address(src.get("wallet"), "wallet")
        _require(wallet not in seen_wallets, f"duplicate EOA {wallet}")
        seen_wallets.add(wallet)
        cells = src.get("cells")
        _require(isinstance(cells, list) and len(cells) == expected_tokens,
                 f"{wallet}: cell count mismatch")
        by_ca: dict[str, dict] = {}
        output_cells: list[dict] = []
        for cell in cells:
            name = cell.get("token")
            ca = _address(cell.get("ca"), f"{wallet} token CA")
            _require(name in token_by_name and token_by_name[name] == ca,
                     f"{wallet}: token name/CA identity mismatch")
            _require(ca not in by_ca, f"{wallet}: repeated exact CA {ca}")
            by_ca[ca] = cell
            state = cell.get("state")
            _require(state in (FULL_OBSERVED, FULL_ZERO),
                     f"{wallet} {name}: partial or unrecognized cell state {state!r}")
            count_in = _nonnegative_int(cell.get("complete_in_events"),
                                        f"{wallet} {name} inbound")
            count_out = _nonnegative_int(cell.get("complete_out_events"),
                                         f"{wallet} {name} outbound")
            present = state == FULL_OBSERVED
            _require((count_in + count_out > 0) == present,
                     f"{wallet} {name}: transfer presence/count conflict")
            observed_total += int(present)
            record = {
                "wallet": wallet,
                "token": name,
                "ca": ca,
                "frozen_transfer_state": state,
                "ERC20_presence": "PRESENT" if present else "ABSENT_IN_FROZEN_CA",
                "complete_in_events": count_in,
                "complete_out_events": count_out,
                "original_evidence": cell.get("evidence"),
                "token_quantity_audit_state": (
                    "RECONCILED_TRANSFER_QUANTITY_NOT_TRADE_CLOSE" if present else "NO_POSITIVE_ERC20_TRANSFER"
                ),
                "major_2026_research_priority": name in priority_2026_names,
                # Never infer a signer, economic outcome, recent activity or lost opportunity
                # from ERC20 logs alone.
                "owner_signed_buy_state": UNKNOWN,
                "owner_signed_sell_state": UNKNOWN,
                "recent_30d_true_signed_meme_swap": UNKNOWN,
                "last_true_signed_swap_UTC": None,
                "realized_cashflow_and_profit": UNKNOWN,
                "major_opportunity_eligible_miss": UNKNOWN,
                "followability": UNKNOWN,
                "claim_level": "CONFIRMED_TRANSFER_ONLY",
                "missing_evidence": [
                    "OWNER_SIGNER_AND_RECEIPT",
                    "QUOTE_ASSET_PROCEEDS_AND_GAS",
                    "LAST_REAL_SIGNED_MEME_SWAP_UTC",
                    "TRADE_VENUE_AND_CAUSAL_ENTRY",
                    "EXECUTABLE_FOLLOW_LAG",
                ],
            }
            output_cells.append(record)
            all_cells.append(record)

        _require(set(by_ca) == set(token_by_name.values()),
                 f"{wallet}: missing expected CA")
        priority_names = [
            name for name in priority_2026_names if by_ca[token_by_name[name]]["state"] == FULL_OBSERVED
        ]
        all_observed_names = [
            t["token"] for t in token_universe
            if by_ca[t["ca"]]["state"] == FULL_OBSERVED
        ]
        records.append({
            "wallet": wallet,
            "all_19_erc20_present": len(all_observed_names),
            "all_19_erc20_absent": expected_tokens - len(all_observed_names),
            "priority_2026_major_transfer_present_count": len(priority_names),
            "priority_2026_major_transfer_present": priority_names,
            "all_transfer_present_tokens": all_observed_names,
            "owner_signed_trade_verified_major_count": None,
            "independently_closed_positive_major_count": None,
            "independently_closed_negative_major_count": None,
            "last_confirmed_true_swap_UTC": None,
            "recent_30d_activity_state": UNKNOWN,
            "profit_rank": None,
            "profit_ranking_allowed": False,
            "research_priority_only": True,
            "cells": output_cells,
        })

    _require(observed_total == expected_observed,
             f"transfer present total {observed_total} != {expected_observed}")

    # Coverage order is an evidence-investigation queue, not a profitability score.
    records.sort(key=lambda w: (
        -w["priority_2026_major_transfer_present_count"],
        -w["all_19_erc20_present"],
        w["wallet"],
    ))
    for ordinal, record in enumerate(records, 1):
        record["investigation_order_only"] = ordinal

    return {
        "schema": SCHEMA,
        "generated_for_frozen_date": FREEZE_DATE,
        "authority": "RESEARCH_ONLY_UNBIASED_PROOF_REQUIRED",
        "production": "NO_GO",
        "input_source": {
            "file": SOURCE_BASENAME,
            "git_blob_sha": source_git_blob_sha.lower(),
            "frozen": True,
        },
        "cohort": {
            "wallets": expected_wallets,
            "exact_CAs": expected_tokens,
            "cells": expected_wallets * expected_tokens,
            "ERC20_present": expected_observed,
            "ERC20_absent": expected_wallets * expected_tokens - expected_observed,
            "source_is_exhaustive_BSC_top_profit_traders": False,
            "completed_transaction_PnL_cells": 0,
            "completed_transaction_PnL_cells_note":
                "P1 intentionally imports no economic results; zero is P1 evidence ingestion count, NOT zero market profit or no profitable trades.",
        },
        "major_2026_priority_exact_CA": [
            {"token": name, "ca": token_by_name[name]} for name in priority_2026_names
        ],
        "ranking_contract": {
            "metric": "RESEARCH_PRIORITY_ONLY_BY_2026_ERC20_PRESENCE_AND_19_CA_BREADTH",
            "not": ["PROFIT_RANK", "WIN_RATE", "CONFIRMED_MISSED_OPPORTUNITY"],
            "unknown_profit_is_zero": False,
            "all_wallets_included_even_when_all_missing": True,
            "rankable_realized_profit_wallets": 0,
            "reason": "Full comparable quote-asset PnL, owner signatures, recent true swaps and eligible opportunity denominators not uniformly audited.",
        },
        "wallets": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-git-blob-sha", required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("output must be different from frozen input")
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_baseline(source, source_git_blob_sha=args.source_git_blob_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "status": "PASS_READ_ONLY_BASELINE",
        "wallets": result["cohort"]["wallets"],
        "cells": result["cohort"]["cells"],
        "present": result["cohort"]["ERC20_present"],
        "missing": result["cohort"]["ERC20_absent"],
        "profit_rank": "DISABLED",
        "production": "NO_GO",
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
