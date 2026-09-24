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
