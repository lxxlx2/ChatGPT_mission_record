"""Versioned facts over archived normalized Solana evidence and indexed trade rows."""

from collections import Counter
import re

from ..frank.parser import WSOL
from ..hashing import digest, loads
from ..meme.holder_ranks import valid_pubkey
from ..signals.policy import USDC
from .wallet_activity import SIDES, fixed_class, safe_id


SCHEMA_VERSION = 1
MECHANICAL_CLASSES = {
    "ACTIVE_SWAP_LIKE", "PASSIVE_RECEIPT_LIKE", "FAILED", "STAKE_LIKE",
    "TRANSFER_OUT_LIKE", "TRANSFER_IN_LIKE", "UNKNOWN",
}
AUTHORITY_FLAGS = (
    "wallet_authority", "dex_program_interaction", "swap_instruction_evidence",
    "opposing_economic_flows",
)
TRADE_DIRECTIONS = {
    "BUY": "BUY", "ADD": "BUY", "REENTRY": "BUY", "SELL": "SELL",
    "EXIT": "SELL", "SELL_POSITION_UNRESOLVED": "SELL",
}
MISSING = object()
INVALID = object()
SKIP = object()


def _integer(value, low=0, high=2**64-1):
    return value if type(value) is int and low <= value <= high else None


def _raw(value, *, signed=False):
    if type(value) is int:
        return str(value) if _integer(value, -(2**64-1) if signed else 0) is not None else None
    pattern = r"(?:0|-?[1-9][0-9]{0,19})" if signed else r"(?:0|[1-9][0-9]{0,19})"
    return value if isinstance(value, str) and re.fullmatch(pattern, value) and _raw(int(value), signed=signed) else None


def _pubkey(value):
    return value if valid_pubkey(value) else None


def _flag(value):
    return value if type(value) is bool else None


def _enum(value, allowed):
    return value if isinstance(value, str) and value in allowed else None


def _denomination(mint):
    return {WSOL: "WSOL", USDC: "USDC"}.get(mint, "SPL_TOKEN")


def _bound_evidence(row, evidence, wallet, signature, slot, raw_hash, version):
    if not evidence:
        return {}, "MISSING", None
    if not isinstance(evidence, dict):
        return {}, "INVALID", None
    identity = {
        "wallet": wallet, "signature": signature, "slot": slot,
        "raw_transaction_sha256": raw_hash,
    }
    if (version is None or any(value is None or evidence.get(key) != value for key, value in identity.items())
            or type(evidence.get("slot")) is not int
            or _version(evidence.get("parser_version")) != version):
        return {}, "BINDING_MISMATCH", None
    if row.get("at") is not None and evidence.get("block_time") != row["at"]:
        return {}, "BINDING_MISMATCH", None
    evidence_hash = safe_id(evidence.get("evidence_sha256"), re.compile(r"[0-9a-f]{64}"))
    try:
        matches = evidence_hash is not None and digest({
            key: value for key, value in evidence.items() if key != "evidence_sha256"
        }) == evidence_hash
    except (ValueError, TypeError, UnicodeError, RecursionError):
        matches = False
    return (evidence, "BOUND", evidence_hash) if matches else ({}, "INVALID", None)


def _version(value):
    return safe_id(str(value), re.compile(r"[A-Za-z0-9_.:-]{1,128}")) if type(value) in (int, str) else None


def _execution(evidence):
    error = evidence.get("tx_err", MISSING)
    if error is None:
        return "SUCCEEDED"
    if isinstance(error, (dict, str)) and error:
        return "FAILED"
    return "UNKNOWN"


def _instruction(record):
    scope = record.get("scope")
    reference = record.get("instruction")
    if scope == "outer" and isinstance(reference, str) and re.fullmatch(r"[0-9]{1,10}", reference):
        return [int(reference), -1]
    if scope == "inner" and isinstance(reference, str) and re.fullmatch(r"[0-9]{1,10}:[0-9]{1,10}", reference):
        return list(map(int, reference.split(":")))
    return None


