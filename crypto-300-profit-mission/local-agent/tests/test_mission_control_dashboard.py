import time

from mission_agent.mission_control.server import (
    CLUSTER_PRESETS, ClusterJobManager, DashboardState, _atomic_write_text, _content_type_is_json, _decode_json_object, _origin_is_loopback,
)
from mission_agent.mission_control.service import MissionMemeService
from test_mission_control_service import make_prod, policy


def quote(price):
    return {
        "status":"OK",
        "source":"JUPITER_OFFICIAL",
        "observed_at":time.time(),
        "input_usdc":"30",
        "execution_price_usdc":price,
        "price_impact_pct":"0.5",
        "route_exists":True,
        "route_plan":[{}],
    }


def test_same_decision_refreshes_dashboard_metrics_without_new_event(tmp_path):
    prod=tmp_path/"prod";control=tmp_path/"control";p=tmp_path/"policy.json"
    make_prod(prod);policy(p)
    service=MissionMemeService(production_root=prod,control_root=control,policy_path=p)
    service.jupiter.quote_usdc_to_token=lambda *a,**k:quote("1.02")
    first=service.cycle()
    assert first["decision_events"][0]["decision"]=="BUY"
    service.control.db.execute("delete from market_cache")
    service.jupiter.quote_usdc_to_token=lambda *a,**k:quote("1.05")
    second=service.cycle()
    assert second["decision_events"]==[]
    assert service.control.db.execute("select count(*) from decision_snapshots").fetchone()[0]==1
    assert service.control.db.execute("select count(*) from decision_events").fetchone()[0]==1
    assert service.control.db.execute("select count(*) from candidate_latest").fetchone()[0]==1
    dashboard=DashboardState(prod,control)
    rows=dashboard.candidates()
    assert rows[0]["decision"]=="BUY"
    assert rows[0]["metrics"]["execution_price_usdc"]=="1.05"
    assert rows[0]["decision_quote"]["status"]=="OK"
    assert rows[0]["decision_quote"]["execution_price_usdc"]=="1.05"
    assert rows[0]["latest_buy_price_usdc"]=="1"
    service.close()


def test_stale_wait_still_exposes_quote_and_frank_price_for_research(tmp_path):
    prod=tmp_path/"prod";control=tmp_path/"control";p=tmp_path/"policy.json"
    make_prod(prod,latest_at=int(time.time())-3600);policy(p)
    service=MissionMemeService(production_root=prod,control_root=control,policy_path=p)
    service.jupiter.quote_usdc_to_token=lambda *a,**k:quote("1.07")
    result=service.cycle()
    assert result["decision_events"][0]["decision"]=="WAIT"
    dashboard=DashboardState(prod,control)
    row=dashboard.candidates()[0]
    assert row["latest_buy_price_usdc"]=="1"
    assert row["metrics"].get("execution_price_usdc") is None
    assert row["decision_quote"]["status"]=="OK"
    assert row["decision_quote"]["execution_price_usdc"]=="1.07"
    assert row["decision_quote"]["price_impact_pct"]=="0.5"
    service.close()


def test_cluster_query_validates_solana_ca_and_presets(tmp_path):
    manager=ClusterJobManager(tmp_path/"control")
    mint="So11111111111111111111111111111111111111112"
    assert manager.validate_mint(mint)==mint
    for bad in ("", "not-a-ca", "../escape", "0"*32):
        try:
            manager.validate_mint(bad)
        except ValueError as exc:
            assert str(exc)=="INVALID_SOLANA_CA"
        else:
            raise AssertionError("invalid CA accepted")


def test_dashboard_static_contains_signal_and_cluster_tabs():
    from mission_agent.mission_control.server import Handler
    html=(Handler.static_root/"index.html").read_text()
    assert 'data-view="signals"' in html
    assert 'data-view="cluster"' in html
    assert 'id="cluster-form"' in html
    assert 'id="cluster-result"' in html
    assert 'id="cluster-conclusion"' in html
    assert 'id="cluster-token-profile"' in html
    assert 'id="cluster-market"' in html
    assert 'id="cluster-narrative"' in html
    assert 'Top20 全解析' in html


class NoRunExecutor:
    def submit(self,*args,**kwargs):
        return object()


def test_cluster_post_json_must_be_object():
    assert _decode_json_object(b'{"mint":"M"}')=={"mint":"M"}
    for raw,reason in ((b'[]',"JSON_OBJECT_REQUIRED"),(b'"x"',"JSON_OBJECT_REQUIRED"),(b'{',"INVALID_JSON")):
        try:
            _decode_json_object(raw)
        except ValueError as exc:
            assert str(exc)==reason
        else:
            raise AssertionError("invalid cluster POST accepted")


def test_cluster_post_rejects_cross_origin_and_non_json():
    assert _origin_is_loopback(None) is True
    assert _origin_is_loopback("http://127.0.0.1:8766") is True
    assert _origin_is_loopback("http://localhost:8766") is True
    assert _origin_is_loopback("http://evil.example") is False
    assert _content_type_is_json("application/json") is True
    assert _content_type_is_json("application/json; charset=utf-8") is True
    assert _content_type_is_json("text/plain") is False


def test_cluster_jobs_dedupe_only_same_ca_and_same_preset(tmp_path):
    manager=ClusterJobManager(tmp_path/"control")
    manager.executor=NoRunExecutor()
    mint="So11111111111111111111111111111111111111112"
    quick=manager.submit(mint,"quick")
    deep=manager.submit(mint,"deep")
    quick_again=manager.submit(mint,"quick")
    assert quick["job_id"]!=deep["job_id"]
    assert quick_again["job_id"]==quick["job_id"]


