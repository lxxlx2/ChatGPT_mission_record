# BSC Meme 研究：禁止付费 GMGN API 依赖（2026-10-10 更正）

**Current approved route: ONCHAIN_RPC_ONLY, NO_GMGN_PAID_API, NO_USER_INSTALL_OR_KEY_REQUIRED.**

This README supersedes earlier commands in this folder. The previously committed scripts `bsc_meme_top_traders_readonly.py`, `bsc_top_trader_crosscheck.py`, and their tests are **deprecated / NOT_APPROVED_FOR_EXECUTION**. Those programs attempted GMGN API-based sampling. User explicitly rejected GMGN API because it requires funding and imposes request limits. Do not ask the user to download scripts, install GMGN CLI, buy a GMGN plan, provide API keys, or execute these programs. Do not treat those scripts as task completion.

The assistant has already connected and used an existing read-only Alchemy BSC blockchain application, so it can collect transfers, historical token/pair activity, transactions, transaction receipts and balance snapshots **itself in this conversation**, without user-side steps. No automated monitoring is authorized.

## Actual independent on-chain proof obtained during this correction

On 2026-10-10, direct `bnb-mainnet` Alchemy `getAssetTransfers` calls (5 pages of 10 transfers per pair) obtained:

| Token | Contract | BSC Pancake V2/WBNB pair | Transfer entries | Unique transaction hashes | Block range |
| --- | --- | --- | ---: | ---: | --- |
| 牛来 | `0xbeea1d618e533a387d941f58a7d4c9b7bd377777` | `0xbfc26980d8068ae744f5405d3abf6e7df02e11b3` | 50 | 25 | 116314923 to 116318053 |
| MARSCOIN | `0xfe189e97832da1573e4e4ff034f4ffc3a15c7777` | `0x9f286c9bd510150c62a08da72af797ac45311ae0` | 50 | 25 | 112668718 to 112679229 |

First rows included pool fee/self-token transfers. These entries are NOT all separate buys; the 25 distinct hashes are also NOT confirmed distinct beneficial traders. Underlying individual `ethGetTransactionByHash` calls were made for the first 10 distinct hashes of each token. Some result fields were truncated in the connector response and thus original signers were not reported as confirmed where missing. This research does not pretend the full history or per-token profit top-100 is already indexed.

Baseline: the previous 19-token universe, initial Pancake V2 scans, historical cross-wallet cluster and PnL examples remain in `BSC_MEME_TOP_TRADERS_AUDIT_2026-10-10.md`. Especially important: BUBB's pre-V2 trade included WBNB *rather than native BNB* sale proceeds, proving both pre-migration venues and receipt-level quote asset accounting are required.

## How to complete the task in this chat, with no paid third-party top-trader API

1. For each of 19 known tokens, and later add any official Binance Alpha-only BSC meme omissions, identify the actual original launchpad pool and subsequent Pancake V2/V3 WBNB or stablecoin routes. Do not assume V2-only captures first trades.
2. Query all token inflows/outflows and true original swap signers in paginated batches via connected Alchemy, using proper `pageKey` and block-scoped request limits. Persist research evidence and coverage/completeness notes to Git directly. For large volumes, divide into bounded sub-windows and deduplicate hashes and events.
3. Decode transaction receipts for token flows and **quote settlement assets** (BNB, WBNB, USDT, USDC, BUSD) and gas. Transfers or airdrops alone are not purchases; transfer-out alone is not realized sale. Pool/router intermediaries or shared recipient addresses are not single traders.
4. Build a candidate wallet table including **all sampled positions, including losses**. Only rank profits when quote cashflows and cost basis are reconstructed; distinguish unverified/closed/open positions.
5. Identify >=2-token profit repeaters, actual bilateral transfers/shared funding, source identity ambiguity and **true** recent signed Meme swaps. Then run 5/15/30-minute delayed entry followability check.
6. Only publish conclusions that have corroborated original transaction hashes, dates, cost proceeds and conditions. Write UNVERIFIED when necessary. Never manufacture a full top-100 ranking or imply it was retrieved from Alchemy directly.

We may read public Binance leaderboard or Dune data as non-authoritative lead generation when no paid plan is required, but every claimed wallet PnL is to be verified with the same original-chain audit.

**No further commands for the user; user explicitly wants the assistant to perform data collection and Git updates.**

Research: OBSERVE_ONLY. Production: NO_GO. Do not create monitoring, automations or live-trading jobs.

