# Mission Meme V1 — REVIEW BUILD

Status: `CODE_ONLY / NOT_EXECUTED / NOT_AUTHORIZED_LIVE`

Branch: `codex/mission-meme-v1-review`

## Scope

Mission Meme V1 is a **local Frank follow-assistance tool**. It does four jobs only:

1. show whether the Frank runtime is actually alive now;
2. show Frank ACCUMULATION / MULTIPLE episodes and observed positions;
3. apply a fixed deterministic follow rule to the current executable Jupiter quote;
4. notify the user locally and by Gmail when a fresh result or meaningful result transition exists.

No LLM, no auto-trading, no wallet signing, no cloud deployment, no new scheduler.

## Data path

```text
Frank production
  health.json
  forward.sqlite  [READ ONLY]
        |
        v
Mission Control reader
        |
        +--> Jupiter official quote API [read only]
        |
        v
FOLLOW_POLICY_V1
        |
        v
mission-control.sqlite [separate writable DB]
        |
        +--> localhost dashboard
        +--> macOS notification
        +--> Gmail via existing authorized OAuth provider
```

## Isolation

- `forward.sqlite` is opened with SQLite `mode=ro` and `PRAGMA query_only=ON`.
- Existing Frank classifier/evaluator/engine/scanner/policy/delivery/Gmail files are not modified by this build.
- No LaunchAgent, cron, ChatGPT automation or other scheduler is created.
- Dashboard binds only to `127.0.0.1` / localhost / `::1`.
- Jupiter adapter only calls the official quote endpoint. It cannot build/sign/send a swap.
- Mission Control writes only `mission-control.sqlite` under its own control root.

## Decision states

`BUY`
- Frank runtime is LIVE;
- MULTIPLE is active;
- observed inventory is known/open;
- latest action is not SELL;
- fresh Jupiter route exists;
- executable price deviation and impact are inside BUY thresholds.

`SMALL_BUY`
- ACCUMULATION or MULTIPLE remains active;
- execution remains followable but misses the full BUY limits.

`WAIT`
- Frank runtime is not LIVE;
- latest action is SELL;
- quote is stale/unavailable;
- price ran too far;
- price impact is too high.

`NO_BUY`
- observed position is CLOSED / INVENTORY_UNDETERMINED;
- or Jupiter reports no executable route.

## Review policy gate

`config/follow_policy_v1.review.json` ships with:

```text
status = REVIEW_ONLY
live_delivery_approved = false
```

Therefore accidental execution cannot send live local/Gmail notifications.

Live delivery requires all three:

```text
status = FROZEN_APPROVED
live_delivery_approved = true
manual CLI flag = --live-delivery
```

Current numeric thresholds are deliberately provisional review values. External review may replace them before approval.

## Review fixes after 82f980a2

The external review found two P0 regressions and two additional quality issues. The review branch now addresses them as follows:

1. **Fresh quote false-stale regression**: evaluation time is read after each Jupiter quote returns. A newly fetched quote can no longer be rejected merely because its `observed_at` is a few milliseconds later than a cycle-level clock captured before the request.
2. **New episode first result missing notification**: first notification eligibility is no longer tied to the entire database bootstrap. Every newly appearing episode can notify when its own Frank activity is fresh; old historical episodes remain silent.
3. **Dashboard values freezing**: `candidate_latest` stores exactly one mutable latest row per person/mint/episode and is refreshed every evaluation. Immutable snapshot/event history is still created only on Decision transitions.
4. **Ambiguous Gmail delivery unbounded**: unresolved `SENDING` / `SENT_UNVERIFIED` state older than one hour is promoted to `MANUAL_REVIEW`; it is never blindly resent.
5. **Actionable invalidation**: a BUY/SMALL_BUY that becomes WAIT because Frank runtime/data becomes stale is notified once. Initial/transient non-actionable WAIT states remain dashboard-only to avoid outage storms.

## Notification behavior

A fresh new episode or a Decision transition is eligible for notification.

To prevent historical spam:

