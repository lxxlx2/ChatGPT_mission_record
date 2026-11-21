"""Amount-free analysis of immutable wallet facts and captured observations."""
from collections import defaultdict
from decimal import Decimal, InvalidOperation
import re

from ..meme.holder_ranks import valid_pubkey
from ..signals.policy import USDC
from .evidence_manifests import digest
from .intelligence import analyze_candidate
from .market_observations import comparable_usdc_market
from .wallet_cost_fifo import _verified_archive
from .wallet_facts import _raw

SHA = re.compile(r"[0-9a-f]{64}")
MARKET_MAX_AGE = 60


def _epoch(value):
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not converted.is_finite() or not 1_600_000_000 < converted < 4_000_000_000:
        return None
    return float(converted)


def _usdc_buy_price(exchange):
    if not isinstance(exchange, dict):
        return None
    quotes = exchange.get("quotes")
    if (exchange.get("basis") != "VERIFIED_WALLET_BOUNDARY_SINGLE_TARGET"
            or not isinstance(quotes, list) or len(quotes) != 1 or quotes[0].get("mint") != USDC):
        return None
    quote = quotes[0]
    spent = _raw(quote.get("raw_delta"), signed=True)
    tokens = _raw(exchange.get("token_amount_raw"))
    decimals, quote_decimals = exchange.get("token_decimals"), quote.get("decimals")
    if (spent is None or int(spent) >= 0 or tokens in (None, "0")
            or type(decimals) is not int or not 0 <= decimals <= 255 or quote_decimals != 6):
        return None
    return str(Decimal(-int(spent)).scaleb(decimals - quote_decimals) / Decimal(tokens))


def _action_events(row, cutoff):
    fact = row.get("transaction_fact")
    if not isinstance(fact, dict):
        return
    archived = _verified_archive(fact)
    if not archived or archived.get("execution_status") != "SUCCEEDED":
        return
    at, slot = _epoch(archived.get("event_at")), archived.get("slot")
    evidence_id, signature = fact.get("fact_id"), archived.get("signature")
    if (at is None or at > cutoff or type(slot) is not int or slot < 0
            or not isinstance(evidence_id, str) or not SHA.fullmatch(evidence_id)
            or not isinstance(signature, str) or not signature):
        return
    exchange = archived.get("economic_exchange")
    balances = defaultdict(int)
    for balance in archived.get("token_account_balances") or []:
        delta = _raw(balance.get("delta_raw"), signed=True)
        if delta is not None:
            balances[(balance.get("mint"), balance.get("decimals"))] += int(delta)
    actions = {}
    for leg in fact.get("trade_legs") or []:
        mint, token = leg.get("mint"), leg.get("recorded_token")
        if not valid_pubkey(mint) or not isinstance(token, dict):
            continue
        direction, amount = token.get("direction"), _raw(token.get("raw_amount"))
        wallet_delta = balances[(mint, token.get("decimals"))]
        if (amount in (None, "0") or direction not in ("BUY", "SELL") or
                wallet_delta != int(amount) * (1 if direction == "BUY" else -1)):
            continue
        # Only use the durable indexed classifier for trade intent when the same
        # original transaction was classified as an active trade on replay.
        if fact.get("archived_replay", {}).get("replayed_class") == "ACTIVE_TRADE":
            actions[mint] = (direction, leg.get("side") == "REENTRY", None)
    if isinstance(exchange, dict) and exchange.get("basis") == "VERIFIED_WALLET_BOUNDARY_SINGLE_TARGET":
        mint, side = exchange.get("mint"), exchange.get("side")
        if valid_pubkey(mint) and side in ("BUY", "SELL"):
            actions[mint] = (side, actions.get(mint, (None, False, None))[1],
                             _usdc_buy_price(exchange) if side == "BUY" else None)
    for mint, (side, reentry, buy_price) in actions.items():
        yield mint, {"side": side, "signature": signature, "observed_at": at, "slot": slot,
                     "fact_id": evidence_id, "reentry": reentry, "buy_price": buy_price}


