# Frank / CA F01 current follow opportunities: actionable-only display checkpoint

Date: 2026-10-13 Asia/Bangkok
Status: `F01_IMPLEMENTED_IN_DRAFT / EXACT_HEAD_TEST_PENDING / EXTERNAL_REVIEW_PENDING / NOT_DEPLOYED`

## Required behavior and source

F01 is the first visible fix for the original 12 screenshot problems 1 and 3. The current first panel can no longer display `WAIT / NO_BUY / UNASSESSED / CLOSED / latest SELL / expired quote` as current follow opportunities. Any such rows remain in the **collapsed** `不跟、已失效与历史判断` view. The existing Frank observed watchlist, immutable events, raw history and delivery records are untouched.

Source of authority: `MISSION_SPEC.md`, `FRANK_CA_MULTI_PERSON_IMPLEMENTATION_TODO_20261013.md`, frozen `follow_policy_v1.approved.json`. The presentation filter is read-only and uses configured `max_frank_buy_age_seconds` and `max_quote_age_seconds`. It requires a CURRENT `BUY/SMALL_BUY`, `OPEN`, positive model inventory, valid source signal, recent BUY/ADD/REENTRY, current LIVE Frank runtime, fresh decision, and the saved Jupiter quote must be `OK + route_exists=true` and unexpired. The filter does not generate or extend any frozen Decision. If source/policy unavailable, the UI marks it as `待核实` and exposes **zero actionable** rows. A historical null/unknown balance remains unknown; a zero balance is never inferred to be an actual SELL.

## Implementation

- Pure backend `mission_control/follow_view.py` partitioner computes eligible vs excluded and specific exclusion reasons, without writing to any database.
- `DashboardState.follow_opportunities()` creates only a view from existing frozen service data and approved policy thresholds; introduces `GET /api/follow-opportunities`, retaining original `GET /api/candidates` unchanged for backward compatibility.
- `quote_observed_at` now propagates from the existing saved immutable input into the read-only candidate presentation, so quote freshness can be assessed without a new Jupiter request.
- `static/app.js` shows only `eligible` as first-panel follow cards, historical/excluded rows in a separate collapsed search/research area, and a distinct API-unavailable state. The original `renderCandidates(rows)` function name and one-argument contract are preserved for old DOM regression tests. `index.html` adds the dedicated collapsed panel.
- No trading, no new live research person, no new notification, no new sidecar writer, no policy change, no existing Gmail/retry/Loop restart, no production database mutation.

## Red-green and review

- **Red baseline**: [Actions #38416881805](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38416881805) failed because the F01 classifier did not exist. This is genuine original contract failure.
- The first full-suite run with changed UI [#38417415079](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38417415079) exposed existing DOM tests requiring the old `renderCandidates(rows)` signature; fixed without deleting tests.
- Dedicated F01 regression covers actionable/nonactionable, latest SELL, old decision, missing quote, stale BUY, wrong person and removed/current history. End-to-end local fake Frank+control cycle tests check read-only API, quote timestamp, failure-safe excluded history and unchanged outbox rows. No actual Mac account, live chain inventory or cross-source outcome is claimed.
- Final exact-head CI status and independent reviewer verdict must be recorded after GitHub runs; this file intentionally does not mark them PASS until observed.

## Known pending work

- F01 requires another AI's independent review and F01 UI browser acceptance at the Mac later. No merging/deployment without those checks.
- **F02:** accurate *chain-verified* current balances/ATA, model-vs-chain explanation and refresh; F01 cannot fill in missing inventory.
- **A03–A06:** person identity and economic ledger, real chain owner validation, cross-wallet cost/PnL before attaching verified holdings to follow cards.
- **C01–C10:** CA single-mode identity, history, holder, narrative and TTL issues remain separate.

This is a functional **current-opportunities display** change only. It is not an independent claim that BUY decisions are profitable.
