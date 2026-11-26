"""One-shot CoinGecko Demo capture for a new local history sidecar.

Only an explicit invocation performs reads. It needs an already authorized
Demo key and accepts only Solana Mint addresses, never wallet or trade IDs.
Use a fresh staging destination; this tool cannot replace a control file.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.request

from .buy_admission import EXCLUDED_MINTS, exact_mint
from .category_evidence import COINGECKO_SOLANA, _MAX_MANIFEST_BYTES, _MAX_RESPONSE_BYTES, _parse

_MAX_MINTS = 6
_MAX_ELAPSED = 30.0


class _RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, handle, status, reason, headers, url):
        # Never forward a credential to a redirected URL.
        return None


def _open(request, *, timeout):
    return urllib.request.build_opener(_RejectRedirect()).open(request, timeout=timeout)


def capture(mints, *, api_key, open_url=_open, clock=time.time, monotonic=time.monotonic):
    """Return versioned raw captures and sanitized per-item coverage counts."""
    if not isinstance(mints, (list, tuple)) or not 1 <= len(mints) <= _MAX_MINTS:
        raise ValueError("CATEGORY_CAPTURE_MINT_LIMIT")
    if not all(exact_mint(mint) for mint in mints):
        raise ValueError("CATEGORY_CAPTURE_MINT_INVALID")
    if not isinstance(api_key, str) or not api_key or len(api_key) > 256 or not api_key.isascii() or any(
        ch.isspace() or not ch.isprintable() for ch in api_key
    ):
        raise ValueError("CATEGORY_CAPTURE_DEMO_KEY_REQUIRED")
    records, counts = [], {}

    def count(status):
        counts[status] = counts.get(status, 0) + 1

    deadline = monotonic() + _MAX_ELAPSED
    for mint in dict.fromkeys(mints):
        if mint in EXCLUDED_MINTS:
            count("HARD_EXCLUDED")
            continue
        remaining = deadline - monotonic()
        if remaining <= 0:
            count("CAPTURE_DEADLINE")
            break
        url = COINGECKO_SOLANA + mint
        request = urllib.request.Request(url, headers={"Accept": "application/json", "x-cg-demo-api-key": api_key})
        try:
            with open_url(request, timeout=min(8.0, remaining)) as response:
                if response.geturl() != url:
                    count("SOURCE_REDIRECT_REFUSED")
                    break
                chunks, used = [], 0
                while used <= _MAX_RESPONSE_BYTES:
                    if monotonic() >= deadline:
                        raise TimeoutError("CATEGORY_CAPTURE_DEADLINE")
                    chunk = response.read1(min(65536, _MAX_RESPONSE_BYTES + 1 - used))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    used += len(chunk)
                raw = b"".join(chunks)
            if len(raw) > _MAX_RESPONSE_BYTES:
                count("SOURCE_RESPONSE_LIMIT")
                continue
            at = int(clock())
            row = {"mint": mint, "observed_at": at, "url": url, "body": raw.decode("utf-8"),
                   "sha256": hashlib.sha256(raw).hexdigest()}
            parsed = _parse(row, at)
            if parsed is None:
                count("SOURCE_RECEIPT_UNUSABLE")
                continue
            records.append(row)
            count(parsed[1].status)
        except urllib.error.HTTPError as error:
            if 300 <= error.code < 400:
                count("SOURCE_REDIRECT_REFUSED")
                break
            if error.code in (401, 403, 429):
                count({401: "SOURCE_AUTH_REQUIRED", 403: "SOURCE_FORBIDDEN", 429: "SOURCE_RATE_LIMIT"}[error.code])
                break
            count("SOURCE_NO_RECORD" if error.code == 404 else "SOURCE_HTTP_UNAVAILABLE")
        except (OSError, ValueError):
            count("SOURCE_UNAVAILABLE")
    return {"version": 1, "records": records}, counts


def write_new_sidecar(path, document):
    """Atomically publish a private local file, refusing to replace any target."""
    path = Path(path)
    body = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > _MAX_MANIFEST_BYTES:
        raise ValueError("CATEGORY_CAPTURE_FILE_TOO_LARGE")
    with tempfile.TemporaryDirectory(prefix=".category-", dir=path.parent) as work:
        temporary = Path(work) / "evidence.json"
        with open(temporary, "xb", opener=lambda p, f: os.open(p, f, 0o600)) as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new local staging file, never overwritten")
    parser.add_argument("mint", nargs="+", help="one to six complete Solana mint addresses")
    args = parser.parse_args(argv)
    target = Path(args.output)
    if not target.parent.is_dir() or os.path.lexists(target):
        parser.error("CATEGORY_CAPTURE_NEW_STAGING_FILE_REQUIRED")
    try:
        document, coverage = capture(args.mint, api_key=os.environ.get("COINGECKO_DEMO_API_KEY"))
        if document["records"]:
            write_new_sidecar(target, document)
    except (OSError, ValueError) as error:
        # Do not expose filesystem paths or credential text from exceptions.
        parser.error(str(error) if isinstance(error, ValueError) and str(error).startswith("CATEGORY_CAPTURE_")
                     else "CATEGORY_CAPTURE_FAILED")
    print(json.dumps({"records": len(document["records"]), "coverage": coverage}, sort_keys=True))
    return 0 if document["records"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
