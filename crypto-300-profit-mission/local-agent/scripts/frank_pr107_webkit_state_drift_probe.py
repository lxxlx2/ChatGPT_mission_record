#!/usr/bin/env python3
"""Real WebKit / actual PR106 product: naturally occurring refresh invalidates QA.

Runs offline against temporary 127.0.0.1 native Dashboard and the real GET-only
QA handler; injects runtime 503 only into synthetic source AFTER ready, waits
for the actual 5-second app.js setInterval (no forced refresh/DOM mutation).
No production dashboard, Safari.app, blockchain, POST, mail or trades.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import threading
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

import frank_pr106_safari_refresh_acceptance as qa


@contextmanager
def server(handler):
    s=ThreadingHTTPServer(("127.0.0.1",0),handler)
    t=threading.Thread(target=s.serve_forever,daemon=True)
    t.start()
    try:
        yield s
    finally:
        s.shutdown()
        s.server_close()
        t.join(timeout=2)


class RealSyntheticSource(BaseHTTPRequestHandler):
    degraded=False
    calls=[]

    def do_GET(self):
        cls=type(self)
        cls.calls.append((self.command,self.path))
        if self.path=="/api/runtime" and cls.degraded:
            code,body=503,{"error":"RUNTIME_TEMPORARILY_UNAVAILABLE"}
        elif self.path=="/api/runtime":
            code,body=200,{"status":"LIVE","heartbeat_age_seconds":1}
        elif self.path in ("/api/trades","/api/candidates","/api/review-activity","/api/decisions"):
            code,body=200,[]
        elif self.path=="/api/frank-observed-watchlist":
            code,body=200,{"status":"OBSERVED","rows":[],"summary":{}}
        elif self.path=="/api/coverage":
            code,body=200,{"status":"OBSERVED","trades":0,"candidates":0}
        elif self.path=="/api/control-health":
            code,body=200,{"status":"HEALTHY"}
        elif self.path in qa.base.GET_PATHS:
            code,body=200,{}
        else:
            code,body=404,{"error":"UNKNOWN_FAKE_ROUTE"}
        raw=json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        raise AssertionError("HTTP POST forbidden")

    def log_message(self,*args): pass


def run() -> None:
    static=Path(__file__).resolve().parents[1]/"mission_agent/mission_control/static"
    with sync_playwright() as playwright:
        browser=playwright.webkit.launch(headless=True)
        try:
            for stage in qa.STAGES:
                class Synthetic(RealSyntheticSource):
                    degraded=False
                    calls=[]
                token="a"*32
                receipts={}
                observed=defaultdict(list)
                checks={}
                with server(Synthetic) as upstream:
                    with server(qa.make_handler(
                            static,upstream.server_port,stage,token,receipts,observed,checks)) as preview:
                        page=browser.new_page(viewport={"width":1440,"height":900})
                        try:
                            url=f"http://127.0.0.1:{preview.server_port}/__qa/panel?"+urlencode(
                                {"token":token,"stage":stage})
                            page.goto(url,wait_until="domcontentloaded")
                            page.wait_for_function(
                                """() => document.title.startsWith('FRANK_106_') &&
                                  document.title !== 'FRANK_106_STATE_REVOKED'""",
                                timeout=18000)
                            assert receipts.get(stage)==qa.EXPECTED[stage], (stage,receipts)
                            first=qa.confirm_fresh_dom(
                                stage,receipts,observed,checks,"before",timeout=5)
                            assert first and not checks.get("invalidated")
                            # Force the synthetic upstream to degrade, but do not mutate
                            # the DOM or manually invoke product refresh().
                            Synthetic.degraded=True
                            page.wait_for_function(
                                """() => {
                                  const e=document.getElementById('product')
                                    ?.contentDocument?.getElementById('runtime');
                                  return e?.classList.contains('offline') &&
                                    e.textContent.includes('/api/runtime 503');
                                }""",
                                timeout=8500)
                            assert any(c==503 for c in observed["/api/runtime"])
                            assert checks["invalidated"] is True
                            page.wait_for_function(
                                "() => document.title === 'FRANK_106_STATE_REVOKED'",
                                timeout=2500)
                            try:
                                qa.confirm_fresh_dom(
                                    stage,receipts,observed,checks,"after",timeout=.2)
                            except RuntimeError as e:
                                assert ("INVALIDATED" in str(e) or
                                        "REQUIRED_FRANK_GET_NOT_200" in str(e))
                            else:
                                raise AssertionError("FALSE_ACCEPTANCE_AFTER_NATURAL_RUNTIME_503")
                            assert all(method=="GET" for method,_ in Synthetic.calls)
                            print("FRANK_PR107_NATURAL_REFRESH_STATE_DRIFT_REJECTED="+stage,
                                  flush=True)
                        finally:
                            page.close()
        finally:
            browser.close()


if __name__=="__main__":
    run()
