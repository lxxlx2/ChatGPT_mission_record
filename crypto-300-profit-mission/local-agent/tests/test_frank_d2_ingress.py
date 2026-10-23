"""Offline D2 product-ingress contract regression tests. Synthetic data only.

NO original wallet balances, Solana RPC, production SQLite or live services.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

from mission_agent.mission_control.wallet_d2_ingress import (
    PAGE_SIZE, SOURCE_NAME, D2IngressError, _digest,
    build_d2_document_from_verified_pr60_replay,
    query_d2, read_d2_source, validate_d2_document,
)
from test_frank_d2_owner_at_slot import (
    source, MINT_A, MINT_B, MINT_C, MINT_ABSENT, WATCH,
)


class D2IngressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="frank-d2-ingress-")
        self.root = Path(self.tmp.name).resolve()
        self.root.chmod(0o700)
        self.doc = build_d2_document_from_verified_pr60_replay(source())

    def tearDown(self):
        self.tmp.cleanup()

    def _import_private(self, doc=None):
        file = self.root / SOURCE_NAME
        file.write_text(json.dumps(doc if doc is not None else self.doc),
                        encoding="utf-8")
        file.chmod(0o600)
        return file

    def test_real_synthetic_pr60_replay_source_all_mints_not_preview(self):
        doc=self.doc
        self.assertEqual(doc["account_count"], 4)
        self.assertEqual(doc["mint_count"], 3)
        self.assertEqual(doc["nonzero_mint_count"], 2)
        self.assertEqual(len(doc["mints"]), 3)
        self.assertFalse(doc["same_slot_atomic"])
        self.assertFalse(doc["current_chain_balance_verified"])
        self.assertFalse(doc["usd_value_verified"])
        self.assertFalse(doc["pnl_verified"])
        by_mint={x["mint"]:x for x in doc["mints"]}
        self.assertEqual(by_mint[MINT_A]["raw_amount"], "12000000")
        self.assertEqual(by_mint[MINT_A]["account_count"],2)
        self.assertEqual(by_mint[MINT_B]["raw_amount"], "0")
        self.assertNotIn(MINT_ABSENT,by_mint)
        self.assertNotIn("token_accounts",str(doc))
        self.assertEqual(doc["document_sha256"],_digest(doc))

    def test_source_is_not_automatically_imported(self):
        doc,fail=read_d2_source(self.root)
        self.assertIsNone(doc)
        self.assertEqual(fail["status"],"SOURCE_NOT_IMPORTED")
        self.assertEqual(fail["rows"],[])
        answer=query_d2(self.root,mint=MINT_A)
        self.assertEqual(answer["status"],"SOURCE_NOT_IMPORTED")
        self.assertFalse(answer["current_chain_balance_verified"])

    def test_imported_but_date_still_never_current(self):
        self._import_private()
        output=query_d2(self.root,page=0)
        self.assertEqual(output["status"],
                         "BALANCE_AT_OBSERVED_FINALIZED_SLOTS_NOT_LIVE")
        self.assertFalse(output["current_chain_balance_verified"])
        self.assertFalse(output["usd_value_verified"])
        self.assertFalse(output["same_slot_atomic"])
        self.assertEqual(len(output["program_coverage"]),2)
        self.assertEqual([x["slot"] for x in output["program_coverage"]],
                         [460482174,460482176])
        self.assertEqual(len(output["rows"]),3)
        self.assertEqual(output["total_pages"],1)
        self.assertGreater(output["age_seconds_at_response"],0)

    def test_exact_mint_valid_zero_and_absent_are_different(self):
        self._import_private()
        a=query_d2(self.root,mint=MINT_A)
        z=query_d2(self.root,mint=MINT_B)
        absent=query_d2(self.root,mint=MINT_ABSENT)
        self.assertEqual(a["lookup_state"],"NONZERO_AT_SLOT")
        self.assertEqual(a["rows"][0]["raw_amount"],"12000000")
        self.assertEqual(z["lookup_state"],"ZERO_AT_SLOT")
        self.assertEqual(z["rows"][0]["raw_amount"],"0")
        self.assertEqual(absent["lookup_state"],
                         "NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS")
        self.assertEqual(absent["rows"],[])
        self.assertEqual(absent["result_count"],0)

    def test_bounded_pagination_no_unbounded_dump(self):
        # Generate 210 synthetic valid Mint identities, no TokenAccount data.
        doc=deepcopy(self.doc)
        from test_frank_d2_owner_at_slot import pubkey
        extras=[]
        for i in range(210):
            mint=pubkey(30+i)
            extras.append({
                "mint":mint, "raw_amount":"0","decimals":6,
                "account_count":1, "program_ids":[doc["program_coverage"][0]["program_id"]],
                "slot_min":460482174, "slot_max":460482174,
            })
        doc["mints"].extend(extras)
        doc["mint_count"]=len(doc["mints"])
        doc["account_count"]+=len(extras)
        doc["program_coverage"][0]["account_count"]+=len(extras)
        doc["document_sha256"]=_digest(doc)
        self._import_private(doc)
        for page,expected in ((0,100),(1,100),(2,13),(3,0)):
            result=query_d2(self.root,page=page)
            self.assertEqual(result["result_count"],expected)
            self.assertLessEqual(len(result["rows"]),PAGE_SIZE)
            self.assertEqual(result["total_pages"],3)
        self.assertEqual(query_d2(self.root,mint=MINT_C)["result_count"],1)

    def test_invalid_explicit_params_fail_without_reading_source(self):
        for kwargs in ({"page":-1},{"page":1000},{"page":True},
                       {"mint":"NOT_A_MINT"},{"mint":""}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(D2IngressError):
                    query_d2(self.root,**kwargs)

    def test_tampered_bytes_do_not_become_zero(self):
        doc=deepcopy(self.doc)
        doc["mints"][0]["raw_amount"]="0"
        self._import_private(doc)
        got,bad=read_d2_source(self.root)
        self.assertIsNone(got)
        self.assertEqual(bad["status"],"SOURCE_REJECTED")
        self.assertEqual(bad["rows"],[])

    def test_reforged_checksum_still_must_reconcile_count(self):
        doc=deepcopy(self.doc)
        doc["mints"][0]["raw_amount"]="0"
        doc["document_sha256"]=_digest(doc)
        # Changing raw + self-hash cannot prove original PR60 provenance, but
        # the validator must still detect mismatched aggregate nonzero count.
        with self.assertRaisesRegex(D2IngressError,"D2_MINT_ACCOUNT_AGGREGATES_INVALID"):
            validate_d2_document(doc)

    def test_noncanonical_zero_string_fails_closed_even_with_new_digest(self):
        doc=deepcopy(self.doc)
        zero=next(r for r in doc["mints"] if r["raw_amount"] == "0")
        zero["raw_amount"]="00"
        doc["document_sha256"]=_digest(doc)
        with self.assertRaisesRegex(D2IngressError,"D2_MINT_QUANTITY_INVALID"):
            validate_d2_document(doc)

    def test_duplicate_mint_with_recalculated_checksum_rejected(self):
        doc=deepcopy(self.doc)
        doc["mints"].append(deepcopy(doc["mints"][0]))
        doc["mint_count"]+=1
        doc["account_count"]+=doc["mints"][0]["account_count"]
        doc["program_coverage"][0]["account_count"]+=doc["mints"][0]["account_count"]
        doc["document_sha256"]=_digest(doc)
        with self.assertRaisesRegex(D2IngressError,"D2_MINT_IDENTITY_DUPLICATE_OR_INVALID"):
            validate_d2_document(doc)

    def test_partial_or_false_live_source_rejected(self):
        for field,value in (("same_slot_atomic",True),
                            ("current_chain_balance_verified",True),
                            ("source_kind","MINT_FILTERED_LEGACY"),
                            ("wallet","INVALID_OWNER")):
            doc=deepcopy(self.doc)
            doc[field]=value
            doc["document_sha256"]=_digest(doc)
            with self.subTest(field=field),self.assertRaises(D2IngressError):
                validate_d2_document(doc)

    def test_private_source_file_permissions_and_symlinks_required(self):
        file=self._import_private()
        file.chmod(0o644)
        doc,bad=read_d2_source(self.root)
        self.assertIsNone(doc)
        self.assertEqual(bad["reason"],"D2_SOURCE_TYPE_OR_PERMISSIONS_INVALID")
        file.unlink()
        real=self.root/"private-other.json"
        real.write_text(json.dumps(self.doc))
        real.chmod(0o600)
        file.symlink_to(real)
        doc,bad=read_d2_source(self.root)
        self.assertIsNone(doc)
        self.assertEqual(bad["reason"],"D2_SOURCE_TYPE_OR_PERMISSIONS_INVALID")

    def test_bad_private_parent_and_oversized_source_rejected(self):
        self._import_private()
        self.root.chmod(0o755)
        _,bad=read_d2_source(self.root)
        self.assertEqual(bad["reason"],"D2_PARENT_NOT_PRIVATE")
        self.root.chmod(0o700)
        file=self.root/SOURCE_NAME
        file.write_bytes(b"x"*4_000_001)
        file.chmod(0o600)
        _,bad=read_d2_source(self.root)
        self.assertEqual(bad["reason"],"D2_SIZE_INVALID")

    def test_utc_bangkok_source_time_not_automatic_refresh(self):
        doc=deepcopy(self.doc)
        doc["observed_at_utc"]=(datetime.now(timezone.utc)+
                                timedelta(days=2)).isoformat()
        doc["document_sha256"]=_digest(doc)
        with self.assertRaisesRegex(D2IngressError,"D2_FUTURE_OBSERVATION"):
            validate_d2_document(doc)

    def test_source_document_never_includes_raw_token_account_keys(self):
        raw=json.dumps(self.doc,sort_keys=True)
        for row in source()["program_coverage"]:
            for account in row["accounts"]:
                self.assertNotIn(account["token_account"],raw)


if __name__ == "__main__":
    unittest.main()
