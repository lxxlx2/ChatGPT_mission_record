# $300-3000 Crypto Mission

Updated: 2026-10-10
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

The latest **2026-10-10 read-only wallet refresh** directly confirmed:
- Solana USDC **58.047629**, SOL **0.038163041**; approximate independently marked subtotal **~$62.31**.
- Ethereum Credits owned **0**; Unichain UNICRED owned **0**.
- Other checked EVM native assets individually < $1; full ERC-20/NFT completeness remains **UNRESOLVED** where provider responses were truncated or blocked.
- Binance Earn **~$656.07** is the last **2026-10-09 user-screenshot value**, **not** a new private-account reading.
- Bybit **~$353.42 UI** is separate personal rent/living cash and excluded from Mission capital.
- GANG **500 USDC** committed escrow is distinct from liquid funds, final rights unresolved; JUMP refunded and closed.
- Sui = 0 by user confirmation, not by a fresh Sui-native query.

**Permanent marked-asset display rule: value each separately identifiable asset; include only reliable USD values >= $1.00, exclude values < $1.00 without summing dust.** Unknown prices remain unresolved, not zero. See `MISSION_SPEC.md`.

The ~**$718.38** combination of fresh chain ~$62.31 plus historical Binance screenshot ~$656.07 is **mixed-freshness indicative invested assets**, not verified comprehensive NAV or Mission PnL. Mission performance attribution remains unresolved in `performance/current.md`.

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
