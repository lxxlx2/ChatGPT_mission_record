#!/usr/bin/env python3
"""Stage103 fail-closed: Claude CHAT review and separate user's install consent.

Cryptographic hashes verify only bytes, not model or user identity.
Review is not consent. Nothing here installs, schedules or contacts networks.
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

RECEIPT = ("crypto-300-profit-mission/monster/evidence/"
           "monster_stage102_actual_claude_chat_independent_review.json")
AUTHORIZATION = ("crypto-300-profit-mission/monster/evidence/"
                 "monster_stage103_explicit_user_local_install_authorization.json")
SCHEMA = "MONSTER_STAGE103_USER_SUPPLIED_CLAUDE_CHAT_REVIEW_RECEIPT_V2"
AUTH_SCHEMA = "MONSTER_STAGE103_SEPARATE_USER_INSTALL_AUTHORIZATION_V1"
REVIEW_ORIGIN = "CLAUDE_CHAT_USER_SUPPLIED_FULL_OUTPUT"
REQUIRED_SOURCES = (
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage38_usdm_original_v4_1m_pilot.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage80_dual_entry_core.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py",
    "crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py",
    ".github/workflows/monster-stage99-mac-one-shot-capture-safety.yml",
)
REVIEW_PROMPT_PATH = ("crypto-300-profit-mission/monster/"
                      "MONSTER_STAGE103_EXTERNAL_CLAUDE_CHAT_REVIEW_PROMPT_20261013.md")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def current_blobs(*, read_blob=None):
    if read_blob is None:
        def read_blob(path):
            return stage99.git("hash-object", "--", path, capture=True)
    return {path:read_blob(path) for path in REQUIRED_SOURCES}


def reviewed_fingerprint(review: dict) -> str:
    # Complete content hash of review + exact review-target files, independent
    # of unrelated evidence/docs commits on the active research branch.
    return sha256(json.dumps({
        "reply_sha":review["full_reply_sha256"],
        "commit":review["reviewed_commit"],
        "files":review["reviewed_file_git_blobs"],
    },sort_keys=True,separators=(",",":")))


def validate_review(*, root=None, read_blob=None, is_ancestor=None):
    home=stage99.CLONE if root is None else Path(root)
    record=home/RECEIPT
    if not record.is_file():
        raise RuntimeError("STAGE103_CLAUDE_CHAT_REVIEW_NOT_RECEIVED")
    try:
        review=json.loads(record.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise RuntimeError("STAGE103_INVALID_CHAT_REVIEW_RECEIPT") from None
    if (review.get("schema")!=SCHEMA or review.get("source_origin")!=REVIEW_ORIGIN
        or review.get("repository")!=stage99.REPO_NAME
        or review.get("branch")!=stage99.BRANCH):
        raise RuntimeError("STAGE103_REVIEW_WRONG_REPO_BRANCH_OR_SCHEMA")
    commit=review.get("reviewed_commit")
    if not isinstance(commit,str) or len(commit)!=40 or not all(
            x in "0123456789abcdef" for x in commit):
        raise RuntimeError("STAGE103_MISSING_EXACT_REVIEWED_COMMIT")
    if not isinstance(review.get("reviewer_model"),str) or not review["reviewer_model"].strip():
        raise RuntimeError("STAGE103_REVIEWER_MODEL_NOT_RECORDED")
    if (review.get("verdict")!="APPROVE" or review.get("blocking_findings")!=[]
        or not isinstance(review.get("nonblocking_findings"),list)):
        raise RuntimeError("STAGE103_CLAUDE_REVIEW_IS_NOT_APPROVE")
    reply=review.get("full_claude_reply")
    if (not isinstance(reply,str) or len(reply.strip())<160
        or sha256(reply)!=review.get("full_reply_sha256")):
        raise RuntimeError("STAGE103_REVIEW_CONTENT_SHA_INVALID")
    blobs=review.get("reviewed_file_git_blobs")
    if not isinstance(blobs,dict) or set(blobs)!=set(REQUIRED_SOURCES):
        raise RuntimeError("STAGE103_REVIEW_BINDING_MISSING_RUNTIME_SOURCES")
    actual=current_blobs(read_blob=read_blob)
    for path,expected in blobs.items():
        if (not isinstance(expected,str) or len(expected)!=40 or
            not all(ch in "0123456789abcdef" for ch in expected)
            or actual[path]!=expected):
            raise RuntimeError("STAGE103_CHANGED_CODE_SINCE_REVIEW_"+path)
    evidence=review.get("reviewed_risks_and_test_evidence")
    if not isinstance(evidence,list) or len(evidence)<3:
        raise RuntimeError("STAGE103_REVIEW_LACKS_EVIDENCE")
    if is_ancestor is None:
        def is_ancestor(commit):
            stage99.git("merge-base","--is-ancestor",commit,"HEAD")
            return True
    if is_ancestor(commit) is not True:
        raise RuntimeError("STAGE103_REVIEWED_COMMIT_NOT_ANCESTOR")
    return review


def validate_authorization(*, root=None, read_blob=None, is_ancestor=None):
    home=stage99.CLONE if root is None else Path(root)
    review=validate_review(root=home,read_blob=read_blob,is_ancestor=is_ancestor)
    auth_path=home/AUTHORIZATION
    if not auth_path.is_file():
        raise RuntimeError("STAGE103_USER_INSTALL_AUTHORIZATION_NOT_GIVEN")
    try:
        a=json.loads(auth_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise RuntimeError("STAGE103_INVALID_USER_AUTHORIZATION_RECORD") from None
    expected=reviewed_fingerprint(review)
    if (a.get("schema")!=AUTH_SCHEMA
        or a.get("repository")!=stage99.REPO_NAME
        or a.get("branch")!=stage99.BRANCH
        or a.get("reviewed_commit")!=review["reviewed_commit"]
        or a.get("review_fingerprint")!=expected
        or a.get("exact_windows_utc")!=list(stage99.stage91.WINDOWS)
        or a.get("permission_scope")!="INSTALL_ONLY_LOCAL_MONSTER_USDM_RESEARCH_SNAPSHOTS"):
        raise RuntimeError("STAGE103_INSTALL_NOT_AUTHORIZED_FOR_REVIEWED_BYTES")
    # Authorization statement must be an independently supplied explicit user
    # instruction *after* the review, not text inserted by the model.
    if (a.get("explicit_user_consent") is not True
        or not isinstance(a.get("user_original_message"),str)
        or len(a["user_original_message"].strip())<12
        or not isinstance(a.get("consented_at_utc"),str)
        or len(a["consented_at_utc"])<20):
        raise RuntimeError("STAGE103_MISSING_SEPARATE_EXPLICIT_USER_CONSENT")
    return {"review_fingerprint":expected,"auth_file":str(auth_path),
            "consented_at_utc":a["consented_at_utc"]}


def interactive_install_consent(authorization:dict, *,input_fn=input,
                                stdin=None,stdout=None):
    import sys
    if stdin is None:stdin=sys.stdin
    if stdout is None:stdout=sys.stdout
    if not (stdin.isatty() and stdout.isatty()):
        raise RuntimeError("STAGE103_INSTALL_NEEDS_INTERACTIVE_HUMAN_TTY")
    # Contains both exact reviewed SHA corpus and independently archived reply.
    stamp=authorization["review_fingerprint"][:16]
    challenge="CONFIRM LOCAL MONSTER CAPTURE "+stamp
    print("仅本地三次研究市场快照任务；绝非Monster/Frank交易部署。",file=stdout)
    print("核对用户已单独授权的Git记录后，手动完整输入确认短语：",file=stdout)
    print(challenge,file=stdout)
    if input_fn("确认短语: ").strip()!=challenge:
        raise RuntimeError("STAGE103_USER_DID_NOT_CONFIRM_LOCAL_INSTALL")
    return True


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        try:validate_authorization(root=root,read_blob=lambda x:"a"*40,is_ancestor=lambda _:True)
        except RuntimeError as e:assert "NOT_RECEIVED" in str(e)
        else:raise AssertionError("STAGE103_MUST_BLOCK_NO_INDEPENDENT_REVIEW")
        reply="TEST-ONLY NOT A REAL CLAUDE REVIEW "+"x"*170
        review={
            "schema":SCHEMA,"source_origin":REVIEW_ORIGIN,
            "repository":stage99.REPO_NAME,"branch":stage99.BRANCH,
            "reviewer_model":"SYNTHETIC_NOT_A_REAL_REVIEW",
            "reviewed_commit":"a"*40,
            "verdict":"BLOCK","blocking_findings":["synthetic"],
            "nonblocking_findings":[],
            "full_claude_reply":reply,"full_reply_sha256":sha256(reply),
            "reviewed_file_git_blobs":{p:"a"*40 for p in REQUIRED_SOURCES},
            "reviewed_risks_and_test_evidence":["clock","sha","branch"],
        }
        path=root/RECEIPT
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(review))
        try:validate_review(root=root,read_blob=lambda p:"a"*40,is_ancestor=lambda _:True)
        except RuntimeError as e:assert "NOT_APPROVE" in str(e)
        else:raise AssertionError("STAGE103_EXTERNAL_BLOCK_MUST_HOLD")
        review["verdict"]="APPROVE";review["blocking_findings"]=[]
        path.write_text(json.dumps(review))
        try:validate_authorization(root=root,read_blob=lambda p:"a"*40,is_ancestor=lambda _:True)
        except RuntimeError as e:assert "AUTHORIZATION_NOT_GIVEN" in str(e)
        else:raise AssertionError("STAGE103_REVIEW_IS_NOT_USER_AUTHORIZATION")
        auth={
            "schema":AUTH_SCHEMA,"repository":stage99.REPO_NAME,
            "branch":stage99.BRANCH,"reviewed_commit":"a"*40,
            "review_fingerprint":reviewed_fingerprint(review),
            "exact_windows_utc":list(stage99.stage91.WINDOWS),
            "permission_scope":"INSTALL_ONLY_LOCAL_MONSTER_USDM_RESEARCH_SNAPSHOTS",
            "explicit_user_consent":True,
            "user_original_message":"TEST EXPLICIT INSTALL PERMISSION ONLY",
            "consented_at_utc":"2026-10-13T09:00:00+00:00",
        }
        auth_path=root/AUTHORIZATION
        auth_path.write_text(json.dumps(auth))
        assert validate_authorization(
            root=root,read_blob=lambda p:"a"*40,is_ancestor=lambda _:True
        )["review_fingerprint"]==auth["review_fingerprint"]
        try:interactive_install_consent(auth,stdin=type("F",(),{"isatty":lambda self:False})(),
                                        stdout=type("F",(),{"isatty":lambda self:False})())
        except RuntimeError as e:assert "TTY" in str(e)
        else:raise AssertionError("STAGE103_NO_UNATTENDED_AUTOMATIC_INSTALL")
        try:validate_review(root=root,read_blob=lambda p:"b"*40,is_ancestor=lambda _:True)
        except RuntimeError as e:assert "CHANGED_CODE" in str(e)
        else:raise AssertionError("STAGE103_STAGE91_CHANGE_MUST_FAIL")
        try:validate_review(root=root,read_blob=lambda p:"a"*40,is_ancestor=lambda _:False)
        except RuntimeError as e:assert "NOT_ANCESTOR" in str(e)
        else:raise AssertionError("STAGE103_COMMIT_BINDING_REQUIRED")
    print("STAGE103_SEPARATE_USER_CONSENT_TTY_EXACT_8_RUNTIME_BLOBS_COMMIT_AND_REVIEW_FAILCLOSED_PASS")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("selftest","verify"))
    args=parser.parse_args()
    if args.action=="selftest":selftest()
    else:print(json.dumps(validate_authorization(),sort_keys=True))


if __name__=="__main__":
    main()
