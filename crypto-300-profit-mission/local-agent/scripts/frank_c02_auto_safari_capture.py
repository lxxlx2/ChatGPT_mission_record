#!/usr/bin/env python3
"""Automatic *isolated* Mac Safari C02 acceptance capture; no manual clicks.

Uses existing GET-only preview and immutable Git-object snapshot implementation.
Discovers a relevant local CA, opens the real C02 UI, auto-clicks its
'查看已有归档（只读）' control, waits for browser acknowledgement, captures two
screenshots, writes SHA-attested private ZIP in Downloads, then Finder-reveals it.
No production deploy/POST/new RPC/Gmail/trade/SQLite write or public upload.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.client import HTTPConnection
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
from urllib.parse import urlencode, urlsplit, parse_qs
from uuid import uuid4
import zipfile

import frank_pr101_safari_evidence as old

MAX_MINTS = 24
MAX_SOURCE_BYTES = 2_000_000
WAIT_SECONDS = 20.0
STAGES = ("overview", "report")


def local_json(port: int, path: str):
    conn = HTTPConnection("127.0.0.1", port, timeout=4)
    try:
        conn.request("GET", path, headers={"Accept": "application/json"})
        response = conn.getresponse()
        body = response.read(MAX_SOURCE_BYTES + 1)
        if (response.status != 200 or len(body) > MAX_SOURCE_BYTES
                or "application/json" not in (response.getheader("Content-Type") or "")):
            return None
        return json.loads(body)
    except (OSError, ValueError, TimeoutError):
        return None
    finally:
        conn.close()


def collect_mints(value):
    if isinstance(value, list):
        items = value
    elif isinstance(value, dict):
        items = next((value[k] for k in ("candidates", "rows", "watchlist", "items")
                      if isinstance(value.get(k), list)), [])
    else:
        items = []
    result = []
    for row in items:
        if not isinstance(row, dict):
            continue
        mint = row.get("mint") or row.get("token_mint")
        if isinstance(mint, str) and re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", mint) and mint not in result:
            result.append(mint)
    return result


def select_local_ca(port: int, explicit: str | None) -> dict:
    if explicit is not None:
        if not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", explicit):
            raise RuntimeError("INVALID_EXPLICIT_SOLANA_CA")
        report = local_json(port, "/api/cluster-latest?" + urlencode({"mint": explicit}))
        exists = isinstance(report, dict) and report.get("mint") == explicit
        return {"mint": explicit, "archive_found": exists, "source": "USER_EXPLICIT_CA",
                "checked": 1}
    ordered = []
    for endpoint in ("/api/candidates", "/api/frank-observed-watchlist"):
        for mint in collect_mints(local_json(port, endpoint)):
            if mint not in ordered:
                ordered.append(mint)
            if len(ordered) >= MAX_MINTS:
                break
        if len(ordered) >= MAX_MINTS:
            break
    for i, mint in enumerate(ordered):
        report = local_json(port, "/api/cluster-latest?" + urlencode({"mint": mint}))
        if isinstance(report, dict) and report.get("mint") == mint:
            return {"mint": mint, "archive_found": True, "source": "LOCAL_CACHED_CA_MATCH",
                    "checked": i + 1}
    return {"mint": ordered[0] if ordered else None, "archive_found": False,
            "source": "LOCAL_CA_WITHOUT_ARCHIVE" if ordered else "NO_LOCAL_CA",
            "checked": len(ordered)}


def qa_page(mint: str | None, stage: str, token: str) -> bytes:
    """Nonproduction parent frame; real product iframe and actual button execute normally."""
    if stage not in STAGES:
        raise ValueError("QA_STAGE_NOT_ALLOWED")
    mint_js = json.dumps(mint or "", ensure_ascii=True)
    token_js = json.dumps(token)
    stage_js = json.dumps(stage)
    body = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mission C02 自动验收</title>
<style>
html,body{margin:0;height:100%;background:#0e1116;color:#eef2f9;font:14px system-ui}
header{height:64px;box-sizing:border-box;padding:9px 18px;background:#151a22;border-bottom:1px solid #465064}
header b{display:block;font-size:16px}header span{font-size:12px;color:#abb9c8}
iframe{display:block;width:100%;height:calc(100% - 64px);border:0;background:#101419}
</style></head><body>
<header><b>Mission C02 · 自动只读验收（非生产部署）</b>
<span id="qa-progress">加载实际 CA 页面并自动点击「查看已有归档（只读）」...</span></header>
<iframe id="qa-app" title="真实 C02 应用界面" src="/index.html#cluster"></iframe>
<script>
(function(){
const MINT=__MINT__, STAGE=__STAGE__, TOKEN=__TOKEN__;
const frame=document.getElementById('qa-app');
let ended=false;
function ready(state){
  if(ended) return;
  ended=true;
  document.getElementById('qa-progress').textContent=
    '页面交互：'+state+' · CA：'+(MINT||'本地无 CA')+' · 仅已有归档 GET，不执行扫描';
  document.title='C02_AUTOMATED_'+state;
  const signal='/__qa/ready?'+new URLSearchParams({token:TOKEN,stage:STAGE,state:state});
  fetch(signal,{method:'GET',cache:'no-store'}).catch(()=>{});
}
frame.onload=()=>{
  try{
    const d=frame.contentDocument;
    if(!MINT){ready('NO_LOCAL_CA');return;}
    const input=d.getElementById('cluster-mint');
    const button=d.getElementById('cluster-archive-load');
    if(!input||!button){ready('PRODUCT_BUTTON_MISSING');return;}
    input.value=MINT;
    button.click();
    const begin=Date.now();
    const poll=setInterval(()=>{
      const status=d.getElementById('cluster-status');
      const message=status?.textContent||'';
      const found=message.includes('已读取本地历史分析');
      const missing=message.includes('没有可读取的本地历史分析');
      const timeout=Date.now()-begin>12500;
      if(!found&&!missing&&!timeout)return;
      clearInterval(poll);
      const activeMint=d.querySelector('.summary-ca')?.textContent||'';
      if(found && activeMint!==MINT){ready('PRODUCT_UI_MINT_MISMATCH');return;}
      if(STAGE==='report'&&found){
         d.getElementById('cluster-market')?.scrollIntoView({block:'start'});
      }else{
         d.getElementById('cluster-status')?.scrollIntoView({block:'start'});
      }
      setTimeout(()=>ready(found?'ARCHIVE_FOUND':missing?'ARCHIVE_MISSING':'PRODUCT_TIMEOUT'),700);
    },180);
  }catch(e){ready('PRODUCT_UI_ERROR');}
};
setTimeout(()=>ready('PRODUCT_TIMEOUT'),17000);
})();
</script></body></html>"""
    return body.replace("__MINT__", mint_js).replace("__TOKEN__", token_js).replace("__STAGE__", stage_js).encode("utf-8")


