"""Offline tests for bounded S3 listing; no real network access."""
import importlib.util
import io
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[1] / "mission_agent" / "early" / "aws_bnb_public_source_probe.py"
spec = importlib.util.spec_from_file_location("aws_bnb_probe", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.close()


class SourceProbeTests(unittest.TestCase):
    def test_xml_parser_and_limits(self):
        def fake(url, timeout):
            self.assertEqual(timeout, 15)
            self.assertIn("max-keys=10", url)
            self.assertIn("prefix=v1.1%2Fbnb%2F", url)
            return FakeResponse(b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Prefix>v1.1/bnb/blocks/</Prefix><IsTruncated>true</IsTruncated><CommonPrefixes><Prefix>v1.1/bnb/blocks/date=2025-07-01/</Prefix></CommonPrefixes><Contents><Key>v1.1/bnb/blocks/a.parquet</Key><Size>123</Size></Contents></ListBucketResult>')
        r=m.read_listing("v1.1/bnb/blocks/", delimiter="/", opener=fake)
        self.assertEqual(r["objects"], [{"key":"v1.1/bnb/blocks/a.parquet","size_bytes":123}])
        self.assertTrue(r["truncated"])

    def test_reject_prefix_spoof(self):
        def fake(*_args, **_kwargs):
            return FakeResponse(b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Prefix>v1.1/bnb/transactions/</Prefix></ListBucketResult>')
        with self.assertRaisesRegex(ValueError, "S3_PREFIX_MISMATCH"):
            m.read_listing("v1.1/bnb/blocks/", opener=fake)

    def test_empty_or_failed_listing_cannot_prove_absence(self):
        def reader(prefix, delimiter=None):
            if "transactions" in prefix:
                raise OSError("offline")
            return {"objects":[], "child_prefixes":[], "truncated":False}
        r=m.probe(reader=reader)
        self.assertFalse(r["results"]["blocks"]["date_objects_observed"])
        self.assertEqual(len(r["results"]["transactions"]["errors"]), 5)
        self.assertFalse(r["pit_verified"])
        self.assertFalse(r["sellability_verified"])

    def test_positive_date_still_not_prove_logs(self):
        def reader(prefix, delimiter=None):
            rows=[] if "date=2025-07-01/" not in prefix else [{"key":prefix+"a.parquet","size_bytes":42}]
            return {"objects":rows,"child_prefixes":[],"truncated":False}
        r=m.probe(reader=reader)
        self.assertTrue(r["results"]["blocks"]["date_objects_observed"])
        self.assertTrue(r["results"]["transactions"]["date_objects_observed"])
        self.assertFalse(r["log_receipt_columns_verified"])
        self.assertFalse(r["pit_verified"])

if __name__ == "__main__":
    unittest.main()