## Current research authority: V21 inventory + Stage 16 economic reconciliation (2026-10-12)

The BSC address-model research itself has advanced beyond the 2026-10-10 collection notes above. Preserve earlier evidence and chronological scope:

- Frozen 23 wallet × 19 exact CA matrix: `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json`. All 437/437 exact CA ERC20 positive-transfer cursors exhausted; 148/148 observed-transfer CA token raw quantities independently reconciled; 289 zero-positive-transfer CA cells. This is **not** a closed economic PnL ledger or viable follow-trader proof.
- Current economic research handoff: `BSC_MEME_ADDRESS_MODEL_5_STAGE16_CROSS_WALLET_MANAGER_FEE_CAUSAL_QA_2026-10-12.md`.
- Exact EOA-indexed manager events and WBNB real quote asset flow: `BSC_MEME_STAGE16_3_EOA_ROUTER_FEE_AND_SIGNED_ROUNDTRIP_QA_2026-10-12.json`. Across 8 original signed buy/sell txs in 3 wallets and 3 meme tokens the manager event equals **floor(1% of appropriate gross amount)**. Event ABI semantics have not been independently decoded, and do not extrapolate fee policy to other routes.
- Three initial raw-token fully paired original buy/sell cycle **BNB block scopes**, not fully internal-traced causal PnL: DDAC/MARSCOIN `+0.051496246460395600 BNB`, 2ADF/BOB `+0.009515610472872943 BNB`, and A83B/BROCCOLI714 `-0.239887492433116024 BNB`. An extra successful EOA transaction on each DDAC sell block is explicitly gas-accounted. Its following partial-token exit is **not** a completed loss.
- Correction: a legacy unscoped BOB manager log `0x11c37937e080000` means 0.08 BNB and must **not** be labeled the 2ADF original buy fee. Exact manager topic + wallet-indexed log + original tx hash returns **0.005 BNB** in the updated fee proof.

Next research stage: reconstruct true original-owner quote-denominated trade costs/proceeds for repeated major meme opportunities, include unsuccessful or missed eligible opportunities as denominator, distinguish open inventory and internal tracing limitations, and **only then** study delayed follower prices/liquidity. Do not rank wallet PnL merely from Transfer logs, account balance snapshots, or three convenient examples. No GMGN paid API. OBSERVE_ONLY / PRODUCTION_TRADING = NO_GO.

## Latest handoff: Stage 17 cross-wallet and negative outcome controls (2026-10-13)

Continue the ADDRESS MODEL research from `BSC_MEME_ADDRESS_MODEL_5_STAGE17_CROSS_WALLET_2_MEME_TIME_AND_ECONOMICS_2026-10-13.md`, not from the deprecated GMGN scripts or from more 23×19 token-balance rescans.

- V21 23 wallets × 19 frozen exact CAs: 437/437 positive ERC20 cursors complete; 148/148 observed raw token quantities independently conserved. **Token inventory phase is complete.**
- Stage 17 cohort raw onchain source: `BSC_MEME_STAGE17_DDAC_8E6B_IFML_LOBSTER_TWO_TOKEN_NEGATIVE_CONTROL_2026-10-13.json`. In 9 selected, fully token-inventory-closed native-BNB-block trading episodes across DDAC/IFML (5), DDAC/Lobster (2), 8E6B/IFML (2), 4 scopes are positive and **5 are negative**. This 4/9 is a selected audit-sample observation, **not** candidate win rate or all eligible major opportunities.
- DDAC on IFML: first four native-block scopes positive, fifth `-0.446324586902254802 BNB`; 8E6B two separate fully inventory-closed IFML cycles `-0.231346571585353217` and `-0.367677245259552299 BNB`, 6/6 original EOA signatures and 6/6 receipt success statuses checked. DDAC late IFML loss exited 2026-01-08 07:32:10 UTC, 8E6B bought 11 seconds later: **timing ≠ proof of following**.
- DDAC/Lobster both closed cycles negative (combined `-0.183543131928304728 BNB`); V2 negative sell cashflow and fee validated in `BSC_MEME_STAGE17_DDAC_LOBSTER_V2_SELL_ADDITIONAL_APPROVAL_GAS_2026-10-13.json`. Previous gas label of **208457** is **the sum** of the actual extra approve gas **46327** and inferred swap gas **162130**, NOT one sale GasUsed.
- 8E6B/Lobster has an opposite `+4.794001707717376678 BNB` *native block scope*, but original receipt status is confirmed only 11/13, and no equivalent closed-cycles realized-PnL partition yet. Do not rank it as a verified winner.
- 8E6B IFML first manager sell receipt truncated: targeted WBNB Withdrawal + indexed 1% fee-like manager event + separate same-block EOA approve receipt allow exact conditional sale-gas reconciliation. Its later IFML episode used both manager and direct router venues. Do not mix route fee structures.
- Next priorities: economic lifecycle/classification of more *major token opportunities* and all qualified non-entries/losses in the denominator, then real-time-to-signal availability and delay-capacity historical simulation only after complete independent QA and another AI review.

