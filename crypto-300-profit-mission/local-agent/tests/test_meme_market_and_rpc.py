import io
import json
import urllib.error
from email.message import Message

from mission_agent.meme.cluster import SolanaReadOnlyRPC, WalletClusterAnalyzer
from mission_agent.meme.market import DexScreenerMarketClient


class Response:
    def __init__(self,value):
        self.value=value
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self):
        return json.dumps(self.value).encode()


def test_dexscreener_selects_highest_liquidity_base_pair():
    mint="Mint111"
    payload=[
        {
            "chainId":"solana","dexId":"small","pairAddress":"P1",
            "baseToken":{"address":mint,"name":"Coin","symbol":"COIN"},
            "quoteToken":{"address":"Q","symbol":"SOL"},
            "priceUsd":"0.1","marketCap":100000,"fdv":120000,
            "liquidity":{"usd":1000,"base":1,"quote":1},
            "volume":{"h24":5000},"txns":{"h24":{"buys":2,"sells":1}},
            "priceChange":{"h24":10},
        },
        {
            "chainId":"solana","dexId":"main","pairAddress":"P2",
            "baseToken":{"address":mint,"name":"Coin","symbol":"COIN"},
            "quoteToken":{"address":"Q","symbol":"SOL"},
            "priceUsd":"0.2","marketCap":200000,"fdv":220000,
            "liquidity":{"usd":9000,"base":2,"quote":2},
            "volume":{"h24":15000},"txns":{"h24":{"buys":20,"sells":10}},
            "priceChange":{"h24":20},
            "info":{"websites":[{"url":"https://example.test"}],"socials":[{"platform":"twitter","handle":"coin"}]},
        },
        {
            "chainId":"solana","dexId":"wrong","pairAddress":"P3",
            "baseToken":{"address":"OTHER","name":"Other","symbol":"O"},
            "quoteToken":{"address":mint,"symbol":"COIN"},
            "liquidity":{"usd":999999},
        },
    ]
    client=DexScreenerMarketClient(open_url=lambda *a,**k:Response(payload))
    out=client.token_snapshot(mint)
    assert out["status"]=="OK"
    assert out["main_pair"]["pair_address"]=="P2"
    assert out["market_cap_usd"]=="200000"
    assert out["aggregate_liquidity_usd"]=="10000"
    assert out["socials"][0]["handle"]=="coin"


def test_rpc_rotates_after_429():
    calls=[]
    headers=Message();headers["Retry-After"]="0"
    def open_url(request,timeout=20):
        calls.append(request.full_url)
        if "primary.test" in request.full_url:
            raise urllib.error.HTTPError(request.full_url,429,"rate",headers,io.BytesIO(b""))
        return Response({"jsonrpc":"2.0","id":1,"result":{"value":{"amount":"100","decimals":0}}})
    rpc=SolanaReadOnlyRPC(
        "https://primary.test",
        fallback_endpoints=["https://fallback.test"],
        open_url=open_url,
        sleep=lambda *_:None,
        min_interval=0,
    )
    result=rpc.call("getTokenSupply",["Mint",{"commitment":"finalized"}])
    assert result["value"]["amount"]=="100"
    assert calls[:2]==["https://primary.test","https://fallback.test"]
    assert rpc.endpoint_failures["https://primary.test"]==1
    assert rpc.endpoint_calls["https://fallback.test"]==1


def test_token_profile_reads_chain_authorities_without_market_guessing():
    class RPC:
        endpoint="test";calls=0;cache_hits=0
        def call(self,method,params,ttl=0):
            assert method=="getAccountInfo"
            return {"value":{
                "owner":"TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
                "data":{"parsed":{"info":{
                    "mintAuthority":None,"freezeAuthority":None,"decimals":6,"supply":"946242000000000",
                    "extensions":[{"extension":"tokenMetadata","state":{"updateAuthority":None}}],
                }}}
            }}
    a=WalletClusterAnalyzer("Mint",rpc=RPC())
    out=a.token_profile()
    assert out["status"]=="OK"
    assert out["token_program"]=="SPL Token-2022"
    assert out["mint_authority"] is None
    assert out["freeze_authority"] is None
    assert out["metadata_update_authority"] is None
    assert out["metadata_update_authority_status"]=="CHAIN_PARSED"
    assert out["sensitive_extensions"]==[]
    assert out["risk_flags"]==[]


def test_null_get_transaction_is_not_cached(tmp_path):
    from mission_agent.meme.cluster import RpcCache
    cache=RpcCache(tmp_path/"rpc.sqlite")
    calls=[]
    def open_url(request,timeout=20):
        calls.append(request.full_url)
        return Response({"jsonrpc":"2.0","id":1,"result":None})
    rpc=SolanaReadOnlyRPC(
        "https://one.test",
        fallback_endpoints=["https://two.test"],
        open_url=open_url,
        sleep=lambda *_:None,
        min_interval=0,
        cache=cache,
    )
    assert rpc.call("getTransaction",["sig",{"encoding":"jsonParsed"}],ttl=999) is None
    before=len(calls)
    assert rpc.call("getTransaction",["sig",{"encoding":"jsonParsed"}],ttl=999) is None
    assert len(calls)>before
    cache.close()


def test_rpc_keeps_primary_for_healthy_requests():
    calls=[]
    def open_url(request,timeout=20):
        calls.append(request.full_url)
        return Response({"jsonrpc":"2.0","id":1,"result":{"value":{"amount":"100","decimals":0}}})
    rpc=SolanaReadOnlyRPC(
        "https://primary.test",
        fallback_endpoints=["https://fallback.test"],
        open_url=open_url,
        sleep=lambda *_:None,
        min_interval=0,
    )
    rpc.call("getTokenSupply",["MintA",{"commitment":"finalized"}])
    rpc.call("getTokenSupply",["MintB",{"commitment":"finalized"}])
    assert calls==["https://primary.test","https://primary.test"]


def test_token_2022_sensitive_extensions_are_explicit_risk_flags():
    class RPC:
        endpoint="test";calls=0;cache_hits=0
        def call(self,method,params,ttl=0):
            assert method=="getAccountInfo"
            return {"value":{
                "owner":"TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
                "data":{"parsed":{"info":{
                    "mintAuthority":None,"freezeAuthority":None,"decimals":6,"supply":"1000000",
                    "extensions":[
                        {"extension":"transferFeeConfig"},
                        {"extension":"tokenMetadata","state":{"updateAuthority":None}},
                    ],
                }}}
            }}
    out=WalletClusterAnalyzer("Mint",rpc=RPC()).token_profile()
    assert out["sensitive_extensions"]==["transferFeeConfig"]
    assert "SENSITIVE_EXTENSION:transferFeeConfig" in out["risk_flags"]
