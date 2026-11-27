# BSC address model | P4-C Stage: DDAC 龙虾 original signed buy–sale closed native-negative round

**Date:** 2026-10-15 Asia/Bangkok. **Environment:** live BNB mainnet historical READ-ONLY Alchemy; same Mission PR #40; no paid data source, execution, app deploy, alert, trade, merge, or Frank/Monster modification.

**Status:** One independently source-pinned **P4-C economic round PASS, native negative**; entire 23-wallet profitable-repeats model **NOT BUILT**; **P4-B global executable U still UNKNOWN; P5 NO_GO; production NO_GO**.

## Result — causal sign, actual settlement, exact units

| Original immutable facts | Value |
| --- | --- |
| Exact major CA | 龙虾 `0xeccbb861c0dda7efd964010085488b69317e4444` |
| Original candidate owner / signer | DDAC `0xddac928a240bdace3994c2cc0783d4e29a002127` (one of original 23) |
| Actual first purchase | Original Four.meme TokenPurchase plus received original ERC20 token, tx `0x35793699fbf006cfb07d5775991f50c106af64ea840db10a2f580b4661a0df12`, block `83635776` |
| Actual sale | Original successful Four.meme TokenSale, tx `0xd63edbb070a8171af5aa37cfb2953ae868a77ff6607b5a1a4f5378abb2249219`, block `83635800` |
| Bought token raw | 99,069,253,510,299,993,000,000,000 |
| Sold token raw | 99,069,253,510,299,993,000,000,000 |
| Residual original token inventory after exact close | **0 raw units** |
| Historical window | 24 BNB Chain blocks after original purchase |
| Native BNB owner balance before buy | 17.806507402194926070 BNB |
| Native BNB owner balance after buy | 16.997499825194926074 BNB |
| Native BNB owner balance before exit | 16.997499825194926074 BNB |
| Native BNB owner balance after exit | 17.714337786680311798 BNB |
| Wallet BNB debit in original purchase block | **0.809007576999999996 BNB** |
| Native BNB credit in original exit block, gas already deducted | **0.716837961485385724 BNB** |
| Net BNB wallet change across exact original early-round window | **-0.092169615514614272 BNB** |
| Return as percentage of original native wallet debit | **-11.3929%** (truncated return -1139 basis points) |
| Sign | **REALIZED_NEGATIVE_BNB_WINDOW** |

**Proof chain and non-circular reconciliation:** The original signer DDAC and original CA match on purchase event, original transfer to DDAC, later owner's exact ERC20 return to Four TokenManager2, and **successful** full receipt `TokenSale(address,address,uint256,uint256,uint256,uint256,uint256,uint256)` (topic0 `0x0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19`). Earlier whole-block Topic log read was truncated, but this **specific successful sale tx's full 7-log receipt** was accessible and is archived as original JSON. Never infer a sale from token transfer alone.

There were exactly **one externally indexed DDAC signed transaction in the buy block** and **two DDAC signed transactions in the sale block** (a successful approval, followed by the successful sale); independent original `eth_getTransactionByHash` agreed. These sale-block full receipts contain the two paid gas amounts `0.000030978840000000 BNB` total. Original transaction receipts prove success and exact gas. There were zero other incoming `external` wallet BNB transfers found on those two blocks; provider BNB internal transfers are unsupported, so we **never claim complete internal call tracing**. Nonetheless independent actual wallet balances at buy-before, buy-after, sale-before and sale-after give direct historical native economics.

The Four TokenSale raw event reported `cost=0.731498918699373186 BNB`, `fee=0.007314989186993731 BNB`. The observed exit wallet native credit **plus both paid gas costs** is `0.716868940325385724 BNB`, exactly equal to the event `cost - 2×reported fee`. This is a **source-checked numerical equality**, not a claim about whether one of these fee multiples is the protocol vs intermediary fee without independent router ABI/trace; keep those fee semantic labels unresolved. The original *buy* receipt JSON was too large to reproduce, so its gas is not split from the original *buy-block native wallet debit*, and the primary exact native net uses owner balance snapshots rather than invented component fees.

