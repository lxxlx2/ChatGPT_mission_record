#!/usr/bin/env python3
"""Stage127: frozen, research-only 519 first-D0 as-of chronological priority.

Never a buy model, order engine, sender or forward OOS proof.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path

SOURCE_KEYS = (
    "ret60_pct", "quote15_USDT", "trade_count15",
    "quote15_normalized_prev45", "taker_buy_share15", "taker_buy_share60",
)
SIX_ANCHORS = ("2025-01-30", "2025-06-02", "2025-08-01", "2025-10-02", "2026-06-21", "2026-07-28")
SOURCE_BLOBS = {
    "stage64": "8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a",
    "stage83": "c76b3a137c8dbe56feed3a79a63adcc0752f5e2e",
}
SCHEMA = "MONSTER_STAGE127_FROZEN_EXPOSED_FIRST_D0_WALKFORWARD_V1"
EPOCHS, LEARNING_RATE, L2 = 400, 0.2, 0.05


def as_float(val, name):
    try:
        d = Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("STAGE127_BAD_ASOF_FEATURE_" + name)
    if not d.is_finite():
        raise ValueError("STAGE127_NONFINITE_ASOF_FEATURE_" + name)
    return float(d)


def features(x):
    if not isinstance(x, dict) or any(k not in x for k in SOURCE_KEYS):
        raise ValueError("STAGE127_REQUIRED_ASOF_FEATURE_MISSING")
    ret, q, n, accel, share15, share60 = (as_float(x[k], k) for k in SOURCE_KEYS)
    if q < 0 or n < 0 or accel < 0 or not(0 <= share15 <= 1) or not (0 <= share60 <= 1):
        raise ValueError("STAGE127_ASOF_FEATURE_OUT_OF_DOMAIN")
    if n != int(n):
        raise ValueError("STAGE127_TRADE_COUNT_NOT_INTEGER")
    return (
        ret / 20,
        math.log1p(q),
        math.log1p(n),
        math.log1p(accel),
        share15,
        share15 - share60,
    )


def parse_utc(x):
    if not isinstance(x, str) or not x.endswith("Z"):
        raise ValueError("STAGE127_NON_UTC_D0")
    try:
        d = datetime.fromisoformat(x.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("STAGE127_INVALID_D0_TIME")
    return d


def day_bucket(anchor, observed):
    base = datetime.fromisoformat(anchor).replace(tzinfo=timezone.utc, hour=6)
    delta = observed - base
    if delta < timedelta(0) or delta >= timedelta(days=7):
        raise ValueError("STAGE127_D0_OUTSIDE_7DAY_UTC06_ANCHOR")
    return int(delta.total_seconds() // 86400)


def parse_inputs(stage64, stage83):
    if len(stage64) != 519 or len(stage83) != 519:
        raise ValueError("STAGE127_REQUIRE_ORIGINAL519_COMPLETE")
    right = {}
    for v in stage83:
        k = (v.get("date"), v.get("symbol"))
        if k in right:
            raise ValueError("STAGE127_DUPLICATE_STAGE83_KEY")
        if v.get("source_status") != "COMPLETE_OFFICIAL_PREFIX_SHA_VERIFIED_3M_48H" or type(v.get("D0_at_least_5m_before_2x")) is not bool:
            raise ValueError("STAGE127_UNVERIFIABLE_STAGE83_LABEL")
        right[k] = v
    out = []
    seen = set()
    for v in stage64:
        k = (v.get("date"), v.get("symbol"))
        if k in seen:
            raise ValueError("STAGE127_DUPLICATE_STAGE64_KEY")
        seen.add(k)
        if k not in right or v.get("source_status") != "COMPLETE_OFFICIAL_DAILY_USDM_61M_PUBLISHER_SHA_NO_FUTURE":
            raise ValueError("STAGE127_MISSING_SOURCE_PARITY")
        h = right[k]
        if v.get("first_D0_UTC") != h.get("D0_FIRST_UTC") or k[0] not in SIX_ANCHORS:
            raise ValueError("STAGE127_SOURCE_DATE_OR_D0_MISMATCH")
        if not v.get("publisher_SHA_receipts") or not h.get("source_day_sha256_receipts"):
            raise ValueError("STAGE127_SOURCE_SHA_PROVENANCE_MISSING")
        when = parse_utc(v["first_D0_UTC"])
        out.append({
            "anchor": k[0], "symbol": k[1], "venue": "BINANCE_USDM",
            "D0_UTC": v["first_D0_UTC"], "utc06_day_bucket": day_bucket(k[0], when),
            "asof_features": features(v["features_ASOF_ONLY"]),
            "evaluated_early5_2x": h["D0_at_least_5m_before_2x"],
            "original_D1_UTC_comparison_only": h.get("D1_FIRST_UTC"),
        })
    if set(right) != seen:
        raise ValueError("STAGE127_SOURCE_KEYS_INCOMPLETE")
    return sorted(out, key=lambda r:(r["anchor"], r["symbol"]))


def fit(train):
    n = len(train)
    positive = sum(int(r["evaluated_early5_2x"]) for r in train)
    if n < 30 or positive < 6 or n-positive < 10:
        return None
    x = [r["asof_features"] for r in train]
    width = len(SOURCE_KEYS)
    means = [sum(v[j] for v in x)/n for j in range(width)]
    scales = [z if z >= 1e-9 else 1.0 for z in ((sum((v[j]-means[j])**2 for v in x)/n)**0.5 for j in range(width))]
    def convert(vals):
        return [max(-6., min(6., (vals[j]-means[j])/scales[j])) for j in range(width)]
    xx = [convert(v) for v in x]
    ys = [float(r["evaluated_early5_2x"]) for r in train]
    weights = [0.]*width
    intercept = math.log((positive+1)/(n-positive+1))
    for _ in range(EPOCHS):
        ds = [0.]*width
        di = 0.
        for v,y in zip(xx, ys):
            score = intercept+sum(a*b for a,b in zip(v,weights))
            pred = sigmoid(score)
            error = pred-y
            di += error
            for j in range(width):
                ds[j] += error*v[j]
        for j in range(width):
            weights[j] -= LEARNING_RATE*(ds[j]/n+L2*weights[j])
        intercept -= LEARNING_RATE*(di/n)
    def score(row):
        v = convert(row["asof_features"])
        return sigmoid(intercept+sum(a*b for a,b in zip(v,weights)))
    train_scores = [score(r) for r in train]
    threshold = calibrate(train, train_scores)
    return {"score": score, "threshold": threshold, "train_n": n, "train_positives": positive, "weights": weights, "intercept": intercept,
            "normalizer_means": means, "normalizer_scales": scales}


def sigmoid(x):
    if x >= 0:
        return 1/(1+math.exp(-x))
    z = math.exp(x)
    return z/(1+z)


def burden(rows, decisions, dates):
    counts = defaultdict(int)
    for r, selected in zip(rows, decisions):
        if selected:
            counts[(r["anchor"], r["utc06_day_bucket"])] += 1
    buckets = [counts.get((d,day),0) for d in dates for day in range(7)]
    return {"attention_n":sum(buckets), "days":len(buckets), "per_day_mean":sum(buckets)/len(buckets) if buckets else 0,
            "peak_day":max(buckets) if buckets else 0, "daily_buckets":buckets}


def calibrate(train, scores):
    if not scores or len(scores) != len(train):
        raise ValueError("STAGE127_CALIBRATION_NO_COHORT")
    dates = sorted(set(r["anchor"] for r in train))
    candidates = [-1.0]+sorted(set(scores))
    for threshold in candidates:
        decisions = [p>threshold for p in scores]
        b = burden(train, decisions, dates)
        if b["per_day_mean"] <= 5 and b["peak_day"] <= 12:
            return threshold
    raise ValueError("STAGE127_NO_VALID_CALIBRATION")


def evaluate(rows):
    actual = tuple(sorted(set(r["anchor"] for r in rows)))
    if actual != SIX_ANCHORS:
        raise ValueError("STAGE127_WRONG_ANCHOR_COHORT")
    outcomes, fold_summary = [], []
    for date in SIX_ANCHORS:
        train = [r for r in rows if r["anchor"] < date]
        testing = [r for r in rows if r["anchor"] == date]
        model = fit(train)
        chosen = []
        for r in testing:
            p = None if model is None else model["score"](r)
            pick = bool(p is not None and p>model["threshold"])
            chosen.append(pick)
            outcomes.append({
                "anchor":date, "venue":r["venue"], "symbol":r["symbol"], "first_D0_UTC":r["D0_UTC"],
                "utc06_day_bucket":r["utc06_day_bucket"],
                "fold_status":"WARMUP_NO_MODEL" if model is None else "SCORED_EXPOSED_HISTORIC_CHRONOLOGICAL",
                "historical_train_n":len(train), "historical_train_positive_count":sum(x["evaluated_early5_2x"] for x in train),
                "model_score":None if p is None else str(p),
                "training_calibrated_attention_threshold":None if model is None else str(model["threshold"]),
                "research_priority":pick, "original_D0_retained":True,
                "historical_2x_first_D0_early5_evaluation_only":r["evaluated_early5_2x"],
            })
        wins = sum(int(r["evaluated_early5_2x"]) for r in testing)
        got = sum(int(p and r["evaluated_early5_2x"]) for r,p in zip(testing,chosen))
        b = burden(testing,chosen,[date])
        fold_summary.append({
            "anchor":date,"train_n":len(train),"train_positive":sum(x["evaluated_early5_2x"] for x in train),
            "original_D0_n":len(testing),"original_early5_2x":wins,"research_priority_n":sum(chosen),
            "original_early5_kept":got,"original_early5_missed":wins-got,
            "early5_keep_fraction":None if wins==0 or model is None else got/wins,
            "scored":model is not None,"attention":b,
            "historical_false_negative_symbols":[r["symbol"] for r,p in zip(testing,chosen) if r["evaluated_early5_2x"] and not p],
        })
    scored_folds = [x for x in fold_summary if x["scored"]]
    positives = sum(x["original_early5_2x"] for x in scored_folds)
    selected = sum(x["original_early5_kept"] for x in scored_folds)
    all_buckets = [v for x in scored_folds for v in x["attention"]["daily_buckets"]]
    mean = sum(all_buckets)/len(all_buckets) if all_buckets else 0
    peak = max(all_buckets) if all_buckets else 0
    status = ("NOT_EVALUABLE_NO_TRAINED_FOLDS" if not scored_folds or positives==0 else
              "REJECTED_EXPOSED_HISTORICAL" if selected/positives<.8 or mean>5 or peak>12 else
              "HISTORICAL_DIAGNOSTIC_NOT_OOS")
    return {
        "schema":SCHEMA, "frozen_strategy":"SIX_ASOF_FEATURE_LOGISTIC_FIXED_BATCH_GD",
        "old_exposed_only_not_independent_OOS":True,
        "source_git_blobs":SOURCE_BLOBS,
        "all_original_D0_n":len(rows),
        "all_original_positive_early5":sum(r["evaluated_early5_2x"] for r in rows),
        "warmup_positive_early5_not_scored":sum(x["original_early5_2x"] for x in fold_summary if not x["scored"]),
        "scored_folds":len(scored_folds),
        "scored_historical_early5_positive":positives,
        "scored_historical_early5_retained":selected,
        "scored_early5_keep_fraction":selected/positives if positives else None,
        "scored_attention_daily_mean":mean, "scored_attention_daily_peak":peak,
        "frozen_recall_gate":.8, "frozen_attention_mean_gate":5, "frozen_attention_daily_peak_gate":12,
        "historical_research_verdict":status,
        "prior_failed_stage118":"REJECTED_UNCHANGED",
        "full_venue_no_watch_denominator":"UNAVAILABLE_NOT_FULL_MARKET_G1",
        "genuine_new_OOS":"NOT_DONE", "G0":"PARTIAL", "G4_real_executable_net":"UNKNOWN",
        "other_AI_independent_review":"NOT_DONE", "monster_deployment":"NO_GO", "frank":"UNCHANGED",
        "folds":fold_summary, "rows":outcomes,
    }


def run(stage64_path, stage83_path):
    def read(path):
        return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]
    return evaluate(parse_inputs(read(stage64_path),read(stage83_path)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage64",type=Path,required=True)
    p.add_argument("--stage83",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--rows",type=Path)
    a=p.parse_args()
    result=run(a.stage64,a.stage83)
    print(json.dumps({k:v for k,v in result.items() if k not in ("rows",)},ensure_ascii=False,sort_keys=True))
    if a.rows:
        a.rows.parent.mkdir(parents=True,exist_ok=True)
        a.rows.write_text("".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in result["rows"]),encoding="utf-8")
    del result["rows"]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
