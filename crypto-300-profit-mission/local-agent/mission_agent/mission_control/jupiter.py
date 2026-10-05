"""Official Jupiter quote adapter used only for followability checks.

No swap transaction is built or signed. This module requests read-only quotes.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class JupiterQuoteClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        endpoint: str = "https://api.jup.ag/swap/v1/quote",
        open_url=urllib.request.urlopen,
        minimum_interval_seconds: float = 1.05,
    ):
        self.api_key = api_key
        self.endpoint = endpoint
        self.open_url = open_url
        self.minimum_interval_seconds = minimum_interval_seconds
        self._last_request_monotonic = 0.0

    def quote_usdc_to_token(
        self,
        mint: str,
        token_decimals: int,
        *,
        usdc_amount: Decimal = Decimal("30"),
        slippage_bps: int = 100,
    ) -> dict:
        observed_at = time.time()
        if not self.api_key:
            return {
                "status": "UNAVAILABLE",
                "reason": "JUPITER_API_KEY_NOT_CONFIGURED",
                "observed_at": observed_at,
                "source": "JUPITER_OFFICIAL",
            }
        delay = self.minimum_interval_seconds - (time.monotonic() - self._last_request_monotonic)
        if delay > 0:
            time.sleep(delay)
        amount_raw = int(usdc_amount * Decimal(10**6))
        params = urllib.parse.urlencode(
            {
                "inputMint": USDC,
                "outputMint": mint,
                "amount": str(amount_raw),
                "slippageBps": str(slippage_bps),
                "instructionVersion": "V2",
            }
        )
        request = urllib.request.Request(
            self.endpoint + "?" + params,
            headers={"x-api-key": self.api_key, "User-Agent": "mission-meme-v1/1"},
        )
        try:
            self._last_request_monotonic = time.monotonic()
            with self.open_url(request, timeout=8) as response:
                body = json.load(response)
            if body.get("error"):
                return {
                    "status": "UNAVAILABLE",
                    "reason": "JUPITER_QUOTE_ERROR",
                    "error": str(body.get("error")),
                    "observed_at": observed_at,
                    "source": "JUPITER_OFFICIAL",
                }
            out_raw = Decimal(str(body["outAmount"]))
            if out_raw <= 0:
                raise ValueError("JUPITER_ZERO_OUTPUT")
            token_out = out_raw / (Decimal(10) ** int(token_decimals))
            executable_price = usdc_amount / token_out
            impact_fraction = Decimal(str(body.get("priceImpactPct") or "0"))
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
                "route_exists": bool(body.get("routePlan")),
                "route_plan": body.get("routePlan") or [],
                "time_taken": body.get("timeTaken"),
            }
        except urllib.error.HTTPError as exc:
            reason = "JUPITER_RATE_LIMITED" if exc.code == 429 else "JUPITER_HTTP_" + str(exc.code)
        except (urllib.error.URLError, TimeoutError, OSError):
            reason = "JUPITER_NETWORK_UNAVAILABLE"
        except (ValueError, KeyError, InvalidOperation, TypeError):
            reason = "JUPITER_RESPONSE_INVALID"
        return {
            "status": "UNAVAILABLE",
            "reason": reason,
            "observed_at": observed_at,
            "source": "JUPITER_OFFICIAL",
        }
