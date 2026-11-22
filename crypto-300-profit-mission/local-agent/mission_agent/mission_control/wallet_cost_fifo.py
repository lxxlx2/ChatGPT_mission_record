"""Exact, deterministic FIFO over immutable Frank wallet transaction facts."""
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from fractions import Fraction
import re

from ..hashing import digest
from ..meme.holder_ranks import valid_pubkey
from .wallet_facts import _denomination, _raw

ACCOUNTING_VERSION = "frank-fifo-v1"
EXCHANGE_BASIS = "VERIFIED_WALLET_BOUNDARY_SINGLE_TARGET"
HASH = re.compile(r"[0-9a-f]{64}")


def amount(value, *, signed=False):
    raw = _raw(value, signed=signed)
    return None if raw is None else int(raw)


def hex_hash(value):
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def money(totals, quantities=None):
    rows = []
    for (mint, decimals), raw in sorted(totals.items()):
        raw = Fraction(raw)
        row = {"mint": mint, "denomination": _denomination(mint), "decimals": decimals,
               "raw_numerator": str(raw.numerator), "raw_denominator": str(raw.denominator)}
        if quantities is not None:
            row["covered_quantity_raw"] = str(quantities[(mint, decimals)])
        rows.append(row)
    return rows


@dataclass
class Lot:
    id: str
    fact_id: str | None
    slot: int | None
    quantity: int
    remaining: int
    quote: tuple | None
    cost: Fraction | None
    reason: str

    def project(self):
        return {
            "lot_id": self.id, "source_fact_id": self.fact_id, "slot": self.slot,
            "quantity_raw": str(self.quantity), "remaining_quantity_raw": str(self.remaining),
            "cost_status": "KNOWN" if self.cost is not None else "UNKNOWN", "reason": self.reason,
            "costs": money({self.quote: self.cost}) if self.cost is not None else None,
            "remaining_costs": money({self.quote: self.cost * self.remaining / self.quantity})
            if self.cost is not None else None,
        }


