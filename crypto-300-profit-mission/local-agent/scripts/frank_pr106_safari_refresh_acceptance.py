#!/usr/bin/env python3
"""Zero-touch Mac Safari proof for approved PR106 historical decisions GET failure isolation.

A fixed Git-object snapshot of PR106 product UI is served through the existing
GET-only Frank QA proxy. Only the disposable QA proxy returns synthetic
/api/decisions 503, never the running Dashboard. The next stage restores real GET.
No RPC, POST, SQLite writes, trades, mail, deploy, or production source changes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import uuid4
import zipfile

import frank_pr101_safari_evidence as base
import frank_c02_auto_safari_capture as capture
from frank_decisions_readonly_diagnostic import read_git_head_passively

PRODUCT_SHA = "8a8b4fcc36242c0ba03b03170225f723d847fa53"
STAGES = ("fault", "recovery")
EXPECTED = {"fault":"HISTORY_UNAVAILABLE_OTHERS_LIVE",
            "recovery":"HISTORY_AVAILABLE_OTHERS_LIVE"}
CORE = frozenset(("/api/runtime", "/api/control-health", "/api/candidates",
                  "/api/trades", "/api/review-activity", "/api/coverage"))
API = CORE | frozenset(("/api/decisions", "/api/frank-observed-watchlist"))
WAIT_SECONDS = 23.0


def committed_blob(checkout: Path, sha: str, path: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or path not in {
            base.STATIC_REL + "/" + name for name in base.STATIC_FILES}:
        raise RuntimeError("UNAPPROVED_STATIC_OBJECT")
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_PAGER="cat")
    p = subprocess.run(["git", "-C", str(checkout), "--no-pager",
                        "cat-file", "blob", f"{sha}:{path}"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env, timeout=20, check=True)
    if not p.stdout:
        raise RuntimeError("EMPTY_PINNED_STATIC_OBJECT")
    return p.stdout


def export_approved_static(checkout: Path, qa_sha: str, out: Path) -> dict[str,str]:
    """Require PR106 and QA HEAD static blobs bytewise equal; serve PR106 objects."""
    if read_git_head_passively(checkout) != qa_sha:
        raise RuntimeError("QA_HEAD_MISMATCH")
    out.mkdir(mode=0o700)
    hashes = {}
    for name in sorted(base.STATIC_FILES):
        path = base.STATIC_REL + "/" + name
        original = committed_blob(checkout, PRODUCT_SHA, path)
        if committed_blob(checkout, qa_sha, path) != original:
            raise RuntimeError("QA_MODIFIED_APPROVED_PRODUCT_STATIC_" + name)
        dest = out / name
        dest.write_bytes(original)
        dest.chmod(0o400)
        hashes[name] = base.sha256_bytes(original)
    base.verify_preview_snapshot(out, hashes)
    return hashes


def qa_page(stage: str, token: str) -> bytes:
    if stage not in STAGES or not re.fullmatch(r"[0-9a-f]{32}", token):
        raise ValueError("QA_STAGE_OR_TOKEN_INVALID")
    page = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Frank PR106 Safari 故障隔离验收</title>
<style>
html,body{margin:0;height:100%;background:#10141c;color:#e9edf4;font:14px system-ui}
header{height:72px;box-sizing:border-box;background:#151d2b;border-bottom:1px solid #394155;padding:10px 18px}
header b{display:block;font-size:16px}header span{display:block;font-size:12px;color:#afbed5;margin-top:5px}
iframe{display:block;width:100%;height:calc(100% - 72px);border:0}
</style></head><body>
<header><b>Mission Frank PR106 · Mac Safari 只读验收（非生产部署）</b>
<span id="qa-status">MODE=__MODE__ · 仅隔离预览注入历史判断 503；真实 Dashboard 不受影响</span>
</header><iframe id="product" title="固定 PR106 Frank 信号真实页面" src="/index.html#signals"></iframe>
<script>
(function() {
const stage=__STAGE__,token=__TOKEN__,expected=__EXPECTED__;
const frame=document.getElementById('product');
let finished=false, invalidated=false, checking=false, lastNonce='';
function domValid() {
  const d=frame.contentDocument;
  const runtime=d?.getElementById('runtime');
  const history=d?.getElementById('decisions');
  const stamp=d?.getElementById('updated');
  const stats=d?.getElementById('stats');
  const historyText=history?.textContent||'';
  const unavailable=historyText.includes('历史判断记录暂时无法读取')&&
     historyText.includes('本区域数据未核实')&&historyText.includes('/api/decisions');
  const recovered=historyText.trim().length>0&&!unavailable&&
     !historyText.includes('正在读取');
  return !!((stamp?.textContent||'').includes('更新于 ')&&
    runtime&&!runtime.classList.contains('offline')&&
    !(runtime.textContent||'').includes('控制台读取失败')&&
    stats?.textContent.trim()&&(stage==='fault'?unavailable:recovered));
}
async function attestCurrentPage() {
  if(!finished||checking||invalidated)return;
  checking=true;
  try {
    if(!domValid()){invalidated=true;return;}
    const query=new URLSearchParams({token,stage});
    const response=await fetch('/__qa/challenge?'+query,{cache:'no-store'});
    if(!response.ok){invalidated=true;return;}
    const {nonce}=await response.json();
    if(!domValid()){invalidated=true;return;}
    if(nonce&&nonce!==lastNonce) {
      lastNonce=nonce;
      const attestation=new URLSearchParams({token,stage,nonce,state:expected});
      const ack=await fetch('/__qa/attest?'+attestation,{cache:'no-store'});
      if(!ack.ok||!domValid()){invalidated=true;return;}
    }
  }catch(error){invalidated=true;}
  finally{checking=false;}
}
setInterval(()=>{
  if(!finished)return;
  if(!domValid()){invalidated=true;return;}
  void attestCurrentPage();
},120);
function ready(value) {
  if(finished)return;
  finished=true;
  document.title='FRANK_106_'+value;
  document.getElementById('qa-status').textContent='MODE='+stage.toUpperCase()+' · '+value+
     ' · 此环境不执行链上扫描或交易';
  const q=new URLSearchParams({token,stage,state:value});
  fetch('/__qa/ready?'+q,{method:'GET',cache:'no-store'}).catch(()=>{});
}
frame.onload=()=>{
  const started=Date.now();
  const timer=setInterval(()=>{
    try {
      const historyPanel=frame.contentDocument?.getElementById('decision-history');
      if(domValid()) {
         clearInterval(timer);
         if(historyPanel)historyPanel.open=true;
         historyPanel?.scrollIntoView({block:'center'});
         setTimeout(()=>ready(expected),700);
      } else if(Date.now()-started>15500) {
         clearInterval(timer);
         ready('PRODUCT_UI_NOT_VERIFIED');
      }
    } catch(e) {
       clearInterval(timer);ready('PRODUCT_UI_EXCEPTION');
    }
  },170);
};
setTimeout(()=>ready('PRODUCT_TIMEOUT'),20000);
})();
</script></body></html>"""
    return (page.replace("__MODE__", "SYNTHETIC_FAULT" if stage=="fault" else "REAL_READ_ONLY_GET")
            .replace("__STAGE__", json.dumps(stage))
            .replace("__TOKEN__", json.dumps(token))
            .replace("__EXPECTED__", json.dumps(EXPECTED[stage]))).encode("utf-8")


