"""Run the fixed-SHA Frank acceptance matrix against isolated fixtures."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from mission_agent.signals.reconciliation import ReconciliationError, reconcile_snapshot


ROOT = Path(__file__).resolve().parents[1]
PYTHON_TESTS = (
    "tests/test_frank_local_signals.py", "tests/test_frank_v1.py",
    "tests/test_frank_category_capture.py", "tests/test_frank_historical_usd_tick.py",
    "tests/test_frank_historical_holder_compare.py", "tests/test_meme_market_and_rpc.py",
    "tests/test_frank_rebuild_buys.py", "tests/test_frank_rebuild_delivery.py",
    "tests/test_frank_scanner_reconciliation.py", "tests/test_frank_wallet_reconciliation_v2.py",
    "tests/test_frank_buy_latency_percentiles.py", "tests/test_frank_acceptance_runner.py",
    "tests/test_frank_multi_buy_proof.py", "tests/test_frank_configured_rpc.py",
    "tests/test_ca_job_checkpoint.py", "tests/test_frank_ca_job_rpc_budget.py",
    "tests/test_frank_ca_market_series.py", "tests/test_frank_ca_scoped_analyzer.py",
    "tests/test_frank_ca_launch_flow.py", "tests/test_meme_market_parity.py",
    "tests/test_mission_control_dashboard.py", "tests/test_meme_ca_trader_ui.py",
    "tests/research/test_frank_dashboard_priority_layout.py",
)
NODE_TESTS = ("tests/test_frank_ca_get_resume.mjs", "tests/test_frank_ca_report_render.mjs")


def _git(*args):
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def _assert_revision(expected):
    try:
        return (re.fullmatch("[0-9a-f]{40}", expected) is not None
                and _git("rev-parse", "HEAD") == expected
                and not _git("status", "--porcelain", "--untracked-files=all"))
    except (OSError, subprocess.CalledProcessError):
        return False


def _run(command, *, env=None):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, stdout=sys.stderr, env=env, timeout=240)
    except subprocess.TimeoutExpired:
        return {"status": "FAIL", "reason": "ISOLATED_TEST_TIMEOUT"}
    except OSError:
        return {"status": "BLOCKED", "reason": "RUNNER_UNAVAILABLE"}
    return {"status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode, "seconds": round(time.monotonic()-started, 3)}


def _chrome():
    binary = Path(os.environ.get(
        "FRANK_CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ))
    if not binary.is_file() or importlib.util.find_spec("playwright") is None:
        return {"status": "BLOCKED", "reason": "LOCAL_CHROME_OR_PYTHON_PLAYWRIGHT_REQUIRED"}
    web = _run(("node", "tests/test_frank_rebuild_browser.cjs"))
    http = _run((sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                 "tests/test_frank_rebuild_buys.py::test_browser_default_entry_filters_and_prefills_ca"),
                env={**os.environ, "FRANK_TEST_CHROMIUM": str(binary)})
    ca = _run(("node", "tests/test_frank_parallel_ca_browser.cjs"),
              env={**os.environ, "FRANK_PYTHON": sys.executable})
    status = "PASS" if web["status"] == http["status"] == ca["status"] == "PASS" else "FAIL"
    return {"status": status, "intercepted_assets": web, "local_http": http, "ca_worker": ca}


def _wallet(args):
    if args.snapshot is None:
        return {"status": "BLOCKED", "reason": "INDEPENDENT_WINDOW_REQUIRED"}
    evidence = (args.qualifications, args.qualifications_sha256, args.qualification_as_of)
    try:
        report = reconcile_snapshot(
            args.snapshot, args.snapshot_sha256, args.reference, args.reference_sha256,
            scanner_source_id=args.scanner_source_id,
            buy_qualifications=evidence if args.qualifications is not None else None,
            buy_archive_root=args.buy_archive_root, buy_legacy_archive_root=args.buy_legacy_archive_root,
        )
    except ReconciliationError:
        return {"status": "FAIL", "reason": "WINDOW_INPUT_REJECTED"}
    fields = (
        "status", "scope", "start_slot", "end_slot", "scanner_cursor_slot",
        "reference_signatures", "unexpected_indexed_signatures", "stages",
        "snapshot_sha256", "reference_sha256", "reference_capture_sha256",
        "reference_provenance", "buy_admission",
    )
    return {key: report[key] for key in fields if key in report}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--allow-partial", action="store_true",
                        help="Exit zero after required offline checks; does not indicate release approval")
    parser.add_argument("--chrome", action="store_true", help="Require isolated Chrome with local Playwright")
    parser.add_argument("--require-wallet-window", action="store_true",
                        help="Require a matched window and per-transaction buy evidence")
    parser.add_argument("--max-index-p95-seconds", type=float,
                        help="Apply an explicit SLA to complete timing samples from the supplied window")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--snapshot-sha256")
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--reference-sha256")
    parser.add_argument("--scanner-source-id")
    parser.add_argument("--qualifications", type=Path)
    parser.add_argument("--qualifications-sha256")
    parser.add_argument("--qualification-as-of", type=int)
    parser.add_argument("--buy-archive-root", type=Path, help="Trusted absolute archive directory for legacy buys")
    parser.add_argument("--buy-legacy-archive-root", type=Path, help="Optional second trusted archive directory")
    args = parser.parse_args(argv)
    window = (args.snapshot, args.snapshot_sha256, args.reference,
              args.reference_sha256, args.scanner_source_id)
    qualification = (args.qualifications, args.qualifications_sha256, args.qualification_as_of)
    if ((any(value is not None for value in window) and None in window)
            or (any(value is not None for value in qualification)
                and (None in qualification or None in window))):
        parser.error("supply all of the window inputs, and all qualification inputs if used")
    if ((args.buy_archive_root is not None and (None in qualification or not args.buy_archive_root.is_absolute()))
            or (args.buy_legacy_archive_root is not None
                and (args.buy_archive_root is None or not args.buy_legacy_archive_root.is_absolute()))):
        parser.error("supply buy qualification inputs and absolute archive paths, with the primary archive first")
    threshold = args.max_index_p95_seconds
    if threshold is not None and (not math.isfinite(threshold) or threshold <= 0):
        parser.error("P95 threshold must be finite and positive")
    if not _assert_revision(args.source_sha):
        print(json.dumps({"status": "FAIL", "reason": "SOURCE_SHA_OR_WORKTREE_MISMATCH",
                          "release": {"status": "NO_GO"}}))
        return 1

    python = _run((sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "-k", "not browser_default_entry", *PYTHON_TESTS))
    node = _run(("node", "--test", *NODE_TESTS))
    chrome = (_chrome() if args.chrome
              else {"status": "BLOCKED", "reason": "ISOLATED_CHROME_NOT_RUN"})
    wallet = _wallet(args)
    buys = wallet.get("buy_admission", {})
    window_matched = (wallet["status"] == buys.get("status") == "MATCHED_WITHIN_SUPPLIED_WINDOW")
    timing = buys.get("chain_to_index", {})
    index_p95 = timing.get("p95_seconds")
    sla = {"status": "NOT_SCORED", "reason": "THRESHOLD_NOT_SET"}
    if threshold is not None:
        if not window_matched or index_p95 is None or timing["unknown_count"]:
            sla = {"status": "BLOCKED", "reason": "COMPLETE_SCORABLE_WINDOW_REQUIRED"}
        else:
            sla = {"status": "PASS" if index_p95 <= threshold else "FAIL",
                   "threshold_seconds": threshold, "p95_seconds": index_p95,
                   "sample_count": timing["sample_count"]}
    source_intact = _assert_revision(args.source_sha)
    failures = (not source_intact or any(row["status"] != "PASS" for row in (python, node))
                or (args.chrome and chrome["status"] != "PASS")
                or wallet["status"] in {"GAPS", "FAIL"} or sla["status"] == "FAIL")
    required_evidence_missing = ((args.require_wallet_window and not window_matched)
                                or sla["status"] == "BLOCKED")
    report = {
        "status": "FAIL" if failures else "PARTIAL",
        "source_sha": args.source_sha, "source_intact": source_intact,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "isolated_python": python, "isolated_node": node, "isolated_chrome": chrome,
        "supplied_wallet_window": wallet, "wallet_index_sla": sla,
        "live_ca_freshness_and_latency": {"status": "BLOCKED", "reason": "LIVE_MEASUREMENT_REQUIRED"},
        "real_joint_pool_full_holder_parity": {"status": "NOT_VERIFIED"},
        "real_recipient_delivery": {"status": "NOT_VERIFIED"},
        "release": {"status": "NO_GO", "reason": "REAL_CA_JOINT_PARITY_AND_DELIVERY_NOT_VERIFIED"},
    }
    print(json.dumps(report, sort_keys=True))
    return 1 if failures else 2 if required_evidence_missing or not args.allow_partial else 0


if __name__ == "__main__":
    raise SystemExit(main())
