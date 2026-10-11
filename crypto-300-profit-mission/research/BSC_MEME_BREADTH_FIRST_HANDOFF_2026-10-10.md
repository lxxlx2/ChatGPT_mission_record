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

## 2026-10-11 follow-up: all 23 candidate addresses

Research-only BSC breadth: all 23 candidate wallets checked against all 19 previously researched token CAs for both inbound and outbound ERC20 transfers. 46 directions, 394 sampled events, 33 remaining paginated. Four raw source files BSC_MEME_CORE_WALLET_CROSS_TOKEN_TRANSFER_SCREEN_B01 through B04 dated 2026-10-11; machine-readable index BSC_MEME_23_WALLET_BREADTH_COVERAGE_MATRIX_2026-10-11.json. First ten transfers per direction are partial and MUST NOT overwrite prior verified material event trades.

Native BNB external inbound breadth: 227 sampled transfers for all 23 addresses, source files BSC_MEME_FUNDING_FIRST_NATIVE_INBOUND_B01 through B04 dated 2026-10-11. Deduplicated links in BSC_MEME_23_EOA_NATIVE_FUNDING_SHARED_SOURCES_2026-10-11.json: 13 distinct funding senders repeated across recipients, seven candidate-to-candidate native transfers, all 7 independently verified by signed transaction and SUCCESS receipt. The 13 shared source addresses were code-checked as EOAs, but some can be exchange/infrastructure wallets.

Two notable possible clusters: historical reciprocal 5 BNB between 0xd70ce47e... and 0x57c98bc7...; three confirmed payments totalling 0.9 BNB from 0x4789f192... to 0x3638cd44..., and two totalling 0.165 BNB to 0xe54bdcaf.... These are funding relationships, NOT proof of same beneficial controller or independent winners. Do not score exchange wallet 0x8894e0a0... (prior Binance 51 label) as an owner cluster.

Priority remains verified core major-opportunity histories: 0x2adf... four selected 2026 winners; 0xd70ce... three historical; 0x239e... two scoped 2026 winners; 0x5c48... two fully reconciled ERC20 inventories with positive native BNB trade-block differences pending quote and same-block attribution. No production signals, automated trading, monitors or paid APIs enabled.

### 2026-10-11 supplemental linked-wallet bounded settlement

From 23-wallet full-token-transfer directions, 13 wallet-token positions had both directions completely paginated, including 9 ERC20 exact-zero-inventory positions. Four new selected positions involving 0x4789f192..., 0xbeb713cc..., 0x3638cd44... were audited by native BNB balance before/after their token-transfer blocks. Native block deltas were +0.0647332647750577 BNB (0x4789, 4), +2.763333641645156 BNB (0xbeb, 4), +1.9953488229651442 BNB (0x3638, 4), +0.2002632378274792 BNB (0x3638, 币安人生). Source BSC_MEME_LINKED_2025_CORE_POSITIONS_NATIVE_SETTLEMENT_2026-10-11.json. These remain NOT CONFIRMED isolated net PnL; native same-block attribution, unobserved quote assets and cluster controllers unresolved. No production change.


## 2026-10-11 recovered result after connection drop: 0xddac MARSCOIN / 牛来

Git-backed latest research corpus for 23 EOAs: 19 token contracts, **1,021** inbound/outbound ERC20 transfer rows, **25** pagination directions remaining, **9** wallets completed all 19-CA in/out cursors (not a full BSC universe). Source: `BSC_MEME_23_EOA_POSITION_COVERAGE_MATRIX_REFRESH_2026-10-11.json`.

`0xddac928a240bdace3994c2cc0783d4e29a002127` has per-contract **fully paginated** transfer history for both major 2026 tokens:

