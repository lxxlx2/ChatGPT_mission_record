# A04 immutable V2 -> V3 migration — independent Claude P2 defect correction

Date: 2026-10-14 (Asia/Bangkok)
Status: `CODE_IMPLEMENTED / CROSS_SHA_MIGRATION_TESTED / INDEPENDENT_REREVIEW_REQUIRED / MAC_NOT_DEPLOYED`

## Source review and preserved parent

- Independent Claude review submitted by user examined exact [Draft PR #52](https://github.com/lxxlx2/ChatGPT_mission_record/pull/52) HEAD `e547203c6e4b00c80372c125785c9feb72fb8e87` against its parent `c2cf581196d19e61306148cdfb85ce4857d8f02f` and returned **REQUEST_CHANGES** for one **P2 backward-compatibility defect**. The parent implementation fixes fee-only native SOL, N1 manual opt-in raw-only owner-gap continuation, real Token-2022 ATA funding attribution and old V1 schema migration; that review did not find defects in those areas.
- Defect: new `native_sol_coverage_status` behavior and `native_sol_observation_reason` changed source-derived content but continued to write **the same** `normalizer_version=SOL_TOKEN_VIEW_V2`, immutable `WALLET_TX_VIEW_V2`, and `:v2` identity as previously archived economic views. Rebuilding from unchanged RAW_TX compares the previous V2 content SHA and fails with `DERIVED_V2_EVIDENCE_CONFLICT`, persisted `V2_REBUILD_BLOCKED`. That is a versioning correctness flaw, not a bad RPC receipt.
- This remediation uses a new isolated child branch of #52. Parent #52 and the independently APPROVED C02 #49 `8898134a` keep their exact original SHAs.

## Versioned source model

| Evidence | Historical | Current algorithm |
|---|---|---|
| Normalizer | `SOL_TOKEN_VIEW_V2` | `SOL_TOKEN_VIEW_V3` |
| schema_version | `2` | `3` |
| Kind | `WALLET_TX_VIEW_V2` | `WALLET_TX_VIEW_V3` |
| Identity | `<wallet>:<signature>:<slot>:v2` | `<wallet>:<signature>:<slot>:v3` |
| Persistent repair reason | `v2_error_code` (legacy retained) | `v3_error_code` (new migration) |
| Coverage | old v2 irrelevant to v3 | `v3_missing_count`, `v3_blocked_count`, verified V3 token-owner and native-SOL gaps |

Immutable `RAW_TX`, `WALLET_TX_VIEW` (old V1) and `WALLET_TX_VIEW_V2` remain unchanged and individually queryable. Historical V2 error codes also remain stored, reported separately as `legacy_v2_error_count`, and are never silently recast as V3 success. Captured source signatures without current V3 views are `PARTIAL_ECONOMIC_EVIDENCE`, even if old V2 reported AVAILABLE. Explicit `HistoryJournal.rebuild_versioned_views` deterministically regenerates V3 from the archived raw transaction, yields `new=1` once and `already_present=1` on identical retry; a source/data error remains a persisted V3 blocker.

New wallet ingestion writes V3 only and checks the projected schema+normalizer version to reject accidental V2 injection. Manual N1 owner quarantine still archives raw only, persists **V3** incomplete economic coverage and never claims BUY/SELL/PnL. No background RPC polls, production databases, strategies or Mac launchd changes.

## Real frozen-code cross-SHA migration evidence

The GitHub workflow `.github/workflows/frank-ca-a04-v3-cross-sha-20261014.yml` performs a **true two-code-version** test in isolated runner worktrees:

1. Checkout exact PR #51 `c2cf581196d19e61306148cdfb85ce4857d8f02f` and run **its actual old module** (path checked) to create a SQLite RAW_TX + V2 wallet view: `native_sol_coverage_status=NATIVE_SOL_FLOW_UNCLASSIFIED` even for fee-only token trade.
2. Checkout exact PR #52 `e547203c6e4b00c80372c125785c9feb72fb8e87` and similarly create a second genuine SQLite RAW_TX + V2 view, but with changed `native_sol_coverage_status=NO_NATIVE_SOL_FLOW_OBSERVED` while **still** identified as V2.
3. For both original Sidecars, reopen with this corrected code, verify schema migration adds `v3_error_code`, source pagination is preserved, prior V2 is audited but does not satisfy current coverage, then explicitly rebuild from archived immutable RAW_TX into V3. Verify `new=1`, repeat `already_present=1`, both blocked=0, previous V2/RAW_TX hashes and exact payload bytes and original pagination cursor identical, fee-only native SOL classified accurately, V3 status transitions from PARTIAL to AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN (still not genesis-proven).
4. Run existing red/green A04 history, archived evidence, N1, token owner gaps and actual finalized Token-2022 ATA creation fixture regression plus full local-agent suite; run separate ephemeral main + A04 + reviewed C02 + F01 full-source integration. No pushes or production action from workflow.

Local synthetic V2 test exists in `tests/test_frank_a04_v2_v3_upgrade.py`, but the **stronger independent evidence** is this immutable PR #51/PR #52 cross-SHA worktree execution, not a hand-built old payload.

## Out-of-scope business acceptance (unchanged)

- Full failed Solana `getTransaction` with parsed instructions and genuinely missing-owner nonzero delta, plus ATA close raw receipt, are not yet independently saved as complete fixtures.
- Only the complete public finalized ATA **creation** transaction at slot `456789461` is saved and independently replayable.
- Current Mac actual complete 32-mint/ATA and historical funding/trade/PnL remain incomplete. Study coverage never authorizes Frank V1 buy alerts or production trading.
- Require another AI **exact-current-HEAD** independent review and combined CI before any Mac read-only controlled acceptance, then separate user approval for deploying.

**No main merge, no PR merge, no real transactions, no production SQLite/Gmail/LaunchAgent writes.**
