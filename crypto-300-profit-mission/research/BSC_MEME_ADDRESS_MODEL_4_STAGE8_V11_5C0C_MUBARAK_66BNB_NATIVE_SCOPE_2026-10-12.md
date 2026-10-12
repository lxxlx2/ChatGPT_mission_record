# BSC Address Model 4 — Stage 8: 18/23 complete wallet ledgers; 5c0c MUBARAK signed 12-transaction native scope

Research as of 2026-10-12, BNB Chain. Frozen denominator: 23 EOA candidates × 19 canonical token contracts (437 wallet/CA cells). **PRODUCTION NO_GO; OBSERVE_ONLY; NO AUTOMATIONS/EXECUTION.**

## Answer-first coverage

Stage 8 V11 increases full-source coverage to **18/23 wallets**, **387/437** CA histories cursor-exhausted, **50** unfinished known-positive-transfer cells, **0** presence-unknown cells. Across the frozen sample, 148 wallet/CA combinations have positive ERC20 transfers; 289 have no nonzero ERC20 events after full cursor query; 56 *token quantities* are closed. None of these equate to a realized winning trade or missed opportunity.

Newly completed wallet `0x5c0c5d788661dde7437842fb7f0bbff7f1607583` is now **19/19**, after individually cursor-exhausting both directions on its last five tokens and independently checking exact integer `balanceOf(wallet) = sum(token in) - sum(token out)`:

| Token | Complete in ERC20 logs | Complete out ERC20 logs | Raw token remainder |
| --- | ---: | ---: | ---: |
| BROCCOLIF3B | 45 | 29 | 1 |
| TUT | 30 | 7 | 0 |
| CHEEMS | 11 | 2 | 0 |
| MUBARAK | 14 | 21 | 0 |
| BROCCOLI714 | 34 | 61 | 1 |

**Raw balance 1 means the smallest contract integer unit, not one whole displayed token.** Multiple ERC20 tax/fee logs can share an original transaction: 14 MUBARAK inbound logs represent just 5 owner-original transactions; 21 outbound logs represent 7 original transactions. Never use ERC20 log counts as buy/sell counts.

## MUBARAK — large-capital owner trade provenance and exact block-native financial scope

Canonical MUBARAK CA `0x5c85d6c6825ab4032337f11ee92a72df936b46f6`. First original self-signed buy occurred at block **47460891**, **18742 blocks after the frozen earliest sampled Pancake V2 pool event** at block 47442149. This is a sample-based timeline comparison, **not** a verified launch or first-tradable time.

Five original wallet-signed buy transactions have direct `ethGetTransactionByHash` evidence for native transaction values **39 BNB + 2 BNB + 10 BNB + 10 BNB + 8 BNB = 69 BNB** total. Four large-caldadata outgoing `ethGetTransactionByHash` responses truncated before `from`; these originators were independently proven wallet-signed via `getAssetTransfers(category=['external'], fromAddress=wallet, excludeZeroValue=false)` on each exact transaction block. The remaining three outgoings were directly signed by the wallet. **All 12 of 12** inbound/outbound token-transaction hashes are wallet-origin signed, and each of the twelve blocks has exactly **one** original native external wallet-origin transaction in the direct filtered scan.

| Financial quantity, historical BNB balance at block N minus N−1 | Exact result |
| --- | ---: |
| Owner buy transactions | 5 |
| Original buy transactions native `msg.value` | 69.000000000000000000 BNB |
| Sum of 5 owner buy blocks' wallet native BNB deltas | **-69.001930306324410814 BNB** |
| Owner-origin token outgoing transactions | 7 |
| Sum of 7 token-outgoing blocks' wallet native BNB deltas | **+135.381593517675978407 BNB** |
| Net native wallet BNB delta across these 12 specific blocks | **+66.379663211351567593 BNB** |
| Net as % of native input-side block outflow (diagnostic only) | 96.1997% |
| MUBARAK quantity remaining | 0 raw units |
| Final realized economic PnL | **UNVERIFIED — NOT the +66.38 BNB figure** |

