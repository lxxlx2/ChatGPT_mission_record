"""Exact-slot acceptance checks for saved ranked rows, no transport."""
import json
import unittest

from mission_agent.meme.historical_holder_compare import compare_ranked_holder_capture
from mission_agent.meme.holder_ranks import _b58, TOKEN_2022_PROGRAM


def address(n):
    return _b58(bytes([n])*32)


MINT, OWNER, OWNER2, A, B, C = [address(i) for i in range(121, 127)]


class HistoricalHolderCompareTest(unittest.TestCase):
    def fixtures(self):
        ranking = {"status": "COMPLETE_SNAPSHOT", "mint": MINT, "program_id": TOKEN_2022_PROGRAM,
                   "decimals": 6, "snapshot_slot": 100, "response_sha256": "a"*64, "account_count": 3,
                   "accounts": [{"token_account": account, "owner": owner, "raw": amount, "decimals": 6}
                                for account, owner, amount in ((A, OWNER, "900"), (B, OWNER, "500"), (C, OWNER2, "1"))]}
        response = {"jsonrpc": "2.0", "id": 1, "result": {"mint": MINT, "slot": 100,
                    "sortBy": "balance_desc", "holders": [
                        {"holder": A, "owner": OWNER, "balanceRaw": "900", "balanceUi": "ignored"},
                        {"holder": B, "owner": OWNER, "balanceRaw": "500"},
                    ]}}
        return ranking, response

    def compare(self, ranking, response, *, limit=2):
        return compare_ranked_holder_capture(MINT, ranking, json.dumps(response).encode(), requested_limit=limit)

    def test_two_accounts_one_owner_capped_only(self):
        primary, reference = self.fixtures()
        result = self.compare(primary, reference)
        self.assertEqual(result["status"], "SAME_SLOT_RANKED_ROWS_MATCH")
        self.assertEqual((result["matched_accounts"], result["owners_within_reference"]), (2, 1))
        self.assertTrue(result["reference_at_requested_limit"])
        self.assertFalse(result["whole_mint_coverage_verified"])
        self.assertFalse(result["same_chain_state_verified"])
        no_cap = self.compare(primary, reference, limit=10000)
        self.assertFalse(no_cap["whole_mint_coverage_verified"])

    def test_same_minimum_cannot_substitute_for_exact_slot(self):
        primary, reference = self.fixtures()
        reference["result"]["slot"] += 1
        result = self.compare(primary, reference)
        self.assertEqual(result["status"], "DIFFERENT_REPORTED_SLOTS")
        self.assertNotIn("matched_accounts", result)

    def test_changed_owner_and_unseen_account(self):
        primary, reference = self.fixtures()
        reference["result"]["holders"][0]["owner"] = OWNER2
        reference["result"]["holders"][1]["holder"] = address(130)
        result = self.compare(primary, reference)
        self.assertEqual(result["status"], "SAME_SLOT_RANKED_DIFFERENCE")
        self.assertEqual((result["changed_owner_or_raw"], result["reference_only_accounts"]), (1, 1))
        self.assertFalse(result["whole_mint_coverage_verified"])

    def test_duplicates_malformed_amount_and_wrong_mint_fail_closed(self):
        for field, value in (("holder", A), ("balanceRaw", "0500"), ("balanceRaw", str(2**64)),
                             ("balanceRaw", 500), ("balanceRaw", "901")):
            with self.subTest(field=field, value=value):
                primary, reference = self.fixtures()
                reference["result"]["holders"][1][field] = value
                self.assertEqual(self.compare(primary, reference)["reason"], "REFERENCE_ROWS_INVALID")
        primary, reference = self.fixtures()
        reference["result"]["mint"] = OWNER2
        self.assertEqual(self.compare(primary, reference)["reason"], "REFERENCE_IDENTITY_UNVERIFIED")
