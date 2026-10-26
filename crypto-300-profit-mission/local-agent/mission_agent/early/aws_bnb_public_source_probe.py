"""Bounded anonymous S3 listing for Monster P0; no downloads or file writes.

Directory and object listings prove only current bucket visibility, not historical
log/receipt coverage, contemporaneous availability, or executable sellability.
"""
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ENDPOINT = "https://aws-public-blockchain.s3.us-east-2.amazonaws.com/"
PREFIX = "v1.1/bnb/"
TABLES = ("blocks", "transactions")
XML_NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def read_listing(prefix, delimiter=None, opener=urllib.request.urlopen):
    params = {"list-type": "2", "prefix": prefix, "max-keys": "10"}
    if delimiter is not None:
        params["delimiter"] = delimiter
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    with opener(url, timeout=15) as response:
        body = response.read(128 * 1024 + 1)
    if len(body) > 128 * 1024:
        raise ValueError("S3_LIST_RESPONSE_TOO_LARGE")
    root = ET.fromstring(body)
    if root.tag != "{%s}ListBucketResult" % XML_NS["s"]:
        raise ValueError("NOT_S3_LIST_BUCKET_RESULT")
    def string(path):
        el = root.find(path, XML_NS)
        return el.text if el is not None else None
    if string("s:Prefix") != prefix:
        raise ValueError("S3_PREFIX_MISMATCH")
    objects = []
    for el in root.findall("s:Contents", XML_NS):
        key = el.findtext("s:Key", default="", namespaces=XML_NS)
        size = el.findtext("s:Size", default="", namespaces=XML_NS)
        if not key.startswith(prefix) or not size.isdecimal():
            raise ValueError("S3_OBJECT_ENTRY_INVALID")
        objects.append({"key": key, "size_bytes": int(size)})
    folders = [x.findtext("s:Prefix", default="", namespaces=XML_NS)
               for x in root.findall("s:CommonPrefixes", XML_NS)]
    if any(not folder.startswith(prefix) for folder in folders):
        raise ValueError("S3_CHILD_PREFIX_INVALID")
    return {"objects": objects, "child_prefixes": folders,
            "truncated": string("s:IsTruncated") == "true"}


def probe(day="2025-07-01", reader=read_listing):
    dt.date.fromisoformat(day)
    year, month, date = day.split("-")
    suffixes = (f"date={day}/", f"{day}/", f"{year}/{month}/{date}/",
                f"year={year}/month={month}/day={date}/")
    results = {}
    for table in TABLES:
        prefix = PREFIX + table + "/"
        row = {"top_level": None, "date_prefix_probes": {},
               "date_objects_observed": False, "errors": []}
        try:
            row["top_level"] = reader(prefix, delimiter="/")
        except (OSError, ValueError, ET.ParseError) as exc:
            row["errors"].append("top_level:" + type(exc).__name__ + ":" + str(exc)[:180])
        for suffix in suffixes:
            try:
                got = reader(prefix + suffix)
                row["date_prefix_probes"][suffix] = got
                row["date_objects_observed"] |= bool(got["objects"])
            except (OSError, ValueError, ET.ParseError) as exc:
                row["date_prefix_probes"][suffix] = {"error": type(exc).__name__ + ":" + str(exc)[:180]}
                row["errors"].append(suffix + ":" + type(exc).__name__)
        results[table] = row
    return {"source": ENDPOINT, "base_prefix": PREFIX, "utc_day": day,
            "scope": "ANONYMOUS_LIST_ONLY_NO_OBJECT_CONTENT", "results": results,
            "log_receipt_columns_verified": False,
            "pit_verified": False, "sellability_verified": False}


def main():
    print(json.dumps(probe(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
