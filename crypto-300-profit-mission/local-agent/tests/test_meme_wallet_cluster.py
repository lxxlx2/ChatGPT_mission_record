from decimal import Decimal

from mission_agent.frank.parser import DEX_PROGRAMS
from mission_agent.meme.cluster import Holder, RpcCache, WalletClusterAnalyzer


class DummyRPC:
    endpoint="test"
    calls=0
    cache_hits=0


def holders():
    return [
        Holder("ta1","A",200,0,"ORDINARY","test"),
        Holder("ta2","B",150,0,"ORDINARY","test"),
        Holder("ta3","C",100,0,"LP","test"),
        Holder("ta4","D",80,0,"ORDINARY","test"),
    ]


def analyzer():
    a=WalletClusterAnalyzer("Mint",rpc=DummyRPC(),deep_holders=4,material_pct=Decimal("1"))
    a.holders=lambda:(1000,0,holders())
    a.token_profile=lambda:{
        "status":"OK","mint_authority":None,"freeze_authority":None,
        "metadata_update_authority":"UNAVAILABLE","metadata_update_authority_status":"UNAVAILABLE",
        "token_program":"SPL Token",
    }
    a.market_snapshot=lambda:{"status":"UNAVAILABLE","source":"DEXSCREENER_API","reason":"FIXTURE_DISABLED"}
    a._scan_funding=lambda *a,**k:None
    return a


def test_direct_transfer_is_relation_not_control():
    a=analyzer()
    def scan(h,mapping,top_owners):
        if h.owner=="A":a._edge("A","B","DIRECT_TOKEN_TRANSFER","tx1")
        return {"block_time":100,"signature":"first-"+h.owner}
    a._scan_holder=scan
    out=a.analyze()
    assert out["confirmed_relation_groups"][0]["supply_pct"]=="35.0000"
    assert out["probable_control_clusters"]==[]


