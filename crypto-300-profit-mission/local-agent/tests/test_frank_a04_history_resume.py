"""A04 realistic bounded chain history pagination/resume from a local journal."""
import json

import pytest

from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import (
    HistoryJournal, WalletHistoryCollector, SourceEvidenceError,
)


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58(raw):
    n = int.from_bytes(raw, "big")
    res = ""
    while n:
        n, v = divmod(n, 58)
        res = ALPHABET[v] + res
    return "1" * (len(raw) - len(raw.lstrip(b"\\x00"))) + res


W1, W2, MINT, ATA1, ATA2 = [
    b58(bytes([i]) * 32) for i in range(2, 7)
]


def signature(n):
    return b58(n.to_bytes(8, "big") + b"Z" * 56)


def receipt(sig, slot, wallet, *, other=None):
    keys = [{"pubkey": wallet}]
    if other:
        keys.append({"pubkey": other})
    return {
        "slot": slot, "transaction": {
            "signatures": [sig], "message": {"accountKeys": keys,
                                             "instructions": []},
        },
        "meta": {
            "err": None, "preTokenBalances": [], "postTokenBalances": [],
            "fee": 5000, "innerInstructions": [],
        },
    }


class FakeRPC:
    """Finalized, descending and exclusive before cursors only."""

    def __init__(self, wallet, count, shared_tx=False):
        self.wallet = wallet
        self.rows = [{"signature": signature(i + 1), "slot": 10000 - i,
                      "confirmationStatus": "finalized", "err": None}
                     for i in range(count)]
        self.calls = []
        self.unavailable_signatures = set()
        self.missing_details = set()
        self.unavailable_page_before = set()
        self.corrupt_slot = False
        self.shared_tx = shared_tx

    def __call__(self, method, args):
        self.calls.append((method, args))
        if method == "getSignaturesForAddress":
            wallet, config = args
            assert wallet == self.wallet
            assert config["commitment"] == "finalized"
            assert 1 <= config["limit"] <= 1000
            before = config.get("before")
            if before in self.unavailable_page_before:
                self.unavailable_page_before.remove(before)
                return {"error": {"code": 429, "message": "RPC rate limited"}}
            idx = next((i + 1 for i, row in enumerate(self.rows)
                        if row["signature"] == before), 0) if before else 0
            return {"result": self.rows[idx:idx + config["limit"]]}
        assert method == "getTransaction"
        sig, config = args
        assert config == {"encoding": "jsonParsed", "commitment": "finalized",
                          "maxSupportedTransactionVersion": 0}
        if sig in self.unavailable_signatures:
            self.unavailable_signatures.remove(sig)
            raise TimeoutError("connection unavailable")
        if sig in self.missing_details:
            self.missing_details.remove(sig)
            return {"result": None}
        match = next(x for x in self.rows if x["signature"] == sig)
        return {"result": receipt(sig, match["slot"] + int(self.corrupt_slot),
                                  self.wallet,
                                  other=W2 if self.shared_tx else None)}


def setup(tmp_path, name="wallet-history-sidecar.sqlite"):
    store = WalletEvidenceStore(tmp_path / name)
    return store, HistoryJournal(store)


