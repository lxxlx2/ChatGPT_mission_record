"""Local, explicit asset qualification and conservative buy admission.

No symbol, venue, quote mint or classifier verdict alone establishes Meme identity.
Unknown, conflicting and explicitly excluded records fail closed.
"""
from dataclasses import dataclass
import hashlib
import json
import re

from ..meme.holder_ranks import valid_pubkey
from .classifier import QUOTE_MINTS, USDT
from .policy import USDC
from .reconciliation import _base58_size


def exact_mint(mint):
    return valid_pubkey(mint)

@dataclass(frozen=True)
class Asset:
    status: str
    source: str
    observed_at: int
    name: str | None


def qualification(path, as_of, *, sha256=None):
    """Read trusted local observations, never fetch or infer qualification."""
    with path.open("rb") as f:
        payload = f.read(1_048_577)
    if len(payload) > 1_048_576:
        raise ValueError("QUALIFICATION_TOO_LARGE")
    if sha256 is not None and hashlib.sha256(payload).hexdigest() != sha256:
        raise ValueError("QUALIFICATION_SHA256_MISMATCH")

    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError("DUPLICATE_QUALIFICATION_KEY")
            out[key] = value
        return out

    doc = json.loads(payload, object_pairs_hook=unique)
    if (not isinstance(doc, dict) or type(doc.get("version")) is not int or doc["version"] != 1
            or not isinstance(doc.get("records"), list)):
        raise ValueError("INVALID_QUALIFICATION")
    result = {}
    for r in doc["records"]:
        if not isinstance(r, dict) or r.get("chain") != "solana" or not exact_mint(r.get("mint")):
            raise ValueError("INVALID_ASSET_IDENTITY")
        status, source, at = r.get("status"), r.get("source"), r.get("observed_at")
        name = r.get("name")
        if (status not in ("VERIFIED_MEME", "EXCLUDED", "PENDING")
                or not isinstance(source, str) or not 1 <= len(source.strip()) <= 512
                or type(at) is not int or not 0 < at <= as_of
                or (name is not None and (not isinstance(name, str) or not 1 <= len(name.strip()) <= 80))):
            raise ValueError("INVALID_ASSET_QUALIFICATION")
        mint = r["mint"]
        if mint in result:
            raise ValueError("DUPLICATE_ASSET_QUALIFICATION")
        result[mint] = Asset(status, source.strip(), at, name.strip() if name else None)
    return result


def _units(raw, decimals):
    if (not isinstance(raw, str) or not re.fullmatch(r"[1-9][0-9]{0,29}", raw)
            or type(decimals) is not int or not 0 <= decimals <= 255):
        return None
    if not decimals:
        return raw
    raw = raw.zfill(decimals + 1)
    fraction = raw[-decimals:].rstrip("0")
    return raw[:-decimals] + ("." + fraction if fraction else "")


def admit_buy(event, assets, *, wallet, signature, slot, block_time, raw_hash, mint):
    """Return only facts bound to this classified, archived wallet event."""
    asset = assets.get(mint)
    if not asset or asset.status != "VERIFIED_MEME" or mint in QUOTE_MINTS or not exact_mint(mint):
        return None
    if not isinstance(event, dict) or event.get("classification") != "ACTIVE_TRADE":
        return None
    evidence, trade = event.get("evidence"), event.get("trade")
    if not isinstance(evidence, dict) or not isinstance(trade, dict):
        return None
    if (not exact_mint(wallet) or not _base58_size(signature, 64)
            or type(slot) is not int or slot < 0 or type(block_time) is not int
            or not 0 < block_time <= 4_000_000_000 or not isinstance(raw_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", raw_hash)
            or any(row.get(k) != v for row in (event, evidence)
                   for k, v in (("wallet", wallet), ("signature", signature), ("slot", slot), ("block_time", block_time)))
            or evidence.get("raw_transaction_sha256") != raw_hash
            or evidence.get("tx_err", False) is not None
            or event.get("frank_is_signer") is not True or evidence.get("wallet_is_signer") is not True
            or evidence.get("mechanical_classification") != "ACTIVE_SWAP_LIKE"
            or trade.get("mint") != mint or trade.get("direction") != "BUY"):
        return None
    proof = evidence.get("classification_evidence")
    if not isinstance(proof, dict) or any(proof.get(k) is not True for k in
            ("dex_program_interaction", "swap_instruction_evidence", "opposing_economic_flows")):
        return None
    tokens = _units(trade.get("token_amount_raw"), trade.get("token_decimals"))
    quote_raw, quote_decimals = trade.get("quote_amount_raw"), trade.get("quote_decimals")
    paid = _units(quote_raw, quote_decimals)
    currency = trade.get("quote_asset")
    legs = trade.get("quote_legs")
    if (tokens is None or paid is None or currency not in ("SOL", USDC, USDT)
            or trade.get("route_intermediate_evidence_status") != "NO_INTERMEDIATE_TRANSFER_OBSERVED"
            or trade.get("route_amount_semantics") != "DIRECT_OR_SINGLE_TARGET_QUOTE"
            or legs != [{"asset": currency, "raw_delta": "-" + quote_raw, "decimals": quote_decimals}]):
        return None
    return {"mint": mint, "name": asset.name, "signature": signature, "slot": slot, "at": block_time,
            "quantity": tokens, "paid": paid, "currency": {USDC: "USDC", USDT: "USDT"}.get(currency, currency)}
