"""Economic evidence gates for one cached, read-only Frank Solana root window."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mission_agent.meme.fomo_crosschain import (
    DEPOSIT_DISCRIMINATOR, FOMO_COSIGNER, SOL_CASH_WALLET,
    SOL_RELAY_DEPOSIT, SOL_ROUTERS, USDC,
)
from scripts import inspect_frank_solana_root_window as audit


MINT = "HfAFNsnjmbWMMRkwNeUUoHJ8V6UnUGFzkpu3Seajpump"
WALLET = SOL_CASH_WALLET


def balance(index: int, mint: str, owner: str, amount: int, decimals: int = 6):
    return {
        "accountIndex": index, "mint": mint, "owner": owner,
        "uiTokenAmount": {"amount": str(amount), "decimals": decimals},
    }


def transaction(*, signed=True, cosigned=True, target_before=0,
                target_after=1_500_000, quote_before=60_000_000,
                quote_after=40_000_000, other_owner=False,
                ix_program=None, payload=None):
    keys = [
        {"pubkey": FOMO_COSIGNER, "signer": cosigned},
        {"pubkey": WALLET, "signer": signed},
    ]
    pre = [
        balance(2, MINT, WALLET, target_before),
        balance(3, USDC, WALLET, quote_before),
    ]
    post = [
        balance(2, MINT, WALLET, target_after),
        balance(3, USDC, WALLET, quote_after),
    ]
    if other_owner:
        pre.append(balance(4, USDC, "counterparty", 0))
        post.append(balance(4, USDC, "counterparty", 123_000_000))
    instructions = [
        {"programId": ix_program or next(iter(sorted(SOL_ROUTERS))),
         "data": payload or ""}
    ]
    return {
        "slot": 123, "blockTime": 1791400000,
        "transaction": {"message": {"accountKeys": keys, "instructions": instructions}},
        "meta": {
            "err": None, "preTokenBalances": pre, "postTokenBalances": post,
            "innerInstructions": [],
        },
    }


def b58encode(raw: bytes) -> str:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = int.from_bytes(raw, "big")
    result = ""
    while num:
        num, remainder = divmod(num, 58)
        result = alphabet[remainder] + result
    return "1" * (len(raw) - len(raw.lstrip(b"\\x00"))) + result


def test_cosigned_actual_opposing_token_and_quote_is_candidate_with_amounts():
    row = audit.inspect_tx("sig", transaction(), WALLET)
    assert row["category"] == "SWAP_CANDIDATE"
    assert row["direction_candidate"] == "BUY"
    assert row["target"]["mint"] == MINT
    assert row["target"]["net_amount"] == "1.5"
    assert row["quote"]["net_amount"] == "20"
    assert row["wallet_signed"] and row["fomo_cosigned"]
    assert row["trade_confirmed"] is False


def test_fomo_cosigned_one_sided_receipt_is_not_buy():
    row = audit.inspect_tx("sig", transaction(quote_before=60_000_000,
                                               quote_after=60_000_000), WALLET)
    assert row["category"] == "TOKEN_MOVEMENT"
    assert row["direction_candidate"] is None


def test_relay_pay_with_real_usdc_debit_is_not_sol_meme_buy():
    deposit = (DEPOSIT_DISCRIMINATOR + (5_000_000).to_bytes(8, "little")
               + bytes.fromhex("11" * 32))
    tx = transaction(
        target_before=0, target_after=0,
        quote_before=6_000_000, quote_after=1_000_000,
        ix_program=SOL_RELAY_DEPOSIT, payload=b58encode(deposit),
    )
    row = audit.inspect_tx("relay", tx, WALLET)
    assert row["category"] == "RELAY_PAY"
    assert row["direction_candidate"] is None
    assert row["trade_confirmed"] is False


def test_only_wallet_owned_token_account_flows_can_set_quote_size():
    row = audit.inspect_tx(
        "sig", transaction(other_owner=True), WALLET
    )
    assert row["quote"]["net_amount"] == "20"
    assert row["category"] == "SWAP_CANDIDATE"


class FakeCache:
    def __init__(self, tx):
        self.tx = tx

    def load(self, wallet, signature, slot):
        return self.tx if signature == "A" * 88 else None


def test_partial_if_historical_cache_does_not_have_every_live_rpc_signature():
    rows = [
        {"signature": "A" * 88, "slot": 123, "blockTime": 1791400000},
        {"signature": "B" * 88, "slot": 124, "blockTime": 1791400001},
    ]
    result = audit.audit(WALLET, rows, 2, FakeCache(transaction()),
                         1791386454, 1791472854)
    assert result["status"] == "PARTIAL"
    assert result["missing_cached_transactions"] == 1
    assert result["cache_decoded_count"] == 1
    assert result["candidate_trades"][0]["trade_confirmed"] is False


def test_source_report_requires_matching_window_and_complete_root(tmp_path):
    path = tmp_path / "source.json"
    path.write_text(json.dumps({
        "cutoff_epoch": 1791386454, "audited_at_epoch": 1791472854,
        "chains": [{"chain": "SOL", "wallet": WALLET,
                    "status": "INCOMPLETE", "signatures_scanned": 173}],
    }))
    path.chmod(0o600)
    with pytest.raises(audit.EvidenceError, match="SOURCE_ROOT_COVERAGE_UNVERIFIED"):
        audit.read_report(path, WALLET, 1791386454, 1791472854)
    with pytest.raises(audit.EvidenceError, match="SOURCE_REPORT_WRONG_WINDOW"):
        audit.read_report(path, WALLET, 1791386454, 1791472855)
