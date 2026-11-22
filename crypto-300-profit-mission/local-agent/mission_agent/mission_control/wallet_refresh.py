"""Explicit full-owner captures using the existing RPC transport, never a scanner.

Both token programs and native SOL are read at finalized contexts. Different
slots remain separate; this is an open-account snapshot, not lifetime history.
"""
from __future__ import annotations

import json
import time
import uuid
from decimal import Decimal

from ..meme.cluster import SolanaReadOnlyRPC
from ..meme.holder_ranks import valid_pubkey
from .source_evidence import build_source_ref, raw_amount, token_amount, coverage

PROGRAMS = (
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
)


class OwnerRPC(SolanaReadOnlyRPC):
    ALLOWED = SolanaReadOnlyRPC.ALLOWED | {"getTokenAccountsByOwner", "getBalance"}

    def __init__(self, endpoints, *, clock=time.time):
        super().__init__(endpoints[0], fallback_endpoints=endpoints[1:])
        self.clock = clock
        self.last_receipt = None
        open_url = self.open_url

        def recorded(request, timeout):
            response = open_url(request, timeout=timeout)
            owner = self

            class Response:
                def __enter__(self):
                    response.__enter__()
                    return self

                def read(self, *args):
                    raw = response.read(*args)
                    owner.last_receipt = {
                        "raw": raw, "provider": request.full_url,
                        "received_at": owner.clock(),
                    }
                    return raw

                def __exit__(self, *args):
                    return response.__exit__(*args)

            return Response()

        self.open_url = recorded

    def read_evidence(self, method, params):
        self.last_receipt = None
        result = self.call(method, params, ttl=0)
        if self.last_receipt is None:
            raise ValueError("RAW_RECEIPT_MISSING")
        return result, self.last_receipt


def _slot(result, minimum):
    context = result.get("context") if isinstance(result, dict) else None
    slot = context.get("slot") if isinstance(context, dict) else None
    if type(slot) is not int or slot < max(1, minimum):
        raise ValueError("INVALID_CONTEXT_SLOT")
    return slot


def _source(method, params, result, receipt):
    # Verify that the exact captured response really contains the admitted result.
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("RPC_DUPLICATE_JSON_KEY")
            value[key] = item
        return value
    envelope = json.loads(receipt["raw"], object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))
    if (not isinstance(envelope, dict) or envelope.get("jsonrpc") != "2.0"
            or type(envelope.get("id")) is not int or envelope["id"] != 1
            or ("error" in envelope and envelope["error"] is not None)
            or "result" not in envelope
            or json.dumps(envelope["result"], sort_keys=True, allow_nan=False)
            != json.dumps(result, sort_keys=True, allow_nan=False)):
        raise ValueError("RPC_RECEIPT_RESULT_MISMATCH")
    return build_source_ref(
        provider_identity=receipt["provider"], method=method, params=params,
        response_bytes=receipt["raw"], observed_at=receipt["received_at"],
        received_at=receipt["received_at"], slot=result["context"]["slot"],
        commitment="finalized", receipt_id=str(uuid.uuid4()),
    )


def _units(raw, decimals):
    """A Mint aggregate can exceed u64; digit placement must not round it."""
    if not decimals:
        return raw
    padded = raw.zfill(decimals + 1)
    return (padded[:-decimals] + "." + padded[-decimals:]).rstrip("0").rstrip(".") or "0"


