"""Read-only, fail-closed diagnosis of old Mac runtime fingerprint mismatches."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import frank_pr39_controlled_release as release


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def fixture_repo(tmp_path):
    root = tmp_path / "repo"
    prod = root / "crypto-300-profit-mission" / "local-agent"
    for name, data in (
        ("mission_agent/mission_control/frank.py", "ORIGINAL='no trade'\n"),
        ("mission_agent/mission_control/static/index.html", "<main>old</main>\n"),
        ("config/follow_policy_v1.approved.json", '{"status":"FROZEN_APPROVED"}\n'),
        ("scripts/mission_meme_v1.py", "print('mission')\n"),
    ):
        path = prod / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
    git(root, "init", "-q")
    git(root, "add", ".")
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Tester",
                    "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "frozen base"], check=True)
    return root, prod


def test_legacy_source_diagnostic_shows_specific_changed_hashes_without_approving(tmp_path):
    repo, prod = fixture_repo(tmp_path)
    before = release.source_drift_diagnostic(prod)
    assert before["status"] == "BYTES_VERIFIED"
    assert before["different_or_missing_count"] == 0
    candidate = prod / "mission_agent/mission_control/static/index.html"
    candidate.write_text("<main>previously approved hot patch</main>\n")
    report = release.source_drift_diagnostic(prod)
    assert report["status"] == "UNVERIFIED_SOURCE_DRIFT"
    assert report["different_or_missing_count"] == 1
    assert report["mismatches"][0]["file"] == "mission_agent/mission_control/static/index.html"
    assert len(report["mismatches"][0]["expected_git_blob"]) == 40
    assert len(report["mismatches"][0]["observed_git_blob"]) == 40
    assert str(tmp_path) not in json.dumps(report)
    with pytest.raises(RuntimeError, match="SOURCE_MIXED_BYTES"):
        release.source_manifest(prod)


def test_diagnostic_does_not_hide_untracked_scripts_or_missing_files(tmp_path):
    repo, prod = fixture_repo(tmp_path)
    (prod / "mission_agent/unknown.py").write_text("x=1")
    (prod / "config/follow_policy_v1.approved.json").unlink()
    report = release.source_drift_diagnostic(prod)
    assert report["untracked_executable_count"] == 1
    assert report["different_or_missing_count"] == 1
    assert report["mismatches"][0]["reason"] == "MISSING_OR_SYMLINK"
    assert report["unexpected_source_paths"] == ["mission_agent/unknown.py"]
    assert report["status"] == "UNVERIFIED_SOURCE_DRIFT"


@pytest.mark.parametrize("runner_delta,expected", [
    (-20.0, "RUNNER_OLDER_THAN_PROCESS"),
    (0.35, "UNVERIFIED_SAME_SECOND"),
    (2.0, "RUNNER_NEWER_THAN_PROCESS"),
])
def test_runner_timestamp_probe_only_labels_ambiguity(tmp_path, monkeypatch, runner_delta, expected):
    runner = tmp_path / "dashboard.sh"
    runner.write_text("LOCAL_AGENT=\"/not-a-real-agent\"\n")
    started = int(time.time()) - 600
    os.utime(runner, (started + runner_delta, started + runner_delta))
    mac = SimpleNamespace(runners={"dashboard": runner},
                          labels={"dashboard": "fake.dashboard"},
                          launch=lambda _: (4242, "fake output"))
    stamp = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime(started))
    orig_run = release.run
    def fake_run(argv, **kw):
        if argv[:2] == ["/bin/ps", "-p"]:
            return stamp
        raise AssertionError("unexpected subprocess")
    monkeypatch.setattr(release, "run", fake_run)
    result = release.runner_start_time_diagnostic(mac, "dashboard", runner.read_text())
    assert result["status"] == expected
    assert result["pid"] == 4242
    assert str(tmp_path) not in json.dumps(result)
    assert result["timestamp_resolution"] == "ps_lstart_one_second"
