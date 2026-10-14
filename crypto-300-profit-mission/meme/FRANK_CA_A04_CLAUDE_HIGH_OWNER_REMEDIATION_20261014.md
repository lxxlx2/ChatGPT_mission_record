# Claude review remediation — A04 owner gaps and source replay

Date: 2026-10-14 Asia/Bangkok
Status: `CODE_SUBMITTED / EXACT_HEAD_TEST_AND_REVIEW_PENDING / NO_MERGE / NO_DEPLOY`

Review source: user-provided independent Claude report, conclusions **REQUEST_CHANGES** on PR #49 `9c16829e` and A04 PR #48 `26c40912` stacked on #45 `92fbacbc`. This fixes the A04 findings on a **new child branch of #48**, preserving reviewed parent SHAs, while C02 is fixed on its existing review-remediation child PR #49.

## A04 findings handled

- **High E1:** `wallet_economic_ledger._balance_map()` previously discarded rows with owner missing *before* pairing pre/post balances, creating false OUT or IN when amount was unchanged. New normalization **keeps all parsed rows**, computes raw change first, then attributes to tracked owners. Single-sided missing owner with unchanged amount becomes a `TOKEN_OWNER_UNRESOLVED` coverage gap with no economic leg. Unresolved owner with a **nonzero change connected to a tracked wallet** throws `TOKEN_OWNER_UNRESOLVED_DELTA`: the entire RPC-derived transaction remains pending and cannot contaminate the immutable Sidecar. Both owners unknown produces an explicit gap and no attributed leg. Normal provenance remains exact owner/mint/quantity.
- **Medium SOL:** all transactions explicitly mark `native_sol_coverage_status=NATIVE_SOL_FLOW_UNCLASSIFIED`, `native_sol_flow_lamports=null`. Token deltas do not establish native SOL funding. No fictitious zero cost or native profit.
- **Medium integration:** history capture now invokes `wallet_instruction_evidence.transfer_instructions()` (outer and inner parsed SPL/Token-2022) as part of its **versioned derived wallet view**. It remains clear that `POSSIBLE_PEER_FLOW` is not proof of a market trade or same-person control. `active_market_buys_confirmed=0` and PnL `null` unchanged.
- **Medium immutable contamination:** raw source `RAW_TX` remains immutable. New normalized view is tagged `schema_version=2`, `normalizer_version=SOL_TOKEN_VIEW_V2`, plus `research_wallet`. `HistoryJournal.rebuild_versioned_views(wallet)` replays archived `RAW_TX` into separate immutable kind `WALLET_TX_VIEW_V2`, never alters original `WALLET_TX_VIEW`. Explicit manual invocation and idempotent write, conflicts block. Invalid source cannot be upgraded.
- **Low label:** `UNKNOWN_TOKEN_DELTA_NOT_MARKET_TRADE` incorrectly asserted it was not a market trade; changed to `UNVERIFIED_TOKEN_DELTA`. Existing assertion migrated rather than deleted.
- **Low wallet binding:** `HistoryJournal.record_transaction` requires the derived view's `research_wallet` match the signature's wallet before committing.
- **Low pending / concurrency:** continued fail-closed blocking for a persistently unavailable first pending transaction; `record_page` pretransaction cursor read is a recorded multiwriter gap. No new locks, no autonomous retries introduced solely for edge cases.

## Reproducibility and acceptance

- `tests/test_frank_a04_claude_owner_review.py` includes Claude E1a, E1b, E1c, unresolved nonzero, native SOL, wallet identity mismatch and immutable v2 reconstruction, plus parsed transfer integration.
- Branch-specific Actions workflow: `frank-ca-a04-claude-owner-review-20261014.yml` runs targeted A04 A05 plus full local-agent real Git regression.
- No new RPC credentials or raw private transactions in Git. No unattended jobs or production state change. This remains *research-only*: still not full ATA/32-mint coverage, market BUY/SELL proof, complete SOL economic attribution, current Mac holdings or PnL.
- Need exact-HEAD CI, independent **another-AI review on fixed SHA**, later full combined A02→A03→A04→F01→CA integrity testing and separately authorized Mac read-only acceptance. No PR merge or deploy until reviewed and approved.

## C02 separate review response

The same Claude report found a genuine Unicode `ß -> ss` silent conflict collapse in PR #49 using `casefold()`. C02 remediation is isolated to that PR: comparison uses `lower()`, source mismatch and authority divergence regression, verified 32-byte base58 CA validation before dashboard preview; not part of this A04 branch. Original PR #47 unchanged.

This checkpoint is an engineering trace, not a new claim of complete business acceptance.
