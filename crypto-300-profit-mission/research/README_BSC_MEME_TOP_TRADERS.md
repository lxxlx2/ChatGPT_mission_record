# BSC Meme 研究：禁止付费 GMGN API 依赖（2026-10-10 更正）

**Current approved route: ONCHAIN_RPC_ONLY, NO_GMGN_PAID_API, NO_USER_INSTALL_OR_KEY_REQUIRED.**

This README supersedes earlier commands in this folder. The previously committed scripts `bsc_meme_top_traders_readonly.py`, `bsc_top_trader_crosscheck.py`, and their tests are **deprecated / NOT_APPROVED_FOR_EXECUTION**. Those programs attempted GMGN API-based sampling. User explicitly rejected GMGN API because it requires funding and imposes request limits. Do not ask the user to download scripts, install GMGN CLI, buy a GMGN plan, provide API keys, or execute these programs. Do not treat those scripts as task completion.

The assistant has already connected and used an existing read-only Alchemy BSC blockchain application, so it can collect transfers, historical token/pair activity, transactions, transaction receipts and balance snapshots **itself in this conversation**, without user-side steps. No automated monitoring is authorized.

## Actual independent on-chain proof obtained during this correction

On 2026-10-10, direct `bnb-mainnet` Alchemy `getAssetTransfers` calls (5 pages of 10 transfers per pair) obtained:

| Token | Contract | BSC Pancake V2/WBNB pair | Transfer entries | Unique transaction hashes | Block range |
| --- | --- | --- | ---: | ---: | --- |
| 牛来 | `0xbeea1d618e533a387d941f58a7d4c9b7bd377777` | `0xbfc26980d8068ae744f5405d3abf6e7df02e11b3` | 50 | 25 | 116314923 to 116318053 |
| MARSCOIN | `0xfe189e97832da1573e4e4ff034f4ffc3a15c7777` | `0x9f286c9bd510150c62a08da72af797ac45311ae0` | 50 | 25 | 112668718 to 112679229 |

First rows included pool fee/self-token transfers. These entries are NOT all separate buys; the 25 distinct hashes are also NOT confirmed distinct beneficial traders. Underlying individual `ethGetTransactionByHash` calls were made for the first 10 distinct hashes of each token. Some result fields were truncated in the connector response and thus original signers were not reported as confirmed where missing. This research does not pretend the full history or per-token profit top-100 is already indexed.

Baseline: the previous 19-token universe, initial Pancake V2 scans, historical cross-wallet cluster and PnL examples remain in `BSC_MEME_TOP_TRADERS_AUDIT_2026-10-10.md`. Especially important: BUBB's pre-V2 trade included WBNB *rather than native BNB* sale proceeds, proving both pre-migration venues and receipt-level quote asset accounting are required.

## How to complete the task in this chat, with no paid third-party top-trader API

1. For each of 19 known tokens, and later add any official Binance Alpha-only BSC meme omissions, identify the actual original launchpad pool and subsequent Pancake V2/V3 WBNB or stablecoin routes. Do not assume V2-only captures first trades.
2. Query all token inflows/outflows and true original swap signers in paginated batches via connected Alchemy, using proper `pageKey` and block-scoped request limits. Persist research evidence and coverage/completeness notes to Git directly. For large volumes, divide into bounded sub-windows and deduplicate hashes and events.
3. Decode transaction receipts for token flows and **quote settlement assets** (BNB, WBNB, USDT, USDC, BUSD) and gas. Transfers or airdrops alone are not purchases; transfer-out alone is not realized sale. Pool/router intermediaries or shared recipient addresses are not single traders.
4. Build a candidate wallet table including **all sampled positions, including losses**. Only rank profits when quote cashflows and cost basis are reconstructed; distinguish unverified/closed/open positions.
5. Identify >=2-token profit repeaters, actual bilateral transfers/shared funding, source identity ambiguity and **true** recent signed Meme swaps. Then run 5/15/30-minute delayed entry followability check.
6. Only publish conclusions that have corroborated original transaction hashes, dates, cost proceeds and conditions. Write UNVERIFIED when necessary. Never manufacture a full top-100 ranking or imply it was retrieved from Alchemy directly.

We may read public Binance leaderboard or Dune data as non-authoritative lead generation when no paid plan is required, but every claimed wallet PnL is to be verified with the same original-chain audit.

**No further commands for the user; user explicitly wants the assistant to perform data collection and Git updates.**

Research: OBSERVE_ONLY. Production: NO_GO. Do not create monitoring, automations or live-trading jobs.

## Current research authority: V21 inventory + Stage 16 economic reconciliation (2026-10-12)

The BSC address-model research itself has advanced beyond the 2026-10-10 collection notes above. Preserve earlier evidence and chronological scope:

