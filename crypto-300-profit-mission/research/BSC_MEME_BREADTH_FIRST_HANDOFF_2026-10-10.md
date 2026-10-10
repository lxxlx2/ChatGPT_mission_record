# BSC Meme breadth-first research handoff, 2026-10-10

RESEARCH_ONLY / OBSERVE_ONLY / PRODUCTION_TRADING_NO_GO.

## Persisted breadth coverage

Prior Git research scoped 18 Futures/Spot-oriented BSC meme token contracts and one Alpha-only BUBB control. This is not the complete Binance token universe.

21 historical pool sources: 19 V2/WBNB and two Four.meme pre-V2 pools.
Each pool: first 50 ERC20 outgoing transfer events only. Full pagination and full venues are still incomplete.
Raw transfer provenance is recorded as tx hash, block, sender, recipient, ERC20 raw quantity and decimals.

Captured earliest V2/Four.meme ERC20 transfer rows: 1050, plus second-pass global earliest ERC20 transfers: 530; additional event-anchor windows: 80
Unique pool transfer recipients: 567
Observed recipients repeated in >=2 token samples: 44
Among overlaps EOA (code=0x): 9
Among overlaps deployed smart contracts: 35
Combined wallet candidate queue: 19 (updated after second pass; see appended section)
Fully paginated venues: 0

## Sampled source coverage

TST | PANCAKE_V2_WBNB | pool 0xb36c81707e5ca2bd6f68cd6b71b3178d29c48a4b | transfer rows 50 | distinct tx hashes 49 | blocks 46421406 to 46421439
CHEEMS | PANCAKE_V2_WBNB | pool 0xaf0eb8f2f114917ef0026105c070cf08423f488e | transfer rows 50 | distinct tx hashes 50 | blocks 42638564 to 42639101
MUBARAK | PANCAKE_V2_WBNB | pool 0xb7c6f7db26cde42550e4017bb9855bbaaa20eb44 | transfer rows 50 | distinct tx hashes 49 | blocks 47442149 to 47442279
TUT | PANCAKE_V2_WBNB | pool 0xd7efdee04e508502bdc666f67f3d9b006c20318d | transfer rows 50 | distinct tx hashes 50 | blocks 46521969 to 46522238
BROCCOLI714 | PANCAKE_V2_WBNB | pool 0x9eb0bc7a207f77811ee365729d00152622a745b7 | transfer rows 50 | distinct tx hashes 50 | blocks 46627716 to 46627739
BROCCOLIF3B | PANCAKE_V2_WBNB | pool 0xd32041a219835ed79c1ffd7f43df68d06b9b13d5 | transfer rows 50 | distinct tx hashes 50 | blocks 46628417 to 46628441
SIREN | PANCAKE_V2_WBNB | pool 0xa9b4493042830109b44e18ec3586ecd22bd032ed | transfer rows 50 | distinct tx hashes 50 | blocks 46828940 to 47373254
BANANAS31 | PANCAKE_V2_WBNB | pool 0xe518025b12f424f825f3b53c8d4a747ccbfc6127 | transfer rows 50 | distinct tx hashes 50 | blocks 46871949 to 47227781
BOB | PANCAKE_V2_WBNB | pool 0x3c79593e01a7f7fed5d0735b16621e2d52a6bc58 | transfer rows 50 | distinct tx hashes 29 | blocks 44007572 to 44007612
BULLA | PANCAKE_V2_WBNB | pool 0x3551191f78869c29388886330f31739a87866c38 | transfer rows 50 | distinct tx hashes 50 | blocks 50982375 to 51168776
4 | PANCAKE_V2_WBNB | pool 0xf0a949d3d93b833c183a27ee067165b6f2c9625e | transfer rows 50 | distinct tx hashes 50 | blocks 63056879 to 63056888
GIGGLE | PANCAKE_V2_WBNB | pool 0xd6b652aecb704b0aebec6317315afb90ba641d57 | transfer rows 50 | distinct tx hashes 25 | blocks 61963755 to 61963755
币安人生 | PANCAKE_V2_WBNB | pool 0x66f289de31eef70d52186729d2637ac978cfc56b | transfer rows 50 | distinct tx hashes 50 | blocks 63454407 to 63454417
我踏马来了 | PANCAKE_V2_WBNB | pool 0xa651c8deb3ff9f8d56a26e72042b7a8a1f433480 | transfer rows 50 | distinct tx hashes 50 | blocks 73658907 to 73658916
龙虾 | PANCAKE_V2_WBNB | pool 0x22af7297243c4eef12e2d5a4f888b92e56bf127c | transfer rows 50 | distinct tx hashes 50 | blocks 83636129 to 83636147
牛来 | PANCAKE_V2_WBNB | pool 0xbfc26980d8068ae744f5405d3abf6e7df02e11b3 | transfer rows 50 | distinct tx hashes 25 | blocks 116314923 to 116318053
MARSCOIN | PANCAKE_V2_WBNB | pool 0x9f286c9bd510150c62a08da72af797ac45311ae0 | transfer rows 50 | distinct tx hashes 25 | blocks 112668718 to 112679229
哈基米 / HAJIMI | PANCAKE_V2_WBNB | pool 0xc33bacff9141da689875e6381c1932348ab4c5cb | transfer rows 50 | distinct tx hashes 50 | blocks 63838944 to 63838984
BUBB | PANCAKE_V2_WBNB | pool 0xaa80df50c2f6ecb6963636cd2b1a3bf0413b7e3c | transfer rows 50 | distinct tx hashes 50 | blocks 47620848 to 47621501
MARSCOIN | FOUR_MEME_PRE_V2 | pool 0x94f3ed36706c746ad59fadcaf271b7431ab1d8f1 | transfer rows 50 | distinct tx hashes 25 | blocks 112441460 to 112441466
牛来 | FOUR_MEME_PRE_V2 | pool 0x595d70977dff3c841df0bc0138ce89f80c7c9423 | transfer rows 50 | distinct tx hashes 25 | blocks 115853707 to 115853797

