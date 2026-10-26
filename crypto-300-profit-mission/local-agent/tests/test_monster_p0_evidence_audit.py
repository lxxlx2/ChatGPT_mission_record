"""Pure offline tests of the archived-evidence joining gate."""
import copy
import importlib.util
import json
import tempfile
import pathlib
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1] / 'mission_agent' / 'early' / 'p0_evidence_audit.py'
spec = importlib.util.spec_from_file_location('p0_gate_tested', SRC)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def dossier():
    rank_data = []
    for rank in range(1, 31):
        rank_data.append({"rank": rank,
                          "token_ca": "0x%040x" % rank,
                          "pool": "0x%040x" % (1000 + rank),
                          "first_actual_public_available_at": "UNKNOWN",
                          "uniform_research_notional_sellability": "NOT_SCORABLE"})
    sells = []
    depth = []
    cases = []
    for rank in audit.FROZEN_SELL_RANKS:
        h = "0x%064x" % rank
        raw_min = "123" if rank == 1 else "0"
        sells.append({"rank": rank, "token_ca": rank_data[rank-1]["token_ca"],
                      "original_sell_transaction": h,
                      "method": "V2_ROUTER_SWAP_EXACT_TOKENS_FOR_ETH",
                      "minimum_output_raw": raw_min,
                      "min_output_positive": rank == 1,
                      "pool_depth_above_frozen_floor": rank not in (2, 6, 10, 22)})
        depth.append({"rank": rank, "token_ca": rank_data[rank-1]["token_ca"],
                      "exact_sell_tx_hash": h, "pre_swap_research_depth_pass": rank not in (2, 6, 10, 22),
                      "depleted_over_99_percent": rank in (2, 6, 9, 10, 19, 22, 27)})
        if rank in audit.FROZEN_ROUNDTRIP_RANKS:
            cases.append({"rank": rank, "token_ca": rank_data[rank-1]["token_ca"],
                          "historical_sell_tx": h,
                          "actual_same_token_recipient_exact_received_quantity_reversed": True,
                          "actual_buy_sell_receipt_status": "0x1_BOTH",
                          "observed_buy_quote_in_wei": "1000",
                          "observed_sell_pool_quote_out_wei": "900" if rank in (7, 12) else "1100",
                          "route_class": "EOA_CALLS_CUSTOM_SMART_CONTRACT_RECEIVING_TOKEN_AND_WBNB" if rank in (3, 13, 23) else "EOA_CALLS_PANCAKESWAP_V2_ROUTER"})
    return {audit.KEY_ROSTER: {"rows": rank_data},
            audit.KEY_SELL_ROUTE: {"rows": sells},
            audit.KEY_SELL_DEPTH: {"rows": depth},
            audit.KEY_ROUNDTRIP: {"rows": cases}}


class TestP0EvidenceReconciliation(unittest.TestCase):
    def test_happy_path_proves_no_p1(self):
        x = audit.reconcile(dossier())
        self.assertEqual(x['selected_sell_count'], 22)
        self.assertEqual(x['sell_depth_floor_count'], 18)
        self.assertEqual(x['roundtrip_count'], 7)
        self.assertEqual(x['positive_min_out_ranks'], [1])
        self.assertEqual(x['full_roundtrip_and_positive_min_out_ranks'], [])
        self.assertEqual(x['pool_quote_gross_negative_before_cost_ranks'], [7, 12])
        self.assertFalse(x['p1_gate_passed'])
        self.assertEqual(x['sellable_same_notional_18_of_30_gate'], 'NOT_SCORABLE')

    def test_rank_and_ca_mutation_fail_closed(self):
        x = dossier()
        x[audit.KEY_SELL_ROUTE]['rows'][0]['token_ca'] = '0x' + 'f' * 40
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'TOKEN_IDENTITY_MISMATCH'):
            audit.reconcile(x)

    def test_sell_hash_mismatch_fail_closed(self):
        x = dossier()
        x[audit.KEY_SELL_DEPTH]['rows'][0]['exact_sell_tx_hash'] = '0x' + 'f' * 64
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'SELL_TX_HASH_MISMATCH'):
            audit.reconcile(x)

    def test_depth_assertion_tamper_fail_closed(self):
        x = dossier()
        x[audit.KEY_SELL_DEPTH]['rows'][0]['pre_swap_research_depth_pass'] = False
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'SELL_PREDEPTH_DISAGREEMENT'):
            audit.reconcile(x)

    def test_router_min_out_assertion_tamper_fail_closed(self):
        x = dossier()
        x[audit.KEY_SELL_ROUTE]['rows'][1]['min_output_positive'] = True
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'MIN_OUT_ASSERTION_DISAGREEMENT'):
            audit.reconcile(x)

    def test_roundtrip_must_refer_to_known_real_sell(self):
        x = dossier()
        x[audit.KEY_ROUNDTRIP]['rows'][0]['rank'] = 15
        x[audit.KEY_ROUNDTRIP]['rows'][0]['token_ca'] = x[audit.KEY_ROSTER]['rows'][14]['token_ca']
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'FROZEN_SELECTED_CASES_CHANGED'):
            audit.reconcile(x)

    def test_future_clock_claim_not_promoted(self):
        x = dossier()
        x[audit.KEY_ROSTER]['rows'][0]['first_actual_public_available_at'] = '2025-07-01T02:00:00Z'
        result = audit.reconcile(x)
        self.assertIsNone(result['pit_verified_count'])
        self.assertFalse(result['p1_gate_passed'])

    def test_missing_archive_not_silently_zero(self):
        x = dossier()
        del x[audit.KEY_SELL_DEPTH]
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'MISSING_OR_INVALID_ROWS'):
            audit.reconcile(x)

    def test_uint_and_bool_refused(self):
        x = dossier()
        x[audit.KEY_ROUNDTRIP]['rows'][0]['observed_buy_quote_in_wei'] = True
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'INVALID_UINT_FIELD'):
            audit.reconcile(x)

    def test_frozen_selected_rank_mutation_fails_closed(self):
        x = dossier()
        x[audit.KEY_SELL_ROUTE]['rows'].pop()
        x[audit.KEY_SELL_DEPTH]['rows'].pop()
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'FROZEN_SELECTED_CASES_CHANGED'):
            audit.reconcile(x)

    def test_modified_json_rejected_by_git_blob_pin(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'evidence.json'
            path.write_text(json.dumps(dossier()))
            with self.assertRaisesRegex(audit.EvidenceAuditError, 'UNPINNED_EVIDENCE_BLOB'):
                audit.audit_file(path)

    def test_large_file_rejected_without_parse(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'evidence.json'
            path.write_bytes(b'x' * (audit.MAX_INPUT_BYTES + 1))
            with self.assertRaisesRegex(audit.EvidenceAuditError, 'INPUT_TOO_LARGE'):
                audit.audit_file(path)

    def test_duplicate_pool_identity_rejected(self):
        x = dossier()
        x[audit.KEY_ROSTER]['rows'][1]['pool'] = x[audit.KEY_ROSTER]['rows'][0]['pool']
        with self.assertRaisesRegex(audit.EvidenceAuditError, 'DUPLICATE_OR_MISSING_POOL'):
            audit.reconcile(x)

    def test_rerun_is_deterministic(self):
        x = dossier()
        self.assertEqual(audit.reconcile(x), audit.reconcile(copy.deepcopy(x)))


if __name__ == '__main__':
    unittest.main()
