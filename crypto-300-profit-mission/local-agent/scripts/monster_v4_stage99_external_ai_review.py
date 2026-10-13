#!/usr/bin/env python3
"""Read-only real external Claude Code review for Stage99 before any Mac installation.

Uses user's authenticated Claude Code CLI in non-interactive read-only mode.
Never synthesizes an AI review. No CLI / BLOCK / bad metadata => FAIL CLOSED.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

try:
    import monster_v4_stage99_mac_launchd_one_shot as gate
except ImportError:
    from scripts import monster_v4_stage99_mac_launchd_one_shot as gate

ROOT = gate.CLONE
REVIEW_PATH = "crypto-300-profit-mission/monster/evidence/monster_stage99_actual_external_claude_ai_review.json"
REVIEW_TARGETS = (
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py",
    "crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py",
    ".github/workflows/monster-stage99-mac-one-shot-capture-safety.yml",
    "crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md",
    "crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md",
)
REVIEW_SCHEMA = "MONSTER_STAGE99_EXTERNAL_CLAUDE_CODE_REAL_INDEPENDENT_REVIEW_V1"
CLAUDE_OUTPUT_JSON_SCHEMA={
    "type":"object",
    "additionalProperties":False,
    "properties":{
        "decision":{"type":"string","enum":["APPROVE","BLOCK"]},
        "blocking_findings":{"type":"array","items":{"type":"string"}},
        "nonblocking_findings":{"type":"array","items":{"type":"string"}},
        "reviewed_files":{"type":"array","items":{"type":"string"}},
        "tests_and_security_evidence":{"type":"array","items":{"type":"string"}},
        "review_summary":{"type":"string"}
    },
    "required":["decision","blocking_findings","nonblocking_findings",
                "reviewed_files","tests_and_security_evidence","review_summary"]
}


def code_blobs():
    return {path:gate.git("hash-object","--",path,capture=True)
            for path in REVIEW_TARGETS}


def prompt_for_review():
    return """Act as an INDEPENDENT security and reliability reviewer of a macOS
launchd one-shot Binance USD-M research snapshot capture, not the author.
Use Read, Glob, Grep only; no Bash, edits, shell, writes, external MCP or execution.
Read these actual repository files in full, particularly:
"""+"\n".join(REVIEW_TARGETS)+"""

Review against MONSTER_MODULE_DEVELOPMENT_RULES. Focus on:
1. point-in-time UTC/Bangkok DST/local calendar correctness, sleeper/wake misses,
   exact three future windows and self-unloading launchd jobs, no annual recurrence.
2. only official HTTPS /fapi/v1/time + /fapi/v1/exchangeInfo evidence,
   header/raw SHA and spoofing; 15min fail closed; no after-the-fact recapture.
3. isolated clone: git push conflicts/auth, no force push, no main/Frank/production,
   no persisted secrets, no false GIT_PUSH_CONFIRMED, retry of original bytes.
4. test realism, unexpected Stage99 installation before review, failure recovery,
   log retention and duplicate execution, user commands.
5. Does a single review/install command actually run the other AI before installing?
6. stage97 event clock and raw SHA validation restrictions.

