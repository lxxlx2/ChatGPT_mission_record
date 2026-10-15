"""Approved Mac passive source preflight; test-only temporary repositories."""
import json
import shlex
import subprocess

from scripts import frank_mac_readonly_preflight as preflight


def _git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True,
        text=True, timeout=8,
    ).stdout.strip()


def _test_git(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "file.txt").write_text("original", encoding="utf-8")
    _git(repo, "add", "file.txt")
    _git(repo, "commit", "-qm", "initial")
    return repo


def test_repo_passive_reader_does_not_modify_source(tmp_path, monkeypatch):
    repo = _test_git(tmp_path)
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", preflight.EVIDENCE_REF, sha)
    monkeypatch.setattr(preflight, "EXPECTED_PINS", {
        "test": sha,
        "pr73_reviewed": "5755b8b96080f21635eaa5354588cbb8f6561ab0",
    })
    monkeypatch.setattr(preflight, "EXPECTED_EVIDENCE_SHA", sha)
    (repo / "new-unsaved.txt").write_text("research-data", encoding="utf-8")
    before = {
        "tracked": (repo / "file.txt").read_bytes(),
        "unsaved": (repo / "new-unsaved.txt").read_bytes(),
        "index": (repo / ".git/index").read_bytes(),
        "status": _git(repo, "status", "--porcelain"),
    }
    out = preflight.inspect_repo(repo)
    assert out["state"] == "READ_ONLY_INSPECTED"
    assert out["source_changes"] == "HAS_USER_CHANGES"
    assert out["fixed_git_objects"]["test"] == "PRESENT"
    assert out["historical_evidence_ref"] == "EXPECTED_LOCAL_SHA"
    assert out["head_matches_reviewed_pr73"] is False
    assert (repo / "file.txt").read_bytes() == before["tracked"]
    assert (repo / "new-unsaved.txt").read_bytes() == before["unsaved"]
    assert (repo / ".git/index").read_bytes() == before["index"]
    assert _git(repo, "status", "--porcelain") == before["status"]


def test_session_inventory_only_checks_file_existence(tmp_path):
    sessions = tmp_path / "manual-sessions"
    s1 = sessions / "session-synthetic"
    raw = s1 / "wire" / "owner-test" / "manifest.json"
    raw.parent.mkdir(parents=True)
    raw.write_text("intentionally invalid json and private wallet example",
                   encoding="utf-8")
    sidecar = s1 / "positions.sqlite"
    sidecar.write_bytes(b"not actually sqlite private bytes")
    single = sessions / "session-other"
    single.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    (sessions / "session-symlink").symlink_to(external, target_is_directory=True)
    result = preflight.inspect_private_sessions(sessions)
    assert result == {
        "state": "INVENTORY_ONLY", "sessions": 2,
        "session_scan_truncated": False,
        "sessions_with_sidecar_file": 1,
        "sessions_with_wire_manifest": 1,
        "sessions_with_both_files": 1,
        "contents_or_sha_verified": False,
        "session_freshness_verified": False,
    }
    assert preflight.inspect_private_sessions(
        sessions / "session-symlink")["state"] == "UNSAFE_SYMLINK"


def test_missing_sources_are_unverified_without_any_network(tmp_path, monkeypatch):
    def forbid(*args, **kwargs):
        raise AssertionError("unexpected Git/port command")
    monkeypatch.setattr(preflight, "safe_exec", forbid)
    monkeypatch.setattr(preflight, "inspect_port",
                        lambda _: "NO_LISTENER_SEEN")
    doc = preflight.run(home=tmp_path)
    assert doc["known_review_clone"]["state"] == "NOT_FOUND_OR_UNSAFE"
    assert doc["private_f02_session_inventory"]["state"] == "NOT_FOUND"
    assert all(v is False for v in doc["side_effects"].values())
    assert "private" not in json.dumps(doc).lower().split("observed_at_utc")[0]


def test_output_sanitized_and_reports_only_port_presence(tmp_path, monkeypatch,
                                                          capsys):
    repo = _test_git(tmp_path)
    monkeypatch.setattr(preflight, "inspect_port",
                        lambda p: "LISTENER_PRESENT" if p == 18766
                        else "NO_LISTENER_SEEN")
    result = preflight.run(home=tmp_path, repo=repo)
    raw = json.dumps(result)
    assert str(repo) not in raw
    assert str(tmp_path) not in raw
    assert "file.txt" not in raw
    assert "localhost" not in raw
    assert result["loopback_port_listener_presence"]["f01_c02_control"] == (
        "LISTENER_PRESENT")
    # The CLI must never enumerate the test runner's actual user home.
    monkeypatch.setattr(preflight.Path, "home", lambda: tmp_path)
    assert preflight.main(["--repo", str(repo)]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["private_f02_session_inventory"]["state"] == "NOT_FOUND"
    assert "files_written_or_deleted" in doc["side_effects"]
    assert doc["side_effects"]["service_or_socket_started"] is False


def test_git_failure_and_no_lsof_report_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: None)
    assert preflight.inspect_port(18765) == "CANNOT_CHECK_NO_LSOF"
    empty = tmp_path / "not-git"
    empty.mkdir()
    assert preflight.inspect_repo(empty)["state"] == "NOT_A_STANDALONE_REPO"



def test_real_git_fsmonitor_helper_is_never_invoked(tmp_path):
    """Regression for independently reproduced PR74 P2, using real Git."""
    repo = _test_git(tmp_path)
    sentinel = tmp_path / "fsmonitor-executed.txt"
    helper = tmp_path / "fsmonitor-helper.sh"
    helper.write_text(
        "#!/bin/sh\\n"
        + "printf unexpected > " + shlex.quote(str(sentinel)) + "\\n",
        encoding="utf-8",
    )
    helper.chmod(0o755)
    _git(repo, "config", "core.fsmonitor", str(helper))
    unsaved = repo / "unsaved.txt"
    unsaved.write_bytes(b"valuable-user-research")
    index_before = (repo / ".git" / "index").read_bytes()
    tracked_before = (repo / "file.txt").read_bytes()
    unsaved_before = unsaved.read_bytes()
    head_before = _git(repo, "rev-parse", "HEAD")

    doc = preflight.inspect_repo(repo)

    assert doc["state"] == "READ_ONLY_INSPECTED"
    assert doc["source_changes"] == "HAS_USER_CHANGES"
    assert not sentinel.exists(), "git status invoked configured core.fsmonitor"
    assert (repo / ".git" / "index").read_bytes() == index_before
    assert (repo / "file.txt").read_bytes() == tracked_before
    assert unsaved.read_bytes() == unsaved_before
    assert _git(repo, "rev-parse", "HEAD") == head_before
