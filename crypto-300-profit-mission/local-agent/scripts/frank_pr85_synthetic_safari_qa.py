"""Manual synthetic-only PR85 Safari launcher. No external RPC or prod data."""
import argparse
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request

from mission_agent.meme.identity import reconcile_identity
from mission_agent.mission_control.follow_view import partition_candidates
from mission_agent.mission_control.server import Handler
from mission_agent.mission_control.wallet_chain_capture import SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM
from scripts.frank_f02_manual_refresh import refresh_session
from scripts.frank_f02_readonly_positions_api import make_handler as positions_handler
from scripts.frank_joint_readonly_http import JointReadOnly, make_handler as joint_handler
from scripts.frank_reconcile_frozen32_offline import ROSTER, load_frozen_roster

TREE = "eea30efa09cb1509d7eee3fde3043ee7155257cf"
PINS = (
    "662ba4aceb9d53cb7a541ad3f251f9e12b8c09ea",
    "5755b8b96080f21635eaa5354588cbb8f6561ab0",
    "8d425e4d0e9db9f27abd8ad662e4d59e64b57e53",
    "d2eeebc1b49d2bae38e05d7d01f6839e3ba237f4",
    "40febd8275c7710a8697af5a0503569a2bb5cb8d",
)
WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
ABC = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def preflight(root):
    root = root.expanduser().resolve(strict=True)
    expected = (Path.home() / ".local/share/frank-pr85-mac-qa-R1c6kmCU").resolve()
    if root != expected:
        raise ValueError("QA_ROOT_NOT_APPROVED")
    repo = root / "repo"
    if git(repo, "rev-parse", "HEAD^{tree}") != TREE:
        raise ValueError("SOURCE_TREE_SHA_MISMATCH")
    if git(repo, "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"):
        raise ValueError("QA_SOURCE_NOT_CLEAN")
    for sha in PINS:
        subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, "HEAD"], check=True)
    return root, repo


def only_loopback():
    orig = socket.socket.connect
    orig_ex = socket.socket.connect_ex
    def check(sock, address):
        if sock.family not in (socket.AF_INET, socket.AF_INET6) or not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1"):
            raise OSError("EXTERNAL_SOCKET_FORBIDDEN")
    def connect(sock, address):
        check(sock, address)
        return orig(sock, address)
    def connect_ex(sock, address):
        check(sock, address)
        return orig_ex(sock, address)
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex


def pubkey(seed):
    n = int.from_bytes(bytes([seed]) * 32, "big")
    out = ""
    while n:
        n, d = divmod(n, 58)
        out = ABC[d] + out
    return out


def fake_entry(wallet, mint, program, amount, seed):
    return {"pubkey": pubkey(seed), "account": {"owner": program, "data": {"parsed": {
        "type": "account", "info": {"owner": wallet, "mint": mint, "state": "initialized",
        "tokenAmount": {"amount": amount, "decimals": 6}}}}}}


def sources(root):
    records = load_frozen_roster(ROSTER, WALLET)["records"]
    a, b = records[0]["mint"], records[1]["mint"]
    calls = []
    def read_raw(method, params, ident):
        if method != "getTokenAccountsByOwner" or ident not in (1, 2) or params[0] != WALLET:
            raise ValueError("UNEXPECTED_SYNTHETIC_RPC_CALL")
        calls.append(ident)
        program = SPL_TOKEN_PROGRAM if ident == 1 else TOKEN_2022_PROGRAM
        mint, amount = (a, "123000000") if ident == 1 else (b, "0")
        return json.dumps({"jsonrpc": "2.0", "id": ident,
            "result": {"context": {"slot": 5000 + ident},
                "value": [fake_entry(WALLET, mint, program, amount, 90 + ident)]}}).encode()
    receipt, f02 = refresh_session(session_root=root / "synthetic-f02", read_raw=read_raw)
    if receipt["status"] != "VERIFIED_MANUAL_RESEARCH_SESSION" or calls != [1, 2]:
        raise ValueError("SYNTHETIC_SOURCE_NOT_VERIFIED")
    f02.max_age_seconds = 120
    return a, b, f02


