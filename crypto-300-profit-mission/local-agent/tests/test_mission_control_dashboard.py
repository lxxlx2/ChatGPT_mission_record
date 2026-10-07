import time

from mission_agent.mission_control.server import (
    ClusterJobManager, DashboardState, _content_type_is_json, _decode_json_object, _origin_is_loopback,
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
