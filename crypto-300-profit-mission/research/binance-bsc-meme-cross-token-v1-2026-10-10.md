# Binance BSC Meme Cross-Token Wallet Research V1

Date: 2026-10-10 (Asia/Bangkok)
Status: RESEARCH_ONLY / OBSERVE_ONLY / CROSS-TOKEN-PNL-NOT-VERIFIED
Execution authority: none. Do not enable trading, alerts, watch tasks, Mission Control integration, or change production configuration.
Mission authority: MISSION_SPEC.md; PROJECT_ANALYSIS_FRAMEWORK.md; token_trading_principles.md; meme_trading_principles.md.

## Objective and falsifiable rule

Research whether wallets profit **repeatedly** from BSC-native narrative / memecoin tokens that later enter Binance Alpha, Binance USD-M perpetuals, and/or Spot, across 2025–2026. All earliest tradable periods, pool deployments, spot/perp listing times, buy/sell cashflows and later exits must be considered. These are researcher-selected candidates, **not an exhaustive census** of Binance Alpha BSC tokens and **not evidence that Binance manipulated prices**.

Authority: direct BSC RPC over Alchemy bnb-mainnet for token identity, DEX pool identity, transactions, ERC-20 transfer history, contract-code checks and block timestamps. English-language Binance original announcements for listing. Community analytics are leads, not verified realized PnL.

Never conflate an exchange market name (BANANAS31) with ERC20 symbol ($BANANA), two BROCCOLI contracts, or Build On BNB BOB with the unrelated later Build on Bitcoin BOB. Never infer true trader identity from a router/aggregator contract's Transfer recipient, nor treat token transfer out, airdrop, CEX deposit or movement between wallets as a realized sale.

## Canonical candidate token contracts (18; all ERC20 metadata read from bnb-mainnet)

| Research label | ERC-20 token name / symbol where noteworthy | BSC CA | Onboarding fact / maturity |
|---|---|---|---|
| TST | Test / TST | 0x86Bb94DdD16Efc8bc58e6b056e8df71d9e666429 | Binance Spot 2025-02-09 11:00 UTC, perp 13:00 UTC |
| CHEEMS | Cheems / Cheems | 0x0df0587216a4a1bb7d5082fdc491d93d2dd4b413 | Perp already live 2024-11-25, Spot 2025-02-09 |
| MUBARAK | mubarak / mubarak | 0x5c85d6c6825ab4032337f11ee92a72df936b46f6 | Perp 2025-03-17, Spot 2025-03-27 |
| TUT | Tutorial / TUT | 0xcaae2a2f939f51d97cdfa9a86e79e3f085b799f3 | Perp 2025-03-20, Spot 2025-03-27; AI/narrative-adjacent |
| BROCCOLI714 | CZ'S DOG / Broccoli | 0x6d5ad1592ed9d6d1df9b93c793ab759573ed6714 | Perp 2025-03-21, Spot 2025-03-27 |
| BROCCOLIF3B | Broccoli / Broccoli | 0x12b4356c65340fb02cdff01293f95febb1512f3b | Separate perp 2025-03-21; do not merge with 714 |
| SIREN | SIREN / SIREN | 0x997a58129890bbda032231a52ed1ddc845fc18e1 | Perp 2025-03-22; narrative-adjacent |
| BANANAS31 | Banana For Scale / $BANANA | 0x3d4f0513e8a29669b960f9dbca61861548a9a760 | Perp March 2025, Spot 2025-03-27 |
| BOB | Build On BNB / BOB | 0x51363f073b1e4920fda7aa9e9d84ba97ede1560e | 1000000BOBUSDT perp 2025-06-05 |
| BULLA | BULLA / BULLA | 0x595e21b20e78674f8a64c1566a20b2b316bc3511 | Added in this pass; perp 2025-07-04 |
| 4 | 4 / 4 | 0x0a43fc31a73013089df59194872ecae4cae14444 | Perp 2025-10-08 |
| GIGGLE | Giggle Fund / GIGGLE | 0x20d6015660b3fe52e6690a889b5c51f69902ce0e | Perp 2025-10-09; Spot 2025-10-25 |
| 币安人生 | 币安人生 / 币安人生 | 0x924fa68a0fc644485b8df8abfa0a41c2e7744444 | Perp 2025-10-20; Spot 2026-01-07 |
| 我踏马来了 | 我踏马来了 / 我踏马来了 | 0xc51a9250795c0186a6fb4a7d20a90330651e4444 | Perp 2026-01-21 |
| 龙虾 | 龙虾 / 龙虾 | 0xeccbb861c0dda7efd964010085488b69317e4444 | Perp 2026-03-11; association of this exact CA to Binance announcement requires further primary corroboration |
| 牛来 | 牛来 / 牛来 | 0xbeea1d618e533a387d941f58a7d4c9b7bd377777 | Perp 2026-08-30, Spot 2026-09-09 |
| MARSCOIN | MarsCoin / MarsCoin | 0xfe189e97832da1573e4e4ff034f4ffc3a15c7777 | Perp 2026-09-01, Spot 2026-09-04 |
| 哈基米 / HAJIMI | 哈基米 / 哈基米 | 0x82ec31d69b3c289e541b50e30681fd1acad24444 | Perp 2026-09-06 |

