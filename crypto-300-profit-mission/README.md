# $300-3000 Crypto Mission

Updated: 2026-10-15 (Oct 15 portfolio pointer/screenshot and finalized source; module operational authority unchanged)
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

**Latest user-reported and direct-chain asset observation: 2026-10-15, 17:46–17:50 Asia/Bangkok** ([portfolio source](portfolio/current.md), [current state](state/latest.md)):

- **Binance investment reserve:** Flexible Earn **776.01087688 USDC**, current Alchemy USDC/USD 1.00106 reference **~$776.83**, from user screenshot (not live Binance account API). Screenshot real-time APR 2.09%, yesterday reward 0.07794003 USDC and cumulative 1.34887353 USDC already included. Do not double-add interest.
- **Canonical Solana direct finalized chain:** **501.630372 USDC** (USDC price 1.00106 → ~$502.16), **0.012905142 SOL** (SOL price $102.15 → ~$1.32), **0 GANG**. Finalized slots 457210185/457210186. USDC quantity rose **29.913613** vs Oct 13; do not treat the amount as verified trading profit. Four Token-2022 mints with no reliable price are unpriced/excluded rather than assumed $0.
- **Identified newly observed investment USD reference:** **~$1,280.31** (Binance + direct Solana only, with ~17:50 USD pricing; asynchronous observation times). If **old Oct 12** OKX screenshot ETH 0.002403 and TRX 3.3847 were still held, today's quotes would yield a **mixed-freshness conditional ~$1,287.12**. Neither is a full audited cross-account NAV; screenshot OKX Solana assets are duplicate holdings. Exact user-controlled cashflows, CEX balances beyond provided screenshots, Sui owner balance, and some EVM ERC-20 are unresolved.
- **Bybit life/rent only, wholly excluded:** screenshot total **474.425221 USDC** (Earn 438.953400, Funding 35.385365, Unified 0.086456); app USD estimate **~$474.94**. Record for household funds only, **do not add to investment portfolio** even though account-wide value >$1.
- **Canonical EVM:** separate native balances each <$1 across rechecked networks, excluded by the permanent per-position threshold. Robinhood SurfBoard **NFT #5396** ownership reconfirmed direct-chain; NFT liquid USD value unpriced, not inserted into NAV. ERC20 availability partial; Sui current data unavailable. 2026-10-15 Surf entitlement/reveal/pending-right history retained in [portfolio](portfolio/current.md).
- **GANG:** Oct 12 fully exited, realized loss **−96.210562 USDC before SOL gas** separately reported in [performance](performance/current.md). Overall original $300 Mission PnL **UNRESOLVED**. Current asset balance increases are not necessarily realized trading profits.

**Permanent accounting contract:** Only add each independently priced identifiable asset >= $1; omit dust individually. Unknown/illiquid/contract-restricted NFTs and claim rights are documented separately without guessed executable marks. `PRODUCTION_TRADING=NO_GO`. No new tasks, trade actions, monitoring or activation of paused lanes.


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
