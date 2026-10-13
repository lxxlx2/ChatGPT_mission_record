"""A04/A05 dual-token-program source, immutable sidecar and token-leg tests."""
import copy
import json

import pytest

from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM, ChainCaptureError, capture_owner,
    normalize_owner_program,
)
from mission_agent.mission_control.wallet_economic_ledger import (
    LedgerEvidenceError, dedupe_transactions, normalize_transaction,
)
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def pk(seed):
    num = int.from_bytes(bytes([seed]) * 32, "big")
    digits = ""
    while num:
        num, rem = divmod(num, 58)
        digits = ALPHABET[rem] + digits
    return digits


OWNER_A, OWNER_B, MINT, ATA_A, ATA_B = (pk(i) for i in range(2, 7))


def entry(owner, mint, account, program, amount="1000000", decimals=6):
    return {
        "pubkey": account,
        "account": {
            "owner": program,
            "data": {"parsed": {"type": "account", "info": {
                "owner": owner, "mint": mint, "state": "initialized",
                "tokenAmount": {"amount": amount, "decimals": decimals},
            }}},
        },
    }


def response(slot, values):
    return {"result": {"context": {"slot": slot}, "value": values}}


def request_factory(spl, newer, fail=None):
    calls = []
    def request(method, params):
        assert method == "getTokenAccountsByOwner"
        wallet, program, config = params
        calls.append((wallet, program["programId"], config))
        assert config["commitment"] == "finalized"
        assert config["encoding"] == "jsonParsed"
        if program["programId"] == fail:
            raise TimeoutError("provider timeout, no zero fallthrough")
        return spl if program["programId"] == SPL_TOKEN_PROGRAM else newer
    return request, calls


def test_correct_official_token2022_id_is_used_and_both_programs_queried():
    assert TOKEN_2022_PROGRAM == "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
    call, records = request_factory(
        response(450, [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)]),
        response(451, [entry(OWNER_A, MINT, ATA_B, TOKEN_2022_PROGRAM, "2000000")]),
    )
    result = capture_owner(OWNER_A, call)
    assert result["status"] == "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC"
    assert result["both_programs_observed"]
    assert result["account_count"] == 2
    assert result["mint_count_observed"] == 1
    assert result["mints"][0]["raw_amount_observed_sum"] == "3000000"
    assert result["mints"][0]["quantity_observed_sum"] == "3"
    assert result["mints"][0]["balance_single_atomic_slot_verified"] is False
    assert result["wallet_nav_usd"] is None
    assert [x[1] for x in records] == [SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM]
    assert records[1][2]["minContextSlot"] == 450
    assert (result["slot_min"], result["slot_max"]) == (450, 451)


def test_only_one_program_success_is_partial_even_with_zero_accounts():
    call, _ = request_factory(response(800, []), response(801, []),
                              fail=TOKEN_2022_PROGRAM)
    result = capture_owner(OWNER_A, call)
    assert result["status"] == "PARTIAL_SOURCE"
    assert not result["both_programs_observed"]
    assert result["account_count"] == 0
    assert result["mints"] == []
    assert result["wallet_total_balance_verified"] is False
    assert result["missing"][0]["program_id"] == TOKEN_2022_PROGRAM


def test_both_empty_programs_are_observed_but_not_full_chain_history():
    call, _ = request_factory(response(300, []), response(301, []))
    result = capture_owner(OWNER_A, call)
    assert result["both_programs_observed"]
    assert result["account_count"] == 0
    assert result["all_history_complete"] is False
    assert result["same_slot_atomic"] is False


@pytest.mark.parametrize(("mutate", "reason"), [
    (lambda x: x["result"]["value"][0]["account"].update(owner=TOKEN_2022_PROGRAM), "TOKEN_ACCOUNT_OWNER_MISMATCH"),
    (lambda x: x["result"]["value"][0]["account"]["data"]["parsed"]["info"].update(owner=OWNER_B), "TOKEN_ACCOUNT_OWNER_MISMATCH"),
    (lambda x: x["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"].update(amount="-1"), "INVALID_RAW_AMOUNT"),
    (lambda x: x["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"].update(decimals=True), "INVALID_TOKEN_DECIMALS"),
    (lambda x: x["result"]["value"].append(copy.deepcopy(x["result"]["value"][0])), "DUPLICATE_TOKEN_ACCOUNT"),
    (lambda x: x["result"].update(context={"slot": None}), "INVALID_CONTEXT_SLOT"),
])
def test_invalid_owner_account_or_source_never_enters_verified_snapshot(mutate, reason):
    raw = response(200, [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)])
    mutate(raw)
    with pytest.raises(ChainCaptureError, match=reason):
        normalize_owner_program(OWNER_A, SPL_TOKEN_PROGRAM, raw)


