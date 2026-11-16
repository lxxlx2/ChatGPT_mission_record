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
import uuid

BASE="https://api.dexscreener.com"


def _num(value):
    if value in (None,"") or isinstance(value,bool):
        return None
    try:
        parsed=Decimal(str(value))
        return str(parsed) if parsed.is_finite() else None
    except (InvalidOperation,ValueError,TypeError):
        return None


class DexScreenerMarketClient:
    def __init__(self, *, open_url=urllib.request.urlopen,clock=time.time):
        self.open_url=open_url
        self.clock=clock
        self.last_response_evidence=None

    def _evidence(self,mint,raw,observed_at,route=None):
        # Local import keeps this transport usable without importing server or
        # research storage. The ref binds exact HTTP bytes, not a reserialized dict.
        from ..mission_control.source_evidence import build_source_ref
        params={"chain":"solana","mint":mint,"route":route or "/token-pairs/v1/solana/"+mint}
        ref=build_source_ref(provider_identity=BASE,method="GET",params=params,response_bytes=raw,
                             observed_at=observed_at,received_at=observed_at,receipt_id=str(uuid.uuid4()))
        self.last_response_evidence={"response_bytes":raw,"observed_at":observed_at,"method":"GET",
                                     "request_params":params,"provider_identity":BASE,"source_ref":ref}
        return ref

    def token_snapshot(self,mint:str)->dict:
        self.last_response_evidence=None
        url=BASE+"/token-pairs/v1/solana/"+urllib.parse.quote(mint,safe="")
        request=urllib.request.Request(url,headers={
            "Accept":"application/json",
            "User-Agent":"mission-meme-research/2",
        })
        observed_at=self.clock()
        try:
            with self.open_url(request,timeout=10) as response:
                raw=response.read()
            observed_at=self.clock()
            source_ref=self._evidence(mint,raw,observed_at)
            payload=json.loads(raw)
        except urllib.error.HTTPError as exc:
            observed_at=self.clock()
            try:source_ref=self._evidence(mint,exc.read(),observed_at)
            except (OSError,TypeError,ValueError):source_ref=None
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","chain":"solana","mint":mint,
                    "source_ref":source_ref,"observed_at":observed_at,"reason":"HTTP_"+str(exc.code)}
        except (urllib.error.URLError,TimeoutError,OSError,ValueError,TypeError):
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","chain":"solana","mint":mint,
                    "source_ref":(self.last_response_evidence or {}).get('source_ref'),
                    "observed_at":observed_at,"reason":"NETWORK_OR_RESPONSE_INVALID"}
        return self._snapshot_from_payload(mint,payload,observed_at,source_ref)

    def _snapshot_from_payload(self,mint,payload,observed_at,source_ref):
        if not isinstance(payload,list):
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","chain":"solana","mint":mint,
                    "source_ref":source_ref,"observed_at":observed_at,"reason":"RESPONSE_INVALID"}

        pairs=[
            x for x in payload
            if isinstance(x,dict)
            and x.get("chainId")=="solana"
            and (x.get("baseToken") or {}).get("address")==mint
        ]
        if not pairs:
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","chain":"solana","mint":mint,
                    "source_ref":source_ref,"observed_at":observed_at,"reason":"NO_BASE_TOKEN_PAIR"}

        def liquidity(pair):
            try:
                value=_num((pair.get("liquidity") or {}).get("usd"))
                return Decimal(value) if value is not None and Decimal(value)>=0 else Decimal(0)
            except (InvalidOperation,ValueError,TypeError):return Decimal(0)
        pairs.sort(key=liquidity,reverse=True)
        main=pairs[0]
        base=main.get("baseToken") or {};quote=main.get("quoteToken") or {}
        info=main.get("info") or {}
        known_liquidity=[_num((x.get("liquidity") or {}).get("usd")) for x in pairs]
        valid_liquidity=[Decimal(x) for x in known_liquidity if x is not None and Decimal(x)>=0]
        total_liquidity=sum(valid_liquidity,Decimal(0)) if len(valid_liquidity)==len(pairs) else None
        return {
            "status":"OK",
            "source":"DEXSCREENER_API",
            "chain":"solana",
            "source_ref":source_ref,
            "mint":mint,
            "observed_at":observed_at,
            "pair_count":len(pairs),
            "pool_candidates":[{"pair_address":x.get("pairAddress"),"base_address":(x.get("baseToken") or {}).get("address"),"quote_address":(x.get("quoteToken") or {}).get("address")} for x in pairs],
            "pool_candidates_not_selected":0,
            "name":base.get("name"),
            "symbol":base.get("symbol"),
            "price_usd":_num(main.get("priceUsd")),
            "market_cap_usd":_num(main.get("marketCap")),
            "fdv_usd":_num(main.get("fdv")),
            "main_pair":{
                "dex_id":main.get("dexId"),
                "pair_address":main.get("pairAddress"),
                "base_address":base.get("address"),
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
            "aggregate_liquidity_usd":str(total_liquidity) if total_liquidity is not None else None,
            "aggregate_liquidity_complete_for_returned_pairs":total_liquidity is not None,
            "known_pair_liquidity_subtotal_usd":str(sum(valid_liquidity,Decimal(0))) if valid_liquidity else None,
            "websites":[x.get("url") for x in (info.get("websites") or []) if isinstance(x,dict) and x.get("url")],
            "socials":[
                {"platform":x.get("platform") or x.get("type"),"handle":x.get("handle"),"url":x.get("url")}
                for x in (info.get("socials") or [])
                if isinstance(x,dict) and (x.get("platform") or x.get("type") or x.get("handle") or x.get("url"))
            ],
        }

    def token_snapshots(self,mints):
        """Free provider batch capacity is 30 addresses; never a total Mint cap.

        References cover returned indexed pairs, not independent/exhaustive pool
        discovery. CA continues to use the single-address token-pairs route.
        """
        mints=list(dict.fromkeys(mints))
        if not mints or len(mints)>30:
            raise ValueError("INVALID_MARKET_BATCH_CAPACITY")
        from .holder_ranks import valid_pubkey
        if not all(valid_pubkey(m) for m in mints):
            raise ValueError("INVALID_MARKET_BATCH_MINT")
        self.last_response_evidence=None
        route="/tokens/v1/solana/"+",".join(mints)
        req=urllib.request.Request(BASE+route,headers={"Accept":"application/json","User-Agent":"mission-meme-research/2"})
        observed_at=self.clock(); source_ref=None
        try:
            with self.open_url(req,timeout=10) as response:raw=response.read()
            observed_at=self.clock();source_ref=self._evidence(mints,raw,observed_at,route)
            payload=json.loads(raw)
        except urllib.error.HTTPError as exc:
            observed_at=self.clock()
            try:source_ref=self._evidence(mints,exc.read(),observed_at,route)
            except (OSError,TypeError,ValueError):pass
            return [{"status":"UNAVAILABLE","source":"DEXSCREENER_API","chain":"solana","mint":m,
                     "source_ref":source_ref,"observed_at":observed_at,"reason":"HTTP_"+str(exc.code)} for m in mints]
        except (urllib.error.URLError,TimeoutError,OSError,ValueError,TypeError):
            return [{"status":"UNAVAILABLE","source":"DEXSCREENER_API","chain":"solana","mint":m,
                     "source_ref":source_ref,"observed_at":observed_at,"reason":"NETWORK_OR_RESPONSE_INVALID"} for m in mints]
        return [{**self._snapshot_from_payload(m,payload,observed_at,source_ref),
                 "pair_coverage":"PROVIDER_RETURNED_BATCH_PAIRS_NOT_EXHAUSTIVE_POOL_ENUMERATION"} for m in mints]
