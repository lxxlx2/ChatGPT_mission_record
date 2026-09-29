# $300 Crypto Automatic Runtime

Updated: 2026-09-29 17:35 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_TELEMETRY

Authority for the existing :29 task.

## Highest-priority scheduler compaction override — 2026-09-29 19:52

This override supersedes older multi-read / multi-file scheduler persistence rules.

### $300 hourly task
- sole GitHub startup state: `state/hourly-final-bundle.md` schema_version 2;
- startup GitHub reads: exactly one file fetch, except one retry of the same repo/path after fetch failure;
- scheduled cycle must not pre-read this runtime doc, Frank watchlist, Monster/NFT watchlists, portfolio, or per-lane GitHub state;
- frozen lane rules are embedded in the automation prompt and a compact execution contract in the rolling file;
- entire cycle permits at most one GitHub mutation: existing-file update of `state/hourly-final-bundle.md`;
- Git commit history is the per-cycle audit trail;
- infrastructure failure leaves the rolling state unchanged and is user-silent.

### Frank 30D replay task
- sole scheduled checkpoint: `state/frank-30d-checkpoint.md`;
- the large `research/frank-30d-replay-state.md` is archival/manual history and must not be rewritten by scheduled runs;
- every scheduled run processes exactly 10 contiguous signatures from the compact checkpoint;
- 10/10 complete with zero unresolved/provider gap is required before one existing-file update;
- compact checkpoint stores only cumulative counters/current cursor/current last_chunk; commit history preserves prior scheduled chunks;
- PHASE 3 must merge compact checkpoint commit history with archival/manual checkpoints before historical signal simulation.


## Highest-priority rolling durability override — 2026-09-29 17:35

Observed scheduled failure:
- the 17:31 cycle completed CORE, Frank, NFT and Monster calculations;
- its sole attempt to create a new per-run `HHMMSS-final-bundle.md` was blocked by the runtime safety layer;
- therefore computation succeeded but no durable completion proof was created.

Effective immediately, this section overrides all older attempt/final/per-lane persistence ordering below.

Canonical scheduled durable file:
`crypto-300-profit-mission/state/hourly-final-bundle.md`

Scheduled-cycle rule:
1. fetch this existing file and its current blob SHA before work;
2. complete CORE, FRANK, NFT and MONSTER in memory;
3. perform exactly one GitHub mutation by **updating this existing file** with that SHA;
4. do not create attempt, RUNNING, per-lane, per-run final, cursor, NFT receipt, Monster receipt or other GitHub files inside the same scheduled cycle;
5. Git commit history of this rolling file is the per-cycle durable history while this override is active.

The replacement body must contain:
- run_time and scheduled_cycle;
- CORE receipt;
- FRANK cursor_before/cursor_after, signatures_seen, active/passive/unresolved counts, stage result and delivery state;
- NFT source/candidate/result receipt;
- MONSTER due/not_due/full-scan receipt and deferred handling;
- COMPLETION run_status and data gaps.

Authority/recovery:
- only a successful update of `state/hourly-final-bundle.md` makes that cycle authoritative;
- if the update is blocked, the file remains unchanged and the previous cursor/state stays authoritative;
- the next cycle must replay the Frank gap from the cursor in the unchanged rolling file;
- `state/frank-live-cursor.md` is legacy fallback only until a successful rolling bundle exists;
- no infrastructure failure may be relabeled SUCCESS.

This override changes persistence shape only. Frank/Monster/NFT detection semantics remain unchanged.


## Mission scope

Core Mission goal:
- starting asset set = **300 USD cash principal + original six Credits NFTs**
- target = **3,000 USD-equivalent Mission net liquidation value**

Current original Credits holdings:
- #23042
- #23232

The other four original Credits are historical sold assets/provenance.

Private Binance inventory authority:
- combined earn bucket = **682.40 USDT-equivalent**
- PONSUSDT perpetual = **CLOSED**
- no active Binance trading position
- do not invent or carry forward any Binance spot/futures asset without a newer USER_CONFIRMED source.

The 659.9 earn bucket is tracked for asset completeness and remains outside speculative Mission performance unless provenance is explicitly reclassified.

## Audit

