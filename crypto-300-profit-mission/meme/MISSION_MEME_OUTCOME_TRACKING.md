# Mission Meme Forward Outcome Tracking

Purpose: make the one-month Frank strategy review reproducible from data captured forward in time.

## What is measured

Each distinct Frank research signal stage is tracked independently:
- REENTRY_WATCH
- ACCUMULATION
- MULTIPLE

The tracker registers the first moment Mission Control sees that stage. If a real Jupiter 30 USDC -> token route exists at that moment, the exact token raw output becomes the hypothetical executable entry inventory.

Future exit value is measured by asking Jupiter for a read-only quote from that exact token raw amount back to USDC.

This avoids using Frank's own fill as if the user could have obtained it.

## Fixed horizons

- T+5m
- T+15m
- T+1h
- T+6h
- T+24h

A horizon accepts only a sample inside the configured grace window. If the Mac/service was down and the first later sample arrives too late, the horizon is recorded as MISSED_WINDOW instead of backfilled with the wrong price.

## Path sampling

While a track is active, the service samples at most once per 5-minute bucket. This supports:
- 5-minute-sampled MFE
- 5-minute-sampled MAE
- 5-minute-sampled max drawdown

These are sampled approximations, not tick-perfect extrema.

To protect free keyless Jupiter usage, the tracker processes at most two outcome quotes per Mission Control cycle. Backlogged due samples are spread across later cycles.

## Data tables

Stored in the existing separate writable `mission-control.sqlite`:
- outcome_tracks
- outcome_samples
- outcome_horizons

No Frank production DB write is introduced.

## Report

    PYTHONPATH=. python3 scripts/mission_meme_monthly_report.py \
      --control-root "$(cat ~/.frank_meme_control_root)" \
      --since "2026-10-07T00:00:00+07:00"

Output:
- JSON machine report
- Markdown human report

The report separates data coverage from performance. Missing horizon data remains missing; it is never estimated.
