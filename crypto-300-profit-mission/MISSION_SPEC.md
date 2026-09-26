# Crypto Profit Mission

Updated: 2026-09-26 12:05 Asia/Bangkok
Timezone: Asia/Bangkok

## Authority

This file defines global Mission policy. Detailed execution rules live in the referenced position and watchlist files.

Precedence:
1. `MISSION_SPEC.md`
2. `portfolio/current.md` and `state/latest.md`
3. active `positions/*.md`
4. active `watchlists/*.md`
5. `strategy.md` as historical/background only

Never use stale chat values to overwrite newer verified GitHub state.

## Objective

Use the speculative Mission capital to pursue asymmetric crypto opportunities while preventing one trade from consuming the Mission.

Execution of transactions remains manual unless the user explicitly authorizes the transaction. Research, monitoring, calculations, GitHub audit and already-authorized alerts may run automatically.

The separate 500 USD-equivalent low-risk interest bucket is outside the speculative Mission and cannot be reassigned automatically.

## Canonical wallets and live data

Primary EVM wallet:
`0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`

Primary Solana wallet:
`BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

Use the connected Alchemy app `ChatGPT Crypto Monitor` for direct-chain reads.

Data labels:
- DIRECT_CHAIN: fresh RPC result.
- USER_CONFIRMED: latest user screenshot or explicit statement from an unconnected private venue.
- MARKET: fresh public market data.
- UNAVAILABLE / UNRESOLVED: do not estimate.

Rules:
- RPC failure must be recorded as UNAVAILABLE.
- Never reuse an old wallet balance and call it current.
- Unknown/spam assets are excluded from NAV until identity and value are verified.
- Public market data cannot overwrite private venue fill, quantity, margin, PnL or order state.
- `portfolio/current.md` and `state/latest.md` contain current state only. Historical snapshots belong in Git history and immutable run audits.

## Current capital map

The current authoritative balance map is `portfolio/current.md`.

At the latest verified reconciliation:
- 400 USDC: JUMP conditional reserve on Ethereum.
- 150 USDC: short-window opportunity reserve.
- 100 USDC: ETH conditional reserve.
- current direct-chain residual: 90.407390 USDC.
- PONS: separate 50 USDT margin budget.
- 500 USD-equivalent low-risk bucket: excluded from this Mission.

Balance changes are not profit until transaction history and cost basis support that conclusion.

## Active positions and plans

### PONS
Authority: `positions/pons.md`

Key invariant:
- total margin budget stays 50 USDT;
- only user-confirmed fills count;
- pending orders do not count as deployed exposure;
- hard stop and order changes follow the position file;
- no automatic budget increase.

### XRP / Variational
Authority: `positions/xrp-variational.md`

Latest private state remains USER_CONFIRMED until a fresh venue read or user update exists. Public XRP data is used only for risk/event monitoring.

### ETH
Authority: `positions/eth-conditional.md`

No live ETH Mission position is assumed. The 100 USDC reserve stays idle until the conditional setup fully qualifies.

### JUMP
Authority: `positions/jump.md`

The Ethereum USDC reserve is conditional application capital. The 2026-09-29 preflight must verify authenticated Legion terms, allocation rules, current gas and execution readiness before any application.

### UNICRED and Credits
Authorities:
- `positions/unicred.md`
- `positions/credits.md`

These are medium-lane positions unless an unlock, security event, executable sale/claim event or other material action makes them urgent.

## Closed / historical liquid exposure

- SHART direct wallet balance is 0 and routine monitoring is closed.
- liquid CRED direct wallet balance is 0; only its effect on UNICRED economics remains relevant.
- auxiliary WSOL recovery is completed and the old accounts are closed.

## Market / opportunity watchlists

Active watchlists:
- `watchlists/btc-regime-jasonleo.md`
- `watchlists/famous-token-launch-radar.md`
- `watchlists/nft-mint-radar.md`
- `watchlists/monster-squeeze-v2.1.md`
- `watchlists/robinhood-fomo-mev.md`
- `watchlists/saga-squeeze-cycle.md`

BSC smart-money cluster research remains outside this Mission because it is handled in a separate workflow.

## Hourly coverage contract

The scheduler runs every hour at :29 Asia/Bangkok.

Every run must cover the following logical lanes:
- wallet/gas
- PONS
- XRP/Variational
- ETH conditional
- BTC regime
- JUMP
- launch radar
- NFT radar
- active-position security
- monster squeeze V2.1
- Robinhood/FOMO execution-flow

"Covered" does not require a full independent internet crawl for every lane. The execution-efficient method in `RUNBOOK.md` is authoritative:
- critical positions use fresh direct market/wallet data;
- discovery lanes first consume the latest Crypto Daily research;
- broad markets use bulk screening;
- detailed work is limited to shortlisted candidates;
- fallback direct discovery is used when upstream research is stale or a trigger appears.

This keeps the functional scope while allowing the run to finish reliably.

## Medium lane

Every 3 hours, or immediately when material:
- UNICRED economics, rent, unlock and protocol health;
- Credits floor / executable offers / volume / creator mechanics;
- slower holder/liquidity checks.

## Daily reconciliation

First successful Mission run after 00:00 Asia/Bangkok:
- direct-chain reconciliation across Ethereum, Solana, Base, Unichain and Robinhood Chain when supported;
- reconcile `portfolio/current.md`, active positions, reserved capital and `state/latest.md`;
- never carry stale balances forward as current if a live read fails.

## Alerts

Default is silence.

Gmail + user-visible ChatGPT are required for:
- ACTION;
- new or materially changed WATCH;
- position stop/TP or other defined actionable risk;
- material security/deadline event;
- MONITOR_HEALTH_GAP;
- MONITOR_LANE_FAILURE;
- 19:29 monster daily summary.

WATCH email subject:
`[Crypto Mission提醒][WATCH][asset/project]`

A WATCH alert must state:
- why it entered WATCH;
- what is still missing;
- next trigger/event/level;
- primary invalidation/risk.

Unchanged WATCH, NO_ACTION, rejected/noise and ordinary volatility stay silent.

Alerts go to:
`lxx.run688@gmail.com`

If Gmail fails, the run must still record the alert and surface ChatGPT output when the automation supports it.

## Monster V2.1

Authority: `watchlists/monster-squeeze-v2.1.md`.

The model parameters remain frozen. Full-market coverage must use bulk screening plus candidate deep-checks as defined in `RUNBOOK.md`; do not issue one expensive per-symbol deep query across the entire universe.

At 19:29 Asia/Bangkok, the same existing Mission task produces the daily monster summary. The separate legacy monster automation remains disabled.

## Launch / NFT opportunities

Use the active watchlists. An actionable candidate requires verified canonical identity, official participation path, live/imminent window, no unresolved contract/domain/payment conflict and plausible upside.

Any proposed spend uses only the existing opportunity reserve unless the user explicitly reallocates capital.

## Performance

Authority: `performance/current.md`.

Rules:
- wallet balance alone is not PnL;
- internal transfers are not profit;
- listing prices are not executable NAV;
- unresolved closed-position cost/proceeds stay UNRESOLVED;
- private venue unrealized PnL remains USER_CONFIRMED unless directly readable.

## Runtime / audit

`RUNBOOK.md` is authoritative for execution order, workload limits, skeleton audit, retry behavior, health checks and finalization.

A scheduler trigger is not proof of success. A successful run requires a finalized GitHub audit.

Temporary GitHub, Gmail or source failure must never automatically disable or pause the existing automation.
