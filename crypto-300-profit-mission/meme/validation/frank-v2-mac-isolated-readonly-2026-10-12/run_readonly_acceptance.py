#!/usr/bin/env python3
"""Isolated Mac-only Frank PR #31 read-only acceptance (no mail, live RPC, or producer restart).

Fetches the exact reviewed commit into a disposable Git directory, snapshots SQLite
through mode=ro, serves only a loopback Dashboard on a free ephemeral port,
executes synthetic RPC/export failure probes, offers manual render review,
and exports only a small sanitized result JSON ZIP to Downloads.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

REPO = "https://github.com/lxxlx2/ChatGPT_mission_record.git"
PINNED = "c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7"
J7 = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"
BPXX = "BPxxfRCXkUVhig4HS1Lh7kZqV6SPJhzfEk4x6fVBjPCy"
SIG = "3opgLQn1cfQPPoKHNnU986rA9QyAzdmSoLPAXFwxA1tP7Vbx7J3MEHSoAczvcmHPpH7X1pxV3kmE4cGewJnxyR5n"
SIGNER = "VP4B4yj63FNP4BZLZdBJYRsTi1LqUuUENY8wfAdtSn8"

checks: dict[str, str] = {}
details: dict[str, object] = {}
stage = "PREFLIGHT"
proc = None


def require(name: str, condition: bool):
    checks[name] = "PASS" if condition else "FAIL"
    print(f"{name}={checks[name]}", flush=True)
    if not condition:
        raise RuntimeError(f"CHECK_FAILED_{name}")


def run(args: list[str], **kwargs):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=180, **kwargs)


def sqlite_snapshot(source: Path, destination: Path):
    if not source.is_file():
        raise FileNotFoundError("MISSING_REQUIRED_SQLITE")
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True, timeout=5) as db:
        db.execute("PRAGMA query_only=ON")
        with sqlite3.connect(destination) as target:
            db.backup(target)
            require("SQLITE_SNAPSHOT_INTEGRITY",
                    target.execute("PRAGMA integrity_check").fetchone()[0] == "ok")


def var(data: str, name: str) -> str:
    m = re.search(r'^' + re.escape(name) + r'="([^"]+)"$', data, re.M)
    if not m:
        raise RuntimeError("RUNNER_FIELD_UNAVAILABLE_" + name)
    return m.group(1)


def local_get(port: int, path: str) -> bytes:
    # Disable even an inherited HTTP proxy for loopback queries.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                 headers={"Accept": "application/json"})
    with opener.open(req, timeout=5) as response:
        if response.status != 200:
            raise RuntimeError("LOCAL_HTTP_NON_200")
        return response.read(5_000_000)


def assert_watch(data: dict, base: dict):
    require("WATCH_SCHEMA_V2", data.get("ata_gap_source_status") == "DATED_ATA_INDEX_SCOPE_V2")
    observed = {row["mint"]: row for row in data.get("rows", [])}
    original = {row["mint"]: row for row in base.get("rows", [])}
    require("J7_AND_BPXX_PRESENT", J7 in observed and BPXX in observed)
    expected = {
        J7: (0, 2, 0, 0, 2),
        BPXX: (63, 3, 1, 1, 1),
    }
    for mint, expected_counts in expected.items():
        item = observed[mint]
        values = tuple(item.get(k) for k in (
            "ata_outside_index_window_signatures",
            "ata_inside_index_window_signatures",
            "ata_inwindow_failed_signatures",
            "ata_inwindow_success_unverified",
            "ata_verified_extra_passive_receipts",
        ))
        tag = "J7" if mint == J7 else "BPXX"
        require(tag + "_ATA_WINDOW", values == expected_counts)
        require(tag + "_NOT_INFERRED_BUY", item.get("is_follow_signal") is False
                and item.get("pnl_usd") is None
                and item.get("sender_cost_basis_usd") is None)
        baseline = original.get(mint)
        require(tag + "_TRADES_UNCHANGED", baseline is not None and all(
            baseline.get(field) == item.get(field)
            for field in ("local_recognized_buys", "local_recognized_sells")))
        details[tag + "_window_counts"] = list(values)
    require("ALL_LOCAL_TRADE_COUNTS_UNCHANGED", all(
        mint in original and all(original[mint].get(field) == item.get(field)
            for field in ("local_recognized_buys", "local_recognized_sells"))
        for mint, item in observed.items()))
    require("PASSIVE_NO_BUY", all(
        row.get("local_recognized_buys", 0) == 0
        for row in observed.values()
        if row.get("watch_state") == "PASSIVE_RECEIPT_ONLY"))
    details["watchlist_row_count"] = len(observed)


def rpc_injection(temp: Path):
    from mission_agent.mission_control.ata_backfill import (
        WALLET, TOKEN_2022, derive_ata, scan_ata_mints,
    )
    ata, _ = derive_ata(WALLET, J7, TOKEN_2022)
    record = {
        "slot": 454705300, "blockTime": 1791505760,
        "transaction": {"signatures": [SIG], "message": {"accountKeys": [
            {"pubkey": SIGNER, "signer": True},
            {"pubkey": SIGNER, "signer": False},
            {"pubkey": ata, "signer": False}]}},
        "meta": {"err": None,
                 "preTokenBalances": [{"accountIndex": 2, "mint": J7, "owner": WALLET,
                                       "programId": TOKEN_2022,
                                       "uiTokenAmount": {"amount": "0", "decimals": 6}}],
                 "postTokenBalances": [{"accountIndex": 2, "mint": J7, "owner": WALLET,
                                        "programId": TOKEN_2022,
                                        "uiTokenAmount": {"amount": "5000000", "decimals": 6}}]}}
    class FixtureRPC:
        def call(self, method, params):
            if method == "getTransaction":
                return record
            if method != "getSignaturesForAddress":
                raise AssertionError("UNEXPECTED_RPC_METHOD")
            if params[0] == ata:
                if params[1].get("before"):
                    raise http.client.BadStatusLine("SYNTHETIC_CLOSED_TRANSPORT")
                return [{"signature": SIG, "slot": 454705300, "blockTime": 1791505760,
                         "err": None}]
            return []
    report = scan_ata_mints(FixtureRPC(), [J7], known_signatures=set(),
                            page_size=1, max_pages_per_ata=2, max_tx_fetches=4)
    require("RPC_PARTIAL_STATUS", report.get("scan_status") == "PARTIAL_RPC_INTERRUPTED")
    require("RPC_PARTIAL_PRESERVES_PRIOR_VALID", any(
        o.get("signature") == SIG and o.get("status") == "VERIFIED_ATA_BALANCE_DELTA"
        for o in report.get("observations", [])))
    require("RPC_NOT_COMPLETE", report.get("complete_wallet_history") is False)
    (temp / "rpc-synthetic.json").write_text(json.dumps({
        "scan_status": report.get("scan_status"),
        "validated_observations": sum(o.get("status") == "VERIFIED_ATA_BALANCE_DELTA"
                                      for o in report.get("observations", [])),
        "complete_wallet_history": report.get("complete_wallet_history"),
    }, indent=2), encoding="utf-8")


def export_injection(temp: Path):
    from mission_agent.mission_control.evidence_sync import EvidenceSpool, GitEvidencePublisher
    spool = EvidenceSpool(temp / "drill")
    pending = spool.ca_done(mint=J7, job_id="readonly-drill-20261012",
                            report={"mint": J7, "coverage": {"status": "SYNTHETIC"}})
    publisher = GitEvidencePublisher(spool, gh="/no-such-git-program")
    def failed_transport(*args, **kwargs):
        raise RuntimeError("SYNTHETIC_TRANSPORT_UNAVAILABLE")
    publisher._gh = failed_transport
    result = publisher.sync()
    require("EXPORT_FAILURE_REPORTED", result.get("status") == "SYNC_PARTIAL"
            and len(result.get("errors", [])) > 0)
    require("EXPORT_PENDING_RETAINED", pending.is_file()
            and result.get("pending_ca", 0) >= 1)
    require("EXPORT_NO_NETWORK", result.get("uploaded") == 0)


def main():
    global stage, proc
    home = Path.home()
    runner = home / "Library/Application Support/FrankMeme/dashboard.sh"
    pointer = home / ".frank_meme_control_root"
    require("KNOWN_RUNNER_AND_CONTROL", runner.is_file() and pointer.is_file())
    content = runner.read_text(encoding="utf-8")
    production = Path(var(content, "PROD")).resolve()
    python_bin = Path(var(content, "VENV")) / "bin/python"
    control = Path(pointer.read_text(encoding="utf-8").strip()).resolve()
    require("KNOWN_VENV_AND_DBS", python_bin.is_file()
            and (production / "forward.sqlite").is_file()
            and (control / "mission-control.sqlite").is_file())
    agents_folder = home / "Library/LaunchAgents"
    before_agents = sorted(p.name for p in agents_folder.iterdir()) if agents_folder.is_dir() else []
    stage = "TEMP_ISOLATION"
    with tempfile.TemporaryDirectory(prefix="frank-pr31-isolated-") as folder:
        tmp = Path(folder)
        source = tmp / "git"
        source.mkdir()
        stage = "EXACT_SOURCE"
        git_env = os.environ.copy()
        git_env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/usr/bin/false"})
        run(["/usr/bin/git", "-C", str(source), "init", "-q"], env=git_env)
        run(["/usr/bin/git", "-C", str(source), "-c", "credential.helper=",
             "fetch", "-q", "--depth=1", REPO, PINNED], env=git_env)
        run(["/usr/bin/git", "-C", str(source), "checkout", "--detach", "-q", "FETCH_HEAD"],
            env=git_env)
        head = run(["/usr/bin/git", "-C", str(source), "rev-parse", "HEAD"],
                   env=git_env).stdout.strip()
        require("EXACT_SOURCE_SHA", head == PINNED)
        agent = source / "crypto-300-profit-mission/local-agent"
        require("ISOLATED_SOURCE_COMPLETE", (agent / "scripts/mission_meme_v1.py").is_file()
                and (source / "crypto-300-profit-mission/meme/evidence/"
                     "frank-v2-ata-index-scope-correction-2026-10-11.json").is_file())
        stage = "SNAPSHOT"
        copy_prod, copy_control = tmp / "prod", tmp / "ctrl"
        copy_prod.mkdir()
        copy_control.mkdir()
        sqlite_snapshot(production / "forward.sqlite", copy_prod / "forward.sqlite")
        sqlite_snapshot(control / "mission-control.sqlite",
                        copy_control / "mission-control.sqlite")
        for origin, destination in [
            (production / "health.json", copy_prod / "health.json"),
            (control / "mission-control-health.json", copy_control / "mission-control-health.json"),
            (control / "frank-inventory-snapshot.json",
             copy_control / "frank-inventory-snapshot.json"),
        ]:
            if origin.is_file():
                shutil.copyfile(origin, destination)
        require("NO_LIVE_DB_IN_ISOLATION",
                (copy_prod / "forward.sqlite").resolve() !=
                (production / "forward.sqlite").resolve()
                and (copy_control / "mission-control.sqlite").resolve() !=
                (control / "mission-control.sqlite").resolve())
        stage = "ISOLATED_DASHBOARD"
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0))
            port = sk.getsockname()[1]
        require("NO_PRODUCTION_PORT_COLLISION", port not in (8765, 8766))
        env = os.environ.copy()
        for secret in ("GH_TOKEN", "GITHUB_TOKEN", "JUPITER_API_KEY", "GMAIL_TOKEN",
                       "SOLANA_RPC_URLS", "SOLANA_RPC_URL", "ALCHEMY_API_KEY"):
            env.pop(secret, None)
        env.update({"PYTHONPATH": str(agent),
                    "MISSION_EVIDENCE_EXPORT_ENABLED": "0",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "GIT_TERMINAL_PROMPT": "0"})
        log = (tmp / "isolation-server.log").open("wb")
        try:
            proc = subprocess.Popen(
                [str(python_bin), str(agent / "scripts/mission_meme_v1.py"), "serve",
                 "--production-root", str(copy_prod), "--control-root", str(copy_control),
                 "--host", "127.0.0.1", "--port", str(port)],
                cwd=str(agent), env=env, stdout=log, stderr=subprocess.STDOUT)
            response = None
            for _ in range(45):
                if proc.poll() is not None:
                    break
                try:
                    response = local_get(port, "/api/frank-observed-watchlist")
                    break
                except (OSError, ValueError, RuntimeError):
                    time.sleep(0.25)
            require("ISOLATED_DASHBOARD_HTTP_200", response is not None)
            data = json.loads(response)
            js = local_get(port, "/static/app.js").decode("utf-8")
            require("NO_OLD_GAP_LABELS", "历史索引缺口" not in js
                    and "CONFIRMED_HISTORICAL_GAP" not in js)
            require("NEW_AT_A_GLANCE_WINDOW_LABEL", "窗口前" in js and "窗口内" in js)
            sys.path.insert(0, str(agent))
            from mission_agent.mission_control.wallet_watch import from_sqlite
            base = from_sqlite(copy_prod / "forward.sqlite")
            stage = "WINDOW_AND_TRADE_VALIDATION"
            assert_watch(data, base)
            stage = "RPC_AND_EXPORT_FAILURE_INJECTION"
            rpc_injection(tmp)
            export_injection(tmp)
            stage = "BROWSER_RENDER"
            print(f"ISOLATED_URL=http://127.0.0.1:{port}/", flush=True)
            print("请用浏览器检查 J7 和 BPxx 文字、窗口 0/2 与 63/3。只检查，不点击提交分析按钮。", flush=True)
            if sys.stdin.isatty():
                answer = input("检查后输入 PASS / FAIL / SKIP 并回车：").strip().upper()
                checks["BROWSER_RENDER"] = (
                    "PASS" if answer == "PASS" else
                    "FAIL" if answer == "FAIL" else "SKIPPED")
            else:
                checks["BROWSER_RENDER"] = "SKIPPED"
            print(f"BROWSER_RENDER={checks['BROWSER_RENDER']}", flush=True)
        finally:
            stage = "CLEANUP"
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                proc = None
            log.close()
            require("ISOLATED_DASHBOARD_STOPPED", True)
    after_agents = sorted(p.name for p in agents_folder.iterdir()) if agents_folder.is_dir() else []
    require("LAUNCHAGENTS_UNCHANGED", before_agents == after_agents)


if __name__ == "__main__":
    failed_stage = None
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        failed_stage = f"{stage}:{type(exc).__name__}"
        print("ACCEPTANCE_PROBE_ERROR=" + failed_stage, flush=True)
    finally:
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        all_states = list(checks.values())
        outcome = ("FAIL" if failed_stage or "FAIL" in all_states else
                   "PARTIAL" if "SKIPPED" in all_states else "PASS")
        report = {
            "schema_version": 1,
            "target_sha": PINNED,
            "check_mode": "DISPOSABLE_LOCAL_CLONE_AND_SQLITE_RO_SNAPSHOTS",
            "time_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "checks": checks,
            "details": details,
            "failed_stage_type": failed_stage,
            "mac_readonly_acceptance": outcome,
            "production_database_write_attempted": False,
            "mission_loop_restarted": False,
            "gmail_send_attempted": False,
            "git_push_attempted": False,
            "live_solana_rpc_attempted": False,
        }
        downloads = Path.home() / "Downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        output = downloads / f"frank-pr31-mac-readonly-{stamp}.zip"
        with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("mac-readonly-acceptance.json",
                             json.dumps(report, sort_keys=True, ensure_ascii=False,
                                        indent=2) + "\n")
        print("MAC_READONLY_ACCEPTANCE=" + outcome, flush=True)
        print("RESULT_ARCHIVE=" + str(output), flush=True)
        print("NO_PRODUCTION_RESTART=YES NO_GMAIL=YES NO_GIT_PUSH=YES", flush=True)
        if Path("/usr/bin/open").exists():
            subprocess.run(["/usr/bin/open", "-R", str(output)], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(0 if outcome == "PASS" else 2 if outcome == "PARTIAL" else 1)
