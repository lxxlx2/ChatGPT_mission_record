# BSC smart-money cluster / copy-alpha research

Checked: 2026-09-25 13:19 Asia/Bangkok
Status: RESEARCH_ONLY
Execution status: DO_NOT_AUTO_TRADE_YET

## Mission goal

Determine whether the observed BSC wallet cluster provides a reproducible positive-EV trading signal after tax, protocol fee, gas, price impact and realistic execution delay.

Primary observed wallets:
- A: `0xe1e3252b8b2f9bf2a8335389ba8ee62e6ea29407`
- B: `0xbf004bff64725914ee36d03b87d6965b0ced4903`
- Early sniper candidate: `0x87a028be9aefc5e04723c1a603ea2bd2290cdbf4`
- Higher-priority cluster leader candidate: `0xb2e8c2d90ebc988fde867c1edacc24864216054c`
- B2 child wallet 1: `0x9656f3c2b2c264c4fcb506c5a9735b206787cf34`
- B2 child wallet 2: `0xdc1e86900dc3ac30ac49ef9c3048bca52082e089`

Relevant Flap execution contracts observed:
- Router: `0x1de460f363af910f51726def188f9004276bf4bc`
- Execution/recipient path used by 87a: `0x12fc59e1512ed2ac450c3152a45440d7bf3cbaa6`

## Current ranking

1. B2 cluster
2. 87a early sniper
3. A
4. B

B remains useful as a late confirmation / attention signal, but current samples show materially worse entry timing than A and the earlier wallets.

## 87a backtest snapshot

18 recent closed `...7777` trades were reconstructed from actual on-chain buy value and Swap event amountOut.

Aggregate:
- Total principal: about 2.0 BNB
- Actual sale proceeds: about 2.24477 BNB
- Gross PnL: about +0.24477 BNB
- Gross ROI: about +12.24%
- Winners: 3 / 18
- Win rate: 16.7%
- Median trade ROI: about -14.8%

Important dependency:
- Results are strongly dependent on rare outliers.
- Removing the large `无用` winner makes the remaining basket unattractive.
- Therefore direct unconditional copying of 87a is rejected.

### 87a / 无用

Token:
`0x9803b9e4536e2ffdfcd745756f25243d82ad7777`

87a:
- Initial buy: 0.1 BNB
- Before A entered, first two realized sales returned:
  - 0.0950708 BNB
  - 0.1522107 BNB
- Pre-A realized proceeds: 0.2472815 BNB
- Pre-A realized ROI on original principal: about +147.3%
- Six reconstructed sale proceeds total: about 0.619082 BNB
- Realized ROI versus 0.1 BNB principal: about +519%, excluding remaining tail and gas

Timing:
- 87a buy: 2026-09-25 03:50:51 UTC
- A buy: 2026-09-25 03:56:06 UTC

Execution-path implication:
- Some 87a buys are submitted by rotating outer EOAs to `0x12fc59...baa6`, with calldata directing the token to 87a.
- A pending-transaction monitor should inspect calldata recipient, not only wait for the ERC20 transfer into 87a.

Counterexample:
- `乌萨奇`: 0.1 BNB -> about 0.075006 BNB, about -25%.
- 87a cannot be copied blindly.

## B2 cluster evidence

Leader:
`0xb2e8c2d90ebc988fde867c1edacc24864216054c`

Strong-linked child wallets:
- `0x9656f3c2b2c264c4fcb506c5a9735b206787cf34`
- `0xdc1e86900dc3ac30ac49ef9c3048bca52082e089`

Evidence supporting cluster treatment:
- Repeated direct token transfers from B2 to child wallets.
- Repeated multi-BNB transfers in both directions.
- B2 -> dc1e historical native transfers include approximately 3.10, 9.15, 6.87 and 8.17 BNB.
- 9656 has repeatedly returned multi-BNB amounts to B2, including approximately 2.16, 4.04 and 5.61 BNB.
- B2 and children perform synchronized token exits in identical blocks after position splitting.

This is strong evidence of a coordinated trading cluster. It does not by itself prove the same beneficial owner.

## B2 ordinary closed-trade sample

Ten reconstructed ordinary closed trades, excluding the large `宝拉` and `星星人` cluster winners:

| Token | Principal BNB | Actual proceeds BNB | ROI |
| --- | ---: | ---: | ---: |
| 算命 | 0.150 | 0.43673 | +191.2% |
| 努努 | 0.250 | 0.30612 | +22.4% |
| 流浪狗 | 0.250 | 0.25928 | +3.7% |
| CLAIMR | 0.025 | 0.02511 | +0.4% |
| 中华 | 0.050 | 0.04585 | -8.3% |
| 甲亢蛙 | 0.050 | 0.04565 | -8.7% |
| 菊花 | 0.075 | 0.06692 | -10.8% |
| LP | 0.500 | 0.41876 | -16.2% |
| Poly | 0.150 | 0.12482 | -16.8% |
| china | 0.050 | 0.04051 | -19.0% |