All economic results remain native-wallet block-scope with BSC internal trace limitations unless explicitly transaction-causal verified. NO_GMGN_PAID_API / OBSERVE_ONLY / PRODUCTION NO_GO.

## Latest handoff: Stage 18, 8E6B Lobster two closed native-positive episodes (2026-10-13)

Stage 18 supersedes only Stage 17's unresolved **8E6B/Lobster** section, not its other findings. See `BSC_MEME_ADDRESS_MODEL_6_STAGE18_8E6B_LOBSTER_TWO_CLOSED_EPISODES_AND_DENOMINATOR_2026-10-13.md` and machine evidence `BSC_MEME_STAGE18_8E6B_LOBSTER_13_SIGNED_TWO_CLOSED_ROUNDS_2026-10-13.json`.

- Independent Alchemy `ethGetTransactionReceipt` success headers now cover 13/13 owner-signed Lobster original trades; the formerly unknown two are successful `0x1`. Their **complete receipt bodies remain truncated**. Internal trace remains unavailable on free RPC.
- Full 4 in / 9 out raw token integer chronology partitions into **two zero-to-zero inventory rounds**: 11 trades (3 buys/8 sells), **+4.540701425397987363 BNB**; then 2 trades (1 buy/1 sell), **+0.253300282319389315 BNB**; sum equals prior +4.794001707717376678 native-wallet block scope. Both are selected *conditional native-scope positives*, not fully traced realized trading PnL.
- Cross-wallet two-token selected closed episodes become **11 (6 positive/5 negative native-block scopes)**. Do not convert selected 6/11 into win rate.
- Next work MUST address qualified opportunity denominators, wallet funds/age at tradeable time, non-entry vs ineligible vs unknown, and causal quote settlement of more significant projects before follower execution backtests. 23×19 token-transfer 437/437 completeness is done; do not repeat rescanning as modelling work. Research-only, NO_GO.

## Latest handoff: Stage 19, historical capital prerequisites and all-19 transfer-only opportunity denominator (2026-10-13)

Read `BSC_MEME_ADDRESS_MODEL_6_STAGE19_MAJOR_OPPORTUNITY_DENOMINATOR_AND_HISTORICAL_CAPITAL_2026-10-13.md` and machine evidence `BSC_MEME_STAGE19_SIX_EOA_FIVE_MAJOR_PRE_TRANSFER_NATIVE_ELIGIBILITY_MATRIX_2026-10-13.json` before further ADDRESS MODEL work.

- Six already frozen priority EOA wallets × all 19 exact CA from V21: **114 cells, 74 with positive ERC20 Transfers, 40 without**. These are historical token presence statuses, not original signed buys, successful trades or eligible missed opportunities.
- Direct Alchemy `bnb-mainnet` historical RPC at one block before *sampled global ERC20 transfer reference*: 6 wallets × 5 material CA = 30 BNB balances + 30 wallet nonces; then second checks at one block before sampled Pancake V2 pool reference for three non-transfer cells, 6 more reads. **66 directly queried historical values** (not 66 independent transactions). No paid GMGN API.
- Of the selected 5-token 30 cells, 3 had no ERC20 Transfer: DDAC/4 and 877AF/我踏马来了 both 0 BNB / 0 nonce at BOTH sampled reference points; ADFF/4 has nonce 101 but only 881635 wei native BNB at both. **Do not label any qualified missed opportunity from these results.** Alternative quote assets and true first tradable venue still unresolved.
- The `GLOBAL_GENESIS` sample is not canonical first executable swap; Pancake V2 sample can postdate bonding-curve execution. Next research must prove true market start + owner-signed buying + quote liquidity/funding before counting qualified misses. Existing 11 selected closed native-positive/negative episodes remain conditional, not verified causal trading PnL or win rate.
- Proceed to higher-quality economic audit and qualifying denominators; no 23×19 rescan, no live followers, no deployment. **NO_GO**.

