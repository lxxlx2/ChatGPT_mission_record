"""Interpret trusted local exact-address category receipts without network.

Capture and source authentication belong to the local evidence collector. An
archive digest binds bytes, not the publisher of those bytes. Never fetch from
the read path or follow links from a receipt. Alert admission requires an
explicitly enabled local receipt path and its separate trigger proof.
"""
import hashlib
import os
import stat

from .buy_admission import Asset, EXCLUDED_MINTS, exact_mint
from .reconciliation import _object

COINGECKO_SOLANA = "https://api.coingecko.com/api/v3/coins/solana/contract/"
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_MAX_RESPONSE_BYTES = 512 * 1024
_MEME = {"meme", "solana meme"}
_NOT_MEME = {"stablecoins", "liquid staking tokens", "exchange-based tokens"}
_CONFLICT = "CATEGORY_EVIDENCE_CONFLICT"


def _parse(row, as_of):
    if not isinstance(row, dict):
        return None
    mint, at, body = (row.get(field) for field in ("mint", "observed_at", "body"))
    if (not exact_mint(mint) or mint in EXCLUDED_MINTS or type(at) is not int or not 0 < at <= as_of
            or row.get("url") != COINGECKO_SOLANA + mint or not isinstance(body, str)):
        return None
    try:
        raw = body.encode("utf-8")
    except UnicodeError:
        return None
    if len(raw) > _MAX_RESPONSE_BYTES:
        return None
    digest = hashlib.sha256(raw).hexdigest()
    if digest != row.get("sha256"):
        return None
    payload = _object(raw)
    if not payload or "error" in payload or payload.get("preview_listing") is not False:
        return None
    platforms, details = payload.get("platforms"), payload.get("detail_platforms")
    solana = details.get("solana") if isinstance(details, dict) else None
    if (not isinstance(platforms, dict) or platforms.get("solana") != mint
            or not isinstance(solana, dict) or solana.get("contract_address") != mint):
        return None
    categories = payload.get("categories")
    if not isinstance(categories, list) or not all(isinstance(x, str) for x in categories):
        return None
    tags = {tag.strip().casefold() for tag in categories}
    positive, negative = bool(tags & _MEME), bool(tags & _NOT_MEME)
    status = ("VERIFIED_MEME" if positive and not negative else
              "EXCLUDED" if negative and not positive else "PENDING")
    name = payload.get("name")
    name = name.strip() if isinstance(name, str) and 0 < len(name.strip()) <= 80 else None
    source = COINGECKO_SOLANA + mint + "#sha256=" + digest
    return mint, Asset(status, _CONFLICT if positive and negative else source, at, name)


def _regular_file(path, flags):
    fd = os.open(path, flags | os.O_NONBLOCK | os.O_NOFOLLOW)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise OSError("CATEGORY_EVIDENCE_FILE_REQUIRED")
    return fd


def read_category_evidence(path, as_of):
    """Read local captures; only one unambiguous category result per Mint."""
    if path is None:
        return {}
    try:
        with open(path, "rb", opener=_regular_file) as handle:
            raw = handle.read(_MAX_MANIFEST_BYTES + 1)
    except OSError:
        return {}
    if len(raw) > _MAX_MANIFEST_BYTES:
        return {}
    document = _object(raw)
    if (not document or type(document.get("version")) is not int or document["version"] != 1
            or not isinstance(document.get("records"), list)):
        return {}
    return _parse_records(document["records"], as_of)


def _parse_records(records, as_of):
    assets = {}
    for row in records:
        item = _parse(row, as_of)
        if item is not None:
            merge_category_assets(assets, {item[0]: item[1]})
    return assets


def merge_category_assets(base, additions):
    """Merge observations by exact Mint and keep contradictory evidence pending."""
    for mint, asset in additions.items():
        prior = base.get(mint)
        if prior is None:
            base[mint] = asset
        elif (_CONFLICT in (prior.source, asset.source)
              or {prior.status, asset.status} == {"VERIFIED_MEME", "EXCLUDED"}):
            base[mint] = Asset("PENDING", _CONFLICT, max(prior.observed_at, asset.observed_at), None)
        elif (asset.status != "PENDING" and prior.status == "PENDING"
              or asset.status == prior.status and (asset.observed_at, asset.source) > (prior.observed_at, prior.source)):
            # Unclassified is absence, not conflicting negative evidence.
            base[mint] = asset
    return base


def read_scanner_category_evidence(db, as_of, *, mint=None):
    """Read only the existing Scanner ledger. Legacy copies need no migration to read."""
    if db is None or db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='buy_category_auto'"
    ).fetchone() is None:
        return {}
    query = "SELECT mint,receipt FROM buy_category_auto WHERE receipt IS NOT NULL"
    parameters = ()
    if mint is not None:
        query += " AND mint=?"
        parameters = (mint,)
    assets = {}
    for key, raw in db.execute(query, parameters):
        if not isinstance(raw, str) or len(raw) > _MAX_RESPONSE_BYTES * 6 + 512:
            continue
        row = _object(raw)
        if row is not None and row.get("mint") == key:
            parsed = _parse(row, as_of)
            if parsed is not None:
                assets[key] = parsed[1]
    return assets
