#!/usr/bin/env python3
"""Mac Safari F01 / cached C02 acceptance evidence: isolated, GET only.

Clones exactly the externally approved PR101 source to a disposable checkout.
No installation, launchctl, production SQLite access, Gmail, Solana RPC or POST.
Interactive macOS screen-region screenshots are local-only and zipped into
~/Downloads, then Finder reveals and selects the ZIP. Never uploads artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
from http.client import HTTPConnection, HTTPException
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
import zipfile

REPO = "https://github.com/lxxlx2/ChatGPT_mission_record.git"
APPROVED = "e8bc450d836ac46df5224ce7b6fc048ea5720db0"
BRANCH = "feat/frank-f01-current-candidates-history-20261018"
STATIC_REL = "crypto-300-profit-mission/local-agent/mission_agent/mission_control/static"
GET_PATHS = frozenset((
    "/api/runtime", "/api/control-health", "/api/candidates",
    "/api/follow-opportunities", "/api/trades", "/api/decisions",
    "/api/coverage", "/api/review-activity", "/api/frank-observed-watchlist",
    "/api/cluster-latest", "/api/research/current-follow-context",
))
STATIC_FILES = frozenset((
    "index.html", "styles.css", "app.js", "frank_candidate_sections.js",
    "frank_f01_primary_freshness.js", "frank_source_context.js",
    "frank_source_context.css",
))
CAPTURE_STAGES = (
    ("01-current-history", "Safari 顶部当前机会、展开的历史与不可跟候选"),
    ("02-trades-stats", "Safari 的统计数据、Frank 最近买卖"),
    ("03-watchlist", "Safari 的持续观察池、历史和待复核链上行为"),
    ("04-c02-archive", "Safari 的 CA 查询页；可点击“查看已有归档（只读）”，不要点击“开始查询”"),
)

def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def validate_ca(query: str) -> bool:
    if not isinstance(query, str):
        return False
    args = parse_qs(query, strict_parsing=True)
    return (set(args) == {"mint"} and len(args["mint"]) == 1
            and re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", args["mint"][0]) is not None)

def discover_dashboard_port(home: Path) -> int:
    support = home / "Library/Application Support/FrankMeme"
    paths = []
    runner = support / "dashboard.sh"
    if runner.is_file():
        match = re.search(r'^LOCAL_AGENT="([^"]+)"\s*$', runner.read_text(encoding="utf-8"), re.M)
        if match:
            agent = Path(match.group(1)).expanduser()
            paths.append(agent / "mission_agent/mission_control/dashboard.port")
    paths.append(support / "dashboard_port")
    for source in paths:
        if not source.is_file() or source.is_symlink():
            continue
        raw = source.read_text(encoding="ascii").strip()
        if raw.isdecimal() and 1 <= int(raw) <= 65535:
            return int(raw)
    raise RuntimeError("FRANK_LOCAL_DASHBOARD_PORT_UNAVAILABLE")

def verify_local_source(port: int) -> None:
    conn = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        conn.request("GET", "/api/runtime", headers={"Accept":"application/json"})
        response = conn.getresponse()
        if response.status != 200 or "application/json" not in (response.getheader("Content-Type") or ""):
            raise RuntimeError("FRANK_LOCAL_DASHBOARD_GET_UNAVAILABLE")
        if len(response.read(262145)) > 262144:
            raise RuntimeError("FRANK_LOCAL_DASHBOARD_RESPONSE_OVERSIZED")
    finally:
        conn.close()

def exact_review_checkout(destination: Path) -> Path:
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", "--filter=blob:none",
         "--branch", BRANCH, REPO, str(destination)],
        check=True, timeout=180,
    )
    result = subprocess.run(["git", "-C", str(destination), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True, timeout=15)
    actual = result.stdout.strip()
    if actual != APPROVED:
        raise RuntimeError("STOP_REVIEWED_SHA_DRIFT " + actual)
    static = destination / STATIC_REL
    if not static.is_dir() or any(not (static / name).is_file() for name in STATIC_FILES):
        raise RuntimeError("STOP_REVIEWED_STATIC_INCOMPLETE")
    subprocess.run(["git", "-C", str(destination), "checkout", "-q", "--detach", APPROVED],
                   check=True, timeout=15)
    return static

def pinned_candidate_checkout(script_file: Path, expected_sha: str) -> Path:
    """Preview a newer QA product tree only after an explicit exact-SHA request.

    This *never* deploys candidate code. Its review status is not implied.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise RuntimeError("CANDIDATE_SHA_INVALID")
    root = script_file.resolve().parents[3]
    actual = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    if actual != expected_sha:
        raise RuntimeError("CANDIDATE_SHA_MISMATCH")
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                           capture_output=True, text=True, check=True, timeout=15).stdout
    if dirty:
        raise RuntimeError("CANDIDATE_WORKTREE_DIRTY")
    static = root / STATIC_REL
    if not static.is_dir() or any(not (static / name).is_file() for name in STATIC_FILES):
        raise RuntimeError("CANDIDATE_STATIC_INCOMPLETE")
    return static


