# Monster Stage105 Codex／其他AI复审全量源码（固定SHA）

仓库：lxxlx2/ChatGPT_mission_record；原PR #30；采集器锁定commit `2f25f2b921a97ab864ced7a0bc93aab1c9e85169`；精确SHA CI [#38383381420](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383381420) macOS+Ubuntu成功。此文是单一便于完整读取的只读文档，不表示部署授权或其他AI APPROVE。用户不使用Claude CLI；此前独立Codex报告判`BLOCK`，新代码仍需独立审核。

本文件由GitHub工具从固定commit逐个读取原文件全文，顺序合并，不补写源码；文件Git Blob清单如下。

| 路径 | Git blob SHA | 字符数 |
|---|---|---:|
| `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py` | `1431573db90d7655f2ff4e0f5c82607833448188` | 6088 |
| `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py` | `1d4fb2dffed821850b94b9780a9bf83be13904ae` | 10613 |
| `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py` | `2543c2547366867bcb3aa002479fd46c7f83f683` | 27607 |
| `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py` | `c73aedbbb503d9d61955bc2c8ddf3cdf20cc4677` | 11636 |
| `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py` | `df87055342971352cfc60d8670b233ea7c239c21` | 24073 |
| `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py` | `e614326c0aa102a90ab3434f036d3508585ed296` | 8276 |
| `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py` | `06f1cb7964888f896b0e2bfa266763ca691c428c` | 2766 |
| `.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml` | `74dc578ecb143dea6735eda06e7490f73daca2e1` | 4404 |
| `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py` | `6f9db6dab45017cb741f1e7be67a10abcb8a76f0` | 15005 |
| `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md` | `55668e29cac33ababd3e9e844f08545bca89cbde` | 4779 |
| `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py` | `429dac1b52de154edb451f9b1a0a96ba17f4c1a9` | 801 |
| `crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md` | `47d322c2642542db03ae454d9c1e356ef71f2254` | 3406 |

## 逐文件完整原文

### 1. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py` blob=`1431573db90d7655f2ff4e0f5c82607833448188`

```python
#!/usr/bin/env python3
"""Stage105 only: bounded, side-effect-free frozen USD-M source population core.

No historical replay, Shadow module, model import, network call, task, email,
Frank or deployment. Both Stage97 HTTPS collector and Stage91 research reuse
this exact contract; import-time external model execution is impossible here.
"""
from __future__ import annotations

from datetime import datetime,timezone
import hashlib
import json
import re

SCHEMA = "MONSTER_STAGE91_FROZEN_FORWARD_USDM_FULL_POPULATION_REPLAY_V1"
WINDOWS = (
    "2026-10-14T06:00:00Z",
    "2026-10-28T06:00:00Z",
    "2026-11-11T06:00:00Z",
)
EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
WINDOW_MS = 7 * 24 * 3600_000
MIN = 60_000
FRESH_MAX_MS = 15 * MIN


def num(x):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError("STAGE91_INT_TIMESTAMP_REQUIRED")
    return x


def sha256_raw(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValueError("STAGE91_EXCHANGE_INFO_RAW_REQUIRED")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_window(utc: str) -> int:
    if utc not in WINDOWS:
        raise ValueError("STAGE91_NOT_ONE_OF_THE_THREE_FROZEN_FORWARD_DATES")
    if not isinstance(utc,str) or not utc.endswith("Z"):
        raise ValueError("STAGE105_UTC_WINDOW_REQUIRED")
    d=datetime.fromisoformat(utc[:-1]+"+00:00")
    if d.second!=0 or d.microsecond!=0:
        raise ValueError("STAGE105_WINDOW_NOT_MINUTE_ALIGNED")
    return int(d.timestamp()*1000)


def freeze_universe(packet: dict) -> dict:
    """Validate only the archived bytes/clock. No claim of live official origin."""
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        raise ValueError("STAGE91_WRONG_MARKET_SNAPSHOT_SCHEMA")
    start = verify_window(packet.get("window_start_utc"))
    if packet.get("venue") != "BINANCE_USDM" or packet.get("source_url") != EXCHANGE_INFO_URL:
        raise ValueError("STAGE91_WRONG_EXCHANGE_OR_SOURCE_URL")
    cap = num(packet.get("capture_ms"))
    if not start - FRESH_MAX_MS <= cap <= start:
        raise ValueError("STAGE91_UNIVERSE_NOT_CAPTURED_BEFORE_FIXED_START")
    raw = packet.get("raw_exchangeInfo_json")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("STAGE91_EMPTY_OFFICIAL_POPULATION")
    if sha256_raw(raw) != packet.get("raw_sha256"):
        raise ValueError("STAGE91_UNIVERSE_RAW_BYTE_TAMPER")
    try:
        payload = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        raise ValueError("STAGE91_MALFORMED_EXCHANGE_INFO") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise ValueError("STAGE91_EXCHANGE_INFO_MISSING_SYMBOLS")
    if not payload["symbols"]:
        raise ValueError("STAGE91_EMPTY_MARKET_POPULATION")
    # Binance's USD-M exchangeInfo official docs explicitly say to IGNORE its
    # serverTime for clock verification; use a separately fetched /fapi/v1/time
    # HTTP body in the Stage97 authenticated capture validator instead.
    server_time = payload.get("serverTime")
    if server_time is not None:
        num(server_time)
    seen, rows = set(), []
    for item in payload["symbols"]:
        if not isinstance(item, dict):
            raise ValueError("STAGE91_NONOBJECT_MARKET_ROW")
        symbol = item.get("symbol")
        # USD-M exchangeInfo can include dated delivery contracts with "_".
        # Preserve *all* contracts in the population and choose PERPETUAL
        # separately. Do not use Unicode isalnum() as a venue symbol validator.
        if (not isinstance(symbol, str)
            or not re.fullmatch(r"[A-Z0-9]+(?:_[A-Z0-9]+)*",symbol)
            or symbol in seen):
            raise ValueError("STAGE91_MARKET_SYMBOL_DUPLICATE_OR_INVALID")
        seen.add(symbol)
        status = item.get("status")
        contract_type = item.get("contractType")
        quote_asset = item.get("quoteAsset")
        base_asset = item.get("baseAsset")
        if (not isinstance(status,str) or not status
            or not isinstance(contract_type,str) or not contract_type
            or not isinstance(quote_asset,str) or not quote_asset
            or not isinstance(base_asset,str) or not base_asset):
            raise ValueError("STAGE91_INCOMPLETE_OFFICIAL_MARKET_ROW")
        onboard = item.get("onboardDate")
        if onboard is not None:
            num(onboard)
        active_at_capture = (
            status == "TRADING" and contract_type == "PERPETUAL"
            and quote_asset == "USDT" and bool(base_asset)
            and (onboard is None or onboard <= cap)
        )
        rows.append({
            "symbol": symbol, "status_asof_capture": status,
            "contract_type":contract_type, "quote_asset":quote_asset,
            "base_asset":base_asset,
            "onboard_ms":onboard,
            "candidate_for_raw_USDM_attempt":active_at_capture,
            "crypto_identity":"UNKNOWN_NEEDS_INDEPENDENT_PROOF",
            "mapping":"UNKNOWN_UNTIL_INDEPENDENT_UNITS_VERIFIED",
        })
    candidates=[x for x in rows if x["candidate_for_raw_USDM_attempt"]]
    if not candidates:
        raise ValueError("STAGE91_NO_USDT_PERPETUAL_IN_UNIVERSE")
    return {
        "schema":SCHEMA,
        "window_start_utc":packet["window_start_utc"],
        "window_end_utc":datetime.fromtimestamp((start+WINDOW_MS)/1000,timezone.utc).isoformat().replace("+00:00","Z"),
        "raw_sha256":packet["raw_sha256"],
        "capture_ms":cap,
        "population_all_exchange_symbols":len(rows),
        "usd_m_usdt_perpetual_asof_candidates":len(candidates),
        "rows":rows,
        "market_population_archive_consistency":"PASS_UNTRUSTED_ORIGIN",
        "source_authenticity":"UNVERIFIED_EXTERNAL_CAPTURE",
        "exchangeInfo_serverTime_clock_authority":"NONE_OFFICIAL_DOCS_SAY_IGNORE",
        "historical_or_forward_replay":"NOT_RUN",
        "G0_point_in_time_crypto_only":"NOT_DONE",
        "OOS":"NOT_DONE",
        "Gmail":"OFF","Monster_deployment":"NO_GO",
    }
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py`

### 2. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py` blob=`1d4fb2dffed821850b94b9780a9bf83be13904ae`

