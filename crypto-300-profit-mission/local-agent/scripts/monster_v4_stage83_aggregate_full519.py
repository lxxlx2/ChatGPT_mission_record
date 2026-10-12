#!/usr/bin/env python3
"""Aggregate exactly 36 Stage83 genuine source shards with pinned old D0 + labels."""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

try:
    import monster_v4_stage81_continuous3m_official_pilot as st81
    import monster_v4_stage83_full519_official_continuous as st83
    from monster_v4_stage80_dual_entry_core import sha_blob, utc_ms
except ImportError:
    from scripts import monster_v4_stage81_continuous3m_official_pilot as st81
    from scripts import monster_v4_stage83_full519_official_continuous as st83
    from scripts.monster_v4_stage80_dual_entry_core import sha_blob, utc_ms

EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"
OLD = EVIDENCE / "monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
OLD_SHA = "ad7544f97e8a0d6c1f2635aa54052cca42d08cf1"
STAGE81 = EVIDENCE / "monster_stage81_official_12_continuous3m_source_replay_summary_20261013.json"
SCHEMA = "MONSTER_STAGE83_REAL519_STAGE52_ANCHOR_AND_STAGE81_PARITY_V1"
MS5 = 5 * 60000
D24 = 24 * 3600000
DAY_SLOTS = 42


def load_old_labels():
    raw = OLD.read_bytes()
    if sha_blob(raw) != OLD_SHA:
        raise ValueError("STAGE83_ORIGINAL_STAGE52_BLOB_SOURCE_DRIFT")
    items = [json.loads(s) for s in raw.decode("utf-8").splitlines() if s.strip()]
    if len(items) != 5400 or len({(x["date"], x["symbol"]) for x in items}) != 5400:
        raise ValueError("STAGE83_WRONG_ORIGINAL5400_FUTURES_SOURCE")
    return {(x["date"], x["symbol"]): x for x in items}


def pre5(event: str | None, cross: str | None) -> bool:
    return bool(event and cross and utc_ms(event) + MS5 <= utc_ms(cross))


def shard_files(root: Path) -> list[Path]:
    return sorted(root.glob("monster-stage83-*.json"))


def read_shards(root: Path) -> list[dict]:
    files = shard_files(root)
    if len(files) != 36:
        raise ValueError("STAGE83_NOT_ALL36_SOURCE_SHARDS " + str(len(files)))
    shards, seen, out = set(), set(), []
    for path in files:
        batch = json.loads(path.read_text())
        if batch.get("schema") != st83.SCHEMA:
            raise ValueError("STAGE83_SHARD_WRONG_SCHEMA")
        key = (batch["date"], batch["shard"])
        if key in shards or batch["date"] not in st83.DATES or batch["shard"] not in range(6):
            raise ValueError("STAGE83_UNEXPECTED_DATE_SHARD")
        shards.add(key)
        original = st83.selected_for(*key)
        expect = {(x["date"], x["symbol"]) for x in original}
        got = {(x["date"], x["symbol"]) for x in batch["rows"]}
        if got != expect or len(batch["rows"]) != len(expect):
            raise ValueError("STAGE83_SHARD_ORIGINAL_D0_LOST_OR_ADDED " + str(key))
        if batch["original_Stage64_complete_coin_dates"] != len(expect):
            raise ValueError("STAGE83_SHARD_WRONG_ORIGINAL_COUNT")
        for x in batch["rows"]:
            id_ = (x["date"], x["symbol"])
            if id_ in seen:
                raise ValueError("STAGE83_DUPLICATE_GLOBAL_CASE")
            seen.add(id_)
            if x["source_status"] not in (st83.GOOD, st83.CENSORED):
                raise ValueError("STAGE83_FORBIDDEN_SUCCESS_WITH_UNKNOWN_STATUS")
        out += batch["rows"]
    if len(out) != 519 or shards != {(d, s) for d in st83.DATES for s in range(6)}:
        raise ValueError("STAGE83_MISSING_EXPECTED_519_OR_SHARD")
    all_519 = {(x["date"], x["symbol"]) for x in st81.load_population()}
    if seen != all_519:
        raise ValueError("STAGE83_519_ORIGINAL_WATCH_IDENTITY_CHANGED")
    return sorted(out, key=lambda x: (x["date"], x["symbol"]))