## Latest handoff: Stage 20, all 40 no-transfer candidate wallets' historical capital and three early market execution proofs (2026-10-13)

See `BSC_MEME_ADDRESS_MODEL_6_STAGE20_40_MISSED_CHANCE_COHORT_AND_EXECUTABLE_TRADE_CHECK_2026-10-13.md` for the report and `BSC_MEME_STAGE20_40_ABSENCE_CHAIN_CAPITAL_AND_EXECUTION_EVIDENCE_2026-10-13.json` for machine evidence.

- Read-only direct RPC: **all 40/40 frozen six-wallet×19-CA cells with NO positive ERC20 Transfer** at each token's prior sampled-global-transfer-block - 1: **35 have native BNB 0 + EOA nonce 0**, **2 have native dust (<0.001 BNB) + nonzero nonce**, **3 have nonzero nonce and material native BNB**. All 40 statuses were queried, not inferred from no-transfer alone. **86 BNB balance/nonce RPC reads** including three later V2 pool anchor checks.
- **8E6B / BROCCOLI714** had 8.7515 BNB and nonce 139 at earliest sampled token event -1; another signer successfully paid **1.01 BNB** to Four.meme manager and received the token in that original event. **8E6B / BUBB** had 3.7235 BNB/nonce 887; another signer successfully paid **0.3131 BNB** and received BUBB. These are qualified *further research candidates*, NOT verified profitable missed entries.
- **2ADF / BULLA** had 9.2389 BNB/nonce 4028 before the first sampled token Transfer, but that original tx was contract deployment, not a swap. On sampled V2 swap, 0.0008 WBNB -> ~2.8489 BULLA was observed with pre-swap WBNB reserves only ~0.7862 WBNB; cannot assume full-size trading at same price. 2ADF had 5.9457 BNB/nonce 4801 at pre-sampled V2 swap block.
- Do not rank 35 early no-nonce wallets as missing qualified opportunities. Historical ERC20 presence is not owner-signed entries or repeat profit. Next focus: historical observable first-trade windows, onchain executable route/size and quote-cashflow, realized gains versus losses, then copy-lag backtest. Refrain from re-running completed 437× exact-CA ERC20 pagination or paid GMGN API. Research-only; **PRODUCTION_TRADING=NO_GO**.

## Latest handoff: Stage 21, three early V2 pools exact fee and reserve-scaled static quotes; BULLA LP Burn verified (2026-10-13)

Read `BSC_MEME_ADDRESS_MODEL_6_STAGE21_THREE_OPPORTUNITY_HISTORICAL_V2_QUOTE_AND_BULLA_LP_BURN_2026-10-13.md` and machine proof `BSC_MEME_STAGE21_THREE_MISSED_CANDIDATES_V2_HISTORICAL_QUOTE_CAPACITY_2026-10-13.json`.

- **3/3** early sampled V2 pools (8E6B/BROCCOLI714, 8E6B/BUBB, 2ADF/BULLA) directly prove 25-bps pool fee because 9975/10000 AMM formula exactly matches original 3 onchain Swap outputs in integer token units; distinct from Four.meme curve fees.
- Freeze post-sampled-pool block+1 as entry state, and exits at +100,+300,+600,+1200 blocks (timestamp-check each). **18** archive pool snapshots, 3 theoretical buys at 0.01/0.1/1 WBNB per pool and **36** hypothetical sell-back quotes. These are **STATIC HISTORICAL POOL QUOTES NOT REAL EXECUTED OR CAUSAL PnL**, exclude taxes, gas, MEV, off-pool liquidity and changed historical market after a hypothetical buy.
- BROCCOLI714 early V2 WBNB reserve only 0.151970701851567928: 0.1 WBNB buy is **65.80%** and 1 WBNB **658.02%** of that reserve. At approx 60 min, hypothetical pool exit / input: 0.01 WBNB scenario 5.48x, 0.1 scenario 3.52x, 1 scenario only 0.77x; not proof of practical profitable follow.
- BUBB selected V2 early 0.01/0.1/1 WBNB hypothetical exit quotes all below 1x across the measured ~5/15/30/60 min checkpoints; this is a negative control, not token-wide ex-post price performance.
- Crucial correction: BULLA V2 pool `0x3551191f78869c29388886330f31739a87866c38` dramatically depleted due to **confirmed liquidity removal**, not a token dumping price inference. Original SUCCESS `0xe95b4a39f3ac23adb0558397756c32a0fe25d2a728453647e9b21e9705db85c4`, block **50982590**, original Pancake pair `Burn` amounts EXACTLY equal preceding/following reserves removed: **99.99120756% BULLA and WBNB**. Pool-specific post-Burn quote CANNOT represent global token exit price.
- No verified qualified missed profit opportunity denominator yet; after this liquidity/amount gate, prioritize curve-time price and wallet entry eligibility plus full owner-signed settlement for repeated profits/losses. No deployment, paid GMGN or trading: **NO_GO**.

