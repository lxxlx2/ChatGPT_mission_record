"""Integration sandbox builds from local Git objects; no source mutation/network."""
import json
from pathlib import Path
import subprocess

import pytest

from scripts import frank_pinned_joint_workspace as workspace


def git(repo, *cmd):
    return subprocess.run(
        ["git", "-C", str(repo), *cmd],
        capture_output=True, text=True, check=True, timeout=20,
    ).stdout.strip()


def commit(repo, filename, body, message):
    (repo / filename).write_text(body, encoding="utf-8")
    git(repo, "add", filename)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo_and_pins(tmp_path, monkeypatch):
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Synthetic Tester")
    git(repo, "config", "user.email", "local-test@example.invalid")
    base = commit(repo, "main.txt", "main fixture\n", "main")
    git(repo, "switch", "-c", "integration")
    candidate = commit(repo, "integration.txt", "integration fixture\n", "integration")
    git(repo, "switch", "main")
    git(repo, "switch", "-c", "c02")
    c02 = commit(repo, "c02.txt", "c02 fixture\n", "c02")
    git(repo, "switch", "main")
    git(repo, "switch", "-c", "f01")
    f01 = commit(repo, "f01.txt", "f01 fixture\n", "f01")
    git(repo, "switch", "main")
    monkeypatch.setattr(workspace, "MAIN", base)
    monkeypatch.setattr(workspace, "C02", c02)
    monkeypatch.setattr(workspace, "F01", f01)
    monkeypatch.setattr(workspace, "REVIEWED_PARENT", base)
    staging = tmp_path / "staging"
    staging.mkdir()
    (repo / "untracked-production-local.txt").write_text("do not touch")
    return repo, staging, candidate


def test_default_plan_only_never_creates_or_uses_git(tmp_path, capsys):
    assert workspace.main(["--source-repo", str(tmp_path),
                           "--staging-root", str(tmp_path)]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["status"] == "PLAN_ONLY"
    assert doc["network_invoked"] is False
    assert doc["workspace_created"] is False
    assert list(tmp_path.iterdir()) == []


def test_assemble_verified_pins_and_preserve_source_tree(repo_and_pins):
    repo, staging, candidate = repo_and_pins
    before = git(repo, "status", "--porcelain")
    name = "frank-joint-pinnedfixture"
    proof = workspace.assemble(repo, staging, name, candidate)
    target = staging / name
    assert proof["status"] == "FRANK_ISOLATED_ASSEMBLED"
    assert proof["pins"]["integrated_review_candidate"] == candidate
    assert target.is_dir()
    assert git(target, "rev-parse", "HEAD") == proof["integrated_head"]
    assert git(target, "status", "--porcelain") == ""
    assert (target / "main.txt").is_file()
    assert (target / "integration.txt").is_file()
    assert (target / "c02.txt").is_file()
    assert (target / "f01.txt").is_file()
    assert (repo / "untracked-production-local.txt").read_text() == "do not touch"
    assert git(repo, "status", "--porcelain") == before
    verified = workspace.verify(staging, name)
    assert verified["status"] == "FRANK_ISOLATED_VERIFIED"
    assert verified["integrated_head"] == proof["integrated_head"]
    with pytest.raises(ValueError, match="DESTINATION_ALREADY_EXISTS"):
        workspace.assemble(repo, staging, name, candidate)
    assert git(repo, "status", "--porcelain") == before


def test_cli_assemble_and_verify_only_when_explicit(repo_and_pins, capsys):
    repo, staging, candidate = repo_and_pins
    args = ["--staging-root", str(staging), "--name",
            "frank-joint-cli-proof"]
    assert workspace.main(["--assemble", "--source-repo", str(repo),
                           "--integration-sha", candidate, *args]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["status"] == "FRANK_ISOLATED_ASSEMBLED"
    assert workspace.main(["--verify", *args]) == 0
    check = json.loads(capsys.readouterr().out)
    assert check["status"] == "FRANK_ISOLATED_VERIFIED"
    target = staging / "frank-joint-cli-proof"
    (target / "new-user-research.txt").write_text("not tracked")
    assert workspace.main(["--verify", *args]) == 1
    assert capsys.readouterr().err.strip() == "FRANK_ISOLATED_WORKSPACE_REJECTED"
    assert (target / "new-user-research.txt").read_text() == "not tracked"


def test_reject_wrong_pin_and_overlapping_paths(repo_and_pins):
    repo, staging, candidate = repo_and_pins
    with pytest.raises(ValueError, match="PIN_INVALID"):
        workspace.assemble(repo, staging, "frank-joint-badpin", "f" * 39)
    with pytest.raises(ValueError, match="TEMP_ROOT_INVALID"):
        workspace.assemble(repo, repo, "frank-joint-overlap", candidate)
    with pytest.raises(ValueError, match="NAME_REQUIRED"):
        workspace.assemble(repo, staging, "unsafe", candidate)
    assert not any(staging.iterdir())


def test_manifest_tamper_or_head_drift_fails_closed(repo_and_pins):
    repo, staging, candidate = repo_and_pins
    name = "frank-joint-provenance"
    workspace.assemble(repo, staging, name, candidate)
    target = staging / name
    marker = target / ".git" / workspace.MARKER
    original = marker.read_text()
    doc = json.loads(original)
    doc["pins"]["main"] = "f" * 40
    marker.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="MANIFEST_INVALID"):
        workspace.verify(staging, name)
    marker.write_text(original)
    git(target, "checkout", "--detach", workspace.MAIN)
    with pytest.raises(ValueError, match="HEAD_DRIFT"):
        workspace.verify(staging, name)
