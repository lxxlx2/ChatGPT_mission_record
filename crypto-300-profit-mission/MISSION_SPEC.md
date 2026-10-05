# Crypto Profit Mission

Updated: 2026-10-04
Timezone: Asia/Bangkok

## Authority

This file defines global Mission policy and current authority boundaries.

Current scope/status detail:
- `STATUS_SCOPE_2026-10-04.md`

Current-state precedence:
1. `MISSION_SPEC.md`
2. `STATUS_SCOPE_2026-10-04.md`
3. `portfolio/current.md` and `state/latest.md`
4. active `positions/*.md`
5. active module policy/watchlist files
6. historical/background strategy and immutable reports

A newer dated scope/status file supersedes older dated scope snapshots. Historical reports remain evidence for what happened but do not override a newer current-state authority.

Never use stale chat values or older Git snapshots to overwrite newer verified state.

## Objective

Core objective remains to grow the Mission starting asset set toward **3,000 USD-equivalent net liquidation value** while preserving auditable provenance.

Starting-set provenance includes:
- **300 USD cash principal**;
- the original six Credits NFTs: #21646, #21753, #22857, #23042, #23232, #23328.

All six Credits are now historical exited assets; fresh current ownership is zero. Their starting-asset provenance remains relevant to Mission performance accounting.

Execution remains manual unless the user explicitly authorizes a transaction.

`PRODUCTION_TRADING = NO_GO`.

## Canonical wallets and data truth

Primary EVM wallet:
`0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`

Primary Solana wallet:
`BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

Primary Sui wallet:
`0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

Preferred connected broad-chain app:
- Alchemy `ChatGPT Crypto Monitor All Chains`, app id `h6m5pairkgzet7vz`.

Labels:
- `DIRECT_CHAIN`: fresh supported RPC/API result;
- `USER_CONFIRMED`: latest explicit user statement/screenshot for a source not directly readable;
- `MARKET`: fresh public market data;
- `UNAVAILABLE` / `UNRESOLVED`: do not estimate.

Rules:
- provider failure = unavailable, not zero;
- never reuse an old wallet balance and call it fresh;
- unknown/spam assets remain outside NAV until identity/value are verified;
- public market data cannot overwrite private-venue fill, quantity, margin, PnL or order state;
- wallet balance changes are not PnL without transaction/cost-basis evidence;
- historical snapshots belong in Git history or immutable reports, not `state/latest.md`.

Sui note:
- current generic connected portfolio method does not accept the canonical Sui address format;
- until a supported Sui-native endpoint is used, fresh Sui state must not be labeled `DIRECT_CHAIN`.

## Current Mission module map

### Frank / Meme — LIVE

Status:
`FRANK_LOCAL_SIGNAL_V1_LIVE`

Current authority:
- Frank only;
- local deterministic runtime owns chain collection, classification, stage evaluation, dedupe and delivery authority;
- GPT is not in the Frank signal critical path;
- other persons and TOKEN_CONSENSUS are deferred.

Canonical policy:
- `meme/FRANK_LOCAL_SIGNAL_V1_POLICY.md`

Signal delivery:
- `ACCUMULATION` -> local macOS notification;
- `MULTIPLE` -> local macOS notification + standalone Gmail;
- same person/mint/episode/stage is deduped;
- Gmail Sent readback and durable receipt are part of delivery correctness.

Frozen ACCUMULATION mapping:
- within 60 minutes >=2 confirmed ACTIVE BUYs;
- cumulative raw USDC quote >=25,000;
- the old single-large-buy Path C branch is explicitly **not** ACCUMULATION.

MULTIPLE keeps the frozen V1 conviction/persistence/inventory/distribution/HFT/stale predicates. Do not silently change thresholds from live data.

Latest historical delivery acceptance:
- STONK historical frozen-V1 MULTIPLE E2E passed;
- replay -> historical-test local notification -> one historical-test Gmail -> Sent readback -> dedupe -> crash recovery;
- live scanner remained isolated and gap-free;
- no policy threshold was tuned against the test.

Evidence:
- `meme/FRANK_HISTORICAL_MULTIPLE_DELIVERY_E2E.md`

### NFT opportunity radar — PAUSED

Status:
`SPEC_PRESENT / RUNTIME_PAUSED`

Specification:
- `watchlists/nft-mint-radar.md`

The radar design remains preserved, including issuer identity verification, opportunity gates, security/risk checks and discovery-source policy.

Current authority:
- there is no active Mission scheduler/LaunchAgent that may claim hourly NFT opportunity coverage;
- no automatic NFT opportunity Gmail is currently authorized through the paused Mission umbrella task;
- NFT research may still be performed interactively on user request.

Current NFT holdings are separate from the radar:
- Credits current owned count: 0;
- UNICRED current owned count: 0;
- INK #372 remains prior-known inventory but was not freshly ownership-verified/marked in the 2026-10-04 refresh.

### MONSTER / 妖币 — FROZEN

Status:
`RESEARCH_FROZEN / VALIDATION_NOT_PASSED`

Latest authority:
- `local-agent/PHASE_MONSTER_D1_V3_REDESIGN_REPORT.md`

Current result:
- `MONSTER_D1_V3_TRAIN_PASS`;
- frozen winner V3-062;
- TRAIN median/p95 candidate entities/day: 89/127;
- TRAIN >=5X: 19/20;
- TRAIN >=10X: 6/7;
- >=20X 2/2 is descriptive only;
- once-only 2024 validation: `INSUFFICIENT_DATA + CEILING_FAIL`;
- 2024 median/p95 101/152 exceeds unchanged 100/150 ceiling;
- D2 `BLOCKED_VALIDATION_NOT_PASSED`;
- D3 `NOT_STARTED`;
- Monster LaunchAgent = 0;
- no live Monster Gmail/scanner authority.