def test_1005_signatures_across_three_full_and_short_pages_and_terminal_empty(tmp_path):
    store, journal = setup(tmp_path)
    try:
        rpc = FakeRPC(W1, 1005)
        result = WalletHistoryCollector(journal, rpc, wallet=W1, page_size=400).collect(
            max_pages=5, tx_budget=1100)
        assert result["pages_fetched_this_run"] == 4
        assert result["transactions_imported_this_run"] == 1005
        assert result["captured"] == 1005
        assert result["pending"] == 0
        assert result["page_count"] == 4
        assert result["pagination_end_observed"]
        assert result["coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
        assert result["status"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
        assert not result["history_complete"]
        assert store.count("RAW_TX") == 1005
        assert store.count("WALLET_TX_VIEW") == 1005
        assert all(call[1][1]["commitment"] == "finalized"
                   for call in rpc.calls if call[0] == "getSignaturesForAddress")
        assert len({call[1][1].get("before") for call in rpc.calls
                    if call[0] == "getSignaturesForAddress"}) == 4
    finally:
        store.close()


def test_restart_after_page_journal_before_any_tx_does_not_lose_signatures(tmp_path):
    store, journal = setup(tmp_path)
    rpc = FakeRPC(W1, 5)
    first = WalletHistoryCollector(journal, rpc, wallet=W1, page_size=5).collect(
        max_pages=1, tx_budget=0)
    assert first["pending"] == 5 and first["captured"] == 0
    before = first["next_before"]
    store.close()
    store, journal = setup(tmp_path)
    try:
        second = WalletHistoryCollector(journal, rpc, wallet=W1, page_size=5).collect(
            max_pages=0, tx_budget=5)
        assert second["next_before"] == before
        assert second["pending"] == 0
        assert second["captured"] == 5
        assert store.count("RAW_TX") == 5
        assert not second["history_complete"]
    finally:
        store.close()


def test_page_429_fails_closed_and_retry_uses_identical_before(tmp_path):
    store, journal = setup(tmp_path)
    try:
        rpc = FakeRPC(W1, 3)
        rpc.unavailable_page_before.add(None)
        reader = WalletHistoryCollector(journal, rpc, wallet=W1, page_size=2)
        bad = reader.collect(max_pages=3, tx_budget=10)
        assert bad["status"] == "SOURCE_LIMITED"
        assert bad["captured"] == bad["pending"] == bad["page_count"] == 0
        assert bad["next_before"] is None
        fixed = reader.collect(max_pages=3, tx_budget=10)
        assert fixed["captured"] == 3
        assert fixed["pagination_end_observed"]
        assert fixed["last_error_code"] is None
        assert [c[1][1].get("before") for c in rpc.calls
                if c[0] == "getSignaturesForAddress"][:2] == [None, None]
    finally:
        store.close()


@pytest.mark.parametrize("failure", ["timeout", "null"])
def test_tx_failure_keeps_pending_durable_and_resume_before_next_page(tmp_path, failure):
    store, journal = setup(tmp_path)
    rpc = FakeRPC(W1, 4)
    target = rpc.rows[0]["signature"]
    if failure == "timeout":
        rpc.unavailable_signatures.add(target)
    else:
        rpc.missing_details.add(target)
    try:
        worker = WalletHistoryCollector(journal, rpc, wallet=W1, page_size=3)
        partial = worker.collect(max_pages=2, tx_budget=10)
        assert partial["pending"] == 3
        assert partial["page_count"] == 1
        assert partial["next_before"] == rpc.rows[2]["signature"]
        assert store.count("RAW_TX") == 0
        resumed = worker.collect(max_pages=2, tx_budget=10)
        assert resumed["captured"] == 4
        assert resumed["pending"] == 0
        assert resumed["pagination_end_observed"]
        assert store.count("RAW_TX") == 4
    finally:
        store.close()


def test_global_signature_deduplicated_across_wallets_but_views_separate(tmp_path):
    store, journal = setup(tmp_path)
    sig = signature(42)
    # Shared signature/slot with same raw transaction, regardless of which
    # wallet requested it. 0 economic market BUY by either viewpoint.
    original = receipt(sig, 900, W1, other=W2)
    class SharedRPC:
        def __init__(self):
            self.wallets = set()
        def __call__(self, method, args):
            if method == "getSignaturesForAddress":
                wallet, config = args
                self.wallets.add(wallet)
                if config.get("before"):
                    return {"result": []}
                return {"result": [{"signature": sig, "slot": 900,
                                    "confirmationStatus": "finalized"}]}
            return {"result": original}
    try:
        source = SharedRPC()
        for wallet in (W1, W2):
            result = WalletHistoryCollector(journal, source, wallet=wallet,
                                            page_size=1).collect(max_pages=2, tx_budget=4)
            assert result["captured"] == 1
        assert store.count("RAW_TX") == 1
        assert store.count("WALLET_TX_VIEW") == 2
        saved = json.loads(store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='RAW_TX'",
        ).fetchone()[0])
        assert saved["transaction"]["signatures"][0] == sig
        assert saved["meta"]["preTokenBalances"] == []
        for row in store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='WALLET_TX_VIEW'"
        ).fetchall():
            view = json.loads(row[0])
            assert view["active_market_buys_confirmed"] == 0
            assert view["person_pnl_usd"] is None
    finally:
        store.close()


