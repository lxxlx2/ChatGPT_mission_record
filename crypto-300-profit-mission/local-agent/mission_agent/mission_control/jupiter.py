"""Official Jupiter quote adapter used only for followability checks.

No swap transaction is built or signed. This module requests read-only quotes.
API-key access is optional: current Jupiter keyless quote access is supported,
with a conservative default request interval when no key is configured.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def _no_route_error(value) -> bool:
    text = str(value or "").lower()
    return "route" in text and any(x in text for x in ("could not find", "no route", "not found"))


def _retry_after_seconds(exc: urllib.error.HTTPError) -> float:
    try:
        value = exc.headers.get("Retry-After") if exc.headers is not None else None
        if value is None:
            return 0.0
        return min(60.0, max(0.0, float(value)))
    except (TypeError, ValueError, AttributeError):
        return 0.0


class JupiterQuoteClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        endpoint: str = "https://api.jup.ag/swap/v1/quote",
        open_url=urllib.request.urlopen,
        minimum_interval_seconds: float | None = None,
        rate_limit_cooldown_seconds: float | None = None,
    ):
        self.api_key = api_key or None
        self.endpoint = endpoint
        self.open_url = open_url
        # Keyless access is documented at 0.5 requests/second. Use 2.5s by
        # default to leave headroom for sliding-window accounting and other
        # review traffic sharing the same public bucket. Keyed callers keep
        # the previous cadence. Tests may override explicitly.
        if minimum_interval_seconds is None:
            minimum_interval_seconds = 1.05 if self.api_key else 2.5
        if rate_limit_cooldown_seconds is None:
            rate_limit_cooldown_seconds = 5.0 if self.api_key else 10.0
        self.minimum_interval_seconds = float(minimum_interval_seconds)
        self.rate_limit_cooldown_seconds = float(rate_limit_cooldown_seconds)
        self._last_request_monotonic = 0.0
        self._cooldown_until_monotonic = 0.0

    def quote_usdc_to_token(
        self,
        mint: str,
        token_decimals: int,
        *,
        usdc_amount: Decimal = Decimal("30"),
        slippage_bps: int = 100,
    ) -> dict:
        now = time.monotonic()
        not_before = max(
            self._last_request_monotonic + self.minimum_interval_seconds,
            self._cooldown_until_monotonic,
        )
        delay = not_before - now
        if delay > 0:
            time.sleep(delay)
        amount_raw = int(usdc_amount * Decimal(10**6))
        params = urllib.parse.urlencode(
            {
                "inputMint": USDC,
                "outputMint": mint,
                "amount": str(amount_raw),
                "slippageBps": str(slippage_bps),
            }
        )
        headers = {"User-Agent": "mission-meme-v1/1"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        request = urllib.request.Request(
            self.endpoint + "?" + params,
            headers=headers,
        )
        reason = "JUPITER_RESPONSE_INVALID"
        observed_at = None
        try:
            self._last_request_monotonic = time.monotonic()
            with self.open_url(request, timeout=8) as response:
                body = json.load(response)
            observed_at = time.time()
            if body.get("error"):
                if _no_route_error(body.get("error")):
                    return {
                        "status": "OK",
                        "reason": "JUPITER_NO_ROUTE",
                        "observed_at": observed_at,
                        "source": "JUPITER_OFFICIAL",
                        "input_usdc": str(usdc_amount),
                        "route_exists": False,
                    }
                return {
                    "status": "UNAVAILABLE",
                    "reason": "JUPITER_QUOTE_ERROR",
                    "error": str(body.get("error")),
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                }
            route_plan = body.get("routePlan") or []
            if not route_plan:
                return {
                    "status": "OK",
                    "reason": "JUPITER_NO_ROUTE",
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                    "input_usdc": str(usdc_amount),
                    "route_exists": False,
                }
            raw_impact = body.get("priceImpactPct")
            if raw_impact in (None, ""):
                return {
                    "status": "UNAVAILABLE",
                    "reason": "JUPITER_PRICE_IMPACT_MISSING",
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                }
            out_raw = Decimal(str(body["outAmount"]))
            if out_raw <= 0:
                raise ValueError("JUPITER_ZERO_OUTPUT")
            token_out = out_raw / (Decimal(10) ** int(token_decimals))
            executable_price = usdc_amount / token_out
            impact_fraction = Decimal(str(raw_impact))
            return {
                "status": "OK",
                "source": "JUPITER_OFFICIAL",
                "observed_at": observed_at,
                "input_usdc": str(usdc_amount),
                "out_amount_raw": str(out_raw),
                "token_out": str(token_out),
                "execution_price_usdc": str(executable_price),
                "price_impact_pct": str(impact_fraction * Decimal(100)),
                "other_amount_threshold": str(body.get("otherAmountThreshold") or ""),
                "route_exists": True,
                "route_plan": route_plan,
                "time_taken": None if body.get("timeTaken") is None else str(body.get("timeTaken")),
            }
        except urllib.error.HTTPError as exc:
            observed_at = time.time()
            try:
                raw = exc.read().decode("utf-8", errors="replace")
                error_body = json.loads(raw) if raw else {}
            except (OSError, ValueError, TypeError):
                error_body = {}
            error_value = error_body.get("error") or error_body.get("message") or ""
            if _no_route_error(error_value):
                return {
                    "status": "OK",
                    "reason": "JUPITER_NO_ROUTE",
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                    "input_usdc": str(usdc_amount),
                    "route_exists": False,
                }
            if exc.code == 429:
                cooldown = max(self.rate_limit_cooldown_seconds, _retry_after_seconds(exc))
                self._cooldown_until_monotonic = max(
                    self._cooldown_until_monotonic,
                    time.monotonic() + cooldown,
                )
                reason = "JUPITER_RATE_LIMITED"
            else:
                reason = "JUPITER_HTTP_" + str(exc.code)
        except (urllib.error.URLError, TimeoutError, OSError):
            observed_at = time.time()
            reason = "JUPITER_NETWORK_UNAVAILABLE"
        except (ValueError, KeyError, InvalidOperation, TypeError):
            observed_at = time.time()
            reason = "JUPITER_RESPONSE_INVALID"
        return {
            "status": "UNAVAILABLE",
            "reason": reason,
            "observed_at": observed_at if observed_at is not None else time.time(),
            "source": "JUPITER_OFFICIAL",
        }

    def quote_token_to_usdc(
        self,
        mint: str,
        token_amount_raw: str | int,
        token_decimals: int,
        *,
        slippage_bps: int = 100,
    ) -> dict:
        """Read-only reverse quote for forward outcome measurement."""
        try:
            amount_raw = int(str(token_amount_raw))
            if amount_raw <= 0:
                raise ValueError("TOKEN_AMOUNT_INVALID")
        except (ValueError, TypeError):
            return {
                "status": "UNAVAILABLE",
                "reason": "TOKEN_AMOUNT_INVALID",
                "observed_at": time.time(),
                "source": "JUPITER_OFFICIAL",
            }
        now = time.monotonic()
        not_before = max(
            self._last_request_monotonic + self.minimum_interval_seconds,
            self._cooldown_until_monotonic,
        )
        delay = not_before - now
        if delay > 0:
            time.sleep(delay)
        params = urllib.parse.urlencode(
            {
                "inputMint": mint,
                "outputMint": USDC,
                "amount": str(amount_raw),
                "slippageBps": str(slippage_bps),
            }
        )
        headers = {"User-Agent": "mission-meme-v1/1"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        request = urllib.request.Request(self.endpoint + "?" + params, headers=headers)
        reason = "JUPITER_RESPONSE_INVALID"
        observed_at = None
        try:
            self._last_request_monotonic = time.monotonic()
            with self.open_url(request, timeout=8) as response:
                body = json.load(response)
            observed_at = time.time()
            if body.get("error"):
                if _no_route_error(body.get("error")):
                    return {
                        "status": "OK",
                        "reason": "JUPITER_NO_ROUTE",
                        "observed_at": observed_at,
                        "source": "JUPITER_OFFICIAL",
                        "route_exists": False,
                        "input_token_raw": str(amount_raw),
                    }
                return {
                    "status": "UNAVAILABLE",
                    "reason": "JUPITER_QUOTE_ERROR",
                    "error": str(body.get("error")),
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                }
            route_plan = body.get("routePlan") or []
            if not route_plan:
                return {
                    "status": "OK",
                    "reason": "JUPITER_NO_ROUTE",
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                    "route_exists": False,
                    "input_token_raw": str(amount_raw),
                }
            raw_impact = body.get("priceImpactPct")
            if raw_impact in (None, ""):
                return {
                    "status": "UNAVAILABLE",
                    "reason": "JUPITER_PRICE_IMPACT_MISSING",
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                }
            out_raw = Decimal(str(body["outAmount"]))
            if out_raw <= 0:
                raise ValueError("JUPITER_ZERO_OUTPUT")
            out_usdc = out_raw / Decimal(10**6)
            token_in = Decimal(amount_raw) / (Decimal(10) ** int(token_decimals))
            if token_in <= 0:
                raise ValueError("JUPITER_ZERO_INPUT")
            executable_price = out_usdc / token_in
            impact_fraction = Decimal(str(raw_impact))
            return {
                "status": "OK",
                "source": "JUPITER_OFFICIAL",
                "observed_at": observed_at,
                "input_token_raw": str(amount_raw),
                "token_in": str(token_in),
                "out_amount_raw": str(out_raw),
                "out_usdc": str(out_usdc),
                "execution_price_usdc": str(executable_price),
                "price_impact_pct": str(impact_fraction * Decimal(100)),
                "other_amount_threshold": str(body.get("otherAmountThreshold") or ""),
                "route_exists": True,
                "route_plan": route_plan,
                "time_taken": None if body.get("timeTaken") is None else str(body.get("timeTaken")),
            }
        except urllib.error.HTTPError as exc:
            observed_at = time.time()
            try:
                raw = exc.read().decode("utf-8", errors="replace")
                error_body = json.loads(raw) if raw else {}
            except (OSError, ValueError, TypeError):
                error_body = {}
            error_value = error_body.get("error") or error_body.get("message") or ""
            if _no_route_error(error_value):
                return {
                    "status": "OK",
                    "reason": "JUPITER_NO_ROUTE",
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                    "route_exists": False,
                    "input_token_raw": str(amount_raw),
                }
            if exc.code == 429:
                cooldown = max(self.rate_limit_cooldown_seconds, _retry_after_seconds(exc))
                self._cooldown_until_monotonic = max(
                    self._cooldown_until_monotonic,
                    time.monotonic() + cooldown,
                )
                reason = "JUPITER_RATE_LIMITED"
            else:
                reason = "JUPITER_HTTP_" + str(exc.code)
        except (urllib.error.URLError, TimeoutError, OSError):
            observed_at = time.time()
            reason = "JUPITER_NETWORK_UNAVAILABLE"
        except (ValueError, KeyError, InvalidOperation, TypeError):
            observed_at = time.time()
            reason = "JUPITER_RESPONSE_INVALID"
        return {
            "status": "UNAVAILABLE",
            "reason": reason,
            "observed_at": observed_at if observed_at is not None else time.time(),
            "source": "JUPITER_OFFICIAL",
        }