## Candidate backlog

Every wallet below needs source-complete net-profit accounting; sample receiver overlap or signed buys alone never prove gains.

0x2adf961b40951736bcff3b36b7fb1cd5775475ba | observed sample tokens: none in earliest 50 | newly checked original signer tokens: none in this pass
0xd70ce47ec32625420640da206f0b3525c2bec678 | observed sample tokens: 4, 币安人生, 哈基米 / HAJIMI | newly checked original signer tokens: none in this pass
0x239e74bfbd02d71cdc70fecc2d505dc13acfb337 | observed sample tokens: 我踏马来了, 龙虾 | newly checked original signer tokens: none in this pass
0xe54bdcaff91ed27e53a19bb1203b10bc5e2dc568 | observed sample tokens: 币安人生, 哈基米 / HAJIMI | newly checked original signer tokens: none in this pass
0x57c98bc732f0e9ed7156d21f74c17bee4bb0cbf4 | observed sample tokens: 币安人生, 哈基米 / HAJIMI | newly checked original signer tokens: none in this pass
0xadffbebbd2d9141cff80f8a905846ba8f9e3946d | observed sample tokens: none in earliest 50 | newly checked original signer tokens: none in this pass
0x877af245c61289b24f0c619a4346cdbc68f1aaac | observed sample tokens: none in earliest 50 | newly checked original signer tokens: none in this pass
0x498528e32b04bdaa73d5c8943a09aeffd15bd99a | observed sample tokens: none in earliest 50 | newly checked original signer tokens: none in this pass
0x5c0c5d788661dde7437842fb7f0bbff7f1607583 | observed sample tokens: none in earliest 50 | newly checked original signer tokens: none in this pass
0x2b40f892a5b8aefdf9868317330ca0f956f70d2b | observed sample tokens: SIREN, BANANAS31 | newly checked original signer tokens: SIREN, BANANAS31
0x47b87148e6ddff25fe765a0ac23aaa4c19f1b429 | observed sample tokens: 4, 币安人生 | newly checked original signer tokens: 4, 币安人生
0x4789f192df5deb559af2bd9185781fda995856d5 | observed sample tokens: 4, 币安人生 | newly checked original signer tokens: 4, 币安人生
0xbeb713cced9ef608cd349cc14971c32d4e6e2ffc | observed sample tokens: 4, 币安人生 | newly checked original signer tokens: 4, 币安人生
0x3638cd44e7d8449a1adfc423cbc39e06942bc203 | observed sample tokens: 4, 币安人生 | newly checked original signer tokens: 4, 币安人生

## Canonical evidence files

BSC_MEME_BREADTH_FIRST_UNIVERSE_2026-10-10.json
BSC_MEME_BREADTH_FIRST_CANDIDATE_QUEUE_2026-10-10.json
BSC_MEME_EARLY_POOL_SAMPLE_B01_2026-10-10.json through B04_2026-10-10.json
BSC_MEME_EARLY_RECIPIENT_CROSSCHECK_B01/B02 and EXT_B01/EXT_B02, all 2026-10-10.json
BSC_MEME_CROSS_TOKEN_NEW_EOA_SIGNERS_2026-10-10.json
BSC_MEME_MAJOR_OPPORTUNITY_DEEP_AUDIT_2026-10-10.md

## Next phases