def test_cluster_job_memory_retention_is_bounded(tmp_path):
    manager=ClusterJobManager(tmp_path/"control")
    now=time.time()
    with manager.lock:
        for i in range(80):
            job_id=f"done-{i}"
            manager.jobs[job_id]={
                "job_id":job_id,"mint":"M","preset":"quick","status":"DONE",
                "created_at":now-i,"started_at":now-i,"finished_at":now-i,"error":None,
            }
        manager._prune_jobs_locked()
    assert len(manager.jobs)==manager.max_retained_jobs


def test_dashboard_frontend_restores_latest_cluster_report():
    from mission_agent.mission_control.server import Handler
    js=(Handler.static_root/"app.js").read_text()
    assert "/api/cluster-latest?mint=" in js
    assert "mission-meme-last-cluster-ca" in js


def test_dashboard_cluster_report_shows_observation_age_and_shared_infra_label():
    from mission_agent.mission_control.server import Handler
    js=(Handler.static_root/"app.js").read_text()
    assert "观测时间" in js
    assert "report.observed_at" in js
    assert "共享公共基础设施（不代表共同控制）" in js


def test_atomic_cluster_report_write_replaces_complete_file(tmp_path):
    path=tmp_path/"latest.json"
    _atomic_write_text(path,'{"version":1}')
    assert path.read_text()=='{"version":1}'
    _atomic_write_text(path,'{"version":2,"complete":true}')
    assert path.read_text()=='{"version":2,"complete":true}'
    assert list(tmp_path.glob("latest.json.tmp-*"))==[]


def test_cluster_dashboard_explains_presets_and_localizes_rate_limit():
    from mission_agent.mission_control.server import Handler
    html=(Handler.static_root/"index.html").read_text()
    js=(Handler.static_root/"app.js").read_text()
    assert "快速" in html and "标准" in html and "深度" in html
    assert "浅扫前 6 个 owner" in html
    assert "自动加深到 30 + 12" in html
    assert "Top20 owner 全部深扫" in html
    assert "免费 Solana RPC 触发限流（HTTP 429）" in js
    assert "execution_quote_30_usdc" in js
    assert "token_profile" in js
    assert "first_acquisition" in js


def test_cluster_manager_has_multiple_free_rpc_endpoints_by_default(tmp_path,monkeypatch):
    monkeypatch.delenv("SOLANA_RPC_URLS",raising=False)
    monkeypatch.delenv("SOLANA_RPC_URL",raising=False)
    manager=ClusterJobManager(tmp_path/"control")
    assert manager.rpc_endpoints[0]=="https://api.mainnet.solana.com"
    assert "https://solana-rpc.publicnode.com" in manager.rpc_endpoints
    assert "https://api.mainnet-beta.solana.com" in manager.rpc_endpoints
    assert "https://rpc.ankr.com/solana" in manager.rpc_endpoints
    assert len(manager.rpc_endpoints)>=4


def test_cluster_dashboard_has_two_level_conclusions():
    from mission_agent.mission_control.server import Handler
    js=(Handler.static_root/"app.js").read_text()
    assert "链上 / 市场结构结论" in js
    assert "完整投资结论" in js
    assert "完整投资结论待叙事 / 官方关系核实" in js


def test_standard_cluster_preset_is_adaptive_not_bruteforce():
    standard=CLUSTER_PRESETS["standard"]
    assert standard["deep_holders"]==6
    assert standard["history_per_holder"]==12
    assert standard["funding_lookback"]==8
    assert standard["adaptive_history_per_holder"]==30
    assert standard["adaptive_funding_lookback"]==12


def test_assessment_history_only_appends_on_meaningful_change(tmp_path):
    manager=ClusterJobManager(tmp_path/"control")
    out=tmp_path/"report"
    out.mkdir()
    base={
        "observed_at":100,
        "assessment":{
            "trading_status":"WATCH / WALLET_CLUSTER_UNRESOLVED",
            "chain_permission_status":"PASS",
            "cluster_status":"WALLET_CLUSTER_UNRESOLVED",
            "narrative_status":"NOT_AUTOMATICALLY_VERIFIED",
        },
        "metrics":{
            "LARGEST_PROBABLE_CONTROL_CLUSTER_PCT":"0",
            "UNRESOLVED_MATERIAL_HOLDER_PCT":"12.0000",
        },
        "token_profile":{"mint_authority":None,"freeze_authority":None},
    }
    manager._attach_assessment_history(out,base,"standard")
    assert len(base["assessment_history"])==1
    same=json.loads(json.dumps(base))
    same["observed_at"]=200
    manager._attach_assessment_history(out,same,"standard")
    assert len(same["assessment_history"])==1
    changed=json.loads(json.dumps(base))
    changed["observed_at"]=300
    changed["assessment"]["cluster_status"]="PROBABLE_CONTROL_CLUSTER_PRESENT"
    changed["assessment"]["trading_status"]="WATCH / CONTROL_CLUSTER_RISK"
    changed["metrics"]["LARGEST_PROBABLE_CONTROL_CLUSTER_PCT"]="24.0000"
    manager._attach_assessment_history(out,changed,"standard")
    assert len(changed["assessment_history"])==2
    latest=changed["assessment_history"][-1]
    assert "PROBABLE_CONTROL_CLUSTER_PRESENT" in latest["new_risk"]
    assert "cluster_status" in latest["changed_fields"]


def test_dashboard_frontend_shows_progress_and_conclusion_history():
    from mission_agent.mission_control.server import Handler
    js=(Handler.static_root/"app.js").read_text()
    assert "clusterProgressDetail" in js
    assert "ADAPTIVE_DEEPEN" in js
    assert "结论变化" in js
    assert "assessment_history" in js
