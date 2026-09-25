# $300 Crypto Profit Mission

Timezone: Asia/Bangkok

## Capital plan

- JUMP Legion ICO reserve: 150 USDC
- PONS trading margin: about 50 USDT
- ETH trading margin: about 50 USDT
- Flexible reserve: 50 USDT

The goal is to maximize upside over roughly three months without allowing one PONS or ETH trade to consume the whole capital pool.

## PONS plan

Instrument: Binance PONSUSDT perpetual
Mode: isolated
Max leverage: 3x
Primary resting entries:
- 0.6250, about 40 USDT notional
- 0.5850, about 49.73 USDT notional
- 0.5450, about 59.95 USDT notional

Hard stop for the resting-entry plan:
- 0.4980, Mark Price, Stop Market
- Never widen this stop to rescue the trade.

If all three entries fill, expected average entry is about 0.578 and planned loss at 0.498 is about 20 to 21 USDT before fees, funding and slippage.

Profit-taking plan:
- 0.738: close 10%
- 0.795: close 15%
- 0.955: close 20%
- 1.28: close 20%
- 1.75: close 15%
- final 20% runner

Stop management:
- After a valid 4h hold above 0.742, move remaining stop to about 0.618.
- After a valid break above 0.80, move remaining stop to about 0.665.
- After a valid break above 0.97, move remaining stop to about 0.795.
- After a valid break above 1.30, move remaining stop to about 0.955.
- After 1.75, manage the final 20% with roughly a 15% trailing stop unless market structure materially changes.

Stale-order rules:
- If PONS establishes a valid 4h close above 0.742, cancel any unfilled 0.585 and 0.545 resting bids.
- If all three resting entries fill, do not add more PONS with the reserve capital automatically.
- If the hard stop is hit, wait for a fresh 4h structure before considering re-entry.

Breakout alternative when none of the resting entries has filled:
- Require a 4h close above 0.666.
- Then require a 1h retest of 0.655 to 0.665 that holds above roughly 0.650.
- Cancel old resting-entry orders before switching to this breakout setup.
- Use about 100 USDT notional, 2x isolated, roughly 50 USDT margin.
- Stop about 0.618.
- Initial targets: 0.738, 0.795, 0.955, 1.28.
- Do not chase a vertical move into 0.70 to 0.80 without a retest.

PONS non-price risk triggers:
- Funding above +0.03% per 4h for 24h: pause adding.
- Funding above +0.05% per 4h persistently: reassess and consider reducing 25% to 50%.
- Binance ADL risk HIGH: do not raise leverage above 3x and favor incremental profit-taking.
- Significant deterioration in top-trader long/short ratio, OI, liquidation structure, or abnormal basis: reassess before adding.
- Official change to the Pons buyback/burn mechanism: immediate reassessment.
- Large onchain treasury/distributor movements, large holder deposits to exchanges, abnormal mint/burn changes, or contract/admin changes: immediate reassessment.
- If 7d holder revenue falls below about 1.5M USD and 7d DEX volume below about 250M USD for a sustained period, reassess the thesis even if the hard stop has not traded.

## ETH plan

Do not force an entry before the September 25, 2026 quarterly options expiry.
Deribit quarterly options expire at 08:00 UTC, which is 15:00 Asia/Bangkok.

Primary post-expiry long setup:
- Look for ETH roughly 2,590 to 2,630.
- Require a 4h reclaim/hold above about 2,640 after the reaction.
- Use about 50 USDT margin, isolated, normally 4x.
- Approximate 200 USDT notional.
- Stop about 2,535.
- TP1 2,800: close 25%
- TP2 3,000: close 30%
- TP3 3,300: close 25%
- Final 20% runner / trailing management.

Breakout alternative:
- If ETH closes a daily candle above about 2,810 without giving the pullback setup, wait for a 2,760 to 2,790 retest before considering entry.
- Do not chase a vertical move.
- Invalidate the current long setup if daily structure breaks materially below about 2,540, then reassess from fresh market data.

ETH monitoring must include:
- spot/perpetual price structure
- funding
- open interest
- top-trader positioning
- Hyperliquid / major perpetual market context when available
- large options positioning / expiry effects
- Polymarket probabilities
- ETF flows and material macro catalysts

## JUMP reserve

Keep 150 USDC reserved until the official Legion/Jumper sale page confirms sale date, FDV, token price, allocation, TGE unlock, vesting and initial circulation.

