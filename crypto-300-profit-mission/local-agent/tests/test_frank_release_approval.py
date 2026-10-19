"""Isolated signed-release and MC-loop-only stop tests, no real launchctl."""
import hashlib
import importlib.util
import json
import os
import plistlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mission_agent.mission_control.release_approval import (
    SCOPE, trusted_checkout_identity, verify_signed_release_approval,
)


@pytest.fixture
def signed_fixture(tmp_path):
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    subprocess.run(
        ["/usr/bin/openssl", "genpkey", "-algorithm", "RSA",
         "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(private)],
        check=True, capture_output=True, timeout=15,
    )
    subprocess.run(
        ["/usr/bin/openssl", "pkey", "-in", str(private),
         "-pubout", "-out", str(public)],
        check=True, capture_output=True, timeout=10,
    )
    policy = tmp_path / "policy.json"
    policy.write_bytes(b'{"status":"FROZEN_APPROVED","live_delivery_approved":true}\n')
    sha = hashlib.sha256(policy.read_bytes()).hexdigest()
    commit = "a" * 40
    now = datetime.now(timezone.utc)
    record = tmp_path / "release.json"
    signature = tmp_path / "release.sig"
    payload = {
        "schema_version": 1, "scope": SCOPE, "policy_sha256": sha,
        "integration_sha": commit, "approved_by": "test-human-signing-key",
        "approved_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "deployment_approved": False,
    }
    def resign(data):
        record.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        subprocess.run(
            ["/usr/bin/openssl", "dgst", "-sha256", "-sign", str(private),
             "-out", str(signature), str(record)],
            check=True, capture_output=True, timeout=10,
        )
    resign(payload)
    return {
        "record_path": record, "signature_path": signature,
        "policy_path": policy, "externally_approved_sha": sha,
        "code_commit_sha": commit, "trusted_key": public,
        "enforce_protected_key": False,
        "payload": payload, "resign": resign,
        "now": now,
    }


def _args(fixture):
    return {k: v for k, v in fixture.items()
            if k in {"record_path","signature_path","policy_path",
                     "externally_approved_sha","code_commit_sha",
                     "trusted_key","enforce_protected_key","now"}}


def test_signed_user_release_approval_validates_both_byte_sha_and_code(signed_fixture):
    result = verify_signed_release_approval(**_args(signed_fixture))
    assert result["scope"] == SCOPE
    assert result["policy_sha256"] == signed_fixture["externally_approved_sha"]
    assert result["integration_sha"] == "a" * 40


@pytest.mark.parametrize("change", ["wrong_policy", "wrong_commit", "expired",
                                      "tamper", "fake_scope", "wrong_deploy_flag"])
def test_signed_approval_fails_closed(signed_fixture, change):
    f = signed_fixture
    args = _args(f)
    if change == "wrong_policy":
        args["externally_approved_sha"] = "b" * 64
    elif change == "wrong_commit":
        args["code_commit_sha"] = "b" * 40
    elif change == "expired":
        p = dict(f["payload"])
        p["expires_at"] = (f["now"] - timedelta(seconds=1)).isoformat()
        f["resign"](p)
    elif change == "fake_scope":
        p = dict(f["payload"])
        p["scope"] = "V1_SOURCE_AND_MC_UNAUTHORIZED"
        f["resign"](p)
    elif change == "wrong_deploy_flag":
        p = dict(f["payload"])
        p["deployment_approved"] = True
        f["resign"](p)
    elif change == "tamper":
        f["record_path"].write_bytes(f["record_path"].read_bytes() + b" ")
    with pytest.raises(ValueError, match="APPROVAL_"):
        verify_signed_release_approval(**args)


def test_self_computed_sha_without_a_user_signature_is_not_approval(signed_fixture):
    f = signed_fixture
    f["signature_path"].write_bytes(b"not-an-authentic-signature")
    with pytest.raises(ValueError, match="APPROVAL_SIGNATURE_INVALID"):
        verify_signed_release_approval(**_args(f))


def test_public_key_must_be_provisioned_in_protected_external_location(signed_fixture):
    args = _args(signed_fixture)
    args["enforce_protected_key"] = True
    with pytest.raises(ValueError, match="EXTERNAL_APPROVAL_TRUST_ANCHOR_UNSAFE"):
        verify_signed_release_approval(**args)


def _safe_stop_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "mc_loop_only_safe_stop.py"
    spec = importlib.util.spec_from_file_location("frank_mc_stop_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_loop_only_stop_targets_one_exact_agent_and_never_dashboard(tmp_path):
    module = _safe_stop_module()
    home = tmp_path / "home"
    runner = home / "Library" / "Application Support" / "FrankMeme" / "mission-loop.sh"
    plist = home / "Library" / "LaunchAgents" / "com.testuser.frank-meme.loop.plist"
    runner.parent.mkdir(parents=True)
    plist.parent.mkdir(parents=True)
    runner.write_text("test-owned loop runner only")
    plist.write_bytes(plistlib.dumps({
        "Label": "com.testuser.frank-meme.loop",
        "ProgramArguments": [str(runner)],
    }))
    plan = module.stop_plan(home, 501, "testuser")
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)
    module.stop_loop_only(plan, run=fake_run)
    assert calls == [
        ["launchctl", "disable", "gui/501/com.testuser.frank-meme.loop"],
        ["launchctl", "bootout", "gui/501", str(plist)],
    ]
    assert "dashboard" not in json.dumps(calls).lower()
    assert plan["mc_evaluation_will_stop"] is True
    assert plan["v1_source_touched"] is False


def test_loop_only_stop_rejects_foreign_or_symlinked_plist(tmp_path):
    module = _safe_stop_module()
    home = tmp_path / "home"
    runner = home / "Library" / "Application Support" / "FrankMeme" / "mission-loop.sh"
    plist = home / "Library" / "LaunchAgents" / "com.testuser.frank-meme.loop.plist"
    runner.parent.mkdir(parents=True)
    plist.parent.mkdir(parents=True)
    runner.write_text("test")
    plist.write_bytes(plistlib.dumps({
        "Label": "com.testuser.frank-meme.dashboard",
        "ProgramArguments": [str(runner)],
    }))
    with pytest.raises(ValueError, match="LOOP_ONLY_TARGET_MISMATCH"):
        module.stop_plan(home, 501, "testuser")


def _init_git_repo(root: Path, note: str) -> str:
    root.mkdir()
    subprocess.run(["/usr/bin/git","-C",str(root),"init","-q"],check=True)
    subprocess.run(
        ["/usr/bin/git","-C",str(root),
         "-c","user.name=Isolated Test","-c","user.email=git-test@example.invalid",
         "commit","-q","--allow-empty","-m",note],
        check=True,
    )
    return subprocess.check_output(
        ["/usr/bin/git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()


def test_git_identity_cannot_be_redirected_by_inherited_git_environment(
    signed_fixture, tmp_path, monkeypatch
):
    other=tmp_path/"repo-A"
    actual=tmp_path/"repo-B"
    signed_sha=_init_git_repo(other,"signed unrelated repo A")
    actual_sha=_init_git_repo(actual,"actual checked-out code B")
    assert signed_sha != actual_sha

    # First independently reproduce the vulnerability with real system git.
    monkeypatch.setenv("GIT_DIR",str(other/".git"))
    monkeypatch.setenv("GIT_WORK_TREE",str(other))
    monkeypatch.setenv("GIT_CONFIG_COUNT","1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0","core.bare")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0","false")
    poisoned=subprocess.check_output(
        ["/usr/bin/git","-C",str(actual),"rev-parse","HEAD"],text=True
    ).strip()
    assert poisoned==signed_sha

    # The release identity helper must derive B even if A is inherited.
    checked_sha=trusted_checkout_identity(actual)
    assert checked_sha==actual_sha
    payload=dict(signed_fixture["payload"])
    payload["integration_sha"]=signed_sha
    signed_fixture["resign"](payload)
    args=_args(signed_fixture)
    args["code_commit_sha"]=checked_sha
    with pytest.raises(ValueError,match="APPROVAL_POLICY_OR_CODE_MISMATCH"):
        verify_signed_release_approval(**args)


def test_live_cli_rejects_real_signature_for_wrong_inherited_git_repo(
    signed_fixture, tmp_path, monkeypatch
):
    import scripts.mission_meme_v1 as entry
    other=tmp_path/"repo-A"
    actual=tmp_path/"repo-B"
    signed_sha=_init_git_repo(other,"approved only repo A")
    actual_sha=_init_git_repo(actual,"running code repo B")
    assert signed_sha!=actual_sha
    payload=dict(signed_fixture["payload"])
    payload["integration_sha"]=signed_sha
    signed_fixture["resign"](payload)

    monkeypatch.setenv("GIT_DIR",str(other/".git"))
    monkeypatch.setenv("GIT_WORK_TREE",str(other))
    monkeypatch.setattr(entry,"__file__",str(actual/"scripts"/"mission_meme_v1.py"))
    def really_verify(**kwargs):
        return verify_signed_release_approval(
            **kwargs,
            trusted_key=signed_fixture["trusted_key"],
            enforce_protected_key=False,
            now=signed_fixture["now"],
        )
    monkeypatch.setattr(entry,"verify_signed_release_approval",really_verify)
    monkeypatch.setattr(entry,"MissionMemeService",lambda **kw:
                        pytest.fail("Unapproved CLI must not construct a live service"))
    monkeypatch.setattr(sys,"argv",[
        "mission_meme_v1.py","cycle",
        "--production-root",str(tmp_path/"prod"),
        "--control-root",str(tmp_path/"control"),
        "--policy",str(signed_fixture["policy_path"]),
        "--live-delivery",
        "--approved-policy-sha256",signed_fixture["externally_approved_sha"],
        "--approval-record",str(signed_fixture["record_path"]),
        "--approval-signature",str(signed_fixture["signature_path"]),
    ])
    with pytest.raises(ValueError,match="APPROVAL_POLICY_OR_CODE_MISMATCH"):
        entry.main()
