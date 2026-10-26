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


if __name__ == "__main__":
    unittest.main()
