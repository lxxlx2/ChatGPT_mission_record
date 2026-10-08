"""Read-only FOMO cross-chain evidence decoding. No legacy ledger or signal imports.

Candidate addresses are independently attributed *leads*, not verified owners.
Do not call any activity a followable BUY from a single Relay payment, a solver
receipt, or a social profile association. All outputs are OBSERVE_ONLY.
Reference: https://github.com/chainstacklabs/fomo-solana-rh-listeners
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

SOL_CASH_WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
SOL_CANDIDATE_WALLET = "A5SEXYJY4jTEi6sjMLfZs5KAP8SVFvLDPDV67GgSSZSk"
RH_CANDIDATE_WALLET = "0x696d1265c8fc4f14797abebfae3c43ebfa9d8e28"
FOMO_COSIGNER = "AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51"
SOL_RELAY_DEPOSIT = "99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2"
SOL_RELAY_SOLVER = "F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
QUOTE_MINTS = frozenset({USDC, "So11111111111111111111111111111111111111112"})
SOL_ROUTERS = frozenset({
    "DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "proVF4pMXVaYqmy4NjniPh4pqKNfMmsihgd4wdkCX3u",
})
SOL_MEMO = frozenset({
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
    "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo",
})
RH_CHAIN_ID = 4663
RH_ENTRYPOINT = "0x4337084d9e255ff0702461cf8895ce9e3b5f108"
RH_RELAY_DEPOSITORY = "0x4cd00e387622c35bddb9b4c962c136462338bc31"
RH_RELAY_ROUTER = "0xccc88a9d1b4ed6b0eaba998850414b24f1c315be"
RH_RELAY_EXECUTOR = "0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f"
RH_USDG = "0x5fc5360d0400a0fd4f2af552add042d716f1d168"
FOMO_EIP7702_CODE = "0xef0100e6cae83bde06e4c305530e199d7217f42808555b"
TOPIC_USEROP = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOPIC_DEPOSIT = "0x49fed1d0b752ce30eee63c7a81133f3363b532fec5d4d7dd1ccfd005de4555e1"
TOPIC_NATIVE_DEPOSIT = "0x8032066556caf3967d8fec4ad22a2d9e1e9576556b2903a0fcd5b1fd201e3477"
DEPOSIT_DISCRIMINATOR = bytes.fromhex("0b9c60da27a3b413")
_BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(encoded: str) -> bytes:
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("INVALID_BASE58")
    value = 0
    for char in encoded:
        try:
            digit = _BASE58.index(char)
        except ValueError as exc:
            raise ValueError("INVALID_BASE58") from exc
        value = value * 58 + digit
    zeroes = len(encoded) - len(encoded.lstrip("1"))
    return b"\0" * zeroes + (value.to_bytes((value.bit_length() + 7) // 8, "big") if value else b"")


def order_id(value: str) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
        return None
    if int(value, 16) == 0:
        return None
    return value.lower()


def _hex_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("BAD_INTEGER")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.startswith("0x") else int(value)
    raise ValueError("BAD_INTEGER")


def _keys(tx: dict) -> list[dict]:
    message = (tx.get("transaction") or {}).get("message") or {}
    result = message.get("accountKeys") or []
    if not all(isinstance(x, dict) and isinstance(x.get("pubkey"), str) for x in result):
        raise ValueError("JSON_PARSED_KEYS_REQUIRED")
    return result


def _ix_program(instruction: dict, names: list[str]) -> str | None:
    if instruction.get("programId"):
        return instruction["programId"]
    index = instruction.get("programIdIndex")
    if isinstance(index, int) and 0 <= index < len(names):
        return names[index]
    return None


def _token_deltas(tx: dict, wallet: str) -> dict[str, dict]:
    meta = tx.get("meta") or {}
    pre = meta.get("preTokenBalances")
    post = meta.get("postTokenBalances")
    if not isinstance(pre, list) or not isinstance(post, list):
        raise ValueError("TOKEN_BALANCES_UNAVAILABLE")
    totals: dict[str, dict] = defaultdict(lambda: {"raw": 0, "decimals": None})
    for sign, balances in ((-1, pre), (1, post)):
        for row in balances:
            if row.get("owner") != wallet:
                continue
            mint = row.get("mint")
            part = row.get("uiTokenAmount") or {}
            if not mint or "amount" not in part or "decimals" not in part:
                raise ValueError("TOKEN_DECIMALS_UNAVAILABLE")
            item = totals[mint]
            if item["decimals"] is not None and item["decimals"] != int(part["decimals"]):
                raise ValueError("TOKEN_DECIMALS_CONFLICT")
            item["decimals"] = int(part["decimals"])
            item["raw"] += sign * int(part["amount"])
    return {mint: row for mint, row in totals.items() if row["raw"]}


def _row(chain: str, kind: str, tx_id: str, wallet: str, *,
         order: str | None = None, asset: str | None = None,
         amount_raw: int | None = None, decimals: int | None = None,
         slot: int | None = None, at: int | None = None, reason: str = "") -> dict:
    return {
        "chain": chain, "kind": kind, "tx_id": tx_id, "wallet": wallet,
        "order_id": order, "asset": asset, "amount_raw": str(amount_raw) if amount_raw is not None else None,
        "decimals": decimals, "slot": slot, "block_time": at, "reason": reason,
        "attribution": "THIRD_PARTY_UNVERIFIED", "signal_eligible": False,
    }


def solana_events(signature: str, tx: dict, wallet: str) -> list[dict]:
    """Derive only observed legs from a parsed Solana transaction for one wallet.

    No payment, payout or single-sided token arrival is directly labelled BUY.
    Multiple wallet-owned quote/target deltas remain SWAP_CANDIDATE pending routing.
    """
    keys = _keys(tx)
    names = [k["pubkey"] for k in keys]
    if wallet not in names or (tx.get("meta") or {}).get("err") is not None:
        return []
    signed = any(k["pubkey"] == wallet and k.get("signer") is True for k in keys)
    cosigned = any(k["pubkey"] == FOMO_COSIGNER and k.get("signer") is True for k in keys)
    solver = any(k["pubkey"] == SOL_RELAY_SOLVER and k.get("signer") is True for k in keys)
    message = tx["transaction"]["message"]
    instructions = list(message.get("instructions") or [])
    for group in (tx.get("meta") or {}).get("innerInstructions") or []:
        instructions += list(group.get("instructions") or [])
    rows = []
    deltas = _token_deltas(tx, wallet)
    base = {"slot": tx.get("slot"), "at": tx.get("blockTime")}
    for ix in instructions:
        program = _ix_program(ix, names)
        if program == SOL_RELAY_DEPOSIT and signed:
            payload = ix.get("data")
            try:
                decoded = b58decode(payload)
            except (ValueError, TypeError):
                continue
            if len(decoded) < 48 or decoded[:8] != DEPOSIT_DISCRIMINATOR:
                continue
            amount = int.from_bytes(decoded[8:16], "little")
            oid = order_id("0x" + decoded[16:48].hex())
            cash = deltas.get(USDC, {}).get("raw", 0)
            if amount > 0 and oid and cash < 0:
                rows.append(_row("SOL", "RELAY_PAY", signature, wallet, order=oid,
                                 asset=USDC, amount_raw=amount, decimals=6,
                                 reason=("FOMO_COSIGNED_RELAY_DEPOSIT" if cosigned else
                                         "RELAY_DEPOSIT_NO_FOMO_COSIGNER"),
                                 **base))
        if program in SOL_MEMO and solver:
            info = ix.get("parsed")
            memo = (info if isinstance(info, str) else
                    info.get("memo", info.get("info", {}).get("memo", "")) if isinstance(info, dict) else "")
            oid = order_id(memo.strip()) if isinstance(memo, str) else None
            credit = deltas.get(USDC, {}).get("raw", 0)
            if oid and credit > 0:
                rows.append(_row("SOL", "RELAY_PAYOUT", signature, wallet, order=oid,
                                 asset=USDC, amount_raw=credit, decimals=6,
                                 reason="SOLVER_SIGNED_USDC_RECEIPT", **base))
    if not rows and signed and cosigned:
        tokens = [(mint, x) for mint, x in deltas.items() if mint not in QUOTE_MINTS]
        quotes = [(mint, x) for mint, x in deltas.items() if mint in QUOTE_MINTS]
        programs = {_ix_program(ix, names) for ix in instructions}
        if len(tokens) == 1 and len(quotes) == 1 and programs & SOL_ROUTERS:
            mint, target = tokens[0]
            quote, funding = quotes[0]
            if target["raw"] * funding["raw"] < 0:
                rows.append(_row("SOL", "SWAP_CANDIDATE", signature, wallet,
                                 asset=mint, amount_raw=abs(target["raw"]),
                                 decimals=target["decimals"],
                                 reason="COSIGNED_OPPOSING_OWNED_BALANCES_ROUTER_PRESENT", **base))
    return rows


def _word(data: str, index: int) -> str:
    raw = data.removeprefix("0x")
    part = raw[index * 64:(index + 1) * 64]
    if len(part) != 64 or not re.fullmatch("[0-9a-fA-F]{64}", part):
        raise ValueError("BAD_EVENT_DATA")
    return part


def _topic_address(topic: str) -> str:
    if not isinstance(topic, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", topic):
        raise ValueError("BAD_LOG_TOPIC")
    return "0x" + topic[-40:].lower()


def _transfer(log: dict) -> tuple[str, str, str, int] | None:
    topics = log.get("topics") or []
    if len(topics) != 3 or str(topics[0]).lower() != TOPIC_TRANSFER:
        return None
    try:
        return (str(log["address"]).lower(), _topic_address(topics[1]),
                _topic_address(topics[2]), int(_word(log["data"], 0), 16))
    except (KeyError, ValueError, TypeError):
        return None


def robinhood_user_operations(receipt: dict, wallet: str) -> list[dict]:
    """Attribute transfers ONLY inside the matching UserOperation log boundary.

    A handleOps transaction bundles unrelated users. Never assign whole receipt
    transfers to all operations or infer a buy from an unrelated executor transfer.
    """
    wallet = wallet.lower()
    logs = sorted(receipt.get("logs") or [], key=lambda log: _hex_int(log["logIndex"]))
    boundaries = [n for n, log in enumerate(logs) if
                  str(log.get("address", "")).lower() == RH_ENTRYPOINT
                  and len(log.get("topics") or []) >= 3
                  and str(log["topics"][0]).lower() == TOPIC_USEROP]
    txid = receipt.get("transactionHash") or ""
    rows = []
    for i, end in enumerate(boundaries):
        event = logs[end]
        try:
            if _topic_address(event["topics"][2]) != wallet:
                continue
            succeeded = int(_word(event["data"], 1), 16) != 0
        except (ValueError, IndexError, KeyError):
            continue
        if not succeeded:
            continue
        begin = boundaries[i-1] if i else -1
        own = logs[begin + 1:end]
        spent = []
        deposits = []
        for log in own:
            transfer = _transfer(log)
            if transfer and transfer[1] == wallet and transfer[0] != RH_USDG and transfer[3] > 0:
                spent.append(transfer)
            if str(log.get("address", "")).lower() != RH_RELAY_DEPOSITORY:
                continue
            topics = log.get("topics") or []
            try:
                topic = str(topics[0]).lower()
                if topic == TOPIC_DEPOSIT:
                    oid = order_id("0x" + _word(log["data"], 3))
                    owner = "0x" + _word(log["data"], 0)[-40:].lower()
                    raw = int(_word(log["data"], 2), 16)
                elif topic == TOPIC_NATIVE_DEPOSIT:
                    oid = order_id("0x" + _word(log["data"], 2))
                    owner = "0x" + _word(log["data"], 0)[-40:].lower()
                    raw = int(_word(log["data"], 1), 16)
                else:
                    continue
                if oid and owner == wallet and raw > 0:
                    deposits.append(oid)
            except (ValueError, TypeError, IndexError):
                continue
        if len(deposits) == 1 and len(spent) == 1:
            token, _, _, amount = spent[0]
            rows.append(_row("RH", "SELL_EXECUTED", txid + "#" + str(event["logIndex"]),
                             wallet, order=deposits[0], asset=token, amount_raw=amount,
                             reason="MATCHED_USEROP_BOUNDARY_TOKEN_OUT_RELAY_DEPOSIT"))
        elif spent or deposits:
            rows.append(_row("RH", "USEROP_AMBIGUOUS", txid + "#" + str(event["logIndex"]),
                             wallet, reason="MULTIPLE_OR_UNPAIRED_TRANSFER_OR_DEPOSIT"))
    return rows


def robinhood_buy_fills(tx: dict, receipt: dict, wallet: str) -> list[dict]:
    wallet = wallet.lower()
    if str(tx.get("to") or "").lower() != RH_RELAY_ROUTER or _hex_int(receipt.get("status", 0)) != 1:
        return []
    calldata = tx.get("input") or ""
    oid = order_id("0x" + calldata[-64:]) if isinstance(calldata, str) else None
    if not oid:
        return []
    txid = tx.get("hash") or receipt.get("transactionHash") or ""
    rows = []
    for log in receipt.get("logs") or []:
        transfer = _transfer(log)
        if transfer and transfer[1] == RH_RELAY_EXECUTOR and transfer[2] == wallet and transfer[3] > 0:
            token, _, _, amount = transfer
            rows.append(_row("RH", "BUY_FILL", txid + "#" + str(log["logIndex"]), wallet,
                             order=oid, asset=token, amount_raw=amount,
                             reason="RELAY_EXECUTOR_ERC20_TO_WALLET"))
    return rows


def pair_orders(events: list[dict]) -> list[dict]:
    """Join exact Relay IDs; preserve ambiguity, never fabricate a buy signal."""
    groups = defaultdict(list)
    for event in events:
        if event.get("order_id"):
            groups[event["order_id"]].append(event)
    result = []
    for oid, legs in sorted(groups.items()):
        pay = [x for x in legs if x["kind"] == "RELAY_PAY"]
        buy = [x for x in legs if x["kind"] == "BUY_FILL"]
        sell = [x for x in legs if x["kind"] == "SELL_EXECUTED"]
        payout = [x for x in legs if x["kind"] == "RELAY_PAYOUT"]
        if (len(pay) == len(buy) == 1 and not sell and not payout
                and pay[0].get("reason") == "FOMO_COSIGNED_RELAY_DEPOSIT"):
            kind = "PAIRED_BUY_EVIDENCE"
        elif len(sell) == len(payout) == 1 and not pay and not buy:
            kind = "PAIRED_SELL_EVIDENCE"
        else:
            kind = "INCOMPLETE_OR_AMBIGUOUS_ORDER"
        result.append({
            "order_id": oid, "kind": kind, "chains": sorted({x["chain"] for x in legs}),
            "tx_ids": sorted({x["tx_id"] for x in legs}),
            "assets": sorted({x["asset"] for x in legs if x.get("asset")}),
            "legs": len(legs), "attribution": "THIRD_PARTY_UNVERIFIED",
            "follow_signal_eligible": False,
        })
    return result
