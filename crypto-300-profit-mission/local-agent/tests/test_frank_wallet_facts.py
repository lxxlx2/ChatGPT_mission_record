"""Offline transaction fact projection tests with synthetic source evidence."""

import json

import pytest

from mission_agent.frank.parser import WSOL
from mission_agent.hashing import digest
from mission_agent.mission_control.ata_backfill import b58encode
from mission_agent.mission_control.wallet_facts import build_fact
from mission_agent.signals.policy import USDC


WALLET, MINT, ACCOUNT, COUNTERPARTY = (b58encode(bytes([n]) * 32) for n in range(1, 5))
SIGNATURE = "2" * 88
RAW_HASH = "a" * 64


def activity_row(classification="ACTIVE_TRADE", version="frank-v8"):
    return {"wallet": WALLET, "sig": SIGNATURE, "slot": 42, "class": classification,
            "raw_sha256": RAW_HASH, "parser_version": version}


def seal_evidence(row=None, **fields):
    row = row or activity_row()
    body = {"wallet": row["wallet"], "signature": row["sig"], "slot": row["slot"],
            "parser_version": row["parser_version"], "raw_transaction_sha256": row["raw_sha256"],
            "pre_SOL_lamports": "9007199254750999", "post_SOL_lamports": "9007199254745999",
            "SOL_delta_lamports": "-5000", "fee": 5000, "wallet_is_signer": True,
            "wallet_is_fee_payer": True, "mechanical_classification": "ACTIVE_SWAP_LIKE", "tx_err": None,
            **fields}
    return {**body, "evidence_sha256": digest(body)}


def balance(mint, account_index, pre, post, decimals):
    return {"wallet_owned": True, "owner": WALLET, "mint": mint, "account_index": account_index,
            "pre_amount": str(pre), "post_amount": str(post), "delta": str(post - pre), "decimals": decimals}


def transfer(mint, index, amount, decimals, direction="IN"):
    source, destination = (COUNTERPARTY, ACCOUNT) if direction == "IN" else (ACCOUNT, COUNTERPARTY)
    return {"scope": "inner", "instruction": f"3:{index}", "outer_index": 3, "inner_index": index,
            "mint": mint, "source": source, "destination": destination, "raw_amount": str(amount),
            "decimals": decimals, "direction": direction}


def trade(mint, rowid=1, **fields):
    body = {"mint": mint, "side": "BUY", "direction": "BUY", "token_amount_raw": "5",
            "token_decimals": 6, "quote_asset": "SOL", "quote_amount_raw": "1000000001",
            "quote_decimals": 9, **fields}
    return {"wallet": WALLET, "signature": SIGNATURE, "mint": mint, "side": "BUY",
            "source_trade_rowid": rowid, "body": json.dumps(body)}


def test_projects_exact_native_units_gross_instructions_and_duplicate_trade_rows():
    evidence = seal_evidence(
        token_balance_deltas=[balance(MINT, 5, 0, 5, 6), balance(USDC, 6, 90, 70, 6),
                              balance(WSOL, 7, 2**64 - 1, 2**64 - 2, 9)],
        wallet_token_transfer_flows=[transfer(MINT, 1, 10, 6), transfer(USDC, 2, 20, 6, "OUT"),
                                     transfer(WSOL, 3, 1, 9, "OUT"), transfer(MINT, 4, 5, 6, "OUT")],
        native_incoming_transfer_evidence=[{"scope": "outer", "instruction": "2", "source": COUNTERPARTY,
                                            "lamports": "23"}],
        created_token_accounts=[{"scope": "outer", "instruction": "1", "account": ACCOUNT,
                                 "mint": MINT, "owner": WALLET}],
        closed_token_accounts=[{"scope": "outer", "instruction": "4", "account": ACCOUNT,
                                "destination": WALLET, "owner": WALLET}],
    )
    quote_legs = [{"asset": "SOL", "raw_delta": "-1000000001", "decimals": 9},
                  {"asset": USDC, "raw_delta": "-20", "decimals": 6}]
    source_legs = [trade(MINT, 11, quote_legs=quote_legs), trade(MINT, 12, quote_legs=quote_legs),
                   trade(USDC, 13, quote_asset=WSOL)]
    fact = build_fact(activity_row(), evidence, source_legs)
    assert fact["coverage"]["normalized_evidence"] == "BOUND"
    assert fact["classification"]["indexed_class"] == "ACTIVE_TRADE"
    assert fact["execution_status"] == "SUCCEEDED"
    assert fact["native_balance"] == {"denomination": "SOL", "decimals": 9, "pre_raw": "9007199254750999",
                                      "post_raw": "9007199254745999", "delta_raw": "-5000"}
    assert fact["fee"]["transaction_fee_raw"] == fact["fee"]["wallet_fee_raw"] == "5000"
    assert fact["fee"]["payer_account"] == WALLET
    assert fact["rent"]["wallet_paid_lamports"] is fact["rent"]["wallet_refunded_lamports"] is None
    assert [x["raw_amount"] for x in fact["token_transfers"]] == ["10", "20", "1", "5"]
    assert [x["denomination"] for x in fact["token_transfers"]] == ["SPL_TOKEN", "USDC", "WSOL", "SPL_TOKEN"]
    assert fact["token_account_balances"][2]["pre_raw"] == str(2**64 - 1)
    assert fact["token_account_balances"][2]["delta_raw"] == "-1"
    assert fact["native_transfers"][0]["destination_account"] == WALLET
    assert fact["account_creations"][0]["instruction_ref"] == [1, -1]
    assert fact["account_closures"][0]["operation"] == "CLOSE"
    assert len({x["leg_id"] for x in fact["trade_legs"]}) == 3
    assert [x["mint"] for x in fact["trade_legs"]] == [MINT, MINT, USDC]
    assert fact["trade_legs"][0]["recorded_primary_quote"]["mint"] == WSOL
    assert [x["denomination"] for x in fact["trade_legs"][0]["recorded_quote_legs"]] == ["WSOL", "USDC"]
    assert fact["coverage"]["route_cost_allocation"] == "UNRESOLVED"
    assert build_fact(activity_row(), evidence, source_legs) == fact


