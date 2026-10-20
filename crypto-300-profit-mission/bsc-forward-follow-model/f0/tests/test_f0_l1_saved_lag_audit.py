"""Offline-only raw archive diagnostics: 62 local files, no network."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from f0_l1_saved_lag_audit import replay_saved
from f0_l1_saved_lag_audit import sha

MANIFEST=(ROOT/"F0_COHORT_PRESELECTION.json").read_bytes()
REGISTRY=(ROOT/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes()
PRIMARY=next(x["wallet"] for x in json.loads(MANIFEST)["preliminary_wallets"]
             if x["role"]=="PRIMARY")
ROUTER=json.loads(REGISTRY)["routers"][0]["address"]


def fixture(root):
    raw=root/"raw_responses"
    raw.mkdir()
    zero=datetime(2026,10,20,8,0,tzinfo=timezone.utc)
    fmt=lambda x:x.isoformat(timespec="milliseconds").replace("+00:00","Z")
    rows=[]
    for i in range(1,63):
        if i==1:
            method, params, result="eth_chainId", [],"0x38"
        elif i==2:
            method, params, result="eth_blockNumber", [],"0x63"
        else:
            h=99+i-2
            hash_hex="0x"+format(h,"064x")
            parent="0x"+format(h-1,"064x")
            txs=[]
            if i==3:
                for index,(frm,to) in enumerate([
                    (PRIMARY,ROUTER),
                    ("0x"+"a"*40,ROUTER)]):
                    txs.append({"hash":"0x"+format(10000+index,"064x"),
                                "from":frm,"to":to,"value":"0x0",
                                "input":"0x12345678","blockNumber":hex(h),
                                "blockHash":hash_hex})
            result={"number":hex(h),"hash":hash_hex,"parentHash":parent,
                    "timestamp":hex(1_760_000_000+(i-3)), "transactions":txs}
            method,params="eth_getBlockByNumber",[hex(h),True]
        rpc={"jsonrpc":"2.0","id":i,"result":result}
        body=json.dumps(rpc).encode()
        (raw/f"{i:03d}.response.json").write_bytes(body)
        at=zero+timedelta(milliseconds=1200*i)
        rows.append({"index":i,"method":method,"params":params,
                     "state":"RPC_RESPONSE","requested_utc":fmt(at-timedelta(milliseconds=500)),
                     "completed_utc":fmt(at),"requested_monotonic_ns":i*1_200_000_000,
                     "completed_monotonic_ns":i*1_200_000_000+500_000_000,
                     "response_sha256":sha(body),
                     "local_raw_response_file":f"{i:03d}.response.json"})
    journal={"schema":"bsc-f0-l1-short-http-single-use-v1",
             "attempted_calls":62,"attempts":rows}
    return journal, raw


def replay(journal,raw):
    return replay_saved(json.dumps(journal).encode(),raw,MANIFEST,REGISTRY)


class LagArchiveOfflineTests(unittest.TestCase):
    def test_sixty_contiguous_saved_blocks_and_sixtytwo_raw_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            j,raw=fixture(root)
            out=replay(j,raw)
            self.assertEqual(out["verified_raw_responses"],62)
            self.assertEqual((out["start_height"],out["end_height"]),(100,159))
            self.assertEqual(out["complete_requested_interval_blocks"],60)
            self.assertEqual(out["consecutive_height_count"],60)
            self.assertEqual(out["internal_parent_links_verified"],59)
            self.assertEqual(out["internal_parent_links_possible"],59)
            self.assertFalse(out["first_saved_block_parent_anchored_to_observed_head"])
            self.assertFalse(out["observed_head_hash_available"])
            self.assertEqual(out["parentage_verification_scope"],
                             "59_INTERNAL_LINKS_ONLY_FIRST_PARENT_UNANCHORED")
            self.assertEqual(out["total_full_block_transactions"],2)
            self.assertEqual(out["watch_signer_candidate_transactions"],1)
            self.assertEqual(out["router_address_candidate_transactions"],1)
            self.assertEqual(out["router_selectors_address_match_only"],{"0x12345678":1})
            self.assertGreater(out["local_span_minus_header_span_s"],0)
            self.assertEqual(out["network_requests_by_this_tool"],0)
            self.assertFalse(out["control_eligible"])

    def test_raw_response_mutation_detected_without_rpc(self):
        with tempfile.TemporaryDirectory() as d:
            j,raw=fixture(Path(d))
            path=raw/"018.response.json"
            path.write_bytes(path.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"RAW_RESPONSE_SHA256_MISMATCH"):
                replay(j,raw)

    def test_first_saved_block_parent_remains_unanchored_even_with_62_matching_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            j,raw=fixture(Path(d))
            path=raw/"003.response.json"
            rpc=json.loads(path.read_bytes())
            rpc["result"]["parentHash"]="0x"+"f"*64
            body=json.dumps(rpc).encode()
            path.write_bytes(body)
            j["attempts"][2]["response_sha256"]=sha(body)
            # The initial head was observed ONLY via eth_blockNumber;
            # there is no head block hash in the archive for this comparison.
            out=replay(j,raw)
            self.assertEqual(out["internal_parent_links_verified"],59)
            self.assertFalse(out["first_saved_block_parent_anchored_to_observed_head"])
            self.assertEqual(out["consecutive_height_count"],60)

    def test_header_parent_break_fails_even_with_updated_sha(self):
        with tempfile.TemporaryDirectory() as d:
            j,raw=fixture(Path(d))
            path=raw/"020.response.json"
            rpc=json.loads(path.read_bytes())
            rpc["result"]["parentHash"]="0x"+"f"*64
            body=json.dumps(rpc).encode()
            path.write_bytes(body)
            j["attempts"][19]["response_sha256"]=sha(body)
            with self.assertRaisesRegex(ValueError,"PARENT_HASH_NOT_CONTIGUOUS"):
                replay(j,raw)

    def test_journal_id_sequence_broken_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            j,raw=fixture(Path(d))
            j["attempts"][0]["index"]=2
            with self.assertRaisesRegex(ValueError,"JOURNAL_SEQUENCE_OR_OUTCOME_INVALID"):
                replay(j,raw)

    def test_timestamp_missing_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            j,raw=fixture(Path(d))
            path=raw/"024.response.json"
            rpc=json.loads(path.read_bytes())
            rpc["result"].pop("timestamp")
            body=json.dumps(rpc).encode()
            path.write_bytes(body)
            j["attempts"][23]["response_sha256"]=sha(body)
            with self.assertRaisesRegex(ValueError,"BLOCK_TIMESTAMP_MISSING"):
                replay(j,raw)

if __name__=="__main__":
    unittest.main()
