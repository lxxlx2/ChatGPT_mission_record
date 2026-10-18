"""Hermetic zero-touch C02 QA coverage: no actual Mac screenshot is claimed."""
from __future__ import annotations

from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import importlib
import json
import os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from urllib.parse import urlencode, urlsplit, parse_qs
import zipfile

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
qa = importlib.import_module("frank_c02_auto_safari_capture")
old = importlib.import_module("frank_pr101_safari_evidence")
MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
OTHER = "So11111111111111111111111111111111111111112"


@contextmanager
def server(handler):
    instance = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=2)


def get_request(port, path, method="GET"):
    conn = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        conn.request(method, path)
        response = conn.getresponse()
        return response.status, response.read()
    finally:
        conn.close()


def test_automatically_selects_cached_exact_ca_and_no_scanner(monkeypatch):
    requests = []
    def fake_json(port, path):
        requests.append(path)
        if path == "/api/candidates":
            return {"candidates":[{"mint":MINT},{"mint":OTHER},{"mint":"invalid"}]}
        if path == "/api/frank-observed-watchlist":
            return {"rows":[{"mint":OTHER},{"mint":MINT}]}
        if path.endswith(MINT):
            return {"mint":MINT,"observed_at":123}
        return None
    monkeypatch.setattr(qa, "local_json", fake_json)
    selected=qa.select_local_ca(8777,None)
    assert selected == {"mint":MINT,"archive_found":True,
                        "source":"LOCAL_CACHED_CA_MATCH","checked":1}
    assert all(x.startswith("/api/cluster-latest?mint=") or
               x in ("/api/candidates","/api/frank-observed-watchlist") for x in requests)
    assert all("cluster-analysis" not in x for x in requests)
    explicit=qa.select_local_ca(8777,OTHER)
    assert explicit["mint"]==OTHER and not explicit["archive_found"]
    with pytest.raises(RuntimeError,match="INVALID_EXPLICIT_SOLANA_CA"):
        qa.select_local_ca(8777,"bad")
    assert qa.collect_mints({"rows":[{"mint":MINT},{"mint":MINT},{"mint":"??"}]})==[MINT]


def test_qa_parent_has_real_c02_button_click_and_waits_for_exact_mint():
    html=qa.qa_page(MINT,"overview","testtoken").decode("utf-8")
    assert 'id="qa-app"' in html
    assert 'src="/index.html#cluster"' in html
    assert 'button.click()' in html
    assert 'cluster-archive-load' in html
    assert "d.querySelector('.summary-ca')" in html
    assert "PRODUCT_UI_MINT_MISMATCH" in html
    assert '"/api/cluster-analysis"' not in html
    assert "fetch(signal,{method:'GET'" in html
    with pytest.raises(ValueError):
        qa.qa_page(MINT,"unknown","token")


