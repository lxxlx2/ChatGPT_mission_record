"""Explicit amount-free analysis runs and durable local risk updates."""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import base64
import json
import math
from pathlib import Path
import re
import sqlite3
import time
import uuid

from ..meme.holder_ranks import valid_pubkey
from .archived_wallet_facts import _signature
from .evidence_manifests import canonical, digest
from .f01_source_view import WINDOW_SECONDS
from .market_observations import CHAIN, SOURCE
from .wallet_activity import connect

ANALYSIS_VERSION = "frank-amount-free-risk-v1"
RUN_ID = re.compile(r"[0-9a-f]{32}")
SHA = re.compile(r"[0-9a-f]{64}")
GIT_SHA = re.compile(r"[0-9a-f]{40}")
MARK_AGE = 60
SCOPE = "LOCAL_RESEARCH_RISK_UPDATES"
KINDS = frozenset({
    "SELL_OBSERVED", "REENTRY_OBSERVED", "PRICE_REFERENCE_STALE",
    "ABOVE_VERIFIED_BUY_REFERENCE", "EVIDENCE_GAP", "POSITION_REDUCTION_OBSERVED",
})
REFS = frozenset({"facts_sha256", "fact_manifest_id", "fact_as_of", "position_sha256", "market_sha256", "cost_sha256"})
MISSING = frozenset({
    "CANDIDATE_EVENT_AFTER_AS_OF", "LATEST_ACTION_NOT_PROVEN", "V1_SOURCE_SIGNAL_NOT_VERIFIED",
    "POSITION_STATE_UNKNOWN", "VERIFIED_COMPARABLE_FRANK_BUY_PRICE_UNAVAILABLE", "MARKET_REFERENCE_MISSING",
    "MARKET_REFERENCE_MINT_OR_CHAIN_MISMATCH", "MARKET_REFERENCE_UNVERIFIABLE", "MARKET_REFERENCE_AFTER_AS_OF",
    "MARKET_REFERENCE_STALE", "COMPARABLE_CURRENCY_CONVERSION_UNAVAILABLE", "LATEST_SLOT_ORDER_UNVERIFIED",
})


class RiskRunError(ValueError):
    def __init__(self, code, http_status=400):
        self.code, self.http_status = code, http_status
        super().__init__(code)


def _matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _time(value):
    if type(value) not in (int, float, str):
        return None
    try:
        when = float(value)
    except (ValueError, OverflowError):
        return None
    return when if math.isfinite(when) and 0 < when < 4_000_000_000 else None


def _refs(value, requested, as_of):
    if not isinstance(value, dict) or set(value) - REFS or not _matches(SHA, value.get("facts_sha256")):
        raise ValueError("INVALID_FACTS_REFERENCE")
    result = {key: value.get(key) for key in sorted(REFS)}
    for key, item in result.items():
        if key == "fact_as_of":
            cutoff = _time(item)
            if cutoff is None or cutoff > as_of:
                raise ValueError("INVALID_SOURCE_CUTOFF")
            result[key] = cutoff
            continue
        pattern = RUN_ID if key == "fact_manifest_id" else SHA
        if item is not None and not _matches(pattern, item):
            raise ValueError("INVALID_SOURCE_REFERENCE")
    if requested is not None and result["fact_manifest_id"] != requested:
        raise RiskRunError("RISK_INPUT_MANIFEST_MISMATCH", 409)
    return result


def _position(value, mint, as_of, ref):
    if not ref or not isinstance(value, dict) or value.get("mint") != mint or value.get("verification") != "COMPLETE_CAPTURE":
        return None
    amount, decimals, when = value.get("raw_amount"), value.get("decimals"), _time(value.get("observed_at"))
    if not (_matches(re.compile(r"(?:0|[1-9][0-9]{0,19})"), amount)
            and int(amount) < 2**64 and type(decimals) is int and 0 <= decimals <= 255 and when and when <= as_of):
        return None
    return {"raw_amount": amount, "decimals": decimals, "observed_at": when, "snapshot_sha256": ref}


def _verified_market(reference, mint, as_of):
    if (not isinstance(reference, dict) or reference.get("mint") != mint or reference.get("chain_id") != CHAIN
            or reference.get("source") != SOURCE or reference.get("currency") != "USD"
            or reference.get("status") != "OK"):
        return None
    when = _time(reference.get("observed_at"))
    ref = reference.get("observation_sha256")
    if not when or when > as_of or not _matches(SHA, ref):
        return None
    if digest({key: value for key, value in reference.items() if key != "observation_sha256"}) != ref:
        return None
    return {"observed_at": when, "sha256": ref}


