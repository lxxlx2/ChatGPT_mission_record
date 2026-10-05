# Mission Meme V1 — REVIEW BUILD

Status: `CODE_ONLY / NOT_EXECUTED / NOT_AUTHORIZED_LIVE`

Branch: `codex/mission-meme-v1-review`

## Scope

Mission Meme V1 is a **local Frank follow-assistance tool**. It does four jobs only:

1. show whether the Frank runtime is actually alive now;
2. show Frank ACCUMULATION / MULTIPLE episodes and observed positions;
3. apply a fixed deterministic follow rule to the current executable Jupiter quote;
4. notify the user locally and by Gmail when a fresh result or result transition exists.

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

## Notification behavior

Every **new result** or **Decision transition** is meaningful:

```text
NONE -> BUY
NONE -> SMALL_BUY
NONE -> WAIT
NONE -> NO_BUY
BUY -> WAIT
BUY -> NO_BUY
WAIT -> BUY
WAIT -> SMALL_BUY
...etc
```

Same-state reevaluation is silent.

To prevent historical spam on first startup:

- existing old episodes are recorded as baseline;
- first-cycle notification is allowed only when the candidate's latest Frank activity is within `initial_notification_max_age_seconds`;
- default review value: 600 seconds;
- later state transitions notify normally.

Both local and Gmail delivery use a stable `decision_id`.

Gmail delivery has independent state in `mission-control.sqlite`, performs Sent readback, and treats ambiguous acceptance as non-resendable until reconciled.

## Dashboard

Local high-density dashboard shows:

- Frank LIVE / DEGRADED / OFFLINE / UNKNOWN;
- PID and heartbeat age;
- current candidate table;
- Decision;
- ACCUMULATION / MULTIPLE;
- Frank BUY/SELL count;
- latest action;
- latest Frank buy price;
- current executable price;
- price deviation;
- price impact;
- position state;
- recent Frank trades;
- recent Decision transitions.

The dashboard reads the latest **snapshot**, not only the latest transition event, so same-state price updates remain visible without sending duplicate notifications.

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

## New tests included

- production SQLite rejects writes;
- same Decision state creates snapshots but no duplicate event;
- Decision transition retains previous state;
- MULTIPLE near Frank -> BUY;
- ACCUMULATION -> at most SMALL_BUY;
- SELL / stale quote / high impact / chase -> no BUY;
- runtime not LIVE -> WAIT;
- no Jupiter route -> NO_BUY;
- missing Jupiter API key fails closed without network;
- dashboard refuses a public bind address;
- REVIEW_ONLY cannot live-deliver;
- bootstrap old episode cannot enqueue historical notification;
- Gmail decision identity is exactly-once;
- post-acceptance Gmail crash does not resend.

## Acceptance before first execution

External AI/code review should confirm:

1. production DB cannot be mutated;
2. no existing production file changed;
3. provisional threshold values are acceptable or replaced;
4. stale/missing data cannot produce BUY;
5. Frank OFFLINE/DEGRADED cannot produce BUY;
6. first startup cannot mass-send historical results;
7. Gmail/local dedupe is sound;
8. review mode cannot deliver;
9. localhost server cannot bind publicly;
10. Jupiter integration is quote-only and official;
11. full old + new test suite is expected to pass before approval.

## Files added

```text
mission_agent/mission_control/
  __init__.py
  db.py
  frank.py
  jupiter.py
  policy.py
  delivery.py
  service.py
  server.py
  static/
    index.html
    app.js
    styles.css

scripts/mission_meme_v1.py
config/follow_policy_v1.review.json

tests/test_mission_control_policy.py
tests/test_mission_control_db.py
tests/test_mission_control_delivery.py
tests/test_mission_control_service.py
tests/test_mission_control_misc.py
```

## Execution

No command in this document has been executed during the code-only phase.

After review, the first step is to run the existing and new tests. Only after they pass should the policy gate be changed from `REVIEW_ONLY`.
