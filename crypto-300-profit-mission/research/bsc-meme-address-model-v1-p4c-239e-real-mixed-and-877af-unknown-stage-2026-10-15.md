# BSC P4-C — 239E 龙虾两笔真实 BNB 原生资金结果、877AF MARSCOIN 原始库存闭合与完整 23×19 样本对账

Date: **2026-10-15 Asia/Bangkok**. Research only. Same [Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40). This stage is **PARTIAL**, not a candidate trading recommendation or a completed repeat-winner model. **P4-B first public executable opportunity U unknown, P5 blocked, production NO_GO, NO_MERGE, NO_DEPLOY.**

## Why this batch was valid and frozen

The original P2 precommitted balanced 4-round batch was frozen BEFORE fresh RPC: P2 episode indexes 29/30 for `239E / 龙虾` (a previously native-negative and native-positive pair) and indexes 37/38 for `877AF / MARSCOIN` (a previously native-positive and native-negative pair). **2 distinct wallets, 2 frozen major 2026 exact CA, 4 original inventory episodes, 11 original signed transactions verified on BNB chain ID 56**. Selection is outcome-stratified, NOT a representative wallet success-rate or an unbiased first-market sample. Original manifest `bsc-meme-address-model-v1-p4c-next239e877af-balanced-four-rounds-precommit-2026-10-15.json`; subsequent source-query manifest `bsc-meme-address-model-v1-p4c-next239e877af-economic-original-probe-precommit-2026-10-15.json`, before fresh events/receipts/owner balances.

### First original 239E / 龙虾 two rounds — actual settled wallet BNB native PnL with named limitation

Original EOA: `0x239e74bfbd02d71cdc70fecc2d505dc13acfb337`; major CA: `0xeccbb861c0dda7efd964010085488b69317e4444`; pool `0x22af7297243c4eef12e2d5a4f888b92e56bf127c`.

| Frozen round | Original buy count | Original sell count | Raw token in = out | Actual observed EOA wallet BNB net (including original paid Gas and observed route residual) | Sign |
| --- | ---: | ---: | --- | ---: | --- |
| P2 #29 | 2 | 1 | `5733541559033810010318` | **-0.015332805033002259 BNB** | native owner loss |
| P2 #30 | 1 | 1 | `9324059273385582494656` | **+0.022647938898252522 BNB** | native owner profit |

**How independently proven:** Re-read 5 exact CA owner-directed original ERC20 Transfer source transactions, **5/5 full original successful receipts** (`status=0x1`), matching original owner and original token, purchase WBNB Deposit plus original WBNB pool transfer, sale pool WBNB transfer plus original WBNB Withdrawal in each original transaction, original paid receipt Gas and **5/5 historical EOA BNB `N−1`/N balance snapshots**. Independently checked only **one original signed outbound external owner transaction in each of five blocks**, and **zero external native BNB credits to the original owner** in those blocks (all fully returned with no next page). Original EOA token inventory closed to **zero** in both rounds.

Wallet native delta on buys equals `-WBNB_in_pool - receipt_gas - additional_observed_route_cost`; on sells equals `+WBNB_from_pool - receipt_gas - additional_observed_route_cost`. All five additional route residuals are nonnegative and source measured, not assumed zero. Reconciled original network Gas / other routing-cost residual:

| Round | Paid network Gas (BNB) | Other route cost residual (BNB; origin/fee receiver not independently attributed) |
| --- | ---: | ---: |
| #29 | 0.000462361 | 0.003419229310441465 |
| #30 | 0.000336679 | 0.005530936882066810 |

These native wallet economic outcomes are established for those exact signed historical trades; **do not label the extra residual a particular platform fee/tax beneficiary** or assume the entire EOA's lifetime profit. Missing trace of the aggregator's internal fee beneficiary does not change the actual observed wallet debit/credit in the five original blocks; it **does** restrict any breakdown of fee semantics. More importantly, a historical owner actually making a positive closed round **is not proof an observer could enter 1/5/15 minutes later**.

Source-pinned normalized result: `bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json`; immutable replayer `bsc_meme_address_model_v1_p4c_239e_dragon_two_native.py`; adversarial tests `test_bsc_meme_address_model_v1_p4c_239e_dragon_two_native.py`; all 6 original source blob SHAs are in the source manifest. Raw immutable sources include `bsc-meme-address-model-v1-p4c-next239e877af-original-ca-events-part1-2026-10-15.json`, `bsc-meme-address-model-v1-p4c-next239e877af-receipts-part1-2026-10-15.json`, native balance part1, original EOA block external outgoing and incoming source files.