The token contract metadata check (read-only Alchemy getTokenMetadata on bnb-mainnet) succeeded for all 18. **This does not independently verify their Binance listing chronology or exact Alpha debut dates**. Alpha first appearance is NOT yet individually audited; do not record implied A->F->S order without evidence. Binance support URLs below support individual listings as indicated.

Canonical English first-party source URLs:
- TST/CHEEMS spot https://www.binance.com/en/support/announcement/detail/8aa1b6610a534fcb95b46956f2ed4391
- TST perp https://www.binance.com/en/support/announcement/detail/5c6d784eaa0845fb85625cacbce01821
- MUBARAK/TUT/BROCCOLI714/BANANAS31 spot https://www.binance.com/en/support/announcement/detail/6e3391cffa774b2a9711e8597a618edb
- MUBARAK perp https://www.binance.com/en/support/announcement/detail/b4a7eb2646c640b39eab0e329a0d656b
- March 2025 derivative cohort https://www.binance.com/en/support/announcement/detail/347f9455d9b94d258498df2e2d5e56a7
- Build On BNB BOB perp https://www.binance.com/en/support/announcement/detail/9d12cbfb72bb46e6835313471b6b3c85
- BULLA perp https://www.binance.com/en/support/announcement/detail/ace718d550c546b6a0e6db56af71f956
- 4 perp https://www.binance.com/en/support/announcement/detail/17fabba926004325b780c4d6883f0729
- GIGGLE perp https://www.binance.com/en/support/announcement/detail/8272526b66b042dfbfbd7b717f3d4490
- GIGGLE spot https://www.binance.com/en/support/announcement/detail/9de462f111c64723ac54331163e2652c
- 币安人生 perp https://www.binance.com/en/support/announcement/detail/a6aeec228c6a403da616e873011317ea
- 币安人生 spot https://www.binance.com/en/support/announcement/detail/51881f9d018242ce80bed6ce015de2a7
- 我踏马来了 perp https://www.binance.com/en/support/announcement/detail/7736f9a5aae24206b17884e5de02dabc
- 牛来 perp https://www.binance.com/en/support/announcement/detail/6e9e9784397745f4a49d3f69b1cfebda
- 牛来 spot https://www.binance.com/en/support/announcement/detail/6133e417dcfe43a8ad20c0db1b53c7e8
- MARSCOIN perp https://www.binance.com/en/support/announcement/detail/4d9ae75c02114187b699cfe1380ac81e
- MARSCOIN spot https://www.binance.com/en/support/announcement/detail/c2eaa763831745b2b1701dab45e20225
- HAJIMI perp https://www.binance.com/en-KZ/support/announcement/detail/ca3196e008da448da107d397bae0b4b0

## Validated V2/WBNB pool baseline

Factory 0xca143ce32fe78f1f7019d7d551a6402fc5350c73, token WBNB 0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c, read getPair(token,WBNB) over eth_call; note this does not prove V2 is the dominant pool.

| Token | Pancake V2/WBNB pair | First observed pair->token transfer (block; UTC) |
|---|---|---|
| TST | 0xb36c81707e5ca2bd6f68cd6b71b3178d29c48a4b | 46421406; 2025-02-06 12:39:40Z |
| MUBARAK | 0xb7c6f7db26cde42550e4017bb9855bbaaa20eb44 | 47442149; 2025-03-13 23:21:25Z |
| BROCCOLI714 | 0x9eb0bc7a207f77811ee365729d00152622a745b7 | 46627716; 2025-02-13 16:36:19Z |
| TUT | 0xd7efdee04e508502bdc666f67f3d9b006c20318d | 46521969; 2025-02-10 00:28:24Z |
| BANANAS31 | 0xe518025b12f424f825f3b53c8d4a747ccbfc6127 | 46871949; 2025-02-22 04:09:32Z |
| GIGGLE | 0xd6b652aecb704b0aebec6317315afb90ba641d57 | 61963755; 2025-09-21 16:21:27Z |
| MARSCOIN | 0x9f286c9bd510150c62a08da72af797ac45311ae0 | 112668718; 2026-07-28 17:48:28Z |

All first observed transfers reflect *this* particular V2 pool's visible history, not necessarily the token's earliest trade on any venue. They were read directly via getAssetTransfers and block timestamps.

## First five token earliest-swap pilot and false positives

Per token TST, MUBARAK, BROCCOLI714, TUT, BANANAS31: sampled first 30 pair->token ERC20 transfer entries, 150 total. This is a limited exploration sample, not all historical traders and not 150 independent investors; transactions may emit multiple transfers.

10 token-transfer recipient addresses appeared in >=2 sample tokens, two of them in >=3 tokens:
- 0xa01cd5b68265b972b73a713f6d824d1a6d3612b0: TST/TUT/MUBARAK
- 0x17cd8e8d4c64aa7f2a8db6947b330885da56b833: TST/TUT/MUBARAK
All 10 apparent overlapping recipients in this sample had non-empty contract code, frequently routers/intermediaries. **No profitable EOA is confirmed from this naive overlap.** Proper linkage must inspect transaction.from, router final beneficiaries, pool route, funds and historical sell receipts. Example 0x3e41e4f503dde84d7c0efa79002167e0176dbf26 appears as a real EOA transaction initiator on both MUBARAK and TUT, but win rate and realized PnL unknown; high-frequency trading/router usage requires screening.

