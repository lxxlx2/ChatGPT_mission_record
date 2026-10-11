"""Research-only ATA backfill safety, J7 Token-2022 derivation and replay."""
from __future__ import annotations
from collections import Counter
import pytest

from mission_agent.mission_control.ata_backfill import (
    WALLET, TOKEN, TOKEN_2022, SCOPE, derive_ata, scan_ata_mints,
    validate_transaction, b58decode, b58encode,
)

J7 = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"
J7_ATA = "FjESMbdMaDapesMo889siXL1oQmgvQz8wsLTnHKeTNem"
J7_TRADITIONAL_ATA = "DbEAuRyJKJYcs6DS1TeLNph7snPDcXqwTqXVrmNyNhLe"
SIGNATURES = [
    "3opgLQn1cfQPPoKHNnU986rA9QyAzdmSoLPAXFwxA1tP7Vbx7J3MEHSoAczvcmHPpH7X1pxV3kmE4cGewJnxyR5n",
    "dveTCqqEWwbH2Xg6cXvgnvZ5C8qjtYQZoGfYToyD1N6yFGYxkwiQ2CfgQ3mGnXc1Ehq4Y4AtWjjpUnoQsWzkkej",
    "4JMFca46bpxkkVfykETjzwytqP9cNPtYFc9yKJD9cUnz1pKDf2MiHVgugTPxQp6HqVFpVCjpKXsYd243DCQi4LUU",
]
TX_RAW = [
    ("0", "2846838050235", 454705300),
    ("2846838050235", "7846838050235", 454705824),
    ("7846838050235", "12508217470763", 454705939),
]


class FakeRPC:
    def __init__(self, results=None, txs=None):
        self.results = results or {}
        self.txs = txs or {}
        self.calls = []

    def call(self, method, args):
        self.calls.append((method, args))
        if method == "getSignaturesForAddress":
            assert args[1]["commitment"] == "finalized"
            assert 1 <= args[1]["limit"] <= 100
            return self.results.get(args[0], [])
        if method == "getTransaction":
            assert args[1]["encoding"] == "jsonParsed"
            assert args[1]["commitment"] == "finalized"
            return self.txs.get(args[0])
        raise AssertionError("Read-only allowlist")


def tx(pre, post, slot, *, signer="VP4B4yj63FNP4BZLZdBJYRsTi1LqUuUENY8wfAdtSn8",
       program=TOKEN_2022, ata=J7_ATA, include_post=True):
    base = {"accountIndex": 2, "mint": J7, "owner": WALLET, "programId": program,
            "uiTokenAmount": {"amount": pre, "decimals": 6}}
    after = {**base, "uiTokenAmount": {"amount": post, "decimals": 6}}
    return {"slot": slot, "blockTime": 1791505760,
            "transaction": {"message": {"accountKeys": [
                {"pubkey": signer, "signer": True},
                {"pubkey": "VP4B4yj63FNP4BZLZdBJYRsTi1LqUuUENY8wfAdtSn8", "signer": False},
                {"pubkey": ata, "signer": False},
            ]}},
            "meta": {"err": None, "preTokenBalances": [base],
                     "postTokenBalances": [after] if include_post else []}}


def test_j7_real_ata_derives_only_under_token2022():
    a, bump = derive_ata(WALLET, J7, TOKEN_2022)
    assert a == J7_ATA
    assert bump == 255
    b, traditional_bump = derive_ata(WALLET, J7, TOKEN)
    assert b == J7_TRADITIONAL_ATA
    assert traditional_bump == 253
    assert b58encode(b58decode(J7_ATA)) == J7_ATA
    assert b58encode(b58decode(WALLET)) == WALLET
    assert b != a


