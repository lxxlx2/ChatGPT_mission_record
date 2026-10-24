"""Resolve remaining 7 positive asset identities in frozen Spot511 D1 research.

Pure offline overlay, preserves all event IDs and timestamps. Distinguishes
football fan tokens from ordinary crypto protocol utility and securities.
No automated classification into historically trade-eligible opportunities.
"""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit

from .spot_g3_positive_bound import g3_positive_identity_bound, PositiveBoundError

CATEGORIES = frozenset({
    "CRYPTO_NETWORK_PROTOCOL_UTILITY", "FAN_TOKEN_SCOPE_REQUIRES_DECISION"
})
SCHEMA = "MONSTER_SPOT511_SEVEN_PRE_EVENT_REMAINING_ASSET_IDENTITIES_V1"
WINDOW_FIRST_MS = 1792274760000
MONITOR_TAG_SENSITIVITY_ONLY = frozenset({
    "AVAUSDT", "GNSUSDT", "QKCUSDT", "SOPHUSDT"
})


def resolve_all_46_asset_types(replay, core26, securities79, last7):
    baseline = g3_positive_identity_bound(replay, core26, securities79)
    if (baseline["raw_setup_events_preserved"] != 46 or
        baseline["positively_source_crypto_identity_count"] != 37 or
        baseline["positively_source_security_excluded_events"] != 2 or
        baseline["unresolved_identity_events"] != 7):
        raise PositiveBoundError("FINAL7_FROZEN_BASELINE_DRIFT")
    if not isinstance(last7, dict) or last7.get("schema") != SCHEMA:
        raise PositiveBoundError("FINAL7_MANIFEST_SCHEMA")
    if last7.get("fixed_original_replay_sha256") != replay.get("replay_inner_json_sha256"):
        raise PositiveBoundError("FINAL7_REPLAY_SHA_DRIFT")
    events = replay["complete_46_original_core_setups"]
    all_symbols = {e["symbol"] for e in events}
    old_crypto = {r["symbol"] for r in core26["rows"]}
    known_securities = {s for a in securities79["announcements"] for s in a["positive_bstock_symbols"]}
    unknown = all_symbols - old_crypto - known_securities
    if unknown != set(baseline["unresolved_symbols"]):
        raise PositiveBoundError("FINAL7_UNKNOWN_CENSUS_DRIFT")
    entries = last7.get("official_positive_identity_rows")
    if not isinstance(entries, list) or len(entries) != 7:
        raise PositiveBoundError("FINAL7_ROW_DENOMINATOR")
    by_symbol = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise PositiveBoundError("FINAL7_MALFORMED_ROW")
        symbol = entry.get("symbol")
        if (not isinstance(symbol, str) or symbol in by_symbol or symbol not in unknown or
            entry.get("category") not in CATEGORIES or not isinstance(entry.get("asset_name"), str)):
            raise PositiveBoundError("FINAL7_MALFORMED_OR_CONFLICTING_IDENTITY")
        date_text = entry.get("source_published_utc")
        if not isinstance(date_text, str) or not date_text.endswith("Z"):
            raise PositiveBoundError("FINAL7_TIME_MISSING")
        try:
            published = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise PositiveBoundError("FINAL7_BAD_OFFICIAL_TIME") from exc
        if int(published.timestamp()*1000) >= WINDOW_FIRST_MS:
            raise PositiveBoundError("FINAL7_SOURCE_NOT_PRE_EVENT")
        link = entry.get("official_url")
        if not isinstance(link, str):
            raise PositiveBoundError("FINAL7_UNTRUSTED_OFFICIAL_URL")
        url = urlsplit(link)
        if (url.scheme != "https" or url.hostname != "www.binance.com" or
            not (url.path.startswith("/en/support/") or url.path.startswith("/en-AE/support/")
                 or url.path.startswith("/en/research/"))):
            raise PositiveBoundError("FINAL7_UNTRUSTED_OFFICIAL_URL")
        by_symbol[symbol] = entry
    if set(by_symbol) != unknown:
        raise PositiveBoundError("FINAL7_POSITIVE_CENSUS_NOT_COMPLETE")
    count = Counter()
    fan_events = []
    resolved = []
    for event in events:
        kind = ("CRYPTO_NETWORK_PROTOCOL_UTILITY" if event["symbol"] in old_crypto else
                "TOKENIZED_STOCK_OUT_OF_SCOPE" if event["symbol"] in known_securities else
                by_symbol[event["symbol"]]["category"])
        count[kind] += 1
        if kind == "FAN_TOKEN_SCOPE_REQUIRES_DECISION":
            fan_events.append(event["event_id"])
        resolved.append({
            "event_id": event["event_id"], "symbol": event["symbol"],
            "observed_ms": event["observed_ms"], "asset_identity_class": kind,
            "official_source": by_symbol[event["symbol"]]["official_url"]
                if event["symbol"] in by_symbol else None
        })
    if (count["CRYPTO_NETWORK_PROTOCOL_UTILITY"] != 41 or
        count["FAN_TOKEN_SCOPE_REQUIRES_DECISION"] != 3 or
        count["TOKENIZED_STOCK_OUT_OF_SCOPE"] != 2 or
        sum(count.values()) != 46):
        raise PositiveBoundError("FINAL7_CATEGORY_RECONCILIATION_FAILED")
    monitor_count = sum(1 for e in events if
        e["symbol"] in MONITOR_TAG_SENSITIVITY_ONLY and
        (e["symbol"] in old_crypto or
         by_symbol.get(e["symbol"], {}).get("category") == "CRYPTO_NETWORK_PROTOCOL_UTILITY"))
    if monitor_count != 6:
        raise PositiveBoundError("MONITORING_TAG_SENSITIVITY_COHORT_DRIFT")
    raw_dailies = Counter(datetime.fromtimestamp(e["observed_ms"]/1000, timezone.utc)
                         .date().isoformat() for e in events)
    return {
        "schema": "MONSTER_SPOT511_EXACT_46_G3_ASSET_TYPE_PARTITION_V1",
        "original_replay_sha256": replay["replay_inner_json_sha256"],
        "original_run_id": replay.get("run_id"),
        "raw_setup_count": 46, "unmodified_original_setups": True,
        "crypto_protocol_utility_setups": count["CRYPTO_NETWORK_PROTOCOL_UTILITY"],
        "separately_scoped_chiliz_fan_token_setups": count["FAN_TOKEN_SCOPE_REQUIRES_DECISION"],
        "verified_tokenized_stock_setups": count["TOKENIZED_STOCK_OUT_OF_SCOPE"],
        "asset_identity_unresolved_setups": 0,
        "raw_setup_utc_dates": dict(sorted(raw_dailies.items())),
        "full_seven_day_G3_attention_ceiling": 35,
        "core_crypto_type_only_7day_conditional_mean": 41/7,
        "core_plus_fan_token_7day_conditional_mean": 44/7,
        # Stage77 G3 tests attention load, not a particular account's ability
        # to place an order. Never subtract Monitoring Tag quizzes from G3.
        "G3_raw_upgrade_events_are_attention_not_trade_orders": True,
        "G3_crypto_type_signal_lower_bound": 41,
        "G3_over_ceiling_even_if_remaining_source_has_zero_new_setups": True,
        "G3_historical_subset_attention_ceiling_status": "EXCEEDED_WITH_CRYPTO_TYPE_POSITIVE_EVIDENCE",
        "G3_full_4599_publisher_source_and_PIT": "NOT_PROVEN",
        # Monitoring Tag quizzes are a distinct Stage77 G4 per-account issue.
        "G4_monitoring_tag_account_permission_sensitivity": {
            "affected_crypto_type_setup_events": monitor_count,
            "if_all_accounts_cannot_trade_tagged_core_events": 41-monitor_count,
            "if_fan_tokens_included_and_all_tagged_unavailable": 44-monitor_count,
            "source_type": "ACCOUNT_QUIZ_UNVERIFIED_NOT_A_DELISITING_FACT",
            "cannot_subtract_from_G3_attention_events": True,
        },
        "fan_token_in_scope_formal_decision": "UNRESOLVED_FROZEN_SCOPE_INTERPRETATION",
        "historical_account_permissions": "UNKNOWN",
        "historical_dynamic_listing_and_PIT": "UNKNOWN",
        "actual_fee_net_execution": "UNKNOWN",
        "G3": "NOT_PASSED_G3_ATTENTION_LOWER_BOUND_EXCEEDED_BUT_FULL_SOURCE_AND_PIT_PENDING",
        "G6": "NO_GO",
        "fan_token_event_ids": sorted(fan_events),
        "actual_events": resolved,
        "no_new_trade_mail_schedule_deploy": True
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description="Offline G3 asset type ledger, original SETUP IDs unchanged")
    p.add_argument("--replay", required=True, type=Path)
    p.add_argument("--crypto26", required=True, type=Path)
    p.add_argument("--securities79", required=True, type=Path)
    p.add_argument("--final7", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise PositiveBoundError("OUTPUT_ALREADY_EXISTS")
    out = resolve_all_46_asset_types(*[
        json.loads(p.read_text()) for p in
        (args.replay, args.crypto26, args.securities79, args.final7)
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as fp:
        json.dump(out,fp,ensure_ascii=False,sort_keys=True,indent=2)
        fp.write("\n")
    print(json.dumps({k:out[k] for k in
        ("raw_setup_count","crypto_protocol_utility_setups",
         "separately_scoped_chiliz_fan_token_setups","verified_tokenized_stock_setups",
         "asset_identity_unresolved_setups","G6")}))


if __name__ == "__main__":
    main()
