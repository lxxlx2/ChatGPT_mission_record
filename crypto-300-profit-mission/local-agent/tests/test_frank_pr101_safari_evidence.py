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


def test_git_snapshot_is_from_exact_commit_and_checkout_drift_fails(tmp_path):
    import subprocess
    root = tmp_path / "repo"
    root.mkdir()
    static = root / module.STATIC_REL
    static.mkdir(parents=True)
    script = root / "crypto-300-profit-mission/local-agent/scripts" / "screenshot.py"
    script.parent.mkdir(parents=True)
    script.write_text("fixed script", encoding="utf-8")
    for name in module.STATIC_FILES:
        (static / name).write_text("PRIOR " + name, encoding="utf-8")
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    git("init", "-q")
    git("config", "user.email", "qa@example.invalid")
    git("config", "user.name", "QA fixture")
    git("add", ".")
    git("commit", "-qm", "historical source")
    parent = git("rev-parse", "HEAD")
    (static / "index.html").write_text("CANDIDATE PAGE", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "candidate source")
    candidate = git("rev-parse", "HEAD")
    assert module.pinned_candidate_checkout(script, candidate) == static

    snapshot = tmp_path / "snapshot"
    hashes = module.export_exact_git_static(root, candidate, snapshot)
    assert (snapshot / "index.html").read_text() == "CANDIDATE PAGE"
    with server(module.make_handler(snapshot, 8765)) as preview:
        assert b"CANDIDATE PAGE" in request(preview, "GET", "/")[1]
        (static / "index.html").write_text("TAMPERED TRACKED", encoding="utf-8")
        assert b"CANDIDATE PAGE" in request(preview, "GET", "/")[1]
        assert b"TAMPERED" not in request(preview, "GET", "/")[1]
        try:
            module.verify_git_source(root, candidate)
        except RuntimeError as exc:
            assert str(exc) == "STOP_SOURCE_WORKTREE_CHANGED"
        else:
            raise AssertionError("source mutation must be rejected")
        git("reset", "--hard", parent)
        assert git("status", "--porcelain") == ""
        assert b"CANDIDATE PAGE" in request(preview, "GET", "/")[1]
        try:
            module.verify_git_source(root, candidate)
        except RuntimeError as exc:
            assert str(exc) == "STOP_SOURCE_HEAD_CHANGED"
        else:
            raise AssertionError("clean HEAD switch must be rejected")
        module.verify_preview_snapshot(snapshot, hashes)

    (snapshot / "index.html").chmod(0o600)
    (snapshot / "index.html").write_text("ALTERED SNAPSHOT", encoding="utf-8")
    try:
        module.verify_preview_snapshot(snapshot, hashes)
    except RuntimeError as exc:
        assert "STOP_STATIC_SNAPSHOT_CHANGED" in str(exc)
    else:
        raise AssertionError("preview snapshot mutation must be rejected")


def test_main_rejects_both_mid_capture_drifts_preserves_images_and_no_accepted_zip(
        tmp_path, monkeypatch):
    import subprocess
    import sys
    from types import SimpleNamespace
    base_run = subprocess.run
    original_platform = sys.platform
    png = b"\x89PNG\r\n\x1a\n" + bytes(1600)
    home = tmp_path / "home"
    downloads = home / "Downloads"
    downloads.mkdir(parents=True)
    monkeypatch.setattr(module.Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr(module.sys, "platform", "darwin")
    monkeypatch.setattr(module.shutil, "which", lambda name: "/mock/" + name)

    for mode in ("dirty_tracked", "clean_head_switch"):
        root = tmp_path / mode / "repo"
        root.mkdir(parents=True)
        static = root / module.STATIC_REL
        static.mkdir(parents=True)
        script = root / "crypto-300-profit-mission/local-agent/scripts" / "screenshot.py"
        script.parent.mkdir(parents=True)
        script.write_text("qa script", encoding="utf-8")
        for name in module.STATIC_FILES:
            (static / name).write_text("PARENT " + name, encoding="utf-8")
        def git(*args):
            return base_run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, check=True).stdout.strip()
        git("init", "-q")
        git("config", "user.email", "qa@example.invalid")
        git("config", "user.name", "QA")
        git("add", ".")
        git("commit", "-qm", "old")
        parent = git("rev-parse", "HEAD")
        (static / "index.html").write_text("FIXED CANDIDATE " + mode, encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "reviewed candidate")
        candidate = git("rev-parse", "HEAD")
        assert git("status", "--porcelain") == ""
        active = {}
        class RecordingServer(ThreadingHTTPServer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                active["server"] = self
        def fake_run(cmd, *args, **kwargs):
            if cmd[0] == "open":
                return SimpleNamespace(returncode=0)
            return base_run(cmd, *args, **kwargs)
        def fake_screenshots(capture_root):
            sock = active["server"]
            status, first = request(sock, "GET", "/")
            assert status == 200 and b"FIXED CANDIDATE" in first
            if mode == "dirty_tracked":
                (static / "index.html").write_text("MUTATED LIVE WORKTREE", encoding="utf-8")
            else:
                git("reset", "--hard", parent)
                assert git("status", "--porcelain") == ""
            status, after = request(sock, "GET", "/")
            assert status == 200 and after == first, "preview must use pinned Git snapshot"
            picture = capture_root / "01-current-history.png"
            picture.write_bytes(png)
            return [{"file": picture.name, "bytes": len(png),
                     "sha256": hashlib.sha256(png).hexdigest(),
                     "meaning": "synthetic drift test; not Safari evidence"}]
        with monkeypatch.context() as case:
            case.setattr(module, "__file__", str(script))
            case.setattr(module, "discover_dashboard_port", lambda _home: 8765)
            case.setattr(module, "verify_local_source", lambda _port: None)
            case.setattr(module, "screenshots", fake_screenshots)
            case.setattr(module, "ThreadingHTTPServer", RecordingServer)
            case.setattr(module.subprocess, "run", fake_run)
            case.setattr(module.sys, "argv", ["screenshot.py", "--skip-safari",
                                             "--candidate-sha", candidate])
            assert module.main() == 3, "must never report successful evidence after source drift"
        assert not list(downloads.glob("*.zip"))
        rejected = list(downloads.glob("frank-pr101-REJECTED-source-drift-*"))
        assert len(rejected) > 0
        matching = [p for p in rejected if p.name.endswith(candidate[:8])]
        assert len(matching) == 1
        assert (matching[0] / "01-current-history.png").read_bytes() == png
        rejection = json.loads((matching[0] / "REJECTED.json").read_text())
        assert rejection["status"] == "REJECTED_SOURCE_DRIFT_NO_VALID_ATTESTATION"
        assert rejection["expected_sha"] == candidate
        assert "HEAD" in rejection["reason"] or "WORKTREE" in rejection["reason"]
    assert sys.platform == "darwin"
