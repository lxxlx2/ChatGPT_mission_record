"""Immutable PR #39 release staging: real git archive, marker verification, read-only bits.

Production runners must never point at an operator checkout or a cache clone. These tests
run real git against a temporary repository and never touch Mission production state.
"""
import importlib.util
import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

TOOL = Path(__file__).resolve().parents[1] / "scripts" / "frank_pr39_controlled_release.py"
spec = importlib.util.spec_from_file_location("frank_pr39_controlled_release", TOOL)
rel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rel)

FILES = {
    "mission_agent/__init__.py": "",
    "mission_agent/mission_control/static/app.js": "const UI='new';// 未确认（已识别资金腿\n",
    "config/follow_policy_v1.approved.json": '{"policy":"approved"}\n',
    "scripts/mission_meme_v1.py": "print('mission')\n",
}


def _git_env():
    return {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}


def _make_repo(tmp_path, prefix):
    """Repository with the local-agent tree under `prefix` (the nested cache-clone layout)."""
    repo = tmp_path / "clone"
    for rel_path, content in FILES.items():
        target = repo / prefix / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "release"], check=True, env=_git_env())
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    root = repo / prefix if prefix else repo
    source = {rel_path: rel.sha(root / rel_path) for rel_path in FILES}
    return repo, root, sha, source


def _mac(tmp_path):
    return SimpleNamespace(support=tmp_path / "support")


@pytest.mark.parametrize("prefix", ["", "crypto-300-profit-mission/local-agent"])
def test_immutable_release_is_exact_marker_verified_and_read_only(tmp_path, prefix):
    repo, root, sha, source = _make_repo(tmp_path, prefix)
    mac = _mac(tmp_path)
    final = rel.stage_immutable_release(mac, root, sha, source)
    assert final == mac.support / "pr39-immutable-releases" / sha[:12]
    assert (final / "mission_agent/__init__.py").is_file()
    assert rel.source_manifest(final) == source
    for name in ("mission_agent/mission_control/static/app.js", "config/follow_policy_v1.approved.json"):
        mode = stat.S_IMODE(os.stat(final / name).st_mode)
        assert mode & 0o222 == 0, "staged source must be read-only"
    assert not any(p.name.startswith(".staging") for p in mac.support.rglob("*"))


def test_tampered_immutable_file_is_rejected_by_runtime_manifest(tmp_path):
    repo, root, sha, source = _make_repo(tmp_path, "")
    final = rel.stage_immutable_release(_mac(tmp_path), root, sha, source)
    target = final / "mission_agent/mission_control/static/app.js"
    os.chmod(target, 0o644)
    target.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="RELEASE_MANIFEST_MISMATCH"):
        rel.source_manifest(final)


def test_extra_source_file_in_immutable_release_is_rejected(tmp_path):
    repo, root, sha, source = _make_repo(tmp_path, "")
    final = rel.stage_immutable_release(_mac(tmp_path), root, sha, source)
    os.chmod(final / "mission_agent", 0o755)
    (final / "mission_agent/injected.py").write_text("X = 1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="RELEASE_EXTRA_FILE"):
        rel.source_manifest(final)


def test_existing_release_with_different_source_is_refused(tmp_path):
    repo, root, sha, source = _make_repo(tmp_path, "")
    mac = _mac(tmp_path)
    rel.stage_immutable_release(mac, root, sha, source)
    different = dict(source, **{"config/follow_policy_v1.approved.json": "0" * 64})
    with pytest.raises(RuntimeError, match="EXISTING_IMMUTABLE_RELEASE_MISMATCH"):
        rel.stage_immutable_release(mac, root, sha, different)


def test_unsafe_archive_member_cannot_be_staged(tmp_path, monkeypatch):
    repo, root, sha, source = _make_repo(tmp_path, "")
    real_run = subprocess.run

    def malicious(args, **kwargs):
        if "archive" in args:
            import io, tarfile
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w") as archive:
                info = tarfile.TarInfo("../escape.txt")
                payload = b"x"
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            return SimpleNamespace(stdout=buffer.getvalue(), returncode=0)
        return real_run(args, **kwargs)
    monkeypatch.setattr(rel.subprocess, "run", malicious)
    with pytest.raises(RuntimeError, match="ARCHIVE_MEMBER_UNSAFE"):
        rel.stage_immutable_release(_mac(tmp_path), root, sha, source)
    assert not (tmp_path / "escape.txt").exists()



def test_existing_source_with_writeable_permissions_is_rejected(tmp_path):
    _, root, commit, source = _make_repo(tmp_path, "")
    mac = _mac(tmp_path)
    final = rel.stage_immutable_release(mac, root, commit, source)
    target = final / "mission_agent/mission_control/static/app.js"
    os.chmod(target, 0o644)
    with pytest.raises(RuntimeError, match="EXISTING_RELEASE_NOT_READ_ONLY"):
        rel.stage_immutable_release(mac, root, commit, source)