```python
#!/usr/bin/env python3
"""One-shot, manually triggered point-in-time USD-M population capture.

No scheduler, service, monitoring, trading, notifications or state mutation.
Actual HTTPS GETs occur ONLY with --capture-request in the frozen 15-minute window.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

try:
    import monster_v4_stage105_capture_universe_core as freeze
except ImportError:
    from scripts import monster_v4_stage105_capture_universe_core as freeze

TIME_URL = "https://fapi.binance.com/fapi/v1/time"
EXCHANGE_URL = freeze.EXCHANGE_INFO_URL
MAX_BYTES = 5_000_000
CLOCK_MAX_DRIFT_MS = 5000
WINDOW_MS = 15 * 60000
SCHEMA = "MONSTER_STAGE97_ONE_SHOT_AUTHENTICATED_HTTPS_USDM_UNIVERSE_V1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_ms() -> int:
    return int(time.time()*1000)


def strict_get(url: str, *, max_bytes=MAX_BYTES) -> dict:
    if url not in (TIME_URL, EXCHANGE_URL):
        raise ValueError("STAGE97_NON_OFFICIAL_HTTPS_HOST_OR_PATH")
    req=urllib.request.Request(url,headers={
        "User-Agent":"Monster-Stage97-OneShot-GitHubEvidence/1.0",
        "Accept":"application/json"})
    before=now_ms()
    with urllib.request.urlopen(req,timeout=14) as response:
        if response.status!=200:
            raise ValueError("STAGE97_UNEXPECTED_HTTP_STATUS")
        raw=response.read(max_bytes+1)
        final_url=response.url
        content_type=response.headers.get("Content-Type","")
        if len(raw)>max_bytes or not raw:
            raise ValueError("STAGE97_EMPTY_OR_OVERSIZE_RESPONSE")
    after=now_ms()
    if final_url!=url or "json" not in content_type.lower():
        raise ValueError("STAGE97_HTTP_REDIRECT_OR_NON_JSON_SOURCE")
    text=raw.decode("utf-8","strict")
    try:
        payload=json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("STAGE97_HTTP_BODY_NOT_JSON") from None
    if not isinstance(payload,dict):
        raise ValueError("STAGE97_HTTP_BODY_NOT_OBJECT")
    return {"url":url,"raw":text,"raw_sha256":sha(raw),
            "request_start_ms":before,"response_end_ms":after,
            "content_type":content_type,
            "json":payload}


def check_window(window: str, now: int) -> int:
    start=freeze.verify_window(window)
    if not isinstance(now,int) or isinstance(now,bool) \
       or not start-WINDOW_MS<=now<=start:
        raise ValueError("STAGE97_OUTSIDE_REAL_CAPTURE_15MIN_BEFORE_WINDOW_START")
    return start


def verify_time_proof(first:dict, after:dict,exchange:dict,window:str) -> dict:
    """Raw-byte tampering, official TIME clock drift, and monotonic HTTP bounds."""
    for x in (first, after):
        if x.get("url")!=TIME_URL:
            raise ValueError("STAGE97_TIME_SOURCE_NOT_BINANCE")
        raw=x.get("raw")
        if not isinstance(raw,str) or sha(raw.encode("utf-8"))!=x.get("raw_sha256"):
            raise ValueError("STAGE97_TIME_RAW_SHA_CHANGED")
        payload=json.loads(raw)
        if payload!=x.get("json") or not isinstance(payload.get("serverTime"),int):
            raise ValueError("STAGE97_OFFICIAL_TIME_RAW_MISMATCH")
        mid=(x["request_start_ms"]+x["response_end_ms"])//2
        if abs(payload["serverTime"]-mid)>CLOCK_MAX_DRIFT_MS:
            raise ValueError("STAGE97_INDEPENDENT_BINANCE_SERVER_CLOCK_DRIFT")
        if x["request_start_ms"]>x["response_end_ms"]:
            raise ValueError("STAGE97_NEGATIVE_HTTP_TIME")
    if exchange.get("url")!=EXCHANGE_URL:
        raise ValueError("STAGE97_WRONG_USDM_EXCHANGE_INFO_URL")
    raw=exchange.get("raw")
    if not isinstance(raw,str) or sha(raw.encode("utf-8"))!=exchange.get("raw_sha256"):
        raise ValueError("STAGE97_EXCHANGE_INFO_RAW_SHA_CHANGED")
    if json.loads(raw)!=exchange.get("json"):
        raise ValueError("STAGE97_EXCHANGE_INFO_JSON_RAW_CONFLICT")
    if not (first["request_start_ms"]<=first["response_end_ms"]
            <=exchange["request_start_ms"]<=exchange["response_end_ms"]
            <=after["request_start_ms"]<=after["response_end_ms"]):
        raise ValueError("STAGE97_NOT_CAUSALLY_ORDERED_TLS_GETS")
    before_server=first["json"]["serverTime"]
    after_server=after["json"]["serverTime"]
    if not before_server<=after_server:
        raise ValueError("STAGE97_OFFICIAL_BINANCE_TIME_WENT_BACKWARDS")
    capture=exchange["response_end_ms"]
    start=check_window(window,capture)
    if not start-WINDOW_MS<=before_server<=capture+CLOCK_MAX_DRIFT_MS:
        raise ValueError("STAGE97_OFFICIAL_CLOCK_OUTSIDE_WINDOW")
    if not start-WINDOW_MS<=after_server<=start+CLOCK_MAX_DRIFT_MS:
        raise ValueError("STAGE97_OFFICIAL_AFTER_CLOCK_OUTSIDE_WINDOW")
    packet={
        "schema":freeze.SCHEMA,
        "venue":"BINANCE_USDM","window_start_utc":window,
        "source_url":EXCHANGE_URL,
        "capture_ms":capture,
        "raw_exchangeInfo_json":raw,
        "raw_sha256":exchange["raw_sha256"],
    }
    identity=freeze.freeze_universe(packet)
    return {"schema":SCHEMA,"window_start_utc":window,
      "raw_market_packet":packet,
      "before_official_time":{
        key:first[key] for key in ("url","raw","raw_sha256","request_start_ms","response_end_ms")},
      "after_official_time":{
        key:after[key] for key in ("url","raw","raw_sha256","request_start_ms","response_end_ms")},
      "exchange_info_http_capture":{
        key:exchange[key] for key in ("url","raw_sha256","request_start_ms","response_end_ms","content_type")},
      "source_implementation":"PYTHON_STDLIB_HTTPS_STANDARD_TLS",
      "provenance_ci_env":{
        "GITHUB_RUN_ID":os.environ.get("GITHUB_RUN_ID"),
        "GITHUB_RUN_ATTEMPT":os.environ.get("GITHUB_RUN_ATTEMPT"),
        "GITHUB_SHA":os.environ.get("GITHUB_SHA"),
        "GITHUB_REF":os.environ.get("GITHUB_REF"),
      },
      "snapshot_symbol_summary":{
        k:identity[k] for k in ("population_all_exchange_symbols",
                 "usd_m_usdt_perpetual_asof_candidates")},
      "source_authenticity":"RECORDED_HTTPS_BINANCE_REQUEST_AND_RESPONSE_CLOCK_PROOF",
      "crypto_only_classification":"NOT_VERIFIED",
      "intrawindow_new_listings":"NOT_VERIFIED",
      "G0_full_venue_OOS":"PARTIAL",
      "G1_G2_G3":"NOT_EVALUATED",
      "D1_G3_HISTORICAL":"REJECTED",
      "actual_trades":"NONE",
      "gmail":"OFF","monster_deploy":"NO_GO",
      "autotrade":"NO_GO","frank":"UNCHANGED"}


def capture_one(request:dict,*,get=strict_get,clock=now_ms) -> dict:
    if (not isinstance(request,dict) or
        request.get("schema")!="MONSTER_STAGE97_USER_REQUEST_V1"
        or request.get("authorized_one_shot") is not True):
        raise ValueError("STAGE97_EXPLICIT_ONE_SHOT_GIT_REQUEST_REQUIRED")
    window=request.get("window_start_utc")
    check_window(window,clock())
    first=get(TIME_URL,max_bytes=4096)
    check_window(window,clock())
    exchange=get(EXCHANGE_URL,max_bytes=MAX_BYTES)
    check_window(window,clock())
    last=get(TIME_URL,max_bytes=4096)
    check_window(window,clock())
    return verify_time_proof(first,last,exchange,window)


def fixture(url,body,before,after):
    raw=json.dumps(body,separators=(",",":"))
    return {"url":url,"raw":raw,"raw_sha256":sha(raw.encode()),"json":body,
            "request_start_ms":before,"response_end_ms":after,
            "content_type":"application/json"}


def selftest():
    window=freeze.WINDOWS[0]
    start=freeze.verify_window(window)
    assert check_window(window,start-1000)==start
    for dt in (-16*60000,1000):
        try:check_window(window,start+dt)
        except ValueError as e:assert "OUTSIDE_REAL" in str(e)
        else:raise AssertionError("STAGE97_TIME_MUST_FAIL_CLOSED")
    market={
        "serverTime":start-86_400_000,  # officially ignored, NOT a clock
        "symbols":[{"symbol":"SYNTHUSDT","status":"TRADING",
                    "contractType":"PERPETUAL","baseAsset":"SYNTH",
                    "quoteAsset":"USDT","onboardDate":start-86400000}]
    }
    st=start-2*60000
    first=fixture(TIME_URL,{"serverTime":st+100},st,st+200)
    exchange=fixture(EXCHANGE_URL,market,st+200,st+400)
    last=fixture(TIME_URL,{"serverTime":st+500},st+400,st+600)
    proved=verify_time_proof(first,last,exchange,window)
    assert proved["snapshot_symbol_summary"]["usd_m_usdt_perpetual_asof_candidates"]==1
    assert proved["source_authenticity"].startswith("RECORDED_HTTPS")
    modified=json.loads(json.dumps(exchange))
    modified["json"]["symbols"][0]["symbol"]="TAMPERUSDT"
    try:verify_time_proof(first,last,modified,window)
    except ValueError as e:assert "RAW_CONFLICT" in str(e)
    else:raise AssertionError("STAGE97_TAMPERED_SOURCE_SHOULD_FAIL")
    drift=json.loads(json.dumps(last))
    drift["json"]["serverTime"]=st+20000
    drift["raw"]=json.dumps(drift["json"],separators=(",",":"))
    drift["raw_sha256"]=sha(drift["raw"].encode())
    try:verify_time_proof(first,drift,exchange,window)
    except ValueError as e:assert "CLOCK_DRIFT" in str(e)
    else:raise AssertionError("STAGE97_OFFICIAL_TIME_DRIFT_SHOULD_FAIL")
    request={"schema":"MONSTER_STAGE97_USER_REQUEST_V1",
             "window_start_utc":window,"authorized_one_shot":True}
    def reader(url,*,max_bytes):
        return {TIME_URL:first,EXCHANGE_URL:exchange}[url]
    try:capture_one(request,get=reader,clock=lambda:start+1000)
    except ValueError as e:assert "OUTSIDE_REAL" in str(e)
    else:raise AssertionError("STAGE97_FUTURE_TIME_MUST_BLOCK_ALL_HTTP_GETS")
    assert len(freeze.WINDOWS)==3
    print("STAGE97_OFFICIAL_TIME_SEPARATE_FROM_EXCHANGEINFO_CLOCK_RAW_SHA_AND_ONESHOT_GATE_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--capture-request",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest();return
    if not a.capture_request or not a.out:
        p.error("offline --selftest or explicit --capture-request and --out required")
    request=json.loads(a.capture_request.read_text())
    result=capture_one(request)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE97_REAL_HTTPS_FROZEN_UNIVERSE_CAPTURED "+json.dumps({
        "window":result["window_start_utc"],
        "source":result["source_authenticity"],
        "symbols":result["snapshot_symbol_summary"]},sort_keys=True))


if __name__=="__main__":
    main()
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py`

### 3. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py` blob=`2543c2547366867bcb3aa002479fd46c7f83f683`