def _buy_cap(price, market, as_of):
    if not market or as_of - market["observed_at"] > MARK_AGE:
        return None
    evidence = price.get("conversion_evidence")
    bought = _time(price.get("buy_observed_at"))
    if (price.get("status") != "COMPARABLE_REFERENCE_CHANGE" or not isinstance(evidence, dict)
            or evidence.get("target_observation_sha256") != market["sha256"]
            or not _matches(SHA, evidence.get("usdc_observation_sha256")) or not bought or bought > as_of):
        return None
    try:
        cost = Decimal(str(price.get("buy_price_usdc")))
        mark = Decimal(str(price.get("market_price_usdc")))
        if cost.is_finite() and mark.is_finite() and 0 < cost < mark:
            return [bought, str(cost.normalize())]
    except (InvalidOperation, ValueError):
        pass
    return None


def _project(row, refs, as_of):
    mint = row.get("mint")
    if not valid_pubkey(mint) or row.get("chain") != CHAIN:
        raise ValueError("INVALID_RISK_SUBJECT")
    raw_facts = row.get("facts")
    facts = {x for x in raw_facts if isinstance(x, str)} if isinstance(raw_facts, list) else set()
    raw_missing = row.get("missing")
    missing = sorted({x for x in raw_missing if isinstance(x, str) and x in MISSING}) if isinstance(raw_missing, list) else []
    side = row.get("latest_side")
    at, signature = _time(row.get("latest_action_at")), row.get("latest_signature")
    if side not in ("BUY", "SELL") or f"FRANK_LATEST_ACTION_{side}" not in facts or not at or at > as_of or not _signature(signature):
        at, signature, side = None, None, None
    reentry = None
    original = row.get("reentry")
    if side == "BUY" and isinstance(original, dict):
        event_at, event_sig = _time(original.get("observed_at")), original.get("signature")
        if event_at and event_at <= at and _signature(event_sig):
            reentry = {"at": event_at, "signature": event_sig}
    if (reentry is None and side == "BUY" and row.get("pattern") == "REENTRY_WATCH" and
            "REENTRY_OBSERVE_ONLY" in facts and row.get("reentry_latest_verified") is True):
        reentry = {"at": at, "signature": signature}
    price = row.get("price")
    price = price if isinstance(price, dict) else {}
    market = _verified_market(row.get("market_reference"), mint, as_of) if refs["market_sha256"] else None
    signal = row.get("source_signal_id")
    fact_id = row.get("latest_fact_id")
    return {
        "mint": mint, "action_at": at, "side": side, "signature": signature,
        "source_signal_id": signal if _matches(SHA, signal) else None,
        "event_fact_id": fact_id if _matches(SHA, fact_id) else None,
        "sell_review": "FRANK_SELL_OBSERVED_REVIEW_RISK" in facts,
        "reentry": reentry, "missing": missing, "market": market, "above_buy": _buy_cap(price, market, as_of),
        "position": _position(row.get("position"), mint, as_of, refs["position_sha256"]),
    }