The mandatory automatic-run artifact is:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-final.md`

Fallback:
`HHMMSS-final-retry.md`

A scheduler trigger is not proof of success.

A manual reconciliation file is not automatic-run proof.

## Required hourly lanes

Run in this bounded order:

1. **Stored-rule market facts**
   - ETH stored setup facts
   - BTC stored regime facts
   - no PONS position lane while PONS exposure remains closed

2. **Recent Crypto Daily input**
   - read newest two available research/final artifacts
   - no broad duplicate news scan

3. **Monster V2.1**
   - one Binance USD-M bulk screen
   - bounded shortlist
   - deep-check **maximum 3 symbols per hourly run**
   - if a deep source is unavailable, record the gap and continue; do not loop on fallbacks

4. **Persist final immediately**
   - write final/final-retry before any optional work

## Hard reliability guardrail

If any required lane has a tool/source error:
- record the affected lane as unavailable/partial;
- skip expensive fallback loops;
- do not start optional enrichment;
- immediately persist a compact final/final-retry with completed lanes, failed lanes, data gaps and alert state.

A partial factual run with honest unavailable fields is preferable to a missing audit.

No optional state/cache update may run before final persistence.

## Optional / slower work

Only after a final/final-retry exists:
- launch/NFT/FOMO enrichment when upstream evidence contains a plausible candidate;
- UNICRED / Credits market enrichment only when a material project/market event or explicit user request makes it relevant;
- presentation/cache updates.

Optional failure never downgrades a completed final.

## Credits lane

On explicit/manual reconciliation, retain the two DIRECT_CHAIN Credits:
- #23042
- #23232

The original six remain Mission provenance:
- #21646, #21753, #22857, #23042, #23232, #23328

Do not value 0.25/0.40 ETH listing asks as executable NAV.

## JUMP

JUMP is a stored sale/project reserve, not a public market symbol.

Outside a known participation/deadline window:
- record `JUMP_check: not_due`.

During a due window:
- check official sale/deadline/gas facts.

No automatic application or transaction.

## Wallet fallback and classification

Preferred:
- Alchemy/direct RPC for supported chains;
- Blockscout for supported EVM fallback;
- direct Solana RPC for SPL + Token-2022.

Read critical chains independently.

If one chain is unavailable, mark only that chain unavailable.

If market/Monster lanes complete and a wallet provider fails, use `partial_success`, not a fabricated current balance.

Never reuse an old balance and label it current.

## Notifications

Default: silent.

Infrastructure/runtime/source/audit/health problems:
- GitHub audit only
- no Gmail
- no ChatGPT alert

User-visible Gmail + ChatGPT only for a new substantive stored-rule event:
- position stop/TP/event threshold crossing;
- stored ETH setup becomes qualified;
- materially changed WATCH;
- Monster IGNITION or relevant EXHAUSTION;
- material real-asset wallet anomaly;
- material security/solvency/deadline event affecting active capital;
- verified launch/NFT/TGE timing or eligibility change;
- scheduled 19:29 Monster factual daily summary.

No unchanged WATCH/NO_ACTION/ordinary volatility notification.

## Monster persistence

Authority:
`state/monster-squeeze-v2.1-current.md`

For newly confirmed STRUCTURAL_CANDIDATE/PRESSURE:
- first_seen
- setup_price
- current_state
- 7-day expiry

Do not retroactively invent setup_price.

Every automatic final records:
- universe_count
- shortlist
- structural_count
- pressure_count
- ignition_count
- exhaustion_count
- data_gaps

## 19:29 Monster summary

The 19:29 run must actually deliver the factual daily summary by Gmail + ChatGPT.

Subject:
`Crypto Mission｜Monster V2.1 日汇总｜YYYY-MM-DD`

Before sending:
- dedupe Gmail Sent by exact subject.

If missed:
- first later successful same-date run sends once;
- record `monster_daily_summary_recovery: true`;
- record Gmail message_id/readback.

## XRP / Variational

CLOSED.

Do not run XRP/Bitget attacker-flow, XRP TP/SL or Variational monitoring as a Mission hourly lane unless the user explicitly reactivates relevant exposure.


## Scheduler-survival override — 2026-09-27

Observed incident:
- automatic final/final-retry exists at 08:27;
- scheduler metadata later advanced through morning cycles;
- no 09:29, 10:29 or 11:29 completion audit was persisted.

Therefore the following rules override the earlier hourly ordering.

### Phase 0: attempt proof first

The first write action of every scheduled run is:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-attempt.md`

