"""Explicit same-report, same-pool public GeckoTerminal reads; no RPC or execution."""
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from .holder_ranks import valid_pubkey
from .market_parity import BASE, MAX_RESPONSE_BYTES, GeckoTerminalRequestBudget, _open, number
from ..signals.reconciliation import _base58_size

SOURCE = "GECKOTERMINAL_PUBLIC_API"
PERIODS = {"5m": ("minute", 5), "1h": ("hour", 1), "1d": ("day", 1)}
MAX_POINTS = 120
MAX_TRADES = 300


def report_pool(mint, profile, market, pool):
    """Allow only the exact two Mint identities present in the saved CA report."""
    if (profile.get("status") != "OK" or profile.get("is_initialized") is not True
            or market.get("chain") != "solana" or market.get("mint") != mint
            or not valid_pubkey(mint) or not valid_pubkey(pool)):
        return None
    pairs = market.get("pool_candidates")
    candidates = list(pairs) if isinstance(pairs, list) else []
    if market.get("main_pair"):
        candidates.append(market["main_pair"])
    members = set()
    for row in candidates:
        if not isinstance(row, dict) or row.get("pair_address") != pool:
            continue
        a, b = row.get("base_address"), row.get("quote_address")
        if not all(valid_pubkey(v) for v in (a,b)) or len({a,b,pool}) != 3 or mint not in (a,b):
            return None
        members.add(b if a == mint else a)
    return next(iter(members)) if len(members) == 1 else None


def _parse_chart(payload, mint, peer, now, before=None):
    if not isinstance(payload, dict):
        raise ValueError()
    meta = payload.get("meta")
    items = [meta.get(k) for k in ("base","quote")] if isinstance(meta, dict) else []
    if len(items)!=2 or not all(isinstance(x,dict) and isinstance(x.get("address"),str) for x in items):
        raise ValueError()
    if {x["address"] for x in items} != {mint,peer}:
        raise ValueError()
    data = payload.get("data")
    attrs = data.get("attributes") if isinstance(data,dict) and data.get("type")=="ohlcv_request_response" else None
    rows = attrs.get("ohlcv_list") if isinstance(attrs,dict) else None
    if not isinstance(rows,list) or len(rows)>MAX_POINTS:
        raise ValueError()
    kept={}
    for raw in rows:
        if not isinstance(raw,list) or len(raw)!=6:
            raise ValueError()
        at,*values=raw
        bounded=[number(v) for v in values]
        if (type(at) is not int or not 0 < at <= now+60 or at in kept or None in bounded
                or any(Decimal(n)<=0 for n in bounded[:4])):
            raise ValueError()
        o,h,l,c,_=map(Decimal,bounded)
        if not l<=min(o,c)<=max(o,c)<=h:
            raise ValueError()
        if before is not None and at >= before:
            # Some responses include the boundary bar. The preceding page
            # already owns it; anything newer indicates a mismatched page.
            if at != before:
                raise ValueError()
            continue
        kept[at]=[at,*bounded]
    return [kept[at] for at in sorted(kept)]


def _trade_time(text, now):
    if not isinstance(text,str) or not 1<=len(text)<=50:
        return None
    try:
        value=datetime.fromisoformat(text.replace("Z","+00:00"))
        at=int(value.timestamp()) if value.tzinfo else 0
    except (ValueError,OverflowError,OSError):
        return None
    return at if 0 < at <= now+60 else None


def _parse_trades(payload,mint,peer,pool,now):
    rows=payload.get("data") if isinstance(payload,dict) else None
    if not isinstance(rows,list) or len(rows)>MAX_TRADES:
        raise ValueError()
    kept, conflicts, skipped = {},set(),0
    for row in rows:
        item=row.get("attributes") if isinstance(row,dict) and row.get("type")=="trade" else None
        key=row.get("id") if isinstance(row,dict) else None
        if not isinstance(item,dict) or not isinstance(key,str) or not re.fullmatch(r"solana_[A-Za-z0-9_-]{1,230}",key):
            skipped+=1
            continue
        left,right=item.get("from_token_address"),item.get("to_token_address")
        at=_trade_time(item.get("block_timestamp"),now)
        sig=item.get("tx_hash")
        if ((left,right) not in ((mint,peer),(peer,mint)) or at is None or not _base58_size(sig,64)
                or item.get("pool_address",pool)!=pool):
            skipped+=1
            continue
        buying=right==mint
        leg="to" if buying else "from"
        quantity=number(item.get(leg+"_token_amount"))
        price=number(item.get("price_"+leg+"_in_usd"))
        if not quantity or Decimal(quantity)<=0:
            skipped+=1
            continue
        wallet=item.get("tx_from_address")
        record={"id":key,"signature":sig,"at":at,"side":"BUY" if buying else "SELL",
                "quantity":quantity,"price_usd":price if price and Decimal(price)>0 else None,
                "wallet":wallet if valid_pubkey(wallet) else None}
        if key in kept and kept[key]!=record:
            conflicts.add(key)
        kept[key]=record
    items=sorted((v for k,v in kept.items() if k not in conflicts),key=lambda r:(r["at"],r["id"]),reverse=True)
    if rows and not items:
        raise ValueError("NO_VERIFIABLE_TRADE_ROWS")
    return items,{"provider_rows":len(rows),"unusable_rows":skipped+len(conflicts),
                  "earliest":items[-1]["at"] if items else None,"latest":items[0]["at"] if items else None,
                  "scope":"FIRST_PAGE_LAST_24H_ONLY","has_more":len(rows)>=MAX_TRADES or bool(payload.get("links",{}).get("next"))
                  if isinstance(payload.get("links",{}),dict) else len(rows)>=MAX_TRADES}