def test_real_localhost_qa_server_readiness_and_post_blocked(tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("REAL INDEX",encoding="utf-8")
    receipts={}
    secret="a"*32
    with server(qa.make_auto_handler(static,8765,secret,MINT,receipts)) as srv:
        page="/__qa/panel?" + urlencode({"token":secret,"stage":"overview"})
        code,html=get_request(srv.server_port,page)
        assert code==200
        assert b"cluster-archive-load" in html
        assert MINT.encode("ascii") in html
        assert get_request(srv.server_port,"/__qa/panel?token=wrong&stage=overview")[0]==403
        assert get_request(srv.server_port,"/__qa/panel?token="+secret+"&stage=nope")[0]==403
        ready="/__qa/ready?" + urlencode({"token":secret,"stage":"overview","state":"ARCHIVE_MISSING"})
        assert get_request(srv.server_port,ready)[0]==204
        assert receipts == {"overview":"ARCHIVE_MISSING"}
        assert get_request(srv.server_port,ready.replace(secret,"wrong"))[0]==403
        assert get_request(srv.server_port,"/api/cluster-analysis",method="POST")[0]==405
        assert get_request(srv.server_port,"/index.html")[0]==200


@pytest.mark.parametrize("outcome,expected_rc,front_fault,archive_race", [
    ("ARCHIVE_MISSING",0,None,False),
    ("PRODUCT_UI_MINT_MISMATCH",3,None,False),
    ("ARCHIVE_MISSING",3,"report_stays_overview",False),
    ("ARCHIVE_MISSING",3,"report_wrong_token",False),
    ("ARCHIVE_MISSING",3,None,True),
])
def test_zero_touch_capture_path_automatically_produces_zip_and_finder_selection(
        tmp_path,monkeypatch,outcome,expected_rc,front_fault,archive_race):
    home=tmp_path / "home"
    (home/"Downloads").mkdir(parents=True)
    monkeypatch.setattr(Path,"home",staticmethod(lambda:home))
    monkeypatch.setattr(qa.sys,"platform","darwin")
    monkeypatch.setattr(qa.shutil,"which",lambda _: "/mock")
    monkeypatch.setattr(old,"discover_dashboard_port",lambda _home: 8765)
    monkeypatch.setattr(old,"verify_local_source",lambda _:None)

    path=tmp_path/"copy"/old.STATIC_REL
    path.mkdir(parents=True)
    for name in old.STATIC_FILES:
        (path/name).write_text("TEST EXACT GIT STATIC "+name,encoding="utf-8")
    approved_sha="f"*40
    monkeypatch.setattr(old,"pinned_candidate_checkout",lambda _script,_sha: path)
    monkeypatch.setattr(old,"verify_git_source",lambda *_:None)
    def fake_export(_root,_sha,dest):
        dest.mkdir()
        result={}
        for name in old.STATIC_FILES:
            payload=("STATIC "+name).encode("utf-8")
            (dest/name).write_bytes(payload)
            result[name]=old.sha256_bytes(payload)
        return result
    monkeypatch.setattr(old,"export_exact_git_static",fake_export)
    monkeypatch.setattr(qa,"select_local_ca",lambda *_:{"mint":MINT,"archive_found":True,
                           "source":"LOCAL_CACHED_CA_MATCH","checked":1})
    urls=[]
    front=[None]
    def fake_run(command,**_kwargs):
        if command[:3]==["open","-a","Safari"]:
            link=command[-1]
            urls.append(link)
            bits=urlsplit(link)
            params=parse_qs(bits.query)
            if front_fault=="report_stays_overview" and params["stage"]==["report"]:
                pass
            elif front_fault=="report_wrong_token" and params["stage"]==["report"]:
                front[0]=link.replace(params["token"][0],"wrongtoken")
            else:
                front[0]=link
            ready="/__qa/ready?" + urlencode({"token":params["token"][0],
               "stage":params["stage"][0],"state":outcome})
            status,_=get_request(int(bits.netloc.split(":")[-1]),ready)
            assert status==204
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(qa.subprocess,"run",fake_run)
    monkeypatch.setattr(qa,"safari_front_url",lambda:front[0])
    def fake_png(target):
        binary=b"\x89PNG\r\n\x1a\n"+bytes(4096)
        target.write_bytes(binary)
        return {"file":target.name,"bytes":len(binary),
                "sha256":old.sha256_bytes(binary),"meaning":"SYNTHETIC_ONLY"}
    monkeypatch.setattr(qa,"automatic_screenshot",fake_png)
    monkeypatch.setattr(qa.time,"sleep",lambda *_:None)
    other_archive_bytes=[]
    if archive_race:
        native_link=os.link
        def competitor_creates_same_name_before_link(source,destination):
            with zipfile.ZipFile(destination,"x") as z:
                z.writestr("OTHER_RUN.txt","independent valid competitor evidence")
            other_archive_bytes.append(Path(destination).read_bytes())
            return native_link(source,destination)
        monkeypatch.setattr(qa.os,"link",competitor_creates_same_name_before_link)
    assert qa.run_auto(sha=approved_sha,mint=None)==expected_rc
    assert len(urls)==(1 if outcome=="PRODUCT_UI_MINT_MISMATCH" else 2)
    files=list((home/"Downloads").glob("frank-c02-auto-evidence-*.zip"))
    if expected_rc!=0:
        if archive_race:
            assert len(files)==1, "competing run ZIP must remain"
            assert files[0].read_bytes()==other_archive_bytes[0], "must not erase or mutate the competing ZIP"
            with zipfile.ZipFile(files[0]) as other:
                assert other.read("OTHER_RUN.txt")==b"independent valid competitor evidence"
        else:
            assert files==[], "bad product UI must not produce a valid acceptance ZIP"
        rejected=list((home/"Downloads").glob("frank-c02-REJECTED-*"))
        assert len(rejected)==1
        assert (rejected[0]/"c02-overview.png").is_file()
        rejection=json.loads((rejected[0]/"REJECTED.json").read_text())
        if front_fault:
            assert "SAFARI_FRONT_STAGE_OR_TOKEN_MISMATCH_report" in rejection["reason"]
        elif archive_race:
            assert "FileExistsError" in rejection["reason"]
        else:
            assert "STOP_C02_PRODUCT_UI_NOT_VERIFIED" in rejection["reason"]
        return
    assert len(files)==1
    with zipfile.ZipFile(files[0]) as z:
        assert {"manifest.json","c02-automatic-acceptance.json",
                "screenshots/c02-overview.png","screenshots/c02-report.png"}==set(z.namelist())
        manifest=json.loads(z.read("manifest.json"))
        metadata=json.loads(z.read("c02-automatic-acceptance.json"))
        assert manifest["preview_source_sha"]==approved_sha
        assert metadata["backend_code_identity"]=="UNVERIFIED"
        assert metadata["selected"]["mint"]==MINT
        assert metadata["page_states"]=={"overview":"ARCHIVE_MISSING","report":"ARCHIVE_MISSING"}
        assert metadata["archive_reporting"]=="NO_VERIFIED_CACHED_ARCHIVE"
        assert metadata["real_mac_safari"] is True
    assert all("/__qa/panel?" in link for link in urls)


def test_mint_not_in_local_records_returns_explicit_unknown(monkeypatch):
    monkeypatch.setattr(qa,"local_json",lambda *_:None)
    result=qa.select_local_ca(8765,None)
    assert result["mint"] is None and result["source"]=="NO_LOCAL_CA"
    assert result["archive_found"] is False

def test_safari_front_requires_exact_origin_path_token_and_stage():
    good="http://127.0.0.1:50998/__qa/panel?token=abcd1234&stage=report"
    valid="http://127.0.0.1:50998/__qa/panel?stage=report&token=abcd1234"
    assert qa.safari_front_matches(good,good)
    assert qa.safari_front_matches(valid,good)
    rejects=(
        None,
        "http://127.0.0.1:50998/__qa/panel?token=abcd1234&stage=overview",
        "http://127.0.0.1:50998/__qa/panel?token=wrong&stage=report",
        "http://127.0.0.1:50999/__qa/panel?token=abcd1234&stage=report",
        "http://localhost:50998/__qa/panel?token=abcd1234&stage=report",
        "https://127.0.0.1:50998/__qa/panel?token=abcd1234&stage=report",
        "http://127.0.0.1:50998/__qa/panel?token=abcd1234&stage=report&stage=report",
        "http://127.0.0.1:50998/__qa/panel?token=abcd1234&stage=report&extra=1",
        "http://127.0.0.1:50998/__qa/panel?token=abcd1234&stage=report#fake",
    )
    assert all(not qa.safari_front_matches(actual,good) for actual in rejects)
