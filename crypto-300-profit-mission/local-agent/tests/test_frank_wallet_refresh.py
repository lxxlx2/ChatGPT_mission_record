"""Whole-Owner snapshot failures and durable publication, injected RPC only."""
import copy
import hashlib
import json
from decimal import localcontext
from urllib.error import HTTPError

import pytest

from mission_agent.mission_control.wallet_refresh import capture_owner, PROGRAMS
from mission_agent.mission_control.research_data import ResearchData
from test_meme_holder_ranks import key


WALLET, MINT, MINT22 = key(6000), key(6001), key(6002)
SECRET = "https://rpc.example.invalid/v2/SECRET_KEY"
PRIVATE = "/Users/private/SECRET_FILE.json"


def account(program, n, raw="1000000", *, mint=MINT, decimals=6):
    return {"pubkey": key(n), "account": {
        "owner": program, "executable": False,
        "data": {"program": "spl-token", "parsed": {"type": "account", "info": {
            "mint": mint, "owner": WALLET,
            "tokenAmount": {"amount": raw, "decimals": decimals, "uiAmount": None},
        }}, "space": 165},
    }}


class RPC:
    def __init__(self):
        self.results = [
            {"context": {"slot": 100}, "value": [account(PROGRAMS[0], 7000)]},
            {"context": {"slot": 103}, "value": [account(PROGRAMS[1], 7001, "0", mint=MINT22)]},
            {"context": {"slot": 104}, "value": 1234567890},
        ]
        self.calls = []
        self.fail = None
        self.raw_change = None

    def read_evidence(self, method, params):
        i = len(self.calls)
        self.calls.append((method, copy.deepcopy(params)))
        if i == self.fail:
            raise HTTPError(SECRET, 403, PRIVATE, {}, None)
        result = copy.deepcopy(self.results[i])
        envelope = {"jsonrpc": "2.0", "id": 1, "result": result}
        raw = json.dumps(envelope, separators=(",", ":")).encode()
        if self.raw_change:
            raw = self.raw_change(i, raw)
        return result, {"raw": raw, "provider": SECRET, "received_at": 1000 + i}


def capture(rpc, **kw):
    return capture_owner(WALLET, rpc, clock=lambda: 1010, **kw)


def test_full_open_owner_snapshot_contains_both_programs_zeros_native_and_exact_raw_receipts():
    rpc = RPC()
    receipts, checkpoints = [], []
    out = capture(rpc, save_receipt=lambda ref, raw: receipts.append((ref, raw)), checkpoint=checkpoints.append)
    assert out["status"] == "COMPLETE_WITHIN_SCOPE"
    assert out["scope"] == "FULL_OWNER_OPEN_ACCOUNTS_AT_FINALIZED_PROGRAM_SLOTS"
    assert out["same_slot_atomic"] is False and out["full_chain_history_verified"] is False
    assert out["account_count"] == out["mint_count"] == 2
    assert out["nonzero_mint_count"] == 1
    assert [x["program_id"] for x in out["programs"]] == list(PROGRAMS)
    assert [x["slot"] for x in out["programs"]] == [100, 103]
    assert out["native_sol"]["raw_amount"] == "1234567890"
    assert out["native_sol"]["ui_amount"] == "1.23456789"
    assert len(receipts) == 3 and len(checkpoints) == 2
    assert all(hashlib.sha256(raw).hexdigest() == ref["response_sha256"] for ref, raw in receipts)
    public = json.dumps(out)
    assert SECRET not in public and "SECRET_KEY" not in public and PRIVATE not in public
    assert out["observed_at"] == "1000" and out["expires_at"] == "1300"


def test_later_program_and_native_reads_inherit_previous_actual_min_context_slot():
    rpc = RPC()
    capture(rpc)
    assert rpc.calls[0] == ("getTokenAccountsByOwner", [WALLET, {"programId": PROGRAMS[0]}, {"encoding": "jsonParsed", "commitment": "finalized"}])
    assert rpc.calls[1][1][2]["minContextSlot"] == 100
    assert rpc.calls[2] == ("getBalance", [WALLET, {"commitment": "finalized", "minContextSlot": 103}])


def test_large_multiple_account_sum_and_native_precision_do_not_round_under_global_decimal_context():
    rpc = RPC()
    maximum = str(2**64 - 1)
    rpc.results[0]["value"] = [account(PROGRAMS[0], 7000, maximum), account(PROGRAMS[0], 7002, maximum)]
    rpc.results[2]["value"] = int(maximum)
    with localcontext() as context:
        context.prec = 3
        out = capture(rpc)
    mint = next(x for x in out["rows"] if x["mint"] == MINT)
    assert mint["raw_amount"] == "36893488147419103230"
    assert mint["ui_amount"] == "36893488147419.10323"
    assert out["native_sol"]["ui_amount"] == "18446744073.709551615"


