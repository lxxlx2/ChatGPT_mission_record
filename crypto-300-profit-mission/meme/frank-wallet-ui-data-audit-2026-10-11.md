# Frank 钱包看板交易账本差异与 GMGN 功能对照：证据审计

Updated: 2026-10-11 Asia/Bangkok
Authority: read-only product/data research; **no code modification, local deployment, monitor creation or trading**.
Canonical Frank wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ` from `local-agent/config/frank_local_registry.json`.
Related design: `frank-wallet-monitor-dashboard-v2-design-2026-10-11.md`.
Evidence types below explicitly distinguish user screenshots, current Git source, actually performed chain RPC reads and third-party documentation.

## 1. Screenshot observation, not on-chain audit

User-supplied localhost screenshot (~2026-10-11 04:48 Asia/Bangkok) shows:
- Frank runtime “正常”; last heartbeat around 27 seconds earlier.
- **24h 已索引签名 = 198, 本地已识别买入 = 0, 本地已识别卖出 = 0, 24h待复核=0, 当前可跟候选=0**.
- “Frank 最近买卖” still displays **2026-10-09 08:27:21** buy **3,300 USDC**, 08:26:53 sell **2,232.34 USDC**, 08:26:47 sell **7,031.56 USDC**, and an older 2026-10-08 buy **6,715.73 USDC**. These are *on-screen historical classifications*, not independently re-decoded transactions in this pass.
- A GMGN wallet detail screenshot of the **same Frank wallet** illustrates current/token PnL, buy/sell count, current positions, realized/unrealized accounting, avg cost, hold duration, wallet transfer rows and multi-day history. The highlighted baton token shows 25 displayed buys and 19 sells over its history. That scope is **not** identical to the localhost “past 24h” counter.

**Immediate temporal reconciliation:** from 2026-10-09 08:27 to 2026-10-11 04:48 local ≈ **44h21m**, outside the local 24h filter. Therefore “24h buy 0/sell 0” and “recent historical trades show Oct 9 trades” **can both be true**. The screenshot alone cannot prove a 24h active-swap miss; the missing persistent watch portfolio and ambiguous periods are nonetheless verifiable product defects. Never present the 198 indexed signatures as 198 buys/sells.

## 2. Current Git code provides a concrete root cause for invisible positions

**A. Misleading window / different query scopes**
- `local-agent/mission_agent/mission_control/frank.py::activity_coverage` computes 24h/7d/30d classified counts from local `signatures` and `trades`, explicitly reporting `scope=LOCAL_INDEX_ONLY`, `chain_completeness_verified=false`.
- `FrankReader.recent_trades` queries the newest stored trades **without the 24h cutoff**, then the UI displays only the newest 50. Old transactions can therefore remain visible while 24h counts are zero. Current UI labels do not sufficiently distinguish those scopes.
- The “Frank status 正常” banner validates process/heartbeat/local DB and decision engine health. It is **not** a complete-wallet-history/GMGN-equivalent correctness proof.

**B. Watch pool is filtered out before rendering**
- `FrankReader.candidates()` reads only `v1_states`, chooses **signal-bearing** ACCUMULATION/MULTIPLE episodes, or a special `REENTRY_WATCH` case requiring a recorded REENTRY trade. All other observation states are skipped.
- `service.py::cycle` consumes those filtered candidates for the *follow decision*. That gating is appropriate for frozen high-conviction alerts, but **cannot be reused to construct a general wallet position/watchlist view**.
- `static/app.js::refresh` renders `/api/candidates` split by current `CLOSED` status. `renderCandidates` says “当前没有需要跟踪的 Frank 候选” when empty.
- `static/app.js::renderEnded` further limits exited candidates to **last 24h**, despite long-lived observation value. The dashboard currently has no independent persistent all-observed-mints/positions registry or manual pin groups; it is not a wallet portfolio.
- Existing early `WATCH` idea already appears in `state/frank-wallet-watch.md` and was explicitly **silent**. A visible read-only WATCH portfolio must not auto-promote to an alert or change its frozen thresholds.

**C. Classification explains large signature volume**
- `frank/parser.py::normalize` requires wallet active authority, recognized DEX and opposing token economic flows with swap instruction evidence to promote an active swap. A passive receipt does not qualify. The rule prevents bot fee/reward/ATA activity from masquerading as insider BUY.
- The new UI must still disclose the **other categories**: wallet-signed transfers, passive receipts, claims/rewards, unknown routed swaps, failed transactions and known gaps. A purely “valid signals only” view loses legitimate user-interest behavior.
- Current `review_activity` only exposes a narrow `UNKNOWN_NEEDS_REVIEW` subset; it does not make all token ledger movements visible.

## 3. Fresh read-only independent chain sample, actually executed

Source: Alchemy Solana mainnet RPC, selected app `ChatGPT Crypto Monitor All Chains`. This connector sample is independent of the user's localhost and the GMGN screenshot. No paid GMGN API requested or used.

Wallet `getSignaturesForAddress` read at finalized commitment:
- **15 latest signatures** at first read, newest `2h9g4WDoeXktU4N3yRQvKavxyKAtT34QC6ke8PQkCtuJATf1n44u1Jw3wzCZ1ACJWWppJk7L379QYUruf7Ed9LYs`, block time **2026-10-10 21:46:50 UTC** (2026-10-11 04:46:50 Bangkok), finalized slot **455408653**.
- Paginated **132** signature metadata entries across **6 pages × 22**, ranging **2026-10-10 21:46:50** to **2026-10-10 09:00:17 UTC**; all those 132 rows fall on Oct 10 UTC. Next request failed with **Alchemy RPC 429 compute-units-per-second cap**. The 132-row set **does not reach the full 24h start** or Oct 9 observed sale window; no complete 24h/7d/daily active trade claim is made.
- First signature's transaction was independently decoded via finalized `getTransaction`:
  - signature `2h9g4WDoeXktU4N3yRQvKavxyKAtT34QC6ke8PQkCtuJATf1n44u1Jw3wzCZ1ACJWWppJk7L379QYUruf7Ed9LYs`;
  - the wallet was **not a signer**; `8ZeY1dBtj9fdkJ9RhnVKFKhymRqdsbNPra8DXSFvsyYE` was the signer; token `A7bdiYdS5GjqGFtxf17ppRHtDKPkkRqbKtR27dxvQXaS` was transferred into Frank-owned ATA with `transferChecked` amount **21 raw units / 8 decimals = 0.00000021**; no DEX swap; class **PASSIVE_RECEIPT**.
  - verifiable explorer: https://solscan.io/tx/2h9g4WDoeXktU4N3yRQvKavxyKAtT34QC6ke8PQkCtuJATf1n44u1Jw3wzCZ1ACJWWppJk7L379QYUruf7Ed9LYs
- Second signature similarly independently decoded:
  - `4QtHVndAuGogj49sF9AySPWUm58gYqMgohw96tmoPg4pj7YSd2UvNQ4Abz27as2pntTUYD8iu5GyQE7uwbPJ45Cz`; finalized 2026-10-10 21:36:54 UTC; same external signer; same mint **492 raw / 8 decimals = 0.00000492** transferred to Frank-owned ATA; no active Frank signer/DEX swap; class **PASSIVE_RECEIPT**.
  - explorer: https://solscan.io/tx/4QtHVndAuGogj49sF9AySPWUm58gYqMgohw96tmoPg4pj7YSd2UvNQ4Abz27as2pntTUYD8iu5GyQE7uwbPJ45Cz
- A further `getTransaction` payload could not be fully parsed owing to response clipping, and was **not** used to classify activity. This sample **does not establish** how many active Frank swaps occurred in the entire Oct 10–11 window.

**Operational feasibility observation:** a naive one-time fully historic wallet scan with sequential full RPC pages is vulnerable to rate limits; this precise test hit 429 after six 22-signature pages. A credible design must include incremental durable indexing, request pacing, checkpoints and resume, reproducible historical backfill with explicit coverage gaps, and no price/PnL numbers derived from truncated RPC responses.

## 4. Actual GMGN feature comparison, using first-party English documentation

Docs consulted:
- Wallet detail: https://docs.gmgn.ai/index/wallet-detail-page ; built-in wallet notes, 7D/30D trade counts/PnL, realized/unrealized, token cost, holding time, position distribution, transfers/not bought vs sell > bought/HFT behavior.
- Follow, monitor square and watchlist: https://docs.gmgn.ai/index/follow-monitor-square-follow-watchlist ; multi-window tracked inflows, following, manually saved token groups and notes.
- Token page: https://docs.gmgn.ai/index/token-page-chart-multicharts-activity-trading-system ; detailed activity, holder and trader sections, source/TF time, buy/sell average, PnL.
- Wallet Radar: https://docs.gmgn.ai/index/wallet-radar ; multi-token wallet overlap and profit/activity classes.

| User-important capability | GMGN documented / screenshot | Current local dashboard in main | Design action |
| --- | --- | --- | --- |
| Real on-chain buy/sell timeline | token and wallet history, periods | newest 50 *recognized* trades, no explicit period label | all-event ledger + actual market swap view, time filters and pagination |
| Distinguish passive transfers | transfer-in/out available, specific non-bought labels | passive class exists inside parser but not in primary UI | visible clearly-labeled transfer/receipt/reward rows; no false BUY |
| Token holdings and wallet PnL | positions, cost basis, realized/unrealized | no independent held-token portfolio; no per-mint full PnL | separate wallet position ledger; price/cost completeness badges |
| Persistent watchlist | followed-wallet inflows + saved token groups | `/api/candidates` only signal-eligible subset; recent exited limited 24h | independent durable WATCH/HELD/TRIMMED/EXITED/FAVORITES list |
| Multiwindow activity | 1m/5m/1h/6h/24h watch; 7D/30D wallet metrics | 24h primary counts, 7D/30D coverage collapsed | explicit separately labeled rolling windows and lifetime with completeness |
| Token/pool/narrative | market chart, social and token context | generic manual CA report under separate accuracy-remediation | open CA research detail with source stamps and GMGN comparison |
| Fast one-click trading | available on GMGN | deliberately excluded in Mission | **No RPC signing / no local orders**; only evidence and external links |

**Parity principle:** GMGN is useful as a **UI/function reference and external bounded manual comparison**, not automatically ground truth for exact PnL, identity or transaction semantics. No paid GMGN API, no guessed GMGN authenticated endpoints, no CAPTCHA bypass. Independent raw transactions determine observed facts; source windows/transfer treatment/cost accounting must match before declaring a data discrepancy.

## 5. Data-confidence verdict and unresolved facts

**CONFIRMED**
1. Current implemented candidate filter hides non-signal-held or watched tokens by construction.
2. Historical Oct 9 screenshot trades precede Oct 11 04:48 by ~44h and need not count in last-24h values.
3. At least two directly decoded most-recent Frank account signatures were passive inbound token transfers signed by someone else; treating them as new Frank BUYS would be false.
4. Current local 24h window is explicitly **LOCAL_INDEX_ONLY** and does not certify chain completeness.
5. Broad backfill hit Alchemy RPC 429.

**NOT VERIFIED**
1. The complete 24h or 7D count of Frank's true active buys/sells.
2. Whether the specific screenshot's Oct 9 3,300 buy and 2,232.34/7,031.56 sales exactly match original explorer transactions. Need their full signatures and independent transaction readback; screenshots alone are not proof.
3. Wallet-wide or baton-specific GMGN PnL parity; held-token cost basis, transfers and time ranges need same semantics and historical completeness.
4. User's current Mac runtime version and source-archive completeness beyond the screenshot.

No numerical profit, unseen trade, hourly false negative or passing data-parity test should be inferred from the available evidence.
