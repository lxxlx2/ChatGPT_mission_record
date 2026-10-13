# PR #39: Mac read-only predeploy evidence (2026-10-13, Asia/Bangkok)

**Status:** `PASS_READ_ONLY_PREDEPLOY`. **Not a production deployment.**

Provenance: an operator-generated JSON file, `frank-pr39-preflight-20261013.json`, uploaded after executing the read-only Mac inspection. This file contains only aggregate counts and source verification booleans; neither production DB nor Gmail records were imported to Git.

## Source integrity and release identity

- Prepared release branch HEAD: `2c1afea6d74126aa6df8284442ecdc8ef6f08a2c`
- Independently reviewed, unchanged product pin: `bda7ef0dfd89e6c1b11f9020163bf754bed5ae74`
- `reviewed_product_unchanged=true`
- `worktree_clean=true`
- `merge_performed=false`
- `mutated_production=false`
- `restarted_services=false`
- `sent_gmail=false`

## Actual Mac SQLite measurements

| Probe | Value |
| --- | ---: |
| Frank indexed `v1_states` | 26 |
| Frank states with at least one BUY | 26 |
| Last-BUY `USDC_DIRECT_NUMERIC` | 26 |
| Last-BUY missing `amount_predicate` | 0 |
| Last-BUY legacy direct-USDC missing predicate | 0 |
| Last-BUY `UNDETERMINED` | 0 |
| Control decision history rows | 35 |
| Historical LIVE Gmail rows | 17 |
| LIVE Gmail `SENT_VERIFIED` | 2 |
| LIVE Gmail `MANUAL_REVIEW` | 15 |
| LIVE Gmail actively queued/in-flight | 0 |
| Local desktop `COMMAND_ACCEPTED` | 17 |
| Local unresolved alerts | 0 |
| DRY_RUN_AUDIT Gmail/local rows | 1 / 1 |
| `local_delivery_presentation` | NOT_YET_CREATED |
| `PRAGMA quick_check` and foreign key validation | ok |

**N1 actual-data coverage: PASS.** The current 26 last-BUY events each supply the direct-USDC predicate. This is a statement about the latest BUY in each of the 26 indexed states, **not** an exhaustive claim that every historical transaction has correct quote evidence.

**Queue gate: PASS at this observation time.** There are no in-flight Gmail or local desktop rows. The 15 `MANUAL_REVIEW` rows are terminal audit records; the aggregate-only JSON contains no `last_error` values, so **their specific reasons are not verified** by this evidence. Do not automatically delete, reclassify, or resend them.

**Additive table:** `NOT_YET_CREATED` is expected on the old runtime. This report **does not** establish that the new schema has already been migrated.

## Merge and Mac release boundaries

- GitHub verified original independently approved product CI at `bda7ef0d`: run `38289617455`, 50 targeted and 1,277 complete tests passed.
- The read-only-preflight-repair operations workflow run `38293197931` passed: 50 targeted and 1,289 complete tests.
- Current PR #39 is still DRAFT/unmerged at time of evidence recording; production Loop and Dashboard were **not** switched to PR #39.
- This dated observation cannot substitute for a **fresh** active-queue and PID/runner check immediately before a future authorized source switch.
- A controlled release would need private SQLite backup+verification, protected-file hashes, approved policy pin, additive-schema acceptance, immutable Gmail/local queue checks and rollback, followed by actual post-switch Mac evidence.
- **No production auto-trading**. `PRODUCTION_TRADING = NO_GO`.

This report is a repository record of user-provided local measurements, not a claim of remote access to the user's Mac.
