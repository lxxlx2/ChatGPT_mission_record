"""Emit evidence for verified local fixture gates, never for live deployment.

From the local-agent directory:
  python -B tests/fixtures/frank_rebuild_offline_acceptance.py --commit "$(git rev-parse HEAD)"

Use --source-snapshot for a Git-free, independently acquired source snapshot.
That records a fingerprint, not verified Git provenance. No Chrome binary,
production workspace, account, real market source or notification is needed.
"""
import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
from weakref import WeakSet


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from mission_agent.meme.job_checkpoint import source_fingerprint


FIXTURE_GATES = {
    "S11_CATEGORY_CAPTURE": ("test_frank_category_capture",),
    "S12_EXACT_SECOND_USD_INPUT": ("test_frank_historical_usd_tick",),
    "S12_LOCAL_USD_BUILD_AND_READ": ("test_frank_build_usd_evidence",),
    "S08_INDEPENDENT_HOLDER_INPUT": ("test_frank_historical_holder_compare",),
    "C13_SCOPE_AND_PACING": ("test_frank_parallel_ca_scopes", "test_frank_shared_provider_pacing", "test_frank_dex_market_pacing"),
    "PERSON_SCOPE_AND_DRY_RUN": ("test_frank_staged_person_scope",),
}
UNMEASURED = {
    "CHROME_ON_MAC": "requires an attached browser host; run test_frank_rebuild_browser.cjs and test_frank_parallel_ca_browser.cjs",
    "ACTUAL_NEW_MINT_CATEGORY_AND_LATENCY": "requires a verified contemporaneous market-category source",
    "ACTUAL_TRADE_TIME_USD": "requires genuine archived observations bound to exact payment asset and trade time",
    "ACTUAL_PROVIDER_CONCURRENCY_AND_LATENCY": "requires real source-approved cold/warm/throttle/pool comparison",
    "ACTUAL_ACCOUNT_AND_POOL_PARITY": "requires complete same-slot independent evidence",
    "ACTUAL_PERSON_RUNTIME_AND_DELIVERY": "production candidates and external sends deliberately not enabled",
}


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)


def code_identity(expected, snapshot):
    result = git("rev-parse", "--verify", "HEAD")
    if result.returncode:
        if snapshot:
            return "SOURCE_FINGERPRINT_ONLY"
        raise ValueError("exact Git checkout required (or explicitly use --source-snapshot)")
    if result.stdout.strip() != expected:
        raise ValueError("current Git HEAD differs from --commit")
    clean = git("status", "--porcelain=v1", "--untracked-files=all", "--", "mission_agent", "scripts", "tests", "config")
    if clean.returncode or clean.stdout:
        raise ValueError("product, script or test worktree differs from pinned HEAD")
    return "GIT_HEAD_AND_CLEAN_PRODUCT_TEST_PATHS"


def module_evidence(name, modules):
    suite = unittest.TestSuite()
    inputs = {}
    output = io.StringIO()
    started = time.perf_counter()
    with redirect_stdout(output), redirect_stderr(output):
        for module_name in modules:
            module = importlib.import_module(module_name)
            tests = unittest.defaultTestLoader.loadTestsFromModule(module)
            if tests.countTestCases() < 1:
                raise RuntimeError("No tests for " + module_name)
            suite.addTests(tests)
            path = Path(module.__file__).resolve()
            inputs[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        result = unittest.TextTestRunner(stream=output, verbosity=0).run(suite)
    total = result.testsRun
    failing = [test.id() for test, _ in result.failures + result.errors] + [test.id() for test in result.unexpectedSuccesses]
    skipped = [test.id() for test, _ in result.skipped]
    return {
        "gate": name, "kind": "SYNTHETIC_FIXTURES_ONLY",
        "status": "PASS" if result.wasSuccessful() and total and not skipped else "FAIL",
        "test_count": total, "failed": failing,
        "skipped": skipped, "inputs_sha256": inputs,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def install_fixture_audit():
    servers = WeakSet()

    def local_fixtures_only(event, args):
        if event == "socket.bind":
            sock, address = args
            if address != ("127.0.0.1", 0):
                raise RuntimeError("only ephemeral loopback fixture binds are allowed")
            servers.add(sock)
        if event in {"socket.connect", "socket.getaddrinfo"}:
            address = args[1] if event == "socket.connect" else args[:2]
            if not isinstance(address, tuple) or len(address) != 2 or address[0] != "127.0.0.1":
                raise RuntimeError("only fixture loopback connections are allowed")
            for sock in list(servers):
                if sock.fileno() >= 0 and sock.getsockname() == address:
                    break
            else:
                raise RuntimeError("connection does not belong to an in-process fixture")
        if event in {"os.system", "subprocess.Popen"}:
            raise RuntimeError("no subprocess is allowed during fixture tests")

    sys.addaudithook(local_fixtures_only)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True, help="full expected Git SHA")
    parser.add_argument("--source-snapshot", action="store_true", help="explicitly allow a checkout without Git")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.commit):
        parser.error("expected a full lowercase Git SHA")
    try:
        identity = code_identity(args.commit, args.source_snapshot)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    install_fixture_audit()
    results = [module_evidence(gate, modules) for gate, modules in FIXTURE_GATES.items()]
    doc = {
        "schema_version": 1, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit_supplied_by_runner": args.commit, "code_identity": identity,
        "product_source_sha256": source_fingerprint(),
        "usd_evidence_builder_sha256": hashlib.sha256((ROOT / "scripts/frank_build_usd_evidence.py").read_bytes()).hexdigest(),
        "acceptance_runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "ca_registry_sha256": hashlib.sha256((ROOT / "config/meme_special_addresses.json").read_bytes()).hexdigest(),
        "fixture_gates": results,
        "independent_gates": [{"gate": gate, "status": "NOT_RUN", "reason": reason}
                              for gate, reason in UNMEASURED.items()],
        "production_cutover": "NO_GO",
    }
    print(json.dumps(doc, ensure_ascii=False, indent=2))
    return 0 if all(gate["status"] == "PASS" for gate in results) else 1


if __name__ == "__main__":
    sys.exit(main())