- **MARSCOIN**: 17 ERC20 incoming, 23 outgoing; small raw token remainder `3050660512775076744` (convert only after checking contract decimals). Native wallet BNB balance verified at **29/29 distinct ERC20 transfer blocks**, total **+3.4097121953161076 BNB**. Of 19 blocks with nonzero BNB change, **19/19** token-bearing original transactions were signer-matched to that EOA, and **18/19** targeted the Four.meme Token Manager contract `0x1de460f363af910f51726def188f9004276bf4bc`. For the 18 manager-target blocks, sum positive block-native deltas **+6.260142344876108 BNB**, negative **-2.85032382036 BNB**, net **+3.409818524516108 BNB**; one other self-signed block was **-0.0001063292 BNB**, yielding **+3.4097121953161076 BNB** across all 29 token-bearing blocks. **13/19 nonzero-block transaction receipts had visible successful status headers; 6 remained receipt-status unconfirmed due provider 8-KB response truncation.** This is a material strong positive onchain cashflow candidate but *not yet exact realized PnL*: same-block unrelated actions, quote assets, full success receipts, inter-wallet transfers, eventual remaining inventory and beneficial-control linkage still require independent reconciliation. Evidence: `BSC_MEME_DDAC_MARS_NATIVE_BLOCK_DELTA_2026-10-11.json` and `BSC_MEME_DDAC_MARS_29_TX_ORIGIN_AND_SETTLEMENT_AUDIT_2026-10-11.json`.
- **牛来**: 19 incoming, 4 outgoing ERC20 events, exact raw token in = out, **22/22 BNB native balance-delta blocks** verified, total **+0.011321909495709853 BNB**. All 10 transactions on the nonzero-BNB-change blocks rechecked as originally signed by this wallet. Still native block activity result, not fully verified realized PnL. Evidence `BSC_MEME_DDAC_NIULAI_CLOSED_BNB_BLOCK_AUDIT_2026-10-11.json`, `BSC_MEME_DDAC_NIULAI_TX_SIGNER_EVIDENCE_2026-10-11.json`.

**Research triage update**: `0xddac...` should be moved forward for material MARS profit attribution. 牛来 activity is small in native BNB terms and provides less evidence of a repeated large winner. Do NOT imply two material proven wins, do NOT enable copy trading or live monitoring. Queue updated in `BSC_MEME_BREADTH_FIRST_CANDIDATE_QUEUE_2026-10-10.json`. Subsequent priority is to audit receipt/traces/quote assets of MARS, plus breadth-first remaining 25 cursors and independent material winners.

## 2026-10-11 0x8e6b repeat-major event audit

In 23-wallet scope, 19 token CAs, 1,224 ERC20 transfer records, 23 direction cursors remain. Pagination must resume by last verified block plus event ID dedup (stale Alchemy page keys can reset).

0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0 personally signed all 32 token transactions in three quantity-closed core event positions: 我踏马来了 -0.5990238168449055 BNB native wallet block net (6 receipts success), HAJIMI +1.2428992807984849 BNB (13 receipts success), 龙虾 +4.794001707717377 BNB (11 receipt success headers, 2 truncated). Aggregate +5.437877171670956 BNB native block difference. These are verified trade-associated wallet balance changes, NOT finalized independent realized profits until traces, same-block attribution and other quote assets are fully ruled out. No independently proven profitable followability or controller linkage.

Original chain data, 26 signed tx receipts and all 26 block deltas are retained in BSC_MEME_8E6B_HAJIMI_LOBSTER_26_BLOCK_BALANCES_2026-10-11.json, BSC_MEME_8E6B_HAJIMI_LOBSTER_TX_PROVENANCE_2026-10-11.json and BSC_MEME_8E6B_THREE_CORE_EVENT_CASHFLOW_RECONCILIATION_2026-10-11.json. Prior candidate queue retained and promoted this wallet's investigation priority. Research only, NO_GO.

## 2026-10-11 final status: 0x8e6b 4-token settlement after interrupted UI

