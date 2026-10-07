import io
import json

from mission_agent.meme.token_report import DexScreenerClient, automated_assessment, inspect_mint


class RPC:
    endpoint="test";calls=1;cache_hits=0
    def call(self,method,params,ttl=0):
        assert method=="getAccountInfo"
        return {"value":{
            "owner":"TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
            "data":{"parsed":{"type":"mint","info":{
                "decimals":6,"supply":"946242000000000","isInitialized":True,
                "mintAuthority":None,"freezeAuthority":None,
                "extensions":[{"extension":"tokenMetadata","state":{"updateAuthority":None,"name":"Claudia","symbol":"CLAUDIA"}}],
            }}}
        }}


class Response:
    def __init__(self,body):
        self.body=json.dumps(body).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return self.body


def test_inspect_token2022_mint_authorities_and_supply():
    out=inspect_mint(RPC(),"Mint")
    assert out["status"]=="OK"
    assert out["token_standard"]=="SPL Token-2022"
    assert out["mint_authority"] is None
    assert out["freeze_authority"] is None
    assert out["supply_quantity"]=="946242000"
    assert out["metadata_update_authority"] is None
    assert out["metadata_update_authority_status"]=="VERIFIED"
    assert out["risk_flags"]==[]


def test_dexscreener_chooses_highest_liquidity_base_pair():
    body=[
        {"chainId":"solana","dexId":"x","pairAddress":"P1","baseToken":{"address":"M","name":"M","symbol":"M"},"quoteToken":{"address":"S","symbol":"SOL"},"priceUsd":"1","liquidity":{"usd":100},"marketCap":1000,"volume":{"h24":500},"txns":{"h24":{"buys":1,"sells":2}}},
        {"chainId":"solana","dexId":"pumpswap","pairAddress":"P2","baseToken":{"address":"M","name":"Meme","symbol":"MEME"},"quoteToken":{"address":"S","symbol":"SOL"},"priceUsd":"2","liquidity":{"usd":10000},"marketCap":200000,"volume":{"h24":90000},"txns":{"h24":{"buys":10,"sells":9}}},
        {"chainId":"solana","dexId":"x","pairAddress":"WRONG","baseToken":{"address":"OTHER"},"quoteToken":{"address":"M"},"priceUsd":"99","liquidity":{"usd":999999}},
    ]
    client=DexScreenerClient(open_url=lambda *a,**k:Response(body))
    out=client.token_market("M")
    assert out["status"]=="OK"
    assert out["pair_address"]=="P2"
    assert out["price_usd"]=="2"
    assert out["liquidity_usd"]==10000
    assert out["pair_count"]==2


def test_automated_assessment_preserves_external_relation_uncertainty():
    report={
        "token_security":{"status":"OK","mint_authority":None,"freeze_authority":None,"risk_flags":[],"sensitive_extensions":[]},
        "market":{"status":"OK","liquidity_usd":50000,"volume":{"h24":100000}},
        "metrics":{"KNOWN_EX_LP_TOP10_PCT":"17","LARGEST_PROBABLE_CONTROL_CLUSTER_PCT":"0","UNRESOLVED_MATERIAL_HOLDER_PCT":"8"},
        "coverage":{"special_normalization_complete":False},
    }
    out=automated_assessment(report)
    assert out["label"]=="WATCH / NEED_EXTERNAL_VERIFICATION"
    assert "Mint Authority 已撤销" in out["positives"]
    assert any("项目方/名人" in x for x in out["uncertainties"])
