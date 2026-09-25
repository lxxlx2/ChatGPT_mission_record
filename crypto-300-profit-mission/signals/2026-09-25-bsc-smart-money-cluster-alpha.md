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


## Incremental backtest update — 2026-09-25 20:54 Asia/Bangkok

Additional B2 closed sample:
- `花花` `0x37f5f45774bb540b4d342ba624e0499d6a2a7777`
- B2 active Router buy principal: 0.15 BNB
- Full later sell actual Swap amountOut: 0.149061550586942 BNB
- Realized ROI: about -0.63%
- No later A or B buy was found for this token in the checked history.

Updated B2 ordinary closed-trade aggregate:
- Closed samples: 11
- Total principal: about 1.70 BNB
- Actual realized proceeds: about 1.91881 BNB
- Gross realized PnL: about +0.21881 BNB
- Gross ROI: about +12.87%
- Winners: 4 / 11
- Win rate: about 36.4%
- Median trade ROI remains approximately -8.3%
- Removing the `算命` outlier leaves the other ten trades around -4.38% combined.

Open / excluded from realized-PnL aggregate:
- `KIMI` `0xd0c2337e71835dea2d2b2823c60ffa8d81677777`: fresh B2 Router buy 0.025 BNB at 2026-09-25 05:50:41 UTC; no B2 sell found yet; no A/B follow-on buy found yet.
- `BUFO` `0x057e599eb2d99a546773778cfe6c5275d50e7777`: B2 Router buy 0.25 BNB; no B2 sell found yet. B had historical BUFO activity earlier than this B2 entry, so it is not a B2-first -> B-later confirmation sample.
- `超级智脑` `0x5aee960f83c18e01a46cc2a3910ad6edcf6c7777`: B2 Router buy 0.1 BNB; no B2 sell found yet; no A/B follow-on buy found in the checked history.

Interpretation update:
- Unconditional B2 copying still does not pass the promotion gate because ordinary-trade profitability remains outlier-dependent.
- The strongest unresolved signal class remains `B2 first -> A later`; the currently confirmed 宝拉 and 星星人 examples remain exceptional winners, while reverse-order CLAIMR was near flat.
- Do not count open positions or wallet-marked token values as realized PnL.


## Initial execution-latency findings

Updated: 2026-09-25 Asia/Bangkok

Alchemy BNB RPC supports `eth_getBlockByNumber("pending", true)` and returns full pending transaction objects. Therefore a local monitor can inspect pending B2/child transactions before ERC20 receipt confirmation. This materially improves the feasibility of same-block / next-block detection.

### Representative real-price deterioration

The following comparisons use actual on-chain buy transaction BNB value divided by actual token output received. They measure market price deterioration after B2's entry. They do not yet include the hypothetical follower's own price impact.

#### FROGE

B2:
- 0.075 BNB -> 7,097,267.143 tokens
- average buy price = about 1.0567448e-8 BNB/token

Same B2 block:
- next 0.075 BNB buy -> 6,975,314.445 tokens
- next -> 6,856,478.250
- B2 child 9656 -> 6,740,653.267
- each sequential order gets progressively worse execution.

Next block:
- 0.69 BNB -> 56,959,095.307 tokens
- average price is about 14.63% above B2.

Two blocks after B2:
- 0.516 BNB -> 28,499,111.827 tokens
- average price is about 71.34% above B2.

FROGE's own realized B2 ROI was about +437.24%.
If a hypothetical copy receives the same eventual exit multiple but enters at the observed delayed price:
- +1 block price proxy: theoretical ROI about +368.7%
- +2 block price proxy: theoretical ROI about +213.6%

This remains highly profitable because FROGE was an extreme right-tail winner.

#### 宝拉

B2:
- 0.5 BNB -> 57,496,903.500 tokens
- average price about 8.69612e-9 BNB/token

Next block:
- first observed buy: 3 BNB -> 229,141,408.565 tokens
- average price about 50.55% above B2.
- another buy in the same block: 2 BNB -> 91,252,282.704 tokens
- average price about 152.03% above B2.

Three blocks after B2:
- observed 1.2 BNB buy -> 36,964,851.763 tokens
- average price about 273.31% above B2.

Using only the currently confirmed lower-bound B2-cluster ROI of about +111.2%:
- entry at the first next-block observed price would reduce the lower-bound theoretical ROI to roughly +40.3%
- entry at the later same next-block price would reduce it to roughly -16.2%
- entry at the +3-block observed price would reduce it to roughly -43.4%

This demonstrates that transaction ordering inside the next block can decide whether the same underlying winner is profitable to copy.