@pytest.mark.parametrize("change", [
    lambda r: r.results[1].update(context={"slot": 99}),
    lambda r: r.results[1].update(context={"slot": True}),
    lambda r: r.results[1].update(value=None),
    lambda r: r.results[1].update(context=[]),
    lambda r: r.results[2].update(context={"slot": 102}),
    lambda r: r.results[2].update(value=True),
])
def test_incomplete_or_regressed_later_response_cannot_return_a_snapshot(change):
    rpc = RPC()
    change(rpc)
    with pytest.raises(ValueError):
        capture(rpc)


@pytest.mark.parametrize("change", [
    lambda r: r.results[0]["value"].append(copy.deepcopy(r.results[0]["value"][0])),
    lambda r: r.results[1]["value"][0].update(pubkey=r.results[0]["value"][0]["pubkey"]),
    lambda r: r.results[0]["value"][0]["account"].update(owner=PROGRAMS[1]),
    lambda r: r.results[0]["value"][0]["account"].update(executable=True),
    lambda r: r.results[0]["value"][0]["account"]["data"]["parsed"]["info"].update(owner=key(8000)),
    lambda r: r.results[0]["value"][0]["account"]["data"]["parsed"]["info"].update(mint=SECRET),
    lambda r: r.results[0]["value"][0]["account"].update(data=[PRIVATE]),
    lambda r: r.results[0]["value"][0]["account"]["data"]["parsed"]["info"].update(tokenAmount=PRIVATE),
    lambda r: r.results[0]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"].update(amount=str(2**64)),
    lambda r: r.results[0]["value"].append(account(PROGRAMS[0], 7002, mint=MINT, decimals=9)),
    lambda r: r.results[1]["value"].append(account(PROGRAMS[1], 7002, mint=MINT)),
])
def test_duplicate_wrong_owner_program_or_precision_metadata_is_not_silently_aggregated(change):
    rpc = RPC()
    change(rpc)
    with pytest.raises(ValueError) as raised:
        capture(rpc)
    assert SECRET not in str(raised.value) and PRIVATE not in str(raised.value)


@pytest.mark.parametrize("raw", [
    b'{"jsonrpc":"2.0","id":true,"result":{}}',
    b'{"jsonrpc":"2.0","id":2,"result":{}}',
    b'{"jsonrpc":"2.0","id":1,"result":{},"result":{}}',
    b'{"jsonrpc":"2.0","id":1,"result":{},"error":{}}',
])
def test_receipt_with_wrong_identity_duplicate_keys_or_error_never_admits_the_result(raw):
    rpc = RPC()
    rpc.raw_change = lambda i, original: raw if i == 0 else original
    with pytest.raises(ValueError):
        capture(rpc)


class DeferredExecutor:
    def submit(self, *args):
        pass


def repository(root, rpc_factory):
    data = ResearchData(root, wallet=WALLET, rpc_factory=rpc_factory,
                        market_client=None, observed_mints=lambda: [],
                        binding="fixed-source", code_sha="a" * 40, clock=lambda: 1010)
    data.executor.shutdown(wait=True)
    data.executor = DeferredExecutor()
    return data


def test_second_program_failure_preserves_previous_snapshot_and_records_safe_error_separately(tmp_path):
    rpc = RPC()
    data = repository(tmp_path, lambda: rpc)
    first = data.submit("balance", {"idempotency_key": "good"})
    data._run(first["job_id"])
    previous = data.latest("balance")
    assert data.job(first["job_id"])["state"] == "DONE"
    assert previous["observed_at"] == "1000"
    failed = RPC()
    failed.fail = 1
    data.rpc_factory = lambda: failed
    second = data.submit("balance", {"idempotency_key": "second-program-fails"})
    data._run(second["job_id"])
    state = data.job(second["job_id"])
    assert state["state"] == "ERROR" and state["errors"] == [{"code": "HTTP_403"}]
    assert state["result_ref"] is None and state["progress"]["completed_items"] == 1
    assert data.latest("balance") == previous
    assert SECRET not in json.dumps(state) and PRIVATE not in json.dumps(state)


def test_interrupted_resume_recaptures_both_programs_and_old_binding_cannot_resume(tmp_path):
    rpc = RPC()
    data = repository(tmp_path, lambda: rpc)
    job = data.submit("balance", {"idempotency_key": "interrupted"})
    data.active.clear()
    assert data.job(job["job_id"])["state"] == "PAUSED"
    data.binding = "changed-source"
    with pytest.raises(ValueError, match="^SOURCE_BINDING_CHANGED$"):
        data.resume(job["job_id"])
    data.binding = "fixed-source"
    data.resume(job["job_id"])
    data._run(job["job_id"])
    assert [method for method, _ in rpc.calls] == ["getTokenAccountsByOwner", "getTokenAccountsByOwner", "getBalance"]
    assert data.job(job["job_id"])["state"] == "DONE"