def _events(current, prior, as_of):
    """Yield messages for proved events and material evidence state transitions."""
    at = current["action_at"]
    newest = prior.get("action_at")
    reentry = current["reentry"]
    if at is not None and (newest is None or newest <= at) and 0 <= as_of - at <= WINDOW_SECONDS:
        if current["side"] == "SELL" and current["sell_review"]:
            signature = current["signature"]
            yield "SELL_OBSERVED", signature, at, signature, "VERIFIED_FRANK_SELL"
        if (reentry is not None and 0 <= as_of - reentry["at"] <= WINDOW_SECONDS
                and (newest is None or reentry["at"] >= newest)):
            signature = reentry["signature"]
            yield "REENTRY_OBSERVED", signature, reentry["at"], signature, "VERIFIED_FRANK_REENTRY"
    if at is None or newest is not None and at < newest:
        current["action_at"] = newest

    market = current["market"]
    former = prior.get("market")
    if market and former and market["observed_at"] < former["observed_at"]:
        current["market"], current["above_buy"] = former, prior.get("above_buy")
    elif market:
        if (former == market and prior.get("as_of", 0) - market["observed_at"] <= MARK_AGE
                and as_of - market["observed_at"] > MARK_AGE):
            yield "PRICE_REFERENCE_STALE", market["sha256"], market["observed_at"], None, "CAPTURED_MARKET_REFERENCE_EXPIRED"
        above_buy = current["above_buy"]
        if above_buy is not None and above_buy != prior.get("above_buy"):
            # Quote movement while already above the same buy reference does not
            # create another update. A different reference needs new evidence.
            yield "ABOVE_VERIFIED_BUY_REFERENCE", [above_buy, market["sha256"]], market["observed_at"], None, "COMPARABLE_PRICE_ABOVE_VERIFIED_BUY"
    elif former:
        current["market"] = former

    if current["missing"] and current["missing"] != prior.get("missing"):
        witness = [current["missing"], prior.get("last_update_id")]
        yield "EVIDENCE_GAP", witness, as_of, None, "REQUIRED_EVIDENCE_UNAVAILABLE"

    position, previous = current["position"], prior.get("position")
    if position and previous and position["observed_at"] > previous["observed_at"]:
        if (position["snapshot_sha256"] != previous["snapshot_sha256"]
                and position["decimals"] == previous["decimals"]
                and int(position["raw_amount"]) < int(previous["raw_amount"])):
            yield ("POSITION_REDUCTION_OBSERVED", [previous["snapshot_sha256"], position["snapshot_sha256"]],
                   position["observed_at"], None, "TOKEN_BALANCE_DECREASE_BETWEEN_BOUND_CAPTURES")
    elif previous:
        current["position"] = previous


def _encode_cursor(value):
    return base64.urlsafe_b64encode(canonical(value).encode()).decode().rstrip("=")


def _cursor(value, mint, kind):
    try:
        if not isinstance(value, str) or not 1 <= len(value) <= 1024:
            raise ValueError
        parsed = json.loads(base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True))
        if (not isinstance(parsed, dict) or set(parsed) != {"store", "mint", "kind", "fence", "before"}
                or not _matches(RUN_ID, parsed["store"]) or type(parsed["fence"]) is not int
                or type(parsed["before"]) is not int or not 0 < parsed["before"] <= parsed["fence"] <= 2**63-1
                or _encode_cursor(parsed) != value):
            raise ValueError
    except (ValueError, TypeError, RecursionError):
        raise RiskRunError("INVALID_RISK_CURSOR") from None
    if (parsed["mint"], parsed["kind"]) != (mint, kind):
        raise RiskRunError("RISK_CURSOR_QUERY_CHANGED", 409)
    return parsed


def _sealed(obj, field):
    return {**obj, field: digest(obj)}


def _load_sealed(record, field):
    try:
        body = json.loads(record)
        if body[field] != digest({k: v for k, v in body.items() if k != field}):
            raise ValueError
        return body
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        raise RiskRunError("RISK_STORAGE_INTEGRITY_FAILED", 503) from None


