# Close Call V4.0 correctness patch review

Review branch: `review/flop-v4-correctness-20260929`

This branch is intentionally **review-only**. It has not been merged to `main`
and does not change the running LaunchAgent on the user's Mac.

## Scope

This patch only addresses execution/reconstruction correctness issues that were
independently identified by multiple reviews and confirmed against the current
implementation.

### 1. Settlement close source

V5a/V5b reconstruction now uses only the sweep close from
`d-close1-price.ref.px`.

It no longer substitutes `d-close1-pnl.mark`, because the mark is the live
global-price board value and is not the close used by the official clawback fold.

Affected paths:

- `_v5a_pair_snapshot`
- active `dense_v5a_harvest_step`
- `_v5b_verify_open`
- `_v5b_verify_close`

### 2. NOT_VISIBLE is UNKNOWN

Compact referee flow may omit settled/void IDs. V5 overlays now require explicit
visible `settled` evidence before reconstructing an opening or advancing an
open/close verification.

An absent ID is no longer silently treated as settled.

When an active V5 action cannot be verified, the state is blocked with evidence
including the settlement sweep and that sweep's `omitted` counts. This is
deliberately fail-closed.

### 3. Private-room registration lifecycle

The previous implementation treated a historical `flow.rooms` observation as
permanent. The referee can unlist quiet rooms after 12 sweeps.

The patch:

- reconstructs current room state from both `flow.rooms` and `flow.unlisted`;
- refreshes room registration every 8 sweeps;
- prevents Dense/V5b owner registration from being posted into an unconfirmed
  private room;
- keeps an already-listed room refresh from consuming the V4 strategy slot.

### 4. Deterministic trade IDs

Current V4/V5 strategy trade IDs no longer depend on `time.time()`.

Stable IDs are generated for:

- V4 baseline long/short
- V4 multiplicity long/short
- V5a staged closes
- V5b open/close legs

Goal: if HTTP submission succeeds and the process crashes before local state is
saved, a retry reuses the same logical ID instead of creating a second distinct
trade.

### 5. V4 execution priority

The autopilot now attempts the current sweep's V4 entry before starting new
V5 work.

Existing V5a/V5b risk management may still run when V4 is waiting for referee
alignment, but new V5b cycles are gated until V4 has completed for the sweep.
New V5a work also remains below V4.

## Deliberately NOT changed in this patch

These are strategy questions and should be reviewed/backtested separately:

- V4 long/short offsets
- V4 3/2/3 short copy allocation
- V4 safety coefficients
- splitting long and short quantities
- V5a harvest thresholds
- V5b TP/SL values
- V5b entry fee fraction
- V5b direction/flip model
- feeder publisher choice

This keeps the review focused on correctness before changing the trading model.

## Recommended deployment gate after review

Before deploying a reviewed version, pause **new** V5a/V5b actions while
preserving management of any already in-flight action:

```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py pause-dense-v5a
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py pause-dense-v5b
```

Do not run those commands merely to review this branch.

## Suggested local checks

```bash
cd ~/ChatGPT_mission_record/crypto-300-profit-mission/tools/technocore-close-call

uv run python -m py_compile close_call_fleet.py
uv run python -m unittest -v test_correctness_patch.py

uv run close_call_fleet.py dense-status
uv run close_call_fleet.py dense-v4-preview
uv run close_call_fleet.py dense-v5a-preview
uv run close_call_fleet.py dense-v5b-preview
```

The first two are code/test checks. The preview/status commands are read-only.