def state_for(a, b):
    profile = {"mint": a, "status": "OK", "mint_account_status": "VERIFIED", "metadata": {"status": "VERIFIED", "records": [
        {"mint": a, "name": "SYNTHETIC SAME-NAME TOKEN", "symbol": "SYNTH",
         "source": "TOKEN2022_METADATA", "update_authority": None}]}}
    market = {"mint": a, "status": "OK", "market_match_status": "EXACT_BASE_MINT_MATCH",
        "identity_records": [{"mint": a, "name": "SYNTHETIC SAME-NAME TOKEN",
                              "symbol": "SYNTH", "source": "DEXSCREENER_API"}]}
    identity = reconcile_identity(a, profile, market)
    if identity["identity_status"] != "VERIFIED":
        raise ValueError("SYNTHETIC_A_IDENTITY_NOT_VERIFIED")
    reports = {
        a: {"mint": a, "chain": "solana", "token_identity": identity,
            "token_profile": {"status": "OK", "source": "SOLANA_FINALIZED_JSON_RPC",
                "mint_account_status": "VERIFIED", "is_initialized": True, "mint_slot": 5001,
                "program_id": SPL_TOKEN_PROGRAM, "mint_authority": None,
                "freeze_authority": None, "extensions": [], "active_extension_risks": [],
                "inactive_sensitive_extensions": [], "unresolved_sensitive_extensions": []},
            "market": {"status": "UNAVAILABLE"}, "assessment": {
                "chain_permission_status": "PASS", "trading_status": "WATCH / CLUSTER_UNRESOLVED",
                "narrative_status": "UNVERIFIED"}},
        b: {"mint": b, "chain": "solana", "token_identity": {
                "identity_status": "UNCONFIRMED", "display_label": "SYNTHETIC SAME-NAME TOKEN",
                "conflict_status": "UNRESOLVED", "market_match_status": "NOT_CHECKED",
                "sources": [{"source": "SYNTHETIC_ONLY", "mint": b,
                             "reason": "mint_sha256_" + ("a" * 64)}],
                "metadata_attempts": [{"source": "SYNTHETIC_ONLY", "status": "FAILED",
                                       "reason": "slot_502"}]},
            "token_profile": {"status": "OK", "mint_account_status": "UNCONFIRMED",
                "is_initialized": False, "extensions": [], "active_extension_risks": [],
                "inactive_sensitive_extensions": [], "unresolved_sensitive_extensions": []},
            "market": {"status": "UNAVAILABLE"}, "assessment": {
                "chain_permission_status": "UNRESOLVED",
                "trading_status": "WATCH / CHAIN_PERMISSION_UNRESOLVED",
                "narrative_status": "UNVERIFIED"}},
    }
    class Jobs:
        def latest(self, mint):
            return reports.get(mint)
        def submit(self, mint, preset):
            if mint not in reports:
                raise ValueError("SYNTHETIC_MINT_ONLY")
            return {"job_id": "synthetic-a" if mint == a else "synthetic-b",
                    "mint": mint, "status": "DONE"}
        def get(self, job_id):
            if job_id not in ("synthetic-a", "synthetic-b"):
                return None
            return {"job_id": job_id, "status": "DONE",
                    "mint": a if job_id == "synthetic-a" else b}
    class State:
        cluster_jobs = Jobs()
        def runtime(self):
            return {"status": "LIVE", "heartbeat_age_seconds": 1}
        def mission_control_health(self):
            return {"status": "OK", "manual_review_breakdown_available": True,
                    "manual_review_actionable_count": 0}
        def candidates(self):
            return []
        def follow_opportunities(self):
            now = time.time()
            def candidate(mint, name, side, price):
                return {"mint": mint, "person_id": "frank", "decision": "BUY",
                    "source_signal_id": name, "pattern": "MULTIPLE", "episode_id": "SYNTHETIC",
                    "position_state": "OPEN", "current_raw": "123000000",
                    "latest_side": side, "latest_at": now - 9, "latest_buy_at": now - 9,
                    "decision_created_at": now - 2, "quote_observed_at": now - 2,
                    "decision_quote": {"status": "OK", "route_exists": True,
                        "execution_price_usdc": price, "price_impact_pct": "0.1"},
                    "metrics": {"execution_price_usdc": "0.1", "price_impact_pct": "0.1",
                                "frank_latest_buy_price_usdc": "0.08"}}
            rows = [candidate(a, "synthetic-buy", "BUY", "0.1"),
                    candidate(b, "synthetic-sell", "SELL", "0.1"),
                    candidate(pubkey(87), "synthetic-invalid-quote", "BUY", "1e-999")]
            partition = partition_candidates(
                rows, now=now, runtime_status="LIVE",
                max_frank_buy_age_seconds=600, max_quote_age_seconds=30)
            if partition["eligible_count"] != 1 or partition["excluded_count"] != 2:
                raise ValueError("F01_SYNTHETIC_PARTITION_FAILED")
            return partition
        def recent_trades(self):
            return []
        def review_activity(self):
            return []
        def decisions(self):
            return []
        def activity_coverage(self):
            return {"status": "OK", "windows": {"24h": {
                "indexed_signatures": 3, "recognized_trades": 2,
                "recognized_buys": 1, "recognized_sells": 1,
                "unknown_needs_review": 0}, "7d": {}, "30d": {}}}
        def frank_observed_watchlist(self):
            return {"status": "OK", "summary": {"total_observed": 2},
                "rows": [{"mint": a, "watch_state": "MODEL_OPEN",
                    "snapshot_verified_slot": 123456789,
                    "snapshot_inventory_state": "NONZERO_AT_SLOT",
                    "snapshot_token_quantity": "123.000000",
                    "last_event_time": time.time() - 8},
                    {"mint": b, "watch_state": "WATCH_UNRESOLVED",
                     "last_event_time": time.time() - 8}]}
    return State()


