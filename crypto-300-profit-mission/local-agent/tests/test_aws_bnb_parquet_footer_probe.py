"""Offline tests for the AWS BNB Parquet footer probe. No network."""
import importlib.util
import io
import pathlib
import struct
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "mission_agent" / "early" / "aws_bnb_parquet_footer_probe.py"
spec = importlib.util.spec_from_file_location("aws_bnb_parquet_probe", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def varint(n):
    out = bytearray()
    while n >= 128:
        out.append(128 | (n & 127))
        n >>= 7
    out.append(n)
    return bytes(out)


def signed(n):
    return varint((n << 1) ^ (n >> 63))


def name(s):
    raw = s.encode()
    return varint(len(raw)) + raw


def sample():
    root = b"\x48" + name("schema") + b"\x15" + signed(1) + b"\x00"
    leaf = b"\x15" + signed(6) + b"\x38" + name("block_number") + b"\x00"
    group = b"\x00"
    footer = (b"\x15" + signed(1) + b"\x19\x2c" + root + leaf
              + b"\x16" + signed(10) + b"\x19\x1c" + group + b"\x00")
    return b"PAR1" + b"\x00" * 100 + footer + struct.pack("<I", len(footer)) + b"PAR1"


class Reply(io.BytesIO):
    def __init__(self, content, start, end, total, status=206, etag='"same"'):
        super().__init__(content)
        self.status = status
        self.headers = {"Content-Range": f"bytes {start}-{end}/{total}", "ETag": etag}


class FooterProbeTests(unittest.TestCase):
    def test_thrift_parquet_schema_and_count(self):
        raw = sample()
        length = struct.unpack("<I", raw[-8:-4])[0]
        parsed = m.parse_footer(raw[-8-length:-8])
        self.assertEqual(parsed["schema_paths"], ["schema", "schema.block_number"])
        self.assertEqual(parsed["num_rows_declared"], 10)
        self.assertEqual(parsed["row_groups_declared"], 1)

    def test_two_exact_http_ranges_and_fail_closed_status(self):
        raw, calls = sample(), []
        def opener(request, timeout):
            self.assertEqual(timeout, 20)
            value = request.get_header("Range")
            calls.append(value)
            if value.startswith("bytes=-"):
                return Reply(raw[-8:], len(raw) - 8, len(raw) - 1, len(raw))
            start, end = map(int, value[6:].split("-"))
            self.assertEqual(request.get_header("If-match"), '"same"')
            return Reply(raw[start:end + 1], start, end, len(raw))
        result = m.probe_file("blocks/date=2025-07-01/blocks.parquet", len(raw), opener=opener)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["num_rows_declared"], 10)
        self.assertFalse(result["full_day_coverage_verified"])
        self.assertFalse(result["ordinary_user_sellability_verified"])

    def test_full_http_200_rejected(self):
        class Full(io.BytesIO):
            status = 200
            headers = {}
        with self.assertRaisesRegex(m.SourceError, "RANGE_UNSUPPORTED"):
            m.read_range("https://example.invalid", None, None,
                         opener=lambda request, timeout: Full(b"x" * 20))

    def test_size_mismatch_rejected(self):
        raw = sample()
        with self.assertRaisesRegex(m.SourceError, "OBJECT_SIZE_CHANGED"):
            m.read_range("https://example.invalid", None, None, len(raw) + 1,
                         opener=lambda request, timeout: Reply(
                             raw[-8:], len(raw) - 8, len(raw) - 1, len(raw)))

    def test_wrong_magic_rejected(self):
        raw = b"NOTPAR1?"
        with self.assertRaisesRegex(m.SourceError, "NOT_UNENCRYPTED"):
            m.probe_file("blocks/date=2025-07-01/blocks.parquet", len(raw),
                         opener=lambda request, timeout: Reply(
                             raw[-8:], len(raw) - 8, len(raw) - 1, len(raw)))

    def test_oversized_footer_reads_bounded_prefix_only(self):
        raw = sample()
        original_len = struct.unpack("<I", raw[-8:-4])[0]
        prefix_data = raw[-8-original_len:-8]
        fake_footer_size = m.CAP + 1024
        fake_total = fake_footer_size + 8192
        prefix = prefix_data + b"\x00" * (m.SCHEMA_PREFIX_CAP-len(prefix_data))
        calls = []
        def opener(request, timeout):
            header = request.get_header("Range")
            calls.append(header)
            if header == "bytes=-8":
                return Reply(struct.pack("<I", fake_footer_size) + b"PAR1",
                             fake_total-8, fake_total-1, fake_total)
            start, end = map(int, header[6:].split("-"))
            self.assertEqual(end-start+1, m.SCHEMA_PREFIX_CAP)
            self.assertEqual(request.get_header("If-match"), '"same"')
            return Reply(prefix, start, end, fake_total)
        result = m.probe_file("transactions/date=2025-07-01/transactions.parquet",
                              fake_total, opener=opener)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["schema_paths"], ["schema", "schema.block_number"])
        self.assertEqual(result["num_rows_declared"], 10)
        self.assertEqual(result["footer_bytes"], fake_footer_size)
        self.assertIsNone(result["row_groups_declared"])
        self.assertIsNone(result["footer_sha256"])
        self.assertEqual(result["metadata_prefix_bytes"], m.SCHEMA_PREFIX_CAP)
        self.assertEqual(result["scope"], "OVERSIZED_FOOTER_SCHEMA_PREFIX_ONLY")
        self.assertFalse(result["footer_fully_verified"])
        self.assertFalse(result["pit_verified"])

    def test_oversized_footer_invalid_schema_fails_closed(self):
        fake_footer_size = m.CAP + 1
        fake_total = fake_footer_size + 8192
        def opener(request, timeout):
            header = request.get_header("Range")
            if header == "bytes=-8":
                return Reply(struct.pack("<I", fake_footer_size) + b"PAR1",
                             fake_total-8, fake_total-1, fake_total)
            start, end = map(int, header[6:].split("-"))
            return Reply(b"\x00" * (end-start+1), start, end, fake_total)
        with self.assertRaisesRegex(m.SourceError, "SCHEMA_PREFIX_MISSING_FIELDS"):
            m.probe_file("transactions/date=2025-07-01/transactions.parquet",
                         fake_total, opener=opener)

    def test_impossible_footer_length_rejected_without_download(self):
        fake_total = 100
        def opener(request, timeout):
            self.assertEqual(request.get_header("Range"), "bytes=-8")
            return Reply(struct.pack("<I", 1000) + b"PAR1", 92, 99, 100)
        with self.assertRaisesRegex(m.SourceError, "FOOTER_INVALID_LENGTH"):
            m.probe_file("transactions/date=2025-07-01/transactions.parquet",
                         fake_total, opener=opener)



if __name__ == "__main__":
    unittest.main()