Recovered durable artifacts for wallet `0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0`: `BSC_MEME_8E6B_4_EXACT_SETTLEMENT_RECONCILIATION_2026-10-11.json` independently checked 19/19 original transaction signers and 19/19 successful receipts. Token `4` had two direct native buys totaling 0.8 BNB; 17 token exits had WBNB Withdrawal events totaling 14.004497756745366 BNB. Exact 19-receipt gas is 0.030466745273120165 BNB; first two Four.meme exits show an additional 0.009043557869177855 BNB gross-to-native settlement difference consistent with approximately 1% of those respective exits. These reconcile **exactly** to the native BNB wallet block-delta sum `+13.164987453603066 BNB`. All ERC20 token-4 inventory quantities reconcile. This is strong, successful, self-signed *scoped native settled cashflow evidence*, not complete wallet-lifetime PnL or proof of followable future results. Precise fee mechanism and full same-block internal-trace isolation remain to be audited.

The same wallet's prior proven block-native sums were HAJIMI +1.2428992807984849 (13/13 signer and receipt verified), 龙虾 +4.794001707717377 (13/13 signer and 11/13 receipt status confirmed), and 我踏马来了 -0.5990238168449055 (6/6 signed + success receipts), making aggregate four-token block-native change **+18.602864625274023 BNB**; keep their provisional attribution levels distinct, and do not reclassify all four as finalized PnL. Full provenance: `BSC_MEME_8E6B_HAJIMI_LOBSTER_TX_PROVENANCE_2026-10-11.json`, `BSC_MEME_8E6B_THREE_CORE_EVENT_CASHFLOW_RECONCILIATION_2026-10-11.json`. Comparator: `0x239e74bf...` had +0.296492314017711706 BNB across two selected event block histories, with signer/receipt verification outstanding (`BSC_MEME_239E_TWO_MAJOR_NATIVE_CASHFLOW_2026-10-11.json`). Continue breadth-first 23-wallet coverage and independent-person deduplication. Production NO_GO.

## 2026-10-11 address modeling 3: 0x8e6b GIGGLE closure and five-event scope

Added `BSC_MEME_8E6B_GIGGLE_OUTBOUND_FULL_CURSOR_AUDIT_2026-10-11.json`: five fresh Alchemy outgoing-transfer pages, 23 distinct outward GIGGLE ERC20 events (previously 18 and paginated), with all four verified incoming events, exact integer GIGGLE inflows = outflows = 359697844369402752279 raw units. Independent current token-balance check returned zero GIGGLE. This closes the selected GIGGLE transfer inventory without showing native/quote profit.

Added `BSC_MEME_8E6B_GIGGLE_16_BLOCK_NATIVE_RECONCILIATION_2026-10-11.json`: all **16** independent GIGGLE token-event txs were re-read from BSC originals, **16/16 signer matched wallet**, **16/16 receipt status 0x1**, and **16/16 block native BNB balances** checked from block N-1 to N. Scoped block-native sum **+5.715925819273344974 BNB**. Self-signed original tx native inputs total **2.505 BNB**, 16 successful receipt gas total **0.042023445 BNB**, and block-native residual after input+gas **8.262949264273344974 BNB**. Six outgoing GIGGLE blocks showed *only gas spend, no native BNB receipts*. One incoming block has a +0.0006 BNB residual. Their WBNB/stablecoin and transaction-level attribution remains open; **do not treat +5.7159 as final realized GIGGLE profit**.

Independently re-read two previously truncated 龙虾 receipt status prefixes and both returned `status=0x1`: `0x9337a2b919c2ac9749e1b311eb7a4db93c0ea62f1deba93cfa9e88bdd0b683e1` and `0x8367b2fb591be4f52a7fa4c1dae41d60889e9542208f3cfbde15119d04f14871`. Thus 13/13 lobster token-associated tx have confirmed success flags, while these two *full receipt bodies* are still truncated and complete logs/traces remain unavailable.

