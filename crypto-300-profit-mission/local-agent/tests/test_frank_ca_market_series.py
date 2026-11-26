from datetime import datetime, timezone
import io
import json
from types import SimpleNamespace
import urllib.error
from urllib.parse import parse_qs, urlsplit

from mission_agent.meme.ca_market_series import CAMarketSeries, report_pool
from mission_agent.meme.holder_ranks import _b58
from mission_agent.meme.narrative import extract_page_claim
from mission_agent.mission_control.server import ClusterJobManager, Handler

MINT, PEER, POOL, OTHER, ACTOR = [_b58(bytes([n])*32) for n in range(1,6)]
SIG = _b58(bytes([3])*64)
JOB = "a"*32
AS_OF = 1796000500
PROFILE = {"status":"OK","is_initialized":True}
REVERSED = {"pair_address":POOL,"base_address":PEER,"quote_address":MINT}
MARKET = {"chain":"solana","mint":MINT,"pool_candidates":[REVERSED]}


def candles(*, base=PEER, quote=MINT):
    return {"meta":{"base":{"address":base},"quote":{"address":quote}},
            "data":{"type":"ohlcv_request_response","attributes":{"ohlcv_list":[
                [AS_OF-100,2,3,1,2.7,80],[AS_OF-400,1,2,1,2,50],
            ]}}}


def event(index, *, receive=True, wallet=ACTOR, pool=POOL, change=None):
    left,right=(PEER,MINT) if receive else (MINT,PEER)
    return {"type":"trade","id":f"solana_event_{index}","attributes":{
        "pool_address":pool,"from_token_address":left,"to_token_address":right,
        "tx_hash":SIG,"tx_from_address":wallet,"kind":"provider-direction-is-ignored",
        "block_timestamp":datetime.fromtimestamp(AS_OF-5,timezone.utc).isoformat(),
        "from_token_amount":"9","to_token_amount":"3","price_from_in_usd":"1.6","price_to_in_usd":"2.1",
        **(change or {}),
    }}


def test_reverse_pool_binds_only_exact_peers_and_candles_use_exact_mint():
    assert report_pool(MINT,PROFILE,MARKET,POOL)==PEER
    assert report_pool(MINT,PROFILE,MARKET,OTHER) is None
    assert report_pool(MINT,{"status":"OK"},MARKET,POOL) is None
    assert report_pool(MINT,PROFILE,{**MARKET,"chain":"eth"},POOL) is None
    assert report_pool(MINT,PROFILE,{**MARKET,"pool_candidates":[REVERSED,{**REVERSED,"base_address":OTHER}]},POOL) is None
    urls=[]
    def source(req,timeout):
        urls.append(req.full_url)
        return io.BytesIO(json.dumps(candles() if "/ohlcv/" in req.full_url else {"data":[
            event(1),event(1),event(2,receive=False,wallet=None),event(3,pool=OTHER),
            event(4),event(4,change={"to_token_amount":"7"}),
        ]}).encode())
    series=CAMarketSeries(open_url=source,clock=lambda:AS_OF,monotonic=lambda:0)
    result=series.read(MINT,POOL,PEER,"5m")
    q=parse_qs(urlsplit(urls[0]).query)
    assert q["token"]==[MINT] and q["currency"]==["usd"] and q["aggregate"]==["5"]
    trades_url=urlsplit(urls[1])
    assert trades_url.path.endswith(f"/pools/{POOL}/trades")
    assert parse_qs(trades_url.query)=={"token":[MINT]}
    assert result["chart"]["rows"]==[[AS_OF-400,"1","2","1","2","50"],[AS_OF-100,"2","3","1","2.7","80"]]
    trades=result["trades"]
    assert [(r["side"],r["quantity"],r["price_usd"]) for r in trades["rows"]]==[
        ("SELL","9","1.6"),("BUY","3","2.1")]
    assert trades["rows"][0]["wallet"] is None
    assert trades["coverage"]["unusable_rows"]==2
    assert trades["coverage"]["scope"]=="FIRST_PAGE_LAST_24H_ONLY"
    assert series.read(MINT,POOL,PEER,"5m")["chart"]["cache"]=="FRESH"
    changed=series.read(MINT,POOL,PEER,"1h")
    assert changed["trades"]["cache"]=="FRESH" and len(urls)==3


def test_stale_keeps_original_clock_and_never_returns_other_pool_data():
    now=[AS_OF]
    urls=[]
    def source(req,timeout):
        url=req.full_url
        urls.append(url)
        if now[0] > AS_OF:
            raise urllib.error.HTTPError(url,429,"rate limit",{},None)
        return io.BytesIO(json.dumps(candles() if "/ohlcv/" in url else {"data":[]}).encode())
    client=CAMarketSeries(open_url=source,clock=lambda:now[0],monotonic=lambda:now[0])
    original=client.read(MINT,POOL,PEER,"5m")
    now[0]+=62
    refresh=client.read(MINT,POOL,PEER,"5m")
    assert refresh["chart"]["status"]==refresh["trades"]["status"]=="STALE"
    assert refresh["chart"]["observed_at"]==original["chart"]["observed_at"]==AS_OF
    assert len(urls)==3
    unseen=client.read(MINT,OTHER,PEER,"5m")
    assert unseen["chart"]["status"]=="UNAVAILABLE" and unseen["chart"]["rows"]==[]
    assert len(urls)==3


