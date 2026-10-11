"""Replay real user-confirmed Git evidence, not a synthetic 224-mint fixture.

No RPC, tokens, credentials or production DB. CI requires the evidence branch
to be fetched at full depth. Developers without it can run normal unit tests.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from mission_agent.mission_control.wallet_watch import from_seed, merge_signature_activity

SNAPSHOT = "1cda7a289db31582f24d327c7dedd911c14475912346e1c4ff6e731a4f56a96a"
FRANK_PREFIX = "crypto-300-profit-mission/meme/local-evidence"
BRANCH = "origin/evidence/frank-ca-local"
J7 = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"


def _git(path: str) -> bytes:
    repo = Path(__file__).resolve().parents[4]
    p = subprocess.run(
        ["git", "-C", str(repo), "show", BRANCH + ":" + path],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        timeout=15,
    )
    if p.returncode:
        if os.environ.get("FRANK_EXPECT_REAL_GIT_REPLAY") == "1":
            pytest.fail("REQUIRED_REAL_FRANK_EVIDENCE_REF_NOT_FETCHED")
        pytest.skip("Real Git evidence branch is not present in this checkout")
    return p.stdout


def test_actual_mac_1720_signature_archive_replays_to_224_scoped_mints():
    path = f"{FRANK_PREFIX}/frank-transfer-history/{SNAPSHOT}.json"
    manifest = json.loads(_git(path))
    assert manifest["snapshot_id"] == SNAPSHOT
    assert manifest["record_count"] == 1720
    assert len(manifest["parts"]) == 12
    data = []
    for i, part in enumerate(manifest["parts"]):
        packet = json.loads(_git(
            f"{FRANK_PREFIX}/frank-transfer-history/{SNAPSHOT}/{part['file']}"))
        raw = base64.b64decode(packet["payload_b64"], validate=True)
        assert part["part_index"] == packet["part_index"] == i
        assert part["sha256"] == packet["part_sha256"] == hashlib.sha256(raw).hexdigest()
        data.append(raw)
    joined = b"".join(data)
    assert hashlib.sha256(joined).hexdigest() == SNAPSHOT
    actual = json.loads(joined)
    assert len(actual["records"]) == 1720
    assert actual["local_classifications"]["PASSIVE_TRANSFER"] == 1393
    assert not any(x["transfer_flows"] for x in actual["records"])

    bucket = json.loads(_git(f"{FRANK_PREFIX}/frank/2026-10-11/0715.json"))
    poll = next(x for x in bucket["events"] if x["poll_count"] == 21754)
    prior = poll["observed_watchlist"]["rows"]
    assert len(prior) == 33
    watch = from_seed([{
        "mint": x["mint"], "local_state": x["local_model_state"],
        "local_recognized_buy_count": x["local_recognized_buys"],
        "local_recognized_sell_count": x["local_recognized_sells"],
    } for x in prior])
    source_rows = [{
        "signature": row["signature"],
        "block_time": row["block_time"],
        "body": json.dumps({
            "classification": row["local_classification"],
            "evidence": {
                "wallet_is_signer": row["wallet_is_signer"],
                "wallet_token_transfer_flows": row["transfer_flows"],
                "token_balance_deltas": row["wallet_owned_token_deltas"],
            },
        }),
    } for row in actual["records"]]
    merged = merge_signature_activity(watch, source_rows)
    summary = merged["summary"]
    assert summary["total_observed"] == 224
    assert summary["original_trade_or_model_observed"] == 33
    assert summary["passive_receipt_only"] == 104
    assert summary["other_account_activity_only"] == 87
    assert merged["signature_activity_provenance"]["signature_rows_scanned"] == 1720
    assert merged["signature_activity_provenance"][
        "signature_rows_without_parsed_counterparty_flow"] == 1720
    by_mint = {x["mint"]: x for x in merged["rows"]}
    assert len(by_mint) == 224
    # This is the local-only count; never present it as all-chain J7 history.
    assert by_mint[J7]["passive_receipt_events"] == 1
    from mission_agent.mission_control.wallet_watch import annotate_known_ata_gaps
    gap_file = (Path(__file__).resolve().parents[3] / "meme" / "evidence" /
                "frank-v2-ata-index-scope-correction-2026-10-11.json")
    source = json.loads(gap_file.read_text())
    annotated = annotate_known_ata_gaps(merged, source)
    covered = {x["mint"]: x for x in annotated["rows"]}
    assert covered[J7]["owner_index_gap_status"] == "DATED_ATA_VS_OWNER_INDEX_SCOPE"
    assert covered[J7]["ata_outside_index_window_signatures"] == 0
    assert covered[J7]["ata_inside_index_window_signatures"] == 2
    assert covered[J7]["owner_index_missing_signatures"] == 2
    assert covered[J7]["ata_verified_extra_passive_receipts"] == 2
    bp = "BPxxfRCXkUVhig4HS1Lh7kZqV6SPJhzfEk4x6fVBjPCy"
    assert covered[bp]["owner_index_missing_signatures"] == 66
    assert covered[bp]["ata_outside_index_window_signatures"] == 63
    assert covered[bp]["ata_inside_index_window_signatures"] == 3
    assert covered[bp]["ata_inwindow_failed_signatures"] == 1
    assert covered[bp]["ata_inwindow_success_unverified"] == 1
    assert covered[bp]["ata_verified_extra_passive_receipts"] == 1
    assert by_mint[J7]["signature_observed_in_raw"] == "2846838050235"
    assert by_mint[J7]["signature_observed_out_raw"] == "12508217470763"
    assert by_mint[J7]["sender_cost_basis_usd"] is None
    assert all(row["is_follow_signal"] is False for row in merged["rows"])


def test_real_j7_ata_evidence_joins_main_wallet_archive_without_relabeling_buy():
    from mission_agent.mission_control.ata_backfill import (
        TOKEN_2022, derive_ata
    )
    root = Path(__file__).resolve().parents[4]
    evidence_file = (root / "crypto-300-profit-mission" / "meme" / "evidence" /
                     "frank-v2-ata-j7-and-five-account-chain-verification-2026-10-11.json")
    documented = json.loads(evidence_file.read_text())
    j7 = documented["j7"]
    associated, _ = derive_ata(documented["frank_wallet"], j7["mint"], TOKEN_2022)
    assert associated == j7["canonical_token2022_ata"]
    assert j7["ata_successful_signatures"] == 4
    assert j7["ata_failed_signatures"] == 13
    rows = []
    manifest = json.loads(_git(
        f"{FRANK_PREFIX}/frank-transfer-history/{SNAPSHOT}.json"))
    for part in manifest["parts"]:
        packet = json.loads(_git(
            f"{FRANK_PREFIX}/frank-transfer-history/{SNAPSHOT}/{part['file']}"))
        rows.append(base64.b64decode(packet["payload_b64"]))
    signatures = {x["signature"] for x in json.loads(b"".join(rows))["records"]}
    found_in_owner_index, outside_owner_index = [], []
    for transfer in j7["successful_receipts"]:
        signature = transfer["signature"]
        if signature in signatures:
            found_in_owner_index.append(signature)
        else:
            outside_owner_index.append(signature)
    assert len(found_in_owner_index) == 1
    assert len(outside_owner_index) == 2
    assert j7["newly_recovered_qty"] == "9661379.420528"
    assert j7["source_cost_status"] == "UNVERIFIED"


def test_real_bpxx_ata_pages_expose_preindex_and_inwindow_owner_index_misses():
    """Audit actual 70 finalized BPxx ATA signatures against immutable 1720 Mac rows.

    A missed *signature* is not automatically a token transfer, market trade
    or profit. The one in-window failed transaction is explicitly excluded
    from any potential successful missing-transfer classification.
    """
    from datetime import datetime, timezone
    root = Path(__file__).resolve().parents[4]
    source = json.loads((
        root / "crypto-300-profit-mission" / "meme" / "evidence" /
        "frank-v2-bpxx-ata-eight-page-bounded-signature-replay-2026-10-11.json"
    ).read_text())
    assert source["unique_signatures"] == 70
    assert source["history_entirely_verified"] is False
    assert source["acquisition_cost_usd"] is None
    assert len(source["pages"]) == 7
    assert [page["returned_count"] for page in source["pages"]] == [10] * 7
    ata_rows = [row for page in source["pages"] for row in page["entries"]]
    ata_signatures = [row["signature"] for row in ata_rows]
    assert len(set(ata_signatures)) == 70
    assert sum(row["err"] is not None for row in ata_rows) == 1

    manifest = json.loads(_git(
        f"{FRANK_PREFIX}/frank-transfer-history/{SNAPSHOT}.json"))
    chunks = []
    for part in manifest["parts"]:
        packet = json.loads(_git(
            f"{FRANK_PREFIX}/frank-transfer-history/{SNAPSHOT}/{part['file']}"))
        payload = base64.b64decode(packet["payload_b64"], validate=True)
        assert hashlib.sha256(payload).hexdigest() == part["sha256"]
        chunks.append(payload)
    normalized = b"".join(chunks)
    assert hashlib.sha256(normalized).hexdigest() == SNAPSHOT
    owner_records = json.loads(normalized)["records"]
    assert len(owner_records) == 1720
    owner_signatures = {row["signature"] for row in owner_records}
    overlap = [row for row in ata_rows if row["signature"] in owner_signatures]
    missing = [row for row in ata_rows if row["signature"] not in owner_signatures]
    assert len(overlap) == 4
    assert len(missing) == 66

    index_start = int(datetime(2026, 10, 2, 22, 54, 44,
                               tzinfo=timezone.utc).timestamp())
    preindex = [row for row in missing if row["block_time_unix"] < index_start]
    inwindow = [row for row in missing if row["block_time_unix"] >= index_start]
    assert len(preindex) == 63
    assert len(inwindow) == 3
    assert sum(row["err"] is not None for row in inwindow) == 1
    assert sum(row["err"] is None for row in inwindow) == 2
    assert {row["signature"] for row in inwindow if row["err"] is None} == {
        "4Gxq6UnNbqYvBYeGbN94Qa6Qyh8qLombBirUHsvszT4UXqDxQPhsQb5YBuQa2zsHHW9WWwm4DwY7M6Hbv8ios7ac",
        "3knjrZuSocitUtSunifVFy1V1mYyAzz7NLJUf96Kqg77T85x4wU8wkoHSWBxPKh22xhBAGpCewARmHksQJABGXVU",
    }
    assert not source["transaction_balance_deltas_verified"]
    assert not source["owner_signed_trades_verified"]
    assert source["profit_usd"] is None