def test_conflicting_same_signature_raw_source_rolls_back_view_and_cursor_state(tmp_path):
    store, journal = setup(tmp_path)
    sig = signature(44)
    original = receipt(sig, 901, W1, other=W2)
    edited = receipt(sig, 901, W1, other=W2)
    edited["meta"]["fee"] = 7000
    class Conflicting:
        def __init__(self):
            self.which = 0
        def __call__(self, method, args):
            if method == "getSignaturesForAddress":
                if args[1].get("before"):
                    return {"result": []}
                return {"result": [{"signature": sig, "slot": 901,
                                    "confirmationStatus": "finalized"}]}
            return {"result": original if self.which == 0 else edited}
    try:
        source = Conflicting()
        WalletHistoryCollector(journal, source, wallet=W1, page_size=1).collect(
            max_pages=1, tx_budget=1)
        source.which = 1
        output = WalletHistoryCollector(journal, source, wallet=W2, page_size=1).collect(
            max_pages=1, tx_budget=1)
        assert output["pending"] == 1
        assert output["captured"] == 0
        assert output["status"] == "SOURCE_LIMITED"
        assert store.count("RAW_TX") == 1
        assert store.count("WALLET_TX_VIEW") == 1
    finally:
        store.close()


def test_source_receipt_slot_mismatch_does_not_advance_economic_evidence(tmp_path):
    store, journal = setup(tmp_path)
    rpc = FakeRPC(W1, 1)
    rpc.corrupt_slot = True
    try:
        result = WalletHistoryCollector(journal, rpc, wallet=W1).collect(
            max_pages=1, tx_budget=3)
        assert result["status"] == "SOURCE_LIMITED"
        assert result["pending"] == 1
        assert result["captured"] == 0
        assert store.count("RAW_TX") == 0
    finally:
        store.close()


def test_source_page_bad_order_signature_and_nonfinalized_rejected_without_cursor(tmp_path):
    store, journal = setup(tmp_path)
    try:
        sigs = [
            {"signature": signature(11), "slot": 90, "confirmationStatus": "finalized"},
            {"signature": signature(12), "slot": 91, "confirmationStatus": "finalized"},
        ]
        with pytest.raises(SourceEvidenceError, match="PAGE_NOT_NEWEST_FIRST"):
            journal.record_page(W1, None, sigs)
        assert journal.state(W1)["page_count"] == 0
        sigs[1]["slot"] = 89
        sigs[1]["confirmationStatus"] = "confirmed"
        with pytest.raises(SourceEvidenceError, match="SIGNATURE_NOT_FINALIZED"):
            journal.record_page(W1, None, sigs)
        assert journal.state(W1)["page_count"] == 0
    finally:
        store.close()


def test_sidecar_read_only_cannot_initialize_cursor(tmp_path):
    store, _ = setup(tmp_path)
    store.close()
    readonly = WalletEvidenceStore(tmp_path / "wallet-history-sidecar.sqlite", read_only=True)
    try:
        with pytest.raises(PermissionError):
            HistoryJournal(readonly)
    finally:
        readonly.close()


def test_no_pnl_or_full_chain_history_from_terminal_rpc_page(tmp_path):
    store, journal = setup(tmp_path)
    try:
        result = WalletHistoryCollector(journal, FakeRPC(W1, 0),
                                        wallet=W1).collect(max_pages=1)
        assert result["pagination_end_observed"]
        assert result["history_complete"] is False
        assert result["cost_basis_usd"] is result["realized_pnl_usd"] is None
        assert result["coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
    finally:
        store.close()
