import json

import pytest

from scripts import accept_frank_rebuild as runner


SHA = "a" * 40


@pytest.fixture
def isolated(monkeypatch):
    monkeypatch.setattr(runner, "_assert_revision", lambda actual: actual == SHA)
    monkeypatch.setattr(runner, "_run", lambda *args, **kw: {"status": "PASS"})
    return ["--source-sha", SHA]


def invoke(capsys, args):
    code = runner.main(args)
    return code, json.loads(capsys.readouterr().out)


def test_offline_run_defaults_to_partial_nonzero_and_explicit_opt_in_never_releases(isolated, capsys):
    code, report = invoke(capsys, isolated)
    assert (code, report["status"]) == (2, "PARTIAL")
    assert report["supplied_wallet_window"]["reason"] == "INDEPENDENT_WINDOW_REQUIRED"
    code, report = invoke(capsys, isolated + ["--allow-partial"])
    assert (code, report["status"], report["release"]["status"]) == (0, "PARTIAL", "NO_GO")
    assert report["live_ca_freshness_and_latency"]["status"] == "BLOCKED"
    assert report["real_joint_pool_full_holder_parity"]["status"] == "NOT_VERIFIED"
    assert report["real_recipient_delivery"]["status"] == "NOT_VERIFIED"


def test_partial_opt_in_cannot_bypass_explicit_wallet_or_chrome_requirement(isolated, capsys, monkeypatch):
    monkeypatch.setattr(runner, "_chrome", lambda: {"status": "BLOCKED", "reason": "NO_FIXTURE"})
    code, report = invoke(capsys, isolated + ["--allow-partial", "--require-wallet-window"])
    assert (code, report["status"]) == (2, "PARTIAL")
    code, report = invoke(capsys, isolated + ["--allow-partial", "--chrome"])
    assert (code, report["status"], report["release"]["status"]) == (1, "FAIL", "NO_GO")


@pytest.mark.parametrize(("unknown", "threshold", "code", "state"), [
    (0, "32", 0, "PASS"), (0, "30", 1, "FAIL"), (1, "32", 2, "BLOCKED"),
])
def test_sla_uses_known_original_nearest_rank_only(monkeypatch, isolated, capsys, unknown, threshold, code, state):
    matched = "MATCHED_WITHIN_SUPPLIED_WINDOW"
    monkeypatch.setattr(runner, "_wallet", lambda args: {
        "status": matched, "buy_admission": {"status": matched, "chain_to_index": {
            "p95_seconds": 31.2, "unknown_count": unknown, "sample_count": 20,
            "percentile_method": "NEAREST_RANK"}}})
    actual, report = invoke(capsys, isolated + ["--allow-partial", "--max-index-p95-seconds", threshold])
    assert (actual, report["wallet_index_sla"]["status"], report["release"]["status"]) == (code, state, "NO_GO")


def test_wrong_sha_or_worktree_never_starts_tests(monkeypatch, capsys):
    monkeypatch.setattr(runner, "_assert_revision", lambda expected: False)
    def denied(*a, **kw):
        raise AssertionError("must not run")
    monkeypatch.setattr(runner, "_run", denied)
    code, report = invoke(capsys, ["--source-sha", SHA])
    assert (code, report["reason"], report["release"]["status"]) == (1, "SOURCE_SHA_OR_WORKTREE_MISMATCH", "NO_GO")
