# Crypto Profit Mission Runbook

Updated: 2026-09-26 12:05 Asia/Bangkok
Timezone: Asia/Bangkok
Schedule: hourly at :29

Purpose: preserve all Mission functions while guaranteeing that the hourly run reaches a durable conclusion.

## 0. First persistent action

Before broad reads, searches or market work:

1. get current Asia/Bangkok time;
2. create `runs/YYYY-MM-DD/HHMMSS.md`;
3. write:
   - run_time
   - automation_id
   - run_status: in_progress
   - phase: skeleton

If the path collides, use a new second-level timestamp and retry once.

If the skeleton cannot be created, continue only long enough to attempt a health/error record. Never disable/pause the automation.

## 1. Minimal required reads

After skeleton creation read only:
- `MISSION_SPEC.md`
- `portfolio/current.md`
- `state/latest.md`
- `health/current.md`
- `positions/pons.md`
- `positions/xrp-variational.md`
- `positions/eth-conditional.md`
- `positions/jump.md`
- `watchlists/btc-regime-jasonleo.md`
- `watchlists/monster-squeeze-v2.1.md`

Read another position/watchlist only when its cadence or a candidate requires it.

Do not bulk-read closed/historical files.

## 2. Phase A: critical risk lanes

Phase A must finish before discovery work.

### Wallet / gas
Every hour:
- fresh Ethereum canonical USDC + native ETH;
- fresh Solana canonical USDC + native SOL;
- known active liquid token balances when relevant.

Daily reconciliation adds Base, Unichain and Robinhood Chain.

RPC failure = UNAVAILABLE. Never substitute stale data.

### PONS
Use fresh public Binance market data and the USER_CONFIRMED private execution state. Check only strategy/stop/breakout triggers from `positions/pons.md`.

### XRP / Variational
Use fresh XRP public market/derivatives data to evaluate the trigger rules in `positions/xrp-variational.md`. Do not fabricate private venue state.

### ETH
Evaluate only the explicit setups in `positions/eth-conditional.md`.

### BTC
Use the BTC watchlist only as regime/risk overlay.

### JUMP
Normal hourly check is lightweight:
- deadline proximity;
- Ethereum reserve/gas readiness;
- new authenticated terms only when a relevant update/deadline is detected.

The full Legion preflight runs on the defined Sep-29 window.

### Active-position security
Check only material exchange/protocol/security developments relevant to current positions.

After Phase A, update the run audit with each lane as checked / trigger / unavailable.

## 3. Phase B: opportunity discovery

The objective is full functional coverage without duplicating an entire web crawl.

### Upstream research first
Read at most the two newest `crypto-daily/research/` files from the previous 2 hours.

Use them as the first discovery feed for:
- launch/token sale opportunities;
- NFT/digital-art opportunities;
- security;
- ecosystem events;
- unusual market moves.

If no fresh Crypto Daily research exists within roughly 90 minutes, perform one compact fallback discovery search.

### Monster V2.1
Maintain full-market coverage efficiently:

1. obtain one bulk Binance USDⓈ-M 24h universe/ticker snapshot;
2. obtain Binance Alpha discovery data when available;
3. merge with 7-day carried candidates and active SAGA watch;
4. shortlist at most 8 symbols using abnormal return, turnover, OI/liquidity structure or prior STRUCTURAL/PRESSURE state;
5. run detailed funding/OI/taker/top-trader/klines only for the shortlist;
6. evaluate the frozen V2.1 gate;
7. record counts and transitions.

Do not make a separate heavy per-symbol query for every perpetual in the universe.

A lane is considered checked when the bulk universe was screened and every shortlisted candidate was evaluated or explicitly marked unavailable.

### Launch radar
Use `watchlists/famous-token-launch-radar.md` only when:
- upstream research contains a candidate;
- an official high-priority source has a new launch/sale/mint/claim;
- fallback discovery is required because upstream research is stale.

Deep verify only actual candidates.

### NFT radar
Use `watchlists/nft-mint-radar.md`.

Do not query every scanner every hour. Use:
- fresh upstream candidate;
- one primary discovery surface;
- fallback sources only if the primary source fails or yields a candidate requiring confirmation.

A 403/loading page means source unavailable, not "no opportunity".

### Robinhood/FOMO
Use `watchlists/robinhood-fomo-mev.md`.

Hourly work is limited to:
- current carried candidates;
- new relevant upstream research;
- existing calibration state.

No candidate = checked_no_candidate. Do not replay historical round trips every hour.

## 4. Phase C: medium cadence

Only when current Bangkok hour modulo 3 == 0, or a material event requires it:
- read `positions/unicred.md`;
- read `positions/credits.md`;
- perform their defined medium checks.

Otherwise record medium_lane: not_due.

## 5. Alert handling

Follow MISSION_SPEC and the relevant position/watchlist.

ACTION and changed WATCH use Gmail + ChatGPT.

No-action states remain silent except the required 19:29 monster summary.

Do not let Gmail failure stop the rest of the run.

## 6. Write current state

Before updating a mutable current file, fetch its newest SHA in the same run.

Update:
- `state/latest.md` with fresh current data only;
- `health/current.md` with current scheduler/run health.

If no material state changed, keep the write compact. Do not append repeated historical snapshots.

On SHA conflict:
- refetch;
- retry once;
- if still failing, mark the write failed and continue to audit finalization.

## 7. Finalize, even when partial

The run must make a best-effort final update to the same skeleton audit.

Allowed final status:
- success
- partial_success
- partial_failure
- failed

Never leave `in_progress` intentionally.

Minimum final audit:
- phase completion;
- wallet status;
- each Phase A lane;
- upstream research freshness;
- monster universe_checked / shortlist count / states;
- launch/NFT/FOMO status;
- medium lane due/not_due;
- alerts attempted/sent;
- state write;
- health write;
- exact tool/source failures.

If Phase A completed but a discovery lane failed, finalize as partial_success or partial_failure rather than disappearing.

## 8. Health rules

- no finalized audit for a scheduler trigger = missing_audit;
- successful-run gap >90 minutes = MONITOR_HEALTH_GAP on recovery;
- same mandatory lane unavailable for two consecutive finalized runs = MONITOR_LANE_FAILURE;
- temporary failure never disables or pauses the task.

## 9. Success definition

Success requires:
- skeleton was created;
- all Phase A lanes have a status;
- Monster bulk screen has a status;
- launch/NFT/FOMO have checked / no_candidate / trigger / unavailable;
- state and health update completed;
- same audit finalized.

Scheduler metadata alone never counts as success.
