"""Multi-mint USD market observations and pure provided-position valuation.

Only ``capture_market`` calls an injected ``token_snapshot`` client.  The existing
DexScreener client is scoped to /token-pairs/v1/solana; its snapshot does not carry
chainId, so absent chain fields inherit that explicit client contract.  Explicit
chain conflicts and wrong mint/pair fields are rejected here as well.

Prices are indexer USD references, not USDC balances, executable quotes or PnL.
Snapshot hashes cover canonical client output, never claim raw HTTP provenance.
Retrieval freshness does not establish the source's market observation time.
There is no scheduler, storage mutation, portfolio discovery or notification.
"""
from __future__ import annotations

from decimal import Decimal, DecimalException, InvalidOperation, localcontext, MAX_EMAX, MIN_EMIN
import hashlib
import json
import math
import re
import time
import uuid

from ..meme.holder_ranks import valid_pubkey


SOURCE = "DEXSCREENER_API"
CHAIN = "solana"


def _hash(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _seal(record):
    return {**record, "observation_sha256": _hash(record)}


def _time(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value > 0 else None


def _number(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    try:
        parsed = Decimal(str(value))
        if not parsed.is_finite() or parsed < 0 or (positive and parsed == 0):
            return None
        return parsed
    except (InvalidOperation, ValueError, TypeError):
        return None


def _reason(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", value) else "SOURCE_UNAVAILABLE"


def _chain_matches(value):
    return not isinstance(value, dict) or all(value.get(key, CHAIN) == CHAIN
                                             for key in ("chain", "chain_id", "chainId"))


def normalize_market(mint, snapshot, *, received_at):
    """Normalize one exact-mint snapshot, retaining every failure as a record.

    ``received_at`` is supplied by the caller after retrieval. ``observed_at`` is
    the client's recorded retrieval timestamp; neither proves market as-of time.
    """
    if _time(received_at) is None:
        raise ValueError("RECEIVED_TIME_INVALID")
    record = {"version": 1, "chain_id": CHAIN, "mint": mint, "source": SOURCE,
              "status": "UNAVAILABLE", "reason": None, "price_usd": None,
              "market_cap_usd": None, "fdv_usd": None, "liquidity_usd": None,
              "volume_h24_usd": None, "main_pair": None,
              "observed_at": None, "received_at": received_at,
              "source_market_asof": None,
              "freshness_basis": "CLIENT_RETRIEVAL_TIME_NOT_MARKET_ASOF",
              "source_payload_sha256": None, "source_ref": None,
              "source_hash_kind": "CANONICAL_CLIENT_SNAPSHOT_NOT_RAW_HTTP",
              "identity_basis": "SOLANA_SCOPED_CLIENT_AND_EXACT_PAIR_FIELDS",
              "currency": "USD", "executable_quote": False}

    def unavailable(reason):
        return _seal({**record, "reason": reason})

    if not valid_pubkey(mint):
        return unavailable("MINT_INVALID")
    if not isinstance(snapshot, dict):
        return unavailable("RESPONSE_INVALID")
    try:
        record["source_payload_sha256"] = _hash(snapshot)
    except (ValueError, TypeError):
        return unavailable("RESPONSE_NOT_CANONICAL_JSON")
    if snapshot.get("source") != SOURCE:
        return unavailable("SOURCE_IDENTITY_MISMATCH")
    if not _chain_matches(snapshot):
        return unavailable("CHAIN_IDENTITY_MISMATCH")
    observed = _time(snapshot.get("observed_at"))
    record["observed_at"] = observed
    if observed is None:
        return unavailable("OBSERVATION_TIME_INVALID")
    if observed > received_at:
        return unavailable("FUTURE_OBSERVATION")
    ref = snapshot.get("source_ref")
    if ref is not None:
        required = {"schema_version", "provider_id", "method", "request_hash", "response_sha256",
                    "observed_at", "received_at", "slot", "commitment", "receipt_id"}
        try:
            if (not isinstance(ref, dict) or set(ref) != required or ref["schema_version"] != 1
                    or not re.fullmatch(r"provider_[0-9a-f]{64}", ref["provider_id"])
                    or not all(re.fullmatch(r"[0-9a-f]{64}", ref[k]) for k in ["request_hash", "response_sha256"])
                    or ref["method"] != "GET" or str(uuid.UUID(ref["receipt_id"])) != ref["receipt_id"]
                    or Decimal(str(ref["observed_at"])) != Decimal(str(observed))
                    or not Decimal(str(observed)) <= Decimal(str(ref["received_at"])) <= Decimal(str(received_at))):
                return unavailable("SOURCE_REFERENCE_INVALID")
        except (ValueError, TypeError, AttributeError, KeyError, InvalidOperation):
            return unavailable("SOURCE_REFERENCE_INVALID")
        record["source_ref"] = dict(ref)
    if snapshot.get("status") != "OK":
        return unavailable(_reason(snapshot.get("reason")))
    pair = snapshot.get("main_pair")
    if snapshot.get("mint") != mint:
        return unavailable("MINT_IDENTITY_MISMATCH")
    if not isinstance(pair, dict) or not _chain_matches(pair):
        return unavailable("PAIR_IDENTITY_MISMATCH")
    address, quote = pair.get("pair_address"), pair.get("quote_address")
    if (pair.get("base_address") != mint or not valid_pubkey(address)
            or not valid_pubkey(quote) or len({mint, address, quote}) != 3):
        return unavailable("PAIR_IDENTITY_MISMATCH")
    record["main_pair"] = {"pair_address": address, "base_address": mint,
                           "quote_address": quote, "dex_id": pair.get("dex_id")}
    for key, value in (("market_cap_usd", snapshot.get("market_cap_usd")),
                       ("fdv_usd", snapshot.get("fdv_usd")),
                       ("liquidity_usd", pair.get("liquidity_usd")),
                       ("volume_h24_usd", (pair.get("volume") or {}).get("h24")
                        if isinstance(pair.get("volume"), dict) else None)):
        number = _number(value)
        record[key] = str(number) if number is not None else None
    price = _number(snapshot.get("price_usd"), positive=True)
    if price is None:
        return _seal({**record, "status": "UNAVAILABLE", "reason": "USD_PRICE_UNAVAILABLE"})
    return _seal({**record, "status": "OK", "reason": None, "price_usd": str(price)})


def capture_market(mints, client, clock=time.time):
    """Capture all requested distinct mints through the existing injected client.

    No count cap: duplicate navigation inputs are deduplicated, every unique mint
    has a success/failure record, and one failed source read does not erase others.
    The caller owns persistence; this function does not touch a file or database.
    """
    requested = list(mints)
    if any(not isinstance(mint, str) for mint in requested):
        raise ValueError("MINT_INPUT_TYPE_INVALID")
    unique = list(dict.fromkeys(requested))
    records = []
    for mint in unique:
        if not valid_pubkey(mint):
            records.append(normalize_market(mint, None, received_at=clock()))
            continue
        try:
            snapshot = client.token_snapshot(mint)
        except Exception as exc:
            # Never copy exception text: it can contain a URL, key or response.
            snapshot = {"status": "UNAVAILABLE", "source": SOURCE,
                        "observed_at": clock(),
                        "reason": "SOURCE_TIMEOUT" if isinstance(exc, TimeoutError) else "SOURCE_READ_FAILED"}
        records.append(normalize_market(mint, snapshot, received_at=clock()))
    return records


def _observations(value):
    if isinstance(value, dict) and isinstance(value.get("observations"), list):
        rows = value["observations"]
    elif isinstance(value, dict):
        rows = list(value.values())
    else:
        rows = list(value)
    grouped = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("mint"), str):
            continue
        mint = row["mint"]
        if mint in grouped and grouped[mint] != row:
            grouped[mint] = None
        else:
            grouped[mint] = row
    return grouped


def portfolio_valuation(positions, observations, as_of, max_age_seconds=60):
    """Pure USD reference valuation of the supplied positions, with no source IO.

    Position rows require exact ``mint``, integer-string/int ``raw_amount`` (or
    legacy ``raw``) and integer
    ``decimals`` (0..255). No USD-to-USDC assumption, cost basis, realized PnL or
    full-wallet completeness claim is made. Unknown rows never become zero NAV.
    """
    if _time(as_of) is None:
        raise ValueError("AS_OF_TIME_INVALID")
    if (type(max_age_seconds) not in (int, float) or not math.isfinite(max_age_seconds)
            or max_age_seconds < 0):
        raise ValueError("MAX_AGE_INVALID")
    observed = _observations(observations)
    rows, values = [], []
    for position in positions:
        row = {"mint": position.get("mint") if isinstance(position, dict) else None,
               "status": "UNPRICED", "reason": None, "quantity": None,
               "price_usd": None, "value_usd": None, "currency": "USD",
               "observation_sha256": None, "source_payload_sha256": None}
        reason = None
        mint = row["mint"]
        raw = position.get("raw_amount", position.get("raw")) if isinstance(position, dict) else None
        decimals = position.get("decimals") if isinstance(position, dict) else None
        if (not isinstance(position, dict) or not valid_pubkey(mint)
                or not _chain_matches(position)
                or not ((type(raw) is int and raw >= 0)
                        or (isinstance(raw, str) and re.fullmatch(r"[0-9]+", raw)))
                or type(decimals) is not int or not 0 <= decimals <= 255):
            reason = "POSITION_INVALID"
        else:
            observation = observed.get(mint)
            try:
                valid_hash = (isinstance(observation, dict)
                              and observation.get("observation_sha256") == _hash(
                                  {k: v for k, v in observation.items() if k != "observation_sha256"}))
            except (TypeError, ValueError):
                valid_hash = False
            if not valid_hash:
                reason = "OBSERVATION_MISSING_OR_INVALID"
            elif (observation.get("mint") != mint or observation.get("chain_id") != CHAIN
                  or observation.get("source") != SOURCE or observation.get("currency") != "USD"):
                reason = "OBSERVATION_IDENTITY_MISMATCH"
            elif observation.get("status") != "OK":
                reason = observation.get("reason") or "USD_PRICE_UNAVAILABLE"
            else:
                when = _time(observation.get("observed_at"))
                price = _number(observation.get("price_usd"), positive=True)
                if when is None:
                    reason = "OBSERVATION_TIME_INVALID"
                elif when > as_of:
                    reason = "FUTURE_OBSERVATION"
                elif as_of - when > max_age_seconds:
                    reason = "STALE_OBSERVATION"
                elif price is None:
                    reason = "USD_PRICE_UNAVAILABLE"
                else:
                    try:
                        with localcontext() as ctx:
                            ctx.prec = max(28, len(str(raw)) + len(price.as_tuple().digits) + decimals + 4)
                            ctx.Emax, ctx.Emin = MAX_EMAX, MIN_EMIN
                            quantity = Decimal(raw).scaleb(-decimals)
                            value = quantity * price
                        if not value.is_finite():
                            raise InvalidOperation
                        row.update(status="PRICED", quantity=str(quantity), price_usd=str(price),
                                   value_usd=str(value), observation_sha256=observation["observation_sha256"],
                                   source_payload_sha256=observation["source_payload_sha256"])
                        values.append(value)
                    except DecimalException:
                        reason = "VALUATION_NUMBER_INVALID"
        row["reason"] = reason
        rows.append(row)
    try:
        with localcontext() as ctx:
            # Preserve every coefficient across addition as well as row products.
            nonzero = [v for v in values if v]
            high = max((v.adjusted() for v in nonzero), default=0)
            low = min((v.as_tuple().exponent for v in nonzero), default=0)
            precision = max(28, high - low + len(str(len(values) or 1)) + 2)
            # If a hostile exponent would require an unbounded expanded output,
            # keep all original rows but decline the exact sum. Never round it
            # into a purported total or allocate arbitrary memory from source text.
            if precision > 10000:
                raise InvalidOperation
            ctx.prec = precision
            ctx.Emax, ctx.Emin = MAX_EMAX, MIN_EMIN
            subtotal = sum(values, Decimal(0))
    except DecimalException:
        subtotal = None
    covered = sum(row["status"] == "PRICED" for row in rows)
    complete = covered == len(rows) and subtotal is not None
    return {"version": 1, "chain_id": CHAIN, "currency": "USD", "as_of": as_of,
            "status": "OK" if complete else "PARTIAL" if covered else "UNAVAILABLE",
            "scope": "PROVIDED_POSITIONS_ONLY", "freshness_basis": "CLIENT_RETRIEVAL_TIME_NOT_MARKET_ASOF",
            "rows": rows, "covered_positions": covered, "unpriced_positions": len(rows) - covered,
            "priced_subtotal_usd": str(subtotal) if subtotal is not None else None,
            "total_value_usd": str(subtotal) if complete else None,
            "valuation_complete_for_provided_positions": complete,
            "executable_quote": False, "pnl_calculated": False}
