# $300 Crypto Automatic Runtime

Updated: 2026-09-28 17:58 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_TELEMETRY

Authority for the existing :29 task.

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