**Scope guard:** This is one **original signed round's exact BNB native wallet outcome**, including paid network gas and observed same-block account state, not a general DDAC profitable-winner score, not a USD or time-indexed investment return, not a public observer executable buy/sell lag claim, not the owner's total PnL (later token activity exists), and not proof that buying at launch is followable.

## Git source, code, and test deliverable

- Raw original selected EOA outflows (asc/desc complete exactly 2) `bsc-meme-address-model-v1-p4c-major3-owner-transfer-exit-raw-2026-10-15.json`
- Exact 4 historical owner native balances and external block activity `bsc-meme-address-model-v1-p4c-dragon-native-block-balance-raw-2026-10-15.json`
- Three owner-signed original transaction header readbacks + external inbound negative samples `bsc-meme-address-model-v1-p4c-dragon-three-tx-header-and-inbound-raw-2026-10-15.json`
- **Both complete successful exit-block original receipts** and Four `TokenSale`: `bsc-meme-address-model-v1-p4c-dragon-approval-and-sale-full-receipts-2026-10-15.json`
- Source-pinned normalized machine result `bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json`; reproducible `bsc_meme_address_model_v1_p4c_ddac_dragon_closed.py`, immutable source blob pins, adversarial tests
- All frozen **23 × 19 = 437** evidence cells updated through a **new append-only** overlay `bsc-meme-address-model-v1-p4c-23x19-native-economic-evidence-grid-2026-10-15.json` / `bsc_meme_address_model_v1_p4c_closed_grid23x19.py`. Exactly **1** `REALIZED_NEGATIVE_BNB_CLOSED_OWNER_ROUND` (DDAC/龙虾); **436** `NOT_ECONOMICALLY_AUDITED`. Earlier P2 sampled positives/negatives and P3 7 recent major-swap-active wallets are **preserved as their own evidence classes**, never converted to full actual owner profits or missed trades.

**CI fixed SHA accepted on commit `ce5455b375947c0af10183d87258340899a89452`:** [GitHub Actions #38609581389](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38609581389) PASS, **264** main tests + **9** supplementary tests, including source-pinned exact replay and mutations in TokenSale topic, owner, token inventory, exact gas, extra EOA tx, native owner balances, cohort and fabricated profitable classifications.

## Bounded data-source limitations, no paid workaround

- Alchemy first 20 transfers for some wallets truncated at 8KB. For 牛来/MARSCOIN a **precommitted 2-per-page** first/last outbound historical read was collected with `pageKey` preserved; no completeness claim. Actual signer outbound transactions and Flap original sale events did not close a same-tx original-quote-token cash flow, so Flap economic PnL **UNKNOWN**. An event *math quote* was returned after each original buy but is never proof of actual sell execution.
- Alchemy BNB mainnet internal transfer category unsupported. `trace_transaction` and `debug_traceTransaction` were explicitly **free-tier prohibited**; no fee upgrade, no hidden trace assumptions. Blockscout MCP reported **chain ID 56 unsupported**, and the public BscScan transaction detail was not available through browser fetch. All such failures are preserved as source-status evidence, not negative transaction results.
- Main DDAC manager `TokenSale` whole-block filter was truncated. **The complete exact original 7-log transaction receipt** solved this actual sell and gas identity, so **do not repeatedly retry the truncated whole-block filter**.

## Next mainline: owner-economic closure in breadth, then P5

1. Choose a **precommitted balanced batch of existing P3's seven recent 2026-major active original wallet signers** across multiple CAs, with early winners, losers, and no-sell/unknown controls. Batch analyze signed original **buy → sell**, exact BNB/quote-asset balances, Gas, transfer taxes, and incomplete exits; retain untouched cohort denominators and source query pagination. **No DDAC-only optimization.**
2. Verify Flap major2 original buyers' owner actual native or quote-token returns through a supported *free* complete receipt or validated wallet economic window if directly material; early first/last pages are only candidates. Do not use unrelated currency raw quote amounts as BNB or USD PnL.
3. Only if a sufficient sample of repeat winner wallets has net-positive and net-negative causal rounds, stable observer-visible market-U, funds-at-U, liquidity and buy/sell exit, freeze 1/5/15 minute delay P5 replay with no-hindsight periods. Do not skip other-AI independent fixed-SHA review, tests, source readback, separate explicit Mac read-only authorization. **Still NO_GO, no PR merge or production deployment.**
