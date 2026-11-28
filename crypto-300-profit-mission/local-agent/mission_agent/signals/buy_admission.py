"""Local, explicit asset qualification and conservative buy admission.

No symbol, venue, quote mint or classifier verdict alone establishes Meme identity.
Unknown, conflicting and explicitly excluded records fail closed.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

from ..meme.holder_ranks import valid_pubkey
from ..frank.parser import DEX_PROGRAMS
from .classifier import QUOTE_MINTS, USDT, transaction_market_trades
from .policy import BUY_DELIVERY_MAX_AGE_SECONDS, USDC
from .reconciliation import _base58_size

# Independently documented non-Meme asset identities. Match the complete mint,
# never a ticker; a local positive label cannot override known exclusion.
# https://learn.backpack.exchange/blog/backpack-token-ticker-bp
BACKPACK_MINT = "BPxxfRCXkUVhig4HS1Lh7kZqV6SPJhzfEk4x6fVBjPCy"
EXCLUDED_MINTS = QUOTE_MINTS | {BACKPACK_MINT}


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
    def open_regular(local_path, flags):
        fd = os.open(local_path, flags | os.O_NONBLOCK)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise ValueError("QUALIFICATION_FILE_REQUIRED")
        return fd

    with open(path, "rb", opener=open_regular) as f:
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


MEME_SCOPE_BLOCKED = "MEME_SCOPE_BLOCKED"


def qualification_path(path=None, *, default=None):
    configured = path or os.environ.get("FRANK_BUY_QUALIFICATIONS_PATH") or default
    return Path(configured) if configured else None


def effective_qualification(manual_path, category_path, as_of, *, scanner_db=None, auto_mint=None):
    """Apply explicit local manual choices over validated category receipts."""
    from .category_evidence import read_category_evidence

    receipts = read_category_evidence(category_path, as_of)
    if scanner_db is not None:
        from .category_evidence import merge_category_assets, read_scanner_category_evidence

        receipts = merge_category_assets(receipts, read_scanner_category_evidence(scanner_db, as_of, mint=auto_mint))
    try:
        if manual_path is None:
            raise FileNotFoundError("MANUAL_QUALIFICATION_UNAVAILABLE")
        receipts.update(qualification(manual_path, as_of))
    except FileNotFoundError:
        if not receipts:
            raise
    return receipts


class BuyDeliveryGate:
    """Local evidence required for a new Frank notification."""

    def __init__(self, path=None, *, clock=time.time, category_evidence_path=None):
        self.path = qualification_path(path)
        # Existing deployments must opt in explicitly; no source is fetched here.
        self.category_evidence_path = Path(category_evidence_path) if category_evidence_path is not None else None
        self.clock = clock

    def block_reason(self, db, signal):
        return self.assess(db, signal, for_delivery=True)[1]

    def assess(self, db, signal, *, for_delivery=False):
        if not isinstance(signal, dict):
            return None, "TRIGGER_IS_NOT_PROVEN_BUY"
        if signal.get("delivery_mode") != "LIVE" or signal.get("delivery_forbidden"):
            return None, "HISTORICAL_DELIVERY_FORBIDDEN"
        if signal.get("person_id") != "frank":
            return None, "NOT_FRANK_BUY"
        mint = signal.get("mint")
        if not exact_mint(mint):
            return None, "INVALID_SOLANA_MINT"
        if mint in EXCLUDED_MINTS:
            return None, "EXCLUDED_NON_MEME_MINT"
        signature = signal.get("triggering_signature")
        if (not _base58_size(signature, 64)
                or signature != signal.get("latest_trade_signature")
                or signature != signal.get("latest_buy_signature")):
            return None, "TRIGGER_IS_NOT_PROVEN_BUY"
        as_of = int(self.clock())
        try:
            assets = effective_qualification(self.path, self.category_evidence_path, as_of, scanner_db=db, auto_mint=mint)
        except (OSError, ValueError, RecursionError):
            return None, "MEME_QUALIFICATION_UNAVAILABLE"
        asset = assets.get(mint)
        if not asset or asset.status != "VERIFIED_MEME":
            return None, ("MEME_QUALIFICATION_EXCLUDED" if asset and asset.status == "EXCLUDED"
                          else "MEME_QUALIFICATION_UNPROVEN")

        rows = db.execute(
            "SELECT wallet, signature, slot, block_time, raw_hash, body FROM signatures "
            "WHERE person_id = ? AND signature = ? LIMIT 2", ("frank", signature),
        ).fetchall()
        if len(rows) == 1:
            row = rows[0]
            try:
                evidence = json.loads(row["body"])
            except (TypeError, ValueError):
                evidence = None
            fact = admit_buy(evidence, assets, wallet=row["wallet"], signature=row["signature"],
                             slot=row["slot"], block_time=row["block_time"], raw_hash=row["raw_hash"], mint=mint)
            if fact:
                frozen = signal.get("verified_buy")
                trigger = signal.get("triggered_at")
                if for_delivery and frozen is None:
                    # With no enqueue-time proof, a newly observed classification
                    # must not turn an old pending signal into a new notification.
                    if type(trigger) is not int or trigger <= 0:
                        return None, "LEGACY_SIGNAL_TRIGGER_TIME_UNVERIFIED"
                    if asset.observed_at > trigger:
                        return None, "LEGACY_QUALIFICATION_OBSERVED_LATE"
                if frozen is not None and (
                    not isinstance(frozen, dict)
                    or any(frozen.get(key) != value for key, value in fact.items() if key != "name")
                ):
                    return None, "FROZEN_BUY_FACT_CONFLICT"
                stage = signal.get("signal_type")
                if not isinstance(stage, str) or type(trigger) is not int or not fact["at"] <= trigger <= as_of:
                    return None, "BUY_NOTIFICATION_TIME_UNVERIFIED"
                max_age = BUY_DELIVERY_MAX_AGE_SECONDS.get(stage)
                if max_age is None:
                    return None, "BUY_NOTIFICATION_TIME_UNVERIFIED"
                if as_of - fact["at"] > max_age:
                    return None, "BUY_NOTIFICATION_EXPIRED"
                return fact, None
        return None, "TRIGGER_IS_NOT_PROVEN_BUY"


def _units(raw, decimals):
    if (not isinstance(raw, str) or not re.fullmatch(r"[1-9][0-9]{0,29}", raw)
            or type(decimals) is not int or not 0 <= decimals <= 255):
        return None
    if not decimals:
        return raw
    raw = raw.zfill(decimals + 1)
    fraction = raw[-decimals:].rstrip("0")
    return raw[:-decimals] + ("." + fraction if fraction else "")


def _buy_trade(event, mint, leg_index):
    legs = event.get("trade_legs")
    if legs is None:
        trade = event.get("trade")
        return trade if leg_index is None and isinstance(trade, dict) else None
    if event.get("trade") is not None or not isinstance(legs, list) or len(legs) < 2:
        return None
    indices = set()
    for leg in legs:
        if not isinstance(leg, dict) or leg.get("direction") != "BUY":
            return None
        index, proof = leg.get("leg_index"), leg.get("instruction_evidence")
        if (type(index) is not int or index < 0 or index in indices or not isinstance(proof, dict)
                or not isinstance(proof.get("program"), str) or proof["program"] not in DEX_PROGRAMS
                or not exact_mint(leg.get("mint"))):
            return None
        refs = [proof.get(key) for key in ("target_transfer", "payment_transfer")]
        if (any(not isinstance(ref, str) or not re.fullmatch(fr"{index}:[0-9]+", ref) for ref in refs)
                or refs[0] == refs[1]):
            return None
        indices.add(index)
    if leg_index is not None:
        return next((leg for leg in legs if type(leg_index) is int and leg["leg_index"] == leg_index
                     and leg["mint"] == mint), None)
    try:
        return next((trade for trade in transaction_market_trades(event) if trade["mint"] == mint), None)
    except (KeyError, TypeError, ValueError):
        return None


def admit_buy(event, assets, *, wallet, signature, slot, block_time, raw_hash, mint, allow_unpriced=False, leg_index=None):
    """Return only facts bound to this classified, archived wallet event."""
    asset = assets.get(mint)
    if not asset or asset.status != "VERIFIED_MEME" or mint in EXCLUDED_MINTS or not exact_mint(mint):
        return None
    if not isinstance(event, dict) or event.get("classification") != "ACTIVE_TRADE":
        return None
    evidence, trade = event.get("evidence"), _buy_trade(event, mint, leg_index)
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
            or legs != [{"asset": currency, "raw_delta": "-" + quote_raw, "decimals": quote_decimals}]):
        return None
    route_evidence = trade.get("route_intermediate_evidence_status")
    route_amount = trade.get("route_amount_semantics")
    if route_evidence != "NO_INTERMEDIATE_TRANSFER_OBSERVED" or route_amount != "DIRECT_OR_SINGLE_TARGET_QUOTE":
        # A routed swap may prove the wallet's single final receipt while its
        # total outflow cannot be attributed to the target. Only the read-only
        # buy page can show that receipt without attaching an amount paid.
        before, after = trade.get("referenced_pre_raw"), trade.get("referenced_post_raw")
        intermediates = trade.get("route_intermediate_assets")
        if (not allow_unpriced or route_evidence != "UNVERIFIED"
                or route_amount != "GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST"
                or not isinstance(intermediates, list) or not intermediates
                or not isinstance(before, str) or not isinstance(after, str)
                or not re.fullmatch(r"[0-9]{1,30}", before) or not re.fullmatch(r"[0-9]{1,30}", after)
                or int(after) - int(before) != int(trade["token_amount_raw"])):
            return None
        paid, currency = None, None
    fact = {"mint": mint, "name": asset.name, "signature": signature, "slot": slot, "at": block_time,
            "quantity": tokens, "paid": paid, "currency": {USDC: "USDC", USDT: "USDT"}.get(currency, currency)}
    if trade.get("leg_indices"):
        fact["leg_indices"] = trade["leg_indices"]
    elif type(trade.get("leg_index")) is int:
        fact["leg_index"] = trade["leg_index"]
    return fact


def needs_archive_replay(event, identity):
    if not isinstance(event, dict) or event.get("classification") != "ACTIVE_TRADE":
        return False
    trade, evidence = event.get("trade"), event.get("evidence")
    return (
        isinstance(trade, dict) and isinstance(evidence, dict)
        and identity["mint"] not in EXCLUDED_MINTS
        and trade.get("mint") == identity["mint"] and trade.get("direction") == "BUY"
        and event.get("frank_is_signer") is True and evidence.get("wallet_is_signer") is True
        and evidence.get("raw_transaction_sha256") == identity["raw_hash"]
        and all(source.get(key) == identity[key] for source in (event, evidence)
                for key in ("wallet", "signature", "slot", "block_time"))
        and not {"quote_legs", "route_amount_semantics", "route_intermediate_evidence_status"} & trade.keys()
    )
