# Crypto Profit Mission — Authoritative Spec

Updated: 2026-09-25
Timezone: Asia/Bangkok

## Authority / precedence

This file is the highest-priority execution specification for the Crypto Profit Mission.

Read order for every monitoring run:
1. `MISSION_SPEC.md`
2. `portfolio/current.md`
3. active `positions/*.md`
4. active `watchlists/*.md`
5. `strategy.md` as legacy/background only

If any lower-priority file conflicts with this spec, this spec wins. Never use stale chat parameters when GitHub has a newer value.

## Mission objective

Primary objective: maximize absolute profit and return on deployed speculative capital over roughly three months while avoiding a single-trade failure that consumes the Mission.

Execution remains manual unless the user explicitly authorizes a transaction. Monitoring, research, calculations, GitHub logging and actionable alerts may be automated.

The separate 500 USD-equivalent low-risk bucket is user-confirmed as currently earning interest. It is excluded from speculative capital and must not be reassigned without explicit approval.

## Canonical wallets

EVM primary wallet:
`0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`

Solana wallet:
`BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

Use connected Alchemy `ChatGPT Crypto Monitor` for direct-chain reads when available. A failed RPC read must be marked unavailable; never substitute an old balance and label it current.

## Latest direct-chain capital reconciliation

Fresh direct-chain read on 2026-09-25:

Ethereum mainnet:
- USDC: 400.308121
- native ETH: 0.001667063838788351

Solana:
- canonical USDC: 390.866576
- native SOL: 0.063112228
- additional wrapped SOL held in SPL token accounts: approximately 0.033891318 WSOL
- SHARTCOIN canonical mint balance: 0

Base:
- canonical USDC: 0.252982
- native ETH: 0.000790846510479134

Unichain:
- canonical USDC: 0.021286
- native ETH: 0.000231941590232335
- CRED: 0

Robinhood Chain:
- native balance: approximately 0.000081643478484768
- unknown/spam ERC-20 balances must not be treated as positions without identity verification.

A small unidentified Solana token balance may exist; keep it outside Mission accounting until identity and value are verified.

Approx direct-chain stablecoin total from the canonical balances above: 791.448965 USDC.

## Current active exposure

### PONS
- Binance PONSUSDT perpetual.
- Total margin budget remains 50 USDT.
- Only the first resting entry at 0.6250 has actually filled.
- Remaining orders stay open:
  - 0.5850, about 49.73 USDT notional.
  - 0.5450, about 59.95 USDT notional.
- Hard stop: 0.4980 Mark Price.
- Do not increase the 50-USDT margin budget.
- Do not move the two resting bids upward just because price rises.

### JUMP / Legion
- 400.308121 USDC is already on Ethereum mainnet and is the conditional application reserve.
- Application target: 400 USDC if authenticated Legion terms remain approximately:
  - 75M FDV,
  - 50% TGE unlock,
  - remaining 50% linear over 4 months,
  - no new material TGE-float / insider-overhang problem.
- If final sale FDV >100M: reduce application target to 250 USDC.
- If FDV >125M: re-evaluate / normally skip.
- If TGE unlock is materially below 50% or a worse cliff/lockup appears: reduce size.
- Do not buy a Polymarket hedge before allocation.
- Application open reference: 2026-09-29 20:00 Asia/Bangkok.
- First Mission run on 2026-09-29 at or after 19:00 Asia/Bangkok must perform a full preflight: authenticated terms, jurisdiction, min/max allocation, Ethereum USDC balance, allowance/approval path and gas readiness.
- Gas rule: current ETH must cover at least 2x the estimated approval + application transaction cost at then-current gas. If exact estimation is unavailable and native ETH remains below 0.003 ETH, issue a preflight top-up warning rather than assuming gas is sufficient.

### ETH
- No live ETH trading position is authorized by this spec.
- Up to 100 USDC remains reserved for a high-quality ETH setup.
- Use the post-expiry setup logic in `strategy.md` only if still valid under fresh market data.
- Do not force an entry simply because capital is reserved.


### XRP / Bitget hack event trade — added 2026-09-26
- Venue: Variational Omni XRP perpetual.
- Current user-confirmed state: **FILLED LONG**.
- Filled position: 77.12 XRP at **1.55589**, isolated 3x.
- Position value at latest screenshot: about 120.96 USD; margin used about 40.99 USDC.
- Attached exit orders remain active: take profit **1.6280**, stop loss **1.5140**.
- Latest user screenshot shows mark 1.56844, unrealized PnL +0.97 USD (+2.42%), liquidation price 1.24430, Omni equity 50.87 USD and available balance 10.55 USD.
- Dedicated position file: `positions/xrp-variational.md`.
- Capital source is the Mission's approximately 141 USDC-equivalent previously uncommitted pool. User explicitly reallocated about 52 USD-equivalent from that pool to Arbitrum/Variational for this event trade and Variational points participation. This is an internal Mission reallocation, not an external contribution and not profit.
- Private venue position state is now user-confirmed by screenshot. Public market data must not overwrite the confirmed fill fields unless the user later updates them or a connected Variational source proves a change.

Hourly monitoring while this order or resulting position is active:
- XRP spot/perpetual mark and 15m/1h/4h candles.
- OI, funding, top-trader positioning and taker buy/sell imbalance.
- Bitget hack-related XRP wallet movements and credible Bitget reserve/replenishment movements when available.
- Track the order/position levels 1.5140, 1.5190, 1.5560, 1.6280, 1.6300 and 1.7000.

XRP Gmail trigger rules. Send only on a NEW trigger or materially changed trigger:
1. rapid price move: absolute 15m move >=2.0%, 1h move >=3.0%, or 4h move >=5.0%;
2. price reaches or crosses 1.5140 stop, 1.6280 take-profit, or 1.6300 event-high breakout area;
3. XRP OI changes >=10% within roughly 1h together with >=1.5% price move, or funding magnitude reaches >=0.05% per 8h, indicating leverage stress;
4. attacker-controlled XRP moves >=5,000,000 XRP toward executable liquidity, bridges or exchange deposit routes, or credible Bitget-controlled wallets acquire/receive >=5,000,000 XRP in a replenishment pattern;
5. any verified security/solvency development at Bitget that materially changes the XRP replenishment or attacker-sale thesis.

When triggered, use connected Gmail to send to lxx.run688@gmail.com. Subject starts with `Crypto Mission 操作提醒｜XRP｜`. Body must include current XRP price, trigger, order/position status as confirmed vs probable, OI/funding when relevant, the concrete action to take, and one-line reason. No trigger means no Gmail and no ChatGPT notification.

### BTC
- No dedicated BTC position or budget.
- BTC is a market-regime / risk-overlay signal only.
- Any new BTC long, short or hedge requires explicit user approval.

### UNICRED
- Active position is UNICRED NFT #230 staked on Unichain.
- CRED liquid token balance is currently 0 and is no longer an active token position.
- NFT acquisition cost reference: 0.0105 ETH.
- On-chain unlock time: 2026-10-01 17:28:04 Asia/Bangkok.
- At the first Mission run at or after unlock, perform a live decision check and alert with one of:
  - remain staked,
  - unstake + hold,
  - unstake + list/sell.
- Decision must use current minted/4444, remaining mint-funded rent, claimable rent, collection executable floor/offer and protocol health.

### Credits
- Credit #23042 listed at 0.25 ETH.
- Credit #23232 listed at 0.40 ETH.
- These are long-duration aspirational listings.
- No fresh Mission capital for additional Credits.

### SHARTCOIN
- Canonical wallet balance is now 0.
- Treat the SHART position as closed for Mission exposure accounting.
- Stop hourly price/liquidity monitoring unless a new user position is opened or a transaction-history reconciliation is specifically requested.

### CRED
- Direct Unichain wallet balance is now 0.
- Stop standalone CRED position monitoring.
- Continue checking CRED only insofar as CRED/buyback economics materially affect UNICRED #230.

## Capital map

From the current direct-chain stablecoin pool:
- 400 USDC: conditional JUMP reserve on Ethereum.
- 150 USDC: hard short-window opportunity reserve, preferably kept liquid on Solana.
- 100 USDC: ETH setup reserve.
- approximately 89 USDC-equivalent: remains uncommitted after the user reallocated about 52 USD-equivalent from the prior ~141 uncommitted pool to the XRP/Variational sleeve. Exact residual remains subject to bridge/swap/gas reconciliation.
- PONS uses its separate 50-USDT margin budget.
- 500 USD-equivalent low-risk interest bucket remains outside the Mission.

Do not automatically consume the 150-USDC short-window reserve for BTC, PONS averaging, ordinary dips, or portfolio housekeeping.

## Monitoring scope

The BSC smart-money cluster / address-copying research is explicitly out of scope for this Mission monitor because it is being handled in a separate workflow. Historical BSC research files may remain for audit, but the main Mission must not spend scan time on BSC cluster research or generate duplicate BSC alerts.

### Fast lane — every hourly run
Check:
- canonical wallet stablecoin/native balances for meaningful deltas,
- PONS price/mark, funding, OI, positioning, ADL and strategy triggers,
- ETH setup validity and BTC regime,
- JUMP readiness / terms until allocation is completed,
- famous/established issuer short-window launch radar,
- NFT mint radar,
- rapid drawdown / security conditions for actual active positions.

### Medium lane — every 3 hours
Check:
- UNICRED protocol economics and #230 rent/unlock state,
- Credits floor/top offer/24h volume/listing ratio and material creator/mechanic changes,
- slower-moving holder/liquidity data that are not needed hourly.

If a medium-lane event is already material/actionable, it may be checked immediately outside the 3-hour cadence.

### Daily reconciliation — first run after 00:00 Asia/Bangkok
Perform a full direct-chain balance reconciliation across Ethereum, Solana, Base, Unichain and Robinhood Chain for the canonical wallet set.
Then reconcile:
- portfolio/current.md,
- active position files,
- state/latest.md,
- reserved capital,
- closed positions.

Do not carry forward stale balances when a fresh direct read is available.

## Opportunity radar rules

Short-window launch and NFT discovery stays hourly because windows may last only 1-3 hours.

A candidate may alert only after:
- canonical issuer identity is anchored,
- official participation/mint/sale path is verified,
- action window is live or imminent,
- no unresolved contract/domain/payment conflict remains,
- expected upside has a plausible reason beyond social hype,
- risk size comes only from the 150-USDC opportunity reserve unless the user explicitly reallocates.

Use English-language and primary sources. Do not use Chinese websites as confirmation sources.

### Blast.fun / Flight 001 watch — added 2026-09-26

Treat Blast.fun as a Sui launchpad opportunity source inside the existing hourly opportunity radar, not as a presumed airdrop farm or dedicated Mission position.

Canonical identity:
- Project: Blast.fun
- Official X: `@blastdotfun`
- Official root domain: `blast.fun`
- Builder/operator context: Interest Labs / Interest Protocol / IPX ecosystem
- Chain: Sui
- Product class: memecoin/social-token launchpad and discovery platform

Current baseline as of 2026-09-26:
- Flight 001 recruiting / launch-code phase is public.
- Mission Control is still offline.
- No verified public launch date/time is available.
- No verified user points program, Season Zero token allocation, platform-token distribution, user airdrop snapshot or claim flow has been established.
- Public Blast.fun code contains creator/LP reward claiming and referral accounting, and an airdrop tool for token issuers; these are not evidence of a Blast.fun user airdrop or platform token.

Hourly monitoring should check official Blast.fun / Interest Labs sources for:
- Flight 001 / Mission Control going live and any concrete access deadline or launch time;
- changes to launch-code / eligibility requirements that affect the user's ability to participate;
- official user-facing points, rewards, snapshot, platform token, airdrop, claim or allocation rules;
- unusually strong launches on Blast.fun that independently clear the Mission opportunity-radar gate, especially established issuers/builders, verified ecosystem-backed launches, or launches with measurable liquidity/attention and a plausible positive-EV entry;
- material security, contract, migration or liquidity issues affecting participation.

Stay silent for:
- ordinary new meme launches;
- additional invite-code marketing without a new economic benefit or deadline;
- generic social hype, follower growth or routine platform updates;
- launches lacking verified identity, liquidity or an explainable edge.

Do not reserve dedicated capital for Blast.fun. Any candidate trade must compete for the existing 150-USDC short-window opportunity reserve and still satisfy the Mission's identity, liquidity, downside and EV gates. Execution remains manual and requires user approval.

### Robinhood Chain / FOMO MEV flow watch — added 2026-09-26

Purpose: treat suspected FOMO MEV / front-run / sandwich activity as an order-flow sensor and execution-cost filter for the Mission. Do not copy-trade the MEV wallet after its transaction is visible; the observed round trips can complete within seconds or blocks and the edge may already be gone.

Chain:
- Robinhood Chain, chain ID 4663.

Seed cluster:
- current observed address: `0xb49deec1a52eea46f3a6a158f8f9b155809b8c44`
- prior observed address: `0x44c0ba0b734d4b7705fcd07ddae9fbbc078d74dd`
- common execution contract observed in both patterns: `0x68a04a63Fd1d8EAbF167EF48ed0A0EF06c2374d9`
- cluster membership must be expanded only from on-chain evidence such as common funding/settlement paths, identical execution contract and transaction pattern, same profit collection, or repeated address rotation. Do not infer ownership from naming or social claims.

Verified baseline examples from 2026-09-25 on Robinhood Chain:
- Protocol: approximately 1,000 USDG out, the same 3,318,036.187... tokens returned, approximately 1,065.421329 USDG back within the same timestamp / a few blocks; gross spread about 65.42 USDG or 6.54% before gas.
- EARNED: approximately 579.942580 USDG out, the same 13,523,596.391... tokens returned about one second later, approximately 609.717726 USDG back; gross spread about 29.78 USDG or 5.13% before gas.
These examples confirm a rapid profitable round-trip pattern. They do not by themselves prove the operator identity, information source, or an internal FOMO/Relay relationship.

Hourly scan requirements:
- inspect seed addresses and newly evidenced cluster members on chain 4663;
- detect sequences where the suspected bot buys a token and sells the same or near-identical quantity within <=5 seconds or <=3 blocks;
- identify intervening third-party buy(s) when observable and estimate victim notional;
- aggregate per token: attacks in 5m/15m, distinct third-party buyers, third-party buy notional, bot gross stablecoin profit, gas/fees when available, estimated extraction %, liquidity/depth, and post-bot-exit returns at 30s/1m/5m/15m;
- track whether price repeatedly absorbs the MEV sell and continues higher or collapses after the extraction;
- use cluster behavior as a negative execution filter when a candidate is being heavily extracted.

Backtest / calibration:
- build a rolling sample before treating this signal as a standalone positive entry edge;
- minimum calibration target: >=30 complete MEV round trips across >=10 distinct tokens;
- record forward returns after bot exit at 30s/1m/5m/15m and after realistic entry slippage/fees;
- until the calibration target is met, MEV flow may strengthen or reject another Mission candidate, but must not by itself authorize a positive trade alert.

Immediate risk / avoid trigger:
- if a Mission candidate or active token shows >=3 suspected MEV extractions within 10 minutes and average extraction >=4%, or realistic entry slippage is estimated >5%, flag it as execution-toxic;
- if the user is about to enter or already exposed, this qualifies as an actionable risk alert.

Positive candidate use after calibration:
- require repeated independent third-party buying, continued positive net flow after MEV selling, adequate executable liquidity, and positive forward-return statistics after costs;
- any positive alert must still pass the Mission identity, venue, liquidity, downside and expected-value gates and must state the exact evidence, sample size and realistic execution cost.

Logging:
- maintain detailed baseline and methodology in `watchlists/robinhood-fomo-mev.md`;
- every Mission run records whether this lane was checked, new cluster addresses, candidate tokens, extraction metrics and alert decision in the immutable run audit.

## GitHub state / audit consistency

Every Mission run must:
1. overwrite `state/latest.md` with the latest authoritative state,
2. create one immutable run audit under `runs/YYYY-MM-DD/HHMMSS.md`,
3. update the daily report only for:
   - a material/actionable change,
   - the daily full reconciliation,
   - a configuration/architecture change.

Do not append routine NO_ACTION text to the daily report every hour.

A run cannot be marked success if the required GitHub write failed. Use `partial_failure` or `failed` and record the exact tool error.

Every `state/latest.md` must distinguish:
- direct-chain current values,
- current market values,
- user-reported values,
- stale last-known values,
- unavailable values.

## Notification policy

Default is silence.

NO_ACTION:
- GitHub only.
- No Gmail.
- No ChatGPT notification.

Notify only for a newly actionable change, major risk, or deadline-sensitive user action, including:
- PONS entry/stop/take-profit/cancel/reduce trigger,
- valid ETH entry/stop/cancel setup,
- JUMP application-size decision or gas/terms preflight issue,
- UNICRED unlock / sell-stake decision,
- Credits repricing only after a real market/mechanic trigger,
- verified high-potential launch/NFT opportunity,
- security event affecting an active position,
- major wallet-balance discrepancy that changes the capital plan.

Do not send duplicate alerts without new information.

### Alert delivery requirement
For every event that validly passes the Mission notification gate:
- send a real Gmail message through the connected Gmail account to `lxx.run688@gmail.com`;
- also return a concise user-visible ChatGPT alert from the automation run;
- Gmail subject format: `[Crypto Mission提醒][event type][asset/project]`;
- body must contain the trigger, current verified data, concrete user action, invalidation/risk, capital source if relevant, and primary/chain evidence;
- if Gmail sending fails, still return the ChatGPT alert and record the exact Gmail error in the run audit;
- if ChatGPT delivery is unavailable, Gmail remains the required external alert path;
- NO_ACTION, rejected candidates and duplicate signals remain fully silent.

This general delivery rule applies to launch/NFT/ICO opportunities, active-position risk, FOMO/Robinhood execution-toxicity, wallet discrepancies, deadlines and other Mission-level actionable events. Asset-specific delivery rules such as XRP may add fields but cannot weaken this requirement.

## Schedule architecture

Keep the main Mission automation hourly at minute 29 Asia/Bangkok.

This intentionally staggers the stack:
- around :00 — broad Crypto research pipeline,
- around :14 — airdrop/TGE monitor,
- around :29 — action-oriented Mission monitor.

The Mission run is the decision layer and should consume fresh information after the broader collection layers have had time to run.


## Opportunity engine / research integration

Every hourly Mission run must read the most recent available files under `crypto-daily/research/` covering roughly the previous 2 hours and convert broad research into Mission-level candidate decisions. The 3-hour medium lane performs a deeper multi-run review, but actionable opportunity discovery must not wait for the medium lane.

Candidate universe includes:
- liquid perpetual / futures setups beyond existing PONS/ETH when there is a clearly defined catalyst, liquidity and invalidation;
- ICO / public sale / Legion-style allocations;
- NFT mints / secondary breakouts;
- established-issuer meme / social-token launches;
- event-driven cross-chain or prediction-market opportunities when execution is realistically available.

For each candidate, require:
- a concrete catalyst or structural edge,
- verified tradable venue / participation path,
- sufficient liquidity and realistic fees/slippage,
- explicit invalidation / downside,
- a plausible expected-value advantage after costs,
- a defined capital source.

Do not manufacture a candidate every cycle. If none clears the gate, record NO_CANDIDATE and remain silent.

New speculative ideas may only use:
- the ~141 USDC uncommitted pool, or
- the 150-USDC opportunity reserve when the event is truly short-window/high-conviction.

JUMP, ETH reserve, PONS budget and the 500 low-risk bucket are ring-fenced unless the user explicitly reallocates them.

Any new derivatives idea outside existing PONS/ETH/BTC monitoring is recommendation-only until the user explicitly approves the capital allocation.

## Performance tracking

Read and maintain `performance/current.md`.

The Mission must track:
- external net contributions,
- realized P&L,
- unrealized P&L,
- open exposure,
- reserved cash,
- closed positions awaiting reconciliation.

Never use raw wallet balance growth as profit because new deposits/transfers may exist.

Update `performance/current.md` on the daily full reconciliation and whenever a position opens/closes, a material take-profit happens, an ICO/NFT allocation is confirmed, or realized proceeds are reconstructed.

Maintain two scorecards once sufficient history is available:
- original-$300 sleeve performance;
- total speculative-capital performance after later contributions.

Do not publish an exact return percentage while contribution history or closed-position proceeds remain unresolved.


## WSOL auxiliary-account correction — 2026-09-25
Direct Solana RPC shows four wallet-owned native WSOL token accounts:
- `6FV88kiLJFmm5bprPfD4NitTHNFsfyUZZFn6wFNrLziE`: 0.019445574 WSOL + 0.002039280 SOL rent reserve = 0.021484854 SOL recoverable on close.
- `6LbxShFopPRf56AWJvdQP57CnTNW5G9nvw8rKQhfofi1`: 0.006972803 WSOL + 0.002039280 rent = 0.009012083 SOL recoverable.
- `8XszhZXZUKPiCLCkC7pbvhLyDwZqQQ8YV6BHHqY9X8TT`: 0.007191552 WSOL + 0.002039280 rent = 0.009230832 SOL recoverable.
- `FuC71ndKhDJ6ngtwGfoy7o44vEjuhacg2x2KwSJiSxW8`: 0.000281389 WSOL + 0.002039280 rent = 0.002320669 SOL recoverable.

Token amount total = 0.033891318 WSOL. Full lamports recoverable by closing all four native WSOL accounts = **0.042048438 SOL** before transaction fees. With current native wallet balance 0.063112228 SOL, post-close native SOL would be about **0.105160666 SOL** before transaction fees.

These accounts are auxiliary native-token accounts associated historically with Orca Whirlpool activity. Wallet swap UIs may fail to spend them because they are separate token accounts rather than a single default token account. For wrapped SOL, the protocol-level recovery operation is CloseAccount/unwrap, not a market swap. Do not treat 0.033891318 alone as the full recoverable amount because refundable rent is also present.


## WSOL recovery completion — 2026-09-26
Direct Alchemy Solana RPC after the user completed the recovery shows:
- native SOL balance: **0.105136682 SOL**;
- all four previously tracked auxiliary native WSOL token accounts now return `value: null`, confirming they were closed.
The recovery is complete. Remove those WSOL accounts from active monitoring; keep the prior investigation only as audit/history.
