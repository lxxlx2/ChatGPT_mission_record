"""Explicit ExactIn reference quotes over the existing free Jupiter source."""

from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .jupiter import JupiterQuoteClient, _retry_after_seconds
from ..meme.holder_ranks import valid_pubkey


SOURCE = "JUPITER_OFFICIAL"
ENDPOINT = "https://api.jup.ag/swap/v1/quote"
QUOTE_TTL_SECONDS = 30
MAX_SLIPPAGE_BPS = 10_000
U64_MAX = 2**64 - 1
_FIELDS = {"mint", "input_mint", "input_amount_raw", "slippage_bps"}
_NO_ROUTE_CODES = {"COULD_NOT_FIND_ANY_ROUTE", "NO_ROUTES_FOUND"}


class QuoteError(ValueError):
    """Safe error values for the local HTTP layer."""

    def __init__(self, code: str, http_status: int = 400):
        super().__init__(code)
        self.code = code
        self.http_status = http_status


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ExplicitJupiterQuoteClient(JupiterQuoteClient):
    """Use the same quote endpoint and pacing, with raw response bytes for provenance."""

    def __init__(self, api_key=None, *, open_url=None, minimum_interval_seconds=None,
                 rate_limit_cooldown_seconds=None):
        if api_key is not None:
            raise ValueError("EXPLICIT_QUOTE_REQUIRES_FREE_KEYLESS_SOURCE")
        super().__init__(
            None,
            endpoint=ENDPOINT,
            open_url=open_url if open_url is not None else build_opener(_NoRedirect()).open,
            minimum_interval_seconds=minimum_interval_seconds,
            rate_limit_cooldown_seconds=rate_limit_cooldown_seconds,
        )
        self._last_request_monotonic = float("-inf")
        self._quote_lock = threading.Lock()

    def quote_exact_in(self, input_mint, output_mint, amount_raw, slippage_bps):
        query = urlencode({
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_raw,
            "slippageBps": slippage_bps,
            "swapMode": "ExactIn",
            "instructionVersion": "V2",
        })
        request = Request(
            ENDPOINT + "?" + query,
            headers={"User-Agent": "mission-meme-v1/1", "Accept": "application/json", "Cache-Control": "no-cache"},
            method="GET",
        )
        with self._quote_lock:
            now = time.monotonic()
            if now < max(self._last_request_monotonic + self.minimum_interval_seconds,
                         self._cooldown_until_monotonic):
                raise QuoteError("JUPITER_RATE_LIMITED", 503)
            self._last_request_monotonic = now
            try:
                with self.open_url(request, timeout=8) as response:
                    return response.status, response.read()
            except HTTPError as exc:
                if exc.code == 429:
                    cooldown = max(self.rate_limit_cooldown_seconds, _retry_after_seconds(exc))
                    self._cooldown_until_monotonic = time.monotonic() + cooldown
                    exc.close()
                    raise QuoteError("JUPITER_RATE_LIMITED", 503) from None
                with exc:
                    return exc.code, exc.read()
            except (URLError, TimeoutError, OSError):
                raise QuoteError("JUPITER_NETWORK_UNAVAILABLE", 503) from None


def _valid_raw_amount(value, *, allow_zero=False):
    return (
        isinstance(value, str)
        and re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is not None
        and (allow_zero or value != "0")
        and int(value) <= U64_MAX
    )


def _validate_input(body):
    if not isinstance(body, dict) or set(body) != _FIELDS:
        raise QuoteError("EXPLICIT_QUOTE_INPUT_REQUIRED")
    input_mint, mint = body["input_mint"], body["mint"]
    if not valid_pubkey(input_mint) or not valid_pubkey(mint) or mint == input_mint:
        raise QuoteError("INVALID_QUOTE_MINT_PAIR")
    if not _valid_raw_amount(body["input_amount_raw"]):
        raise QuoteError("INVALID_QUOTE_RAW_AMOUNT")
    bps = body["slippage_bps"]
    if type(bps) is not int or not 0 <= bps <= MAX_SLIPPAGE_BPS:
        raise QuoteError("INVALID_QUOTE_SLIPPAGE_BPS")
    return dict(body)


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate quote key")
        result[key] = value
    return result


