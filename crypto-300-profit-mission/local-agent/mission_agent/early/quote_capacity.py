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
