# BSC address model V1 — P4-C Stage: frozen 7-wallet independent cross-major native settlement batch

Date: **2026-10-15 Asia/Bangkok**. Branch: `research/bsc-address-model-v1-20261013`. Original **Draft PR #40**, read-only research. **P4-C PARTIAL; P4-B executable opportunity U unresolved; P5 BLOCKED; NO_GO / NO_MERGE / NO_DEPLOY**.

## Objective and precommit

The frozen business goal has **not** changed: find multiple owner-signed repeatedly profitable 2026 major-BSC-Meme wallets with real net economic PnL, negative controls, wallet funds at first observer-visible executable opportunity U, and defensible 1/5/15-minute delayed follower execution. Do not optimize one DDAC spectacular early buy, rescan all 437 cells unnecessarily, or promote an ERC20 transfer or sampled BNB increase to an investable signal.

Used existing P3 **7** recent strict owner market-swap signers from frozen 23-EOA roster; fixed **5 original inventory-round candidates across 4 wallets** plus **2 activity-only controls** in `bsc-meme-address-model-v1-p4c-sevenwallet-balanced-five-round-precommit-2026-10-15.json` before new RPC reads. Prior independently closed **DDAC 龙虾 negative** was kept without rescanning it. Samples represent both positive and negative historical economic directions, multiple EOA and CA. No new wallet added to universe.

Source-signed original tx rechecks: **14/14** hash/block/owner identity; 11/11 original independent historical **BNB wallet N−1 and N** block balance snapshots; **6 complete successful receipts**, **8 receipt bodies truncated** (not actual failed tx). All original raw/normalized evidence is Git-blob pinned. No GMGN, paid trace provider or fake Tx status.

## Outcome table — economic grade is not just sign

| Original wallet | 2026 major CA | Fresh selected owner-block net, BNB | Original complete success receipts | Economically settled? |
| --- | --- | ---: | ---: | --- |
| 8E6B `0x8e6b3c9c…4e9ea0` | 哈基米 / HAJIMI | **+0.268592992917629933** | 3/3 | **YES: actual positive original WBNB/Gas, raw inventory zero** |
| 8E6B | 龙虾 | **+0.253300282319389315** | 2/2 | **YES: actual positive original WBNB/Gas, raw inventory zero** |
| ADFF `0xadffbebbd…3946d` | 龙虾 | +0.004522437855804654 | 1/2 | **NO: NATIVE_BLOCK_SCOPE_ONLY** |
| 2ADF `0x2adf961b…5475ba` | 牛来 | +0.031837686901930499 | 0/2 | **NO: NATIVE_BLOCK_SCOPE_ONLY; possible distinct quote/tax** |
| A83B `0xa83b73f…48811` | 牛来 | −0.213598956812665039 | 0/3 | **NO: NATIVE_BLOCK_SCOPE_ONLY; two owner buys in one block counted ONCE** |
| DDAC `0xddac928a…002127` | 龙虾 | **−0.092169615514614272** | Prior completed independent sale proof | **YES: actual successful Four.meme TokenSale negative native round** |
| 0ABB and 498 | P3 latest original strict major swap only | Not an economically closed sample | Source signer independently rechecked | **ACTIVITY_ONLY; no profit/loss assigned** |

The two independent *positive* 8E6B original closed rounds across **two distinct CAs** total **+0.521893275237019248 BNB**; historical signed buys to full inventory zero, native account movement + actual historical on-chain WBNB withdrawal and Gas are fully reconciled. This is not 8E6B's full-wallet cumulative PnL, and two selected winners do not demonstrate out-of-sample repeatability or follower profitability. The 3 other newly examined rounds' BNB block scopes have genuine signs but still lack equivalent owner buy/sell quote full cashflow success proofs. Do not call ADFF/2ADF new source-approved winners or A83B a new complete realized loser until those gaps close.

### Independent real positive round details — 8E6B

**HAJIMI:** original signed buy tx `0x379a9f56fa6b47182c30a5854240aeb08a599b61d530ea969a446adfbfa09231`, native wallet debit `5.005442723` BNB; successful original signed sells `0x7e6c7bfecd6815c38ad53af6d15faef516f6aec40ca5d5ee7ca2200053357efe`, `0x3055cbb9f252a4b20a8cb2a127011fea8fc3c4ccaa24464a7f4bd75881d0e95e`. Real two WBNB withdrawal amounts `2.626966650753062114` and `2.647606433164567819` BNB; verified receipt paid gas is subtracted and historic wallet credit totals `5.274035715917629933` BNB. Original receipt ERC20 HAJIMI buy quantity exactly equals combined two sells. Net **+0.268592992917629933 BNB**, approximately **+5.36%** relative to original native buy debit.

