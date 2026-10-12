# Address Analysis Model 4 — Stage 6: 23×19 complete presence classification and MARS early trader capital

Date: 2026-10-12, Asia/Bangkok. Historical BNB Chain only, exact **23** frozen candidate EOAs × **19** frozen canonical token CAs. **OBSERVE_ONLY / PRODUCTION NO_GO**.

## Main verified results

This round independently split busy addresses' 19 CA histories into smaller fixed subsets. Every **completed subset** was exhausted in both token-transfer directions and each nonzero subset's integer `in - out` was matched to current onchain `balanceOf(wallet)`. The historical 2026-10-11 baseline, V3 and V4 overlays remain unmodified.

**V5 is a two-layer coverage measurement.** We have evidence of whether there have been positive-value ERC20 transfers at **437/437** wallet/CA intersections, but only **367/437** have *complete cursor-exhaustive* positive-value ERC20 histories.

| Frozen 23×19 ledger status | Cells | Valid interpretation |
| --- | ---: | --- |
| Complete with at least one ERC20 transfer | 78 | Full transfer history of exact canonical CA |
| Complete with no nonzero ERC20 transfer | 289 | No observed nonzero ERC20 transfer in full exact-CA query |
| Known transfers, incomplete pagination | **70** | Presence is proved from saved original tx hashes; aggregate amounts, absence of other transactions and inventory unknown |
| No evidence either way | **0** | None left in this fixed roster |
| Total | **437** | 23 × 19 |
| Wallets with all 19 CAs complete | **14/23** | 9 wallets still need work on high-volume CAs |
| Complete exact token-quantity-zero wallet/CA pairs | **44** | Does not prove earned BNB or positive final PnL |

The 40 V4 `PARTIAL_UNKNOWN` cells were all corrected after finding their saved original ERC20 transaction hashes, via independently verified `BSC_MEME_V4_RESIDUAL40_PREFIX_PROOF_BATCH_A` (22 cells) and `BSC_MEME_V4_RESIDUAL40_PREFIX_PROOF_BATCH_B` (18 cells). **Zero "presence unknown" is NOT the same as zero "transfer count incomplete": 70 remain open.**

### Nine incomplete high-frequency wallets

| Wallet | Distinct token CAs with positive ERC20 Transfer evidence | Fully cursor-complete CAs | Positive-transfer CAs still unexhausted |
| --- | ---: | ---: | ---: |
| `0xa83b73f5…` | 17 | 4/19 | 15 |
| `0xadffbebb…` | 14 | 10/19 | 9 |
| `0x2adf961b…` | 12 | 8/19 | 11 |
| `0x877af245…` | 12 | 13/19 | 6 |
| `0x0abb84c9…` | 10 | 11/19 | 8 |
| `0x11a73279…` | 8 | 12/19 | 7 |
| `0x498528e3…` | 7 | 15/19 | 4 |
| `0x5c0c5d78…` | 7 | 14/19 | 5 |
| `0x8d8c031f…` | 6 | 14/19 | 5 |

These 9 wallets are not ranked here by tokens touched: distributions, launch allocations, quote token routing, burns/taxes, custodial receipts and true owner-signed buys are economically distinct. The existing 14 full-roster wallets remain independent comparators, including proven losing and nontrading controls.

## MARSCOIN: newly verified earliest sampled-block buyer is 877AF

Frozen reference: earliest archived `FOUR_MEME_PRE_V2` pool sample block **112441460**. It is a **sample window**, not confirmed pool creation or first tradable block.

| Comparative item | `0x877af245…` | `0x498528e3…` |
| --- | ---: | ---: |
| First original wallet-signed MARS buy block | **112441460** | 112441470 |
| Gap after frozen earliest pool sample | **0 blocks** | 10 blocks |
| Before-first-exit original wallet-signed buys | **7 / 7** | **7 / 7** |
| Original total BNB `msg.value` into those buys | **0.610000000 BNB** | **1.400000000 BNB** |
| Historical buy blocks | 4 | 5 |
| First original wallet-signed sell block | 112441495 | 112442022 |
| Gross MARS sold in first exit / MARS received before exit | **64.1093%** | **9.9999%** |
| Raw MARS quantity remaining from the pre-exit acquisitions | **35.8907%** | **90.0001%** |
| Wallet BNB change on first-sale block (gas and any same-block movements included) | **+0.508198463 BNB** | **+0.399318753 BNB** |
| First-sale native wallet inflow as percent of original seven-buy `msg.value` | **83.3112%** | **28.5227%** |
| Sum of audited original seven buy blocks **plus first sale** native BNB block changes | **-0.103228071 BNB** | **-1.001063455 BNB** |
| Original MARS first-sell ERC20 3% tax `floor(3% × gross)` | Exactly reconciled | Exactly reconciled |
| Full MARS transfer history and final closed position PnL | **Unverified / open** | **Unverified / open** |

