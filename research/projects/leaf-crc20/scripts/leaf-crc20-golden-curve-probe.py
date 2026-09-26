#!/usr/bin/env python3
import json, re, shutil, subprocess, tempfile, time
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

ORIGIN="https://crc.garden"
PAGES=["/","/activity","/legal/terms?lang=en","/legal/privacy?lang=en","/robots.txt","/sitemap.xml"]
KEYWORDS=["golden","curve","quote","allocation","allocate","indexer","mint","crc-20","leaf","activity","balance","supply","api","rpc","graphql","trpc","supabase","fetch(","axios"]
OUT=Path("leaf_crc20_golden_curve_probe_report.json")
SNIPPETS_OUT=Path("leaf_crc20_golden_curve_relevant_snippets.txt")
ASSET_DIR=Path("leaf_crc20_crc_garden_assets")
UA="Mozilla/5.0 leaf-crc20-research/1.0"

def fetch(url,timeout=25):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return {"url":r.geturl(),"status":getattr(r,"status",200),"content_type":r.headers.get("Content-Type",""),"body":r.read()}

def txt(b): return b.decode("utf-8","replace")

def extract_assets(html,base):
    urls=set()
    pat=r'(?:src|href)\s*=\s*["\']([^"\']+)["\']'
    for m in re.finditer(pat,html,re.I):
        u=urllib.parse.urljoin(base,m.group(1)); p=urllib.parse.urlparse(u)
        if p.netloc=="crc.garden" and (p.path.endswith(".js") or "/_next/static/" in p.path or "/assets/" in p.path):
            urls.add(u)
    return sorted(urls)

