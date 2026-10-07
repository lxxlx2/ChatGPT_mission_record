from decimal import Decimal

from mission_agent.meme.cluster import Holder, WalletClusterAnalyzer


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
    a._scan_funding=lambda *a,**k:None
    return a


def test_direct_transfer_is_relation_not_control():
    a=analyzer()
    def scan(h,mapping):
        if h.owner=="A":a._edge("A","B","DIRECT_TOKEN_TRANSFER","tx1")
        return 100
    a._scan_holder=scan
    out=a.analyze()
    assert out["confirmed_relation_groups"][0]["supply_pct"]=="35.0000"
    assert out["probable_control_clusters"]==[]


def test_common_funder_plus_sync_can_form_probable_control_cluster():
    a=analyzer();a.registry={"normalization_complete":False,"addresses":{"F":{"role":"EOA","source":"fixture"}}}
    def scan(h,mapping):
        if h.owner=="A":
            a.funding.append({"owner":"A","source":"F","lamports":"1","signature":"fa","block_time":90})
            a.trades.append({"owner":"A","signature":"a1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["A"]})
        if h.owner=="B":
            a.funding.append({"owner":"B","source":"F","lamports":"1","signature":"fb","block_time":90})
            a.trades.append({"owner":"B","signature":"b1","block_time":101,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["B"]})
        return 100
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
    def scan(h,mapping):
        if h.owner=="A":
            a.trades.append({"owner":"A","signature":"a1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["A"]})
        if h.owner=="B":
            a.trades.append({"owner":"B","signature":"b1","block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":["B"]})
        return 100
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
    def scan(h,mapping):
        if h.owner in {"A","B"}:
            a.funding.append({"owner":h.owner,"source":"UNKNOWN","lamports":"1","signature":"f-"+h.owner,"block_time":90})
            a.trades.append({"owner":h.owner,"signature":"t-"+h.owner,"block_time":100,"direction":"BUY","quote_asset":"SOL","quote_amount_raw":"100","quote_decimals":9,"program_ids":["DEX"],"signers":[h.owner]})
        return 100
    a._scan_holder=scan
    out=a.analyze()
    assert out["probable_control_clusters"]==[]
    assert "COMMON_FUNDER_UNRESOLVED" in {e["type"] for e in out["edges"]}
