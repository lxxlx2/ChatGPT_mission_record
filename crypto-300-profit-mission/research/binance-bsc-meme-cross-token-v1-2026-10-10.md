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
