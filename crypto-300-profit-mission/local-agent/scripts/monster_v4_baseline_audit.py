#!/usr/bin/env python3
"""Read existing immutable Monster V3 aggregate JSON; no raw-data or market call.

This is a reproducible *baseline analysis* for V4 research, NOT a V4 replay.
The historical V1-V3 high/anchor-close target is NOT an executable return.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read_json(base: Path, relative: str):
    return json.loads((base / relative).read_text(encoding="utf-8"))


def analyze(train: list[dict], validation: dict, winner: dict, gate: dict) -> dict:
    if not isinstance(train, list) or len(train) != 72:
        raise ValueError("EXPECTED_72_TRAIN_CONFIGS")
    ids = [r["config_id"] for r in train]
    if len(set(ids)) != len(ids):
        raise ValueError("DUPLICATE_TRAIN_CONFIG_ID")
    selected = winner["winner"]
    match = next((row for row in train if row["config_id"] == selected["config_id"]), None)
    if match is None or match != selected:
        raise ValueError("FROZEN_TRAIN_WINNER_MISMATCH")
    result = validation["result"]
    if result["config_id"] != selected["config_id"] or result["parameters"] != selected["parameters"]:
        raise ValueError("VALIDATION_WINNER_CHANGED")
    if gate["validated_config"] != selected["config_id"] or gate["validation_ceiling_pass"] != result["ceiling_pass"]:
        raise ValueError("VALIDATION_GATE_MISMATCH")
    hits = Counter(r["entity"]["5"]["prehit"] for r in train)
    modes = {}
    for mode in ("QUALITY_OR_RS", "QUALITY", "QUALITY_AND_RS_OR_DUAL"):
        group = [x for x in train if x["parameters"][2] == mode]
        if len(group) != 24:
            raise ValueError("EXPECTED_24_PER_CONFIRMATION_MODE")
        modes[mode] = {
            "configs": len(group),
            "train_ceiling_pass": sum(bool(x["ceiling_pass"]) for x in group),
            "mean_5x_pre_hits_out_of_20": round(sum(x["entity"]["5"]["prehit"] for x in group) / len(group), 3),
            "mean_of_config_median_entities_per_day": round(sum(x["median_entities_day"] for x in group) / len(group), 3),
        }
    return {
        "status": "BASELINE_ONLY_V4_NOT_YET_REPLAYED",
        "label": "HISTORICAL_7D_HIGH_OVER_ANCHOR_CLOSE_NOT_EXECUTABLE_RETURN",
        "train_period": "2021-01-01/2024-01-01",
        "validation_period": "2024-01-01/2025-01-01_EXPOSED",
        "train_configs": len(train),
        "train_ceiling_pass_configs": sum(bool(x["ceiling_pass"]) for x in train),
        "train_config_5x_hits_histogram": {str(k): hits[k] for k in sorted(hits)},
        "train_5x_pre_hits_ge_19_configs": sum(x["entity"]["5"]["prehit"] >= 19 for x in train),
        "train_group_aggregate": modes,
        "frozen_winner": {
            "id": selected["config_id"],
            "parameters": selected["parameters"],
            "median_entities_day": selected["median_entities_day"],
            "p95_entities_day": selected["p95_entities_day"],
            "entity_5x": {"events": selected["entity"]["5"]["events"], "prehit": selected["entity"]["5"]["prehit"]},
            "entity_10x": {"events": selected["entity"]["10"]["events"], "prehit": selected["entity"]["10"]["prehit"]},
        },
        "exposed_validation": {
            "status": validation["status"],
            "ceiling_pass": result["ceiling_pass"],
            "median_entities_day": result["median_entities_day"],
            "p95_entities_day": result["p95_entities_day"],
            "entity_5x_events": result["entity"]["5"]["events"],
            "entity_5x_prehit": result["entity"]["5"]["prehit"],
            "entity_10x_events": result["entity"]["10"]["events"],
        },
        "v4_historical_replay_completed": False,
        "v4_live_notification_authorized": False,
        "notes": [
            "No source time series were downloaded or newly reprocessed.",
            "2024 and 2025-2026 were exposed in prior work; no independent V4 holdout claim.",
            "The 2021-2023/train winners are not an executable return, precision, or future hit rate.",
            "This script never sends mail or changes trading/Frank processes.",
        ],
    }


def run(base: Path = ROOT) -> dict:
    t = read_json(base, "docs/results/monster_d1_v3_train.json")
    v = read_json(base, "docs/results/monster_d1_v3_validation.json")
    winner = read_json(base, "config/monster_d1_v3_winner.json")
    gate = read_json(base, "config/monster_d1_v3_validation_gate.json")
    return analyze(t, v, winner, gate)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-agent-root", type=Path, default=ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()
    result = run(args.local_agent_root)
    data = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