## Latest handoff: Stage 22, independent early BROCCOLI realized exits vs same EOA TST negative control (2026-10-13)

Primary report: `BSC_MEME_ADDRESS_MODEL_6_STAGE22_EARLY_BUYER_REALIZED_BROCCOLI_PROFIT_TST_LOSS_2026-10-13.md`; machine source: `BSC_MEME_STAGE22_BROCCOLI_12_OWNER_SELLS_TST_NEGATIVE_COHORT_2026-10-13.json`.

- A **new discovery candidate EOA outside the frozen 23 ×19 cohort**, `0x392eb7553df2400e0a3fc8ac65f35ae3114a3924`, paid 1.01 BNB for early BROCCOLI714 on 2025-02-13 16:12:19 UTC. One exact-CA ERC20 inflow / **18** paginated fully exhausted outward transactions; raw integer token inventory zero. All 18 original EOA signed; **12 actual owner-signed successful manager sells, 6 successful plain ERC20 transfers NOT counted as sales**.
- **12/12 sell receipts fully settled**: Sum original WBNB withdrawals **9,739.659476212188132497 BNB**, manager floor(1%) fees **97.396594762121881319 BNB**, actual sale gas **16.684085224 BNB**; 12 archive `N-1 -> N` wallet BNB gains **+9,625.578796226066251178 BNB**, exact integer equality PER SELL (not approximated). Subtract isolated initial buy native balance cost **1.340903968999999997 BNB**, plus six plain ERC20 transfer gas **0.068265744 BNB** -> original EOA onchain transaction-attributable native cashflow **+9,624.169626513066251181 BNB**. This is strong realized original-account quote cashflow, **NOT fully audited beneficial owner profit**, six downstream token transfers not pursued and external native funding/withdrawal unrelated to 19 transactions excluded. VERY high execution gas; NOT a copyable public signal.
- **Negative control in the SAME address:** TST 2025-02-06 12:25:36 buy 2 BNB, 12:26:57 sell; one exact-CA token in/out equals, receipts and fee/gas match native blocks, net **-0.104324485826119481 BNB**. Other exact-CA SIREN inbound is another EOA's direct transfer, NOT original owner-signed trade. Screening remaining 18 of the 19 frozen CAs via both directions found no other active major trades. **ONLY ONE verified major positive**, not a repeat-profits address.
- BUBB early separate buyer `0x5ab695629cc77d79b317242fb4f19fdf579f865b`: first outgoing token `0xa2917a1c...` was actual token `transfer` selector `0xa9059cbb` and wallet BNB fell just gas; NOT an executed sale or realized negative PnL.
- Preserve Stage21 static pool quote vs Stage22 direct realized accounting distinction and Stage20 absence denominator. Continue Stage22+ with OTHER profitable major token closed rounds in FROZEN cohort or evidence-first new discovery candidates; compare negative episodes, historical execution viability and copy latency. No launch, monitoring, paid GMGN or trading. **NO_GO**.

## Latest handoff: Stage 23, frozen 8E6B dual major meme repeat positive native settlements (2026-10-13)

Read `BSC_MEME_ADDRESS_MODEL_6_STAGE23_FROZEN_8E6B_TWO_MAJOR_PROFIT_CANDIDATE_2026-10-13.md` and machine evidence `BSC_MEME_STAGE23_8E6B_REPEAT_WINNER_HAJIMI_LOBSTER_IFML_CROSS_MAJOR_ROUNDS_2026-10-13.json`.

