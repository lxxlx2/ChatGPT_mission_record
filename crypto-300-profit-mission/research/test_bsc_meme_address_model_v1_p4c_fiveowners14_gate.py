"""Adversarial offline tests; no RPC, wallets, deployment or trade outputs."""
import copy
import unittest

from bsc_meme_address_model_v1_p4c_fiveowners14_gate import classify, load, PINS


class FiveOwnersFourMajorsPinnedSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = load()

    def reject(self, mutate):
        copied = copy.deepcopy(self.original)
        mutate(copied)
        with self.assertRaises(ValueError):
            classify(copied)

    def test_pinned_real_source_roundtrip_is_not_trading_signal(self):
        out = classify(self.original)
        self.assertEqual(len(PINS), 6)
        self.assertEqual(out["p2_original_episodes"], [15, 31, 38, 46, 44])
        self.assertEqual(out["frozen_original_signed_transactions"], 14)
        self.assertEqual(out["original_signer_and_block_recheck_passed"], 14)
        self.assertEqual(out["full_receipts_parsed"], 5)
        self.assertEqual(out["original_receipt_status_unreadable"], 3)
        self.assertEqual(out["realized_fully_attributable_cross_major_profits"], "UNRESOLVED")
        self.assertEqual(out["public_observer_executable_U"], "UNRESOLVED")
        self.assertEqual(out["production"], "NO_GO")

    def test_2025_wrongly_called_2026_refused(self):
        self.reject(lambda d: d["pre"]["cases"][4].update(p2_index=42))

    def test_cannot_reselect_after_source_frozen(self):
        self.reject(lambda d: d["manifest"]["cases"][1].update(p2_index=30))

    def test_native_scope_positive_cannot_be_regraded_posthoc(self):
        self.reject(lambda d: d["pre"]["cases"][0].update(source_native_scope_sign="POSITIVE_NATIVE_SCOPE"))

    def test_original_ca_cannot_be_replaced(self):
        self.reject(lambda d: d["manifest"]["cases"][0].update(ca="0x" + "b" * 40))

    def test_missing_original_tx_hash_detected(self):
        self.reject(lambda d: d["manifest"]["cases"][2]["original_transactions"].pop())

    def test_double_count_original_tx_rejected(self):
        self.reject(lambda d: d["manifest"]["cases"][4]["original_transactions"][0].update(
            hash=d["manifest"]["cases"][3]["original_transactions"][0]["hash"]))

    def test_original_signer_tampered_rejected(self):
        self.reject(lambda d: d["B"]["cases"][0].update(tx_from="0x" + "a" * 40))

    def test_original_block_tampered_rejected(self):
        self.reject(lambda d: d["C"]["cases"][0].update(tx_block=0))

    def test_false_promotion_truncated_receipt_detected(self):
        self.reject(lambda d: d["B"]["cases"][0].update(receipt_full_JSON=True))

    def test_missing_status_cannot_be_claimed_success(self):
        self.reject(lambda d: d["A"]["cases"][5].update(receipt_status="0x1"))

    def test_receipt_failure_cannot_be_censored(self):
        self.reject(lambda d: d["B"]["cases"][1].update(receipt_status="0x0"))

    def test_incomplete_rpc_group_cannot_be_silently_dropped(self):
        self.reject(lambda d: d["A"]["cases"].pop())

    def test_missing_original_gas_on_full_receipt_rejected(self):
        self.reject(lambda d: d["A"]["cases"][0].update(gas_used=None))


if __name__ == "__main__":
    unittest.main()