`877AF`: first self-signed buy was **0.55 BNB**, followed by six more self-signed buys of **0.01 BNB** each on blocks 112441467–470, all before its first sale at block 112441495 (35 blocks after the first). All four buy-block native N−1/N deltas and the first sell-block native delta were independently checked. The original seven buy messages total **0.61 BNB**. Its first sale moved **64.1093%** of the MARS quantity received during those seven buys. Remaining tokens are not valued here.

`498528`: seven original self-signed buys of **0.2 BNB each**, on blocks 112441470, 471, 555, 584 and 585, total **1.4 BNB** before its first sell at 112442022. All five buy-block native N−1/N deltas were checked. Its first sale moved only **approximately 10%** of previously received MARS tokens. Other token receipts and later MARS sells remain unexhausted.

**Do not label either negative net BNB buy-blocks-plus-first-sale calculation as a trading loss.** Both exits were partial, the earliest sampled pool date is not first-tradable proof, later disposals are omitted, and quote pools, wallet gas, other transaction overlap and non-BNB settlement assets are not yet comprehensively reconciled. Likewise, native inflow at the first sale is not an independently isolated router net receipt for all trade legs.

## Cross-token provenance and candidate controls

Eight additional first original transfer transaction signers were checked for the two wallets. **7/8** were original wallet signed; `498528` TUT first inbound was explicitly **other-signed** via `0xeb91d9…` selector `0x84da2c7b`, so do not count it as an owner purchase. `498528` 牛来 sampled first inbound was wallet signed with **1 BNB** original input. `877AF` sampled first inbound trades on 币安人生, 哈基米 and TUT were wallet signed with **0.52 BNB**, **0.465 BNB**, and **0.1 BNB** respectively. The first observed `877AF` MARS outgoing tx was wallet signed, and its earlier true wallet-signed MARS inbound was subsequently recovered at block 112441460.

For a wallet to be promoted to an **observable followable trader**, still require: exhaustive original owner-signed entry/exit transaction ledger, gas and router fee decomposition, token taxes, no hidden funding/rewards, same-block deconfliction, open inventory, adverse missed-signal and negative outcomes, launch-to-order latency, pre-frozen market-wide eligible opportunity denominator and an independent untouched out-of-sample follower simulation.

## Durable files and immutable evidence

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V5_2026-10-12.json` (read-back blob `8761851193d99cc26d0c8a3e95f1a800ae50f925`)
- `BSC_MEME_877AF_MARS_SEVEN_EARLY_BUYS_BEFORE_FIRST_EXIT_2026-10-12.json` (read-back blob `6f1e9c378a15f0cdd27a6cdf1feac905b3c6a260`)
- `BSC_MEME_498528_MARS_SEVEN_EARLY_BUYS_BEFORE_FIRST_EXIT_2026-10-12.json` (read-back blob `2dde5a2f9de4500a0a128336235034d06e559c3b`)
- `BSC_MEME_877AF_MARS_FIRST7_BUY_NATIVE_BLOCKS_AND_FIRST_EXIT_2026-10-12.json` (read-back blob `9d2441799d45e90920c51659d6cf36e0d40edfed`)
- `BSC_MEME_498528_MARS_FIRST7_BUY_NATIVE_BLOCKS_AND_FIRST_EXIT_2026-10-12.json` (read-back blob `3ed08d676689ca287f5fb4568879945c2a7abd53`)
- `BSC_MEME_498528_877AF_CROSS_TOKEN_FIRST_ORIGIN_PROVENANCE_2026-10-12.json` (read-back blob `4c86fd282485c0d9e2f57558d8cfe7b28b3e2c89`)
- `BSC_MEME_V4_RESIDUAL40_PREFIX_PROOF_BATCH_A_2026-10-12.json` — original hashes for 22 unresolved cells.
- `BSC_MEME_V4_RESIDUAL40_PREFIX_PROOF_BATCH_B_2026-10-12.json` — original hashes for remaining 18.
- `BSC_MEME_877AF_MARSCOIN_EXACT_CA_FULL_HISTORY_FIRST_EXIT_2026-10-12.json` — first 40 in/out events with open pageKey preserved.
- `BSC_MEME_877AF_MARS_GENESIS_SAMPLE_OWNER_BUY_AND_SELL_NATIVE_QA_2026-10-12.json` — 0.55 BNB signed first buy and first exit 3% tax evidence.

Only Git research reports, immutable analysis snapshots, and candidate queue evidence pointers were changed. No new automation, price monitor, live trading rule, wallet signature, or production execution was started. **NO_GO**.