Sample outcome/counterexample:
- BROCCOLI714 trader 0x4fd7927d6cab9d5da0191303f585923ef00dfb98 spent 5 BNB tx 0x982185a6abe5fad6c65df85bed504567818c0d807975dd0efbdd9a286d0bbb1d (block 46627719); sold acquired 5941.6644 units tx 0xf06073abb94588ab1df40648be1c34dfc4bb5e4bb731fa7606eff8845291a3bc (block 46627928), receiver's BNB balance delta +0.5192281859 BNB (after sell gas), gross simple return approx -89.6% against initial 5 BNB. This is one completed position, not a sample mean.
- TST trader 0xd225bc3852a84ec4f63a35ae019040bc5308b3ce spent 0.01 BNB tx 0x0cfa780f55ef31cba01f0881e0f358e89e8d028bf9415fd0f445fd3e2487bc84 and exited block 46422471 tx 0xa3a8aa80e8b9bb8afb15112739874c8a956d1258f3b74d009cca8d865e55bfdd, net BNB change +0.01086588158 BNB (~+8.7% against 0.01 BNB, not fully adjusted for buy gas). Small lot; no multi-token proven edge.

## Priority cross-token wallet candidate: 0x5c0c5d788661dde7437842fb7f0bbff7f1607583

The English Lookonchain 2025-04-15 article https://lookonchain.com/articles/1054 is a *lead* claiming very large MUBARAK+TUT historical gains. The article adds unrealized inventory market values to sold proceeds. Its PnL numbers MUST NOT be treated as independently validated realized profits.

Direct on-chain results:
- EOA (eth_getCode 0x).
- Received/traded both MUBARAK and TUT; as of 2026-10-10 tokenBalances from primary sender are zero for both.
- MUBARAK transfer of 6,000,000 from this EOA to 0x7c7adc5846c7d96debecf0d439f8a91bf8ea4228, tx 0xbf52c954489eacd9190355a65dbcbcdb422e54d8849c47e01200863bed26c81e block 47586058.
- TUT transfer of 9,200,000 from same EOA to the same destination, tx 0x1c6f67c7d3e64cad424b19a171cdc3f046132390a56d8ab9357ed5eb077a7ff2 block 47586023. Difference 35 blocks. **Confirmed co-movement**. Shared control/ownership is INFERRED, not verified through signature/funding proof; destination could be custodial.
- Receiver 0x7c7adc5846c7d96debecf0d439f8a91bf8ea4228 current MUBARAK and TUT balance also zero, with outflows through routers and further transfers.
- Receiver later sent 8,000,000 TUT to EOA 0x91355579743440529de8d7d8e298be93ebc64ec3, tx 0xfc90512fcad0a2c8b927f76c675611b243eea5b805a67ba0035c7ef6a7000d40. That EOA subsequently sent TUT to 0x471aab13166c3c8b80996b495966b078a5b40a07, which in turn transferred it onward to 0x8894e0a0c962cb723c1976a4421c95949be2d4e3. These token movements alone are NOT realized profit.
- Entry timing directly checked via eth_getBlockByNumber and original transaction: this wallet's MUBARAK purchase tx 0xe2fe41b715bf1e8532fbdff05642433e1a88536f4093f6c9e51406ee8ae4f9b5 (39 BNB native transaction.value, **not necessarily complete all-in purchase cost**) occurred 2025-03-14 14:58:43 UTC, BEFORE the 2025-03-17 Binance MUBARAK perpetual listing and 2025-03-27 Spot listing. Its TUT buy transaction 0x16e655d2e80bb672ed8ca71b2211df60fe5aab58269ffb6f48eaead4047faede occurred 2025-03-04 14:47:22 UTC, BEFORE the 2025-03-20 perpetual and 2025-03-27 Spot listing; transaction.value was zero so token acquisition cost and quote asset require decoding token/log and internal swaps.
- The 6M MUBARAK and 9.2M TUT co-transfers into the same later wallet occurred on 2025-03-18 23:17:28 UTC and 2025-03-18 23:15:43 UTC respectively, **before either asset's Binance Spot listing**. This creates an auditably reproducible pre-listing two-token trader hypothesis, not an insider/manipulation or profit finding.
- RESEARCH FLAG: CROSS_TOKEN_CONFIRMED; REPEATED_REALIZED_PROFIT=UNVERIFIED; person pattern OBSERVE_ONLY.

## Next steps, in priority order

