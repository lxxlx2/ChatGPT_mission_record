# $300-3000 Crypto Mission

Updated: 2026-10-17 (newest CEX screenshots, finalized Solana chain, SurfBoard NFT exit; module operational authority unchanged)
Timezone: Asia/Bangkok

Current mutable facts: [`MISSION_SPEC.md`](MISSION_SPEC.md), [`state/latest.md`](state/latest.md), [`portfolio/current.md`](portfolio/current.md), [`performance/current.md`](performance/current.md). Historical 2026-10-04 scope: [`STATUS_SCOPE_2026-10-04.md`](STATUS_SCOPE_2026-10-04.md).

## 开发主线规则

Frank/Meme V2 必须按 [Mission 开发主线与停止规则](../docs/DEVELOPMENT_MAINLINE_RULES.md) 推进：D0 真数据基线 → D1 事实账本 → D2 持仓/观察池 → D3 跟单辅助及 GMGN 同口径核对 → D4 集成及真实 Mac 整体验收。现有运行进展与 Draft PR 不能替代任何未完成的阶段出口；停止重复已获独立批准的 C02/503 截图和非阻断 P3 循环。

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

**Latest CEX screenshots and directly rechecked wallet reference: 2026-10-17, 17:27–17:30 Asia/Bangkok** ([full asset ledger](portfolio/current.md), [state](state/latest.md), [Surf transaction performance provenance](performance/current.md)):

- **Binance Flexible Earn:** **816.18870429 USDC**, screenshot UI **~817.24 USDT**; at Oct 17 17:27 Alchemy USDC/USD **1.00126** → **~$817.22** indicative USD market mark. Cumulative interest **1.52670094 USDC** already included. Binance is investment capital and counted once.
- **Direct Solana finalized:** **607.524474 USDC** (mark **~$608.29**) and **0.0279625 SOL** (mark **~$2.93**), **GANG 0**; Alchemy finalized slots **458003718/458003719**, SOL/USD **104.71**. Four indivisible one-unit Token-2022 mints unpriced, not assumed $0. Solana USDC up **105.894102** since Oct 15 but source/PnL not established.
- **Directly marked investment reference:** **~$1,428.44** for Binance plus canonical Solana, with dated screenshots and asynchronous chain observations. Historical unverified Oct 12 OKX 0.002403 ETH + 3.3847 TRX would give a **mixed-freshness conditional ~$1,435.42** at Oct 17 prices; not complete real-time NAV. No double-counting of older OKX Solana or recently sold NFT.
- **Bybit household/rent only:** screenshot **493.683808 USDC**, app estimate **~$494.32**; Earn 473.286900, Funding 20.310452, Unified 0.086456, **entire account excluded from investment assets**.
- **SurfBoard #5396 sold/transferred from canonical wallet:** Seaport Robinhood Chain direct transaction **[0xb222259e...dde91e9](https://explorer.robinhood.com/tx/0xb222259e480d4b9264af49cbbcd9709b7296d0ee35aec35b264fff35fdde91e9)** on Oct 17 03:34 Bangkok confirms transfer to another owner. `OrderFulfilled`: total gross 0.04 ETH, seller consideration **0.0376 ETH**, followed by **0.03783 ETH** wallet outbound to another address at 05:01 Bangkok. Current Robinhood native balance < $1. No retained NFT position and no duplicated sale proceeds; NFT actual net economic PnL unresolved, earlier Surf membership service $228 not automatically an NFT basis. Historical Oct 15 ownership remains correctly preserved as a dated snapshot.
- **Other EVM/Sui:** latest EVM native sweep across thirteen networks all individually < $1 and excluded; token inventories incomplete/unpriced. Sui current native balance not obtained; old zero remains historical only. No unsupported zero assumptions.
- **Permanent accounting policy:** include only independently marked individual holdings >=$1; Bybit never included; unknown price/claim/NFT excluded without guessing. Oct 15 investable reference ~$1,280.31 vs Oct 17 ~$1,428.44 **+~$148.12 snapshot delta**, **not Mission realized profit**. Existing GANG loss **−96.210562 USDC before SOL gas** unchanged. `MISSION_PNL_UNRESOLVED`, `PRODUCTION_TRADING=NO_GO`; no trades, wallet signing, task, Gmail, monitor, or runtime changes by this research.


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
