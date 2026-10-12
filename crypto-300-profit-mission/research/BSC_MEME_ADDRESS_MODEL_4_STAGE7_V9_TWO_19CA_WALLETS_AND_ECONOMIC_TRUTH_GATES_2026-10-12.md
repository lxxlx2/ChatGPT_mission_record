# BSC Address Model 4 — Stage 7 | Fully reconstructed 498528 and 877AF token histories

Date: 2026-10-12, timezone Asia/Bangkok. Chain: BNB mainnet. Universe frozen: 23 candidate EOAs × 19 exact token CAs. `OBSERVE_ONLY / PRODUCTION_TRADING=NO_GO`.

## Executive result

**16 / 23** wallets now have complete ERC20 histories in both directions for the frozen 19 CAs; **381 / 437** wallet×token cells are complete, and **56** remain high-traffic positive-transfer cells without exhausted historical cursors. The presence/absence of positive-value ERC20 transfers is independently classified at all 437 cells, but **none of these counts is a realized win rate or owner-trade count**.

Previous V8 evidence remains intact; V9 adds four complete token histories to `0x8d8c031fd095b15f6e7ce1b27c1318015723ae25`: 牛来, 哈基米, 币安人生, 龙虾. All four have exactly zero current raw token quantity and `balanceOf` matches full `incoming - outgoing` transfers. **MARSCOIN remains incomplete** for that wallet: incoming direction fully paginated (14 logs), outgoing direction already has at least **162** logged transfers after separately checkpointed source+continuations, but still has an unread cursor. This wallet stays at **18 / 19**, not 19 / 19.

## Two full-coverage high-priority MARSCOIN addresses

| Wallet / contract-scope metric | `0x498528e3…` | `0x877af245…` |
| --- | ---: | ---: |
| First proven original wallet-signed MARS entry | block 112441470 | block 112441460 |
| ERC20 MARS inbound Transfer logs | **76** | **73** |
| Unique inbound original transaction hashes | **76** | **73** |
| ERC20 MARS outgoing Transfer logs | **170** | **97** |
| Unique outgoing original transaction hashes | **89** | **50** |
| Exact token net raw units | `0` | `68700271596483656647` |
| Direct onchain balanceOf matches net? | YES | YES |
| Both complete ERC20 direction cursors? | YES | YES |
| Final owner trading PnL? | **UNVERIFIED** | **UNVERIFIED** |

Both are now **19/19 canonical token-CA full-ledger wallets**. `498528` closed its entire MARS token quantity, and independently closed NIULAI quantity; those are **token-balance closures**, not profit. `877af` also closed Lobster and HAJIMI raw balances, but still holds a nonzero MARS token remainder and nonzero NIULAI, 币安人生, TUT raw quantities.

Additional full-history BSC-source results:

- `877af` 牛来: 124 inward ERC20 logs, 115 outward logs, net raw `138878417262324072549` equals direct `balanceOf`.
- `877af` 龙虾: 125 inward ERC20 logs, 124 outward logs, net raw **0** equals direct `balanceOf`.
- `877af` 哈基米: 3 inward, 3 outward; net 0.
- `877af` 币安人生: 47 inward, 21 outward; net raw `17242288439229428163`.
- `877af` TUT: 35 inward, 18 outward; net raw `19942830750055696512`.
- `498528` NIULAI: 30 inward, 32 outward; net raw 0; TUT 3/1 and 币安人生 2/0, both nonzero net.

### Original transaction-origin control

Twelve evenly distributed (first, chronology-median, last; separate in and out) original MARS transactions were independently queried. **11** have the sampled wallet as `eth_getTransactionByHash.from`. **One** inbound receipt at `498528` is **not** original wallet signed: transaction `0x5a892f6cf9dd394e1d3f78bb12d7f5a6bbec4414f587a81079ddecc10fc9c6e1` was signed by `0x679d8a9a2bb243ca42d0c3a7a49d46203b5a0632` and sent to dispatch contract `0xeb91d9ed63a060077d51678248ae11dc784ab735` (`0x84da2c7b`, native input zero). Therefore **do not treat 76 incoming MARS transaction hashes as 76 original wallet-signed buys**.

The last outgoing MARS `498528` transaction, `0x49748cf3ec185c54bc3b46dc4bb6c92e225d2bcbf0a1aadf1a49c0fb093f53ca`, was wallet signed but routed via a different target `0x5994814f2c4040b863a0125a45de152a8c2a4dec` selector `0x0c307f76`. The historical native wallet balance change from block 123506148 to 123506149 was `+3077368798990424` wei (0.003077368798990424 BNB). Direct ERC20 Transfer queries found no wallet-directed WBNB, USDT or SPCXB records for that transaction in that block; this **does not** exclude other quote tokens or other same-block wallet transactions and must not be treated as isolated sale PnL.

### Historical pagination audit

