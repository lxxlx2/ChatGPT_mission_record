"""A03 read-only person-scoped wallet research; no production authority.

This reader only consumes explicit wallet facts from an injected provider. It
does not scan arbitrary people, read Frank production state, create decisions,
send notifications, price assets, or infer beneficial ownership. A04 will
supply a reviewed normalized sidecar evidence provider.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from .person_registry import PersonRegistry, WalletBinding, _solana_pubkey_32_bytes


class WalletFactsProvider(Protocol):
    """Contract for point-in-time observations from a separate read-only source.

    Return None when a wallet/mint has not been covered. Never return 0 for an
    unavailable source. A valid response is an archived observation only.
    """

    def observed_mint(
        self, *, chain: str, wallet: str, mint: str, as_of_slot: int
    ) -> dict | None: ...


def _snapshot(fact: dict | None, *, binding: WalletBinding, mint: str,
              as_of_slot: int) -> dict:
    if fact is None:
        return {
            "status": "NOT_CAPTURED",
            "balance": None,
            "missing": ["WALLET_MINT_NOT_COVERED"],
            "chain_complete": False,
            "current_balance_verified": False,
        }
    if not isinstance(fact, dict):
        raise ValueError("WALLET_FACT_INVALID")
    # A source must identify its exact wallet and mint, so one person's
    # records can never be relabeled as another person's inventory.
    if any((
        fact.get("chain") != binding.chain,
        fact.get("wallet") != binding.address,
        fact.get("mint") != mint,
        fact.get("commitment") != "finalized",
    )):
        raise ValueError("WALLET_FACT_IDENTITY_OR_FINALITY_MISMATCH")
    slot = fact.get("slot")
    if type(slot) is not int or not binding.valid_from_slot <= slot <= as_of_slot:
        raise ValueError("WALLET_FACT_OUTSIDE_BINDING_SLOT")
    if binding.valid_to_slot is not None and slot >= binding.valid_to_slot:
        raise ValueError("WALLET_FACT_OUTSIDE_BINDING_SLOT")
    raw = fact.get("raw_amount")
    decimals = fact.get("decimals")
    if (not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal()
            or type(decimals) is not int or not 0 <= decimals <= 18):
        raise ValueError("WALLET_FACT_UNITS_INVALID")
    source = fact.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("WALLET_FACT_SOURCE_MISSING")
    account = fact.get("token_account")
    # An aggregate wallet/mint balance is meaningless without token accounts
    # and an owner/ATA coverage explanation. A04/A05 own proof validation.
    if not isinstance(account, str) or not _solana_pubkey_32_bytes(account):
        raise ValueError("WALLET_FACT_TOKEN_ACCOUNT_INVALID")
    return {
        "status": "DATED_SOURCE_ASSERTION_NOT_WALLET_COMPLETENESS",
        "balance": {
            "raw_amount": raw,
            "decimals": decimals,
            "quantity": str(Decimal(raw) / (Decimal(10) ** decimals)),
            "slot": slot,
            "token_account": account,
            "source": source,
            "commitment": "finalized",
        },
        "missing": ["ALL_OWNED_TOKEN_ACCOUNTS_UNVERIFIED",
                    "BENEFICIAL_OWNERSHIP_UNVERIFIED",
                    "COST_BASIS_UNVERIFIED"],
        "chain_complete": False,
        "current_balance_verified": False,
    }


class PersonResearchReader:
    """Allowlisted research identity selection, with immutable Frank V1 isolation."""

    def __init__(self, registry: PersonRegistry, facts: WalletFactsProvider):
        self.registry = registry
        self.facts = facts

    def people(self) -> list[dict]:
        return [{
            "person_id": p.person_id,
            "display_name": p.display_name,
            "research_only": True,
            "signal_allowed": False,
            "delivery_allowed": False,
            "wallet_binding_count": len(p.wallets),
        } for p in self.registry.research_people()]

    def mint_observations(self, *, person_id: str, mint: str,
                          as_of_slot: int) -> dict:
        # Strict slot and mint are required. No latest/real-time assertion is
        # possible from the A03 research contract.
        if type(as_of_slot) is not int or as_of_slot < 0:
            raise ValueError("INVALID_RESEARCH_AS_OF_SLOT")
        if not isinstance(mint, str) or not _solana_pubkey_32_bytes(mint):
            raise ValueError("INVALID_RESEARCH_MINT")
        p = self.registry.person(person_id)
        bindings = self.registry.wallets_for(person_id, slot=as_of_slot)
        rows = []
        for binding in bindings:
            source = self.facts.observed_mint(
                chain=binding.chain, wallet=binding.address,
                mint=mint, as_of_slot=as_of_slot,
            )
            record = _snapshot(source, binding=binding, mint=mint,
                               as_of_slot=as_of_slot)
            rows.append({
                "wallet_id": binding.wallet_id,
                "wallet": binding.address,
                "chain": binding.chain,
                "role": binding.role,
                "binding_valid_from_slot": binding.valid_from_slot,
                "binding_valid_to_slot": binding.valid_to_slot,
                "binding_evidence_state": binding.evidence_state,
                "binding_approval_status": binding.approval_status,
                "inventory": record,
            })
        return {
            "schema_version": 1,
            "person_id": p.person_id,
            "mint": mint,
            "as_of_slot": as_of_slot,
            "research_only": True,
            "status": "PARTIAL_RESEARCH_EVIDENCE" if rows else "NO_BOUND_WALLETS_AT_SLOT",
            "wallets": rows,
            "observed_wallets": sum(x["inventory"]["balance"] is not None for x in rows),
            "queried_wallets": len(rows),
            # A03 forbids person portfolio aggregation until verified ownership,
            # full ATA coverage, cost lots and transfer dedup exist in A04–A06.
            "person_balance": None,
            "person_pnl_usd": None,
            "chain_complete": False,
            "portfolio_verified": False,
            "signal_allowed": False,
            "delivery_allowed": False,
            "trading_allowed": False,
        }
