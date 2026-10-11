# BSC address modeling 3: four-wallet proof and third-token negative control

Date: 2026-10-11 (Asia/Bangkok). Status: `RESEARCH_ONLY / OBSERVE_ONLY / PRODUCTION_TRADING=NO_GO`.

## Decision-relevant findings

**1. 5C48 has now been audited on three rather than only two hand-picked major BSC token contracts.** On 我踏马来了 and 龙虾, 22/22 self-signed successful original transactions, exact ERC20 inventory closure, 22/22 wallet-native BNB block reads, six owner-inventory episodes all positive. They sum to +2.977085388546443 BNB block-native scope on 3.8 BNB total original source transaction input. **On 币安人生, 17/17 additional original transactions are likewise self-signed successful, with 17/17 native block reads and -0.10037539659126939 BNB summed scope on 3.8 BNB original source inputs.** Across these 39 selected original trades, three token CAs, native-block scope sums to +2.8767099919551735 BNB over 7.6 BNB of cumulative native transaction input. The quotient +37.8514% is strictly a scope-normalized cashflow ratio, **not realized portfolio ROI**.

**2. Binance Life's ERC20 transfers require a different interpretation.** Original address-token transfer history has 17 incoming and 10 outgoing transfers but only 17 transaction hashes. In **10 same-transaction pairs**, manager-to-wallet token receipt is matched by an equal wallet-to-0x66f289… token transfer. The net quantity across all inputs and outputs is exactly 247691 *raw units*, not zero. Seven owner-signed transactions carried a nonzero native input and ten did not. Do not count 17 inbound ERC20 logs as 17 standalone buys; do not certify all inventory closed or claim remaining dust USD value without contract decimal/price proof. The native-block result can coexist with route churn or co-block cashflows. Router quotes and fees remain unresolved for this token.

**3. Two-venue original route attribution in the IFML/Lobster scope is mostly complete.** All 22 receipts self-signed successful, 12 pre-migration Four.meme Manager2 flows and 10 PancakeSwap V2 flows. Of 12 Manager2, 11 original cost/fee event logs were directly matched; one original 龙虾 sell (block 83636094, tx `0x4ad7226b748a5e227bd759bfd477e9eaab4b9b27546193718136d432088dde6e`) remains unreadable due upstream 8KB log truncation. Of 10 V2 trades, three exact pair Swap event logs and seven exact transaction-matched pool/router WBNB ERC20 transfers support pool-side gross quote amounts; the seventh transfer required pagination six small pages because bulk query truncated. All three V2 buys put exactly 99% of the original transaction's BNB into the matched pool quote, and all ten V2 trades are consistent with a 1% routing deduction assumption on applicable leg and a positive integer gasUsed within the transaction gas limit. This is **fee arithmetic corroboration**, not standalone proof of actual per-tx receipt gas or every internal transfer. Five Manager2 buys retain ~1% input-cost-minus-base-fee residual whose final routing attribution needs tracing.

**4. Four wallet comparison remains highly in-sample.** Two selected contract CA only, cumulative original native buy amount versus scoped native wallet block delta:

| EOA | Cumulative source native buy value | Native block delta on IFML+Lobster | Delta divided by gross native buy inputs |
|---|---:|---:|---:|
| DDAC | 7.3000 BNB | +2.146131 BNB | 29.40% |
| 9D1240 | 0.6500 BNB | +2.497877 BNB | 384.29% |
| 239E | 0.8575 BNB | +0.296492 BNB | 34.58% |
| 5C48 | 3.8000 BNB | +2.977085 BNB | 78.34% |

This cannot establish risk-adjusted or capital-efficiency ranking in the full market. DDAC has two negative original 龙虾 rounds; 5C48's negative Binance Life broadening control shows the original six all-positive rounds must not be generalized. Wallet ownership/control overlap also remains unverified.

