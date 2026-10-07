"""Free secondary market snapshot for Solana Meme research.

DEX Screener is used only for market/pair metadata. Chain ownership, authorities
and wallet-cluster conclusions never depend on this client.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

BASE="https://api.dexscreener.com"


def _num(value):
    if value in (None,""):
        return None
    try:
        return str(Decimal(str(value)))
    except (InvalidOperation,ValueError,TypeError):
        return None


class DexScreenerMarketClient:
    def __init__(self, *, open_url=urllib.request.urlopen):
        self.open_url=open_url

    def token_snapshot(self,mint:str)->dict:
        url=BASE+"/token-pairs/v1/solana/"+urllib.parse.quote(mint,safe="")
        request=urllib.request.Request(url,headers={
            "Accept":"application/json",
            "User-Agent":"mission-meme-research/2",
        })
        observed_at=time.time()
        try:
            with self.open_url(request,timeout=10) as response:
                payload=json.load(response)
            observed_at=time.time()
        except urllib.error.HTTPError as exc:
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","observed_at":observed_at,"reason":"HTTP_"+str(exc.code)}
        except (urllib.error.URLError,TimeoutError,OSError,ValueError,TypeError):
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","observed_at":observed_at,"reason":"NETWORK_OR_RESPONSE_INVALID"}
        if not isinstance(payload,list):
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","observed_at":observed_at,"reason":"RESPONSE_INVALID"}

        pairs=[
            x for x in payload
            if isinstance(x,dict)
            and x.get("chainId")=="solana"
            and (x.get("baseToken") or {}).get("address")==mint
        ]
        if not pairs:
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","observed_at":observed_at,"reason":"NO_BASE_TOKEN_PAIR"}

        def liquidity(pair):
            try:return Decimal(str((pair.get("liquidity") or {}).get("usd") or 0))
            except (InvalidOperation,ValueError,TypeError):return Decimal(0)
        pairs.sort(key=liquidity,reverse=True)
        main=pairs[0]
        base=main.get("baseToken") or {};quote=main.get("quoteToken") or {}
        info=main.get("info") or {}
        total_liquidity=sum((liquidity(x) for x in pairs),Decimal(0))
        return {
            "status":"OK",
            "source":"DEXSCREENER_API",
            "observed_at":observed_at,
            "pair_count":len(pairs),
            "name":base.get("name"),
            "symbol":base.get("symbol"),
            "price_usd":_num(main.get("priceUsd")),
            "market_cap_usd":_num(main.get("marketCap")),
            "fdv_usd":_num(main.get("fdv")),
            "main_pair":{
                "dex_id":main.get("dexId"),
                "pair_address":main.get("pairAddress"),
                "url":main.get("url"),
                "quote_address":quote.get("address"),
                "quote_symbol":quote.get("symbol"),
                "price_native":_num(main.get("priceNative")),
                "liquidity_usd":_num((main.get("liquidity") or {}).get("usd")),
                "liquidity_base":_num((main.get("liquidity") or {}).get("base")),
                "liquidity_quote":_num((main.get("liquidity") or {}).get("quote")),
                "volume":{k:_num(v) for k,v in (main.get("volume") or {}).items()},
                "txns":main.get("txns") or {},
                "price_change":{k:_num(v) for k,v in (main.get("priceChange") or {}).items()},
                "pair_created_at_ms":main.get("pairCreatedAt"),
            },
            "aggregate_liquidity_usd":str(total_liquidity),
            "websites":[x.get("url") for x in (info.get("websites") or []) if isinstance(x,dict) and x.get("url")],
            "socials":[
                {"platform":x.get("platform"),"handle":x.get("handle")}
                for x in (info.get("socials") or [])
                if isinstance(x,dict) and (x.get("platform") or x.get("handle"))
            ],
        }
