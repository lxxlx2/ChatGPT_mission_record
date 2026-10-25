"""One verified Spot511 minute tape for D0 context and D1 closed-5m inputs.

Historical research-only: derived 24h quote volume/last close are NOT archived
live ticker snapshots. Stage166 publisher checksum validates every admitted UTC
file. No network, orders, mail, daemon, scheduler, changes to original D0/D1.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import io
import zipfile

import monster_v4_spot511_closed_minute_feed as d0

FIVE_MS = 300_000
VALID_DAYS = tuple(d0.FIRST + timedelta(days=x) for x in range(9))
FIELDS = (1, 2, 3, 4, 5, 7)


class VerifiedClosedMinuteTape:
    """Load at most one Spot symbol's frozen nine days, preserving gaps.

    The roster injection is for offline tests. In regular use a frozen
    historical T0 roster must be loaded from Stage166, never current symbols.
    """

    def __init__(self, root, symbol, *, asof_utc, roster=None):
        if not isinstance(asof_utc, datetime) or asof_utc.tzinfo is None or asof_utc.utcoffset() is None:
            raise ValueError("TAPE_ASOF_NEEDS_TIMEZONE")
        asof_utc = asof_utc.astimezone(timezone.utc)
        if roster is None:
            roster = d0.stage166.frozen_roster()
        if (not isinstance(roster, list) or len(roster) != 511
                or roster != sorted(set(roster)) or symbol not in roster):
            raise ValueError("TAPE_FROZEN_511_ROSTER_REQUIRED")
        self.symbol = symbol
        self.asof_utc = asof_utc
        self.minutes = [None] * d0.TOTAL_MINUTES
        self.day_states = {}
        self.publisher_zip_sha = {}
        for i, day in enumerate(VALID_DAYS):
            next_midnight = datetime.combine(day + timedelta(days=1),
                                             datetime.min.time(), timezone.utc)
            if next_midnight > asof_utc:
                self.day_states[day.isoformat()] = "UTC_DAY_NOT_YET_ENDED"
                continue
            archive, check = d0.stage166.daily_paths(Path(root), symbol, day)
            if not archive.is_file() or not check.is_file():
                self.day_states[day.isoformat()] = "SOURCE_NOT_SUPPLIED"
                continue
            try:
                proof = d0.stage166.validate_daily_zip(archive, check, symbol, day)
                with zipfile.ZipFile(archive) as z:
                    filename = f"{symbol}-1m-{day.isoformat()}.csv"
                    with z.open(filename) as stream:
                        reader = csv.reader(io.TextIOWrapper(stream, encoding="utf-8", newline=""))
                        bars = [tuple(Decimal(row[x]) for x in FIELDS) for row in reader]
                if len(bars) != d0.DAY_MINUTES:
                    raise ValueError("VERIFIED_DAY_ROW_COUNT_CHANGED")
            except (ValueError, OSError, UnicodeError, zipfile.BadZipFile, InvalidOperation) as exc:
                self.day_states[day.isoformat()] = "SOURCE_REJECTED_OR_INCOMPLETE"
                continue
            self.minutes[i*d0.DAY_MINUTES:(i+1)*d0.DAY_MINUTES] = bars
            self.day_states[day.isoformat()] = "VERIFIED_FULL_DAY_1440"
            self.publisher_zip_sha[day.isoformat()] = proof["zip_sha256"]
        self.quote_prefix = [Decimal(0)]
        self.missing_prefix = [0]
        for bar in self.minutes:
            self.quote_prefix.append(self.quote_prefix[-1] + (bar[5] if bar else Decimal(0)))
            self.missing_prefix.append(self.missing_prefix[-1] + (bar is None))

    def _index(self, tick_ms):
        if type(tick_ms) is not int:
            raise ValueError("TAPE_UTC_TICK_MS_REQUIRED")
        if not d0.START_MS <= tick_ms < d0.END_MS or tick_ms % d0.MINUTE_MS:
            raise ValueError("TAPE_OUTSIDE_FROZEN_3M_WINDOW")
        return (tick_ms - d0.EPOCH_MS) // d0.MINUTE_MS

    def d0_at(self, tick_ms):
        """At T, only [T-24h,T) completed 1m (no future closes)."""
        right = self._index(tick_ms)
        if tick_ms % (3*d0.MINUTE_MS):
            raise ValueError("TAPE_D0_REQUIRES_3MIN_TICK")
        left = right - d0.DAY_MINUTES
        if left < 0 or self.missing_prefix[right] != self.missing_prefix[left]:
            return None
        last = self.minutes[right-1]
        return {"symbol": self.symbol, "lastPrice": str(last[3]),
                "quoteVolume": str(self.quote_prefix[right] - self.quote_prefix[left])}

    def six_closed_5m(self, tick_ms):
        """Original shadow.evaluate_closed_5m-compatible OHLCV list.

        Six contiguous fully closed 5m candles, no partial/cross-future candle.
        Raise on ANY gap instead of inventing prices or zero quote turnover.
        """
        right = self._index(tick_ms)
        if tick_ms % (3*d0.MINUTE_MS):
            raise ValueError("TAPE_D1_REQUIRES_3MIN_TICK")
        last_closed_end_ms = (tick_ms // FIVE_MS) * FIVE_MS
        end = (last_closed_end_ms - d0.EPOCH_MS) // d0.MINUTE_MS
        start = end - 30
        if start < 0 or end > d0.TOTAL_MINUTES or self.missing_prefix[end] != self.missing_prefix[start]:
            raise ValueError("TAPE_D1_CENSORED_MINUTE_SOURCE")
        candles = []
        for offset in range(start, end, 5):
            segment = self.minutes[offset:offset+5]
            if len(segment) != 5 or any(bar is None for bar in segment):
                raise ValueError("TAPE_D1_INCOMPLETE_5MIN_BAR")
            opening = segment[0][0]
            highest = max(bar[1] for bar in segment)
            lowest = min(bar[2] for bar in segment)
            closing = segment[-1][3]
            volume = sum((bar[4] for bar in segment), Decimal(0))
            quote_volume = sum((bar[5] for bar in segment), Decimal(0))
            open_ms = d0.EPOCH_MS + offset*d0.MINUTE_MS
            close_ms = open_ms + FIVE_MS - 1
            if close_ms >= tick_ms:
                raise ValueError("TAPE_D1_FUTURE_OR_PARTIAL_CANDLE")
            candles.append([open_ms, str(opening), str(highest), str(lowest),
                            str(closing), str(volume), close_ms, str(quote_volume)])
        if len(candles) != 6:
            raise ValueError("TAPE_D1_EXPECTS_SIX_CLOSED_5MIN")
        return candles

    def d1_fetch(self, venue, symbol, tick_ms):
        """Inject as fetch_candles(venue,symbol,now) into original D1 engine."""
        if venue != "spot" or symbol != self.symbol:
            raise ValueError("TAPE_D1_VENUE_OR_SYMBOL_MISMATCH")
        return self.six_closed_5m(tick_ms)

    def readiness(self):
        counts = {name: list(self.day_states.values()).count(name)
                  for name in sorted(set(self.day_states.values()))}
        return {"symbol": self.symbol, "day_states": dict(self.day_states),
                "day_counts": counts, "publisher_zip_sha256": dict(self.publisher_zip_sha),
                "source_is_publisher_sha_verified": all(x == "VERIFIED_FULL_DAY_1440"
                    for x in self.day_states.values()),
                "spot_listing_pit_verified": False,
                "historical_1m_available_at_original_tick": "UNKNOWN",
                "d0_last_price_is_live_ticker": False,
                "d0_quote24_is_live_ticker": False,
                "reconstructed_source_only_not_signal_backtest": True,
                "G0": "PARTIAL", "G4": "UNKNOWN", "G6": "NO_GO"}