Minimum fields:
- run_time
- automation_id
- status: started
- scheduled_cycle: :29

Only after this write should market/wallet/research tools be called.

The attempt file is diagnostic only. A final/final-retry remains completion proof.

### Phase 1: independent core lanes

Core lanes are independent. Failure in one lane must never cancel the remaining lanes.

Maximum critical work before final persistence:
1. BTC/ETH public facts, using bounded per-symbol calls; PONS position facts are not queried while exposure is closed;
2. read one newest Crypto Daily research/final artifact.

Routine wallet balance polling is intentionally excluded from hourly core work.

For each lane:
- success -> record current data;
- tool/source error -> record `unavailable`;
- do not retry more than once;
- never reuse stale data as current.

After these three lanes, immediately create final/final-retry.

A complete audit with one or more unavailable lanes is `partial_success`.
Use `failed` only when no meaningful core lane completes or final persistence itself cannot be achieved.

### Phase 2: Monster and opportunity enrichment after core final

Hourly Monster scanning is enrichment and must not be able to erase core-run proof.

After the core final exists:
- every 3 hours, run one bounded Monster V2.1 universe screen;
- deep-check at most 3 candidates;
- persist Monster results separately to `state/monster-squeeze-v2.1-current.md` and/or a unique `HHMMSS-monster.md` audit;
- if IGNITION / relevant EXHAUSTION is confirmed, send the stored-rule alert.

At 19:29:
- Monster full screen + factual daily summary is required;
- if it cannot complete, the next successful run performs the existing missed-summary recovery.

On non-Monster hours:
- only refresh already persisted active Monster candidates when cheap;
- do not fetch the whole futures universe.

### Phase 3: slower enrichment

Only after core final:
- JUMP due-window checks;
- launch/NFT/FOMO;
- Credits/UNICRED only when a material event or explicit request makes them relevant;
- cache/state presentation updates.

No enrichment failure changes an already persisted core final.

### Final audit fields

Every core final/final-retry must contain:
- attempt_path
- market_lane
- crypto_daily_lane
- data_gaps
- substantive_event
- notification
- monster_due
- monster_status: pending_after_core / not_due / recovered_separately

This bounded architecture prioritizes durable monitoring proof while retaining Monster coverage on its own cadence.


## Retired meme-position monitors — 2026-09-27

Direct-chain reconciliation confirms:
- SHARTCOIN = 0
- KARDASHEV = 0
- e/acc = 0

These are historical positions only.

While their wallet balances remain zero:
- do not fetch their price, liquidity, pool reserves, holder distribution, creator wallets or dedicated social/news updates in the hourly Mission;
- do not emit stored-rule alerts for them;
- do not include them in active-wallet Token-2022 polling;
- preserve historical position/research files for audit only.

A fresh non-zero direct balance or explicit user instruction is required to reactivate a retired meme-position monitor.

PAID is residual dust only and does not consume an active position-specific lane.

This retirement does not disable general Monster V2.1 or launch-radar discovery for the broader market.


## Cleared meme override — 2026-09-27 12:46

Fresh direct-chain balances:
- Solana PAID: 0
- BNB GSTOCK: 0.096724707311314713 residual dust
- Robinhood PONS: 0.000953441979624353 residual dust
- SHARTCOIN: 0
- KARDASHEV: 0
- e/acc: 0 from prior direct verification

All are treated as economically closed on-chain meme positions.

Hourly Mission rules:
- do not run dedicated price/liquidity/holder/creator/pool/order monitoring for any of these;
- residual dust does not reactivate a position;
- wallet reconciliation may record the raw dust balance without opening a monitoring lane;
- Binance PONSUSDT futures are now closed; no active PONS market lane remains;
- general Monster V2.1 and launch discovery remain market-wide scanners.

Current Solana canonical USDC is 430.483714 and SOL is 0.135926955 as of the 2026-09-28 15:00 finalized scan.


## PONS full-close override — 2026-09-28

