"""Compare a saved Alchemy ranked holder response with a primary CA snapshot.

This is offline evidence interpretation, not a provider client. The caller must
authenticate the source and request. Same reported slot and matching ranked
rows do not establish chain identity, whole-mint coverage, or supply parity.
"""
from collections import defaultdict
import hashlib
import re

from .holder_ranks import valid_pubkey
from .independent_check import _primary_account_set
from ..signals.reconciliation import _object

_MAX_ROWS = 10_000
_MAX_BYTES = 4 * 1024 * 1024
_MAX_RAW = 2**64 - 1
_AMOUNT = re.compile(r"[1-9][0-9]{0,19}\Z")


def compare_ranked_holder_capture(mint, ranking, raw_response, *, requested_limit):
    """Return aggregate exact-address comparisons; never infer missing accounts."""
    base = {"version": 1, "status": "UNAVAILABLE", "scope": "RANKED_NONZERO_TOKEN_ACCOUNTS_ONLY",
            "whole_mint_coverage_verified": False, "same_chain_state_verified": False}
    if not valid_pubkey(mint):
        return {**base, "reason": "INVALID_MINT"}
    if not isinstance(ranking, dict) or ranking.get("status") != "COMPLETE_SNAPSHOT":
        return {**base, "reason": "PRIMARY_SNAPSHOT_INCOMPLETE"}
    primary = _primary_account_set(mint, ranking)
    if primary is None:
        return {**base, "reason": "PRIMARY_SNAPSHOT_INVALID"}
    if (type(requested_limit) is not int or not 1 <= requested_limit <= _MAX_ROWS
            or not isinstance(raw_response, bytes) or len(raw_response) > _MAX_BYTES):
        return {**base, "reason": "INVALID_REFERENCE_CAPTURE"}
    _, _, slot, primary_sha, accounts = primary
    base.update(primary_slot=slot, primary_response_sha256=primary_sha,
                reference_response_sha256=hashlib.sha256(raw_response).hexdigest(),
                requested_limit=requested_limit)
    envelope = _object(raw_response)
    result = envelope.get("result") if isinstance(envelope, dict) and envelope.get("jsonrpc") == "2.0" and "error" not in envelope else None
    if not isinstance(result, dict) or result.get("mint") != mint or result.get("sortBy") != "balance_desc":
        return {**base, "reason": "REFERENCE_IDENTITY_UNVERIFIED"}
    observed = result.get("slot")
    if type(observed) is not int or observed <= 0:
        return {**base, "reason": "REFERENCE_SLOT_INVALID"}
    if observed != slot:
        return {**base, "status": "DIFFERENT_REPORTED_SLOTS", "reference_slot": observed}
    base.update(reference_slot=observed, same_reported_slot=True)
    rows = result.get("holders")
    if not isinstance(rows, list) or len(rows) > requested_limit:
        return {**base, "reason": "REFERENCE_ROWS_INVALID"}

    seen = set()
    reference_totals, primary_totals = defaultdict(int), defaultdict(int)
    matches = differences = missing = 0
    previous_balance = _MAX_RAW
    for row in rows:
        if not isinstance(row, dict):
            return {**base, "reason": "REFERENCE_ROWS_INVALID"}
        holder, owner, amount = row.get("holder"), row.get("owner"), row.get("balanceRaw")
        if (not valid_pubkey(holder) or holder == mint or holder in seen or not valid_pubkey(owner)
                or not isinstance(amount, str) or not _AMOUNT.fullmatch(amount)
                or int(amount) > previous_balance):
            return {**base, "reason": "REFERENCE_ROWS_INVALID"}
        raw = previous_balance = int(amount)
        seen.add(holder)
        reference_totals[owner] += raw
        original = accounts.get(holder)
        if original is None:
            missing += 1
            continue
        primary_totals[original["owner"]] += int(original["raw"])
        if original["owner"] == owner and original["raw"] == amount:
            matches += 1
        else:
            differences += 1
    return {**base, "status": ("SAME_SLOT_RANKED_DIFFERENCE" if differences or missing else
                               "SAME_SLOT_RANKED_ROWS_MATCH" if seen else "SAME_SLOT_NO_RANKED_ROWS"),
            "reference_returned_count": len(seen), "reference_at_requested_limit": len(seen) == requested_limit,
            "matched_accounts": matches, "changed_owner_or_raw": differences, "reference_only_accounts": missing,
            "owners_within_reference": len(reference_totals),
            "unequal_owner_totals_within_reference": sum(
                primary_totals.get(key, 0) != reference_totals.get(key, 0)
                for key in primary_totals.keys() | reference_totals.keys()
            ) }