@dataclass
class Asset:
    mint: str
    decimals: int
    lots: list = field(default_factory=list)
    fifo: deque = field(default_factory=deque)
    accounts: dict = field(default_factory=dict)
    movements: list = field(default_factory=list)
    realized: list = field(default_factory=list)
    problems: set = field(default_factory=set)
    pnl_by_quote: dict = field(default_factory=lambda: defaultdict(Fraction))
    quantity: int = 0
    sold: int = 0
    covered: int = 0
    saw_unidentified_account: bool = False

    def add(self, fact_id, slot, quantity, reason, *, quote=None, price=None, oldest=False):
        if not quantity:
            return
        key = digest([ACCOUNTING_VERSION, self.mint, fact_id, len(self.lots), reason])
        lot = Lot(key, fact_id, slot, quantity, quantity, quote, price, reason)
        self.lots.append(lot)
        (self.fifo.appendleft if oldest else self.fifo.append)(lot)
        self.quantity += quantity

    def record(self, fact_id, slot, kind, delta, reason):
        entry = {"movement_id": digest([ACCOUNTING_VERSION, self.mint, fact_id, len(self.movements), kind]),
                 "source_fact_id": fact_id, "slot": slot, "kind": kind, "delta_raw": str(delta), "reason": reason}
        self.movements.append(entry)
        return entry

    def forget_costs(self, fact_id, slot, reason):
        """Close the old lots and reintroduce the observed quantity as unknown."""
        prior_quantity = self.quantity
        for lot in self.fifo:
            lot.remaining = 0
        self.quantity = 0
        self.fifo.clear()
        self.add(fact_id, slot, prior_quantity, reason)
        self.problems.add(reason)

    def remove(self, quantity):
        remaining = quantity
        consumed = defaultdict(Fraction)
        used = Counter()
        while remaining and self.fifo:
            lot = self.fifo[0]
            used_units = min(remaining, lot.remaining)
            if lot.cost is not None:
                consumed[lot.quote] += lot.cost * used_units / lot.quantity
                used[lot.quote] += used_units
            lot.remaining -= used_units
            self.quantity -= used_units
            remaining -= used_units
            if not lot.remaining:
                self.fifo.popleft()
        return consumed, used, remaining

    def sell(self, movement, quantity, costs, used, quote=None, proceeds=None, reason=None):
        if proceeds is None:
            covered, partial = 0, None
            comparability = reason or "SALE_QUOTE_UNVERIFIED"
        else:
            covered = used[quote]
            partial = proceeds * covered / quantity - costs.get(quote, 0) if covered else None
            comparability = ("ALL_SALE_UNITS_COMPARABLE" if covered == quantity
                             else "PARTIAL_SALE_COST_COVERAGE" if covered
                             else "NO_COST_IN_SALE_QUOTE")
        pnl = money({quote: partial}) if partial is not None else None
        if partial is not None:
            self.pnl_by_quote[quote] += partial
        self.sold += quantity
        self.covered += covered
        self.realized.append({
            "movement_id": movement["movement_id"], "source_fact_id": movement["source_fact_id"],
            "slot": movement["slot"], "quantity_raw": str(quantity), "covered_quantity_raw": str(covered),
            "gross_only": True, "costs": money(costs) if costs else None,
            "proceeds": money({quote: proceeds}) if proceeds is not None else None,
            "partial_pnl": pnl, "pnl": pnl if covered == quantity else None, "reason": comparability,
        })

    def project(self, opening_known):
        known, costs, quantities = 0, defaultdict(Fraction), Counter()
        for lot in self.fifo:
            if lot.cost is not None:
                known += lot.remaining
                costs[lot.quote] += lot.cost * lot.remaining / lot.quantity
                quantities[lot.quote] += lot.remaining
        partial_pnl = money(self.pnl_by_quote) if self.pnl_by_quote else None
        return {"mint": self.mint, "decimals": self.decimals, "quantity_raw": str(self.quantity),
                "known_cost_quantity_raw": str(known), "unknown_cost_quantity_raw": str(self.quantity-known),
                "coverage": ("COMPLETE_INPUT" if opening_known and not self.problems else "PARTIAL"),
                "coverage_reasons": sorted(self.problems | (set() if opening_known else {"OPENING_WALLET_HISTORY_UNVERIFIED"})),
                "lots": [lot.project() for lot in self.lots], "movements": self.movements,
                "remaining_costs": money(costs, quantities), "realized": self.realized,
                "realized_summary": {"gross_only": True, "sold_quantity_raw": str(self.sold),
                                     "covered_quantity_raw": str(self.covered), "partial_pnl": partial_pnl,
                                     "pnl": partial_pnl if self.sold and self.sold == self.covered else None}}


def _extract_legs(fact):
    """Extract wallet quantity deltas once, skipping gross instructions and index duplicates."""
    balances = fact.get("token_account_balances")
    if not isinstance(balances, list):
        return {}, True
    by_mint = defaultdict(list)
    seen_indexes = set()
    incomplete = False
    for b in balances:
        if not isinstance(b, dict):
            incomplete = True
            continue
        mint, decimals, account_index = b.get("mint"), b.get("decimals"), b.get("account_index")
        pre, post = amount(b.get("pre_raw")), amount(b.get("post_raw"))
        if (not valid_pubkey(mint) or type(decimals) is not int or not 0 <= decimals <= 255
                or type(account_index) is not int or account_index < 0 or account_index in seen_indexes
                or pre is None or post is None or post - pre != amount(b.get("delta_raw"), signed=True)):
            incomplete = True
            continue
        seen_indexes.add(account_index)
        account = b.get("account")
        by_mint[mint].append((decimals, account if valid_pubkey(account) else None, pre, post))
    full = fact.get("coverage", {}).get("components", {}).get("token_account_balances") == "RECORDED"
    return dict(by_mint), incomplete or not full


def _verified_archive(fact):
    replay = fact.get("archived_replay")
    if not isinstance(replay, dict) or replay.get("status") != "VERIFIED":
        return None
    raw = replay.get("raw_sha256")
    archived = replay.get("fact")
    if not isinstance(archived, dict) or not hex_hash(raw):
        return None
    if (archived.get("source_ref", {}).get("raw_transaction_sha256") != raw
            or fact.get("source_ref", {}).get("raw_transaction_sha256") != raw
            or any(archived.get(k) != fact.get(k) for k in ("slot", "wallet", "signature"))
            or archived.get("coverage", {}).get("normalized_evidence") != "BOUND"):
        return None
    return archived


