#!/usr/bin/env python3
"""Offline-safe, read-only GMGN Top Traders research; NEVER a production trading signal."""
import argparse, csv, datetime, json, os, pathlib, re, shutil, subprocess, sys, time

# Exact BSC ERC20 contract IDs; do not merge homonymous tokens.
TOKENS = [
 ("我踏马来了","0xc51a9250795c0186a6fb4a7d20a90330651e4444",2026),
 ("龙虾","0xeccbb861c0dda7efd964010085488b69317e4444",2026),
 ("牛来","0xbeea1d618e533a387d941f58a7d4c9b7bd377777",2026),
 ("MARSCOIN","0xfe189e97832da1573e4e4ffc3a15c7777",2026),
 ("CHEEMS","0x0df0587216a4a1bb7d5082fdc491d93d2dd4b413",2024),
 ("BOB","0x51363f073b1e4920fda7aa9e9d84ba97ede1560e",2024),
 ("TST","0x86bb94ddd16efc8bc58e6b056e8df71d9e666429",2025),
 ("MUBARAK","0x5c85d6c6825ab4032337f11ee92a72df936b46f6",2025),
 ("TUT","0xcaae2a2f939f51d97cdfa9a86e79e3f085b799f3",2025),
 ("BROCCOLI714","0x6d5ad1592ed9d6d1df9b93c793ab759573ed6714",2025),
 ("BROCCOLIF3B","0x12b4356c65340fb02cdff01293f95febb1512f3b",2025),
 ("SIREN","0x997a58129890bbda032231a52ed1ddc845fc18e1",2025),
 ("BANANAS31","0x3d4f0513e8a29669b960f9dbca61861548a9a760",2025),
 ("BULLA","0x595e21b20e78674f8a64c1566a20b2b316bc3511",2025),
 ("4","0x0a43fc31a73013089df59194872ecae4cae14444",2025),
 ("GIGGLE","0x20d6015660b3fe52e6690a889b5c51f69902ce0e",2025),
 ("币安人生","0x924fa68a0fc644485b8df8abfa0a41c2e7744444",2025),
 ("哈基米","0x82ec31d69b3c289e541b50e30681fd1acad24444",2025),
 ("BUBB","0xd5369a3cac0f4448a9a96bb98af9c887c92fc37b",2025),
]
PUBLIC_TEST_KEY="gmgn_solbscbaseethmonadtron" # GMGN official documentation, TEST only.
ADDR=re.compile(r"^0x[0-9a-f]{40}$")

def unwrap(obj):
    if isinstance(obj,list): return obj
    if not isinstance(obj,dict): raise ValueError("JSON root not object")
    if obj.get("code") not in (None,0,"0",200,"200"):
        raise ValueError("GMGN non-success status: "+str(obj.get("code")))
    for k in ("data","result"):
        if isinstance(obj.get(k),(dict,list)):
            try: return unwrap(obj[k])
            except ValueError: pass
    for k in ("list","items","traders"):
        if isinstance(obj.get(k),list): return obj[k]
    raise ValueError("No trader list in GMGN response")

def num(x):
    try:
        if x is None or x=="":return None
        return float(x)
    except (ValueError,TypeError):return None

