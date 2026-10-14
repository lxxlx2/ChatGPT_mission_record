# A04 fourth Claude REQUEST_CHANGES remediation — N1, fee-only SOL and actual ATA source

Checked 2026-10-14 Asia/Bangkok. **Engineering development / independent fourth-review pending / research-only / Draft / NO_MERGE / NO_DEPLOY.**

## Provenance

- Input: independent Claude review of [Draft #51](https://github.com/lxxlx2/ChatGPT_mission_record/pull/51) at exact `c2cf581196d19e61306148cdfb85ce4857d8f02f`. Review independently confirmed previous three High fixes P2/P4/P6, V2 kind separation, migration manual replay and multiwallet RAW_TX dedupe. **Verdict remained REQUEST_CHANGES** due false-positive native SOL unknown for fee-only transactions, N1 unrelated-owner pagination stall, missing automated pre-fix SQLite migration test, and missing real raw-chain failure/owner-gap fixtures. Original #51 SHA is not modified in this child.
- Prior separately reviewed [Draft #49](https://github.com/lxxlx2/ChatGPT_mission_record/pull/49) at `8898134a8a302e1187138f7fb3da87a554567e6d` received independent Claude **APPROVE**. No C02 files touched.
- This branch is a child of #51 with isolated A04 economic classification, manual history replay path, tests/fixture. No Mac, Gmail, Frank V1 policy, production SQLite, scheduler or trade changes.

## Actual fixes and operator policy

1. **Fee-only/native SOL (Medium):** `normalize_transaction` validates aligned `meta.preBalances`/`postBalances` against parsed account keys, separately subtracts the documented fee payer `meta.fee` (index 0), and inspects parsed system value instructions from outer and inner instructions **only when relevant to the tracked wallet**. A normal token-only transaction with no non-fee tracked lamport change becomes `NO_NATIVE_SOL_FLOW_OBSERVED` / `TRACKED_BALANCES_FEE_ONLY`. Tracked non-fee change or relevant system create/transfer becomes `NATIVE_SOL_FLOW_UNCLASSIFIED`. Missing or malformed balance evidence remains `NATIVE_SOL_BALANCE_EVIDENCE_MISSING`, **not** fabricated zero and not counted as an actual observed flow. `state()` has independent `native_sol_unclassified_count` and `native_sol_balance_evidence_missing_count`; source-pagination end remains distinct from full economic closure.
2. **N1 unrelated token-owner gap availability policy (Medium):** **Fail closed is default**: a nonzero token balance with unresolved owner leaves the signature `PENDING` and the exact `TOKEN_OWNER_UNRESOLVED_DELTA` reason. To avoid blocking all older history indefinitely, only a deliberately **manual opt-in** (`--execute --continue-on-owner-gaps` in the research-only CLI, or collector's explicit boolean) allows an unresolved-owner transaction to have its authentic immutable `RAW_TX` archived while its **economic V2 view remains ABSENT**. That signature is marked source `CAPTURED` but persists `v2_error_code=TOKEN_OWNER_UNRESOLVED_DELTA`. `state()` reports `v2_missing_count`, `v2_blocked_count`, `missing_detail_counts` and `PARTIAL_ECONOMIC_EVIDENCE` even after another page and source pagination end. It **never** emits made-up BUY/SELL, position, cost/PnL or native flow. Manual operator choice is visible in CLI output. If raw source conflicts or the identity/slot differs, quarantining fails atomically.
3. **Old Sidecar migration (Medium):** automated test actually creates a prior-format SQLite `wallet_history_signature` without `v2_error_code`, with old `RAW_TX` and discredited `WALLET_TX_VIEW`, closes it and reopens through the new journal. The additive `ALTER TABLE` is idempotent and preserves raw bytes, old v1 evidence and cursor; V2 is still missing and coverage remains PARTIAL until separately repaired.
4. **Legacy artifacts (Low):** no v1 source deletion or silent revision. New journal only writes `WALLET_TX_VIEW_V2`; old v1 kind stays archival/untrusted until explicit inspected repair. No attempt to reinterpret legacy gains/PnL.

## Fully preserved real chain fixture

Unlike the prior synthetic-only regression suite, this branch contains a **complete real finalized official Solana getTransaction JSON**:

`local-agent/tests/fixtures/solana_finalized_ata_creation_slot456789461.json`.

- Source: connected read-only Alchemy Solana mainnet RPC, `getTransaction` with `encoding=jsonParsed`, `commitment=finalized`, `maxSupportedTransactionVersion=0`; raw tool response returned **complete JSON** (not a truncated 8KB payload).
- Signature `5mR2gU7XF7rSVTv4tvF17KTrBBCJoMSuVW5MreEGk3V2xwmNvXaChSJEtgWELMoTQASQgSHRybaai19DVoj1U8vL`; slot `456789461`; `meta.err=null`; Token-2022 `createIdempotent` ATA for public Frank research wallet `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`.
- Fee/rent payer is **a separate signer** `9o5pt24KgQkq9kYJEch9gKrq1rLJvZqReYFbd9Sbewh`. Frank wallet's pre/post lamports were equal, and the real associated token account was initialized with quantity zero. Parsed **inner System createAccount** paid by that external signer is present. This is exactly a case where a naive test of *any* System program instruction would wrongly claim Frank had native SOL flow. Regression asserts `NO_NATIVE_SOL_FLOW_OBSERVED` for Frank and `NATIVE_SOL_FLOW_UNCLASSIFIED` for the actual rent funder; no market BUY or PnL.
- No RPC credentials or private keys are in the public fixture. This is public blockchain transaction data. Archived exact raw receipt is usable for independent replay; source RPC and slot are documented.

**Known remaining source limits (NOT silently accepted as business complete):** a real failed finalized transaction at slot `456780885` was observed in `getSignaturesForAddress` (`meta.err` visible when querying) but its **full** parsed `getTransaction` output was truncated by the connector, so it is NOT committed as a full failed-instruction fixture. No authentic nonzero owner-missing raw receipt or ATA-close source has been independently confirmed; the user has not approved accepting that missing acceptance evidence for production. Synthetic P2/P4 tests remain labeled synthetic. Real source coverage and full 32-Mint/ATA historical reconciliation remain open.

## Acceptance/tests and release

- Targeted `tests/test_frank_a04_claude_fourth_review.py`: fee-only negative test, native nonfee positive test, relevant system instruction, missing balance gap, default N1 block vs explicit quarantined continuation through older page, old Sidecar `ALTER TABLE` migration, full real ATA fixture replay.
- Workflow `.github/workflows/frank-ca-a04-claude-fourth-review-20261014.yml` runs focused A04 suites, pyflakes/compileall/Node and full local-agent real Git. Record **exact final HEAD** after any documentation/code updates; don't reuse earlier CI.
- Follow with disposable combined A04+CA/F01 runner and independent other-AI review of exact final SHA. Only then consider real Mac source/QA and explicit user deployment authorization. Keep all parent PRs Draft and NO_DEPLOY.