def _nonfinite_json(_):
    raise ValueError("non-finite quote JSON value")


def _impact_percent(value):
    if not isinstance(value, str) or re.fullmatch(r"-?[0-9]{1,32}(?:\.[0-9]{1,80})?", value) is None:
        raise ValueError("invalid impact")
    whole, _, fractional = value.partition(".")
    places = len(fractional)
    magnitude = int(whole.removeprefix("-") + fractional) * 100
    scale = 10**places
    integer, remainder = divmod(magnitude, scale)
    suffix = f".{remainder:0{places}d}".rstrip("0") if remainder else ""
    sign = "-" if value.startswith("-") and magnitude else ""
    return f"{sign}{integer}{suffix}"


def _route_leg(step):
    info = step["swapInfo"]
    amm, source, target = (info[key] for key in ("ammKey", "inputMint", "outputMint"))
    amount_in, amount_out = info["inAmount"], info["outAmount"]
    if (not all(map(valid_pubkey, (amm, source, target))) or source == target
            or not _valid_raw_amount(amount_in) or not _valid_raw_amount(amount_out)):
        raise ValueError("invalid route leg")
    share_bps, percent = step.get("bps"), step.get("percent")
    for share, largest in ((share_bps, MAX_SLIPPAGE_BPS), (percent, 100)):
        if share is not None and (type(share) is not int or not 0 <= share <= largest):
            raise ValueError("invalid route share")
    fee, fee_mint = info.get("feeAmount"), info.get("feeMint")
    if fee is not None and not _valid_raw_amount(fee, allow_zero=True):
        raise ValueError("invalid route fee")
    if fee not in (None, "0") and not valid_pubkey(fee_mint):
        raise ValueError("invalid route fee mint")
    return {
        "amm_key": amm, "input_mint": source, "output_mint": target,
        "in_amount_raw": amount_in, "out_amount_raw": amount_out,
        "share_bps": share_bps, "percent": percent, "fee_amount_raw": fee,
        "fee_mint": fee_mint if fee is not None and valid_pubkey(fee_mint) else None,
    }


def _reachable(graph, start):
    visited = {start}
    pending = deque([start])
    while pending:
        for target in graph[pending.popleft()] - visited:
            visited.add(target)
            pending.append(target)
    return visited


def _route_plan(steps, source_mint, target_mint, input_amount):
    if not isinstance(steps, list) or not steps:
        raise ValueError("missing route plan")
    legs = [_route_leg(step) for step in steps]
    forward, backward = defaultdict(set), defaultdict(set)
    for leg in legs:
        source, target = leg["input_mint"], leg["output_mint"]
        if target == source_mint or source == target_mint:
            raise ValueError("invalid route boundary")
        forward[source].add(target)
        backward[target].add(source)
    reachable = _reachable(forward, source_mint)
    can_finish = _reachable(backward, target_mint)
    if any(leg["input_mint"] not in reachable or leg["output_mint"] not in can_finish for leg in legs):
        raise ValueError("unbound route")
    if sum(int(leg["in_amount_raw"]) for leg in legs if leg["input_mint"] == source_mint) != int(input_amount):
        raise ValueError("route input mismatch")
    return legs