def _exchange(archived, mint, delta, decimals):
    exchange = archived.get("economic_exchange") if archived else None
    if (not isinstance(exchange, dict) or exchange.get("basis") != EXCHANGE_BASIS
            or exchange.get("mint") != mint or exchange.get("side") != ("BUY" if delta > 0 else "SELL")
            or amount(exchange.get("token_amount_raw")) != abs(delta) or exchange.get("token_decimals") != decimals):
        return None
    quotes = exchange.get("quotes")
    if not isinstance(quotes, list) or len(quotes) != 1 or not isinstance(quotes[0], dict):
        return None
    quote = quotes[0]
    asset, precision = quote.get("mint"), quote.get("decimals")
    value = amount(quote.get("raw_delta"), signed=True)
    if (not valid_pubkey(asset) or asset == mint or not isinstance(precision, int) or isinstance(precision, bool)
            or not 0 <= precision <= 255 or value is None or value * delta >= 0
            or quote.get("denomination") != _denomination(asset)):
        return None
    return (asset, precision), Fraction(abs(value))


def _indexed_sale(fact, mint, quantity, decimals):
    """Use a matching indexed sale as a label, never as a quote amount source."""
    trades = fact.get("trade_legs")
    if not isinstance(trades, list):
        return False
    for leg in trades:
        if not isinstance(leg, dict) or leg.get("mint") != mint:
            continue
        token = leg.get("recorded_token")
        if (isinstance(token, dict) and token.get("direction") == "SELL" and token.get("decimals") == decimals
                and amount(token.get("raw_amount")) == quantity):
            return True
    return False


def _observe_opening(asset, records, fact_id, slot, opening_known):
    """Reconcile only the token accounts named by the fixed input."""
    missing_account = any(account is None for _, account, _, _ in records)
    previous = asset.quantity
    pre_total = sum(pre for _, _, pre, _ in records)
    unexplained, opening = 0, 0
    then_unknown = missing_account or asset.saw_unidentified_account
    for _, account, pre, post in records:
        if account is None:
            continue
        earlier = asset.accounts.get(account)
        if account not in asset.accounts:
            if not then_unknown:
                opening += pre
        elif earlier is not None and earlier != pre:
            asset.problems.add("ACCOUNT_BALANCE_DISCONTINUITY")
            unexplained += pre - earlier
        asset.accounts[account] = post
    asset.saw_unidentified_account |= missing_account
    if then_unknown:
        opening = max(0, pre_total - previous - unexplained)
    if opening:
        reason = "OBSERVED_UNPRICED_OPENING_BALANCE"
        asset.add(fact_id, slot, opening, reason, oldest=True)
        asset.record(fact_id, slot, "OPENING_UNKNOWN", opening, reason)
        asset.problems.add("OPENING_ASSERTION_INCONSISTENT" if opening_known else "UNPRICED_OPENING")
    if unexplained:
        reason = "ACCOUNT_BALANCE_DISCONTINUITY"
        asset.forget_costs(fact_id, slot, reason)
        if unexplained > 0:
            asset.add(fact_id, slot, unexplained, reason)
        else:
            asset.remove(-unexplained)
        asset.record(fact_id, slot, "RECONCILIATION_UNKNOWN", unexplained, reason)