```python
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
import tempfile
import time

try:
    import monster_v4_stage97_one_shot_usdm_capture as stage97
    import monster_v4_stage105_capture_universe_core as stage91
except ImportError:
    from scripts import monster_v4_stage97_one_shot_usdm_capture as stage97
    from scripts import monster_v4_stage105_capture_universe_core as stage91

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


def review_gate():
    try:
        import monster_v4_stage102_claude_chat_review_gate as gate
    except ImportError:
        from scripts import monster_v4_stage102_claude_chat_review_gate as gate
    return gate


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


def isolated_checkout_preflight_local():
    """No GitHub request before valuable Binance snapshot capture."""
    if not CLONE.exists() or not (CLONE/".git").is_dir():
        raise RuntimeError("STAGE103_EXPECTED_PRIVATE_CLONE_MISSING")
    if Path(__file__).resolve()!=(CLONE/SCRIPT_IN_CLONE).resolve():
        raise RuntimeError("STAGE103_RUNTIME_NOT_IN_PRIVATE_CLONE")
    if git("branch","--show-current",capture=True)!=BRANCH:
        raise RuntimeError("STAGE103_WRONG_LOCAL_BRANCH")
    origin=git("remote","get-url","origin",capture=True)
    if origin not in ("https://github.com/"+REPO_NAME+".git",
                      "https://github.com/"+REPO_NAME,
                      "git@github.com:"+REPO_NAME+".git"):
        raise RuntimeError("STAGE103_WRONG_REPO_REMOTE")


def assert_reviewed_runtime_source():
    """Cross-check real HEAD tree, reviewed commit tree and current tracked bytes.

    HEAD cannot EQUAL the reviewed commit because the authentic Claude review
    and later user consent are separately committed after code review; requiring
    equality would make the approved Git process impossible. Instead require
    reviewed commit ancestry, all file blobs identical in BOTH trees, and a
    clean execution-path worktree. No future-archive files are checked.
    """
    gate=review_gate()
    review=gate.validate_review()
    gate.validate_authorization()
    head=git("rev-parse","HEAD",capture=True)
    reviewed=review["reviewed_commit"]
    if not head or not reviewed:
        raise RuntimeError("STAGE104_NO_ACTUAL_REVIEWED_HEAD")
    if git("status","--porcelain","--",*gate.REQUIRED_SOURCES,capture=True):
        raise RuntimeError("STAGE104_RUNTIME_EXECUTABLE_FILES_DIRTY")
    for path,expected in review["reviewed_file_git_blobs"].items():
        head_blob=git("rev-parse","HEAD:"+path,capture=True)
        review_blob=git("rev-parse",reviewed+":"+path,capture=True)
        local_blob=git("hash-object","--",path,capture=True)
        if not (head_blob==review_blob==local_blob==expected):
            raise RuntimeError("STAGE104_RUNTIME_TREE_BLOB_NOT_REVIEWED_"+path)
    return {"reviewed_commit":reviewed,"actual_head":head,
            "complete_execution_path_verified":len(gate.REQUIRED_SOURCES)}


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


def read_frank_launchd_labels():
    """Read-only coexistence fingerprint; no management of Frank processes."""
    result=subprocess.run(["launchctl","list"],env=env_no_prompts(),
                          capture_output=True,text=True,timeout=12,check=False)
    if result.returncode!=0:
        raise RuntimeError("STAGE103_CANNOT_VERIFY_FRANK_LAUNCHD_COEXISTENCE")
    return sorted(line.split()[-1] for line in result.stdout.splitlines()
                  if line.strip() and "frank" in line.lower())


def plist_path(window):
    return AGENTS/(label_for(window)+".plist")


def assert_unloaded(window):
    """Read-only BOTH registry and named-service state; uncertainty is FAILURE."""
    service=label_for(window)
    registry=subprocess.run(["launchctl","list"],env=env_no_prompts(),
                            capture_output=True,text=True,timeout=15,check=False)
    if registry.returncode!=0:
        raise RuntimeError("STAGE104_LAUNCHD_LIST_UNAVAILABLE_CANNOT_PROVE_UNLOADED")
    labels={line.split()[-1] for line in registry.stdout.splitlines()
            if line.strip() and len(line.split())>=3}
    detail=subprocess.run(["launchctl","print",gui_domain()+"/"+service],
                          env=env_no_prompts(),capture_output=True,text=True,
                          timeout=15,check=False)
    if service in labels or detail.returncode==0:
        raise RuntimeError("STAGE104_SERVICE_STILL_LOADED_"+service)
    # A failing launchctl print plus an explicitly absent exact label from the
    # successful launchctl list proves the service is no longer registered.
    return True


def bootout(window):
    service=label_for(window)
    # Keep plist until the service is VERIFIED absent, for safe manual recovery.
    code=launchctl("bootout",gui_domain()+"/"+service)
    if code!=0:
        raise RuntimeError("STAGE104_LAUNCHD_BOOTOUT_FAILED_RC_"+str(code))
    assert_unloaded(window)
    plist_path(window).unlink(missing_ok=True)
    return 0


def install(*,now=None,dry_run=False,windows=None):
    if sys.platform!="darwin" and not dry_run:
        raise RuntimeError("STAGE99_ONLY_MACOS_LAUNCHD_SUPPORTED")
    if not dry_run:
        # Real Claude CHAT approval is not installation authorization.
        approval=review_gate().validate_authorization()
        review_gate().interactive_install_consent(approval)
        isolated_checkout_preflight_local()
        assert_reviewed_runtime_source()
        if not shutil.which("launchctl"):
            raise RuntimeError("STAGE99_NO_LAUNCHCTL")
        if not os.access(Path.home(),os.W_OK):
            raise RuntimeError("STAGE99_HOME_NOT_WRITABLE")
        # Push dry-run verifies the user's current credential can update PR30.
        git("push","--dry-run","origin","HEAD:refs/heads/"+BRANCH,timeout=35)
    start_now=int(datetime.now(timezone.utc).timestamp()*1000) if now is None else now
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
    planned={w:job_plist(w,script,Path(sys.executable)) for w in future}
    scheduled={w:{"scheduled_local":planned[w]["StartCalendarInterval"],
                  "service":planned[w]["Label"]} for w in future}
    if dry_run:
        return scheduled
    # Check all conflicts BEFORE creating even the first job.
    AGENTS.mkdir(parents=True,exist_ok=True)
    if any(plist_path(w).exists() for w in future):
        raise RuntimeError("STAGE103_ONE_OF_THE_PLISTS_ALREADY_EXISTS_NO_PARTIAL_INSTALL")
    before_frank=read_frank_launchd_labels()
    LOGS.mkdir(parents=True,exist_ok=True)
    STATES.mkdir(parents=True,exist_ok=True)
    added=[]
    try:
        for window in future:
            destination=plist_path(window)
            with open(destination,"wb") as out:
                plistlib.dump(planned[window],out)
            added.append(window)
            if launchctl("bootstrap",gui_domain(),str(destination))!=0:
                raise RuntimeError("STAGE103_LAUNCHCTL_BOOTSTRAP_FAILED_"+window)
            store_status(window,"SCHEDULE_INSTALLED",
                         scheduled_local=planned[window]["StartCalendarInterval"],
                         launchd_label=planned[window]["Label"])
        if read_frank_launchd_labels()!=before_frank:
            raise RuntimeError("STAGE103_FRANK_LAUNCHD_COEXISTENCE_CHANGED_ABORT")
    except BaseException as install_error:
        rollback_failures=[]
        journal_failures=[]
        # Never let a disk-full/readonly state file abort rollback of the NEXT
        # already-loaded launchd service. Treat journal and unload separately.
        for window in reversed(added):
            unloaded=False
            reason=""
            try:
                bootout(window)
                unloaded=True
            except BaseException as failure:
                reason=type(failure).__name__+":"+str(failure)[:180]
                rollback_failures.append(window)
            status=("INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED" if unloaded
                    else "ROLLBACK_FAILED_SERVICE_STILL_LOADED")
            try:
                store_status(window,status,reason=reason)
            except BaseException as journal_error:
                journal_failures.append(window)
                # stderr is the fallback if state volume has no free space.
                print("STAGE105_ROLLBACK_JOURNAL_FAILED window="+window+
                      " status="+status+" error="+type(journal_error).__name__,
                      file=sys.stderr)
        if rollback_failures or journal_failures:
            raise RuntimeError(
                "STAGE105_INSTALL_ROLLBACK_SAFETY_UNVERIFIED"
                " services="+",".join(rollback_failures)+
                " journal="+",".join(journal_failures)
            ) from install_error
        raise
    return scheduled



def _git_in_worktree(where: Path, *args, capture=False, timeout=55):
    proc=subprocess.run(["git","-C",str(where),*args],env=env_no_prompts(),
             text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
             timeout=timeout,check=False)
    if proc.returncode:
        raise RuntimeError("STAGE103_UPLOAD_GIT_FAILED_"+str(args[0])+
                           "_RC_"+str(proc.returncode))
    return proc.stdout.strip() if capture else None


def safe_git_commit_and_push(window):
    """Upload captured bytes using disposable Git worktrees, never rebase code.

    GitHub is contacted only after bytes were saved locally. The active
    reviewed executable clone is never rebased, force-pushed or checked out.
    """
    origin=CLONE/expected_path(window)
    if not origin.is_file():
        raise RuntimeError("STAGE103_REAL_CAPTURE_FILE_MISSING")
    proof=origin.read_bytes()
    packet=json.loads(proof)
    if packet.get("window_start_utc")!=window:
        raise RuntimeError("STAGE103_WRONG_CAPTURED_WINDOW")
    local_sha=stage97.sha(proof)
    ref="refs/heads/"+BRANCH
    for attempt in range(3):
        git("fetch","origin",ref,timeout=35)
        with tempfile.TemporaryDirectory(prefix="monster-stage103-upload-") as directory:
            worktree=Path(directory)/"checkout"
            git("worktree","add","--detach",str(worktree),"FETCH_HEAD",timeout=35)
            try:
                remote=worktree/expected_path(window)
                if remote.exists():
                    if stage97.sha(remote.read_bytes())!=local_sha:
                        raise RuntimeError("STAGE103_EXISTING_REMOTE_ARCHIVE_DIFFERS")
                    return _git_in_worktree(worktree,"rev-parse","HEAD",capture=True)
                remote.parent.mkdir(parents=True,exist_ok=True)
                remote.write_bytes(proof)
                _git_in_worktree(worktree,"add","--",expected_path(window))
                _git_in_worktree(worktree,
                    "-c","user.name=monster-local-capture",
                    "-c","user.email=monster-local-capture@users.noreply.github.com",
                    "commit","-m","monster: archive original USD-M source "+window[:10])
                review_gate().validate_authorization()
                if stage97.sha(origin.read_bytes())!=local_sha:
                    raise RuntimeError("STAGE103_ARCHIVED_ORIGINAL_BYTES_CHANGED")
                try:
                    _git_in_worktree(worktree,"push","origin","HEAD:"+ref,timeout=45)
                    return _git_in_worktree(worktree,"rev-parse","HEAD",capture=True)
                except RuntimeError:
                    if attempt==2:raise
            finally:
                git("worktree","remove","--force",str(worktree),timeout=30)
    raise RuntimeError("STAGE103_UPLOAD_RETRIES_EXHAUSTED")


def run(window, *,clock=None,capture=None,git_push=None):
    stage91.verify_window(window)
    # Integrity/consent before even returning ALREADY_PUSHED, or retrying
    # SHA from a prior capture. The executable cannot silently drift.
    assert_reviewed_runtime_source()
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
    isolated_checkout_preflight_local()
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
    commit=git_push(window)
    store_status(window,"GIT_PUSH_CONFIRMED",git_commit=commit,
                 branch=BRANCH,evidence_path=expected_path(window),
                 source_sha256=stage97.sha(archive.read_bytes()))
    return "GIT_PUSH_CONFIRMED"


def retry_saved_push(window: str):
    """Never re-download historical data; only publish a previously captured SHA."""
    stage91.verify_window(window)
    assert_reviewed_runtime_source()
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
    review_gate().validate_authorization()
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
        # A failed self-unload must never be represented as clean exit.
        # Catch to preserve earlier trace, but force a nonzero process result.
        try:
            bootout(window)
        except (RuntimeError,OSError,subprocess.TimeoutExpired) as unload_error:
            prior=STATES/(window[:10]+".json")
            saved={}
            if prior.is_file():
                try:saved=json.loads(prior.read_text())
                except (ValueError,UnicodeDecodeError):saved={}
            store_status(window,"AUTO_UNLOAD_FAILED_SERVICE_MAY_REMAIN",
                         source_sha256=saved.get("source_sha256"),
                         previous_state=saved.get("status"),
                         reason=type(unload_error).__name__+":"+str(unload_error)[:180])
            print("STAGE104_UNLOAD_FAILED_SERVICE_MAY_REMAIN",
                  file=sys.stderr)
            # SystemExit in finally signals FAILURE, never a clean task exit.
            raise SystemExit(4) from unload_error


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
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py`

### 4. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py` blob=`c73aedbbb503d9d61955bc2c8ddf3cdf20cc4677`

```python
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
OTHER_APPROVED_REVIEW_ORIGINS = (
    REVIEW_ORIGIN,
    "CODEX_CHAT_USER_SUPPLIED_FULL_OUTPUT",
)
# Only actual user-supplied independent review output is accepted. The name
# Claude in this historical filename is NOT a requirement to use Claude CLI.
REQUIRED_SOURCES = (
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py",
    "crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py",
    "crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py",
    "crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py",
    "crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py",
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
    if (review.get("schema")!=SCHEMA or review.get("source_origin") not in OTHER_APPROVED_REVIEW_ORIGINS
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
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py`

### 5. crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py` blob=`df87055342971352cfc60d8670b233ea7c239c21`

