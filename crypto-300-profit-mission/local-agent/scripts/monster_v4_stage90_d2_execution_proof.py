#!/usr/bin/env python3
"""Monster D2 read-only evidence checker. No APIs, local runtime, orders, Gmail."""
from __future__ import annotations

import argparse
import collections
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
HISTORIC_PATH = E / "monster_stage88_all305_D1_post_signal_24h72h_price_paths.jsonl"
HISTORIC_GIT_BLOB = "86e96b726f677a15f5a7c8d740e3caca5c83e3fc"
SOURCE_URLS = {
    "BINANCE_USDM": "https://fapi.binance.com/fapi/v1/depth",
    "BINANCE_SPOT": "https://api.binance.com/api/v3/depth",
}
MAX_ASOF_LAG_MS = 5000
SCHEMA = "MONSTER_STAGE90_PURE_D2_SNAPSHOT_COST_EVIDENCE_V1"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def dec(raw) -> Decimal:
    if raw is None or isinstance(raw, bool):
        raise ValueError("INVALID_DECIMAL")
    try:
        d = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_DECIMAL") from None
    if not d.is_finite():
        raise ValueError("NONFINITE_NUMBER")
    return d


def result(status: str, reason: str, **kwargs) -> dict:
    return {
        "schema": SCHEMA, "status": status, "reason": reason,
        "real_buy_or_sell_fill": "NOT_OBSERVED",
        "historical_real_executable_net_profit": "UNKNOWN",
        "not_a_live_trade_signal": True,
        **kwargs,
    }