1. Complete missing first-venue, V3, aggregation and Binance-event-window samples across all 19 tokens before deep-diving a single wallet.
2. Resolve original tx signer and shared-control clusters, exclude router/fee/pool addresses.
3. Reconstruct both winners and losers with BNB/WBNB/stablecoins and gas, and mark transfers/CEX deposits separately.
4. Compare materially repeatable big-event captures before testing delayed-follow profit; unrelated small meme wins/losses do not drive ranking.

Five additional early EOAs have 10 independently signer-matched transactions across pairs of tokens, but NO complete net PnL evidence.
Several 4 and 币安人生 sampled buys occurred in close blocks. Common beneficial control remains UNVERIFIED.
No paid GMGN, new monitoring, automated trading or user-side execution was used.

## 2026-10-10 second pass: broad ERC20 inception, overlap and event anchors

This section supersedes the first-pass candidate count above; it does not supersede the raw first-50-per-pool provenance.

- Read the **globally earliest 20 ERC20 transfer events** for each of 19 token CAs directly through Alchemy without filtering to a known DEX pool. Expanded five 2026-priority event assets (我踏马来了, 龙虾, 牛来, MARSCOIN, HAJIMI) to first **50** each. Total **530** globally earliest ERC20 transfer events across 19 CAs, archived in `BSC_MEME_GENESIS_GLOBAL_TRANSFERS_2026_PRIORITY_2026-10-10.json`, `...LEGACY_A_2026-10-10.json`, and `...LEGACY_B_2026-10-10.json`.
- `BSC_MEME_GLOBAL_GENESIS_V2_GAP_MATRIX_2026-10-10.json` records all 19 exact CAs, earliest globally observed Transfer block and previously observed V2 first outgoing Transfer block, and the block-number gap. Not proof of first tradable price, launchpad transaction, Alpha initial listing or historical realized gains.
- Re-read **67 original signed transactions** using `ethGetTransactionByHash`, 25 from the five priority tokens and 42 from other scoped contracts. `BSC_MEME_ORIGINAL_SIGNERS_GLOBAL_EARLY_2026-10-10.json` and `BSC_MEME_GLOBAL_EARLY_SIGNERS_LEGACY_2026-10-10.json` contain the full transaction hashes, signers, target and selectors. **No signer overlapped across two different tokens within just these 67 selected first transactions**; this is a sample result, not evidence repeat-winning wallets do not exist.
- Deduplicating the first-global and first-50 V2/Four.meme recipient histories surfaced **60 distinct cross-token recipient addresses**. All received onchain contract-code checks (44 inherited from the previous verified check; 16 new). **46 contracts, 14 EOAs**. Contracts are excluded from PERSON_PATTERN rankings even when their address appears in many token flows.
- Five previously unqueued EOA addresses appeared across two scoped token samples and **each had two original transactions verified as self-signed**, one per token. Their realized costs, sale proceeds, major-event timing and PnL remain unknown:
  - `0x11a7327957ed5d370d2e009ec250ab0da2ab98d8`: TST + BOB.
  - `0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0`: 4 + MUBARAK.
  - `0xa83b73f5644cde337b61da79589f10ea15548811`: 4 + MARSCOIN.
  - `0xcceea39c8a5b5306a4eabaaca82a2777a39d8037`: 4 + HAJIMI.
  - `0xddac928a240bdace3994c2cc0783d4e29a002127`: 我踏马来了 + 龙虾.
- The durable candidate wallet queue now contains **19 unique EOA addresses**, old and new, with explicit signed provenance in `BSC_MEME_BREADTH_FIRST_CANDIDATE_QUEUE_2026-10-10.json`. There are NOT 19 proven independent material winners.
- Captured two chain-anchored trading intervals: GIGGLE near a previously proven 2025-10-25 post-Spot Binance-deposit transaction block `65829269`, and MARSCOIN near a 2026-09-05 signed post-Spot sale block `120088241`. Each had 50-block before and 50-block at/after intervals; first 20 ERC20 transfers per interval, **80 total**; all still paginated. Independently verified 15/20 selected original signer transactions; five long RPC responses were truncated/invalid and **remain unresolved**. These are not comprehensive listing-hour/highest-profit trader populations. Evidence: `BSC_MEME_VERIFIED_EVENT_ANCHOR_TRANSFER_WINDOWS_2026-10-10.json`.
- Provider note: the prior optional Blockscout session is invalid and offered a paid upgrade. **No upgrade, key, new monitoring or private API requested**; all completed reads use the previously approved connected Alchemy. Archive gaps explicitly rather than inventing block-to-date conversions.

**Required next phase:** continue expanding the eligible Binance BSC meme contract population via official CA and announcement corroboration; paginate actual first venues and material event windows beyond earliest-50; compare significant profitable and losing core positions, actual quote proceeds (BNB/WBNB/stables), cross-wallet clusters and delayed followability. Keep `OBSERVE_ONLY` and `NO_GO` with no auto-alert setup.