Five selected core token-event native balance sums for wallet 0x8e6b (4, GIGGLE, HAJIMI, 龙虾, 我踏马来了) now total **+24.318790444547367859 BNB** in exact wei arithmetic, archived in `BSC_MEME_8E6B_FIVE_MAJOR_EVENT_SCOPED_CHECKPOINT_2026-10-11.json`. **It is not complete wallet PnL and not a verified followable pattern.** 23 candidate wallets / 19 known token CAs / 1,224 observed transfer rows / 23 outstanding pagination directions remain the current breadth baseline; there are six additional observed 8e6b token names not accounted by this five-event PnL proxy. Counterparty clusters, untracked losses and delayed follower execution remain unknown. NO_GO; no automation or paid RPC activated.

## 2026-10-11 address analysis 3: complete 11 tracked 8e6b positions and comparator strengthening

**Scope caveat first:** selected token-bearing **native BNB wallet block deltas** are not realized portfolio or wallet-lifetime profits, even when every event hash is signed and the receipt is successful. Direct ERC20 USDT transfer settlement is maintained as a distinct denomination. A closed ERC20 quantity may have been acquired or disposed through another asset, fee routing, off-wallet transfer, or same-block activity. Full call traces and historical follower replay remain missing. `NO_GO` throughout.

**0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0**: 11 previously observed ERC20 contract positions now have both in/out directions fully paginated. Across exactly **131 distinct token-event blocks**, no shared block keys across those 11 cohorts, wallet BNB block changes sum in exact integer wei to **+35.831320964689925406 BNB**. Of 11 inventory histories, **8 are quantity closed**, **3 have open raw token remainder** (BROCCOLIF3B, TUT, 币安人生). The +35.8313 BNB is strictly **scoped native balance variation** across 131 selected blocks and **must not** be called realized PnL, wallet lifetime earnings, or a capital-ROI ranking. Provenance and nonoverlap: `BSC_MEME_8E6B_ELEVEN_TOKEN_COHORT_NONOVERLAP_AUDIT_2026-10-11.json`. This figure supersedes *only the earlier five-token selected-block aggregate* when referring to the same 11-CA expanded coverage; do not add the five-token sum to it again.

Evidence improvements:
- **GIGGLE**: 16/16 self-signed successful original tx receipts, 16/16 native BNB block pairs, 4 inbound and 23 outbound ERC20 token logs, exact quantity closure, scoped native block delta +5.715925819273344974 BNB. The six outward GIGGLE tx with only gas as native movement all credited USDT directly to this wallet under the **same transaction hashes**; exact six incoming USDT raw total 5061629806775951927704 (18 decimals), and one USDT-funded incoming GIGGLE tx debited 1000000000000000000000 raw. **Net USDT +4061.629806775951927704**, tracked separately from BNB. Detailed matching IDs and exact wei: `BSC_MEME_8E6B_GIGGLE_MIXED_BNB_USDT_SETTLEMENT_2026-10-11.json`. Full internal contract call traces unavailable on existing free tier, native +0.0006 BNB residual in one buy needs attribution.
- **MUBARAK**: 5 incoming +11 outgoing transfers, quantities exactly closed, 16/16 signed and successful original tx, scoped native +5.299103329471661818 BNB. Exact 16-block audit: `BSC_MEME_8E6B_MUBARAK_16_BLOCK_NATIVE_RECONCILIATION_2026-10-11.json`.
- **SIREN** two signed successful transactions, exact token inventory closed, native block sum **-0.068385433689666233 BNB**; **BULLA** two success receipts, native +0.195730110912580299 BNB but original initial tx signer unverified; **BROCCOLIF3B** seven receipts, native +0.914907916334251713 BNB, has open current ERC20 token remainder. Raw signer/block evidence: `BSC_MEME_8E6B_EARLY_2025_THREE_TOKEN_BLOCK_AND_TX_RECONCILIATION_2026-10-11.json`.
- **TUT** 10/10 successful status receipts, 8/10 self-signed, one other-signed, another original payload truncated; +0.317210430780095567 BNB native selected blocks, still holds 28050472618166057283 raw TUT units. `BSC_MEME_8E6B_TUT_10_BLOCK_NATIVE_RECONCILIATION_2026-10-11.json`.
- **币安人生** 27/27 historical token-block native balances, +4.853964166333634383 BNB selected native change. All 17 nonzero native movement original tx confirmed self-signed and successful; remaining 10 zero-native token event transactions have not all been original-signer-verified. 6176475552388755 raw units remain in wallet; realized PnL unknown. `BSC_MEME_8E6B_BINANCE_LIFE_27_BLOCK_BALANCE_AUDIT_2026-10-11.json` and `BSC_MEME_8E6B_BINANCE_LIFE_NONZERO_TX_PROVENANCE_2026-10-11.json`.

