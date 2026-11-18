"""Archived transaction identity, instruction provenance, and manifest compatibility."""
import gzip
import hashlib
import json
import sqlite3

import pytest

from mission_agent.mission_control.archived_wallet_facts import read_archived_fact
from mission_agent.mission_control.ata_backfill import ASSOCIATED, TOKEN, TOKEN_2022, b58encode, derive_ata
from mission_agent.mission_control.evidence_manifests import EvidenceManifests
from test_frank_activity_paging import NOW, make_db

SYSTEM = "1" * 32
SIGNATURE = "1" * 64
WALLET, OTHER, MINT = (b58encode(bytes([n]) * 32) for n in (1, 2, 3))


def ix(program, kind, stack_height=1, **info):
    return {"programId": program, "stackHeight": stack_height, "parsed": {"type": kind, "info": info}}


@pytest.fixture
def sample(tmp_path):
    archive = tmp_path / "raw"
    archive.mkdir()
    account = derive_ata(WALLET, MINT, TOKEN_2022)[0]
    ata = ix(ASSOCIATED, "createIdempotent", source=OTHER, wallet=WALLET, mint=MINT,
             account=account, tokenProgram=TOKEN_2022, systemProgram=SYSTEM)
    funding = ix(SYSTEM, "createAccount", 2, source=OTHER, newAccount=account,
                 owner=TOKEN_2022, lamports=2039280, space=165)
    native = ix(SYSTEM, "transferWithSeed", source=WALLET, destination=OTHER, lamports=42)
    token = ix(TOKEN_2022, "transferChecked", source=OTHER, destination=account, mint=MINT,
               tokenAmount={"amount": "505", "decimals": 2})
    tx = {"slot": 42, "blockTime": NOW-10, "meta": {
        "err": None, "fee": 5000, "preBalances": [3000000, 10000, 0],
        "postBalances": [955762, 9958, 2039280], "preTokenBalances": [], "postTokenBalances": [],
        "innerInstructions": [{"index": 0, "instructions": [funding]}], "logMessages": []},
        "transaction": {"signatures": [SIGNATURE], "message": {
            "accountKeys": [{"pubkey": OTHER, "signer": True}, {"pubkey": WALLET, "signer": True},
                            {"pubkey": account, "signer": False}],
            "instructions": [ata, native, token]}}}
    row = {"wallet": WALLET, "sig": SIGNATURE, "class": "ATA_CREATE", "slot": 42, "at": NOW-10}
    return archive, row, tx


def publish(archive, row, tx):
    payload = json.dumps(tx, sort_keys=True, separators=(",", ":")).encode()
    (archive / (SIGNATURE + ".json.gz")).write_bytes(gzip.compress(payload))
    row["raw_sha256"] = hashlib.sha256(payload).hexdigest()


def test_exact_transfers_and_third_party_funding(sample):
    archive, row, tx = sample
    publish(*sample)
    result = read_archived_fact(archive, row)
    assert result["status"] == "VERIFIED"
    assert result["indexed_class"] == "ATA_CREATE"
    fact = result["fact"]
    assert fact["fee"]["wallet_fee_raw"] == "0"
    assert [(x["direction"], x["raw_amount"], x["instruction_ref"]) for x in fact["native_transfers"]] == [
        ("OUT", "42", [1, -1])]
    assert [(x["direction"], x["raw_amount"], x["mint"]) for x in fact["token_transfers"]] == [
        ("IN", "505", MINT)]
    funding = fact["account_funding"]["items"][0]
    assert (funding["payer_role"], funding["owner_role"]) == ("OTHER", "WALLET")
    assert (funding["amount_raw"], funding["funding_instruction_ref"]) == ("2039280", [0, 0])
    assert fact["rent"]["wallet_paid_lamports"] is None
    assert fact["rent"]["wallet_refunded_lamports"] is None


@pytest.mark.parametrize(("change", "reason"), [
    ({"slot": 40}, "ARCHIVE_SLOT_MISMATCH"),
    ({"at": NOW-11}, "ARCHIVE_TIME_MISMATCH"),
    ({"wallet": MINT}, "ARCHIVE_WALLET_MISMATCH"),
    ({"raw_sha256": "b"*64}, "ARCHIVE_HASH_MISMATCH"),
    ({"sig": "../../secret"}, "INDEX_IDENTITY_INCOMPLETE"),
])
def test_identity_mismatch_has_no_fact(sample, change, reason):
    publish(*sample)
    archive, row, _ = sample
    result = read_archived_fact(archive, {**row, **change, "raw_reference": "/sensitive/secret"})
    assert result["reason"] == reason and result["fact"] is None
    assert "/sensitive/" not in json.dumps(result)


def test_neither_file_nor_directory_symlinks_are_read(sample, tmp_path):
    archive, row, _ = sample
    publish(*sample)
    original = archive / (SIGNATURE + ".json.gz")
    duplicate = tmp_path / "outside.gz"
    original.rename(duplicate)
    original.symlink_to(duplicate)
    assert read_archived_fact(archive, row)["reason"] == "ARCHIVE_FILE_UNAVAILABLE"
    mirror = tmp_path / "mirror"
    mirror.symlink_to(archive, target_is_directory=True)
    assert read_archived_fact(mirror, row)["reason"] == "ARCHIVE_FILE_UNAVAILABLE"
    original.unlink()
    assert read_archived_fact(archive, row)["reason"] == "ARCHIVE_NOT_FOUND"