The exposed 2024 validation set must not be reused to tune or reselect a V4 winner. No automatic V4/D2/D3 work is authorized.

### CORE PRICE / overall-market trend — PAUSED

Status:
`PAUSED`

This is the previously paused “整体走势” module. It refers to the old price-abnormality monitoring system, not to an ad-hoc analysis of recent BTC/ETH/SOL market movement.

Legacy task:
- `$300 Crypto资产状态监控`: disabled.

Stored intended universe if explicitly restored:
- BTC
- ETH
- SOL
- HYPE
- BNB

Prior stored threshold/model work remains historical engineering state. Current status does not authorize:
- live CORE PRICE polling;
- current market classification;
- CORE PRICE Gmail;
- new thresholds/model tuning.

Do not claim this module is providing coverage while paused.

## GPT Mission task state

Umbrella task:
- `$300-3000`: **PAUSED on 2026-10-04**.

Reason:
- Frank/Meme authority moved fully local;
- Monster is frozen;
- NFT runtime is paused;
- CORE PRICE is paused;
- other persons/consensus are deferred.

The task therefore had no substantive currently authorized lane and was paused rather than retained as a silent hourly no-op.

Rules:
- do not create a replacement Mission task;
- do not re-enable the legacy `$300 Crypto资产状态监控` automatically;
- future task/module restoration requires explicit user authorization and a concrete scope.

This pause does **not** modify independent tasks such as Crypto Daily, the all-project Airdrop/TGE monitor or the US-stock morning report.

## Current portfolio authority

Current holdings:
- `portfolio/current.md`
- `state/latest.md`

Latest 2026-10-04 chain refresh materially confirms:
- Solana USDC `142.162136`;
- Solana SOL `0.003093645`;
- Ethereum USDC `1.006555`;
- Ethereum ETH `0.000634360344095958`;
- Base ETH `0.000967183780184779`;
- Ink ETH `0.011133212494942321`;
- Credits current owned count `0`;
- UNICRED current owned count `0`.

SUI remains 0 by latest explicit user-confirmed state but was not freshly readable through the connected generic method.

Latest private/off-chain values carried forward with their labels:
- Binance available balance: `$523.72`, USER_CONFIRMED, not independently refreshed in the chain scan;
- Legion/JUMP pending capital: `$1,000`, USER_CONFIRMED / PENDING_ALLOCATION.

Displayed current asset reference is approximately `$701.13` liquid/available plus `$1,000` pending JUMP, for approximately `$1,701.13` tracked reference, excluding sub-$1 dust and unpriced/unverified inventory. This is not Mission PnL.

## Position state rules

Closed/cleared current exposures must not consume routine Mission runtime merely because historical files exist.

Currently closed/cleared examples include:
- Credits current inventory: 0;
- UNICRED #230: not owned;
- PONS perpetual/spot: closed;
- XRP / Variational: closed;
- prior zero-balance meme sleeves: historical only;
- SUI: 0 by latest user-confirmed state.

JUMP remains a pending/committed-capital item until allocation/refund is verified.

Do not originate new positions, order levels, stops, leverage or allocation from an automatic monitor.

## Wallet refresh policy

Routine scheduled wallet polling is disabled.

Refresh `portfolio/current.md` / `state/latest.md` only:
- on explicit user request;
- after a user-reported material wallet action;
- when a verified event requires an ownership/balance check.

A failed or unsupported chain query must stay `UNAVAILABLE`; never copy an old value forward as if freshly verified.

## Notifications and delivery

Default for paused/non-live modules: no claim of monitoring and no alerts.

Frank is the only live Mission signal-delivery module under this spec:
- ACCUMULATION local notification;
- MULTIPLE local notification + standalone Gmail.

Frank signal delivery is deterministic and does not require GPT SEND/NO_SEND.

Historical/dry-run signals must never be mistaken for live signals. Historical delivery tests require an explicit `HISTORICAL TEST` identity/namespace.

Operational/runtime failures must not be disguised as market signals.

## Research organization

Long-form research:
- `research/projects/`
- `research/tokens/`
- `research/memes/`
- `research/nfts/`

Reusable project analysis:
- `PROJECT_ANALYSIS_FRAMEWORK.md`
- `token_trading_principles.md`

Operational state:
- `portfolio/`
- `performance/`
- `state/`
- `positions/`
- `watchlists/`
- `signals/`
- `runs/`
- `reports/`

Do not move operational authority paths solely for repository cosmetics.

## Performance accounting

Authority:
- `performance/current.md`

Rules:
- wallet balance alone is not PnL;
- internal transfer is not profit;
- listing ask is not executable NAV;
- private-venue PnL stays USER_CONFIRMED unless directly readable;
- pending committed capital is not liquid cash;
- historical sale proceeds and current balances must not be double-counted;
- unknown cost basis/proceeds remain unresolved rather than estimated.

## Hard boundaries

- no autonomous trade execution;
- no wallet mutation/signing;
- no new Mission automation/task without explicit user authorization;
- no automatic restoration of NFT/Monster/CORE;
- no automatic new tracked person;
- no silent threshold tuning from forward outcomes;
- no claim that a paused module is running;
- `PRODUCTION_TRADING = NO_GO`.
