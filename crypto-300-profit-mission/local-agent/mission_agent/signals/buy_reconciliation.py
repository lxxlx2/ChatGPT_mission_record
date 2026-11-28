"""Offline S08 overlay: compare projected buys against per-signature expectations."""
from collections import Counter
from datetime import datetime
import math

from ..mission_control.archived_wallet_facts import read_archived_classification
from .buy_admission import EXCLUDED_MINTS, admit_buy, exact_mint, needs_archive_replay, qualification
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


def audit_buys(db, reference, result, path, sha256, as_of, *, archive_root=None, legacy_archive_root=None):
    if reference["person_id"] != "frank":
        raise ReconciliationError("BUY_AUDIT_FRANK_ONLY")
    if not _matches(SHA256, sha256) or type(as_of) is not int or not 0 < as_of <= 4_000_000_000:
        raise ReconciliationError("BUY_QUALIFICATION_PIN_REQUIRED")
    try:
        assets = qualification(path, as_of, sha256=sha256)
    except (ValueError, RecursionError) as error:
        if str(error) == "QUALIFICATION_SHA256_MISMATCH":
            raise ReconciliationError("BUY_QUALIFICATION_SHA256_MISMATCH") from None
        raise ReconciliationError("BUY_QUALIFICATION_INVALID") from None

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
        expected = tx.get("expected_frank_buy")
        if explicit and (not (expected is False or exact_mint(expected))
                         or not _matches(SHA256, tx.get("expectation_sha256"))):
            raise ReconciliationError("BUY_EXPECTATION_MINT_OR_FALSE_AND_SHA256_REQUIRED")
        if explicit:
            counts["EXPECTED_OUT" if expected is False else "EXPECTED_IN"] += 1
        wallet, sig = reference["wallet"], row["signature"]
        indexed = row["stages"]["indexed"]["status"]
        event, actual, source = {}, None, None
        unresolved = None
        if indexed == "MATCH":
            source = db.execute("SELECT * FROM signatures WHERE wallet=? AND signature=?", (wallet, sig)).fetchone()
            event = _object(source["body"]) or {}
            trade = db.execute("SELECT mint FROM trades WHERE wallet=? AND signature=? "
                               "AND side IN ('BUY','ADD','REENTRY')", (wallet, sig)).fetchone()
            if trade:
                identity = {"wallet": wallet, "signature": sig, "slot": tx["slot"],
                            "block_time": source["block_time"], "raw_hash": source["raw_hash"],
                            "mint": trade["mint"]}
                actual = admit_buy(event, assets, **identity)
                if actual is None and not _recognized_exclusion(event, assets):
                    if needs_archive_replay(event, identity):
                        proof = read_archived_classification(
                            archive_root, {"sig": sig, "wallet": wallet, "slot": tx["slot"],
                                           "at": source["block_time"], "raw_sha256": source["raw_hash"]},
                            legacy_archive_root=legacy_archive_root,
                        ) if archive_root is not None else None
                        if proof is None:
                            unresolved = "LEGACY_BUY_ARCHIVE_UNAVAILABLE"
                        else:
                            actual = admit_buy(proof, assets, **identity)
                            if actual is None:
                                if admit_buy(proof, assets, **identity, allow_unpriced=True):
                                    unresolved = "LEGACY_BUY_PAYMENT_UNPROVEN"
                                elif _recognized_exclusion(proof, assets):
                                    event = proof
                                else:
                                    unresolved = "LEGACY_BUY_EVIDENCE_INCONCLUSIVE"
                    elif admit_buy(event, assets, **identity, allow_unpriced=True):
                        unresolved = "BUY_PAYMENT_UNPROVEN"
        mint = actual["mint"] if actual else None
        if not explicit:
            status = "UNRESOLVED"
        elif indexed == "UNKNOWN":
            status = "PENDING"
        elif indexed != "MATCH":
            status = "MISSED" if expected is not False and indexed == "MISSING" else "UNRESOLVED"
        elif unresolved is not None:
            status = "UNRESOLVED"
        elif expected is False:
            # A missing/corrupt classifier cannot certify that the negative was recognized.
            status = "UNEXPECTED" if mint else "MATCHED_OUT" if _recognized_exclusion(event, assets) else "UNRESOLVED"
        elif not mint:
            status = "MISSED"
        else:
            status = "MATCHED_IN" if mint == expected else "WRONG_MINT"
        counts[status] += 1
        row["buy_admission"] = {"status": status, "expected_mint_or_false": expected, "projected_mint": mint}
        if unresolved is not None:
            row["buy_admission"]["reason"] = unresolved
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