class CAMarketSeries:
    def __init__(self, *, open_url=_open, clock=time.time, monotonic=time.monotonic, request_budget=None):
        self.open_url,self.clock,self.monotonic=open_url,clock,monotonic
        self.cache=OrderedDict()
        self.lock=threading.Lock()
        self.request_budget=request_budget if request_budget is not None else GeckoTerminalRequestBudget(monotonic)

    def _read(self,url):
        req=urllib.request.Request(url,headers={"Accept":"application/json;version=20230203",
                                              "User-Agent":"frank-ca-market/1"})
        deadline=self.monotonic()+6
        with self.open_url(req,timeout=6) as response:
            if hasattr(response,"read1"):
                parts, size=[],0
                while size<=MAX_RESPONSE_BYTES:
                    if self.monotonic()>=deadline:
                        raise TimeoutError("SOURCE_READ_DEADLINE")
                    part=response.read1(min(65536,MAX_RESPONSE_BYTES+1-size))
                    if not part:
                        break
                    parts.append(part)
                    size+=len(part)
                raw=b"".join(parts)
            else:
                raw=response.read(MAX_RESPONSE_BYTES+1)
        if not isinstance(raw,bytes) or len(raw)>MAX_RESPONSE_BYTES:
            raise ValueError()
        return json.loads(raw,parse_float=Decimal)

    def _read_cached(self,mint,pool,peer,kind,period,suffix,before=None):
        key=(mint,pool,peer,kind,period,before)
        with self.lock:
            cached=self.cache.get(key)
            now=self.monotonic()
            if cached and now-cached[0]<60:
                return {**cached[1],"cache":"FRESH"}
            if not self.request_budget.admit():
                reason="RATE_LIMIT"
            else:
                try:
                    data=self._read(BASE+pool+suffix)
                    observed=int(self.clock())
                    if kind=="chart":
                        rows=_parse_chart(data,mint,peer,observed,before)
                        coverage={"scope":"PROVIDER_INTERVAL_PAGE","before":before,
                                  "next_before":rows[0][0] if rows else None}
                    else:
                        rows,coverage=_parse_trades(data,mint,peer,pool,observed)
                    result={"status":"OK","rows":rows,"coverage":coverage,"observed_at":observed}
                    self.cache[key]=(self.monotonic(),result)
                    self.cache.move_to_end(key)
                    if len(self.cache)>128:self.cache.popitem(last=False)
                    return result
                except urllib.error.HTTPError as error:
                    reason="HTTP_"+str(error.code)
                    if error.code==429:self.request_budget.rate_limited()
                except (ValueError,TypeError,TimeoutError,OSError,RecursionError):
                    reason="SOURCE_UNAVAILABLE_OR_MISMATCH"
            if cached and now-cached[0]<1800:
                return {**cached[1],"status":"STALE","reason":reason}
            return {"status":"UNAVAILABLE","rows":[],"reason":reason}

    def read(self,mint,pool,peer,period,*,before=None):
        if (not all(valid_pubkey(value) for value in (mint,pool,peer)) or len({mint,pool,peer})!=3
                or period not in PERIODS or (before is not None and
                    (type(before) is not int or not 1 < before <= self.clock()+60))):
            raise ValueError("INVALID_MARKET_SERIES_SCOPE")
        frame,aggregate=PERIODS[period]
        params={"aggregate":aggregate,"limit":MAX_POINTS,"token":mint,"currency":"usd"}
        if before is not None:
            params["before_timestamp"]=before-1
        chart_q=urllib.parse.urlencode(params)
        # The public route defaults to 300 trades in one day; both controls are Pro-only.
        trades_q=urllib.parse.urlencode({"token":mint})
        chart=self._read_cached(mint,pool,peer,"chart",period,"/ohlcv/"+frame+"?"+chart_q,before)
        out={"source":SOURCE,"mint":mint,"pool":pool,"period":period,"currency":"USD","chart":chart}
        if before is not None:
            return {**out,"before":before}
        return {**out,"trades":self._read_cached(mint,pool,peer,"trades",None,"/trades?"+trades_q)}
