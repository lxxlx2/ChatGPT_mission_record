"""Offline P0 constant-product capacity bounds at a historical reserve snapshot.

No RPC, scoring, model, wallet, scheduling or default purchase notional.
A result is AMM_MATH_ONLY, never evidence of a transferable or executable trade.
"""


class QuoteCapacityError(ValueError):
    pass


def max_input_for_average_impact(reserve_in_raw, reserve_out_raw,
                                 max_total_impact_bps, *, swap_fee_bps=25):
    """Largest integer input with average price impact incl. AMM fee <= budget.

    Assumes a fee-on-input, constant-product V2 pool with unchanging reserves:
      effective_fraction = (10000-fee)/10000
      average_execution_vs_spot = effective_fraction * reserve_in /
          (reserve_in + effective_fraction * input)
    No tax, gas, MEV, quote expiry, price move, or ERC20 transfer semantics.
    """
    if (type(reserve_in_raw) is not int or type(reserve_out_raw) is not int
            or reserve_in_raw <= 0 or reserve_out_raw <= 0):
        raise QuoteCapacityError("POSITIVE_INTEGER_RESERVES_REQUIRED")
    if (type(max_total_impact_bps) is not int
            or not 0 < max_total_impact_bps < 10000):
        raise QuoteCapacityError("IMPACT_BPS_OUT_OF_RANGE")
    if (type(swap_fee_bps) is not int or not 0 <= swap_fee_bps < 10000):
        raise QuoteCapacityError("FEE_BPS_OUT_OF_RANGE")
    if max_total_impact_bps <= swap_fee_bps:
        return 0
    return (reserve_in_raw * (max_total_impact_bps - swap_fee_bps) * 10000
            // ((10000 - swap_fee_bps) * (10000 - max_total_impact_bps)))


def historical_v2_snapshot_capacity(*, block_number, quote_reserve_raw,
                                    token_reserve_raw, max_total_impact_bps,
                                    swap_fee_bps=25):
    """Both independent directions at one historical end-of-block snapshot.

    Sell side measures a token-input bound, NOT the tokens a hypothetical
    entrant could buy and subsequently sell. No time-varying round trip is
    inferred, and historical public availability is explicitly unverified.
    """
    if type(block_number) is not int or block_number < 0:
        raise QuoteCapacityError("BLOCK_NUMBER_INVALID")
    buy = max_input_for_average_impact(
        quote_reserve_raw, token_reserve_raw, max_total_impact_bps,
        swap_fee_bps=swap_fee_bps)
    sell = max_input_for_average_impact(
        token_reserve_raw, quote_reserve_raw, max_total_impact_bps,
        swap_fee_bps=swap_fee_bps)
    return {
        "evidence_grade": "AMM_MATH_ONLY",
        "historical_block_number": block_number,
        "historical_public_available_at": "UNKNOWN",
        "max_quote_in_raw_at_snapshot": str(buy),
        "max_token_in_raw_at_snapshot": str(sell),
        "max_total_impact_bps": max_total_impact_bps,
        "assumed_swap_fee_bps": swap_fee_bps,
        "real_buy_path": "UNKNOWN",
        "real_sell_path": "UNKNOWN",
        "uniform_notional_sellability": "NOT_SCORABLE",
        "p0_gate_passed": False,
    }


def frozen30_capacity_audit(evidence, *, max_total_impact_bps,
                            swap_fee_bps=25):
    """Join all frozen V2 CA identities to end-of-block reserve evidence.

    Missing reserves remain missing. The output contains no label, profitability,
    original public observation clock, or default study order notional.
    """
    if not isinstance(evidence, dict):
        raise QuoteCapacityError("EVIDENCE_OBJECT_REQUIRED")
    try:
        identities = evidence["bsc_v2_p0_current_frozen30_p0_gate_matrix_20261020"]["rows"]
        reserves = evidence["bsc_v2_p0_all24_next_block_reserve_source_read_20261020"]["rows"]
    except (KeyError, TypeError):
        raise QuoteCapacityError("FROZEN_P0_SOURCE_ROWS_MISSING") from None
    if not isinstance(identities, list) or not isinstance(reserves, list):
        raise QuoteCapacityError("FROZEN_P0_ROWS_NOT_ARRAYS")
    ranks = [row.get("rank") for row in identities if isinstance(row, dict)]
    if (len(identities) != 30 or ranks != list(range(1, 31))
            or len({row.get("token_ca") for row in identities}) != 30
            or len({row.get("pool") for row in identities}) != 30):
        raise QuoteCapacityError("FROZEN_30_IDENTITY_MISMATCH")
    by_rank = {}
    for row in reserves:
        if not isinstance(row, dict) or type(row.get("rank")) is not int:
            raise QuoteCapacityError("RESERVE_ROW_INVALID")
        rank = row["rank"]
        if rank in by_rank or rank < 1 or rank > 30:
            raise QuoteCapacityError("RESERVE_RANK_DUPLICATE_OR_OUT_OF_RANGE")
        ident = identities[rank - 1]
        if any(row.get(field) != ident.get(field) for field in
               ("token_ca", "pool", "quote_asset")):
            raise QuoteCapacityError("RESERVE_IDENTITY_NOT_FROZEN")
        by_rank[rank] = row
    output = []
    for row in identities:
        rank = row["rank"]
        item = {
            "rank": rank,
            "token_ca": row["token_ca"],
            "pool": row["pool"],
            "quote_asset": row["quote_asset"],
        }
        if rank not in by_rank:
            item.update({"capacity_status": "NOT_SCORABLE_NO_HISTORIC_RESERVES",
                         "max_quote_in_raw_at_snapshot": None,
                         "max_token_in_raw_at_snapshot": None})
        else:
            src = by_rank[rank]
            try:
                quote = int(src["quote_reserve_raw_at_next_block_end"])
                token = int(src["token_reserve_raw_at_next_block_end"])
                block = src["asof_end_block"]
            except (KeyError, TypeError, ValueError):
                raise QuoteCapacityError("RESERVE_FIELD_MALFORMED") from None
            if (type(src.get("first_confirmed_depth_block")) is not int
                    or type(block) is not int
                    or block <= src["first_confirmed_depth_block"]
                    or not src.get("token_reserve_positive")):
                raise QuoteCapacityError("RESERVE_SNAPSHOT_SCOPE_INVALID")
            item.update({"capacity_status": "AMM_MATH_ONLY", **
                         historical_v2_snapshot_capacity(
                             block_number=block, quote_reserve_raw=quote,
                             token_reserve_raw=token,
                             max_total_impact_bps=max_total_impact_bps,
                             swap_fee_bps=swap_fee_bps)})
        output.append(item)
    return {
        "frozen_population": 30,
        "available_end_block_snapshots": len(by_rank),
        "missing_reserve_snapshots": 30 - len(by_rank),
        "rows": output,
        "historical_public_available_at": "UNKNOWN",
        "uniform_notional_sellability": "NOT_SCORABLE",
        "p0_gate_passed": False,
    }
