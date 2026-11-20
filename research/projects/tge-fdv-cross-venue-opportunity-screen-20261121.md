# TGE / FDV 跨预测市场停运项目的 No 交易机会调查（2026-11-21）

Status: RESEARCH_ONLY / WATCH / ORDER_BOOK_UNVERIFIED
As-of: 2026-11-21 Asia/Bangkok
Base branch/commit at research start: `main` / `f5c07f601425ec2e1de6ee9d448d2e140336fb30`
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `token_trading_principles.md`, `MISSION_SPEC.md`.
Scope: first-pass multi-venue catalog, event-rule verification, issuer-state screening, not trades or production monitoring. No limit orders, position changes, or task/monitor creation.

## Method and important limitations

1. Discover TGE and post-TGE FDV questions **before** classifying project survivorship; dedupe by project, market, threshold and settlement deadline.
2. Preserve evidence tiers: official issuer shutdown/token cancellation; operations suspended but token uncertainty; merger/pivot but product alive; no corresponding open PM; resolved market.
3. Verify individual market terms. The typical FDV contract resolves NO if the qualifying token has not launched by the specified deadline, but dates vary. Do not equate a product's sunset date with the prediction contract's resolution date.
4. Record venue, collateral, deadline, price-source rule, all listed thresholds, executable No ASK, aggregate quantities and fee-adjusted price. Index-page % is **not** a No ASK and lifetime volume is **not** executable depth.
5. Compute `gross payoff if No = (1-p)/p`; breakeven Yes probability is `1-p`; price must be from executable level, not a midpoint; include time cost, fees, collateral issuer and oracle risk. Markets in different venues may share the same upstream resolution, so not an independent hedge.
6. This pass could read the browser-opened Polymarket Abstract page for 9 displayed prices and inspect indexed webpages for other venues. **Live CLOB level sizes, fillable quantities, precise order execution, full catalog pagination and fee schedule were NOT verified.** No list can honestly be called exhaustive across all currently-listed individual prediction markets with these access limitations.

## A. High-confidence cancellation / sunset candidates

| Project | Status and original evidence | Polymarket | Predict.fun | OPINION | Limitless | Rule-based No scenario | Verification |
|---|---|---|---|---|---|---|---|
| StandX | 2026-10-15 official announcement: platform token cancelled; DUSD compensation and scheduled wind-down. https://x.com/StandX_Official/article/2110613283967230232 | https://polymarket.com/event/standx-fdv-above-one-day-after-launch ; also https://polymarket.com/event/will-standx-launch-a-token-by | https://predict.fun/market/standx-fdv-above-one-day-after-launch | https://app.opinion.trade/market/standx-fdv-above-one-day-after-launch | https://limitless.exchange/markets/standx-fdv-above-dollar1b-one-day-after-launch-1767884376556 | No qualifying token by 2026-12-31 23:59 ET => No for FDV markets reviewed | Strong project No, executable quotes missing |
| Abstract (ABS) | 2026-10-06 official wind-down and no token, chain closure planned 2026-12-15; original official account: https://x.com/AbstractChain ; independent original report https://www.coindesk.com/tech/2026/10/07/pudgy-penguins-abstract-becomes-second-ethereum-layer-2-to-shut-in-a-week | https://polymarket.com/event/abstract-fdv-above-one-day-after-launch ; TGE timing markets also indexed | https://predict.fun/market/abstract-fdv-above-one-day-after-launch | No verified matching contract in this pass | No verified matching contract in this pass | No qualifying governance token by 2027-12-31 23:59 ET => No | Strong project No, ~1y+ lockup |
| Ventuals | Official 2026-06-15 sunset and explicit no Ventuals token: https://app.ventuals.com/ | https://polymarket.com/event/ventuals-fdv-above-one-day-after-launch ; https://polymarket.com/event/will-ventuals-launch-a-token-by | https://predict.fun/market/ventuals-fdv-above-one-day-after-launch | No verified matching contract | No verified matching contract | No qualifying token by 2026-12-31 23:59 ET => No | Strong project No; Predict.fun was near-zero historical volume |

### Full discovered FDV threshold groups in primary target venues