**5. Full selected reference-denominator evidence stored.** The existing **23-wallet x 19 historical CA matrix** now has a derived **4 EOA x 19 CA** 76-cell coverage/evidence-grade expansion, separating confirmed self-signed transaction research from passive/unverified ERC20 records and zero ERC20 observations. Counts of matched CA: DDAC 5 (only two fully signed research cohorts), 9D1240 4 (three cohorts with signed provenance), 5C48 3 (three signed original provenance), 239E 3 (two signed active cohorts, 牛来 inbound-only unresolved). None yields a general 'wins / 19 opportunities' statistic, because many historical samples precede wallets' verified activity window and market-wide opportunity selection is retrospective.

## Method and independent QA

- Historical BNB data: read wallet native balance at block N-1 and N for each known owner token event, using the existing read-only BSC RPC. Confirm original `eth_getTransactionByHash.from` and status=0x1 in the receipt; preserve if receipt gas details are truncated.
- For quote attribution, decode exact original Manager2 token-purchase/token-sale events when possible. For Pancake V2, decode original pair Swap logs; on oversized dense blocks, query the exact WBNB ERC20 pair/router transfer filtered by source/destination, block and transaction hash with bounded pagination. These fallbacks are independently labeled lower-tier evidence, not silently upgraded into full Swap logs.
- Reconcile native block deltas, gross owner native input, quoted pool WBNB, potential 1% router fee, hypothetical implied gasUsed and independent available receipt gas. Preserve all failures or gaps.
- Quoted cumulative native source inputs reflect **repeat transaction values**, not maximum simultaneous capital. Native N-1/N block delta is not isolated lifetime token PnL or a verified reproducible follower fill.

## Important open work

1. Audit DDAC's other source-covered coins (GIGGLE, MARSCOIN, 币安人生), especially any negative or unclosed positions, before ranking wallet skill.
2. Audit 9D1240's 币安人生 and 239E's unverified 牛来 inbound without fabricating active buys.
3. Resolve truncated Manager2 sell and Binance Life internal route settlement using supported original trace/receipt or a source preserving individual logs; if unavailable keep them UNRESOLVED.
4. Design unbiased chronology-based opportunity coverage beyond the 19 hindsight-selected CA, wallet alive-window checks, negative/no-trade outcomes, historical executable quote and fee checks, untouched dates and independent external reviewer. No production trial or new monitoring tasks without explicit authorization.

## Canonical source files

- `BSC_MEME_5C48_TWO_VENUE_22_FROZEN_RECONCILIATION_SPEC_2026-10-11.json`
- `BSC_MEME_5C48_TWO_VENUE_22_RAW_EVENT_RECONCILIATION_2026-10-11.json`
- `BSC_MEME_5C48_V2_TRUNCATED_WBNB_ROUTER_EVIDENCE_2026-10-11.json`
- `BSC_MEME_5C48_22_TX_TWO_VENUE_SETTLEMENT_QA_2026-10-11.json`
- `BSC_MEME_5C48_IFML_LOBSTER_22_CLOSED_EPISODES_2026-10-11.json`
- `BSC_MEME_5C48_BINANCE_LIFE_FULL_ERC20_HISTORY_2026-10-11.json`
- `BSC_MEME_5C48_BINANCE_LIFE_17_NATIVE_BLOCK_CASHFLOW_2026-10-11.json`
- `BSC_MEME_5C48_BINANCE_LIFE_17_ORIGINAL_SIGNER_RECEIPT_PROVENANCE_2026-10-11.json`
- `BSC_MEME_5C48_THREE_TOKEN_SCOPE_INCLUDE_NEGATIVE_CONTROL_2026-10-11.json`
- `BSC_MEME_FOUR_EOA_IFML_LOBSTER_CAPITAL_AND_EPISODE_COMPARISON_2026-10-11.json`
- `BSC_MEME_FOUR_WALLETS_19_CA_BREADTH_AND_EVIDENCE_GAPS_2026-10-11.json`

No price alerts, automated trades, Gmail, paid RPC or production state has been modified.