- Major modelling milestone **IN ORIGINAL FROZEN 23 EOA**, not external selected winner: **8E6B** (`0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0`) has 13/19 CAs with token-transfer presence, but only THREE CAs have selected completed signed/economic trade cohorts audited: HAJIMI, 龙虾, 我踏马来了.
- HAJIMI raw exact ERC20 token 6 buys /7 sells reconstructs **FOUR zero-inventory rounds**, 3 positive /1 negative native-wallet block cashflows: +0.268592992917629933, **-0.141716957486616687**, +0.935157578391160618, +0.180865666976311244 BNB; total **+1.242899280798485108 BNB**. 13/13 owner success headers direct recheck (10 complete receipts, 3 truncated but success headers), independently replayed **13/13 native N-1/N balance deltas**. HAJIMI round 1 (2026-01-10 15:19–15:22 UTC) full 3 trades: 5 BNB buy, two signed sells: WBNB withdrawal minus Gas EXACTLY matches wallet native delta; closed round **+0.268592992917629933 BNB**. HAJIMI round 3 two sell receipts also WBNB/gas reconcile. HAJIMI round4 last receipt incomplete, no fake gas values.
- 龙虾 Stage18 complete two zero-inventory rounds, both positive +4.540701425397987363, +0.253300282319389315 BNB, total **+4.794001707717376678 BNB**; INDEPENDENTLY directly checked latter round (2026-04-20 to 2026-04-23): original 3 BNB owner buy, one full exit with WBNB withdrawal - Gas = wallet BNB gain, net **+0.253300282319389315 BNB**.
- Critical negative control: same EOA IFML/我踏马来了 TWO completed LOSS rounds -0.231346571585353217 and -0.367677245259552299 BNB, total **-0.599023816844905516 BNB**.
- Across those 3 **selected audited** major CAs: **8 inventory-zero rounds, 5 positive, 3 negative**, native-account event-block net **+5.437877171670956270 BNB**. This is NOT an all-19-token owner PnL, a 5/8 statistically-valid win rate, qualified missed-profit denominator or validated follower strategy. Other token CA settlements remain unresolved.
- New research label: `REPEAT_POSITIVE_ACROSS_2_MAJOR_CA_RESEARCH_CANDIDATE`, **NOT** `FOLLOWABLE_ALPHA_APPROVED`. Next prioritize verifying execution signal observability, historical native/WBNB path, liquidity/slippage and delay in more independent major opportunities (especially 2026) plus cross-wallet address/funding links. No 23×19 rescan, no paid GMGN, no deployment/notification/trading. **NO_GO**.

## Latest handoff: Stage 24, frozen 8E6B third major Meme positive trade with token-4 (2026-10-13)

Read `BSC_MEME_ADDRESS_MODEL_6_STAGE24_THIRD_MAJOR_WINNER_TOKEN4_ECONOMIC_2026-10-13.md` and machine evidence `BSC_MEME_STAGE24_8E6B_TOKEN4_TWO_ROUNDS_THREE_MAJOR_POSITIVE_COHORT_2026-10-13.json`.

- **Same FROZEN EOA 8E6B**, not an extra post-selected high-profit wallet. Token `4` exact CA `0x0a43fc31a73013089df59194872ecae4cae14444` original full ERC20 history **2 in /17 out**, raw token zero balance partitions **TWO separately closed rounds**: R1 **-0.117977426190152496 BNB** (2025-10-01 04:08:45–04:09:34 UTC), R2 **+13.282964879793219111 BNB** (2025-10-01 04:21:19 to 2025-10-13 08:13:21 UTC), total **+13.164987453603066615 BNB**. First loss must never be dropped. Second round began with **0.3 BNB** native input and 16 partial sells across ~12 days.
- 19/19 original owner-signed-success receipt and WBNB/gas/native-account reconciliation records independently integer checked from saved frozen source. Exact: **14.004497756745364634 WBNB gross withdrawals - 0.8 native buy inputs - 0.030466745273120164 Gas - 0.009043557869177855 quote route differences = +13.164987453603066615 native BNB scoped balance changes**. This session directly re-fetched FIVE selected original signed tx/receipts/native wallet N-1 to N balances and block timestamps; all 5 agree with archived data. No claim all 19 RPC were newly repeated.
- With Stage23's HAJIMI (+1.242899...), 龙虾 (+4.794001...), 我踏马来了 (-0.599023...), FOUR preselected audited CAs now **10 zero-token-inventory closed rounds: 6 native-positive /4 native-negative**, selected owner-block native net **+18.602864625274022885 BNB**. Actual **3 different major CAs** with positive closed rounds. Label `REPEAT_POSITIVE_ACROSS_3_MAJOR_CA_RESEARCH_CANDIDATE` only, not an all-19-CA win rate, proven full lifetime realized PnL or verified follower alpha.
- GIGGLE held apart as **MIXED_BNB_USDT_SETTLEMENT_REQUIRES_UNIT_NORMALIZATION**: existing stored native BNB event-block +5.715925819273344974 BNB and USDT net +4061.629806775951927704 USDT (18 decimals). DO NOT add or treat GIGGLE as fourth settled comparable gain without event-specific quote reconciliation and entry/exit eligibility proof.
- Mainline next: finish GIGGLE mixed-quote economics, remaining active major opportunities, independently verify signer/sources + execution lag/market depth. No 437 combination re-scan, no paid GMGN, no live trading/production/notifications; **NO_GO**. Other AI review still pending.

