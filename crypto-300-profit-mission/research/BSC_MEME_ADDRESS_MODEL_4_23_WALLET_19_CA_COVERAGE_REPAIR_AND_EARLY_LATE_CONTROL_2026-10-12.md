# Address Analysis Model 4 | 23x19 audit upgrade and cross-opportunity negative controls

Date: 2026-10-12 (Asia/Bangkok). Scope: **frozen 23 EOA wallets × 19 BSC CA**, direct original BSC ERC20 plus prior archived evidence.  
Status: **HISTORICAL RESEARCH / OBSERVE_ONLY / PRODUCTION_TRADING=NO_GO**.

## Answer-first result

A direct **bidirectional cursor-to-exhaustion re-scan** of two high-priority wallets, `0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0` and `0xddac928a240bdace3994c2cc0783d4e29a002127`, has materially corrected the old 23-wallet / 19-CA matrix. The former now has **13 distinct scoped CA histories with ERC20 events** and the latter **6**. Their full frozen 19-CA both-direction coverage is established by joining the earlier 11/5 fully scanned CA histories with the newly exhausted remaining 8/14 CAs, respectively.

| Snapshot completeness indicator | Old 2026-10-11 baseline / first overlay | New validated V2 |
| --- | ---: | ---: |
| Wallets whose all 19 fixed CAs are fully paginated | 11 | **13** |
| Complete wallet/CA directional coverage cells | 225 | **247 / 437** |
| Complete observed wallet/CA transfer pairs | 48 | **51** |
| Complete no-ERC20-transfer wallet/CA pairs | 177 | **196** |
| Partially observed transfer pairs | 34 | **34** |
| Unread/unobserved and not complete | 178 | **156** |
| Exact quantity-closed pairs, irrespective of trade intent | 32 | **33** |

The **196** completed no-transfer cells are **contract-specific factual absence of ERC20 movements**, not proved opportunities missed. Trader eligibility must be based on original wallet activity date, launch opportunity timing, exact CA and venue availability; these have not been established for all 23.

## Material third-party wallet expansion

| Wallet | Completed 19-CA coverage | CA with historical ERC20 | Quantity-closed CA |
| --- | ---: | ---: | ---: |
| `0x239e…` | 19/19 | 3 | 2 |
| `0x8e6b…` | 19/19 | 13 | 8 |
| `0xccee…` | 19/19 | 5 | 5 |
| `0xddac…` | 19/19 | 6 | 3 |
| `0x5c48…` | 19/19 | 3 | 2 |
| `0x9d12…` | 19/19 | 4 | 4 |

- **8e6b MARSCOIN**: new full cursor 19 in / 29 out original ERC20 logs; exact net `14.730395959988410675` MARS, current contract `balanceOf` agrees. Earliest newly found acquisition in block **112782241** was a **self-signed router trade with original native input 3 BNB**. A sampled outbound was also self-signed. This is an independently proved extra traded major token. **Complete realized net quote PnL for MARS remains unknown**, and unclosed token inventory still exists.
- **8e6b 牛来**: 10 inbound original ERC20 transfers and one original outbound transaction emitting two token transfers, net `65.856455282881733964` 牛来 matching direct contract balance. **All 10 inbound transaction blocks show zero BNB wallet balance movement. Five original inbound transaction signers are confirmed *other* addresses, five unreadable due large calldata. All ten invoke contract `0xeb91d9ed63a060077d51678248ae11dc784ab735`, selector `0x84da2c7b`. No self-signed original acquisition is established.** The single sale/disposal is self-signed, and is not automatically a profitable bought position.
- **DDAC 牛来**: historical 19 in / 4 out ERC20 transfers, **zero net token balance** matching direct `balanceOf`; first sampled buy and exit origin signers are DDAC. Earlier scope audit reported +0.011321909495709853 BNB native-event-block change, **not** independently isolated realized net PnL. It remains a distinct owner-action opportunity beyond the already audited IFML, 龙虾, 币安人生, MARSCOIN and GIGGLE (the latter shared-source receipt dominated).