**Comparator upgrades**:
- **0xddac...** MARSCOIN: earlier 19 nonzero-BNB token transfer transactions had matched owner signing; 13 known success headers. Previously 6 unverified full-receipt responses were re-queried at original hashes, all six provide `status=0x1` and matching block numbers; therefore 19/19 success header evidence for nonzero MARS trade-linked txs. Full six receipts still truncated; +3.409712195316107766 BNB remains scoped native block cashflow, not realized PnL. `BSC_MEME_DDAC_MARS_SIX_PREVIOUSLY_TRUNCATED_RECEIPT_HEADERS_RECHECK_2026-10-11.json`.
- **0x239e...**: both scoped ERC20 token inventories exactly closed. 我踏马来了 6/6 original wallet signatures and success flags, 龙虾 21/21 original signatures and success flags. Scoped 27 block-native sum across the two is **+0.296492314017711706 BNB**, independent capital/quote profit not yet fully isolated. Source: `BSC_MEME_239E_TWO_MAJOR_FULL_SIGNED_FLOW_SOURCE_2026-10-11.json`, `BSC_MEME_239E_IFML_ORIGINAL_TX_RECEIPT_PROVENANCE_2026-10-11.json`, `BSC_MEME_239E_LOBSTER_21_ORIGINAL_SIGNER_RECEIPT_AUDIT_2026-10-11.json`.

**Next work**: separate same-block unrelated cashflows and per-transaction WBNB/native/USDT settlements for the remaining 10 8e6b cohorts, determine earliest major-entry block timestamps and favorable vs losing cohort opportunity capture; compare independent 23 candidate wallets against 2025/2026 token opportunity universe; only then test historical simulated follower delays, sizes, price impact and survivorship bias. Research only. No paid upgrades, no monitoring, no live validation, no automation, no trading.


## 2026-10-11 address modeling 3: frozen block-lag replay and cross-wallet entry timing

