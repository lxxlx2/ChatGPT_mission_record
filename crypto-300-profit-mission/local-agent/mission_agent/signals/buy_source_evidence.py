"""Read normalized, locally trusted source captures for buy classification and USD."""
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
import re
import stat

from ..meme.market_parity import number
from .classifier import USDT
from .policy import USDC
from .reconciliation import _base58_size, _unique_pairs


CAPTURE_NAME = "frank-buy-source-captures.json"
_QUOTE_ASSETS = frozenset(("SOL", USDC, USDT))
_MAX_BYTES = 4 * 1024 * 1024


def _open_capture(path, flags):
    fd = os.open(path, flags | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise OSError("BUY_SOURCE_CAPTURE_FILE_REQUIRED")
    return fd


def load_captures(path, as_of):
    if path is None:
        return {}, {}, None
    try:
        with open(path, "rb", opener=_open_capture) as source:
            raw = source.read(_MAX_BYTES + 1)
        if len(raw) > _MAX_BYTES:
            return {}, {}, None
        data = json.loads(raw, object_pairs_hook=_unique_pairs, parse_float=Decimal)
    except (OSError, ValueError, InvalidOperation, RecursionError):
        return {}, {}, None
    if (not isinstance(data, dict) or type(data.get("version")) is not int
            or data["version"] != 1 or not isinstance(data.get("captures"), list)):
        return {}, {}, None

    categories, usd = {}, {}
    for row in data["captures"]:
        if not isinstance(row, dict):
            continue
        at, source, sha = row.get("observed_at"), row.get("source"), row.get("source_sha256")
        if (type(at) is not int or not 0 < at <= as_of or not isinstance(source, str)
                or not 0 < len(source.strip()) <= 384 or not isinstance(sha, str)
                or not re.fullmatch("[a-f0-9]{64}", sha)):
            continue
        if row.get("kind") == "EXACT_MINT_CATEGORY" and row.get("chain") == "solana":
            mint, category, name = row.get("mint"), row.get("category"), row.get("name")
            if not _base58_size(mint, 32) or category not in ("MEME", "NON_MEME"):
                continue
            if name is not None and (not isinstance(name, str) or not 0 < len(name.strip()) <= 80):
                continue
            value = ("VERIFIED_MEME" if category == "MEME" else "EXCLUDED",
                     source.strip() + "#" + sha, at, name.strip() if name else None)
            prior = categories.get(mint)
            if mint not in categories:
                categories[mint] = value
            elif prior is not None and prior[0] == value[0] and value[2] < prior[2]:
                categories[mint] = value
            elif prior is not None and prior[0] != value[0]:
                categories[mint] = None
        elif row.get("kind") == "QUOTE_USD_OBSERVATION":
            asset, quote_time = row.get("asset"), row.get("quote_time")
            if not isinstance(asset, str) or asset not in _QUOTE_ASSETS or type(quote_time) is not int or not 0 < quote_time <= at:
                continue
            price = number(row.get("usd_per_unit"))
            if price is None or Decimal(price) <= 0:
                continue
            key = (asset, quote_time)
            value = Decimal(price)
            if key not in usd:
                usd[key] = value
            elif usd[key] != value:
                usd[key] = None
    return categories, usd, hashlib.sha256(raw).hexdigest()