def build_risk_inputs(metadata, frozen_rows, *, position_snapshot, market, as_of):
    """Bind durable analysis to a fixed fact set and present-time market age."""
    cutoff = _epoch(metadata.get("as_of"))
    now = _epoch(as_of)
    if cutoff is None or now is None or cutoff > now:
        raise ValueError("INVALID_RISK_SOURCE_CUTOFF")
    history = defaultdict(list)
    for row in frozen_rows:
        for mint, event in _action_events(row, cutoff):
            history[mint].append(event)
    positions = {}
    pos_at = _epoch(position_snapshot.get("observed_at")) if isinstance(position_snapshot, dict) else None
    expiry = _epoch(position_snapshot.get("expires_at")) if isinstance(position_snapshot, dict) else None
    if pos_at is not None and expiry is not None and pos_at <= now <= expiry:
        for record in position_snapshot["rows"]:
            mint = record.get("mint")
            raw, decimals = _raw(record.get("raw_amount")), record.get("decimals")
            if valid_pubkey(mint) and raw is not None and type(decimals) is int and 0 <= decimals <= 255:
                positions[mint] = {"mint": mint, "observed_at": pos_at, "raw_amount": raw,
                                   "decimals": decimals, "verification": "COMPLETE_CAPTURE"}
    analyzed = []
    for mint, events in sorted(history.items()):
        latest_slot = max(e["slot"] for e in events)
        latest = [e for e in events if e["slot"] == latest_slot]
        event = latest[0] if len(latest) == 1 else None
        buys = [e for e in events if e["side"] == "BUY"]
        latest_buy_slot = max((e["slot"] for e in buys), default=-1)
        latest_buy = [e for e in buys if e["slot"] == latest_buy_slot]
        buy = latest_buy[0] if len(latest_buy) == 1 else None
        candidate = {"mint": mint, "buy_count": len(buys), "sell_count": len(events)-len(buys)}
        if event:
            candidate.update(latest_side=event["side"], latest_at=event["observed_at"],
                             latest_signature=event["signature"])
        if buy and buy["buy_price"] is not None:
            candidate.update(latest_buy_at=buy["observed_at"], latest_buy_price_usdc=buy["buy_price"],
                             latest_buy_price_status="USDC_DIRECT")
        reference = comparable_usdc_market(mint, market, as_of=now, max_age_seconds=MARKET_MAX_AGE)
        result = analyze_candidate(candidate, as_of=now, market=reference, max_market_age_seconds=MARKET_MAX_AGE)
        if not event:
            result["missing"].append("LATEST_SLOT_ORDER_UNVERIFIED")
        else:
            result["latest_fact_id"] = event["fact_id"]
        if position := positions.get(mint):
            result["position"] = position
        if event and event["side"] == "BUY":
            first = [e for e in buys if e["reentry"] and e["slot"] <= event["slot"]]
            if first:
                recent = max(e["slot"] for e in first)
                matches = [e for e in first if e["slot"] == recent]
                if len(matches) == 1 and not any(e["side"] == "SELL" and e["slot"] >= recent for e in events):
                    result["reentry"] = {k: matches[0][k] for k in ("signature", "observed_at")}
        captured = market.get(mint)
        if isinstance(captured, dict):
            when = _epoch(captured.get("observed_at"))
            original_hash = captured.get("observation_sha256")
            if original_hash == digest({k: v for k, v in captured.items() if k != "observation_sha256"}):
                result["market_reference"] = captured
                result["price"]["conversion_evidence"] = reference.get("conversion_evidence") if reference else None
                fresh = when is not None and 0 <= now-when <= MARKET_MAX_AGE and captured.get("status") == "OK"
                result["price"]["reference_status"] = "FRESH_CAPTURE" if fresh else "STALE_OR_UNAVAILABLE"
                result["price"]["reference_observed_at"] = when if when is not None and when <= now else None
                if reference is None and captured.get("status") == "OK" and when is not None:
                    if "MARKET_REFERENCE_MISSING" in result["missing"]:
                        result["missing"].remove("MARKET_REFERENCE_MISSING")
                    if when > now:
                        result["missing"].append("MARKET_REFERENCE_AFTER_AS_OF")
                    elif fresh:
                        result["missing"].append("COMPARABLE_CURRENCY_CONVERSION_UNAVAILABLE")
                    else:
                        result["missing"].append("MARKET_REFERENCE_STALE")
        analyzed.append(result)
    return {"as_of": now, "rows": analyzed,
            "source_refs": {"facts_sha256": metadata["manifest_sha256"], "fact_manifest_id": metadata["manifest_id"],
                            "fact_as_of": cutoff, "position_sha256": digest(position_snapshot) if positions else None,
                            "market_sha256": digest(market) if market else None}}
