"""Read-only export of source-verified Frank token transfers from local SQLite.

All fields are whitelisted public Solana transaction facts; no RPC endpoints,
raw signed payloads, local filesystem paths, emails, tokens or credentials.
No claim that the observed source account is its economic owner/funder.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
from .db import open_production_ro

SOURCE_SCOPE = "LOCAL_NORMALIZED_SIGNATURE_TRANSFER_EVIDENCE_NOT_FULL_CHAIN"
FLOW_FIELDS = ("mint", "direction", "raw_amount", "decimals",
               "source", "destination", "outer_index", "inner_index")
DELTA_FIELDS = ("mint", "owner", "wallet_owned", "pre_amount",
                "post_amount", "delta", "decimals", "account_index")
MAX_SIGNATURES = 200_000
MAX_LEGS_PER_SIGNATURE = 100


def _body(value):
    try:
        j = json.loads(value or "{}")
        return j if isinstance(j, dict) else {}
    except (ValueError, TypeError):
        return {}


def _public_rows(value, keys):
    if not isinstance(value, list):
        return []
    if len(value) > MAX_LEGS_PER_SIGNATURE:
        raise ValueError("SIGNATURE_EVIDENCE_UNBOUNDED")
    return [{key: rec[key] for key in keys if key in rec}
            for rec in value if isinstance(rec, dict)]


def export_signature_evidence(path: Path, *, person_id: str = "frank") -> dict:
    """Preserves passive in/out transfers omitted from the trade-only ledger."""
    db = open_production_ro(path)
    try:
        cursor = db.execute(
            "SELECT signature,block_time,body FROM signatures "
            "WHERE person_id=? ORDER BY block_time,signature", (person_id,))
        records = []
        by_class = Counter()
        provenance = Counter()
        seen = set()
        for row in cursor:
            if len(records) >= MAX_SIGNATURES:
                raise ValueError("SIGNATURE_INDEX_TOO_LARGE")
            signature = row["signature"]
            if signature in seen:
                raise ValueError("DUPLICATE_SIGNATURE_CONFLICT")
            seen.add(signature)
            body = _body(row["body"])
            evidence = body.get("evidence") or {}
            if not isinstance(evidence, dict):
                evidence = {}
            classification = body.get("classification") or "UNKNOWN"
            by_class[str(classification)] += 1
            flows = _public_rows(evidence.get("wallet_token_transfer_flows"), FLOW_FIELDS)
            deltas = _public_rows(evidence.get("token_balance_deltas"), DELTA_FIELDS)
            deltas = [x for x in deltas if x.get("wallet_owned") is True]
            provenance["signature_rows"] += 1
            provenance["signature_rows_with_parsed_counterparty_flows"] += bool(flows)
            provenance["wallet_owned_delta_rows"] += bool(deltas)
            meaningful = [
                x for x in deltas if
                isinstance(x.get("delta"), str)
                and x["delta"].lstrip("-").isascii()
                and x["delta"].lstrip("-").isdecimal()
                and int(x["delta"]) != 0
            ]
            provenance["nonzero_wallet_delta_signature_rows"] += bool(meaningful)
            provenance["passive_nonzero_delta_without_parsed_counterparty"] += (
                classification == "PASSIVE_TRANSFER" and
                not flows and bool(meaningful)
            )
            records.append({
                "signature": signature, "block_time": row["block_time"],
                "slot": evidence.get("slot"),
                "local_classification": classification,
                "local_classification_reason": body.get("classification_reason"),
                "wallet_is_signer": evidence.get("wallet_is_signer"),
                "wallet_is_fee_payer": evidence.get("wallet_is_fee_payer"),
                "mechanical_classification": evidence.get("mechanical_classification"),
                "tx_err": evidence.get("tx_err"),
                "transfer_flows": flows,
                "counterparty_attribution_status": (
                    "PARSED_TOKEN_ACCOUNT_FLOW" if flows else
                    "BALANCE_DELTA_ONLY_COUNTERPARTY_UNRESOLVED" if meaningful else
                    "NO_NONZERO_TOKEN_DELTA_PROVEN"
                ),
                "wallet_owned_token_deltas": deltas,
                "raw_transaction_sha256": evidence.get("raw_transaction_sha256"),
                "normalizer_version": evidence.get("parser_version"),
                "source_scope": "LOCAL_NORMALIZED_INDEX_ONLY",
            })
        return {
            "schema_version": 1,
            "person_id": person_id,
            "source_scope": SOURCE_SCOPE,
            "record_count": len(records),
            "local_classifications": dict(sorted(by_class.items())),
            "source_attribution_coverage": dict(sorted(provenance.items())),
            "all_counterparties_verified": (
                provenance["passive_nonzero_delta_without_parsed_counterparty"] == 0),
            "source_evidence_includes_untraded_transfers": True,
            "chain_history_complete": False,
            "pnl_verified": False,
            "source_token_account_is_sender_owner_verified": False,
            "records": records,
        }
    finally:
        db.close()