def _account_balance(record, wallet):
    if record.get("owner") != wallet and record.get("wallet_owned") is False:
        return SKIP
    if record.get("owner") != wallet or record.get("wallet_owned") is not True:
        return INVALID
    mint = _pubkey(record.get("mint"))
    index = _integer(record.get("account_index"), high=255)
    pre = _raw(record.get("pre_amount"))
    post = _raw(record.get("post_amount"))
    delta = _raw(record.get("delta"), signed=True)
    decimals = _integer(record.get("decimals"), high=255)
    if None in (mint, index, pre, post, delta, decimals) or int(post) - int(pre) != int(delta):
        return INVALID
    return index, {"account_index": index, "mint": mint, "denomination": _denomination(mint),
                   "decimals": decimals, "pre_raw": pre, "post_raw": post, "delta_raw": delta}


def _token_transfer(record):
    reference = _instruction(record)
    mint = _pubkey(record.get("mint"))
    source = _pubkey(record.get("source"))
    destination = _pubkey(record.get("destination"))
    amount = _raw(record.get("raw_amount"))
    direction = _enum(record.get("direction"), {"IN", "OUT"})
    decimals = _integer(record.get("decimals"), high=255)
    if (None in (reference, mint, source, destination, amount, direction) or source == destination
            or [_integer(record.get("outer_index")), _integer(record.get("inner_index"), -1)] != reference
            or record.get("decimals") is not None and decimals is None):
        return INVALID
    return reference, {"instruction_ref": reference, "mint": mint, "denomination": _denomination(mint),
                       "direction": direction, "raw_amount": amount, "decimals": decimals,
                       "source_account": source, "destination_account": destination}


def _native_transfer(record, wallet):
    reference = _instruction(record)
    source = _pubkey(record.get("source"))
    amount = _raw(record.get("lamports"))
    if None in (reference, source, amount):
        return INVALID
    return reference, {"instruction_ref": reference, "denomination": "SOL", "direction": "IN",
                       "raw_amount": amount, "decimals": 9, "source_account": source,
                       "destination_account": wallet}


def _transient_flow(record, wallet):
    account = _pubkey(record.get("account"))
    decimals = _integer(record.get("decimals"), high=255)
    amount = _raw(record.get("net_transfer_raw"), signed=True)
    refs = record.get("transfer_refs")
    if (record.get("owner") != wallet or record.get("mint") != WSOL or decimals != 9
            or account is None or amount in (None, "0") or not isinstance(refs, list) or not refs):
        return INVALID
    transfers = []
    for ref in refs:
        reference = _instruction(ref) if isinstance(ref, dict) else None
        delta = _raw(ref.get("delta"), signed=True) if reference is not None else None
        if delta in (None, "0"):
            return INVALID
        transfers.append({"instruction_ref": reference, "delta_raw": delta})
    if (len({tuple(x["instruction_ref"]) for x in transfers}) != len(transfers)
            or sum(int(x["delta_raw"]) for x in transfers) != int(amount)):
        return INVALID
    return account, {"account": account, "mint": WSOL, "denomination": "WSOL", "decimals": 9,
                     "net_transfer_raw": amount, "transfer_refs": transfers}


def _lifecycle(record, wallet, operation):
    if record.get("owner") != wallet and (operation != "CLOSE" or record.get("destination") != wallet):
        return SKIP
    account = _pubkey(record.get("account"))
    reference = _instruction(record)
    owner = _pubkey(record.get("owner"))
    field = "mint" if operation == "CREATE_OR_INITIALIZE" else "destination"
    value = _pubkey(record.get(field))
    if None in (account, reference, owner, value):
        return INVALID
    return reference, {"operation": operation, "instruction_ref": reference, "account": account,
                       "owner": owner, field: value}


def _records(records, project, make_id, *, effect=None):
    if records is MISSING:
        return None, "NOT_RECORDED"
    if not isinstance(records, list):
        return None, "INVALID"
    entries = []
    invalid = False
    for record in records:
        result = project(record) if isinstance(record, dict) else INVALID
        if result is INVALID:
            invalid = True
        elif result is not SKIP:
            index, item = result
            item["leg_id"] = make_id(index)
            if effect is not None:
                item["instruction_effect"] = effect
            entries.append(item)
    counts = Counter(x["leg_id"] for x in entries)
    if any(n > 1 for n in counts.values()):
        entries = [x for x in entries if counts[x["leg_id"]] == 1]
        invalid = True
    return entries, "PARTIAL_INVALID_RECORDS" if invalid else "RECORDED"