def extract_urlish(text):
    out=set()
    for m in re.finditer(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+",text):
        out.add(m.group(0).rstrip(')"\',;'))
    for m in re.finditer(r'["\'](\/[A-Za-z0-9_./?&=%:{}\[\]-]{2,220})["\']',text):
        out.add(urllib.parse.urljoin(ORIGIN,m.group(1)))
    return out

def snippets(text,source,radius=240,cap=180):
    low=text.lower(); out=[]; seen=set()
    for kw in KEYWORDS:
        pos=0
        while True:
            i=low.find(kw.lower(),pos)
            if i<0: break
            s=re.sub(r"\s+"," ",text[max(0,i-radius):min(len(text),i+len(kw)+radius)])
            k=s[:180]
            if k not in seen:
                seen.add(k); out.append({"source":source,"keyword":kw,"snippet":s})
                if len(out)>=cap: return out
            pos=i+max(1,len(kw))
    return out

def parse_url(u):
    try:
        return urllib.parse.urlparse(u)
    except (ValueError, TypeError):
        return None

def interesting(u):
    p=parse_url(u)
    if p is None: return False
    s=str(u).lower()
    if p.netloc and p.netloc!="crc.garden":
        return any(k in s for k in ["supabase","graphql","api","index","rpc"])
    return any(k in s for k in ["/api","quote","allocation","alloc","index","activity","balance","supply","mint","curve","golden","state","graphql","trpc"])

def safe_get(u):
    p=parse_url(u)
    if p is None: return False
    s=str(u).lower()
    if p.scheme not in ("http","https") or p.netloc!="crc.garden": return False
    if any(x in s for x in ["{","}","[","]","broadcast","submit","sign","claim","swap"]): return False
    if p.path.endswith((".js",".css",".png",".jpg",".svg",".woff",".ico")): return False
    return interesting(u)

def find_chrome():
    for c in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary","/Applications/Chromium.app/Contents/MacOS/Chromium"]:
        if Path(c).exists(): return c
    for n in ["google-chrome","chrome","chromium","chromium-browser"]:
        p=shutil.which(n)
        if p: return p
    return None

def collect_urls(obj,out):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if isinstance(v,str):
                if "crc.garden" in v or (k.lower()=="url" and v.startswith("http")): out.add(v)
            else: collect_urls(v,out)
    elif isinstance(obj,list):
        for x in obj: collect_urls(x,out)

def chrome_capture(chrome):
    result={"chrome":chrome,"runs":[],"urls":[]}; all_urls=set()
    for path in ["/","/activity"]:
        with tempfile.TemporaryDirectory(prefix="leaf-crc20-chrome-") as td:
            netlog=Path(td)/"netlog.json"; profile=Path(td)/"profile"; url=urllib.parse.urljoin(ORIGIN,path)
            cmd=[chrome,"--headless=new","--disable-gpu","--no-first-run","--no-default-browser-check",f"--user-data-dir={profile}",f"--log-net-log={netlog}","--net-log-capture-mode=Everything","--virtual-time-budget=7000","--dump-dom",url]
            try:
                p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
                run={"url":url,"returncode":p.returncode,"stderr_tail":p.stderr.decode("utf-8","replace")[-1500:]}
                if netlog.exists():
                    try:
                        obj=json.loads(netlog.read_text(encoding="utf-8",errors="replace")); urls=set(); collect_urls(obj,urls)
                        urls={u for u in urls if "crc.garden" in u}; all_urls.update(urls); run["crc_garden_url_count"]=len(urls)
                    except Exception as e: run["netlog_parse_error"]=repr(e)
                result["runs"].append(run)
            except Exception as e: result["runs"].append({"url":url,"error":repr(e)})
    result["urls"]=sorted(all_urls); return result

def main():
    ASSET_DIR.mkdir(exist_ok=True)
    report={"origin":ORIGIN,"pages":[],"assets":[],"candidate_urls":[],"safe_get_probes":[],"chrome_network":None,"errors":[]}
    sn=[]; assets=set(); urlish=set()
    print("[1/5] fetch pages")
    for path in PAGES:
        u=urllib.parse.urljoin(ORIGIN,path)
        try:
            r=fetch(u); t=txt(r["body"])
            report["pages"].append({"url":r["url"],"status":r["status"],"content_type":r["content_type"],"bytes":len(r["body"])})
            sn.extend(snippets(t,r["url"],cap=80)); urlish.update(extract_urlish(t))
            if "html" in r["content_type"].lower() or "<html" in t.lower(): assets.update(extract_assets(t,r["url"]))
        except Exception as e: report["errors"].append({"url":u,"error":repr(e)})
    print(f"[2/5] fetch {len(assets)} assets")
    for i,u in enumerate(sorted(assets),1):
        try:
            r=fetch(u); t=txt(r["body"]); name=re.sub(r"[^A-Za-z0-9._-]+","_",urllib.parse.urlparse(u).path.strip("/"))[-180:] or f"asset_{i}.txt"
            (ASSET_DIR/name).write_bytes(r["body"])
            report["assets"].append({"url":u,"status":r["status"],"content_type":r["content_type"],"bytes":len(r["body"]),"saved_as":str(ASSET_DIR/name)})
            urlish.update(extract_urlish(t)); sn.extend(snippets(t,u,cap=180))
        except Exception as e: report["errors"].append({"url":u,"error":repr(e)})
        if i%10==0 or i==len(assets): print(f"  {i}/{len(assets)}")
    print("[3/5] chrome passive network")
    chrome=find_chrome()
    report["chrome_network"]=chrome_capture(chrome) if chrome else {"available":False}
    if chrome: urlish.update(report["chrome_network"].get("urls",[]))
    candidates=sorted({u for u in urlish if interesting(u)}); report["candidate_urls"]=candidates
    print(f"[4/5] safe GET candidates {sum(safe_get(u) for u in candidates)}")
    for u in candidates:
        if not safe_get(u): continue
        try:
            r=fetch(u,15); b=txt(r["body"])
            report["safe_get_probes"].append({"url":r["url"],"status":r["status"],"content_type":r["content_type"],"bytes":len(r["body"]),"body_prefix":b[:2000]})
        except urllib.error.HTTPError as e: report["safe_get_probes"].append({"url":u,"status":e.code,"error":str(e)})
        except Exception as e: report["safe_get_probes"].append({"url":u,"error":repr(e)})
        time.sleep(.05)
    uniq=[]; seen=set()
    for x in sn:
        k=(x["source"],x["snippet"])
        if k not in seen: seen.add(k); uniq.append(x)
    report["relevant_snippet_count"]=len(uniq)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    with SNIPPETS_OUT.open("w",encoding="utf-8") as f:
        for x in uniq: f.write(f"\n=== {x['source']} | {x['keyword']} ===\n{x['snippet']}\n")
    print("[5/5] done")
    print(OUT); print(SNIPPETS_OUT); print(ASSET_DIR)
    print("candidate_urls",len(candidates),"snippets",len(uniq))
if __name__=="__main__": main()