#### 算命

B2:
- 0.15 BNB -> 7,017,406.502 tokens

B2 child in the same block:
- 0.15 BNB -> 6,840,197.610 tokens
- about 2.59% worse average price than B2.

B2 realized ROI was about +191.15%.
At this later same-block price proxy, the theoretical follower ROI remains about +183.8%.

#### FOMOSquare

B2:
- first 0.15 BNB buy -> 5,418,538.124 tokens

Next block observed buy:
- 0.04 BNB -> 1,294,734.896 tokens
- about 11.60% worse average price.

B2 itself lost about -47.51%.
At the next-block price proxy, a follower following the same exit would lose roughly -53.0%.

### Latency conclusion

The profitable copy problem is asymmetric:
- Right-tail winners can tolerate some delay, but the delay tax can be enormous.
- Ordinary losers become worse after delay.
- A generic next-block follower can therefore lose expectancy even when B2's own gross backtest is positive.
- Same-block pending detection is materially more valuable than post-confirmation alerts.
- Pending detection alone does not solve selection quality; the trade filter still must identify which B2 attempts are worth following.

### Required latency expansion

Next:
1. Repeat real-price deterioration reconstruction across at least 15-20 closed B2 samples.
2. Compute equal-notional copy EV at same-block-later, +1 block and +2 block where observable.
3. Include own order-size price impact for candidate copy sizes 0.01, 0.025 and 0.05 BNB.
4. Add gas to entry/exit.
5. Preserve right-tail exits; avoid TP rules that cap the rare large winners.


## Final historical backtest snapshot — 2026-09-25 22:01 Asia/Bangkok

### Historical-universe completion

The available B2 direct `...7777` history was scanned backward through the earlier BSC block ranges. No additional `...7777` B2 activity was found in the earlier 2026-09-20/21 ranges checked. As of this cutoff, the clean historical universe that satisfies all of the following is 20 distinct closed trade cycles:
- B2 actively paid BNB into the Flap router.
- The token address ends in `7777`.
- Buy principal can be reconstructed from transaction value.
- The trade cycle is closed enough to reconstruct actual realized Swap output.
- Old positions, open positions and duplicate child-wallet legs are excluded as separate independent samples.

Do not inflate the sample to 30 by counting synchronized child-wallet legs as independent trades. The next 10 distinct closed signals must be treated as forward-validation data.

### 20 clean B2 closed cycles

| Token | Principal BNB | Actual realized BNB | ROI |
| --- | ---: | ---: | ---: |
| FROGE | 0.100 | 0.537243 | +437.24% |
| 算命 | 0.150 | 0.436730 | +191.15% |
| OPAI | 0.125 | 0.235697 | +88.56% |
| 超级智能 | 0.150 | 0.193047 | +28.70% |
| 努努 | 0.250 | 0.306119 | +22.45% |
| ILY | 0.075 | 0.082882 | +10.51% |
| Kabosu | 0.125 | 0.137187 | +9.75% |
| DOG | 0.075 | 0.080951 | +7.93% |
| 流浪狗 | 0.250 | 0.259282 | +3.71% |
| CLAIMR | 0.025 | 0.025108 | +0.43% |
| 花花 | 0.150 | 0.149062 | -0.63% |
| 交易人生 | 0.500 | 0.475872 | -4.83% |
| BINANCIEN | 0.500 | 0.473072 | -5.39% |
| 中华 | 0.050 | 0.045850 | -8.30% |
| 甲亢蛙 | 0.050 | 0.045648 | -8.70% |
| 菊花 | 0.075 | 0.066915 | -10.78% |
| LP | 0.500 | 0.418762 | -16.25% |
| Poly | 0.150 | 0.124824 | -16.78% |
| china | 0.050 | 0.040510 | -18.98% |
| 杜杜 | 0.100 | 0.080623 | -19.38% |

Aggregate:
- Principal: 3.45 BNB
- Actual realized proceeds: 4.2153836678 BNB
- Gross realized PnL: +0.7653836678 BNB
- Capital-weighted gross ROI: +22.19%
- Winners: 10 / 20
- Win rate: 50%
- Median trade ROI: approximately -0.10%
- Average winning-trade ROI: approximately +80.0%
- Average losing-trade ROI: approximately -11.0%

Tail dependence:
- Full 20: +22.19% capital-weighted gross ROI.
- Remove largest winner (FROGE): approximately +9.80%.
- Remove top two winners (FROGE + 算命): approximately +1.29%.
- Remove top three winners (FROGE + 算命 + OPAI): approximately -2.25%.