def test_j7_real_chain_triplet_signatures_recover_missing_two_without_false_buy():
    j7 = [
        {"signature": sig, "slot": raw[2], "blockTime": 1791505760 + i*90,
         "err": None}
        for i, (sig, raw) in enumerate(zip(SIGNATURES, TX_RAW))
    ]
    rpc = FakeRPC({J7_ATA: list(reversed(j7))}, {
        sig: tx(*raw) for sig, raw in zip(SIGNATURES, TX_RAW)
    })
    result = scan_ata_mints(rpc, [J7], known_signatures={SIGNATURES[0]},
                            since_time=1791490000)
    assert result["source_scope"] == SCOPE
    assert len(result["accounts"]) == 2
    assert {x["token_program"] for x in result["accounts"]} == {TOKEN, TOKEN_2022}
    assert result["verified_nonzero_signatures_absent_from_local_index"] == sorted(
        SIGNATURES[1:])
    assert result["statistics"]["VERIFIED_ATA_BALANCE_DELTA"] == 3
    verified = [x for x in result["observations"] if x.get("status") == "VERIFIED_ATA_BALANCE_DELTA"]
    assert [int(x["raw_delta"]) for x in verified] == [4661379420528, 5000000000000, 2846838050235]
    assert all(x["wallet_signed"] is False for x in verified)
    assert all(x["acquisition_cost_usd"] is None and x["realized_pnl_usd"] is None for x in verified)
    assert not any(x[0] not in ("getTransaction", "getSignaturesForAddress") for x in rpc.calls)
    assert result["complete_wallet_history"] is False


def test_owner_program_mismatch_does_not_promote_balance_evidence():
    j7 = tx("0", "5000000", 454705824, program=TOKEN)
    result = validate_transaction(j7, SIGNATURES[1], J7_ATA, J7, TOKEN_2022)
    assert result["status"] == "OWNER_OR_BALANCE_UNVERIFIED"
    assert "raw_delta" not in result


def test_missing_post_balance_not_assumed_zero():
    j7 = tx("0", "5000000", 454705824, include_post=False)
    result = validate_transaction(j7, SIGNATURES[1], J7_ATA, J7, TOKEN_2022)
    assert result["status"] == "PARTIAL_PRE_POST_BALANCE_UNVERIFIED"
    assert "raw_delta" not in result


def test_failed_transaction_is_never_a_transfer():
    data = tx("10000", "0", 454705824)
    data["meta"]["err"] = {"InstructionError": [0, "Custom"]}
    result = validate_transaction(data, SIGNATURES[0], J7_ATA, J7, TOKEN_2022)
    assert result["status"] == "FAILED_TX_NO_BALANCE_PROOF"
    assert "raw_delta" not in result


def test_history_budget_cannot_be_interpreted_as_chain_complete():
    a, _ = derive_ata(WALLET, J7, TOKEN_2022)
    records = [{"signature": SIGNATURES[i % 3], "slot": 454705824 - i,
                "blockTime": 1791505760, "err": None}
               for i in range(4)]
    rpc = FakeRPC({a: records}, {
        sig: tx(*TX_RAW[i]) for i, sig in enumerate(SIGNATURES)
    })
    result = scan_ata_mints(rpc, [J7], known_signatures=set(),
                            page_size=4, max_pages_per_ata=1)
    assert result["complete_wallet_history"] is False
    assert result["accounts"][1]["status"] == "BOUNDED"


def test_no_implicit_wallet_history_or_signal_when_no_local_index():
    result = scan_ata_mints(FakeRPC(), [J7])
    assert result["verified_nonzero_signatures_absent_from_local_index"] is None
    assert result["known_main_wallet_signatures_supplied"] is False
    assert result["trading_signal_emitted"] is False


@pytest.mark.parametrize("inputs", [
    {"mints": []}, {"mints": [J7] * 13},
    {"mints": [J7], "page_size": 1000},
    {"mints": [J7], "max_tx_fetches": 0},
    {"mints": [J7], "max_pages_per_ata": 20},
])
def test_fail_closed_on_invalid_scan_batch_or_budget(inputs):
    with pytest.raises(ValueError):
        scan_ata_mints(FakeRPC(), **inputs)


def test_canonical_ata_invalid_mint_or_wrong_program_rejected():
    with pytest.raises(ValueError):
        derive_ata(WALLET, "not-base58!", TOKEN)
    with pytest.raises(ValueError):
        derive_ata(WALLET, J7, "malicious-token-program")