```python
#!/usr/bin/env python3
"""No-network Stage99 orchestration tests: never launch a real job or touch Mac state."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

try:
    import monster_v4_stage99_mac_launchd_one_shot as module
    import monster_v4_stage97_one_shot_usdm_capture as stage97
    import monster_v4_stage91_forward_oos_replay_gate as freeze
except ImportError:
    from scripts import monster_v4_stage99_mac_launchd_one_shot as module
    from scripts import monster_v4_stage97_one_shot_usdm_capture as stage97
    from scripts import monster_v4_stage91_forward_oos_replay_gate as freeze


ORIGINAL_ASSERT_UNLOADED = module.assert_unloaded


class OneShotIsolatedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.patches=[
            patch.object(module,"ROOT",root),
            patch.object(module,"CLONE",root/"repo"),
            patch.object(module,"STATES",root/"state"),
            patch.object(module,"LOGS",root/"logs"),
            patch.object(module,"AGENTS",root/"LaunchAgents"),
            patch.object(module,"assert_reviewed_runtime_source",
                         return_value={"complete_execution_path_verified":8}),
            patch.object(module,"assert_unloaded",return_value=True),
            patch.object(module,"review_gate",return_value=Mock(
                validate_authorization=Mock(return_value={
                    "review_fingerprint":"a"*64}),
                interactive_install_consent=Mock(return_value=True))),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        module.CLONE.mkdir(parents=True,exist_ok=True)
        module.STATES.mkdir(parents=True,exist_ok=True)
        self.window=freeze.WINDOWS[0]
        self.start=freeze.verify_window(self.window)

    def fake_official(self):
        # No Internet involved: a hash-bound artificial reference for isolation tests.
        t=self.start-2*60000
        market={
            "serverTime":t-86_400_000,
            "symbols":[{
                "symbol":"SYNTHUSDT","status":"TRADING",
                "contractType":"PERPETUAL","baseAsset":"SYNTH",
                "quoteAsset":"USDT","onboardDate":t-3600000
            }]}
        first=stage97.fixture(stage97.TIME_URL,{"serverTime":t+100},t,t+200)
        exchange=stage97.fixture(stage97.EXCHANGE_URL,market,t+200,t+400)
        last=stage97.fixture(stage97.TIME_URL,{"serverTime":t+500},t+400,t+600)
        return stage97.verify_time_proof(first,last,exchange,self.window)

    def test_mac_plist_has_exactly_one_calendar_run_and_no_periodic_monitor(self):
        b=module.job_plist(self.window,Path("/tmp/repo/source.py"),Path("/usr/bin/python3"),
            user_tz=ZoneInfo("Asia/Bangkok"))
        self.assertFalse(b["RunAtLoad"])
        self.assertFalse(b["KeepAlive"])
        self.assertNotIn("StartInterval",b)
        self.assertNotIn("WatchPaths",b)
        self.assertNotIn("Program",b)
        self.assertEqual(b["StartCalendarInterval"],
            {"Month":10,"Day":14,"Hour":12,"Minute":48})
        us=module.job_plist(self.window,Path("/tmp/repo/source.py"),Path("/usr/bin/python3"),
            user_tz=ZoneInfo("America/Los_Angeles"))
        self.assertEqual(us["StartCalendarInterval"],
            {"Month":10,"Day":13,"Hour":22,"Minute":48})
        self.assertIn(self.window,b["ProgramArguments"])

    def test_offline_install_never_performs_network_or_writes_plist(self):
        out=module.install(now=self.start-15*60000,dry_run=True)
        self.assertEqual(len(out),3)
        self.assertFalse(module.AGENTS.exists())
        self.assertTrue(all(x in out for x in freeze.WINDOWS))

    def test_approved_review_installs_exact_three_isolated_launchd_jobs(self):
        try:
            import monster_v4_stage102_claude_chat_review_gate as external_ai
        except ImportError:
            from scripts import monster_v4_stage102_claude_chat_review_gate as external_ai
        now=self.start-20*60000
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank.daemon"]), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            installed=module.install(now=now,dry_run=False)
        self.assertEqual(len(installed),3)
        self.assertEqual(launch.call_count,3)
        for w in freeze.WINDOWS:
            plist=module.plist_path(w)
            self.assertTrue(plist.exists())
            with open(plist,"rb") as f:
                import plistlib
                data=plistlib.load(f)
            self.assertFalse(data["KeepAlive"])
            self.assertFalse(data["RunAtLoad"])
            self.assertEqual(data["ProgramArguments"][-1],w)
            self.assertTrue(data["Label"].startswith("com.lxxlx2.monster.stage99."))
            self.assertEqual(module.status()[w]["status"],"SCHEDULE_INSTALLED")
        with patch.object(module,"launchctl",return_value=0) as boot:
            for w in freeze.WINDOWS:module.bootout(w)
        self.assertEqual(boot.call_count,3)
        self.assertTrue(all(not module.plist_path(w).exists() for w in freeze.WINDOWS))

    def test_stage103_install_preflights_all_plists_before_creating_any(self):
        module.AGENTS.mkdir(parents=True,exist_ok=True)
        second=module.plist_path(freeze.WINDOWS[1])
        second.write_text("other existing stage99 job must remain")
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"PLISTS_ALREADY_EXISTS"):
                module.install(now=self.start-20*60000,dry_run=False)
        launch.assert_not_called()
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())
        self.assertEqual(second.read_text(),"other existing stage99 job must remain")

    def test_stage103_bootstrap_midfailure_rolls_back_all_created_jobs(self):
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",side_effect=[0,1,0,0]) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"BOOTSTRAP_FAILED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertTrue(all(not module.plist_path(w).exists() for w in freeze.WINDOWS))
        for w in freeze.WINDOWS[:2]:
            self.assertEqual(module.status()[w]["status"],"INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED")
        self.assertEqual(module.status()[freeze.WINDOWS[2]]["status"],"NOT_INSTALLED")

    def test_stage103_frank_mutation_aborts_only_our_services(self):
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",
                          side_effect=[["frank.original"],["frank.original","frank.extra"]]), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"FRANK_LAUNCHD_COEXISTENCE_CHANGED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,6)
        self.assertTrue(all(not module.plist_path(w).exists() for w in freeze.WINDOWS))

    def test_stage104_bootout_failed_retains_plist_and_cannot_claim_success(self):
        module.AGENTS.mkdir(parents=True,exist_ok=True)
        file=module.plist_path(self.window)
        file.write_text("keep for safety")
        with patch.object(module,"launchctl",return_value=5):
            with self.assertRaisesRegex(RuntimeError,"BOOTOUT_FAILED"):
                module.bootout(self.window)
        self.assertTrue(file.is_file())

    def test_stage104_rollback_marks_still_loaded_on_failure(self):
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",side_effect=[0,1,7,0]) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"ROLLBACK_SAFETY_UNVERIFIED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertEqual(module.status()[freeze.WINDOWS[1]]["status"],
                         "ROLLBACK_FAILED_SERVICE_STILL_LOADED")
        self.assertTrue(module.plist_path(freeze.WINDOWS[1]).exists())
        self.assertEqual(module.status()[freeze.WINDOWS[0]]["status"],
                         "INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED")
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())

    def test_stage104_assert_unloaded_checks_both_registry_and_detail(self):
        from types import SimpleNamespace
        absent="PID\tStatus\tLabel\n42\t0\tcom.someone.frank\n"
        present=absent+"123\t0\t"+module.label_for(self.window)+"\n"
        def response(rc,txt=""):
            return SimpleNamespace(returncode=rc,stdout=txt,stderr="")
        with patch.object(module.subprocess,"run",side_effect=[
                response(0,absent),response(113)]):
            self.assertTrue(ORIGINAL_ASSERT_UNLOADED(self.window))
        with patch.object(module.subprocess,"run",side_effect=[
                response(0,present),response(113)]):
            with self.assertRaisesRegex(RuntimeError,"STILL_LOADED"):
                ORIGINAL_ASSERT_UNLOADED(self.window)
        with patch.object(module.subprocess,"run",side_effect=[
                response(0,absent),response(0,"still exists")]):
            with self.assertRaisesRegex(RuntimeError,"STILL_LOADED"):
                ORIGINAL_ASSERT_UNLOADED(self.window)
        with patch.object(module.subprocess,"run",side_effect=[response(1)]):
            with self.assertRaisesRegex(RuntimeError,"CANNOT_PROVE"):
                ORIGINAL_ASSERT_UNLOADED(self.window)

    def test_stage104_bootout_verification_failure_does_not_delete_plist(self):
        module.AGENTS.mkdir(parents=True,exist_ok=True)
        file=module.plist_path(self.window)
        file.write_text("do not erase the only recovery pointer")
        with patch.object(module,"launchctl",return_value=0), \
             patch.object(module,"assert_unloaded",side_effect=RuntimeError(
                 "STAGE104_SERVICE_STILL_LOADED")):
            with self.assertRaisesRegex(RuntimeError,"SERVICE_STILL_LOADED"):
                module.bootout(self.window)
        self.assertTrue(file.exists())

    def test_stage105_enospc_status_write_does_not_interrupt_other_bootouts(self):
        attempts=[]
        def fail_disk(window,status,**kwargs):
            attempts.append((window,status))
            if window==freeze.WINDOWS[1] or status.startswith("INSTALL_ROLLED"):
                raise OSError(28,"synthetic disk full")
            return None
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module,"store_status",side_effect=fail_disk), \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"ROLLBACK_SAFETY_UNVERIFIED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertEqual(
            [call.args[0] for call in launch.call_args_list],
            ["bootstrap","bootstrap","bootout","bootout"])
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())
        self.assertFalse(module.plist_path(freeze.WINDOWS[1]).exists())
        self.assertTrue(any(x[0]==freeze.WINDOWS[0] and
                            x[1]=="INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED"
                            for x in attempts))
        self.assertTrue(any(x[0]==freeze.WINDOWS[1] and
                            x[1]=="INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED"
                            for x in attempts))

    def test_stage105_disk_full_and_one_failed_unload_still_attempts_every_service(self):
        def fail_disk(window,status,**kwargs):
            if status=="SCHEDULE_INSTALLED" and window==freeze.WINDOWS[1]:
                raise OSError(28,"synthetic disk full")
            if status.startswith("INSTALL_ROLLED") or status.startswith("ROLLBACK_FAILED"):
                raise OSError(28,"synthetic rollback journal full")
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",side_effect=[0,0,7,0]) as launch, \
             patch.object(module,"store_status",side_effect=fail_disk), \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"ROLLBACK_SAFETY_UNVERIFIED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())
        self.assertTrue(module.plist_path(freeze.WINDOWS[1]).exists())

    def test_no_frozen_date_can_be_replaced(self):
        with self.assertRaises(ValueError):
            module.label_for("2026-10-15T06:00:00Z")
        with self.assertRaises(ValueError):
            module.install(now=self.start+1000,windows=(self.window,),dry_run=True)

    def test_real_path_is_exact_original_pr_not_main(self):
        expected=module.expected_path(self.window)
        self.assertIn("monster_stage97_point_in_time_usdm_2026-10-14_raw_https.json",expected)
        self.assertEqual(module.BRANCH,"research/monster-v4-local-discovery-20261010")
        self.assertNotIn("main",expected)

    def test_capture_and_git_push_full_success_with_replay_guard(self):
        proof=self.fake_official()
        f=Mock(return_value=proof)
        push=Mock(return_value="f"*40)
        with patch.object(module,"isolated_checkout_preflight_local"), patch.object(module,"git"):
            result=module.run(self.window,clock=lambda:self.start-1000,
                              capture=f,git_push=push)
        self.assertEqual(result,"GIT_PUSH_CONFIRMED")
        self.assertEqual(f.call_count,1)
        self.assertEqual(push.call_count,1)
        archive=module.CLONE/module.expected_path(self.window)
        saved=json.loads(archive.read_text())
        self.assertEqual(saved["window_start_utc"],self.window)
        status=module.status()[self.window]
        self.assertEqual(status["status"],"GIT_PUSH_CONFIRMED")
        self.assertTrue(status["source_sha256"])
        with patch.object(module,"isolated_checkout_preflight_local") as pre:
            ret=module.run(self.window,clock=lambda:self.start-900,
                           capture=f,git_push=push)
        self.assertEqual(ret,"ALREADY_PUSHED")
        self.assertEqual(f.call_count,1)
        pre.assert_not_called()

    def test_stale_window_fails_before_network(self):
        get=Mock()
        with patch.object(module,"isolated_checkout_preflight_local") as checkout:
            status=module.run(self.window,clock=lambda:self.start+2,
                              capture=get,git_push=Mock())
        self.assertEqual(status,"MISSED_WINDOW")
        self.assertEqual(module.status()[self.window]["status"],"MISSED_WINDOW_NO_BACKFILL")
        get.assert_not_called()
        checkout.assert_not_called()

    def test_failed_source_does_not_commit_false_evidence(self):
        get=Mock(side_effect=ValueError("synthetic no network"))
        push=Mock()
        with patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module.time,"sleep"), \
             patch.object(module,"git"):
            status=module.run(self.window,clock=lambda:self.start-120000,
                              capture=get,git_push=push)
        self.assertEqual(status,"SOURCE_FAILED")
        self.assertEqual(get.call_count,3)
        push.assert_not_called()
        self.assertEqual(module.status()[self.window]["status"],"SOURCE_FAILED_NO_BACKFILL")

    def test_git_failure_preserves_sha_and_retry_never_recaptures(self):
        evidence=self.fake_official()
        fail=Mock(side_effect=RuntimeError("fake git push denied"))
        with patch.object(module,"isolated_checkout_preflight_local"), patch.object(module,"git"):
            with self.assertRaisesRegex(RuntimeError,"fake git push"):
                module.run(self.window,clock=lambda:self.start-1000,
                           capture=lambda _:evidence,git_push=fail)
        archive=module.CLONE/module.expected_path(self.window)
        self.assertTrue(archive.exists())
        self.assertEqual(module.status()[self.window]["status"],
                         "CAPTURE_VALIDATED_GIT_PUSH_PENDING")
        with patch.object(module,"isolated_checkout_preflight_for_saved"), \
             patch.object(module,"git"), \
             patch.object(module,"safe_git_commit_and_push",return_value="a"*40):
            result=module.retry_saved_push(self.window)
        self.assertEqual(result,"a"*40)
        self.assertTrue(module.status()[self.window][
            "uploaded_from_original_official_raw_without_recapture"])
        self.assertEqual(module.status()[self.window]["status"],"GIT_PUSH_CONFIRMED")

    def test_tampered_saved_evidence_cannot_upload(self):
        proof=self.fake_official()
        with patch.object(module,"isolated_checkout_preflight_local"), patch.object(module,"git"):
            with self.assertRaises(RuntimeError):
                module.run(self.window,clock=lambda:self.start-1000,
                           capture=lambda _:proof,
                           git_push=Mock(side_effect=RuntimeError("blocked")))
        path=module.CLONE/module.expected_path(self.window)
        path.write_text(path.read_text()+" ")
        with patch.object(module,"isolated_checkout_preflight_for_saved"), \
             patch.object(module,"git"), \
             patch.object(module,"safe_git_commit_and_push") as push:
            with self.assertRaisesRegex(RuntimeError,"MODIFIED_SHA"):
                module.retry_saved_push(self.window)
            push.assert_not_called()

    def test_raw_frozen_15min_window_not_extended_by_retry(self):
        proof=self.fake_official()
        self.assertEqual(proof["snapshot_symbol_summary"][
            "usd_m_usdt_perpetual_asof_candidates"],1)
        with patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"):
            status=module.run(self.window,clock=lambda:self.start-16*60000,
                              capture=Mock(return_value=proof),
                              git_push=Mock(return_value="a"*40))
        self.assertEqual(status,"MISSED_WINDOW")

    def test_real_install_is_hard_blocked_without_other_ai_review(self):
        from unittest.mock import patch
        try:
            import monster_v4_stage102_claude_chat_review_gate as external_ai
        except ImportError:
            from scripts import monster_v4_stage102_claude_chat_review_gate as external_ai
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"review_gate",return_value=Mock(
                 validate_authorization=Mock(side_effect=
                     RuntimeError("STAGE103_USER_INSTALL_AUTHORIZATION_NOT_GIVEN")))) as blocked_gate, \
             patch.object(module,"isolated_checkout_preflight") as checkout, \
             patch.object(module,"launchctl") as launch:
            with self.assertRaisesRegex(RuntimeError,"AUTHORIZATION_NOT_GIVEN"):
                module.install(now=self.start-15*60000,dry_run=False)
            blocked_gate.return_value.validate_authorization.assert_called_once()
            checkout.assert_not_called()
            launch.assert_not_called()

    def test_external_ai_mock_result_never_counts_as_approval(self):
        try:
            import monster_v4_stage102_claude_chat_review_gate as external_ai
        except ImportError:
            from scripts import monster_v4_stage102_claude_chat_review_gate as external_ai
        with self.assertRaises(RuntimeError):
            external_ai.validate_authorization(root=module.CLONE,
               read_blob=lambda _: "a"*40,is_ancestor=lambda _:True)
        external_ai.selftest()
        self.assertFalse((module.CLONE / external_ai.RECEIPT).exists())

    def test_execute_git_failure_preserves_retryable_original_bytes(self):
        evidence=self.fake_official()
        with patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"bootout") as unload:
            with patch.object(module.stage97,"now_ms",return_value=self.start-1000), \
                 patch.object(module.stage97,"capture_one",return_value=evidence), \
                 patch.object(module,"safe_git_commit_and_push",
                              side_effect=RuntimeError("synthetic push failed")):
                result=module.execute(self.window)
        self.assertEqual(result,3)
        persisted=module.status()[self.window]
        self.assertEqual(persisted["status"],"GIT_UPLOAD_FAILED_RETRYABLE")
        self.assertTrue(persisted["source_sha256"])
        self.assertTrue((module.CLONE / module.expected_path(self.window)).exists())
        unload.assert_called_once()
        with patch.object(module,"isolated_checkout_preflight_for_saved"), \
             patch.object(module,"git"), \
             patch.object(module,"safe_git_commit_and_push",return_value="a"*40), \
             patch.object(module.stage97,"capture_one") as no_second_capture:
            self.assertEqual(module.run(self.window,clock=lambda:self.start+9000),
                             "GIT_PUSH_CONFIRMED")
            no_second_capture.assert_not_called()
        self.assertEqual(module.status()[self.window]["status"],"GIT_PUSH_CONFIRMED")

    def test_uninstall_can_only_mention_our_exact_three_labels(self):
        for w in freeze.WINDOWS:
            self.assertTrue(module.label_for(w).startswith(
                "com.lxxlx2.monster.stage99.usdm."))
        self.assertNotIn("frank"," ".join(module.label_for(w) for w in freeze.WINDOWS))


if __name__=="__main__":
    unittest.main(verbosity=2)
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py`