def _event(asset, fact, archived, records, fact_id, slot, opening_known):
    _observe_opening(asset, records, fact_id, slot, opening_known)
    delta = sum(post - pre for _, _, pre, post in records)
    if not delta:
        if any(pre != post for _, _, pre, post in records):
            asset.record(fact_id, slot, "WALLET_NET_ZERO", 0, "ACCOUNT_BALANCE_MOVEMENT_WITH_NO_WALLET_NET_CHANGE")
        return
    priced = _exchange(archived, asset.mint, delta, asset.decimals)
    if delta > 0:
        reason = EXCHANGE_BASIS if priced else "ACQUISITION_COST_UNVERIFIED"
        asset.add(fact_id, slot, delta, reason, **({"quote": priced[0], "price": priced[1]} if priced else {}))
        asset.record(fact_id, slot, "BUY" if priced else "INFLOW_UNKNOWN_COST", delta, reason)
        return
    quantity = -delta
    consumed, used, shortfall = asset.remove(quantity)
    if shortfall:
        asset.problems.add("UNOBSERVED_INVENTORY")
    sale = priced or _indexed_sale(fact, asset.mint, quantity, asset.decimals)
    reason = EXCHANGE_BASIS if priced else "SALE_QUOTE_UNVERIFIED" if sale else "OUTFLOW_DISPOSITION_UNVERIFIED"
    movement = asset.record(fact_id, slot, "SELL" if sale else "OUTFLOW", delta, reason)
    movement["removed_costs"] = money(consumed) if consumed else None
    movement["inventory_shortfall_raw"] = str(shortfall)
    if sale:
        asset.sell(movement, quantity, consumed, used, *(priced or (None, None)))


def _ambiguous_slot(asset, events, slot):
    touched = Counter(account for _, _, _, records in events for _, account, _, _ in records if account)
    cohort_id = digest([x[0] for x in events])
    # A repeated account may have intermediate snapshots within the slot.
    # Only singleton account rows can prove an opening balance without order.
    singletons = [b for _, _, _, rows in events for b in rows if b[1] and touched[b[1]] == 1]
    _observe_opening(asset, singletons, cohort_id, slot, False)
    for account, count in touched.items():
        if count > 1:
            asset.accounts[account] = None
    reason = "SLOT_ORDER_UNVERIFIED"
    asset.forget_costs(cohort_id, slot, reason)
    aggregate = 0
    for fact_id, fact, archived, records in events:
        delta = sum(post - pre for _, _, pre, post in records)
        aggregate += delta
        movement = asset.record(fact_id, slot, "UNORDERED_EVENT", delta, reason)
        if delta < 0 and (_exchange(archived, asset.mint, delta, asset.decimals)
                          or _indexed_sale(fact, asset.mint, -delta, asset.decimals)):
            # An exchange source can still prove total proceeds independently.
            priced = _exchange(archived, asset.mint, delta, asset.decimals)
            asset.sell(movement, -delta, {}, Counter(), *(priced or (None, None)), reason=reason)
    if aggregate > 0:
        asset.add(cohort_id, slot, aggregate, reason)
    else:
        asset.remove(-aggregate)


def _fee_summary(facts):
    sums = Counter()
    unknown = Counter()
    for fact, archived in facts:
        bound = archived or fact
        fee = amount(bound.get("fee", {}).get("wallet_fee_raw"))
        if fee is None:
            unknown["network_fee"] += 1
        else:
            sums["network_fee"] += fee
        for key in ("wallet_paid_lamports", "wallet_refunded_lamports"):
            value = amount(bound.get("rent", {}).get(key))
            if value is None:
                unknown[key] += 1
            else:
                sums[key] += value
        funding = bound.get("account_funding", {}).get("items", [])
        for item in funding:
            value = amount(item.get("amount_raw"))
            if item.get("status") == "CONFIRMED_INITIAL_FUNDING" and item.get("payer_role") == "WALLET" and value is not None:
                sums["initial_funding"] += value
        refunds = bound.get("account_close_refunds", [])
        for item in refunds:
            value = amount(item.get("amount_raw"))
            if item.get("status") == "CONFIRMED_CLOSE_REFUND" and item.get("destination_role") == "WALLET" and value is not None:
                sums["close_refund"] += value
    return {"denomination": "SOL", "decimals": 9, "attribution": "WALLET_TOTALS_SEPARATE_FROM_GROSS_PNL",
            "network_fee_lamports": str(sums["network_fee"]),
            "network_fee_unknown_transactions": unknown["network_fee"],
            "initial_funding_paid_lamports": str(sums["initial_funding"]),
            "close_refund_received_lamports": str(sums["close_refund"]),
            "rent_paid_lamports": None if unknown["wallet_paid_lamports"] else str(sums["wallet_paid_lamports"]),
            "rent_refunded_lamports": None if unknown["wallet_refunded_lamports"] else str(sums["wallet_refunded_lamports"]),
            "rent_paid_unknown_transactions": unknown["wallet_paid_lamports"],
            "rent_refunded_unknown_transactions": unknown["wallet_refunded_lamports"]}


