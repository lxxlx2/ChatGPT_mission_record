#!/usr/bin/env python3
"""Stage102: verify a real user-supplied Claude *chat* review archived in Git.

No Claude CLI, no background automation, no side effects on production.
The repo review receipt is authored only after the user supplies actual review
text; checks integrity and code binding, not cryptographic Claude identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    import monster_v4_stage99_mac_launchd_one_shot as stage99
except ImportError:
    from scripts import monster_v4_stage99_mac_launchd_one_shot as stage99

RECEIPT = (
    "crypto-300-profit-mission/monster/evidence/"
    "monster_stage102_actual_claude_chat_independent_review.json"
)
SCHEMA = "MONSTER_STAGE102_USER_SUPPLIED_CLAUDE_CHAT_REVIEW_RECEIPT_V1"
REQUIRED_SOURCES = (
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py",
    "crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py",
    ".github/workflows/monster-stage99-mac-one-shot-capture-safety.yml",
)
REVIEW_ORIGIN = "CLAUDE_CHAT_USER_SUPPLIED_FULL_OUTPUT"


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def verify_approved(*, root: Path | None = None, read_blob=None) -> dict:
    """A readable review record is necessary, NEVER sufficient without matching blobs.

    A review request, simulated test, source hash or CI green alone fails closed.
    """
    home = stage99.CLONE if root is None else root
    record = home / RECEIPT
    if not record.is_file():
        raise RuntimeError("STAGE102_REAL_CLAUDE_CHAT_REVIEW_MISSING_NO_INSTALL")
    try:
        review = json.loads(record.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise RuntimeError("STAGE102_REVIEW_RECORD_NOT_VALID_JSON") from None
    if (review.get("schema") != SCHEMA
        or review.get("source_origin") != REVIEW_ORIGIN
        or review.get("repository") != stage99.REPO_NAME
        or review.get("branch") != stage99.BRANCH):
        raise RuntimeError("STAGE102_REVIEW_IDENTITY_BRANCH_OR_SCHEMA_INVALID")
    if (review.get("verdict") != "APPROVE"
        or review.get("blocking_findings")
        or not isinstance(review.get("nonblocking_findings"), list)):
        raise RuntimeError("STAGE102_REAL_CLAUDE_CHAT_REVIEW_NOT_APPROVED")
    actual_text = review.get("full_claude_reply")
    if (not isinstance(actual_text, str) or len(actual_text.strip()) < 160
        or review.get("full_reply_sha256") != sha256(actual_text)):
        raise RuntimeError("STAGE102_MISSING_OR_MODIFIED_ACTUAL_REVIEW_TEXT")
    checks = review.get("reviewed_file_git_blobs")
    if not isinstance(checks, dict) or set(checks) != set(REQUIRED_SOURCES):
        raise RuntimeError("STAGE102_REVIEW_DOES_NOT_COVER_FROZEN_CORE_FILES")
    if read_blob is None:
        def read_blob(path):
            return stage99.git("hash-object", "--", path, capture=True)
    mismatches = [
        path for path in REQUIRED_SOURCES if (
            not isinstance(checks[path], str) or
            len(checks[path]) != 40 or
            read_blob(path) != checks[path]
        )
    ]
    if mismatches:
        raise RuntimeError("STAGE102_CODE_CHANGED_AFTER_INDEPENDENT_REVIEW")
    findings = review.get("reviewed_risks_and_test_evidence")
    if not isinstance(findings, list) or len(findings) < 3:
        raise RuntimeError("STAGE102_REVIEW_UNSUBSTANTIATED")
    # Important: SHA is only an integrity check; user-provided text is not an
    # authenticated Claude message. The assistant must separately inspect it.
    return {
        "status": "CHAT_REVIEW_RECORDED_MATCHING_SOURCE_AND_APPROVED",
        "source_origin": REVIEW_ORIGIN,
        "independent_model_origin_authentication": "USER_ATTESTED_NOT_CRYPTOGRAPHIC",
        "covered_file_count": len(REQUIRED_SOURCES),
        "full_reply_sha256": review["full_reply_sha256"],
    }


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        try:
            verify_approved(root=root, read_blob=lambda _: "a" * 40)
        except RuntimeError as exc:
            assert "MISSING" in str(exc)
        else:
            raise AssertionError("STAGE102_MUST_REQUIRE_REAL_CLAUDE_CHAT_RECEIPT")
        text = "Synthetic test-only review text " * 9
        source = {p: "a" * 40 for p in REQUIRED_SOURCES}
        receipt = {
            "schema": SCHEMA,
            "repository": stage99.REPO_NAME, "branch": stage99.BRANCH,
            "source_origin": REVIEW_ORIGIN,
            "verdict": "BLOCK",
            "full_claude_reply": text, "full_reply_sha256": sha256(text),
            "reviewed_file_git_blobs": source,
            "blocking_findings": ["test simulated block"],
            "nonblocking_findings": [],
            "reviewed_risks_and_test_evidence": ["clock", "git", "cleanup"],
        }
        dst = root / RECEIPT
        dst.parent.mkdir(parents=True)
        dst.write_text(json.dumps(receipt))
        try:
            verify_approved(root=root, read_blob=lambda _: "a" * 40)
        except RuntimeError as exc:
            assert "NOT_APPROVED" in str(exc)
        else:
            raise AssertionError("STAGE102_BLOCKED_REVIEW_MUST_NOT_INSTALL")
        receipt["verdict"] = "APPROVE"
        receipt["blocking_findings"] = []
        receipt["full_reply_sha256"] = "b" * 64
        dst.write_text(json.dumps(receipt))
        try:
            verify_approved(root=root, read_blob=lambda _: "a" * 40)
        except RuntimeError as exc:
            assert "MODIFIED" in str(exc)
        else:
            raise AssertionError("STAGE102_TAMPERED_REPLY_MUST_BE_REJECTED")
        receipt["full_reply_sha256"] = sha256(text)
        dst.write_text(json.dumps(receipt))
        try:
            verify_approved(root=root, read_blob=lambda _: "b" * 40)
        except RuntimeError as exc:
            assert "CODE_CHANGED" in str(exc)
        else:
            raise AssertionError("STAGE102_DIFFERENT_CODE_MUST_BE_REJECTED")
        assert verify_approved(
            root=root, read_blob=lambda _: "a" * 40
        )["covered_file_count"] == len(REQUIRED_SOURCES)
    print("STAGE102_OFFLINE_CHAT_REVIEW_BLOCK_MISSING_TAMPER_BLOB_TESTS_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("verify", "selftest"))
    args = p.parse_args()
    if args.action == "selftest":
        selftest()
    else:
        print(json.dumps(verify_approved(), sort_keys=True))


if __name__ == "__main__":
    main()
