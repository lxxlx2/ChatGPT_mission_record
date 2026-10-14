# A05-R2 frozen historical 32 Mint offline reconciliation implementation

Date: 2026-10-14 Asia/Bangkok
Status: `USER_MAC_DUAL_PROGRAM_CLI_REPLAY_REPORTED / REPO_HISTORICAL_32_SOURCE_VERIFIED / OFFLINE_R2_CODE_SUBMITTED / REVIEW_PENDING / NO_MERGE / NO_DEPLOY`.

## A05-R1 Mac receipt evidence reported by user

The user executed reviewed PR #60 fixed `e4529ba7069e5499d12323a7160ceac08c481fae` from a separate nonproduction checkout, confirmed `PLAN_ONLY`, and ran explicit `--execute`. Result (user-provided Mac stdout, NOT independently read from its local raw files here):

- `status=FULL_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED`
- Frank registry wallet `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`
- `capture_sha256=a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261`
- `slot_min=456895319, slot_max=456895320`; two non-atomic finalized RPC program reads
- `token_account_count=3233`, `mint_count_observed=3233`; these are all currently open owner Token Accounts/Mints observed by the query, **NOT the Frank follow/trade target roster**, and spam/passive assets must not be promoted to actionable positions.
- Local evidence bundle path (private source): `$HOME/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6`.
- `research_sidecar_imported=null`, `writes_production_sqlite=false` reported. No actual raw JSON files uploaded to ChatGPT or Git. Remote verification of two original byte files and their claimed hash remains **not independently performed**. No profit, sale, USD amount or control attribution proven.

## Frozen factual historical roster discovered in Mission

Existing tracked file: `crypto-300-profit-mission/meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json`.

- Actual Git blob SHA: **`c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1`**. Historical `records=32`, distinct Mints. Its stated origin is `EXACT_32_MINTS_FROM_MAC_D0_LOCAL_TRADE_AND_MODEL_UNION`; dates 2026-10-11; each Mint originally read with finalized **per-Mint** query at distinct slots `[455426889,455430371]`. Historical account observation **10 nonzero, 22 zero**, not the current 2026-10-14 inventory.
- Separate immutable `frank-v2-33-mint-mac-ledger-gap-analysis-2026-10-11.json` identifies subsequent distinct 33rd Mint `2j5SaS7xy776qCBpyPQbZjyQSAtKiFgrwjfErthnW2ZM`. Do not alter the original 32 array to produce a false roster; reconcile that new observation separately in follow-on scope.
- This prior record does not claim closed ATA enumeration, full wallet history, true person control, current USD value or verified token cost/PnL.

## New child-stage implementation

Base: exact externally independently reviewed PR #60 SHA `e4529ba7069e5499d12323a7160ceac08c481fae`. This child adds **only a manual, zero-network, nonproduction offline projection** plus tests/workflow; does not modify or redeploy the approved transport/normalizer/Sidecar.

- `scripts/frank_reconcile_frozen32_offline.py`: immutable Git blob pin for original 32 snapshot, registered Frank wallet match, actual complete source replay via `replay_owner_full_receipts`; validates whole current inventory internal counts and projects only 32 exact Mints.
- Distinguishes current `OPEN_ACCOUNT_NONZERO` / `OPEN_ACCOUNT_ZERO` / `NO_OPEN_ACCOUNT_OBSERVED`; the last remains **null observed amount**, never fabricated market SELL/zero historical position. Multiple live token accounts (not only canonical ATA) are preserved with account pubkey, program, raw balance, decimals and Slot; old vs new balance comparison explicitly different time slots.
- CLI prints a bounded aggregate, optional explicit `--output` writes complete 32-only research JSON under restricted local user path with `0600` permissions. No default writes, no network, no production SQLite, no email/trade/price/PnL. Private 3,233-account raw bundle never goes to public Git.
- Focused synthetic source tests and actual original Git 32 roster immutability test validate all 32 and partial failures. CI and independent another-AI Review on final exact SHA required **before marking A05-R2 code accepted**. Real Mac output count and 32-mint matched balances require an actual manual invocation from an approved checkout; the created CI fixtures are not that proof.

## Product milestone chain

`A05-R1 reviewed code + USER_MAC_FULL_SOURCE_CLI_OUTPUT` → `A05-R2 REAL_32_RECONCILIATION_PENDING` → `F02-R1 read-only source-backed positions` → `Dashboard` → `Mac isolated QA` → independent cross-module review → final whole-system independent review.

All existing production Frank V1, Gmail, LaunchAgents and protected SQLite untouched. `NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PROD_SQLITE / NO_NEW_AUTOMATION`.
