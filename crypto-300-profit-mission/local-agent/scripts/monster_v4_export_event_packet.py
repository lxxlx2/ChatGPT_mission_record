#!/usr/bin/env python3
"""Read-only export of previously verified Monster event evidence for offline review.

Includes all 3904 event metadata rows and 30d-before/7d-after 1h
normalized price windows for every exported >=5x instrument event. This is
NOT a forward replay, a trading executable, or a fresh checksum verification.
Does not access the network, launch/restart any service or send messages.
"""
import argparse
import csv
import gzip
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path


def locate(name, roots):
    for root in roots:
        path = root / name
        if path.is_file():
            return path
    for root in roots:
        if root.is_dir():
            for path in root.rglob(name):
                if path.is_file():
                    return path
    raise ValueError("MISSING_REQUIRED_EVENT_FILE:" + name)


def sha_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def export(home, output):
    fm2 = home / "crypto-monitor-fm2-evidence-20260930/monster"
    fm3 = home / "crypto-monitor-fm3-evidence-20261001/monster"
    v3 = home / "crypto-monitor-monster-v3-evidence-20261003"
    required = {
        "monster-history-all-events.csv": home / "monster-history-all-events.csv",
        "monster-history-5x-plus.csv": home / "monster-history-5x-plus.csv",
    }
    for name in (
        "train-instrument-events.json",
        "validation-instrument-events.json",
        "ground-truth-events-v1.json",
    ):
        required[name] = locate(name, (fm3, fm2, v3))
    for name, path in required.items():
        if not path.is_file():
            raise ValueError("MISSING_REQUIRED_FILE:" + name)
    with required["monster-history-5x-plus.csv"].open(
        newline="", encoding="utf-8-sig"
    ) as f:
        positives = list(csv.DictReader(f))
    with required["monster-history-all-events.csv"].open(
        newline="", encoding="utf-8-sig"
    ) as f:
        all_events = list(csv.DictReader(f))
    if len(positives) != 40 or len(all_events) != 3904:
        raise ValueError(
            f"UNEXPECTED_EVENT_COUNTS: all={len(all_events)} positive={len(positives)}"
        )
    expanded = fm3 / "expanded-coverage.json"
    if not expanded.is_file():
        raise ValueError("MISSING_EXPANDED_COVERAGE")
    coverage = json.loads(expanded.read_text(encoding="utf-8"))
    by_symbol = {
        (r["venue"], r["symbol"]): Path(r["bars_path"])
        for r in coverage
        if r.get("bars_path")
    }
    manifest = {
        "scope": "READ_ONLY_CACHED_OFFICIAL_1H_BARS",
        "ground_truth_version": "V1_2025_2026_PLUS_V2_2021_2024",
        "all_event_rows": len(all_events),
        "positive_event_rows": len(positives),
        "source_file_hashes": {
            name: sha_file(path) for name, path in required.items()
        },
        "windows": [],
        "missing": [],
    }
    source_hash_cache = {}
    windows = 0
    bar_count = 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
        allowZip64=True
    ) as packet:
        for name, source in required.items():
            packet.write(source, arcname="events/" + name)
        for idx, row in enumerate(positives, 1):
            period, venue, symbol = (
                row["period"], row["venue"], row["symbol"]
            )
            if period == "EXPOSED_2025_2026":
                path = fm2 / "bars" / venue / (symbol + ".json.gz")
            else:
                path = by_symbol.get(
                    (venue, symbol),
                    fm3 / "bars" / venue / (symbol + ".json.gz")
                )
            identity = {"period": period, "venue": venue, "symbol": symbol}
            if not path.is_file():
                manifest["missing"].append({
                    **identity, "reason": "BAR_SOURCE_NOT_FOUND"
                })
                continue
            try:
                moment = datetime.fromisoformat(
                    row["anchor_utc"].replace("Z", "+00:00")
                )
                anchor = int(moment.timestamp() * 1000)
                with gzip.open(path, "rt", encoding="utf-8") as f:
                    all_bars = json.load(f)
                hour = 3600000
                bars = [
                    b for b in all_bars
                    if anchor - 720 * hour <= int(b[0]) <= anchor + 168 * hour
                ]
                if not bars:
                    manifest["missing"].append({
                        **identity, "reason": "EMPTY_1H_WINDOW"
                    })
                    continue
                source_key = str(path)
                if source_key not in source_hash_cache:
                    source_hash_cache[source_key] = sha_file(path)
                entry = f"bars/{period}/{venue}/{symbol}/{idx:03d}.json"
                packet.writestr(entry, json.dumps({
                    **identity,
                    "anchor_utc": row["anchor_utc"],
                    "source_gzip_sha256": source_hash_cache[source_key],
                    "bars": bars,
                }, separators=(",", ":")))
                manifest["windows"].append({
                    **identity, "entry": entry, "bar_count": len(bars),
                    "first_open_ms": bars[0][0], "last_open_ms": bars[-1][0],
                })
                windows += 1
                bar_count += len(bars)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                manifest["missing"].append({
                    **identity, "reason": type(exc).__name__
                })
        packet.writestr(
            "packet-manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False)
        )
    return {
        "PACKET": str(output),
        "EVENT_ROWS": len(all_events),
        "POSITIVE_ROWS": len(positives),
        "HISTORICAL_WINDOWS": windows,
        "HISTORICAL_1H_BARS": bar_count,
        "MISSING": manifest["missing"],
        "PACKET_BYTES": output.stat().st_size,
        "SHA256": sha_file(output),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--home", type=Path,
        default=Path.home() / "Documents/ChatGPT"
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    home = args.home.resolve()
    output = args.output or home / "monster-backtest-packet-20261010.zip"
    result = export(home, output)
    for key, value in result.items():
        print(key + "=" + (
            json.dumps(value, ensure_ascii=False)
            if isinstance(value, list) else str(value)
        ))


if __name__ == "__main__":
    main()