def verify_git_source(root: Path, expected_sha: str) -> None:
    """Recheck both commit and tracked checkout, even after a long screenshot session."""
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True, timeout=15)
    if result.stdout.strip() != expected_sha:
        raise RuntimeError("STOP_SOURCE_HEAD_CHANGED")
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                            capture_output=True, text=True, check=True, timeout=15)
    if status.stdout.strip():
        raise RuntimeError("STOP_SOURCE_WORKTREE_CHANGED")


def verify_preview_snapshot(static: Path, expected_hashes: dict[str, str]) -> None:
    if set(expected_hashes) != STATIC_FILES:
        raise RuntimeError("STOP_STATIC_IDENTITY_INCOMPLETE")
    for name, digest in expected_hashes.items():
        target = static / name
        if target.is_symlink() or not target.is_file() or sha256_bytes(target.read_bytes()) != digest:
            raise RuntimeError("STOP_STATIC_SNAPSHOT_CHANGED " + name)


def export_exact_git_static(root: Path, expected_sha: str, destination: Path) -> dict[str, str]:
    """Export bytes from the Git object, never serve a mutable checkout."""
    verify_git_source(root, expected_sha)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    hashes = {}
    for name in sorted(STATIC_FILES):
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{expected_sha}:{STATIC_REL}/{name}"],
            capture_output=True, check=True, timeout=30,
        )
        payload = result.stdout
        if not payload:
            raise RuntimeError("STOP_EMPTY_COMMITTED_STATIC_FILE")
        target = destination / name
        target.write_bytes(payload)
        target.chmod(0o400)
        hashes[name] = sha256_bytes(payload)
    verify_preview_snapshot(destination, hashes)
    verify_git_source(root, expected_sha)
    return hashes


