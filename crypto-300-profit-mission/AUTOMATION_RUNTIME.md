# Existing $300 Crypto Automation Runtime

Updated: 2026-09-26 14:18 Asia/Bangkok
Mode: FACTUAL_PORTFOLIO_TELEMETRY
Schedule: hourly at :29 Asia/Bangkok

This file is intentionally limited to factual telemetry and pre-existing alert rules. The scheduler does not originate investment recommendations or transactions.

## Start

The first persistent action of every automatic run is:

`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS.md`

Initial fields:
- run_time
- automation_id
- mode: FACTUAL_PORTFOLIO_TELEMETRY
- run_status: in_progress

Do this before external market research.

## Wallet telemetry

Every hour read the canonical wallets using connected sources.

Required:
- Ethereum: canonical USDC + native ETH
- Solana: canonical USDC + native SOL + both legacy SPL Token and Token-2022 active holdings
- BNB Chain: canonical USDC + native BNB + canonical GSTOCK balance
- Robinhood Chain: native ETH + canonical PONS
- supported known active liquid tokens

Daily / when changed:
- Base
- Unichain
- Ink
- known NFTs / points when supported

Token-2022 correction:
- the canonical Solana wallet currently holds e/acc and PAID in Token-2022 accounts;
- every Solana wallet scan must query both the legacy SPL Token program and known Token-2022 mints/accounts;
- never conclude that an asset is absent from a legacy-program-only scan.

Rules:
- failed read = UNAVAILABLE
- never reuse an old value as current
- unsolicited/unpriced tokens stay outside NAV
- private exchange/venue state remains USER_CONFIRMED

## Current factual asset references

### PONS
Read `positions/pons.md`.
Compare public data and direct-chain balances only with thresholds/orders already stored there.
No automatic order change.

### XRP
Read `positions/xrp-variational.md`.
Compare public data with already stored thresholds.
Private venue fields remain USER_CONFIRMED.

### ETH
Read `positions/eth-conditional.md`.
Return only stored-condition status: qualified / not_qualified / unavailable.

### JUMP
Read `positions/jump.md`.
Track authenticated term/deadline/gas changes only.

### GSTOCK / BNB Chain
Read `positions/gstock-plan.md`.
This is currently PLAN_NOT_FILLED unless direct chain shows canonical GSTOCK > 0 or the user supplies a newer order/fill confirmation.

BSC smart-money cluster research remains excluded. Direct wallet telemetry and the user's explicit GSTOCK plan are included.

## Discovery telemetry

Use at most the two newest Crypto Daily research files from the previous two hours as the primary discovery feed.

### Monster V2.1
Read `watchlists/monster-squeeze-v2.1.md`.
Use one bulk Binance futures screen plus bounded shortlist.
Only classify the frozen states:
- STRUCTURAL_CANDIDATE
- PRESSURE
- IGNITION
- EXHAUSTION
- NO_STATE_CHANGE

### Launch / NFT / Robinhood-FOMO
Use the existing watchlists.
Outputs are factual candidate state only:
- checked_no_candidate
- WATCH_CANDIDATE_REVIEW_REQUIRED
- unavailable

Do not create a new spend amount or transaction instruction.

Ink-specific current context:
- wallet already owns Fresh INK commemorative NFT #372;
- 7.665136656205785948 Tydro Ink Points are present;
- the newly discussed target Ink NFT is still treated as pending until a new NFT / mint transaction appears or the user confirms mint.

## Alerts

Only notify for a new factual state change already covered by stored rules:
- stored threshold/order trigger crossed
- changed WATCH
- Monster state transition
- wallet balance anomaly
- security/deadline event
- monitor health failure
- 19:29 Monster factual daily summary

When a user decision is needed:
`decision_status: REVIEW_REQUIRED`

Do not add new investment instructions.

## Finish

Best-effort update:
- `portfolio/current.md` when wallet state materially changed
- `state/latest.md`
- `health/current.md`

Then finalize the same run audit as:
- success
- partial_success
- partial_failure
- failed

A scheduler timestamp without a finalized audit is not success.
Temporary source/GitHub/Gmail failure never disables or pauses this existing automation.