Working allocation rule:
- Around 75M FDV with at least 50% sale-token TGE unlock: up to 150 USDC application.
- Around 100M to 125M FDV: reduce application to about 100 USDC.
- Above 150M FDV or unfavorable unlock/circulation: reduce sharply or skip.

Do not treat community-posted tokenomics as confirmed until official Jumper/Legion documentation is available.

## Notification rules

Every monitor run should update the mission repository, but email and user notification must remain silent unless there is a material actionable change.

Material changes include:
- entry/stop/take-profit trigger
- stale-order cancellation trigger
- breakout setup confirmation
- funding/OI/long-short/ADL deterioration significant enough to alter the plan
- large onchain PONS flow or contract/admin/burn mechanism change
- official Pons announcement that materially changes token economics or market structure
- ETH post-expiry trade window becoming actionable
- official JUMP/Legion sale terms becoming available or materially changing

No material change means NO_ACTION and no email.


## SHARTCOIN / kids.fun additional position

User committed 1 SOL to the first kids.fun Shartcoin campaign before the 2026-09-24 01:30 UTC close. Treat this as an additional position outside the original $300 allocation unless later reconciled otherwise.

Canonical identities from YokaiCapital/kids-launchpad current campaign plan:
- Network: Solana mainnet
- Program: BLiaZWNQoPm4mG4cXNm4sXifFqs1Xmxx12qD9T4Y5NeN
- Campaign / escrow: 9FjwHicbkzP17NEW94UasBa3LfWtqmsmddzstq8UqKxP
- Canonical planned mint: UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids
- Fartcoin parent mint: 9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump
- Buttcoin parent mint: Cm6fNnMk7NfzStP9CZpsQA2v3jjzbcYGAxdJySmHpump
- Funding window: 2026-09-23 23:30 UTC to 2026-09-24 01:30 UTC
- Soft cap: 200 SOL
- Hard cap / max accepted SOL: 1,000 SOL
- Supply split: 43.5% participants, 43.5% liquidity, 10% parent holders, 3% dev
- Dev: 1% at launch, 2% linear over three calendar months.

The separate address GKpNJz7yMuhZka9izamv6sDUxCsDr58pFMUaw1TQpump was not found in the canonical repository campaign evidence as of the review and must not be treated as the KIDS Shartcoin mint unless new official evidence explicitly changes the canonical identity.

Post-close verification gates:
1. Confirm final total committed SOL and the exact pro-rata acceptance factor: min(1,1000/final_committed).
2. For the user's 1 SOL commitment, estimate accepted SOL, refundable excess and token allocation. Participant pool is 435,000,000 tokens, so at a fully accepted 1,000 SOL hard cap the entitlement rate is 435,000 SHARTCOIN per accepted SOL.
3. Confirm actual launch transaction, actual mint, pool and fee tier directly from official/on-chain evidence.
4. Confirm mint authority and freeze authority are revoked.
5. Confirm LP lock state and amount. Do not infer permanent lock from documentation alone.
6. Confirm refund path is active and excess refunds are actually claimable/processed.
7. Confirm actual mainnet pool swap fee. Current code policy indicates new mainnet pools use the 2.5% Raydium CPMM tier and no token transfer tax, but the live pool decides.
8. Check program upgrade authority. Current launch program is upgradeable; any authority change is material.
9. Check participant concentration, parent-claim sell pressure, top holders, pool liquidity, first-hour volume, buys/sells and large wallets after launch.
10. Monitor official kids.fun / YokaiCapital announcements and repository changes affecting tokenomics, claims, refunds, pool, authority, fee routing or security.

Initial valuation reference if hard cap is fully accepted:
- 43.5% token liquidity paired against 1,000 SOL implies opening FDV about 2,298.85 SOL.
- Opening token price about 0.00000229885 SOL.
- Opening pool gross two-sided liquidity about 2,000 SOL.
Recalculate USD figures using live SOL at launch.

Profit management after live pool verification:
- Security failure or canonical identity mismatch overrides all price targets and triggers immediate reassessment / exit.
- If price reaches about 2x verified launch price: take about 10%.
- At about 3x: take another 30%. Combined 2x+3x exits recover roughly 1.1x of the accepted SOL principal before fees/slippage.
- At about 5x: take another 20%.
- At about 10x: take another 20%.
- Keep final 20% as runner if liquidity/volume/community remain healthy.
- After 10x, manage the runner with a wide meme-appropriate trailing exit, roughly 25% to 30%, reassessed against liquidity.
- Avoid adding during the first price-discovery spike. Any new buy requires a fresh structure/liquidity/holder review.
- If after initial price discovery the token sustains below roughly 0.6x to 0.7x launch price with falling volume and no structural catalyst, reassess and consider cutting risk rather than averaging down automatically.

