"""A05 archived capture provider for A03 PersonResearchReader.

Never interprets a missing record as a zero current balance. Consumes a
manually imported sidecar only, so a request cannot trigger background RPC.
"""
from __future__ import annotations

from .wallet_evidence_store import WalletEvidenceStore


class CapturedWalletFactsProvider:
    def __init__(self, store: WalletEvidenceStore):
        self.store = store

    def observed_mint(self, *, chain: str, wallet: str, mint: str,
                      as_of_slot: int) -> dict | None:
        if chain != "solana":
            return None
        for document in self.store.read_wallet_captures(wallet, limit=100):
            if document.get("wallet") != wallet or document.get("network") != "solana-mainnet":
                continue
            max_slot = document.get("slot_max")
            if type(max_slot) is not int or max_slot > as_of_slot:
                continue
            for row in document.get("mints", []):
                if row.get("mint") != mint:
                    continue
                return {
                    "chain": chain, "wallet": wallet, "mint": mint,
                    "slot": row["slot_max"], "slot_min": row["slot_min"],
                    "slot_max": row["slot_max"], "commitment": "finalized",
                    "raw_amount": row["raw_amount_observed_sum"],
                    "decimals": row["decimals"],
                    "token_accounts": row["token_accounts"],
                    "source": "LOCAL_IMPORTED_SOLANA_OWNER_RPC_ARCHIVE",
                    "source_capture_sha256": document["capture_sha256"],
                    "programs_observed": bool(document["both_programs_observed"]),
                    "source_non_atomic": True,
                    "usd_value": None, "pnl_usd": None,
                }
        return None