def preserve_rejected_screenshots(capture_root: Path, destination: Path,
                                  preview_sha: str, reason: str) -> Path | None:
    """Retain already captured images on a rejected run, no accepted ZIP."""
    source_images = [capture_root / f"{stage}.png" for stage, _ in CAPTURE_STAGES
                     if (capture_root / f"{stage}.png").is_file()]
    if not source_images:
        return None
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    for png in source_images:
        if not png.is_symlink():
            shutil.copy2(png, destination / png.name)
    (destination / "REJECTED.json").write_text(
        json.dumps({"status": "REJECTED_SOURCE_DRIFT_NO_VALID_ATTESTATION",
                    "expected_sha": preview_sha, "reason": reason,
                    "captured_at_utc": datetime.now(timezone.utc).isoformat()},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def make_handler(static: Path, live_port: int):
    class View(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(static), **kwargs)

        def log_message(self, *_args):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_POST(self):
            self.send_error(405, "READ_ONLY_PREVIEW_NO_POST")

        def do_PUT(self):
            self.send_error(405, "READ_ONLY_PREVIEW_NO_PUT")

        def do_GET(self):
            host = self.headers.get("Host", "")
            if host not in {f"127.0.0.1:{self.server.server_port}",
                            f"localhost:{self.server.server_port}"}:
                return self.send_error(421, "LOOPBACK_HOST_REQUIRED")
            parsed = urlsplit(self.path)
            request_path = parsed.path
            if request_path.startswith("/api/"):
                if request_path not in GET_PATHS:
                    return self.send_error(404, "UNAPPROVED_ENDPOINT")
                if request_path == "/api/cluster-latest":
                    if not validate_ca(parsed.query):
                        return self.send_error(400, "EXACT_CA_REQUIRED")
                elif parsed.query:
                    return self.send_error(400, "NO_QUERY_ALLOWED")
                conn = HTTPConnection("127.0.0.1", live_port, timeout=3)
                try:
                    conn.request("GET", self.path, headers={"Accept": "application/json"})
                    response = conn.getresponse()
                    if response.status not in (200, 404, 503):
                        return self.send_error(503, "LOCAL_API_UNAVAILABLE")
                    if "application/json" not in (response.getheader("Content-Type") or ""):
                        return self.send_error(503, "LOCAL_API_NOT_JSON")
                    data = response.read(4_000_001)
                    if len(data) > 4_000_000:
                        return self.send_error(503, "LOCAL_API_OVERSIZED")
                    self.send_response(response.status)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except (OSError, ValueError, HTTPException, TimeoutError):
                    self.send_error(503, "LOCAL_API_SOURCE_UNAVAILABLE")
                finally:
                    conn.close()
                return
            if request_path in ("/", "/index.html"):
                self.path = "/index.html"
            elif request_path.startswith("/static/") and not parsed.query:
                name = request_path[len("/static/"):]
                if name not in STATIC_FILES:
                    return self.send_error(404, "STATIC_FILE_NOT_APPROVED")
                self.path = "/" + name
            else:
                return self.send_error(404, "PREVIEW_STATIC_ONLY")
            super().do_GET()
    return View

def screenshots(capture_root: Path, *, input_fn=input, invoke=subprocess.run) -> list[dict]:
    result = []
    for label, instruction in CAPTURE_STAGES:
        response = input_fn(f"\n{label}: {instruction}\n切换 Safari 到对应内容，按 Enter 框选截图，输入 s 跳过，输入 done 结束: ").strip().lower()
        if response == "done":
            break
        if response == "s":
            continue
        filename = capture_root / f"{label}.png"
        invocation = invoke(["screencapture", "-i", "-x", str(filename)], check=False)
        if invocation.returncode != 0 or not filename.is_file():
            print(f"SKIPPED_SCREENSHOT={label}")
            continue
        payload = filename.read_bytes()
        if not payload.startswith(b"\x89PNG\r\n\x1a\n") or len(payload) < 1024:
            filename.unlink(missing_ok=True)
            print(f"SKIPPED_INVALID_CAPTURE={label}")
            continue
        result.append({"file": filename.name, "bytes": len(payload), "sha256": sha256_bytes(payload),
                       "meaning": instruction})
        print("CAPTURED=" + filename.name)
    return result

def package_evidence(screenshots_dir: Path, out_path: Path, captures: list[dict], static: Path,
                     *, source_port: int, preview_port: int, preview_sha: str = APPROVED,
                     verified_static_hashes: dict[str, str] | None = None) -> Path:
    if verified_static_hashes is not None:
        verify_preview_snapshot(static, verified_static_hashes)
    manifest = {
        "kind": "FRANK_PR101_MAC_SAFARI_MANUAL_EVIDENCE",
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "approved_pr101_base_sha": APPROVED,
        "preview_source_sha": preview_sha,
        "approved_product_sha": preview_sha if preview_sha == APPROVED else None,
        "candidate_source_review_status": "PR101_EXTERNALLY_APPROVED" if preview_sha == APPROVED
            else "CANDIDATE_REQUIRES_SEPARATE_INDEPENDENT_REVIEW",
        "reviewed_static_files_sha256": (dict(verified_static_hashes) if verified_static_hashes is not None
                                         else {name: sha256_bytes((static / name).read_bytes())
                                               for name in sorted(STATIC_FILES)}),
        "capture_method": "macOS interactive screencapture -i -x, chosen regions",
        "screenshot_count": len(captures),
        "screenshots": captures,
        "live_existing_dashboard_port": source_port,
        "isolated_preview_port": preview_port,
        "proxy_get_only": True,
        "new_rpc": False,
        "production_sqlite_modified": False,
        "emails_sent": False,
        "trades_issued": False,
        "production_deployment": False,
        "mac_safari_visual_confirmation_by_user": "PENDING_USER_REVIEW",
        "local_index_is_complete_chain": False,
        "screenshot_contents_private": True,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        raise RuntimeError("EVIDENCE_ARCHIVE_ALREADY_EXISTS")
    with zipfile.ZipFile(out_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        zipf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for row in captures:
            zipf.write(screenshots_dir / row["file"], "screenshots/" + row["file"])
    return out_path

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-safari", action="store_true",
                        help="Leave the preview URL printed, useful if Safari is already open")
    parser.add_argument("--candidate-sha",
                        help="Explicit SHA of a newer candidate source tree from this script's clean Git checkout; isolated QA only")
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("STOP: macOS Safari capture only")
    if not shutil.which("screencapture") or not shutil.which("open"):
        raise SystemExit("STOP: macOS screenshot or Finder tool unavailable")
    source_port = discover_dashboard_port(Path.home())
    verify_local_source(source_port)
    with tempfile.TemporaryDirectory(prefix="frank-pr101-safari-evidence-") as tmp:
        work = Path(tmp)
        if args.candidate_sha:
            candidate_static = pinned_candidate_checkout(Path(__file__), args.candidate_sha)
            checkout_root = candidate_static.parents[4]
            preview_sha = args.candidate_sha
        else:
            approved_static = exact_review_checkout(work / "approved")
            checkout_root = approved_static.parents[4]
            preview_sha = APPROVED
        static = work / "immutable-committed-static"
        committed_hashes = export_exact_git_static(checkout_root, preview_sha, static)
        screenshots_dir = work / "screenshots"
        screenshots_dir.mkdir(mode=0o700)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(static, source_port))
        port = server.server_port
        url = f"http://127.0.0.1:{port}/#signals"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            print(f"PR101_APPROVED_BASE_SHA={APPROVED}")
            print(f"PREVIEW_SOURCE_SHA={preview_sha}")
            print("REVIEW_SCOPE=" + ("PR101_APPROVED" if preview_sha == APPROVED
                  else "QA_CANDIDATE_NOT_PRODUCTION_APPROVED"))
            print("GET_ONLY=YES; NEW_RPC=NO; POST=BLOCKED; NO_DEPLOY=YES")
            print("SAFARI_PREVIEW_URL=" + url)
            if not args.skip_safari:
                subprocess.run(["open", "-a", "Safari", url], check=False)
            captured = screenshots(screenshots_dir)
            if not captured:
                print("NO_SCREENSHOT_CAPTURED; NO_ZIP_CREATED")
                return 2
            stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
            archive = Path.home() / "Downloads" / f"frank-pr101-safari-evidence-{stamp}-{preview_sha[:8]}.zip"
            archive_created = False
            try:
                verify_git_source(checkout_root, preview_sha)
                verify_preview_snapshot(static, committed_hashes)
                package_evidence(
                    screenshots_dir, archive, captured, static,
                    source_port=source_port, preview_port=port,
                    preview_sha=preview_sha, verified_static_hashes=committed_hashes,
                )
                archive_created = True
                verify_git_source(checkout_root, preview_sha)
                verify_preview_snapshot(static, committed_hashes)
            except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
                if archive_created:
                    archive.unlink(missing_ok=True)
                rejected = Path.home() / "Downloads" / (
                    f"frank-pr101-REJECTED-source-drift-{stamp}-{preview_sha[:8]}")
                preserved = preserve_rejected_screenshots(
                    screenshots_dir, rejected, preview_sha, type(exc).__name__ + ": " + str(exc))
                print("STOP_EVIDENCE_REJECTED_SOURCE_DRIFT=" + str(exc))
                if preserved is not None:
                    print("REJECTED_SCREENSHOTS_PRESERVED=" + str(preserved))
                    subprocess.run(["open", "-R", str(preserved)], check=False)
                return 3
            print("EVIDENCE_ZIP=" + str(archive))
            print("SCREENSHOT_COUNT=" + str(len(captured)))
            subprocess.run(["open", "-R", str(archive)], check=False)
            print("FINDER_REVEAL_REQUESTED=YES; NOT_UPLOADED=YES")
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

if __name__ == "__main__":
    raise SystemExit(main())