Notification rules for SHARTCOIN:
Email only for a material action or material risk, including launch completion, final allocation/refund becoming known if it requires a claim/action, security/authority mismatch, LP-lock failure, mint/freeze authority issue, official tokenomics/claim change, major holder/treasury movement, abnormal liquidity removal, or a defined take-profit/risk threshold. Routine price noise or unchanged status stays silent.


## SHARTCOIN live execution update — 2026-09-24 09:01 Asia/Bangkok

User-reported live execution:
- Wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Original commitment: 1 SOL.
- Confirmed refund shown by kids.fun: 0.600039112 SOL.
- Accepted principal inferred from refund: 0.399960888 SOL.
- Participant entitlement rate: 435,000 SHARTCOIN per accepted SOL.
- Estimated original allocation before integer rounding: 173,982.98628 SHARTCOIN.
- User reports price reached about 5x the fixed participation price and executed the latest chat sell ladder through the 5x target.
- Latest chat ladder used for accounting: 2x sell 10%, 3x sell 25%, 5x sell 20%, 8x sell 20%, 15x sell 10%, final 15% runner.
- Assuming those three completed exits filled as intended, cumulative sold = 55% of original allocation, estimated remaining = 45% = about 78,292.34 SHARTCOIN before any rounding/slippage discrepancy.
- Gross SOL proceeds estimated from exact target multiples: about 0.779923732 SOL. At a 2%–2.5% pool fee, approximate net proceeds are about 0.764325257–0.760425638 SOL before price impact/network fees.
- The accepted principal has therefore already been recovered in cash if the user-reported fills occurred as specified. Do not re-risk recovered principal by averaging up automatically.

Updated profit-management plan from this point:
- Do not sell additional tokens merely because 5x was touched; the 5x tranche is already treated as completed.
- At 8x fixed participation price: sell 20% of original allocation, about 34,796.60 SHARTCOIN.
- At 15x fixed participation price: sell 10% of original allocation, about 17,398.30 SHARTCOIN.
- Keep final 15% of original allocation, about 26,097.45 SHARTCOIN, as runner only while liquidity, volume, holder growth and official/project structure remain healthy.
- For the runner, reassess a wide 25%–30% trailing exit after a major extension rather than using a tight stop during the first price-discovery hours.
- If price loses the 3x participation level after having reached 5x, treat it as a material momentum failure and reassess immediately. If it loses 2x with declining volume/liquidity, prioritize protecting remaining profit.
- Any LP-liquidity anomaly, canonical mint mismatch, mint/freeze authority issue, unexpected program/upgrade-authority change, or concentrated large-wallet distribution overrides the price ladder.

Verification caveat:
- The user's wallet balance and individual swap fills were not independently read from a Solana RPC in this update because the connected Alchemy authorization is currently expired and public search indexes have not yet indexed the new canonical mint reliably. The execution quantities above are therefore accounting estimates from the user's confirmed 1 SOL commitment, 0.600039112 SOL refund and user-reported completed target sells. The hourly monitor must replace these estimates with direct on-chain balances/transactions as soon as an accessible verified Solana source becomes available.


### SHART live-mint verification correction — 2026-09-24
A fresh public YokaiCapital social post explicitly associates the launch with `GKpNJz7yMuhZka9izamv6sDUxCsDr58pFMUaw1TQpump`, while the public GitHub campaign plan still lists `UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids`. Treat this as an unresolved canonical-identity mismatch until direct Solana chain data confirms which mint was allocated/traded. Do not use stale search results for unrelated SHART tokens. The wallet-received mint and launch transaction are authoritative once RPC access is available.


## Capital plan update — 2026-09-24, additional 200 USDC

Total liquid-plan capital is now treated as about 500 USDC, excluding the residual SHART position itself.

Base commitments remain:
- JUMP/Legion base reserve: 150 USDC.
- PONS margin budget: 50 USDT; do not enlarge merely because more cash is available.
- ETH initial margin budget: 50 USDT; wait for the post-expiry setup.
- Existing general reserve: 50 USDC.

