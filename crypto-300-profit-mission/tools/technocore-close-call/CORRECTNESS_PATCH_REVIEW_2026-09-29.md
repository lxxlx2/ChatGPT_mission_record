# Close Call V4.0 correctness patch review

Review branch: `review/flop-v4-correctness-20260929-v2`

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

Goal: reduce accidental duplicate logical trades by making IDs stable for the
same strategy action.

Important limitation: this is not yet a full write-ahead exactly-once protocol.
A retry that is recomputed as a different logical action (for example on a later
sweep) can still receive a different ID. Reviewers should treat a durable
pre-send intent/WAL as a separate follow-up if stronger crash guarantees are
required.

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


## External review round 2 changes

After DeepSeek, Grok and Gemini reviewed PR #11, the review branch was amended
again. These changes are still review-only.

### Confirmed blockers fixed

1. **Compact flow omissions no longer deadlock V5**
   - explicit visible `void` still blocks;
   - explicit visible `settled` is accepted;
   - when compact flow omits outcomes, active V5 verification can continue using
     deterministic local reconstruction with an explicit
     `local_reconstruction_due_to_compact_omission` evidence marker;
   - when the compact post reports no omissions and the trade is absent, the
     action waits instead of assuming success.

2. **Hot-path room checks no longer rescan historical flow on every helper call**
   - `room_registration_confirmed()` is now an O(1) cached-state read;
   - `dense_room_maintenance()` updates that state from the latest flow once;
   - a 5-second in-process export cache deduplicates repeated export reads within
     one autopilot poll and is invalidated immediately after a local room write.

3. **Exact room-name matching**
   - room listing/unlisting checks use recursive exact membership;
   - substring matches such as `cc-test` vs `cc-test-extra` no longer count.

4. **V4 two-leg posting order**
   - both V4 long and short signed trades are now posted by the feeder account.
   - The underlying maker/taker signatures and terms are unchanged.
   - This follows the official rule that either side may post the countersigned
     trade and gives both legs one publisher/nonce stream.

5. **V4 reserve partial-error recovery**
   - same-sweep `partial_error` reserve copies retain plan/trade metadata;
   - only missing legs are retried with the same logical trade IDs;
   - stale partials from prior sweeps are expired and replaced by reserve refill.

6. **V5 scheduling**
   - V4 still gets first opportunity;
   - already-open V5b risk is managed next;
   - already-started V5a staged close is managed before any pending/new V5b
     housekeeping;
   - pending/new V5 work can no longer starve an active V5a close.

### Conservative strategy guard added for review

New V5 overlays are hard-paused on this review branch:

```python
V5A_REVIEW_PAUSE_NEW = True
V5B_REVIEW_PAUSE_NEW = True
```

Already-active V5 actions remain manageable.

The V5b protective stop candidate is now relative to the realized seed:

```text
stop = max(20, seed_locked_score * 0.85)
```

This is intentionally a review candidate, not a claim that 0.85 is the
mathematically optimal value.

### Outcome parsing clarification

One external report claimed the code handled referee `void` rows only as
dictionaries. That claim does not match the current PR implementation.
`_v5a_visible_outcomes()` uses recursive `contains_value()`, which detects
nested list forms such as:

```json
[["trade-id", "funds"]]
```

A regression test was added for this format.

### PR cleanliness clarification

GitHub's PR metadata currently reports **3 changed files** for PR #11:

- `close_call_fleet.py`
- `test_correctness_patch.py`
- this review document

A report of 53 changed files came from a local comparison context and does not
match the current GitHub PR file set.

## Still deliberately unresolved

The following remain strategy/research work and are not claimed solved:

- V4 stress sizing against the full distribution of next-sweep close moves
- independent long/short quantity optimization
- V4 safety ladder and 3/2/3 copy allocation
- V5a projected locked-value/retention trigger model
- V5b clawback-optimized entry/exit pricing
- proof that any V5b directional flip has positive expectation
- final-S coverage optimization versus the actual prize-line topology

The next quantitative step should use the official fold to replay V4 quantity
and price grids before changing the production ladder.