def _known_legacy_wsol(version):
    # The archived v7 and v8 classifiers used SOL as a display alias for WSOL.
    return version in {"frank-v7", "frank-v8"}


def _legacy_quote(record, version, *, signed=False):
    label = record.get("asset" if signed else "quote_asset")
    asset = _pubkey(label)
    if label == "SOL" and _known_legacy_wsol(version):
        asset = WSOL
    elif label != "SOL" and asset is None:
        return None
    decimals = _integer(record.get("decimals" if signed else "quote_decimals"), high=255)
    amount = _raw(record.get("raw_delta" if signed else "quote_amount_raw"), signed=signed)
    if None in (decimals, amount):
        return None
    return {"source_asset": label, "mint": asset,
            "denomination": "LEGACY_SOL_UNRESOLVED" if asset is None else _denomination(asset),
            "decimals": decimals, "delta_raw" if signed else "raw_amount": amount}


def _trade_leg(record, wallet, signature, version, index):
    if (not isinstance(record, dict) or record.get("wallet") != wallet
            or record.get("signature") != signature):
        return None, True
    mint = _pubkey(record.get("mint"))
    side = _enum(record.get("side"), SIDES)
    leg = {"leg_index": index, "mint": mint, "side": side, "recorded_token": None,
           "recorded_primary_quote": None, "recorded_quote_legs": None}
    try:
        body = loads(record["body"]) if isinstance(record.get("body"), str) else None
    except (ValueError, TypeError, UnicodeError, RecursionError):
        body = None
    if (mint is None or side is None or not isinstance(body, dict) or body.get("mint") != mint
            or body.get("side") != side or body.get("direction") != TRADE_DIRECTIONS[side]):
        return leg, True
    amount = _raw(body.get("token_amount_raw"))
    decimals = _integer(body.get("token_decimals"), high=255)
    if None not in (amount, decimals):
        leg["recorded_token"] = {"denomination": _denomination(mint), "raw_amount": amount,
                                 "decimals": decimals, "direction": body["direction"]}
    if body.get("quote_normalization") is not None:
        return leg, True
    leg["recorded_primary_quote"] = _legacy_quote(body, version)
    quotes = body.get("quote_legs", MISSING)
    incomplete = leg["recorded_token"] is None or leg["recorded_primary_quote"] is None
    if isinstance(quotes, list):
        legs = [_legacy_quote(q, version, signed=True) if isinstance(q, dict) else None for q in quotes]
        leg["recorded_quote_legs"] = [q for q in legs if q is not None]
        incomplete = incomplete or None in legs
    elif quotes is not MISSING:
        incomplete = True
    return leg, incomplete