Of seven outflow blocks, **five had a positive native BNB change**. The other two were direct ERC20 transfer-selector token sends and correspond to small negative native BNB changes. For each of the five positive-native outflow blocks: direct checks found **no wallet ERC20 Transfer in/out of WBNB, USDT, USDC or BUSD**, and **no other external direct BNB transfer to the wallet** in that block. Internal router BNB receipts are not enumerated by the current free-tier provider. This increases confidence that MUBARAK is a genuine large positive native scope but **does not independently prove causal profit attribution or all alternative quote/counterparty inflows**.

### Economic truth gates — do not skip

- Zero *token* inventory does **not** mean all seven outgoing transactions were market sells: the last two are wallet-signed ERC20 `transfer` calls. Distribution to another address can close quantity without cash proceeds.
- Blockchain native balance `N-1→N` includes all effects on a wallet in that block. Even one source-signed external transaction does not exclude unsolicited or internal receipts; internal BSC traces are unavailable under the connected free-tier API.
- For high-volume route calls full receipts may truncate at ~8kB and independently exposed `gasUsed` was not confirmed. The exact block delta includes any gas but does not isolate it.
- Only the named WBNB/USDT/USDC/BUSD wallet quote transfers were checked and ruled out on five positive sale blocks. Other quote tokens, intermediary paths, source-wallet funding and all 19-CA per-transaction economic effects require deeper reconstruction before official realized PnL.
- Position capital was **69 BNB**, much larger than a small-copy-trade bankroll. Observing a whale's scope does not prove performance at a $300 entry size or pre-signal follower latency.

### Cross-token active-trader controls

In the five newly completed token CAs, first inbound/outbound origin transaction signer checks total **10 original transactions**, of which **7 wallet signed**, **1 from a different EOA** (BROCCOLI714 first incoming ERC20 transfer), and **2 initially unreadable from long calldata** (CHEEMS first incoming; MUBARAK first outgoing). The MUBARAK first outgoing was subsequently resolved through an original external zero-native-value wallet-origin check, and all other MUBARAK original transactions were individually audited. CHEEMS first *outbound* original transaction was a wallet-signed plain ERC20 `transfer`, not a proven DEX sale. A self-signed zero-native-value trade may spend WBNB or other quote tokens rather than be free.

The Stage 8 MUBARAK candidate is **PRIORITY_FOR_FULL_PNL_CAUSAL_AUDIT**, not **VERIFIED_FOLLOWABLE_PROFIT**. Continue expanding other five remaining incomplete wallets; frozen major-opportunity denominator, original owner-signature evidence for all major tokens, missed eligible events, adverse outcomes and an independently reviewed delayed-entry simulation are still required.

## Immutable source evidence

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V11_2026-10-12.json` (blob `3c700f19120306dd48ac9574baeca9b22b9b6afa`)
- `BSC_MEME_5C0C_MUBARAK_ALL12_OWNER_SIGNED_66BNB_NATIVE_SCOPE_AUDIT_2026-10-12.json` (blob `3bfcb838a2222dd470fc99171e991e82f2bf4037`)
- `BSC_MEME_5C0C_FIVE_CA_FIRST_OWNER_SIGNER_AND_MUBARAK_39BNB_QA_2026-10-12.json` (blob `3a2c20d8b724dd9f6d34491873617f294e55fdd5`)
- `BSC_MEME_BREADTH_FIRST_CANDIDATE_QUEUE_2026-10-10.json` (blob `f8297b7d76f9040a85254cc9cfacf9a8a8220c1f`)
- `BSC_MEME_5C0C_BROCCOLIF3B_FULL_ERC20_BALANCE_CENSUS_2026-10-12.json`
- `BSC_MEME_5C0C_TUT_FULL_ERC20_BALANCE_CENSUS_2026-10-12.json`
- `BSC_MEME_5C0C_CHEEMS_FULL_ERC20_BALANCE_CENSUS_2026-10-12.json`
- `BSC_MEME_5C0C_MUBARAK_FULL_ERC20_BALANCE_CENSUS_2026-10-12.json`
- `BSC_MEME_5C0C_BROCCOLI714_FULL_ERC20_BALANCE_CENSUS_2026-10-12.json`

All changes are original-chain read-only research and Git evidence. **NO_GO.**
