# Crypto Profit Mission

Updated: 2026-09-26 12:36 Asia/Bangkok
Timezone: Asia/Bangkok

## Authority

This file defines global Mission policy. Detailed thresholds and state rules live in the referenced position and watchlist files.

Precedence:
1. `MISSION_SPEC.md`
2. `portfolio/current.md` and `state/latest.md`
3. active `positions/*.md`
4. active `watchlists/*.md`
5. `strategy.md` as historical/background only

Never use stale chat values to overwrite newer verified GitHub state.

## Automation mode

The existing hourly automation is a **factual rule monitor**, not an autonomous trading adviser.

It may automatically:
- read connected wallet / market / official-source data;
- calculate factual deltas and predefined indicators;
- compare current data with thresholds already stored in GitHub;
- classify predefined states such as WATCH / IGNITION / EXHAUSTION / setup-qualified;
- log results;
- send factual trigger notifications already authorized by the user.

It must not automatically:
- originate a new trade;
- invent a new entry, stop, take-profit, leverage or position size;
- tell the user to buy/sell/short/long a newly discovered asset;
- reallocate capital;
- modify an existing private-venue order or position;
- turn a newly discovered candidate into an execution recommendation.

When a factual trigger fires, the alert should say what changed, which stored rule fired, current data, missing conditions and invalidation/risk. Interactive follow-up in chat can perform deeper decision analysis if the user asks.

Existing user-confirmed position rules and already-stored thresholds remain valid monitoring inputs.

## Objective

Maintain reliable, auditable coverage of the user's speculative crypto Mission and surface material factual changes early enough for the user to decide what to do.

Execution of transactions remains manual unless the user explicitly authorizes a transaction.

The separate 500 USD-equivalent low-risk interest bucket remains outside the speculative Mission.

## Canonical wallets and data truth

Primary EVM wallet:
`0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`