def build_fact(row, evidence, raw_trade_legs):
    """Project one indexed row without reclassifying it or allocating transaction costs."""
    wallet, signature = safe_id(row.get("wallet")), safe_id(row.get("sig"))
    slot = _integer(row.get("slot"))
    raw_hash = safe_id(row.get("raw_sha256"), re.compile(r"[0-9a-f]{64}"))
    version = _version(row.get("parser_version"))
    evidence, binding, evidence_hash = _bound_evidence(row, evidence, wallet, signature, slot, raw_hash, version)
    execution = _execution(evidence)
    effect = {"SUCCEEDED": "EXECUTED", "FAILED": "ATTEMPT_ONLY", "UNKNOWN": "UNRESOLVED"}[execution]

    def leg_id(kind, index):
        return digest([SCHEMA_VERSION, wallet, signature, version, kind, index])

    pre = _raw(evidence.get("pre_SOL_lamports"))
    post = _raw(evidence.get("post_SOL_lamports"))
    delta = _raw(evidence.get("SOL_delta_lamports"), signed=True)
    native_balance = {"denomination": "SOL", "decimals": 9, "pre_raw": None, "post_raw": None, "delta_raw": None}
    balance_valid = None not in (pre, post, delta) and int(post) - int(pre) == int(delta)
    if balance_valid:
        native_balance.update(pre_raw=pre, post_raw=post, delta_raw=delta)
    tx_fee = _raw(evidence.get("fee"))
    signer = _flag(evidence.get("wallet_is_signer"))
    is_payer = _flag(evidence.get("wallet_is_fee_payer"))
    if is_payer is True and signer is not True:
        is_payer = None
    wallet_fee = (tx_fee if is_payer else "0") if tx_fee is not None and is_payer is not None else None
    fee = {"denomination": "SOL", "decimals": 9, "transaction_fee_raw": tx_fee,
           "wallet_is_fee_payer": is_payer, "payer_account": wallet if is_payer else None,
           "wallet_fee_raw": wallet_fee}

    class_evidence = evidence.get("classification_evidence")
    class_evidence = class_evidence if isinstance(class_evidence, dict) else {}
    programs = evidence.get("program_ids")
    classification = {
        "indexed_class": (row["class"] if row.get("class") == "OTHER_OR_UNKNOWN" else fixed_class(row.get("class"))),
        "mechanical_class": _enum(evidence.get("mechanical_classification"), MECHANICAL_CLASSES),
        "wallet_is_signer": signer,
        "normalized_flags": {key: _flag(class_evidence.get(key)) for key in AUTHORITY_FLAGS},
        "recorded_program_ids": sorted({p for p in programs if valid_pubkey(p)}) if isinstance(programs, list) else None,
    }
    projectors = {
        "token_account_balances": ("token_balance_deltas", lambda x: _account_balance(x, wallet), None),
        "token_transfers": ("wallet_token_transfer_flows", _token_transfer, effect),
        "native_transfers": ("native_incoming_transfer_evidence", lambda x: _native_transfer(x, wallet), effect),
        "transient_token_flows": ("decoded_transient_token_flows", lambda x: _transient_flow(x, wallet), effect),
        "account_creations": ("created_token_accounts", lambda x: _lifecycle(x, wallet, "CREATE_OR_INITIALIZE"), effect),
        "account_closures": ("closed_token_accounts", lambda x: _lifecycle(x, wallet, "CLOSE"), effect),
    }
    components = {"native_balance": "RECORDED" if balance_valid else "UNRESOLVED",
                  "fee": "RECORDED" if wallet_fee is not None else "UNRESOLVED", "rent": "UNRESOLVED"}
    projected = {}
    for name, (source_key, project, instruction_effect) in projectors.items():
        projected[name], components[name] = _records(
            evidence.get(source_key, MISSING), project, lambda index: leg_id(name, index), effect=instruction_effect)

    trades = []
    incomplete_trades = False
    for index, record in enumerate(raw_trade_legs):
        leg, incomplete = _trade_leg(record, wallet, signature, version if binding == "BOUND" else None, index)
        incomplete_trades = incomplete_trades or incomplete
        if leg is not None:
            leg["leg_id"] = leg_id("trade_legs", index)
            trades.append(leg)
    components["trade_legs"] = "PARTIAL_INVALID_RECORDS" if incomplete_trades else "RECORDED"
    return {
        "schema_version": SCHEMA_VERSION, "chain": "solana", "wallet": wallet,
        "signature": signature, "slot": slot, "event_at": _integer(row.get("at")),
        "source_ref": {"scope": "LOCAL_NORMALIZED_INDEX_ONLY", "raw_transaction_sha256": raw_hash,
                       "normalized_evidence_sha256": evidence_hash, "parser_version": version},
        "classification": classification, "execution_status": execution,
        "native_balance": native_balance, "fee": fee,
        "rent": {"wallet_paid_lamports": None, "wallet_refunded_lamports": None,
                 "reason": "ACCOUNT_LAMPORT_ATTRIBUTION_NOT_RECORDED"},
        **projected, "trade_legs": trades,
        "coverage": {"normalized_evidence": binding, "components": components,
                     "native_transfer_scope": "ARCHIVED_SYSTEM_TRANSFER_INSTRUCTIONS_TO_WALLET_ONLY",
                     "token_transfer_scope": "ARCHIVED_GROSS_INSTRUCTIONS_WITH_ONE_WALLET_OWNED_ENDPOINT",
                     "trade_amount_scope": "INDEXED_LEGACY_CLASSIFIER_PROJECTION",
                     "route_cost_allocation": "UNRESOLVED", "full_chain_verified": False},
    }
