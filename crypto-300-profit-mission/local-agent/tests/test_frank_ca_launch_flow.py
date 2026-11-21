from collections import OrderedDict
import hashlib

import pytest

from mission_agent.meme import launch_flow
from mission_agent.meme.cluster import RPCJobBudgetExceeded
from mission_agent.meme.launch_flow import collect_launch_flow
from mission_agent.meme.launch_identity import PUMP_PROGRAM


MINT = "fixture-mint"
CURVE = "fixture-bonding-curve"
DEV = "fixture-creator"
LAUNCH = {"pump": {"status": "VERIFIED_CHAIN_STATE", "bonding_curve": CURVE, "creator": DEV}}
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


def discriminator(name):
    payload = hashlib.sha256(f"global:{name}".encode()).digest()[:8] + bytes(range(7))
    number = int.from_bytes(payload, "big")
    result = []
    while number:
        number, digit = divmod(number, 58)
        result.append(launch_flow.BASE58[digit])
    return "".join(reversed(result))


def transaction(sig, slot, action=None, owner=DEV, amount=100, *, cpi=False, vendor="source"):
    names = [owner, CURVE, MINT, "ata-" + owner, "ata-curve", PUMP_PROGRAM]
    instructions, inner, balances = [], [], []
    if action is not None:
        instructions.append({"programId": PUMP_PROGRAM, "accounts": names[:-1], "data": discriminator(action)})
    else:
        instructions.append({"programId": "11111111111111111111111111111111"})
    if action not in {None, "create", "create_v2"}:
        source, destination = names[4], names[3]
        if action == "sell":
            source, destination = destination, source
        transfer = {"programId": TOKEN_PROGRAM, "parsed": {"type": "transferChecked", "info": {
            "source": source, "destination": destination, "mint": MINT, "tokenAmount": {"amount": str(amount)},
        }}}
        if cpi:
            instructions[0]["stackHeight"] = 2
            transfer["stackHeight"] = 3
            inner.append({"index": 0, "instructions": [instructions[0], transfer]})
            instructions = [{"programId": vendor}]
        else:
            inner.append({"index": 0, "instructions": [transfer]})
        balances = [{"accountIndex": 3, "mint": MINT, "owner": owner},
                    {"accountIndex": 4, "mint": MINT, "owner": CURVE}]
    meta = {"err": None, "innerInstructions": inner,
            "preTokenBalances": balances, "postTokenBalances": balances}
    return {"slot": slot, "transaction": {"signatures": [sig], "message": {
        "accountKeys": [{"pubkey": name, "signer": name == owner} for name in names],
        "instructions": instructions,
    }}, "meta": meta}


class Replay:
    def __init__(self, txs, pages=None):
        self.txs = txs
        self.pages = iter(pages) if pages is not None else None
        self.rows = [{"signature": sig, "slot": tx["slot"], "err": tx["meta"].get("err")}
                     for sig, tx in reversed(list(txs.items()))]
        self.pages_read = []
        self.tx_reads = []

    def call(self, method, params, ttl):
        if method == "getSignaturesForAddress":
            curve, options = params
            assert curve == CURVE and options["commitment"] == "finalized"
            after = options.get("before")
            self.pages_read.append(after)
            if self.pages is not None:
                return next(self.pages)
            start = next(i + 1 for i, row in enumerate(self.rows) if row["signature"] == after) if after else 0
            return self.rows[start:start + options["limit"]]
        assert method == "getTransaction"
        self.tx_reads.append(params[0])
        return self.txs[params[0]]


def fixture(rows):
    return OrderedDict((sig, transaction(sig, slot, action, owner, amount))
                       for sig, slot, action, owner, amount in rows)


