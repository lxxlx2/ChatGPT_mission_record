"""Synthetic, read-only per-person Frank ledger scope acceptance."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control.frank_buys import read_buys
from mission_agent.signals.buy_admission import BuyDeliveryGate
from mission_agent.signals.delivery import drain
from mission_agent.signals.person_scope import load_staged_person_scopes
from mission_agent.signals.policy import USDC
from mission_agent.signals.registry import load as load_production_registry
from mission_agent.signals.store import Ledger


A1, A2, B1, B2, MINT, FOREIGN = [_b58(bytes([n]) * 32) for n in range(1, 7)]
NOW = 1796000000
PEOPLE = frozenset({"frank", "candidate"})


def registry(path, rows):
    path.write_text(json.dumps({"persons": [
        {"person_id": name, "enabled": enabled,
         "wallets": [{"chain": "solana", "address": addr} for addr in wallets]}
        for name, enabled, wallets in rows
    ]}))


def qualification(path):
    path.write_text(json.dumps({"version": 1, "records": [
        {"chain": "solana", "mint": MINT, "name": "synthetic", "status": "VERIFIED_MEME",
         "source": "fixture", "observed_at": NOW - 500}
    ]}))


def tx(ledger, person, wallet, n, raw_quantity, *, advance=False, stages=(), expected_insert=True):
    sig = _b58(n.to_bytes(64, "big"))
    raw_hash = hashlib.sha256(("fixture signed bytes " + str(n)).encode()).hexdigest()
    identity = {"wallet": wallet, "signature": sig, "slot": 100 + n, "block_time": NOW - 500 + n}
    e = {
        **identity, "classification": "ACTIVE_TRADE", "classification_reason": "SYNTHETIC_ONLY",
        "frank_is_signer": True,
        "evidence": {**identity, "raw_transaction_sha256": raw_hash, "wallet_is_signer": True,
                     "tx_err": None, "mechanical_classification": "ACTIVE_SWAP_LIKE",
                     "classification_evidence": dict.fromkeys(
                         ("dex_program_interaction", "swap_instruction_evidence", "opposing_economic_flows"), True)},
        "trade": {"mint": MINT, "direction": "BUY", "token_amount_raw": str(raw_quantity), "token_decimals": 0,
                  "quote_amount_raw": "2000000", "quote_decimals": 6, "quote_asset": USDC,
                  "quote_legs": [{"asset": USDC, "decimals": 6, "raw_delta": "-2000000"}],
                  "route_intermediate_evidence_status": "NO_INTERMEDIATE_TRANSFER_OBSERVED",
                  "route_amount_semantics": "DIRECT_OR_SINGLE_TARGET_QUOTE"},
    }
    assert ledger.put(person, e, raw_hash, "synthetic-no-path", advance=advance, dry_run=True,
                      stages=stages) == expected_insert
    return sig


class ReadOnlyPersonScopeTests(unittest.TestCase):
    def test_same_mint_and_signature_are_isolated_by_person_wallet_and_cursor(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reg, cfg, db = root / "registry", root / "qualifications", root / "forward.sqlite"
            registry(reg, [("frank", True, (A1, A2)), ("candidate", True, (B1, B2))])
            scopes = load_staged_person_scopes(reg, allowed_person_ids=PEOPLE)
            qualification(cfg)
            ledger = Ledger(db)
            try:
                for n in range(1, 33):
                    ap = tx(ledger, "frank", A1 if n % 2 else A2, n, n, advance=True)
                    bp = tx(ledger, "candidate", B1 if n % 2 else B2, n, 100 + n, advance=(n <= 29))
                    self.assertEqual(ap, bp)
                # A row with a matching person field but unregistered wallet must not appear.
                tx(ledger, "candidate", FOREIGN, 35, 900)
                # A registry wallet with the wrong person field must not appear.
                tx(ledger, "frank", B2, 36, 901)
                wrong = tx(ledger, "candidate", B1, 37, 902)
                old = ledger.db.execute("SELECT body FROM signatures WHERE wallet=? AND signature=?", (B1, wrong)).fetchone()[0]
                event = {**json.loads(old), "person_id": "frank"}
                ledger.db.execute("UPDATE signatures SET body=? WHERE wallet=? AND signature=?",
                                  (json.dumps(event), B1, wrong))
                ledger.db.commit()
                before = hashlib.sha256(db.read_bytes()).digest()

                def read(scope=None, **opts):
                    return read_buys(db, cfg, as_of=NOW, mint=MINT, person_scope=scope, **opts)

                a, b = scopes["frank"], scopes["candidate"]
                first_a, first_b = read(a), read(b)
                self.assertEqual(first_a["rows"][0]["signature"], first_b["rows"][0]["signature"])
                self.assertEqual([int(r["quantity"]) for r in first_a["rows"]], list(range(32, 2, -1)))
                self.assertEqual([int(r["quantity"]) for r in first_b["rows"]], list(range(132, 102, -1)))
                self.assertEqual([r["quantity"] for r in read(b, cursor=first_b["next_cursor"])["rows"]], ["102", "101"])
                self.assertEqual(len(read(b.for_wallet(B1))["rows"]), 16)
                self.assertEqual(len(read(b.for_wallet(B2))["rows"]), 16)
                self.assertEqual(ledger.cursor(A1)["slot"], 131)
                self.assertEqual(ledger.cursor(B1)["slot"], 129)
                self.assertEqual(ledger.cursor(B2)["slot"], 128)
                for foreign_scope, opts in ((a, {}), (None, {}), (b.for_wallet(B1), {}), (b, {"days": "1"})):
                    with self.subTest(scope=foreign_scope, opts=opts), self.assertRaisesRegex(ValueError, "INVALID_OR_STALE_CURSOR"):
                        read(foreign_scope, cursor=first_b["next_cursor"], **opts)
                with self.assertRaisesRegex(ValueError, "WALLET_OUTSIDE_PERSON_SCOPE"):
                    b.for_wallet(A1)
                self.assertEqual(read()["rows"][0]["quantity"], "901")  # Preserve the unscoped Frank contract.
                self.assertEqual(ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0], 0)
                self.assertEqual(hashlib.sha256(db.read_bytes()).digest(), before)
            finally:
                ledger.db.close()

    def test_outbox_identity_distinguishes_people_but_never_sends_staged_rows(self):
        with TemporaryDirectory() as tmp:
            filename = Path(tmp) / "forward.sqlite"
            stage = ({"signal_type": "FRANK_MULTIPLE_SIGNAL", "stage": "SUSPECTED_CONVICTION",
                      "reason_codes": ["FIXTURE_ONLY"]},)
            ledger = Ledger(filename)
            try:
                sig = tx(ledger, "frank", A1, 1, 1, stages=stage)
                self.assertEqual(tx(ledger, "candidate", B1, 1, 100, stages=stage), sig)
                self.assertEqual(tx(ledger, "frank", A2, 1, 1, stages=stage), sig)
                self.assertEqual(tx(ledger, "candidate", B2, 1, 100, stages=stage), sig)
            finally:
                ledger.db.close()
            restarted = Ledger(filename)
            try:
                tx(restarted, "frank", A1, 1, 1, stages=stage, expected_insert=False)
                tx(restarted, "candidate", B1, 1, 100, stages=stage, expected_insert=False)
                signals = restarted.db.execute(
                    "SELECT person_id,mint,signal_id,episode_id,body FROM signals ORDER BY person_id"
                ).fetchall()
                self.assertEqual([(s["person_id"], s["mint"]) for s in signals],
                                 [("candidate", MINT), ("frank", MINT)])
                self.assertNotEqual(signals[0]["signal_id"], signals[1]["signal_id"])
                self.assertNotEqual(signals[0]["episode_id"], signals[1]["episode_id"])
                self.assertTrue(all(json.loads(s["body"])["latest_trade_signature"] == sig for s in signals))
                for row in signals:
                    outbox = restarted.db.execute(
                        "SELECT channel,status,attempts FROM outbox WHERE signal_id=? ORDER BY channel",
                        (row["signal_id"],),
                    ).fetchall()
                    self.assertEqual([tuple(o) for o in outbox],
                                     [("gmail", "DRY_RUN_AUDIT", 0), ("local", "DRY_RUN_AUDIT", 0)])
                gate = BuyDeliveryGate()
                fake_live = {**json.loads(signals[0]["body"]), "delivery_mode": "LIVE"}
                self.assertEqual(gate.block_reason(restarted.db, fake_live), "NOT_FRANK_BUY")
                with patch("mission_agent.signals.gmail.kick") as kick, patch(
                    "mission_agent.signals.delivery.LocalNotifier"
                ) as notify:
                    drain(restarted, delivery_gate=gate)
                    notify.return_value.assert_not_called()
                    kick.assert_called_once_with(restarted, delivery_gate=gate)
                self.assertEqual(restarted.db.execute("SELECT sum(attempts) FROM outbox").fetchone()[0], 0)
            finally:
                restarted.db.close()

    def test_production_gate_stays_frank_only_and_ambiguous_staging_is_rejected(self):
        with TemporaryDirectory() as tmp:
            reg = Path(tmp) / "registry"
            registry(reg, [("frank", True, (A1,)), ("candidate", True, (B1,))])
            with self.assertRaisesRegex(ValueError, "FRANK_ONLY_ENABLED_REQUIRED"):
                load_production_registry(reg)
            with self.assertRaisesRegex(ValueError, "UNAPPROVED_STAGED_PERSON"):
                load_staged_person_scopes(reg, allowed_person_ids=frozenset({"frank"}))
            registry(reg, [("frank", True, (A1,)), ("candidate", False, (B1,))])
            self.assertEqual(load_production_registry(reg)[1], {A1: "frank"})
            with self.assertRaisesRegex(ValueError, "STAGED_PERSON_NOT_ENABLED"):
                load_staged_person_scopes(reg, allowed_person_ids=PEOPLE)
            registry(reg, [("frank", True, (A1,)), ("candidate", True, (A1,))])
            with self.assertRaisesRegex(ValueError, "WALLET_IN_MULTIPLE_PERSON_SCOPES"):
                load_staged_person_scopes(reg, allowed_person_ids=PEOPLE)
            registry(reg, [("frank", True, (A1,)), ("candidate", True, ("WRONG",))])
            with self.assertRaisesRegex(ValueError, "INVALID_PERSON_WALLETS"):
                load_staged_person_scopes(reg, allowed_person_ids=PEOPLE)


if __name__ == "__main__":
    unittest.main()