USER_CONFIRMED:
- Binance PONSUSDT perpetual: CLOSED
- Robinhood PONS spot: CLOSED_DUST
- Binance inventory: 682.40 USDT-equivalent earn only

Effective immediately:
- remove PONS mark/funding/TP/SL from required hourly core lanes;
- do not emit user-position PONS alerts;
- do not carry old 64-PONS futures state into audits;
- residual Robinhood PONS dust does not reactivate monitoring;
- general Monster / launch discovery may still include PONS as a market-wide candidate.

Full wallet reconciliation should include material NFTs:
- Credits #23042 and #23232 with a current market reference;
- UNICRED #230 with a current market reference;
- exclude aspirational listing asks and spam NFTs from NAV.


## Broad all-chain reconciliation override — 2026-09-28 15:00

Primary wallet provider:
- Alchemy app `ChatGPT Crypto Monitor All Chains`
- app id `h6m5pairkgzet7vz`

Known wallet authorities:
- EVM `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

Do **not** run scheduled broad-chain wallet reconciliation.

Wallet / NFT inventory reads are **manual or event-driven only**:
1. when the user explicitly asks for a wallet reconciliation;
2. when the user tells us they made a material deposit/withdrawal/trade/claim/bridge/NFT action;
3. when another verified event specifically requires confirming ownership or balance.

Do not spend hourly or 3-hour automation budget re-reading unchanged wallet balances.

Do not let an unsupported enhanced token/NFT endpoint hide a native balance. Use independent native-balance RPC reads.

Current special-chain baseline includes:
- Optimism ETH 0.000065278581034767 + USDT 0.000449;
- Polygon POL 0.291295907607284273;
- Avalanche AVAX 0.000678889764814817;
- HyperEVM HYPE 0.000234033730511199 + USDC 0.00172 + USD₮0 0.004646;
- Linea ETH 0.000283128973717299 + LINEA 0.221708425875998735 + REX 0.101880947178375346;
- Monad MON 0.3817997 + canonical USDC 0.024112;
- World Chain ETH 0.000106736504323280 + WLD 0.04;
- MegaETH ETH 0.000082071511230598;
- Plasma XPL 0.009576790735189758;
- Sonic S 0.577025845877296.

Zero-native baseline:
- Berachain / Blast / Mantle / RISE / Scroll / Sei / zkSync.

Aptos/Bitcoin/Starknet/Tron remain `UNAVAILABLE_USER_ADDRESS`. Sui is now canonicalized but currently `UNAVAILABLE_PROVIDER_METHOD` through the generic portfolio API; use a Sui-specific supported endpoint when available.

### Claim-safety rule

A token/NFT received unsolicited is not "money to claim" merely because its metadata says claim/airdrop/reward/compensation.

Never promote such an asset to ACTION without:
- canonical issuer identity;
- official claim path;
- eligibility tied to the user;
- no contract/domain conflict.

Known scam-like examples from the 2026-09-28 scan include Avalanche fake PENDLE/claim-link receipts, Linea compensation-attestation bait, and multiple Optimism/BNB/Polygon/Robinhood claim-style receipts.

Generic wallet balance scanning does not prove protocol-side reward escrow is zero. If a known active protocol position can hold rewards off-wallet, use its protocol-specific contract/dashboard read when due.


### Sui provider rule — 2026-09-28

Canonical Sui wallet:
`0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

Do not pass this 32-byte Sui address to EVM-only generic portfolio endpoints and interpret rejection as zero balance.

Current Alchemy state:
- SUI_MAINNET enabled in the broad app;
- generic `getTokensByAddress` / `getTokenBalancesByAddress` reject the Sui address format;
- Alchemy docs indicate Sui-specific balance methods such as `suix_getBalance` / `suix_getAllBalances`, with JSON-RPC deprecation requiring migration to supported Sui gRPC.

Until a working Sui-specific tool is exposed in the runtime:
- classify Sui wallet balance as `UNAVAILABLE_PROVIDER_METHOD`;
- never carry a stale Sui balance as current;
- never claim there is no Sui asset/claim based on generic EVM portfolio scans;
- do not periodically retry Sui; retry only on explicit user request or a material event.


## Wallet polling policy — 2026-09-28 15:52

