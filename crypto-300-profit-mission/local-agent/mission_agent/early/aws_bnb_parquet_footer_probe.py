"""Bounded Parquet footer-only metadata probe for AWS public BNB Chain.

Exactly two ranged HTTP GETs per immutable object, no full-file download,
dependencies, AWS account, disk writes, RPC, transactions, or background task.
Metadata names and row counts cannot establish PIT, full coverage or G4.
"""
import hashlib
import json
import re
import struct
import urllib.request

BASE = "https://aws-public-blockchain.s3.us-east-2.amazonaws.com/v1.1/bnb/"
FILES = {
    "blocks": ("blocks/date=2025-07-01/blocks.parquet", 147077458),
    "transactions": ("transactions/date=2025-07-01/transactions.parquet", 4826591204),
}
CAP = 8 * 1024 * 1024
CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


class SourceError(ValueError):
    pass


def read_range(url, start, end, expected_size=None, etag=None, opener=urllib.request.urlopen):
    if start is None:
        spec, count = "bytes=-8", 8
    else:
        if not 0 <= start <= end:
            raise SourceError("INVALID_RANGE")
        count = end - start + 1
        spec = "bytes=%d-%d" % (start, end)
    if count > CAP:
        raise SourceError("RANGE_EXCEEDS_CAP")
    headers = {"Range": spec, "Accept-Encoding": "identity"}
    if etag is not None:
        headers["If-Match"] = etag
    req = urllib.request.Request(url, headers=headers)
    with opener(req, timeout=20) as response:
        match = CONTENT_RANGE.fullmatch(response.headers.get("Content-Range", "").strip())
        if response.status != 206 or match is None:
            raise SourceError("RANGE_UNSUPPORTED_OR_NOT_PARTIAL")
        low, high, total = map(int, match.groups())
        if total < 8:
            raise SourceError("OBJECT_TOO_SMALL")
        if start is None:
            if low != total - 8 or high != total - 1:
                raise SourceError("SUFFIX_RANGE_MISMATCH")
        elif low != start or high != end:
            raise SourceError("CONTENT_RANGE_MISMATCH")
        if expected_size is not None and total != expected_size:
            raise SourceError("OBJECT_SIZE_CHANGED")
        new_etag = response.headers.get("ETag")
        if etag is not None and new_etag != etag:
            raise SourceError("OBJECT_ETAG_CHANGED")
        body = response.read(count + 1)
        if len(body) != count:
            raise SourceError("BAD_RANGE_LENGTH")
        return body, total, new_etag


class CompactReader:
    """Read relevant Apache Parquet Thrift CompactProtocol metadata only."""
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, n):
        if n < 0 or self.pos + n > len(self.data):
            raise SourceError("COMPACT_TRUNCATED")
        result = self.data[self.pos:self.pos + n]
        self.pos += n
        return result

    def byte(self):
        return self.take(1)[0]

    def varint(self):
        number = 0
        for i in range(10):
            value = self.byte()
            number |= (value & 127) << (i * 7)
            if not value & 128:
                return number
        raise SourceError("COMPACT_VARINT_OVERFLOW")

    def signed(self):
        number = self.varint()
        return (number >> 1) ^ -(number & 1)

    def binary(self):
        n = self.varint()
        if n > CAP:
            raise SourceError("COMPACT_BINARY_TOO_LARGE")
        return self.take(n)

    def list_header(self):
        value = self.byte()
        length, typ = value >> 4, value & 15
        if length == 15:
            length = self.varint()
        if length > 1000000:
            raise SourceError("COMPACT_LIST_TOO_LARGE")
        return length, typ

    def fields(self, wanted, depth=0):
        if depth > 64:
            raise SourceError("COMPACT_TOO_DEEP")
        previous, result = 0, {}
        while True:
            header = self.byte()
            if not header:
                break
            delta, kind = header >> 4, header & 15
            field = previous + delta if delta else self.signed()
            if field <= 0:
                raise SourceError("COMPACT_FIELD_ID_INVALID")
            previous = field
            if field in wanted:
                result[field] = wanted[field](kind, depth + 1)
            else:
                self.skip(kind, depth + 1)
        return result

    def skip(self, kind, depth=0):
        if depth > 64:
            raise SourceError("COMPACT_TOO_DEEP")
        if kind in (1, 2):
            return
        if kind == 3:
            self.take(1)
        elif kind in (4, 5, 6):
            self.varint()
        elif kind == 7:
            self.take(8)
        elif kind == 8:
            self.binary()
        elif kind in (9, 10):
            n, nested_kind = self.list_header()
            for _ in range(n):
                self.skip(nested_kind, depth + 1)
        elif kind == 11:
            n = self.varint()
            if n:
                types = self.byte()
                for _ in range(n):
                    self.skip(types >> 4, depth + 1)
                    self.skip(types & 15, depth + 1)
        elif kind == 12:
            self.fields({}, depth + 1)
        elif kind == 13:
            self.take(16)
        else:
            raise SourceError("COMPACT_UNKNOWN_TYPE_%d" % kind)


