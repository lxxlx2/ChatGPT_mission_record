#!/usr/bin/env python3
"""Mac PR #29 predeployment shadow acceptance.

This tool does NOT install/deploy/restart/send mail/trade or execute the live
MissionMemeService cycle. It performs SQLite online read-only backups into a
temporary directory; compares OLD installed vs NEW PR FrankReader candidates
and pure policy.evaluate decisions using IDENTICAL input and synthetic quotes.
The synthetic quotes are ONLY test vectors, never live prices or buy signals.
No wallet address, API key, email address or SQL row contents are printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path


WORKER = r"""
import hashlib,json,sys
from pathlib import Path
root,prod,policy_path,now=sys.argv[1:]
sys.path.insert(0,root)
from mission_agent.mission_control.frank import FrankReader
from mission_agent.mission_control.policy import load_policy,evaluate
reader=FrankReader(Path(prod))
policy,_=load_policy(Path(policy_path))
candidates=reader.candidates()
def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),
                                   ensure_ascii=False,default=str).encode()).hexdigest()
rows=[]
for candidate in candidates:
    c={**candidate,"runtime_status":"LIVE"}
    price=c.get("latest_buy_price_usdc")
    try:
        from decimal import Decimal
        valid_price=Decimal(str(price))>0 and Decimal(str(price)).is_finite()
    except Exception:
        valid_price=False
    base_price=str(price) if valid_price else "1"
    from decimal import Decimal
    now_decimal=Decimal(now)
    def quote(status="OK", observed=None,route=True,price_value=None,impact="0.5"):
        return {
            "status":status,
            "source":"SYNTHETIC_PARITY_ONLY_NOT_A_JUPITER_QUOTE",
            "observed_at":str(now_decimal if observed is None else observed),
            "route_exists":route,
            "input_usdc":"30",
            "execution_price_usdc":base_price if price_value is None else price_value,
            "price_impact_pct":impact,
            "reason":"SHADOW_QUOTE_UNAVAILABLE" if status!="OK" else None,
        }
    vectors=[
        {"status":"UNAVAILABLE","reason":"SHADOW_NO_LIVE_QUOTE",
         "observed_at":str(now_decimal)},
        quote(),
        quote(price_value=str(Decimal(base_price)*Decimal("1.22")),impact="3.5"),
        quote(route=False),
        quote(observed=str(now_decimal-Decimal(120))),
    ]
    decisions=[evaluate(c,q,policy,now=float(now)) for q in vectors]
    rows.append({
        "identity_hash":digest([c.get("person_id"),c.get("mint"),c.get("episode_id")]),
        "candidate_hash":digest(candidate),
        "decision_hashes":[digest(d) for d in decisions],
        "decisions":[d["decision"] for d in decisions],
    })
