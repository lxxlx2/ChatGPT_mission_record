"""Free, read-only Solana wallet-cluster analysis for Meme CA research.

The analyzer prefers raw finalized JSON-RPC evidence over third-party labels.
It never upgrades a graph link to common ownership without the explicit
multi-evidence rules in WALLET_CLUSTER_ANALYSIS_SPEC.md.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..frank.parser import DEX_PROGRAMS, INFRA_PROGRAMS
from ..signals.classifier import classify
from ..market.sol_usd import USDC, WSOL
from .market import DexScreenerMarketClient

DEFAULT_RPC = "https://api.mainnet.solana.com"
DEFAULT_RPC_FALLBACKS = (
    "https://solana-rpc.publicnode.com",
    "https://api.mainnet-beta.solana.com",
    "https://rpc.ankr.com/solana",
)
SYSTEM_PROGRAM = "11111111111111111111111111111111"
TOKEN_PROGRAMS = {
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
}
SENSITIVE_EXTENSION_WORDS = (
    "transferfee","transferhook","permanentdelegate","pausable",
    "confidentialtransfer","defaultaccountstate",
)
SPECIAL_ROLES = {
    "LP", "AMM_POOL", "PROTOCOL_VAULT", "ESCROW", "VESTING", "LOCK",
    "BURN", "CEX", "BRIDGE", "ROUTER", "PUBLIC_INFRA", "PUBLIC_PROGRAM", "MARKET_MAKER",
}
DEV_ROLES = {"DEV", "CREATOR", "TREASURY"}

def _extension_name(value):
    return str(value or "").lower().replace("_","").replace("-","")

def _config_values(value, wanted):
    found=[]
    if isinstance(value,dict):
        for key,child in value.items():
            if _extension_name(key) in wanted:found.append(child)
            found.extend(_config_values(child,wanted))
    elif isinstance(value,list):
        for child in value:found.extend(_config_values(child,wanted))
    return found

def _authority_active(value):
    return value not in (None,"","11111111111111111111111111111111")

def _decimal_value(value):
    try:
        number=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError):
        return None
    return number if number.is_finite() else None

def _positive_number(value):
    number=_decimal_value(value)
    return number is not None and number>0

def _authority_state(value):
    if value in (None,"","11111111111111111111111111111111"):
        return "REVOKED"
    if isinstance(value,str):
        return "ACTIVE"
    return "INVALID"

def _all_valid_nonnegative(values):
    if not values:return False
    parsed=[_decimal_value(value) for value in values]
    return all(value is not None and value>=0 for value in parsed)

def _direct_alias_values(mapping, aliases):
    if not isinstance(mapping,dict):
        return []
    return [
        value for key,value in mapping.items()
        if _extension_name(key) in aliases
    ]

def _fee_schedule(config, schedule_name):
    schedules=_config_values(config,{schedule_name})
    if not schedules:
        return {"status":"INCOMPLETE"}
    if len(schedules)!=1 or not isinstance(schedules[0],dict):
        return {"status":"INVALID"}
    schedule=schedules[0]
    basis=_direct_alias_values(schedule,{"transferfeebasispoints","basispoints"})
    maximum=_direct_alias_values(schedule,{"maximumfee","maxfee"})
    if not basis or not maximum:
        return {"status":"INCOMPLETE"}
    if len(basis)!=1 or len(maximum)!=1:
        return {"status":"INVALID"}
    basis_value=_decimal_value(basis[0]);maximum_value=_decimal_value(maximum[0])
    if (
        basis_value is None or maximum_value is None
        or basis_value<0 or maximum_value<0
    ):
        return {"status":"INVALID"}
    return {
        "status":"VALID",
        "basis_points":basis_value,
        "maximum_fee":maximum_value,
    }

def _extension_risk(extension):
    if not isinstance(extension,dict):
        return {"name":str(extension),"status":"UNRESOLVED","reason":"EXTENSION_CONFIG_UNAVAILABLE","config":extension}
    name=extension.get("extension") or extension.get("type") or "UNKNOWN"
    normalized=_extension_name(name)
    config={k:v for k,v in extension.items() if k not in {"extension","type"}}
    status="UNRESOLVED";reason="SENSITIVE_EXTENSION_STATE_UNRESOLVED"
    authorities=_config_values(config,{"authority","transferfeeconfigauthority","withdrawwithheldauthority"})
    active_authority=any(_authority_active(v) for v in authorities)
    if "transferfee" in normalized:
        config_authorities=_config_values(config,{"transferfeeconfigauthority"})
        withdraw_authorities=_config_values(config,{"withdrawwithheldauthority"})
        authority_values=config_authorities+withdraw_authorities
        authority_states=[_authority_state(v) for v in authority_values]
        older=_fee_schedule(config,"oldertransferfee")
        newer=_fee_schedule(config,"newertransferfee")
        positive_fee=any(
            schedule.get("status")=="VALID"
            and (schedule["basis_points"]>0 or schedule["maximum_fee"]>0)
            for schedule in (older,newer)
        )
        # A directly parseable positive fee elsewhere in an incomplete payload
        # is still sufficient to remain fail-closed as active risk.
        if not positive_fee:
            raw_fee_values=_config_values(config,{"transferfeebasispoints","basispoints","maximumfee","maxfee"})
            positive_fee=any(_positive_number(v) for v in raw_fee_values)
        if "ACTIVE" in authority_states or positive_fee:
            status="ACTIVE_RISK";reason="TRANSFER_FEE_ACTIVE_OR_MUTABLE"
        else:
            authorities_complete=len(config_authorities)==1 and len(withdraw_authorities)==1
            authorities_valid=(
                authorities_complete
                and all(state=="REVOKED" for state in authority_states)
            )
            schedules=(older,newer)
            schedules_complete=all(item["status"]!="INCOMPLETE" for item in schedules)
            schedules_valid=all(item["status"]=="VALID" for item in schedules)
            schedules_zero=(
                schedules_valid
                and all(
                    item["basis_points"]==0 and item["maximum_fee"]==0
                    for item in schedules
                )
            )
            if authorities_valid and schedules_zero:
                status="INACTIVE";reason="TRANSFER_FEE_ZERO_AND_AUTHORITIES_REVOKED"
            elif not authorities_complete or not schedules_complete:
                reason="TRANSFER_FEE_CONFIG_INCOMPLETE"
            else:
                reason="TRANSFER_FEE_CONFIG_INVALID"
    elif "transferhook" in normalized:
        hook_authorities=_config_values(config,{"authority"})
        programs=_config_values(config,{"programid","programidpubkey"})
        authority_states=[_authority_state(v) for v in hook_authorities]
        program_states=[_authority_state(v) for v in programs]
        if "ACTIVE" in authority_states or "ACTIVE" in program_states:
            status="ACTIVE_RISK";reason="TRANSFER_HOOK_ACTIVE_OR_MUTABLE"
        elif (
            len(hook_authorities)==1 and len(programs)==1
            and authority_states==["REVOKED"]
            and program_states==["REVOKED"]
        ):
            status="INACTIVE";reason="TRANSFER_HOOK_DISABLED_AND_AUTHORITY_REVOKED"
        elif not hook_authorities or not programs:
            reason="TRANSFER_HOOK_CONFIG_INCOMPLETE"
        else:
            reason="TRANSFER_HOOK_CONFIG_INVALID"
    elif "permanentdelegate" in normalized:
        delegates=_config_values(config,{"delegate"})
        if any(_authority_active(v) for v in delegates):
            status="ACTIVE_RISK";reason="PERMANENT_DELEGATE_ACTIVE"
        elif delegates:
            status="INACTIVE";reason="PERMANENT_DELEGATE_REVOKED"
    elif "pausable" in normalized:
        paused=_config_values(config,{"paused","ispaused"})
        if active_authority or any(v is True or str(v).lower()=="true" for v in paused):
            status="ACTIVE_RISK";reason="PAUSABLE_ACTIVE_OR_MUTABLE"
        elif authorities or paused:
            status="INACTIVE";reason="PAUSABLE_NOT_PAUSED_AND_AUTHORITY_REVOKED"
    elif "defaultaccountstate" in normalized:
        states=[str(v).lower() for v in _config_values(config,{"state","accountstate"}) if v is not None]
        if any("frozen" in v for v in states):
            status="ACTIVE_RISK";reason="DEFAULT_ACCOUNT_STATE_FROZEN"
        elif states and all("initialized" in v for v in states):
            status="INACTIVE";reason="DEFAULT_ACCOUNT_STATE_INITIALIZED"
    elif "confidentialtransfer" in normalized:
        if active_authority:
            status="ACTIVE_RISK";reason="CONFIDENTIAL_TRANSFER_MUTABLE_AUTHORITY"
        elif authorities:
            status="UNRESOLVED";reason="CONFIDENTIAL_TRANSFER_PRESENT_AUTHORITY_REVOKED_OTHER_STATE_UNRESOLVED"
    return {"name":str(name),"status":status,"reason":reason,"config":config}
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


class SolanaReadOnlyRPC:
    ALLOWED={"getTokenSupply","getTokenLargestAccounts","getMultipleAccounts","getAccountInfo","getSignaturesForAddress","getTransaction"}
    RETRYABLE_HTTP={403,429,500,502,503,504}

    def __init__(
        self,
        endpoint=DEFAULT_RPC,
        *,
        fallback_endpoints=None,
        open_url=urllib.request.urlopen,
        sleep=time.sleep,
        min_interval=.45,
        cache:RpcCache|None=None,
    ):
        endpoints=[endpoint]
        endpoints.extend(DEFAULT_RPC_FALLBACKS if fallback_endpoints is None else fallback_endpoints)
        self.endpoints=[]
        from urllib.parse import urlsplit
        for value in endpoints:
            if not value:continue
            if not isinstance(value,str) or any(c.isspace() for c in value):
                raise ValueError("RPC_ENDPOINT_INVALID")
            parsed=urlsplit(value)
            if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
                raise ValueError("RPC_ENDPOINT_INVALID")
            if value not in self.endpoints:self.endpoints.append(value)
        self.endpoint=self.endpoints[0]
        self.open_url=open_url
        self.sleep=sleep
        self.min_interval=float(min_interval)
        self.cache=cache
        self.cache_hits=0
        self.calls=0
        self.endpoint_calls=defaultdict(int)
        self.endpoint_failures=defaultdict(int)
        self._last_by_endpoint=defaultdict(float)
        self._cooldown_until=defaultdict(float)

    def _next_endpoint(self):
        now=time.monotonic()
        primary=self.endpoints[0]
        # Keep the official/configured primary as the normal source. Only move to
        # fallbacks while the primary is in an error cooldown window.
        primary_cooldown=self._cooldown_until[primary]
        if primary_cooldown<=now:
            endpoint=primary
            ready=max(now,self._last_by_endpoint[endpoint]+self.min_interval)
        else:
            ranked=[]
            for priority,endpoint in enumerate(self.endpoints[1:],1):
                ready=max(
                    self._cooldown_until[endpoint],
                    self._last_by_endpoint[endpoint]+self.min_interval,
                )
                ranked.append((ready,priority,endpoint))
            if ranked:
                ready,_,endpoint=min(ranked,key=lambda x:(x[0],x[1]))
            else:
                endpoint=primary;ready=max(primary_cooldown,self._last_by_endpoint[primary]+self.min_interval)
        delay=ready-now
        if delay>0:self.sleep(delay)
        self.endpoint=endpoint
        return endpoint

    @staticmethod
    def _retry_after(exc):
        try:return min(60.0,max(0.0,float(exc.headers.get("Retry-After","0"))))
        except (TypeError,ValueError,AttributeError):return 0.0

    @staticmethod
    def _rpc_rate_limited(error):
        if not isinstance(error,dict):return False
        code=error.get("code")
        message=str(error.get("message") or "").lower()
        return code in {-32005,-32429,429} or "rate limit" in message or "too many request" in message

    def call(self, method, params, *, ttl=0):
        if method not in self.ALLOWED:raise ValueError("READ_ONLY_METHOD_ALLOWLIST")
        now=time.time()
        if ttl and self.cache:
            hit=self.cache.get(method,params,now)
            if hit is not None:self.cache_hits+=1;return hit

        body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
        last_error=None
        null_seen=0
        max_attempts=max(6,len(self.endpoints)*3)
        for attempt in range(max_attempts):
            endpoint=self._next_endpoint()
            req=urllib.request.Request(endpoint,data=body,headers={
                "Content-Type":"application/json",
                "User-Agent":"mission-meme-cluster/2",
            })
            try:
                self._last_by_endpoint[endpoint]=time.monotonic()
                self.calls+=1;self.endpoint_calls[endpoint]+=1
                with self.open_url(req,timeout=20) as response:value=json.loads(response.read())
                if value.get("error"):
                    error=value.get("error") or {}
                    if self._rpc_rate_limited(error):
                        self.endpoint_failures[endpoint]+=1
                        self._cooldown_until[endpoint]=max(
                            self._cooldown_until[endpoint],
                            time.monotonic()+min(30.0,1.5*(2**min(attempt,4))),
                        )
                        last_error=RPCError("RPC_RATE_LIMITED")
                        continue
                    raise RPCError("RPC_"+str(error.get("code","ERROR")))
                if "result" not in value:raise RPCError("RPC_ENVELOPE_INVALID")
                result=value["result"]
                if method=="getTransaction" and result is None and len(self.endpoints)>1 and null_seen<1:
                    null_seen+=1
                    continue
                if ttl and self.cache and result is not None:
                    self.cache.put(method,params,result,ttl,time.time())
                return result
            except urllib.error.HTTPError as exc:
                last_error=RPCError("HTTP_"+str(exc.code));self.endpoint_failures[endpoint]+=1
                if exc.code not in self.RETRYABLE_HTTP:raise last_error
                retry=max(self._retry_after(exc),min(30.0,1.5*(2**min(attempt,4))))
                self._cooldown_until[endpoint]=max(self._cooldown_until[endpoint],time.monotonic()+retry)
            except (urllib.error.URLError,TimeoutError,OSError,ValueError) as exc:
                last_error=RPCError(type(exc).__name__);self.endpoint_failures[endpoint]+=1
                self._cooldown_until[endpoint]=max(
                    self._cooldown_until[endpoint],
                    time.monotonic()+min(10.0,1.0*(2**min(attempt,3))),
                )
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
    def __init__(
        self,mint:str,*,rpc:SolanaReadOnlyRPC,special_registry:dict|None=None,
        history_per_holder=30,deep_holders=10,funding_lookback=12,
        material_pct=Decimal("1"),market_client:DexScreenerMarketClient|None=None,
        adaptive_history_per_holder=None,adaptive_funding_lookback=None,
        progress_callback=None,
    ):
        self.mint=mint;self.rpc=rpc;self.registry=special_registry or {};self.history_per_holder=int(history_per_holder);self.deep_holders=int(deep_holders);self.funding_lookback=int(funding_lookback);self.material_pct=Decimal(material_pct)
        self.market_client=market_client
        self.adaptive_history_per_holder=int(adaptive_history_per_holder) if adaptive_history_per_holder else None
        self.adaptive_funding_lookback=int(adaptive_funding_lookback) if adaptive_funding_lookback else None
        self.progress_callback=progress_callback
        self.edges=[];self.trades=[];self.funding=[];self.consolidations=[];self.tx_errors=[]
        self.adaptive_deepened_owners=[]

    def _progress(self,stage,**details):
        if not self.progress_callback:return
        try:self.progress_callback(stage,details)
        except Exception:
            # UI progress must never alter evidence collection or report correctness.
            return

    @staticmethod
    def _accepts_optional_limit(method, positional_without_limit):
        """Keep compatibility with old tests/local overrides that use the pre-v3 signature."""
        try:
            params=list(inspect.signature(method).parameters.values())
        except (TypeError,ValueError):
            return True
        if any(p.kind==inspect.Parameter.VAR_POSITIONAL for p in params):
            return True
        positional=[
            p for p in params
            if p.kind in (inspect.Parameter.POSITIONAL_ONLY,inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        return len(positional)>positional_without_limit

    def _scan_holder_bounded(self,holder,account_to_owner,top_owners,limit):
        method=self._scan_holder
        if self._accepts_optional_limit(method,3):
            return method(holder,account_to_owner,top_owners,limit)
        # Legacy override path: preserve the old 3-argument call contract.
        original=self.history_per_holder
        self.history_per_holder=int(limit)
        try:return method(holder,account_to_owner,top_owners)
        finally:self.history_per_holder=original

    def _scan_funding_bounded(self,holder,first,top_owners,limit):
        method=self._scan_funding
        if self._accepts_optional_limit(method,3):
            return method(holder,first,top_owners,limit)
        original=self.funding_lookback
        self.funding_lookback=int(limit)
        try:return method(holder,first,top_owners)
        finally:self.funding_lookback=original
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

    @staticmethod
    def _find_key(value,key):
        if isinstance(value,dict):
            if key in value:return True,value.get(key)
            for child in value.values():
                found,result=WalletClusterAnalyzer._find_key(child,key)
                if found:return True,result
        elif isinstance(value,list):
            for child in value:
                found,result=WalletClusterAnalyzer._find_key(child,key)
                if found:return True,result
        return False,None

    def token_profile(self):
        try:
            result=self.rpc.call("getAccountInfo",[self.mint,{"encoding":"jsonParsed","commitment":"finalized"}],ttl=60)
        except Exception as exc:
            return {"status":"UNAVAILABLE","source":"SOLANA_FINALIZED_JSON_RPC","reason":type(exc).__name__}
        value=(result or {}).get("value") or {}
        parsed=((value.get("data") or {}).get("parsed") or {}) if isinstance(value.get("data"),dict) else {}
        info=parsed.get("info") or {}
        program=value.get("owner")
        if program=="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb":token_program="SPL Token-2022"
        elif program=="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":token_program="SPL Token"
        else:token_program=program or "UNRESOLVED"
        found_update,update_authority=self._find_key(parsed,"updateAuthority")
        extension_names=[];extension_details=[]
        for extension in info.get("extensions") or []:
            if isinstance(extension,dict):
                name=extension.get("extension") or extension.get("type")
                if name:extension_names.append(str(name))
                normalized=_extension_name(name)
                if any(word in normalized for word in SENSITIVE_EXTENSION_WORDS):
                    extension_details.append(_extension_risk(extension))
            elif extension:
                extension_names.append(str(extension))
                normalized=_extension_name(extension)
                if any(word in normalized for word in SENSITIVE_EXTENSION_WORDS):
                    extension_details.append(_extension_risk(extension))
        sensitive=[row["name"] for row in extension_details]
        active_extension_risks=[row for row in extension_details if row["status"]=="ACTIVE_RISK"]
        inactive_sensitive_extensions=[row for row in extension_details if row["status"]=="INACTIVE"]
        unresolved_sensitive_extensions=[row for row in extension_details if row["status"]=="UNRESOLVED"]
        risk_flags=[]
        if info.get("mintAuthority"):risk_flags.append("MINT_AUTHORITY_ACTIVE")
        if info.get("freezeAuthority"):risk_flags.append("FREEZE_AUTHORITY_ACTIVE")
        risk_flags.extend("ACTIVE_EXTENSION:"+row["name"]+":"+row["reason"] for row in active_extension_risks)
        return {
            "status":"OK",
            "source":"SOLANA_FINALIZED_JSON_RPC",
            "token_program":token_program,
            "program_id":program,
            "mint_authority":info.get("mintAuthority"),
            "freeze_authority":info.get("freezeAuthority"),
            "decimals":info.get("decimals"),
            "supply_raw":str(info.get("supply")) if info.get("supply") is not None else None,
            "is_initialized":info.get("isInitialized"),
            "metadata_update_authority":update_authority if found_update else "UNAVAILABLE",
            "metadata_update_authority_status":"CHAIN_PARSED" if found_update else "UNAVAILABLE",
            "extensions":extension_names,
            "sensitive_extensions":sensitive,
            "sensitive_extension_details":extension_details,
            "active_extension_risks":active_extension_risks,
            "inactive_sensitive_extensions":inactive_sensitive_extensions,
            "unresolved_sensitive_extensions":unresolved_sensitive_extensions,
            "risk_flags":risk_flags,
        }

    def market_snapshot(self):
        if self.market_client is None:
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","reason":"MARKET_CLIENT_DISABLED"}
        try:return self.market_client.token_snapshot(self.mint)
        except Exception as exc:
            return {"status":"UNAVAILABLE","source":"DEXSCREENER_API","reason":type(exc).__name__}

    @staticmethod
    def _quote_quantity(record):
        raw=record.get("quote_amount_raw")
        decimals=record.get("quote_decimals")
        if raw in {None,""} or decimals is None:return None
        try:return str(Decimal(str(raw))/(Decimal(10)**int(decimals)))
        except (ValueError,TypeError,InvalidOperation):return None
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
        raw_top10=top[:10]
        self._raw_top10_snapshot_pct=(
            str((Decimal(sum(int(x["amount"]) for x in raw_top10))*100/Decimal(supply)).quantize(Decimal("0.01")))
            if supply>0 and raw_top10 and all(str(x.get("amount","")).isdigit() for x in raw_top10)
            else None
        )
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
    def _scan_holder(self,holder:Holder,account_to_owner,top_owners,history_limit=None):
        limit=int(history_limit or self.history_per_holder)
        try:rows=self.rpc.call("getSignaturesForAddress",[holder.token_account,{"commitment":"finalized","limit":limit}],ttl=300)
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
                record={"owner":holder.owner,"signature":sig,"block_time":bt,"direction":trade.get("direction"),"quote_asset":trade.get("quote_asset"),"quote_amount_raw":trade.get("quote_amount_raw"),"quote_decimals":trade.get("quote_decimals"),"token_amount_raw":trade.get("token_amount_raw"),"token_decimals":trade.get("token_decimals"),"program_ids":(c.get("evidence") or {}).get("program_ids") or [],"signers":_signers(tx)}
                if not any(x["owner"]==holder.owner and x["signature"]==sig for x in self.trades):self.trades.append(record)
                if trade.get("direction")=="BUY" and bt is not None and (first is None or bt < first["block_time"]):
                    first={
                        "block_time":int(bt),"signature":sig,"type":"MARKET_BUY",
                        "quote_asset":trade.get("quote_asset"),
                        "quote_amount_raw":trade.get("quote_amount_raw"),
                        "quote_decimals":trade.get("quote_decimals"),
                        "token_amount_raw":trade.get("token_amount_raw"),
                        "token_decimals":trade.get("token_decimals"),
                        "program_ids":(c.get("evidence") or {}).get("program_ids") or [],
                    }
        return first
    def _scan_funding(self,holder:Holder,first,top_owners,funding_limit=None):
        if not first:return
        limit=int(funding_limit or self.funding_lookback)
        options={"commitment":"finalized","limit":limit,"before":first["signature"]}
        try:rows=self.rpc.call("getSignaturesForAddress",[holder.owner,options],ttl=300)
        except Exception as exc:
            self.tx_errors.append({"address":holder.owner,"phase":"funding_signatures","error":type(exc).__name__})
            return
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
        # A single CEX payout transaction can serve independent users.
        # Require the SAME identified non-public funder, not just a tx signature.
        batches=defaultdict(list)
        for sig,rows in by_sig.items():
            for row in rows:batches[(sig,row["source"])].append(row)
        for (sig,source),rows in batches.items():
            owners=sorted({r["owner"] for r in rows})
            if len(owners)<2:continue
            role=(self._entry(source) or {}).get("role")
            if role=="CEX":kind="COMMON_FUNDER_CEX"
            elif role in {"PUBLIC_INFRA","PUBLIC_PROGRAM","ROUTER","BRIDGE","AMM_POOL","PROTOCOL_VAULT"}:kind="SHARED_INFRA"
            elif role in {"EOA","DEV","CREATOR","TREASURY"}:kind="BATCH_FUNDING"
            else:kind="COMMON_FUNDER_UNRESOLVED"
            for i,a in enumerate(owners):
                for b in owners[i+1:]:self._edge(a,b,kind,sig,funder=source,batch=True)
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
        token_profile=self.token_profile()
        market=self.market_snapshot()
        self._progress("BASE_READY",token_profile=token_profile,market=market)

        supply,decimals,holders=self.holders()
        preview_top10_pct=getattr(self,"_raw_top10_snapshot_pct",None)
        self._progress(
            "HOLDERS_READY",top_accounts_resolved=len(holders),
            supply_raw=str(supply),decimals=decimals,
            raw_top10_resolved_pct=preview_top10_pct,
            holder_snapshot_status="BOUNDED_RESOLVED_ONLY",
        )
        account_to_owner={h.token_account:h.owner for h in holders}
        firsts={};deep=[];deep_seen=set()
        for h in holders:
            if h.owner in deep_seen:continue
            deep_seen.add(h.owner);deep.append(h)
            if len(deep)>=self.deep_holders:break
        top_owners=set(account_to_owner.values())

        for idx,h in enumerate(deep,1):
            self._progress("OWNER_SCAN",scanned=idx-1,target=len(deep),owner=h.owner,mode="SHALLOW")
            firsts[h.owner]=self._scan_holder_bounded(h,account_to_owner,top_owners,self.history_per_holder)
            self._progress("OWNER_SCAN",scanned=idx,target=len(deep),owner=h.owner,mode="SHALLOW")
        for idx,h in enumerate(deep,1):
            self._progress("FUNDING_SCAN",scanned=idx-1,target=len(deep),owner=h.owner,mode="SHALLOW")
            self._scan_funding_bounded(h,firsts.get(h.owner),top_owners,self.funding_lookback)
        self._derive_pair_edges()

        adaptive_history=self.adaptive_history_per_holder or self.history_per_holder
        adaptive_funding=self.adaptive_funding_lookback or self.funding_lookback
        if adaptive_history>self.history_per_holder or adaptive_funding>self.funding_lookback:
            suspicious=set()
            for edge in self.edges:
                if edge.get("type") not in {"SHARED_INFRA","COMMON_FUNDER_CEX"}:
                    suspicious.update(x for x in (edge.get("a"),edge.get("b")) if x)
            # Static role/materiality is known for all resolved Top20 holders, not
            # only the shallow-scan prefix. A material DEV/unresolved owner outside
            # the first six must still be eligible for targeted deepening.
            owner_holder={}
            owner_balance=defaultdict(int)
            owner_roles=defaultdict(set)
            for h in holders:
                owner_holder.setdefault(h.owner,h)
                owner_balance[h.owner]+=h.raw
                owner_roles[h.owner].add(h.role)
            risky_roles=DEV_ROLES | {"UNRESOLVED","PROGRAM_OWNED_UNRESOLVED","TOKEN_ACCOUNT_OWNER_UNRESOLVED"}
            for owner,raw in owner_balance.items():
                pct=Decimal(raw)*100/Decimal(supply) if supply else Decimal(0)
                if pct>=self.material_pct and owner_roles[owner] & risky_roles:
                    suspicious.add(owner)
            # A relationship discovered from a shallow-scanned owner may point to
            # rank 7-20. Deepen that known Top20 counterpart too rather than
            # silently restricting adaptive work to the first-six prefix.
            targets=[owner_holder[owner] for owner in owner_holder if owner in suspicious]
            self.adaptive_deepened_owners=[h.owner for h in targets]
            if targets:
                self._progress("ADAPTIVE_DEEPEN",scanned=0,target=len(targets),owners=self.adaptive_deepened_owners)
                for idx,h in enumerate(targets,1):
                    firsts[h.owner]=self._scan_holder_bounded(h,account_to_owner,top_owners,adaptive_history) or firsts.get(h.owner)
                    self._scan_funding_bounded(h,firsts.get(h.owner),top_owners,adaptive_funding)
                    self._progress("ADAPTIVE_DEEPEN",scanned=idx,target=len(targets),owner=h.owner)
                self._derive_pair_edges()
        self._progress("FINALIZING",deep_holders_scanned=len(deep),adaptive_deepened=len(self.adaptive_deepened_owners))

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

        funding_by_owner={}
        for row in self.funding:
            current=funding_by_owner.get(row["owner"])
            if current is None or (row.get("block_time") or 0)>(current.get("block_time") or 0):
                funding_by_owner[row["owner"]]=row

        def acquisition(owner):
            row=firsts.get(owner)
            if not row or not isinstance(row,dict):
                return {"status":"UNRESOLVED","type":"UNRESOLVED"} if owner in deep_seen else {"status":"NOT_SCANNED","type":"NOT_SCANNED"}
            token_qty=None
            if row.get("token_amount_raw") not in {None,""} and row.get("token_decimals") is not None:
                try:token_qty=str(Decimal(str(row["token_amount_raw"]))/(Decimal(10)**int(row["token_decimals"])))
                except (ValueError,TypeError,InvalidOperation):token_qty=None
            return {
                "status":"CONFIRMED_BOUNDED",
                "type":row.get("type") or "MARKET_BUY",
                "block_time":row.get("block_time"),
                "signature":row.get("signature"),
                "quote_asset":row.get("quote_asset"),
                "quote_quantity":self._quote_quantity(row),
                "token_quantity":token_qty,
                "program_ids":row.get("program_ids") or [],
            }

        def funding_record(owner):
            row=funding_by_owner.get(owner)
            if not row:return None
            source=row.get("source");entry=self._entry(source) or {}
            try:sol=str(Decimal(str(row.get("lamports")))/Decimal(10**9))
            except (InvalidOperation,ValueError,TypeError):sol=None
            return {
                "source":source,"sol":sol,"signature":row.get("signature"),"block_time":row.get("block_time"),
                "source_role":entry.get("role") or "UNRESOLVED",
                "source_label":entry.get("label"),
            }

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
                    "first_target_acquisition":{x:acquisition(x) for x in sorted(g)},
                    "funding_evidence":[x for x in self.funding if x["owner"] in g],
                    "trade_evidence":[x for x in self.trades if x["owner"] in g],
                })
            return sorted(out,key=lambda x:int(x["combined_raw"]),reverse=True)

        relation_groups=group_records(relation.groups(),"REL","CONFIRMED_RELATION")
        control_groups=group_records(control.groups(),"CTRL","PROBABLE_CONTROL_CLUSTER")
        execution_groups=group_records(execution.groups(),"EXEC","PROBABLE_EXECUTION_CLUSTER")
        raw_top10=sum(h.raw for h in holders[:10])
        nonspecial=[h for h in holders if h.role not in SPECIAL_ROLES]
        ex_lp=[h for h in holders if h.role not in {"LP","AMM_POOL","PROTOCOL_VAULT"}]
        ex_special_top10=sum(h.raw for h in nonspecial[:10])
        ex_lp_top10=sum(h.raw for h in ex_lp[:10])
        dev_owners={h.owner for h in holders if h.role in DEV_ROLES}
        dev_linked_owners=set(dev_owners)
        for group in control.groups():
            if set(group) & dev_owners:dev_linked_owners.update(group)
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
        for g in control_groups+relation_groups:classified.update(g["wallets"])
        for h in nonspecial:
            pct=Decimal(h.raw)*100/Decimal(supply) if supply else Decimal(0)
            if pct>=self.material_pct and h.owner not in classified and h.role in {"ORDINARY","UNRESOLVED","PROGRAM_OWNED_UNRESOLVED","TOKEN_ACCOUNT_OWNER_UNRESOLVED"}:
                unresolved_raw+=h.raw

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

        holder_rows=[]
        for i,h in enumerate(holders):
            holder_rows.append({
                "rank":i+1,"token_account":h.token_account,"owner":h.owner,"raw":str(h.raw),
                "quantity":str(h.quantity),"supply_pct":self._pct(h.raw,supply),"role":h.role,
                "role_source":h.role_source,"account_program":h.account_program,
                "deep_scanned":h.owner in deep_seen,
                "first_acquisition":acquisition(h.owner),
                "funding":funding_record(h.owner),
            })

        if token_profile.get("status")=="OK":
            active_authorities=[
                name for name in ("mint_authority","freeze_authority")
                if token_profile.get(name) not in {None,""}
            ]
            sensitive_extensions=list(token_profile.get("sensitive_extensions") or [])
            active_extension_risks=list(token_profile.get("active_extension_risks") or [])
            unresolved_extension_risks=list(token_profile.get("unresolved_sensitive_extensions") or [])
            if active_authorities or active_extension_risks:chain_status="RISK"
            elif unresolved_extension_risks:chain_status="UNRESOLVED"
            else:chain_status="PASS"
        else:
            active_authorities=[];sensitive_extensions=[];active_extension_risks=[];unresolved_extension_risks=[];chain_status="UNRESOLVED"

        unresolved_pct=Decimal(str(metrics["UNRESOLVED_MATERIAL_HOLDER_PCT"] or "0"))
        if control_groups:
            cluster_status="PROBABLE_CONTROL_CLUSTER_PRESENT"
        elif (not normalization_complete or unresolved_pct>0 or
              any(edge.get("type") in {
                  "COMMON_FUNDER_UNRESOLVED","COMMON_SIGNER_UNRESOLVED",
                  "COMMON_CONSOLIDATION_UNRESOLVED"
              } for edge in self.edges)):
            cluster_status="WALLET_CLUSTER_UNRESOLVED"
        else:
            cluster_status="NO_MATERIAL_CONTROL_CLUSTER_FOUND"

        if chain_status=="RISK":
            trading_status="RISK / ACTIVE_CHAIN_PERMISSION"
        elif chain_status=="UNRESOLVED":
            trading_status="WATCH / CHAIN_PERMISSION_UNRESOLVED"
        elif control_groups:
            trading_status="WATCH / CONTROL_CLUSTER_RISK"
        elif cluster_status=="WALLET_CLUSTER_UNRESOLVED":
            trading_status="WATCH / WALLET_CLUSTER_UNRESOLVED"
        else:
            trading_status="WATCH / CHAIN_STRUCTURE_PASS"

        assessment={
            "chain_permission_status":chain_status,
            "active_authorities":active_authorities,
            "sensitive_extensions":sensitive_extensions,
            "active_extension_risks":active_extension_risks,
            "unresolved_extension_risks":unresolved_extension_risks,
            "cluster_status":cluster_status,
            "trading_status":trading_status,
            "narrative_status":"NOT_AUTOMATICALLY_VERIFIED",
            "next_checks":[
                "Verify whether the project/narrative owner explicitly recognizes this exact CA.",
                "Verify creator-fee claim, creator buy, lock or treasury relationship on-chain when relevant.",
                "Use live executable quote and current market structure before any entry; this report does not infer an ATH that was not observed.",
            ],
        }

        # Never persist credential-bearing RPC URLs in JSON, markdown, latest,
        # or API responses. Stable labels keep diagnostics without secret values.
        raw_endpoints=list(getattr(self.rpc,"endpoints",[getattr(self.rpc,"endpoint","UNKNOWN")]))
        endpoint_labels={value:("PRIMARY" if i==0 else f"FALLBACK_{i}")
                         for i,value in enumerate(raw_endpoints)}
        def safe_rpc_label(value):
            return endpoint_labels.get(value,"UNLISTED_RPC")
        endpoints=[safe_rpc_label(value) for value in raw_endpoints]
        endpoint_calls={safe_rpc_label(k):v for k,v in
                        (getattr(self.rpc,"endpoint_calls",{}) or {}).items()}
        endpoint_failures={safe_rpc_label(k):v for k,v in
                           (getattr(self.rpc,"endpoint_failures",{}) or {}).items()}
        return {
            "schema_version":2,"mint":self.mint,"source":"SOLANA_FINALIZED_JSON_RPC",
            "rpc_endpoint":safe_rpc_label(getattr(self.rpc,"endpoint","UNKNOWN")),"rpc_endpoints":endpoints,
            "observed_at":time.time(),"supply_raw":str(supply),"decimals":decimals,
            "token_profile":token_profile,"market":market,"assessment":assessment,"holders":holder_rows,
            "metrics":metrics,"confirmed_relation_groups":relation_groups,"probable_control_clusters":control_groups,
            "probable_execution_clusters":execution_groups,
            "shared_infrastructure_exclusions":[{k:v for k,v in e.items() if k!="_key"} for e in self.edges if e["type"] in {"COMMON_FUNDER_CEX","SHARED_INFRA"}],
            "unresolved_relation_edges":[{k:v for k,v in e.items() if k!="_key"} for e in self.edges if e["type"] in {"COMMON_FUNDER_UNRESOLVED","COMMON_SIGNER_UNRESOLVED","COMMON_CONSOLIDATION_UNRESOLVED"}],
            "edges":[{k:v for k,v in e.items() if k!="_key"} for e in self.edges],
            "funding_evidence":self.funding,"consolidation_evidence":self.consolidations,
            "trade_evidence":self.trades,"transaction_errors":self.tx_errors,
            "coverage":{
                "top_accounts_resolved":len(holders),"deep_holders_scanned":len(deep),
                "history_per_holder":self.history_per_holder,"funding_lookback":self.funding_lookback,
                "adaptive_history_per_holder":self.adaptive_history_per_holder,
                "adaptive_funding_lookback":self.adaptive_funding_lookback,
                "adaptive_deepened_owners":list(self.adaptive_deepened_owners),
                "scan_mode":"ADAPTIVE" if self.adaptive_history_per_holder or self.adaptive_funding_lookback else "FIXED",
                "material_pct":str(self.material_pct),"special_normalization_complete":normalization_complete,
                "rpc_calls":getattr(self.rpc,"calls",0),"rpc_cache_hits":getattr(self.rpc,"cache_hits",0),
                "rpc_endpoint_calls":endpoint_calls,"rpc_endpoint_failures":endpoint_failures,
            },
            "limitations":[
                "Raw finalized RPC is authoritative for chain ownership/transactions; DexScreener is secondary market data only.",
                "CEX/public-infrastructure identity is never guessed from funding alone.",
                "Program-owned holder accounts remain unresolved unless explicitly labelled.",
                "Bounded history can miss older funding, consolidation, and cross-token coordination.",
                "PROBABLE_EXECUTION_CLUSTER never implies common beneficial ownership.",
                "Narrative ownership, social endorsement and creator identity are not automatically inferred from token name or social links.",
            ],
        }


def load_registry(path:Path|None):
    if path is None:return {"schema_version":1,"addresses":{}}
    data=json.loads(Path(path).read_text())
    if data.get("schema_version")!=1 or not isinstance(data.get("addresses"),dict) or not isinstance(data.get("tokens",{}),dict):raise ValueError("SPECIAL_REGISTRY_SCHEMA")
    return data


def markdown(report:dict)->str:
    m=report.get("metrics") or {}
    profile=report.get("token_profile") or {}
    market=report.get("market") or {}
    assessment=report.get("assessment") or {}
    quote=report.get("execution_quote_30_usdc") or {}
    pair=market.get("main_pair") or {}
    lines=[
        f"# Meme CA Research — {report.get('mint')}",
        "",
        f"Observed at: {report.get('observed_at')}",
        f"Schema: {report.get('schema_version')}",
        "",
        "## Conclusion",
        "",
        f"- Trading status: {assessment.get('trading_status','UNRESOLVED')}",
        f"- Chain permission: {assessment.get('chain_permission_status','UNRESOLVED')}",
        f"- Wallet cluster: {assessment.get('cluster_status','UNRESOLVED')}",
        f"- Narrative: {assessment.get('narrative_status','UNRESOLVED')}",
        "",
        "## Conclusion history",
        "",
    ]
    history=report.get("assessment_history") or []
    if history:
        for row in history[-10:]:
            lines.append(
                f"- {row.get('observed_at')} [{row.get('preset','unknown')}] "
                f"{row.get('structure_rating','UNRESOLVED')} / {row.get('investment_rating','UNRESOLVED')} "
                f"— {row.get('reason','')}"
            )
    else:
        lines.append("- No material conclusion change recorded yet.")
    lines += [
        "",
        "## Token / contract",
        "",
        f"- Name / Symbol: {market.get('name') or 'UNAVAILABLE'} / {market.get('symbol') or 'UNAVAILABLE'}",
        f"- Token program: {profile.get('token_program','UNAVAILABLE')}",
        f"- Supply raw: {report.get('supply_raw')}",
        f"- Decimals: {report.get('decimals')}",
        f"- Mint authority: {profile.get('mint_authority')}",
        f"- Freeze authority: {profile.get('freeze_authority')}",
        f"- Metadata update authority: {profile.get('metadata_update_authority','UNAVAILABLE')}",
        f"- Active Token-2022 extension risks: {json.dumps(profile.get('active_extension_risks') or [],ensure_ascii=False,sort_keys=True)}",
        f"- Inactive sensitive extensions: {json.dumps(profile.get('inactive_sensitive_extensions') or [],ensure_ascii=False,sort_keys=True)}",
        f"- Unresolved sensitive extensions: {json.dumps(profile.get('unresolved_sensitive_extensions') or [],ensure_ascii=False,sort_keys=True)}",
        "",
        "## Current market",
        "",
        f"- Market source status: {market.get('status','UNAVAILABLE')} / {market.get('source','UNAVAILABLE')}",
        f"- Price USD: {market.get('price_usd','UNAVAILABLE')}",
        f"- Market cap USD: {market.get('market_cap_usd','UNAVAILABLE')}",
        f"- Main DEX: {pair.get('dex_id','UNAVAILABLE')}",
        f"- Main pair: {pair.get('pair_address','UNAVAILABLE')}",
        f"- Main-pair liquidity USD: {pair.get('liquidity_usd','UNAVAILABLE')}",
        f"- 24h volume USD: {(pair.get('volume') or {}).get('h24','UNAVAILABLE')}",
        f"- Jupiter $30 quote: {quote.get('status','UNAVAILABLE')} / price={quote.get('execution_price_usdc','UNAVAILABLE')} / impact={quote.get('price_impact_pct','UNAVAILABLE')}%",
        "",
        "## Concentration",
        "",
    ]
    for k,v in m.items():
        suffix="%" if v not in {"UNRESOLVED","UNAVAILABLE",None} else ""
        lines.append(f"- {k}: {v}{suffix}")
    lines += [
        "",
        "## Top holders",
        "",
        "|#|Owner|Share|Role|First acquisition|Funding source|",
        "|---:|---|---:|---|---|---|",
    ]
    for h in report.get("holders") or []:
        a=h.get("first_acquisition") or {}
        first=(
            f"{a.get('type')} {a.get('quote_quantity') or ''} {a.get('quote_asset') or ''} "
            f"@ {a.get('block_time') or ''}"
        ).strip() if a.get("status")=="CONFIRMED_BOUNDED" else a.get("status","UNRESOLVED")
        funding=h.get("funding") or {}
        funder=f"{funding.get('source') or 'UNRESOLVED'} {funding.get('sol') or ''} SOL".strip()
        lines.append(
            f"|{h.get('rank')}|{h.get('owner')}|{h.get('supply_pct')}%|{h.get('role')}|{first}|{funder}|"
        )
    for title,key in [
        ("Confirmed relations","confirmed_relation_groups"),
        ("Probable control","probable_control_clusters"),
        ("Probable execution","probable_execution_clusters"),
    ]:
        lines += ["",f"## {title}"]
        rows=report.get(key) or []
        if not rows:lines.append("- None confirmed in bounded evidence.")
        for g in rows:
            edge_types=sorted({x.get("type") for x in (g.get("evidence") or []) if x.get("type")})
            lines.append(
                f"- {g.get('cluster_id')}: {g.get('supply_pct')}% — "
                + ", ".join(g.get("wallets") or [])
                + (" — evidence: "+", ".join(edge_types) if edge_types else "")
            )
    lines += [
        "",
        "## Coverage",
        "",
        "~~~json",
        json.dumps(report.get("coverage") or {},ensure_ascii=False,indent=2),
        "~~~",
        "",
        "## Next checks",
    ]
    lines += [f"- {x}" for x in assessment.get("next_checks") or []]
    lines += ["","## Limitations"]
    lines += [f"- {x}" for x in report.get("limitations") or []]
    return "\n".join(lines)+"\n"
