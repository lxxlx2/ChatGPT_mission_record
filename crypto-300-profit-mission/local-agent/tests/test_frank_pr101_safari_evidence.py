"""Mac Safari evidence capture module: hermetic tests, no Safari or network."""
from __future__ import annotations
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import zipfile

MODULE = Path(__file__).resolve().parents[1] / "scripts/frank_pr101_safari_evidence.py"
spec = importlib.util.spec_from_file_location("frank_pr101_safari_evidence", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


@contextmanager
def server(handler):
    s = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=s.serve_forever, daemon=True)
    thread.start()
    try:
        yield s
    finally:
        s.shutdown()
        s.server_close()
        thread.join(timeout=3)


class FakeExistingDashboard(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/cluster-latest?mint="):
            body = json.dumps({"mint": USDC, "execution_quote_30_usdc": {"status": "OK"}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def log_message(self, *_):
        pass


def request(s, method, path, host=None):
    c = HTTPConnection("127.0.0.1", s.server_port, timeout=3)
    try:
        c.request(method, path, headers={"Host": host or f"127.0.0.1:{s.server_port}"})
        r = c.getresponse()
        return r.status, r.read()
    finally:
        c.close()


def test_mac_source_sha_pin_and_exact_ca_validation():
    assert module.APPROVED == "e8bc450d836ac46df5224ce7b6fc048ea5720db0"
    assert module.validate_ca("mint=" + USDC)
    for q in ("mint=bad", "mint=" + USDC + "&mint=" + USDC,
              "mint=" + USDC + "&rpc=https://attacker.invalid", ""):
        assert not module.validate_ca(q)
    assert "/api/cluster-analysis" not in module.GET_PATHS


def test_isolated_get_proxy_blocks_every_post_and_other_api():
    with tempfile.TemporaryDirectory() as temp:
        static = Path(temp)
        (static / "index.html").write_text("FRANK STATIC REVIEW", encoding="utf-8")
        (static / "app.js").write_text("/* mock */", encoding="utf-8")
        with server(FakeExistingDashboard) as existing:
            with server(module.make_handler(static, existing.server_port)) as preview:
                status, data = request(preview, "GET", "/")
                assert status == 200 and b"FRANK STATIC REVIEW" in data
                assert request(preview, "GET", "/static/app.js")[0] == 200
                assert request(preview, "POST", "/api/cluster-analysis")[0] == 405
                assert request(preview, "GET", "/api/cluster-analysis")[0] == 404
                assert request(preview, "GET", "/static/../../.env")[0] == 404
                assert request(preview, "GET", "/api/cluster-latest?mint=bad")[0] == 400
                assert request(preview, "GET", "/api/cluster-latest?mint=" + USDC + "&x=1")[0] == 400
                assert request(preview, "GET", "/api/runtime?x=1")[0] == 400
                assert request(preview, "GET", "/", host="evil.example")[0] == 421
                status, raw = request(preview, "GET", "/api/cluster-latest?mint=" + USDC)
                assert status == 200 and json.loads(raw)["mint"] == USDC


def test_zip_contains_only_local_screenshots_and_sha256_manifest():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        static = root / "static"
        static.mkdir()
        for name in module.STATIC_FILES:
            (static / name).write_text("pinned test " + name, encoding="utf-8")
        pics = root / "captures"
        pics.mkdir()
        png = b"\x89PNG\r\n\x1a\n" + bytes(1600)
        (pics / "01-current-history.png").write_bytes(png)
        captured = [{"file": "01-current-history.png", "bytes": len(png),
                     "sha256": hashlib.sha256(png).hexdigest(),
                     "meaning": "UI acceptance demo"}]
        archive = root / "frank-pr101-safari-evidence-test.zip"
        module.package_evidence(pics, archive, captured, static,
                                source_port=8765, preview_port=49152)
        with zipfile.ZipFile(archive) as z:
            assert sorted(z.namelist()) == [
                "manifest.json", "screenshots/01-current-history.png"
            ]
            manifest = json.loads(z.read("manifest.json"))
            assert manifest["approved_product_sha"] == module.APPROVED
            assert manifest["screenshots"][0]["sha256"] == captured[0]["sha256"]
            assert len(manifest["reviewed_static_files_sha256"]) == len(module.STATIC_FILES)
            assert manifest["new_rpc"] is False
            assert manifest["production_deployment"] is False
            assert manifest["screenshot_count"] == 1
            assert z.read("screenshots/01-current-history.png") == png
        candidate_zip = root / "frank-c02-unreviewed-sandbox.zip"
        candidate_sha = "f" * 40
        module.package_evidence(pics, candidate_zip, captured, static,
                                source_port=8765, preview_port=49153, preview_sha=candidate_sha)
        with zipfile.ZipFile(candidate_zip) as candidate:
            m = json.loads(candidate.read("manifest.json"))
            assert m["preview_source_sha"] == candidate_sha
            assert m["approved_pr101_base_sha"] == module.APPROVED
            assert m["approved_product_sha"] is None
            assert m["candidate_source_review_status"] == "CANDIDATE_REQUIRES_SEPARATE_INDEPENDENT_REVIEW"

        try:
            module.package_evidence(pics, archive, captured, static,
                                    source_port=8765, preview_port=49152)
        except RuntimeError as exc:
            assert str(exc) == "EVIDENCE_ARCHIVE_ALREADY_EXISTS"
        else:
            raise AssertionError("archive must refuse overwrite")


def test_screenshot_cancel_does_not_create_fabricated_png():
    with tempfile.TemporaryDirectory() as temp:
        class Skipped:
            returncode = 1
        calls = []
        def fake_capture(cmd, check):
            calls.append(cmd)
            return Skipped()
        values = iter(["", "done"])
        result = module.screenshots(Path(temp), input_fn=lambda _p: next(values),
                                    invoke=fake_capture)
        assert result == [] and len(calls) == 1
        assert not list(Path(temp).iterdir())
