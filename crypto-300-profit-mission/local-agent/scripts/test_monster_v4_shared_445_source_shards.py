#!/usr/bin/env python3
"""Frozen 445 single-DB offline source pipeline integrity, no external network."""
import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

import monster_v4_shared_445_official_source_shards as shards
import monster_v4_shared_445_one_db_from_shards as assemble
from test_monster_v4_shared_spot_d0_d1_original_core import fixture, fake_receipts


class SourceShardsAndMergeTests(unittest.TestCase):
    def test_01_exact_445_frozen_shard_coverage_nonoverlap(self):
        names=shards.roster()
        self.assertEqual(len(names),445)
        shards_all=[s for i in range(28) for s in shards.members(i)]
        self.assertEqual(tuple(shards_all),names)
        self.assertEqual(len(set(shards_all)),445)
        self.assertEqual([len(shards.members(i)) for i in range(28)],
                         [16]*27+[13])
        for bad in (-1,28,1.1,True,"1"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,"INVALID_FROZEN_SHARD"):
                    shards.members(bad)

    def test_02_one_shard_real_shape_synthetic_source_and_zip_sha_roundtrip(self):
        selected=shards.members(1)
        visited=[]
        def mock_reader(sym,day):
            visited.append(sym)
            return fixture(sym),fake_receipts(sym)
        with tempfile.TemporaryDirectory(prefix="monster445_frozen_shard_test_") as tmp:
            z=Path(tmp)/"original_source.zip"
            p=Path(tmp)/"source.proof.json"
            proof=shards.collect(1,z,p,fetch=mock_reader,max_workers=2)
            self.assertEqual(sorted(visited),list(selected))
            self.assertFalse(proof["source_origin_verified_at_collection"])
            self.assertEqual(proof["source_symbol_count"],16)
            self.assertEqual(len(proof["source_sha256_by_symbol"]),16)
            self.assertEqual(proof["original_denominator"],758)
            self.assertEqual(proof["historical_original_censored"],313)
            self.assertEqual(shards.sha(z.read_bytes()),proof["sha256_zip"])
            entries=list(shards.read_archive(z,proof=proof,expected_shard=1))
            self.assertEqual(tuple(x[0] for x in entries),selected)
            for name,bars,receipts,meta in entries:
                self.assertEqual(len(bars),12960)
                self.assertEqual(len(receipts),10)
                self.assertEqual(bars[0][0],shards.shared.utc_ms(shards.DAY)-
                                 1440*shards.shared.MIN)
                self.assertFalse(meta["source_origin_verified_at_collection"])
            with self.assertRaisesRegex(ValueError,"SOURCE_OUTPUT_ALREADY_EXISTS"):
                shards.collect(1,z,p,fetch=mock_reader,max_workers=2)
            with self.assertRaisesRegex(ValueError,"SHARD_ZIP_SHA_MISMATCH"):
                list(shards.read_archive(z,proof={**proof,"sha256_zip":"0"*64},
                                         expected_shard=1))
            with self.assertRaisesRegex(ValueError,"SHARD_SCHEMA_OR_ID_DRIFT"):
                list(shards.read_archive(z,proof=proof,expected_shard=2))
            with self.assertRaisesRegex(ValueError,"SHARD_PROOF_OR_OFFICIAL_ORIGIN"):
                # A synthetic source archive, even with valid bytes and SHA,
                # CANNOT be certified as official through proof metadata.
                with patch.object(assemble,"expected_file_pair",
                        side_effect=lambda _folder,_i:(z,p)):
                    assemble.verified_shard_paths(tmp)

    def test_03_missing_27_shards_blocks_before_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"28_ORIGINAL_SOURCE_SHARDS_MISSING"):
                assemble.verified_shard_paths(tmp)
            with self.assertRaisesRegex(ValueError,"28_ORIGINAL_SOURCE_SHARDS_MISSING"):
                assemble.run_all(tmp)

    def test_04_invalid_445_injected_population_rejected_before_sqlite(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_RUN_PARTIAL_MARKET"):
            assemble.run_all("not_used",read_inputs=lambda _:
              ({"BTCUSDT":([],[])},[{"shard":0}]))

    def test_05_malformed_raw_serialization_and_nan_rejected(self):
        r=fixture("BTCUSDT")
        raw=shards.encode_bars(r)
        rebuilt=shards.decode_bars(raw)
        self.assertEqual(r,rebuilt)
        corrupted=json.loads(raw)
        corrupted[0][2]="NaN"
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            shards.decode_bars(json.dumps(corrupted).encode())
        corrupted=json.loads(raw)
        corrupted[0]=corrupted[0][:-1]
        with self.assertRaisesRegex(ValueError,"BAD_ROW_SHAPE"):
            shards.decode_bars(json.dumps(corrupted).encode())

    def test_06_publisher_reader_concurrency_max_two(self):
        for value in (0,3,-1,1.1,True):
            with self.subTest(value=value):
                with tempfile.TemporaryDirectory() as td:
                    with self.assertRaisesRegex(ValueError,"LIMIT_TWO"):
                        shards.collect(1,Path(td)/"bad.zip",
                            Path(td)/"bad.json",fetch=lambda s,d:None,
                            max_workers=value)

    def test_07_source_manifest_requires_original_full_population(self):
        cohort=shards.roster()
        self.assertEqual(len(cohort),445)
        self.assertEqual(shards.members(0)[0],"0GUSDT")
        self.assertEqual(shards.members(1)[0],cohort[16])
        self.assertTrue(set(shards.members(1)).isdisjoint(shards.members(0)))
        self.assertFalse(Path("monster445_production.db").exists())


if __name__=="__main__":
    unittest.main()
