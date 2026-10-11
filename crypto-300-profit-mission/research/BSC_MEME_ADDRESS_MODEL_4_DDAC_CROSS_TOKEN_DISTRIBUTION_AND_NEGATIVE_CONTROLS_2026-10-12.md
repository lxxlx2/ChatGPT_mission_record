# Address Model 4 | DDAC cross-token distributor cohort and negative-trade controls

Date: 2026-10-12 (Asia/Bangkok)  
Subject wallet: `0xddac928a240bdace3994c2cc0783d4e29a002127`  
Status: **HISTORICAL RESEARCH / OBSERVE_ONLY / NO_GO**

## Key result: 69 matched cross-token distributions

Both the fully paginated GIGGLE Fund and 币安人生 ERC20 history archives show inbound transfers from the same contract, `0x2f7fe96e3d0308cdbf6143e7dc0bb05df73a4a83`. GIGGLE has 70 source transfers out of its 71 total inbound records; 币安人生 has 69 of its 78 total inbound records.

Applying chronological monotone one-to-one minimum-total-absolute-block-distance matching to the **frozen source-only cohorts** produces **69 unique paired events**; one source-funded GIGGLE transfer remains unmatched. All paired hashes are distinct across tokens. Absolute block gaps have minimum 2, median 13, and maximum 108; 65 pairs are within 20 blocks and 68 within 100 blocks. Binance Life arrives first in 68 pairs. This alignment is a reproducible finding on archived transfers, **not** proof of a common economic payout rule or owner control.

Direct chain spot checks: **4 original Transfer logs** (both token cohorts' first and last pair) re-read with `eth_getLogs` on `bnb-mainnet`, filtered by exact canonical token CA, sender and wallet, and matched original block, tx hash and raw amount. The other 134 paired Transfer rows are supported by the archived fully paginated input artifacts and were **not** newly queried on chain here.

Evidence source: `BSC_MEME_DDAC_GIGGLE_BINANCE_LIFE_69_PAIRED_SOURCE_DISTRIBUTIONS_2026-10-12.json` (full 69 pair table, one unmatched event, four fresh onchain samples).

## Economic classification of five scoped token histories

| Token | Original trade / episode evidence | Scoped capital evidence | Inventory / limitations |
| --- | --- | --- | --- |
| GIGGLE Fund | 71 ERC20 inward transfers, 0 outward; no original signed buy/sell established | No realized GIGGLE trade PnL | Archived net residual `1.887709367246662512` tokens; repeated shared-source inflows should not count as profitable buys |
| 币安人生 | 7 owner-signed WBNB V2 pool transactions, 3 buys + 4 sells; 69 shared-source receipts are separate | Original 7 pool-event block native delta +0.462620236646267526 BNB | Archived `21.665763559661594798` tokens unclosed; no complete realized economic PnL |
| MARSCOIN | 18 owner-signed pool trades (16 SPCXB/MARS V2, 2 USDT/MARS V3); 14 direct V2 raw swaps, 2 fallback quote transfers | 29 involved token-event block native change +3.409712195316107766 BNB | 12/16 SPCXB route hops to USDT independently matched from two V3 pools; 4 unresolved; `3.050660512775076744` token residual, not final PnL |
| 我踏马来了 | 5 ERC20-zero-balance-to-zero-balance episodes, 4 positive and 1 negative on scoped native-block accounting | +2.329674116520169814 BNB over 5 sampled closed episodes | 1 negative episode; native block scope is not audited complete wallet capital PnL |
| 龙虾 | 2 ERC20-zero-balance-to-zero-balance episodes | -0.183543131928304728 BNB over 2 sampled closed episodes | Both episodes have negative scoped native-block changes |

The last two rows were recomputed from the archived `BSC_MEME_DDAC_IFML_LOBSTER_CLOSED_EPISODES_NATIVE_CASHFLOW_2026-10-11.json`: each episode's signed per-block BNB changes sum exactly to its recorded episode change and episode totals agree with original token-scoped net wei.

| Closed sample | Episodes | Positive native scope | Negative native scope | Native sum |
| --- | ---: | ---: | ---: | ---: |
| 我踏马来了 | 5 | 4 | 1 | +2.329674116520169814 BNB |
| 龙虾 | 2 | 0 | 2 | -0.183543131928304728 BNB |

**Do not sum the five token-scope native numbers into DDAC's verified total realized PnL.** They have different observation windows, unresolved owner/counterparty attribution and quote-asset exposures, gas limitations and open token inventory. In particular MARSCOIN routed USDT/SPCXB funds cannot be equated directly to BNB without matching full routes.

## Model consequences

1. De-duplicate all ERC20 receipt rows by token, tx hash, origin signer and pool evidence. Specifically remove **139 shared-source receipt events** (70 GIGGLE + 69 币安人生) from candidate original active-trade counts; retain them as factual distributions with **economic cause unresolved**. This does not erase the independent 7 verified Binance Life active pool transactions.
2. Preserve DDAC as an active major-token multi-opportunity candidate, because it has independent original pool trades and previously documented completed closed episodes. The GIGGLE distribution cohort **does not support** an independent GIGGLE trading win.
3. Carry through the **three recorded negative closed episodes** across IFML and 龙虾 as adverse evidence, alongside positives, when assessing whether DDAC can consistently capture big events.
4. Before adding a followability/return ranking, independently verify full native plus WBNB/USDT/SPCXB cash receipts, router gas/tax, historical inventory, wallet/controller clustering and a no-hindsight opportunity denominator. Do not treat BNB native-block deltas as final isolated strategy PnL.
5. Next chain work: inspect the source contract's payout function and original sender/tx receipts at representative correlated events; complete remaining four unresolved MARS quote route cases; evaluate the same frozen opportunity matrix across other candidate wallets and missed major token launches.

Evidence levels: **DIRECT_CHAIN** for four current-period receipt-log spot checks; **ARCHIVED_CHAIN_ARTIFACT + arithmetic QA** for remaining original event histories and negative episode outcomes; **INFERRED** for possible coordinated distribution mechanism; **UNCONFIRMED** for causal program identity, origin controller, total portfolio PnL and trade followability.

No change to runtime, notifications, trade automation, threshold rules or candidate universe. Production remains **NO_GO**.