def capture_owner(wallet, rpc, *, clock=time.time, save_receipt=lambda ref, raw: None,
                  checkpoint=lambda section: None):
    if not valid_pubkey(wallet):
        raise ValueError("INVALID_OWNER")
    started = clock()
    minimum = 0
    seen = set()
    mints = {}
    sources = []
    programs = []
    for program in PROGRAMS:
        config = {"encoding": "jsonParsed", "commitment": "finalized"}
        if minimum:
            config["minContextSlot"] = minimum
        params = [wallet, {"programId": program}, config]
        result, receipt = rpc.read_evidence("getTokenAccountsByOwner", params)
        slot = _slot(result, minimum)
        if not isinstance(result.get("value"), list):
            raise ValueError("INCOMPLETE_PROGRAM_RESPONSE")
        source = _source("getTokenAccountsByOwner", params, result, receipt)
        save_receipt(source, receipt["raw"])
        for row in result["value"]:
            if not isinstance(row, dict) or not valid_pubkey(row.get("pubkey")) or row["pubkey"] in seen:
                raise ValueError("INVALID_OR_DUPLICATE_TOKEN_ACCOUNT")
            account = row.get("account")
            data = account.get("data") if isinstance(account, dict) else None
            parsed = data.get("parsed") if isinstance(data, dict) else None
            info = parsed.get("info") if isinstance(parsed, dict) else None
            if not isinstance(info, dict):
                raise ValueError("TOKEN_ACCOUNT_PARSED_METADATA_INVALID")
            mint = info.get("mint")
            amount = info.get("tokenAmount")
            if not isinstance(amount, dict):
                raise ValueError("TOKEN_ACCOUNT_PARSED_METADATA_INVALID")
            if (account.get("owner") != program or account.get("executable") is not False
                    or parsed.get("type") != "account" or info.get("owner") != wallet
                    or not valid_pubkey(mint)):
                raise ValueError("TOKEN_ACCOUNT_IDENTITY_MISMATCH")
            value = token_amount(amount.get("amount"), amount.get("decimals"))
            prior = mints.get(mint)
            if prior and (prior["decimals"] != value["decimals"] or program not in prior["program_ids"]):
                raise ValueError("MINT_DECIMALS_OR_PROGRAM_CONFLICT")
            seen.add(row["pubkey"])
            item = mints.setdefault(mint, {
                "mint": mint, "raw_amount": "0", "decimals": value["decimals"],
                "program_ids": [program], "accounts": [], "source_refs": [],
            })
            # Aggregates may exceed one account's u64. Python integer sums are exact.
            item["raw_amount"] = str(int(item["raw_amount"]) + int(value["raw_amount"]))
            item["accounts"].append({"token_account": row["pubkey"], **value, "program_id": program, "slot": slot})
            if source["receipt_id"] not in item["source_refs"]:
                item["source_refs"].append(source["receipt_id"])
        section = {"program_id": program, "slot": slot, "account_count": len(result["value"]),
                   "source_ref": source, "status": "COMPLETE_WITHIN_SCOPE"}
        programs.append(section)
        sources.append(source)
        checkpoint(section)
        minimum = slot
    params = [wallet, {"commitment": "finalized", "minContextSlot": minimum}]
    result, receipt = rpc.read_evidence("getBalance", params)
    slot = _slot(result, minimum)
    native = raw_amount(result.get("value"))
    source = _source("getBalance", params, result, receipt)
    save_receipt(source, receipt["raw"])
    sources.append(source)
    rows = []
    for item in sorted(mints.values(), key=lambda r: r["mint"]):
        item["ui_amount"] = _units(item["raw_amount"], item["decimals"])
        item["account_count"] = len(item["accounts"])
        rows.append(item)
    observed_at = min(Decimal(s["observed_at"]) for s in sources)
    return {
        "schema_version": 1, "parser_version":"frank-owner-snapshot-v1", "snapshot_id": str(uuid.uuid4()), "wallet": wallet,
        "chain": "solana", "scope": "FULL_OWNER_OPEN_ACCOUNTS_AT_FINALIZED_PROGRAM_SLOTS",
        "status": "COMPLETE_WITHIN_SCOPE", "same_slot_atomic": False,
        "coverage":coverage("FULL_OWNER_OPEN_ACCOUNTS_AT_FINALIZED_PROGRAM_SLOTS",enumeration_status="COMPLETE_WITHIN_SCOPE"),
        "full_chain_history_verified": False, "captured_started_at": started,
        "captured_finished_at": clock(), "observed_at": str(observed_at),
        "expires_at": str(observed_at + 300), "max_age_seconds": 300,
        "programs": programs, "sources": sources,
        "native_sol": {"raw_amount": native, "decimals": 9, "slot": slot,
                       "ui_amount": _units(native, 9), "source_ref": source["receipt_id"]},
        "account_count": len(seen), "mint_count": len(rows),
        "nonzero_mint_count": sum(int(r["raw_amount"]) > 0 for r in rows), "rows": rows,
    }
