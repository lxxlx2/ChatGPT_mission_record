"""Deterministic token-security and market context for Meme CA reports."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

TOKEN_2022_PROGRAM="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
TOKEN_PROGRAM="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
DEXSCREENER_ENDPOINT="https://api.dexscreener.com/tokens/v1/solana/{mint}"

SENSITIVE_EXTENSION_WORDS=(
    "transferfee","transferhook","permanentdelegate","pausable",
    "confidentialtransfer","defaultaccountstate",
)


def _recursive_values(value,key):
    found=[]
    if isinstance(value,dict):
        for k,v in value.items():
            if str(k).lower()==key.lower():found.append(v)
            found.extend(_recursive_values(v,key))
    elif isinstance(value,list):
        for item in value:found.extend(_recursive_values(item,key))
    return found


def inspect_mint(rpc,mint:str)->dict:
    observed=time.time()
    try:
        result=rpc.call("getAccountInfo",[mint,{"encoding":"jsonParsed","commitment":"finalized"}],ttl=30)
    except Exception as exc:
        return {"status":"UNAVAILABLE","reason":type(exc).__name__,"observed_at":observed,"source":"SOLANA_FINALIZED_JSON_RPC"}
    value=(result or {}).get("value") or {}
    data=value.get("data") or {}
    parsed=data.get("parsed") if isinstance(data,dict) else None
    info=(parsed or {}).get("info") if isinstance(parsed,dict) else {}
    if not isinstance(info,dict):
        return {"status":"UNAVAILABLE","reason":"MINT_PARSE_UNAVAILABLE","observed_at":observed,"source":"SOLANA_FINALIZED_JSON_RPC"}
    program=value.get("owner")
    standard="SPL Token-2022" if program==TOKEN_2022_PROGRAM else "SPL Token" if program==TOKEN_PROGRAM else "UNKNOWN"
    extensions=info.get("extensions") or []
    extension_names=[]
    for ext in extensions if isinstance(extensions,list) else []:
        if isinstance(ext,dict):
            name=ext.get("extension") or ext.get("type")
            if name:extension_names.append(str(name))
    update_values=[x for x in _recursive_values(info,"updateAuthority") if x not in (None,"")]
    update_authority=str(update_values[0]) if update_values else None
    mint_authority=info.get("mintAuthority")
    freeze_authority=info.get("freezeAuthority")
    sensitive=[
        name for name in extension_names
        if any(word in name.lower().replace("_","") for word in SENSITIVE_EXTENSION_WORDS)
    ]
    risks=[]
    if mint_authority:risks.append("MINT_AUTHORITY_ACTIVE")
    if freeze_authority:risks.append("FREEZE_AUTHORITY_ACTIVE")
    for name in sensitive:risks.append("SENSITIVE_EXTENSION:"+name)
    supply_raw=str(info.get("supply")) if info.get("supply") is not None else None
    decimals=info.get("decimals")
    supply_quantity=None
    try:
        if supply_raw is not None and decimals is not None:
            supply_quantity=str(Decimal(supply_raw)/(Decimal(10)**int(decimals)))
    except (InvalidOperation,TypeError,ValueError):
        pass
    return {
        "status":"OK","source":"SOLANA_FINALIZED_JSON_RPC","observed_at":observed,
        "token_program":program,"token_standard":standard,
        "supply_raw":supply_raw,"supply_quantity":supply_quantity,
        "decimals":decimals,"is_initialized":info.get("isInitialized"),
        "mint_authority":mint_authority,"freeze_authority":freeze_authority,
        "metadata_update_authority":update_authority,
        "metadata_update_authority_status":"VERIFIED" if update_values else "UNRESOLVED",
        "extensions":extension_names,"sensitive_extensions":sensitive,"risk_flags":risks,
    }


class DexScreenerClient:
    def __init__(self,*,open_url=urllib.request.urlopen):
        self.open_url=open_url
    def token_market(self,mint:str)->dict:
        url=DEXSCREENER_ENDPOINT.format(mint=urllib.parse.quote(mint,safe=""))
        request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"mission-meme-market/1"})
        observed=time.time()
        try:
            with self.open_url(request,timeout=8) as response:
                body=json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return {"status":"UNAVAILABLE","reason":"DEXSCREENER_HTTP_"+str(exc.code),"observed_at":observed,"source":"DEXSCREENER"}
        except (urllib.error.URLError,TimeoutError,OSError,ValueError,TypeError) as exc:
            return {"status":"UNAVAILABLE","reason":type(exc).__name__,"observed_at":observed,"source":"DEXSCREENER"}
        if not isinstance(body,list):
            return {"status":"UNAVAILABLE","reason":"DEXSCREENER_RESPONSE_INVALID","observed_at":observed,"source":"DEXSCREENER"}
        pairs=[
            x for x in body
            if isinstance(x,dict)
            and (x.get("baseToken") or {}).get("address")==mint
            and x.get("chainId")=="solana"
        ]
        def liq(pair):
            try:return Decimal(str((pair.get("liquidity") or {}).get("usd") or 0))
            except (InvalidOperation,TypeError,ValueError):return Decimal(0)
        pairs.sort(key=liq,reverse=True)
        if not pairs:
            return {"status":"UNAVAILABLE","reason":"DEXSCREENER_NO_BASE_PAIR","observed_at":observed,"source":"DEXSCREENER","pair_count":0}
        p=pairs[0];base=p.get("baseToken") or {};quote=p.get("quoteToken") or {}
        mc=p.get("marketCap");liq_usd=(p.get("liquidity") or {}).get("usd")
        ratio=None
        try:
            if mc and Decimal(str(mc))>0 and liq_usd is not None:
                ratio=str(Decimal(str(liq_usd))*100/Decimal(str(mc)))
        except (InvalidOperation,TypeError,ValueError,ZeroDivisionError):
            pass
        return {
            "status":"OK","source":"DEXSCREENER","observed_at":observed,
            "pair_count":len(pairs),"name":base.get("name"),"symbol":base.get("symbol"),
            "quote_symbol":quote.get("symbol"),"quote_address":quote.get("address"),
            "dex_id":p.get("dexId"),"pair_address":p.get("pairAddress"),"pair_url":p.get("url"),
            "price_usd":p.get("priceUsd"),"price_native":p.get("priceNative"),
            "market_cap":mc,"fdv":p.get("fdv"),"liquidity_usd":liq_usd,
            "liquidity_to_market_cap_pct":ratio,
            "volume":p.get("volume") or {},"txns":p.get("txns") or {},
            "price_change":p.get("priceChange") or {},"pair_created_at":p.get("pairCreatedAt"),
            "websites":((p.get("info") or {}).get("websites") or []),
            "socials":((p.get("info") or {}).get("socials") or []),
            "boosts":p.get("boosts") or {},
        }


def automated_assessment(report:dict)->dict:
    security=report.get("token_security") or {};market=report.get("market") or {}
    metrics=report.get("metrics") or {};coverage=report.get("coverage") or {}
    blockers=[];positives=[];uncertainties=[]
    flags=security.get("risk_flags") or []
    if "MINT_AUTHORITY_ACTIVE" in flags:blockers.append("Mint Authority 仍可增发")
    if "FREEZE_AUTHORITY_ACTIVE" in flags:blockers.append("Freeze Authority 仍可冻结")
    sensitive=security.get("sensitive_extensions") or []
    if sensitive:blockers.append("Token-2022 存在敏感扩展："+", ".join(sensitive))
    try:
        control=Decimal(str(metrics.get("LARGEST_PROBABLE_CONTROL_CLUSTER_PCT") or 0))
        if control>=20:blockers.append("最大 probable control cluster ≥20%")
    except (InvalidOperation,TypeError,ValueError):
        pass
    if security.get("status")=="OK" and not security.get("mint_authority"):positives.append("Mint Authority 已撤销")
    if security.get("status")=="OK" and not security.get("freeze_authority"):positives.append("Freeze Authority 已撤销")
    known_ex_lp=metrics.get("KNOWN_EX_LP_TOP10_PCT")
    try:
        if known_ex_lp is not None and Decimal(str(known_ex_lp))<=20:positives.append("已知口径去 LP 后 Top10 ≤20%")
    except (InvalidOperation,TypeError,ValueError):
        pass
    if market.get("status")=="OK":
        try:
            if Decimal(str(market.get("liquidity_usd") or 0))>=30000:positives.append("主交易对流动性 ≥$30K")
        except (InvalidOperation,TypeError,ValueError):
            pass
        try:
            if Decimal(str((market.get("volume") or {}).get("h24") or 0))>=50000:positives.append("24h 成交量 ≥$50K")
        except (InvalidOperation,TypeError,ValueError):
            pass
    if not coverage.get("special_normalization_complete"):
        uncertainties.append("特殊地址身份归一化未完成")
    unresolved=metrics.get("UNRESOLVED_MATERIAL_HOLDER_PCT")
    try:
        if unresolved is not None and Decimal(str(unresolved))>0:
            uncertainties.append("仍有重大 holder 关系未闭环："+str(unresolved)+"%")
    except (InvalidOperation,TypeError,ValueError):
        pass
    uncertainties.append("项目方/名人/creator-fee/官方背书关系未由本地链上工具自动验证")
    if blockers:label="HIGH_RISK"
    elif uncertainties:label="WATCH / NEED_EXTERNAL_VERIFICATION"
    else:label="CHAIN_STRUCTURE_OK"
    return {"label":label,"blockers":blockers,"positives":positives,"uncertainties":uncertainties}
