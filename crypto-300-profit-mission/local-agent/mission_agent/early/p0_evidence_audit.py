"""Offline, fail-closed reconciliation of the frozen Monster BSC V2 P0 dossier.

This checks the *internal integrity* of already archived derived assertions.
It neither authenticates historical source bytes nor verifies contemporaneous PIT,
real user sellability or returns. No network, wallet, database or file writes.
"""
import hashlib
import json
import re
from pathlib import Path

KEY_ROSTER = "bsc_v2_p0_current_frozen30_p0_gate_matrix_20261020"
KEY_SELL_ROUTE = "bsc_v2_p0_22_sell_transaction_route_price_protection_20261026"
KEY_SELL_DEPTH = "bsc_v2_p0_22_actual_sell_pool_quote_depletion_20261026"
KEY_ROUNDTRIP = "bsc_v2_p0_seven_same_recipient_full_token_roundtrip_execution_route_20261020"
HEX_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}\Z")
HEX_TX = re.compile(r"0x[0-9a-fA-F]{64}\Z")
MAX_INPUT_BYTES = 4 * 1024 * 1024
PINNED_EVIDENCE_GIT_BLOB_SHA1 = "1a6940290d03cc79ca86fd2c7f22ff4a0982c7a6"
FROZEN_SELL_RANKS = (1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 16, 17, 19, 21, 22, 23, 24, 25, 27, 29, 30)
FROZEN_ROUNDTRIP_RANKS = (3, 7, 12, 13, 21, 23, 30)


class EvidenceAuditError(ValueError):
    pass


def _rows(evidence, key):
    src = evidence.get(key)
    if not isinstance(src, dict) or not isinstance(src.get("rows"), list):
        raise EvidenceAuditError("MISSING_OR_INVALID_ROWS:" + key)
    return src["rows"]


def _indexed(rows, roster=None):
    index = {}
    for row in rows:
        if not isinstance(row, dict):
            raise EvidenceAuditError("ROW_MUST_BE_OBJECT")
        rank = row.get("rank")
        ca = row.get("token_ca")
        if type(rank) is not int or not 1 <= rank <= 30:
            raise EvidenceAuditError("RANK_INVALID")
        if not isinstance(ca, str) or not HEX_ADDRESS.fullmatch(ca):
            raise EvidenceAuditError("TOKEN_CA_INVALID")
        if rank in index:
            raise EvidenceAuditError("DUPLICATE_RANK")
        if roster is not None:
            frozen = roster.get(rank)
            if frozen is None or frozen["token_ca"].lower() != ca.lower():
                raise EvidenceAuditError("TOKEN_IDENTITY_MISMATCH")
        index[rank] = row
    return index


def _wei(value, field):
    if not isinstance(value, str) or not value.isdecimal() or len(value) > 100:
        raise EvidenceAuditError("INVALID_UINT_FIELD:" + field)
    return int(value)


