"""PR157 exact-source Mac staged Dashboard integration, no production mutation.

Only inbound source access: one snapshot of existing Frank 127.0.0.1:8766
GET endpoints. The HTTP server on 127.0.0.1:18766 uses PR157's *actual*
DashboardState.frank_activity_watch() and Handler.do_GET() implementation.
Original production-backed FrankReader is replaced with in-memory snapshot
rows. Existing reviewed PR157 UI/JS/CSS is served, without any alteration to
its on-disk sources.

NO direct SQLite, on-chain/RPC/Jupiter, SMTP, notifier, outbox, order, DB
mutation, launchd, installed service or production server restart. No POST
or provider/cluster GET access. Do not interpret snapshots as live quotes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import mimetypes
from http.server import ThreadingHTTPServer
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

PINNED_PR157 = "31dd598df248ca15f731913a5cbf82e88b981874"
QA_REL_PATH = "crypto-300-profit-mission/local-agent/scripts/frank_pr157_mac_integrated_staging.py"
LOCAL_AGENT = Path(__file__).resolve().parents[1]
REPO = LOCAL_AGENT.parents[1]
STATIC = LOCAL_AGENT / "mission_agent" / "mission_control" / "static"
SOURCE_PORT = 8766
STAGING_PORT = 18766
MAX_BYTES = 6_000_000
BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,88}$")

sys.path.insert(0, str(LOCAL_AGENT))
from mission_agent.mission_control import server as reviewed_server  # noqa: E402

SOURCE_ENDPOINTS = (
    "/api/runtime", "/api/control-health", "/api/candidates",
    "/api/trades", "/api/coverage", "/api/frank-observed-watchlist",
    "/api/review-activity", "/api/decisions",
)
OPTIONAL_ENDPOINTS = (
    "/api/frank-signed-activity?days=1",
    "/api/frank-signed-activity?days=7",
)
API_PATHS = (
    set(SOURCE_ENDPOINTS)
    | {"/api/frank-intelligence", "/api/frank-activity-watch",
       "/api/frank-signed-activity"}
)
STATIC_PATHS = {"/", "/index.html", "/static/app.js", "/static/styles.css"}


def ensure_only_qa_addition():
    def git(*args):
        return subprocess.run(
            ["git", "-C", str(REPO), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    if git("rev-parse", "--verify", PINNED_PR157 + "^{commit}") != PINNED_PR157:
        raise RuntimeError("REVIEWED_PR157_PARENT_NOT_AVAILABLE")
    if git("diff", "--name-only", PINNED_PR157, "HEAD").splitlines() != [QA_REL_PATH]:
        raise RuntimeError("QA_HAS_UNREVIEWED_PRODUCT_CODE_CHANGES")
    if git("status", "--porcelain"):
        raise RuntimeError("STAGING_GIT_CHECKOUT_DIRTY")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)


def source_get(endpoint):
    url = f"http://127.0.0.1:{SOURCE_PORT}{endpoint}"
    with OPENER.open(urllib.request.Request(url, method="GET"), timeout=8) as response:
        if response.status != 200:
            raise RuntimeError("PRODUCTION_SOURCE_GET_FAILED")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise RuntimeError("SOURCE_GET_TOO_LARGE")
        return json.loads(raw)


def one_time_capture():
    data = {p: source_get(p) for p in SOURCE_ENDPOINTS}
    for p in OPTIONAL_ENDPOINTS:
        try:
            data[p] = source_get(p)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            data[p] = {
                "status": "UNAVAILABLE",
                "reason": "OLDER_FRANK_RUNTIME_D1_ROUTE_NOT_PRESENT",
                "scope": "OLDER_FRANK_LOCAL_INDEX_NOT_COMPLETE_CHAIN",
                "rows": [],
                "signatures": None,
            }
    if not isinstance(data["/api/trades"], list) or not isinstance(data["/api/candidates"], list):
        raise RuntimeError("SNAPSHOT_SOURCE_TYPES_UNEXPECTED")
    if len(data["/api/trades"]) > 100:
        raise RuntimeError("SNAPSHOT_SOURCE_OVER_100_TRADE_CONTRACT")
    return data, time.time()


class InMemoryFrank:
    """Read from the captured existing GET response, never from SQLite."""

    def __init__(self, snapshots):
        self.snapshots = snapshots

    def recent_trades(self, limit):
        if limit != 100:
            raise ValueError("STAGE_ONLY_100_SOURCE_ROWS")
        return self.snapshots["/api/trades"]

    def candidates(self):
        return self.snapshots["/api/candidates"]


class StagedSnapshotState:
    def __init__(self, snapshots, frozen_at):
        self.snapshots = snapshots
        self.frozen_at = frozen_at
        self.product = reviewed_server.DashboardState.__new__(reviewed_server.DashboardState)
        self.product.frank = InMemoryFrank(snapshots)

    def frank_activity_watch(self):
        result = self.product.frank_activity_watch()
        result["staging_source_captured_at"] = self.frozen_at
        result["staging_source_mode"] = "ONE_TIME_8766_GET_REPLAY_NOT_LIVE"
        # Production method is actually executed; this extra field describes
        # where its data came from, not when each historical trade occurred.
        return result

    def frank_intelligence(self):
        result = self.product.frank_intelligence()
        result["staging_source_captured_at"] = self.frozen_at
        result["staging_source_mode"] = "ONE_TIME_8766_GET_REPLAY_NOT_LIVE"
        return result

    def runtime(self):
        return {
            "status": "STAGING_SNAPSHOT_NOT_LIVE",
            "runtime_reason": "CAPTURE_ONCE_NOT_CONTINUOUS_INDEX",
            "heartbeat_age_seconds": "UNAVAILABLE",
            "production_db_readable": False,
        }

    def mission_control_health(self):
        return {
            "status": "STAGING_SNAPSHOT_NOT_LIVE",
            "reason": "NO_PRODUCTION_DB_OR_MAIL_OR_NOTIFICATION",
            "manual_review_breakdown_available": False,
            "manual_review_breakdown_error": None,
        }

    def candidates(self):
        return self.snapshots["/api/candidates"]

    def recent_trades(self):
        return self.snapshots["/api/trades"]

    def activity_coverage(self):
        return self.snapshots["/api/coverage"]

    def frank_observed_watchlist(self):
        return self.snapshots["/api/frank-observed-watchlist"]

    def frank_signed_activity(self, days=1):
        return self.snapshots[f"/api/frank-signed-activity?days={days}"]

    def review_activity(self):
        return self.snapshots["/api/review-activity"]

    def decisions(self):
        return self.snapshots["/api/decisions"]


class StagedHandler(reviewed_server.Handler):
    state = None
    static_root = STATIC

    def _allowed_host(self):
        return (
            self.client_address[0] == "127.0.0.1"
            and self.headers.get("Host") in {
                f"127.0.0.1:{STAGING_PORT}",
                f"localhost:{STAGING_PORT}",
            }
        )

    def _file(self, path):
        """Serve EXACT PR157 static source; annotate the in-memory QA copy."""
        if not path.is_file() or not path.resolve().is_relative_to(STATIC.resolve()):
            return self.send_error(404)
        body = path.read_bytes()
        if path.name == "index.html":
            html = body.decode("utf-8")
            banner = (
                '<div role="alert" style="padding:14px;background:#34313d;'
                'color:#fff;font-weight:600">'
                "PR #157 Mac 隔离集成验收。已固定审核源码；"
                "页面仅重放启动时一次采集的 Frank 本地历史数据。"
                "不是实时监控；没有新 RPC、报价、消息、订单或生产变更。"
                "禁止把历史候选当作实时买入机会。"
                "</div>"
            )
            if "<body>" not in html or "frank-activity-panel" not in html:
                raise RuntimeError("PR157_PRODUCT_UI_MARKERS_MISSING")
            html = html.replace("<body>", "<body>" + banner, 1)
            html = html.replace(
                'id="cluster-submit" class="primary-btn" type="submit"',
                'id="cluster-submit" class="primary-btn" type="submit" '
                'disabled aria-disabled="true" '
                'title="隔离验收禁用实时 CA 查询"',
            )
            body = html.encode("utf-8")
        self.send_response(200)
        self.send_header(
            "Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        )
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frank-Stage", "PR157_ONE_SHOT_LOCAL_SNAPSHOT")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; connect-src 'self'; "
                         "style-src 'self' 'unsafe-inline'; script-src 'self'; "
                         "img-src 'self' data:; object-src 'none'; "
                         "form-action 'none'; frame-ancestors 'none'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frank-Stage", "PR157_ONE_SHOT_LOCAL_SNAPSHOT")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path not in API_PATHS | STATIC_PATHS:
            return self._json({"error": "STAGING_ROUTE_DISABLED_NO_EXTERNAL_NETWORK"}, 403)
        if parsed.path in STATIC_PATHS and parsed.query:
            return self._json({"error": "STATIC_QUERY_NOT_ALLOWED"}, 400)
        # Use actual reviewed PR157 Handler.do_GET, not an emulated route.
        return super().do_GET()

    def do_POST(self):
        return self._json({"error": "STAGING_POST_DISABLED_NO_SEND_OR_RPC"}, 405)

    def do_PUT(self):
        return self.do_POST()

    def do_DELETE(self):
        return self.do_POST()

    def log_message(self, *_args):
        return


def evidence(data, response):
    rows = data["/api/trades"]
    found = {}
    for tr in rows:
        if not isinstance(tr, dict):
            continue
        s, m = tr.get("signature"), tr.get("mint")
        if isinstance(s, str) and BASE58.fullmatch(s) and isinstance(m, str) and BASE58.fullmatch(m):
            found.setdefault(s, (m, tr.get("side")))
    return {
        "source": "OLDER_FRANK_8766_ONE_SHOT_GET_NOT_LIVE",
        "source_runtime_at_capture": data["/api/runtime"].get("status"),
        "source_scope": data["/api/coverage"].get("scope"),
        "chain_completeness_verified": False,
        "source_candidates": len(data["/api/candidates"]),
        "source_recent_rows": len(rows),
        "source_unique_signatures": len(found),
        "source_distinct_mints": len({p[0] for p in found.values()}),
        "source_sides": dict(Counter(str(p[1]) for p in found.values())),
        "activity_displayed_transactions": response["displayed_transactions"],
        "activity_counts": response["counts"],
        "no_addresses_signatures_mints_or_db_paths_exported": True,
        "real_notification_sent": False,
        "production_db_writes": False,
    }


def probe(port, expected):
    url = f"http://127.0.0.1:{port}"
    with OPENER.open(url + "/", timeout=5) as response:
        html = response.read().decode("utf-8")
        assert "隔离集成验收" in html
        assert 'id="frank-activity-panel"' in html
        assert 'id="frank-activity-type"' in html
    with OPENER.open(url + "/static/app.js", timeout=5) as response:
        source = response.read().decode("utf-8")
        assert "get('/api/frank-activity-watch')" in source
        assert "renderFrankActivity(" in source
        assert "get('/api/frank-intelligence')" in source
    with OPENER.open(url + "/api/frank-activity-watch", timeout=5) as response:
        actual = json.load(response)
        assert actual["status"] == "LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY"
        assert actual["notification_authorized"] is False
        assert actual["counts"] == expected["counts"]
        assert actual["displayed_transactions"] == expected["displayed_transactions"]
        assert all(row["send_allowed"] is False and row["order_amount_usdc"] is None
                   for row in actual["rows"])
    with OPENER.open(url + "/api/frank-intelligence", timeout=5) as response:
        intelligent = json.load(response)
        assert intelligent["status"] == "LOCAL_SOURCE_RESEARCH_ONLY"
        assert intelligent["live_notification_authorized"] is False
    for bad_url, expected_code in (
        ("/api/frank-activity-watch?market=live", 400),
        ("/api/cluster-analysis", 403),
    ):
        try:
            OPENER.open(url + bad_url, timeout=5)
        except urllib.error.HTTPError as error:
            assert error.code == expected_code
        else:
            raise AssertionError("STAGING_UNSAFE_GET_ACCEPTED")
    try:
        OPENER.open(
            urllib.request.Request(url + "/api/cluster-analysis",
                                   data=b"{}", method="POST"),
            timeout=5,
        )
    except urllib.error.HTTPError as error:
        assert error.code == 405
    else:
        raise AssertionError("STAGING_UNSAFE_POST_ACCEPTED")
    print("PR157_STAGED_PRODUCT_GET_AND_UI_SMOKE: PASS", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=STAGING_PORT)
    args = parser.parse_args()
    if args.port != STAGING_PORT:
        parser.error("Only audited local isolated port 18766 is allowed")
    ensure_only_qa_addition()
    data, captured_at = one_time_capture()
    state = StagedSnapshotState(data, captured_at)
    StagedHandler.state = state
    product_result = state.frank_activity_watch()
    if product_result["status"] != "LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY":
        raise RuntimeError("PR157_PRODUCT_ACTIVITY_UNAVAILABLE_ON_SOURCE")
    print("PINNED_REVIEWED_PRODUCT_SHA:", PINNED_PR157, flush=True)
    print("SOURCE_CAPTURED_AT_UNIX:", round(captured_at, 3), flush=True)
    print("REAL_PRODUCT_ACTIVITY_EVIDENCE:",
          json.dumps(evidence(data, product_result), ensure_ascii=False), flush=True)
    print("PRODUCTION_MODIFICATIONS: 0", flush=True)
    print("REAL_NOTIFICATIONS_SENT: 0", flush=True)
    thread_server = ThreadingHTTPServer(("127.0.0.1", STAGING_PORT), StagedHandler)
    thread_server.daemon_threads = True
    worker = threading.Thread(target=thread_server.serve_forever, daemon=True)
    worker.start()
    try:
        probe(STAGING_PORT, product_result)
        print(f"OPEN_REVIEWED_PR157_UI: http://127.0.0.1:{STAGING_PORT}/", flush=True)
        print("Press Ctrl+C to stop only this temporary staging server.", flush=True)
        worker.join()
    except KeyboardInterrupt:
        print("PR157_STAGING_STOP_REQUESTED", flush=True)
    finally:
        thread_server.shutdown()
        thread_server.server_close()


if __name__ == "__main__":
    main()