New 200 USDC:
- 100 USDC = conditional JUMP/Legion second tranche. It is NOT committed yet. Add it only if official final sale terms are strong: roughly <=100M FDV, >=50% sale-token TGE unlock, and sane initial circulation/tokenomics. If FDV is roughly 100M-125M, use only about 50 USDC of this extra tranche. If >150M FDV, poor unlock, or excessive initial circulation/insider overhang, keep all 100 USDC as cash/opportunity reserve.
- 50 USDC = ETH second-bullet reserve. Do not add to the initial position automatically. Use only after the September 25 options-expiry setup is confirmed and either (a) the initial trade has favorable confirmation / successful retest, or (b) a separate high-quality second setup appears.
- 50 USDC = additional general opportunity reserve. Combined with the previous 50 USDC reserve, keep at least 100 USDC uncommitted unless a clearly superior event-driven opportunity appears.

Maximum planned deployment if JUMP terms are excellent:
- JUMP up to 250 USDC application/reserve.
- PONS 50 USDT margin budget.
- ETH up to 100 USDT across initial + second bullet, not necessarily deployed simultaneously.
- General reserve at least 100 USDC.

If JUMP terms fail the quality gates, the extra 100 USDC remains cash; do not mechanically redirect it into PONS or ETH.

Current PONS/ETH context at update:
- PONSUSDT mark about 0.6369, funding about +0.009422% for the current funding interval, OI about 64.18M PONS, top-trader 4h position L/S about 2.21. This does not justify increasing the existing PONS budget.
- ETHUSDT mark about 2681.7, funding about +0.009484%, OI about 2.288M ETH, top-trader 4h position L/S about 1.54. ETH remains a wait-for-expiry setup rather than a reason to deploy extra cash immediately.


## Liquid capital reconciliation — 2026-09-24 09:27 Asia/Bangkok
User wallet now shows 206.43 USDC of new liquid capital. Treat the total strategy pool as about 506.43 USDC-equivalent against the prior 300 USDC plan, excluding the residual SHART mark-to-market.

Exact working allocation:
- JUMP/Legion: 150 USDC base reserve, plus up to 100 USDC conditional second tranche only if official FDV/unlock/circulation gates pass. Maximum 250 USDC.
- PONS: 50 USDT margin budget unchanged. Do not scale up merely because liquid capital increased.
- ETH: 50 USDT initial margin budget plus up to 50 USDT second bullet only after the post-expiry setup/confirmation. Maximum 100 USDT.
- General/opportunity reserve: at least 106.43 USDC if JUMP receives the full conditional 100 and ETH receives the full second bullet; more remains in cash if either setup fails its gates.
- SHART: residual position is managed independently; do not recycle new USDC into SHART automatically.


## Famous / established-brand token-launch radar — mandatory hourly scan

Purpose: discover short-window opportunities similar to SHARTCOIN, STONK and other launches where an already-known onchain builder, creator, founder, project, consumer brand or established community issues a new token or opens a new public sale/fair launch.

This scan is mandatory on every hourly mission run. It is discovery-first: do not restrict the universe to the current portfolio or a static whitelist.

### Primary discovery surfaces
- English X/Twitter posts from official project/person/brand accounts and their directly linked launch accounts.
- Official launchpads, token-sale pages, project websites, blogs and docs.
- Onchain launch/mint/pool creation and DEX discovery where the issuer identity can be directly anchored.
- GitHub/deployment repositories when a launch is technical/open source.
- High-signal English onchain analysts only as leads; always return to the issuer's official account/domain or direct chain data before calling it confirmed.
- Reddit/community discussion only as secondary heat/sentiment evidence.

Seed ecosystems/entities include, but are not limited to: YokaiCapital/kids.fun, StonkFun/LaunchOnSF, pump.fun and major Solana launch ecosystems, BONK-related launch infrastructure, Believe-style social token launch systems, Jupiter/Meteora/Solana ecosystem builders, Base/Farcaster/Coinbase ecosystem launches, Hyperliquid ecosystem launches, Robinhood/Robinhood Chain, major NFT/digital-art creators, established crypto founders, and globally recognizable consumer/creator brands entering onchain markets. Expand from official quote/repost/reply networks and newly trending verified/known accounts; the seed list is not an upper bound.

### Search concepts
Actively look for: token launch, fair launch, presale/public sale, prelaunch, launchpad, commit/escrow, mint/CA/contract, TGE, claim, airdrop tied to a new token, bonding curve, LP creation, liquidity lock, buyback/burn token, creator coin, community coin, brand coin, new tokenized asset, and posts that publish a contract address or a short participation window.