1. Complete listing evidence matrix per token for token contract, first launchpad/DEX trade, actual first Alpha timestamp, first USD-M perpetual, first Spot; preserve original Binance sources and UTC announcements. Do not fill missing dates.
2. Capture ALL DEX pools / migrators (Four.meme, Pancake V2/V3, aggregators), quote assets and token trade receipts around each first event. Never rely only on one V2/WBNB pool.
3. Reconstruct source and related recipient wallet complete tx sequence for MUBARAK and TUT; link BNB/USDT/USDC inflows to full cost and realized proceeds, follow follow-on transfer addresses, separate open position/transfer/CEX deposits. This must precede “two profitable tokens” status.
4. Build cross-token wallet candidate table keyed by verified true trader EOA or evidence-backed controlled cluster, not contracts; compare 2+ distinct token profitable trades and event timing, initial liquidity, gas/slippage, buyer entry delay, winners and losers, realistic follow delay and max drawdown.
5. Keep raw queries, transaction hashes, first listing evidence and missing-data counts in reproducible audit artifacts. No production, alerts, automations or wallet actions.

### Caveat / no manipulation attribution

Official Binance listings evidence only Binance product listings and decisions. Insider association, front-running, coordinated trades, controlled wallet cluster, Binance-directed price manipulation and actual multi-meme realized PnL remain UNVERIFIED unless independently established with adequate direct evidence.


## 2026-10-10 additional complete V1 pair-onset coverage / active wallet pilot

User-priority modification: **investigate all 18 candidate tokens**, prioritize 2026, and treat currently active wallets as more relevant than historical wallets abandoned after a one-off success. A 30-day activity window is a *research filter for the observation date*, not a production signal, immutable threshold, or evidence of profitability. When no active profitable cross-token wallet can be verified, report that rather than upgrading stale winners.

### Full 18/18 Pancake V2/WBNB first-observed outward transfer audit

Factory `0xca143ce32fe78f1f7019d7d551a6402fc5350c73`, WBNB `0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c`. All below involve a valid deployed BSC ERC20 and the corresponding `getPair(token,WBNB)` result. Timestamp obtained with `eth_getBlockByNumber`. **Not** a claim of earliest token trade across all Pancake V3/Four.meme/aggregators or the earliest Binance Alpha debut.

| Token | First pair -> token transfer (block) | UTC timestamp |
|---|---:|---|
| CHEEMS | 42638564 | 2024-09-28 03:51:30 |
| BOB | 44007572 | 2024-11-14 16:57:32 |
| TST | 46421406 | 2025-02-06 12:39:40 |
| TUT | 46521969 | 2025-02-10 00:28:24 |
| BROCCOLI714 | 46627716 | 2025-02-13 16:36:19 |
| BROCCOLIF3B | 46628417 | 2025-02-13 17:11:22 |
| SIREN | 46828940 | 2025-02-20 16:18:55 |
| BANANAS31 | 46871949 | 2025-02-22 04:09:32 |
| MUBARAK | 47442149 | 2025-03-13 23:21:25 |
| BULLA | 50982375 | 2025-06-06 13:46:08 |
| GIGGLE | 61963755 | 2025-09-21 16:21:27 |
| 4 | 63056879 | 2025-10-01 04:08:41 |
| 币安人生 | 63454407 | 2025-10-04 15:01:32 |
| 哈基米 | 63838944 | 2025-10-07 23:09:03 |
| 我踏马来了 | 73658907 | 2026-01-01 05:46:51 |
| 龙虾 | 83636129 | 2026-02-27 08:50:41 |
| MARSCOIN | 112668718 | 2026-07-28 17:48:28 |
| 牛来 | 116314923 | 2026-08-16 17:47:19 |

Important: MARSCOIN canonical CA is **exactly** `0xFe189E97832DA1573e4e4Ff034F4fFC3a15c7777`; its V2 pair is `0x9f286c9bd510150c62a08da72af797ac45311ae0`. A malformed shortened address in an exploratory query incorrectly returned zero pair; its correct lookup was repeated, validated, and returned the pool above. Do not use the malformed value.

Additional V2/WBNB pair addresses:
- CHEEMS `0xaf0eb8f2f114917ef0026105c070cf08423f488e`
- BROCCOLIF3B `0xd32041a219835ed79c1ffd7f43df68d06b9b13d5`
- SIREN `0xa9b4493042830109b44e18ec3586ecd22bd032ed`
- BOB `0x3c79593e01a7f7fed5d0735b16621e2d52a6bc58`
- BULLA `0x3551191f78869c29388886330f31739a87866c38`
- 4 `0xf0a949d3d93b833c183a27ee067165b6f2c9625e`
- 币安人生 `0x66f289de31eef70d52186729d2637ac978cfc56b`
- 我踏马来了 `0xa651c8deb3ff9f8d56a26e72042b7a8a1f433480`
- 龙虾 `0x22af7297243c4eef12e2d5a4f888b92e56bf127c`
- 牛来 `0xbfc26980d8068ae744f5405d3abf6e7df02e11b3`
- 哈基米 `0xc33bacff9141da689875e6381c1932348ab4c5cb`