def make_auto_handler(static: Path, live_port: int, token: str, mint: str | None, receipts: dict):
    base = old.make_handler(static, live_port)

    class AutoHandler(base):
        def do_GET(self):
            host = self.headers.get("Host", "")
            if host not in {f"127.0.0.1:{self.server.server_port}",
                            f"localhost:{self.server.server_port}"}:
                return self.send_error(421, "LOOPBACK_HOST_REQUIRED")
            parsed = urlsplit(self.path)
            if parsed.path == "/__qa/panel":
                params = parse_qs(parsed.query)
                if set(params) != {"token", "stage"} or params.get("token") != [token] or params.get("stage", [None])[0] not in STAGES:
                    return self.send_error(403, "QA_TOKEN_OR_STAGE_INVALID")
                payload = qa_page(mint, params["stage"][0], token)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if parsed.path == "/__qa/ready":
                params = parse_qs(parsed.query)
                if (set(params) != {"token", "stage", "state"} or params.get("token") != [token]
                        or params.get("stage", [None])[0] not in STAGES
                        or params.get("state", [None])[0] not in {
                            "ARCHIVE_FOUND","ARCHIVE_MISSING","NO_LOCAL_CA",
                            "PRODUCT_TIMEOUT","PRODUCT_UI_ERROR","PRODUCT_BUTTON_MISSING",
                            "PRODUCT_UI_MINT_MISMATCH"
                        }):
                    return self.send_error(403)
                receipts[params["stage"][0]] = params["state"][0]
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return super().do_GET()

    return AutoHandler


