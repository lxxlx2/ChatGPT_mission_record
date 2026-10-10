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