### Early-alert rule
Because some windows last only 1-3 hours, do not wait for full post-launch data when an official issuer announces an actionable launch.
Send an EARLY ALERT when all are true:
1. The announcement is from the issuer's canonical official X/account or canonical official domain, or is directly linked by it.
2. There is a real action window now or within 24h: commit, public sale, mint, claim, launch, deposit, whitelist/registration, or confirmed live trading.
3. The issuer has meaningful pre-existing reputation/audience/product/community/history OR the launchpad itself has an established track record.
4. No unresolved identity/domain/contract conflict makes participation unsafe.

A contract address is not required for the first early alert if the issuer itself confirms the launch and the official launch page is live. In that case label CA/chain details as pending and follow up only when new actionable details become available.

### Quality / opportunity assessment
For each candidate, verify as much as available:
- issuer identity and historical projects
- chain and canonical CA/mint
- start/end/TGE time converted to Asia/Bangkok
- participation asset and minimum/maximum/hard cap
- fixed price vs auction/bonding curve/pro-rata
- initial FDV / circulating market cap / implied valuation
- initial liquidity and LP lock/burn
- mint/freeze/admin/upgrade authority
- team/dev/insider allocation and vesting
- token transfer/swap taxes and DEX fee
- holder concentration and bundled/related wallets
- first 5m/15m/1h volume, unique buyers, liquidity and large-wallet flow after launch
- issuer's prior launches: initial valuation, 10m/1h/1d behavior when verifiable, ATH multiple/time-to-ATH, and drawdown
- X attention: views/replies/reposts/known-account interaction and acceleration, not just raw follower count
- Reddit/other community evidence
- whether a real-money prediction market exists when relevant

### Alert classes
A) PRELAUNCH / SALE: short participation window from a recognized issuer. Send immediately with exact official link, Bangkok deadline, currency, cap/FDV, allocation mechanism, what is verified vs pending, and a suggested maximum test allocation from the general opportunity reserve.
B) LIVE LAUNCH: canonical CA/pool becomes live at an attractive early valuation/liquidity profile. Include price, FDV, liquidity, volume, holder/buyer data and exact risk controls.
C) MECHANISM CHANGE: an existing revenue/buyback token such as STONK/PONS materially changes buyback %, burn, fees, revenue share or supply mechanics.
D) SOCIAL ACCELERATION: a recognized issuer's new token becomes materially viral before price discovery is mature. Require official identity plus at least one quantitative heat signal or multiple independent high-signal accounts.

### Anti-spam / anti-scam rules
- Random meme launches, anonymous deployers, copied tickers, unofficial celebrity coins, paid-KOL-only shills, and old announcements do not trigger.
- Celebrity/brand launches require direct official-account/domain evidence; a token merely using a famous name is rejected.
- Never use a Chinese-language website as confirmation.
- If CA/domain/account identity conflicts remain unresolved, record the candidate but do not give a participation link.
- Duplicate posts or no material change => NO_ACTION.
- A later alert is allowed only when it adds an actionable change, such as CA, window opening, final valuation, pool live, allocation/refund, or a major risk/exit signal.

### Notification payload
When a qualifying new launch appears, email lxx.run688@gmail.com and notify the user with:
- WHO / project
- official X/source link
- WHAT is launching
- chain and CA if confirmed
- exact Bangkok start/end/TGE
- how to participate and with SOL/USDC/other
- hard cap / implied FDV / initial liquidity
- why this issuer is notable, including prior-launch evidence where available
- current social/onchain heat
- key red flags
- one concise action: participate/watch/skip, and a maximum test size sourced only from the mission's general opportunity reserve unless the user later reallocates capital

Use subject: `Crypto Mission 新发币机会｜<issuer/project>｜<event>`.
If there is no qualifying opportunity, remain completely silent and only write the scan result to GitHub.

### GitHub audit
Write discovered candidates and rejected candidates to:
`crypto-300-profit-mission/radar/YYYY/YYYY-MM/YYYY-MM-DD.md`
and actionable alerts additionally to:
`crypto-300-profit-mission/signals/YYYY/YYYY-MM/YYYY-MM-DDTHHMM-launch-radar-<slug>.md`.

Record source account, official URL, discovery time, issuer history, launch mechanics, identity check, onchain verification status, social heat, valuation/liquidity, reason accepted/rejected, and whether Gmail was sent.