User preference: routine periodic wallet rescans are unnecessary. The user will report material wallet changes.

Effective immediately:
- no hourly wallet-balance lane;
- no every-3-hours full-chain reconciliation;
- no daily automatic wallet reconciliation;
- no periodic Sui retry;
- no periodic Credits/UNICRED ownership recheck merely to prove unchanged ownership.

Current wallet state in `portfolio/current.md` / `state/latest.md` is a snapshot, not a continuously refreshed feed.

Refresh wallet state only:
- on explicit user request;
- after the user reports a material wallet action/change;
- when a verified event requires an ownership/balance check to determine eligibility or risk.

Market/opportunity/security/TGE/Monster monitoring remains separate and may continue on its existing event/cadence rules.


## Current portfolio materiality threshold — 2026-09-28 17:58

For wallet snapshots requested by the user:
- omit individual assets/NFTs worth < $0.10 from the current presentation;
- keep historical provenance in Git history;
- spam/unpriced claim-bait remains excluded regardless of nominal token count.

Current USER_CONFIRMED Binance earn authority:
- 382.27204197 USDC
- 300 USDT
- displayed total ~682.40 USDT-equivalent
- no active Binance trading position.


### Monster anti-starvation / due override — 2026-09-28

Regression found with BTWUSDT:
- BTW was explicitly shortlisted on 2026-09-27 12:34 at +17.39%;
- it was deferred solely by the max-3 deep-check budget;
- no durable deferred queue existed;
- subsequent runs repeatedly marked Monster `not_due`, so the candidate was never revisited;
- retrospective market gates show BTW later produced a qualifying squeeze-style breakout window.

Effective immediately:
- `max 3 deep-checks` remains a bounded runtime limit;
- every non-checked shortlist symbol must persist to a durable `DEFERRED_SHORTLIST` queue;
- every due full scan reserves at least one deep-check slot for the oldest deferred candidate;
- candidate starvation is forbidden;
- Monster full screen is due whenever >=3h elapsed since `last_successful_full_scan_at`, regardless of scheduler drift or wall-clock hour;
- 19:29 Asia/Bangkok remains mandatory;
- every completed full screen persists `last_successful_full_scan_at`;
- if a due scan cannot run, record a data gap and retry at the next successful cycle.

BTW is now a prospective PRESSURE watch with setup_price 1.2825. Historical IGNITION is not backfilled because the frozen model forbids reconstructing setup price after the fact.


### 19:22 health-check proof — 2026-09-28

Manual full-universe health-check succeeded:
- 226 Binance USD-M symbols with >=10M USDT 24h quote volume;
- BTW/RARE/QNT/HBAR/MARSCOIN deep-checks completed;
- HBAR newly qualifies as PRESSURE;
- no sampled IGNITION at that moment;
- durable deferred queue now exists in Monster state.

The 19:29 daily full scan remains mandatory regardless of the manual 19:22 scan.


### 19:29 scheduler completion failure — 2026-09-28

The scheduler metadata advanced at approximately 19:31, but by 19:38 there was:
- no new attempt/final/monster GitHub artifact;
- no Monster daily-summary Gmail.

The 19:29 scheduled cycle therefore failed completion proof.

A manual recovery at 19:39:
- ran a fresh bulk Binance USD-M screen;
- deep-checked HBAR/MARSCOIN/QNT and retained BTW context;
- found no current IGNITION;
- sent the required daily summary;
- Gmail id: `1a0e80712e5441b9`.

After this incident, the automation prompt was shortened further so 19:29 does only:
core final -> one bulk screen -> max-3 deep checks -> compact summary persistence -> Gmail/readback.
Optional Alpha/social/on-chain enrichment cannot run before delivery proof.


## Frank wallet conviction lane — 2026-09-29

Authority:
`state/frank-wallet-watch.md`

This is part of the existing hourly :29 $300 Mission task. Do not create a separate scheduler.

