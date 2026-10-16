#!/usr/bin/env python3
"""First 32-source-shard research: identity and fail-closed regression checks."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import monster_v4_shared_445_first32_real_comparison as first
import monster_v4_shared_445_official_source_shards as shards
from test_monster_v4_shared_spot_d0_d1_original_core import fixture


class First32TwoShardRegressions(unittest.TestCase):
    def test_01_not_winner_selected_and_cohort_disjoint(self):
        roster=first.strict_roster()
        self.assertEqual(len(roster),32)
        self.assertEqual(roster,shards.roster()[:32])
        self.assertEqual(roster[:16],shards.members(0))
        self.assertEqual(roster[16:],shards.members(1))
        self.assertEqual(len(set(roster)),32)
        self.assertEqual(first.shared.original_758_coverage(
            shards.DAY,roster)["source_complete_but_not_replayed"],413)

    def test_02_missing_source_shard_blocks_even_before_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,
                                         "TWO_VERIFIED_SOURCE_SHARDS_REQUIRED"):
                first.analyze_two(tmp)

    def test_03_fake_source_attestation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in (0,1):
                root=Path(tmp)
                (root/f"monster_feb445_shard{i:02d}.zip").write_bytes(b"not-verified")
                (root/f"monster_feb445_shard{i:02d}.proof.json").write_text(
                    json.dumps({"shard":i,
                      "source_origin_verified_at_collection":False,
                      "symbols":list(shards.members(i))}))
            with self.assertRaisesRegex(ValueError,
                                         "SOURCE_PROVENANCE_REJECTED"):
                first.analyze_two(tmp)

    def test_04_shard_source_duplicate_wrong_identity_must_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in (0,1):
                root=Path(tmp)
                (root/f"monster_feb445_shard{i:02d}.zip").write_bytes(b"fake")
                (root/f"monster_feb445_shard{i:02d}.proof.json").write_text(
                    json.dumps({"shard":i,
                      "source_origin_verified_at_collection":True,
                      "sha256_zip":"0"*64,
                      "trigger_commit_sha":"SYNTHETIC_UNVERIFIED",
                      "symbols":list(shards.members(i))}))
            def fake_shard(_path,proof,expected_shard):
                return iter([(shards.members(0)[0],[],[],{})])
            with patch.object(first.shards,"read_archive",side_effect=fake_shard):
                with self.assertRaisesRegex(ValueError,
                             "INVALID_OR_DUPLICATED_SOURCE_MEMBER"):
                    first.analyze_two(tmp)

    def test_05_no_445_claim_from_32_member_roster(self):
        self.assertEqual(len(first.strict_roster()),32)
        self.assertEqual(first.shards.POPULATION,445)
        self.assertNotEqual(len(first.strict_roster()),first.shards.POPULATION)
        self.assertEqual(first.SCHEMA,
             "MONSTER_FEB2026_FROZEN_FIRST32_TWO_SOURCE_SHARD_ONE_GLOBAL_SQLITE_V1")


if __name__=="__main__":
    unittest.main()
