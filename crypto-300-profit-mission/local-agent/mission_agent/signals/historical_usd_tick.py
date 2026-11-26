"""Offline exact-second interpretation of local Kraken Spot PostTrade captures.

The caller owns authenticated collection and the separate signed-buy binding.
A market print is a payment-asset conversion, never that buy's fiat fill.
"""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import re
from urllib.parse import urlencode

from .reconciliation import _object

_BASE = "https://api.kraken.com/0/public/PostTrade"
_ASSETS = frozenset({"SOL", "USDC", "USDT"})
_COUNT = 1000
_MAX_CAPTURE = 2 * 1024 * 1024
_DECIMAL = re.compile(r"[0-9]{1,20}(?:\.[0-9]{1,30})?\Z")
_TIMESTAMP = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.[0-9]{1,9})?Z\Z", re.ASCII)
_ID = re.compile(r"[A-Z0-9-]{1,19}\Z", re.ASCII)


def _second(value):
    if type(value) is not int or not 0 <= value <= 4_000_000_000:
        raise ValueError("INVALID_TRADE_SECOND")
    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def capture_url(asset, block_time):
    if not isinstance(asset, str) or asset not in _ASSETS:
        raise ValueError("INVALID_PAYMENT_ASSET")
    target = _second(block_time)
    if block_time == 0:
        raise ValueError("INVALID_TRADE_SECOND")
    # Kraken begins strictly after from_ts and includes to_ts.
    return _BASE + "?" + urlencode({
        "symbol": asset + "/USD", "from_ts": _second(block_time-1) + ".999999999Z",
        "to_ts": target + ".999999999Z", "count": _COUNT,
    })


def observe_usd_tick(asset, block_time, *, url, raw):
    """Accept only an unambiguous bounded market observation in that second."""
    expected = capture_url(asset, block_time)
    if url != expected or not isinstance(raw, bytes) or len(raw) > _MAX_CAPTURE:
        return {"status": "UNAVAILABLE", "reason": "CAPTURE_INVALID"}
    payload = _object(raw)
    result = payload.get("result") if isinstance(payload, dict) and not payload.get("error") else None
    if not isinstance(result, dict):
        return {"status": "UNAVAILABLE", "reason": "SOURCE_RESULT_INVALID"}
    rows, count = result.get("trades"), result.get("count")
    if not isinstance(rows, list) or type(count) is not int or count != len(rows):
        return {"status": "UNAVAILABLE", "reason": "SOURCE_COUNT_INVALID"}
    if count >= _COUNT:
        return {"status": "UNAVAILABLE", "reason": "SOURCE_WINDOW_SATURATED"}
    if not rows:
        return {"status": "UNAVAILABLE", "reason": "NO_TRADE_IN_SECOND"}
    seen, prices = {}, set()
    second = _second(block_time)
    for row in rows:
        if not isinstance(row, dict):
            return {"status": "UNAVAILABLE", "reason": "SOURCE_TRADE_INVALID"}
        stamp, ident, price = (row.get(key) for key in ("trade_ts", "trade_id", "price"))
        match = _TIMESTAMP.fullmatch(stamp) if isinstance(stamp, str) else None
        if (row.get("symbol") != asset + "/USD" or row.get("base_asset") != asset
                or row.get("quote_asset") != "USD" or match is None or match.group(1) != second
                or not isinstance(ident, str) or not _ID.fullmatch(ident) or ident in seen
                or not isinstance(price, str) or not _DECIMAL.fullmatch(price)):
            return {"status": "UNAVAILABLE", "reason": "SOURCE_TRADE_INVALID"}
        price = Decimal(price)
        if price <= 0:
            return {"status": "UNAVAILABLE", "reason": "SOURCE_TRADE_INVALID"}
        seen[ident] = stamp
        prices.add(price)
    if len(prices) != 1:
        return {"status": "UNAVAILABLE", "reason": "IN_SECOND_PRICES_DISAGREE"}

    rate = format(prices.pop(), "f")
    if "." in rate:
        rate = rate.rstrip("0").rstrip(".")
    return {"status": "OBSERVED_SECOND_CONVERSION", "scope": "PAYMENT_ASSET_MARKET_TRADE_NOT_FIAT_FILL",
            "source": "KRAKEN_SPOT_POST_TRADE", "source_url": url,
            "source_at": block_time, "source_sha256": hashlib.sha256(raw).hexdigest(),
            "matched_trade_count": len(seen), "usd_per_quote_unit": rate,
            "matched_trades": [{"id": ident, "trade_ts": stamp} for ident, stamp in sorted(seen.items())]}
