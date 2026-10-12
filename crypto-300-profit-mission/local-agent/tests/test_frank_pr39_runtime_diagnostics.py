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


def test_documented_legacy_overlay_is_identified_without_waiving_source_integrity(tmp_path, monkeypatch):
    repo, prod = fixture_repo(tmp_path)
    for name in ("server.py", "static/app.js"):
        target = prod / "mission_agent/mission_control" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("original\n")
    git(repo, "add", ".")
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Tester",
                    "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "old UI baseline"], check=True)
    for name in ("server.py", "static/app.js", "delivery_review.py"):
        target = prod / "mission_agent/mission_control" / name
        target.write_text("documented legacy placeholder\n")
    expected = release.HISTORICAL_UI_LEGACY_BLOBS
    extra = release.HISTORICAL_UI_LEGACY_EXTRA
    base_run = release.run

    def verify_known_git_hashes(argv, **kw):
        if "rev-parse" in argv and len(argv) and str(argv[-1]).startswith("HEAD:"):
            for name, (baseline, _) in expected.items():
                if str(argv[-1]).endswith(name):
                    return baseline
        if "hash-object" in argv and argv:
            for name, (_, legacy) in expected.items():
                if str(argv[-1]).endswith(name):
                    return legacy
            for name, legacy in extra.items():
                if str(argv[-1]).endswith(name):
                    return legacy
        return base_run(argv, **kw)

    monkeypatch.setattr(release, "run", verify_known_git_hashes)
    report = release.source_drift_diagnostic(prod)
    assert report["historical_overlay_classification"] == "DOCUMENTED_LEGACY_DISK_BYTES_RUNTIME_UNVERIFIED"
    assert report["status"] == "UNVERIFIED_SOURCE_DRIFT"
    assert report["different_or_missing_count"] == 2
    assert report["untracked_executable_count"] == 1
    assert report["unexpected_source_git_blobs"] == extra
    assert "SCRIPT_OR_POLICY_APPROVED" not in json.dumps(report)

    monkeypatch.setattr(release, "run", base_run)
    with pytest.raises(RuntimeError, match="SOURCE_MIXED_BYTES"):
        release.source_manifest(prod)


def test_nonmatching_legacy_extra_stays_unverified(tmp_path):
    _, prod = fixture_repo(tmp_path)
    (prod / "mission_agent/mission_control/delivery_review.py").write_text("malicious=1\n")
    report = release.source_drift_diagnostic(prod)
    assert report["historical_overlay_classification"] == "NO_EXACT_LEGACY_MATCH"
    assert report["status"] == "UNVERIFIED_SOURCE_DRIFT"
    assert report["untracked_executable_count"] == 1


@pytest.mark.parametrize("late,expected", [
    (False, "ALL_OBSERVED_SOURCE_FILES_PREDATE_PROCESS_SECOND"),
    (True, "SOURCE_FILES_MAY_HAVE_CHANGED_AFTER_START")
])
def test_legacy_source_mtimes_are_measured_without_altering_live_data(tmp_path, monkeypatch, late, expected):
    _, prod = fixture_repo(tmp_path)
    start = int(time.time()) - 1000
    for name in ("mission_agent", "config"):
        for path in (prod / name).rglob("*"):
            if path.is_file():
                os.utime(path, (start - 60, start - 60))
    entry = prod / "scripts/mission_meme_v1.py"
    os.utime(entry, (start - 60, start - 60))
    changed = prod / "mission_agent/mission_control/frank.py"
    if late:
        os.utime(changed, (start + 8, start + 8))
    runner = tmp_path / "loop.sh"
    runner.write_text('LOCAL_AGENT="' + str(prod) + '"\n')
    mac = SimpleNamespace(runners={"loop": runner},
                          labels={"loop": "fake.loop"},
                          launch=lambda _: (321, "loaded"))
    stamp = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime(start))
    def fake_run(argv, **kwargs):
        if argv[:2] == ["/bin/ps", "-p"]:
            return stamp
        raise AssertionError("unexpected subprocess " + repr(argv))
    monkeypatch.setattr(release, "run", fake_run)
    report = release.source_start_temporal_diagnostic(mac, "loop")
    assert report["status"] == expected
    assert report["files_not_proven_to_predate_process_count"] == int(late)
    assert (report["late_source_files"] == []) is (not late)
    assert str(tmp_path) not in json.dumps(report)