### 6. crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py` blob=`e614326c0aa102a90ab3434f036d3508585ed296`

```python
#!/usr/bin/env python3
"""Stage103 real LOCAL Git integration: no mocks for Git, no network, no installs."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock,patch

try:
    import monster_v4_stage99_mac_launchd_one_shot as stage99
except ImportError:
    from scripts import monster_v4_stage99_mac_launchd_one_shot as stage99


def command(*args,cwd=None):
    result=subprocess.run(list(args),cwd=cwd,check=True,text=True,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=35)
    return result.stdout.strip()


class LocalGitUploaderIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        t=Path(self.temp.name)
        self.remote=t/"remote.git"
        self.seed=t/"seed"
        self.second=t/"second"
        self.clone=t/"private"/"repo"
        command("git","init","--bare",str(self.remote))
        command("git","init",str(self.seed))
        command("git","-C",str(self.seed),"switch","-c",stage99.BRANCH)
        (self.seed/"README.md").write_text("stage103 git test origin\n")
        self.review_target=(
            "crypto-300-profit-mission/local-agent/scripts/"
            "monster_v4_stage105_capture_universe_core.py")
        original=self.seed/self.review_target
        original.parent.mkdir(parents=True,exist_ok=True)
        original.write_text("FROZEN_REVIEWED_SOURCE_FIXTURE=1\n")
        command("git","-C",str(self.seed),"add","--all")
        command("git","-C",str(self.seed),"-c","user.name=fixture",
                "-c","user.email=fixture@example.test","commit","-m","initial local")
        command("git","-C",str(self.seed),"remote","add","origin",str(self.remote))
        command("git","-C",str(self.seed),"push","origin",
                "HEAD:refs/heads/"+stage99.BRANCH)
        self.clone.parent.mkdir(parents=True)
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(self.clone))
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(self.second))
        patch_clone=patch.object(stage99,"CLONE",self.clone)
        patch_clone.start();self.addCleanup(patch_clone.stop)
        review=patch.object(stage99,"review_gate",return_value=Mock(
            validate_authorization=Mock(return_value={"review_fingerprint":"a"*64})))
        review.start();self.addCleanup(review.stop)
        self.window=stage99.stage91.WINDOWS[0]
        self.path=stage99.expected_path(self.window)
        original=self.clone/self.path
        original.parent.mkdir(parents=True,exist_ok=True)
        original.write_text(json.dumps({
            "schema":"TEST_CAPTURE_BYTES_NOT_ACTUAL_BINANCE",
            "window_start_utc":self.window,"proof":"fixed synthetic bytes"},
            sort_keys=True)+"\n")
        self.original=original
        self.local_head=command("git","-C",str(self.clone),"rev-parse","HEAD")

    def another_commit(self, name, content):
        path=self.second/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content)
        command("git","-C",str(self.second),"add","--",name)
        command("git","-C",str(self.second),"-c","user.name=independent",
                "-c","user.email=independent@example.test","commit","-m","unrelated")
        command("git","-C",str(self.second),"push","origin",
                "HEAD:refs/heads/"+stage99.BRANCH)

    def test_actual_local_bare_git_source_push_preserves_remote_changes_and_reviewed_clone(self):
        self.another_commit("unrelated_remote_change.md","do not overwrite\n")
        pushed=stage99.safe_git_commit_and_push(self.window)
        self.assertEqual(len(pushed),40)
        self.assertEqual(command("git","-C",str(self.clone),"rev-parse","HEAD"),
                         self.local_head)
        self.assertEqual(command("git","-C",str(self.clone),"branch","--show-current"),
                         stage99.BRANCH)
        self.assertEqual(command("git","-C",str(self.clone),"ls-files",self.path),"")
        self.assertFalse((self.clone/".git"/"rebase-merge").exists())
        self.assertFalse((self.clone/".git"/"rebase-apply").exists())
        fetched=t=Path(self.temp.name)/"checked"
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(fetched))
        self.assertEqual((fetched/self.path).read_bytes(),self.original.read_bytes())
        self.assertEqual((fetched/"unrelated_remote_change.md").read_text(),"do not overwrite\n")
        second=stage99.safe_git_commit_and_push(self.window)
        self.assertEqual(second,pushed)

    def test_reviewed_runtime_git_tree_rejects_dirty_and_recommitted_sources(self):
        one=self.review_target
        pinned=self.local_head
        frozen=command("git","-C",str(self.clone),"rev-parse",pinned+":"+one)
        gate=Mock(
            REQUIRED_SOURCES=(one,),
            validate_authorization=Mock(return_value={"review_fingerprint":"f"*64}),
            validate_review=Mock(return_value={
                "reviewed_commit":pinned,
                "reviewed_file_git_blobs":{one:frozen}}))
        with patch.object(stage99,"review_gate",return_value=gate):
            clean=stage99.assert_reviewed_runtime_source()
            self.assertEqual(clean["actual_head"],pinned)
            self.assertEqual(clean["complete_execution_path_verified"],1)
            local=self.clone/one
            local.write_text("MALICIOUS_DIRTY_CHANGE=1\n")
            with self.assertRaisesRegex(RuntimeError,"EXECUTABLE_FILES_DIRTY"):
                stage99.assert_reviewed_runtime_source()
            # Deliberately commit a different executable in the same branch.
            command("git","-C",str(self.clone),"add","--",one)
            command("git","-C",str(self.clone),"-c","user.name=fixture",
                    "-c","user.email=fixture@example.test",
                    "commit","-m","unreviewed tracked source")
            with self.assertRaisesRegex(RuntimeError,"TREE_BLOB_NOT_REVIEWED"):
                stage99.assert_reviewed_runtime_source()
            gate.validate_authorization.assert_called()

    def test_push_race_remote_moves_between_fetch_and_push_then_retries(self):
        actual=stage99._git_in_worktree
        raced=[False]
        def advance_then_git(where,*args,**kwargs):
            if args and args[0]=="push" and not raced[0]:
                raced[0]=True
                self.another_commit("just_before_push.md","race from second clone\n")
            return actual(where,*args,**kwargs)
        with patch.object(stage99,"_git_in_worktree",side_effect=advance_then_git):
            newcommit=stage99.safe_git_commit_and_push(self.window)
        self.assertTrue(raced[0])
        self.assertEqual(len(newcommit),40)
        self.assertEqual(command("git","-C",str(self.clone),"rev-parse","HEAD"),self.local_head)
        check=Path(self.temp.name)/"race_checked"
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(check))
        self.assertEqual((check/self.path).read_bytes(),self.original.read_bytes())
        self.assertEqual((check/"just_before_push.md").read_text(),"race from second clone\n")

    def test_remote_archive_conflict_never_overwrites_known_file(self):
        remote=self.second/self.path
        remote.parent.mkdir(parents=True,exist_ok=True)
        remote.write_text('{"window_start_utc":"2026-10-14T06:00:00Z","other":"conflict"}')
        command("git","-C",str(self.second),"add","--",self.path)
        command("git","-C",str(self.second),"-c","user.name=independent",
                "-c","user.email=independent@example.test",
                "commit","-m","existing different archive")
        command("git","-C",str(self.second),"push","origin",
                "HEAD:refs/heads/"+stage99.BRANCH)
        with self.assertRaisesRegex(RuntimeError,"REMOTE_ARCHIVE_DIFFERS"):
            stage99.safe_git_commit_and_push(self.window)
        self.assertEqual(command("git","-C",str(self.clone),"rev-parse","HEAD"),
                         self.local_head)
        self.assertEqual(self.original.exists(),True)


if __name__=="__main__":
    unittest.main(verbosity=2)
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py`

### 7. crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py` blob=`06f1cb7964888f896b0e2bfa266763ca691c428c`

```python
#!/usr/bin/env python3
"""No-network NEW-PROCESS proof: capture loader does not execute historical models.

The malicious fixture makes an explicit filesystem marker at import time.
The 3 production capture/gate modules must not import Stage91/38/80,
Shadow or historical_replay, even when those imports have malicious effects.
"""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

SRC=Path(__file__).resolve().parent
PRODUCTION=(
    "monster_v4_stage105_capture_universe_core.py",
    "monster_v4_stage97_one_shot_usdm_capture.py",
    "monster_v4_stage99_mac_launchd_one_shot.py",
    "monster_v4_stage102_claude_chat_review_gate.py",
)
NOT_CAPTURE_DEPENDENCIES=(
    "monster_v4_stage91_forward_oos_replay_gate",
    "monster_v4_stage38_usdm_original_v4_1m_pilot",
    "monster_v4_stage80_dual_entry_core",
    "monster_v4_shadow",
    "monster_v4_historical_replay",
)


class FreshInterpreterImports(unittest.TestCase):
    def test_malicious_historical_module_never_imports(self):
        with tempfile.TemporaryDirectory(prefix="monster-stage105-import-") as td:
            root=Path(td)
            for file in PRODUCTION:
                shutil.copyfile(SRC/file,root/file)
            marker=root/"UNREVIEWED_HISTORICAL_IMPORT_EXECUTED"
            # A module could run arbitrary top-level side effects when imported.
            for name in NOT_CAPTURE_DEPENDENCIES:
                (root/(name+".py")).write_text(
                    "from pathlib import Path\n"
                    f"Path({str(marker)!r}).write_text({name!r})\n"
                    "raise RuntimeError('UNREVIEWED_DEPENDENCY_WAS_EXECUTED')\n")
            code=(
                "import sys,json\n"
                "import monster_v4_stage99_mac_launchd_one_shot as x\n"
                "import monster_v4_stage102_claude_chat_review_gate as gate\n"
                "import monster_v4_stage97_one_shot_usdm_capture as p\n"
                f"disallowed={list(NOT_CAPTURE_DEPENDENCIES)!r}\n"
                "assert not any(n in sys.modules for n in disallowed)\n"
                "assert len(x.stage91.WINDOWS)==3\n"
                "assert len(gate.REQUIRED_SOURCES)>=8\n"
                "assert p.freeze is x.stage91\n"
                "print('STAGE105_FRESH_PROCESS_NO_HISTORICAL_IMPORT_PASS')\n"
            )
            done=subprocess.run([sys.executable,"-c",code],cwd=root,
                capture_output=True,text=True,timeout=18,check=False)
            self.assertEqual(done.returncode,0,done.stderr)
            self.assertIn("NO_HISTORICAL_IMPORT_PASS",done.stdout)
            self.assertFalse(marker.exists())


if __name__=="__main__":
    unittest.main(verbosity=2)
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py`