def test_explicit_ata_cli_reads_existing_index_without_changes(tmp_path):
    import json
    import sqlite3
    from scripts.frank_ata_backfill import run
    db = tmp_path / "forward.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE signatures(person_id TEXT,signature TEXT)")
        conn.execute("INSERT INTO signatures VALUES (?,?)", ("frank", SIGNATURES[0]))
    rpc = FakeRPC({
        J7_ATA: [{"signature": SIGNATURES[0], "slot": 454705300,
                  "blockTime": 1791505760, "err": None}]
    }, {SIGNATURES[0]: tx(*TX_RAW[0])})
    output = tmp_path / "result.json"
    before = db.stat().st_mtime_ns
    report = run(["--database", str(db), "--mint", J7,
                  "--output", str(output), "--page-size", "5"], rpc=rpc)
    assert report["absent_verified_signatures"] == 0
    assert report["production_modified"] is False
    assert db.stat().st_mtime_ns == before
    assert output.exists()
    assert (output.stat().st_mode & 0o777) == 0o600
    packet = json.loads(output.read_text())
    assert packet["source_scope"] == SCOPE
    assert packet["observations"][0]["already_in_main_wallet_index"] is True
    with pytest.raises(FileExistsError):
        run(["--database", str(db), "--mint", J7,
             "--output", str(output)], rpc=rpc)


def test_explicit_git_sync_uses_only_dedicated_evidence_branch_and_retains_local_file(
        tmp_path, monkeypatch):
    import sqlite3
    from scripts.frank_ata_backfill import run
    from mission_agent.mission_control import evidence_sync
    p = tmp_path / "forward.sqlite"
    with sqlite3.connect(p) as db:
        db.execute("CREATE TABLE signatures(person_id TEXT,signature TEXT)")
        db.execute("INSERT INTO signatures VALUES (?,?)", ("frank", SIGNATURES[0]))
    captured = []
    def upload(self, path, data):
        captured.append((path, data))
    monkeypatch.setattr(evidence_sync.GitEvidencePublisher, "_upload", upload)
    out = tmp_path / "ata-proof.json"
    rpc = FakeRPC({
        J7_ATA: [{"signature": SIGNATURES[0], "slot": 454705300,
                  "blockTime": 1791505760, "err": None}]
    }, {SIGNATURES[0]: tx(*TX_RAW[0])})
    result = run(["--database", str(p), "--mint", J7,
                  "--output", str(out), "--sync-git"], rpc=rpc)
    assert result["git_sync"] == "SYNC_OK_READBACK_VERIFIED"
    assert len(captured) == 1
    path, content = captured[0]
    assert path.startswith("crypto-300-profit-mission/meme/local-evidence/frank-ata-backfill/")
    assert path.endswith(result["git_snapshot_id"] + ".json")
    assert b"COMPLETE_CHAIN" not in content
    assert out.exists()


def test_git_failure_preserves_ata_file_and_returns_non_success(tmp_path, monkeypatch):
    import sqlite3
    from scripts.frank_ata_backfill import run
    from mission_agent.mission_control import evidence_sync
    p = tmp_path / "forward.sqlite"
    with sqlite3.connect(p) as db:
        db.execute("CREATE TABLE signatures(person_id TEXT,signature TEXT)")
        db.execute("INSERT INTO signatures VALUES (?,?)", ("frank", SIGNATURES[0]))
    def blocked_upload(*args):
        raise RuntimeError("SIMULATED_GITHUB_FAILURE")
    monkeypatch.setattr(evidence_sync.GitEvidencePublisher, "_upload", blocked_upload)
    out = tmp_path / "saved.json"
    report = run(["--database", str(p), "--mint", J7, "--output", str(out),
                  "--sync-git"], rpc=FakeRPC())
    assert report["git_sync"] == "SYNC_FAILED_LOCAL_FILE_RETAINED"
    assert report["git_error_type"] == "RuntimeError"
    assert out.exists()
