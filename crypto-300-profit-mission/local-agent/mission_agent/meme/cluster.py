"""Free, read-only Solana wallet-cluster analysis for Meme CA research.

The analyzer prefers raw finalized JSON-RPC evidence over third-party labels.
It never upgrades a graph link to common ownership without the explicit
multi-evidence rules in WALLET_CLUSTER_ANALYSIS_SPEC.md.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from ..frank.parser import DEX_PROGRAMS, INFRA_PROGRAMS
from ..signals.classifier import classify
from ..market.sol_usd import USDC, WSOL

DEFAULT_RPC = "https://api.mainnet.solana.com"
FALLBACK_RPCS = ("https://solana-rpc.publicnode.com",)
SYSTEM_PROGRAM = "11111111111111111111111111111111"
TOKEN_PROGRAMS = {
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
}
SPECIAL_ROLES = {
    "LP", "AMM_POOL", "PROTOCOL_VAULT", "ESCROW", "VESTING", "LOCK",
    "BURN", "CEX", "BRIDGE", "ROUTER", "PUBLIC_INFRA", "PUBLIC_PROGRAM", "MARKET_MAKER",
}
DEV_ROLES = {"DEV", "CREATOR", "TREASURY"}
STRONG = {"COMMON_FUNDER_EOA", "BATCH_FUNDING", "COMMON_SIGNER", "COMMON_CONSOLIDATION"}
BEHAVIOR = {"SYNC_BUY", "SYNC_SELL", "IDENTICAL_SIZE", "SAME_EXECUTION_PROGRAM", "REPEATED_SYNC_BEHAVIOR"}


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


class RPCError(RuntimeError):
    pass


class RpcCache:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("CREATE TABLE IF NOT EXISTS rpc_cache(key TEXT PRIMARY KEY,method TEXT,created_at REAL,expires_at REAL,content_hash TEXT,body TEXT)")
    def close(self):
        self.db.close()
    def get(self, method, params, now):
        key=_hash({"method":method,"params":params})
        row=self.db.execute("SELECT body,expires_at,content_hash FROM rpc_cache WHERE key=?",(key,)).fetchone()
        if not row or row[1] < now:return None
        try:value=json.loads(row[0])
        except (TypeError,ValueError):return None
        if row[2]!=_hash(value):return None
        return value
    def put(self, method, params, body, ttl, now):
        key=_hash({"method":method,"params":params})
        self.db.execute("INSERT OR REPLACE INTO rpc_cache VALUES(?,?,?,?,?,?)",(key,method,now,now+ttl,_hash(body),json.dumps(body,sort_keys=True)))
        self.db.commit()


class MultiEndpointSolanaRPC:
    """Read-only failover across free Solana RPC endpoints.

    Cache keys are chain-method/params based, so successful finalized responses can
    be reused regardless of which endpoint returned them.
    """
    RETRYABLE = {"HTTP_403","HTTP_429","HTTP_500","HTTP_502","HTTP_503","HTTP_504","RPC_-32005","RPC_-32004"}

    def __init__(self, endpoints, *, cache=None, min_interval=.30):
        values=[]
        for endpoint in endpoints:
            endpoint=(endpoint or "").strip()
            if endpoint and endpoint not in values:
                values.append(endpoint)
        if not values:
            values=[DEFAULT_RPC]
        self.clients=[
            SolanaReadOnlyRPC(endpoint,cache=cache,min_interval=min_interval,max_attempts=1)
            for endpoint in values
        ]
        self.endpoint=values[0]
        self.endpoint_history=[]
    @property
    def calls(self):
        return sum(x.calls for x in self.clients)
    @property
    def cache_hits(self):
        return sum(x.cache_hits for x in self.clients)
    def call(self, method, params, *, ttl=0):
        last=None
        for client in self.clients:
            try:
                result=client.call(method,params,ttl=ttl)
                self.endpoint=client.endpoint
                if not self.endpoint_history or self.endpoint_history[-1]!=client.endpoint:
                    self.endpoint_history.append(client.endpoint)
                return result
            except RPCError as exc:
                last=exc
                if str(exc) not in self.RETRYABLE:
                    raise
        raise last or RPCError("RPC_ALL_ENDPOINTS_FAILED")


class SolanaReadOnlyRPC:
    ALLOWED={"getTokenSupply","getTokenLargestAccounts","getMultipleAccounts","getAccountInfo","getSignaturesForAddress","getTransaction"}
    def __init__(self, endpoint=DEFAULT_RPC, *, open_url=urllib.request.urlopen, sleep=time.sleep, min_interval=.30, cache:RpcCache|None=None, max_attempts=3):
        self.endpoint=endpoint;self.open_url=open_url;self.sleep=sleep;self.min_interval=float(min_interval);self.cache=cache;self.last=0.0;self.calls=0;self.cache_hits=0;self.max_attempts=max(1,int(max_attempts))
    def call(self, method, params, *, ttl=0):
        if method not in self.ALLOWED:raise ValueError("READ_ONLY_METHOD_ALLOWLIST")
        now=time.time()
        if ttl and self.cache:
            hit=self.cache.get(method,params,now)
            if hit is not None:self.cache_hits+=1;return hit
        wait=self.min_interval-(time.monotonic()-self.last)
        if wait>0:self.sleep(wait)
        body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
        req=urllib.request.Request(self.endpoint,data=body,headers={"Content-Type":"application/json","User-Agent":"mission-meme-cluster/1"})
        last_error=None
        for attempt in range(self.max_attempts):
            try:
                self.last=time.monotonic();self.calls+=1
                with self.open_url(req,timeout=20) as response:value=json.loads(response.read())
                if value.get("error"):raise RPCError("RPC_"+str(value["error"].get("code","ERROR")))
                if "result" not in value:raise RPCError("RPC_ENVELOPE_INVALID")
                result=value["result"]
                if ttl and self.cache:self.cache.put(method,params,result,ttl,time.time())
                return result
            except urllib.error.HTTPError as exc:
                last_error=RPCError("HTTP_"+str(exc.code))
                if exc.code not in {429,500,502,503,504} or attempt==self.max_attempts-1:raise last_error
                try:retry_after=min(30.0,max(0.0,float(exc.headers.get("Retry-After","0"))))
                except (TypeError,ValueError,AttributeError):retry_after=0.0
                self.sleep(max(min(5.0,1.0*(2**attempt)),retry_after))
            except (urllib.error.URLError,TimeoutError,OSError,ValueError) as exc:
                last_error=RPCError(type(exc).__name__)
                if attempt==self.max_attempts-1:raise last_error
                self.sleep(min(5.0,1.0*(2**attempt)))
        raise last_error or RPCError("RPC_FAILED")


def _instructions(tx):
    if not tx:return []
    msg=tx.get("transaction",{}).get("message",{})
    out=list(msg.get("instructions") or [])
    for group in tx.get("meta",{}).get("innerInstructions") or []:out.extend(group.get("instructions") or [])
    return out


def _signers(tx):
    return [k.get("pubkey") for k in tx.get("transaction",{}).get("message",{}).get("accountKeys",[]) if isinstance(k,dict) and k.get("signer")]


def _native_transfers(tx):
    rows=[]
    for ix in _instructions(tx):
        p=ix.get("parsed")
        if not isinstance(p,dict) or p.get("type")!="transfer":continue
        info=p.get("info") or {}
        src=info.get("source");dst=info.get("destination")
        if src and dst and "lamports" in info:
            rows.append({"source":src,"destination":dst,"lamports":str(info["lamports"])})
    return rows


def _native_funders(tx, target):
    return [(x["source"],x["lamports"]) for x in _native_transfers(tx) if x["destination"]==target]


def _token_account_meta(tx):
    keys=tx.get("transaction",{}).get("message",{}).get("accountKeys",[])
    names=[x.get("pubkey") if isinstance(x,dict) else x for x in keys]
    out={}
    balances=(tx.get("meta",{}).get("preTokenBalances") or [])+(tx.get("meta",{}).get("postTokenBalances") or [])
    for row in balances:
        try:address=names[int(row["accountIndex"])]
        except (KeyError,IndexError,TypeError,ValueError):continue
        owner=row.get("owner");mint=row.get("mint")
        if address and owner and mint:out[address]={"owner":owner,"mint":mint}
    return out


def _owner_token_transfers(tx):
    meta=_token_account_meta(tx);rows=[]
    for ix in _instructions(tx):
        p=ix.get("parsed")
        if not isinstance(p,dict) or p.get("type") not in {"transfer","transferChecked"}:continue
        info=p.get("info") or {};src=info.get("source");dst=info.get("destination")
        sm=meta.get(src) or {};dm=meta.get(dst) or {}
        mint=info.get("mint") or sm.get("mint") or dm.get("mint")
        so=sm.get("owner");do=dm.get("owner")
        if not mint or not so or not do or so==do:continue
        amount=(info.get("tokenAmount") or {}).get("amount") or info.get("amount")
        rows.append({"source_owner":so,"destination_owner":do,"mint":mint,"amount_raw":str(amount) if amount is not None else None})
    return rows


class UnionFind:
    def __init__(self, values):self.p={x:x for x in values}
    def find(self,x):
        while self.p[x]!=x:self.p[x]=self.p[self.p[x]];x=self.p[x]
        return x
    def union(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b:self.p[b]=a
    def groups(self):
        out=defaultdict(list)
        for x in self.p:out[self.find(x)].append(x)
        return list(out.values())


@dataclass
class Holder:
    token_account:str
    owner:str
    raw:int
    decimals:int
    role:str
    role_source:str
    account_program:str|None=None
    @property
    def quantity(self):return Decimal(self.raw)/(Decimal(10)**self.decimals)


class WalletClusterAnalyzer:
    def __init__(self,mint:str,*,rpc:SolanaReadOnlyRPC,special_registry:dict|None=None,history_per_holder=30,deep_holders=10,funding_lookback=12,material_pct=Decimal("1")):
        self.mint=mint;self.rpc=rpc;self.registry=special_registry or {};self.history_per_holder=int(history_per_holder);self.deep_holders=int(deep_holders);self.funding_lookback=int(funding_lookback);self.material_pct=Decimal(material_pct)
        self.edges=[];self.trades=[];self.funding=[];self.consolidations=[];self.tx_errors=[]
    def _entry(self,address):
        token_cfg=(self.registry.get("tokens") or {}).get(self.mint) or {}
        return (token_cfg.get("addresses") or {}).get(address) or (self.registry.get("addresses") or {}).get(address)

    def _role(self,address,account_info):
        explicit=self._entry(address)
        if explicit:return explicit.get("role","UNRESOLVED"),explicit.get("source","LOCAL_REGISTRY")
        value=(account_info or {}).get("value") if isinstance(account_info,dict) else None
        if not value:return "UNRESOLVED","ACCOUNT_INFO_UNAVAILABLE"
        program=value.get("owner")
        if value.get("executable"):return "PUBLIC_PROGRAM","RPC_EXECUTABLE_ACCOUNT"
        if program==SYSTEM_PROGRAM:return "ORDINARY","RPC_SYSTEM_OWNED"
        if program in DEX_PROGRAMS:return "PROTOCOL_VAULT","RPC_RECOGNIZED_DEX_PROGRAM:"+str(program)
        if program in TOKEN_PROGRAMS:return "TOKEN_ACCOUNT_OWNER_UNRESOLVED","RPC_TOKEN_PROGRAM_OWNED"
        return "PROGRAM_OWNED_UNRESOLVED","RPC_PROGRAM_OWNER:"+str(program)
    def _supply(self):
        r=self.rpc.call("getTokenSupply",[self.mint,{"commitment":"finalized"}],ttl=30)
        v=(r or {}).get("value") or {}
        return int(v["amount"]),int(v["decimals"])
    def _top(self):
        r=self.rpc.call("getTokenLargestAccounts",[self.mint,{"commitment":"finalized"}],ttl=30)
        return (r or {}).get("value") or []
    def _accounts(self,addresses):
        r=self.rpc.call("getMultipleAccounts",[addresses,{"encoding":"jsonParsed","commitment":"finalized"}],ttl=60)
        return (r or {}).get("value") or []
    def holders(self):
        supply,decimals=self._supply();top=self._top()[:20];tas=[x["address"] for x in top]
        infos=self._accounts(tas)
        owners=[];temp=[]
        for row,info in zip(top,infos):
            parsed=(((info or {}).get("data") or {}).get("parsed") or {}).get("info") or {}
            owner=parsed.get("owner")
            amount=((parsed.get("tokenAmount") or {}).get("amount")) or row.get("amount")
            if not owner or amount is None:continue
            owners.append(owner);temp.append((row,owner,int(amount)))
        unique_owners=list(dict.fromkeys(owners))
        owner_infos=self._accounts(unique_owners) if owners else []
        owner_map={o:i for o,i in zip(unique_owners,owner_infos)}
        result=[]
        for row,owner,raw in temp:
            role,source=self._role(owner,{"value":owner_map.get(owner)})
            program=(owner_map.get(owner) or {}).get("owner") if isinstance(owner_map.get(owner),dict) else None
            result.append(Holder(row["address"],owner,raw,decimals,role,source,program))
        return supply,decimals,result
    def _edge(self,a,b,kind,signature,**extra):
        if not a or not b or a==b:return
        x,y=sorted([a,b]);record={"a":x,"b":y,"type":kind,"signature":signature,**extra}
        key=_hash(record)
        if key not in {e["_key"] for e in self.edges}:self.edges.append({**record,"_key":key})
    def _scan_holder(self,holder:Holder,account_to_owner,top_owners):
        try:rows=self.rpc.call("getSignaturesForAddress",[holder.token_account,{"commitment":"finalized","limit":self.history_per_holder}],ttl=300)
        except Exception as exc:self.tx_errors.append({"address":holder.token_account,"error":type(exc).__name__});return None
        first=None
        for meta in rows or []:
            sig=meta.get("signature")
            if not sig:continue
            try:tx=self.rpc.call("getTransaction",[sig,{"commitment":"finalized","encoding":"jsonParsed","maxSupportedTransactionVersion":1}],ttl=3650*86400)
            except Exception as exc:self.tx_errors.append({"signature":sig,"error":type(exc).__name__});continue
            if not tx:continue
            bt=tx.get("blockTime")
            for tr in _native_transfers(tx):
                if tr["source"] in top_owners and tr["destination"] in top_owners:
                    self._edge(tr["source"],tr["destination"],"DIRECT_QUOTE_TRANSFER",sig,asset="SOL",amount_raw=tr["lamports"],block_time=bt)
            for tr in _owner_token_transfers(tx):
                src=tr["source_owner"];dst=tr["destination_owner"];mint=tr["mint"]
                if mint==self.mint:
                    if src in top_owners and dst in top_owners:
                        self._edge(src,dst,"DIRECT_TOKEN_TRANSFER",sig,amount_raw=tr["amount_raw"],block_time=bt)
                    elif src in top_owners and dst not in top_owners:
                        record={"source_owner":src,"destination_owner":dst,"mint":mint,"amount_raw":tr["amount_raw"],"signature":sig,"block_time":bt}
                        if not any(x["source_owner"]==src and x["destination_owner"]==dst and x["signature"]==sig for x in self.consolidations):self.consolidations.append(record)
                elif mint in {USDC,WSOL} and src in top_owners and dst in top_owners:
                    self._edge(src,dst,"DIRECT_QUOTE_TRANSFER",sig,asset=mint,amount_raw=tr["amount_raw"],block_time=bt)
            try:c=classify(sig,tx,holder.owner)
            except Exception:continue
            trade=c.get("trade") or {}
            if c.get("classification")=="ACTIVE_TRADE" and trade.get("mint")==self.mint:
                if bt is not None and (first is None or bt < first["block_time"]):
                    first={"block_time":int(bt),"signature":sig}
                record={"owner":holder.owner,"signature":sig,"block_time":bt,"direction":trade.get("direction"),"quote_asset":trade.get("quote_asset"),"quote_amount_raw":trade.get("quote_amount_raw"),"quote_decimals":trade.get("quote_decimals"),"program_ids":(c.get("evidence") or {}).get("program_ids") or [],"signers":_signers(tx)}
                if not any(x["owner"]==holder.owner and x["signature"]==sig for x in self.trades):self.trades.append(record)
        return first
    def _scan_funding(self,holder:Holder,first,top_owners):
        if not first:return
        options={"commitment":"finalized","limit":self.funding_lookback,"before":first["signature"]}
        try:rows=self.rpc.call("getSignaturesForAddress",[holder.owner,options],ttl=300)
        except Exception:return
        best=None
        for meta in rows or []:
            sig=meta.get("signature")
            if not sig:continue
            try:tx=self.rpc.call("getTransaction",[sig,{"commitment":"finalized","encoding":"jsonParsed","maxSupportedTransactionVersion":1}],ttl=3650*86400)
            except Exception as exc:
                self.tx_errors.append({"signature":sig,"phase":"funding","error":type(exc).__name__})
                continue
            if not tx:
                self.tx_errors.append({"signature":sig,"phase":"funding","error":"UNAVAILABLE_ON_PUBLIC_RPC"})
                continue
            bt=tx.get("blockTime")
            if bt is None or bt>first["block_time"]:continue
            for source,lamports in _native_funders(tx,holder.owner):
                candidate={"owner":holder.owner,"source":source,"lamports":lamports,"signature":sig,"block_time":bt}
                if source in top_owners:self._edge(source,holder.owner,"DIRECT_QUOTE_TRANSFER",sig,asset="SOL",amount_raw=lamports,block_time=bt)
                if best is None or bt>best["block_time"]:best=candidate
        if best and not any(x["owner"]==best["owner"] and x["signature"]==best["signature"] for x in self.funding):self.funding.append(best)
    def _derive_pair_edges(self):
        by_funder=defaultdict(list);by_sig=defaultdict(list)
        for f in self.funding:by_funder[f["source"]].append(f);by_sig[f["signature"]].append(f)
        for source,rows in by_funder.items():
            if len({r["owner"] for r in rows})<2:continue
            role=(self._entry(source) or {}).get("role")
            if role=="CEX":kind="COMMON_FUNDER_CEX"
            elif role in {"PUBLIC_INFRA","PUBLIC_PROGRAM","ROUTER","BRIDGE","AMM_POOL","PROTOCOL_VAULT"}:kind="SHARED_INFRA"
            elif role in {"EOA","DEV","CREATOR","TREASURY"}:kind="COMMON_FUNDER_EOA"
            else:kind="COMMON_FUNDER_UNRESOLVED"
            owners=sorted({r["owner"] for r in rows})
            for i,a in enumerate(owners):
                for b in owners[i+1:]:self._edge(a,b,kind,rows[0]["signature"],funder=source)
        by_destination=defaultdict(set)
        for row in self.consolidations:by_destination[row["destination_owner"]].add(row["source_owner"])
        for destination,owners in by_destination.items():
            role=(self._entry(destination) or {}).get("role")
            if role in {"EOA","DEV","CREATOR","TREASURY"}:kind="COMMON_CONSOLIDATION"
            elif role in {"PUBLIC_INFRA","PUBLIC_PROGRAM","ROUTER","BRIDGE","AMM_POOL","PROTOCOL_VAULT","CEX"}:kind="SHARED_INFRA"
            else:kind="COMMON_CONSOLIDATION_UNRESOLVED"
            owners=sorted(owners)
            if len(owners)>1:
                evidence=next(x for x in self.consolidations if x["destination_owner"]==destination)
                for i,a in enumerate(owners):
                    for b in owners[i+1:]:self._edge(a,b,kind,evidence["signature"],destination=destination)
        for sig,rows in by_sig.items():
            owners=sorted({r["owner"] for r in rows})
            if len(owners)>1:
                for i,a in enumerate(owners):
                    for b in owners[i+1:]:self._edge(a,b,"BATCH_FUNDING",sig)
        trades=sorted(self.trades,key=lambda x:(x.get("block_time") or 0,x["owner"]))
        pair_counts=defaultdict(lambda:defaultdict(int))
        for i,a in enumerate(trades):
            for b in trades[i+1:]:
                if a["owner"]==b["owner"]:continue
                if a.get("block_time") is None or b.get("block_time") is None:continue
                if b["block_time"]-a["block_time"]>2:break
                pair=tuple(sorted([a["owner"],b["owner"]]))
                if a["direction"]==b["direction"]:
                    kind="SYNC_BUY" if a["direction"]=="BUY" else "SYNC_SELL";pair_counts[pair][kind]+=1
                    self._edge(*pair,kind,a["signature"],other_signature=b["signature"],seconds_apart=abs(a["block_time"]-b["block_time"]))
                if a.get("quote_asset")==b.get("quote_asset") and a.get("quote_amount_raw")==b.get("quote_amount_raw") and a.get("quote_amount_raw"):
                    pair_counts[pair]["IDENTICAL_SIZE"]+=1;self._edge(*pair,"IDENTICAL_SIZE",a["signature"],other_signature=b["signature"],quote_amount_raw=a["quote_amount_raw"])
                common=set(a.get("program_ids") or []) & set(b.get("program_ids") or [])
                public_common={
                    program for program in common
                    if program in INFRA_PROGRAMS
                    or program in DEX_PROGRAMS
                    or (self._entry(program) or {}).get("role") in {"PUBLIC_INFRA","PUBLIC_PROGRAM","ROUTER","AMM_POOL","PROTOCOL_VAULT"}
                }
                if public_common:
                    self._edge(*pair,"SHARED_INFRA",a["signature"],other_signature=b["signature"],programs=sorted(public_common))
                nonpublic_common=common-public_common
                if nonpublic_common:
                    pair_counts[pair]["SAME_EXECUTION_PROGRAM"]+=1;self._edge(*pair,"SAME_EXECUTION_PROGRAM",a["signature"],other_signature=b["signature"],programs=sorted(nonpublic_common))
        signer_owners=defaultdict(set)
        for t in trades:
            for signer in t.get("signers") or []:
                if signer!=t["owner"] and signer not in INFRA_PROGRAMS:signer_owners[signer].add(t["owner"])
        for signer,owners in signer_owners.items():
            owners=sorted(owners)
            if len(owners)>1:
                role=(self._entry(signer) or {}).get("role")
                if role in {"EOA","DEV","CREATOR","TREASURY"}:kind="COMMON_SIGNER"
                elif role in {"PUBLIC_INFRA","PUBLIC_PROGRAM","ROUTER","BRIDGE","AMM_POOL","PROTOCOL_VAULT","CEX"}:kind="SHARED_INFRA"
                else:kind="COMMON_SIGNER_UNRESOLVED"
                for i,a in enumerate(owners):
                    for b in owners[i+1:]:self._edge(a,b,kind,"MULTI_TX",signer=signer)
        for pair,counts in pair_counts.items():
            if sum(counts.values())>=3:self._edge(*pair,"REPEATED_SYNC_BEHAVIOR","MULTI_TX",counts=dict(counts))
    @staticmethod
    def _pct(raw,supply):
        return None if supply<=0 else str((Decimal(raw)*Decimal(100)/Decimal(supply)).quantize(Decimal("0.0001")))
    def analyze(self):
        supply,decimals,holders=self.holders()
        account_to_owner={h.token_account:h.owner for h in holders}
        firsts={};deep=[];deep_seen=set()
        for h in holders:
            if h.owner in deep_seen:continue
            deep_seen.add(h.owner);deep.append(h)
            if len(deep)>=self.deep_holders:break
        top_owners=set(owners for owners in account_to_owner.values())
        for h in deep:firsts[h.owner]=self._scan_holder(h,account_to_owner,top_owners)
        for h in deep:self._scan_funding(h,firsts.get(h.owner),top_owners)
        self._derive_pair_edges()
        owners=sorted({h.owner for h in holders});balances=defaultdict(int)
        for h in holders:balances[h.owner]+=h.raw
        relation=UnionFind(owners);control=UnionFind(owners);execution=UnionFind(owners)
        pair_types=defaultdict(set)
        for e in self.edges:
            pair=(e["a"],e["b"]);pair_types[pair].add(e["type"])
            if e["type"] in {"DIRECT_TOKEN_TRANSFER","DIRECT_QUOTE_TRANSFER"}:relation.union(*pair)
        for pair,types in pair_types.items():
            strong=len(types & STRONG);behavior=len(types & BEHAVIOR)
            if strong>=2 or (strong>=1 and behavior>=1) or ("DIRECT_TOKEN_TRANSFER" in types and strong>=1):control.union(*pair)
            if behavior>=2 or "REPEATED_SYNC_BEHAVIOR" in types:execution.union(*pair)
        def group_records(groups,kind,confidence):
            out=[]
            for idx,g in enumerate(groups,1):
                if len(g)<2:continue
                raw=sum(balances[x] for x in g)
                evidence=[{k:v for k,v in e.items() if k!="_key"} for e in self.edges if e["a"] in g and e["b"] in g]
                out.append({
                    "cluster_id":f"{kind}-{idx}","confidence":confidence,"wallets":sorted(g),
                    "wallet_balances_raw":{x:str(balances[x]) for x in sorted(g)},
                    "combined_raw":str(raw),"supply_pct":self._pct(raw,supply),"evidence":evidence,
                    "first_target_acquisition":{x:({"block_time":firsts[x]["block_time"],"signature":firsts[x]["signature"],"type":"BOUNDED_EARLIEST_MARKET_TRADE"} if firsts.get(x) else {"block_time":None,"signature":None,"type":"UNRESOLVED"}) for x in sorted(g)},
                    "funding_evidence":[x for x in self.funding if x["owner"] in g],
                    "trade_evidence":[x for x in self.trades if x["owner"] in g],
                })
            return sorted(out,key=lambda x:int(x["combined_raw"]),reverse=True)
        relation_groups=group_records(relation.groups(),"REL","CONFIRMED_RELATION")
        control_groups=group_records(control.groups(),"CTRL","PROBABLE_CONTROL_CLUSTER")
        execution_groups=group_records(execution.groups(),"EXEC","PROBABLE_EXECUTION_CLUSTER")
        raw_top10=sum(h.raw for h in holders[:10])
        nonspecial=[h for h in holders if h.role not in SPECIAL_ROLES]
        ex_lp=[h for h in holders if h.role not in {"LP","AMM_POOL"}]
        ex_special_top10=sum(h.raw for h in nonspecial[:10])
        ex_lp_top10=sum(h.raw for h in ex_lp[:10])
        dev_owners={h.owner for h in holders if h.role in DEV_ROLES}
        dev_linked_owners=set(dev_owners)
        for group in control.groups():
            if set(group) & dev_owners:
                dev_linked_owners.update(group)
        dev_raw=sum(balances[o] for o in dev_linked_owners)
        cluster_values=[];seen=set();group_by_owner={}
        for g in control.groups():
            for o in g:group_by_owner[o]=tuple(sorted(g))
        for h in nonspecial:
            g=group_by_owner.get(h.owner,(h.owner,))
            if g in seen:continue
            seen.add(g);cluster_values.append(sum(balances[o] for o in g))
        cluster_values.sort(reverse=True)
        unresolved_raw=0;classified=set()
        # Execution-only similarity never resolves holder identity/control. Keep
        # those material holders in the unresolved bucket unless a direct
        # relation or probable-control cluster independently explains them.
        for g in control_groups+relation_groups:classified.update(g["wallets"])
        for h in nonspecial:
            pct=Decimal(h.raw)*100/Decimal(supply) if supply else Decimal(0)
            if pct>=self.material_pct and h.owner not in classified and h.role in {"ORDINARY","UNRESOLVED","PROGRAM_OWNED_UNRESOLVED","TOKEN_ACCOUNT_OWNER_UNRESOLVED"}:unresolved_raw+=h.raw
        token_cfg=(self.registry.get("tokens") or {}).get(self.mint) or {}
        normalization_complete=bool(token_cfg.get("normalization_complete",self.registry.get("normalization_complete",False)))
        metrics={
            "RAW_TOP10_PCT":self._pct(raw_top10,supply),
            "EX_LP_TOP10_PCT":self._pct(ex_lp_top10,supply) if normalization_complete else "UNRESOLVED",
            "EX_SPECIAL_TOP10_PCT":self._pct(ex_special_top10,supply) if normalization_complete else "UNRESOLVED",
            "LARGEST_CONFIRMED_RELATION_GROUP_PCT":relation_groups[0]["supply_pct"] if relation_groups else "0",
            "LARGEST_PROBABLE_CONTROL_CLUSTER_PCT":control_groups[0]["supply_pct"] if control_groups else "0",
            "LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT":execution_groups[0]["supply_pct"] if execution_groups else "0",
            "DEV_LINKED_CLUSTER_PCT":self._pct(dev_raw,supply) if normalization_complete else "UNRESOLVED",
            "CLUSTER_ADJUSTED_TOP10_PCT":self._pct(sum(cluster_values[:10]),supply) if normalization_complete else "UNRESOLVED",
            "UNRESOLVED_MATERIAL_HOLDER_PCT":self._pct(unresolved_raw,supply),
            "KNOWN_EX_LP_TOP10_PCT":self._pct(ex_lp_top10,supply),
            "KNOWN_EX_SPECIAL_TOP10_PCT":self._pct(ex_special_top10,supply),
            "KNOWN_CLUSTER_ADJUSTED_TOP10_PCT":self._pct(sum(cluster_values[:10]),supply),
        }
        holder_rows=[{"rank":i+1,"token_account":h.token_account,"owner":h.owner,"raw":str(h.raw),"quantity":str(h.quantity),"supply_pct":self._pct(h.raw,supply),"role":h.role,"role_source":h.role_source,"account_program":h.account_program} for i,h in enumerate(holders)]
        return {
            "schema_version":1,"mint":self.mint,"source":"SOLANA_FINALIZED_JSON_RPC","rpc_endpoint":self.rpc.endpoint,
            "observed_at":time.time(),"supply_raw":str(supply),"decimals":decimals,"holders":holder_rows,
            "metrics":metrics,"confirmed_relation_groups":relation_groups,"probable_control_clusters":control_groups,
            "probable_execution_clusters":execution_groups,
            "shared_infrastructure_exclusions":[{k:v for k,v in e.items() if k!="_key"} for e in self.edges if e["type"] in {"COMMON_FUNDER_CEX","SHARED_INFRA"}],
            "unresolved_relation_edges":[{k:v for k,v in e.items() if k!="_key"} for e in self.edges if e["type"] in {"COMMON_FUNDER_UNRESOLVED","COMMON_SIGNER_UNRESOLVED","COMMON_CONSOLIDATION_UNRESOLVED"}],
            "edges":[{k:v for k,v in e.items() if k!="_key"} for e in self.edges],
            "funding_evidence":self.funding,"consolidation_evidence":self.consolidations,"trade_evidence":self.trades,"transaction_errors":self.tx_errors,
            "coverage":{"top_accounts_resolved":len(holders),"deep_holders_scanned":len(deep),"history_per_holder":self.history_per_holder,"funding_lookback":self.funding_lookback,"material_pct":str(self.material_pct),"special_normalization_complete":normalization_complete,"rpc_calls":self.rpc.calls,"rpc_cache_hits":self.rpc.cache_hits,"rpc_endpoint_history":getattr(self.rpc,"endpoint_history",[self.rpc.endpoint])},
            "limitations":[
                "Only raw finalized RPC evidence and explicit local labels are treated as authoritative.",
                "CEX/public-infrastructure identity is never guessed from funding alone.",
                "Program-owned holder accounts remain unresolved unless explicitly labelled.",
                "Bounded history can miss older funding, consolidation, and cross-token coordination.",
                "PROBABLE_EXECUTION_CLUSTER never implies common beneficial ownership.",
            ],
        }


def load_registry(path:Path|None):
    if path is None:return {"schema_version":1,"addresses":{}}
    data=json.loads(Path(path).read_text())
    if data.get("schema_version")!=1 or not isinstance(data.get("addresses"),dict) or not isinstance(data.get("tokens",{}),dict):raise ValueError("SPECIAL_REGISTRY_SCHEMA")
    return data


def markdown(report:dict)->str:
    m=report["metrics"];lines=[f"# Meme Wallet Cluster — {report['mint']}","",f"Source: {report['source']}","", "## Concentration"]
    for k,v in m.items():
        suffix="%" if v not in {"UNRESOLVED","UNAVAILABLE",None} else ""
        lines.append(f"- {k}: {v}{suffix}")
    lines+=["","## Top holders","", "|#|Owner|Share|Role|","|---:|---|---:|---|"]
    for h in report["holders"]:lines.append(f"|{h['rank']}|{h['owner']}|{h['supply_pct']}%|{h['role']}|")
    for title,key in [("Confirmed relations","confirmed_relation_groups"),("Probable control","probable_control_clusters"),("Probable execution","probable_execution_clusters")]:
        lines+=["",f"## {title}"]
        rows=report[key]
        if not rows:lines.append("- None confirmed in bounded evidence.")
        for g in rows:lines.append(f"- {g['cluster_id']}: {g['supply_pct']}% — "+", ".join(g["wallets"]))
    lines+=["","## Coverage","",json.dumps(report["coverage"],ensure_ascii=False,indent=2),"", "## Limitations"]
    lines += [f"- {x}" for x in report["limitations"]]
    return "\n".join(lines)+"\n"