def test_xnu_proc_bsdinfo_layout_and_verified_microsecond_birth(monkeypatch):
    import ctypes

    assert ctypes.sizeof(release._DarwinProcBSDInfo) == 136
    ps_second = 1791856800
    pid = 4321

    class FakeProcPidInfo:
        def __call__(self, supplied_pid, flavor, arg, buffer, supplied_size):
            assert supplied_pid == pid and flavor == 3 and arg == 0
            assert supplied_size == 136
            info = ctypes.cast(buffer, ctypes.POINTER(release._DarwinProcBSDInfo)).contents
            info.pbi_pid = pid
            info.pbi_start_tvsec = ps_second
            info.pbi_start_tvusec = 765432
            return supplied_size

    fake = SimpleNamespace(proc_pidinfo=FakeProcPidInfo())
    monkeypatch.setattr(release.sys, "platform", "darwin")
    monkeypatch.setattr(release.ctypes, "CDLL", lambda *a, **kw: fake)
    observed = release.darwin_precise_process_start(pid, ps_second)
    assert abs(observed - (ps_second + .765432)) < .000002
    with pytest.raises(RuntimeError, match="PROCESS_BIRTH_VS_PS_MISMATCH"):
        release.darwin_precise_process_start(pid, ps_second + 5)


def test_mac_precise_birth_can_disambiguate_same_second_old_runner(tmp_path, monkeypatch):
    runner = tmp_path / "dashboard.sh"
    runner.write_text("safe")
    started = int(time.time()) - 300
    os.utime(runner, (started + .57, started + .57))
    mac = SimpleNamespace(runners={"dashboard": runner},
                          labels={"dashboard": "fake.dashboard"},
                          launch=lambda _: (322, "loaded"))
    stamp = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime(started))
    def fake_run(argv, **kw):
        if argv[:2] == ["/bin/ps", "-p"]:
            return stamp
        raise AssertionError("unexpected command")
    monkeypatch.setattr(release, "run", fake_run)
    monkeypatch.setattr(release.sys, "platform", "darwin")
    monkeypatch.setattr(release, "darwin_precise_process_start",
                        lambda pid, second: float(second) + .85)
    result = release.runner_start_time_diagnostic(mac, "dashboard", runner.read_text())
    assert result["kernel_birth_check"] == "VERIFIED_AGAINST_PS_SECOND"
    assert result["status"] == "RUNNER_OLDER_THAN_PROCESS"
    assert result["runner_minus_precise_process_start_seconds"] < 0
    assert result["timestamp_resolution"] == "kernel_microsecond"


def test_mac_kernel_birth_unavailable_preserves_ambiguous_block(tmp_path, monkeypatch):
    runner = tmp_path / "dashboard.sh"
    runner.write_text("safe")
    started = int(time.time()) - 300
    os.utime(runner, (started + .57, started + .57))
    mac = SimpleNamespace(runners={"dashboard": runner},
                          labels={"dashboard": "fake.dashboard"},
                          launch=lambda _: (322, "loaded"))
    stamp = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime(started))
    monkeypatch.setattr(release, "run", lambda *_a, **_kw: stamp)
    monkeypatch.setattr(release.sys, "platform", "darwin")
    def unavailable(_pid, _reported):
        raise RuntimeError("KERNEL_PROCESS_BIRTH_UNAVAILABLE")
    monkeypatch.setattr(release, "darwin_precise_process_start", unavailable)
    result = release.runner_start_time_diagnostic(mac, "dashboard", runner.read_text())
    assert result["kernel_birth_check"] == "KERNEL_PROCESS_BIRTH_UNAVAILABLE"
    assert result["status"] == "UNVERIFIED_SAME_SECOND"