def test_failed_transaction_counts_attempts_without_financial_effect(sample):
    archive, row, tx = sample
    tx["meta"]["err"] = {"InstructionError": [0, "Custom"]}
    publish(*sample)
    fact = read_archived_fact(archive, row)["fact"]
    assert fact["execution_status"] == "FAILED"
    assert all(leg["instruction_effect"] == "ATTEMPT_ONLY"
               for leg in fact["token_transfers"] + fact["native_transfers"])
    assert fact["account_funding"]["items"][0]["status"] == "ATTEMPT_ONLY"
    assert fact["account_funding"]["items"][0]["amount_raw"] is None


@pytest.mark.parametrize("case", ["duplicate", "not_child", "preexisting", "wrong_owner"])
def test_uncertain_funding_does_not_impute_payment(sample, case):
    archive, row, tx = sample
    group = tx["meta"]["innerInstructions"][0]
    if case == "duplicate":
        group["instructions"].append(group["instructions"][0].copy())
    elif case == "not_child":
        group["instructions"][0]["stackHeight"] = 3
    elif case == "preexisting":
        tx["meta"]["preBalances"][2] = 90000
    else:
        group["instructions"][0]["parsed"]["info"]["owner"] = TOKEN
    publish(*sample)
    item = read_archived_fact(archive, row)["fact"]["account_funding"]["items"][0]
    assert item["status"] == "UNRESOLVED"
    assert item["amount_raw"] is None


def test_unrelated_program_cannot_establish_account_ownership(sample):
    archive, row, tx = sample
    tx["transaction"]["message"]["instructions"][0]["programId"] = OTHER
    publish(*sample)
    result = read_archived_fact(archive, row)
    assert result["fact"] is None and result["status"] == "UNRESOLVED"


def test_legacy_archive_only_follows_explicit_root_when_current_is_missing(sample, tmp_path):
    archive, row, tx = sample
    publish(*sample)
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    original = archive / (SIGNATURE + ".json.gz")
    original.rename(legacy / original.name)
    result = read_archived_fact(archive, row, legacy_archive_root=legacy)
    assert result["status"] == "VERIFIED" and result["archive_tier"] == "LEGACY"
    assert str(legacy) not in json.dumps(result)
    assert read_archived_fact(archive, {**row, "raw_reference": str(legacy / original.name)})["fact"] is None
    altered = {**tx, "slot": 99}
    publish(archive, dict(row), altered)
    assert read_archived_fact(archive, row, legacy_archive_root=legacy)["reason"] == "ARCHIVE_HASH_MISMATCH"


def test_explicit_token2022_fee_and_net_keep_raw_amounts(sample):
    archive, row, tx = sample
    parsed = tx["transaction"]["message"]["instructions"][2]["parsed"]
    parsed["type"] = "transferCheckedWithFee"
    parsed["info"]["feeAmount"] = {"amount": "5", "decimals": 2}
    publish(*sample)
    transfers = read_archived_fact(archive, row)["fact"]["token_transfers"]
    assert len(transfers) == 1
    assert (transfers[0]["raw_amount"], transfers[0]["explicit_transfer_fee_raw"],
            transfers[0]["explicit_destination_amount_raw"]) == ("505", "5", "500")


@pytest.mark.parametrize("other_flow", [False, True])
def test_close_refund_requires_isolated_prebalance(sample, other_flow):
    archive, row, tx = sample
    account = tx["transaction"]["message"]["accountKeys"][2]["pubkey"]
    message = tx["transaction"]["message"]
    message["instructions"] = [ix(TOKEN_2022, "closeAccount", account=account,
                                  destination=WALLET, owner=WALLET)]
    if other_flow:
        message["instructions"].insert(0, ix(SYSTEM, "transfer", source=OTHER, destination=account,
                                             lamports=12))
    tx["meta"].update(preBalances=[90000, 15000, 2039280], postBalances=[85000, 2054280, 0],
                      innerInstructions=[])
    publish(*sample)
    result = read_archived_fact(archive, row)["fact"]
    refund = result["account_close_refunds"][0]
    assert refund["amount_raw"] == (None if other_flow else "2039280")
    assert result["rent"]["wallet_refunded_lamports"] is None


def test_enriched_facts_keep_the_v2_envelope_and_frozen_read(sample, tmp_path):
    archive, row, _ = sample
    publish(*sample)
    source = tmp_path / "source.sqlite"
    make_db(source, 0)
    with sqlite3.connect(source) as db:
        db.execute("INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?)",
                   (WALLET, SIGNATURE, "frank", row["slot"], row["at"], None, row["raw_sha256"],
                    json.dumps({"classification": row["class"]})))
    old = EvidenceManifests(tmp_path / "private", source, clock=lambda: NOW)
    v2 = old.create("facts", "old")
    latest = EvidenceManifests(old.root, source, clock=lambda: NOW, archive_root=archive)
    richer = latest.create("facts", "new", v2["manifest_id"])
    assert v2["schema_version"] == richer["schema_version"] == 2 and set(v2) == set(richer)
    assert richer["fact_revision_counts"]["revised"] == 1
    assert richer["counts"]["archive_replay"]["verified"] == 1
    assert richer["counts"]["archive_replay"]["executed_native_transfers"] == 1
    repeat = latest.create("facts", "same", richer["manifest_id"])
    assert repeat["fact_revision_counts"]["unchanged"] == 1
    frozen = latest.activity(richer["manifest_id"])
    assert frozen["archive_replay_summary"] == richer["counts"]["archive_replay"]
    old_fact = latest.activity(v2["manifest_id"])["rows"][0]["transaction_fact"]
    assert frozen["rows"][0]["transaction_fact"]["supersedes_id"] == old_fact["fact_id"]
    (archive / (SIGNATURE + ".json.gz")).unlink()
    assert latest.activity(richer["manifest_id"]) == frozen
    newer = latest.create("facts", "missing", repeat["manifest_id"])
    assert newer["counts"]["archive_replay"]["missing"] == 1
    assert newer["fact_revision_counts"]["revised"] == 1