def test_mismatched_source_and_bad_candles_do_not_hide_other_sections():
    def source(req,timeout):
        return io.BytesIO(json.dumps(candles(base=OTHER) if "/ohlcv/" in req.full_url else {"data":[event(1)]}).encode())
    client=CAMarketSeries(open_url=source,clock=lambda:AS_OF,monotonic=lambda:0)
    out=client.read(MINT,POOL,PEER,"5m")
    assert out["chart"]["status"]=="UNAVAILABLE"
    assert out["trades"]["status"]=="OK" and len(out["trades"]["rows"])==1


def test_older_candles_page_uses_its_boundary_cache_and_never_reloads_trades():
    requests=[]
    def source(request, timeout):
        url=urlsplit(request.full_url)
        params=parse_qs(url.query)
        requests.append((url.path,params))
        if url.path.endswith("/trades"):
            return io.BytesIO(b'{"data":[]}')
        response=candles()
        cutoff=params.get("before_timestamp",[None])[0]
        if cutoff is not None:
            older=int(cutoff)
            response["data"]["attributes"]["ohlcv_list"]=(
                [[older,2,3,1,2,80],[older+1,2,3,1,2,95]]
                if older==AS_OF-401 else []
            )
        return io.BytesIO(json.dumps(response).encode())

    client=CAMarketSeries(open_url=source,clock=lambda:AS_OF,monotonic=lambda:0)
    latest=client.read(MINT,POOL,PEER,"5m")
    assert latest["chart"]["coverage"]["next_before"]==AS_OF-400
    older=client.read(MINT,POOL,PEER,"5m",before=AS_OF-400)
    assert older["before"]==AS_OF-400 and "trades" not in older
    assert [row[0] for row in older["chart"]["rows"]]==[AS_OF-401]
    assert requests[2][1]["before_timestamp"]==[str(AS_OF-401)]
    assert client.read(MINT,POOL,PEER,"5m",before=AS_OF-400)["chart"]["cache"]=="FRESH"
    last=client.read(MINT,POOL,PEER,"5m",before=AS_OF-401)
    assert last["chart"]["coverage"]["next_before"] is None
    assert sum(path.endswith("/trades") for path,_ in requests)==1


def test_unusable_trade_page_is_unavailable_but_provider_empty_page_is_valid():
    trades = [[event(1, pool=OTHER)]]

    def source(req, timeout):
        payload = candles() if "/ohlcv/" in req.full_url else {"data": trades[0]}
        return io.BytesIO(json.dumps(payload).encode())

    client = CAMarketSeries(open_url=source, clock=lambda: AS_OF, monotonic=lambda: 0)
    result = client.read(MINT, POOL, PEER, "5m")
    assert result["chart"]["status"] == "OK"
    assert result["trades"]["status"] == "UNAVAILABLE"
    assert result["trades"]["reason"] == "SOURCE_UNAVAILABLE_OR_MISMATCH"
    trades[0] = []
    empty = client.read(MINT, POOL, PEER, "5m")["trades"]
    assert empty["status"] == "OK"
    assert empty["rows"] == [] and empty["coverage"]["provider_rows"] == 0


def test_unusable_trade_refresh_does_not_replace_verified_same_pool_cache():
    now = [AS_OF]
    trades = [[event(1)]]

    def source(req, timeout):
        payload = candles() if "/ohlcv/" in req.full_url else {"data": trades[0]}
        return io.BytesIO(json.dumps(payload).encode())

    client = CAMarketSeries(open_url=source, clock=lambda: now[0], monotonic=lambda: now[0])
    original = client.read(MINT, POOL, PEER, "5m")["trades"]
    now[0] += 62
    trades[0] = [event(1), event(1, change={"to_token_amount": "7"})]
    refresh = client.read(MINT, POOL, PEER, "5m")["trades"]
    assert refresh["status"] == "STALE"
    assert refresh["observed_at"] == AS_OF and refresh["rows"] == original["rows"]