Conclusion:
The historical gross edge is real in the observed sample, but it is strongly dependent on a small number of convex winners. Unconditional copying does not pass a robust promotion gate.

### Real same-block execution penalty

A useful real-world latency proxy exists because strong-linked child wallet `0x9656...cf34` frequently bought the same token in the same block as B2.

Observed child execution price premium versus B2:
- FROGE: +5.29%
- DOG: +8.87%
- OPAI: +6.53%
- ILY: +6.86%
- CLAIMR: +1.63%
- 星星人: +8.15%
- 超级智能: +8.73%

Observed range: approximately +1.63% to +8.87%.
Median: approximately +6.86%.
Mean: approximately +6.58%.

This is materially better evidence than an assumed slippage percentage because it uses actual same-block sibling executions.

Applying observed same-block penalties where available and the observed median to the remaining historical trades as a conservative execution proxy:
- Adjusted aggregate ROI: approximately +14.6% before gas.
- Remove largest winner: approximately +2.8%.
- Remove top two winners: approximately -5.2%.
- Remove top three winners: approximately -8.5%.
- Adjusted median trade ROI: approximately -5.0%.
- Adjusted winners: 7 / 20.

This reinforces that execution latency substantially reduces the apparent edge and that rare winners remain essential.

### B2 / A overlap

A was checked against the 20 clean B2 cycles plus the two major cluster case studies.

Clean historical overlap:
- FROGE: B2 first, A later by approximately 48 seconds. B2 cycle ROI +437.24%.
- CLAIMR: A first, B2 later by approximately 13 seconds. B2 ROI +0.43%.
- OPAI: A first by roughly 4h55m, B2 later. B2 ROI +88.56%.

Additional major cluster cases:
- 宝拉: B2 first; A later by approximately 86 seconds. Confirmed synchronized B2/child realized output already exceeded 1.056 BNB in a single reduction block versus B2 initial 0.5 BNB principal.
- 星星人: B2 first; A later by approximately 17 minutes. Confirmed B2-originated B2/child proceeds already exceeded 0.6906 BNB versus 0.25 BNB initial B2 principal.

Thus all five observed B2/A overlap cases were profitable for B2 or the B2-originated cluster position. This is an important research signal, but n=5 is too small and discovered in a highly selected environment; it must not be treated as a guaranteed rule.

### Why waiting for A is too late

For the three B2-first -> A-later examples, A's first executable unit price was already materially above B2's first entry:
- FROGE: A unit price about 6.74x B2's.
- 宝拉: A unit price about 13.48x B2's.
- 星星人: A unit price about 4.48x B2's.

Therefore:
- A overlap is useful as a quality label for research.
- Waiting for A to buy before entering destroys much of the early-price edge.
- The actionable trigger, if eventually promoted, must be B2 / linked-wallet pending or same-block activity, not A confirmation.

### Final decision as of this cutoff

Historical backtest status: COMPLETE FOR AVAILABLE CLEAN HISTORY.
Live-auto-trade status: NOT PROMOTED.

Reason:
1. Gross historical edge exists.
2. Same-block execution still leaves a positive aggregate in this sample.
3. Median trade is approximately flat before execution penalty and negative after realistic same-block degradation.
4. The strategy turns negative when the top 2-3 winners are removed after latency adjustment.
5. There are only 20 independent clean closed historical cycles; counting child duplicates would be statistically invalid.
6. The strongest B2/A overlap pattern has only five observed cases and is not large enough for a robust rule.

### Forward validation gate

Use the next 10 distinct closed B2 `7777` cycles as an untouched forward set.

For each future signal record:
- B2 pending tx detection time
- actual B2 tx inclusion block
- simulated follower inclusion block
- B2 unit price
- follower executable unit price
- child-wallet same-block activity
- A/B later participation
- realized B2 exit path
- copy-strategy realized exit path
- gas
- protocol/token tax
- realized copy PnL

Promotion criteria for tiny-capital execution:
- At least 30 total independent closed signals (20 historical + 10 forward).
- Forward set net positive after actual/realistically simulated execution costs.
- Combined result remains positive after removing the single largest winner.
- Preferably remains non-negative after removing the top two winners.
- No reliance on waiting for A confirmation.
- Maximum per-trade experimental risk must remain small until the forward gate passes.

Current practical signal hierarchy:
1. Detect B2 / linked-wallet active buy as early as possible.
2. Same-block child co-execution is useful context but not sufficient by itself.
3. A later overlap is a strong ex-post quality marker, not an entry trigger.
4. B remains a late attention signal and should not be copied directly.
