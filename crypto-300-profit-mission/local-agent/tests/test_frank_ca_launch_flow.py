from collections import OrderedDict
import hashlib
import json

import pytest

from mission_agent.meme import launch_flow
from mission_agent.meme.cluster import CA_BLOCK_SIGNATURE_OPTIONS, RPCJobBudgetExceeded, SolanaReadOnlyRPC
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
    def __init__(self, txs, pages=None, block=None):
        self.txs = txs
        self.block = block
        self.block_reads = []
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
        if method == "getBlock":
            self.block_reads.append(params)
            assert params[1] == CA_BLOCK_SIGNATURE_OPTIONS
            if isinstance(self.block, Exception):
                raise self.block
            return self.block
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


def transient_sell(*, init_kind="initializeAccount3"):
    tx = transaction("sell", 104, "sell", DEV, 9)
    source_account = "ata-" + DEV
    message = tx["transaction"]["message"]
    meta = tx["meta"]
    transfer_group = meta["innerInstructions"][0]
    transfer_group["index"] = 1
    transfer = transfer_group["instructions"][0]
    transfer["parsed"]["info"]["authority"] = DEV
    token_program = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
    transfer["programId"] = token_program
    init = {"programId": token_program, "parsed": {"type": init_kind, "info": {
        "account": source_account, "mint": MINT, "owner": DEV,
    }}}
    close = {"programId": token_program, "parsed": {"type": "closeAccount", "info": {
        "account": source_account, "destination": DEV, "owner": DEV,
    }}}
    message["instructions"].insert(0, {"programId": "associated-token-program"})
    message["instructions"].append(close)
    meta["innerInstructions"].insert(0, {"index": 0, "instructions": [init]})
    for key in ("preTokenBalances", "postTokenBalances"):
        meta[key] = [row for row in meta[key] if row["owner"] == CURVE]
    return tx, init, transfer, close


@pytest.mark.parametrize("init_kind", ["initializeAccount", "initializeAccount2", "initializeAccount3"])
def test_transient_seller_owner_is_proved_by_ordered_init_transfer_and_close(init_kind):
    sell, _, _, _ = transient_sell(init_kind=init_kind)
    txs = fixture([("create", 100, "create", DEV, 0), ("buy", 102, "buy", "buyer", 100)])
    txs["sell"] = sell
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH)
    assert result["status"] == "OK" and result["transaction_errors"] == 0
    assert result["summary"]["first_buyers"]["count"] == 1
    assert result["dev"]["verified_sell"] == {"signature": "sell", "slot": 104, "token_raw": "9"}


@pytest.mark.parametrize("mismatch", [
    "wrong_mint", "wrong_program", "wrong_authority", "unsigned_owner", "unrelated_snapshot",
    "wrong_order", "authority_change", "opaque_mutation", "repeated_init", "wrong_close_owner",
])
def test_transient_owner_ambiguous_lifecycle_preserves_coverage_gap(mismatch):
    sell, init, transfer, close = transient_sell()
    message = sell["transaction"]["message"]
    meta = sell["meta"]
    token_program = init["programId"]
    source_account = init["parsed"]["info"]["account"]
    if mismatch == "wrong_mint":
        init["parsed"]["info"]["mint"] = "other-mint"
    if mismatch == "wrong_program":
        init["programId"] = TOKEN_PROGRAM
    if mismatch == "wrong_authority":
        transfer["parsed"]["info"]["authority"] = CURVE
    if mismatch == "unsigned_owner":
        message["accountKeys"][0]["signer"] = False
    if mismatch == "unrelated_snapshot":
        meta["postTokenBalances"].append({"mint": "other-mint", "owner": DEV, "accountIndex": 3})
    if mismatch == "wrong_order":
        message["instructions"][0], message["instructions"][2] = (
            message["instructions"][2], message["instructions"][0],
        )
        meta["innerInstructions"][0]["index"] = 2
    if mismatch == "authority_change":
        meta["innerInstructions"][0]["instructions"].append({
            "programId": token_program, "parsed": {"type": "setAuthority", "info": {
                "account": source_account, "authorityType": "accountOwner", "newAuthority": CURVE,
            }},
        })
    if mismatch == "opaque_mutation":
        meta["innerInstructions"][0]["instructions"].append({
            "programId": token_program, "accounts": [source_account], "data": "11",
        })
    if mismatch == "repeated_init":
        meta["innerInstructions"][0]["instructions"].append(init)
    if mismatch == "wrong_close_owner":
        close["parsed"]["info"]["owner"] = CURVE
    txs = fixture([("create", 100, "create", DEV, 0), ("buy", 102, "buy", "buyer", 100)])
    txs["sell"] = sell
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH)
    assert result["status"] == "PARTIAL" and result["transaction_errors"] == 1
    assert result["reason"] == "TRANSACTION_EVIDENCE_INCOMPLETE"
    assert result["dev"]["verified_sell"] is None


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
    assert rpc.block_reads == []
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