def aggregate(rows: list[dict], original: dict, *,
              stage81: dict | None = None) -> tuple[dict, list[dict]]:
    if len(rows) != 519:
        raise ValueError("STAGE83_FULL519_ONLY")
    preserved = {}
    data = []
    for source in rows:
        key = source["date"], source["symbol"]
        old = original[key]
        if old["source_status"] != "COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4":
            raise ValueError("STAGE83_PREVIOUSLY_VERIFIED_D0_BECAME_UNKNOWN")
        if (not old["WATCH_UTC"] or old["WATCH_UTC"][0] != source["first_D0_UTC"] or
            bool(old["hourly_gt2x"]) != bool(source["calendar_anchor_GT2x_EVALUATION_ONLY"])):
            raise ValueError("STAGE83_OLD_SOURCE_D0_LABEL_OR_TIME_CHANGED")
        for threshold in (2, 5, 10):
            if old["hourly_gt" + str(threshold) + "x"] and not (
                old["first_true_2x_HIGH_minute_UTC"] if threshold == 2
                else old.get("first_real_1m_HIGH_gt" + str(threshold) + "x_UTC")):
                raise ValueError("STAGE83_MISSING_HISTORIC_GT_FIRST_CROSS")
        first2 = old["first_true_2x_HIGH_minute_UTC"]
        first5 = old.get("first_real_1m_HIGH_gt5x_UTC")
        first10 = old.get("first_real_1m_HIGH_gt10x_UTC")
        complete = source["source_status"] == st83.GOOD
        d1 = source["first_D1_UTC"] if complete else None
        label = {
            "date": source["date"], "symbol": source["symbol"],
            "source_status": source["source_status"], "identity": source["identity"],
            "D0_FIRST_UTC": source["first_D0_UTC"],
            "D1_FIRST_UTC": d1,
            "D1_PATH": source["first_D1_path"] if complete else None,
            "historical_anchor_GT2": bool(old["hourly_gt2x"]),
            "historical_anchor_GT5": bool(old["hourly_gt5x"]),
            "historical_anchor_GT10": bool(old["hourly_gt10x"]),
            "true_first_2x_HIGH_UTC_EVALUATION_ONLY": first2,
            "true_first_5x_HIGH_UTC_EVALUATION_ONLY": first5,
            "true_first_10x_HIGH_UTC_EVALUATION_ONLY": first10,
            "D0_at_least_5m_before_2x": pre5(source["first_D0_UTC"], first2),
            "D1_at_least_5m_before_2x": pre5(d1, first2) if complete else None,
            "D1_at_least_5m_before_5x": pre5(d1, first5) if complete else None,
            "D1_at_least_5m_before_10x": pre5(d1, first10) if complete else None,
            "D0_PRESERVED": True,
            "source_missing_official_day": source.get("missing_official_day"),
            "source_day_sha256_receipts": source.get("official_daily_publisher_SHA_receipts")
                                         or source.get("publisher_sha_verified_prefix", []),
        }
        if label["D0_at_least_5m_before_2x"] and not label["historical_anchor_GT2"]:
            raise ValueError("STAGE83_FALSE_D0_GT2_ANCHOR")
        data.append(label)
        preserved[key] = source
    if stage81 is not None:
        if len(stage81["cases"]) != 12:
            raise ValueError("STAGE83_STAGE81_PARITY_EXPECTS_12")
        for old in stage81["cases"]:
            x = preserved[(old["date"], old["symbol"])]
            if x["source_status"] != st83.GOOD or x["first_D1_UTC"] != old["d1_first_UTC"] \
                    or x["first_D1_path"] != old["d1_path"]:
                raise ValueError("STAGE83_STAGE81_EXACT_D1_REPLAY_CLOCK_DIFF " + old["symbol"])
    valid = [x for x in data if x["source_status"] == st83.GOOD]
    cens = [x for x in data if x["source_status"] == st83.CENSORED]
    counts = collections.Counter()
    for x in valid:
        if x["D1_FIRST_UTC"]:
            start = utc_ms(x["date"] + "T06:00:00Z")
            slot = (utc_ms(x["D1_FIRST_UTC"]) - start) // D24
            if slot not in range(7):
                raise ValueError("STAGE83_D1_OUTSIDE_WINDOW")
            counts[(x["date"], slot)] += 1
    all_slots = [{"date": d, "slot": n, "D1_candidates": counts[(d,n)]}
                 for d in st83.DATES for n in range(7)]
    targets = [x for x in data if x["historical_anchor_GT2"] and x["D0_at_least_5m_before_2x"]]
    evaluated = [x for x in targets if x["source_status"] == st83.GOOD]
    keep = [x for x in evaluated if x["D1_at_least_5m_before_2x"]]
    missing = [x for x in targets if x["source_status"] == st83.CENSORED]
    non2 = [x for x in valid if not x["historical_anchor_GT2"]]
    huge = [x for x in data if x["historical_anchor_GT5"] or x["historical_anchor_GT10"]]
    load_avg = len([x for x in valid if x["D1_FIRST_UTC"]]) / DAY_SLOTS
    load_peak = max(counts.values(), default=0)
    gates = {
        "G2_retention_at_least_80_percent_for_28": (
            len(missing) == 0 and len(targets) >= 20 and 100*len(keep) >= 80*len(targets)),
        "G3_mean_at_most_5": load_avg <= 5,
        "G3_daily_peak_at_most_12": load_peak <= 12,
        "G0_all519_source_complete": len(cens) == 0,
        "G0_all519_confirmed_as_crypto": all(
            x["identity"] == "CONFIRMED_CRYPTO_POINT_IN_TIME" for x in data),
    }
    summary = {
        "schema": SCHEMA,
        "population":"STAGE64_EXPOSED_USDM_MIXED_INSTRUMENT_519_FIRST_D0",
        "attempted": len(data), "official_valid":len(valid), "source_censored":len(cens),
        "historical_GT2_population":sum(x["historical_anchor_GT2"] for x in data),
        "original_D0_2x_early5":len(targets),
        "original_D0_2x_early5_scored_complete":len(evaluated),
        "original_D0_2x_early5_censored":len(missing),
        "D1_retain_early5_GT2":len(keep),
        "D1_recall_early5_fraction_of_full_original_2x":(
            len(keep)/len(targets) if targets else None),
        "D1_recall_early5_fraction_of_scored_2x":(
            len(keep)/len(evaluated) if evaluated else None),
        "D1_total_first_upgrades":sum(bool(x["D1_FIRST_UTC"]) for x in valid),
        "D1_direct":sum(x["D1_PATH"] == "DIRECT_AT_FIRST_D0" for x in valid),
        "D1_reignition":sum(x["D1_PATH"] == "REIGNITION_AFTER_D0" for x in valid),
        "D1_non2x_upgrades":sum(bool(x["D1_FIRST_UTC"]) for x in non2),
        "historical_GT5_cases":len([x for x in data if x["historical_anchor_GT5"]]),
        "historical_GT10_cases":len([x for x in data if x["historical_anchor_GT10"]]),
        "all_major_cases":huge,
        "all42_real_UTC06_day_slots":all_slots,
        "daily_average_including_zero_days":round(load_avg,4),
        "peak_UTC06_day":load_peak,
        "source_status_counts":dict(collections.Counter(x["source_status"] for x in data)),
        "identity_status_counts":dict(collections.Counter(x["identity"] for x in data)),
        "gates":gates,
        "g2_exposed_historical":(
            "CENSORED_UNSCORABLE" if missing else
            "REJECTED_EXPOSED" if not gates["G2_retention_at_least_80_percent_for_28"] else
            "PASS_EXPOSED_ONLY"),
        "g3_exposed_historical":(
            "PARTIAL_CENSORED" if cens else
            "REJECTED_EXPOSED" if not (gates["G3_mean_at_most_5"] and gates["G3_daily_peak_at_most_12"])
            else "PASS_EXPOSED_ONLY"),
        "market_scope": "MIXED_USDM_CRYPTO_CLASSIFICATION_PARTIAL",
        "independent_future_OOS": "NOT_DONE",
        "actual_executable_net_profit": "UNKNOWN",
        "other_ai_independent_review": "NOT_DONE",
        "deployment": "NO_GO", "Gmail": "OFF",
        "autotrade": "NO_GO", "Frank": "UNCHANGED",
    }
    return summary, data