Primary Solana wallet:
`BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

Use connected Alchemy `ChatGPT Crypto Monitor` for direct-chain reads.

Labels:
- DIRECT_CHAIN: fresh RPC.
- USER_CONFIRMED: latest user screenshot / explicit statement from an unconnected private venue.
- MARKET: fresh public market data.
- UNAVAILABLE / UNRESOLVED: do not estimate.

Rules:
- RPC failure = UNAVAILABLE.
- Never reuse an old wallet balance and call it current.
- Unknown/spam assets stay outside NAV until identity/value are verified.
- Public market data cannot overwrite private venue fill, quantity, margin, PnL or order state.
- `portfolio/current.md` and `state/latest.md` contain current state only.
- historical snapshots belong in Git history / immutable run audits.

## Capital map

Authority: `portfolio/current.md`.

Current accounting buckets:
- JUMP conditional reserve: 400 USDC.
- short-window opportunity reserve: 150 USDC.
- ETH conditional reserve: 100 USDC.
- PONS: original 50-USDT sleeve is now split between the remaining Binance futures position and Robinhood Chain spot PONS + gas; the old 0.5850 and 0.5450 averaging orders are canceled.
- low-risk interest bucket: excluded from Mission.

Wallet balance changes are not PnL unless transaction history and cost basis support that conclusion.

## Active position / plan authorities

### PONS
`positions/pons.md`

Automation may report:
- current public market state for the remaining futures position;
- crossing of the stored 0.4980 stop / material leverage-risk thresholds;
- fresh DIRECT_CHAIN Robinhood PONS spot balance and native gas;
- material unexpected wallet delta;
- private futures order/fill state only when USER_CONFIRMED.

The prior 0.5850 and 0.5450 averaging bids are canceled and must not be monitored as live orders or recreated automatically.

No automatic order modification, averaging order, budget change or spot/futures reallocation.

### XRP / Variational
`positions/xrp-variational.md`

Automation may report:
- price/derivatives changes;
- crossing of stored TP/SL/event thresholds;
- Bitget-event factual developments.

Private Variational state remains USER_CONFIRMED until refreshed directly.

### ETH
`positions/eth-conditional.md`

Automation may report whether Setup A, Setup B or stored breakout conditions are factually satisfied. It must not create a new ETH plan or new levels by itself.

### JUMP
`positions/jump.md`

Automation monitors:
- deadline proximity;
- authenticated sale-term changes;
- reserve/gas readiness;
- the predefined Sep-29 preflight.

No application/transaction is executed automatically.

### UNICRED / Credits
- `positions/unicred.md`
- `positions/credits.md`

Medium cadence unless unlock/security/claim/executable-market change makes them urgent.

## Closed / historical exposure

- SHART direct balance 0: routine monitoring closed.
- liquid CRED direct balance 0: standalone token monitoring closed.
- auxiliary WSOL recovery completed.
- BSC smart-money cluster remains outside this Mission.

## Active watchlists

- `watchlists/btc-regime-jasonleo.md`
- `watchlists/famous-token-launch-radar.md`
- `watchlists/nft-mint-radar.md`
- `watchlists/monster-squeeze-v2.1.md`
- `watchlists/robinhood-fomo-mev.md`
- `watchlists/saga-squeeze-cycle.md`

## Hourly coverage

Every :29 run covers:
- wallet/gas;
- PONS;
- XRP/Variational;
- ETH conditional;
- BTC regime;
- JUMP;
- launch radar;
- NFT radar;
- active-position security;
- Monster V2.1;
- Robinhood/FOMO execution-flow.

Coverage follows the bounded execution method in `RUNBOOK.md`.

## Medium lane

Every 3 hours, or immediately when material:
- UNICRED economics / rent / unlock / protocol health;
- Credits executable market / volume / creator mechanics;
- slower holder/liquidity checks.

## Daily reconciliation

First successful Mission run after 00:00 Asia/Bangkok:
- reconcile supported canonical wallets;
- update `portfolio/current.md`, active positions, reserves and `state/latest.md`;
- never carry a failed live read forward as current.

## Notifications

Default: silent.

Gmail + user-visible ChatGPT are required for a **new factual trigger**:
- stored position stop/TP/event threshold crossed;
- stored ETH setup becomes qualified;
- new/materially changed WATCH;
- Monster IGNITION / relevant EXHAUSTION state transition;
- material security or deadline event;
- MONITOR_HEALTH_GAP;
- MONITOR_LANE_FAILURE;
- 19:29 Monster daily summary.

Alert wording must be factual:
- current value/state;
- exact stored rule that fired;
- what changed since prior state;
- what remains unconfirmed;
- invalidation/risk;
- "review required" when a user decision is needed.

Do not include newly invented trade instructions, leverage, position sizing or capital allocation in an automated alert.

WATCH subject:
`[Crypto Mission提醒][WATCH][asset/project]`

Unchanged WATCH, NO_ACTION, rejected/noise and ordinary volatility stay silent.

Gmail destination:
`lxx.run688@gmail.com`

## Monster V2.1

Authority: `watchlists/monster-squeeze-v2.1.md`.

The model remains frozen. The automation performs factual state classification only.

Full-market coverage uses:
- bulk universe screening;
- bounded shortlist;
- detailed checks only for shortlisted symbols.

At 19:29 the same existing Mission task sends the factual Monster daily summary. The legacy standalone Monster automation remains disabled.

## Launch / NFT discovery

A candidate may be promoted to WATCH only after:
- canonical issuer identity;
- official participation path;
- live/imminent window;
- no unresolved contract/domain/payment conflict;
- sufficient factual opportunity evidence.

The automated alert must remain "candidate for review" and must not generate a new buy/mint amount or execution instruction.

## Performance

Authority: `performance/current.md`.

- wallet balance alone is not PnL;
- internal transfers are not profit;
- listing prices are not executable NAV;
- unresolved closed-position cost/proceeds remain UNRESOLVED;
- private venue PnL remains USER_CONFIRMED unless directly readable.

## Runtime / audit

`RUNBOOK.md` is authoritative for execution order, workload limits, skeleton audit, retry and finalization.

A scheduler trigger is not proof of success.

Temporary GitHub, Gmail or source failures must never automatically disable or pause the existing task.
