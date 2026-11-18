"""Durable FIFO runs from fixed local facts and captured market observations."""

from contextlib import contextmanager
from decimal import Decimal
from fractions import Fraction
import base64
import json
import math
from pathlib import Path
import re
import sqlite3
import time
import uuid

from ..meme.holder_ranks import valid_pubkey
from .evidence_manifests import ManifestError, canonical, digest
from .market_observations import portfolio_valuation
from .wallet_activity import connect


IDENTITY = re.compile(r"[a-f0-9]{32}")
MARK_MAX_AGE = 60
COST_SCOPE = "FIXED_INDEXED_WALLET_ACTIVITY"


class CostStoreError(ValueError):
    def __init__(self, code, http_status=400):
        super().__init__(code)
        self.code = code
        self.http_status = http_status


def _identity(value, error):
    if not isinstance(value, str) or IDENTITY.fullmatch(value) is None:
        raise CostStoreError(error)
    return value


def _clock(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise CostStoreError("COST_CLOCK_INVALID", 503)
    return value


def _cursor(run_id, mint, offset):
    payload = canonical({"run_id": run_id, "mint": mint, "offset": offset})
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def _read_cursor(raw):
    if not isinstance(raw, str) or not 1 <= len(raw) <= 1024:
        raise CostStoreError("INVALID_COST_CURSOR")
    try:
        token = json.loads(base64.b64decode(raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True))
        if (not isinstance(token, dict) or set(token) != {"run_id", "mint", "offset"}
                or type(token["offset"]) is not int or not 0 < token["offset"] <= 2**63-1
                or not isinstance(token["run_id"], str) or IDENTITY.fullmatch(token["run_id"]) is None
                or (token["mint"] is not None and not valid_pubkey(token["mint"]))
                or raw != _cursor(token["run_id"], token["mint"], token["offset"])):
            raise ValueError
    except (ValueError, TypeError, RecursionError):
        raise CostStoreError("INVALID_COST_CURSOR") from None
    return token


def _priced_refs(valuation, market_rows):
    references = {}
    for row in valuation["rows"]:
        mint = row["mint"]
        observed = market_rows.get(mint)
        if row["status"] == "PRICED":
            references[mint] = {
                "mint": mint,
                "observation_sha256": row["observation_sha256"],
                "observed_at": observed["observed_at"],
                "source": observed["source"],
                "price_usd": row["price_usd"],
            }
    return references


def _covered_unrealized(asset, references):
    target = references.get(asset["mint"])
    if target is None or type(asset["decimals"]) is not int:
        return []
    target_price = _mark_decimal(target)
    if target_price is None:
        return []
    results = []
    for component in asset["remaining_costs"]:
        quote = references.get(component["mint"])
        quote_price = _mark_decimal(quote) if quote is not None else None
        if quote_price is None:
            continue
        quantity = int(component["covered_quantity_raw"])
        cost = Fraction(int(component["raw_numerator"]), int(component["raw_denominator"]))
        rate = target_price / quote_price
        mark = Fraction(quantity * 10**component["decimals"], 10**asset["decimals"]) * rate
        difference = mark - cost
        results.append({
            "mint": component["mint"], "denomination": component["denomination"],
            "decimals": component["decimals"], "covered_quantity_raw": str(quantity),
            "raw_numerator": str(difference.numerator), "raw_denominator": str(difference.denominator),
            "mark_basis": "RATIO_OF_CAPTURED_USD_REFERENCES",
            "target_observation": target, "quote_observation": quote,
        })
    return results


def _mark_decimal(reference):
    price = Decimal(reference["price_usd"])
    # Fraction serializes expanded integers; hostile decimal exponents should
    # not become arbitrary allocations. The USD observation remains visible.
    decimal = price.as_tuple()
    if abs(decimal.exponent) + len(decimal.digits) > 1000:
        return None
    return Fraction(price)


def value_assets(assets, market_rows, as_of):
    positions = [{"mint": row["mint"], "raw_amount": row["quantity_raw"], "decimals": row["decimals"]}
                 for row in assets if int(row["quantity_raw"]) > 0]
    valuation = portfolio_valuation(positions, market_rows, as_of, max_age_seconds=MARK_MAX_AGE)
    position_rows = {row["mint"]: row for row in valuation["rows"]}
    quote_mints = sorted({cost["mint"] for asset in assets for cost in asset["remaining_costs"]
                          if valid_pubkey(cost["mint"])})
    quote_valuation = portfolio_valuation(
        [{"mint": mint, "raw_amount": "1", "decimals": 0} for mint in quote_mints],
        market_rows, as_of, max_age_seconds=MARK_MAX_AGE)
    refs = _priced_refs(valuation, market_rows) | _priced_refs(quote_valuation, market_rows)
    result = []
    for asset in assets:
        mint = asset["mint"]
        unrealized = _covered_unrealized(asset, refs)
        result.append({
            **asset,
            "valuation": {**position_rows.get(mint, {"status": "NO_POSITIVE_REPLAYED_BALANCE"}),
                          "observation": refs.get(mint)},
            "covered_unrealized_pnl": unrealized,
            "covered_unrealized_quantity_raw": str(sum(int(r["covered_quantity_raw"]) for r in unrealized)),
            "unrealized_pnl": None,
        })
    summary = {
        "scope": "REPLAYED_POSITIVE_LOTS_AT_CAPTURED_USD_REFERENCES",
        "as_of": as_of, "max_age_seconds": MARK_MAX_AGE,
        "covered_positions": valuation["covered_positions"],
        "unpriced_mints": sorted(row["mint"] for row in valuation["rows"] if row["status"] != "PRICED"),
        "partial_value_usd": valuation["priced_subtotal_usd"] if valuation["covered_positions"] else None,
        "full_wallet_value_usd": None,
    }
    return result, summary


class WalletCostStore:
    def __init__(self, root, manifests, market_rows, *, code_sha="UNPINNED", clock=time.time):
        self.root = Path(root)
        self.path = self.root / "frank-wallet-cost.sqlite"
        self.manifests = manifests
        self.market_rows = market_rows
        self.code_sha = code_sha
        self.clock = clock

    @contextmanager
    def _db(self, *, write=False):
        db = None
        try:
            if self.path.is_symlink():
                raise CostStoreError("COST_STORAGE_UNAVAILABLE", 503)
            if not write and not self.path.exists():
                yield None
                return
            if write:
                self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
                db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
                self.path.chmod(0o600)
                db.execute("PRAGMA synchronous=FULL")
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("BEGIN IMMEDIATE")
                db.execute("""CREATE TABLE IF NOT EXISTS cost_runs(
                    seq INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE, manifest TEXT NOT NULL,
                    version TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(manifest,version))""")
                db.execute("""CREATE TABLE IF NOT EXISTS cost_keys(
                    request_key TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES cost_runs(id))""")
                db.execute("""CREATE TABLE IF NOT EXISTS cost_assets(
                    run_id TEXT NOT NULL REFERENCES cost_runs(id), mint TEXT NOT NULL,
                    body TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(run_id,mint))""")
                db.row_factory = sqlite3.Row
            else:
                db = connect(self.path)
                db.execute("BEGIN")
            yield db
            if write:
                db.commit()
        except (OSError, sqlite3.Error):
            raise CostStoreError("COST_STORAGE_UNAVAILABLE", 503) from None
        finally:
            if db is not None:
                db.close()

    @staticmethod
    def _saved(db, manifest, version, key):
        via_key = db.execute("SELECT r.* FROM cost_keys k JOIN cost_runs r ON r.id=k.run_id WHERE k.request_key=?",
                             (key,)).fetchone()
        if via_key is not None:
            if (via_key["manifest"], via_key["version"]) != (manifest, version):
                raise CostStoreError("COST_IDEMPOTENCY_CONFLICT", 409)
            return via_key
        return db.execute("SELECT * FROM cost_runs WHERE manifest=? AND version=?", (manifest, version)).fetchone()

    @staticmethod
    def _metadata(record):
        if record is None:
            raise CostStoreError("COST_RUN_NOT_FOUND", 404)
        try:
            result = json.loads(record["body"])
            if (result["run_id"], result["manifest_id"], result["accounting_version"]) != (
                    record["id"], record["manifest"], record["version"]):
                raise ValueError
            if result["run_sha256"] != digest({k: v for k, v in result.items() if k != "run_sha256"}):
                raise ValueError
            return result
        except (ValueError, TypeError, KeyError, RecursionError):
            raise CostStoreError("COST_RUN_INTEGRITY_FAILED", 503) from None

    def create(self, input_manifest_id, idempotency_key):
        from .wallet_cost_fifo import ACCOUNTING_VERSION, build_cost_ledger

        manifest = _identity(input_manifest_id, "INVALID_COST_MANIFEST_ID")
        if (not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 256
                or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in idempotency_key)):
            raise CostStoreError("INVALID_COST_IDEMPOTENCY_KEY")
        with self._db(write=True) as db:
            prior = self._saved(db, manifest, ACCOUNTING_VERSION, idempotency_key)
            if prior is not None:
                result = self._metadata(prior)
                db.execute("INSERT OR IGNORE INTO cost_keys VALUES(?,?)", (idempotency_key, result["run_id"]))
                return result
        try:
            evidence, rows = self.manifests.cost_input(manifest)
            ledger = build_cost_ledger(rows)
            created = _clock(self.clock())
            market_status = "LOCAL_CAPTURE_AVAILABLE"
            try:
                market = self.market_rows()
                if not isinstance(market, dict):
                    raise ValueError
            except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
                market, market_status = {}, "LOCAL_CAPTURE_UNAVAILABLE"
            assets, valuation = value_assets(ledger["assets"], market, created)
            valuation["source_status"] = market_status if market else (
                "NO_LOCAL_OBSERVATIONS" if market_status == "LOCAL_CAPTURE_AVAILABLE" else market_status)
            encoded_assets = sorted((asset["mint"], canonical(asset), digest(asset)) for asset in assets)
            identity = uuid.uuid4().hex
            result = {key: value for key, value in ledger.items() if key != "assets"}
            result.update(
                run_id=identity, manifest_id=manifest, manifest_sha256=evidence["manifest_sha256"],
                manifest_parser_sha256=evidence["parser_sha256"], as_of=evidence["as_of"], created_at=created,
                accounting_version=ACCOUNTING_VERSION, scope=COST_SCOPE, state="COMPLETE",
                code_sha=self.code_sha, asset_count=len(assets), valuation=valuation,
                asset_rows_sha256=digest([[mint, sha256] for mint, _, sha256 in encoded_assets]),
                stock_current_verified=False, whole_pnl=None,
            )
            result["run_sha256"] = digest(result)
        except ManifestError as exc:
            raise CostStoreError(exc.code, exc.http_status) from None
        except CostStoreError:
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError, ArithmeticError, KeyError, RecursionError):
            raise CostStoreError("COST_REBUILD_UNAVAILABLE", 503) from None
        # Expensive replay stays outside the transaction. A concurrent identical
        # completion wins once, and all matching requests bind to that run.
        with self._db(write=True) as db:
            prior = self._saved(db, manifest, ACCOUNTING_VERSION, idempotency_key)
            if prior is not None:
                result = self._metadata(prior)
            else:
                db.execute("INSERT INTO cost_runs(id,manifest,version,body) VALUES(?,?,?,?)",
                           (identity, manifest, ACCOUNTING_VERSION, canonical(result)))
                db.executemany("INSERT INTO cost_assets VALUES(?,?,?,?)",
                               [(identity, *asset) for asset in encoded_assets])
            db.execute("INSERT OR IGNORE INTO cost_keys VALUES(?,?)", (idempotency_key, result["run_id"]))
            return result

    def get(self, run_id):
        _identity(run_id, "INVALID_COST_RUN_ID")
        with self._db() as db:
            return self._metadata(db.execute("SELECT * FROM cost_runs WHERE id=?", (run_id,)).fetchone()
                                  if db is not None else None)

    def page(self, *, run_id=None, mint=None, limit=100, cursor=None):
        if run_id is not None:
            _identity(run_id, "INVALID_COST_RUN_ID")
        if mint is not None and not valid_pubkey(mint):
            raise CostStoreError("INVALID_COST_MINT")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise CostStoreError("INVALID_COST_PAGE_SIZE")
        offset = 0
        if cursor is not None:
            token = _read_cursor(cursor)
            if (run_id is not None and run_id != token["run_id"]) or mint != token["mint"]:
                raise CostStoreError("COST_CURSOR_QUERY_CHANGED", 409)
            run_id, offset = token["run_id"], token["offset"]
        with self._db() as db:
            if db is None:
                raise CostStoreError("COST_RUN_NOT_FOUND", 404)
            run = (db.execute("SELECT * FROM cost_runs ORDER BY seq DESC LIMIT 1").fetchone() if run_id is None else
                   db.execute("SELECT * FROM cost_runs WHERE id=?", (run_id,)).fetchone())
            meta = self._metadata(run)
            run_id = meta["run_id"]
            index = [[item["mint"], item["sha256"]] for item in db.execute(
                "SELECT mint,sha256 FROM cost_assets WHERE run_id=? ORDER BY mint", (run_id,))]
            if len(index) != meta["asset_count"] or digest(index) != meta["asset_rows_sha256"]:
                raise CostStoreError("COST_RUN_INTEGRITY_FAILED", 503)
            where = "run_id=?" if mint is None else "run_id=? AND mint=?"
            args = (run_id,) if mint is None else (run_id, mint)
            total = db.execute("SELECT count(*) FROM cost_assets WHERE " + where, args).fetchone()[0]
            if offset and offset >= total:
                raise CostStoreError("INVALID_COST_CURSOR")
            saved = db.execute("SELECT mint,body,sha256 FROM cost_assets WHERE " + where + " ORDER BY mint LIMIT ? OFFSET ?",
                               (*args, limit, offset))
            try:
                rows = []
                for item in saved:
                    row = json.loads(item["body"])
                    if row["mint"] != item["mint"] or digest(row) != item["sha256"]:
                        raise ValueError
                    rows.append(row)
            except (ValueError, TypeError, KeyError, RecursionError):
                raise CostStoreError("COST_RUN_INTEGRITY_FAILED", 503) from None
        after = offset + len(rows)
        return {**meta, "status": "OK", "rows": rows, "returned": len(rows), "total_matching": total,
                "next_cursor": _cursor(run_id, mint, after) if after < total else None}
