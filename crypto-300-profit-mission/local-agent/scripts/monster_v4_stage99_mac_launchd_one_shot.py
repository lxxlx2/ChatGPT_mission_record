#!/usr/bin/env python3
"""Stage99: isolated macOS launchd one-shot official USD-M evidence -> original PR30 Git.

Not a Monster trading, market-monitoring, email, Frank, or production service.
Install explicitly. Three unique launchd calendar jobs remove themselves on execution.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time
import traceback

try:
    import monster_v4_stage97_one_shot_usdm_capture as stage97
    import monster_v4_stage91_forward_oos_replay_gate as stage91
except ImportError:
    from scripts import monster_v4_stage97_one_shot_usdm_capture as stage97
    from scripts import monster_v4_stage91_forward_oos_replay_gate as stage91

BRANCH = "research/monster-v4-local-discovery-20261010"
REPO_NAME = "lxxlx2/ChatGPT_mission_record"
ROOT = Path.home() / ".local" / "share" / "monster-stage99-source-capture"
CLONE = ROOT / "repo"
LOGS = ROOT / "logs"
STATES = ROOT / "state"
AGENTS = Path.home() / "Library" / "LaunchAgents"
CAPTURE_MINUTES_BEFORE = 12
MINUTE_MS = 60_000
REMOTE_PATH = "crypto-300-profit-mission/monster/evidence"
SCRIPT_IN_CLONE = "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py"
SCHEMA = "MONSTER_STAGE99_ISOLATED_LAUNCHD_ONE_SHOT_CAPTURE_V1"


def env_no_prompts():
    e = dict(os.environ)
    e["GIT_TERMINAL_PROMPT"] = "0"
    e["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o ConnectTimeout=12"
    e["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    return e


def git(*args, capture=False, timeout=50):
    res = subprocess.run(["git","-C",str(CLONE),*args],env=env_no_prompts(),
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,timeout=timeout,check=False)
    if res.returncode:
        # Do not echo credentials or full git remote URLs; CI/state gets just error code.
        raise RuntimeError("STAGE99_GIT_COMMAND_FAILED "+
                           str(args[0])+" rc="+str(res.returncode))
    return res.stdout.strip() if capture else None


def label_for(window: str):
    stage91.verify_window(window)
    return "com.lxxlx2.monster.stage99.usdm."+window[:10].replace("-","")


def expected_path(window: str):
    stage91.verify_window(window)
    return REMOTE_PATH+"/monster_stage97_point_in_time_usdm_"+window[:10]+"_raw_https.json"


def job_plist(window: str, script: Path, python: Path, user_tz=None):
    start=stage91.verify_window(window)
    due_utc=datetime.fromtimestamp((start-CAPTURE_MINUTES_BEFORE*MINUTE_MS)/1000,timezone.utc)
    local=due_utc.astimezone(user_tz) if user_tz else datetime.fromtimestamp(due_utc.timestamp())
    service=label_for(window)
    return {
      "Label":service,
      "ProgramArguments":[str(python),str(script),"run","--window",window],
      "RunAtLoad":False,
      "KeepAlive":False,
      "ProcessType":"Background",
      "StartCalendarInterval":{"Month":local.month,"Day":local.day,
                               "Hour":local.hour,"Minute":local.minute},
      "StandardOutPath":str(LOGS/(service+".out.log")),
      "StandardErrorPath":str(LOGS/(service+".err.log")),
      "EnvironmentVariables":{
        "PATH":"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "GIT_TERMINAL_PROMPT":"0",
        "PYTHONDONTWRITEBYTECODE":"1",
        "TZ":"UTC",
      },
    }


def store_status(window, status, **data):
    STATES.mkdir(parents=True,exist_ok=True)
    payload={"schema":SCHEMA,"window":window,"status":status,
             "written_utc":datetime.now(timezone.utc).isoformat(),
             "research_only":True,"actual_trades":"NONE",
             "monster":"NO_GO","frank":"UNCHANGED","gmail":"OFF",**data}
    target=STATES/(window[:10]+".json")
    tmp=STATES/(window[:10]+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    tmp.replace(target)


def isolated_checkout_preflight():
    if not CLONE.exists() or not (CLONE/".git").is_dir():
        raise RuntimeError("STAGE99_NO_ISOLATED_GIT_CLONE_AT_EXPECTED_PATH")
    if Path(__file__).resolve()!= (CLONE/SCRIPT_IN_CLONE).resolve():
        raise RuntimeError("STAGE99_SCRIPT_MUST_RUN_INSIDE_PRIVATE_ISOLATED_CLONE")
    if git("branch","--show-current",capture=True)!=BRANCH:
        raise RuntimeError("STAGE99_WRONG_GIT_BRANCH")
    if git("status","--porcelain",capture=True):
        raise RuntimeError("STAGE99_PRIVATE_CLONE_HAS_UNCOMMITTED_CHANGES")
    remote=git("remote","get-url","origin",capture=True)
    valid=(remote in ("https://github.com/"+REPO_NAME+".git",
                     "https://github.com/"+REPO_NAME,
                     "git@github.com:"+REPO_NAME+".git"))
    if not valid:
        raise RuntimeError("STAGE99_ORIGIN_NOT_EXPECTED_MISSION_REPOSITORY")
    git("ls-remote","--exit-code","origin","refs/heads/"+BRANCH,timeout=35)
    return True


def launchctl(*args):
    result=subprocess.run(["launchctl",*args],env=env_no_prompts(),
                          capture_output=True,text=True,timeout=20,check=False)
    return result.returncode


def gui_domain():
    return "gui/"+str(os.getuid())


def plist_path(window):
    return AGENTS/(label_for(window)+".plist")


def bootout(window):
    service=label_for(window)
    # Remove the file first so a failure cannot cause repeat annual calendar jobs.
    p=plist_path(window)
    p.unlink(missing_ok=True)
    return launchctl("bootout",gui_domain()+"/"+service)


def install(*,now=None,dry_run=False,windows=None):
    if sys.platform!="darwin" and not dry_run:
        raise RuntimeError("STAGE99_ONLY_MACOS_LAUNCHD_SUPPORTED")
    if not dry_run:
        # Mandatory real second-model verdict on the exact source bytes.
        # A CI selftest or GitHub reviewer REQUEST is not independent AI review.
        # Review takes place in Claude CHAT, never via a local Claude CLI.
        # The actual answer is first archived into Git by the project reviewer.
        try:
            import monster_v4_stage102_claude_chat_review_gate as ai_review
        except ImportError:
            from scripts import monster_v4_stage102_claude_chat_review_gate as ai_review
        ai_review.verify_approved()
        isolated_checkout_preflight()
        if not shutil.which("launchctl"):
            raise RuntimeError("STAGE99_NO_LAUNCHCTL")
        if not os.access(Path.home(),os.W_OK):
            raise RuntimeError("STAGE99_HOME_NOT_WRITABLE")
        # Push dry-run verifies the user's current credential can update PR30.
        git("push","--dry-run","origin","HEAD:refs/heads/"+BRANCH,timeout=35)
    start_now=stage91.d1.utc_ms(datetime.now(timezone.utc).isoformat().replace("+00:00","Z")) if now is None else now
    choices=tuple(stage91.WINDOWS if windows is None else windows)
    future=[]
    for window in choices:
        stage91.verify_window(window)
        remaining=stage91.verify_window(window)-CAPTURE_MINUTES_BEFORE*MINUTE_MS-start_now
        if remaining<=0:
            if windows is not None: raise ValueError("STAGE99_INSTALL_AFTER_PLANNED_RUN")
            continue
        future.append(window)
    if not future: raise ValueError("STAGE99_NO_FUTURE_WINDOW_LEFT_TO_INSTALL")
    script=Path(__file__).resolve()
    scheduled={}
    for window in future:
        plist=job_plist(window,script,Path(sys.executable))
        scheduled[window]={"scheduled_local":plist["StartCalendarInterval"],
                           "service":plist["Label"]}
        if dry_run: continue
        LOGS.mkdir(parents=True,exist_ok=True)
        AGENTS.mkdir(parents=True,exist_ok=True)
        STATES.mkdir(parents=True,exist_ok=True)
        name=plist_path(window)
        if name.exists():
            raise RuntimeError("STAGE99_SERVICE_ALREADY_INSTALLED_NO_OVERWRITE_"+window)
        with open(name,"wb") as out:
            plistlib.dump(plist,out)
        if launchctl("bootstrap",gui_domain(),str(name))!=0:
            name.unlink(missing_ok=True)
            raise RuntimeError("STAGE99_LAUNCHCTL_BOOTSTRAP_FAILED_"+window)
        store_status(window,"SCHEDULE_INSTALLED",
                     scheduled_local=plist["StartCalendarInterval"],
                     launchd_label=plist["Label"])
    return scheduled



def safe_git_commit_and_push_for_review():
    """Push one actual other-AI review result to original PR before installation."""
    review="crypto-300-profit-mission/monster/evidence/monster_stage99_actual_external_claude_ai_review.json"
    staged=git("diff","--cached","--name-only",capture=True)
    names=staged.splitlines()
    prefix=review.removesuffix(".json")+"_archive_"
    if (review not in names or len(names)>2
        or any(name!=review and not (
            name.startswith(prefix) and name.endswith(".json")
            ) for name in names)):
        raise RuntimeError("STAGE99_CLAUDE_REVIEW_IS_ONLY_ALLOWED_STAGED_FILE")
    git("-c","user.name=monster-independent-review",
        "-c","user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit","-m","monster: archive real external Claude Stage99 security review before scheduling",
        timeout=45)
    for attempt in range(3):
        try:
            git("push","origin","HEAD:refs/heads/"+BRANCH,timeout=50)
            return git("rev-parse","HEAD",capture=True)
        except RuntimeError:
            if attempt==2:raise
            git("fetch","origin","refs/heads/"+BRANCH,timeout=40)
            git("rebase","FETCH_HEAD",timeout=45)
    raise AssertionError("STAGE99_REVIEW_GIT_PUSH_UNREACHABLE")


def safe_git_commit_and_push(window):
    p=expected_path(window)
    # Exactly one path is allowed to be staged in this isolated clone.
    staged=git("diff","--cached","--name-only",capture=True)
    names=staged.splitlines() if staged else []
    if names and names!=[p]:
        raise RuntimeError("STAGE99_UNEXPECTED_GIT_STAGED_FILES")
    if names:
        git("-c","user.name=monster-source-capture",
            "-c","user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit","-m","monster: archive Stage97 one-shot actual USD-M HTTPS source "+window[:10],
            timeout=35)
    for attempt in range(3):
        try:
            git("push","origin","HEAD:refs/heads/"+BRANCH,timeout=50)
            return git("rev-parse","HEAD",capture=True)
        except RuntimeError:
            if attempt==2:
                raise
            git("fetch","origin","refs/heads/"+BRANCH,timeout=40)
            # Rebase *only* the private isolated clone. Git forbids overwrite on conflicts.
            git("rebase","FETCH_HEAD",timeout=45)
    raise AssertionError("STAGE99_UNREACHABLE_PUSH_RETRY")


def run(window, *,clock=None,capture=None,git_push=None):
    stage91.verify_window(window)
    if clock is None: clock=stage97.now_ms
    if capture is None: capture=stage97.capture_one
    if git_push is None: git_push=safe_git_commit_and_push
    state=STATES/(window[:10]+".json")
    if state.exists():
        existing=json.loads(state.read_text())
        if existing["status"]=="GIT_PUSH_CONFIRMED":
            return "ALREADY_PUSHED"
        # If HTTPS capture already happened, never re-fetch official data.
        # Retry the exact saved SHA even after the original 15-min window.
        if existing.get("source_sha256") and (
            CLONE/expected_path(window)).is_file():
            retry_saved_push(window)
            return "GIT_PUSH_CONFIRMED"
    start=stage91.verify_window(window)
    now=clock()
    if not start-15*MINUTE_MS<=now<start:
        store_status(window,"MISSED_WINDOW_NO_BACKFILL",observed_time_ms=now)
        return "MISSED_WINDOW"
    isolated_checkout_preflight()
    request={"schema":"MONSTER_STAGE97_USER_REQUEST_V1","window_start_utc":window,
             "authorized_one_shot":True}
    # Bounded retries only while within the frozen source window. No post-window API calls.
    evidence=None
    last_error=""
    for attempt in range(3):
        if not start-15*MINUTE_MS<=clock()<start:
            break
        try:
            evidence=capture(request)
            break
        except Exception as error:
            last_error=type(error).__name__+":"+str(error)[:180]
            if attempt<2 and clock()<start-45_000:
                time.sleep(8)
    if evidence is None:
        store_status(window,"SOURCE_FAILED_NO_BACKFILL",reason=last_error)
        return "SOURCE_FAILED"
    if evidence.get("window_start_utc")!=window or evidence.get(
        "source_authenticity")!="RECORDED_HTTPS_BINANCE_REQUEST_AND_RESPONSE_CLOCK_PROOF":
        raise ValueError("STAGE99_CAPTURE_PAYLOAD_NOT_STAGE97_VERIFIED")
    # Real byte evidence is captured once, and stored before any network push;
    # a push failure MUST never cause fresh post-window capture.
    archive=CLONE/expected_path(window)
    if archive.exists():
        raise RuntimeError("STAGE99_REFUSE_TO_OVERWRITE_EXISTING_EVIDENCE")
    archive.parent.mkdir(parents=True,exist_ok=True)
    archive.write_text(json.dumps(evidence,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    store_status(window,"CAPTURE_VALIDATED_GIT_PUSH_PENDING",
                 archive_path=str(archive),source_sha256=stage97.sha(archive.read_bytes()))
    git("add","--",expected_path(window))
    commit=git_push(window)
    store_status(window,"GIT_PUSH_CONFIRMED",git_commit=commit,
                 branch=BRANCH,evidence_path=expected_path(window),
                 source_sha256=stage97.sha(archive.read_bytes()))
    return "GIT_PUSH_CONFIRMED"


def retry_saved_push(window: str):
    """Never re-download historical data; only publish a previously captured SHA."""
    stage91.verify_window(window)
    isolated_checkout_preflight_for_saved()
    path=CLONE/expected_path(window)
    status_file=STATES/(window[:10]+".json")
    if not path.is_file() or not status_file.is_file():
        raise RuntimeError("STAGE99_NO_PREVIOUS_VERIFIED_CAPTURE_TO_RETRY")
    status=json.loads(status_file.read_text())
    saved_sha=status.get("source_sha256")
    if saved_sha is None:
        raise RuntimeError("STAGE99_NO_SAVED_SHA_FOR_PUSH_RETRY")
    original=path.read_bytes()
    if stage97.sha(original)!=saved_sha:
        raise RuntimeError("STAGE99_LOCAL_RAW_CAPTURE_MODIFIED_SHA")
    evidence=json.loads(original.decode("utf-8"))
    if evidence.get("window_start_utc")!=window or evidence.get(
        "source_authenticity")!="RECORDED_HTTPS_BINANCE_REQUEST_AND_RESPONSE_CLOCK_PROOF":
        raise RuntimeError("STAGE99_WRONG_PREVIOUS_CAPTURE")
    packet=evidence["raw_market_packet"]
    def time_body(key):
        part=dict(evidence[key])
        part["json"]=json.loads(part["raw"])
        return part
    raw=packet["raw_exchangeInfo_json"]
    market=dict(evidence["exchange_info_http_capture"])
    market["raw"]=raw
    market["json"]=json.loads(raw)
    verified=stage97.verify_time_proof(
        time_body("before_official_time"),
        time_body("after_official_time"),market,window)
    if verified["raw_market_packet"]!=packet:
        raise RuntimeError("STAGE99_SAVED_CAPTURE_VERIFICATION_CONFLICT")
    git("add","--",expected_path(window))
    committed=safe_git_commit_and_push(window)
    store_status(window,"GIT_PUSH_CONFIRMED",git_commit=committed,
                 branch=BRANCH,evidence_path=expected_path(window),
                 source_sha256=saved_sha,
                 uploaded_from_original_official_raw_without_recapture=True)
    return committed


def isolated_checkout_preflight_for_saved():
    """The only permitted dirty item is our own previously captured archive."""
    if not CLONE.exists() or not (CLONE/".git").is_dir():
        raise RuntimeError("STAGE99_NO_ISOLATED_CLONE_FOR_RETRY")
    if Path(__file__).resolve()!= (CLONE/SCRIPT_IN_CLONE).resolve():
        raise RuntimeError("STAGE99_NOT_RUNNING_IN_ISOLATED_CLONE")
    if git("branch","--show-current",capture=True)!=BRANCH:
        raise RuntimeError("STAGE99_WRONG_BRANCH_FOR_SAVED_CAPTURE")
    remote=git("remote","get-url","origin",capture=True)
    if remote not in ("https://github.com/"+REPO_NAME+".git",
                      "https://github.com/"+REPO_NAME,
                      "git@github.com:"+REPO_NAME+".git"):
        raise RuntimeError("STAGE99_UNEXPECTED_REMOTE_FOR_RETRY")
    git("ls-remote","--exit-code","origin","refs/heads/"+BRANCH,timeout=35)


def execute(window):
    try:
        status=run(window)
        print("STAGE99_SOURCE_JOB_STATUS "+json.dumps({"window":window,"status":status}))
        return 0 if status in ("GIT_PUSH_CONFIRMED","ALREADY_PUSHED") else 2
    except BaseException as exc:
        previous=STATES/(window[:10]+".json")
        persisted=None
        if previous.is_file():
            try:
                persisted=json.loads(previous.read_text())
            except (ValueError, UnicodeDecodeError):
                persisted=None
        if persisted and persisted.get("source_sha256") and (
            CLONE/expected_path(window)).is_file():
            # A failed Git push must NEVER erase the only recovery pointer.
            store_status(window,"GIT_UPLOAD_FAILED_RETRYABLE",
                         reason=type(exc).__name__+":"+str(exc)[:200],
                         source_sha256=persisted["source_sha256"],
                         archive_path=str(CLONE/expected_path(window)))
        else:
            store_status(window,"RUN_FAILED_NO_FALSE_SUCCESS",
                         reason=type(exc).__name__+":"+str(exc)[:200])
        print("STAGE99_FAILED "+type(exc).__name__+": "+str(exc)[:200],file=sys.stderr)
        return 3
    finally:
        # One job only. A loaded launchd job cannot be a perpetual price monitor.
        # The self-unload is the last operation; it may terminate this process.
        bootout(window)


def status():
    out={}
    for w in stage91.WINDOWS:
        p=STATES/(w[:10]+".json")
        out[w]=json.loads(p.read_text()) if p.exists() else {"status":"NOT_INSTALLED"}
        out[w]["launchd_plist_exists"]=plist_path(w).exists()
    return out


def uninstall():
    if sys.platform!="darwin":
        raise RuntimeError("STAGE99_UNINSTALL_REQUIRES_MACOS")
    for w in stage91.WINDOWS:
        bootout(w)
        # Leave source evidence and logs intact for audit. No other agents touched.
    return "STAGE99_ALL_OUR_PLISTS_UNLOADED_AND_REMOVED_NO_EVIDENCE_DELETED"


def selftest():
    assert len(stage91.WINDOWS)==3
    all_jobs=install(now=stage91.verify_window(stage91.WINDOWS[0])-15*MINUTE_MS,
                     dry_run=True)
    assert len(all_jobs)==3
    for window in stage91.WINDOWS:
        a=job_plist(window,Path("/tmp/fake.py"),Path("/usr/bin/python3"))
        assert not a["RunAtLoad"] and not a["KeepAlive"]
        assert "StartInterval" not in a and "WatchPaths" not in a
        assert a["ProgramArguments"][-1]==window
    # Simulated time traveling, without launchctl or network/git.
    try:
        install(now=stage91.verify_window(stage91.WINDOWS[-1])+1,dry_run=True)
    except ValueError as e:
        assert "NO_FUTURE" in str(e)
    else:raise AssertionError("STAGE99_MUST_BLOCK_PAST_WINDOWS")
    for w in stage91.WINDOWS:
        local=job_plist(w,Path("/tmp/fake.py"),Path("/usr/bin/python3"))["StartCalendarInterval"]
        assert 0<=local["Hour"]<24 and 0<=local["Minute"]<60
    print("STAGE99_LAUNCHD_SINGLE_SHOT_THREE_FIXED_FUTURE_WINDOWS_DRYRUN_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("install","run","retry-push","status","uninstall","selftest"))
    p.add_argument("--window")
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    if args.action=="selftest":
        selftest()
    elif args.action=="install":
        print("STAGE99_INSTALLED "+json.dumps(install(dry_run=args.dry_run),
              sort_keys=True,ensure_ascii=False))
    elif args.action=="run":
        if args.window is None:
            p.error("run requires --window from frozen Stage91 windows")
        sys.exit(execute(args.window))
    elif args.action=="retry-push":
        if args.window is None:
            p.error("retry-push requires --window")
        print("STAGE99_SAVED_OFFICIAL_BYTES_PUSHED "+retry_saved_push(args.window))
    elif args.action=="status":
        print(json.dumps(status(),sort_keys=True,ensure_ascii=False,indent=2))
    else:
        print(uninstall())


if __name__=="__main__":
    main()