Aggregate:
- Principal: 1.55 BNB
- Proceeds: about 1.76975 BNB
- Gross PnL: about +0.21975 BNB
- Gross ROI: about +14.18%
- Win rate: 4 / 10 = 40%
- Median ordinary-trade ROI: about -8.5%
- Removing the `算命` +191% outlier leaves the remaining nine trades around -4.8% combined.

Interpretation:
- B2 has a more favorable loss distribution than 87a, but still relies on occasional large winners.
- Position size alone is not enough to identify the winner.
- Mint-to-buy latency alone is not enough either.

Examples:
- LP: bought about 1 second after mint, approximately -16.2%.
- 努努: bought about 2 seconds after mint, approximately +22.4%.
- 算命: bought about 298 seconds after mint, approximately +191%.

## B2 -> A sequence

This is currently the most important hypothesis.

### 宝拉

Token:
`0x06406c6c75fb9c1f8f334265f9afb70244567777`

Sequence:
- B2 buy: 2026-09-25 02:10:22 UTC, 0.5 BNB
- B2 splits approximately 14.626M tokens to child wallet before A entry
- A buy: 2026-09-25 02:11:48 UTC

Synchronized exits:
- At block/time around 02:14:26 UTC:
  - B2 actual Swap output: about 0.527585 BNB
  - child actual Swap output: about 0.528498 BNB
- Combined output from that single synchronized reduction: about 1.05608 BNB
- This alone is about +111% versus the original 0.5 BNB cluster principal, before counting earlier/later exits.

### 星星人

Token:
`0x06a362cb9ebbf17c5aa85e56871a357d7b427777`

Sequence:
- B2 buy: 2026-09-25 02:10:49 UTC, 0.25 BNB
- B2 transfers approximately 14.713M tokens to child `dc1e...e089`
- A buy: 2026-09-25 02:27:53 UTC

Confirmed reconstructed proceeds already exceed about 0.6906 BNB across the cluster, versus 0.25 BNB initial principal.
- Confirmed lower-bound ROI: above +176%

B2 led A by about 17 minutes.

### Reverse-order sample: CLAIMR

Token:
`0x056970957cf6a8ba805591b80ff40c3848847777`

- A buy: 2026-09-22 13:16:19 UTC
- B2 buy: 2026-09-22 13:16:32 UTC
- B2: 0.025 BNB -> about 0.025108 BNB
- ROI: about +0.43%

Current hypothesis:
- `B2 first -> A later` may be materially stronger than `A first -> B2 later`.
- Current overlap sample is too small for a statistical conclusion. Must expand before execution.

## A / B timing conclusion

Observed examples support:
- A is often an earlier high-frequency sniper than B.
- B can enter after A has already started reducing risk.
- Directly copying B is currently rejected.
- Directly copying A is also rejected without filters because A contains rapid-loss / low-quality sniper attempts.

## Deployer relationship

High-frequency deployer:
`0x3197afa90a90074fe25a7b30afd8abf5b18d2bde`

Observed:
- Deployed multiple Flap tokens in a short period, including 宝拉.
- Funding chain previously traced through `0xcefa...3095` and `0x7f2f...b8b8`.
- Only 宝拉 among the sampled recent deployments was jointly selected by A/B.

No direct funding link between B2 and this deployer has been confirmed yet.
Do not classify deployer and B2/A/B as the same controlling party without additional evidence.

## Trading decision gates

No live auto-copy yet.

A candidate trade becomes research-actionable only if:
1. B2 or a strongly linked child wallet makes an active Router buy.
2. Entry can be detected at pending / one-block latency where technically possible.
3. A has not already materially repriced the token.
4. Price is still close enough to B2's executable price after token tax / protocol fee / impact.
5. No immediate B2/child reduction indicates a failed probe.
6. Deployer, first buyers and funding graph do not show an obvious dump/rug pattern.
7. Historical simulation for the corresponding signal class remains positive after realistic costs.

Higher-confidence experimental condition:
- B2 enters first.
- A enters later.
- B2/child cluster does not immediately fully exit.
- The price has not already moved beyond the backtested profitable delay envelope.

## Required next backtest

Expand B2 to at least 30 closed trades, then preferably 50-100.

For every trade store:
- token
- mint time
- B2 buy time
- B2 principal
- child-wallet split yes/no
- child addresses used
- A first-buy time if any
- B first-buy time if any
- all realized Swap outputs
- holding time
- realized ROI
- remaining token balance
- creator / creator funder
- first 20 buyers
- repeated early buyers
- price impact at simulated +1 / +2 / +3 block entry

Compute:
- unconditional EV
- B2-first/A-later EV
- B2 + child-wallet co-activity EV
- no-child EV
- one/two/three-block latency EV
- tail dependence after removing top 1 and top 3 winners
- max drawdown for a fixed-size copy strategy