Target Solana wallet:
`498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

Run this bounded lane once per hourly cycle after the core final has been persisted and before slower optional enrichment.

Rules:
- parse only active DEX/aggregator swaps by the target wallet;
- ignore plain transfers, airdrops, creator-fee/reward receipts, claims and unsolicited deposits;
- filter rapid execution/HFT patterns;
- WATCH/HFT/NO_ACTION are state/GitHub only and must stay silent;
- only FORMAL_ENTRY / FORMAL_EXIT defined in `state/frank-wallet-watch.md` may trigger user delivery;
- Frank-lane formal delivery is Gmail-only, with no ChatGPT notification;
- a formal signal is not delivered until Gmail Sent/readback is proven;
- failed formal email delivery must persist as pending and be retried before evaluating new Frank alerts on the next run;
- never send a test email for this lane;
- never auto-trade.

The Frank lane must not consume or replace the existing Monster V2.1 schedule or 19:29 summary.


## Frank mandatory completion health gate — 2026-09-29

Regression confirmed:
- Frank lane rules were integrated before 04:29 Asia/Bangkok;
- scheduled $300 runs at 05:25, 06:26, 07:25, 08:32, 09:25 and 11:33 persisted core finals with `frank_lane_status: pending_after_core`;
- 10:28 omitted a completed Frank result;
- 12:33 was the first separate Frank audit and returned `unavailable_source`;
- those runs did not prove the enabled Frank feature executed successfully.

Effective immediately, the $300 run cannot be marked healthy success while Frank monitoring is enabled unless the same cycle has a durable Frank audit.

Mandatory per-cycle Frank completion proof:
- `source_selected`;
- `cursor_before`;
- `cursor_after`;
- `signatures_seen`;
- `active_swaps_verified`;
- `passive_or_reward_filtered`;
- `unresolved_tx_count`;
- `cursor_advanced`;
- stage result: WATCH / PRECONFIRM / SUSPECTED_CONVICTION / EXIT / NO_ACTION / UNRESOLVED;
- `stage_events_persisted`;
- `gmail_delivery_state`.

Health semantics:
- core success + Frank audit success = eligible for overall success;
- `pending_after_core`, missing Frank audit, `unavailable_source`, or unresolved provider failure = overall `partial_failure`, never success;
- source failure preserves the old cursor and next cycle MUST catch up before evaluating only-new activity;
- an unresolved transaction that may be an active swap stalls cursor advancement at that gap until resolved or explicitly classified with evidence;
- a quiet later cycle cannot erase an earlier unresolved gap or pending delivery.

Primary live source is Alchemy Solana mainnet finalized via selected app `mkhr4iorbgonin56`. Current recovery baseline:
- wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`
- signature: `35s2Y8jayg4XjASEWmNmFTAYBqbFE1G2XAc3CmVQG5zxiCZWBRcQFDmyAtvDkQn9deNJhSaxofS6NU34mDtWYtQS`
- slot: `451436899`
- time: 2026-09-29 04:15:07 Asia/Bangkok.

The recovery window must be fully replayed before the cursor is promoted to current head.


## Frank recovery completion — 2026-09-29 13:34 Asia/Bangkok

Historical recovery from slot 451436899 through slot 451550987 is complete and archived at:
`crypto-300-profit-mission/runs/2026-09-29/133400-frank-recovery.md`.

Current durable cursor is authoritative in `state/frank-live-cursor.md` and is now LIVE. Future runs start from the durable cursor with the required 15-minute overlap. The old recovery baseline is fallback provenance only and must not force a full replay on every healthy cycle.


## Priority-lane completion override — 2026-09-29

User priority inside the existing $300 Mission:
1. Frank wallet lane;
2. Monster / meme lane;
3. NFT mint radar.

No new scheduler is created. These three lanes are mandatory health inputs for the existing :29 task.

### Authoritative run phases

Phase A — early durable core proof:
- write attempt;
- run bounded BTC/ETH + newest Crypto Daily input;
- persist core final/final-retry with `run_status: core_persisted`.

Phase B — Frank:
- execute Frank lane every hourly cycle;
- persist a dedicated `HHMMSS-frank.md` audit even for NO_ACTION;
- no Frank audit means the overall cycle cannot be healthy success.

Phase C — NFT:
- execute one bounded NFT discovery pass every hourly cycle;
- persist `radar/nft/YYYY/YYYY-MM/YYYY-MM-DD/HHMMSS.md` even when zero candidates qualify;
- missing discovery proof means the overall cycle cannot be healthy success.

