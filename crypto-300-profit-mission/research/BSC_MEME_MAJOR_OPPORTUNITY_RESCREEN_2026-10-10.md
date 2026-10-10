# BSC Meme: major-opportunity wallet rescreen (corrected criteria, 2026-10-10)

Status: RESEARCH_ONLY / OBSERVE_ONLY / PRODUCTION_TRADING=NO_GO. **This report supersedes all earlier recommendations that treated 30-day activity and random small-Meme win rate as primary qualification gates.** No GMGN paid API, new monitors, live trading or user-side scripts.

## User intent (binding for this research)

Identify wallets that **repeatedly capture material profitable trades** on **large BSC meme opportunities that Binance subsequently listed in Alpha, Futures, and/or Spot**. A trader who no longer trades is **still useful for historical pattern research**. Ignore standalone small/unrelated Meme win rate as a ranking dimension; those tokens are used only to determine whether a wallet has continued to operate, plus optional evidence of serious wallet blowups. Small-Meme losses must not negate core Binance-related hits, but major risk exposure must never be silently hidden when assessing an actionable strategy.

## Selection process, not hindsight victory counting

- **Core cohort**: exact BSC contracts with independently verified Binance USDT perpetual or Spot listing events. From the previous 19 candidate addresses, 18 are provisionally core (some announcement path details still require individual link checks). Distinguish launch date, first Alpha, announcement, perpetual live, Spot live. Never imply any trader knew the future Binance listing.
- **Secondary cohort**: BSC Meme listed on Binance Alpha but without verified Binance Futures/Spot; currently BUBB only in this restricted sample. Keep as a separate opportunity class instead of treating BUBB as equal to 2026 MarsCoin/牛来.
- **Unrelated small memecoins**: no weight in major-opportunity profitability or qualification. Optional activity proof only. A tiny loss is NOT a negative main-screen mark. A large catastrophic loss from all-wallet risk audit is a separate **risk warning**, never alter core hit count.
- **Relevant for each core token/wallet**: 1) verified position bought directly (not transferred or router beneficiary confusion), 2) cost, quote settlement incl native BNB/WBNB/stables & gas, 3) closed realized PnL and ROI, 4) position size & hold duration, 5) entry time vs verified listing/announcement milestones, 6) repeated independently profitable tokens/periods; report unverified events.
- **Bucket results**: `MATERIAL_WIN` (confirmed net profit with economically meaningful size/return), `MARGINAL_WIN` (small positive vs deployed capital/Gas), `LOSS`, `TRADED_PNL_UNKNOWN`, `NOT_OBSERVED`. Do NOT combine all positive numbers to assert repeated meaningful mastery. Do NOT use an invented numerical ROI threshold as proof of skill.
- **Wallet role**: `CROSS_TOKEN_WINNER`, `HISTORICAL_WINNER`, `WATCH_CURRENT_ACTIVITY`, `ROUTER_BENEFICIARY_UNVERIFIED`. Recent trading is metadata, not mandatory eligibility. A cluster of wallets funded by the same high-throughput disperser cannot be counted as several independent skilled traders without stronger common-control proof.
- Crucial **sample caveat**: this is a re-screen of **five previously researched candidates**, NOT an exhaustive ranking of all 18/19 tokens' best historical profit wallets and NOT a statistical opportunity hit rate. Denominator must include all independently corroborated *traded* core tokens and known loss-making core positions, rather than all 19 eligible tokens as if every wallet necessarily could trade them.

## Re-screen of five evidence-backed candidate wallets

