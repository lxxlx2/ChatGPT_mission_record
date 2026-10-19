#!/usr/bin/env python3
"""Bounded local Mac comparison of Frank /api/decisions direct versus QA proxy.

Existing localhost HTTP GET only. Do not save decision bodies, wallet addresses,
emails, or production SQLite. Stage a private metrics-only ZIP in Downloads,
atomically publish it and reveal in Finder; never upload it automatically.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPException
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
from uuid import uuid4
import zipfile

from frank_pr101_safari_evidence import discover_dashboard_port, make_handler

SOURCE = "/api/decisions"
MAX_CAPTURE = 4_000_001
PROXY_CAP = 4_000_000
PROXY_SECONDS = 3.0


def request_metadata(port: int, path: str = SOURCE, timeout: float = 8.0) -> dict:
    """GET bytes only to determine length; never retain response body."""
    start = time.monotonic()
    connection = HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request("GET", path, headers={"Accept": "application/json"})
        response = connection.getresponse()
        body = response.read(MAX_CAPTURE)
        mime = (response.getheader("Content-Type") or "").split(";", 1)[0].lower().strip()
        content_length = response.getheader("Content-Length")
        result = {
            "status": response.status,
            "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
            "content_type": mime,
            "declared_bytes": int(content_length) if content_length and content_length.isdecimal() else None,
            "bytes_read": len(body),
            "read_cap_reached": len(body) >= MAX_CAPTURE,
        }
        if response.status == 503 and mime == "text/html":
            # Only whitelist fixed QA proxy error codes. Never save HTTP
            # response text, decisions data or arbitrary HTML.
            for reason in (
                "LOCAL_API_OVERSIZED", "LOCAL_API_SOURCE_UNAVAILABLE",
                "LOCAL_API_NOT_JSON", "LOCAL_API_UNAVAILABLE",
            ):
                if reason.encode("ascii") in body[:8192]:
                    result["qa_proxy_failure_code"] = reason
                    break
        return result
    except (OSError, TimeoutError, HTTPException, ValueError) as exc:
        return {
            "status": "TRANSPORT_ERROR",
            "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
            "error_class": type(exc).__name__,
        }
    finally:
        connection.close()


def sample_pair(direct_port: int, proxy_port: int, index: int, reader=request_metadata) -> dict:
    # Alternate order so a periodic heavy refresh cannot always penalize
    # whichever endpoint is requested second.
    order = ("direct", "proxy") if index % 2 == 0 else ("proxy", "direct")
    results = {}
    ports = {"direct": direct_port, "proxy": proxy_port}
    for name in order:
        results[name] = reader(ports[name])
    return {"sample": index + 1, "utc": datetime.now(timezone.utc).isoformat(),
            "order": list(order), **results}


def classify_samples(samples: list[dict]) -> dict:
    if not samples:
        return {"verdict": "NO_SAMPLES"}
    direct_bad = [s for s in samples if s["direct"].get("status") != 200]
    proxy_bad = [s for s in samples if s["proxy"].get("status") != 200]
    comparisons = [s for s in samples if s["direct"].get("status") == 200
                   and s["proxy"].get("status") == 503]
    oversize = [s for s in comparisons
                if ((s["direct"].get("declared_bytes") or 0) > PROXY_CAP
                    or s["direct"].get("read_cap_reached"))]
    slow = [s for s in comparisons
            if s["direct"].get("elapsed_ms", 0) >= PROXY_SECONDS * 1000]
    proxy_codes = Counter(s["proxy"].get("qa_proxy_failure_code")
                          for s in samples if s["proxy"].get("qa_proxy_failure_code"))
    if direct_bad:
        verdict = "DIRECT_SOURCE_ERROR_OBSERVED"
    elif oversize or proxy_codes.get("LOCAL_API_OVERSIZED"):
        verdict = "PROXY_4MB_LIMIT_PROBABLE"
    elif slow:
        verdict = "PROXY_3S_TIMEOUT_POSSIBLE"
    elif proxy_bad:
        verdict = "PROXY_OR_INTERMITTENT_ERROR_UNRESOLVED"
    else:
        verdict = "NOT_REPRODUCED"
    return {
        "verdict": verdict,
        "sample_count": len(samples),
        "direct_non200_count": len(direct_bad),
        "proxy_non200_count": len(proxy_bad),
        "direct200_proxy503_count": len(comparisons),
        "oversize_suspected_count": len(oversize),
        "slow_source_suspected_count": len(slow),
        "qa_proxy_failure_codes": dict(proxy_codes),
    }


def run_diagnostic(port: int, *, samples: int = 8, spacing: float = 0.25) -> dict:
    if not 1 <= samples <= 20 or not 0 <= spacing <= 2:
        raise ValueError("INVALID_SAMPLING_LIMITS")
    with tempfile.TemporaryDirectory(prefix="frank-decisions-ro-preview-") as directory:
        # Only the actual PR104 GET proxy implementation is under evaluation.
        static = Path(directory)
        handler = make_handler(static, port)
        proxy = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        thread.start()
        try:
            observations = []
            for i in range(samples):
                observations.append(sample_pair(port, proxy.server_port, i))
                d, p = observations[-1]["direct"], observations[-1]["proxy"]
                print(f"DECISIONS_SAMPLE={i+1} DIRECT={d['status']} "
                      f"PROXY={p['status']} D_MS={d['elapsed_ms']} P_MS={p['elapsed_ms']}",
                      flush=True)
                if i + 1 < samples and spacing:
                    time.sleep(spacing)
            report = {
                "kind": "FRANK_DECISIONS_503_READONLY_DIRECT_VS_QA_PROXY",
                "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                "source_endpoint": SOURCE,
                "direct_port": port,
                "qa_proxy_ephemeral_port": proxy.server_port,
                "qa_proxy_timeout_seconds": PROXY_SECONDS,
                "qa_proxy_max_body_bytes": PROXY_CAP,
                "qa_proxy_code_identity": "REPO_SCRIPT_PINNED_BY_CALLER",
                "production_backend_sha": "UNVERIFIED",
                "requests": observations,
                "summary": classify_samples(observations),
                "body_or_decisions_recorded": False,
                "new_rpc": False,
                "production_db_writes": False,
                "new_scans": False,
                "emails_sent": False,
                "trades": False,
                "production_deploy": False,
            }
            return report
        finally:
            proxy.shutdown()
            proxy.server_close()
            thread.join(timeout=3)


def save_evidence(home: Path, report: dict, sha: str) -> Path:
    downloads = home / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    final = downloads / f"frank-decisions-503-diagnostic-{stamp}-{sha[:8]}-{uuid4().hex[:10]}.zip"
    with tempfile.TemporaryDirectory(prefix=".frank-decisions-ro-", dir=downloads) as tmp:
        source = Path(tmp) / "diagnostic.zip"
        with zipfile.ZipFile(source, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("diagnostic.json", json.dumps(report, ensure_ascii=False, indent=2))
        # Atomic and non-overwriting. Never remove a competing final ZIP.
        os.link(source, final)
    return final


def read_git_head_passively(checkout: Path) -> str:
    """Read local Git metadata without running Git, helpers, filters, or index refresh.

    This intentionally verifies only checkout HEAD identity, NOT clean worktree
    bytes. The ephemeral caller checkout must not be represented as fully
    independently verified source content.
    """
    entry = checkout / ".git"
    try:
        if entry.is_dir():
            git_dir = entry
        elif entry.is_file():
            pointer = entry.read_text(encoding="utf-8").strip()
            if not pointer.startswith("gitdir: "):
                raise RuntimeError("DIAGNOSTIC_GITDIR_INVALID")
            target = Path(pointer[len("gitdir: "):].strip())
            git_dir = (target if target.is_absolute() else checkout / target).resolve(strict=True)
        else:
            raise RuntimeError("DIAGNOSTIC_GITDIR_MISSING")
        if not git_dir.is_dir():
            raise RuntimeError("DIAGNOSTIC_GITDIR_INVALID")
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref = head[len("ref: "):].strip()
            if (not re.fullmatch(r"refs/(?:heads|remotes|tags)/[A-Za-z0-9_./-]+", ref)
                    or any(part in {"", ".", ".."} for part in ref.split("/"))):
                raise RuntimeError("DIAGNOSTIC_GIT_REF_INVALID")
            common = git_dir
            commondir = git_dir / "commondir"
            if commondir.is_file():
                relative = commondir.read_text(encoding="utf-8").strip()
                common = (git_dir / relative).resolve(strict=True)
            loose = common / ref
            if loose.is_file():
                head = loose.read_text(encoding="utf-8").strip()
            else:
                packed = common / "packed-refs"
                if not packed.is_file():
                    raise RuntimeError("DIAGNOSTIC_GIT_REF_MISSING")
                matches = [
                    line.split(" ", 1)[0]
                    for line in packed.read_text(encoding="utf-8").splitlines()
                    if line and not line.startswith(("#", "^")) and line.endswith(" " + ref)
                ]
                if len(matches) != 1:
                    raise RuntimeError("DIAGNOSTIC_GIT_REF_MISSING")
                head = matches[0]
        if re.fullmatch(r"[0-9a-f]{40}", head) is None:
            raise RuntimeError("DIAGNOSTIC_GIT_HEAD_INVALID")
        return head
    except (OSError, UnicodeError) as exc:
        raise RuntimeError("DIAGNOSTIC_GIT_METADATA_UNREADABLE") from exc


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--expected-sha", required=True)
    p.add_argument("--samples", type=int, default=8)
    args = p.parse_args()
    if sys.platform != "darwin":
        raise RuntimeError("MACOS_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_sha):
        raise RuntimeError("EXPECTED_SHA_INVALID")
    checkout = Path(__file__).resolve().parents[3]
    actual = read_git_head_passively(checkout)
    if actual != args.expected_sha:
        raise RuntimeError("DIAGNOSTIC_SOURCE_SHA_MISMATCH")
    port = discover_dashboard_port(Path.home())
    report = run_diagnostic(port, samples=args.samples)
    report["diagnostic_checkout_head_sha"] = args.expected_sha
    report["source_identity_scope"] = "PASSIVE_GIT_HEAD_ONLY_WORKTREE_UNVERIFIED"
    final = save_evidence(Path.home(), report, args.expected_sha)
    print("DIAGNOSTIC_STATUS=" + report["summary"]["verdict"])
    print("ZIP_READY=" + str(final), flush=True)
    subprocess.run(["open", "-R", str(final)], timeout=12, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