- Frozen 23 wallet × 19 exact CA matrix: `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json`. All 437/437 exact CA ERC20 positive-transfer cursors exhausted; 148/148 observed-transfer CA token raw quantities independently reconciled; 289 zero-positive-transfer CA cells. This is **not** a closed economic PnL ledger or viable follow-trader proof.
- Current economic research handoff: `BSC_MEME_ADDRESS_MODEL_5_STAGE16_CROSS_WALLET_MANAGER_FEE_CAUSAL_QA_2026-10-12.md`.
- Exact EOA-indexed manager events and WBNB real quote asset flow: `BSC_MEME_STAGE16_3_EOA_ROUTER_FEE_AND_SIGNED_ROUNDTRIP_QA_2026-10-12.json`. Across 8 original signed buy/sell txs in 3 wallets and 3 meme tokens the manager event equals **floor(1% of appropriate gross amount)**. Event ABI semantics have not been independently decoded, and do not extrapolate fee policy to other routes.
- Three initial raw-token fully paired original buy/sell cycle **BNB block scopes**, not fully internal-traced causal PnL: DDAC/MARSCOIN `+0.051496246460395600 BNB`, 2ADF/BOB `+0.009515610472872943 BNB`, and A83B/BROCCOLI714 `-0.239887492433116024 BNB`. An extra successful EOA transaction on each DDAC sell block is explicitly gas-accounted. Its following partial-token exit is **not** a completed loss.
- Correction: a legacy unscoped BOB manager log `0x11c37937e080000` means 0.08 BNB and must **not** be labeled the 2ADF original buy fee. Exact manager topic + wallet-indexed log + original tx hash returns **0.005 BNB** in the updated fee proof.

Next research stage: reconstruct true original-owner quote-denominated trade costs/proceeds for repeated major meme opportunities, include unsuccessful or missed eligible opportunities as denominator, distinguish open inventory and internal tracing limitations, and **only then** study delayed follower prices/liquidity. Do not rank wallet PnL merely from Transfer logs, account balance snapshots, or three convenient examples. No GMGN paid API. OBSERVE_ONLY / PRODUCTION_TRADING = NO_GO.

## Latest handoff: Stage 17 cross-wallet and negative outcome controls (2026-10-13)

Continue the ADDRESS MODEL research from `BSC_MEME_ADDRESS_MODEL_5_STAGE17_CROSS_WALLET_2_MEME_TIME_AND_ECONOMICS_2026-10-13.md`, not from the deprecated GMGN scripts or from more 23×19 token-balance rescans.

- V21 23 wallets × 19 frozen exact CAs: 437/437 positive ERC20 cursors complete; 148/148 observed raw token quantities independently conserved. **Token inventory phase is complete.**
- Stage 17 cohort raw onchain source: `BSC_MEME_STAGE17_DDAC_8E6B_IFML_LOBSTER_TWO_TOKEN_NEGATIVE_CONTROL_2026-10-13.json`. In 9 selected, fully token-inventory-closed native-BNB-block trading episodes across DDAC/IFML (5), DDAC/Lobster (2), 8E6B/IFML (2), 4 scopes are positive and **5 are negative**. This 4/9 is a selected audit-sample observation, **not** candidate win rate or all eligible major opportunities.
- DDAC on IFML: first four native-block scopes positive, fifth `-0.446324586902254802 BNB`; 8E6B two separate fully inventory-closed IFML cycles `-0.231346571585353217` and `-0.367677245259552299 BNB`, 6/6 original EOA signatures and 6/6 receipt success statuses checked. DDAC late IFML loss exited 2026-01-08 07:32:10 UTC, 8E6B bought 11 seconds later: **timing ≠ proof of following**.
- DDAC/Lobster both closed cycles negative (combined `-0.183543131928304728 BNB`); V2 negative sell cashflow and fee validated in `BSC_MEME_STAGE17_DDAC_LOBSTER_V2_SELL_ADDITIONAL_APPROVAL_GAS_2026-10-13.json`. Previous gas label of **208457** is **the sum** of the actual extra approve gas **46327** and inferred swap gas **162130**, NOT one sale GasUsed.
- 8E6B/Lobster has an opposite `+4.794001707717376678 BNB` *native block scope*, but original receipt status is confirmed only 11/13, and no equivalent closed-cycles realized-PnL partition yet. Do not rank it as a verified winner.
- 8E6B IFML first manager sell receipt truncated: targeted WBNB Withdrawal + indexed 1% fee-like manager event + separate same-block EOA approve receipt allow exact conditional sale-gas reconciliation. Its later IFML episode used both manager and direct router venues. Do not mix route fee structures.
- Next priorities: economic lifecycle/classification of more *major token opportunities* and all qualified non-entries/losses in the denominator, then real-time-to-signal availability and delay-capacity historical simulation only after complete independent QA and another AI review.

All economic results remain native-wallet block-scope with BSC internal trace limitations unless explicitly transaction-causal verified. NO_GMGN_PAID_API / OBSERVE_ONLY / PRODUCTION NO_GO.
