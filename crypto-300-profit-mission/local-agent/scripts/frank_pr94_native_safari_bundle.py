"""Native macOS Safari.app screenshots of frozen PR94, synthetic localhost ONLY.

This is NOT the Playwright WebKit browser. macOS may require one-time Terminal
Screen Recording and Automation permission and Safari's developer option
'Allow JavaScript from Apple Events'. No production services or RPC.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

TREE = "e2b291a29decad536c8c10b4b1a4f9b5688d22b4"
QA_PREFIX = "frank-pr94-preflight-"
SWIFT = r"""
import CoreGraphics
import Foundation
let windows = CGWindowListCopyWindowInfo(
    [.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID
) as? [[String: Any]] ?? []
for item in windows {
    let owner = item[kCGWindowOwnerName as String] as? String ?? ""
    let layer = (item[kCGWindowLayer as String] as? NSNumber)?.intValue ?? -1
    let number = (item[kCGWindowNumber as String] as? NSNumber)?.intValue ?? 0
    if owner == "Safari" && layer == 0 && number > 0 {
        print(number)
        exit(0)
    }
}
fputs("NATIVE_SAFARI_WINDOW_NOT_FOUND\n", stderr)
exit(2)
"""

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def apple_escape(value):
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

def osa(lines):
    args = ["/usr/bin/osascript"]
    for line in lines:
        args += ["-e", line]
    out = subprocess.run(args, text=True, capture_output=True, timeout=30)
    if out.returncode:
        detail = (out.stderr or out.stdout).strip()
        if "JavaScript" in detail or "Apple Events" in detail or "not allowed" in detail.lower():
            raise RuntimeError("SAFARI_JAVASCRIPT_FROM_APPLE_EVENTS_DISABLED: " + detail[:400])
        raise RuntimeError("SAFARI_APPLESCRIPT_FAILED: " + detail[:400])
    return out.stdout.strip()

def open_native_safari(url, new=False):
    u = urlsplit(url)
    if u.scheme != "http" or u.hostname != "127.0.0.1":
        raise ValueError("QA_SAFARI_NOT_LOOPBACK")
    value = apple_escape(url)
    if new:
        return osa(["tell application \"Safari\"",
                    "activate",
                    'make new document with properties {URL:"' + value + '"}',
                    "end tell"])
    return osa(["tell application \"Safari\"",
                "activate",
                'set URL of front document to "' + value + '"',
                "end tell"])

def js_eval(source):
    expr = apple_escape(source)
    return osa(['tell application "Safari" to do JavaScript "' + expr + '" in front document'])

def poll(expr, predicate=lambda x: x == "true", seconds=18):
    limit = time.monotonic() + seconds
    latest = ""
    while time.monotonic() < limit:
        latest = js_eval(expr)
        if predicate(latest):
            return latest
        time.sleep(0.35)
    raise RuntimeError("NATIVE_SAFARI_DOM_TIMEOUT: " + latest[:300])

def screenshot(binary, path):
    found = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
    if found.returncode or not found.stdout.strip().isdigit():
        raise RuntimeError("NATIVE_SAFARI_WINDOW_ID_UNAVAILABLE: " + found.stderr.strip()[:300])
    win_id = found.stdout.strip()
    result = subprocess.run(["/usr/sbin/screencapture", "-x", "-l", win_id, str(path)],
                            capture_output=True, text=True, timeout=35)
    if result.returncode or not path.is_file() or path.stat().st_size < 1500:
        raise RuntimeError("SAFARI_SCREEN_RECORDING_PERMISSION_REQUIRED: " + result.stderr.strip()[:300])
    if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("NATIVE_SAFARI_SCREENSHOT_INVALID")
    return {"file":path.name, "window_id":int(win_id), "sha256":sha(path),
            "bytes":path.stat().st_size, "url":js_eval("document.location.href")}

def validate_qa_root(root):
    root = root.expanduser().absolute()
    if root.is_symlink() or root.parent.resolve() != (Path.home()/".local/share").resolve():
        raise ValueError("QA_ROOT_NOT_ISOLATED")
    if not root.name.startswith(QA_PREFIX) or not (root/"repo/.git").is_dir():
        raise ValueError("QA_ROOT_NOT_PR94_PREFLIGHT")
    for child in ["qa-runtime", "qa-evidence", "repo"]:
        if (root/child).is_symlink():
            raise ValueError("QA_SYMLINK_FORBIDDEN:" + child)
    return root

def save(folder, images, bin_path, name):
    shot = screenshot(bin_path, folder/(name+".png"))
    images.append({"scene":name, **shot})
    return shot

def run(root, launcher, helper, folder, images, findings):
    repo = root/"repo"
    spec=importlib.util.spec_from_file_location("frank_qa_bundle", helper)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.check(root)
    proc = reader = None
    try:
        proc, reader, receipt = mod.start(root, repo, launcher, folder)
        findings["qa_launcher_receipt"]=receipt
        findings["synthetic_only"]=receipt.get("synthetic_only") is True
        findings["real_rpc"]=receipt.get("real_rpc")
        if not findings["synthetic_only"] or findings["real_rpc"] is not False:
            raise RuntimeError("QA_REAL_SOURCE_OR_IDENTITY_INVALID")
        url=receipt["urls"]["signals"]
        open_native_safari(url, new=True)
        poll('document.querySelectorAll(".candidate-card.decision-buy[data-f01-guard-state=VERIFIED]").length===1')
        findings["f01_early_verified"]=True
        save(folder,images,BIN,"01-safari-f01-verified")
        js_eval('document.querySelectorAll("details").forEach(x=>x.open=true); window.scrollTo(0,0); "expanded"')
        save(folder,images,BIN,"02-safari-f01-expanded")
        open_native_safari(receipt["urls"]["cluster"])
        poll('!!document.querySelector("#cluster-mint")')
        for i,mint in enumerate([receipt["mint_a"],receipt["mint_b"]],start=3):
            m=json.dumps(mint)
            js_eval('document.querySelector("#cluster-mint").value='+m+
                    ';document.querySelector("#cluster-submit").click();"submitted"')
            poll('(()=>{const x=document.querySelector("#cluster-result");return !!x&&!x.hidden&&x.innerText.length>120})()')
            text=js_eval('document.querySelector("#cluster-result").innerText')
            if mint not in text:
                raise RuntimeError("NATIVE_SAFARI_CA_NOT_EXACT:"+str(i))
            findings["c02_ca_"+str(i)]=mint
            save(folder,images,BIN,f"0{i}-safari-ca")
            js_eval('document.querySelectorAll("details").forEach(x=>x.open=true);window.scrollTo(0,600);"expanded"')
            save(folder,images,BIN,f"0{i}-safari-ca-expanded")
        open_native_safari(receipt["urls"]["f02_research_only"])
        poll('document.querySelectorAll("#position-rows tr").length===32')
        findings["f02_fresh_rows"]=32
        save(folder,images,BIN,"07-safari-f02-fresh")
        found = js_eval('(()=>{const q=document.querySelector("#mint-search");q.value='+json.dumps(receipt["mint_a"])+
                        ';q.dispatchEvent(new Event("input",{bubbles:true}));return q.value})()')
        if found != receipt["mint_a"]:
            raise RuntimeError("F02_MINT_FILTER_FAILED")
        save(folder,images,BIN,"08-safari-f02-filter")
        started = __import__("datetime").datetime.fromisoformat(
            receipt["started_at_utc"].replace("Z","+00:00")).timestamp()
        time.sleep(max(0, 126-(time.time()-started)))
        js_eval('(()=>{const q=document.querySelector("#mint-search");q.value="";q.dispatchEvent(new Event("input",{bubbles:true}));return "clear"})()')
        poll('document.querySelectorAll("#position-rows tr").length===32')
        old = js_eval('Array.from(document.querySelectorAll("#position-rows tr td:nth-child(3)")).some(x=>x.innerText.includes("123.000000")||x.innerText.includes("0.000000"))')
        if old != "false":
            raise RuntimeError("NATIVE_SAFARI_F02_EXPIRED_QUANTITY_RESTORED")
        findings["f02_expired_quantities_masked"]=True
        save(folder,images,BIN,"09-safari-f02-expired")
        open_native_safari(url)
        poll('document.querySelectorAll(".candidate-card.decision-buy[data-f01-guard-state=VERIFIED]").length===1')
        findings["f01_verified_after_f02_expiry"]=True
        save(folder,images,BIN,"10-safari-f01-after-expiry")
        return receipt
    finally:
        if proc is not None:
            mod.stop_process(proc,reader)
            findings["launcher_exit_code"]=proc.returncode
            log=(folder/"launcher.log").read_text(errors="replace")
            findings["native_http_traceback_count"]=log.count("Traceback (most recent call last):")
            findings["f01_synthetic_partition_errors"]=log.count("F01_SYNTHETIC_PARTITION_FAILED")
            if findings["native_http_traceback_count"] or findings["f01_synthetic_partition_errors"] or proc.returncode:
                raise RuntimeError("NATIVE_SAFARI_QA_LAUNCHER_LOG_FAILURE")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--qa-root",type=Path)
    parser.add_argument("--launcher-file",type=Path)
    parser.add_argument("--helper-file",type=Path)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        assert apple_escape('abc"\\') == 'abc\\"\\\\'
        assert urlsplit("http://127.0.0.1:1234/#signals").hostname=="127.0.0.1"
        print("FRANK_PR94_NATIVE_SAFARI_QA_SCRIPT_SELFTEST_PASS")
        return
    if sys.platform != "darwin":
        raise SystemExit("NATIVE_SAFARI_QA_MACOS_ONLY")
    root=validate_qa_root(args.qa_root)
    launcher=(root/"qa-runtime/frank-pr94-safari.py")
    helper=(root/"qa-runtime/frank-pr94-browser-bundle.py")
    if (args.launcher_file != launcher or args.helper_file != helper or
            not launcher.is_file() or not helper.is_file() or
            launcher.is_symlink() or helper.is_symlink()):
        raise SystemExit("QA_HELPERS_NOT_PINNED")
    os.umask(0o077)
    date=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence=root/"qa-evidence"
    evidence.mkdir(mode=0o700,exist_ok=True)
    if evidence.is_symlink():
        raise SystemExit("QA_EVIDENCE_SYMLINK_FORBIDDEN")
    folder=evidence/("native-safari-"+date)
    folder.mkdir(mode=0o700)
    binary=root/"qa-runtime/safari-window-id"
    swift=root/"qa-runtime/safari-window-id.swift"
    if swift.is_symlink() or binary.is_symlink():
        raise SystemExit("QA_SWIFT_SYMLINK_FORBIDDEN")
    swift.write_text(SWIFT)
    subprocess.run(["/usr/bin/xcrun","swiftc",str(swift),"-o",str(binary)],check=True,timeout=90)
    global BIN
    BIN=binary
    manifest={"status":"STARTED","browser":"macOS Safari.app via Apple Events + screencapture",
              "source_tree_sha":TREE,"images":[],"synthetic_only":True,
              "real_rpc":False,"findings":{},"errors":[]}
    try:
        run(root,launcher,helper,folder,manifest["images"],manifest["findings"])
        manifest["status"]="NATIVE_SAFARI_SYNTHETIC_QA_PASS"
    except BaseException as exc:
        manifest["status"]="NATIVE_SAFARI_SYNTHETIC_QA_INCOMPLETE"
        manifest["errors"].append(type(exc).__name__+": "+str(exc))
    manifest_path=folder/"manifest.json"
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    (folder/"SHA256SUMS.txt").write_text("\n".join(
        sha(p)+"  "+p.name for p in sorted(folder.iterdir())
        if p.is_file() and p.name!="SHA256SUMS.txt")+"\n")
    zip_file=evidence/("frank-native-safari-"+date+"-"+TREE[:12]+".zip")
    with ZipFile(zip_file,"w",ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.iterdir()):
            if p.is_file():
                z.write(p,p.name)
    with ZipFile(zip_file) as z:
        if z.testzip() is not None:
            raise RuntimeError("NATIVE_SAFARI_QA_ZIP_CRC_INVALID")
    print(json.dumps({"status":manifest["status"],"zip_file":str(zip_file),
                       "screenshots":len(manifest["images"]),"errors":manifest["errors"]},
                     ensure_ascii=False),flush=True)
    print("UPLOAD_THIS_ZIP="+str(zip_file),flush=True)
    if manifest["errors"]:
        raise SystemExit(1)

if __name__=="__main__":
    main()