def rowsfile(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: rows=[{"status":"NO_DATA"}]
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def load_raw(root,label,kind):
    path=root/"raw"/(label+"_"+kind+".json")
    if not path.exists(): return []
    p=json.loads(path.read_text(encoding="utf-8"))
    if p.get("contract") != next(c for n,c,y in TOKENS if n==label):
        raise ValueError("Cached token contract mismatch: "+label)
    return unwrap(p["response"])

def collect(root,refresh=False):
    cli=shutil.which("gmgn-cli")
    if not cli: raise RuntimeError("Official gmgn-cli not installed; cannot claim ranking collected")
    env=os.environ.copy()
    env.setdefault("GMGN_API_KEY",PUBLIC_TEST_KEY)
    root.joinpath("raw").mkdir(parents=True,exist_ok=True)
    errors=[]
    for label,contract,year in TOKENS:
        for metric in ("profit","sell_volume_cur"):
            path=root/"raw"/(label+"_"+metric+".json")
            if path.exists() and not refresh: continue
            cmd=[cli,"token","traders","--chain","bsc","--address",contract,
                 "--order-by",metric,"--direction","desc","--limit","100","--raw"]
            res=subprocess.run(cmd,capture_output=True,text=True,timeout=100,env=env,check=False)
            if res.returncode:
                # Error messages can contain secrets; do not export raw stderr.
                errors.append({"token":label,"sort":metric,"exit_code":res.returncode})
                if "429" in res.stderr or "RATE_LIMIT" in res.stderr:
                    print("GMGN rate limit hit; STOP without further retries",file=sys.stderr)
                    root.joinpath("collection_errors.json").write_text(json.dumps(errors))
                    return 2
                continue
            try:
                response=json.loads(res.stdout)
                found=unwrap(response)
                if not all(isinstance(x,dict) for x in found):raise ValueError("Bad list")
                path.write_text(json.dumps({"contract":contract,"year":year,
                    "label":label,"sort":metric,"asof_utc":datetime.datetime.now(
                    datetime.timezone.utc).isoformat(),"response":response},
                    ensure_ascii=False,indent=2),encoding="utf-8")
                print("Fetched",label,metric,len(found),flush=True)
            except (ValueError,TypeError):
                errors.append({"token":label,"sort":metric,"error":"Bad response shape"})
            time.sleep(1.5)
    root.joinpath("collection_errors.json").write_text(json.dumps(errors,indent=2))
    return 1 if errors else 0

def analyze(root):
    bytoken=[];coverage=[]
    for label,contract,year in TOKENS:
        persons={}
        metrics=[]
        for metric in ("profit","sell_volume_cur"):
            try: arr=load_raw(root,label,metric)
            except (ValueError,KeyError) as e:
                print("Invalid cache",label,metric,str(e),file=sys.stderr)
                continue
            if not arr:continue
            metrics.append(metric)
            for record in arr:
                address=str(record.get("address","")).lower()
                if not ADDR.fullmatch(address): continue
                if address not in persons: persons[address]=record
        for wallet,entry in persons.items():
            buys=num(entry.get("buy_tx_count_cur"))
            ins=num(entry.get("history_transfer_in_amount"))
            realized=num(entry.get("realized_profit"))
            last=num(entry.get("last_active_timestamp"))
            flags=[]
            if entry.get("addr_type")==2:flags.append("EXCHANGE_OR_POOL")
            if not buys or buys<=0:flags.append("NO_DIRECT_BUY")
            if ins and ins>0:flags.append("TRANSFER_IN_COST_UNVERIFIED")
            if realized is None:flags.append("REALIZED_PNL_MISSING")
            if entry.get("is_suspicious"):flags.append("PROVIDER_SUSPICIOUS")
            bytoken.append({"token":label,"year":year,"contract":contract,
                "wallet":wallet,"reported_realized_usd":realized,
                "reported_total_profit_usd":num(entry.get("profit")),
                "buy_tx":buys,"sell_tx":num(entry.get("sell_tx_count_cur")),
                "transfer_in_qty":ins,"buy_cost_usd":num(entry.get("history_bought_cost")),
                "last_token_activity_utc":last,"flags":";".join(flags),
                "provisional_realized_winner":bool(realized is not None and realized>0
                    and buys and buys>0 and not flags)})
        coverage.append({"token":label,"contract":contract,"year":year,
            "vendor_sort_files":";".join(metrics),"unique_wallets_in_sample":len(persons),
            "all_dex_history_verified":False,"historical_profit_rank_exhaustive":False})
    per_wallet={}
    for row in bytoken: per_wallet.setdefault(row["wallet"],[]).append(row)
    cross=[]
    for addr,data in per_wallet.items():
        wins=[r for r in data if r["provisional_realized_winner"]]
        cross.append({"wallet":addr,"sampled_tokens":len(data),
             "tokens":";".join(r["token"] for r in data),
             "provisional_winning_tokens":len(wins),
             "winning_tokens":";".join(r["token"] for r in wins),
             "winning_2026_tokens":sum(r["year"]==2026 for r in wins),
             "subset_vendor_realized_profit_usd":sum(r["reported_realized_usd"] for r in wins),
             "latest_token_activity_utc":max((r["last_token_activity_utc"] or 0) for r in data),
             "latest_activity_may_be_transfer":True,
             "independent_pnl_verified":False,"signal":"OBSERVE_ONLY"})
    cross.sort(key=lambda x:(-x["winning_2026_tokens"],-x["provisional_winning_tokens"],
                             -x["subset_vendor_realized_profit_usd"]))
    output=root/"analysis"
    rowsfile(output/"coverage.csv",coverage)
    rowsfile(output/"token_trader_samples.csv",bytoken)
    rowsfile(output/"cross_token_wallets.csv",cross)
    summary={"tokens":len(TOKENS),"tokens_with_vendor_rows":sum(x["unique_wallets_in_sample"]>0 for x in coverage),
       "unique_wallets_sampled":len(cross),"cross_token_wallets_in_samples":sum(x["sampled_tokens"]>=2 for x in cross),
       "provisional_repeated_winners":sum(x["provisional_winning_tokens"]>=2 for x in cross),
       "FULL_HISTORICAL_TOP100_PNL_VERIFIED":False,
       "SIGNAL":"OBSERVE_ONLY","PRODUCTION_TRADING":"NO_GO",
       "note":"GMGN vendor-reported PnL is unverified; early trades/funding/true controlled clusters and last 30d actual swaps require direct on-chain corroboration."}
    output.joinpath("summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    return 0 if summary["tokens_with_vendor_rows"] else 3

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("both","collect","analyze"),default="both")
    p.add_argument("--root",type=pathlib.Path,default=pathlib.Path("bsc_meme_top100"))
    p.add_argument("--refresh",action="store_true")
    a=p.parse_args()
    code=collect(a.root,a.refresh) if a.mode in ("both","collect") else 0
    if a.mode in ("both","analyze"):code=analyze(a.root) or code
    return code

if __name__=="__main__":sys.exit(main())
