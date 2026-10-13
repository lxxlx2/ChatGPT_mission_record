# Frank / CA A04-A05 finalized-chain research evidence and Sidecar checkpoint

Date: 2026-10-13 (Asia/Bangkok)

Status: `A04_PARTIAL_CODE / A05_PARTIAL_CODE / INDEPENDENT_REVIEW_REQUIRED / NOT_DEPLOYED`

## Dependency / authority

This work is stacked on unmerged [A03 PR #43](https://github.com/lxxlx2/ChatGPT_mission_record/pull/43), which itself depends on unmerged [A02 PR #42](https://github.com/lxxlx2/ChatGPT_mission_record/pull/42). **Do not merge or deploy a descendant before upstream exact-HEAD independent review and acceptance**.

Canonical Mission rules and `FRANK_CA_MULTI_PERSON_IMPLEMENTATION_TODO_20261013.md` are unchanged. Frank V1 live signals, approved policy, `forward.sqlite`, Mission Control outbox/Gmail, LaunchAgents, UI and trading state remain unchanged.

## New A05 source-capture code

- `mission_control/wallet_chain_capture.py`: Solana finalized `getTokenAccountsByOwner` per *SPL Token* and *Token-2022* program, independent context slots, raw integer balances, token-account owner/mint/program validation, Decimal only for quantity display, active/frozen states, exact per-program completeness, missing source states. Whole wallet USD NAV, cost basis and PnL remain `null`.
- **Official Token-2022 program ID correction**: `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`. A prior local plugin call mistakenly used `TokenzQdBNbLqP5VEhdkAS6EP1vSPNN69ZSbzRfp2SN`, which the RPC rejected. Solana reference: https://www.solana-program.com/docs/token-2022 and https://solana.com/docs/rpc/http/gettokenaccountsbyowner .
- `mission_control/wallet_capture_provider.py` and upgraded `research_wallet_facts.py`: existing A03 read-only interface can consume multiple token accounts for the **same mint** and exact registered person/wallet/Slot, validates account-level sum and owner, never upgrades into current portfolio or realized PnL. An older capture is always labeled dated evidence. Source misses return `null` rather than zero.
- `scripts/frank_capture_owner_readonly.py`: **manual CLI only**, default `PLAN_ONLY`, research allowlist, explicitly bounded two finalized program queries on `--execute`, local private Sidecar output. HTTPS JSON-RPC credential URL never logged. No new scheduler, no purchased GMGN API, no production installer.

Important: Two RPC reads even at matching finalized slots are not a proven atomic account snapshot. All stored records preserve source slots; `both_programs_observed` means only both token program queries succeeded, **not** complete history, full mint supply, approved person ownership, or usable dollar NAV. An incomplete response or RPC 429 is `PARTIAL_SOURCE` with explicit missing records, never a successful empty wallet.

## New A04 economic evidence and local Sidecar code

- `mission_control/wallet_economic_ledger.py`: read-only per-transaction parsed pre/post token-balance delta, exact token account index, owner, mint, source slot/signature, fee and raw balances; dedupe one transaction across two tracked wallets. Matching peer token flows are only `POSSIBLE_PEER_FLOW_NEEDS_INSTRUCTION_PROOF`. Neither positive token delta nor internal transfer is marked active BUY/SELL or PnL.
- `mission_control/wallet_evidence_store.py`: separate append-only research SQLite, immutable document hashes and exact readback, idempotent imports, conflicts fail closed. Prohibits filenames of Frank/Mission production SQLite. Never publicly syncs raw wallet snapshots.
- Full A04 remains incomplete until finalized instruction+inner-instruction normalization, transfers/ATA lifecycle, market-execution classification, recovery cursors, and fee/routing fund legs are verified. Full A05 remains incomplete until historical 32-mint/ATA sample plus current Mac full-account capture and live source audit.

## Actual external RPC evidence this development session

Read-only connected Alchemy Solana RPC at *finalized*:
- Owner: Frank canonical Solana research address, as registered in `config/frank_local_registry.json`.
- SPL Token mint `9N6ZV2DgCBeArFckZCBzyhwF2LdfMtEvYmLJ2EY9e4Rd`: slot `456489219`, one owner-matched token account returned, raw `8140000`, decimals `6`, balance `8.14` token.
- Token-2022 mint `HfAFNsnjmbWMMRkwNeUUoHJ8V6UnUGFzkpu3Seajpump`: slot `456489222`, one owner-matched token account, raw `0`, decimals `6`. **Zero at this Mint/Slot does not prove SELL or whole-wallet zero.**
- One *unfiltered all-token-account* connector response was truncated in the connector's transport and another endpoint returned temporary RPC errors. Therefore no complete full-wallet count, atomic snapshot or comprehensive holdings are claimed. These two mint-specific reads cannot establish 32-mint/current wallet completeness.
- Never include private API keys, full raw histories or personal portfolio trajectories in this public repository.

## Tested behavior and remaining review gates

- `tests/test_frank_a04_a05_chain_capture.py`: dual programs, Token-2022 canonical address, failure as partial, duplicate ATA, wrong owner, missing sources, non-atomic slots, same-signature two wallets, passive receipts, failed transaction no balance delta, immutable Sidecar conflict.
- `tests/test_frank_a04_a05_sidecar_integration.py`: actual local Sidecar -> A03 person research query over two people/two ATA, missing/old evidence, manual plan-only no network and no file creation.
- `frank-ca-a04-a05-chain-evidence-20261013.yml`: targeted and full local-agent actual Git replay. Final exact-head CI and an independent second AI review must still be recorded. CI alone does not establish Mac/on-chain state.

## Mainline next

After independent code review, prioritize the complete A04 transaction instruction/inner-leg parser and archival cursor then A05 real owner/ATA coverage and F02 current holdings UI with explicit verified Slot/time. Keep CA unified query (C01/C02/C07/C08) as separate compatible work. **No live deployment, signal widening, Gmail change or auto trade**.