Phase D — Monster:
- evaluate deterministic due rule;
- if due, run full Binance USD-M screen and persist `HHMMSS-monster.md`;
- if not due, persist explicit `monster_status: NOT_DUE` with last successful full-scan timestamp;
- 19:29 remains mandatory regardless of prior manual scan.

Phase E — completion:
- write `runs/YYYY-MM-DD/HHMMSS-completion.md`.
- this completion file is the authoritative overall health result.

### Overall health semantics

`SUCCESS` requires:
- core final/final-retry persisted;
- Frank audit completed with no unresolved provider/cursor gap;
- NFT discovery receipt persisted;
- Monster PASS when due, or explicit healthy NOT_DUE when not due.

`PARTIAL_FAILURE` when any priority lane is missing, unavailable without fallback recovery, or has an unresolved gap.

Core persistence alone is never sufficient to call the entire $300 Mission healthy.

### Completion fields

Every completion file records:
- core_final_path
- frank_audit_path / frank_status
- nft_receipt_path / nft_status
- monster_audit_path / monster_status
- monster_due
- priority_lanes_complete
- pending_delivery_events
- overall_status
- data_gaps

## Frank dual-source resilience — 2026-09-29

Primary:
- Alchemy app `mkhr4iorbgonin56`

Backup:
- Alchemy app `h6m5pairkgzet7vz`

If the primary finalized signature or transaction request fails with 429/timeout/provider-unavailable:
1. preserve the current cursor;
2. select the backup app;
3. retry the exact request once;
4. if backup succeeds, continue and record `source_selected: alchemy_backup`;
5. if both fail, do not advance cursor and mark Frank partial_failure.

Do not loop between providers.

## Monster throughput override — 2026-09-29

This changes runtime budget only. Frozen V2.1 signal thresholds remain unchanged.

On each due full scan:
- one full Binance USD-M bulk screen;
- deep-check maximum **5** candidates;
- if >=2 deferred candidates exist, reserve at least **2 slots for the oldest deferred**;
- remaining slots go to strongest current shortlist candidates;
- every unprocessed shortlist candidate must enter/remain in durable DEFERRED_SHORTLIST;
- every checked candidate gets a terminal result for that scan: promoted / rejected / retained / data_gap.

Every due Monster audit records:
- universe_count;
- shortlist_count;
- deep_checked_count;
- deferred_checked;
- deferred_added;
- deferred_remaining;
- promotions;
- rejections;
- ignition_count;
- exhaustion_count;
- data_gaps.

No candidate may disappear merely because it was outside the deep-check budget.

## NFT mandatory bounded discovery — 2026-09-29

NFT is no longer optional/slower work.

Every hourly :29 run performs one bounded discovery pass after Frank and before overall completion.

Inputs, bounded:
1. latest available Crypto Daily research/final for NFT/Early candidates;
2. one current English discovery pass across recognized marketplace/mint surfaces;
3. one official creator/project/platform verification pass for actual candidates.

Do not deep-crawl every platform when there is no candidate.

Every NFT receipt records:
- sources_attempted;
- sources_available;
- sources_unavailable;
- candidates_discovered;
- identity_verified;
- premint_candidates;
- live_mint_candidates;
- secondary_breakout_candidates;
- rejected_candidates with reason;
- alerts_emitted;
- gmail_delivery_state.

If all external discovery surfaces fail, `nft_status: PARTIAL_SOURCE_GAP`, not `NO_CANDIDATE`.

A zero-candidate result is healthy only when at least one real discovery source plus the latest Crypto Daily input were successfully checked.

Daily at 19:29 also write:
`crypto-300-profit-mission/reports/nft/YYYY/YYYY-MM/YYYY-MM-DD.md`
summarizing discovered / verified / rejected / alerted / source gaps for that Bangkok date.

No new scheduler is allowed.


## Priority-lane tool-budget optimization — 2026-09-29

The three mandatory lanes must fit in one scheduler cycle. Preserve signal semantics while minimizing external calls.

### Frank
- one signature-page request against primary;
- transaction fetch only for unseen/overlap signatures that need classification;
- backup provider only after an actual primary 429/timeout/unavailable;
- no duplicate provider fanout on healthy runs.