def test_dashboard_read_is_bound_to_report_scope_and_same_origin(tmp_path):
    jobs=ClusterJobManager(tmp_path)
    seen=[]
    def read(*args, **kwargs):
        seen.append((args, kwargs))
        return {"pool":args[1]}
    jobs.ca_market_series=SimpleNamespace(read=read)
    saved={"mint":MINT,"ca_job_id":JOB,"query_scope":"overview","token_profile":PROFILE,"market":MARKET}
    jobs.latest=lambda *args,**kwargs:saved
    handler=Handler.__new__(Handler)
    handler._allowed_host=lambda:True
    handler._research_origin=lambda:False
    handler._json=lambda value,code=200:(value,code)
    handler.state=SimpleNamespace(cluster_jobs=jobs)
    handler.path=f"/api/cluster-market-series?job_id={JOB}&mint={MINT}&pool={POOL}&period=5m"
    assert handler.do_GET()[1]==403
    handler._research_origin=lambda:True
    assert handler.do_GET()==({"job_id":JOB,"pool":POOL},200)
    assert seen==[((MINT,POOL,PEER,"5m"),{})]
    base_path=handler.path
    handler.path+="&before=1796000000"
    assert handler.do_GET()[1]==200
    assert seen[-1]==((MINT,POOL,PEER,"5m"),{"before":1796000000})
    handler.path=base_path+"&before=not-a-timestamp"
    assert handler.do_GET()[1]==400
    handler.path=base_path
    handler.path=handler.path.replace(POOL,OTHER)
    assert handler.do_GET()[1]==404
    handler.path=handler.path.replace(OTHER,POOL)
    saved["ca_job_id"]="b"*32
    assert handler.do_GET()[1]==404
    saved["ca_job_id"]=JOB
    saved["query_scope"]="wallet"
    assert handler.do_GET()[1]==404
    handler.path+="&period=1h"
    assert handler.do_GET()[1]==400 and len(seen)==2


def test_chinese_source_is_not_discarded_or_labeled_as_claim():
    raw='<html lang="zh-CN"><title>项目主页</title><p>社区用公开网页训练人工智能模型，内容由项目团队自行说明。</p></html>'.encode()
    result=extract_page_claim(raw,"https://project.example.org/",MINT,AS_OF)
    assert "训练人工智能模型" in result["excerpt"]
    assert result["classification"]=="THIRD_PARTY_CLAIM" and not result["exact_ca_mentioned"]
    assert result["official_recognition"]=="UNVERIFIED"


def test_overview_uses_only_verified_reverse_target_field_and_ignores_wallet_symbol(monkeypatch):
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    selected=[]
    reverse={"status":"OK","source":"GECKOTERMINAL_PUBLIC_API","mint":MINT,"pool_address":POOL,
             "quote_address":PEER,"price_usd":"0.002","response_sha256":"a"*64}
    analyzer=WalletClusterAnalyzer(MINT,rpc=object(),special_registry={},query_scope="overview",
        independent_market_client=SimpleNamespace(pool_snapshot=lambda *args:selected.append(args) or reverse))
    emitted=[]
    monkeypatch.setattr(analyzer,"token_profile", lambda: PROFILE)
    monkeypatch.setattr(analyzer,"launch_snapshot",lambda *args:{})
    monkeypatch.setattr(analyzer,"market_snapshot",lambda:{**MARKET,"reason":"NO_BASE_TOKEN_PAIR",
        "pool_candidates":[{**REVERSED,"target_name":"Token fixture"}]})
    monkeypatch.setattr(analyzer,"narrative_snapshot",lambda *args:{})
    monkeypatch.setattr(analyzer,"_progress",lambda *args,**kwargs:emitted.append((args,kwargs)))
    market=analyzer._identity_and_narrative()[2]
    assert selected==[(MINT,POOL,PEER)]
    assert market["reverse_market"]["price_usd"]=="0.002" and market["name"]=="Token fixture"
    assert emitted[0][0]==("BASE_READY",) and emitted[0][1]["market"]==market
    monkeypatch.setattr(analyzer,"token_profile", lambda: {"status":"UNAVAILABLE","reason":"MINT_ACCOUNT_TYPE_UNVERIFIED"})
    market_calls=[]
    monkeypatch.setattr(analyzer,"market_snapshot",lambda:market_calls.append(True))
    assert analyzer._identity_and_narrative()[2]["status"]=="UNAVAILABLE"
    assert market_calls==[]


def test_explicit_refresh_revalidates_fresh_same_pool_and_preserves_failed_observation():
    now = [AS_OF]
    calls = []
    def source(req, timeout):
        url = req.full_url
        calls.append(url)
        if now[0] == AS_OF+2:
            raise urllib.error.HTTPError(url, 429, "fixture", {}, None)
        return io.BytesIO(json.dumps(candles() if "/ohlcv/" in url else {"data": []}).encode())

    client = CAMarketSeries(open_url=source, clock=lambda: now[0], monotonic=lambda: now[0])
    client.read(MINT, POOL, PEER, "5m")
    now[0] += 1
    assert client.read(MINT, POOL, PEER, "5m")["chart"]["observed_at"] == AS_OF
    fresh = client.read(MINT, POOL, PEER, "5m", refresh=True)
    assert fresh["chart"]["observed_at"] == fresh["trades"]["observed_at"] == AS_OF+1
    assert len(calls) == 4
    now[0] += 1
    old = client.read(MINT, POOL, PEER, "5m", refresh=True)
    assert old["chart"]["status"] == old["trades"]["status"] == "STALE"
    assert old["chart"]["observed_at"] == old["trades"]["observed_at"] == AS_OF+1
    assert len(calls) == 5