2026 five-token pilot: extracted first 30 V2 pool ERC20 outgoing transfers **per token** for 我踏马来了, 龙虾, 牛来, 哈基米, 币安人生 (150 transfer rows, not 150 unique trades). Six overlapping recipient addresses on two sample tokens; `0x38fb583d3a797219651eb960fdbdeb31f8ec7a18` and `0xb300000b72deaeb607a12d5f54773d1c19c7028d` are smart contracts, not independent profitable traders. Three other repeated earlier recipients are high-activity EOAs with no PnL inferred from the overlap alone. A further shared tx initiator `0x994824828bf19ae7a17dd4004cbdf90e8f4fa1e0` sent early swaps on both 我踏马来了 and 龙虾 via `0x38fb...`; **no direct token balance/transfer position for either token in that EOA** was found, and its nonzero nonce alone cannot be taken as verified profit. No profitability claim for router/MEV overlaps.

### Priority, 2026 cross-token **realized** profitable EOA: 0x239e74bfbd02d71cdc70fecc2d505dc13acfb337

BSC `eth_getCode=0x` (EOA), `eth_getTransactionCount=0x12d6` (=4822) on the observation day. Native active send last checked 2026-09-18 01:06:10Z at block 122514474, and token outgoing later in September. **This is within 30 days of 2026-10-10**, while not proof of recent profitable trades. Its full 4822-tx trading history is NOT reconstructed. Do not rank this wallet on 2 winning examples alone.

1. 我踏马来了 CA `0xc51a9250795c0186a6fb4a7d20a90330651e4444`. Initial buy block 73658908 at 2026-01-01 05:46:51Z, tx `0x5eaf490ddad77bc6ddfc366f49c86b25fda316d6468a95cd3f5907fdcf39e347`, direct `tx.from` wallet; 322094.73547686834 units. Five sales in blocks 73659128, 73659482, 73659538, 73660412, 73664688, signed by same wallet. Wallet now holds zero units; total position accounted. Native BNB balance block deltas: initial buy -0.030755250000000000 BNB, five sales +0.12812197052437657 BNB, approx **+0.09736672052437657 BNB**, return +316.6% relative to buy net debit. Relevant Binance perp listed 2026-01-21 14:30Z, therefore initial entry precedes perp. First sale example `0x2413eaeadd4d7be589d9773bd4c53c2811254c1c641736ad1dacd6fd36137687`.
2. 龙虾 CA `0xeccbb861c0dda7efd964010085488b69317e4444`. Initial buy block 83636130 at 2026-02-27 08:50:41Z, tx `0x5a697b7dc48c947f8f2a1f61677fadb04c2374ca38298302bfc94b8623aaa3fc`; same `tx.from` wallet. **7 buy txs** all signed by the wallet, with token incoming sum **271811.9432272108**, and **14 sell txs** all signed by same wallet with token outgoing sum **271811.94322721084**. Current token balance zero. Buy blocks: 83636130, 85589795, 85767531, 85954137, 85954824, 85959961, 86649314. Sell blocks: 83638195, 83640592, 83641353, 83646760, 83659034, 83673243, 83675049, 84031185, 84188954, 85602706, 85952403, 85957578, 85961371, 87876365. Buy-block net BNB deltas sum -0.82768143708; sale-block net BNB deltas sum +1.0268070305733352; approximate **+0.19912559349333525 BNB**, +24.06%. Example exit `0xbd99c6758d693e9613fcd63d1a0857f8f407ac329dff678734c66a5d70695d45`. Initial entry precedes Binance 龙虾 perp 2026-03-11 11:30Z. Independent exact-contract anchor: https://www.binance.com/en/alpha/bsc/0xeccbb861c0dda7efd964010085488b69317e4444 and https://www.gate.com/announcements/article/50132 .
3. Combined for THESE TWO positions ONLY: **+0.2964923140177118 BNB**, 2/2 closed profitable; sample-selected and therefore *not the wallet's historical win rate*. BNB delta by transaction-containing block includes contemporaneous Gas and could theoretically contain other same-block balance movements. Thus treat as verified token buy/sell counts, verified block cashflows, **estimated position-level realized profit**, not fully fee/internal-flow-audited accounting. Do not extrapolate.

Official Binance first-party listings: 我踏马来了 https://www.binance.com/en/support/announcement/detail/7736f9a5aae24206b17884e5de02dabc ; 龙虾 https://www.binance.com/lo-LA/support/announcement/detail/d9c05581552140eba3f393ef0a9a23b3 ; Binance exact-CA Alpha page for 我踏马来了 https://www.binance.com/en/alpha/bsc/0xc51a9250795c0186a6fb4a7d20a90330651e4444 ; Binance exact-CA Alpha page for 龙虾 https://www.binance.com/en/alpha/bsc/0xeccbb861c0dda7efd964010085488b69317e4444 .

### Research guardrails for next iteration

- This run **checked first V2 pool records for all 18 candidates**, with short samples and a 2026-focused 150-transfer pilot; it DID NOT compute every wallet's full all-DEX lifetime transactions, PnL, all routes/aggregators, or completeness of the Binance Alpha universe. Label coverage faithfully.
- To meet the user's long-run objective, add pre- and post-Binance-listing windows for **each** of the 18, and seek missing BSC 2026 additions only with first-party listing evidence; audit full complete winner AND loser histories per wallet, including other unrelated meme losses.
- Recalculate wallet 0x239e full historical PnL, other tokens, trade timing and max loss; determine whether its activity in September 2026 is actual trading rather than only transfers, and whether any signals would be late but actionable.
- Do not count stale 2025-only winners as present opportunities without 2026 activity and current trading validation.
- Remain `OBSERVE_ONLY`; `PRODUCTION_TRADING=NO_GO`; no monitor/automation/launchd/Gmail config changes.