## UNICRED / Unichain position monitor — added 2026-09-24

UNICRED is now an active Mission position. Read `crypto-300-profit-mission/positions/unicred.md` every run and treat it as the authoritative position file.

Current position summary:
- NFT #230 acquired at 0.0105 ETH and staked 7 days / 1x until 2026-10-01.
- First user-confirmed rent sample: about 0.00087 ETH (~USD 2.30) after about 52 minutes.
- CRED principal has been recovered by the user. Remaining runner: 51.390151 CRED, about 25% of the original CRED amount.
- No automatic additional capital allocation to UNICRED.

Monitor current mint progress/epoch/mint price, staking count and total weight, rent economics, CRED price/liquidity/volume/supply/buyback-burn/NFT-burn dynamics, official rule or contract changes, security, and #230 secondary value around unlock. Notify only for actionable sold-out/end-of-rent, security/mechanism changes, material CRED profit-protection decisions, or the 2026-10-01 unlock decision. Routine rent accumulation and ordinary price/mint movement remain silent and are recorded to GitHub only.


## Active-token rapid drawdown alerts — added 2026-09-24

For active Mission tokens with live market exposure, explicitly monitor rapid downside in addition to the existing strategy-specific levels.

Trigger an actionable downside alert when ANY of the following is confirmed from reliable live market data:
- price falls >=20% within approximately 1 hour;
- price falls >=30% within approximately 4 hours;
- price falls >=15% within approximately 30 minutes AND live liquidity also deteriorates materially;
- live DEX/CEX liquidity falls >=25% from the recent baseline, especially when accompanied by large-holder selling;
- a strategy-specific support/stop/exit threshold in the relevant position file is breached.

For very thin meme / microcap pools such as SHARTCOIN and CRED, require either a confirmed execution-grade price plus liquidity/volume context, or two independent live market sources when possible, to avoid false alerts from bad index prints.

The alert must include: current price, measured drawdown window, liquidity/volume change, large-wallet or holder evidence if available, and a concrete action (hold/reduce/exit/adjust orders). Routine volatility below these thresholds remains silent.


## UNICRED hourly rent / breakeven monitoring — mandatory

Every hourly Mission run must explicitly evaluate UNICRED #230 rent economics, not only sold-out/security events.