### NFT
- read the latest stored Crypto Daily input from GitHub;
- use one batched English discovery search call that can contain multiple queries/surfaces;
- perform official identity verification only for candidates returned by discovery;
- do not enumerate every seed creator separately when there is no candidate.

### Monster
For each due full scan:
1. one all-symbol USD-M 24h ticker call;
2. one all-symbol mark/funding call when needed;
3. select max 5 deep-check candidates using frozen V2.1 prefilters + deferred fairness;
4. for each deep-check use 1h klines and OI history as the default two calls;
5. derive taker-buy share from kline taker-buy volume fields when possible;
6. call dedicated taker/top-trader endpoints only for a candidate that reaches the late-stage IGNITION confirmation boundary or when kline fields are insufficient.

This is a call-count optimization, not a threshold change.
A normal due cycle should aim for <= 15 external market/provider calls after core persistence.

If the external-call budget is exhausted:
- persist completed classifications;
- keep remaining candidates DEFERRED_SHORTLIST or DATA_GAP;
- mark overall partial_failure only if a mandatory lane lacks its required durable receipt.


## Two-write cycle bundle override — 2026-09-29 15:28 Asia/Bangkok

This section overrides earlier per-lane multi-file persistence for the existing $300 automation.

Observed failure: scheduled runs can successfully perform the first one or two GitHub contents writes, then later core/Frank/completion writes are blocked by the runtime safety layer. To keep monitoring reliable, each cycle now uses at most two GitHub contents mutations:

1. create `runs/YYYY-MM-DD/HHMMSS-cycle.md` with `status: RUNNING`;
2. after CORE + FRANK + NFT + MONSTER complete, update that same file once with the full final bundle.

Do not create separate core/frank/nft/monster/completion files in scheduled runtime. The final bundle is authoritative and must contain five sections: CORE, FRANK, NFT, MONSTER, COMPLETION.

Frank cursor continuity:
- read the newest completed cycle bundle with a valid `frank_cursor_after`;
- fall back to `state/frank-live-cursor.md` only when no newer completed bundle exists;
- do not spend a third GitHub write updating the legacy cursor state.

NFT durable receipt:
- the NFT section of the completed bundle is the hourly durable receipt;
- no separate `radar/nft` file is required in scheduled runtime.

Monster/NFT 19:29 coverage:
- include the Bangkok-day coverage summaries inside the 19:29 cycle bundle;
- do not spend additional GitHub writes on separate daily files.

Health:
- RUNNING-only file = UNHEALTHY;
- completed bundle with any missing mandatory lane = PARTIAL_FAILURE;
- SUCCESS only when all mandatory lane semantics pass.

This persistence change does not alter Frank alert thresholds, Monster V2.1 signal thresholds, or NFT alert gates.

## Single-write final-bundle override — 2026-09-29 16:54 Asia/Bangkok

This section supersedes the earlier two-write cycle-bundle rule for scheduled runtime only.

Observed issue:
- later GitHub mutations were repeatedly blocked by the runtime safety layer;
- on 2026-09-29 16:33 even the initial RUNNING write was blocked;
- pre-lane persistence therefore does not improve reliable completion and can consume the only successful mutation opportunity.

Effective scheduled-run rule:
1. perform zero GitHub mutations before CORE + FRANK + NFT + MONSTER are completed in memory;
2. create exactly one `runs/YYYY-MM-DD/HHMMSS-final-bundle.md`;
3. that single file must contain CORE, FRANK, NFT, MONSTER and COMPLETION;
4. no attempt/RUNNING/core/frank/nft/monster/completion/cursor sibling file is created by scheduled runtime;
5. no second GitHub update is attempted in the same cycle.

Frank cursor authority:
- newest successful final bundle with a valid `frank_cursor_after` wins;
- otherwise use `state/frank-live-cursor.md`;
- a cursor calculated in memory is not authoritative until the final bundle write succeeds;
- if the single final write fails, the next run replays from the last durable cursor and deduplicates the overlap.

Health:
- successful final bundle with all mandatory lanes semantically complete can be SUCCESS;
- a blocked final write is UNHEALTHY / partial_failure;
- never convert a persistence failure into NO_ACTION or success.

No monitoring task may be created, deleted, disabled or rebuilt as part of this repair.