### Additional 2026 trades of the same wallet, including losses

To avoid two-winning-trade survivorship bias, researched three more complete, zero-current-balance ERC20 round trips for EOA `0x239e74bfbd02d71cdc70fecc2d505dc13acfb337`. Each of nine original trades (buy/sell transactions across these three tokens) independently checked `transaction.from == EOA`. Values below reflect direct BNB-balance delta across transaction-containing BSC blocks (net of that block's native gas, but possible same-block other-value caveat still applies). The ERC20 contract ID is essential due to non-unique token symbols.

| Token / contract | BUY: BNB net decreases | SELL: BNB net increases | Estimated closed-position PnL | Approx ROI |
|---|---:|---:|---:|---:|
| Meme `0xf9d556ad3eb1836e53e1433bdd6dd5568a047777` | 0.0100847206 | 0.01715114834062531 | +0.007066427740625311 | +70.07% |
| QQ `0xea54485bcfd3096a7e1ca8eccaa0c0cf37057777` | 0.06015111348 | 0.0258475049058344 | -0.0343036085741656 | -57.03% |
| LION `0x705a450d0a0a807d04c75a8ba9a5f88a64067777` | 0.02006709212 | 0.010089712353703808 | -0.009977379766296193 | -49.72% |

- Meme buy/sell block 119919330 / 119920209; buy tx `0xca0ae172afd91a64836af64c8860c1ba310277603b83294a39d696e112c71e09`, sell tx `0x468b5e9739cc4d5aa3c8ea8bb5e23369002c32f66693b9d12caeabc764a852bc`.
- QQ buy blocks 116786906, 116787302, 116787699; sell blocks 116787153, 117904196. One full entry/exit cycle across repeated partial sells. Buy tx `0xb97ea50ed09066a75c02e7d6a82e2f6caea5a57a4b98e4cdf13f83602ec0bb6b`, final sell tx `0x62441767042a2e5e9086bee319b496b0f21717253f1115c12f5a694da384672a`.
- LION buy/sell block 117888218 / 117888395, tx `0x8bb352b783e084f8f296ba06b039af59d451ca09eba95c681720239d2f87680f` and `0x99f5908b8c84354b46dd08f5a003e3430e43d89f46f3176a2cd63eaf20d62a1b`.
- Among these specifically researched **five** closed positions (我踏马来了, 龙虾, Meme, QQ, LION), 3 were net profitable, 2 lost, combined +0.25927775341787535 BNB (limited selected sample win rate 3/5 = 60%). **Do not claim historical wallet win rate 60%**; many other txs were not sampled. Distinct from 18 project candidate universe, which includes only the first two of these five.
- Additional candidate-universe checks on the same wallet for 牛来, MARSCOIN, 哈基米, 币安人生, TST and MUBARAK found no direct trading transfers, except one tiny 16.939109 牛来 inbound transfer with no matching outbound; this is not a repeated hit/profit on those six. Broader active-wallet candidate search is still necessary.
- Bottom line: EOA `0x239e74bf...` is a genuinely active-in-2026 **research candidate** with at least two observed BSC Binance Meme profitable closed positions and observable losing Meme positions elsewhere, but no demonstrated full-history edge, no proof of insider Binance connection, no tested delay-follow profitability. Status remains **OBSERVE_ONLY**.

## 2026-10-10 top-profit-address and cross-wallet linkage expansion

Scope requested: **all 18 sample tokens**, seek highest-realized-profit traders per token, compare them across coins, infer common control only with corroborating chain evidence, and prioritize activity in 2026. This addendum records what is **actually audited** versus what still needs a historical PnL-indexed top-trader export.

### Coverage and rank caveat

- Direct Alchemy BSC RPC read **both first and latest 10 pair->token ERC20 outgoing transfer rows** for each of the 18 candidate token addresses' previously verified Pancake V2/WBNB pool. Some tokens have fewer than 10 distinct observable non-self recipient events within the immediate transfer-page. The first-slice scan produced 11 repeated recipient addresses across >=2 sample tokens, of which 8 had contract code and **only 3 had EOA code**. Repetition of a token-transfer receiver is not proof of the same owner actually initiating a trade, nor a realized-profit leaderboard.
- The latest-slice scan produced 13 repeated recipient addresses across >=2 token pools; **12 contracts and 1 EOA**. The EOA was `0x7817dbf38e9d1c95671625f0052c147864692fe0`, appearing in CHEEMS, TST, BROCCOLI714, MARSCOIN. Original transactions from these four occurrences have **different tx.from signer wallets**, all call destination contract `0x16ceff8d5a4c8648fcc7293f8bd3ac9ada454219`; it is therefore a **shared transfer receiver/intermediary**, not a validated repeated-investor PnL record. Examples:
  - CHEEMS tx `0xbe399e756095a4d381b8474fec39a56234873145928e80697aa565dffa0291d4`, tx.from `0x0aa536530a613b4b3f93601737b91ce183576def`;
  - TST tx `0x84a40b907c12a9d5f62042c9925bd942d1066f9100d503d219adc6626e1f5da6`, tx.from `0x715626db0eb11a093344c6fe325654461c9c2138`;
  - BROCCOLI714 tx `0x61503580a82b5089390af28f3b3ddf96b0ea3b5fb9eaed59ecb27d64e05d90d3`, tx.from `0x366888c9645d96224ff8fafd863d0994df23d7cd`;
  - MARSCOIN tx `0x001ec5bdc03fb1c79f4fa7a5e1c7f298bf22104738c8c05c813e62b9d238bb1c`, tx.from `0xbfc398f7b1e66d11043cafe90f7fad1bd2a77daf`.
- One *actual common tx.from signer* between a MARSCOIN and 牛来 recent V2 pool transfer is `0x92c466204ca732ead4f6517d2d20b0f18e8f6fde`, on original transactions `0x6646815c1ec321d59378bea45f46073b52960c0d6d16a7ea4588fa5d87ed9f78` and `0x487e206f7ef882dfd6602e1946cd30ae2d54ce000d933c791853b14b0139ba54`, respectively. It is an EOA with >100k nonce on observation day, both swaps route through contract `0x29be31e7ef434a74d69da1cb6b51ad65c83e9a7b`; no direct token-in/out ERC20 transfers of these two tokens at signer wallet. **PROFIT_UNVERIFIED / contract-aggregated activity / not a copy-trading candidate without beneficiary tracing.**
- **CRITICAL:** This two-window transfer sampling is not a **top profit** ranking across all time, all DEX versions and launchpads. Even the first 10 recipients can miss the most profitable early traders (for example `0xe54bd...` occurs outside some first-10 rows). Exact 18-token top-N PnL coverage requires historical full-pool/event indexing or a keyed top-trader API. GMGN officially documents `gmgn-cli token traders --chain bsc --address <CA> --tag smart_degen --order-by profit`, requiring a `GMGN_API_KEY` (official https://github.com/GMGNAI/gmgn-skills/blob/main/skills/gmgn-token/SKILL.md); no key or authorized agent integration was used. Birdeye documents EVM token Top Traders PnL support (https://birdeye.so/data-api/blog/detail/token-top-traders-api-updates-track-smart-money-across-evm-and-solana), but 2–90d windows cannot alone reconstruct all 2025 launches in October 2026. No leaderboard data were fabricated.

### Three historical early-trader profit clusters, on-chain confirmed entries and reconstructed exits

All values below are **BNB balance differences at transaction-containing blocks**, with both original ERC20 token flow and buy/sell signer addresses corroborated for sampled trades. This estimates realized trade PnL net of the transaction-block balance changes. It is **not** a complete all-DEX, all-asset wallet audit, and unusual simultaneous block payments or transfers can still affect results. Rows describe a specifically selected and reconstructed set of **complete closed token positions**, not 'top 1' all-market ranking.

| EOA | Token | Native BNB buy net debits | Native BNB sell net credits | PnL BNB | Context |
|---|---|---:|---:|---:|---|
| `0xd70ce47ec32625420640da206f0b3525c2bec678` | 4 | 0.100909664 | 7.146838520587929 | +7.045928856587929 | 1 buy; 27 independently listed sell txs, ERC20 flows balance, dust remains |
| same | 币安人生 | 0.110934684179004 | 1.839729129650899 | +1.728794445471895 | 2 buys, 13 sell txs, token flow balances (tiny dust) |
| same | 哈基米 | 0.4610464146216875 | 3.989050878649783 | +3.528004464028095 | 4 buys, 23 sell txs, token flow balances, final amount zero |
| `0x57c98bc732f0e9ed7156d21f74c17bee4bb0cbf4` | 币安人生 | 0.021267136 | 0.4018086119896191 | +0.38054147598961907 | 1 buy, 5 sells; zero meaningful remaining balance |
| same | 哈基米 | 0.020993536 | 0.3707732340759646 | +0.3497796980759646 | 1 buy, 4 sells; no token remains |
| `0xe54bdcaff91ed27e53a19bb1203b10bc5e2dc568` | 币安人生 | 0.040843136 | 0.08670424522737501 | +0.045861109227375005 | 1 buy and exit, ERC20 balance zero |
| same | 哈基米 | 0.03075549 | 5.855017559114763 | +5.824262069114763 | 1 buy and exit, ERC20 balance zero; EXTREME outlier |
| `0x239e74bfbd02d71cdc70fecc2d505dc13acfb337` | 我踏马来了 | 0.03075525 | 0.12812197052437657 | +0.09736672052437657 | 2026; five sales |
| same | 龙虾 | 0.82768143708 | 1.0268070305733352 | +0.19912559349333525 | 2026; seven buys, fourteen sales; also documented elsewhere in this file |

**Selected-position subtotal / not entire wallet PnL**:
- `0xd70ce...`: 3/3 selected closed Binance Meme winners, +12.30272776608792 BNB. Largest 4 profit +7.045928856587929 BNB; BUY tx `0x035aa1476b0da70d2dd31865cd50a2e073053c70df2f94bdba22dfa12f6aa17a`, earliest SELL tx `0xaf8f4e3f8213ee9c74774e5d093f99e5bf6a39cd479a165c4a422b38e878718b`. Its entire 4 position 751096.660369485 units went out in 27 sell txs (with dust).
- `0x57c98...`: 2/2 selected closed token winners, +0.7303211740655837 BNB. First buys in 币安人生 and 哈基米 at blocks 63454409 and 63838946.
- `0xe54bd...`: 2/2 selected closed token winners, +5.870123178342138 BNB, overwhelmingly from the extreme 哈基米 trade. 币安人生 BUY `0x38f9dc2536bb936c1f2dc4f40851ba326a335e9f328294e11c330fe647b053f5`, SELL `0x839b1202719595f879da5443e13bcafc574dbb5c63914be67fcfca280ec604e4`; 哈基米 BUY `0x5e46faa6f9c95b0c851d8fde6a79b8fe540ab9e29627531fa78614f1a2e6113e`, SELL `0x2523458015a452a3232ae7a2c2fa50cc6c15bd2644956cacfc347948e226d021`.
- `0x239e...`: 2026 selected two +0.2964923140177118 BNB; also three selected *non-universe* Meme positions net -0.0372145605998365 BNB, documented elsewhere, so DO NOT infer all-wallet win rate.

### Actual funding and wallet-wallet linkage, separate from trading coincidences

Two of the historical EOAs have **direct, confirmed bidirectional funding flows**:
- From `0x57c98bc732f0e9ed7156d21f74c17bee4bb0cbf4` to `0xd70ce47ec32625420640da206f0b3525c2bec678`: 5 BNB, tx `0xb5e153902bedc8246633c476525b7c1f5bac843692efa16fdfa9a5937ce695b2` (block 48397922).
- From `0xd70ce...` back to `0x57c98...`: 5 BNB, tx `0x49260f6dd65211c5373d77569234276936ed1bf632bae662d0e5617675c65585` (block 48398195).
- Both received BNB from funding addresses `0x66fa07aae14e110013fb1a8835413ea77fe1b5c6` and `0x5d146231bbb42c2289a827d5c18e13d12e1c39d1`; e.g. `0x66fa07...` sent 3 BNB to first wallet in tx `0x8eca5fbf2a30c2b6e2fc6d388fb2f6a7a018e6b1e37c8d4a4444405b7af6b35e` and 2.1 BNB to second in tx `0x7acb4660a9dbe516815eee68380886e2674317d4e3931ac223809356206b493e`.
- The shared funder `0x66fa07...` had a high outgoing nonce of 12,540 when checked, so shared funding can reflect an exchange, automated disperser or omnibus actor. Direct 5-BNB bilateral settlement PLUS common funding PLUS near-synchronous launch trading supports **COORDINATED_WALLET_CLUSTER / identity still UNCONFIRMED**; it does not prove one person, Binance employment, advance knowledge or manipulation.
- The other high-profit wallet `0xe54bd...` has a **different observed primary funding origin** `0xf5988713400da6fc8a58ec9515e2b0df9b40b115`. Its synchronized early buys alone are insufficient to merge it into this wallet cluster.

### Recency matters: native balance transfers vs actual Meme swaps

As-of observation date 2026-10-10:
- `0xd70ce...`: latest identified token outgoing **2025-12-24** (block 72759513), latest native active outgoing Dec 2025. **STALE**.
- `0x57c98...`: latest token outgoing **2025-12-19** (block 72185878), latest native active Dec 2025. **STALE**.
- `0xe54bd...`: latest identified token outgoing **2026-08-07** (block 114557113), native BNB transfer as late as **2026-09-15** (block 121975534). **Native-active-within-30d, NOT verified Meme swap within 30d**.
- `0x239e...`: latest verified target-independent Meme buy/sell **2026-09-04** (Meme `0xf9d556ad3eb1836e53e1433bdd6dd5568a047777`, blocks 119919330/119920209); native active transfer **2026-09-18** (block 122514474). **Native-active-within-30d, NOT yet verified Meme swap within 30d**.
- Consequently, **none of the four named EOA wallets here has a proved target-Meme swap in the trailing 30d** under this audit. This is an important limitation for the user’s active-copytrading requirement; do not present a 2025 whale as a currently verified actionable target.

### Next audit gate

Acquire complete top-20/100 realized-profit leaderboard PER TOKEN for all 18, with explicit as-of date, chain/CA, all-time-vs-window PnL methodology, and identify real original signer vs multi-user executor. Merge on true signer + corroborated controlling wallet, not token transfer receiver. For every recurring high-profit address require actual lifetime winners AND losers, chronological entry relative to Alpha/perp/Spot, latest true Meme swap within a recent window, liquidity, gas, slippage, selling behavior, copy delay 5/15/30m and relationship funding facts. If the top-profit indexed source cannot be queried, mark `FULL_TOP_PROFIT_LEADERBOARD=UNVERIFIED` rather than manufacturing rankings. Research only, OBSERVE_ONLY, production NO_GO, live validation remains stopped, no monitoring/automation/task modifications.