def test_known_creator_maintenance_does_not_make_the_opening_incomplete():
    txs = fixture([("create", 10, "create", DEV, 0),
                   ("migrate", 11, "migrate_bonding_curve_creator", DEV, 0),
                   ("fees", 12, "distribute_creator_fees_v2", DEV, 0),
                   ("buy", 13, "buy", "one-buyer", 50)])
    for key in ("migrate", "fees"):
        txs[key]["meta"]["innerInstructions"] = []
    result = collect_launch_flow(MINT, Replay(txs), launch=LAUNCH)
    assert result["status"] == "OK"
    assert result["transaction_errors"] == 0
    assert [buyer["owner"] for buyer in result["buyers"]] == ["one-buyer"]

BLOCKHASH = "1" * 31 + "2"
A_SIGNATURE = "1" * 63 + "2"
B_SIGNATURE = "1" * 63 + "3"
OTHER_SIGNATURE = "1" * 63 + "4"


def cutoff_transactions():
    return fixture([("create", 10, "create", DEV, 0)]
                   + [(f"buyer-{i}", 11 + i, "buy", f"user-{i}", 1) for i in range(69)]
                   + [(A_SIGNATURE, 90, "buy", "candidate-a", 1),
                      (B_SIGNATURE, 90, "buy", "candidate-b", 2),
                      (OTHER_SIGNATURE, 90, None, DEV, 0)])


def cutoff_block(signatures):
    return {"blockhash": BLOCKHASH, "parentSlot": 89, "signatures": signatures}


def test_finalized_block_selects_buyer_independently_of_address_page_order():
    rpc = Replay(cutoff_transactions(), block=cutoff_block([B_SIGNATURE, OTHER_SIGNATURE, A_SIGNATURE]))
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH)
    assert rpc.block_reads == [[90, CA_BLOCK_SIGNATURE_OPTIONS]]
    assert result["status"] == "OK"
    assert len(result["buyers"]) == result["summary"]["first_buyers"]["count"] == 70
    assert result["buyers"][-1]["owner"] == "candidate-b" and result["buyers"][-1]["rank"] == 70
    assert result["verified_after_cutoff_buyers"][0]["owner"] == "candidate-a"
    assert result["verified_after_cutoff_buyers"][0]["rank"] == 71
    assert result["cutoff_order"] == {
        "basis": "FINALIZED_BLOCK_SIGNATURE_ORDER",
        "slot": 90,
        "status": "VERIFIED",
        "blockhash": BLOCKHASH,
        "parent_slot": 89,
        "curve_signature_positions": [
            {"signature": B_SIGNATURE, "block_index": 0},
            {"signature": OTHER_SIGNATURE, "block_index": 1},
            {"signature": A_SIGNATURE, "block_index": 2},
        ],
    }


