# BSC Meme 地址模型 P4-B | Stage：2026 major Flap early entry and all-19 market witness

Date: 2026-10-14 (Asia/Bangkok). Status: **RESEARCH_ONLY / P4-B PARTIAL / P5 BLOCKED / PRODUCTION NO_GO**. No signed transaction, alert, monitoring, production change, local Mac deployment, PR merge or live fill was executed in this research session.

## One decision-relevant result

Historical earliest scoped PancakeSwap V2/V3 pool liquidity cannot be the sole start of market U: two 2026 major token creators and buyers were directly confirmed at their **Flap.sh Portal** (`0xe2ce6ab80874fa9fa2aae65d277dd6b8e65c9de0`) before those scoped DEX pools appeared. Flap BNB contract identity and TokenCreated/TokenBought/TokenSold ABI were verified against official Flap documentation and the official `flap-sh/FlapVaultExample` ABI. Not a Chinese secondary source:
- https://docs.flap.sh/flap/developers/deployed-contract-addresses
- https://docs.flap.sh/flap/developers/wallet-and-terminal-and-bot-developers/trade-tokens
- https://docs.flap.sh/flap/developers/wallet-and-terminal-and-bot-developers/index-token-created-events
- https://github.com/flap-sh/FlapVaultExample/blob/main/src/flap/IPortal.sol

Earlier unfettered Portal `eth_getLogs` in a whole block exceeded serialized response size: exact error preserved in `bsc-meme-address-model-v1-p4b-flap-major2-origin-raw-part1..2-2026-10-14.json`. **A separate precommitted** single-block known-ABI topic filter was used, limiting origin evidence to exact original tx hash and unindexed exact token CA; queries/headers and raw logs were committed in `bsc-meme-address-model-v1-p4b-flap-major2-topic-raw-part1..2-2026-10-14.json`. Do not cite the aborted unfiltered response as proof of an empty event set.

## Source-verified comparison; never combine these amounts as BNB, USDT or USD

| Field | 牛来 | MARSCOIN |
| --- | --- | --- |
| Exact CA | `0xbeea1d618e533a387d941f58a7d4c9b7bd377777` | `0xfe189e97832da1573e4e4ff034f4ffc3a15c7777` |
| Flap TokenCreated block | 115628768 | 112441387 |
| First original TokenBought selected from original transfer cohort | 115628774 | 112441394 |
| Original signed outside-23 EOA | `0xb0d0c4c1ee4ba9fac874db4ede587718ad9484d9` | `0x504ba7b11be98c66a379a3e5de91dc5ab2dde3ea` |
| `TokenBought.buyer` on intermediated path | `0x9e698d361bb2375bd335dad156accbbad45bf364` | `0x1de460f363af910f51726def188f9004276bf4bc` |
| ERC20 token transfers | Portal → intermediate → routing contract → original EOA | Portal → routing contract → original EOA |
| Original event amount to owner (18 token decimals) | 37,956,445.907182539413593521 牛来 | 77,163,604.478330373759393953 MARSCOIN |
| Historical original quote CA | `0x205812cdbed920aff76c6580abd681a46d11efc7` | `0xbe9d156892e55e7154bcd3cb0fea677f9d3103e1` |
| Quote metadata symbol (current-only) | Q3B | S5B |
| Historical quote decimals at creation and purchase | 18 / 18 | 18 / 18 |
| Original `TokenBought.eth` (in configured quote units) | 0.205991990065603310 Q3B | 2.674483304192706318 S5B |
| Original `TokenBought.fee` (in same configured quote units) | 0.002059919900656033 Q3B | 0.026744833041927063 S5B |
| Original TokenQuoteSet | non-native ERC20 Q3B CA | non-native ERC20 S5B CA |
| Original FlapTokenTaxSet and FlapTokenAsymmetricTaxSet | buy/sell 100/100 bps | buy/sell 300/300 bps |
| Pre-first-buy mathematical quote: exact 0.01 configured quote token | COMPLETE, positive | COMPLETE, positive |
| Same pre-first-buy reverse quote, 1 token | RPC arithmetic revert, not proof tokens could never be sold | RPC arithmetic revert, not proof tokens could never be sold |
| At original first-buy block, reverse quote of actual full received token inventory | COMPLETE, positive mathematical quote | COMPLETE, positive mathematical quote |
| Original TokenSold in next 10 blocks | Complete source: zero matching token | 10-block query truncated; one-block original buy block COMPLETE: zero matching token |
| Actual later successful realized sell | UNRESOLVED | UNRESOLVED |
| Beneficial round-trip settled wallet PnL / fixed followable U | UNRESOLVED | UNRESOLVED |