def _quote_projection(data, status, request):
    code = data.get("errorCode")
    if status in (200, 400, 404) and isinstance(code, str) and code in _NO_ROUTE_CODES:
        return {
            "status": "NO_ROUTE", "reason": "JUPITER_NO_ROUTE", "route_exists": False,
            "out_amount_raw": None, "other_amount_threshold_raw": None,
            "price_impact_pct": None, "route_plan": [], "context_slot": None,
        }
    if status != 200 or data.get("error") or code:
        raise QuoteError("JUPITER_SOURCE_UNAVAILABLE", 503)
    input_mint, output_mint = request["input_mint"], request["mint"]
    input_amount, slippage_bps = request["input_amount_raw"], request["slippage_bps"]
    if (data.get("inputMint") != input_mint or data.get("outputMint") != output_mint
            or data.get("inAmount") != input_amount or data.get("swapMode") != "ExactIn"
            or type(data.get("slippageBps")) is not int or data["slippageBps"] != slippage_bps):
        raise QuoteError("JUPITER_QUOTE_INPUT_MISMATCH", 503)
    amount_out, threshold = data["outAmount"], data["otherAmountThreshold"]
    if (not _valid_raw_amount(amount_out) or not _valid_raw_amount(threshold, allow_zero=True)
            or int(threshold) > int(amount_out)):
        raise ValueError("invalid quoted output")
    context_slot = data.get("contextSlot")
    if context_slot is not None and (type(context_slot) is not int or not 0 <= context_slot <= U64_MAX):
        raise ValueError("invalid context slot")
    return {
        "status": "OK", "reason": None, "route_exists": True,
        "out_amount_raw": amount_out, "other_amount_threshold_raw": threshold,
        "price_impact_pct": _impact_percent(data["priceImpactPct"]),
        "route_plan": _route_plan(data["routePlan"], input_mint, output_mint, input_amount),
        "context_slot": context_slot,
    }


def _digest(body):
    content = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class FrankQuoteService:
    """Produce an ephemeral reference bound to explicit raw mint units and receipt time."""

    def __init__(self, adapter=None, *, clock=time.time, ttl_seconds=QUOTE_TTL_SECONDS):
        if type(ttl_seconds) is not int or ttl_seconds < 1:
            raise ValueError("INVALID_QUOTE_TTL")
        self.adapter = adapter
        self.clock = clock
        self.ttl_seconds = ttl_seconds

    def create(self, body):
        quote_input = _validate_input(body)
        if self.adapter is None:
            raise QuoteError("JUPITER_QUOTE_NOT_CONFIGURED", 503)
        input_mint, output_mint = quote_input["input_mint"], quote_input["mint"]
        amount_raw, slippage_bps = quote_input["input_amount_raw"], quote_input["slippage_bps"]
        try:
            status, raw = self.adapter.quote_exact_in(input_mint, output_mint, amount_raw, slippage_bps)
            observed_at = self.clock()
            if type(observed_at) not in (int, float) or not math.isfinite(observed_at) or observed_at < 0:
                raise ValueError("invalid receipt time")
            if status == 429:
                raise QuoteError("JUPITER_RATE_LIMITED", 503)
            if status not in (200, 400, 404):
                raise QuoteError("JUPITER_SOURCE_UNAVAILABLE", 503)
            if not isinstance(raw, bytes):
                raise ValueError("invalid source bytes")
            data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json, parse_constant=_nonfinite_json)
            if not isinstance(data, dict):
                raise ValueError("invalid response shape")
            projection = _quote_projection(data, status, quote_input)
        except QuoteError:
            raise
        except (URLError, TimeoutError, OSError):
            raise QuoteError("JUPITER_NETWORK_UNAVAILABLE", 503) from None
        except (AttributeError, KeyError, TypeError, ValueError, OverflowError, RecursionError):
            raise QuoteError("JUPITER_RESPONSE_INVALID", 503) from None
        result = {
            **projection,
            "input": quote_input, "input_mint": input_mint, "output_mint": output_mint,
            "in_amount_raw": amount_raw, "slippage_bps": slippage_bps, "swap_mode": "ExactIn",
            "observed_at": observed_at, "source_time": None, "expires_at": observed_at + self.ttl_seconds,
            "source_ref": {
                "source": SOURCE,
                "request_sha256": _digest({**quote_input, "swap_mode": "ExactIn", "instruction_version": "V2"}),
                "response_sha256": hashlib.sha256(raw).hexdigest(),
                "http_status": status,
            },
        }
        return {"quote_id": _digest(result), **result}

