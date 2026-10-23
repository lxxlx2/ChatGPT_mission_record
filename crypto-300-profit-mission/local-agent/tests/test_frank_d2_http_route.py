"""Direct original server Handler GET route tests with fake in-memory state.

Actual route methods, no socket listener, no real production DB, RPC, secrets.
"""
from __future__ import annotations

import unittest
import json
from pathlib import Path
import tempfile

from mission_agent.mission_control.server import Handler
from mission_agent.mission_control.wallet_d2_ingress import (
    D2IngressError, SOURCE_NAME, build_d2_document_from_verified_pr60_replay,
    query_d2,
)
from test_frank_d2_owner_at_slot import source
from mission_agent.mission_control.wallet_owner_at_slot import _mint_key

MINT = "So11111111111111111111111111111111111111112"


class State:
    def __init__(self):
        self.calls = []

    def frank_d2_at_slot(self, *, mint=None, page=0):
        # Mirror the actual query_d2 validation prior to disk read.
        if mint is not None and not _mint_key(mint):
            raise D2IngressError("INVALID_D2_MINT")
        self.calls.append((mint,page))
        return {"status":"SOURCE_NOT_IMPORTED", "rows":[]}


class Request:
    _d2_same_origin_read=Handler._d2_same_origin_read
    _allowed_host=lambda self: self.good_host

    def __init__(self, path, *, headers=None, host_ok=True):
        self.path=path
        self.headers=headers or {}
        self.good_host=host_ok
        self.state=State()
        self.reply=None

    def _json(self, payload, status=200):
        self.reply=(status,payload)
        return self.reply

    def send_error(self, status, *_):
        self.reply=(status,None)
        return self.reply

    def go(self):
        Handler.do_GET(self)
        return self.reply


class D2HttpSecurityTests(unittest.TestCase):
    def test_custom_request_header_required(self):
        req=Request("/api/frank-d2-at-slot?page=0",headers={"Host":"127.0.0.1:8766"})
        status,body=req.go()
        self.assertEqual(status,403)
        self.assertEqual(req.state.calls,[])

    def test_cross_site_and_foreign_origin_rejected(self):
        for headers in (
            {"Sec-Fetch-Site":"cross-site"},
            {"Sec-Fetch-Site":"same-site"},
            {"Origin":"http://other.local:8766"},
            {"Origin":"https://127.0.0.1:8766"},
        ):
            request=Request("/api/frank-d2-at-slot?mint="+MINT,headers={
                "X-Frank-D2-Read":"1", "Host":"127.0.0.1:8766", **headers})
            self.assertEqual(request.go()[0],403)
            self.assertEqual(request.state.calls,[])

    def test_same_origin_exact_lookup_and_page_use_only_bounded_service(self):
        for url,mint,page in (
            ("/api/frank-d2-at-slot",None,0),
            ("/api/frank-d2-at-slot?page=3",None,3),
            ("/api/frank-d2-at-slot?mint="+MINT,MINT,0),
        ):
            req=Request(url,headers={
                "X-Frank-D2-Read":"1", "Host":"127.0.0.1:8766",
                "Sec-Fetch-Site":"same-origin",
            })
            self.assertEqual(req.go()[0],200)
            self.assertEqual(req.state.calls,[(mint,page)])

    def test_duplicate_unknown_invalid_queries_fail_without_access(self):
        for url in (
            "/api/frank-d2-at-slot?mint="+MINT+"&page=0",
            "/api/frank-d2-at-slot?mint="+MINT+"&mint="+MINT,
            "/api/frank-d2-at-slot?page=-1",
            "/api/frank-d2-at-slot?page=1000",
            "/api/frank-d2-at-slot?page=abc",
            "/api/frank-d2-at-slot?mint=BAD",
            "/api/frank-d2-at-slot?extra=1",
            "/api/frank-d2-at-slot?page=",
            "/api/frank-d2-at-slot?x=1&x=2&x=3",
        ):
            req=Request(url,headers={
                "X-Frank-D2-Read":"1","Host":"127.0.0.1:8766"})
            self.assertEqual(req.go()[0],400,url)
            self.assertEqual(req.state.calls,[],url)

    def test_actual_handler_http_payload_only_exposes_scalar_coverage(self):
        # Real handler route, real disk-backed synthetic source, no socket or RPC.
        with tempfile.TemporaryDirectory(prefix="frank-d2-http-") as tmp:
            root=Path(tmp)
            root.chmod(0o700)
            src=root/SOURCE_NAME
            doc=build_d2_document_from_verified_pr60_replay(source())
            src.write_text(json.dumps(doc),encoding="utf-8")
            src.chmod(0o600)

            class DiskState:
                def frank_d2_at_slot(self,*,mint=None,page=0):
                    return query_d2(root,mint=mint,page=page)

            req=Request("/api/frank-d2-at-slot?page=0",headers={
                "X-Frank-D2-Read":"1", "Host":"127.0.0.1:8766",
                "Sec-Fetch-Site":"same-origin"})
            req.state=DiskState()
            status,body=req.go()
            self.assertEqual(status,200)
            self.assertEqual(len(body["rows"]),3)
            self.assertEqual([set(c) for c in body["program_coverage"]],
                             [{"program_id","slot","account_count"}]*2)
            self.assertNotIn("token_accounts",json.dumps(body))
            self.assertNotIn("accounts",json.dumps(body["program_coverage"]))

    def test_non_loopback_host_gate_runs_before_d2_source(self):
        req=Request("/api/frank-d2-at-slot?page=0",headers={
            "X-Frank-D2-Read":"1","Host":"evil.example"},host_ok=False)
        self.assertEqual(req.go()[0],421)
        self.assertEqual(req.state.calls,[])


if __name__ == "__main__":
    unittest.main()