Research-only continuation on the existing 23-candidate BSC sample. New immutable primary artifacts:
- `BSC_MEME_8E6B_ELEVEN_TOKEN_ENTRY_EXIT_BLOCK_TIMELINE_2026-10-11.json`: all 11 observed wallet-token cohorts with first in, first out, pool sample reference block and historical UTC block timestamps. The reference is earliest sampled *V2 transfer*, **not** actual token launch, earliest tradable quote or pre-V2 Four.meme commencement. 4 first wallet buy was 4 seconds after sampled V2 transfer, 币安人生 15 seconds after; BROCCOLIF3B and MUBARAK buys actually predate their first V2 samples, so an early V2-only test would be invalid.
- `BSC_MEME_8E6B_FOLLOW_LAG_V0_FROZEN_SPEC_2026-10-11.json`: fixed 8 V2-ready, original-first-in signal cohorts (including SIREN and 我踏马来了 losses), hypothetical 0.05/0.1 BNB, 0/10/30/60 block delays, and immediate hypothetical exit after the *first* wallet outgoing event, **before querying new delayed reserve states**. MUBARAK/BROCCOLIF3B (pre-V2 activity) and BULLA (first original signer unverified) were excluded **before V0 reserve replay**. 4/币安人生 baseline reserve snapshots had already been read before freeze, making the entire study exploratory and in-sample.
- `BSC_MEME_8E6B_FOLLOW_LAG_V0_POOL_RESERVE_EVIDENCE_2026-10-11.json`: **64/64** original BSC historical Pancake V2 pool reserve reads, 8/8 correct pair token0/token1 and decimals, **64/64** predeclared zero-fee x*y=k what-if computations, plus posthoc transparent causal and depth QA. **10/64 scenarios are causally invalid:** TUT 30/60, SIREN 30/60 and 币安人生 60 (both fixed amounts), because the owner's first sell occurred **before the follower would even finish its buy**. Eight SIREN rows have serious pool-depth warnings, overlapping with some invalid rows; diagnostic overlap dedup leaves 50/64 arithmetic cases. The 50 are **not proven executable** and the 10/8 failure records have not been removed. Causal invalid raw arithmetic remains for audit and must never be counted as realized/replay winning scenarios.
- `BSC_MEME_8E6B_VS_239E_IFML_LOBSTER_ENTRY_TIMING_2026-10-11.json`: new factual opportunity capture comparator. `0x239e...` first bought both 我踏马来了 and 龙虾 **one block after** each earliest sampled V2 pool transfer, at matching block timestamps (0 seconds lag). The 8e6b first observed buys happened 611130 seconds (7.07 days) and 431 seconds later respectively. 239e initial signed native investments were just 0.0303 and 0.0202 BNB, so first-entry speed cannot prove large-liquidity, live-followable wins.
- `BSC_MEME_239E_FOLLOW_LAG_V0_COMPARATOR_FROZEN_SPEC_2026-10-11.json` and `BSC_MEME_239E_FOLLOW_LAG_V0_COMPARATOR_EVIDENCE_2026-10-11.json`: after fixing the two overlapping cohorts, use *identical* amounts/lag settings, **16/16 valid reserve observations and 16/16 zero-fee scenarios**, 0 causality-invalid. For 0.05 BNB lag 30, 239e IFML theoretical first leg +147.86%, 龙虾 +364.50%; 8e6b same-sample first leg -5.83% and +89.99%. These are **optimistic post-block two-snapshot reserve what-ifs**, not actual execution, cost-basis PnL, broad strategy results, or sound current copy signals. Candidate cohort selection uses known historical successes and cannot establish out-of-sample predictive edge.
- `BSC_MEME_ADDRESS_FOLLOW_LAG_V0_RESEARCH_REPORT_2026-10-11.md` includes full fixed-amount outcomes, explicit `INVALID`/`DEPTH` scenario labels, caveats, missing checks, and all source links.

**Model state:** 239e now has strong *early-entry-timing* samples across two tracked tokens, whereas 8e6b has broader repeated token participation across 11 tracked contracts, eight closed ERC20 inventories, 131 non-overlapping original BNB balance event blocks and additional GIGGLE USDT receipts. No wallet is proven better in complete risk-adjusted return, independent owner-control, outside selected candidates, or future copy execution. Freeze original V0 inputs and the unsuccessful/invalid outputs; do not tune them into retrospective success. Next: full chronological owner trade reconstruction (all buys/sells and quote assets, including alternative venues and same-block attribution), real follower event ordering, fees and pool-depth constraints, untouched token/time holdout and independent external code review. **OBSERVE_ONLY / NO_GO; do not enable price monitoring, automation, Gmail or trading.**

V0 arithmetic QA follow-up: `BSC_MEME_ADDRESS_FOLLOW_LAG_V0_INDEPENDENT_ARITHMETIC_QA_2026-10-11.json` independently recomputed all 80 frozen zero-fee raw reserve scenarios in exact integer wei, verified the causal-invalid masks and price-impact monotonic direction; **80/80 checks, 0 arithmetic issues**. This verifies internal arithmetic only, not execution validity, genuine price access, external AI review, model value, fees, liquidity routing, or production approval.


## 2026-10-11 address modeling 3: V1 all-buy/sell chronological episode evidence

Read `BSC_MEME_ADDRESS_MULTIFILL_V1_CAUSAL_AND_CASHFLOW_REPORT_2026-10-11.md` for all details, frozen scenario inputs and exact source paths.