- an episode with no previous Decision only notifies when its latest Frank activity is within `initial_notification_max_age_seconds`;
- default review value: 600 seconds;
- this rule applies independently to every episode, including episodes first seen after the service has already been running.

Transient WAIT states are normally dashboard-only when there was no actionable state to invalidate. However:

```text
BUY -> WAIT
SMALL_BUY -> WAIT
```

must notify once even when the WAIT reason is runtime/data staleness. Recovery to a later actionable Decision is also a new transition and can notify normally.

Both local and Gmail delivery use a stable `decision_id`.

Gmail delivery has independent state in `mission-control.sqlite`, performs Sent readback, never blindly resends an ambiguous accepted message, and escalates unresolved ambiguity to `MANUAL_REVIEW` after one hour.

## Dashboard storage model

Two storage roles are intentionally separated:

`candidate_latest`
- one mutable row per person/mint/episode;
- refreshed every evaluation;
- used by the dashboard for current executable price, deviation, impact and reasons;
- bounded by the number of observed episodes.

`decision_snapshots` / `decision_events`
- immutable audit history;
- written only when the Decision changes;
- same-state market refresh does not grow this history.

## Jupiter price-impact semantics

Jupiter's official developer documentation states that legacy `priceImpactPct` is a decimal ratio from 0 to 1, not already percentage points. Example: `0.01` means 1% impact. Mission Control therefore multiplies the raw field by 100 before comparing it with policy thresholds expressed in percent.

This semantic point is no longer considered unknown. A separate **real-response fixture requirement remains** before approval so response/error shapes are tested against current production API behavior rather than only synthetic bodies.

## Existing tests remain mandatory

The new code does not replace any existing Frank V1/Gmail/local-notification test. Before live approval the full existing local-agent test suite must still pass, including:

- ACCUMULATION / MULTIPLE mapping;
- HFT behavior;
- restart idempotency;
- transactional rollback;
- frozen policy drift;
- historical replay no-delivery;
- local receipt recovery;
- Gmail exactly-once identity;
- Gmail Sent readback;
- post-acceptance crash recovery;
- Gmail failure not blocking the Frank scanner.

## New review-regression tests

The review branch now includes explicit coverage for:

- production SQLite rejects writes;
- fresh quote returned after cycle start is not falsely `QUOTE_STALE`;
- old bootstrap history remains silent;
- a fresh MULTIPLE episode appearing after bootstrap enqueues its first result;
- BUY invalidated by Frank runtime failure produces one WAIT notification;
- event/latest/outbox writes roll back together on enqueue failure;
- same Decision state does not grow immutable snapshot/event history;
- same Decision state does refresh `candidate_latest`;
- dashboard reads the refreshed latest executable price;
- Gmail decision identity is exactly-once;
- post-acceptance Gmail crash does not resend;
- ambiguous Gmail state cannot remain unresolved forever;
- missing Jupiter key fails closed without network;
- explicit no-route response maps to NO_BUY input;
- Jupiter `priceImpactPct` scaling is covered;
- dashboard refuses public bind/Host values.

## Remaining approval blockers

Do **not** change the policy to `FROZEN_APPROVED` until all of these are complete:

1. external reviewer reruns the Mission Control test set and full local-agent suite against the latest review-branch HEAD;
2. capture current real Jupiter quote responses/fixtures for at least:
   - one liquid routable mint;
   - one thin-liquidity routable mint;
   - one no-route mint/error response;
3. verify the thin-liquidity response against Jupiter's displayed/independent impact interpretation;
4. complete the planned historical threshold replay before treating provisional 8% / 20% deviation and 1.5% / 3% impact values as frozen policy;
5. preserve `PRODUCTION_TRADING = NO_GO`.

## Execution

No local Python service, pytest suite, Jupiter live request, macOS notification or Gmail send is claimed as executed by the code-authoring step documented here.

After external review, tests should be run against the exact review-branch HEAD. Only after all blockers pass should the policy gate be considered for `FROZEN_APPROVED`.