Return APPROVE only if safe to activate the research *evidence-only* launchd job
(no Monster trading). Any correctness/safety blocking issue => BLOCK with concrete
code locations. Do not call this review approved just because CI succeeded.
Explicitly inspect Stage99 runner, separate review gate, tests, Stage97.
Return concise structured English or Chinese strings in the specified JSON schema.
"""


def parse_cli_response(raw_text: str):
    wrapper=json.loads(raw_text)
    if not isinstance(wrapper,dict) or wrapper.get("is_error") or wrapper.get("type")=="error":
        raise ValueError("STAGE99_EXTERNAL_CLAUDE_REVIEW_FAILED")
    structured=wrapper.get("structured_output")
    if structured is None:
        result=wrapper.get("result")
        if not isinstance(result,str):
            raise ValueError("STAGE99_NO_ACTUAL_MODEL_REVIEW_JSON")
        # Do not accept a markdown paragraph falsely described as structured proof.
        structured=json.loads(result)
    if not isinstance(structured,dict):
        raise ValueError("STAGE99_EXTERNAL_AI_RESPONSE_NOT_OBJECT")
    if structured.get("decision") not in ("APPROVE","BLOCK"):
        raise ValueError("STAGE99_MODEL_DID_NOT_PROVIDE_DECISION")
    required=("blocking_findings","nonblocking_findings","reviewed_files",
              "tests_and_security_evidence","review_summary")
    if any(key not in structured for key in required):
        raise ValueError("STAGE99_EXTERNAL_AI_REVIEW_FIELDS_INCOMPLETE")
    for key in ("blocking_findings","nonblocking_findings",
                "reviewed_files","tests_and_security_evidence"):
        if not isinstance(structured[key],list):
            raise ValueError("STAGE99_EXTERNAL_AI_REVIEW_NOT_AUDITABLE")
    # A generic affirmative paragraph is not a review: the other model must
    # explicitly attest to reading the scheduler, reviewer, fixtures and source.
    required_for_review=set(REVIEW_TARGETS[:4])
    declared={str(x) for x in structured["reviewed_files"]}
    if structured["decision"]=="APPROVE" and (
        structured["blocking_findings"]
        or len(structured["tests_and_security_evidence"])<3
        or not required_for_review.issubset(declared)):
        raise ValueError("STAGE99_EXTERNAL_AI_APPROVAL_WITHOUT_REQUIRED_EVIDENCE")
    model_usage=wrapper.get("modelUsage") or wrapper.get("model_usage") or {}
    model_names=list(model_usage.keys()) if isinstance(model_usage,dict) else []
    if not model_names:
        model_names=[str(wrapper.get("model") or "CLAUDE_CLI_MODEL_UNDISCLOSED")]
    return structured,model_names


def review_with_claude(*,invoke=None):
    if invoke is None:
        if shutil.which("claude") is None:
            raise RuntimeError("STAGE99_CLAUDE_CODE_CLI_NOT_INSTALLED_OR_NOT_IN_PATH")
        def invoke(cmd):
            return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,
                                  timeout=420,check=False)
    paths=code_blobs()
    prompt=prompt_for_review()
    cmd=[
        "claude","-p","--output-format","json",
        "--json-schema",json.dumps(CLAUDE_OUTPUT_JSON_SCHEMA,separators=(",",":")),
        "--max-turns","10",
        "--tools","Read,Glob,Grep",
        "--disallowedTools","Bash,Edit,Write,mcp__*",
        "--no-session-persistence",
        prompt,
    ]
    response=invoke(cmd)
    if response.returncode!=0:
        raise RuntimeError("STAGE99_EXTERNAL_CLAUDE_REVIEW_CLI_EXIT_"+str(response.returncode))
    findings,models=parse_cli_response(response.stdout)
    if code_blobs()!=paths:
        raise ValueError("STAGE99_CODE_CHANGED_DURING_INDEPENDENT_REVIEW")
    return {
       "schema":REVIEW_SCHEMA,
       "reviewer_product":"Anthropic Claude Code CLI",
       "independent_external_model_used":models,
       "review_actual_model_response":findings,
       "reviewed_git_content_blobs":paths,
       "reviewed_branch":gate.BRANCH,
       "reviewed_repo":gate.REPO_NAME,
       "reviewed_utc":datetime.now(timezone.utc).isoformat(),
       "review_prompt":prompt,
       "original_CI": "https://github.com/lxxlx2/ChatGPT_mission_record/actions/workflows/monster-stage99-mac-one-shot-capture-safety.yml",
       "no_simulated_review":True,
       "not_monster_strategy_deployment":True,
    }


def verify_approved():
    file=ROOT/REVIEW_PATH
    if not file.is_file():
        raise RuntimeError("STAGE99_OTHER_AI_REAL_REVIEW_NOT_PRESENT_NO_INSTALL")
    review=json.loads(file.read_text())
    if review.get("schema")!=REVIEW_SCHEMA or review.get(
        "reviewer_product")!="Anthropic Claude Code CLI" or not review.get("no_simulated_review"):
        raise RuntimeError("STAGE99_REVIEW_NOT_PROVEN_INDEPENDENT_CLAUDE")
    if (review.get("review_actual_model_response",{}).get("decision")!="APPROVE"
        or review["review_actual_model_response"].get("blocking_findings")):
        raise RuntimeError("STAGE99_CLAUDE_REVIEW_BLOCKED_DO_NOT_INSTALL")
    if review.get("reviewed_git_content_blobs")!=code_blobs():
        raise RuntimeError("STAGE99_CODE_CHANGED_SINCE_OTHER_AI_REVIEW")
    return True


def review_then_install():
    gate.isolated_checkout_preflight()
    report=review_with_claude()
    dest=ROOT/REVIEW_PATH
    dest.parent.mkdir(parents=True,exist_ok=True)
    extra=[]
    if dest.exists():
        # An earlier independent BLOCK is a required audit record, not a reason
        # to prevent a fixed version from getting a fresh REAL review.
        previous=dest.read_bytes()
        old_sha=hashlib.sha256(previous).hexdigest()
        archive=REVIEW_PATH.replace(".json","_archive_"+old_sha[:16]+".json")
        archived=ROOT/archive
        if archived.exists():
            raise RuntimeError("STAGE99_REVIEW_ARCHIVE_ALREADY_PRESENT")
        archived.write_bytes(previous)
        extra.append(archive)
    dest.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    gate.git("add","--",REVIEW_PATH,*extra)
    gate.safe_git_commit_and_push_for_review()
    # Git might have rebased the private branch. The code hashes must remain.
    verify_approved()
    return gate.install()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("review-install","verify","selftest"))
    a=p.parse_args()
    if a.action=="review-install":
        p.error("STAGE99_CLAUDE_CLI_WORKFLOW_WITHDRAWN: Use actual Claude CHAT "
                "review on GitHub code and Stage102 archived review gate. "
                "No local Claude CLI and no automatic installation.")
    elif a.action=="verify":
        print("STAGE99_REAL_OTHER_AI_REVIEW_CURRENT_SOURCE "+str(verify_approved()))
    else:
        # Offline parser checks, not a fabricated AI review.
        simulated={
            "structured_output":{
              "decision":"BLOCK","blocking_findings":["simulated serious issue"],
              "nonblocking_findings":[],"reviewed_files":["one"],
              "tests_and_security_evidence":[],"review_summary":"TEST ONLY"}}
        d,_=parse_cli_response(json.dumps(simulated))
        assert d["decision"]=="BLOCK"
        try:
            parse_cli_response(json.dumps({"structured_output":{
              **simulated["structured_output"],
              "decision":"APPROVE"}}))
        except ValueError as e:
            assert "WITHOUT_REQUIRED" in str(e)
        else:raise AssertionError("STAGE99_SIMULATED_APPROVAL_MUST_FAIL_CLOSED")
        print("STAGE99_CLAUDE_REVIEW_PARSER_MOCKS_DO_NOT_COUNT_AS_OTHER_AI_REVIEW_PASS")


if __name__=="__main__":
    main()
