"""Manual A04 finalized RPC history replay to a private research-only sidecar.

Without --execute, no RPC call, no sqlite file is opened or created. Never
touch production Frank V1, Gmail or macOS schedules. RPC credentials (including
path/query) are never emitted in output or errors.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import (
    HistoryJournal, WalletHistoryCollector,
)


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = (Path.home() / "Library" / "Application Support" / "FrankMeme" /
           "research-wallet-evidence.sqlite")
REGISTRY = ROOT / "config/frank_local_registry.json"
MAX_REPLY_BYTES = 12_000_000


def rpc_reader(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("HTTPS_RPC_URL_REQUIRED")
    counter = 0

    def rpc(method, params):
        nonlocal counter
        if method not in {"getSignaturesForAddress", "getTransaction"}:
            raise ValueError("RESEARCH_RPC_METHOD_NOT_ALLOWED")
        counter += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": counter,
                              "method": method, "params": params}).encode("utf-8")
        request = Request(url, payload, {"Content-Type": "application/json"},
                          method="POST")
        try:
            with urlopen(request, timeout=18) as response:
                content = response.read(MAX_REPLY_BYTES + 1)
        except HTTPError as exc:
            if exc.code in {429, 403}:
                return {"error": {"code": exc.code}}
            raise RuntimeError("RPC_HTTP_UNAVAILABLE") from None
        except (URLError, OSError, TimeoutError):
            raise RuntimeError("RPC_CONNECTION_UNAVAILABLE") from None
        if len(content) > MAX_REPLY_BYTES:
            raise RuntimeError("RPC_RESPONSE_TOO_LARGE")
        try:
            data = json.loads(content)
        except (ValueError, TypeError):
            raise RuntimeError("RPC_JSON_INVALID") from None
        if not isinstance(data, dict) or data.get("id") != counter:
            raise RuntimeError("RPC_REQUEST_ID_MISMATCH")
        return data
    return rpc


def main(argv=None):
    parser = argparse.ArgumentParser(description="A04 bounded manual finalized history capture")
    parser.add_argument("--person-id", default="frank")
    parser.add_argument("--wallet", default=None)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--sidecar", type=Path, default=SIDECAR)
    parser.add_argument("--rpc-url", default=os.environ.get(
        "FRANK_RESEARCH_SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--tx-budget", type=int, default=100)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--continue-on-owner-gaps", action="store_true",
        help="Opt-in: archive immutable RAW_TX of unresolved-owner events, "
             "record blocked economic V2, and continue older historical pages",
    )
    args = parser.parse_args(argv)
    registry = PersonRegistry.from_file(args.registry)
    choices = [binding for binding in registry.wallets_for(args.person_id)
               if binding.chain == "solana" and
               (args.wallet is None or binding.address == args.wallet)]
    if len(choices) != 1:
        raise ValueError("SELECT_ONE_REGISTERED_RESEARCH_WALLET")
    wallet = choices[0].address
    if not (1 <= args.page_size <= 1000 and 0 <= args.max_pages <= 20
            and 0 <= args.tx_budget <= 2000):
        raise ValueError("REPLAY_BUDGET_OUT_OF_RANGE")
    if not args.execute:
        print(json.dumps({
            "status": "PLAN_ONLY", "person_id": args.person_id,
            "wallet": wallet, "page_size": args.page_size,
            "max_pages": args.max_pages, "tx_budget": args.tx_budget,
            "sidecar": str(args.sidecar),
            "continue_on_owner_gaps": args.continue_on_owner_gaps,
            "network_invoked": False,
            "production_written": False, "notifications_enabled": False,
        }, sort_keys=True))
        return 0
    rpc = rpc_reader(args.rpc_url)
    store = WalletEvidenceStore(args.sidecar)
    try:
        reader = WalletHistoryCollector(
            HistoryJournal(store), rpc, wallet=wallet,
            page_size=args.page_size,
            continue_on_owner_gaps=args.continue_on_owner_gaps,
        )
        result = reader.collect(max_pages=args.max_pages, tx_budget=args.tx_budget)
    finally:
        store.close()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, PermissionError):
        print("HISTORY_RESEARCH_FAILED", file=sys.stderr)
        sys.exit(1)