Fresh result: archive confirms 239e's 19-CA transfer coverage is complete, with **two** active signed successful token trading positions (我踏马来了 6 transactions and 龙虾 21 transactions), plus a **牛来** inbound-only ERC20 transfer from external sender/contract in block 116507952, for which wallet native BNB balance did not move, and original sender is unresolved due truncated RPC. It is not proven a self-directed purchase. No MARSCOIN CA transfer is observed. Four venue reference cases occur at/after the wallet's first observed signed token trade approximately: IFML, 龙虾, MARSCOIN, 牛来. Do not charge the wallet for missed coins before observed wallet trade activity, and do not call this 2/4 a global success rate. Source: `BSC_MEME_239E_19_CA_ELIGIBLE_OPPORTUNITY_COVERAGE_2026-10-11.json`.

**Full owner episode checks, hard chain evidence vs scenario**:
- 8e6b token **4**: original exact BNB/WBNB 19/19 reconciliation grouped into two complete inventory episodes: original first -0.1179774261901525 BNB and original second +13.28296487979322 BNB; sum +13.164987453603066615 BNB. See `BSC_MEME_8E6B_4_ORIGINAL_TWO_EPISODE_EXACT_SETTLEMENT_2026-10-11.json`.
- 239e **龙虾**: six complete inventory episodes of token-associated wallet native BNB block changes; first +0.196173568640778761 BNB, next five aggregate +0.002952024852556383 BNB, sum +0.199125593493335144 BNB. These are scoped wallet native balance movements, not fully isolated multi-asset PnL. See `BSC_MEME_239E_ORIGINAL_LATE_EPISODE_NATIVE_CASHFLOW_CHECK_2026-10-11.json`.
- 239e **我踏马来了**: one complete observed inventory episode with +0.097366720524376562 BNB native token-block change, not independently proved final total realized profit.

Frozen V1 research replay uses **46** owner-signed successful original tx (8e6b 4: 2 buys/17 sells; 239e IFML 1 buy/5 sells; 239e 龙虾 7 buys/14 sells), post-signal original-block+1+{0,10} delay, fixed 0.05 or 0.1 BNB **per owner buy**, fraction-of-original-inventory proportional exit, hypothetical initial 1 BNB cash account, zero-fee and hypothetical 25bps swap +0.0005 BNB/action stress variants. All **92/92** pool reserve snapshots valid, **24/24** scenario trade ledgers preserved, **368/368** expected individual simulated trade actions independently reconstructed with exact integer math and zero arithmetical failures, all simulated inventories closed. QA has 5 fixed-Gas amortization size warnings, retained explicitly; original commit subject incorrectly said 1104 checks and was corrected inside QA source to actual 368.

Representative lag-10, hypothetical 0.05 BNB per owner buy with 25bps+fixed-Gas stress: 8e6b 4 +1.324428 BNB net after **0.10 BNB cumulative buys**; 239e IFML +0.118552 BNB after **0.05 BNB cumulative buys**; 239e 龙虾 +0.430373 BNB after **0.35 BNB cumulative buys**. These numbers are **hypothetical selected historical reserve paths only**. In 龙虾 simulation, first modeled round +0.434181 BNB while later five net slightly negative. In actual first 4 trade episode first-round BNB realized net is negative. Read `BSC_MEME_FOLLOW_V1_EPISODE_PROFIT_CONCENTRATION_2026-10-11.json`.

**Guardrail**: historical pair states are exogenous; follower swaps do NOT alter subsequent source reserves; actual onchain buy/sell routing, gas, transfer taxes, MEV, accessible quotes, other losing wallets, market denominator, and independent control-cluster inference remain unresolved. This is an in-sample what-if model, **NOT executable backtesting or proof of copyable profit**. No external AI review, untouched holdout or production trial. No user requests to activate monitoring, and no new tasks/alerts were created. `OBSERVE_ONLY / NO_GO` remains unchanged.

