#!/usr/bin/env python3
"""Explore causal D0 price-only trigger coverage on frozen official 1m histories.

NOT A V4 STRATEGY BACKTEST. Historical 24h ticker states and book snapshots
are not available in these 240m probes. 1m closes proxy 3m observed prices.
"""
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "monster/evidence"
PATHS = [
    ROOT / "monster_v4_backtest_xtz_1m_probe_20261011.json",
    ROOT / "monster_v4_backtest_broccoli714_1m_probe_20261011.json",
]
TRIGGERS = [
    ("3m_5pct", 3, Decimal("0.05")),
    ("15m_8pct", 15, Decimal("0.08")),
    ("60m_15pct", 60, Decimal("0.15")),
]


def price_probe(path):
    src = json.loads(Path(path).read_text(encoding="utf-8"))
    if src.get("interval") != "1m" or src.get("venue") != "spot":
        raise ValueError("NOT_OFFICIAL_SPOT_1M_PROBE")
    bars = src.get("bars")
    if not isinstance(bars, list) or len(bars) < 61:
        raise ValueError("INSUFFICIENT_1M_HISTORY")
    base_time = int(bars[0][0])
    if base_time % 180000:
        raise ValueError("NOT_ALIGNED_3M_START")
    for i, bar in enumerate(bars):
        if int(bar[0]) != base_time + i * 60000:
            raise ValueError("GAPPED_1M_BARS")
        if int(bar[6]) != int(bar[0]) + 59999:
            raise ValueError("INVALID_CLOSED_BAR")
    # A 3m poll at time T sees no later than the 1m candle closed at T.
    closes = [(int(bar[6]) + 1, Decimal(str(bar[4])))
              for i, bar in enumerate(bars) if (i + 1) % 3 == 0]
    anchor_time = int(datetime.fromisoformat(src["watch_anchor_utc"].replace(
        "Z", "+00:00")).timestamp() * 1000)
    out = []
    for label, minutes, threshold in TRIGGERS:
        lag = minutes // 3
        maximum = None
        hits = []
        at_anchor = None
        for i in range(lag, len(closes)):
            ms, price = closes[i]
            old_price = closes[i - lag][1]
            if price <= 0 or old_price <= 0:
                raise ValueError("NONPOSITIVE_PRICE")
            change = (price / old_price - 1) * 100
            maximum = change if maximum is None else max(maximum, change)
            if ms == anchor_time:
                at_anchor = change
            if change >= threshold * 100:
                hits.append(ms)
        out.append({"path": label, "threshold_pct": str(threshold * 100),
                    "max_4h_observed_return_pct": (
                        str(round(maximum, 6)) if maximum is not None else None),
                    "at_historical_watch_pct": (
                        str(round(at_anchor, 6)) if at_anchor is not None else None),
                    "window_trigger_count": len(hits),
                    "first_trigger_utc": (datetime.fromtimestamp(
                        hits[0] / 1000, tz=timezone.utc).isoformat() if hits else None)})
    return {"symbol": src["symbol"], "watch_anchor_utc": src["watch_anchor_utc"],
            "raw_1m_bars": len(bars), "sampled_3m_snapshots": len(closes),
            "evaluation": "PRICE_ONLY_CAUSAL_3M_SAMPLING_PROXY",
            "full_V4_backtest": False, "historical_orderbook_available": False,
            "24h_ticker_history_reconstructed": False,
            "triggers": out}


def main():
    print(json.dumps({"research_only": True,
                      "results": [price_probe(path) for path in PATHS]},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
