"""Spot511 approved-source minute rows -> closed-only D0 snapshot inputs.

Never a live 24h ticker, BUY, signal-backtest result or PIT listing proof.
Loads at most one symbol's 9 fixed UTC days; missing files censor ticks.
Use existing Stage166 original ZIP + publisher-checksum verifier unchanged.
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import csv
import zipfile

import monster_v4_stage166_spot511_official_1m_intake as stage166

SCHEMA = "MONSTER_SPOT511_CLOSED_1M_D0_FEED_V1"
MINUTE_MS = 60_000
DAY_MINUTES = 1440
FIRST = date(2026, 10, 16)
LAST = date(2026, 10, 24)
EPOCH_MS = int(datetime.combine(FIRST, datetime.min.time(), timezone.utc).timestamp() * 1000)
START_MS = int(datetime(2026, 10, 17, 22, 6, tzinfo=timezone.utc).timestamp() * 1000)
END_MS = int(datetime(2026, 10, 24, 22, 6, tzinfo=timezone.utc).timestamp() * 1000)
TOTAL_MINUTES = 9 * DAY_MINUTES


def _read_verified_day(root, symbol, day):
    zip_path, checksum_path = stage166.daily_paths(root, symbol, day)
    if not zip_path.is_file() or not checksum_path.is_file():
        return None
    stage166.validate_daily_zip(zip_path, checksum_path, symbol, day)
    with zipfile.ZipFile(zip_path) as zipped:
        filename = f"{symbol}-1m-{day.isoformat()}.csv"
        with zipped.open(filename) as file:
            import io
            reader = csv.reader(io.TextIOWrapper(file, encoding="utf-8", newline=""))
            return [(Decimal(r[4]), Decimal(r[7])) for r in reader]


def symbol_tick_feed(source_dir, symbol, *, asof_utc, roster=None):
    """Return all 3360 ticks, ready or explicitly censored, in strict UTC order.

    The 24h turnover input is the sum of 1m quote volumes across [T-24h,T),
    deliberately named a reconstructed PROXY, not the actual live ticker.
    Source data dated after asof_utc is not read even if present on disk.
    """
    if (not isinstance(asof_utc, datetime) or asof_utc.tzinfo is None
            or asof_utc.utcoffset() is None):
        raise ValueError("ASOF_MUST_BE_TIMEZONE_AWARE")
    asof_utc = asof_utc.astimezone(timezone.utc)
    if roster is None:
        roster = stage166.frozen_roster()
    if (not isinstance(roster, list) or len(roster) != 511
            or roster != sorted(set(roster)) or symbol not in roster):
        raise ValueError("SPOT511_FROZEN_SYMBOL_REQUIRED")
    closes = [None] * TOTAL_MINUTES
    quotes = [None] * TOTAL_MINUTES
    rejected = set()
    unavailable = set()
    future = set()
    day = FIRST
    for offset in range(9):
        published_earliest = datetime.combine(day + timedelta(days=1),
                                              datetime.min.time(), timezone.utc)
        if asof_utc < published_earliest:
            future.add(day.isoformat())
        else:
            try:
                observed = _read_verified_day(source_dir, symbol, day)
                if observed is None:
                    unavailable.add(day.isoformat())
                elif len(observed) != DAY_MINUTES:
                    raise ValueError("MINUTE_ROWS_NOT_1440")
                else:
                    for j, (price, turnover) in enumerate(observed):
                        closes[offset * DAY_MINUTES + j] = price
                        quotes[offset * DAY_MINUTES + j] = turnover
            except (ValueError, OSError, zipfile.BadZipFile, UnicodeError):
                rejected.add(day.isoformat())
        day += timedelta(days=1)
    pref_quote = [Decimal(0)]
    pref_missing = [0]
    for q in quotes:
        pref_quote.append(pref_quote[-1] + (q if q is not None else Decimal(0)))
        pref_missing.append(pref_missing[-1] + (q is None))
    counts = Counter()
    items = []
    for t in range(START_MS, END_MS, 3 * MINUTE_MS):
        right = (t - EPOCH_MS) // MINUTE_MS
        left = right - DAY_MINUTES
        if right > TOTAL_MINUTES or left < 0:
            raise ValueError("REPLAY_WINDOW_OUTSIDE_FROZEN_MINUTE_GRID")
        missing = pref_missing[right] - pref_missing[left]
        if missing or closes[right-1] is None:
            status = "CENSORED_SOURCE_MISSING_OR_REJECTED"
            row = None
        else:
            status = "READY_RECONSTRUCTED_TICKER_PROXY"
            row = {"symbol": symbol, "lastPrice": str(closes[right-1]),
                   "quoteVolume": str(pref_quote[right]-pref_quote[left])}
        counts[status] += 1
        items.append({"tick_ms": t, "status": status, "source_row": row})
    if len(items) != 3360 or sum(counts.values()) != 3360:
        raise ValueError("FROZEN_3360_TICK_DENOMINATOR_DRIFT")
    return {"schema": SCHEMA, "symbol": symbol, "ticks": items,
            "counts": dict(counts), "source_unavailable_days": sorted(unavailable),
            "source_rejected_days": sorted(rejected),
            "source_future_days": sorted(future),
            "frozen_511_venue_population_processed": False,
            "t0_historical_listing_pit_verified": False,
            "quote24_is_live_ticker": False,
            "quote24_source": "CLOSED_1M_SUM_1440_PROXY_NOT_LIVE_TICKER",
            "publisher_available_at_2026_historical_pit": "UNKNOWN",
            "d1_5m_candles_evaluated": False,
            "real_buy_sell_price": "UNKNOWN", "G0": "PARTIAL", "G1": "NOT_SCORABLE",
            "G4": "UNKNOWN", "G6": "NO_GO"}