rows.sort(key=lambda x:x["identity_hash"])
print(json.dumps({"candidate_count":len(rows),"rows":rows},sort_keys=True))
"""


def _reader(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.is_symlink():
        raise ValueError("SQLITE_SOURCE_NOT_REGULAR")
    db=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True,timeout=8)
    db.execute("PRAGMA query_only=ON")
    return db


def snapshot(source: Path,dest: Path) -> None:
    """Consistent online backup with a read-only source connection."""
    reader=_reader(source)
    backup=sqlite3.connect(dest)
    try:
        reader.backup(backup,pages=200,sleep=0.05)
        if backup.execute("PRAGMA quick_check").fetchone()[0]!="ok":
            raise ValueError("ISOLATED_SQLITE_QUICK_CHECK_FAILED")
    finally:
        backup.close()
        reader.close()
    dest.chmod(0o600)


def _root_from_runner(path: Path,key: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise ValueError("RUNNER_NOT_REGULAR")
    text=path.read_text(encoding="utf-8")
    matches=re.findall(r"^"+re.escape(key)+r'="([^"\n]+)"$',text,re.M)
    if len(matches)!=1:
        raise ValueError("RUNNER_PATH_ANCHOR_INVALID")
    resolved=Path(matches[0]).resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("AGENT_PATH_NOT_DIRECTORY")
    return resolved


def _identity_gate(root:Path,sha:str) -> dict:
    if not re.fullmatch("[0-9a-f]{40}",sha):
        raise ValueError("EXPECTED_HEAD_INVALID")
    def git(*args):
        return subprocess.check_output(
            ["git","-C",str(root),*args],text=True,timeout=12
        ).strip()
    head=git("rev-parse","HEAD")
    if head!=sha:
        raise ValueError("PR_RELEASE_HEAD_MISMATCH")
    if git("rev-parse","--abbrev-ref","HEAD")!="HEAD":
        raise ValueError("PR_RELEASE_NOT_DETACHED")
    if git("status","--porcelain"):
        raise ValueError("PR_RELEASE_WORKTREE_DIRTY")
    return {"head":head,"detached":True,"clean":True}


def _run_worker(agent:Path,prod:Path,policy:Path,now:float,timeout:int=45)->dict:
    env=dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env.pop("PYTHONPATH",None)
    result=subprocess.run(
        [sys.executable,"-B","-c",WORKER,str(agent),str(prod),str(policy),str(now)],
        env=env,text=True,capture_output=True,timeout=timeout,cwd=prod.parent,
        check=False,
    )
    if result.returncode!=0:
        # Never echo worker stderr: external runtime could inadvertently include secrets.
        raise ValueError("ISOLATED_CANDIDATE_WORKER_FAILED")
    value=json.loads(result.stdout)
    if not isinstance(value,dict) or not isinstance(value.get("rows"),list):
        raise ValueError("ISOLATED_CANDIDATE_WORKER_INVALID_JSON")
    return value


def compare(old:dict,new:dict)->dict:
    a={r["identity_hash"]:r for r in old["rows"]}
    b={r["identity_hash"]:r for r in new["rows"]}
    missing=set(a)-set(b); added=set(b)-set(a)
    overlap=set(a)&set(b)
    candidate_diff=sum(a[k]["candidate_hash"]!=b[k]["candidate_hash"] for k in overlap)
    decision_diff=sum(a[k]["decision_hashes"]!=b[k]["decision_hashes"] for k in overlap)
    return {
        "old_candidates":len(a),"new_candidates":len(b),
        "identity_missing":len(missing),"identity_added":len(added),
        "candidate_payload_differences":candidate_diff,
        "decision_vector_differences":decision_diff,
        "synthetic_scenarios_per_candidate":5,
        "status":"PASS" if not (missing or added or candidate_diff or decision_diff) else "REVIEW_DELTAS",
    }


def run(home:Path,release_agent:Path,expected_head:str) -> dict:
    root=_identity_gate(release_agent.parent.parent,expected_head)
    app=home/"Library/Application Support/FrankMeme"
    production=home/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1"
    control=Path((home/".frank_meme_control_root").read_text().strip()).expanduser().resolve(strict=True)
    old=_root_from_runner(app/"mission-loop.sh","LOCAL_AGENT")
    dash=_root_from_runner(app/"dashboard.sh","LOCAL_AGENT")
    if old!=dash:
        raise ValueError("LIVE_LOOP_DASHBOARD_SOURCE_MISMATCH")
    allowed=home/"Documents/ChatGPT"
    try:
        p=old.relative_to(allowed).parts
    except ValueError:
        raise ValueError("LIVE_SOURCE_OUTSIDE_TRUSTED_ROOT")
    if len(p)<3 or not (p[0]=="frank-meme-main" or p[0].startswith("frank-meme-pr29-")) or p[-2:]!=("crypto-300-profit-mission","local-agent"):
        raise ValueError("LIVE_SOURCE_UNEXPECTED")
    if old==release_agent:
        raise ValueError("NEW_RELEASE_ALREADY_INSTALLED")
    policy=app/"follow_policy_v1.approved.json"
    pinned=(app/"approved_policy_sha256").read_text().strip()
    if hashlib.sha256(policy.read_bytes()).hexdigest()!=pinned:
        raise ValueError("APPROVED_POLICY_PIN_MISMATCH")
    if not (release_agent/"mission_agent/mission_control/policy.py").is_file():
        raise ValueError("RELEASE_AGENT_MODULES_MISSING")
    if not (old/"mission_agent/mission_control/policy.py").is_file():
        raise ValueError("INSTALLED_AGENT_MODULES_MISSING")
    with tempfile.TemporaryDirectory(prefix="meme-pr29-readonly-") as scratch:
        sandbox=Path(scratch)
        prod=sandbox/"prod";prod.mkdir()
        snapshot(production/"forward.sqlite",prod/"forward.sqlite")
        shutil.copyfile(production/"health.json",prod/"health.json")
        (prod/"health.json").chmod(0o600)
        snapshot(control/"mission-control.sqlite",sandbox/"control.sqlite")
        copied=_reader(sandbox/"control.sqlite")
        try:
            counts={
                row[0]:int(row[1]) for row in copied.execute(
                    "SELECT channel,COUNT(*) FROM decision_outbox GROUP BY channel"
                ).fetchall()
            }
        finally:
            copied.close()
        common_now=time.time()
        older=_run_worker(old,prod,policy,common_now)
        newer=_run_worker(release_agent,prod,policy,common_now)
        comparison=compare(older,newer)
        result={
            "mode":"READ_ONLY_MAC_PREDEPLOY_SHADOW",
            "release_head":root["head"],
            "new_code_installed":False,
            "source_snapshots":"SQLITE_MODE_RO_BACKUP",
            "production_sqlite_modified":False,
            "approval_policy_pin":"PASS",
            "local_delivery_suppressed":True,
            "gmail_delivery_suppressed":True,
            "live_swap_or_signing":False,
            "network_quote_called":False,
            "outbox_count_by_channel":counts,
            "decision_parity":comparison,
            "mac_reboot_acceptance":"DEFERRED_BY_USER",
            "post_deploy_email_acceptance":"NOT_RUN_NO_NEW_CODE_DEPLOYED",
            "production_trading":"NO_GO",
        }
        return result


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--expected-head",required=True)
    args=parser.parse_args()
    # This script is stored under <git-root>/crypto-300-profit-mission/local-agent/scripts.
    agent=Path(__file__).resolve().parent.parent
    try:
        result=run(Path.home(),agent,args.expected_head)
    except Exception as exc:
        print(json.dumps({
            "mode":"READ_ONLY_MAC_PREDEPLOY_SHADOW",
            "status":"FAIL",
            "error_code":str(exc) if isinstance(exc,ValueError) else type(exc).__name__,
        },ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if result["decision_parity"]["status"]!="PASS":
        raise SystemExit(1)


if __name__=="__main__":
    main()
