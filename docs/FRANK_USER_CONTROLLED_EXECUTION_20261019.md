# Frank: 交易金额与执行方式由用户决定（2026-10-19）

Status: **USER_DIRECTED_CORRECTION / EFFECTIVE_FOR_ALL_FUTURE_FRANK_DEVELOPMENT**.
Scope: Frank wallet monitoring, independent V1/V2 follow signals, CA analysis and hypothetical performance research. This is an authoritative forward-going requirement, **not a retroactive alteration of historical transaction evidence**.

## What the user explicitly rejected

The user **never approved any default fixed $30 transaction size or $30-specific recommendation rule**. The prior assistant treated a provisional historical example as an approved trading assumption. It was not an authorization. **Withdraw it from all future specifications, new code, UI and research methodology.**

- Frank should accurately show wallet activity, original signal triggers, dates, costs where provable, positions with provenance, market-price/liquidity references and source quality. A wallet fact or model signal is not user order authorization.
- The user alone determines **whether to trade, how to execute, and how much**; no model or policy silently chooses a default order amount.
- Never automatically request a Jupiter size-dependent execution quote for an arbitrarily selected notional. Any user-requested quote must have an **explicit amount** and clearly state `QUOTED_ONLY_NOT_FILLED` with source timestamp and expiration.
- No size-dependent price impact/executable quote means **`NOT_ASSESSED`**—not `NO_ROUTE`, not `zero liquidity`, not `BUY/SMALL_BUY verified`. Stored old price quotes do not become today’s evidence.
- Keep Frank V1 independent wallet-signature and ACCUMULATION/MULTIPLE/WAIT classification. Never suppress raw wallet activity or observation-pool membership because no user order size is supplied.
- Do not change unrelated strategy thresholds, auto-execute a trade, backfill signed transactions or modify a user's private production SQLite. Deployment requires a separate approval.

## Repository implementation and safe rollout

- `config/follow_policy_v1.approved.json` and `review.json` omit preset `quote_usdc_amount`. This changes their **content hashes**; an old approved hash MUST NOT be reused. Existing live installations will not be silently edited by this PR.
- `mission_control/service.py` skips optional execution-quote assessment when no amount has been explicitly provided, leaving the independent source signal visible. The existing deterministic BUY/SMALL_BUY recommendation path stays fail-closed without a current user-amount-specific quote. **Potential behavior change to old recommendation notifications requires a separate independent code review and user-authorized deployment.** Do not silently sell this as unchanged production behavior.
- `jupiter.py` refuses to assume a quote amount; only an explicit user-requested amount permits a quote. It never builds or submits a transaction.
- Generic CA research no longer automatically quotes a preset amount or re-publishes old preset quotes. It still shows historical source market prices and on-chain evidence.
- Existing saved historical artifact bytes, past test cases and transaction histories are not retroactively rewritten. Their old sizing assumptions are **deprecated; not an active policy**. Future replay must not treat old fixed-notional outcomes as user PnL or user-approved follow performance.

## Acceptance

1. Default checked-in policy has **no execution notional** and no automatic Jupiter request, quote-price metric, percentage impact or BUY/SMALL_BUY based on a fabricated position size.
2. Other wallet signal/source data and historical artifacts remain available.
3. Explicit optional quote amount in a targeted user-requested experiment is clearly identified as hypothetical, never filled and never a signal predicate.
4. Existing test fixtures may use various explicit numbers to test an API; these numbers **are not trading defaults**.
5. Nontrivial service behavior change and approved-policy SHA invalidate earlier reviews—require independent pinned-SHA review, regression, and actual user permission before merging/deploying.

Other limits: `NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE_WRITE`.