## Latest handoff: Stage 25, 8E6B GIGGLE two actual mixed-quote zero-inventory rounds; fourth major positive CA (2026-10-13)

Main report: `BSC_MEME_ADDRESS_MODEL_6_STAGE25_GIGGLE_MIXED_QUOTE_TWO_REAL_ROUNDS_2026-10-13.md`. Machine evidence: `BSC_MEME_STAGE25_8E6B_GIGGLE_TWO_CLOSED_MIXED_QUOTE_ROUNDS_2026-10-13.json`.

- Same FROZEN 23 EOA `8E6B` exact GIGGLE CA `0x20d6015660b3fe52e6690a889b5c51f69902ce0e`: **4 ERC20 inbound +23 outbound transfer log records** = original 16 owner-signed successful transactions. Token raw integers reconstruct **TWO zero-inventory completed rounds** (R1 10 distinct owner tx, R2 6), not 23 distinct sales.
- **R1 2025-09-22 to Sep24 UTC** owner-account original asset delta **+0.454250515006464697 native BNB AND +5,061.629806775951927704 actual USDT**. BOTH nominal dimensions strictly positive, no USD spot assumption needed to establish positive return direction.
- **R2 2025-09-26 to Oct03 UTC** owner-account native **+5.261675304266880277 BNB**, USDT **-1,000** actual paid. Its nominal break-even quote is ~**190.05 USDT/BNB**. Independently queried exact onchain Pancake V2 Factory `getPair(WBNB,USDT)` and pool `token0/token1`, verified address `0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae`, and **16/16 original tx's N-1 block reserves**; contemporaneous R2 observed spot quotes ~**938–1099 USDT/BNB**, above break-even.
- **7/7** independently rechecked USDT exact-CA indexed Transfer logs matched archived same transaction hashes, 6 inbound +1 outbound; **5/5** independently rechecked native BNB historical N-1/N account deltas. Mark an inherited ~0.0006 BNB same-block attribution exception; not material to sign, but NOT complete call-level audit.
- Pre-block event-time WBNB/USDT onchain spot USDT-equivalent references approximate **R1 +5,505.87**, **R2 +4,750.23**, combined **+10,256.10 USDT**. **THESE ARE HYPOTHETICAL REFERENCE MARKS, NOT ADDITIONAL REALIZED USDT**; all real BNB and USDT settlement values remain separate, no CEX or present-day conversion. Extra fees/slippage and held-BNB price risk may matter.
- With Stage24's FOUR selected audited major CAs, Stage25 adds GIGGLE as fifth studied CA, **FOUR distinct major CAs with positive completed trades** (4, HAJIMI, 龙虾, GIGGLE); **12 selected closed rounds: 8 positive economically on native or independently verified historical mixed-quote marks, 4 negative**. This is NOT 8/12 general wallet win rate, complete all-19 CA PnL, or proof of followable signal. Model label `REPEAT_POSITIVE_ACROSS_4_MAJOR_CA_OWNER_SETTLEMENT_RESEARCH_CANDIDATE`, **not** `FOLLOWABLE_ALPHA_APPROVED`.
- Mainline: other major CAs' true quotes/negative entries + onchain signal observability/lag, external AI review only at model gate; no repeating 437/437 transfers, no paid GMGN, no production/monitor/transaction changes. **NO_GO**.

## Latest handoff: Stage 26, original frozen 8E6B MUBARAK 5 signed zero-inventory rounds with losses (2026-10-13)