| Tier of interest | Wallet BSC | Verified successful **core** Meme tokens | Core profits supported on already reconstructed closed positions | Current/activity note |
| --- | --- | --- | --- | --- |
| A: strongest repeated 2026 | `0x2adf961b40951736bcff3b36b7fb1cd5775475ba` | 2026 我踏马来了, 龙虾, MARSCOIN, 牛来; also small-margin 2025 winners TUT, BOB, 4, 币安人生 | 2026 four: approximately **+13.3 BNB** combined, best single 2026 MARSCOIN about +6.1 BNB and 我踏马来了 about +5.93 BNB; other 2025 tokens have tiny edge, not 4 extra material wins | Confirmed separate direct Meme trades **2026-10-10**, not merely a dormant wallet. Many unrelated small tokens traded: activity evidence only. |
| A: historical repeated large captures | `0xd70ce47ec32625420640da206f0b3525c2bec678` | 4, 币安人生, 哈基米 | Three **core** wins about **+12.3027 BNB** on sampled closed positions | Last observed relevant major-token sell in Dec 2025. **KEEP** for historical pattern research; do not reject for inactivity. |
| B: independent 2026 repeated winner | `0x239e74bfbd02d71cdc70fecc2d505dc13acfb337` | 我踏马来了, 龙虾 | Two core wins ~**+0.2965 BNB** | 2026 BNB activity; unrelated small-token trades/losses excluded from core scoring. |
| B: historical small-position, high-return | `0xe54bdcaff91ed27e53a19bb1203b10bc5e2dc568` | 币安人生, 哈基米 | Two core wins ~**+5.8701 BNB**, almost all from exceptional 哈基米 trade | 2026 activity but not necessary for inclusion. **Outlier concentration**: two successful tokens ≠ a proven reproducible method. |
| B: linked historical secondary | `0x57c98bc732f0e9ed7156d21f74c17bee4bb0cbf4` | 币安人生, 哈基米 | Two core wins ~**+0.7303 BNB** | Shared bilateral BNB transfers with `0xd70ce...`; potential cluster, so **do not count as independent corroboration without control audit**. |

All PnL here is scoped to selected closed token positions reconstructed from token flows and BNB-balance changes, not complete lifetime account PnL, and is subject to quote/internal-flow limitations. **Do not label 4/4 or 3/3 as whole-opportunity capture rate or historical win rate.** Exact BNB cashflow figures and transaction hashes can be reviewed in [binance-bsc-meme-cross-token-v1-2026-10-10.md](binance-bsc-meme-cross-token-v1-2026-10-10.md) and [BSC_MEME_TOP_TRADERS_AUDIT_2026-10-10.md](BSC_MEME_TOP_TRADERS_AUDIT_2026-10-10.md).

### New direct 19-token participation crosscheck

Queried original EOA inbound/outbound transfers with a filter of **all 19 validated 42-character token CAs** through the existing Alchemy connection on BSC. This is NOT a centralized top-trader service. Five wallets:
- `0x2adf...`: beyond four 2026 core closed winners, demonstrated 2025 core participation in TUT, BOB, GIGGLE, 4, 币安人生, 哈基米 and secondary BUBB; 2025 **GIGGLE and 哈基米 full PnL not yet resolved**, owing non-pool destinations, numerous deposits and/or exits. Has demonstrated at least 11 different scoped tokens, not necessarily 11 winners. There may be other eligible tokens in this 19-cohort not yet fully enumerated by dense paginated broad-filter scan.
- `0x239e...`: relevant major positions on 我踏马来了 and 龙虾, plus tiny incidental 牛来 inbound without proven trade. Two core winners confirmed; tiny inbound ≠ a third major successful trade.
- `0xd70ce...`: major inbound tokens 4, 币安人生, 哈基米 plus Alpha-only BUBB. BUBB ~-0.08193 BNB belongs to **secondary**, not a failed core F/S-listed opportunity.
- `0x57c98...`: major 币安人生, 哈基米 (two), both closed profitable.
- `0xe54bd...`: major 币安人生, 哈基米 (two), both closed profitable.

### 2025 core-token margin sanity check for leading 2026 wallet

To distinguish having traded a Binance-listed token from having **captured material profit**, independently fetched every direct in/out ERC20 transfer for BOB, TUT, 4 and BUBB, plus the Binance Life pair buys/sells, and compared BNB native balances before/after each distinct trade-containing block:

| Token | Period/position | Native-cost BNB | Net receipt BNB | Approx net BNB | Classification |
| --- | --- | ---: | ---: | ---: | --- |
| TUT | 3 buys / 3 sell-txs (4 ERC20 out-transfer rows) | 0.9006540936 | 0.9100769136 | **+0.00942282** | CORE / MARGINAL_WIN |
| BOB | 1 buy / 1 sell | 0.50189033 | 0.5114059405 | **+0.00951561** | CORE / MARGINAL_WIN |
| 4 | 2 buys / 2 sells across separate time periods | 0.38033875276 | 0.41213388195 | **+0.03179513** | CORE / MARGINAL_WIN |
| 币安人生 | 8 material buys / 9 material sells, later dust transfer | 2.2425634692 | 2.2531911339 | **+0.01062766** | CORE / MARGINAL_WIN |
| BUBB | 1 buy / 1 sell | 0.5007525014 | 0.4807523012 | **-0.02000020** | SECONDARY Alpha-only / LOSS; not core ranking |

