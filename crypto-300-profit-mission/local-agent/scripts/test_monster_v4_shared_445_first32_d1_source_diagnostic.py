#!/usr/bin/env python3
"""D1 historical raw source failure category; never turn failure into LATE."""
import unittest

import monster_v4_shared_445_first32_d1_source_diagnostic as diagnostic


class DiagnosticSourceContractTests(unittest.TestCase):
    def setUp(self):
        self.bars=[[0,"2","3","1","2","100",299999,"400"] for _ in range(8)]

    def test_01_true_zero_quote_is_unsupported_not_assumed_forged(self):
        self.bars[4][7]="0"
        self.assertEqual(diagnostic.candle_problem(self.bars),
            "ZERO_OR_NEGATIVE_OFFICIAL_KLINE_QUOTE_UNSUPPORTED_BY_FROZEN_D1")

    def test_02_bad_high_is_a_different_true_content_fault(self):
        self.bars[3][2]="0"
        self.assertEqual(diagnostic.candle_problem(self.bars),
                         "INVALID_OHLC_ENVELOPE")

    def test_03_nonfinite_and_negative_real_volume(self):
        self.bars[0][7]="NaN"
        self.assertEqual(diagnostic.candle_problem(self.bars),
                         "NONFINITE_KLINE_FIELDS")
        self.bars[0][7]="400"
        self.bars[0][5]="-2"
        self.assertEqual(diagnostic.candle_problem(self.bars),
                         "NEGATIVE_REAL_VOLUME")

    def test_04_normal_quote_is_valid_not_forced_blocker(self):
        self.assertEqual(diagnostic.candle_problem(self.bars),
                         "UNKNOWN_PRODUCTION_EVALUATOR_OR_TIME_CONTRACT")


if __name__=="__main__":
    unittest.main()
