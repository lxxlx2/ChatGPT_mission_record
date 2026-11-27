"""Read-only Frank buys over the existing signed trade ledger."""
import base64
from contextlib import closing
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import os
import re
import stat

from .archived_wallet_facts import read_archived_classification
from .wallet_activity import connect
from .wallet_activity_paging import _source
from ..meme.market_parity import number
from ..signals.buy_admission import EXCLUDED_MINTS, admit_buy, effective_qualification, exact_mint
from ..signals.classifier import USDT
from ..signals.historical_usd_tick import observe_usd_tick
from ..signals.person_scope import PersonWalletScope
from ..signals.policy import USDC
from ..signals.reconciliation import _unique_pairs


_TRADE_IDENTITY = ("wallet", "signature", "slot", "block_time", "raw_hash", "mint")
_QUOTE_ASSET = {"SOL": "SOL", "USDC": USDC, "USDT": USDT}
_MAX_USD_EVIDENCE_BYTES = 4 * 1024 * 1024


def _second_conversion(capture, asset, second):
    fields = ("source_url", "source_sha256", "raw_base64")
    if any(not isinstance(capture.get(field), str) for field in fields):
        return None
    try:
        raw = base64.b64decode(capture["raw_base64"], validate=True)
        if hashlib.sha256(raw).hexdigest() != capture["source_sha256"]:
            return None
        result = observe_usd_tick(asset, second, url=capture["source_url"], raw=raw)
    except (ValueError, RecursionError):
        return None
    if result["status"] == "OBSERVED_SECOND_CONVERSION":
        return Decimal(result["usd_per_quote_unit"])
    return None


def _read_usd_evidence(path):
    """Index explicitly supplied USD observation records once per request."""
    if path is None:
        return {}, {}, None
    def open_regular(local_path, flags):
        fd = os.open(local_path, flags | os.O_NONBLOCK)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise OSError("USD_EVIDENCE_FILE_REQUIRED")
        return fd

    try:
        with open(path, "rb", opener=open_regular) as source:
            raw = source.read(_MAX_USD_EVIDENCE_BYTES + 1)
        if len(raw) > _MAX_USD_EVIDENCE_BYTES:
            return {}, {}, None
        document = json.loads(raw, parse_float=Decimal, object_pairs_hook=_unique_pairs)
    except (OSError, ValueError, InvalidOperation, RecursionError):
        return {}, {}, None
    if (not isinstance(document, dict) or type(document.get("version")) is not int
            or document["version"] not in (1, 2) or not isinstance(document.get("records"), list)
            or (document["version"] == 2 and not isinstance(document.get("captures"), list))):
        return {}, {}, None

    observations = {}
    for row in document["records"]:
        if not isinstance(row, dict):
            continue
        key = tuple(row.get(field) for field in _TRADE_IDENTITY)
        if tuple(type(value) for value in key) != (str, str, int, int, str, str):
            continue
        fields = row.keys() & {"spent_usd", "usd_per_quote_unit"}
        asset, source = row.get("quote_asset"), row.get("source")
        if (not isinstance(asset, str) or asset not in _QUOTE_ASSET.values()
                or not isinstance(source, str) or not source.strip()
                or not isinstance(row.get("source_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"])
                or type(row.get("source_at")) is not int or row["source_at"] != row["block_time"]
                or len(fields) != 1):
            continue
        field, = fields
        amount = number(row[field])
        if amount is None or Decimal(amount) <= 0:
            continue
        key += (asset,)
        # Conflicting references cannot silently choose the last input row.
        value = (field, Decimal(amount))
        observations[key] = value if key not in observations else None
    captures = {}
    if document["version"] == 2:
        for row in document["captures"]:
            if not isinstance(row, dict):
                continue
            asset, second = row.get("asset"), row.get("block_time")
            if not isinstance(asset, str) or asset not in _QUOTE_ASSET or type(second) is not int:
                continue
            key = (asset, second)
            # Duplicate (even if malformed or identical) is ambiguous.
            captures[key] = None if key in captures else _second_conversion(row, asset, second)
    return observations, captures, hashlib.sha256(raw).hexdigest()


def _buy_usd(item, identity, observations, captures):
    key = tuple(identity[field] for field in _TRADE_IDENTITY) + (_QUOTE_ASSET.get(item["currency"]),)
    empty = {"spent_usd": None, "entry_price_usd": None}
    if item["paid"] is None:
        return empty
    observation = observations.get(key)
    if observation is None:
        rate = captures.get((item["currency"], identity["block_time"]))
        if key in observations or rate is None:
            return empty
        field, value = "usd_per_quote_unit", rate
    else:
        field, value = observation
    paid, quantity = Decimal(item["paid"]), Decimal(item["quantity"])
    with localcontext() as context:
        context.prec = max(50, len(value.as_tuple().digits) + len(paid.as_tuple().digits))
        spent = value if field == "spent_usd" else paid * value
        prices = (format(spent.normalize(), "f"), format((spent / quantity).normalize(), "f"))
    if observation is None:
        return {**empty, "estimated_spent_usd": prices[0], "estimated_entry_price_usd": prices[1],
                "usd_estimate_basis": "PAYMENT_ASSET_MARKET_TRADE_SAME_SECOND"}
    return {"spent_usd": prices[0], "entry_price_usd": prices[1]}

def _encode(row):
    return base64.urlsafe_b64encode(json.dumps(row, separators=(",", ":")).encode()).decode().rstrip("=")