### 877AF / MARSCOIN two closed-quantity but NOT economically settled rounds

Original EOA `0x877af245c61289b24f0c619a4346cdbc68f1aaac`; exact CA `0xfe189e97832da1573e4e4ff034f4ffc3a15c7777`.

- P2 #37 (previous native block scope positive) and P2 #38 (previous native block scope negative) each have successful original 2026 signed-transaction identity from the prior P4-C stage; **6/6 original buy/sell transaction token Transfer event groups read in complete, single-block filtered `eth_getLogs`; both exact original ERC20 token inventory round trips fully close**. Their outbound MARSCOIN token events include pool and token-contract transfers. Native wallet historical **6/6 N−1/N balance snapshots available**, with the same P2 signs.
- However, **all 6 full transaction receipts returned truncated source bodies**. Original free read-only RPC has not proven MARSCOIN's complete original swap quote-asset actual cashflow, paid per-tx Gas and routing. Original wallet native balance block changes alone DO NOT become actual settled trade profit/loss or a claim of 0 gas or 0 tax. Status remains `OWNER_TOKEN_CLOSE_BUT_NONNATIVE_QUOTE_GAS_UNRESOLVED`; no newly promoted economic gains or losses.
- Immutable normalized file `bsc-meme-address-model-v1-p4c-877af-marscoin-inventory-closed-quote-unresolved-2026-10-15.json`, deterministic replay `bsc_meme_address_model_v1_p4c_877af_inventory.py`, tests `test_bsc_meme_address_model_v1_p4c_877af_inventory.py`. Raw receipts/events/native parts 2 pinned; missing material = actual quote output to EOA, gas per original tx, any residual aggregator route fee and causal settlement path. Do not retry the same truncated whole-receipt RPC indefinitely, and do not call MARSCOIN a winning or losing economic round.

## Frozen 23×19 whole-cohort correctly denominated

Add-only overlay: `bsc-meme-address-model-v1-p4c-23x19-five-native-rounds-mixed239e-2026-10-15.json` with replayer `bsc_meme_address_model_v1_p4c_five_native_rounds23x19.py` and guard tests.

- Original **23 wallets × 19 exact CA = 437 cells** unchanged; original P3 verified recent signed swap owner count **7** unchanged.
- **5** source-proven historical BNB native owner buy/sell *rounds*: **3 positive** (8E6B HAJIMI, 8E6B 龙虾, 239E 龙虾 #30); **2 negative** (DDAC 龙虾, 239E 龙虾 #29).
- These **5 rounds cover only 4 distinct original wallet×CA cells**: 8E6B/HAJIMI, 8E6B/龙虾, DDAC/龙虾, 239E/龙虾. All remaining **433 cells `NOT_ECONOMICALLY_AUDITED`**; the 877AF/MARSCOIN 2 inventory-closed-but-unpriced rounds remain within the 433 (not falsely qualified).
- **239E Dragon is explicitly `MIXED_ORIGINAL_NATIVE_ROUNDS_POSITIVE_AND_NEGATIVE`** in the one original wallet×CA cell; one positive and one negative for the same major CA cannot mean two unrelated repeat-winning major tokens.
- Exactly **2 different wallets** have at least one source-verified native positive original round, but only **8E6B** has independently verified profitable original rounds on **2 distinct major CAs**. This is **not a statistically unbiased ranking** and still cannot establish followability after 1/5/15 minutes or first executable public U.
- Verified current follower-qualified signals: **0**. No buy size, victory rate or real-time recommendation is justified.

## Review and stage status

Prior other-AI independently reported `APPROVE` only for pinned SHA `ea6684a3478d301534ff9d26b5984367eb7530f3`; current new original economic round classifications require a **fresh fixed-SHA independent other-AI evidence/code review at this stage's review gate**. Under `bsc-meme-address-model-v1-development-rules-2026-10-15.md`, provide a complete copy-ready pinned-SHA reviewer prompt in the same user-visible response, including PR, code, source and CI, and ask for `APPROVE / REQUEST_CHANGES / BLOCKED_INSUFFICIENT_EVIDENCE`. Do not treat CI as the second AI's review.

**Mainline next:** Resume cross-owner original 2026 major CA P4-C positive and negative cohorts, prioritize cases with complete actual receipt/quote, then P4-B globally first observer-visible and executable opportunity U including actual available wallet capital, and finally P5 precommitted 1/5/15min follower historical access, capacity, tax, gas and exit. Avoid paid GMGN/trace, no overfit to 239E, no Frank/Monster/CA UI changes. Draft PR #40 no merge; no production services, alerts, trading, background collection or Mac deployment.