Authoritative identifiers:
- Wallet `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- NFT contract `0xf60de24F228dc7Ca6fF025958d2eE3A956ED88E5`
- NFT #230
- Purchase cost 0.0105 ETH
- 7-day / 1x stake
- First confirmed claimed rent baseline 0.00087 ETH

On every hourly run:
1. Read current minted count, epoch, mint price, unicorns staked and totalWeight from chain/official app where available.
2. Derive realized rolling mint speed from reliable consecutive snapshots and compare with the protocol target ~1 mint/10 sec.
3. Read wallet-specific cumulative claimed rent and current claimable/pending rent if directly available from chain or the official app. Never fabricate wallet rent.
4. Record hourly rent delta and effective ETH/hour when two reliable consecutive user-rent values exist.
5. Reforecast estimated remaining rent to #4,444 using current mint-price schedule and observed totalWeight dilution, showing at least a base-case dilution assumption derived from recent data.
6. Reforecast theoretical sold-out time using current observed rolling mint pace.
7. Trigger an immediate notification/email if cumulative claimed + claimable rent reaches or exceeds 0.0105 ETH. Use status `UNICRED_RENT_BREAKEVEN`.
8. If minting reaches #4,444 before rent-only breakeven, trigger `UNICRED_SOLD_OUT` and report final/known cumulative rent plus the minimum net NFT sale value needed for whole-position economic breakeven.
9. Routine hourly rent changes below an action threshold are written to GitHub only and do not notify.

Continue the separate active-token rapid-drawdown monitoring for CRED. Large CRED downside remains actionable even though the CRED principal has already been recovered.


## Capital and position decision refresh — 2026-09-25 00:16 Asia/Bangkok

Current active liquid stablecoin pool: about 712 USDC (212 Solana + 500 Base), based on user-confirmed balances pending direct RPC re-verification.

Allocation:
- Keep 150 USDC as a hard short-window opportunity reserve.
- JUMP: hold 250 USDC reserved now. If official Jumper/Legion terms confirm FDV <=75M, >=50% TGE unlock and sane initial float, allow application up to 300 USDC. 75-100M => max 250; 100-125M => max 150; >125M or materially worse unlock/float => re-evaluate/skip.
- Do not hedge JUMP on Polymarket now. The launch-by-Dec-31 market can be monitored, but current No pricing is too expensive as simple timeline insurance and does not hedge post-TGE price. The one-day FDV market is currently too illiquid to use for position sizing.
- ETH: keep up to 100 USDC reserved, 50 first bullet + 50 confirmation bullet, only after Sep-25 options-expiry review.
- PONS budget remains 50 USDT margin, no increase.
- CRED, SHARTCOIN, Credits and UNICRED NFT: no fresh capital.
- Remaining liquid stablecoin after max 300 JUMP + 100 ETH + 150 opportunity reserve is about 162 USDC.

JUMP hedge logic:
- Consider a small Polymarket delay hedge only if official sale capital is meaningfully locked AND Dec-31 No trades at <=10c with adequate liquidity. Above that, hedge drag is too large relative to a 250-300 USDC sale position.
- If a liquid JUMP premarket/perpetual appears after allocation and implies >=2x sale valuation, reassess a partial hedge of unlocked exposure rather than buying a broad timing bet.

Separate 500 principal-preservation bucket:
- Keep separate from speculative Mission capital.
- Prefer the user's currently available Binance account offers: 300 USDT into the 5-day ~25% APR offer (only after checking final account eligibility/terms), and 200 USDC into the current flexible bonus tier.
- Current public Binance USDC campaign runs through 2026-09-30 23:59:59 UTC and pays 7% on <=300 USDC during the promo (real-time account display can differ slightly).
- Reject QQQ/stock-token LP and pPOLY LP for this bucket. QQQ LP has equity-price, range/IL, tokenization, smart-contract and activity-subsidy risk; pPOLY is highly volatile and not direct Polymarket equity.
- Also reject >10% DeFi vaults for the strict principal-preservation bucket even when currently open. Their headline yield compensates for smart-contract, strategy, counterparty/collateral and liquidity risks and can change quickly.


## BTC market-regime overlay and JasonLeo cross-check — added 2026-09-25

Purpose: use BTC as the market-regime anchor for the Mission and track the public BTC framework of X account `@Jason60704294` as one supplementary external signal. This source is never sufficient by itself to open, close, size or reverse a trade. Every actionable conclusion must be cross-checked against live market structure.

Current external framework captured from the 2026-09-25 post:
- Medium-term bias remains constructive while the prior rebound structure holds.
- 79,000 is the key downside decision zone. A confirmed breakdown should shift the Mission toward risk reduction and invalidate aggressive long continuation assumptions.
- A fast vertical move into roughly 98,000 to 105,000 is a defensive-hedge candidate zone for a weekly-scale pullback.
- A daily close holding above roughly 108,000 invalidates that defensive short/hedge thesis.
- If BTC spends meaningful time balancing between roughly 80,000 and 100,000, with leverage/positioning cooling rather than accelerating vertically, the next continuation reference zone becomes roughly 115,000 to 125,000.

Mission execution rules:
1. This is a market-regime overlay. There is currently no dedicated BTC capital allocation and no automatic BTC order execution.
2. A fresh BTC trade requires an explicit user-approved allocation. Do not consume the 150 USDC hard short-window opportunity reserve, JUMP reserve, ETH reserve or the separate principal-preservation bucket automatically.
3. Downside risk-off confirmation: prefer a 4h close below 79,000 plus a failed reclaim, or a daily close below 79,000. On confirmation, do not average down BTC/ETH beta automatically; tighten review of ETH entry conditions and other high-beta Mission exposure.
4. Fast-extension hedge candidate: price must reach 98,000 to 105,000 through a materially accelerated move, and at least two independent overheating confirmations should be present before suggesting a defensive short/hedge. Examples include unusually positive funding, rapid OI expansion with price, crowded long positioning, liquidation-driven acceleration, or an extreme short-window price extension.
5. The 98,000 to 105,000 zone alone is not a short signal. If leverage/positioning remains healthy, do not force the hedge.
6. Hedge invalidation: a daily close that establishes above roughly 108,000 cancels the current defensive-short thesis unless a fresh structure is documented.
7. Consolidation continuation: if BTC develops a multi-day balance inside roughly 80,000 to 100,000, avoids a confirmed 79,000 breakdown, and funding/OI crowding cools, treat 115,000 to 125,000 as the next upside reference zone rather than an immediate take-profit requirement.
8. New posts from `@Jason60704294` are monitored only for material framework changes: new explicit key levels, a disclosed large BTC position change, invalidation of his prior framework, or a materially different path thesis. Generic commentary, reposts, engagement bait or unchanged views remain silent.
9. Before any notification, compare the external post with live BTC price/4h/daily structure, funding, OI, top-trader positioning and broad account long/short data. When available, also check major perpetual venues, options/expiry structure, ETF flows and material macro catalysts.
10. If the external trader changes levels but market data does not confirm an actionable Mission change, record the update in GitHub and remain silent.

BTC overlay notification conditions:
- confirmed 79,000 breakdown / failed reclaim that changes Mission risk posture;
- 98,000 to 105,000 fast-extension hedge conditions become qualified by market data;
- a daily close above roughly 108,000 invalidates an active hedge thesis;
- multi-day 80,000 to 100,000 consolidation transitions into a validated continuation setup;
- `@Jason60704294` materially changes his public framework and the change affects an existing Mission decision.

No qualifying change means NO_ACTION and no email.


## NFT mint radar integration — added 2026-09-25

The hourly Mission now includes a dedicated high-potential NFT mint radar.

Authoritative specification:
- `crypto-300-profit-mission/watchlists/nft-mint-radar.md`

Every hourly NFT radar run must use that file's latest rules. Discovery should include MintGo, Waypoint MintScan, MCT, nftis.fun and the read-only portions of 985monitor, plus English X/Twitter, Reddit, official mint/marketplace pages and direct chain data.

The radar is allowed to email only when a candidate passes both the hard issuer/project identity gate and the high-potential opportunity gate, or when a previously alerted candidate develops a material new action/risk change. Otherwise it must remain completely silent.

Do not connect a main wallet or import private keys/seed phrases into third-party discovery tools. 985monitor is discovery/read-only for this Mission.

Any capital suggestion must use only the Mission general opportunity reserve unless the user explicitly reallocates funds.


## BSC smart-money cluster alpha — 2026-09-25

Research source: `signals/2026-09-25-bsc-smart-money-cluster-alpha.md`

Current priority:
1. B2 cluster `0xb2e8c2d90ebc988fde867c1edacc24864216054c` plus strong-linked children `0x9656f3c2b2c264c4fcb506c5a9735b206787cf34` and `0xdc1e86900dc3ac30ac49ef9c3048bca52082e089`.
2. Early sniper `0x87a028be9aefc5e04723c1a603ea2bd2290cdbf4`.
3. A `0xe1e3252b8b2f9bf2a8335389ba8ee62e6ea29407`.
4. B `0xbf004bff64725914ee36d03b87d6965b0ced4903`.

Execution rule:
- Do not copy B directly.
- Do not copy A or 87a unconditionally.
- Do not auto-trade B2 yet.
- Highest-priority hypothesis to validate is `B2 first -> A later`.
- Pending-calldata / one-block detection is preferred when available; post-confirmation copying must be simulated with realistic latency.
- Any strategy must remain positive after token tax, protocol fee, gas, price impact and slippage.
- Require at least 30 closed B2 samples, preferably 50-100, before tiny live-capital testing.
- Backtest +1/+2/+3 block execution, outlier dependence, win rate, median ROI, net EV and max drawdown.
- A child-wallet position split is a cluster indicator, not by itself a buy signal.
- Deployer association remains unconfirmed until a direct funding/control relationship is demonstrated.

Current evidence snapshot:
- 87a: 18 closed recent `7777` samples, ~+12.24% gross aggregate ROI, 16.7% win rate, median ~-14.8%; highly dependent on the `无用` outlier.
- B2 ordinary sample: 10 closed trades, 1.55 BNB principal -> ~1.76975 BNB actual proceeds, ~+14.18% gross ROI, 40% win rate, median ~-8.5%; removing the `算命` outlier leaves the other nine around -4.8%.
- `宝拉`: B2 0.5 BNB entry before A; one synchronized B2+child reduction block returned ~1.05608 BNB, already >+111% versus initial principal before other exits.
- `星星人`: B2 0.25 BNB entry about 17 minutes before A; already reconstructed cluster proceeds >0.6906 BNB, lower-bound ROI >+176%.
- `CLAIMR`: A preceded B2 by ~13s; B2 only earned about +0.43%. This supports testing trade-order direction as a filter, but sample remains too small.

Promotion gate:
Only move this research into real-money execution after the expanded backtest shows positive net EV under realistic latency and after removing major outliers.
