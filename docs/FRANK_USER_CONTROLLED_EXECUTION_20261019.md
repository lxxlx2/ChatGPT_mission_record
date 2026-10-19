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

## Source notification vs optional execution assessment (G1 compatibility)

- **Already authorized frozen V1 source path (independent):** `signals/engine.py` writes ACCUMULATION/MULTIPLE to **production source `signals` and `outbox`**. ACCUMULATION has a local notification; MULTIPLE has local + Gmail frozen V1 source content. These are unaffected by any Mission Control user amount; this PR does not rewrite, drain, or suppress these source outbox rows.
- **Mission Control decision path (separate):** with no explicit user amount, optional Jupiter execution quote is **not requested**, its observation time is absent, and execution assessment is `NOT_ASSESSED`. The old BUY/SMALL_BUY decision notification cannot still claim executable trading advice; initial WAIT transitions are suppressed here to avoid misleading duplicate *decision* notifications. Historical/visible V1 source signal identity remains on the candidate; no amount is ever invented.
- **Do not conflate the channels:** proof that V1 source `outbox` remains intact is **not** proof that new Mission Control decision/Gmail notifications are unchanged; old quote-dependent decision-alert semantics intentionally differ. If a future release needs additional source-event email beyond existing V1, this requires independent permission, deduplication, and rate-limit policy—not an unapproved new sender.
- **Rollback/migration boundary:** keep the presently running frozen V1 source signal service and its signed event ledger untouched. Do not use the old policy digest to authorize the modified approved JSON. Before separately authorized rollout, verify the new policy SHA, both signal/outbox channels, Mac local notifications, Gmail freshness/deduplication in an isolated copy, and a rollback that restores the previous running Mission Control deployment **without reviving any unapproved default order amount**. No automatic installation, new credentials, or live delivery is authorized by these notes.

## Acceptance

1. Default checked-in policy has **no execution notional** and no automatic Jupiter request, quote-price metric, percentage impact or BUY/SMALL_BUY based on a fabricated position size.
2. Other wallet signal/source data and historical artifacts remain available.
3. Explicit optional quote amount in a targeted user-requested experiment is clearly identified as hypothetical, never filled and never a signal predicate.
4. Existing test fixtures may use various explicit numbers to test an API; these numbers **are not trading defaults**.
5. Nontrivial service behavior change and approved-policy SHA invalidate earlier reviews—require independent pinned-SHA review, regression, and actual user permission before merging/deploying.

Other limits: `NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE_WRITE`.
