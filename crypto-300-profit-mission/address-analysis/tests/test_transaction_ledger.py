import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from transaction_ledger import replay
import json


class FIFOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = json.loads((ROOT / 'fixtures' / 'batch001-row002-sauce-executions.json').read_text())
        cls.manifest = {
            'source_blob_sha':'954f3aba66be21911dd627fa40dd3dd0a9fd1d26',
            'total':449,
            'items':[{'index':i, 'batch':(i-1)//20+1, 'address':cls.sample['wallet'] if i == 2 else '0x'+format(i,'040x')}
                     for i in range(1,450)]}

    def run_case(self, patch=None):
        d = copy.deepcopy(self.sample)
        if patch:
            patch(d)
        return replay(d, self.manifest)

    def test_saved_sauce_row002_exact_closed_native_cashflow(self):
        r = self.run_case()
        self.assertEqual(r['status'], 'CLAIM_REPLAY_ONLY')
        self.assertEqual(r['window_realized_quote_raw'], '156828105278687674')
        self.assertEqual(r['all_period_realized_quote_raw'], '156828105278687674')
        self.assertEqual(r['unspent_base_raw'], '0')
        self.assertEqual(r['gain_exits'], 1)
        self.assertEqual(r['wallet_30d_pnl'], 'UNRESOLVED')
        self.assertEqual(len(r['matched_sells'][0]['fifo_lots']), 2)

    def test_historical_buy_sale_in_window_only(self):
        r = self.run_case()
        self.assertEqual(r['matched_sells'][0]['within_fixed_30d_window'], True)
        self.assertTrue(self.sample['executions'][0]['timestamp_utc'] < self.sample['window_start_utc'])

    def test_negative_outcome_accepted_no_cherrypicking(self):
        def negative(d):
            d['executions'][2]['quote_net_raw'] = '10000000000000000'
        r = self.run_case(negative)
        self.assertEqual(r['status'], 'CLAIM_REPLAY_ONLY')
        self.assertEqual(r['loss_exits'], 1)
        self.assertEqual(r['window_realized_quote_raw'], '-44313975000000000')

    def test_fifo_partial_two_lots_and_loss(self):
        def simple(d):
            es = d['executions']
            es[0]['base_qty_raw'], es[0]['quote_net_raw'], es[0]['balance_after_raw'] = '10', '100', '10'
            es[1]['base_qty_raw'], es[1]['quote_net_raw'], es[1]['balance_after_raw'] = '10', '300', '20'
            es[2]['base_qty_raw'], es[2]['quote_net_raw'], es[2]['balance_after_raw'] = '15', '330', '5'
            extra = copy.deepcopy(es[2]); extra['tx_hash'] = '0x'+'a'*64
            extra['block'] += 10; extra['timestamp_utc']='2026-10-16T13:00:00Z'
            extra['base_qty_raw']='5'; extra['quote_net_raw']='20'; extra['balance_after_raw']='0'
            es.append(extra)
        r = self.run_case(simple)
        self.assertEqual(r['status'], 'CLAIM_REPLAY_ONLY')
        self.assertEqual([e['realized_quote_raw'] for e in r['matched_sells']], ['80', '-130'])
        self.assertEqual(r['all_period_realized_quote_raw'], '-50')
        self.assertEqual(r['gain_exits'], 1)
        self.assertEqual(r['loss_exits'], 1)

    def test_open_inventory_cost_not_realized(self):
        def open_lot(d):
            d['executions'][2]['base_qty_raw'] = '31708285150519965576422'
            d['ending_base_raw'] = '31991630323068868295919'
            d['executions'][2]['balance_after_raw'] = '31991630323068868295919'
        r = self.run_case(open_lot)
        self.assertEqual(r['status'], 'CLAIM_REPLAY_ONLY')
        self.assertEqual(r['unspent_base_raw'], '31991630323068868295919')
        self.assertNotEqual(r['remaining_basis_quote_raw'], '0')
        self.assertEqual(r['wallet_lifetime_pnl'], 'UNRESOLVED')

    def test_over_sell_fails_closed(self):
        def oversell(d): d['executions'][2]['base_qty_raw'] = '9999999999999999999999999'
        r = self.run_case(oversell)
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')
        self.assertEqual(r['matched_sells'], [])

    def test_unsupported_approval_event_unresolved(self):
        r = self.run_case(lambda d: d['executions'][1].update(side='APPROVAL'))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_duplicate_hash_rejected(self):
        r = self.run_case(lambda d: d['executions'][1].update(tx_hash=d['executions'][0]['tx_hash']))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_unverified_fees_fail_closed(self):
        r = self.run_case(lambda d: d['executions'][2].update(fee_included_in_quote_net=False))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_unknown_intermediate_external_transfer_fails(self):
        r = self.run_case(lambda d: d.update(all_token_movements_accounted_for=False))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_tampered_full_source_order_fails(self):
        m = copy.deepcopy(self.manifest)
        m['items'][0], m['items'][1] = m['items'][1], m['items'][0]
        self.assertEqual(replay(copy.deepcopy(self.sample), m)['status'], 'PNL_UNRESOLVED')

    def test_unverified_opening_inventory_fail_closed(self):
        r = self.run_case(lambda d: d.update(opening_inventory='UNKNOWN'))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_bad_source_wallet_fail_closed(self):
        r = self.run_case(lambda d: d.update(wallet='0x'+'0'*40))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_intermediate_token_balance_mismatch_fails(self):
        r = self.run_case(lambda d: d['executions'][1].update(balance_after_raw='1'))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_quote_token_without_execution_gas_fx_fails(self):
        r = self.run_case(lambda d: d.update(quote_asset='0x'+'f'*40))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_quote_token_with_external_fx_assertion(self):
        def quote_fx(d):
            d['quote_asset'] = '0x'+'f'*40
            for e in d['executions']:
                e['gas_converted_quote_raw'] = '1'
                e['gas_fx_source_ref'] = 'synthetic-example-execution-price'
        r = self.run_case(quote_fx)
        self.assertEqual(r['status'], 'CLAIM_REPLAY_ONLY')
        self.assertEqual(r['wallet_30d_pnl'], 'UNRESOLVED')

    def test_wrong_final_token_balance_fail_closed(self):
        r = self.run_case(lambda d: d.update(ending_base_raw='1'))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_out_of_order_or_same_block_fails(self):
        r = self.run_case(lambda d: d['executions'][1].update(block=d['executions'][0]['block']))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_bad_quote_contract_network_mismatch(self):
        r = self.run_case(lambda d: d.update(quote_asset='NATIVE_ETH'))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')

    def test_no_proof_reference_rejected(self):
        r = self.run_case(lambda d: d['executions'][2].update(evidence_ref=''))
        self.assertEqual(r['status'], 'PNL_UNRESOLVED')


if __name__ == '__main__':
    unittest.main()