def reconcile(evidence):
    """Audit joins and return explicit *uncertified* phase gates.

    Counts describe observed prior evidence, not independent people, unbiased
    winners, valid live entries, or fixed-notional executable exits.
    """
    if not isinstance(evidence, dict):
        raise EvidenceAuditError("EVIDENCE_OBJECT_REQUIRED")
    frozen = _rows(evidence, KEY_ROSTER)
    if len(frozen) != 30 or [r.get("rank") for r in frozen if isinstance(r, dict)] != list(range(1, 31)):
        raise EvidenceAuditError("FROZEN_30_ROSTER_CHANGED")
    roster = _indexed(frozen)
    if len({r.get("pool", "").lower() for r in frozen}) != 30:
        raise EvidenceAuditError("DUPLICATE_OR_MISSING_POOL")
    for row in frozen:
        if not isinstance(row.get("pool"), str) or not HEX_ADDRESS.fullmatch(row["pool"]):
            raise EvidenceAuditError("POOL_ADDRESS_INVALID")
    routes = _indexed(_rows(evidence, KEY_SELL_ROUTE), roster)
    depth = _indexed(_rows(evidence, KEY_SELL_DEPTH), roster)
    roundtrips = _indexed(_rows(evidence, KEY_ROUNDTRIP), roster)
    if (tuple(sorted(routes)) != FROZEN_SELL_RANKS
            or tuple(sorted(roundtrips)) != FROZEN_ROUNDTRIP_RANKS):
        raise EvidenceAuditError("FROZEN_SELECTED_CASES_CHANGED")
    if routes.keys() != depth.keys() or not roundtrips.keys() <= routes.keys():
        raise EvidenceAuditError("SELL_AND_ROUNDTRIP_POPULATION_MISMATCH")
    if len(routes) > 30 or len(roundtrips) > len(routes):
        raise EvidenceAuditError("INVALID_SUBSET_CARDINALITY")

    verified_min_out = []
    depth_met = []
    depleted_99 = []
    for rank, route in routes.items():
        dep = depth[rank]
        tx = route.get("original_sell_transaction")
        if not isinstance(tx, str) or not HEX_TX.fullmatch(tx):
            raise EvidenceAuditError("SELL_TX_HASH_INVALID")
        if dep.get("exact_sell_tx_hash", "").lower() != tx.lower():
            raise EvidenceAuditError("SELL_TX_HASH_MISMATCH")
        if route.get("pool_depth_above_frozen_floor") is not dep.get("pre_swap_research_depth_pass"):
            raise EvidenceAuditError("SELL_PREDEPTH_DISAGREEMENT")
        if dep.get("pre_swap_research_depth_pass") is True:
            depth_met.append(rank)
        if dep.get("depleted_over_99_percent") is True:
            depleted_99.append(rank)
        if route.get("method", "").startswith("V2_ROUTER_"):
            amount = _wei(route.get("minimum_output_raw"), "minimum_output_raw")
            if (amount > 0) is not route.get("min_output_positive"):
                raise EvidenceAuditError("MIN_OUT_ASSERTION_DISAGREEMENT")
            if amount > 0:
                verified_min_out.append(rank)
        elif route.get("minimum_output_raw") is not None:
            raise EvidenceAuditError("CUSTOM_CALL_MIN_OUT_NOT_INTERPRETABLE")

    exact = []
    pool_gross_positive = []
    pool_gross_negative = []
    full_standard_zero_min = []
    custom = []
    for rank, item in roundtrips.items():
        if item.get("actual_same_token_recipient_exact_received_quantity_reversed") is not True:
            raise EvidenceAuditError("NOT_AN_EXACT_ROUNDTRIP")
        if item.get("actual_buy_sell_receipt_status") != "0x1_BOTH":
            raise EvidenceAuditError("UNSUCCESSFUL_ROUNDTRIP_RECEIPT")
        if item.get("historical_sell_tx", "").lower() != routes[rank]["original_sell_transaction"].lower():
            raise EvidenceAuditError("ROUNDTRIP_SELL_TX_MISMATCH")
        buy = _wei(item.get("observed_buy_quote_in_wei"), "buy_quote_in")
        sell = _wei(item.get("observed_sell_pool_quote_out_wei"), "sell_quote_out")
        if buy <= 0:
            raise EvidenceAuditError("NONPOSITIVE_BUY")
        if sell > buy:
            pool_gross_positive.append(rank)
        elif sell < buy:
            pool_gross_negative.append(rank)
        exact.append(rank)
        if item.get("route_class") == "EOA_CALLS_PANCAKESWAP_V2_ROUTER":
            if routes[rank].get("minimum_output_raw") == "0":
                full_standard_zero_min.append(rank)
        elif item.get("route_class") == "EOA_CALLS_CUSTOM_SMART_CONTRACT_RECEIVING_TOKEN_AND_WBNB":
            custom.append(rank)
        else:
            raise EvidenceAuditError("UNKNOWN_ROUNDTRIP_ROUTE_CLASS")

    # A non-UNKNOWN timestamp claim is still not an independently verified
    # publication/receive-time witness. Never promote based on this archive.
    all_clock_unknown = all(row.get("first_actual_public_available_at") == "UNKNOWN"
                            for row in frozen)
    all_amounts_unscorable = all(row.get("uniform_research_notional_sellability") == "NOT_SCORABLE"
                                 for row in frozen)
    return {
        "schema": "MONSTER_P0_FROZEN30_ARCHIVE_RECONCILIATION_V1",
        "scope": "ARCHIVED_DERIVED_EVIDENCE_ONLY_NO_RAW_SOURCE_VERIFICATION",
        "cohort_size": len(roster),
        "joined_sell_ranks": sorted(routes),
        "selected_sell_count": len(routes),
        "sell_depth_floor_ranks": sorted(depth_met),
        "sell_depth_floor_count": len(depth_met),
        "quote_depletion_over_99pct_ranks": sorted(depleted_99),
        "roundtrip_ranks": sorted(exact),
        "roundtrip_count": len(exact),
        "positive_min_out_ranks": sorted(verified_min_out),
        "full_roundtrip_and_positive_min_out_ranks": sorted(set(exact) & set(verified_min_out)),
        "standard_router_roundtrip_zero_min_out_ranks": sorted(full_standard_zero_min),
        "custom_contract_roundtrip_ranks": sorted(custom),
        "pool_quote_gross_positive_before_cost_ranks": sorted(pool_gross_positive),
        "pool_quote_gross_negative_before_cost_ranks": sorted(pool_gross_negative),
        "all_frozen_rows_public_available_at_unknown": all_clock_unknown,
        "all_frozen_rows_notional_sellability_not_scorable": all_amounts_unscorable,
        "raw_original_source_independently_authenticated": False,
        "pit_verified_count": 0 if all_clock_unknown else None,
        "pit_24_of_30_gate": "NOT_SCORABLE",
        "sellable_same_notional_18_of_30_gate": "NOT_SCORABLE",
        "p0": "INSUFFICIENT_COVERAGE",
        "p1": "BLOCKED",
        "g4": "UNKNOWN",
        "g6": "NO_GO",
        "p1_gate_passed": False,
    }


def audit_file(path):
    path = Path(path)
    with path.open("rb") as file:
        body = file.read(MAX_INPUT_BYTES + 1)
    if len(body) > MAX_INPUT_BYTES:
        raise EvidenceAuditError("INPUT_TOO_LARGE")
    actual_blob = hashlib.sha1(b"blob " + str(len(body)).encode("ascii") + b"\x00" + body).hexdigest()
    if actual_blob != PINNED_EVIDENCE_GIT_BLOB_SHA1:
        raise EvidenceAuditError("UNPINNED_EVIDENCE_BLOB")
    try:
        return reconcile(json.loads(body))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceAuditError("EVIDENCE_JSON_INVALID") from error


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Offline Monster P0 dossier integrity audit")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(audit_file(args.input), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