- StandX Polymarket: $50M, $100M, $200M, $400M, $800M, $1B, $2B, $3B, $5B, $7B, $10B (11). Predict.fun: $200M, $400M, $800M, $1B, $2B, $3B, $5B, $7B, $10B (9). OPINION: $800M, $1B, $2B, $3B, $5B, $7B, $10B (7). Limitless: observed $800M, $1B, $2B (3). Check every threshold's exact rule before execution.
- Abstract Polymarket: $200M, $400M, $600M, $800M, $1B, $1.5B, $2B, $2.5B, $3B (9); Predict.fun has a matching 9-threshold family. Polymarket live page in browser displayed Buy NO 98.0c, 97.9c, 97.5c, 98.5c, 99.0c, 97.9c, 98.2c, 97.9c, 98.0c respectively, **but no verified size at those quotes**; No at 97.5c yields theoretical 2.56% gross return until settlement.
- Ventuals Polymarket and Predict.fun: $100M, $300M, $500M, $800M, $1B, $1.5B, $2B (7 each). Predict.fun cached indexed book shows ~$100 aggregate trading across group (not executable availability).
- StandX OPINION displayed YES probabilities approximately $800M 7%, $1B 0%, $2B 4%, $3B 5%, $5B 2%, $7B 2%, $10B 10% (fresh indexed Nov 21). THESE ARE NOT EXECUTABLE NO BUY PRICES. OPINION lifetime total displayed ~$195.84M with bonus points active, does not prove usable liquidity.
- Limitless $1B StandX displayed wildly inconsistent snapshot examples (50/50 in recent search excerpt, 15.5% / 84.5% in older opened page) while the exposed orderbook had no bid/ask rows. **Never market-order 50c based on that figure**. Limitless rule text says it resolves according to Polymarket's final resolution and rules, sharing upstream outcome risk.

### Primary market links
- https://polymarket.com/predictions/fdv
- https://predict.fun/
- https://app.opinion.trade/pre-tge
- https://limitless.exchange/crypto/type
- https://kalshi.com/markets/kxtokenlaunchventuals/ventuals-token (historical 2025 token-launch contract; not a currently actionable 2026/2027 market)

## B. Provisional risk candidates, not proven token cancellations

| Entity | Observable state | Linked market | Gate |
|---|---|---|---|
| Neutrl (possibly what user calls 'neural'; exact identity not confirmed) | 2026-08 NUSD reserve/liquidity impairment and paused issuance/redemption; a special redemption program was communicated. None of those facts independently proves governance token cancelled. Official announcements: https://telegram.me/s/NeutrlOfficial | https://polymarket.com/event/neutrl-fdv-above-one-day-after-launch ; https://predict.fun/zh-cn/market/neutrl-fdv-above-one-day-after-launch ; https://polymarket.com/event/will-neutrl-launch-a-token-by | Need official latest operations status and whether governance token plan legally or operationally cancelled; NUSD stablecoin does not satisfy governance token market's launch condition |
| Felix | 2026 HIP-3 trading venue shut, but lending business may still operate; closure of a product is not proof of cancellation of all token plans | https://polymarket.com/event/felix-fdv-above-one-day-after-launch | Require canonical issuer cancellation confirmation |
| Farcaster / Neynar | Acquisition/merger and strategic changes, but network operations not necessarily ended | No verified active matching token-launch/FDV market | Do not classify as automatic No |
| Polynomial | 2026 shutdown reports and cancelled token attempt | No verified currently open matching FDV/TGE market | No executable position identified |
| Tally | 2026 closure reports | No verified currently open matching FDV/TGE market | No executable position identified |
| Blast | Layer 2 closure/wind-down reported in 2026, **BLAST token already launched 2024** | Any future first-TGE proposition requires special scrutiny | Exclude as fake new-token No trade |

## C. Wider surfaced pre-TGE / FDV market inventory awaiting status gate

The indexed market catalogs also surface Predict.fun, Variational, Extended, Puffpaw, OpenSea, Cambria, QFEX, MetaMask, Multipli.fi, Base, MagicBlock, Arc, Unit, Relay, Probable, Pacifica, Theo, Veera, Ostium, Papertrade, Ink, Noble, N1, Nansen, Loopscale, Exponent, Hyperbeat, Perena and fomo.family, among others. These are **not asserted to be shut down or automatic No**. Exact event IDs, all active expiries and per-strike orderbooks require further enumeration. Index search feeds are not a complete authenticated list.

## D. Trade gate and allocation rule

No `SETUP` before all of the following pass:
- exact event and official project canonical identity;
- original English market terms and deadline, qualifying governance token definition, price source, UMA/venue settlement and dispute;
- dated issuer cancellation or verified shutdown, with mergers/rebrands evaluated;
- executable No ASK and aggregate amounts at size $100/$500/$1000 and fill slippage, not screenshot odds, 50/50 placeholders or historical turnover;
- exact fees, settlement currency and collateral risk; date to realistic final redemption, not early shutdown date;
- independent market only if oracle sources genuinely independent, otherwise treat as correlated venue exposure;
- monotonically ordered FDV thresholds and cross-strike mispricing tested with both legs *simultaneously executable*; if not, note pricing inconsistency only.

Current decision: **WATCH** for StandX, Abstract, Ventuals; **RESEARCH / NO_CANCELLATION_PROOF** for Neutrl; **NOT_ACTIONABLE** for historical Kalshi Ventuals and unverified matched markets.

This is a material dated research snapshot, not production authority, a position, or a task. No automated polling, order, wallet signature, Gmail or production change authorized.
