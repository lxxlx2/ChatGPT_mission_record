# A05/F02 — external read-only Solana owner source preflight (not full account census)

Date: 2026-10-14, Asia/Bangkok; from connected read-only Alchemy broad mainnet monitoring app.
Wallet queried: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`. This is a public on-chain address, **not proof of Frank's ultimate beneficial ownership**.
Method: `getTokenAccountsByOwner` with official `programId` filters, commitment `finalized`, encoding `jsonParsed` and alternative `base64`; the two program calls are separate and **non-atomic**.

| Program | Observed finalized context slots in available responses | Result |
| --- | --- | --- |
| SPL Token `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA` | `456863388`, `456863593`, `456864094` (successive preflight invocations, **not a single atomic snapshot**) | Tool response was truncated before full JSON. Partial token-account fragments visible; cannot assert total token-account count or target mint coverage. |
| Token-2022 `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` | `456863389`, `456864097` | Tool response was likewise truncated before valid complete JSON. Cannot assert complete program source. |

Source/tool constraint: the read-only connector returned up to approximately 8,098 characters and appended `[truncated — response too large. Use more specific filters or pagination to narrow results.]`. **Neither SPL nor Token-2022 unfiltered owner result could be fully parsed/archived** through this connector even using base64; do not represent either as `BOTH_PROGRAMS_OBSERVED_NON_ATOMIC` or store a fabricated `ACCOUNT_CAPTURE` with `missing=[]`. Alchemy `getAssetsByOwner(page=1,limit=5)` returned RPC error `-32001 Unable to complete request at this time`; digital asset search is not equivalent to raw owner token-account coverage in any case.

No full response payload, snapshot SHA, accounts count, source-completeness attestation or **exact 32 frozen target Mints** obtained in this preflight. Do not infer token sale from zero or absent fragments. No pricing, inferred funding, cost/PnL or notifications.

## Next usable source acceptance

1. Use the already existing **manual full-response Mac capture** `scripts/frank_capture_owner_readonly.py` on the owner's approved research sidecar, or another provider able to transmit full JSON without tool-output truncation. Keep raw complete RPC responses, result arrays, program-id filters, finalized context slots, account addresses, Mint, raw decimals and response time in segregated immutable evidence. Failure/partial state must remain explicit.
2. Independently read/confirm the actual **32-Mint target roster** from the existing Mac registry/source; do not generate 32 random Mints or use currently held Mints as a substitute for target history.
3. Feed only valid complete two-program captures to the approved `wallet_inventory_snapshot` projection from PR #58; compare UTC freshness and do not report atomic balance, person control or PnL. Test actual Mac/read-only CLI, then implement F02 browser source display, independent module review and a separate cross-module review.
4. This preflight did **not** execute signing, RPC writes, production SQLite mutations, Gmail, trades or launchd restart, and does **not** authorize merging approved patches or deployment.

State: `PUBLIC_CHAIN_READ_ONLY_PARTIAL_RPC_OUTPUT / FULL_32_MINT_SOURCE_UNVERIFIED / NO_MERGE / NO_DEPLOY`.
