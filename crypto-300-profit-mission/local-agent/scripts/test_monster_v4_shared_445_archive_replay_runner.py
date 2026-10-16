#!/usr/bin/env python3
"""Offline identity and anti-overclaim tests for first all445 artifact replay."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import monster_v4_shared_445_archive_replay_runner as r


class Archived445ReplayTests(unittest.TestCase):
    def test_exact_18_artifact_28_shard_445_denominator(self):
        self.assertTrue(r.validate_ledger())
        self.assertEqual(len(r.FROZEN_ARTIFACTS),18)
        self.assertEqual(tuple(i for _,pair in r.FROZEN_ARTIFACTS for i in pair),
                         tuple(range(28)))

    def test_missing_28_archive_source_does_not_contact_gh(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaisesRegex(ValueError,"SOURCE_DIR_ALREADY_EXISTS"):
                r.collect(p,p/"a.json",api=lambda path: self.fail("must not fetch"))

    def test_summarize_rejects_fake_445_proof_and_partial_32_replay(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            audit=d/"audit.json"
            report=d/"replay.json"
            audit.write_text(json.dumps({"source_28_shards_verified":True,
                "source_artifacts":[{"shard":i,"zip_sha256":"0"*64} for i in range(28)]}))
            report.write_text(json.dumps({"actually_complete_symbols":32,
                "execution_counts":{"polls":3360},
                "true_full_758_replay":False,"G6":"NO_GO"}))
            with self.assertRaisesRegex(RuntimeError,"ACTUAL_SHARED_ENGINE_INCOMPLETE"):
                r.summarize(audit,report,d/"out.json")

    def test_collect_rejects_missing_or_expired_api_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            with patch.dict("os.environ",{"GH_TOKEN":"test"}):
                with self.assertRaisesRegex(RuntimeError,"METADATA_OR_EXPIRY"):
                    r.collect(p/"source",p/"audit.json",
                        api=lambda *_: {"id":r.FROZEN_ARTIFACTS[0][0],
                                        "expired":True,
                                        "name":"monster-fake",
                                        "size_in_bytes":1},
                        downloader=lambda *args: self.fail("must not download"))

    def test_summarize_requires_one_actual_sqlite_and_no_758_claim(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            audit=p/"audit.json"; report=p/"replay.json"
            audit.write_text(json.dumps({"source_28_shards_verified":True,
                "source_artifacts":[{"shard":i,"zip_sha256":"0"*64} for i in range(28)]}))
            base={"source_complete_445_members_observed":445,
                "actually_complete_symbols":445,
                "all_28_source_archive_shas":[{"shard":i,"zip_sha256":"0"*64}
                                               for i in range(28)],
                "true_full_445_shared_source_complete_subset_replayed":True,
                "true_full_758_replay":False,
                "one_shared_sqlite_for_all_symbols":False,
                "not_independent_OOS":True,
                "not_real_PIT_listing":True,
                "execution_counts":{"polls":3360},"G6":"NO_GO"}
            report.write_text(json.dumps(base))
            with self.assertRaisesRegex(RuntimeError,"ACTUAL_SHARED_ENGINE_INCOMPLETE"):
                r.summarize(audit,report,p/"out.json")
            base["one_shared_sqlite_for_all_symbols"]=True
            base["true_full_758_replay"]=True
            report.write_text(json.dumps(base))
            with self.assertRaisesRegex(RuntimeError,"ACTUAL_SHARED_ENGINE_INCOMPLETE"):
                r.summarize(audit,report,p/"out.json")


if __name__=="__main__":
    unittest.main()