BNB-balance-delta estimation: verify actual ERC20 receipt quote routes if outcome appears inconsistent or has non-BNB settlement; the known BUBB counterexample on *another* wallet sold for WBNB shows why native-only deltas cannot be universally trusted. For these transactions token quantities enter and exit precisely (except tiny external spam receipts on 币安人生 not counted as economic buys). These are **candidate figures** pending uniform quote-asset receipt audit, not audited profits.

Illustrative original-chain proofs for core wallet:
- 我踏马来了 2026 buy `0x7000ec66e104ca78d0be834d178ab5f8df075b464bb7c7cd3784943807528613`, and all 13 buys / 18 sells reconciled; ~+5.92923 BNB.
- 龙虾 2026 buy `0x7a9cff29108df4a026405cf543e156bd898139c2e41f1137e3c9f2fedbbd7892`; partial sales and later dust receipt separated; ~+0.44 BNB from its own trading.
- MARSCOIN buy `0xf0f8007c0cbf1cebde26948ed1b84d73666dea02d88c261d4408fe34a6b0eb7d`, total buy cost ~0.97148 BNB, sell cashflow ~7.10513 BNB incl small later third-party transfers; approx +6.13 gross scoped, conservative ~+6.12 own initial trading.
- 牛来 buy `0x4ed9e3d87b54fe4de7b7625382280538ce6fc2e9734942fa01959af90a5fa281`, 9 buys cost ~1.08047 BNB, 15 native sell block credits ~1.87523 BNB, net ~+0.79476 BNB.

**Direct confirmation of real recent activity (small token, no core score):** 2026-10-10 at 10:31:46 UTC, `0x2adf...` bought CZ (0.08 BNB), tx `0x329216fd126f5c28d75a8065449ccc4fb6ec08cca733a08049364ce318fcba59`; at 12:40:52 UTC it sold 高雅人士 tx `0x78b276adc4507de9e5326c7932fc9fac79518fd65231f1174f3f208295e02e13`; at 12:54:03 UTC it bought 高雅人士 (0.08 BNB), tx `0x1f3a8cb6bd9f6344c70e4477d4da90a1c058a3bee46e1a263249ba25a3bbb4e3`. Unrelated token returns/losses are activity metadata only.

### Execution/copyability still unconfirmed

An on-chain V2/WBNB reserve spot-price snapshot check of the `0x239e...` wallet's two core early entries found that after 5 minutes the pool spot quote was +439.7% for 我踏马来了, +114.8% for 龙虾 vs that wallet's entry snapshot; 15 minutes +963.4% and +410.1%. This **does not** assert follower profits (fees, timing, liquidity, selling and execution risk not simulated). The strategy's current utility depends on testing delay, but lack of such replay **does not disqualify a historical successful wallet**.

## Updated shortlist and task order

1. **Primary:** `0x2adf...` (four strong distinct 2026 core wins; still trading, also some marginal 2025 outcomes). Finish GIGGLE/哈基米 core position reconstruction, compare relative to listings; investigate genuine repeated *early timing* and avoid judging its irrelevant small-token failures.
2. **Strong historical:** `0xd70ce...` (three material core wins); reconstruct linked-wallet funding network and historical prelisting timing. Do not discard for being inactive.
3. **Independent competitor:** `0x239e...` (two 2026 core wins); rank on major opportunities, not three unrelated mini-Meme losses.
4. **Outlier / cluster control:** `0xe54bd...` (one outsized 哈基米) and `0x57c98...` (funding network with `0xd70ce...`).
5. **Broad universe:** collect top materially profitable addresses for every core token independently using full launchpad + V2/V3 / aggregator receipt evidence. This remains INCOMPLETE. No GMGN paid API or user-side collection. Distinguish unique actual wallets from shared beneficiaries. Do not invent Top 100, full opportunity hit rates, 30-day active profitability or automatic trading.

No monitors/automations/prod configuration changed. User conversation titles untouched.