**龙虾:** original signed buy `0xe96df53014497d00b74d6a08fb903661b35a4ceea42851bcb31de80fca223f34`, native wallet debit `3.00002109684` BNB; successful signed sell `0xd3b7eafb4d5193be7f7ff9dd62b968a65fae16b37c430726e13207ed51c71530`, gross WBNB `3.253458601159389315` (actual receipt), native after paid gas `3.253321379159389315` BNB. Original token quantities close exactly with zero residual. Net **+0.253300282319389315 BNB**, approximately **+8.44%** relative to original buy debit.

Historical cross-currency route checks rely on **actual original receipts**: HAJIMI/龙虾 ERC20 transfer from source pool to EOA on buy, return to pool on sell, paired real WBNB Transfer from pool to router, and paid actual receipt gas. Every selected native block delta matches (1) original signed `tx.value + gas` on buy, or (2) WBNB withdrawal amount minus gas on sell. No simulated prices, no current spot USD/BNB conversion and no profit from partial receipts. The source record `BSC_MEME_STAGE23_8E6B_REPEAT_WINNER_HAJIMI_LOBSTER_IFML_CROSS_MAJOR_ROUNDS_2026-10-13.json` proved historical inventory boundaries before this independent RPC replay. Raw sources are pinned in `bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json`; deterministic code `bsc_meme_address_model_v1_p4c_8e6b_two_positive.py`.

## Whole frozen 23×19 economic ledger

`bsc-meme-address-model-v1-p4c-23x19-crosswallet-native-verified-matrix-2026-10-15.json` and `bsc_meme_address_model_v1_p4c_crosswallet_verified23x19.py`: **23 wallets, 19 CAs, 437 exact cells**, 2 positive native closed owner rounds (8E6B/HAJIMI and 8E6B/龙虾), 1 negative native closed owner round (DDAC/龙虾), **434 `NOT_ECONOMICALLY_AUDITED` cells**. This is three **wallet×CA** observed closed selected-round cells, not exhaustive actual number of rounds across all 23 wallets; the unreviewed cells can contain other prior P2 signed episodes without qualification. Exactly **one** of the original 7 has two *selected source-qualified profitable major CAs*. **DO NOT rank the 23 wallets** by this unequal selection or claim 8E6B is the best one.

`bsc-meme-address-model-v1-p4c-sevenwallet-balanced-signers-native-outcome-2026-10-15.json` and replay `bsc_meme_address_model_v1_p4c_sevenwallet_batch.py` preserve the 5 source-selected round balance observations and two activity-only controls, with 14 actual signer checks and original complete/truncated receipt counts. `UNRESOLVED` is a first-class value. Original P3 recent 7-wallet roster and earlier P2 50 select-graded episodes remain frozen as distinct evidence, **not** silently promoted into global profit ranks.

## Actual QA, controls, review and next bounded mainline

The independent source-pinned 8E6B two-positive CI is [BSC P4C two positive workflow](https://github.com/lxxlx2/ChatGPT_mission_record/actions/workflows/bsc-meme-p4c-two-positive-tests.yml). The all-seven and cross-owner source replay CI is [BSC P4C seven wallet workflow](https://github.com/lxxlx2/ChatGPT_mission_record/actions/workflows/bsc-meme-p4c-sevenwallet-crosschecks.yml). Existing full BSC V1 research CI also performs stdlib unit discovery. One initial CI failure involved heterogeneous old source placement of `production` (`summary.live_production` vs top-level `production`); script was corrected on the original PR branch, **no frozen financial source was rewritten**. Final status to be verified on exact final HEAD after this report and plan are committed.

**Next actionable finite batch:**
1. **P4-C** Reuse the already frozen 5-round precommit. Resolve the 3 partially checked ADFF 龙虾, 2ADF 牛来, A83B 牛来 rounds through original exact tx receipts, per-CA token and *actual* quote asset transfers, owner Gas and previous independent inventory evidence. Use bounded exact selected tx evidence, preserve 8 large truncated receipt responses. Do **not** infer that Flap's quoted Q3B/S5B are BNB or that fee/tax is zero. If data is unavailable using free RPC, preserve `UNRESOLVED` and continue other original wallets rather than obsess over RPC edge cases.
2. Select the next *precommitted multiwallet batch* from P2's existing **50 graded signed episodes** targeting several 2026 majors, positive and negative; prioritize evidence with `SETTLED_NATIVE_DIRECT_WBNB_GAS`. Do not repeat the all-CA transfer census. The positive pair from 8E6B is one repeat-positive wallet, not a deployable scoring model.
3. **P4-B actual globally first executable observer-visible market U** remains lacking, despite true original owner buys/sells. Before P5 1/5/15-minute delayed follower simulation must test market availability after each delay, historical capacity and slippage/tax, capital, actual sellability, and selection biases with out-of-sample positive and negative episodes. Independent other-AI fixed-SHA review required later; separate user authorization for any Mac read-only environment acceptance; NO_GO for production, trade, alerts, PR merge, services.