def safari_front_url():
    r = subprocess.run(
        ["osascript", "-e", 'tell application "Safari" to get URL of front document'],
        capture_output=True, text=True, timeout=12, check=False,
    )
    return r.stdout.strip() if r.returncode == 0 else None


def safari_front_matches(actual: str | None, expected: str) -> bool:
    """Require the expected document including origin, per-run token and stage."""
    try:
        if not actual:
            return False
        front, target = urlsplit(actual), urlsplit(expected)
        expected_params = parse_qs(target.query, strict_parsing=True, keep_blank_values=True)
        received_params = parse_qs(front.query, strict_parsing=True, keep_blank_values=True)
        return (front.scheme == target.scheme == "http"
                and front.netloc == target.netloc
                and front.path == target.path == "/__qa/panel"
                and not front.fragment and not target.fragment
                and set(expected_params) == {"token", "stage"}
                and all(len(values) == 1 and values[0] for values in expected_params.values())
                and received_params == expected_params)
    except (ValueError, TypeError):
        return False


def automatic_screenshot(out: Path):
    subprocess.run(["screencapture", "-x", "-D", "1", str(out)], timeout=15, check=True)
    raw = out.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw) < 2048:
        raise RuntimeError("MAC_SCREENSHOT_INVALID_OR_PERMISSION_DENIED")
    return {"file": out.name, "bytes": len(raw), "sha256": old.sha256_bytes(raw),
            "meaning": "Automatic Safari C02 exact CA GET-only archived-view acceptance"}