Read `BSC_MEME_ADDRESS_MODEL_6_STAGE26_MUBARAK_FIVE_ROUNDS_REAL_POSITIVE_AND_THREE_LOSSES_2026-10-13.md` and evidence `BSC_MEME_STAGE26_8E6B_MUBARAK_FIVE_CLOSED_ROUNDS_NEGATIVE_CONTROLS_2026-10-13.json`.

- No re-download of finished 437/437 ERC20 pairs. Replayed original exact CA `MUBARAK` 5 in /11 out, **16/16 owner signed and successful receipt txs**, precise raw inventory into **5 independently CLOSED 0→0 rounds**: R1 **+5.487703712629279872 BNB**, R2 **+0.006715982175564136 BNB**, then R3 **-0.169122457028181235**, R4 **-0.010906490558303517**, R5 **-0.015287417746697438** BNB. Sum original wallet N-1/N BNB **+5.299103329471661818 BNB** (NOT fully attributed causal realized total). First big winner and 3 later losses preserved.
- Prior original sources documented native owner input **3.333 BNB**, receipt gas **0.02151212 BNB**, **10 of 11 sales with receipt WBNB withdrawal totaling 7.557105239505843199 WBNB**, and no OTHER direct external wallet native tx in any of 16 event blocks. Current stage independently re-fetched **five** representative original signed tx/receipts and N-1/N native historical wallet balance deltas (all match), and **10** true first/last block UTC headers for the five rounds.
- CRITICAL hard caveat: 1st sell `0xe570d7b8...` block `47425526` native wallet BNB **+1.157564561073470034** with **NO direct WBNB Withdrawal log**; unsupported internal BNB trace keeps **full causal realized PnL UNVERIFIED**. Also 0.00396 BNB buy-side unexplained residual. Do NOT silently label the entire +5.299 BNB strictly proven trade PnL.
- Combining 8E6B selected 6 major CAs (4, HAJIMI, 龙虾, 我踏马来了, GIGGLE, MUBARAK): **17 selected closed 0→0 rounds, 10 positive native or evaluated mixed BNB/USDT settlement, 7 negative**, **five different major CA with positive episodes**. Combined owner-wallet related native BNB scopes **+29.617893774019029677 BNB**, PLUS GIGGLE actual USDT ledger **+4,061.629806775951927704 USDT**; cannot sum units or claim fully causal all-token net, 10/17 model win rate, or copyable Alpha.
- Mainline next: continue with actual incomplete/negative economic controls and **followability/time-lag/entry market availability**, without getting stuck on paid native internal traces. No paid GMGN, production, trade or monitoring, external AI review still pending, **NO_GO**.

## V1 baseline and user-objective freeze (2026-10-13; DRAFT PR, no deployment)

**New work is on research branch `research/bsc-address-model-v1-20261013` until the independent review and tests are accepted.** Original objective is frozen in `bsc-meme-address-model-v1-requirements-2026-10-13.md` and phases in `bsc-meme-address-model-v1-implementation-plan-2026-10-13.md`. First model source `bsc_meme_address_model_v1.py`, regression `test_bsc_meme_address_model_v1.py`, all-23-wallet evidence matrix `bsc-meme-address-model-v1-baseline-2026-10-13.json`, and comparison/exception report `bsc-meme-address-model-v1-p1-baseline-review-2026-10-13.md`. This stage is **not** an audited wallet profitability ranking; P1 has not ingested P2 cashflows.

- Strict 437/437; transfer-present 148 and absent 289. Important source exception: **8 8E6B observed-token cells have `complete_in_events/out_events=null` in frozen V21 overlay**, despite separate full transfer history. They are preserved as `PRESENT_WITH_NULL_COMPLETE_COUNTS_IN_V21_OVERLAY`, NEVER zero-filled or backfilled from stale `original_in/out` counts. P2 will map authoritative post-V21 event details without altering original source.
- 2026 major token research-priority order is based on `我踏马来了`, `龙虾`, `牛来`, `MARSCOIN` **ERC20 transfer presence** and 19-CA breadth only; **NOT confirmed buys or realized profit**. Includes all 23 EOAs. P1 does not rank PnL, latest real swaps or omitted qualified opportunities.
- **Next**: compare all 23 original EOAs uniformly with source evidence economic tiers and 2026 recent signed Meme swaps, then require actual observable 1/5/15-minute follower replay and independent AI review. GMGN paid API, runtime, alarms, deployment, automatic trading all out of scope. **NO_GO**.
