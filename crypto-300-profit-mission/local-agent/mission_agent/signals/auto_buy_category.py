"""Fold existing CoinGecko Demo category capture into the Frank Scanner's run."""
import json
import time

from ..db.connection import transaction
from .buy_admission import EXCLUDED_MINTS, exact_mint, qualification
from .category_capture import _MAX_MINTS, capture
from .category_evidence import _CONFLICT, _parse, read_category_evidence, read_scanner_category_evidence

_TERMINAL = {"VERIFIED_MEME", "EXCLUDED"}
_AUTH_FAULT = {"SOURCE_AUTH_REQUIRED", "SOURCE_FORBIDDEN", "SOURCE_REDIRECT_REFUSED"}
_RETRY = {"SOURCE_UNAVAILABLE", "SOURCE_HTTP_UNAVAILABLE", "SOURCE_RATE_LIMIT"}
# Network failures must not spin through the backlog in one scanner cycle.
# A provider Retry-After can raise this interval.
_RETRY_SECONDS = 60


class AutoBuyCategory:
    """Discover candidates from durable BUY rows, with a single Scanner-owned writer."""

    def __init__(self, db, *, api_key, manual_path=None, receipt_path=None, collect=capture, clock=time.time):
        self.db = db
        self.api_key = api_key
        self.manual_path = manual_path
        self.receipt_path = receipt_path
        self.collect = collect
        self.clock = clock
        self.source_fault = None
        db.executescript("""
            CREATE TABLE IF NOT EXISTS buy_category_auto(
              mint TEXT PRIMARY KEY, last_buy_slot INTEGER NOT NULL, attempted_buy_slot INTEGER,
              retry_at INTEGER, outcome TEXT, receipt TEXT
            );
            CREATE TABLE IF NOT EXISTS buy_category_source_state(
              key TEXT PRIMARY KEY, retry_at INTEGER NOT NULL
            );
        """)

    def refresh(self):
        at = int(self.clock())
        if self.source_fault is not None:
            return {"status": self.source_fault, "requests": 0}
        local = read_category_evidence(self.receipt_path, at)
        manual = {}
        if self.manual_path is not None:
            try:
                manual = qualification(self.manual_path, at)
            except FileNotFoundError:
                pass
        # Insert all unseen candidates durably. Reconsider a provider-confirmed
        # unlisted/unclassified Mint if the Scanner observes an additional buy.
        candidates = self.db.execute("""
            SELECT t.mint, max(s.slot) FROM trades t
            JOIN signatures s USING(wallet,signature)
            WHERE s.person_id='frank' AND t.side IN ('BUY','ADD','REENTRY')
              AND s.block_time BETWEEN 1 AND ? AND s.slot>=0 GROUP BY t.mint
        """, (at,)).fetchall()
        with transaction(self.db):
            self.db.executemany("""
                INSERT INTO buy_category_auto(mint,last_buy_slot) VALUES(?,?)
                ON CONFLICT(mint) DO UPDATE SET last_buy_slot=excluded.last_buy_slot
                WHERE excluded.last_buy_slot>buy_category_auto.last_buy_slot
            """, [(mint, stamp) for mint, stamp in candidates if exact_mint(mint) and mint not in EXCLUDED_MINTS])

        backoff = self.db.execute(
            "SELECT retry_at FROM buy_category_source_state WHERE key='coingecko-demo'"
        ).fetchone()
        if backoff and backoff[0] > at:
            return {"status": "SOURCE_BACKOFF", "requests": 0}
        discovered = read_scanner_category_evidence(self.db, at)
        waiting = self.db.execute("""
            SELECT mint,last_buy_slot FROM buy_category_auto
            WHERE (attempted_buy_slot IS NULL OR (retry_at IS NOT NULL AND retry_at<=?)
                   OR (retry_at IS NULL AND attempted_buy_slot<last_buy_slot))
            ORDER BY coalesce(attempted_buy_slot,0), last_buy_slot DESC, mint
        """, (at,))
        selected = {}
        for mint, stamp in waiting:
            if mint in manual:
                continue
            prior = [asset for asset in (local.get(mint), discovered.get(mint)) if asset is not None]
            if any(asset.status in _TERMINAL or asset.source == _CONFLICT for asset in prior):
                continue
            selected[mint] = stamp
            if len(selected) == _MAX_MINTS:
                break
        waiting.close()
        if not selected:
            return {"status": "CURRENT", "requests": 0}

        outcomes = {}
        bundle, _ = self.collect(list(selected), api_key=self.api_key, clock=self.clock,
                                 on_result=lambda mint, status, delay: outcomes.update({mint: (status, delay)}))
        ended = int(self.clock())
        receipts = {}
        for row in bundle["records"]:
            parsed = _parse(row, ended)
            if parsed and parsed[0] in selected:
                receipts[parsed[0]] = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        attempts = 0
        status = "CURRENT"
        with transaction(self.db):
            for mint, (outcome, wait) in outcomes.items():
                if mint not in selected or outcome == "CAPTURE_DEADLINE":
                    continue
                attempts += 1
                delay = max(_RETRY_SECONDS, wait or 0)
                retry_at = ended + delay if outcome in _RETRY else None
                self.db.execute("""
                    UPDATE buy_category_auto SET attempted_buy_slot=?, retry_at=?, outcome=?,
                        receipt=coalesce(?,receipt) WHERE mint=?
                """, (selected[mint], retry_at, outcome, receipts.get(mint), mint))
                if outcome == "SOURCE_RATE_LIMIT":
                    status = outcome
                    self.db.execute("""
                        INSERT INTO buy_category_source_state(key,retry_at) VALUES('coingecko-demo',?)
                        ON CONFLICT(key) DO UPDATE SET retry_at=excluded.retry_at
                    """, (retry_at,))
                if outcome in _AUTH_FAULT:
                    self.source_fault = outcome
                    status = outcome
                    # A repaired key or configuration can retry on service restart.
                    self.db.execute("UPDATE buy_category_auto SET attempted_buy_slot=NULL WHERE mint=?", (mint,))
        return {"status": status, "requests": attempts, "receipts": len(receipts)}