def _decode(cursor, binding):
    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", cursor):
            raise ValueError()
        values = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        version, source, cutoff, rowmax, at, rowid = values
        if version != 1 or source != binding or any(
                type(n) is not int or not 0 < n < 2**63 for n in (cutoff, rowmax, at, rowid)
        ) or at > cutoff or rowid > rowmax:
            raise ValueError()
        return cutoff, rowmax, at, rowid
    except (TypeError, ValueError):
        raise ValueError("INVALID_OR_STALE_CURSOR") from None


def _needs_archive_replay(event, identity):
    if not isinstance(event, dict) or event.get("classification") != "ACTIVE_TRADE":
        return False
    trade, evidence = event.get("trade"), event.get("evidence")
    return (
        isinstance(trade, dict) and isinstance(evidence, dict)
        and identity["mint"] not in EXCLUDED_MINTS
        and trade.get("mint") == identity["mint"] and trade.get("direction") == "BUY"
        and event.get("frank_is_signer") is True and evidence.get("wallet_is_signer") is True
        and evidence.get("raw_transaction_sha256") == identity["raw_hash"]
        and all(source.get(key) == identity[key] for source in (event, evidence)
                for key in ("wallet", "signature", "slot", "block_time"))
        and not {"quote_legs", "route_amount_semantics", "route_intermediate_evidence_status"} & trade.keys()
    )


def read_buys(database, qualifications, *, as_of, days="7", mint=None, cursor=None,
              archive_root=None, legacy_archive_root=None, usd_evidence_path=None,
              category_evidence_path=None, person_scope=None):
    # The normal Dashboard does not pass a person scope. This internal seam
    # accepts a trusted local partition, not a recipient or arbitrary HTTP input.
    if person_scope is not None and not isinstance(person_scope, PersonWalletScope):
        raise ValueError("INVALID_PERSON_WALLET_SCOPE")
    if days not in ("1", "7", "30", "all") or (mint is not None and not exact_mint(mint)):
        raise ValueError("INVALID_BUY_QUERY")
    try:
        assets = effective_qualification(qualifications, category_evidence_path, as_of)
    except FileNotFoundError:
        return {"status": "QUALIFICATION_UNAVAILABLE", "rows": [], "next_cursor": None}
    observations, captures, evidence_sha = _read_usd_evidence(usd_evidence_path)
    source = _source(database)
    inputs = (source, days, mint, sorted(assets.items()), archive_root, legacy_archive_root, evidence_sha)
    if person_scope is not None:
        inputs += (("staged-person", person_scope.person_id, person_scope.wallets),)
    binding = hashlib.sha256(repr(inputs).encode()).hexdigest()
    with closing(connect(database)) as db:
        db.execute("BEGIN")
        if _source(database) != source:
            raise ValueError("INVALID_OR_STALE_CURSOR")
        joined = " FROM trades t JOIN signatures s ON s.wallet=t.wallet AND s.signature=t.signature WHERE "
        if person_scope is None:
            where, params = ["s.person_id='frank'"], []
        else:
            where = ["s.person_id=?", "s.wallet IN (SELECT value FROM json_each(?))"]
            params = [person_scope.person_id, json.dumps(person_scope.wallets)]
        where.append("t.side IN ('BUY','ADD','REENTRY')")
        if cursor is not None:
            cutoff, rowmax, at, rowid = _decode(cursor, binding)
            if cutoff > as_of:
                raise ValueError("INVALID_OR_STALE_CURSOR")
            where.append("(s.block_time,t.rowid)<(?,?)")
            params.extend([at, rowid])
        else:
            cutoff = as_of
            if person_scope is None:
                rowmax = db.execute("SELECT coalesce(max(rowid),0) FROM trades").fetchone()[0]
            else:
                rowmax = db.execute("SELECT coalesce(max(t.rowid),0)" + joined + " AND ".join(where),
                                    params).fetchone()[0]
        where.extend(["s.block_time BETWEEN ? AND ?", "t.rowid<=?"])
        params.extend([1 if days == "all" else cutoff - int(days)*86400, cutoff, rowmax])
        if mint is not None:
            where.append("t.mint=?")
            params.append(mint)
        where.append("t.mint IN (SELECT value FROM json_each(?))")
        params.append(json.dumps([m for m, a in assets.items() if a.status == "VERIFIED_MEME"]))
        records = db.execute(
            "SELECT t.rowid AS trade_id,t.mint,s.wallet,s.signature,s.slot,s.block_time,s.raw_hash,s.body "
            + joined + " AND ".join(where) + " ORDER BY s.block_time DESC,t.rowid DESC", params)
        rows, next_cursor = [], None
        for row in records:
            try:
                event = json.loads(row["body"])
            except (ValueError, TypeError):
                continue
            if person_scope is not None and (not isinstance(event, dict) or event.get("person_id") != person_scope.person_id):
                continue
            identity = {key: row[key] for key in _TRADE_IDENTITY}
            item = admit_buy(event, assets, **identity, allow_unpriced=True)
            if (item is None and archive_root is not None
                    and (person_scope is None or person_scope.person_id == "frank")
                    and _needs_archive_replay(event, identity)):
                replay = read_archived_classification(
                    archive_root, {"sig": row["signature"], "wallet": row["wallet"], "slot": row["slot"],
                                   "at": row["block_time"], "raw_sha256": row["raw_hash"]},
                    legacy_archive_root=legacy_archive_root,
                )
                item = admit_buy(replay, assets, **identity, allow_unpriced=True)
            if not item:
                continue
            if len(rows) == 30:
                next_cursor = _encode([1, binding, cutoff, rowmax, last["block_time"], last["trade_id"]])
                break
            rows.append({**item, **_buy_usd(item, identity, observations, captures)})
            last = row
        return {"status": "LOCAL_EVIDENCE_ONLY", "as_of": cutoff, "rows": rows, "next_cursor": next_cursor}
