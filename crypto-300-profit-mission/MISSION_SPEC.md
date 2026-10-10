# Crypto Profit Mission

Updated: 2026-10-10
Timezone: Asia/Bangkok

## Authority

This file defines global Mission policy and current authority boundaries.

Current dated scope history:
- `STATUS_SCOPE_2026-10-04.md` is an immutable 2026-10-04 historical snapshot. For more recent operational facts, see `state/latest.md`; for live balances see `portfolio/current.md`.

Current Frank/Meme operational status:
- `meme/MISSION_MEME_CURRENT_STATUS_2026-10-07.md`

Current-state precedence:
1. `MISSION_SPEC.md`
2. `STATUS_SCOPE_2026-10-04.md`
3. `portfolio/current.md` and `state/latest.md`
4. active `positions/*.md`
5. active module policy/watchlist files
6. historical/background strategy and immutable reports

A newer dated scope/status file supersedes older dated scope snapshots, and current mutable status pointers override older dated snapshots for facts updated since their dates. Historical reports remain evidence for what happened but do not override a newer current-state authority.

Never use stale chat values or older Git snapshots to overwrite newer verified state.

For current balances, CEX holdings, refunds and capital classifications, use the **latest dated** `portfolio/current.md` and `state/latest.md` over historical dated STATUS_SCOPE snapshots. This does not relax Mission policy/authority boundaries.

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

Mandatory asset display/valuation rule, effective as a continuing Mission policy:
- **Only independently priced, individually identifiable positions with current supportable USD market value >= $1.00 are included in displayed holdings and USD marked subtotals.** Each position worth < $1.00 is excluded individually; never combine multiple dust items to manufacture a qualifying position. At exactly $1.00 the item qualifies.
- A token/NFT whose price or identity cannot be independently verified remains `UNPRICED/UNRESOLVED`, excluded from liquid NAV but not relabeled as zero or proven under $1. Treat scam/claim-bait as excluded.
- This is a **presentation and marked-assets rule**, not authorization to erase transaction history or historical cost, or to ignore dust-related fees when reconstructing actual PnL.
- Binance CEX current amounts require a new authenticated read or user screenshot; historical screenshots remain dated. Bybit is fully excluded as reserved personal cash.
- Wallet portfolio coverage may be incomplete. A failing or truncated token enumerator must never silently imply there are no further holdings.

Sui note:
- current generic connected portfolio method does not accept the canonical Sui address format;
- until a supported Sui-native endpoint is used, fresh Sui state must not be labeled `DIRECT_CHAIN`.

## Current Mission module map

### Frank / Meme — LIVE

Status:
`MISSION_MEME_LIVE_NOTIFICATION_V1`

Current operational authority:
- Frank only;
- Frank production remains the deterministic chain/classification/pattern source;
- Mission Control reads Frank production read-only and owns current follow-decision / local+Gmail delivery state;
- GPT is not in the Frank signal critical path;
- other persons and TOKEN_CONSENSUS remain deferred;
- automatic trading remains forbidden.

Current operational handoff:
- `meme/MISSION_MEME_CURRENT_STATUS_2026-10-07.md`

Canonical Frank V1 policy:
- `meme/FRANK_LOCAL_SIGNAL_V1_POLICY.md`

Approved Mission Control follow policy:
- `local-agent/config/follow_policy_v1.approved.json`
- `status = FROZEN_APPROVED`
- `live_delivery_approved = true`
- approved policy SHA256 must match the explicitly pinned runtime hash.

Current functions:
- ACCUMULATION / MULTIPLE reading from frozen Frank V1;
- REENTRY_WATCH for confirmed CLOSED -> REENTRY episodes, WAIT-only until the frozen signal model independently qualifies;
- Jupiter official executable quote;
- deterministic `BUY / SMALL_BUY / WAIT / NO_BUY`;
- Chinese localhost Dashboard;
- local macOS + Gmail live notification for eligible Decision transitions;
- separate `mission-control.sqlite` audit state;
- 60-day observation retention;
- Gmail Sent readback / dedupe / ambiguity handling;
- LaunchAgent autostart for Mission Control loop and Dashboard after user login;
- runtime approved-policy copy under `~/Library/Application Support/FrankMeme/` to avoid macOS Documents/TCC denial.

