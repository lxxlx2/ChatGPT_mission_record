# Frank A05/F02 independent Claude P2: slotless two-program source authentication

Date: 2026-10-14 Asia/Bangkok
Scope: research-only `ACCOUNT_CAPTURE` latest source projection, **not** real Frank F02 current portfolio or trading.
Parent: [Draft PR #57](https://github.com/lxxlx2/ChatGPT_mission_record/pull/57), independently reviewed exact code `b70245f189a4940eab62288e2da23551f9e31129`, external Claude verdict **REQUEST_CHANGES** (1 P2).
Isolated correction: [Draft PR #58](https://github.com/lxxlx2/ChatGPT_mission_record/pull/58), **new independent exact-head review pending**.

## Original reviewer evidence

Claude independently confirmed both prior #57 P2 fixes: max finalized Slot selection over 601 captures across three SQLite fetch batches, and actual valid older-failure/newer-success plus newer-failure/older-success temporal behavior. It then created a valid capture hash with **two identical SPL Token unavailable events** in `missing`, neither Token-2022 failure recorded. Old projection required `len(missing)==2` without proving distinct program identities, returned `SOURCE_ATTEMPT_FAILED_NO_SLOT` and treated a fabricated double-program failure as real. Hash-valid is not semantically valid.

## New source-identity contract

The no-slot branch now requires the exact `capture_owner()` double-unavailable shape:

- Both `slot_min` and `slot_max` truly null; `status=PARTIAL_SOURCE`, `both_programs_observed=false`, empty `program_coverage`.
- Exactly two `missing` objects, each with precisely `program_id`, `reason` and `error_type`. Program IDs are **both distinct official program addresses** from `wallet_chain_capture.PROGRAMS`: SPL Token and Token-2022, once each. No malformed/unhashable, duplicate or third-party program IDs.
- `reason` must equal `TOKEN_ACCOUNT_QUERY_UNAVAILABLE`; `error_type` must be a nonempty valid identifier with a bounded length, since the capture source records the actual exception class name (including legitimate subclasses) rather than only a fixed list of exact built-in exception names.
- Empty observed `mints`, `account_count==0` and `mint_count_observed==0` with strict integer type. `same_slot_atomic`, `all_history_complete`, beneficial control and wallet balance proof remain false; USD NAV and realized PnL must be null. Incorrect source shape yields `OWNER_CAPTURE_SLOTLESS_PROGRAM_EVIDENCE_INVALID` instead of an invented complete two-program failure.
- The immutable original source hash, import order, RPC-time anchor, latest full-set Slot selection and legitimate failed latest attempt masking of older quantities remain unchanged. This is validation of evidence semantics, not an attempt to prove latest real Frank balances.

## Evidence and test requirements

- `tests/test_frank_a05_f02_latest_inventory.py` includes archived real SQLite **synthetic-adversarial** captures with independently recomputed valid hashes: duplicate SPL, duplicate Token-2022, unknown or unhashable program, non-object entry, omitted/bogus `reason`, omitted or malformed error type, unexpected failure metadata, nonempty observed program/Mint, inconsistent integer counts, atomicity or wallet balance contradictions and extraneous third row. Each must fail closed.
- Valid **source-format** `capture_owner` dual TimeoutError (one per program) still masks old positive token amount and reports a null balance, null Slot, preserved source SHA; a prior valid double failure still permits a later healthy source. Tests are **not** new actual live RPC evidence.
- Retain #57's 121 out-of-order archived source test and all prior A04 V3 immutable storage tests and full local-agent CI.
- Dedicated exact-head and current-main disposable A05/F02+C02+F01 full real-Git CI workflows on the child PR. Record final code SHA and actual success/failure after the last commit.
- **Separate independent Claude Review required on this child exact final SHA**, then later independent integration review and, after all modules, one more whole-product Review under `docs/DEVELOPMENT_REVIEW_POLICY.md` proposal [#55](https://github.com/lxxlx2/ChatGPT_mission_record/pull/55).

## Outstanding business acceptance

Actual fresh Mac 32-Mint roster, genuine current dual-program owner RPC, ATA non-associated accounts and historical deltas, complete failed instruction and owner-missing/ATA-close receipts, F02 Dashboard user test and economic cost/PnL remain unverified. No prior Code APPROVE grants deployment authorization.

**DRAFT / NO_MERGE / NO_DEPLOY / no Frank V1, Gmail, production SQLite, LaunchAgent or actual trade changes.**