def require(kind, expected):
    if kind != expected:
        raise SourceError("PARQUET_METADATA_TYPE_MISMATCH")


def read_int(reader, kind, depth):
    if kind not in (4, 5, 6):
        raise SourceError("EXPECTED_COMPACT_INTEGER")
    return reader.signed()


def read_name(reader, kind, depth):
    require(kind, 8)
    return reader.binary().decode("utf-8")


def schema_element(reader, kind, depth):
    require(kind, 12)
    return reader.fields({
        1: lambda t, d: read_int(reader, t, d),
        3: lambda t, d: read_int(reader, t, d),
        4: lambda t, d: read_name(reader, t, d),
        5: lambda t, d: read_int(reader, t, d),
    }, depth)


def schema_list(reader, kind, depth):
    require(kind, 9)
    count, element_kind = reader.list_header()
    require(element_kind, 12)
    if count > 4096:
        raise SourceError("SCHEMA_TOO_WIDE")
    return [schema_element(reader, element_kind, depth + 1) for _ in range(count)]


def row_group_count(reader, kind, depth):
    require(kind, 9)
    count, element_kind = reader.list_header()
    require(element_kind, 12)
    for _ in range(count):
        reader.skip(element_kind, depth + 1)
    return count


def flattened_schema(schema):
    if not schema:
        raise SourceError("SCHEMA_ROOT_MISSING")
    paths = []
    def walk(index, prefix, depth):
        if index >= len(schema) or depth > 30:
            raise SourceError("SCHEMA_NESTING_INVALID")
        record = schema[index]
        name = record.get(4)
        if not isinstance(name, str) or not name or len(name) > 500:
            raise SourceError("SCHEMA_NAME_INVALID")
        children = record.get(5, 0)
        if children < 0 or children > 4096:
            raise SourceError("SCHEMA_CHILD_COUNT_INVALID")
        current = prefix + [name]
        paths.append(".".join(current))
        index += 1
        for _ in range(children):
            index = walk(index, current, depth + 1)
        return index
    if walk(0, [], 0) != len(schema):
        raise SourceError("SCHEMA_EXTRA_ELEMENTS")
    return paths


def parse_footer(meta):
    reader = CompactReader(meta)
    result = reader.fields({
        1: lambda t, d: read_int(reader, t, d),
        2: lambda t, d: schema_list(reader, t, d),
        3: lambda t, d: read_int(reader, t, d),
        4: lambda t, d: row_group_count(reader, t, d),
    })
    if reader.pos != len(meta) or any(k not in result for k in (1, 2, 3, 4)):
        raise SourceError("PARQUET_FOOTER_MALFORMED")
    if result[3] < 0:
        raise SourceError("NEGATIVE_NUM_ROWS")
    return {
        "schema_paths": flattened_schema(result[2]),
        "num_rows_declared": result[3],
        "row_groups_declared": result[4],
        "parquet_metadata_version": result[1],
    }


def probe_file(key, listed_size, opener=urllib.request.urlopen):
    url = BASE + key
    tail, size, etag = read_range(url, None, None, listed_size, opener=opener)
    if tail[4:] != b"PAR1":
        raise SourceError("NOT_UNENCRYPTED_PARQUET_V1")
    footer_size = struct.unpack("<I", tail[:4])[0]
    if not 0 < footer_size <= CAP or footer_size > size - 8:
        raise SourceError("FOOTER_TOO_LARGE_OR_INVALID")
    first, last = size - 8 - footer_size, size - 9
    meta, second_size, new_etag = read_range(
        url, first, last, size, etag, opener=opener)
    if size != second_size:
        raise SourceError("SIZE_CHANGED_DURING_READ")
    parsed = parse_footer(meta)
    columns = parsed["schema_paths"]
    parsed.update({
        "key": key,
        "listed_object_size_bytes": listed_size,
        "footer_bytes": footer_size,
        "footer_sha256": hashlib.sha256(meta).hexdigest(),
        "etag": new_etag,
        "suspected_log_receipt_fields": [
            p for p in columns if any(
                w in p.lower() for w in (
                    "log", "topic", "receipt", "status", "contract",
                    "timestamp", "gas"))],
        "scope": "PARQUET_FOOTER_ONLY_NO_ROW_VALUES",
        "full_day_coverage_verified": False,
        "pit_verified": False,
        "ordinary_user_sellability_verified": False,
    })
    return parsed


def run():
    report = {
        "source": BASE,
        "utc_day": "2025-07-01",
        "scope": "ANONYMOUS_HTTP_RANGE_METADATA_ONLY",
        "results": {},
        "logs_and_receipts_usable": "UNVERIFIED",
        "pit_status": "NOT_SCORABLE",
        "sellability_status": "UNKNOWN",
    }
    for table, (key, size) in FILES.items():
        try:
            report["results"][table] = probe_file(key, size)
        except Exception as error:
            report["results"][table] = {
                "status": "SOURCE_NOT_ACCESSIBLE_OR_INVALID",
                "error": type(error).__name__ + ":" + str(error)[:220],
            }
    return report


def main():
    print(json.dumps(run(), indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