Latest local acceptance evidence supplied by the user:
- earlier local-agent suite: `706 passed` (historical Oct 7 acceptance only; later PR reviews/tests are in the operational handoff);
- Mission Control health `status = OK`;
- `delivery_allowed = true`;
- Dashboard HTTP 200;
- Mission Control loop LaunchAgent `state = running`;
- Dashboard LaunchAgent `state = running`;
- Gmail OAuth readiness PASS;
- `PRODUCTION_TRADING = NO_GO`.

Remaining Frank validation gaps are tracked in the current operational handoff. In particular, do not silently claim that real SOL normalization, a real Jupiter NO_ROUTE fixture, first real post-enable Mission Control Gmail send, or actual reboot/login recovery have passed until evidence exists.

Frozen ACCUMULATION mapping remains:
- within 60 minutes >=2 confirmed ACTIVE BUYs;
- cumulative raw USDC quote >=25,000;
- the old single-large-buy Path C branch is explicitly **not** ACCUMULATION.

MULTIPLE keeps the frozen V1 conviction/persistence/inventory/distribution/HFT/stale predicates. Do not silently change thresholds from live data.

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

### MONSTER / 妖币 — V4 RESEARCH-ONLY; NO LIVE AUTHORITY

Status:
`V3_VALIDATION_NOT_PASSED / V4_RESEARCH_DRAFT_PR_30 / NO_MONSTER_RUNTIME`

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

The exposed 2024 validation set must not be repackaged as an untouched V4 holdout. V4 **read-only research** is proceeding in Draft PR #30 at `research/monster-v4-local-discovery-20261010`; completed historical studies do **not** establish a profitable or independently validated buy model. No automatic production V4 scanner, LaunchAgent, Gmail, D2/D3 promotion or trading is authorized.

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
- Monster V4 has read-only research but no authorized live runtime;
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

Canonical mutable operational positions and capital classifications:
- `portfolio/current.md`: **2026-10-10 independently rechecked chain asset snapshot**, with explicit chain coverage, Binance and Bybit screenshot freshness, the per-asset $1 filter and unsettled GANG escrow.
- `state/latest.md`: **2026-10-10 current module and asset pointer**.
- `performance/current.md`: current Mission starting-capital provenance and profit reconciliation status; **Mission realized PnL and $3,000 target progress remain UNRESOLVED**.
- `positions/gang.md`: 500 USDC Backable Solana escrow (still committed in 2026-10-10 account read; final claim/refund unknown).
- `positions/jump.md`: sale rejected, **1,000 USDC refunded and no current position**.
- `positions/credits.md`: six original Credits exited; current count **0**, reconfirmed 2026-10-10.
- `positions/unicred.md`: UNICRED owned count **0**, reconfirmed 2026-10-10.

Asset marks, not PnL:
- At the verified 2026-10-10 chain/price snapshot, material Solana holdings are 58.047629 USDC and 0.038163041 SOL, combined **~$62.31**. All independently priced EVM native balances examined were individually below $1; token/NFT completeness remains **UNRESOLVED** owing to truncated/rate-limited coverage.
- Latest private Binance screenshot (2026-10-09) showed USDC Earn with **~$656.07** display mark; it was **not independently refreshed October 10**. A mixed-freshness indicative reference is **~$718.38**, **not** verified comprehensive NAV or $300 Mission return.
- Entire Bybit account is for living expenses/rent and **excluded**; 2026-10-09 screenshot was ~353.173611 USDC (~$353.42 UI).
- GANG 500 USDC commitment is historical encumbered cost **outside** the above liquid balance. No claim/refund allocation is yet established; no double count.
- Sui = 0 by latest `USER_CONFIRMED` state only; no fresh Sui-native RPC was obtained in this sweep.

Historical 2026-10-04 `STATUS_SCOPE` balances and historical strategy plans are not current holdings. All performance attribution needs original Mission cashflows plus six exited Credits, without inventing profits from wallet transfers.

## Position state rules

Closed/cleared current exposures must not consume routine Mission runtime merely because historical files exist.

Currently closed/cleared examples include:
- Credits current inventory: 0;
- UNICRED #230: not owned;
- PONS perpetual/spot: closed;
- XRP / Variational: closed;
- prior zero-balance meme sleeves: historical only;
- SUI: 0 by latest user-confirmed state.

JUMP is closed: its prior 1,000 USDC sale deposit was refunded and its allocation is zero. GANG remains a separate pending 500 USDC escrow until settlement evidence is obtained.

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