### 8. .github/workflows/monster-stage99-mac-one-shot-capture-safety.yml

BEGIN_SOURCE_FILE `.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml` blob=`74dc578ecb143dea6735eda06e7490f73daca2e1`

```yaml
name: Monster Stage99 macOS OneShot Capture Safety

on:
  push:
    branches:
      - research/monster-v4-local-discovery-20261010
    paths:
      - .github/workflows/monster-stage99-mac-one-shot-capture-safety.yml
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage38_usdm_original_v4_1m_pilot.py
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage80_dual_entry_core.py
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py
      - crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py
      - crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py
      - crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py
      - crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py
      - crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md
      - crypto-300-profit-mission/monster/MONSTER_STAGE103_EXTERNAL_CLAUDE_CHAT_REVIEW_PROMPT_20261013.md
  workflow_dispatch:

permissions:
  contents: read

jobs:
  no_network_install_or_real_capture:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    timeout-minutes: 14
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Compile capture, mac scheduler and source-bound script
        run: |
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage38_usdm_original_v4_1m_pilot.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage80_dual_entry_core.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py
          python -m py_compile crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py
      - name: Verify standalone Stage97 source integrity and Stage99 safe dry-run (NO NETWORK)
        run: |
          python crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py --selftest
          python crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py --selftest
          python crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py selftest
          python crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py selftest
          python crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py selftest
      - name: Simulate one-shot capture, correct Git branch, no-recapture retry and failure states
        run: |
          python crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py
          python crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py
          python crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py
```

END_SOURCE_FILE `.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml`

### 9. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py` blob=`6f9db6dab45017cb741f1e7be67a10abcb8a76f0`

```python
#!/usr/bin/env python3
"""Monster Stage91: read-only future cohort intake and same-core D0/D1 causal replay.

No scheduler, monitoring, Gmail, trading, background process or production mutation.
A hash of user-supplied raw JSON proves byte consistency, NOT exchange authenticity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as v4
    import monster_v4_stage80_dual_entry_core as d1
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as v4
    from scripts import monster_v4_stage80_dual_entry_core as d1

# Stage105 is the only authority for frozen time and Binance USD-M population.
# Stage91 historical-replay dependencies remain here but are never imported by
# the Stage97/99 capture process.
try:
    import monster_v4_stage105_capture_universe_core as capture_core
except ImportError:
    from scripts import monster_v4_stage105_capture_universe_core as capture_core

SCHEMA=capture_core.SCHEMA
WINDOWS=capture_core.WINDOWS
EXCHANGE_INFO_URL=capture_core.EXCHANGE_INFO_URL
WINDOW_MS=capture_core.WINDOW_MS
MIN=capture_core.MIN
FRESH_MAX_MS=capture_core.FRESH_MAX_MS
MODEL_SOURCE_V4 = v4.ORIGINAL_V4_GIT_BLOB
D1_SOURCE_CONTRACT = d1.CONTRACT_SHA
num=capture_core.num
sha256_raw=capture_core.sha256_raw
verify_window=capture_core.verify_window
freeze_universe=capture_core.freeze_universe


def source_ready(symbol: str, start_utc: str, bars: list, receipts: list) -> bool:
    anchor=verify_window(start_utc)
    if len(bars)!=v4.BARS or len(receipts)!=9:
        raise ValueError("STAGE91_NINE_DAYS_OFFICIAL_SOURCE_REQUIRED")
    base=anchor - 24*3600_000
    if any(row[0]!=base+i*MIN or len(row)!=7 for i,row in enumerate(bars)):
        raise ValueError("STAGE91_NONCAUSAL_OR_INCOMPLETE_SOURCE_MINUTES")
    expected=[(date.fromisoformat(start_utc[:10]).toordinal()+n) for n in range(-1,8)]
    got=[date.fromisoformat(p["date"]).toordinal() for p in receipts]
    if got!=expected:
        raise ValueError("STAGE91_WRONG_NINE_OFFICIAL_CALENDAR_DATES")
    if any(not p.get("verified_official_publisher_SHA256")
           or not isinstance(p.get("zip_sha256"),str)
           or len(p["zip_sha256"])!=64 or
           not all(ch in "0123456789abcdef" for ch in p["zip_sha256"])
           or p.get("bars")!=1440 for p in receipts):
        raise ValueError("STAGE91_PUBLISHER_SHA_RECEIPTS_NOT_VERIFIED")
    if not symbol or not symbol.endswith("USDT"):
        raise ValueError("STAGE91_USDM_SYMBOL_REQUIRED")
    return True


def early5(event: int | None, high: int | None) -> bool:
    return event is not None and high is not None and event + 5*MIN <= high


def first_cross(bars: list, multiplier: int) -> int | None:
    if multiplier not in (2,5,10):
        raise ValueError("STAGE91_BAD_LABEL_MULTIPLE")
    # This future label is only calculated after a complete 168h archive exists.
    anchor=bars[v4.WARMUP][1]
    return next((x[0] for x in bars[v4.WARMUP:v4.WARMUP+v4.ACTIVE]
                 if x[2]>=anchor*multiplier),None)


def replay_raw_symbol(symbol: str, start_utc: str, bars: list, receipts: list,
                      *, runner=v4.production_scan,
                      d1_core=d1.evaluate) -> dict:
    """Original V4 first WATCH + frozen Stage79 D1 exactly every 3m, all normal cases."""
    source_ready(symbol,start_utc,bars,receipts)
    if v4.blob(v4.production.__file__) != v4.ORIGINAL_V4_GIT_BLOB:
        raise ValueError("STAGE91_ORIGINAL_D0_PRODUCTION_BLOB_NOT_LOCKED")
    d1.load_contract()
    anchor=verify_window(start_utc)
    scan=runner(symbol,start_utc,bars)
    if scan["polls"]!=3360:
        raise ValueError("STAGE91_NOT_ORIGINAL_3M_SCANNING_SCHEDULE")
    watch_times=[d1.utc_ms(x) for x in scan["WATCH_UTC"]]
    if (len(watch_times)!=scan["watch_count"]
        or watch_times != sorted(set(watch_times))
        or any(w<anchor or w>=anchor+WINDOW_MS or w%(3*MIN)!=0
               for w in watch_times)):
        raise ValueError("STAGE91_INVALID_ORIGINAL_D0_WATCH_CLOCK")
    first_d0=watch_times[0] if watch_times else None
    first_d1=None
    first_d1_path=None
    if first_d0 is not None:
        contract=d1.load_contract()
        expiry=min(first_d0+contract["from_first_d0_expiration_hours"]*3600_000,
                   anchor+WINDOW_MS)
        state=None
        t=first_d0
        while t<expiry:
            i=(t-bars[0][0])//MIN
            f=d1.from_archived_closed_bars(bars[i-61:i],t)
            state, outcome=d1_core(
                state, venue="USDM",symbol=symbol,at_utc=v4.stamp(t),
                features=f,is_first_d0=(t==first_d0),contract=contract)
            if outcome in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
                first_d1=t
                first_d1_path=outcome
                break
            t+=3*MIN
        if state is None or d1.utc_ms(state.first_utc)!=first_d0:
            raise ValueError("STAGE91_D0_LOST_IN_D1")
    cross={n:first_cross(bars,n) for n in (2,5,10)}
    score={}
    for n in (2,5,10):
        tc=cross[n]
        score[f"first_GT{n}x_HIGH_UTC_EVALUATION_ONLY"]=v4.stamp(tc) if tc is not None else None
        score[f"D0_first_pre_GT{n}x_strict"]=first_d0 is not None and tc is not None and first_d0<tc
        score[f"D0_first_pre_GT{n}x_5m"]=early5(first_d0,tc)
        score[f"D1_first_pre_GT{n}x_5m"]=early5(first_d1,tc)
    return {
        "date":start_utc[:10], "symbol":symbol, "venue":"BINANCE_USDM",
        "source_status":"COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY",
        "observed_windows":3360, "D0_WATCH_COUNT":len(watch_times),
        "D0_first_UTC":v4.stamp(first_d0) if first_d0 is not None else None,
        "D1_first_UTC":v4.stamp(first_d1) if first_d1 is not None else None,
        "D1_entry_path":first_d1_path,
        "source_9_days_SHA256":receipts,
        "Crypto_identity":"UNKNOWN_NEEDS_INDEPENDENT_ASOF_PROOF",
        "D2_execution":"UNKNOWN",
        "gross_future_labels_not_real_profit":score,
        "true_independent_OOS":"PENDING_POPULATION_AND_COMPLETE_DATES",
    }


def gate_cohort(window_groups: dict[str,list[dict]], frozen_universes: dict):
    """Summary never passes when venue, population, crypto identity or OOS are unknown."""
    if set(window_groups)!=set(WINDOWS):
        return {"OOS":"BLOCKED_MISSING_FIXED_WINDOW",
                "missing":[d for d in WINDOWS if d not in window_groups]}
    rows=[]
    for win in WINDOWS:
        universe=frozen_universes.get(win)
        if not universe or universe.get("source_authenticity")!="ATTESTED_OFFICIAL_CAPTURE":
            return {"OOS":"BLOCKED_POINT_IN_TIME_POPULATION_NOT_AUTHENTICATED",
                    "window":win}
        eligible={r["symbol"] for r in universe["rows"] if r["candidate_for_raw_USDM_attempt"]}
        actual=[r["symbol"] for r in window_groups[win]]
        if len(actual)!=len(set(actual)) or set(actual)!=eligible:
            return {"OOS":"BLOCKED_MISSING_OR_EXTRA_SYMBOL_ATTEMPTS","window":win}
        rows+=window_groups[win]
    if any(x["source_status"]!="COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY"
           for x in rows):
        return {"OOS":"BLOCKED_CENSORED_OR_UNVERIFIED_SOURCE"}
    # The raw venue census retains verified out-of-scope securities and
    # non-crypto rows for audit. Score only certified Crypto; unknown is blocked.
    recognized={"VERIFIED_CRYPTO_ASOF","CONFIRMED_NONCRYPTO_OUT_OF_SCOPE"}
    if any(x["Crypto_identity"] not in recognized for x in rows):
        return {"OOS":"BLOCKED_CRYPTO_IDENTITY_NOT_VERIFIED"}
    if any(x["D2_execution"]!="VERIFIED_2_SIDED_REAL_FILLS" for x in rows):
        return {"OOS":"BLOCKED_EXECUTION_EVIDENCE_INCOMPLETE"}
    # This is still not a full scoring engine; refuse to invent forward-pass stats
    # without separately pinned review of D0/G1/G2/G3.
    return {"OOS":"BLOCKED_G1_G2_G3_FULL_METRIC_SCORING_NOT_IMPLEMENTED"}


def selftest():
    assert len(WINDOWS)==3 and len(set(WINDOWS))==3
    t=verify_window(WINDOWS[0])
    raw=json.dumps({"serverTime":t-2000,"symbols":[
      {"symbol":"CATUSDT","status":"TRADING","contractType":"PERPETUAL",
       "quoteAsset":"USDT","baseAsset":"CAT","onboardDate":t-3600_000},
      {"symbol":"LRCXUSDT","status":"TRADING","contractType":"PERPETUAL",
       "quoteAsset":"USDT","baseAsset":"LRCX","onboardDate":t-3600_000},
      {"symbol":"OLDUSDT","status":"BREAK","contractType":"PERPETUAL",
       "quoteAsset":"USDT","baseAsset":"OLD","onboardDate":t-3600_000},
    ]},separators=(",",":"))
    template={"schema":SCHEMA,"window_start_utc":WINDOWS[0],
              "venue":"BINANCE_USDM","source_url":EXCHANGE_INFO_URL,
              "capture_ms":t-1000,"raw_exchangeInfo_json":raw,"raw_sha256":sha256_raw(raw)}
    result=freeze_universe(template)
    assert result["population_all_exchange_symbols"]==3
    assert result["usd_m_usdt_perpetual_asof_candidates"]==2
    assert result["rows"][1]["crypto_identity"].startswith("UNKNOWN")
    # Real Binance exchangeInfo.serverTime may be stale by design.
    stale_server=json.dumps({"serverTime":t-86_400_000,
         "symbols":json.loads(raw)["symbols"]},separators=(",",":"))
    dated=dict(template,raw_exchangeInfo_json=stale_server,
               raw_sha256=sha256_raw(stale_server))
    assert freeze_universe(dated)["source_authenticity"]=="UNVERIFIED_EXTERNAL_CAPTURE"
    assert result["OOS"]=="NOT_DONE"
    changed=dict(template,window_start_utc="2025-01-30T06:00:00Z")
    try:freeze_universe(changed)
    except ValueError as e: assert "NOT_ONE_OF" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_EXPOSED_2025_DATE")
    future=dict(template,capture_ms=t+1000)
    try:freeze_universe(future)
    except ValueError as e: assert "NOT_CAPTURED_BEFORE" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_FUTURE_EXCHANGEINFO")
    tamper=dict(template,raw_response="wrong",raw_exchangeInfo_json=raw+" ")
    try:freeze_universe(tamper)
    except ValueError as e: assert "TAMPER" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_RAW_JSON_TAMPERING")
    dup=json.dumps({"symbols":[json.loads(raw)["symbols"][0],
                                json.loads(raw)["symbols"][0]]})
    try:freeze_universe(dict(template,raw_exchangeInfo_json=dup,raw_sha256=sha256_raw(dup)))
    except ValueError as e: assert "DUPLICATE" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_DUPLICATE_SYMBOL")
    # A dated delivery contract is retained in the census, never a perp candidate.
    dated_delivery=dict(json.loads(raw)["symbols"][0])
    dated_delivery.update(symbol="BTCUSDT_261225",
                          baseAsset="BTC",contractType="CURRENT_QUARTER")
    mix=json.dumps({"symbols":json.loads(raw)["symbols"]+[dated_delivery]})
    asof=freeze_universe(dict(template,raw_exchangeInfo_json=mix,raw_sha256=sha256_raw(mix)))
    assert asof["population_all_exchange_symbols"]==4
    assert asof["usd_m_usdt_perpetual_asof_candidates"]==2
    assert asof["rows"][-1]["candidate_for_raw_USDM_attempt"] is False
    incomplete=dict(json.loads(raw)["symbols"][0])
    del incomplete["status"]
    wrong=json.dumps({"symbols":[incomplete]})
    try:freeze_universe(dict(template,raw_exchangeInfo_json=wrong,raw_sha256=sha256_raw(wrong)))
    except ValueError as e:assert "INCOMPLETE_OFFICIAL" in str(e)
    else:raise AssertionError("STAGE103_INCOMPLETE_MARKET_ROW_MUST_FAIL")
    assert gate_cohort({}, {})["OOS"]=="BLOCKED_MISSING_FIXED_WINDOW"
    assert gate_cohort({x:[] for x in WINDOWS},{})["OOS"]=="BLOCKED_POINT_IN_TIME_POPULATION_NOT_AUTHENTICATED"
    assert early5(t,t+5*MIN) and not early5(t,t+4*MIN)
    assert not early5(None,t+8*MIN)
    assert MODEL_SOURCE_V4 and D1_SOURCE_CONTRACT
    assert v4.blob(v4.production.__file__)==v4.ORIGINAL_V4_GIT_BLOB
    from decimal import Decimal
    zero=Decimal("100")
    anchor=verify_window(WINDOWS[0])
    begin=anchor-24*3600_000
    ticks=[]
    for i in range(v4.BARS):
        q=Decimal("100000") if v4.WARMUP-12<=i<=v4.WARMUP+2 else Decimal("60000")
        close=Decimal("110") if v4.WARMUP-12<=i<=v4.WARMUP+2 else zero
        high=Decimal("210") if i==v4.WARMUP+300 else max(zero,close)
        ticks.append((begin+i*MIN,zero,high,zero,close,q,1000))
    receipts=[
        {"date":date.fromordinal(date.fromisoformat(WINDOWS[0][:10]).toordinal()+n).isoformat(),
         "zip_sha256":"a"*64,"verified_official_publisher_SHA256":True,"bars":1440}
        for n in range(-1,8)
    ]
    first=v4.stamp(anchor+3*MIN)
    def fake_original_scanner(_symbol,_date,_bars):
        return {"polls":3360,"WATCH_UTC":[first],"watch_count":1}
    score1=replay_raw_symbol("CATUSDT",WINDOWS[0],ticks,receipts,
                             runner=fake_original_scanner)
    assert score1["D0_first_UTC"]==first
    assert score1["D1_first_UTC"]==first
    assert score1["D1_entry_path"]=="DIRECT_AT_FIRST_D0"
    assert score1["gross_future_labels_not_real_profit"]["D0_first_pre_GT2x_5m"]
    future=list(ticks)
    future[v4.WARMUP+300]=(future[v4.WARMUP+300][0],
                             zero,zero,zero,zero,Decimal("60000"),1000)
    future[v4.WARMUP+400]=(future[v4.WARMUP+400][0],
                             zero,Decimal("210"),zero,zero,Decimal("60000"),1000)
    score2=replay_raw_symbol("CATUSDT",WINDOWS[0],future,receipts,
                             runner=fake_original_scanner)
    assert score2["D1_first_UTC"]==score1["D1_first_UTC"]
    assert (score2["gross_future_labels_not_real_profit"]["first_GT2x_HIGH_UTC_EVALUATION_ONLY"]
            !=score1["gross_future_labels_not_real_profit"]["first_GT2x_HIGH_UTC_EVALUATION_ONLY"])
    print("STAGE91_FROZEN_POPULATION_AND_SYNTHETIC_SAME_CORE_CAUSAL_REPLAY_SELFTEST_PASS")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--validate-market-packet",type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if args.selftest:
        selftest()
        return
    if args.validate_market_packet:
        packet=json.loads(args.validate_market_packet.read_text(encoding="utf-8"))
        data=freeze_universe(packet)
        content=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(content,encoding="utf-8")
        print("STAGE91_MARKET_PACKET_INTEGRITY_ONLY "+json.dumps(
            {k:data[k] for k in ("window_start_utc","population_all_exchange_symbols",
                 "usd_m_usdt_perpetual_asof_candidates","source_authenticity","OOS")},
             ensure_ascii=False,sort_keys=True))
        return
    parser.error("no action: supply --selftest or --validate-market-packet")


if __name__=="__main__":
    main()
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py`

