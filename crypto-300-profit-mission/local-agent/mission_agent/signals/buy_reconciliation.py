"""Offline S08 overlay: compare projected buys against per-signature expectations."""
from collections import Counter
from datetime import datetime
import math

from ..mission_control.archived_wallet_facts import read_archived_classification
from .buy_admission import EXCLUDED_MINTS, admit_buy, exact_mint, needs_archive_replay, qualification
from .category_evidence import read_scanner_category_evidence
from .reconciliation import SHA256, ReconciliationError, _matches, _object


def _latency(observed, at):
    if type(at) is not int or at <= 0:
        return None
    if isinstance(observed, str):
        try:
            stamp = datetime.fromisoformat(observed)
            observed = stamp.timestamp() if stamp.tzinfo else None
        except (ValueError, OSError, OverflowError):
            observed = None
    if type(observed) not in (int, float) or not math.isfinite(observed) or observed < at:
        return None
    return round(observed - at, 3)


def _timing(values):
    known = sorted(value for value in values if value is not None)
    size = len(known)
    # Match the acceptance reports' nearest-rank definition, including for an
    # even-sized or small sample. Missing clocks never enter the denominator.
    def percentile(percent):
        return known[(percent * size + 99) // 100 - 1] if size else None
    return {"sample_count": size, "unknown_count": len(values) - size,
            "minimum_seconds": known[0] if size else None,
            "maximum_seconds": known[-1] if size else None,
            "percentile_method": "NEAREST_RANK",
            "p50_seconds": percentile(50), "p95_seconds": percentile(95)}


def _recognized_exclusion(event, assets):
    classification = event.get("classification")
    if classification in ("FAILED_TX", "PASSIVE_TRANSFER", "ATA_CREATE", "FEE"):
        return True
    trade = event.get("trade")
    if classification != "ACTIVE_TRADE" or not isinstance(trade, dict):
        return False
    if trade.get("direction") == "SELL":
        return True
    mint = trade.get("mint")
    if trade.get("direction") != "BUY" or not exact_mint(mint):
        return False
    asset = assets.get(mint)
    return mint in EXCLUDED_MINTS or bool(asset and asset.status == "EXCLUDED")


def _valid_leg_index(value):
    return type(value) is int and value >= 0


def _expected_legs(value):
    # A legacy single Mint asserts exactly one buy. Multi-buy references bind
    # each leg to its outer instruction, even when multiple legs buy one Mint.
    if value is False or exact_mint(value):
        return value
    if (not isinstance(value, list) or not value
            or any(not isinstance(row, dict) or set(row) != {"leg_index", "mint"}
                   or not _valid_leg_index(row["leg_index"]) or not exact_mint(row["mint"]) for row in value)
            or len({row["leg_index"] for row in value}) != len(value)):
        raise ReconciliationError("BUY_EXPECTATION_MINT_OR_FALSE_AND_SHA256_REQUIRED")
    return sorted((row["leg_index"], row["mint"]) for row in value)


def _indexed_buy_facts(db, source, event, assets, wallet, sig, slot, archive_root, legacy_archive_root):
    rows = db.execute("SELECT * FROM trades WHERE wallet=? AND signature=? "
                      "AND side IN ('BUY','ADD','REENTRY')", (wallet, sig)).fetchall()
    legs = event.get("trade_legs")
    if legs is not None and (
            not isinstance(legs, list) or any(not isinstance(leg, dict) or not exact_mint(leg.get("mint"))
                                              or not _valid_leg_index(leg.get("leg_index")) for leg in legs)):
        return [], "INDEXED_BUY_LEG_IDENTITY_UNVERIFIED", False
    recorded = {(leg["mint"], leg["leg_index"]) for leg in (legs or []) if leg.get("direction") == "BUY"}
    facts, unresolved, excluded_legs = [], None, 0
    indexed = set()
    for row in rows:
        identity = {"wallet": wallet, "signature": sig, "slot": slot, "block_time": source["block_time"],
                    "raw_hash": source["raw_hash"], "mint": row["mint"]}
        leg = (_object(row["body"]) or {}) if "body" in row.keys() else {}
        index = leg.get("leg_index")
        if legs:
            key = (row["mint"], index)
            if not _valid_leg_index(index) or key not in recorded or key in indexed:
                unresolved = "INDEXED_BUY_LEG_IDENTITY_UNVERIFIED"
                continue
            indexed.add(key)
            identity["leg_index"] = index

        fact = admit_buy(event, assets, **identity)
        asset = assets.get(row["mint"])
        if fact is not None:
            facts.append((index, fact["mint"]))
        elif row["mint"] in EXCLUDED_MINTS or (asset and asset.status == "EXCLUDED"):
            excluded_legs += 1
        elif not legs and needs_archive_replay(event, identity):
            replay = None
            if archive_root is not None:
                replay = read_archived_classification(archive_root, {
                    "sig": sig, "wallet": wallet, "slot": slot, "at": source["block_time"],
                    "raw_sha256": source["raw_hash"],
                }, legacy_archive_root=legacy_archive_root)
            if replay is None:
                unresolved = "LEGACY_BUY_ARCHIVE_UNAVAILABLE"
            else:
                fact = admit_buy(replay, assets, **identity)
                if fact is not None:
                    facts.append((index, fact["mint"]))
                elif admit_buy(replay, assets, **identity, allow_unpriced=True):
                    unresolved = "LEGACY_BUY_PAYMENT_UNPROVEN"
                elif _recognized_exclusion(replay, assets):
                    excluded_legs += 1
                else:
                    unresolved = "LEGACY_BUY_EVIDENCE_INCONCLUSIVE"
        elif admit_buy(event, assets, **identity, allow_unpriced=True):
            unresolved = "BUY_PAYMENT_UNPROVEN"
        elif legs:
            unresolved = "BUY_LEG_EVIDENCE_UNPROVEN"
    if indexed != recorded:
        unresolved = "INDEXED_BUY_LEG_IDENTITY_UNVERIFIED"
    return facts, unresolved, bool(rows) and excluded_legs == len(rows)


def audit_buys(db, reference, result, path, sha256, as_of, *,
               archive_root=None, legacy_archive_root=None):
    if reference["person_id"] != "frank":
        raise ReconciliationError("BUY_AUDIT_FRANK_ONLY")
    if not _matches(SHA256, sha256) or type(as_of) is not int or not 0 < as_of <= 4_000_000_000:
        raise ReconciliationError("BUY_QUALIFICATION_PIN_REQUIRED")
    try:
        manual_assets = qualification(path, as_of, sha256=sha256)
    except (ValueError, RecursionError) as error:
        if str(error) == "QUALIFICATION_SHA256_MISMATCH":
            raise ReconciliationError("BUY_QUALIFICATION_SHA256_MISMATCH") from None
        raise ReconciliationError("BUY_QUALIFICATION_INVALID") from None
    # The SQLite backup hash also pins its automatic observations. Match the
    # buy view's cutoff and preserve explicit manual overrides.
    assets = read_scanner_category_evidence(db, as_of)
    assets.update(manual_assets)

    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
    if "trades" not in tables:
        raise ReconciliationError("BUY_AUDIT_TRADE_TABLE_REQUIRED")
    detection_timing = "signature_detections" in tables and "seen_at" in {
        r[1] for r in db.execute("PRAGMA table_info(signature_detections)")
    }
    counts = Counter(dict.fromkeys(("EXPECTED_IN", "EXPECTED_OUT", "MATCHED_IN", "MATCHED_OUT",
                                   "MISSED", "UNEXPECTED", "WRONG_MINT", "PENDING", "UNRESOLVED"), 0))
    detection_times, index_times = [], []
    for tx, row in zip(reference["transactions"], result["rows"], strict=True):
        explicit = "expected_frank_buy" in tx
        expected = _expected_legs(tx["expected_frank_buy"]) if explicit else None
        if explicit and not _matches(SHA256, tx.get("expectation_sha256")):
            raise ReconciliationError("BUY_EXPECTATION_MINT_OR_FALSE_AND_SHA256_REQUIRED")
        if explicit:
            counts["EXPECTED_OUT" if expected is False else "EXPECTED_IN"] += 1
        wallet, sig = reference["wallet"], row["signature"]
        indexed = row["stages"]["indexed"]["status"]
        event, facts, source = {}, [], None
        unresolved, excluded_legs = None, False
        if indexed == "MATCH":
            source = db.execute("SELECT * FROM signatures WHERE wallet=? AND signature=?", (wallet, sig)).fetchone()
            event = _object(source["body"]) or {}
            facts, unresolved, excluded_legs = _indexed_buy_facts(
                db, source, event, assets, wallet, sig, tx["slot"], archive_root, legacy_archive_root,
            )
        mint = facts[0][1] if len(facts) == 1 else None
        if not explicit:
            status = "UNRESOLVED"
        elif indexed == "UNKNOWN":
            status = "PENDING"
        elif indexed != "MATCH":
            status = "MISSED" if expected is not False and indexed == "MISSING" else "UNRESOLVED"
        elif expected is False:
            # A known buy disproves this exclusion even when another leg is unknown.
            status = ("UNEXPECTED" if facts else "MATCHED_OUT" if not unresolved
                      and (excluded_legs or _recognized_exclusion(event, assets)) else "UNRESOLVED")
        elif unresolved:
            status = "UNRESOLVED"
        elif not facts:
            status = "MISSED"
        elif isinstance(expected, list):
            status = "MATCHED_IN" if Counter(facts) == Counter(expected) else "WRONG_MINT"
        else:
            status = "MATCHED_IN" if mint == expected else "WRONG_MINT"
        counts[status] += 1
        admission = {"status": status, "expected_mint_or_false": tx.get("expected_frank_buy"), "projected_mint": mint}
        if isinstance(expected, list) or len(facts) > 1:
            admission["projected_buys"] = [
                {"leg_index": index, "mint": projected} for index, projected in sorted(
                    facts, key=lambda pair: (-1 if pair[0] is None else pair[0], pair[1]))]
        if unresolved:
            admission["reason"] = unresolved
        row["buy_admission"] = admission
        if status == "MATCHED_IN":
            detected = None
            if detection_timing and row["stages"]["detection"]["status"] == "MATCH":
                detected = db.execute("SELECT seen_at FROM signature_detections WHERE wallet=? AND signature=?",
                                      (wallet, sig)).fetchone()["seen_at"]
            at = source["block_time"]
            detection_times.append(_latency(detected, at))
            index_times.append(_latency(source["seen_at"], at))
    status = ("GAPS" if any(counts[k] for k in ("MISSED","UNEXPECTED","WRONG_MINT")) else
              "PARTIAL" if not result["rows"] or result["unexpected_indexed_signatures"]
              or any(counts[k] for k in ("PENDING","UNRESOLVED")) else
              "MATCHED_WITHIN_SUPPLIED_WINDOW")
    return {"status": status, "counts": dict(counts), "qualifications_sha256": sha256,
            "qualification_as_of": as_of, "latency_scope": "MATCHED_BUYS_ONLY; SUPPLIED_LOCAL_CLOCKS",
            "chain_to_detection": _timing(detection_times), "chain_to_index": _timing(index_times),
            "delivery_timing": "NOT_VERIFIED", "reference_provenance": "CALLER_SUPPLIED_EXPECTATIONS"}
