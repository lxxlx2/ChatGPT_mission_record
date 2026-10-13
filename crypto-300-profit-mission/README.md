# $300-3000 Crypto Mission

Updated: 2026-10-13 (portfolio pointer/snapshot; module operational authority unchanged)
Timezone: Asia/Bangkok

Current mutable facts: [`MISSION_SPEC.md`](MISSION_SPEC.md), [`state/latest.md`](state/latest.md), [`portfolio/current.md`](portfolio/current.md), [`performance/current.md`](performance/current.md). Historical 2026-10-04 scope: [`STATUS_SCOPE_2026-10-04.md`](STATUS_SCOPE_2026-10-04.md).

## Current status

The Mission remains the umbrella `$300 -> $3000` speculative-asset project, but its modules no longer share one active GPT scheduler.

Current module state:
- **Frank / Meme:** `FRANK_LOCAL_SIGNAL_V1_LIVE`; local deterministic authority; ACCUMULATION local alert LIVE; MULTIPLE local alert + standalone Gmail LIVE; GPT signal authority removed.
- **Frank historical delivery acceptance:** STONK frozen-V1 MULTIPLE historical E2E passed through replay -> local TEST notifications -> Gmail -> Sent readback -> dedupe/crash recovery.
- **NFT radar:** specification/research preserved, runtime currently paused/not active.
- **MONSTER / 妖币:** V3 failed independent 2024 validation. V4 2026-10-10 read-only research continues in [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30) with no validated BUY strategy, live scanner, Gmail or LaunchAgent.
- **CORE PRICE / overall-market trend module:** paused; legacy `$300 Crypto资产状态监控` remains disabled.
- **Other tracked persons / TOKEN_CONSENSUS:** deferred.
- **Production trading:** `NO_GO`.

- **Frank / Meme integration:** [PR #29](https://github.com/lxxlx2/ChatGPT_mission_record/pull/29) merged October 10; user-authorized pre-merge Loop/Dashboard Mac acceptance passed for the scoped version. Later post-merge runtime and new-code real Gmail send are not independently verified here.

## Mission scheduler authority

There is currently **no active umbrella `$300-3000` GPT task**.

- `$300-3000`: **PAUSED on 2026-10-04** because Frank moved fully to local authority and the remaining Mission lanes are paused/frozen/deferred.
- `$300 Crypto资产状态监控`: legacy **DISABLED**; do not re-enable without explicit user authorization.
- Frank signals are produced by the local deterministic runtime, not by a ChatGPT scheduled task.

Do not create a replacement Mission task automatically. Independent non-Mission schedulers such as Crypto Daily, TGE monitoring and the US-stock morning report are not affected by this pause.

## Current holdings authority

Current capital / holdings:
- [`portfolio/current.md`](portfolio/current.md)
- [`state/latest.md`](state/latest.md)

**Latest asset observation: 2026-10-13, 21:48–21:50 Asia/Bangkok** ([full canonical portfolio](portfolio/current.md), [current authority](state/latest.md)):

- **Binance investment reserve:** 745.85545285 USDC flexible Earn, screenshot estimated **~$746.73**. Cumulative screenshot interest is already contained in the balance.
- **Canonical Solana direct finalized RPC:** 471.716759 USDC (approx **$472.22** using Alchemy USD reference), 0.012905142 SOL (approx **$1.39**), **0 GANG**. Token-2022 unpriced assets are preserved separately and excluded from marked NAV, not assumed to be zero.
- **Observed Binance + direct Solana minimum marked reference:** **~$1,220.34**. Adding still-unverified Oct 12 OKX ETH 0.002403 and TRX 3.3847 quantities repriced with Oct 13 market data yields a **mixed-freshness, conditional ~$1,227.52 reference**, not complete NAV or investment profit. OKX Solana USDC/SOL are duplicates of canonical Solana, never double-counted.
- **Bybit personal living/rent only:** 443.029905 USDC, screenshot **~$443.51**; entire Bybit account is **excluded** from investment subtotals.
- **EVM native:** queried across multiple canonical-wallet networks, individually priced under $1, excluded by permanent threshold. Ethereum/Arbitrum/Optimism/Unichain ERC-20 Blockscout holdings returned no reliably priced >=$1 positions; Base/Polygon/BNB-chain and enhanced Solana/NFT/Sui inventory coverage remains incomplete/partly unavailable. Unknown prices/ownership do not become zero.
- **GANG:** fully exited by user Oct 12, position realized loss **−96.210562 USDC before SOL gas** separately evidenced in [performance](performance/current.md). Original Mission start-set PnL and '$300 to $3,000' progress remain **UNRESOLVED**, and holdings reference movement is not income.

**Permanent display rule:** include each separately priced, identifiable asset only if >= $1; exclude individually marked dust < $1 without aggregation. No full-position deletion from transaction history, no inclusion of unpriced NFT asks or private token rights. Unchanged production trading `NO_GO`, no new Mission automation, no activation of deferred modules.

## Frank wallet evidence and dashboard redesign (2026-10-11)

- [Frank wallet / GMGN data-scope audit](meme/frank-wallet-ui-data-audit-2026-10-11.md): concrete Git filter root cause, screenshots vs true 24h time scope, independent two verified passive-transfer transactions, 132 sampled signatures and Alchemy 429 limitation. The current last-24h active trade count has **not** been fully independently reconciled.
- [Frank observed-position/watchlist V2 architecture](meme/frank-wallet-monitor-dashboard-v2-design-2026-10-11.md): separate factual all-activity ledger, durable watch/held/closed list, and **unchanged frozen Frank signal/notification layer**, plus actual GMGN public functional research and accuracy/replay/AI review/real Mac acceptance plan.
- [Single-mode manual CA requirements](meme/ca-analysis-unified-accuracy-acceptance.md): separate CA research redesign.

**Gate:** requirements/data architecture complete, source backfill **incomplete**, code **not implemented**, no post-design tests, no Mac deployment, no live automation/trading change. Do not promote this design to a shipped dashboard feature.

## Canonical module files

Frank / Meme:
- `meme/FRANK_LOCAL_SIGNAL_V1_POLICY.md`
- `meme/FRANK_HISTORICAL_MULTIPLE_DELIVERY_E2E.md`

Monster:
- `local-agent/PHASE_MONSTER_D1_V3_REDESIGN_REPORT.md` (historic V3 failure)
- [Monster V4 research PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30) (research only, not in main)

NFT:
- `watchlists/nft-mint-radar.md`

Global policy:
- `MISSION_SPEC.md`
- `STATUS_SCOPE_2026-10-04.md`

## Repository organization

Long-form human research is organized under:
- `research/projects/`
- `research/tokens/`
- `research/memes/`
- `research/nfts/`

Operational state remains under:
- `portfolio/`
- `performance/`
- `state/`
- `positions/`
- `watchlists/`
- `signals/`
- `runs/`
- `reports/`

Do not move an operational authority path merely for cosmetic organization; path changes require compatibility and validation.

## Audit naming

Automatic run convention where a runtime is actually enabled:
- `runs/YYYY-MM-DD/HHMMSS-start.md`
- `runs/YYYY-MM-DD/HHMMSS-final.md`

Older immutable audit records remain historical evidence.

A scheduler timestamp alone is never proof of a successful run.

## Scope rule

Mission operational files answer:
- what is currently held;
- which module is LIVE / PAUSED / BLOCKED / DEFERRED;
- which frozen rule or threshold is authoritative;
- what factual state changed;
- which runtime owns delivery.

Current status must never be inferred from stale historical checkpoints when a newer canonical status file exists.
