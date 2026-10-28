"""No genuine sockets: exercise physical once launch gates and original RID path."""
from datetime import datetime, timedelta, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from f0_l2_d1_physical_once import (
    _LiveOnceChildPermit, main, run_owner_approved_once, _sync_exclusive_marker)
from f0_l2_d1_physical_foreground_scope import (
    check_physical_foreground_scope, METHODS, ENDPOINT, SCHEMA)
from f0_l2_d1_coordinator import FakeSource, _run_single_shared_coordinator
from f0_l2_d1_physical_source_candidate import (
    BoundedPhysicalReadOnlySource, _UNRELEASED_SOURCE_CODE_SEAL)
from f0_l2_d1_recovery import reconcile_saved_attempts
from f0_l1_http_wire import MAX_BODY_BYTES

SHA = "a" * 40


def scope():
    now=datetime.now(timezone.utc)
    return dict(
        schema=SCHEMA,approved_commit_sha=SHA,
        grant_id="owner-manual-20261028-001",
        endpoint=ENDPOINT,methods=list(METHODS),anchor_initial_head=True,
        max_total=6,max_blocks=2,max_refreshes=1,slots=3,spacing_ms=250,
        head_ttl_ms=4000,head_min_poll_age_ms=250,window_ms=5000,
        timeout_ms=2000,max_body_bytes=MAX_BODY_BYTES,hard_seconds=10,
        window_start_utc=(now-timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        window_end_utc=(now+timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"))


class OncePhysicalForegroundTests(unittest.TestCase):
    def test_no_implicit_entry_or_network_or_child(self):
        with (patch("socket.create_connection",
                    side_effect=AssertionError("TCP_FORBIDDEN")) as tcp,
              patch("socket.getaddrinfo",
                    side_effect=AssertionError("DNS_FORBIDDEN")) as dns,
              patch("subprocess.Popen",
                    side_effect=AssertionError("CHILD_FORBIDDEN")) as spawn):
            with self.assertRaisesRegex(ValueError,"NO_IMPLICIT_LIVE_ENTRY"):
                main(["runner"])
            with self.assertRaisesRegex(ValueError,"NO_IMPLICIT_LIVE_ENTRY"):
                main(["runner","--execute-live"])
            dns.assert_not_called()
            tcp.assert_not_called()
            spawn.assert_not_called()

    def test_scope_check_deterministic_clock_injection(self):
        d=scope()
        raw=json.dumps(d,sort_keys=True).encode()
        fixed=datetime.fromisoformat(
            d["window_start_utc"].replace("Z","+00:00"))+timedelta(seconds=3)
        ok=check_physical_foreground_scope(
            raw,independently_reviewed_sha=SHA,clock=lambda:fixed)
        self.assertFalse(ok["real_rpc_permitted"])
        with self.assertRaisesRegex(ValueError,"CLOCK_INVALID"):
            check_physical_foreground_scope(
                raw,independently_reviewed_sha=SHA,clock=lambda:None)
        with self.assertRaisesRegex(ValueError,"UTC_DENIED"):
            check_physical_foreground_scope(
                raw,independently_reviewed_sha=SHA,
                clock=lambda:fixed+timedelta(hours=2))

    def make_marker(self, base):
        reg=Path(base).resolve()/"registry"
        reg.mkdir(mode=0o700)
        grant="reproducible-grant-123"
        grant_sha=hashlib.sha256(grant.encode()).hexdigest()
        data={"grant_id_sha256":grant_sha,"permit_sha256":"a"*64,
              "outcome":"CONSUMED_OR_UNKNOWN"}
        p=reg/(grant_sha+".consumed.json")
        _sync_exclusive_marker(
            reg,p.name,(json.dumps(data,sort_keys=True)+"\n").encode())
        return p,grant_sha

    def test_once_marker_is_exclusive_process_bound_and_monotonic(self):
        with tempfile.TemporaryDirectory() as td:
            p,ident=self.make_marker(td)
            token=_LiveOnceChildPermit(p,ident,time.monotonic()+4)
            self.assertTrue(token.valid())
            with self.assertRaises(FileExistsError):
                _sync_exclusive_marker(
                    p.parent,p.name,b"SECOND_RUN_FORBIDDEN")
            self.assertTrue(token.valid())
            expired=_LiveOnceChildPermit(p,ident,time.monotonic()-1)
            self.assertFalse(expired.valid())
            wrong=_LiveOnceChildPermit(p,"b"*64,time.monotonic()+4)
            self.assertFalse(wrong.valid())

    def test_invalid_confirmation_refused_before_marker_and_spawn(self):
        d=scope()
        raw=json.dumps(d,sort_keys=True).encode()
        with tempfile.TemporaryDirectory() as td:
            p=Path(td).resolve()/"scope.json"
            p.write_bytes(raw)
            p.chmod(0o600)
            with (patch("f0_l2_d1_physical_once._same_reviewed_checkout",
                        return_value=SHA),
                  patch("f0_l2_d1_physical_once._private_root",
                        side_effect=AssertionError("REGISTRY_FORBIDDEN")) as root,
                  patch("subprocess.Popen",
                        side_effect=AssertionError("SPAWN_FORBIDDEN")) as spawn,
                  patch("socket.getaddrinfo",
                        side_effect=AssertionError("DNS_FORBIDDEN")) as dns):
                with self.assertRaisesRegex(
                        ValueError,"EXPLICIT_ONE_RUN_CONFIRMATION_REQUIRED"):
                    run_owner_approved_once(p,SHA,"NO_USER_AUTHORIZATION")
                root.assert_not_called()
                spawn.assert_not_called()
                dns.assert_not_called()

    def test_real_run_requires_owner_private_scope_file(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td).resolve()/"scope.json"
            p.write_text(json.dumps(scope()))
            p.chmod(0o644)
            with self.assertRaisesRegex(ValueError,"SCOPE_NOT_PRIVATE"):
                run_owner_approved_once(p,SHA,"WRONG")

    def test_real_source_without_child_marker_remains_blocked(self):
        a=(datetime.now(timezone.utc)-timedelta(seconds=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        b=(datetime.now(timezone.utc)+timedelta(seconds=15)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        with tempfile.TemporaryDirectory() as td:
            p,ident=self.make_marker(td)
            expired=_LiveOnceChildPermit(p,ident,time.monotonic()-1)
            with self.assertRaisesRegex(ValueError,"ONCE_CHILD_PERMIT_INVALID"):
                BoundedPhysicalReadOnlySource(
                    a,b,_unreleased_review_seal=_UNRELEASED_SOURCE_CODE_SEAL,
                    _runtime_permit=expired)

    def test_true_runtime_coordinator_under_fake_tls_no_sockets(self):
        with tempfile.TemporaryDirectory() as td:
            evidence=Path(td).resolve()/"evidence"
            evidence.mkdir(mode=0o700)
            marker,ident=self.make_marker(td)
            token=_LiveOnceChildPermit(marker,ident,time.monotonic()+9)
            now=datetime.now(timezone.utc)
            source=BoundedPhysicalReadOnlySource(
                (now-timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                (now+timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                _unreleased_review_seal=_UNRELEASED_SOURCE_CODE_SEAL,
                _runtime_permit=token)
            fake=FakeSource(first_head=1000,growth_bps=15.0,delay_ms=0)
            posts=[]

            class Response:
                def __init__(self, response):
                    self.status,head,self.body=response
                    self.head=list(head.items())
                def getheaders(self):
                    return self.head
                def read(self,n):
                    return self.body[:n]

            class Connection:
                def __init__(self,*args,**kwargs):
                    self.sock=None
                    self.payload=None
                def connect(self):
                    self.sock=object()
                def request(self,method,path,*,body,headers):
                    assert method=="POST" and path=="/"
                    self.payload=json.loads(body)
                    rows=[json.loads(x) for x in
                          (evidence/"attempts.jsonl").read_text().splitlines()]
                    assert any(e["event"]=="RESERVE_UNKNOWN"
                               and e["id"]==self.payload["id"] for e in rows)
                    posts.append(self.payload["id"])
                def getresponse(self):
                    return Response(FakeSource.reply(fake,self.payload))
                def close(self):
                    self.sock=None

            with (patch("http.client.HTTPSConnection",
                        side_effect=Connection) as fake_ctor,
                  patch("f0_l2_d1_concrete_https._ORIGINAL_HTTPS_CONNECTION",
                        new=fake_ctor),
                  patch("socket.create_connection",
                        side_effect=AssertionError("TCP_FORBIDDEN")) as tcp,
                  patch("socket.getaddrinfo",
                        side_effect=AssertionError("DNS_FORBIDDEN")) as dns):
                r=_run_single_shared_coordinator(
                    source,evidence,max_total=6,max_blocks=2,
                    max_refreshes=1,spacing_ms=250,slots=3,
                    head_ttl_ms=4000,window_ms=5000,
                    max_block_response_ms=2000,
                    head_min_poll_age_ms=250,
                    anchor_initial_head=True,_physical_source_candidate=True,
                    _real_foreground_permit=token)
                tcp.assert_not_called()
                dns.assert_not_called()
            self.assertEqual(r["mode"],
                             "F0_ONCE_FOREGROUND_GENUINE_HTTPS_READ_ONLY")
            self.assertGreaterEqual(r["network_requests"],3)
            self.assertEqual(r["network_requests"],len(posts))
            self.assertEqual(r["physical_post_attempted_count"],len(posts))
            self.assertTrue(r["physical_source_released"])
            self.assertTrue(r["real_user_grant_active"])
            self.assertEqual(r["initial_anchor_attempts"],1)
            audit=reconcile_saved_attempts(evidence)
            self.assertEqual(audit["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")
            self.assertEqual(audit["verified_initial_parent_links"],1)
            self.assertEqual(audit["unknown_request_ids"],[])

    def test_cannot_claim_genuine_mode_with_missing_runtime_token(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td).resolve()/"evidence"
            output.mkdir(mode=0o700)
            now=datetime.now(timezone.utc)
            source=BoundedPhysicalReadOnlySource(
                (now-timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                (now+timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                _unreleased_review_seal=_UNRELEASED_SOURCE_CODE_SEAL)
            with patch("socket.create_connection",
                       side_effect=AssertionError("TCP_FORBIDDEN")) as tcp:
                with self.assertRaisesRegex(
                        ValueError,"OWNER_ONCE_PERMIT_REQUIRED"):
                    _run_single_shared_coordinator(
                        source,output,_physical_source_candidate=True,
                        anchor_initial_head=True)
                tcp.assert_not_called()
            self.assertEqual(list(output.iterdir()),[])


if __name__=="__main__":
    unittest.main()