def test_dev_identity_and_verified_sell_are_independent_from_balance_changes():
    txs = fixture([("create", 100, "create", DEV, 0),
                   ("buy1", 101, "buy", "one", 100),
                   ("buy2", 102, "buy", DEV, 20),
                   ("sell", 103, "sell", DEV, 9),
                   ("buy3", 104, "buy", "two", 100)])
    txs["buy3"] = transaction("buy3", 104, "buy_exact_sol_in", "two", cpi=True)
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH, supply_raw=1000,
                                 current_balances={DEV: 11, "one": 40, "two": 100})
    assert result["status"] == "OK"
    assert result["oldest_reach"] == "PROVIDER_EMPTY_PAGE"
    assert result["summary"]["first_buyers"]["count"] == 3
    assert result["summary"]["snipers"]["count"] == 1
    assert result["summary"]["first_buyers"]["current_pct"] == "15.1000"
    assert result["dev"]["current_raw"] == "11"
    assert result["dev"]["verified_sell"] == {"signature": "sell", "slot": 103, "token_raw": "9"}
    assert result["buyers"][0]["status"] == "PARTIAL_REDUCED"
    assert result["buyers"][0]["sol_outflow_lamports"] is None


def test_raw_malformed_full_page_cannot_be_an_oldest_page():
    page = [{"signature": f"sig-{i}", "slot": 2000 - i, "err": None} for i in range(1000)]
    page[10].pop("signature")
    rpc = Replay({}, pages=[page])
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH, supply_raw=100, current_balances={DEV: 40})
    assert result["status"] == "PARTIAL"
    assert result["reason"] == "MALFORMED_SIGNATURE_PAGE"
    assert "oldest_reach" not in result and "summary" not in result
    assert result["dev"]["current_pct"] == "40.0000"
    assert result["dev"]["verified_sell"] is None
    assert rpc.tx_reads == []


@pytest.mark.parametrize(("pages", "reason"), [
    ([[{"signature": "a", "slot": 6, "err": None}],
      [{"signature": "a", "slot": 6, "err": None}]], "CURSOR_STALLED"),
    ([[{"signature": "a", "slot": 6, "err": None}],
      [{"signature": "b", "slot": 7, "err": None}]], "SOURCE_PAGE_CONFLICT"),
    ([[{"signature": "a", "slot": 6, "err": None}, {"signature": "a", "slot": 6, "err": None}]],
     "SOURCE_PAGE_CONFLICT"),
])
def test_invalid_cursor_or_order_remains_partial(pages, reason):
    result = collect_launch_flow(MINT, Replay({}, pages=pages), launch=LAUNCH)
    assert result["status"] == "PARTIAL" and result["reason"] == reason
    assert "oldest_reach" not in result


def test_no_300_transaction_cutoff_and_declared_cutoff_slot_is_complete(monkeypatch):
    monkeypatch.setattr(launch_flow, "SIGNATURE_PAGE", 37)
    txs = fixture([("create", 100, "create", DEV, 0)]
                  + [(f"other-{i}", 101 + i, None, DEV, 0) for i in range(500)]
                  + [(f"buyer-{i}", 602 + i, "buy", f"user-{i}", 1) for i in range(72)])
    rpc = Replay(txs)
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH, current_balances=None)
    assert result["status"] == "OK" and result["summary"]["first_buyers"]["count"] == 70
    assert result["summary"]["first_buyers"]["current_raw"] is None
    assert len(rpc.pages_read) > 16
    assert len(rpc.tx_reads) == 571 and rpc.tx_reads[-1] == "buyer-69"
    assert result["buyers"][-1]["owner"] == "user-69"


def test_same_slot_crossing_cutoff_never_selects_by_rpc_order():
    txs = fixture([("create", 10, "create", DEV, 0)]
                  + [(f"buyer-{i}", 11 + i, "buy", f"user-{i}", 1) for i in range(69)]
                  + [("either-a", 90, "buy", "candidate-a", 1), ("either-b", 90, "buy", "candidate-b", 1)])
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH)
    assert result["status"] == "PARTIAL" and result["reason"] == "BUYER_ORDER_AT_CUTOFF_UNRESOLVED"
    assert len(result["buyers"]) == 69 and "summary" not in result
    assert result["cutoff_slot"] == 90
    assert {row["owner"] for row in result["unranked_cutoff_buyers"]} == {"candidate-a", "candidate-b"}