@pytest.mark.parametrize(("block", "evidence_status"), [
    (OSError("test RPC unavailable"), "SOURCE_UNAVAILABLE"),
    (cutoff_block([B_SIGNATURE, A_SIGNATURE]), "CURVE_SIGNATURES_MISSING"),
    (cutoff_block([B_SIGNATURE, A_SIGNATURE, OTHER_SIGNATURE, A_SIGNATURE]), "BLOCK_EVIDENCE_INVALID"),
    (cutoff_block([B_SIGNATURE, A_SIGNATURE, OTHER_SIGNATURE, "invalid"]), "BLOCK_EVIDENCE_INVALID"),
    ({**cutoff_block([B_SIGNATURE, A_SIGNATURE, OTHER_SIGNATURE]), "parentSlot": 91}, "BLOCK_EVIDENCE_INVALID"),
])
def test_unverified_block_never_guesses_the_cutoff_member(block, evidence_status):
    rpc = Replay(cutoff_transactions(), block=block)
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH)
    assert rpc.block_reads == [[90, CA_BLOCK_SIGNATURE_OPTIONS]]
    assert result["status"] == "PARTIAL" and result["reason"] == "BUYER_ORDER_AT_CUTOFF_UNRESOLVED"
    assert result["cutoff_order"]["status"] == evidence_status
    assert "summary" not in result and len(result["buyers"]) == 69
    assert {row["owner"] for row in result["unranked_cutoff_buyers"]} == {"candidate-a", "candidate-b"}


def test_block_signature_cannot_split_two_buyers_inside_its_transaction():
    txs = cutoff_transactions()
    tx_a = txs[A_SIGNATURE]
    tx_b = txs.pop(B_SIGNATURE)
    message = tx_a["transaction"]["message"]
    other_message = tx_b["transaction"]["message"]
    message["accountKeys"].extend(other_message["accountKeys"][i] for i in (0, 3))
    message["instructions"].extend(other_message["instructions"])
    nested = tx_b["meta"]["innerInstructions"][0]
    tx_a["meta"]["innerInstructions"].append({**nested, "index": 1})
    balances = tx_a["meta"]["preTokenBalances"]
    balances.append({"accountIndex": 7, "mint": MINT, "owner": "candidate-b"})

    rpc = Replay(txs, block=cutoff_block([A_SIGNATURE, OTHER_SIGNATURE]))
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH)
    assert rpc.block_reads == [[90, CA_BLOCK_SIGNATURE_OPTIONS]]
    assert result["cutoff_order"]["status"] == "BOUNDARY_WITHIN_ONE_TRANSACTION"
    assert result["status"] == "PARTIAL" and "summary" not in result
    assert len(result["buyers"]) == 69 and len(result["unranked_cutoff_buyers"]) == 2


def test_unclassified_transaction_skips_unnecessary_block_read():
    txs = cutoff_transactions()
    txs[OTHER_SIGNATURE]["meta"].pop("err")
    rpc = Replay(txs, block=cutoff_block([B_SIGNATURE, A_SIGNATURE, OTHER_SIGNATURE]))
    result = collect_launch_flow(MINT, rpc, launch=LAUNCH)
    assert rpc.block_reads == []
    assert result["status"] == "PARTIAL" and result["reason"] == "TRANSACTION_EVIDENCE_INCOMPLETE"


def test_block_allowlist_permits_exact_finalized_signature_request_only():
    valid = [90, CA_BLOCK_SIGNATURE_OPTIONS]
    requests = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps({"result": cutoff_block([A_SIGNATURE])}).encode()

    def open_url(request, *, timeout):
        requests.append(json.loads(request.data))
        return Response()

    rpc = SolanaReadOnlyRPC(open_url=open_url, fallback_endpoints=[])
    for params in ([True, CA_BLOCK_SIGNATURE_OPTIONS], [-1, CA_BLOCK_SIGNATURE_OPTIONS],
                   [2**64, CA_BLOCK_SIGNATURE_OPTIONS], [90],
                   [90, {**CA_BLOCK_SIGNATURE_OPTIONS, "commitment": "confirmed"}],
                   [90, {**CA_BLOCK_SIGNATURE_OPTIONS, "transactionDetails": "full"}],
                   [90, {**CA_BLOCK_SIGNATURE_OPTIONS, "rewards": 0}],
                   [90, {**CA_BLOCK_SIGNATURE_OPTIONS, "maxSupportedTransactionVersion": False}],
                   [90, {**CA_BLOCK_SIGNATURE_OPTIONS, "minContextSlot": 88}]):
        with pytest.raises(ValueError, match="CA_FINALIZED_BLOCK_SIGNATURE_QUERY_INVALID"):
            rpc.call("getBlock", params)
    assert requests == []
    assert rpc.call("getBlock", valid) == cutoff_block([A_SIGNATURE])
    assert requests == [{"jsonrpc": "2.0", "id": 1, "method": "getBlock", "params": valid}]
