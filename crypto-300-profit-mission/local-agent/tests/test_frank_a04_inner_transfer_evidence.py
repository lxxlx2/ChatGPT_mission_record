"""A04 parsed SPL/Token-2022 transfer evidence versus market ambiguity."""
import pytest

from mission_agent.mission_control.wallet_chain_capture import SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM
from mission_agent.mission_control.wallet_economic_ledger import (
    LedgerEvidenceError, normalize_transaction,
)
from mission_agent.mission_control.wallet_instruction_evidence import transfer_instructions

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def pk(n):
    num = int.from_bytes(bytes([n]) * 32, "big")
    result = ""
    while num:
        num, v = divmod(num, 58)
        result = ALPHABET[v] + result
    return result


A, B, TA, TB, MINT = [pk(i) for i in range(20, 25)]


def record(account_index, owner, amount):
    return {"accountIndex": account_index, "owner": owner, "mint": MINT,
            "uiTokenAmount": {"amount": str(amount), "decimals": 6}}


def tx(program=SPL_TOKEN_PROGRAM, *, inner=False, include=False):
    body = {
        "programId": program,
        "parsed": {"type": "transferChecked", "info": {
            "source": TA, "destination": TB, "mint": MINT,
            "tokenAmount": {"amount": "77", "decimals": 6},
        }},
    }
    message_instructions = [{"programId": pk(30), "parsed": {"type": "noop"}}]
    if not inner:
        message_instructions.append(body)
    return {
        "slot": 555,
        "transaction": {
            "signatures": ["synthetic-transfer-sig"],
            "message": {"accountKeys": [{"pubkey": TA}, {"pubkey": TB}],
                        "instructions": message_instructions},
        },
        "meta": {
            "err": None, "fee": 5000,
            "preTokenBalances": [record(0, A, 77), record(1, B, 0)],
            "postTokenBalances": [record(0, A, 0), record(1, B, 77)],
            "innerInstructions": [{"index": 0, "instructions": [body]}] if inner else [],
        },
    }


@pytest.mark.parametrize("program", [SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM])
@pytest.mark.parametrize("inner", [True, False])
def test_parsed_transfer_between_two_tracked_wallets_never_market_buy(program, inner):
    raw = tx(program, inner=inner)
    normalized = normalize_transaction(raw, tracked_wallets={A, B})
    identified = transfer_instructions(raw, normalized)
    assert identified["transfer_count"] == 1
    event = identified["transfers"][0]
    assert event["classification"] == "TRACKED_TO_TRACKED_TOKEN_TRANSFER"
    assert event["program_id"] == program
    assert event["inner_index"] == (0 if inner else None)
    assert event["raw_amount"] == "77"
    assert event["source_wallet_owner"] == A
    assert event["destination_wallet_owner"] == B
    assert event["source_status"] == "PARSED_TOKEN_INSTRUCTION_CONFIRMED"
    assert not identified["active_market_trades_verified"]
    assert identified["person_pnl_usd"] is None


def test_inbound_transfer_to_tracked_wallet_not_promoted_to_buy():
    raw = tx()
    normalized = normalize_transaction(raw, tracked_wallets={B})
    result = transfer_instructions(raw, normalized)
    assert result["transfers"][0]["classification"] == "ONE_TRACKED_ENDPOINT_TRANSFER"
    assert result["transfers"][0]["source_wallet_owner"] is None
    assert result["transfers"][0]["destination_wallet_owner"] == B
    assert not result["transfers"][0]["market_buy_confirmed"]


def test_token_instruction_unparsed_is_coverage_gap_not_zero():
    raw = tx()
    raw["transaction"]["message"]["instructions"][1] = {
        "programId": SPL_TOKEN_PROGRAM, "data": "opaque",
    }
    normal = normalize_transaction(raw, tracked_wallets={A, B})
    data = transfer_instructions(raw, normal)
    assert data["transfer_count"] == 0
    assert data["unparsed_token_instruction_count"] == 1
    assert data["evidence_gaps"][0]["reason"] == "TOKEN_INSTRUCTION_UNPARSED"


def test_transfer_source_transaction_mismatch_rejected():
    raw = tx()
    normal = normalize_transaction(raw, tracked_wallets={A, B})
    raw["slot"] += 1
    with pytest.raises(LedgerEvidenceError, match="TRANSFER_TRANSACTION_ID_MISMATCH"):
        transfer_instructions(raw, normal)


def test_transfer_checked_missing_amount_kept_as_gap():
    raw = tx()
    del raw["transaction"]["message"]["instructions"][1]["parsed"]["info"]["tokenAmount"]
    normal = normalize_transaction(raw, tracked_wallets={A, B})
    data = transfer_instructions(raw, normal)
    assert data["transfer_count"] == 0
    assert data["evidence_gaps"][0]["reason"] == "TOKEN_TRANSFER_FIELDS_INCOMPLETE"
