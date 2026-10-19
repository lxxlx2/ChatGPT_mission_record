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
    SCOPE, verify_signed_release_approval,
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
