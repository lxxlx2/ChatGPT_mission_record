#!/usr/bin/env python3
"""Fail-closed read-only replay: corrected post-review V1/V2/V3 cohorts, exact 2026
BNB block calendar, 14+2 original senders, and truthfully truncated receipts.
This is NOT an unbiased sample or a profitable follow-trade backtest.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
    "ledger": ("bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json", "2a19dbd88c2971efff60a15894d952d0d05e64d9"),
    "v1": ("bsc-meme-address-model-v1-p4c-fiveowners-fourmajors-replay-precommit-2026-10-16.json", "81766a70568c49ceac5e4906307b324c0a263d3f"),
    "v2": ("bsc-meme-address-model-v1-p4c-fiveowners-fourmajors-replay-precommit-corrected-v2-2026-10-16.json", "93ccf47b87661fd734613d5b6c45aa2ddca26cd6"),
    "v3": ("bsc-meme-address-model-v1-p4c-v3-review-corrected-six-episodes-2026-10-16.json", "96efbd5bd75158601af8a5008d3c1653f30a2052"),
    "header": ("bsc-meme-address-model-v1-p4c-v3-original13-block-header-calendar-2026-10-16.json", "529f5e660dff8134fd609682fa94c0c7aa89f868"),
    "partial": ("bsc-meme-address-model-v1-p4c-v3-nine-truncated-receipt-source-excerpts-2026-10-16.json", "fead633edf1a8abe91f9e308dd54918ec278ac10"),
    "extra": ("bsc-meme-address-model-v1-p4c-v3-restored-p2-13-original-two-transactions-2026-10-16.json", "7406af5caf34fae88c4cdbb60c9053e925fb194d"),
    "manifest": ("bsc-meme-address-model-v1-p4c-fiveowners-fourmajors-original14-pre-rpc-2026-10-16.json", "723de3bb9aad1fb916eb8b958173e633d8338796"),
    "A": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partA-2026-10-16.json", "52a9d1a6661070c79e29e3a16d3f35858b7daac4"),
    "B": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partB-2026-10-16.json", "94d8eca8b73a687f5a7e9dca424757c67fc8416e"),
    "C": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partC-2026-10-16.json", "f1b8a739043de8e3763cfd96bc9025029ade63f4"),
    "stage": ("BSC_MEME_STAGE23_8E6B_REPEAT_WINNER_HAJIMI_LOBSTER_IFML_CROSS_MAJOR_ROUNDS_2026-10-13.json", "6227e69fabd6c0d991add0d7ff5c6e406babd40b"),
}
V1 = [13, 31, 38, 46, 42]
V2 = [15, 31, 38, 46, 44]
V3 = [13, 15, 31, 38, 46, 44]
SUMS_WEI = {"v1": 223671359895044206, "v2": -400073738684035463,
            "v3": -146773456364646148}
MAPPING = {
    "我踏马来了": "0xc51a9250795c0186a6fb4a7d20a90330651e4444",
    "龙虾": "0xeccbb861c0dda7efd964010085488b69317e4444",
    "MARSCOIN": "0xfe189e97832da1573e4e4ff034f4ffc3a15c7777",
    "牛来": "0xbeea1d618e533a387d941f58a7d4c9b7bd377777",
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def load(root=ROOT):
    d = {}
    for key, (name, sha) in PINS.items():
        raw = (Path(root) / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()
        need(actual == sha, "SOURCE_BLOB_MISMATCH:" + key)
        d[key] = json.loads(raw)
    return d


def classify(d):
    need(set(d) == set(PINS), "SOURCES_MISSING")
    ledger = d["ledger"]["episodes"]
    have1 = d["v1"]["freeze_source"]["episode_indices_zero_based"]
    have2 = d["v2"]["source"]["zero_based_P2_indices"]
    have3 = d["v3"]["corrected_scope"]["p2_indices"]
    need((have1, have2, have3) == (V1, V2, V3),
         "H1_SELECTION_HISTORY_WAS_CHANGED")
    need(d["v3"]["type"] == "POST_REVIEW_CORRECTION_NOT_A_NEW_UNTOUCHED_PRECOMMIT"
         and d["v3"]["admission_of_V1_to_V2_change"]["removed_index_13_without_reason_in_prior_V2"]
         and d["v3"]["admission_of_V1_to_V2_change"]["p2_42_2025_dec29_invalid_calendar"],
         "H1_OUTCOME_AWARE_SWAP_NOT_DISCLOSED")
    need(set(d["v3"]["cohort_comparisons"]) == {"v1", "v2", "v3"},
         "H1_COULD_NOT_HIDE_OLDER_V1_OR_V2_DENOMINATORS")
    results = {}
    for name, indices in (("v1", V1), ("v2", V2), ("v3", V3)):
        vals = [ledger[i] for i in indices]
        signed = sum(int(x["net_native_BNB_wallet_event_blocks_wei"]) for x in vals)
        expected = d["v3"]["cohort_comparisons"][name]
        positive = sum(x["net_classification"] == "POSITIVE_NATIVE_SCOPE" for x in vals)
        negative = sum(x["net_classification"] == "NEGATIVE_NATIVE_SCOPE" for x in vals)
        owners = len({x["wallet"] for x in vals})
        cas = len({x["exact_ca"] for x in vals})
        need(signed == SUMS_WEI[name]
             and signed == int(expected["native_scope_sum_wei"])
             and expected["positive"] == positive
             and expected["negative"] == negative
             and expected["unique_wallets"] == owners
             and expected["unique_CAs"] == cas,
             "H1_SOURCE_NATIVE_V1_V2_V3_COMPARISON_MISMATCH")
        results[name] = {"selected_original_P2_indices": indices,
                         "native_block_scope_wei": str(signed),
                         "positive": positive, "negative": negative,
                         "distinct_wallets": owners, "distinct_CA": cas}
    need((results["v3"]["positive"], results["v3"]["negative"],
          results["v3"]["distinct_wallets"], results["v3"]["distinct_CA"])
         == (3, 3, 5, 4), "H1_V3_SIX_CASE_OUTCOME_DRIFT")
    need(ledger[13]["evidence_grade"] == "SETTLED_NATIVE_DIRECT_WBNB_GAS",
         "H1_RESTORED_POSITIVE_SOURCE_GRADE_LOST")
    for i in V3:
        row = ledger[i]
        need(MAPPING[row["token"]] == row["exact_ca"]
             and row["raw_token_round_closed"] is True,
             "TOKEN_EXACT_CA_OR_STOCK_DRIFT")

    hdr = d["header"]
    rows = hdr["all_13_original_block_hashes_and_integer_timestamps"]
    need(len(rows) == 13 and len({r["block"] for r in rows}) == 13,
         "H2_MISSING_OR_DUPLICATED_BLOCK_HEADERS")
    h = {x["block"]: x for x in rows}
    expected_blocks = {73339965}
    for i in V3:
        pair = hdr["historical_2026_pairs"]["p2_" + str(i)]
        need(pair == [ledger[i]["first_block"], ledger[i]["last_block"]],
             "H2_RAW_P2_BLOCK_BOUNDARY_CHANGED")
        expected_blocks.update(pair)
    need(set(h) == expected_blocks, "H2_BLOCK_HEADERS_MISSING")
    calendar = {}
    for b, r in h.items():
        ms = int(r["milliTimestamp_hex"], 16)
        t = int(r["timestamp_hex"], 16)
        actual_utc = datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(
            timespec="milliseconds").replace("+00:00", "Z")
        need(ms // 1000 == t and actual_utc == r["utc_from_integer_milliseconds"]
             and int(r["block_number_hex"], 16) == b
             and len(r["block_hash"]) == 66 and r["header_fields_checked"],
             "H2_FAKE_OR_NONREPRODUCIBLE_ORIGINAL_UTC")
        year = datetime.fromtimestamp(ms / 1000, timezone.utc).year
        need(year == (2025 if b == 73339965 else 2026),
             "H2_REAL_YEAR_BOUNDARY_WRONG")
        calendar[b] = actual_utc
    need(ledger[42]["first_block"] == 73339965
         and ledger[42]["is_2026_major_priority"] is True,
         "H2_P2_PRIORITY_FLAG_IS_NOT_DATE")
    need(calendar[93584281].startswith("2026-04-20")
         and calendar[86649314].startswith("2026-03-15"),
         "H2_ORIGINAL_13_OR_31_CALENDAR_NOT_EVIDENCED")

    original = d["manifest"]["cases"]
    need([q["p2_index"] for q in original] == V2
         and sum(len(x["original_transactions"]) for x in original) == 14,
         "SOURCE_14_ORIGINAL_SELECTION_CHANGED")
    signed = {}
    for r in original:
        for t in r["original_transactions"]:
            need(t["hash"] not in signed, "DUPLICATE_SAME_TX")
            signed[t["hash"]] = (r["p2_index"], r["wallet"], t["block"])
    old = d["A"]["cases"] + d["B"]["cases"] + d["C"]["cases"]
    need(len(old) == 14 and
         [len(d[k]["cases"]) for k in ("A", "B", "C")] == [6, 6, 2],
         "RPC_14_CASES_INCOMPLETE")
    full14 = 0
    clipped14 = {}
    for row in old:
        needle = signed.get(row["tx"])
        need(needle == (row["index"], row["owner"], row["block"])
             and row["tx_from"] == row["owner"]
             and row["tx_block"] == row["block"]
             and row["signer_match"] and row["block_match"],
             "H3_ORIGINAL_SIGNER_OR_BLOCK_NOT_VERIFIED")
        if row["receipt_full_JSON"]:
            full14 += 1
            need(row["receipt_status"] == "0x1"
                 and row["gas_used"] and row["effective_gas_price_wei"],
                 "H3_FULL_RECEIPT_SUCCESS_NOT_REAL")
        else:
            clipped14[row["tx"]] = row
    need((full14, len(clipped14)) == (5, 9),
         "H3_5_FULL_9_INCOMPLETE_CANNOT_BE_PROMOTED")
    newpartial = d["partial"]["observations"]
    need(len(newpartial) == 9
         and {x["hash"] for x in newpartial} == set(clipped14),
         "H3_ALL_NINE_UNVERIFIED_RECEIPTS_NOT_PRESERVED")
    for w in newpartial:
        need(w["evidence_grade"] == "TRUNCATED_SOURCE_WITNESS_ONLY"
             and not w["provider_JSON_parseable"]
             and w["tool_truncated_marker"]
             and w["provider_response_len"] >= 1000,
             "H3_CLIPPED_RECEIPT_AS_FULL_PROOF")
        if w["status_literal_if_visible"]:
            need(w["status_literal_if_visible"] == "0x1"
                 and w["status_direct_raw_span"] is not None
                 and '"status"' in w["status_direct_raw_span"]
                 and '"status"' in w["source_response_first_350_chars"],
                 "H3_VISIBLE_STATUS_RAW_EXCERPT_NOT_PROVEN")
        else:
            need(w["status_literal_offset"] is None,
                 "H3_NONVISIBLE_STATUS_FABRICATED")
    need(d["partial"]["summary"]["partial_visible_status"] ==
         sum(w["status_literal_if_visible"] == "0x1" for w in newpartial),
         "H3_REPLAY_STATUS_WITNESS_COUNT_DRIFT")
    extra = d["extra"]["source_txs"]
    proof = next(r for r in d["stage"]["selected_two_major_positive_receipt_proofs"]
                 if r["token"] == "龙虾" and r["round"] == 2)
    need(len(extra) == 2
         and [x["hash"] for x in extra] ==
         [proof["buy_hash"], proof["sell_hashes"][0]]
         and [x["block"] for x in extra] ==
         [proof["buy_block"], proof["last_sell_block"]]
         and all(x["signer_matches"] and x["block_matches"]
                 and x["full_receipt_parseable"]
                 and x["receipt_status_if_seen"] == "0x1" for x in extra),
         "H1_RESTORED_ORIGINAL_13_BUY_SELL_CANNOT_BE_PROVEN")
    return {
        "schema": "BSC_P4C_V3_SOURCE_HONEST_POST_REVIEW_REPLAY",
        "selection_grade": "POST_REVIEW_OUTCOME_AWARE_EXPOSED_NOT_HOLDOUT",
        "three_original_cohort_comparisons": results,
        "original_2026_calendar_first_and_last_verified_for_six_cases": 12,
        "excluded_p2_42_year": "2025_SOURCE_BLOCK",
        "original_signer_block_matched_count": len(old) + len(extra),
        "full_successful_receipts": full14 + len(extra),
        "truncated_receipts_remaining_UNVERIFIED": len(clipped14),
        "partial_status_visible_but_unverified_full_receipt":
            sum(w["status_literal_if_visible"] == "0x1" for w in newpartial),
        "not_visible_status_unverified":
            sum(w["status_literal_if_visible"] is None for w in newpartial),
        "new_cross_CA_realized_PnL": "UNRESOLVED",
        "public_executable_U": "UNRESOLVED",
        "P4_C": "PARTIAL", "P5": "BLOCKED", "PRODUCTION": "NO_GO",
        "source_pins": {k: {"path": v[0], "blob": v[1]} for k,v in PINS.items()},
    }


if __name__ == "__main__":
    print(json.dumps(classify(load()), ensure_ascii=False, indent=2))
