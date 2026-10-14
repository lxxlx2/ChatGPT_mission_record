# A04 Claude third review — P2 / P4 / P5 / P6 / P7 remediation (2026-10-14)

**Scope:** child of original Draft [PR #50](https://github.com/lxxlx2/ChatGPT_mission_record/pull/50), original locked code SHA `4cef47ac63d1a0a2beb9ec7924214a127c97e32f`. Preserves upstream #48/#45/#43/#42 evidence; no production modifications or automatic trading/Gmail.

## Independent review verdict input

The user-supplied independent Claude adversarial review reported **#49 APPROVE on SHA `8898134a8a302e1187138f7fb3da87a554567e6d`**, with Low conservative Turkish dotted-I mismatch and shortened F01 Mint view, neither a release-blocker for C02. Preserve #49 as reviewed and do not alter its source. The same review returned **#50 REQUEST_CHANGES on SHA `4cef47ac...`**, with High P2/P4/P6, Medium P5/P7 and an authentic Solana raw-fixture evidence gap. This document is remediation evidence, **not** a claim that the patched SHA was independently approved.

## Fixes and explicit remaining unknowns

- **P2 High:** token balance rows with missing owners are paired before attribution. If any missing-owner row has a **nonzero balance delta**, reject normalization with `TOKEN_OWNER_UNRESOLVED_DELTA` **even when neither side names a tracked owner**. Keep the signature in `PENDING`, no `RAW_TX` / V2 view promoted as complete, and store that exact sanitized blocker in `missing_detail_counts`. Unchanged unknown-owner rows remain excluded economic legs with `TOKEN_OWNER_UNRESOLVED` coverage gaps (no invented wallet attribution).
- **P6 High:** private SQLite journal migration adds an optional `v2_error_code` to existing signature rows without rewriting raw/v1 documents. Old `CAPTURED` with missing V2 projections is **not complete**; explicit `rebuild_versioned_views` persists `V2_REBUILD_BLOCKED` or `V2_RAW_TX_MISSING` on the original signature and clears only after independently verified successful rebuild. `state()` and CLI show `v2_missing_count`, `v2_blocked_count` and persistent reason counts. Important: a source signature can remain CAPTURED (historical transaction captured) while its economic V2 view is **blocked**; overall coverage is `PARTIAL_ECONOMIC_EVIDENCE`, never AVAILABLE.
- **P4 High:** an SPL/Token-2022 parsed transfer in `meta.err != null` has `transaction_executed=false`, `executed_transfer_count=0` and per-event `FAILED_TRANSACTION_INSTRUCTION_NOT_EXECUTED`. A decoded instruction in a failed tx is **not proof of transfer execution** or BUY/SELL/PnL.
- **P5 Medium:** wallet `state()` aggregates `native_sol_unclassified_count` and `token_owner_incomplete_count` from V2 economic views, and splits source signature pagination end (`source_pagination_coverage`) from incomplete economic coverage (`coverage=PARTIAL_ECONOMIC_EVIDENCE`). No global USD NAV or lot accounting inferred from SOL deltas.
- **P7 Medium:** new live-derived evidence is written only as separate immutable kind `WALLET_TX_VIEW_V2` and identity ending `:v2`; legacy `WALLET_TX_VIEW` remains strictly archival, never modified. Versioned rebuild writes the same new kind with idempotent immutable content comparison.
- **P2/P4/P5/P6/P7 adversarial SQLite tests:** `tests/test_frank_a04_claude_third_review.py`, alongside existing 1,005-signature pagination/restart/peer-transfer suites. Ensure exact latest SHA CI success before treating code ready for re-review.

## Real Solana provider checks performed during this review

Connected, read-only Alchemy Solana mainnet finalized RPC on 2026-10-14:
- The known public Frank **research wallet** returned 25 recent finalized signature records in five short, consecutive, non-overlapping pages. In the third page, a failed transaction existed at **slot `456780885`**, signature `2JEqgbfFJhmaqkRvtDuqgEFoJWAHNZwCUp6Lx4W9NvJtvnvx6ptwhMtvXJeEroddV4dzTbRjPh4Fjy7kkgdBtQt`; its signature response had `err != null`. A direct `getTransaction` call returned the beginning of `meta.err` but the connector truncates large responses at ~8KB, so **the full parsed failed transfer instructions have not been re-read or imported as a raw fixture**.
- A sampled successful transaction at **slot `456789461`** (getTransaction signature matches the signature page), read in full at jsonParsed: **0 pre-token accounts and 1 post-token account**, with valid post owner, two outer instructions and one inner group. A second successful transaction at slot `456789273` had the same summarized pattern.
- None of the two fully parsed transactions had a missing pre/post owner field (the first had an absent *row*, not an absent owner in a present row). **Real owner-missing frequency and a reproducible failed getTransaction instruction fixture are still UNVERIFIED**. Synthetic adversarial tests deliberately reproduce the failure but are not represented as real chain observations.
- No private Alchemy key, bulk wallet trajectory or full raw histories have been committed to this public repository.

## Release gates

- Invariants: research-only Sidecar, immutable RAW_TX and legacy view, source hashes, finalized reads, no Frank V1 decision/delivery, no Gmail, no production SQLite, no Mac LaunchAgent, no automatic trade.
- **Independent another-AI review required of this new exact SHA** (not old #50), focusing on formerly silent P2/P4/P6 and projection migration, plus real provider evidence limitations.
- Combined source CI, authenticated local Mac owner/ATA/32-mint evidence and user's separate deploy authorization are still required. Every PR remains Draft/NO_MERGE/NO_DEPLOY until then.
