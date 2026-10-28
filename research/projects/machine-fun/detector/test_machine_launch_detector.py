import asyncio
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from machine_launch_detector import (
    B58_ALPHABET, PLATFORM_CONFIG, LAUNCHLAB_PROGRAM, Detector, Journal,
    decode_base58, detect_launches,
)


def b58(data):
    v = int.from_bytes(data, "big")
    out = ""
    while v:
        v, mod = divmod(v, 58)
        out = B58_ALPHABET[mod] + out
    return "1" * (len(data) - len(data.lstrip(b"\x00"))) + out


def tx_template(*, platform=PLATFORM_CONFIG, cpi=False, discriminator="4399af27da102620",
                failed=False, loaded=False, top=True):
    static = ["PayerPubkey111", "CreatorPubkey111", "Global111", platform, "Vault111", "Pool111", "Mint111", "Quote111"]
    prog = len(static)
    static.append(LAUNCHLAB_PROGRAM)
    ix = {"programIdIndex": prog, "accounts": list(range(8)), "data": b58(bytes.fromhex(discriminator) + b"data")}
    # program_id index 8, account list follows the Anchor docs.
    message = {"accountKeys": static, "instructions": [ix] if top else []}
    meta = {"err": {"InstructionError": [0, "InvalidArgument"]} if failed else None,
            "innerInstructions": [{"index": 0, "instructions": [ix]}] if cpi else []}
    if loaded:
        message["accountKeys"] = static[:4] + [LAUNCHLAB_PROGRAM]
        meta["loadedAddresses"] = {"writable": static[4:8], "readonly": []}
        ix["programIdIndex"] = 4
        ix["accounts"] = [0, 1, 2, 3, 5, 6, 7, 8]
    return {"slot": 462490424, "blockTime": 1793193499, "transaction": {"message": message}, "meta": meta}


class ParserTests(unittest.TestCase):
    def test_base58_known_bytes(self):
        data = bytes.fromhex("4399af27da102620") + b"hello"
        self.assertEqual(decode_base58(b58(data)), data)
        self.assertEqual(decode_base58("1"), b"\x00")
        with self.assertRaises(ValueError):
            decode_base58("I")

    def test_successful_initialize_is_candidate(self):
        hits = detect_launches(tx_template(), "signature1")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].mint, "Mint111")
        self.assertEqual(hits[0].platform_config, PLATFORM_CONFIG)
        self.assertEqual(hits[0].instruction, "InitializeV2")
        self.assertEqual(hits[0].evidence, "CHAIN_PLATFORM_CANDIDATE_UNENDORSED")

    def test_cpi_initialize_with_token_2022_is_candidate(self):
        tx = tx_template(cpi=True, top=False, discriminator="25be7ede2c9aab11")
        hits = detect_launches(tx, "signature2")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].instruction, "InitializeWithToken2022")

    def test_failed_tx_ignored(self):
        self.assertEqual(detect_launches(tx_template(failed=True), "s"), [])

    def test_unrelated_platform_ignored(self):
        self.assertEqual(detect_launches(tx_template(platform="OtherPlatform"), "s"), [])

    def test_swap_data_ignored(self):
        self.assertEqual(detect_launches(tx_template(discriminator="1234567890abcdef"), "s"), [])

    def test_duplicate_cpi_top_level_deduplicated(self):
        self.assertEqual(len(detect_launches(tx_template(cpi=True), "s")), 1)

    def test_broken_accounts_fail_closed(self):
        tx = tx_template()
        tx["transaction"]["message"]["instructions"][0]["accounts"] = [0, 1]
        self.assertEqual(detect_launches(tx, "s"), [])

    def test_lookup_table_accounts(self):
        hits = detect_launches(tx_template(loaded=True), "s")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].mint, "Mint111")


class FakeRpc:
    def __init__(self, items, txs):
        self.items, self.txs = items, txs
        self.calls = 0
    def signature_page(self, platform, before, limit):
        self.calls += 1
        pos = 0
        if before is not None:
            pos = next((i + 1 for i, item in enumerate(self.items) if item["signature"] == before), len(self.items))
        return self.items[pos:pos + limit]
    def transaction(self, sig):
        return self.txs.get(sig)


def entry(sig, slot, err=None):
    return {"signature": sig, "slot": slot, "err": err}