### 10. crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md

BEGIN_SOURCE_FILE `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md` blob=`55668e29cac33ababd3e9e844f08545bca89cbde`

```markdown
# Monster 模块开发与交付规则（长期有效）

状态：ACTIVE | 生效日期：2026-10-11 | 模块：`crypto-300-profit-mission/monster/` 及本模块在 `local-agent/` 下的代码、测试、部署和通知组件。

本文件记录用户明确提出的四项开发要求，作为所有后续 Monster 研发、交接、其他 AI Review、测试及本地上线工作的常设模块规则。若与全局 `../MISSION_SPEC.md` 的资金、交易授权、隐私及生产变更边界发生冲突，以全局安全和执行授权边界为准；不得将研发授权误解成自动下单或立即启用邮件发送的授权。

## 一、完成完整工程闭环，不停留在单点讨论

每一阶段应覆盖：**真实数据采集与分析 → 策略/产品设计方案 → 技术方案 → 实际代码实现 → 独立其他 AI Review → 回归与集成测试 → 用户 Mac 本地部署与真实验收 → 故障修复与复验**。

- 应主动推进高价值主链路，不能因一个低价值边界问题反复纠结而阻断核心交付；不为凑测试数量、文件数量或研究深度牺牲早期发现和可成交性。
- 各环节以真实证据标记 `DONE`、`PARTIAL`、`BLOCKED`、`NOT_DONE`。代码推送不等于已部署；CI PASS 不等于真实行情可靠；本地 Dry-run 不等于邮件送达；历史胜率不等于前瞻盈利。
- 独立 Review 必须是其他 AI 或真正独立的审查主体实际提交的审查意见，记录 reviewer、版本、发现项及修复结果；仅自查或 CI 不得写成“已通过其他 AI Review”。
- 用户本地运行目标是**Monster 与 Frank 并行**。Monster 必须使用独立代码/进程、SQLite/状态、日志、通知 outbox、LaunchAgent 服务名和端口；不擅自更改、停止、替换或劫持现有 Frank 任务。先校验共存、资源占用、隔离、重启恢复与回滚。

## 一点五、严格先后顺序与不可跳过的放行门槛

以下为**有依赖的强制顺序**，不得将所有阶段并行开展或把单元测试通过当成最后验收：

1. **事实数据分析**：独立核验并保存当时可见的真实原始数据、全市场样本/历史重大妖币、正常案例、交易所上市退市等；缺少的分钟数据主动获取。已暴露数据的研究不得冒充独立外推检验。
2. **策略与指标方案**：基于历史证据提出至少一套明确、可证伪的 WATCH/D1/执行规则，预先设定漏报、通知负载、成本、风险和净收益门槛，并同时明确什么结果会导致弃用。
3. **技术方案**：定义因果回放/真实实施的数据契约、指标计算、双阶段候选处理、异常恢复与Frank隔离架构；禁止先按易写程度决定业务策略。
4. **代码实现与模型历史回测**：使用实现的**同一份核心规则**在历史时间线上重放，而非把旧V2/V3研究表、单元测试、未来已知5x赢家列表、抽样盘口快照冒充V4回测。报告发现率、预警提前量、漏报、实际通知密度、含手续费滑点假设的净回报/回撤和未满足的数据缺口。V4所需的3m行情/24h成交额/5m回看不可从仅1h汇总表无损重建；不得用估算填实测表。
5. **其他 AI 独立 Review**：将完成的回测方案、实际原始输入与复现步骤、模型代码一起交给另一模型审查。记录模型身份、commit、漏洞、复现和修复。**只有review request而无review output不算完成**。
6. **修复与最终测试**：根据真实review修复后重新跑历史重放、样本外验证、CI/集成/通知故障测试；发现策略结果不可接受时回到数据/方案，**不得继续部署**。
7. **Mac 本地部署**：仅上述证据和验收均已过线，才可提供/执行Monster与Frank并行安装；之后做本机真实数据/延时/重启/告警投递验证，问题修复回到相关关口。

**当前 Monster V4 放行状态：`DEPLOYMENT=NO_GO`。** 原来的 Mac 安装建议是过早交付，已撤回。现在不要求用户安装，不要求用户提供本机日志，不可用Shadow先跑来替代缺失的历史验证。当前已有的Mac安装器保留为待审工程代码，启动入口在源码层面 fail-closed；只有未来通过以上关口的新代码审查提交才能改变门槛。生产自动交易另保持 `NO_GO`。

## 二、优先自主取得数据和完成工作

- 助手能够完成的数据检索、官方行情/链上事实核验、数据处理、建模、方案、代码、自动化测试、Git 提交、CI 检查、文档记录均应自主完成，不得无理由转交用户。
- 缺少资料时先搜索官方/原始数据源、已有仓库材料、可用连接器及允许访问的公开接口；不得因为“获取数据麻烦”就默认要求用户下载 Binance 或其他公开数据。
- 仅当真正需要用户 Mac 私有目录、系统权限、设备上持有的凭据或助手无法读取的原始文件时，才要求用户执行本地命令。所需脚本与完整说明**先提交 Git**，再给最少且可直接复制的 zsh 命令；**命令中不要带 `#` 注释**。若需用户上传文件，命令应包含 Finder 选中文件/打开文件夹的步骤，降低人工寻找成本。
- 对无法自主完成的本地部署环节，明示远程无法执行的原因，交付可重复的单命令安装/验收和回滚；用户执行后根据**真实输出**继续修复，不得虚称部署成功。

## 三、增量成果即时同步 Git，保留审计线索

- 每拿到一批有意义且可验证的数据、一次有效实验结论、一块可运行代码、一组新测试或一次重要修复，就在**同一 Monster PR 分支**分批提交 Git，不待全部做完才提交。
- 每批至少记录：数据来源和观测时间、输入范围/样本偏差、可复现方法、计算或测试结果、commit SHA、当前限制、下一步。保留必要的 CSV/报告/脚本/测试，避免不同对话交接后丢失进度。
- 研究报告必须区分`已核实事实`、`历史事后观察`、`推测`、`预测`。禁止编造数字、市场行情、钱包数据、链上结果、测试/执行状态、Git 状态或外部审查结果；未核实写 `UNVERIFIED` 或 `UNKNOWN`。
- 最新状态应重新查询 Git HEAD、实际工作流和必要的实时数据。旧对话、旧截图或旧报告不能覆盖新 Git/链上事实；失败的 CI 必须读取日志、修复并重新验证。
- 不擅自新建平行的 Monster 任务/监控，不改对话标题；已有 PR #30 为当前研发主线，后续以实际 Git 状态为准。