class Listener:
    def __init__(self, handler):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
    @property
    def port(self):
        return self.httpd.server_port
    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)


def get_json(port, path):
    with urllib.request.urlopen("http://127.0.0.1:" + str(port) + path, timeout=5) as reply:
        if reply.status != 200:
            raise ValueError("SYNTHETIC_HTTP_STATUS_NOT_200")
        return json.loads(reply.read())


QA_BANNER = (
    '<div id="synthetic-qa-banner" role="alert">'
    'SYNTHETIC QA · 模拟数据 · 禁止交易 · 不代表真实 Frank 状态或钱包余额'
    '</div>'
).encode("utf-8")
QA_BANNER_CSS = (
    "#synthetic-qa-banner{position:sticky;top:0;z-index:1000000;"
    "background:#991b3b;color:#fff;text-align:center;"
    "padding:12px;font-size:15px;font-weight:700;"
    "box-shadow:0 2px 8px #0009;}\\n"
)


def read_html(port, path):
    with urllib.request.urlopen("http://127.0.0.1:" + str(port) + path, timeout=5) as reply:
        if reply.status != 200:
            raise ValueError("SYNTHETIC_HTML_STATUS_NOT_200")
        return reply.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-root", required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--no-safari", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    root, repo = preflight(Path(args.qa_root))
    runtime = Path(tempfile.mkdtemp(prefix="safari-session-", dir=str(root)))
    only_loopback()
    listeners = []
    result = {"status": "STARTING", "source_tree_sha": TREE,
              "synthetic_only": True, "real_rpc": False,
              "production_deployment": False, "gmail": False, "trades": False,
              "runtime_directory": str(runtime)}
    try:
        a, b, f02 = sources(runtime)
        class Control(Handler):
            def _file(self, path):
                if path == self.static_root / "index.html":
                    raw = path.read_bytes().replace(b"<body>", b"<body>" + QA_BANNER, 1)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                    return
                return super()._file(path)

        from scripts.frank_f02_readonly_positions_api import WEB_CSP, WEB_ROUTES, WEB_ROOT
        NativeResearch = positions_handler(f02)
        class SyntheticResearch(NativeResearch):
            def _static(self, path):
                if path not in ("/research/positions", "/research/positions.css"):
                    return super()._static(path)
                filename, mime = WEB_ROUTES[path]
                raw = (WEB_ROOT / filename).read_bytes()
                if path == "/research/positions":
                    raw = raw.replace(b"<body>", b"<body>" + QA_BANNER, 1)
                else:
                    raw = raw + QA_BANNER_CSS.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Security-Policy", WEB_CSP)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                self.wfile.write(raw)

        Control.state = state_for(a, b)
        listeners.append(Listener(Control))
        listeners.append(Listener(SyntheticResearch))
        joint = JointReadOnly(control_port=listeners[0].port,
                             f02_port=listeners[1].port)
        listeners.append(Listener(joint_handler(joint)))
        control, research, combined = (x.port for x in listeners)
        if b'id="synthetic-qa-banner"' not in read_html(control, "/"):
            raise ValueError("SYNTHETIC_CONTROL_BANNER_MISSING")
        if b'id="synthetic-qa-banner"' not in read_html(research, "/research/positions"):
            raise ValueError("SYNTHETIC_F02_BANNER_MISSING")
        f01 = get_json(control, "/api/follow-opportunities")
        ca = get_json(control, "/api/cluster-latest?mint=" + a)
        cb = get_json(control, "/api/cluster-latest?mint=" + b)
        p = get_json(research, "/api/research/positions")
        bridge = get_json(combined, "/api/research/alignment?mint=" + a)
        if (f01["eligible_count"] != 1 or f01["excluded_count"] != 2
                or ca["mint"] != a or cb["mint"] != b
                or p["target_mint_count"] != 32
                or p["state_counts"].get("OPEN_ACCOUNT_NONZERO") != 1
                or p["state_counts"].get("OPEN_ACCOUNT_ZERO") != 1
                or bridge["combined_trade_permission"] is not False):
            raise ValueError("NATIVE_SYNTHETIC_HTTP_CONTRACT_FAILED")
        urls = {
            "signals": "http://127.0.0.1:" + str(control) + "/#signals",
            "cluster": "http://127.0.0.1:" + str(control) + "/#cluster",
            "f02_research_only": "http://127.0.0.1:" + str(research) + "/research/positions",
        }
        result.update({"status": "MAC_PR85_SYNTHETIC_HTTP_SMOKE_PASS",
            "mint_a": a, "mint_b": b, "urls": urls, "f02_ttl_seconds": 120,
            "listener_ports": [control, research, combined],
            "synthetic_wire_calls": 2,
            "started_at_utc": datetime.now(timezone.utc).isoformat()})
        (runtime / "session.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
        if not args.smoke:
            if not args.no_safari:
                for route in ("signals", "f02_research_only"):
                    subprocess.run(["open", "-a", "Safari", urls[route]], check=False)
            print("SYNTHETIC_SAFARI_QA_READY", flush=True)
            print("Inspect signals, cluster mint_a and mint_b, then F02 TTL (120s). Press ENTER here when screenshots are captured.", flush=True)
            input()
    finally:
        for listener in reversed(listeners):
            listener.stop()
        result.update({"stopped_at_utc": datetime.now(timezone.utc).isoformat(),
            "services_stopped": True,
            "source_tree_sha_after": git(repo, "rev-parse", "HEAD^{tree}"),
            "repo_clean": not git(repo, "status", "--porcelain=v1",
                "--untracked-files=all", "--ignored=matching")})
        (runtime / "session.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"status": "MAC_PR85_SYNTHETIC_SESSION_ENDED",
            "session_file": str(runtime / "session.json"),
            "services_stopped": True,
            "source_tree_sha": result["source_tree_sha_after"],
            "repo_clean": result["repo_clean"], "real_rpc": False}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