def selftest():
    assert pre5("2026-10-13T00:00:00Z","2026-10-13T00:05:00Z")
    assert not pre5("2026-10-13T00:00:00Z","2026-10-13T00:04:00Z")
    assert not pre5(None,"2026-10-13T00:05:00Z")
    assert len({(d,s) for d in st83.DATES for s in range(6)}) == 36
    print("STAGE83_GLOBAL_SCORING_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--artifact-dir",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.artifact_dir or not a.out:
        p.error("--artifact-dir and --out required")
    rows=read_shards(a.artifact_dir)
    original=load_old_labels()
    previous=json.loads(STAGE81.read_text())
    summary, detailed=aggregate(rows,original,stage81=previous)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage83_all519_source_and_D1_result.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in detailed))
    (a.out/"monster_stage83_all519_D0_D1_official_continuous_summary.json").write_text(
        json.dumps(summary,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE83_GLOBAL_519_RESULT "+json.dumps({
        k:summary[k] for k in ("attempted","official_valid","source_censored",
                               "D1_total_first_upgrades","D1_direct","D1_reignition",
                               "original_D0_2x_early5","D1_retain_early5_GT2",
                               "D1_non2x_upgrades","daily_average_including_zero_days",
                               "peak_UTC06_day","g2_exposed_historical",
                               "g3_exposed_historical")},sort_keys=True))


if __name__=="__main__":
    main()