An old Alchemy `pageKey` saved across independent research sessions was observed to restart from earlier blocks. To prevent silent duplications or omissions, new source continuation was regenerated from the last archived block **inclusive**, using fresh within-request cursor chains and strict ERC20 `uniqueId` deduplication. Each completed contract history was independently tested by `sum(raw inbound)-sum(raw outbound) == latest token.balanceOf(wallet)`. The named source files retain all original transaction hashes and chain block indices.

### BSC native settlement limitation

Alchemy `getAssetTransfers(category=['internal'])` reports this category unsupported on BNB mainnet. Full large transaction receipts from `ethGetTransactionReceipt` were returned truncated at about 8KB and did not expose independently auditable `gasUsed` for the checked examples. Consequently **full native proceeds, per-order gas, router fees, quote-asset allocation, overlapping transactions and realized BNB profit remain unverified**, even for closed-quantity token positions. An arithmetic inference from a historic balance delta is not an independent receipt gasUsed measurement.

## Remaining wallet×token full-ledger gaps

| Incomplete wallet | Finished exact-CA histories | Still open active CA histories | Open token names |
| --- | ---: | ---: | --- |
| `0x2adf961b…` | 8/19 | 11 | TUT、BOB、4、GIGGLE、币安人生、我踏马来了、龙虾、牛来、MARSCOIN、哈基米 / HAJIMI、BUBB |
| `0xadffbebb…` | 10/19 | 9 | CHEEMS、BROCCOLI714、GIGGLE、币安人生、我踏马来了、龙虾、牛来、MARSCOIN、哈基米 / HAJIMI |
| `0x5c0c5d78…` | 14/19 | 5 | CHEEMS、MUBARAK、TUT、BROCCOLI714、BROCCOLIF3B |
| `0x11a73279…` | 12/19 | 7 | TST、MUBARAK、TUT、BROCCOLI714、BROCCOLIF3B、BOB、GIGGLE |
| `0xa83b73f5…` | 4/19 | 15 | TST、CHEEMS、TUT、BROCCOLI714、SIREN、BANANAS31、BOB、4、GIGGLE、币安人生、我踏马来了、龙虾、牛来、MARSCOIN、哈基米 / HAJIMI |
| `0x0abb84c9…` | 11/19 | 8 | TUT、GIGGLE、币安人生、我踏马来了、龙虾、牛来、MARSCOIN、哈基米 / HAJIMI |
| `0x8d8c031f…` | 18/19 | 1 | MARSCOIN |

Research priority is breadth-first completion of missing high-volume CAs, with adverse and missed eligible opportunities retained. Parallel original-signature classification and quote/gas-ledger replay can only be promoted after a reproducible independent holdout. No release, local deployment, trading switch, automated alert or follow-wallet recommendation follows from this report. **NO_GO**.

## Re-readable authoritative sources

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V9_2026-10-12.json` — Git blob `c9f9247f3575453a98077097f208a50f3eeaed99`
- `BSC_MEME_498528_MARS_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json` — Git blob `b759fb0b8e9a51ee568e3af3325994ab1939a436`
- `BSC_MEME_877AF_MARS_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json` — Git blob `8ccb13babfefb726a3a6a44ea5b766ce3628dd28`
- `BSC_MEME_877AF_NIULAI_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json` — Git blob `9e08209bc777e72f3601883ef41c5e13893dda83`
- `BSC_MEME_877AF_LOBSTER_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json` — Git blob `b0015481834a69d34435d0fef04c3586b5a8aa50`
- `BSC_MEME_498528_877AF_MARS_SOURCE_SIGNER_SPOT_CHECKS_2026-10-12.json` — Git blob `82d178cf4cc488dad16a4bc2aa6f5d8af695886c`
- `BSC_MEME_8D8C_MARSCOIN_OUT_ANCHORED_C_2026-10-12.json` — Git blob `3547fdcfb00ce546eefcfd1e795cb08fe042f741`
- `BSC_MEME_498528_TUT_LIFE_SINGLE_CA_FULL_CURSORS_2026-10-12.json`
- `BSC_MEME_498528_NIULAI_SINGLE_CA_FULL_CURSORS_2026-10-12.json`
- `BSC_MEME_877AF_HAJIMI_SINGLE_CA_FULL_CURSORS_2026-10-12.json`
- `BSC_MEME_877AF_BINANCE_LIFE_CURSOR_A_2026-10-12.json`
- `BSC_MEME_877AF_TUT_SINGLE_CA_CURSORS_2026-10-12.json`
- `BSC_MEME_8D8C_NIULAI_FULL_CENSUS_2026-10-12.json`
- `BSC_MEME_8D8C_HAJIMI_FULL_CENSUS_2026-10-12.json`
- `BSC_MEME_8D8C_BINANCE_LIFE_FULL_CENSUS_2026-10-12.json`
- `BSC_MEME_8D8C_LOBSTER_CENSUS_2026-10-12.json`