Only advance to tiny live capital if net EV remains positive after fees/tax/gas/slippage and remains positive under realistic latency.

## Data-quality notes

- PnL figures above use actual transaction value and decoded Swap-event amountOut where stated.
- Unrealized token balances and UI portfolio valuations are not counted as realized profit.
- Some tax-token sells emit multiple transfer legs; count the Swap output once per sell transaction.
- Alchemy Free currently limits broad eth_getLogs ranges, so event reconstruction is performed per exact sell block.
- Blockscout current MCP does not support BSC chain ID 56, so it is not used as a substitute for this BSC backtest.


## Backtest expansion — 31 closed samples

Updated: 2026-09-25 Asia/Bangkok

### 29 ordinary closed B2 samples

All figures below use reconstructed on-chain BNB principal and actual Swap-event amountOut. Open/unrealized positions are excluded.

Aggregate:
- Closed ordinary trades: 29
- Principal: 4.4675623003 BNB
- Actual proceeds: 5.0336856815 BNB
- Realized gross PnL: +0.5661233812 BNB
- Aggregate gross ROI: +12.67%
- Winners: 12 / 29
- Win rate: 41.38%
- Median trade ROI: -5.39%

Tail dependence:
- Remove largest winner FROGE: remaining 28 trades are still about +2.95% aggregate ROI.
- Remove top three winners FROGE, 算命 and FSTOCK: remaining 26 trades are about -8.00% aggregate ROI.
- Therefore B2's observed positive expectancy is materially dependent on capturing rare large right-tail winners. A tight take-profit that truncates winners is likely harmful.

New reconstructed closed samples:
- 超级智能: total buy 0.15 BNB -> 0.1930465254 BNB, about +28.70%.
- 杜杜: total buy 0.10 BNB -> 0.0806225235 BNB, about -19.38%.
- BINANCIEN: 0.50 -> 0.4730723320 BNB, about -5.39%.
- 交易人生: 0.50 -> 0.4758723039 BNB, about -4.83%.
- 东方的神秘力量: 0.0425623003 -> 0.0419695525 BNB, about -1.39%.
- DOG: 0.075 -> 0.0809508660 BNB, about +7.93%.
- 华: 0.075 -> 0.0555016987 BNB, about -26.00%.
- Kabosu: 0.125 -> 0.1371866871 BNB, about +9.75%.
- FOMOSquare: total buy 0.20 -> 0.1049881169 BNB, about -47.51%.
- FROGE: total buy 0.10 -> 0.5372428101 BNB, about +437.24%.
- FSTOCK: total buy 0.30 -> 0.4555054083 BNB, about +51.84%.
- 猴子币: 0.15 -> 0.0978659404 BNB, about -34.76%.
- 电话猴: 0.075 -> 0.0681020243 BNB, about -9.20%.
- TERMINAL: total buy 0.15 -> 0.1062797522 BNB, about -29.15%.
- BFARM: 0.075 -> 0.0608755549 BNB, about -18.83%.
- JEVCAT: 0.075 -> 0.0801613517 BNB, about +6.88%.
- YIHE-405b: 0.075 -> 0.0776354594 BNB, about +3.51%.
- YIHE-cfbc: 0.075 -> 0.0755162408 BNB, about +0.69%.
- AB: 0.075 -> 0.0615417753 BNB, about -17.94%.

### B2/A order-direction evidence

Confirmed overlap examples now include:

B2 first, A later:
- FROGE: B2 first, A about 48 seconds later; B2 realized about +437%.
- 宝拉: B2 first, A later; currently confirmed lower-bound cluster proceeds imply >+111% versus initial B2 principal before other exits.
- 星星人: B2 first, A about 17 minutes later; currently reconstructed lower-bound cluster proceeds imply >+176%.

A first, B2 later:
- CLAIMR: A about 13 seconds first; B2 about +0.43%.
- FOMOSquare: A about 19 seconds first; B2 about -47.51%.
- FSTOCK: A about 5 seconds first; B2 about +51.84%.

Conclusion:
- `B2 first -> A later` remains a promising high-upside filter in the current sample, but order direction alone is not sufficient because FSTOCK is a strong counterexample.
- Continue testing a multivariate rule using order direction, B2 initial size, repeat/add buys, child-wallet split, immediate reduction behavior and current price displacement.

### 31-sample conservative lower bound

Adding 宝拉 and 星星人 to the 29 ordinary samples using only the currently decoded lower-bound proceeds:
- Total principal: about 5.2175623003 BNB
- Confirmed proceeds lower bound: about 6.7804019757 BNB
- Confirmed PnL lower bound: about +1.5628396754 BNB
- Conservative aggregate ROI lower bound: about +29.95%

This is not yet a copy-strategy return because it assumes B2's own execution prices. Next required test is realistic +1 / +2 / +3 block entry latency plus token tax, protocol fee, gas and price impact.