The new event records contain **83 original ERC20 Transfer logs**, not 83 original wallet-signed trades. Six boundary original-signer probes were attempted: five self signed, one truncated. An additional full check on 8e6b 牛来 classified all 10 incoming transactions as **five other-signed, five unknown**, with **ten zero native-block changes**.

## Event timing controls: cannot use token count as skill

Use known first sampled `FOUR_MEME_PRE_V2` event blocks as dated on-chain comparators, **not a proven first tradable timestamp**:

| Token | Earliest source sampled block | DDAC first source-proven inbound | 8e6b first source-proven inbound |
| --- | ---: | ---: | ---: |
| MARSCOIN | 112441460 | 112441920 (+460) | 112782241 (+340781) |
| 牛来 | 115853707 | 116206278 (+352571) | 116507908 (+654201) |

DDAC's first MARS trade is near the earliest sampled Four.meme window; 8e6b's first confirmed owner-signed MARS transaction is much later in **block-number order**. 8e6b's first 牛来 inbound is an external dispatch-receipt with owner signature **unconfirmed**; it must not be compared as a genuine owner-signed early purchase.

## Four-wallet fixed two-major-token adverse comparator

The independent existing four EOA audit uses exactly **我踏马来了** and **龙虾**, with full original scope BNB balance observations and multiple gas/venue limitations. Numbers below are **native BNB net changes on audited token-event blocks, not final ROI or all-wallet PnL**:

| Wallet | 我踏马来了 BNB scoped | 龙虾 BNB scoped | Original source transaction count |
| --- | ---: | ---: | ---: |
| DDAC | 2.329674 | -0.183543 | 25 |
| 9D1240 | 0.855510 | 1.642367 | 39 |
| 239E | 0.097367 | 0.199126 | 27 |
| 5C48 | 1.684350 | 1.292736 | 22 |

This sample already contains a negative DDAC 龙虾 scope. The independent 8e6b 11-token historical cohort also contains negative IFML and SIREN native event-block scopes despite large positive 4 and MUBARAK scopes; no one-sided winner cherry-picking. In a fixed universe, signed trades, missed eligible opportunities, losses, passive distributions, open inventory, capital size and post-signal follower execution must all be measured consistently.

## Corrected evidence tiers and remaining work

1. **COVERAGE_CONFIRMED:** exactly 13/23 wallets now have complete bidirectional ERC20 census for all frozen 19 CAs. Other 10 wallets and 156 partial-unknown cells retain explicit unread status; do not label missing opportunities or zero positions.
2. **TOKEN_QUANTITY_RECONCILED:** new 8e6b MARS and 牛来 open balances and DDAC 牛来 zero balance all directly match integer inbound-minus-outbound, token decimals=18.
3. **ORIGINAL_OWNER_TRADE_PROVEN:** 8e6b MARS sampled source buy/sell; DDAC 牛来 sampled buy/sell; 8e6b 牛来 inbound NOT proven owner trade.
4. **TRADE_RETURN_UNRESOLVED:** pending full signed-original ledger, gross BNB/WBNB/USDT/SPCXB quote settlements, historical swap tax, gas receipts, internal transfers, overlap of token-event blocks, wallet funding and open-inventory valuation.
5. **FOLLOWABILITY_NO_GO:** do not rank by raw win rate or switch real follow alerts until opportunity-eligible, chronology-frozen controlled simulation, independently reviewed reserve/slippage/delay model and untouched holdout evaluation pass.

Artifacts:
- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V2_2026-10-12.json`
- `BSC_MEME_8E6B_EIGHT_PREVIOUSLY_UNOBSERVED_CA_CURSOR_RESCAN_2026-10-12.json`
- `BSC_MEME_DDAC_FOURTEEN_PREVIOUSLY_UNOBSERVED_CA_CURSOR_RESCAN_2026-10-12.json`
- `BSC_MEME_8E6B_DDAC_MARS_NIULAI_NEW_COHORT_BALANCE_AND_SIGNER_QA_2026-10-12.json`
- `BSC_MEME_8E6B_NIULAI_TEN_CONTRACT_DISTRIBUTIONS_VS_OWNER_EXIT_QA_2026-10-12.json`

No notification, scanner, local deployment, trading threshold, or automation was modified. **PRODUCTION_TRADING=NO_GO**.