## 四之前补充：交易金额未指定，禁止默认金额（2026-10-12）

Monster 妖币研究当前没有用户授权的单笔交易金额。历史资料出现的 30U、300U 属于当时实验参数，仅对原历史实验有效，不构成当前用户交易金额、持仓或实盘授权。

后续 Monster 可独立研究早期妖币发现、订单簿价差/深度、量价、成交活跃度、跨场所实际交易路径；执行金额保持显式的用户输入参数，未指定时为 UNKNOWN。不能选择某个固定金额替代用户决定，不能以历史固定金额作为筛币/通知硬门槛。历史原有实验和冻结门槛不得因纠错而倒改；新研究单列当前规则。

本对话继续仅针对 Monster 妖币模块，禁止将其他行情价格监控、Frank、NFT、日报或资产操作混入 Monster 研究和 Git 变更。

## 四、利润目标决定研发与通知优先级

最终目标不是“写完报告”或“发出最多提醒”，而是**尽早发现可能产生净可实现收益的机会，同时避免伪信号、漏报和过时追涨**。

- 数据筛选必须覆盖全市场目标范围和新上市/流动性变化；WATCH 尽早生成。不得只看未来赢家、排行榜或少数历史知名妖币；前瞻验证需涵盖普通样本与实际错过机会。
- 评估机会须包含观察时点可得到的特征、时间因果顺序、交易状态、可用资金、盘口价差/深度、滑点、手续费、实际成交额、潜在回撤及过期机制。没有足够执行证据，`WATCH` 不得冒充 `BUY`。
- 以真实前瞻 Shadow 验证发现时效、召回/漏报、异常恢复、队列积压、去重、信号升级、迟到处理、实际成交近似和通知延迟；目标与实际观测值分开披露。不能以事后选出的 5x 赢家计算预测胜率。
- 重要 WATCH 与有效升级须及时通知；通知系统必须有可持久化 outbox、幂等 ID、限流/重试、陈旧消息处理和最终投递回执验证，不能只凭“邮件发送函数被调用”就认定成功。
- 对通知正常使用的验收至少包括：真实本机运行、数据源故障模拟和恢复、重启去重、积压恢复、真实授权通道送达测试及 Sent/readback 核验。用户明确授权启用发送通道前，保持 `DRY_RUN_ONLY`；绝不把“最终要部署”理解成提前发真实邮件或进行交易。
- 发现模型没有通过实际净收益验证时要直说，继续优先修复提高及时发现/真实可交易性的主要缺口，不为完成项目而声明盈利。

## 定时任务与本地监控的显式授权边界（2026-10-13）

- **未经用户逐项明确授权，严禁创建、启用、恢复或修改任何 ChatGPT Automations、GitHub scheduled workflow、launchd 定时任务、cron、后台守护进程、周期通知或自动采集计划。** 用户要求“开发本地监控功能”“把本地脚本提交 Git”“后台运行并上传 Git”仅授权研发设计、编写代码及非生产测试，**不等于授权创建或启用定时任务**。不得擅自把明确要求的本地Mac方案替换成ChatGPT云端Automation。
- 本地自动采集是独立辅助证据支线，不得占用/拖慢历史妖币模型主线；历史研发、回测与改进不以新数据采集或三个前瞻窗口结束为前置。
- 按既定开发规范先完成数据/设计→实现→独立其他AI审查（用户使用**Claude对话**，不得假定本地已安装Claude CLI）→修复→CI/测试→提供Git已有代码的zsh命令。**真正安装/启用必须在此之后再次得到用户明确授权**，并由用户主动执行本地命令；不代用户进行远程启用。
- 2026-10-13曾未经明确授权创建的ChatGPT市场快照Automation已主动设置 `is_enabled=false`，上一次核查 `last_run_time=null`。该事件是越权纠错记录，不准将其恢复运行。Monster策略和Frank生产仍不变；没有本地部署许可。

## 持续交付状态与关口

每次进度报告采用统一顺序：**已核实的 Git/数据基线 → 本轮实际完成内容和 commit → 实际测试/CI/Review 证据 → 尚未达标/风险 → 已推进或唯一必要的用户操作**。

预期上线架构：`Frank (existing)` 与 `Monster (separate)` 在 Mac 上并行；但仅在实际 V4 回测、独立其他 AI Review、修复及最终测试完成之后，才允许本地部署和上线Shadow；后续真实通知仍须单独授权。生产自动交易保持 `NO_GO`，除非用户另行明确授权且符合 `MISSION_SPEC.md`。

具体模型与工程约束参见 [Monster V4 架构](MONSTER_V4_MODEL_AND_LOCAL_ARCHITECTURE.md)；全局执行边界见 [Mission Spec](../MISSION_SPEC.md)。
```

END_SOURCE_FILE `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`

### 11. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py

BEGIN_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py` blob=`429dac1b52de154edb451f9b1a0a96ba17f4c1a9`

```python
#!/usr/bin/env python3
"""Historical compatibility tombstone: local Claude CLI integration withdrawn.

Do not import as review authority. Real independent review is via Claude chat,
and approval is separately checked with Stage102/103 gate.
"""
from __future__ import annotations
import argparse

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("selftest","review-install","verify"))
    args=p.parse_args()
    if args.action=="selftest":
        assert "claude" not in globals()
        assert "review_then_install" not in globals()
        print("STAGE103_WITHDRAWN_CLAUDE_CLI_NO_RUNNABLE_INSTALL_PATH_PASS")
    else:
        p.error("WITHDRAWN: user uses Claude CHAT; no Claude CLI review or auto-install")

if __name__=="__main__":
    main()
```

END_SOURCE_FILE `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py`

### 12. crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md

BEGIN_SOURCE_FILE `crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md` blob=`47d322c2642542db03ae454d9c1e356ef71f2254`

```markdown
# Monster Stage99：Mac launchd 三个冻结窗口的单次采集→Git PR#30→自动退出

状态：TECHNICAL_DESIGN_FROZEN_2026_10_13；Stage103 修订纠错补充。此为**研究原始证据采集工具**，不是 Monster D0/D1/D2 策略部署、Shadow、Mac常驻Daemon、Frank修改或交易/邮件。用户明确要求定时执行、自动传Git、完成后退出，代码由仓库统一交付并须其他AI独立Review。

## 约束与取舍

- 官方GitHub `schedule` 只读取仓库**默认分支**且可能延迟或丢弃任务；Monster原研究分支 PR #30 为 Draft，不能为采集把代码提前合并到main，也不能凭GitHub Actions排队及时性保证时点。因此选用用户Mac现有launchd **三个独立一次性 LaunchAgent**，不借用/重启Frank任何label。可选研究证据采集不视为已放行的Monster策略服务。
- 三个冻结窗口 `2026-10-14, 2026-10-28, 2026-11-11 06:00 UTC`。Mac各自按用户机器**本地时区**换算 `05:48 UTC` 调度（曼谷`12:48`）；真实HTTPS完成必须在对应 `05:45:00 <= t <= 06:00:00 UTC`；不满足时间/网络不伪造，不事后补抓。
- 使用独立目录 `~/.local/share/monster-stage99-source-capture/repo` 克隆**同一个** `lxxlx2/ChatGPT_mission_record` 及PR30分支；禁止操作用户常用本地repo/Frank/MonsterSQLite/邮箱。入口代码只能 `git` 提交采集结果到原`research/monster-v4-local-discovery-20261010`，不得push main、新建PR或覆盖已有raw历史证据。
- 定时器仅在指定日期启动一次`python3 ... runner run --window ...`，launchd plist `KeepAlive=false`、`RunAtLoad=false`、无WatchPaths/StartInterval；每个任务完成后清除自己的plist并卸载，不继续运行。三个窗口都用同一安装命令完成；不是独立交易/价格通知监控。Mac需保持开机、联网、唤醒；OS休眠或网络中断会使该次窗口`MISSED`，不能声称已采集。
- 每次在窗口内复用**Stage97原`capture_one`**：`/fapi/v1/time`→`/fapi/v1/exchangeInfo`→`/fapi/v1/time`，原始UTF8、SHA256、客户端时间、原始时点完整名单验证。成功后自动写 `crypto-300-profit-mission/monster/evidence/monster_stage97_point_in_time_usdm_YYYY-MM-DD_raw_https.json`，`git add/commit/push`至原PR30分支。远端已有同名不同内容必须拒绝覆盖。失败保存本机日志和状态供用户复核，不向Git写伪造成功或缺失填零。
- 唯一需要用户的操作是**review通过后执行一条zsh命令安装一次性调度**，GitHub远端push使用用户本机现有GitHub Git凭证；绝不要求用户贴token，也不在日志泄漏账号凭据。安装时检查macOS、git/Python3/launchctl、三次日期未来/权限、origin分支存在、独立目录安全，Mac本机时钟有合理UTC窗口约束；已过期的日期直接拒装并可明确改为只装未来日期，但不能将其标成成功。
- **纠正原错误方案（Stage103）**：用户一直只在Claude**普通对话**中进行独立AI Review，不使用任何本地Claude Code CLI。原`monster_v4_stage99_external_ai_review.py`中的可调用CLI/安装功能已经用无可用安装路径的tombstone替换，任何`review-install`均拒绝。用户把实际Claude审查全文发回，研发负责人如实留档并根据`BLOCK`修复，再运行macOS/Ubuntu真实CI；未经第二轮真实`APPROVE`且用户再单独明确授权，**禁止任何本地调度任务安装**。
- Stage102/103双重安装闸门：Claude审查回执绑定完整审查原文哈希、`reviewer_model`、`reviewed_commit`及全部8个执行/测试/工作流文件的Git blob（Stage38/80/91/97/99/102、集成单测、CI）；代码有变更旧审查自动失效。独立的`monster_stage103_explicit_user_local_install_authorization.json`必须在获得用户**明确独立授权**后才建立，记录精确原话、时间、窗口和对应review指纹；安装进程另外必须连接真实交互终端，并由用户现场完整输入绑定上述review/源码的确认短语。**Claude review本身不是授权，用户提交审查报告也不是授权；SHA和回执仅为完整性检查，无法密码学证明文字真正来自人或Claude**。
- 独立用户明确批准后才考虑执行Git内的本地安装入口；Mac必须有现有Git权限、Python3与launchctl、采集时开机并联网，**不需要**Claude CLI或向聊天泄漏任何token。安装先验证所有目标plist不存在，再按窗口独立bootstrap；若任一步失败，逆序只回滚自己本轮创建的服务；安装前后只读对照Frank已有launchd标签，不控制或重启Frank。
- 研究原始数据先通过本地独立目录保存，经独立的`/time`两次校时和`exchangeInfo`原始SHA核验，再上传至原PR30分支。**数据采集之前不访问GitHub远端网络**；Git暂时不可用也保留准确原始字节，稍后只重传原字节。Git上传在临时worktree中以远端最新HEAD新建证据commit，遇到远端新提交有限重试，不对采集程序的已审本地仓库执行`rebase`、`reset`或`force push`。
- `StartCalendarInterval`没有年份：这三个自卸载任务如果因Mac整日关机而错过，理论上可能在以后相同月日被launchd再次启动；运行时必须按精确冻结UTC窗口fail-close且禁止补抓，执行后删除自身plist。这个缺口不能声称三次准时成功。
- 异常优先级：真实性>采集成功率。记录`SCHEDULE_INSTALLED / CAPTURE_VALIDATED / GIT_PUSH_CONFIRMED / MISSED_WINDOW / AUTH_FAILED / SOURCE_FAILED / REVIEW_PENDING`，且`CAPTURE_VALIDATED`不得当成Git成功。GitHub原分支变化安全重试，不以reset覆盖他人提交。若窗口内已抓取有效原始证据但Git push失败，保留本机完整sha证据，允许事后**仅重试上传当时已保存的字节**，不得事后重新抓取。
- `launchd`定时仅保存起始快照，不证明窗口内新上架或停牌覆盖。Crypto身份、D0/D1效果、真实盘口与回报仍未验证。采集完整不等于`G0/G1/G4 PASS`。

### 研发阶段验收

`OTHER_AI_REVIEW=NOT_DONE`直至其他模型真实审查；`STAGE99_INSTALL=BLOCKED_UNTIL_REVIEW_AND_TESTS`；`D1_G3=REJECTED`；`MONSTER_DEPLOY=NO_GO`；`GMAIL=OFF`；`AUTOTRADE=NO_GO`；`FRANK_UNCHANGED`。
```

END_SOURCE_FILE `crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md`
