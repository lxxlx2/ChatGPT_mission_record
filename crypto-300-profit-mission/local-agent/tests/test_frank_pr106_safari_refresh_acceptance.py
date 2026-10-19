"""Hermetic native HTTP checks for PR106 real Mac Safari 503 QA bridge."""
from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
from pathlib import Path
import sys
import threading
from urllib.parse import urlencode

import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/"scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0,str(SCRIPTS))
qa=importlib.import_module("frank_pr106_safari_refresh_acceptance")


@contextmanager
def served(handler):
    server=ThreadingHTTPServer(("127.0.0.1",0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def http_call(port, route, method="GET"):
    conn=HTTPConnection("127.0.0.1",port,timeout=3)
    try:
        conn.request(method,route)
        r=conn.getresponse()
        return r.status,r.read()
    finally:
        conn.close()


class ExistingDashboard(BaseHTTPRequestHandler):
    observed=[]
    def do_GET(self):
        type(self).observed.append(self.path)
        assert self.path in qa.API, "test proxy must not call unknown live routes"
        raw=b'[]' if self.path=="/api/decisions" else b'{"status":"LIVE"}'
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_POST(self):
        raise AssertionError("QA MUST NOT POST to live Dashboard")
    def log_message(self,*_): pass


@pytest.mark.parametrize("stage,expected",[
    ("fault","HISTORY_UNAVAILABLE_OTHERS_LIVE"),
    ("recovery","HISTORY_AVAILABLE_OTHERS_LIVE"),
])
def test_real_localhost_preview_is_readonly_and_synthetic_fault_never_hits_source(
        tmp_path, stage,expected):
    token="c"*32
    receipts={}
    obs=defaultdict(list)
    class Source(ExistingDashboard):
        observed=[]
    with served(Source) as source:
        handler=qa.make_handler(tmp_path,source.server_port,stage,token,receipts,obs)
        with served(handler) as preview:
            panel="/__qa/panel?"+urlencode({"token":token,"stage":stage})
            code,body=http_call(preview.server_port,panel)
            assert code==200
            assert b'iframe id="product"' in body
            assert b'/index.html#signals' in body
            assert b'qa-status' in body
            assert b'__TOKEN__' not in body
            assert http_call(preview.server_port,"/__qa/panel?token=wrong&stage="+stage)[0]==403
            assert http_call(preview.server_port,"/__qa/ready?token="+token+"&stage="+stage)[0]==403
            assert http_call(preview.server_port,"/api/decisions")[0] == (503 if stage=="fault" else 200)
            for endpoint in qa.CORE:
                assert http_call(preview.server_port,endpoint)[0]==200
            assert http_call(preview.server_port,"/api/cluster-analysis",method="POST")[0]==405
            ready="/__qa/ready?"+urlencode({"token":token,"stage":stage,"state":expected})
            assert http_call(preview.server_port,ready)[0]==204
            assert receipts=={stage:expected}
            qa.verify_stage(stage,receipts,obs)
    if stage=="fault":
        assert "/api/decisions" not in Source.observed
    else:
        assert "/api/decisions" in Source.observed
    assert set(Source.observed)==qa.CORE | ({"/api/decisions"} if stage=="recovery" else set())


def test_refuse_false_positive_receipt_or_missing_product_get():
    statuses=defaultdict(list)
    receipts={"fault":qa.EXPECTED["fault"]}
    statuses["/api/decisions"]=[503]
    with pytest.raises(RuntimeError,match="REQUIRED_FRANK_GET_NOT_200"):
        qa.verify_stage("fault",receipts,statuses)
    for endpoint in qa.CORE:
        statuses[endpoint]=[200]
    qa.verify_stage("fault",receipts,statuses)
    statuses["/api/decisions"]=[200]
    with pytest.raises(RuntimeError,match="HISTORY_GET_NOT_EXPECTED_STATUS"):
        qa.verify_stage("fault",receipts,statuses)
    receipts={"fault":"PRODUCT_UI_NOT_VERIFIED"}
    with pytest.raises(RuntimeError,match="FRANK_SAFARI_UI_STAGE_NOT_VERIFIED"):
        qa.verify_stage("fault",receipts,statuses)


def test_qa_html_has_actual_healthy_history_and_state_checks():
    for stage in qa.STAGES:
        text=qa.qa_page(stage,"a"*32).decode("utf-8")
        assert 'frame.contentDocument' in text
        assert "classList.contains('offline')" in text
        assert "历史判断记录暂时无法读取" in text
        assert "本区域数据未核实" in text
        assert "历史判断记录" not in text.split("</script>")[0].split("qa-status")[0]
        assert "fetch('/__qa/ready?'+q" in text
        assert "historyPanel.open=true" in text
        assert qa.EXPECTED[stage] in text
    with pytest.raises(ValueError):
        qa.qa_page("other","a"*32)
    with pytest.raises(ValueError):
        qa.qa_page("fault","not-a-token")


def test_static_snapshot_is_from_approved_product_git_object_not_mutable_worktree(
        tmp_path,monkeypatch):
    fake_root=tmp_path/"checkout"
    fake_root.mkdir()
    sha="b"*40
    approved={name:("approved:"+name).encode() for name in qa.base.STATIC_FILES}
    monkeypatch.setattr(qa,"read_git_head_passively",lambda _:sha)
    requested=[]
    def fake_blob(_,object_sha,path):
        requested.append((object_sha,path))
        return approved[path.split("/")[-1]]
    monkeypatch.setattr(qa,"committed_blob",fake_blob)
    output=tmp_path/"out"
    hashes=qa.export_approved_static(fake_root,sha,output)
    assert set(hashes)==qa.base.STATIC_FILES
    assert len(requested)==2*len(qa.base.STATIC_FILES)
    assert set(sha for sha,_ in requested)=={qa.PRODUCT_SHA,sha}
    for name,value in approved.items():
        assert (output/name).read_bytes()==value
    qa.base.verify_preview_snapshot(output,hashes)
    (output/"app.js").chmod(0o600)
    (output/"app.js").write_text("TAMPERED")
    with pytest.raises(RuntimeError,match="STOP_STATIC_SNAPSHOT_CHANGED"):
        qa.base.verify_preview_snapshot(output,hashes)


def test_modified_qa_static_fails_closed_before_browser(tmp_path,monkeypatch):
    root=tmp_path/"checkout"
    root.mkdir()
    sha="c"*40
    monkeypatch.setattr(qa,"read_git_head_passively",lambda _:sha)
    def changed(_,commit,path):
        if commit==sha and path.endswith("/app.js"):
            return b"EVIL_CHANGE"
        return b"PINNED_SOURCE"
    monkeypatch.setattr(qa,"committed_blob",changed)
    with pytest.raises(RuntimeError,match="QA_MODIFIED_APPROVED_PRODUCT_STATIC_app.js"):
        qa.export_approved_static(root,sha,tmp_path/"static")


def test_source_approval_sha_is_fixed():
    assert qa.PRODUCT_SHA=="8a8b4fcc36242c0ba03b03170225f723d847fa53"
    assert qa.STAGES==("fault","recovery")
    assert qa.API.issubset(qa.base.GET_PATHS)
    assert "/api/cluster-analysis" not in qa.API