class JournalAndBackfillTests(unittest.TestCase):
    def test_journal_persists_and_never_downgrades_delivered(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "events.sqlite"
            j = Journal(p)
            j.save("sig", 3, "CANDIDATE", "[]")
            j.save("sig", 3, "LOCAL_ACCEPTED", "[]")
            j.save("sig", 3, "PENDING")
            j.set_checkpoint("old", 2)
            j.close()
            j2 = Journal(p)
            self.assertEqual(j2.state("sig"), "LOCAL_ACCEPTED")
            self.assertEqual(j2.checkpoint(), ("old", 2))
            j2.close()

    def test_backfill_detects_new_launch_and_ignores_swap(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(Path(root) / "db")
            j.set_checkpoint("old", 10)
            rpc = FakeRpc([entry("new", 13), entry("swap", 12), entry("old", 10)],
                          {"new": tx_template(), "swap": tx_template(discriminator="1234567890abcdef")})
            watcher = Detector(rpc, j, page_size=2, max_pages=5)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                asyncio.run(watcher.backfill())
            self.assertEqual(j.state("new"), "STDOUT_EMITTED")
            self.assertEqual(j.state("swap"), "IGNORED")
            self.assertEqual(j.checkpoint(), ("new", 13))
            self.assertIn("MACHINE_FUN_CHAIN_CANDIDATE", out.getvalue())
            j.close()

    def test_checkpoint_never_advances_on_page_budget_gap(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(Path(root) / "db")
            j.set_checkpoint("old", 1)
            rpc = FakeRpc([entry("n3", 4), entry("n2", 3), entry("n1", 2), entry("old", 1)], {})
            watcher = Detector(rpc, j, page_size=2, max_pages=1)
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                asyncio.run(watcher.backfill())
            self.assertIn("COVERAGE_GAP", stderr.getvalue())
            self.assertEqual(j.checkpoint(), ("old", 1))
            self.assertEqual(j.db.execute("SELECT COUNT(*) FROM gaps").fetchone()[0], 1)
            j.close()

    def test_rpc_unavailable_persists_pending(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(Path(root) / "db")
            rpc = FakeRpc([], {})
            watcher = Detector(rpc, j)
            async def no_sleep(_):
                return None
            with patch("machine_launch_detector.asyncio.sleep", new=no_sleep):
                asyncio.run(watcher.process("unknown", 42))
            self.assertEqual(j.state("unknown"), "PENDING")
            j.close()

    def test_first_boot_sets_fence_without_false_old_alert(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(Path(root) / "db")
            rpc = FakeRpc([entry("already", 12)], {"already": tx_template()})
            watcher = Detector(rpc, j)
            with contextlib.redirect_stderr(io.StringIO()):
                asyncio.run(watcher.backfill())
            self.assertEqual(j.checkpoint(), ("already", 12))
            self.assertEqual(j.state("already"), None)
            j.close()

    def test_local_notification_success_records_accepted_only(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(Path(root) / "db")
            rpc = FakeRpc([], {"launch": tx_template()})
            watcher = Detector(rpc, j, local_notification=True)
            with patch("machine_launch_detector.subprocess.run") as call:
                with contextlib.redirect_stdout(io.StringIO()):
                    asyncio.run(watcher.process("launch", 123))
            self.assertEqual(j.state("launch"), "LOCAL_ACCEPTED")
            self.assertEqual(call.call_count, 1)
            j.close()

    def test_local_notification_failed_remains_candidate(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(Path(root) / "db")
            rpc = FakeRpc([], {"launch": tx_template()})
            watcher = Detector(rpc, j, local_notification=True)
            with patch("machine_launch_detector.subprocess.run", side_effect=RuntimeError("unavailable")):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    asyncio.run(watcher.process("launch", 123))
            self.assertEqual(j.state("launch"), "CANDIDATE")
            j.close()

    def test_malformed_rpc_result_stays_pending(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(Path(root) / "db")
            rpc = FakeRpc([], {"bad": {"meta": {}, "transaction": {}}})
            watcher = Detector(rpc, j)
            asyncio.run(watcher.process("bad", 123))
            self.assertEqual(j.state("bad"), "PENDING")
            j.close()


if __name__ == "__main__":
    unittest.main()