def test_unbound_transfer_and_failed_rpc_record_never_become_buyers():
    txs = fixture([("create", 10, "create", DEV, 0),
                   ("airdrop", 11, "buy", "A", 100),
                   ("failed", 12, "buy", "failed", 200),
                   ("valid", 13, "buy", "V", 300)])
    txs["airdrop"]["transaction"]["message"]["instructions"][0]["programId"] = "unknown-program"
    txs["failed"]["meta"]["err"] = {"InstructionError": [0, "Custom"]}
    rpc = Replay(txs)
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH)
    assert [row["owner"] for row in result["buyers"]] == ["V"]
    assert "failed" not in rpc.tx_reads


def test_missing_valid_transaction_never_certifies_exact_early_buyer_result():
    txs = fixture([("create", 10, "create", DEV, 0), ("invalid", 12, "buy", "I", 200),
                   ("valid", 13, "buy", "V", 300)])
    txs["invalid"]["meta"].pop("err")
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH)
    assert result["reason"] == "TRANSACTION_EVIDENCE_INCOMPLETE"
    assert result["status"] == "PARTIAL" and "summary" not in result
    assert [r["rank"] for r in result["buyers"]] == [None]


def test_no_proved_market_does_not_scan_mint_as_if_it_were_launch_market():
    rpc = Replay({})
    result = collect_launch_flow(MINT, rpc, launch={"pump": {"status": "UNAVAILABLE"}})
    assert result["status"] == "UNAVAILABLE" and result["reason"] == "MARKET_LAUNCH_ADDRESS_NOT_VERIFIED"
    assert rpc.pages_read == []


def test_existing_budget_exception_reaches_checkpoint():
    class Budget:
        def call(self, method, params, ttl):
            raise RPCJobBudgetExceeded("RPC_JOB_TIME_BUDGET_EXHAUSTED")

    with pytest.raises(RPCJobBudgetExceeded):
        collect_launch_flow(MINT, Budget(), launch=LAUNCH)


def test_unknown_pump_action_is_classification_gap():
    txs = fixture([("create", 10, "create", DEV, 0), ("unknown", 11, "future_buy", "A", 12)])
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH)
    assert result["status"] == "PARTIAL"
    assert result["reason"] == "TRANSACTION_EVIDENCE_INCOMPLETE"
    assert result["transaction_errors"] == 1
    assert "summary" not in result


def test_many_pages_without_a_sixty_page_limit(monkeypatch):
    monkeypatch.setattr(launch_flow, "SIGNATURE_PAGE", 4)
    txs = fixture([("create", 50, "create", DEV, 0), ("buy", 51, "buy", "A", 1)]
                  + [(f"x-{i}", 52 + i, None, DEV, 0) for i in range(260)])
    rpc = Replay(txs)
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH)
    assert result["status"] == "OK"
    assert result["signature_requests"] == 67
    assert result["signature_count"] == 262
    assert result["summary"]["first_buyers"]["count"] == 1


def test_first_bought_amount_remains_unknown_for_same_slot_ties():
    txs = fixture([("create", 50, "create", DEV, 0), ("a1", 51, "buy", "A", 40),
                   ("a2", 51, "buy", "A", 60), ("b1", 51, "buy", "B", 22)])
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH, current_balances={"A": 50, "B": 22})
    assert result["status"] == "OK"
    assert result["summary"]["first_buyers"]["bought_raw"] is None
    buyers = {row["owner"]: row for row in result["buyers"]}
    assert buyers["A"]["rank"] is None and buyers["B"]["rank"] is None
    assert buyers["A"]["first_signature"] is None and buyers["A"]["bought_raw"] is None
    assert buyers["A"]["status"] == "UNRESOLVED"
    assert buyers["B"]["bought_raw"] == "22"
