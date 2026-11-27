"""Build a new Frank USD sidecar from private, previously saved captures. Offline only."""
import argparse
import base64
from decimal import Decimal
import json
import os
from pathlib import Path
import stat
import tempfile

from mission_agent.mission_control.frank_buys import _MAX_USD_EVIDENCE_BYTES
from mission_agent.signals.historical_usd_tick import _MAX_CAPTURE, observe_usd_tick
from mission_agent.signals.reconciliation import _unique_pairs


def _read_regular(path, limit):
    def open_regular(name, flags):
        fd = os.open(name, flags | os.O_NONBLOCK)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise ValueError("LOCAL_REGULAR_FILE_REQUIRED")
        return fd
    with open(path, "rb", opener=open_regular) as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError("LOCAL_INPUT_EXCEEDS_LIMIT")
    return data


def _existing_records(path):
    if path is None:
        return []
    document = json.loads(_read_regular(path, _MAX_USD_EVIDENCE_BYTES),
                          parse_float=Decimal, object_pairs_hook=_unique_pairs)
    if (not isinstance(document, dict) or type(document.get("version")) is not int
            or document["version"] != 1 or not isinstance(document.get("records"), list)):
        raise ValueError("VERSION_1_RECORDS_REQUIRED")
    return document["records"]


def _publish_new(path, payload):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".frank-buy-usd-", delete=False) as file:
        temporary = Path(file.name)
        try:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
            # Same-directory exclusive publish. Never replace a previous file.
            os.link(temporary, path)
        finally:
            temporary.unlink()


def build(output, receipts, *, legacy=None):
    """Strictly verify selected receipts before writing any output."""
    records = _existing_records(legacy)
    captures = []
    seen = set()
    # Base64 dominates output size; bound the sum before retaining raw copies.
    encoded_bytes = 0
    for asset, wall_second, url, path in receipts:
        if not isinstance(wall_second, str) or not wall_second.isascii() or not wall_second.isdecimal() or len(wall_second) > 10:
            raise ValueError("INVALID_TRADE_SECOND")
        second = int(wall_second)
        if (asset, second) in seen:
            raise ValueError("DUPLICATE_ASSET_AND_SECOND")
        seen.add((asset, second))
        raw = _read_regular(path, _MAX_CAPTURE)
        observation = observe_usd_tick(asset, second, url=url, raw=raw)
        if observation["status"] != "OBSERVED_SECOND_CONVERSION":
            raise ValueError(observation["reason"])
        encoded_bytes += 4 * ((len(raw) + 2) // 3)
        if encoded_bytes > _MAX_USD_EVIDENCE_BYTES:
            raise ValueError("OUTPUT_EXCEEDS_LIMIT")
        captures.append({"asset": asset, "block_time": second, "source_url": url,
                         "source_sha256": observation["source_sha256"],
                         "raw_base64": base64.b64encode(raw).decode("ascii")})
    if not captures:
        raise ValueError("RECEIPT_REQUIRED")
    payload = (json.dumps({"version": 2, "records": records, "captures": captures},
                          ensure_ascii=False, separators=(",", ":"), default=str) + "\n").encode("utf-8")
    if len(payload) > _MAX_USD_EVIDENCE_BYTES:
        raise ValueError("OUTPUT_EXCEEDS_LIMIT")
    _publish_new(output, payload)
    return len(captures)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New private file; never overwrites")
    parser.add_argument("--legacy", type=Path, help="Optional previous version 1 exact-trade records")
    parser.add_argument("--receipt", action="append", nargs=4, required=True,
                        metavar=("ASSET", "UNIX_SECOND", "REQUEST_URL", "RAW_FILE"))
    args = parser.parse_args(argv)
    try:
        count = build(args.output, args.receipt, legacy=args.legacy)
    except (OSError, ValueError, RecursionError) as exc:
        # Do not print private input paths or raw data.
        error = str(exc) if type(exc) is ValueError and str(exc).isupper() else type(exc).__name__
        parser.exit(2, f"USD evidence not written: {error}\n")
    print(json.dumps({"status": "LOCAL_USD_EVIDENCE_PREPARED", "capture_count": count}))


if __name__ == "__main__":
    main()