def sha_ok(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def levels(items, desc: bool) -> list[tuple[Decimal, Decimal]]:
    if not isinstance(items, list) or not 1 <= len(items) <= 1000:
        raise ValueError("INVALID_ORDERBOOK_LEVEL_COUNT")
    output = []
    for item in items:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("BAD_LEVEL_STRUCTURE")
        p, quantity = dec(item[0]), dec(item[1])
        if p <= 0 or quantity <= 0:
            raise ValueError("INVALID_PRICE_OR_DEPTH")
        output.append((p, quantity))
    for x, y in zip(output, output[1:]):
        if desc and not x[0] > y[0]:
            raise ValueError("BIDS_NOT_STRICT_DESCENDING")
        if not desc and not x[0] < y[0]:
            raise ValueError("ASKS_NOT_STRICT_ASCENDING")
    return output


def buy_with_quote(asks, quote: Decimal) -> tuple[Decimal, Decimal] | None:
    remaining = quote
    base = Decimal(0)
    for price, available in asks:
        spend = min(remaining, price * available)
        base += spend / price
        remaining -= spend
        if remaining == 0:
            break
    if remaining > 0 or base <= 0:
        return None
    return base, quote / base


def sell_base(bids, base: Decimal) -> tuple[Decimal, Decimal] | None:
    remaining = base
    gross_quote = Decimal(0)
    for price, available in bids:
        quantity = min(remaining, available)
        gross_quote += price * quantity
        remaining -= quantity
        if remaining == 0:
            break
    if remaining > 0:
        return None
    return gross_quote, gross_quote / base


def evaluate(candidate: dict, evidence: dict | None, *, notional_quote=None) -> dict:
    """Pure deterministic check: supplied proof is untrusted until external source verification."""
    if not isinstance(candidate, dict):
        raise ValueError("CANDIDATE_REQUIRED")
    venue = candidate.get("venue")
    symbol = candidate.get("symbol")
    t = candidate.get("observed_ms")
    if venue not in SOURCE_URLS or not isinstance(symbol, str) or not symbol.isalnum() or not symbol.isupper():
        return result("VENUE_UNKNOWN", "unsupported venue or invalid symbol")
    if not isinstance(t, int) or isinstance(t, bool) or t < 1_500_000_000_000:
        raise ValueError("BAD_D1_UTC_MILLISECONDS")
    if evidence is None:
        evidence = {}
    if not isinstance(evidence, dict):
        return result("SOURCE_UNKNOWN", "evidence must be a typed object")
    identity = evidence.get("identity", {})
    if not isinstance(identity, dict):
        return result("IDENTITY_UNKNOWN", "identity classification missing")
    category = identity.get("classification", "UNKNOWN")
    # Officially known non-Crypto identity is a hard exclusion, while retained in the raw D0 cohort.
    if category == "CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE":
        return result("OUT_OF_SCOPE", "source classifies underlying as a security/ETF, not Crypto")
    if category == "MULTIPLIER_MAPPING_UNVERIFIED":
        return result("MAPPING_UNKNOWN", "1000/1000000 asset identity and quantity units not verified")
    if category != "CONFIRMED_CRYPTO":
        return result("IDENTITY_UNKNOWN", "affirmative point-in-time Crypto identity absent")
    if (not sha_ok(identity.get("source_sha256")) or identity.get("source") is None
        or identity.get("verified_at_ms") is None
        or not isinstance(identity["verified_at_ms"], int)
        or identity["verified_at_ms"] > t):
        return result("IDENTITY_UNKNOWN", "Crypto evidence provenance or causal time insufficient")
    mapping = evidence.get("mapping")
    if not isinstance(mapping, dict) or mapping.get("verified") is not True \
            or not sha_ok(mapping.get("source_sha256")) or not mapping.get("quantity_unit"):
        return result("MAPPING_UNKNOWN", "book quantity / underlying unit unverified")
    if not isinstance(mapping.get("verified_at_ms"), int) or mapping["verified_at_ms"] > t:
        return result("MAPPING_UNKNOWN", "unit mapping not verified before D1")
    market = evidence.get("market_status")
    if (not isinstance(market, dict)
        or market.get("venue") != venue or market.get("symbol") != symbol
        or not sha_ok(market.get("source_sha256"))
        or not isinstance(market.get("effective_from_ms"), int)
        or not isinstance(market.get("effective_until_ms"), int)
        or not market["effective_from_ms"] <= t <= market["effective_until_ms"]):
        return result("VENUE_UNKNOWN", "historical market listing/status not verified at D1")
    if market.get("status") != "TRADING":
        return result("STATUS_NOT_TRADING", "market status was not TRADING at D1")
    book = evidence.get("book")
    if not isinstance(book, dict):
        return result("BOOK_UNKNOWN", "no archived point-in-time orderbook")
    if (book.get("venue") != venue or book.get("symbol") != symbol
        or book.get("source_url") != SOURCE_URLS[venue]
        or not sha_ok(book.get("raw_response_sha256"))
        or not isinstance(book.get("lastUpdateId"), int)):
        return result("BOOK_INVALID", "book source, identity, sequence or raw provenance invalid")
    cap, event = book.get("capture_ms"), book.get("event_ms")
    if not isinstance(cap, int) or not isinstance(event, int):
        return result("BOOK_UNKNOWN", "capture and exchange-event timestamps missing")
    if not (t <= event <= cap <= t + MAX_ASOF_LAG_MS) or cap - event > MAX_ASOF_LAG_MS:
        return result("BOOK_STALE", "orderbook response is stale, future or predates the D1 event")
    try:
        bids, asks = levels(book.get("bids"), True), levels(book.get("asks"), False)
    except (ValueError, TypeError) as e:
        return result("BOOK_INVALID", str(e))
    if bids[0][0] >= asks[0][0]:
        return result("BOOK_INVALID", "best bid >= best ask; cannot assume an executable market")
    # No default amount. Without user-specified quantity, the book can be described but not filled.
    spread_bps = (asks[0][0] / bids[0][0] - 1) * Decimal(10000)
    spread = {"best_bid": str(bids[0][0]), "best_ask": str(asks[0][0]),
              "spread_over_best_bid_bps": str(spread_bps),
              "snapshot_lastUpdateId": book["lastUpdateId"]}
    if notional_quote is None:
        return result("NOTIONAL_UNKNOWN", "no user-authorized/test quote amount", **spread)
    amount = dec(notional_quote)
    if amount <= 0:
        raise ValueError("NOTIONAL_MUST_BE_POSITIVE")
    fee = evidence.get("fees")
    if not isinstance(fee, dict) or not fee.get("source_sha256") or \
            not sha_ok(fee.get("source_sha256")) or \
            not isinstance(fee.get("effective_from_ms"), int) or \
            fee["effective_from_ms"] > t or "entry_taker_bps" not in fee or "exit_taker_bps" not in fee:
        return result("FEE_UNKNOWN", "point-in-time entry and exit taker fees unavailable", **spread)
    try:
        entry_bps = dec(fee["entry_taker_bps"])
        exit_bps = dec(fee["exit_taker_bps"])
    except ValueError:
        return result("FEE_UNKNOWN", "fee rate invalid", **spread)
    if entry_bps < 0 or exit_bps < 0 or max(entry_bps, exit_bps) >= Decimal(10000):
        return result("FEE_UNKNOWN", "fee rate out of range", **spread)
    buy = buy_with_quote(asks, amount)
    if buy is None:
        return result("DEPTH_INSUFFICIENT", "ask depth cannot fill the specified quote amount", **spread)
    base, buy_vwap = buy
    sell = sell_base(bids, base)
    if sell is None:
        return result("DEPTH_INSUFFICIENT", "bid depth cannot immediately exit acquired base", **spread)
    gross, sell_vwap = sell
    cost = (amount * (1 + entry_bps / Decimal(10000))) - (
        gross * (1 - exit_bps / Decimal(10000)))
    return result(
        "SNAPSHOT_COST_EVIDENCE_ONLY",
        "synthetic instant two-sided book walk; no proof of future exits, fills or profit",
        **spread, quote_amount=str(amount), acquired_base_quantity=str(base),
        buy_vwap=str(buy_vwap), simulated_same_snapshot_sell_vwap=str(sell_vwap),
        same_snapshot_gross_sell_quote=str(gross),
        entry_fee_bps=str(entry_bps), exit_fee_bps=str(exit_bps),
        same_snapshot_immediate_roundtrip_cost_quote=str(cost),
        same_snapshot_immediate_roundtrip_cost_bps=str(cost / amount * Decimal(10000)),
        external_provenance_revalidation_required=True,
    )


def synthetic_fixture():
    t = 1792000000000
    sha = "a" * 64
    c = {"symbol":"TESTUSDT","venue":"BINANCE_USDM","observed_ms":t}
    proof = {
      "identity":{"classification":"CONFIRMED_CRYPTO","source":"Binance original issuer+instrument map",
                  "source_sha256":sha,"verified_at_ms":t-100},
      "mapping":{"verified":True,"quantity_unit":"base_asset","source_sha256":sha,
                 "verified_at_ms":t-100},
      "market_status":{"venue":c["venue"],"symbol":c["symbol"],"status":"TRADING",
                       "effective_from_ms":t-30000,"effective_until_ms":t+30000,
                       "source_sha256":sha},
      "book":{"venue":c["venue"],"symbol":c["symbol"],"source_url":SOURCE_URLS[c["venue"]],
              "raw_response_sha256":sha,"lastUpdateId":12345,
              "capture_ms":t+2000,"event_ms":t+1800,
              "bids":[["99","2"],["98","3"]],"asks":[["101","2"],["102","3"]]},
      "fees":{"source_sha256":sha,"effective_from_ms":t-100,
              "entry_taker_bps":"10","exit_taker_bps":"10"}
    }
    return c, proof


def selftest():
    c, p = synthetic_fixture()
    assert evaluate(c, p)["status"] == "NOTIONAL_UNKNOWN"
    assert evaluate(c, p, notional_quote=100)["status"] == "SNAPSHOT_COST_EVIDENCE_ONLY"
    assert dec(evaluate(c,p,notional_quote=100)["same_snapshot_immediate_roundtrip_cost_quote"]) > 0
    assert evaluate(c,dict(p,fees=None),notional_quote=100)["status"]=="FEE_UNKNOWN"
    assert evaluate(c,p,notional_quote=1000000)["status"]=="DEPTH_INSUFFICIENT"
    stale=json.loads(json.dumps(p));stale["book"]["capture_ms"] += 20000
    assert evaluate(c,stale,notional_quote=100)["status"]=="BOOK_STALE"
    future=json.loads(json.dumps(p));future["book"]["event_ms"] = c["observed_ms"]-1
    assert evaluate(c,future,notional_quote=100)["status"]=="BOOK_STALE"
    crossed=json.loads(json.dumps(p));crossed["book"]["bids"][0][0]="102"
    assert evaluate(c,crossed,notional_quote=100)["status"]=="BOOK_INVALID"
    mixed=json.loads(json.dumps(p));mixed["book"]["symbol"]="OTHERUSDT"
    assert evaluate(c,mixed,notional_quote=100)["status"]=="BOOK_INVALID"
    thin=json.loads(json.dumps(p));thin["book"]["bids"]=[["99","0.01"]]
    assert evaluate(c,thin,notional_quote=100)["status"]=="DEPTH_INSUFFICIENT"
    unmapped=json.loads(json.dumps(p));unmapped["mapping"]["verified"]=False
    assert evaluate(c,unmapped,notional_quote=100)["status"]=="MAPPING_UNKNOWN"
    tradfi=json.loads(json.dumps(p));tradfi["identity"]["classification"]="CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE"
    assert evaluate(c,tradfi,notional_quote=100)["status"]=="OUT_OF_SCOPE"
    halt=json.loads(json.dumps(p));halt["market_status"]["status"]="BREAK"
    assert evaluate(c,halt,notional_quote=100)["status"]=="STATUS_NOT_TRADING"
    nohist=json.loads(json.dumps(p));nohist["book"]=None
    assert evaluate(c,nohist,notional_quote=100)["status"]=="BOOK_UNKNOWN"
    assert evaluate(c,{},notional_quote=100)["status"]=="IDENTITY_UNKNOWN"
    print("STAGE90_D2_READ_ONLY_CAUSAL_ORDERBOOK_SYNTHETIC_15_CASES_PASS")


def audit_historical_305():
    raw = HISTORIC_PATH.read_bytes()
    if git_blob(raw) != HISTORIC_GIT_BLOB:
        raise ValueError("STAGE90_STAGE88_HISTORIC_305_BLOB_CHANGED")
    rows = [json.loads(s) for s in raw.decode().splitlines() if s.strip()]
    if len(rows) != 305 or len({(x["date"],x["symbol"]) for x in rows}) != 305:
        raise ValueError("STAGE90_NOT_ALL_305")
    out = []
    for row in rows:
        # No historical order book or independent identity as-of proof was captured.
        cls = row["identity"]
        if cls not in ("CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE",
                       "MULTIPLIER_MAPPING_UNVERIFIED",
                       "CRYPTO_IDENTITY_UNVERIFIED"):
            raise ValueError("STAGE90_UNEXPECTED_IDENTITY")
        candidate={"symbol":row["symbol"],"venue":"BINANCE_USDM",
                   "observed_ms":int(__import__("datetime").datetime.fromisoformat(
                       row["D1_FIRST_UTC"].replace("Z","+00:00")).timestamp()*1000)}
        outcome=evaluate(candidate, {"identity":{"classification":cls}})
        out.append({"date":row["date"],"symbol":row["symbol"],"D1_UTC":row["D1_FIRST_UTC"],
                    "identity":cls,"D2_evidence_status":outcome["status"],
                    "original_D1_preserved":True})
    counts=dict(collections.Counter(x["D2_evidence_status"] for x in out))
    return {
        "schema":"MONSTER_STAGE90_EXPOSED_ALL305_D2_PROVENANCE_GAP_AUDIT_V1",
        "source_stage88_git_blob":HISTORIC_GIT_BLOB,
        "all_historic_D1":305,"status_counts":counts,"rows":out,
        "archived_book_at_actual_D1":"NONE_AVAILABLE_IN_RESEARCH_SOURCE",
        "point_in_time_crypto_identity_positive_proof":"UNAVAILABLE",
        "notional_quote":"UNSPECIFIED","execution_net_pnl":"UNKNOWN",
        "D1_G3":"REJECTED_EXPOSED","D2_historical_profit":"NOT_SCORABLE",
        "OOS":"NOT_DONE","OTHER_AI_REVIEW":"NOT_DONE",
        "MONSTER_DEPLOY":"NO_GO","GMAIL":"OFF","AUTOTRADE":"NO_GO",
        "FRANK":"UNCHANGED"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--audit-historical",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.selftest:
        selftest()
    elif args.audit_historical:
        report=audit_historical_305()
        raw=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(raw)
        print("STAGE90_D2_ALL305_HISTORIC_PROOF_COUNTS "+json.dumps(
            {"population":report["all_historic_D1"],"status":report["status_counts"],
             "net_pnl":report["execution_net_pnl"]},sort_keys=True))
    else:
        p.error("explicit --selftest or --audit-historical required (no live mode)")


if __name__ == "__main__":
    main()
