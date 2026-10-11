# Address Analysis 3 | DDAC three additional token histories and venue-level attribution

Date: 2026-10-11, timezone Asia/Bangkok. Status: **RESEARCH ONLY, OBSERVE_ONLY / NO_GO**.

## Why the prior ranking cannot be reused without correction

An earlier first-depth 23-wallet/19-CA matrix missed large parts of the DDAC wallet's actual historical ERC20 events. Full pagination on the same canonical contract addresses materially corrected three cells:

| Token | Old matrix in / out | Full cursor in / out | Unique tx hashes | Evidence status |
| --- | ---: | ---: | ---: | --- |
| MARSCOIN | 0 / 19 | 17 / 23 | 29 | 18 owner-signed pool trades, 10 non-trade receipts, 1 owner non-pool receipt |
| GIGGLE Fund | 11 / 0 | 71 / 0 | 71 | Inbound-only, no original wallet sale established |
| 币安人生 | 17 / 5 | 78 / 5 | 82 | 7 wallet-signed original V2 pool actions; 69 contract-sourced token receipts |

The old matrix is a dated historical snapshot. The derived `BSC_MEME_FOUR_WALLETS_19_CA_BREADTH_AND_EVIDENCE_GAPS_2026-10-11.json` has been updated with the previous and new counts. Do not infer win rate or buy count from ERC20 incoming log count.

## MARSCOIN: actual venue and route investigation

Token contract `0xfe189e97832da1573e4e4ff034f4ffc3a15c7777`, 18 decimals verified by current original eth_call. Full 29 hash MARS token transfer pagination and 29/29 owner-native BNB balance before/after-block readings: +3.409712195316107766 BNB net native-block movement. Raw token residual 3050660512775076744 (3.050660512775076744 MARS); balanceOf on current chain state matches exactly.

29 unique tx hashes grouped in chronological order without negative running token balance. Original tx signer evidence: 19 DDAC, 4 other, 6 unknown due 8KB RPC input truncation. 18 explicit 0x1 receipt status; 11 independent receipt status fields unavailable. All 10 other/unknown-signer token-receipt blocks have exactly zero wallet BNB net change. The 19 wallet-signed transactions contain 6 pool buys, 12 pool sells and one unrelated nonpool token receipt, with a sum of 2.85 BNB in original native transaction input. Those exact event-block gains alone cannot be called independently validated realized token profits without final router tracing.

Onchain token0/token1 calls identify **SPCXB/MARS V2 pool** `0x94f3ed36706c746ad59fadcaf271b7431ab1d8f1` and **USDT/MARS V3 pool** `0x4a4bea953813c118c260be9a26b2321e57aa62e5` (V3 fee selector returns 10000 = 1% tier). The 18 owner pool actions consist of 16 SPCXB-V2 and two USDT-V3 transactions. Of those: 14/14 readable V2 direct same-hash Swap logs show **exactly 3% token-transfer quantity decrease** each buy/sell leg, two V2 swap logs remain truncated but matching transaction SPCXB ERC20 pool receipts/payouts were recovered, and both USDT-V3 swaps are independently decoded in their seven-word event with **zero MARS token transfer quantity loss on these two events**. Never apply 3% globally across all venues. Intermediate quote assets SPCXB and USDT cannot be merged into BNB quote without a supported historical multi-hop original settlement trace.

Proof file: `BSC_MEME_DDAC_MARSCOIN_18_POOL_TRADE_V2_V3_TAX_AND_QUOTE_RECONCILIATION_2026-10-11.json`; original 29 hashes and audit in `BSC_MEME_DDAC_MARSCOIN_29_EVENT_PROVENANCE_AND_NATIVE_SCOPE_QA_2026-10-11.json`.

## GIGGLE: passive/token-distribution control

Canonical GIGGLE Fund contract `0x20d6015660b3fe52e6690a889b5c51f69902ce0e`. Complete pagination yielded **71 incoming, zero outgoing** original ERC20 transfer logs, 70 incoming from distributor/source `0x2f7fe96e3d0308cdbf6143e7dc0bb05df73a4a83`, one from another address, verified full net token raw holdings `1887709367246662512`, corresponding to 1.887709367246662512 GIGGLE. Current onchain balanceOf agrees. Three native wallet block delta samples are zero, two original tx responses truncated and one explicitly other-signed. No original independent GIGGLE buy or realized exit established; do not use 71 incoming transfers as successful buys. Provenance file `BSC_MEME_DDAC_GIGGLE_71_PASSIVE_OR_REWARD_INBOUND_CONTROL_2026-10-11.json`.

## Binance Life: separate genuine pool actions from distributor transfers

Canonical contract `0x924fa68a0fc644485b8df8abfa0a41c2e7744444`. Fully paginated 78 inbound and 5 outbound ERC20 records across 82 distinct tx hashes, including one hash with both incoming/outgoing events. Raw token inventory net and current eth_call balanceOf **21665763559661594798** (21.665763559661594798 tokens), still open.

**69 token receipts** came from the same `0x2f7fe96…` source contract as 70 of the GIGGLE receipts, but did not occur in the exact same transaction hashes. Do not assume identical cause or owner signature without full per-transaction evidence.

`0x66f289de31eef70d52186729d2637ac978cfc56b` is Binance Life/WBNB V2 pair (token0 Meme, token1 WBNB confirmed onchain). **7 pair-associated wallet-signed original transactions**: 3 buys, 4 sells, with 6 complete same-hash V2 Swap matches and one exact-hash WBNB router-to-pair transfer fallback. Native wallet BNB changes on these 7 blocks sum to **+0.462620236646267526 BNB**. All 3 buy WBNB pool deposits are exactly 99% original native inputs. All 7 movements match integer gasUsed from original gasPrice under the modeled 1% router deduction within original gas limits, but independent detailed gasUsed receipt fields are not comprehensively reverified. The 6 direct swaps show exact matched token quantities, unlike the 3% taxed MARS SPCXB-V2 path. The remaining 75 Binance Life hashes are not declared owner buys or sales.

Proof file: `BSC_MEME_DDAC_BINANCE_LIFE_82_TX_DISTRIBUTION_VS_7_POOL_SETTLEMENT_QA_2026-10-11.json`.

## Decision

- The 5C48, DDAC, 9D1240 and 239E earlier two-token ranking remains **restricted historical evidence**. DDAC has additional materially positive MARS native-block cashflow and a smaller positive Binance Life pool scope, but larger total histories and passive receipts; full independent realized PnL and wallet-control independence are not yet established.
- Neither an address's large inbound token-transfer count nor the presence of a large positive isolated native-block delta is sufficient to label a skilled active trader. Distinguish owner-signed trade, partner-signed distribution, in-transaction token churn, venue tax, receipt gas, open inventory and hindsight sample bias.
- Next high-value work: complete DDAC's other quote receipts, check 9D1240 extra Binance Life source, 239E NiuLai passive transfer, re-scan 23×19 fixed history with pagination and proof tiers, then freeze an untouched date/universe market opportunity validation with independent AI review before any production consideration.

No real trades, notifications, recurring tasks, local deployments or monitoring rules were created or modified. **PRODUCTION_TRADING = NO_GO**.