**Important causal distinction:** original signed EOA and final ERC20 recipient match exactly with original TokenBought raw amount for each of the two trades. The ABI `TokenBought.buyer` is an intermediate contract, not the outer signed EOA, so it must not be ranked as the trade owner. Neither EOA appears in the frozen original 23 candidate research wallets; they serve only as pre-DEX market venue existence and negative-control evidence. They have not been silently added to the 23-wallet denominator. The original receipts remain API-truncated/unresolved, but single-block canonical TokenBought original tx hash and final ERC20 transfers close **the scoped purchase evidence**. Their quote token and fee are supported as *event values* only; the entire wallet net payment and conversion path still need all quote asset cashflow evidence.

The exact raw price query `quoteExactInput((address,address,uint256))` used selector `0xfc847c2b`; precommit and historical call bytes are preserved. Underlying Flap docs explicitly permit non-native ERC20 quote pools and a native-to-quote intermediate route. A `quoteExactInput` return at the actual first-buy block says a mathematical reverse quote existed, **not** that the signer (or 1/5/15-min follower) actually successfully sold. The raw ten-block `TokenSold` query for MARSCOIN was truncated and cannot be promoted to a complete 10-block negative.

## Uniform V1 major universe and wallet denominator after this increment

`bsc-meme-address-model-v1-p4b-19ca-unified-early-market-buy-evidence-2026-10-14.json`, replay `bsc_meme_address_model_v1_p4b_market19.py`: exactly **19/19 original CA**, original **23 candidate EOA × 19 = 437 cells** retained, original historical V2 math quote on 19/19, exactly **three** bounded original signed early buy market witnesses: **龙虾 / DDAC (in original 23, Four.meme), 牛来 / noncandidate (Flap), MARSCOIN / noncandidate (Flap)**. The other **16** tokens' earliest signed buyers are **NOT AUDITED IN THIS STAGE**, not proof of no earlier buys. No cross-token gross quote raw amounts were ever summed into USD/BNB profit. First global executable market U, minimum public observer-visible entry, historical positive actual sell and tax realization, wallet funds at U and follower PnL remain `UNRESOLVED` for all 19.

**Evidence/test contract:** exact original Git blob manifest of 13 Flap source inputs to `bsc_meme_address_model_v1_p4b_flap_major2.py` and 5 whole-universe source inputs to `bsc_meme_address_model_v1_p4b_market19.py`. Both scripts independently replay raw onchain ABI logs, owner EOA signer and exact output token movement, quote token/tax config, historical decimals, source buy and sell query state, source roster, frozen no-alpha fields; adversarial tests prevent forged signer, token amount, quote CA, tax, missing/short sale window, original 23 cohort drift, and false filled PnL.

Successful actual source replay and unit tests on code SHA `b57e980e2331e40842cadab5064d3f843eb89762`: GitHub Actions `38603891677` **SUCCESS**, 245 main tests + 9 supplementary tests, 33 successful CI job steps. That code CI passed prior to this documentation-only commit; later exact HEAD CI must be checked separately.

## Next mainline gates (finite, no one-wallet tunnel)

1. Preserve entire 19 × 23 cohort. Use true event-confirmed Flap/Four **early market** entrances to construct source-backed actual opportunity U with first publicly observable trading and **exit** (not solely buy mathematical quote), and explicit potential quote-denomination conversions. First resolve existing bounded Flap TokenSold evidence at a few precommitted causal windows across **both** 2026 majors, rather than infinitely chasing one unusually profitable wallet.
2. For the same exact CA and original market, retain source-real receipts/quote token transfers, native Gas and intermediary settlement to identify **causal signed-owner net realized buys and sells**. No same-CA positive trade or a new pre-launch wallet automatically becomes candidate profit.
3. Only when U and seller execution are source-qualified, assess full **23 wallets' funds at observer time**, with eligibility/NO_FILL/UNKNOWN, old P2 negative rounds, and 1/5/15-minute P5 out-of-sample replay. Do not backfit sample, amount, lead-time, route or success thresholds to this first Three-source demo. G4/G5 and other-AI independent fixed-SHA review remain blocked pending evidence and explicit approval for any later read-only Mac acceptance.

**NO_GO / NO_MERGE / NO_DEPLOY.** No Frank/Monster/GMGN/paywalled API/live executions/notifications touched.