Next useful step: cross-check independent 9d1240 early material-event wallet vs 239e, then build out an opportunity-aware wide comparison and real route/fee historical executable replay without changing V0/V1 known outcomes.

## 2026-10-11 address modeling 3: 5C48 two-venue original settlement and independent third-token control

**Read the complete source-backed report first:** `BSC_MEME_ADDRESS_MODEL_3_5C48_THREE_COIN_AND_FOUR_EOA_RESEARCH_REPORT_2026-10-11.md`.

- The 5C48 wallet `0x5c48a7c2113aa044d9c1381588b9c7b3c352387c` has 22/22 self-signed successful source transactions across 我踏马来了 (13) and 龙虾 (9), all two-token position inventories closed. Exact native wallet block-before/after reads for 22/22 give +1.684349807479692629 and +1.292735581066750132 BNB, sum +2.977085388546442761 BNB. Six token-inventory turnover episodes are positive in this narrowly selected scope. Total original source transaction native buy inputs = 3.8 BNB, not necessarily peak simultaneous capital.
- Fixed settlement evidence before any new quote queries, then query raw historical Four.meme Manager2 / Pancake V2 pool events: 12 Manager2 transfers (11 original event matches; one Lobster sell original hash `0x4ad7226b748a5e227bd759bfd477e9eaab4b9b27546193718136d432088dde6e` truncated), ten V2 transfers (three direct swap logs, seven exact hash WBNB pool/router transfer fallbacks). The dense Lobster V2 85952169 buy needed six pages at two items/page to avoid an upstream 8KB response truncation; full direct Swap log is still not read. Three V2 buy pool quote inputs equal 99% owner native value, all ten V2 moves have integer gasUsed-compatible after a hypothesized 1% router deduction, with no available independent receipt gas contradictions. Do not claim independently verified full 1% fee trace or sell PnL.
- **Anti-survivorship update:** Independently examined its third matched major CA, 币安人生 (`0x924fa68a0fc644485b8df8abfa0a41c2e7744444`). Fully paginated 17 native transaction hash / 17 wallet BNB block balance records, 17/17 original self-signed successful receipts; summed native BNB block scope `-100375396591269389` wei. Cumulative native tx input 3.8 BNB. All 17 include an inbound token transfer and ten also an equal-value token outgoing in **the same tx**; these ten pairs must not be counted as separate buy/sell signals. Raw token net residual `247691` smallest units, no independently verified price, precise native route classification remains unresolved.
- Consequently 5C48 **three** selected CA / 39 signed success / 39 native-event-block scope total is `2876709991955173372` wei (+2.876709991955173372 BNB) on 7.6 BNB cumulative source native tx input. The +37.8514% quotient is a research-only scoped cashflow ratio, **not real portfolio ROI**, and the raw third token residue must not be treated as zero just because tiny.
- Four-wallet restricted two-CA comparator for 5C48 / DDAC / 9D1240 / 239E is in `BSC_MEME_FOUR_EOA_IFML_LOBSTER_CAPITAL_AND_EPISODE_COMPARISON_2026-10-11.json`. Across all **19 historically selected token CAs**, the 4×19 cell matrix `BSC_MEME_FOUR_WALLETS_19_CA_BREADTH_AND_EVIDENCE_GAPS_2026-10-11.json` documents exactly which CA has signed transaction evidence, passive/unverified ERC20 observations and no ERC20 transfers. Matrix selection is retrospective, and the verified wallet operational lifetime is not an opportunity denominator; never report winner hit rate over 19.
- Historical original receipt status vs replay state is carefully graded. No tested profitable copy model, out-of-sample validation, external AI independent review, orders, alerts or monitoring activation. **OBSERVE_ONLY / NO_GO** remains unchanged.

**Next research queue:** investigate DDAC's extra MARSCOIN, GIGGLE and 币安人生 records (including potential losses, provenance and source-native balance), 9D1240 币安人生, and 239E 牛来 passive receipt; then freeze an independent full opportunity/date universe before drawing address rankings. Retain unresolved original Manager2 event and route accounting in existing files.
