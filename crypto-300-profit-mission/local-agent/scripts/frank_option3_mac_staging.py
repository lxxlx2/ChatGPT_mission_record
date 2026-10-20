"""Frank Option 3 Mac acceptance: loopback snapshot-only UI at a new port.

The only external input is fixed, one-time localhost GET from the existing
Frank dashboard. All staged HTTP APIs replay in-memory snapshots. There are
no DB paths, RPC clients, quote clients, email senders, OS notifications,
launchd changes, Git writes or production POST forwarding in this program.

This QA helper is intentionally outside the independently reviewed PR #146.
The reviewed application files must remain exactly equal to the pinned SHA.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PINNED = "72cf75c61fdb220a01b98df0abe81ebc5d248fd4"
LOCAL_AGENT = Path(__file__).resolve().parents[1]
REPO = LOCAL_AGENT.parents[1]
STATIC = LOCAL_AGENT / "mission_agent" / "mission_control" / "static"
ALLOWED_DELTAS = (
    "crypto-300-profit-mission/local-agent/scripts/frank_option3_mac_staging.py",
    "crypto-300-profit-mission/local-agent/scripts/frank_option3_p4_history.py",
)
SOURCE_PORT = 8766
MAX_BYTES = 6_000_000

sys.path.insert(0, str(LOCAL_AGENT))
from mission_agent.mission_control.intelligence_preview import (  # noqa: E402
    analyze_rows, fake_intelligence_updates,
)
from frank_option3_p4_history import run_replay  # noqa: E402

SOURCE_PATHS = (
    "/api/runtime", "/api/control-health", "/api/candidates",
    "/api/trades", "/api/coverage", "/api/frank-observed-watchlist",
    "/api/review-activity", "/api/decisions",
)
OPTIONAL_D1 = (
    "/api/frank-signed-activity?days=1",
    "/api/frank-signed-activity?days=7",
)
BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,88}$")


def check_frozen_source() -> None:
    base = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--verify", PINNED + "^{commit}"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if base != PINNED:
        raise RuntimeError("REVIEWED_PARENT_SHA_NOT_FOUND")
    diff = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", PINNED, "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    if sorted(diff) != sorted(ALLOWED_DELTAS):
        raise RuntimeError("QA_BRANCH_CONTAINS_UNREVIEWED_APP_CHANGES: " + repr(diff))
    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if status:
        raise RuntimeError("STAGING_CHECKOUT_NOT_CLEAN")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)


def capture(endpoint: str) -> Any:
    url = "http://127.0.0.1:" + str(SOURCE_PORT) + endpoint
    req = urllib.request.Request(url, method="GET")
    with OPENER.open(req, timeout=8) as response:
        if response.status != 200:
            raise RuntimeError("UNEXPECTED_SOURCE_HTTP_STATUS")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise RuntimeError("SOURCE_REPLY_EXCEEDS_BOUND")
        return json.loads(raw)


def capture_inputs() -> tuple[dict[str, Any], float]:
    out: dict[str, Any] = {}
    for endpoint in SOURCE_PATHS:
        out[endpoint] = capture(endpoint)
    for endpoint in OPTIONAL_D1:
        try:
            out[endpoint] = capture(endpoint)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            out[endpoint] = {
                "status": "UNAVAILABLE",
                "reason": "OLD_RELEASE_D1_ENDPOINT_NOT_PRESENT",
                "scope": "OLDER_RUNTIME_LOCAL_INDEX_ONLY",
                "rows": [],
                "signatures": None,
            }
    if not isinstance(out["/api/candidates"], list):
        raise RuntimeError("CANDIDATES_NOT_LIST")
    if not isinstance(out["/api/trades"], list):
        raise RuntimeError("TRADES_NOT_LIST")
    as_of = time.time()
    return out, as_of


def evidence_summary(captured: dict[str, Any]) -> dict[str, Any]:
    trades = captured["/api/trades"]
    candidates = captured["/api/candidates"]
    coverage = captured["/api/coverage"]
    runtime = captured["/api/runtime"]
    unique = {}
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        signature = trade.get("signature")
        mint = trade.get("mint")
        if (isinstance(signature, str) and BASE58.fullmatch(signature)
                and isinstance(mint, str) and BASE58.fullmatch(mint)):
            unique.setdefault(signature, (mint, trade.get("side")))
    return {
        "source": "OLDER_FRANK_8766_SNAPSHOT_NOT_LIVE",
        "runtime_at_capture": runtime.get("status") if isinstance(runtime, dict) else None,
        "production_db_readable_at_capture": (
            runtime.get("production_db_readable") if isinstance(runtime, dict) else None
        ),
        "source_scope": coverage.get("scope") if isinstance(coverage, dict) else None,
        "source_chain_complete": (
            coverage.get("chain_completeness_verified") if isinstance(coverage, dict) else None
        ),
        "candidates": len(candidates),
        "recent_trades": len(trades),
        "unique_locally_indexed_signatures_in_page": len(unique),
        "distinct_mints_in_page": len({pair[0] for pair in unique.values()}),
        "indexed_trade_sides": dict(Counter(str(pair[1]) for pair in unique.values())),
        "independent_chain_verification": "NOT_PERFORMED",
        "independent_follow_opportunity_count": "UNVERIFIED",
        "mail_or_os_notifications_sent": False,
        "real_trade_authorized": False,
    }


class StageHandler(BaseHTTPRequestHandler):
    snapshots: dict[str, Any] = {}
    intelligence: dict[str, Any] = {}
    p4_replay: dict[str, Any] = {}
    capture_at: float = 0
    port: int = 18766

    def log_message(self, *_args: Any) -> None:
        return

    def _respond(self, code: int, body: bytes, mime: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frank-Mode", "LOCAL_SNAPSHOT_ONLY_NO_SEND")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; connect-src 'self'; "
                         "style-src 'self' 'unsafe-inline'; "
                         "script-src 'self'" + (" 'unsafe-inline'" if self.path == "/qa/p4-replay" else "") + "; "
                         "img-src 'self' data:; object-src 'none'; "
                         "form-action 'none'; frame-ancestors 'none'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, value: Any, status: int = 200) -> None:
        self._respond(status, json.dumps(value, ensure_ascii=False,
                                        default=str).encode("utf-8"),
                      "application/json; charset=utf-8")

    def _allowed_host(self) -> bool:
        return (self.client_address[0] in {"127.0.0.1", "::1"}
                and self.headers.get("Host") in {
                    "127.0.0.1:" + str(self.port),
                    "localhost:" + str(self.port),
                })

    def do_GET(self) -> None:
        if not self._allowed_host():
            self._json({"error": "LOOPBACK_ONLY"}, 421)
            return
        parsed = urllib.parse.urlsplit(self.path)
        path, query = parsed.path, parsed.query
        if path == "/":
            if query:
                self._json({"error": "QUERY_NOT_ALLOWED"}, 400)
                return
            html = (STATIC / "index.html").read_text("utf-8")
            marker = (
                '<div role="alert" style="padding:14px;background:#34313d;'
                'color:white;font-weight:bold">'
                "Frank 方案 3 · 隔离验收 · 历史快照，非实时监控。"
                "此页面仅重放启动时获取的本地数据；刷新不会重新采集。"
                "无真实提醒、报价、RPC、交易、生产变更。"
                "禁止把页面中的旧候选当作实时买入机会。"
                "</div>"
            )
            html = html.replace("<body>", "<body>" + marker, 1)
            html = html.replace(
                'id="cluster-submit" class="primary-btn" type="submit"',
                'id="cluster-submit" class="primary-btn" type="submit" disabled '
                'aria-disabled="true" title="隔离验收不提供链上 CA 实时查询"',
            )
            html = html.replace(
                '<main>',
                '<p style="padding:12px"><a href="/qa/p4-replay" '
                'style="font-weight:bold;color:#9ed3ff">'
                '查看十条真实本地历史交易的模拟分析（不是实时提醒）</a></p>'
                '<main>', 1,
            )
            self._respond(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path in {"/static/app.js", "/static/styles.css"}:
            if query:
                self._json({"error": "QUERY_NOT_ALLOWED"}, 400)
                return
            fn = STATIC / path.rsplit("/", 1)[-1]
            self._respond(200, fn.read_bytes(),
                          "text/javascript; charset=utf-8" if path.endswith(".js")
                          else "text/css; charset=utf-8")
            return
        if path == "/qa/p4-replay":
            if query:
                self._json({"error": "QUERY_NOT_ALLOWED"}, 400)
                return
            report = self.p4_replay
            summary = (
                '<div role="alert" style="padding:16px;background:#34313d;'
                'color:white"><strong>历史回放 · 非实时 · 非链上独立核验</strong>'
                '<p>这些案例取自旧版 Frank 本地索引，仅在历史交易发生时刻模拟分析。'
                '不能证明当时就能发现交易、已有 V1 信号或可以跟单盈利。'
                '所有 SELL 提醒仅为历史模拟，绝不发送。</p>'
                '<p>验收结果：' + str(report.get("status", "UNKNOWN")) +
                '；交易记录数：' + str(report.get("counts", {}).get("distinct_signatures", 0)) +
                '；模拟卖出风险提示：' + str(report.get("counts", {}).get("historical_fake_sell_notices", 0)) +
                '（均未发送）</p><a style="color:#9ed3ff" href="/">返回新版候选看板</a>'
                '</div>'
            )
            html = report.get("html", "").replace(
                "<body>", "<body>" + summary, 1,
            )
            self._respond(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/qa/p4-replay.json":
            if query:
                self._json({"error": "QUERY_NOT_ALLOWED"}, 400)
            else:
                self._json({k: v for k, v in self.p4_replay.items() if k != "html"})
            return
        if path == "/api/frank-intelligence":
            if query:
                self._json({"error": "UNSUPPORTED_INTELLIGENCE_QUERY"}, 400)
            else:
                self._json(self.intelligence)
            return
        if path in self.snapshots:
            if query:
                self._json({"error": "QUERY_NOT_ALLOWED"}, 400)
            else:
                self._json(self.snapshots[path])
            return
        if path == "/api/frank-signed-activity":
            if query not in {"days=1", "days=7"}:
                self._json({"error": "INVALID_ACTIVITY_RANGE"}, 400)
            else:
                self._json(self.snapshots[path + "?" + query])
            return
        self._json({"error": "STAGING_ENDPOINT_DISABLED"}, 403)

    def do_POST(self) -> None:
        self._json({"error": "STAGING_POST_DISABLED_NO_NETWORK"}, 405)

    def do_PUT(self) -> None:
        self.do_POST()

    def do_DELETE(self) -> None:
        self.do_POST()


def smoke(port: int, expected_rows: int) -> None:
    root = f"http://127.0.0.1:{port}"
    with OPENER.open(root + "/", timeout=5) as response:
        page = response.read().decode("utf-8")
        assert "frank-intelligence-panel" in page
        assert "隔离验收" in page
    with OPENER.open(root + "/qa/p4-replay", timeout=5) as response:
        replay_page = response.read().decode("utf-8")
        assert "历史回放" in replay_page
        assert "FAKE ONLY, UNSENT" in replay_page or "No qualifying new SELL fact" in replay_page
    with OPENER.open(root + "/qa/p4-replay.json", timeout=5) as response:
        replay = json.load(response)
        assert replay["source_scope"] == "LOCAL_INDEX_ONLY_NOT_CHAIN_VERIFIED"
        assert replay["profit_or_executability_proven"] is False
        assert "html" not in replay
    with OPENER.open(root + "/static/app.js", timeout=5) as response:
        assert "get('/api/frank-intelligence')" in response.read().decode("utf-8")
    with OPENER.open(root + "/api/frank-intelligence", timeout=5) as response:
        j = json.load(response)
        assert j["status"] == "LOCAL_SOURCE_RESEARCH_ONLY"
        assert len(j["rows"]) == expected_rows
        assert j["live_notification_authorized"] is False
    try:
        OPENER.open(root + "/api/frank-intelligence?market=live", timeout=5)
    except urllib.error.HTTPError as exc:
        assert exc.code == 400
    else:
        raise AssertionError("UNSAFE_INTELLIGENCE_QUERY_ACCEPTED")
    try:
        OPENER.open(
            urllib.request.Request(root + "/api/cluster-analysis", method="POST", data=b"{}"),
            timeout=5,
        )
    except urllib.error.HTTPError as exc:
        assert exc.code == 405
    else:
        raise AssertionError("UNSAFE_POST_ACCEPTED")
    print("LOCAL_HTTP_SMOKE: PASS", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18766)
    args = parser.parse_args()
    if args.port != 18766:
        parser.error("Only audited isolation port 18766 is supported")
    check_frozen_source()
    data, as_of = capture_inputs()
    analyses = analyze_rows(
        data["/api/candidates"], as_of=as_of,
        max_market_age_seconds=1, market_observations=None,
    )
    previews = fake_intelligence_updates(
        analyses, as_of=as_of, max_event_age_seconds=600,
    )
    replay = run_replay(data["/api/trades"], snapshot_at=as_of)
    StageHandler.p4_replay = replay
    StageHandler.snapshots = dict(data)
    StageHandler.intelligence = {
        "status": "LOCAL_SOURCE_RESEARCH_ONLY",
        "as_of": as_of,
        "scope": "LOCAL_8766_CAPTURED_SNAPSHOT_NOT_LIVE",
        "source": "EXISTING_FRANK_LOCALHOST_SNAPSHOT_NO_DB_ACCESS",
        "market_reference": "NOT_REQUESTED",
        "live_notification_authorized": False,
        "rows": analyses,
    }
    StageHandler.capture_at = as_of
    StageHandler.port = args.port
    StageHandler.snapshots["/api/runtime"] = {
        "status": "STAGING_SNAPSHOT_NOT_LIVE",
        "runtime_reason": "FIXED_CAPTURE_REPLAY_ONLY",
        "heartbeat_age_seconds": "UNAVAILABLE",
        "production_db_readable": False,
    }
    StageHandler.snapshots["/api/control-health"] = {
        "status": "STAGING_SNAPSHOT_NOT_LIVE",
        "reason": "NO_PRODUCTION_CONTROL_OR_NOTIFICATION",
        "manual_review_breakdown_available": False,
        "manual_review_breakdown_error": None,
    }

    print("FIXED_REVIEWED_SOURCE_SHA:", PINNED, flush=True)
    print("CAPTURED_AT_UNIX:", round(as_of, 3), flush=True)
    print("SOURCE_EVIDENCE:", json.dumps(evidence_summary(data), ensure_ascii=False), flush=True)
    print("INTELLIGENCE_ROWS:", len(analyses), flush=True)
    print("FAKE_UNSENT_SELL_NOTICES:", len(previews), flush=True)
    print("P4_REPLAY_STATUS:", replay["status"], flush=True)
    print("P4_REPLAY_CASE_COUNTS:", json.dumps(replay["counts"], ensure_ascii=False), flush=True)
    print("P4_REPLAY_CHECK_ERRORS:", json.dumps(replay["errors"], ensure_ascii=False), flush=True)
    print("REAL_NOTICES_SENT: 0", flush=True)
    print("PRODUCTION_FILES_WRITTEN: 0", flush=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), StageHandler)
    server.daemon_threads = True
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        smoke(args.port, len(analyses))
        print(f"OPEN_IN_BROWSER: http://127.0.0.1:{args.port}/", flush=True)
        print(f"OPEN_P4_HISTORY: http://127.0.0.1:{args.port}/qa/p4-replay", flush=True)
        print("Press Ctrl+C to stop the isolated server.", flush=True)
        worker.join()
    except KeyboardInterrupt:
        print("STAGING_STOP_REQUESTED", flush=True)
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