def test_common_funder_plus_sync_can_form_probable_control_cluster():
    a=analyzer();a.registry={"normalization_complete":False,"addresses":{"F":{"role":"EOA","source":"fixture"}}}
    def scan(h,mapping,top_owners):
        if h.owner=="A":
            a.funding.append({"owner":"A","source":"F","lamports":"1","signature":"fa","block_time":90})
            a.trades.append({"owner":"A","signature":"a1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["A"]})
        if h.owner=="B":
            a.funding.append({"owner":"B","source":"F","lamports":"1","signature":"fb","block_time":90})
            a.trades.append({"owner":"B","signature":"b1","block_time":101,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["B"]})
        return {"block_time":100,"signature":"first-"+h.owner}
    a._scan_holder=scan
    out=a.analyze()
    assert out["probable_control_clusters"]
    assert set(out["probable_control_clusters"][0]["wallets"])=={"A","B"}
    types={e["type"] for e in out["probable_control_clusters"][0]["evidence"]}
    assert "COMMON_FUNDER_EOA" in types
    assert "SYNC_BUY" in types


def test_special_lp_is_excluded_but_raw_top10_keeps_it():
    a=analyzer();a.registry={"normalization_complete":True,"addresses":{}};a._scan_holder=lambda *args:100
    out=a.analyze()
    assert out["metrics"]["RAW_TOP10_PCT"]=="53.0000"
    assert out["metrics"]["EX_LP_TOP10_PCT"]=="43.0000"
    assert out["metrics"]["EX_SPECIAL_TOP10_PCT"]=="43.0000"


def test_execution_cluster_does_not_become_control_without_strong_evidence():
    a=analyzer()
    def scan(h,mapping,top_owners):
        if h.owner=="A":
            a.trades.append({"owner":"A","signature":"a1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["A"]})
        if h.owner=="B":
            a.trades.append({"owner":"B","signature":"b1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["B"]})
        return {"block_time":100,"signature":"first-"+h.owner}
    a._scan_holder=scan
    out=a.analyze()
    assert out["probable_execution_clusters"]
    assert out["probable_control_clusters"]==[]


def test_strict_special_metrics_are_unresolved_until_normalization_is_declared_complete():
    a=analyzer();a._scan_holder=lambda *args:100
    out=a.analyze()
    assert out["metrics"]["EX_SPECIAL_TOP10_PCT"]=="UNRESOLVED"
    assert out["metrics"]["DEV_LINKED_CLUSTER_PCT"]=="UNRESOLVED"
    assert out["metrics"]["KNOWN_EX_SPECIAL_TOP10_PCT"]=="43.0000"


def test_unknown_common_funder_is_not_promoted_to_probable_control():
    a=analyzer()
    def scan(h,mapping,top_owners):
        if h.owner in {"A","B"}:
            a.funding.append({"owner":h.owner,"source":"UNKNOWN","lamports":"1","signature":"f-"+h.owner,"block_time":90})
            a.trades.append({"owner":h.owner,"signature":"t-"+h.owner,"block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":[h.owner]})
        return {"block_time":100,"signature":"first-"+h.owner}
    a._scan_holder=scan
    out=a.analyze()
    assert out["probable_control_clusters"]==[]
    assert "COMMON_FUNDER_UNRESOLVED" in {e["type"] for e in out["edges"]}


def test_rpc_cache_rejects_tampered_body(tmp_path):
    cache=RpcCache(tmp_path/"cache.sqlite")
    cache.put("getTokenSupply",["M"],{"value":{"amount":"100"}},60,100)
    assert cache.get("getTokenSupply",["M"],101)=={"value":{"amount":"100"}}
    cache.db.execute("update rpc_cache set body='{}'")
    cache.db.commit()
    assert cache.get("getTokenSupply",["M"],101) is None
    cache.close()


def test_public_dex_program_is_shared_infrastructure_not_execution_evidence():
    a=analyzer()
    jupiter=next(iter(DEX_PROGRAMS))
    def scan(h,mapping,top_owners):
        if h.owner=="A":
            a.trades.append({"owner":"A","signature":"a1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":[jupiter],"signers":["A"]})
        if h.owner=="B":
            a.trades.append({"owner":"B","signature":"b1","block_time":101,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"200","quote_decimals":9,"program_ids":[jupiter],"signers":["B"]})
        return {"block_time":100,"signature":"first-"+h.owner}
    a._scan_holder=scan
    out=a.analyze()
    assert out["probable_execution_clusters"]==[]
    edge_types={e["type"] for e in out["edges"]}
    assert "SAME_EXECUTION_PROGRAM" not in edge_types
    assert "SHARED_INFRA" in edge_types
    assert out["metrics"]["UNRESOLVED_MATERIAL_HOLDER_PCT"]=="43.0000"


def test_funding_scan_skips_public_rpc_null_transaction_instead_of_failing():
    class NullTxRPC:
        endpoint="test";calls=0;cache_hits=0
        def call(self,method,params,ttl=0):
            if method=="getSignaturesForAddress":
                return [{"signature":"missing"}]
            if method=="getTransaction":
                return None
            raise AssertionError(method)
    a=WalletClusterAnalyzer("Mint",rpc=NullTxRPC())
    h=Holder("ta","A",100,0,"ORDINARY","test")
    a._scan_funding(h,{"block_time":100,"signature":"first"},{"A","B"})
    assert a.funding==[]
    assert a.tx_errors==[{"signature":"missing","phase":"funding","error":"UNAVAILABLE_ON_PUBLIC_RPC"}]


def test_dev_linked_cluster_includes_probable_control_wallets():
    a=analyzer()
    a.registry={"normalization_complete":True,"addresses":{"F":{"role":"EOA","source":"fixture"}}}
    a.holders=lambda:(1000,0,[
        Holder("ta1","A",200,0,"DEV","fixture"),
        Holder("ta2","B",150,0,"ORDINARY","fixture"),
        Holder("ta3","C",100,0,"LP","fixture"),
        Holder("ta4","D",80,0,"ORDINARY","fixture"),
    ])
    def scan(h,mapping,top_owners):
        if h.owner=="A":
            a.funding.append({"owner":"A","source":"F","lamports":"1","signature":"fa","block_time":90})
            a.trades.append({"owner":"A","signature":"a1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":[],"signers":["A"]})
        if h.owner=="B":
            a.funding.append({"owner":"B","source":"F","lamports":"1","signature":"fb","block_time":90})
            a.trades.append({"owner":"B","signature":"b1","block_time":101,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"200","quote_decimals":9,"program_ids":[],"signers":["B"]})
        return {"block_time":100,"signature":"first-"+h.owner}
    a._scan_holder=scan
    out=a.analyze()
    assert set(out["probable_control_clusters"][0]["wallets"])=={"A","B"}
    assert out["metrics"]["DEV_LINKED_CLUSTER_PCT"]=="35.0000"


def test_full_report_exposes_bounded_holder_acquisition_and_conservative_conclusion():
    a=analyzer()
    a.token_profile=lambda:{
        "status":"OK","mint_authority":None,"freeze_authority":None,
        "metadata_update_authority":"UNAVAILABLE","metadata_update_authority_status":"UNAVAILABLE",
        "token_program":"SPL Token",
    }
    a.market_snapshot=lambda:{
        "status":"OK","source":"DEXSCREENER_API","price_usd":"0.001","market_cap_usd":"1000000",
        "main_pair":{"liquidity_usd":"100000","volume":{"h24":"2000000"}},
    }
    def scan(h,mapping,top_owners):
        if h.owner=="A":
            a.trades.append({
                "owner":"A","signature":"buy-a","block_time":100,"direction":"BUY",
                "quote_asset":"SOL","quote_amount_raw":"12000000000","quote_decimals":9,
                "token_amount_raw":"1000000","token_decimals":0,"program_ids":[],"signers":["A"],
            })
            return {
                "block_time":100,"signature":"buy-a","type":"MARKET_BUY",
                "quote_asset":"SOL","quote_amount_raw":"12000000000","quote_decimals":9,
                "token_amount_raw":"1000000","token_decimals":0,"program_ids":[],
            }
        return None
    a._scan_holder=scan
    out=a.analyze()
    assert out["schema_version"]==2
    assert out["holders"][0]["first_acquisition"]["type"]=="MARKET_BUY"
    assert out["holders"][0]["first_acquisition"]["quote_quantity"]=="12"
    assert out["assessment"]["chain_permission_status"]=="PASS"
    assert out["assessment"]["cluster_status"]=="WALLET_CLUSTER_UNRESOLVED"
    assert out["assessment"]["trading_status"]=="WATCH / WALLET_CLUSTER_UNRESOLVED"


def token2022_profile(extension):
    class RPC:
        endpoint="test";calls=0;cache_hits=0
        def call(self,*args,**kwargs):
            return {"value":{
                "owner":"TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
                "data":{"parsed":{"info":{
                    "mintAuthority":None,"freezeAuthority":None,"decimals":6,
                    "supply":"1000000","isInitialized":True,"extensions":[extension],
                }}},
            }}
    return WalletClusterAnalyzer("Mint",rpc=RPC(),deep_holders=1).token_profile()


def test_token2022_zero_transfer_fee_with_revoked_authorities_is_inactive_not_risk():
    profile=token2022_profile({
        "extension":"transferFeeConfig",
        "state":{
            "transferFeeConfigAuthority":None,
            "withdrawWithheldAuthority":None,
            "olderTransferFee":{"transferFeeBasisPoints":0,"maximumFee":0},
            "newerTransferFee":{"transferFeeBasisPoints":0,"maximumFee":0},
        },
    })
    assert profile["sensitive_extension_details"][0]["status"]=="INACTIVE"
    assert profile["active_extension_risks"]==[]
    assert profile["risk_flags"]==[]
    a=analyzer();a.token_profile=lambda:profile
    out=a.analyze()
    assert out["assessment"]["chain_permission_status"]=="PASS"


def test_token2022_nonzero_transfer_fee_is_active_risk_even_when_authority_revoked():
    profile=token2022_profile({
        "extension":"transferFeeConfig",
        "state":{
            "transferFeeConfigAuthority":None,
            "withdrawWithheldAuthority":None,
            "olderTransferFee":{"transferFeeBasisPoints":25,"maximumFee":100},
            "newerTransferFee":{"transferFeeBasisPoints":25,"maximumFee":100},
        },
    })
    detail=profile["sensitive_extension_details"][0]
    assert detail["status"]=="ACTIVE_RISK"
    assert "TRANSFER_FEE_ACTIVE_OR_MUTABLE"==detail["reason"]
    assert profile["active_extension_risks"]


def test_token2022_disabled_hook_and_active_delegate_are_distinguished():
    hook=token2022_profile({
        "extension":"transferHook","state":{"authority":None,"programId":None}
    })
    assert hook["sensitive_extension_details"][0]["status"]=="INACTIVE"
    delegate=token2022_profile({
        "extension":"permanentDelegate","state":{"delegate":"Delegate1111111111111111111111111111111"}
    })
    assert delegate["sensitive_extension_details"][0]["status"]=="ACTIVE_RISK"


def test_token2022_transfer_fee_missing_required_fields_stays_unresolved():
    profile=token2022_profile({
        "extension":"transferFeeConfig",
        "state":{"transferFeeConfigAuthority":None},
    })
    detail=profile["sensitive_extension_details"][0]
    assert detail["status"]=="UNRESOLVED"
    assert detail["reason"]=="TRANSFER_FEE_CONFIG_INCOMPLETE"
    a=analyzer();a.token_profile=lambda:profile
    out=a.analyze()
    assert out["assessment"]["chain_permission_status"]=="UNRESOLVED"


def test_token2022_single_older_schedule_with_duplicate_aliases_is_not_complete():
    profile=token2022_profile({
        "extension":"transferFeeConfig",
        "state":{
            "transferFeeConfigAuthority":None,
            "withdrawWithheldAuthority":None,
            "olderTransferFee":{
                "transferFeeBasisPoints":0,
                "basisPoints":0,
                "maximumFee":0,
                "maxFee":0,
            },
        },
    })
    detail=profile["sensitive_extension_details"][0]
    assert detail["status"]=="UNRESOLVED"
    assert detail["reason"]=="TRANSFER_FEE_CONFIG_INCOMPLETE"
    a=analyzer();a.token_profile=lambda:profile
    assert a.analyze()["assessment"]["chain_permission_status"]=="UNRESOLVED"


def test_token2022_transfer_fee_invalid_numeric_fields_stay_unresolved():
    profile=token2022_profile({
        "extension":"transferFeeConfig",
        "state":{
            "transferFeeConfigAuthority":None,
            "withdrawWithheldAuthority":None,
            "olderTransferFee":{"transferFeeBasisPoints":"invalid","maximumFee":"invalid"},
            "newerTransferFee":{"transferFeeBasisPoints":"invalid","maximumFee":"invalid"},
        },
    })
    detail=profile["sensitive_extension_details"][0]
    assert detail["status"]=="UNRESOLVED"
    assert detail["reason"]=="TRANSFER_FEE_CONFIG_INVALID"
    a=analyzer();a.token_profile=lambda:profile
    assert a.analyze()["assessment"]["chain_permission_status"]=="UNRESOLVED"


def test_token2022_transfer_hook_missing_program_id_stays_unresolved():
    profile=token2022_profile({
        "extension":"transferHook",
        "state":{"authority":None},
    })
    detail=profile["sensitive_extension_details"][0]
    assert detail["status"]=="UNRESOLVED"
    assert detail["reason"]=="TRANSFER_HOOK_CONFIG_INCOMPLETE"
    a=analyzer();a.token_profile=lambda:profile
    assert a.analyze()["assessment"]["chain_permission_status"]=="UNRESOLVED"


def test_token2022_sensitive_but_unresolved_config_is_not_upgraded_to_active_risk():
    profile=token2022_profile({
        "extension":"confidentialTransferMint",
        "state":{"autoApproveNewAccounts":False},
    })
    detail=profile["sensitive_extension_details"][0]
    assert detail["status"]=="UNRESOLVED"
    assert profile["active_extension_risks"]==[]
    a=analyzer();a.token_profile=lambda:profile
    out=a.analyze()
    assert out["assessment"]["chain_permission_status"]=="UNRESOLVED"
    assert out["assessment"]["trading_status"]=="WATCH / CHAIN_PERMISSION_UNRESOLVED"


def test_adaptive_scan_deepens_suspicious_counterpart_beyond_initial_prefix():
    a=analyzer()
    a.deep_holders=2
    a.history_per_holder=12
    a.funding_lookback=8
    a.adaptive_history_per_holder=30
    a.adaptive_funding_lookback=12
    calls=[]
    progress=[]
    a.progress_callback=lambda stage,details:progress.append((stage,dict(details)))
    def scan(h,mapping,top_owners,history_limit=None):
        calls.append((h.owner,history_limit))
        if h.owner=="A" and history_limit==12:
            a._edge("A","D","DIRECT_TOKEN_TRANSFER","tx-adaptive")
        return {"block_time":100,"signature":"first-"+h.owner}
    a._scan_holder=scan
    a._scan_funding=lambda *args,**kwargs:None
    out=a.analyze()
    assert ("A",12) in calls and ("B",12) in calls
    assert ("A",30) in calls
    assert ("D",30) in calls
    assert ("B",30) not in calls
    assert out["coverage"]["scan_mode"]=="ADAPTIVE"
    assert out["coverage"]["adaptive_deepened_owners"]==["A","D"]
    stages=[x[0] for x in progress]
    assert "BASE_READY" in stages
    assert "HOLDERS_READY" in stages
    assert "ADAPTIVE_DEEPEN" in stages
    assert "FINALIZING" in stages

def test_adaptive_scan_deepens_material_unresolved_owner_outside_initial_prefix():
    rows=[
        Holder("ta1","A",200,0,"ORDINARY","test"),
        Holder("ta2","B",150,0,"ORDINARY","test"),
        Holder("ta3","C",100,0,"ORDINARY","test"),
        Holder("ta4","D",80,0,"ORDINARY","test"),
        Holder("ta5","E",70,0,"ORDINARY","test"),
        Holder("ta6","F",60,0,"ORDINARY","test"),
        Holder("ta7","G",50,0,"UNRESOLVED","test"),
    ]
    a=analyzer()
    a.holders=lambda:(1000,0,rows)
    a.deep_holders=2
    a.history_per_holder=12
    a.funding_lookback=8
    a.adaptive_history_per_holder=30
    a.adaptive_funding_lookback=12
    calls=[]
    a._scan_holder=lambda h,m,t,history_limit=None:(calls.append((h.owner,history_limit)) or {"block_time":100,"signature":"first-"+h.owner})
    a._scan_funding=lambda *args,**kwargs:None
    out=a.analyze()
    assert ("G",12) not in calls
    assert ("G",30) in calls
    assert "G" in out["coverage"]["adaptive_deepened_owners"]