def build_cost_ledger(rows, *, opening_known=False):
    """Build the replay of observed token inventory and conditional gross PnL.

    The replay covers frozen wallet activity. Only an independently
    archive-verified wallet-boundary exchange supplies prices. It cannot
    reconstruct unobserved accounts and intentionally excludes native SOL
    inventory. Native network fees and verified account financing remain
    wallet-level totals with explicit coverage.
    """
    facts, wallets, duplicates = {}, set(), 0
    unresolved, mints_without_order = set(), set()
    slot_events = defaultdict(lambda: defaultdict(list))
    precision_by_mint = defaultdict(set)
    for row_number, row in enumerate(rows):
        fact = row.get("transaction_fact")
        if not isinstance(fact, dict):
            unresolved.add(("NO_FACT", row_number))
            continue
        wallet, signature = fact.get("wallet"), fact.get("signature")
        if not valid_pubkey(wallet) or not isinstance(signature, str) or not signature:
            unresolved.add(("IDENTITY", row_number))
            continue
        wallets.add(wallet)
        if len(wallets) > 1:
            raise ValueError("MULTIPLE_WALLETS_IN_COST_SOURCE")
        key = (wallet, signature)
        if key in facts:
            if fact != facts[key][0]:
                raise ValueError("CONFLICTING_DUPLICATE_COST_FACT")
            duplicates += 1
            continue
        archived = _verified_archive(fact)
        bound = archived or fact
        evidence_bound = bound.get("coverage", {}).get("normalized_evidence") == "BOUND"
        state = bound.get("execution_status")
        facts[key] = (fact, archived)
        if state == "FAILED" and evidence_bound:
            continue
        if state != "SUCCEEDED" or not evidence_bound:
            unresolved.add(key)
            continue
        legs, incomplete = _extract_legs(bound)
        if incomplete:
            unresolved.add(key)
        slot = bound.get("slot")
        fact_id = fact.get("fact_id")
        fact_id = fact_id if hex_hash(fact_id) else digest([wallet, signature])
        for mint, records in legs.items():
            precision_by_mint[mint].update(record[0] for record in records)
            if type(slot) is not int or slot < 0:
                mints_without_order.add(mint)
                unresolved.add(key)
                continue
            slot_events[slot][mint].append((fact_id, fact, archived, records))
    assets, conflicts = {}, set()
    for mint, precisions in precision_by_mint.items():
        if len(precisions) == 1:
            assets[mint] = Asset(mint, next(iter(precisions)))
        else:
            conflicts.add(mint)
    for slot, cohort in sorted(slot_events.items()):
        for mint, events in cohort.items():
            if mint not in assets:
                continue
            asset = assets[mint]
            if len(events) > 1:
                # Stable output order is distinct from execution order.
                _ambiguous_slot(asset, sorted(events, key=lambda e: e[0]), slot)
                unresolved.update((event[1]["wallet"], event[1]["signature"]) for event in events)
            else:
                fact_id, fact, archived, records = events[0]
                _event(asset, fact, archived, records, fact_id, slot, opening_known)
    for mint in mints_without_order & assets.keys():
        assets[mint].forget_costs(None, None, "TRANSACTION_SLOT_UNAVAILABLE")
    complete_opening = opening_known and not unresolved and not conflicts
    return {"accounting_version": ACCOUNTING_VERSION, "scope": "FROZEN_LOCAL_OBSERVED_TOKEN_INVENTORY_ONLY",
            "opening_known": complete_opening, "input_rows": len(facts) + duplicates + sum(k[0] in ("NO_FACT", "IDENTITY") for k in unresolved),
            "duplicate_transaction_count": duplicates, "unresolved_transaction_count": len(unresolved),
            "unresolved_mints": sorted(conflicts | mints_without_order),
            "fees": _fee_summary(facts.values()),
            "assets": [asset.project(complete_opening) for _, asset in sorted(assets.items())]}