def test_cross_program_duplicate_token_account_rejected():
    call, _ = request_factory(
        response(200, [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)]),
        response(201, [entry(OWNER_A, MINT, ATA_A, TOKEN_2022_PROGRAM)]),
    )
    with pytest.raises(ChainCaptureError, match="CROSS_PROGRAM_DUPLICATE"):
        capture_owner(OWNER_A, call)


def balances(idx, owner, mint, raw, decimals=6):
    return {"accountIndex": idx, "owner": owner, "mint": mint,
            "uiTokenAmount": {"amount": raw, "decimals": decimals}}


def tx(pre, post, failed=False):
    return {
        "slot": 500,
        "transaction": {"signatures": ["test-tx-signature-100"],
                        "message": {"accountKeys": [
                            {"pubkey": ATA_A}, {"pubkey": ATA_B},
                        ]}},
        "meta": {"err": {"code": 1} if failed else None,
                 "fee": 5000, "preTokenBalances": pre, "postTokenBalances": post},
    }


def test_two_wallets_same_tx_counted_once_never_fake_market_buy_or_pnl():
    raw = tx([balances(0, OWNER_A, MINT, "100"), balances(1, OWNER_B, MINT, "0")],
             [balances(0, OWNER_A, MINT, "0"), balances(1, OWNER_B, MINT, "100")])
    row = normalize_transaction(raw, tracked_wallets={OWNER_A, OWNER_B})
    assert row["tracked_wallet_count"] == 2
    assert sorted(x["delta_raw"] for x in row["token_legs"]) == ["-100", "100"]
    assert row["possible_peer_flows"][0]["classification"] == "POSSIBLE_PEER_FLOW_NEEDS_INSTRUCTION_PROOF"
    assert row["active_market_buys_confirmed"] == 0
    assert row["person_pnl_usd"] is None
    assert len(dedupe_transactions([row, row])) == 1


def test_failure_receipt_with_nonzero_balance_delta_rejected():
    raw = tx([balances(0, OWNER_A, MINT, "100")],
             [balances(0, OWNER_A, MINT, "0")], failed=True)
    with pytest.raises(LedgerEvidenceError, match="FAILED_TRANSACTION_NONZERO"):
        normalize_transaction(raw, tracked_wallets={OWNER_A})


def test_passive_receipt_is_not_market_buy():
    result = normalize_transaction(tx([], [balances(1, OWNER_B, MINT, "123")]),
                                   tracked_wallets={OWNER_B})
    assert result["token_legs"][0]["direction"] == "IN"
    assert result["token_legs"][0]["economic_type"] == "UNKNOWN_TOKEN_DELTA_NOT_MARKET_TRADE"
    assert result["active_market_buys_confirmed"] == 0
    assert not result["possible_peer_flows"]


def test_transaction_replay_conflicts_fail_closed():
    row = normalize_transaction(tx([], [balances(1, OWNER_B, MINT, "1")]),
                                tracked_wallets={OWNER_B})
    bad = {**row, "canonical_event_sha256": "another-content-hash"}
    with pytest.raises(LedgerEvidenceError, match="CONFLICTING_TRANSACTION_EVIDENCE"):
        dedupe_transactions([row, bad])


def test_sidecar_immutable_import_and_readback(tmp_path):
    path = tmp_path / "safe" / "wallet-research-sidecar.sqlite"
    store = WalletEvidenceStore(path)
    try:
        call, _ = request_factory(response(600, []), response(601, []))
        snapshot = capture_owner(OWNER_A, call)
        assert store.capture_wallet(snapshot)
        assert store.capture_wallet(snapshot) is False
        assert store.count("ACCOUNT_CAPTURE") == 1
        assert store.read_wallet_captures(OWNER_A)[0] == snapshot
        normalized = normalize_transaction(tx([], [balances(0, OWNER_A, MINT, "2")]),
                                            tracked_wallets={OWNER_A})
        assert store.record_transaction(normalized)
        assert store.record_transaction(normalized) is False
        assert store.count("TX") == 1
        conflict = {**normalized, "fees_lamports": 7000}
        with pytest.raises(ValueError, match="IMMUTABLE_EVIDENCE_CONFLICT"):
            store.record_transaction(conflict)
    finally:
        store.close()


@pytest.mark.parametrize("name", ["forward.sqlite", "mission-control.sqlite",
                                   "sol-normalized-v1.sqlite"])
def test_production_sqlite_names_never_used_as_research_sidecar(tmp_path, name):
    with pytest.raises(ValueError, match="SIDE_CAR_PATH_NOT_ALLOWED"):
        WalletEvidenceStore(tmp_path / name)
