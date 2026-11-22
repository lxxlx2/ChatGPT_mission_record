"""Regression tests through the durable Scanner path with synthetic RPC only."""

import gzip
import json

import pytest

from mission_agent.signals.scanner import Scanner
from mission_agent.signals.store import Ledger


WALLET = "fixture-wallet"
SEED = {"signature": "seed", "slot": 10}
FIRST = {"signature": "first", "slot": 11}
SECOND = {"signature": "second", "slot": 12}


def raw(signature, slot):
    return {"slot": slot, "blockTime": 100, "transaction": {"signatures": [signature]}}


class FixtureRPC:
    def __init__(self, pages, transactions):
        self.pages = pages
        self.transactions = transactions
        self.raw_reads = []

    def signatures(self, before=None):
        return self.pages[before]

    def transaction(self, signature):
        self.raw_reads.append(signature)
        return self.transactions[signature]


def scanner(tmp_path, rpc, *, checkpoint=True):
    ledger = Ledger(tmp_path / "ledger.sqlite")
    if checkpoint:
        ledger.checkpoint(WALLET, SEED["signature"], SEED["slot"])
    return ledger, Scanner(ledger, {WALLET: "frank"}, tmp_path / "raw", {WALLET: rpc})


@pytest.mark.parametrize(("bad", "error"), [
    (raw("second", 99), "CHAIN_SLOT_CONFLICT"),
    (raw("a-different-signature", 12), "CHAIN_SIGNATURE_CONFLICT"),
    ({"slot": 12, "transaction": {"signatures": "prefix-second"}}, "CHAIN_SIGNATURE_CONFLICT"),
    ({"slot": 12, "transaction": {"message": {}}}, "CHAIN_SIGNATURE_CONFLICT"),
    ({"slot": 12, "transaction": {"signatures": ["a-different-signature", "second"]}}, "CHAIN_SIGNATURE_CONFLICT"),
    ({**raw("second", 12), "blockTime": float("nan")}, "CHAIN_TRANSACTION_INVALID"),
])
def test_invalid_transaction_does_not_poison_archive_and_restart_fetches_only_pending(tmp_path, bad, error):
    rpc = FixtureRPC({None: [SECOND, FIRST, SEED]}, {"first": raw("first", 11), "second": bad})
    ledger, service = scanner(tmp_path, rpc)
    with pytest.raises(ValueError, match=error):
        service.cycle(WALLET)
    rejected = service.raw_root / "second.json.gz"
    assert not rejected.exists()
    assert ledger.cursor(WALLET)["signature"] == "first"
    assert dict(ledger.db.execute("SELECT signature,state FROM signature_detections")) == {
        "first": "CLASSIFIED_DURABLE", "second": "RAW_PENDING",
    }
    ledger.db.close()

    rpc.transactions["second"] = raw("second", 12)
    ledger, service = scanner(tmp_path, rpc, checkpoint=False)
    assert service.cycle(WALLET)["new_signatures"] == 1
    assert service.cycle(WALLET)["new_signatures"] == 0
    assert json.loads(gzip.decompress(rejected.read_bytes())) == rpc.transactions["second"]
    assert rpc.raw_reads == ["first", "second", "second"]
    assert ledger.cursor(WALLET)["signature"] == "second"
    assert ledger.db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 0
    ledger.db.close()


@pytest.mark.parametrize(("pages", "error"), [
    ({None: [SECOND, {"signature": "seed", "slot": 11}]}, "CURSOR_SLOT_CONFLICT"),
    ({None: [SECOND], "second": [{"signature": "second", "slot": 11}, SEED]}, "SIGNATURE_SLOT_CONFLICT"),
    ({None: [FIRST, SECOND, SEED]}, "SIGNATURE_PAGE_ORDER_INVALID"),
    ({None: [{"signature": "../outside", "slot": 12}, SEED]}, "INVALID_SIGNATURE_ROW"),
])
def test_contradictory_signature_pages_hold_checkpoint_without_fetching_raw(tmp_path, pages, error):
    rpc = FixtureRPC(pages, {"first": raw("first", 11), "second": raw("second", 12)})
    ledger, service = scanner(tmp_path, rpc)
    with pytest.raises(ValueError, match=error):
        service.cycle(WALLET)
    assert ledger.cursor(WALLET)["signature"] == "seed"
    assert rpc.raw_reads == []
    assert ledger.db.execute("SELECT COUNT(*) FROM signature_detections").fetchone()[0] == 0
    ledger.db.close()


def test_conflicting_already_published_raw_is_preserved_in_place(tmp_path):
    rpc = FixtureRPC({None: [FIRST, SEED]}, {"first": raw("first", 11)})
    ledger, service = scanner(tmp_path, rpc)
    path = service.raw_root / "first.json.gz"
    original = gzip.compress(json.dumps(raw("first", 99)).encode(), mtime=0)
    path.write_bytes(original)
    with pytest.raises(ValueError, match="CHAIN_SLOT_CONFLICT"):
        service.cycle(WALLET)
    assert path.read_bytes() == original
    assert rpc.raw_reads == []
    assert ledger.cursor(WALLET)["signature"] == "seed"
    ledger.db.close()