class FrankRiskRuns:
    def __init__(self, root, *, clock=time.time, code_sha="UNPINNED"):
        self.root = Path(root)
        self.path = self.root / "frank-risk-runs.sqlite"
        self.clock = clock
        self.code_sha = code_sha if _matches(GIT_SHA, code_sha) else "UNPINNED"

    @contextmanager
    def _db(self, *, write=False):
        db = None
        try:
            if self.path.is_symlink():
                raise RiskRunError("RISK_STORAGE_UNAVAILABLE", 503)
            if not write and not self.path.exists():
                yield None
                return
            if write:
                self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
                db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
                self.path.chmod(0o600)
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA synchronous=FULL")
                db.execute("BEGIN IMMEDIATE")
                db.execute("CREATE TABLE IF NOT EXISTS risk_seed(singleton INTEGER PRIMARY KEY CHECK(singleton=1), id TEXT NOT NULL)")
                db.execute("INSERT OR IGNORE INTO risk_seed VALUES(1,?)", (uuid.uuid4().hex,))
                db.execute("""CREATE TABLE IF NOT EXISTS risk_runs(
                    id TEXT PRIMARY KEY, request_key TEXT NOT NULL UNIQUE, manifest_id TEXT, body TEXT NOT NULL)""")
                db.execute("""CREATE TABLE IF NOT EXISTS risk_updates(
                    seq INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE, mint TEXT NOT NULL,
                    kind TEXT NOT NULL, body TEXT NOT NULL)""")
                db.execute("""CREATE TABLE IF NOT EXISTS risk_state(
                    mint TEXT PRIMARY KEY, body TEXT NOT NULL)""")
                db.execute("CREATE INDEX IF NOT EXISTS risk_updates_mint ON risk_updates(mint,seq)")
                db.execute("CREATE INDEX IF NOT EXISTS risk_updates_kind ON risk_updates(kind,seq)")
            else:
                db = connect(self.path)
                db.execute("BEGIN")
            yield db
            if write:
                db.commit()
        except (OSError, sqlite3.Error, ValueError) as exc:
            if isinstance(exc, RiskRunError):
                raise
            raise RiskRunError("RISK_STORAGE_UNAVAILABLE", 503) from None
        finally:
            if db is not None:
                db.close()

    @staticmethod
    def _saved(db, key, manifest_id):
        if db is None:
            return None
        row = db.execute("SELECT id, manifest_id, body FROM risk_runs WHERE request_key=?", (key,)).fetchone()
        if row is None:
            return None
        if row["manifest_id"] != manifest_id:
            raise RiskRunError("RISK_IDEMPOTENCY_CONFLICT", 409)
        saved = _load_sealed(row["body"], "run_sha256")
        if saved["run_id"] != row["id"]:
            raise RiskRunError("RISK_STORAGE_INTEGRITY_FAILED", 503)
        return saved

    def create(self, idempotency_key, input_manifest_id=None, *, load_inputs):
        if (not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 256
                or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in idempotency_key)):
            raise RiskRunError("INVALID_RISK_IDEMPOTENCY_KEY")
        if input_manifest_id is not None and not _matches(RUN_ID, input_manifest_id):
            raise RiskRunError("INVALID_RISK_INPUT_MANIFEST")
        with self._db() as db:
            prior = self._saved(db, idempotency_key, input_manifest_id)
        if prior is not None:
            return prior
        # The injected reader captures only authorized local evidence. A saved
        # request never needs a second source read, even if storage restarts.
        try:
            capture = load_inputs(input_manifest_id)
            as_of, created_at = _time(capture["as_of"]), _time(self.clock())
            if as_of is None or created_at is None or as_of > created_at:
                raise ValueError("ANALYSIS_CUTOFF_INVALID")
            refs = _refs(capture["source_refs"], input_manifest_id, as_of)
            rows = capture["rows"]
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError("INVALID_RISK_ROWS")
            projected = sorted([_project(row, refs, as_of) for row in rows], key=lambda row: row["mint"])
            if len({row["mint"] for row in projected}) != len(projected):
                raise ValueError("DUPLICATE_RISK_SUBJECT")
        except RiskRunError:
            raise
        except (ValueError, KeyError, TypeError, OSError, sqlite3.Error, OverflowError, RecursionError):
            raise RiskRunError("RISK_INPUT_UNAVAILABLE", 503) from None

        run_id = uuid.uuid4().hex
        projection_sha = digest(projected)
        created = deduped = older = 0
        with self._db(write=True) as db:
            prior = self._saved(db, idempotency_key, input_manifest_id)
            if prior is not None:
                return prior
            for row in projected:
                found = db.execute("SELECT body FROM risk_state WHERE mint=?", (row["mint"],)).fetchone()
                state = _load_sealed(found["body"], "state_sha256") if found else {}
                if state.get("as_of", 0) > as_of or state.get("fact_as_of", 0) > refs["fact_as_of"]:
                    older += 1
                    continue
                previous = state.get("last_update_id")
                for kind, witness, at, signature, reason in _events(row, state, as_of):
                    semantic = digest([ANALYSIS_VERSION, row["mint"], kind, witness])
                    update_refs = {
                        **refs,
                        "event_fact_id": row["event_fact_id"] if signature == row["signature"] else None,
                        "market_observation_sha256": row["market"]["sha256"] if row["market"] else None,
                    }
                    update = _sealed({
                        "update_id": semantic, "semantic_sha256": semantic, "kind": kind, "mint": row["mint"],
                        "run_id": run_id, "observed_at": at, "as_of": as_of, "source_refs": update_refs,
                        "previous_update_id": previous, "reason": reason, "missing": row["missing"],
                        "source_signal_id": row["source_signal_id"], "signature": signature,
                        "analysis_version": ANALYSIS_VERSION, "notification_enabled": False,
                    }, "update_sha256")
                    cursor = db.execute("INSERT OR IGNORE INTO risk_updates(id,mint,kind,body) VALUES(?,?,?,?)",
                                        (semantic, row["mint"], kind, canonical(update)))
                    if cursor.rowcount:
                        created += 1
                        previous = semantic
                    else:
                        deduped += 1
                row_state = _sealed({**row, "as_of": as_of, "fact_as_of": refs["fact_as_of"],
                                     "last_update_id": previous}, "state_sha256")
                db.execute("INSERT OR REPLACE INTO risk_state(mint,body) VALUES(?,?)",
                           (row["mint"], canonical(row_state)))
            result = _sealed({
                "run_id": run_id, "state": "COMPLETE", "scope": SCOPE, "as_of": as_of, "created_at": created_at,
                "code_sha": self.code_sha, "analysis_version": ANALYSIS_VERSION, "source_refs": refs,
                "rows_count": len(projected), "projection_sha256": projection_sha, "created_updates": created,
                "deduped_updates": deduped, "older_rows_skipped": older, "notification_enabled": False,
            }, "run_sha256")
            db.execute("INSERT INTO risk_runs(id,request_key,manifest_id,body) VALUES(?,?,?,?)",
                       (run_id, idempotency_key, input_manifest_id, canonical(result)))
            return result

    def get(self, run_id):
        if not _matches(RUN_ID, run_id):
            raise RiskRunError("INVALID_RISK_RUN_ID")
        with self._db() as db:
            row = db.execute("SELECT body FROM risk_runs WHERE id=?", (run_id,)).fetchone() if db else None
            if row is None:
                raise RiskRunError("RISK_RUN_NOT_FOUND", 404)
            result = _load_sealed(row["body"], "run_sha256")
            if result["run_id"] != run_id:
                raise RiskRunError("RISK_STORAGE_INTEGRITY_FAILED", 503)
            return result

    def page(self, mint=None, kind=None, limit=100, cursor=None):
        if mint is not None and not valid_pubkey(mint):
            raise RiskRunError("INVALID_RISK_MINT")
        if kind is not None and (not isinstance(kind, str) or kind not in KINDS):
            raise RiskRunError("INVALID_RISK_KIND")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise RiskRunError("INVALID_RISK_PAGE_SIZE")
        token = _cursor(cursor, mint, kind) if cursor is not None else None
        result = {"status": "OK", "scope": SCOPE, "rows": [], "returned": 0,
                  "total_matching": 0, "next_cursor": None, "notification_enabled": False}
        with self._db() as db:
            if db is None:
                if token:
                    raise RiskRunError("RISK_CURSOR_SOURCE_CHANGED", 409)
                return result
            store_id = db.execute("SELECT id FROM risk_seed WHERE singleton=1").fetchone()["id"]
            if token and token["store"] != store_id:
                raise RiskRunError("RISK_CURSOR_SOURCE_CHANGED", 409)
            fence = (token["fence"] if token else
                     db.execute("SELECT COALESCE(MAX(seq),0) FROM risk_updates").fetchone()[0])
            clauses, params = ["seq<=?"], [fence]
            for name, value in (("mint", mint), ("kind", kind)):
                if value is not None:
                    clauses.append(f"{name}=?")
                    params.append(value)
            base = " AND ".join(clauses)
            total = db.execute("SELECT COUNT(*) FROM risk_updates WHERE " + base, params).fetchone()[0]
            if token:
                base += " AND seq<?"
                params.append(token["before"])
            fetched = db.execute("SELECT seq,id,mint,kind,body FROM risk_updates WHERE " + base +
                                 " ORDER BY seq DESC LIMIT ?", (*params, limit + 1)).fetchall()
            rows = []
            for item in fetched[:limit]:
                body = _load_sealed(item["body"], "update_sha256")
                if (body["update_id"], body["mint"], body["kind"]) != (item["id"], item["mint"], item["kind"]):
                    raise RiskRunError("RISK_STORAGE_INTEGRITY_FAILED", 503)
                rows.append(body)
            next_cursor = _encode_cursor({"store": store_id, "fence": fence, "before": fetched[limit-1]["seq"],
                                          "mint": mint, "kind": kind}) if len(fetched) > limit else None
            return {**result, "rows": rows, "returned": len(rows), "total_matching": total, "next_cursor": next_cursor}