def run_auto(*, sha: str, mint: str | None, skip_browser: bool = False):
    if sys.platform != "darwin":
        raise RuntimeError("MACOS_REQUIRED")
    for command in ("screencapture", "osascript", "open"):
        if not shutil.which(command):
            raise RuntimeError("MAC_TOOL_UNAVAILABLE_" + command)
    source_port = old.discover_dashboard_port(Path.home())
    old.verify_local_source(source_port)
    with tempfile.TemporaryDirectory(prefix="frank-c02-autocapture-") as temp:
        work = Path(temp)
        candidate = old.pinned_candidate_checkout(Path(__file__), sha)
        checkout = candidate.parents[4]
        static = work / "immutable-committed-static"
        hashes = old.export_exact_git_static(checkout, sha, static)
        selected = select_local_ca(source_port, mint)
        captures = work / "screenshots"
        captures.mkdir(mode=0o700)
        token = uuid4().hex
        receipts = {}
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_auto_handler(static, source_port, token, selected["mint"], receipts),
        )
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        output = None
        stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        try:
            rows = []
            for stage in STAGES:
                link = f"http://127.0.0.1:{server.server_port}/__qa/panel?" + urlencode({"token":token,"stage":stage})
                if not skip_browser:
                    subprocess.run(["open", "-a", "Safari", link], check=True, timeout=15)
                end = time.monotonic() + WAIT_SECONDS
                while stage not in receipts and time.monotonic() < end:
                    time.sleep(0.2)
                if stage not in receipts:
                    raise RuntimeError("SAFARI_QA_PAGE_DID_NOT_REPORT_READY_" + stage)
                if not skip_browser:
                    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'],
                                   check=True, capture_output=True, timeout=15)
                    time.sleep(0.8)
                    if not safari_front_matches(safari_front_url(), link):
                        raise RuntimeError("SAFARI_FRONT_STAGE_OR_TOKEN_MISMATCH_" + stage)
                dest = captures / f"c02-{stage}.png"
                rows.append(automatic_screenshot(dest))
                if not skip_browser and not safari_front_matches(safari_front_url(), link):
                    raise RuntimeError("SAFARI_FRONT_CHANGED_DURING_CAPTURE_" + stage)
                print(f"C02_AUTOMATIC_{stage.upper()}={receipts[stage]}", flush=True)
                if receipts[stage] in {
                    "PRODUCT_TIMEOUT", "PRODUCT_UI_ERROR",
                    "PRODUCT_BUTTON_MISSING", "PRODUCT_UI_MINT_MISMATCH",
                }:
                    raise RuntimeError("STOP_C02_PRODUCT_UI_NOT_VERIFIED_" + receipts[stage])
            old.verify_git_source(checkout, sha)
            old.verify_preview_snapshot(static, hashes)
            downloads = Path.home() / "Downloads"
            downloads.mkdir(parents=True, exist_ok=True)
            output = downloads / (
                f"frank-c02-auto-evidence-{stamp}-{sha[:8]}-{uuid4().hex[:12]}.zip")
            # Stage the entire ZIP on the SAME filesystem in a uniquely owned
            # private directory. Never use existence as proof of ownership.
            with tempfile.TemporaryDirectory(prefix=".frank-c02-stage-", dir=downloads) as staging:
                staged_zip = Path(staging) / "evidence.zip"
                old.package_evidence(captures, staged_zip, rows, static,
                                     source_port=source_port, preview_port=server.server_port,
                                     preview_sha=sha, verified_static_hashes=hashes)
                with zipfile.ZipFile(staged_zip, "a", compression=zipfile.ZIP_DEFLATED) as z:
                    z.writestr("c02-automatic-acceptance.json",
                               json.dumps({
                                   "mode":"AUTOMATIC_SAFARI_APP_IFRAME_INTERACTION",
                                   "preview_static_sha":sha, "backend_code_identity":"UNVERIFIED",
                                   "selected":selected,"page_states":receipts,
                                   "new_rpc":False,"new_scan":False,
                                   "captured_at_utc":datetime.now(timezone.utc).isoformat(),
                                   "source":"EXISTING_LOCAL_DASHBOARD_READ_ONLY_GET",
                                   "display_capture":"PRIMARY_DISPLAY_SCREENSHOT",
                                   "real_mac_safari":not skip_browser,
                                   "archive_reporting":(
                                       "ARCHIVE_FOUND" if all(v=="ARCHIVE_FOUND" for v in receipts.values())
                                       else "NO_VERIFIED_CACHED_ARCHIVE"),
                               }, ensure_ascii=False, indent=2))
                old.verify_git_source(checkout, sha)
                old.verify_preview_snapshot(static, hashes)
                # os.link is an atomic no-overwrite publication. A racing ZIP
                # at the final name is NEVER replaced, claimed or unlinked.
                os.link(staged_zip, output)
            print("ZIP_READY="+str(output),flush=True)
            subprocess.run(["open", "-R", str(output)],check=False)
            return 0
        except Exception as exc:
            # Only private per-run staging files can be cleaned up. We never
            # delete a final path we did not exclusively publish.
            rejected_root = Path.home() / "Downloads"
            rejected = rejected_root / f"frank-c02-REJECTED-{stamp}-{sha[:8]}-{uuid4().hex[:8]}"
            rejected.mkdir(mode=0o700)
            for screenshot in captures.glob("c02-*.png"):
                if screenshot.is_file() and not screenshot.is_symlink():
                    shutil.copy2(screenshot, rejected / screenshot.name)
            (rejected / "REJECTED.json").write_text(
                json.dumps({"status":"REJECTED_NOT_VALID_MAC_ACCEPTANCE",
                            "reason":type(exc).__name__ + ": " + str(exc),
                            "expected_sha":sha,
                            "selected_ca":selected.get("mint"),
                            "page_states":receipts,
                            "captured_at_utc":datetime.now(timezone.utc).isoformat()},
                           ensure_ascii=False, indent=2), encoding="utf-8")
            print("STOP_C02_AUTOMATIC_ACCEPTANCE="+str(exc),flush=True)
            print("REJECTED_SCREENSHOTS_PRESERVED="+str(rejected),flush=True)
            subprocess.run(["open","-R",str(rejected)],check=False)
            return 3
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--mint", default=None, help="Optional exact CA; omitted means auto-discover local cached report")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}",args.candidate_sha):
        raise SystemExit("INVALID_CANDIDATE_SHA")
    raise SystemExit(run_auto(sha=args.candidate_sha, mint=args.mint))


if __name__ == "__main__":
    main()