def make_handler(static: Path, port: int, stage: str, token: str,
                 receipts: dict, observations: dict):
    parent = base.make_handler(static, port)
    class StageHandler(parent):
        def send_response(self, code, message=None):
            endpoint=urlsplit(self.path).path
            if endpoint in API:
                observations[endpoint].append(code)
            return super().send_response(code, message)

        def do_GET(self):
            if self.headers.get("Host") not in {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }:
                return self.send_error(421,"LOOPBACK_HOST_REQUIRED")
            parsed=urlsplit(self.path)
            if parsed.path in ("/__qa/panel","/__qa/ready"):
                args=parse_qs(parsed.query,strict_parsing=True)
                keys={"token","stage"} if parsed.path=="/__qa/panel" else {"token","stage","state"}
                if set(args)!=keys or args.get("token")!=[token] or args.get("stage")!=[stage]:
                    return self.send_error(403,"QA_ACCESS_DENIED")
                if parsed.path=="/__qa/panel":
                    data=qa_page(stage,token)
                    self.send_response(200)
                    self.send_header("Content-Type","text/html; charset=utf-8")
                    self.send_header("Content-Length",str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if args.get("state") not in [
                    [EXPECTED[stage]], ["PRODUCT_UI_NOT_VERIFIED"],
                    ["PRODUCT_UI_EXCEPTION"], ["PRODUCT_TIMEOUT"],
                ]:
                    return self.send_error(403,"QA_INVALID_RECEIPT")
                receipts[stage]=args["state"][0]
                self.send_response(204)
                self.send_header("Content-Length","0")
                self.end_headers()
                return
            if parsed.path=="/api/decisions" and stage=="fault":
                if parsed.query:
                    return self.send_error(400,"NO_QUERY_ALLOWED")
                data=b'{"error":"SYNTHETIC_QA_ONLY_DECISIONS_UNAVAILABLE"}'
                self.send_response(503)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.send_header("Content-Length",str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            return super().do_GET()
    return StageHandler


def verify_stage(stage: str, receipts: dict, observations: dict) -> None:
    if receipts.get(stage)!=EXPECTED[stage]:
        raise RuntimeError("FRANK_SAFARI_UI_STAGE_NOT_VERIFIED_"+stage)
    for endpoint in CORE:
        if 200 not in observations.get(endpoint, []):
            raise RuntimeError("REQUIRED_FRANK_GET_NOT_200_"+endpoint)
    expected_status=503 if stage=="fault" else 200
    if expected_status not in observations.get("/api/decisions",[]):
        raise RuntimeError("HISTORY_GET_NOT_EXPECTED_STATUS_"+stage)


def run(*, qa_sha: str, no_browser: bool=False) -> int:
    if sys.platform!="darwin":
        raise RuntimeError("MAC_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{40}",qa_sha):
        raise RuntimeError("QA_SHA_INVALID")
    for cmd in ("open","osascript","screencapture"):
        if not shutil.which(cmd):
            raise RuntimeError("MAC_TOOL_MISSING_"+cmd)
    checkout=Path(__file__).resolve().parents[3]
    home=Path.home()
    existing_port=base.discover_dashboard_port(home)
    base.verify_local_source(existing_port)
    with tempfile.TemporaryDirectory(prefix="frank-pr106-real-safari-") as work:
        temp=Path(work)
        static=temp/"pr106-product-git-objects"
        hashes=export_approved_static(checkout,qa_sha,static)
        screenshots=temp/"screenshots"
        screenshots.mkdir(mode=0o700)
        data=[]
        statuses={}
        stamp=datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        try:
            for stage in STAGES:
                token=uuid4().hex
                receipt={}
                observed=defaultdict(list)
                handler=make_handler(static,existing_port,stage,token,receipt,observed)
                server=ThreadingHTTPServer(("127.0.0.1",0),handler)
                thread=threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                try:
                    link=f"http://127.0.0.1:{server.server_port}/__qa/panel?"+urlencode(
                        {"token":token,"stage":stage})
                    if not no_browser:
                        subprocess.run(["open","-a","Safari",link],check=True,timeout=15)
                    until=time.monotonic()+WAIT_SECONDS
                    while stage not in receipt and time.monotonic()<until:
                        time.sleep(.2)
                    if stage not in receipt:
                        raise RuntimeError("SAFARI_READY_TIMEOUT_"+stage)
                    if not no_browser:
                        subprocess.run(["osascript","-e",'tell application "Safari" to activate'],
                                       check=True,capture_output=True,timeout=15)
                        time.sleep(.8)
                        if not capture.safari_front_matches(capture.safari_front_url(),link):
                            raise RuntimeError("SAFARI_FRONT_URL_MISMATCH_"+stage)
                    verify_stage(stage,receipt,observed)
                    photo=screenshots/f"frank-decisions-{stage}.png"
                    data.append(capture.automatic_screenshot(photo))
                    if not no_browser and not capture.safari_front_matches(
                            capture.safari_front_url(),link):
                        raise RuntimeError("SAFARI_SCREENSHOT_STAGE_DRIFT_"+stage)
                    statuses[stage]={"receipt":receipt[stage],
                                     "http_status_counts":{key:dict(
                                         (str(code),values.count(code)) for code in sorted(set(values)))
                                         for key,values in observed.items()}}
                    print(f"FRANK_DECISIONS_{stage.upper()}={receipt[stage]}",flush=True)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=3)
            base.verify_preview_snapshot(static,hashes)
            if read_git_head_passively(checkout)!=qa_sha:
                raise RuntimeError("QA_HEAD_CHANGED")
            downloads=home/"Downloads"
            downloads.mkdir(parents=True,exist_ok=True)
            output=downloads/f"frank-pr106-safari-503-{stamp}-{qa_sha[:8]}-{uuid4().hex[:10]}.zip"
            metadata={
                "kind":"FRANK_PR106_REAL_MAC_SAFARI_503_ISOLATION_QA",
                "qa_head_sha":qa_sha,"product_approved_sha":PRODUCT_SHA,
                "product_static_sha256":hashes,
                "backend_source_sha":"UNVERIFIED",
                "observed_at_utc":datetime.now(timezone.utc).isoformat(),
                "stages":statuses,
                "screenshots":data,
                "synthetic_503_scope":"EPHEMERAL_QA_PROXY_ONLY",
                "production_dashboard_modified":False,"new_rpc":False,
                "new_scan":False,"new_sqlite_write":False,"mail":False,"trades":False,
                "production_deploy":False,
            }
            with tempfile.TemporaryDirectory(prefix=".frank-pr106-stage-",dir=downloads) as staging:
                tempzip=Path(staging)/"bundle.zip"
                with zipfile.ZipFile(tempzip,"x",compression=zipfile.ZIP_DEFLATED) as z:
                    z.writestr("frank-pr106-acceptance.json",json.dumps(metadata,indent=2,ensure_ascii=False))
                    for row in data:
                        z.write(screenshots/row["file"],"screenshots/"+row["file"])
                base.verify_preview_snapshot(static,hashes)
                if read_git_head_passively(checkout)!=qa_sha:
                    raise RuntimeError("QA_HEAD_CHANGED_BEFORE_ZIP")
                os.link(tempzip,output)
            print("ZIP_READY="+str(output),flush=True)
            subprocess.run(["open","-R",str(output)],check=False,timeout=12)
            return 0

        except Exception as exc:
            # A failed QA run must retain any screenshots already captured and
            # an explicit REJECTED marker, never claim an accepted PASS ZIP.
            downloads=home/"Downloads"
            downloads.mkdir(parents=True,exist_ok=True)
            rejected=downloads/(
                f"frank-pr106-REJECTED-{stamp}-{qa_sha[:8]}-{uuid4().hex[:10]}.zip")
            with tempfile.TemporaryDirectory(prefix=".frank-pr106-rejected-",dir=downloads) as staging:
                staged=Path(staging)/"REJECTED.zip"
                with zipfile.ZipFile(staged,"x",compression=zipfile.ZIP_DEFLATED) as z:
                    z.writestr("REJECTED.json",json.dumps({
                        "status":"NOT_ACCEPTED","error_class":type(exc).__name__,
                        "reason":str(exc),"qa_sha":qa_sha,
                        "product_sha":PRODUCT_SHA,"stage_receipts":statuses,
                        "captured_at_utc":datetime.now(timezone.utc).isoformat(),
                        "no_rpc":True,"no_scan":True,"no_deploy":True,
                    },indent=2,ensure_ascii=False))
                    for row in data:
                        photo=screenshots/row["file"]
                        if photo.is_file() and not photo.is_symlink():
                            z.write(photo,"screenshots/"+photo.name)
                os.link(staged,rejected)
            print("STOP_FRANK_PR106_MAC_ACCEPTANCE="+str(exc),flush=True)
            print("REJECTED_ZIP_READY="+str(rejected),flush=True)
            subprocess.run(["open","-R",str(rejected)],check=False,timeout=12)
            return 3


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--qa-sha",required=True)
    args=p.parse_args()
    raise SystemExit(run(qa_sha=args.qa_sha))


if __name__=="__main__":
    main()
