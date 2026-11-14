#!/usr/bin/env python3
"""Deterministic, offline five-owner 14-signed-tx source-grade replay.

Only four 2026 BSC exact CAs and five prespecified P2 wallets.
Neither historical signed transaction nor BNB block balance is follower PnL.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
    "pre": ("bsc-meme-address-model-v1-p4c-fiveowners-fourmajors-replay-precommit-corrected-v2-2026-10-16.json", "93ccf47b87661fd734613d5b6c45aa2ddca26cd6"),
    "manifest": ("bsc-meme-address-model-v1-p4c-fiveowners-fourmajors-original14-pre-rpc-2026-10-16.json", "723de3bb9aad1fb916eb8b958173e633d8338796"),
    "A": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partA-2026-10-16.json", "52a9d1a6661070c79e29e3a16d3f35858b7daac4"),
    "B": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partB-2026-10-16.json", "94d8eca8b73a687f5a7e9dca424757c67fc8416e"),
    "C": ("bsc-meme-address-model-v1-p4c-fiveowners-recheck14-partC-2026-10-16.json", "f1b8a739043de8e3763cfd96bc9025029ade63f4"),
    "ledger": ("bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json", "2a19dbd88c2971efff60a15894d952d0d05e64d9"),
}
EXPECTED_P2 = [15, 31, 38, 46, 44]
EXPECTED_TX_COUNTS = [4, 2, 3, 3, 2]


def need(condition, error):
    if not condition:
        raise ValueError(error)


def load(root=ROOT):
    sources = {}
    for k, (name, expected_sha) in PINS.items():
        raw = (Path(root) / name).read_bytes()
        git_sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()
        need(git_sha == expected_sha, "SOURCE_PIN_CHANGED:" + k)
        sources[k] = json.loads(raw)
    return sources


def classify(docs):
    need(set(docs) == set(PINS), "SOURCE_SET_CHANGED")
    pre, manifest, ledger = docs["pre"], docs["manifest"], docs["ledger"]
    cases = pre["cases"]
    need(pre["schema"] == "BSC_P4C_FIVE_OWNER_FOUR_EXACT_MAJOR_CORRECTED_FROZEN_COHORT_PRE_RPC_V2"
         and pre["source"]["git_blob_sha"] == PINS["ledger"][1]
         and pre["source"]["zero_based_P2_indices"] == EXPECTED_P2
         and pre["no_new_RPC_called_between_original_precommit_and_this_correction"],
         "PREQUERY_FREEZE_OR_CORRECTION_LOST")
    need([q["p2_index"] for q in cases] == EXPECTED_P2
         and [e["p2_index"] for e in manifest["cases"]] == EXPECTED_P2
         and len(cases) == len(manifest["cases"]) == 5
         and len({q["wallet"] for q in cases}) == 5
         and len({q["exact_ca"] for q in cases}) == 4
         and sum(q["source_native_scope_sign"] == "POSITIVE_NATIVE_SCOPE" for q in cases) == 2
         and sum(q["source_native_scope_sign"] == "NEGATIVE_NATIVE_SCOPE" for q in cases) == 3,
         "FIXED_FIVE_WALLET_FOUR_CA_TWO_POS_THREE_NEG_CHANGED")
    need(manifest["parent_frozen_cohort_blob_sha"] == PINS["pre"][1]
         and manifest["exact_signer_tx_count"] == 14,
         "SIGNED_SOURCE_MANIFEST_CHANGED")
    need(len(ledger["episodes"]) >= max(EXPECTED_P2) + 1, "P2_LEDGER_MISSING")
    need(all(q["p2_index"] != 42 for q in cases), "2025_IFML_FALSELY_INCLUDED_AS_2026")
    src_txs, no_dups = [], set()
    for n, (candidate, old, source) in enumerate(zip(cases, manifest["cases"], EXPECTED_TX_COUNTS)):
        original = ledger["episodes"][candidate["p2_index"]]
        need(candidate["wallet"] == original["wallet"] == old["wallet"]
             and candidate["exact_ca"] == original["exact_ca"] == old["ca"]
             and candidate["original_P2_grade"] == original["evidence_grade"]
             and candidate["source_native_scope_sign"] == original["net_classification"]
             and candidate["source_native_wallet_block_delta_wei"] == original["net_native_BNB_wallet_event_blocks_wei"]
             and candidate["major"] == original["token"] == old["token"]
             and candidate["from_block"] == original["first_block"]
             and candidate["to_block"] == original["last_block"],
             "FROZEN_P2_CASE_IDENTITY_OR_GRADE_DRIFT")
        entries = old["original_transactions"]
        need(len(entries) == source, "FROZEN_ORIGINAL_SIGNED_COUNT_CHANGED")
        need(all(candidate["from_block"] <= t["block"] <= candidate["to_block"] and
                 isinstance(t["hash"], str) and len(t["hash"]) == 66
                 for t in entries), "ORIGINAL_SIGNED_HASH_RANGE_CHANGED")
        for t in entries:
            need(t["hash"] not in no_dups, "DUPLICATE_SIGNED_HASH_ACROSS_CASES")
            no_dups.add(t["hash"])
            src_txs.append((candidate, t))
    need(len(src_txs) == 14, "SOURCE_ORIGINAL_14_LOST")
    rows = docs["A"]["cases"] + docs["B"]["cases"] + docs["C"]["cases"]
    need([len(docs[k]["cases"]) for k in ("A", "B", "C")] == [6, 6, 2]
         and len(rows) == len(src_txs), "SOURCE_RPC_REQUESTS_MISSING")
    full_count = known_success = unknown_status = 0
    for (case, signed), row in zip(src_txs, rows):
        need(row["index"] == case["p2_index"] and row["owner"] == case["wallet"]
             and row["ca"] == case["exact_ca"] and row["tx"] == signed["hash"]
             and row["block"] == signed["block"] and
             row["tx_from"] == case["wallet"] and row["tx_block"] == signed["block"]
             and row["signer_match"] is True and row["block_match"] is True
             and row["status"] == "COMPLETE_VISIBLE_FIELDS",
             "RAW_OWNER_HASH_SIGNATURE_OR_BLOCK_WRONG")
        need(row["receipt_full_JSON"] in (True, False), "RECEIPT_COMPLETENESS_LOST")
        full_count += row["receipt_full_JSON"]
        if row["receipt_status"] is None:
            unknown_status += 1
            need(not row["receipt_full_JSON"], "FULL_RECEIPT_CANNOT_HAVE_UNKNOWN_STATUS")
        else:
            need(row["receipt_status"] == "0x1", "VISIBLE_RECEIPT_FAILED")
            known_success += 1
        if row["receipt_full_JSON"]:
            need(row["gas_used"] is not None and row["effective_gas_price_wei"] is not None,
                 "MISSING_GAS_FROM_FULL_RECEIPT")
    need((full_count, known_success, unknown_status) == (5, 11, 3),
         "FORGED_ALL_RECEIPTS_SUCCESS_OR_HIDE_TRUNCATED")
    return {
        "schema": "BSC_P4C_FIVE_2026_OWNER_FOUR_MAJOR_14_TX_ORIGINAL_GRADE_REPLAY_V1",
        "p2_original_episodes": EXPECTED_P2,
        "selected_wallets": 5,
        "distinct_exact_major_ca": 4,
        "native_block_scope_positive_controls": 2,
        "native_block_scope_negative_controls": 3,
        "frozen_original_signed_transactions": 14,
        "original_signer_and_block_recheck_passed": len(rows),
        "full_receipts_parsed": full_count,
        "truncated_receipt_status_field_observed_unverified": known_success - full_count,
        "truncated_receipts_NOT_FULL_SUCCESS_VERIFIED": 14 - full_count,
        "original_receipt_status_unreadable": unknown_status,
        "selection_provenance": "HISTORICAL_V2_POSTHOC_NOT_CANONICAL_UNTOUCHED",
        "read_only_original_signer_status": "PARTIAL_NOT_ALL_RECEIPTS_VERIFIED",
        "realized_fully_attributable_cross_major_profits": "UNRESOLVED",
        "public_observer_executable_U": "UNRESOLVED",
        "P4_C": "PARTIAL", "P5": "BLOCKED", "production": "NO_GO",
        "source_blobs": {k: dict(zip(("path", "git_blob_sha"), v)) for k, v in PINS.items()},
    }


if __name__ == "__main__":
    print(json.dumps(classify(load()), ensure_ascii=False, indent=2))
