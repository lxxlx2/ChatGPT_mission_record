"""G0-A read-only inventory of existing local Frank evidence. No RPC, no network, no writes.

Usage: python3 g0a_inventory.py
Opens every SQLite with mode=ro and reads the study JSON from the repo.
"""
import collections, json, os, sqlite3, datetime as dt

HOME = os.path.expanduser("~")
RUNTIME_DB = f"{HOME}/Library/Application Support/FrankMeme/release-backups/mission-loop-20261012T145714Z-6720/forward.sqlite"
FM3_DB = "/Users/jerson/Documents/ChatGPT/crypto-monitor-fm3-evidence-20261001/frank/shadow/forward.sqlite"
RPC_CACHE = "/Users/jerson/Documents/ChatGPT/frank-fomo-rpc-cache"
STUDY = os.path.join(os.path.dirname(__file__), "..", "evidence", "frank-trade-coverage-sol-usdt-complex-2026-10-04.json")

def ro(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)

def utc(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()

out = {}

# 1. Study JSON (archived, J0 baseline and M3 model)
s = json.load(open(STUDY))
out["study_J0_baseline"] = s["baseline_classifications"]
out["study_history"] = {k: s["history"][k] for k in ("usable_signatures", "classification_counts", "start", "end", "coverage")}
out["study_M3_signals"] = dict(collections.Counter(x["signal_type"] for x in s["models"]["M3"]["signals"]))
out["study_M3_distinct_mints"] = len({x["mint"] for x in s["models"]["M3"]["signals"]})
out["study_M3_distinct_episodes"] = len({x["episode_id"] for x in s["models"]["M3"]["signals"]})
out["study_price_receipts"] = {"count": len(s["price_receipts"]), "source": s["price_receipts"][0]["source"]}
out["study_SOL_case_directions"] = dict(collections.Counter(c["direction"] for c in s["SOL"]["cases"]))
out["study_per_signature_direction_list_in_json"] = False

# 2. Runtime forward.sqlite snapshot 2026-10-12 (window 2026-10-02..10-12)
c = ro(RUNTIME_DB)
rows = c.execute("select side, signature, mint, episode_id, block_time from trades").fetchall()
buy_like = {"BUY", "ADD", "REENTRY"}
out["runtime_trade_rows"] = len(rows)
out["runtime_side_counts"] = dict(collections.Counter(r[0] for r in rows))
out["runtime_BUY_signatures"] = len({r[1] for r in rows if r[0] in buy_like})
out["runtime_SELL_signatures"] = len({r[1] for r in rows if r[0] not in buy_like})
out["runtime_BUY_episodes"] = len({r[3] for r in rows if r[0] in buy_like})
out["runtime_BUY_mints"] = len({r[2] for r in rows if r[0] in buy_like})
out["runtime_signature_classes"] = dict(collections.Counter(
    json.loads(b).get("classification") for (b,) in c.execute("select body from signatures")))
out["runtime_window_utc"] = [utc(min(r[4] for r in rows)), utc(max(r[4] for r in rows))]
out["runtime_price_fields"] = "none: trades.body has quote_amount_raw and token_amount_raw only"
out["runtime_signals"] = c.execute("select signal_type, count(*) from signals group by 1").fetchall()

# 3. fm3 shadow raw evidence (2026-10-03..04) and cross-check with runtime BUY signatures
f = ro(FM3_DB)
fm = {sig: json.loads(ej) for sig, ej in f.execute("select signature, evidence_json from frank_transactions")}
out["fm3_raw_transactions"] = len(fm)
out["fm3_mechanical"] = dict(collections.Counter(v.get("mechanical_classification") for v in fm.values()))
out["fm3_meme_facts_with_usd"] = sum(
    1 for (b,) in f.execute("select body from meme_facts")
    if json.loads(b)["USD_estimate"]["value"] is not None)
out["fm3_meme_facts"] = f.execute("select count(*) from meme_facts").fetchone()[0]
buy_sigs = {r[1] for r in rows if r[0] in buy_like}
out["runtime_BUY_sigs_present_in_fm3_raw"] = len(buy_sigs & set(fm))

# 4. RPC cache of raw transactions (fomo cache)
import glob
cache = glob.glob(f"{RPC_CACHE}/*/*.json")
bts = [json.load(open(p))["tx"]["blockTime"] for p in cache]
out["rpc_cache_raw_tx"] = len(cache)
out["rpc_cache_window_utc"] = [utc(min(bts)), utc(max(bts))]
out["rpc_cache_has_price_series"] = False

print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
