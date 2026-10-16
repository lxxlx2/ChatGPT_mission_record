"""Synthetic Frank QA full-page screenshot ZIP via Playwright WebKit.

Playwright WebKit is NOT Safari.app. The separately observed Safari screenshots
remain native Safari evidence. Do not use this program for real-wallet data.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

TREE = "eea30efa09cb1509d7eee3fde3043ee7155257cf"
ROOT = Path.home() / ".local/share/frank-pr85-mac-qa-R1c6kmCU"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def check(root):
    if root.resolve(strict=True) != ROOT.resolve(strict=True):
        raise ValueError("QA_ROOT_NOT_APPROVED")
    repo = root / "repo"
    if git(repo, "rev-parse", "HEAD^{tree}") != TREE:
        raise ValueError("FROZEN_TREE_CHANGED")
    if git(repo, "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"):
        raise ValueError("FROZEN_REPO_NOT_CLEAN")
    return repo


def read_output(proc, stream, dest):
    with dest.open("w") as f:
        for line in stream:
            f.write(line)
            f.flush()
            proc.put(line.strip())


def start(root, repo, launcher, folder):
    local_agent = repo / "crypto-300-profit-mission/local-agent"
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "HOME": str(Path.home()), "TMPDIR": str(root / "qa-runtime"),
           "LANG": "en_US.UTF-8", "PYTHONNOUSERSITE": "1",
           "PYTHONPATH": str(local_agent), "NO_PROXY": "127.0.0.1,localhost"}
    process = subprocess.Popen(
        [sys.executable, "-B", str(launcher), "--qa-root", str(root), "--no-safari"],
        cwd=local_agent, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1)
    messages = queue.Queue()
    reader = threading.Thread(target=read_output,
        args=(messages, process.stdout, folder / "launcher.log"), daemon=True)
    reader.start()
    end = time.monotonic() + 50
    while time.monotonic() < end:
        try:
            line = messages.get(timeout=0.25)
        except queue.Empty:
            if process.poll() is not None:
                raise RuntimeError("LAUNCHER_EXITED_" + str(process.returncode))
            continue
        if line.startswith("{"):
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if data.get("status") == "MAC_PR85_SYNTHETIC_HTTP_SMOKE_PASS":
                if data.get("source_tree_sha") != TREE or data.get("real_rpc") is not False:
                    raise RuntimeError("LAUNCHER_SOURCE_FAILED")
                return process, reader, data
    raise TimeoutError("QA_LAUNCHER_TIMEOUT")


def expand(page):
    page.evaluate("""() => {
        document.querySelectorAll('details').forEach(d => {
            if (d.getClientRects().length && getComputedStyle(d).display !== 'none') d.open=true;
        });
    }""")
    page.wait_for_timeout(180)


def label(page):
    page.evaluate("""() => {
        const id='synthetic-qa-banner';
        if (document.getElementById(id)) return;
        const d=document.createElement('div');
        d.id=id;
        d.textContent='SYNTHETIC QA · 模拟数据 · 禁止交易 · WebKit 自动截图（非 Safari.app）';
        d.style.cssText='position:fixed;top:0;left:0;right:0;padding:10px;background:#9c1738;color:#fff;font-size:15px;font-weight:700;text-align:center;z-index:2147483647;pointer-events:none;';
        document.body.append(d);
    }""")


def shot(page, folder, manifest, name, desc, open_details=True):
    if open_details:
        expand(page)
    label(page)
    path = folder / (name + ".png")
    page.screenshot(path=str(path), full_page=True, animations="disabled", timeout=30000)
    manifest["images"].append({"file": path.name, "sha256": sha(path),
        "utc": now(), "route": page.url, "description": desc, "expanded": open_details})


def take(browser, receipt, folder, manifest):
    logs = []
    ctx = browser.new_context(viewport={"width":1440,"height":900}, locale="zh-CN")
    def local_only(route):
        u = urlsplit(route.request.url)
        if u.scheme in ("http","https") and u.hostname in ("127.0.0.1","localhost"):
            route.continue_()
        else:
            route.abort()
    ctx.route("**/*", local_only)
    def track(page):
        page.on("pageerror", lambda err: logs.append({"utc":now(),"url":page.url,"type":"pageerror","text":str(err)}))
        page.on("console", lambda msg: logs.append({"utc":now(),"url":page.url,"type":msg.type,"text":msg.text}) if msg.type in ("error","warning") else None)
    ctx.on("page", track)
    f02 = ctx.new_page()
    f02.goto(receipt["urls"]["f02_research_only"], wait_until="domcontentloaded")
    f02.wait_for_function("document.querySelectorAll('#position-rows tr').length === 32", timeout=15000)
    shot(f02, folder, manifest, "01-f02-fresh-32-all", "fresh 32 Mint research state")
    f02.locator("#mint-search").fill(receipt["mint_a"])
    f02.wait_for_timeout(180)
    shot(f02, folder, manifest, "02-f02-fresh-filter", "fresh exact CA search nonzero")
    f02.locator("#mint-search").fill("")
    signals = ctx.new_page()
    signals.goto(receipt["urls"]["signals"], wait_until="domcontentloaded")
    signals.wait_for_selector(".candidate-card", timeout=15000)
    if signals.locator('button[data-view]').count()!=2:
        raise ValueError("FORMAL_BUSINESS_TAB_COUNT_NOT_TWO")
    if signals.locator(".candidate-card.decision-buy").count()!=1:
        raise ValueError("F01_EXPECT_ONE_ELIGIBLE_SYNTHETIC_BUY")
    shot(signals, folder, manifest, "03-f01-summary", "F01 actionable and excluded", False)
    shot(signals, folder, manifest, "04-f01-expanded", "F01 all visible details")
    for num, key, mint in ((5,"a",receipt["mint_a"]), (7,"b",receipt["mint_b"])):
        page=ctx.new_page()
        page.goto(receipt["urls"]["cluster"], wait_until="domcontentloaded")
        page.locator("#cluster-mint").fill(mint)
        page.locator("#cluster-submit").click()
        page.wait_for_function("() => {let r=document.querySelector('#cluster-result');return r&&!r.hidden&&r.innerText.length>120}",timeout=15000)
        if "mint_sha256_" in page.locator("#cluster-result").inner_text() or "slot_502" in page.locator("#cluster-result").inner_text():
            raise ValueError("C02_EXPOSES_RAW_SOURCE_AUDIT")
        shot(page,folder,manifest,f"{num:02d}-c02-{key}-summary",f"C02 exact CA {mint} summary",False)
        shot(page,folder,manifest,f"{num+1:02d}-c02-{key}-all-expanded",f"C02 exact CA {mint} all details")
        page.close()
    started=datetime.fromisoformat(receipt["started_at_utc"].replace("Z","+00:00")).timestamp()
    remaining=125-(time.time()-started)
    if remaining>0:
        time.sleep(remaining)
    f02.bring_to_front()
    f02.wait_for_timeout(1200)
    shot(f02,folder,manifest,"09-f02-expired-all","after TTL synthetic quantities masked")
    amounts=f02.locator("#position-rows tr td:nth-child(3)").all_inner_texts()
    if any("123.000000" in a or "0.000000" in a for a in amounts):
        raise ValueError("F02_EXPIRED_RESTORED_OLD_QUANTITY")
    f02.locator("#mint-search").fill(receipt["mint_b"])
    f02.wait_for_timeout(150)
    shot(f02,folder,manifest,"10-f02-expired-filter","expired after filter")
    ctx.close()
    return logs


def archive(folder, destination):
    files=sorted(p for p in folder.iterdir() if p.is_file())
    with ZipFile(destination,"w",ZIP_DEFLATED,compresslevel=6) as z:
        for file in files:
            z.write(file,arcname=file.name)
    with ZipFile(destination,"r") as z:
        if z.testzip() is not None or len(z.namelist()) != len(files):
            raise ValueError("ARCHIVE_INTEGRITY_FAILED")
    return len([p for p in files if p.suffix==".png"])


def selftest():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        (root/"test.png").write_bytes(b"fixture")
        (root/"manifest.json").write_text("{}")
        assert archive(root,root/"selftest.zip")==1
    print("BROWSER_EVIDENCE_ZIP_SELFTEST_PASS")


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--qa-root",type=Path)
    cli.add_argument("--launcher-file",type=Path)
    cli.add_argument("--self-test",action="store_true")
    args=cli.parse_args()
    if args.self_test:
        selftest()
        return
    if not args.qa_root or not args.launcher_file:
        cli.error("need --qa-root and --launcher-file")
    root=args.qa_root.expanduser().resolve(strict=True)
    repo=check(root)
    launcher=args.launcher_file.expanduser().resolve(strict=True)
    if launcher != (root/"qa-runtime/frank-pr85-safari.py").resolve():
        raise ValueError("QA_LAUNCHER_NOT_PINNED_IN_ROOT")
    tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out=root/"qa-evidence"
    out.mkdir(mode=0o700,exist_ok=True)
    folder=out/("screenshots-"+tag)
    folder.mkdir(mode=0o700)
    zip_file=out/("frank-safari-"+tag+"-"+TREE[:12]+".zip")
    result={"status":"STARTED","source_tree_sha":TREE,"started_utc":now(),
            "images":[],"browser":"Playwright WebKit, NOT Safari.app",
            "mac_safari_verified_by_automation":False,
            "synthetic_only":True,"real_rpc":False}
    proc=None
    reader=None
    logs=[]
    errors=[]
    try:
        proc,reader,receipt=start(root,repo,launcher,folder)
        result["launcher_receipt"]=receipt
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.webkit.launch(headless=True)
            try:
                result["browser_version"]=browser.version
                logs=take(browser,receipt,folder,result)
                result["status"]="WEBKIT_SCREENSHOTS_CAPTURED_NOT_SAFARI_PASS"
            finally:
                browser.close()
    except Exception as e:
        errors.append(type(e).__name__+": "+str(e))
        result["status"]="PARTIAL_OR_FAILED"
    finally:
        if proc is not None:
            if proc.poll() is None:
                try:
                    proc.stdin.write("\n")
                    proc.stdin.flush()
                    proc.wait(timeout=20)
                except (BrokenPipeError,subprocess.TimeoutExpired):
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=10)
            if reader:
                reader.join(timeout=4)
            result["launcher_exit_code"]=proc.returncode
        if git(repo,"rev-parse","HEAD^{tree}")!=TREE:
            errors.append("FROZEN_SOURCE_DRIFT")
            result["status"]="PARTIAL_OR_FAILED"
        result["errors"]=errors
        result["finished_utc"]=now()
        (folder/"browser-console.json").write_text(json.dumps(logs,ensure_ascii=False,indent=2))
        (folder/"errors.txt").write_text("\n".join(errors)+"\n")
        (folder/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
        idx=["# Frank automated full-page evidence","", "Browser: Playwright WebKit (not Safari.app)",
             "All sources: SYNTHETIC QA, not real balances or trade approvals","",
             "| File | Test scene | UTC |", "|---|---|---|"]
        for im in result["images"]:
            idx.append("| "+im["file"]+" | "+im["description"]+" | "+im["utc"]+" |")
        (folder/"index.md").write_text("\n".join(idx)+"\n")
        (folder/"SHA256SUMS.txt").write_text("\n".join(sha(p)+"  "+p.name for p in sorted(folder.iterdir()) if p.is_file())+"\n")
        count=archive(folder,zip_file)
        print(json.dumps({"status":result["status"],"zip_file":str(zip_file),
            "screenshots":count,"source_tree_sha":TREE,"errors":errors,
            "browser":"Playwright WebKit (not Safari.app)"},ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__=="__main__":
    main()