@pytest.mark.parametrize("indexed_class", ["FAILED_TX", "PASSIVE_TRANSFER", "ATA_CREATE", "UNKNOWN_NEEDS_REVIEW"])
def test_original_categories_and_transaction_status_are_preserved(indexed_class):
    row = activity_row(indexed_class, "frank-v7")
    failed = indexed_class == "FAILED_TX"
    evidence = seal_evidence(
        row, mechanical_classification="FAILED" if failed else "UNKNOWN",
        wallet_is_signer=failed, wallet_is_fee_payer=failed,
        tx_err={"InstructionError": [2, "Custom"]} if failed else None,
        native_incoming_transfer_evidence=[{"scope": "outer", "instruction": "2", "source": COUNTERPARTY,
                                            "lamports": "17"}],
        decoded_transient_token_flows=[{
            "account": ACCOUNT, "owner": WALLET, "mint": WSOL, "decimals": 9, "net_transfer_raw": "-6",
            "transfer_refs": [{"scope": "inner", "instruction": "0:1", "delta": "2"},
                              {"scope": "inner", "instruction": "0:2", "delta": "-8"}],
        }],
    )
    fact = build_fact(row, evidence, [])
    assert fact["classification"]["indexed_class"] == indexed_class
    assert fact["execution_status"] == ("FAILED" if failed else "SUCCEEDED")
    assert fact["native_transfers"][0]["instruction_effect"] == ("ATTEMPT_ONLY" if failed else "EXECUTED")
    assert fact["fee"]["wallet_fee_raw"] == ("5000" if failed else "0")
    assert fact["fee"]["payer_account"] == (WALLET if failed else None)
    assert fact["token_transfers"] is None
    assert fact["coverage"]["components"]["token_transfers"] == "NOT_RECORDED"
    assert fact["transient_token_flows"][0]["net_transfer_raw"] == "-6"


def test_rejects_invalid_seal_and_binding_while_retaining_the_matching_trade_row():
    row = activity_row()
    good = seal_evidence()
    tampered = {**good, "fee": 9000}
    unrelated = seal_evidence(wallet=COUNTERPARTY)
    trade_rows = [trade(MINT), {**trade(MINT, 2), "wallet": COUNTERPARTY}]
    for evidence, reason in [(None, "MISSING"), (tampered, "INVALID"), (unrelated, "BINDING_MISMATCH")]:
        fact = build_fact(row, evidence, trade_rows)
        assert fact["coverage"]["normalized_evidence"] == reason
        assert fact["fee"]["wallet_fee_raw"] is None
        assert fact["source_ref"]["normalized_evidence_sha256"] is None
        assert fact["classification"]["indexed_class"] == "ACTIVE_TRADE"
        assert len(fact["trade_legs"]) == 1
        assert fact["coverage"]["components"]["trade_legs"] == "PARTIAL_INVALID_RECORDS"
        assert fact["trade_legs"][0]["recorded_primary_quote"]["denomination"] == "LEGACY_SOL_UNRESOLVED"


def test_malformed_fields_and_duplicate_conflicts_cannot_become_facts_or_leak():
    secret = "https://rpc.private.invalid/?key=secret"
    wrong = {**transfer(MINT, 1, 10, 6), "source": secret}
    duplicated = [transfer(MINT, 2, 10, 6), transfer(MINT, 2, 11, 6)]
    evidence = seal_evidence(
        source_rpc=secret, SOL_delta_lamports="0", fee=False,
        wallet_token_transfer_flows=[wrong, *duplicated, transfer(MINT, 3, 1, None)],
        token_balance_deltas=[{**balance(MINT, 3, 1, 2, 6), "wallet_owned": False},
                              {**balance(MINT, 4, 1, 2, 6), "delta": "5"}],
        classification_evidence={"wallet_authority": {"secret": secret}},
        program_ids=[secret, ACCOUNT],
    )
    normalized_quote = trade(MINT, 2, quote_normalization="SYNTHETIC", quote_amount_raw="800",
                             original_quote={"source": secret})
    fact = build_fact(activity_row(), evidence, [trade(MINT, source_rpc=secret), normalized_quote])
    assert secret not in json.dumps(fact)
    assert fact["coverage"]["normalized_evidence"] == "BOUND"
    assert fact["native_balance"]["delta_raw"] is None
    assert fact["fee"]["transaction_fee_raw"] is None
    assert fact["token_account_balances"] == []
    assert fact["coverage"]["components"]["token_account_balances"] == "PARTIAL_INVALID_RECORDS"
    assert fact["classification"]["normalized_flags"]["wallet_authority"] is None
    assert fact["classification"]["recorded_program_ids"] == [ACCOUNT]
    assert len(fact["token_transfers"]) == 1
    assert fact["token_transfers"][0]["decimals"] is None
    assert fact["coverage"]["components"]["token_transfers"] == "PARTIAL_INVALID_RECORDS"
    assert fact["trade_legs"][1]["recorded_primary_quote"] is None
