# Frank V2 持续观察池：实际数据核验与只读实现进度

Updated: 2026-10-11 Asia/Bangkok
Branch: `research/frank-wallet-v2-d0-readonly-20261011`
PR: https://github.com/lxxlx2/ChatGPT_mission_record/pull/31
State: `READ_ONLY_WATCHLIST_IMPLEMENTED_ON_RESEARCH_BRANCH / SYNTHETIC_INTEGRATION_TESTED / REAL_CHAIN_SELECTED_BALANCES_CHECKED / MAC_DEPLOYMENT_NOT_DONE / INDEPENDENT_AI_REVIEW_NOT_DONE`

## Confirmed findings and time scope

User Mac local ZIP `frank-ca-evidence-20261011-053908.zip` has `frank-d0-local-index.json`. Its local source (not guaranteed full on-chain history) yields:
- **1,660 local lifetime signature rows** and **199 indexed in previous 24h**, of which 153 passive transfers, 39 failed transactions, 6 ATA creation and 1 active trade classified.
- **32 historical observed token mints** in union of recognized local trades and existing V1 states, even while Dashboard showed **zero qualified follow candidates**. Their local states are **5 OPEN**, **13 CLOSED**, **2 INVENTORY_UNDETERMINED**, **12 UNKNOWN**.
- Mac screenshot Oct9 transactions have signatures restored by D0 audit; their amount labels from local index, actual status finalized, but complex routed full cash flow is still not independently fully re-decoded.
- All 23 originally exported CA/Frank blobs in `evidence/frank-ca-local` were independently Git readback-matched; regular continuous upload remains OFF.

Fresh **direct Solana finalized** owner/mint queries to Frank wallet `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ` checked 5 OPEN and 2 INVENTORY_UNDETERMINED mint accounts at slots **455426889–455426895**:
- The **five OPEN all had positive balances**, with raw quantities preserved in research branch `meme/evidence/frank-v2-seven-wallet-open-mints-2026-10-11.json`.
- One local inventory-uncertain mint `CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU` had raw balance **0**; the other `GTBxUiw6wJdmmkCGZgRHLyYxqu1vG4KtRpeox6yDpump` had **50.017498** tokens.
- These are snapshot quantities, **not** independently priced USD, nor proof of full mint market liquidity or wallet profit.
- A `CLOSED` historical trading episode may still have token residuals, as seen in previous D0 six-mint audit. Closed *episode*, current *token account* and current *liquid investment exposure* are three distinct concepts.

## Implemented design, without changing production

Research branch changes:
1. `local-agent/mission_agent/mission_control/wallet_watch.py`: new stand-alone read-only builder using the **full locally indexed recognized-trade history** plus all per-mint V1 model rows. Includes all locally observed token mints even without any ACCUMULATION/MULTIPLE signal, organizes into `MODEL_OPEN`, `NEEDS_INVENTORY_REVIEW`, `HISTORICAL_EXIT`, `WATCH_UNRESOLVED`, `HISTORY_SELL_ONLY`, `MODEL_STATE_ONLY`. Preserve exact latest signature/time, historical buy/sell counts and native quote leg where reconstructible. The data explicitly labels `LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN` with `current_chain_balance_verified=false`, `market_value_usd=null`, `pnl_usd=null` unless independently justified. Conflicting different trade legs sharing one wallet/mint/signature do **not** silently become a precise single quote.
2. `server.py`: adds the independent `GET /api/frank-observed-watchlist` endpoint with fail-closed `SOURCE_UNAVAILABLE` response. Existing `/api/candidates`, `/api/trades`, Frank writer, quote/signal policy and Gmail delivery unchanged.
3. `static/index.html`, `static/app.js`, `static/styles.css`: read-only **persistent observed-token panel** before formal actionable candidates; all-token search, per-status filters, latest transaction reference, Solscan and GMGN public links. Model-held counts are labeled *not chain-confirmed*. A failed watch endpoint does not blank existing other panels.
4. `evidence_sync.py`, `service.py`, `scripts/meme_evidence_sync.py`: opt-in evidence uploader now records a local-index watchlist snapshot on **material writer polls**, separate from actionable signal-only candidates, with whitelisted fields. Quiet polls still retain small poll checkpoints. This is disabled by default and remains within existing loop when installed and enabled later.
5. Tests `tests/test_frank_wallet_watchlist_v2.py` and `tests/test_meme_evidence_sync.py`: historical >24h events retained, no formal signal required, 32-state Mac baseline, no fake current inventory/value, duplicate trades and conflicting swap legs, Git export of 32 entries with no signal, missing DB and readable UI paths.

## 2026-10-11 D1 extension: all-32-mint finalized balance audit and complete local trade export

**Actual independent on-chain facts:** all **32/32** mints in the user's 2026-10-11 D0 local trade/model observed universe have now been checked individually with Alchemy Solana finalized `getTokenAccountsByOwner(owner,mint)`, recorded across slots **455426889 to 455430371**. **10** returned positive raw balances and **22** returned zero at their respective read slots. Of the 10 positive: **5** local model OPEN, **1** local model INVENTORY_UNDETERMINED, **3** model CLOSED, and **1** model UNKNOWN. These are sample quantities, **not** equal-timestamp atomic reads, verified USD marks, complete passive-receipt token universe, or proof of Frank PnL. The 3 model-closed-with-balance exceptions are **7Vert…pump**, **BXo…pump**, **F5Wv…**; UNKNOWN-with-balance **7KEPA…**. All exact CA, raw amount, decimals and slot sources are in `meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json` on research PR #31.

**Code actually implemented on research PR #31 only:**
- `local-agent/mission_agent/mission_control/wallet_inventory.py`: strict read-only merging of dated finalized owner/mint evidence into historical watch rows; chain snapshot proof and local model state are kept separate. Strict wallet/network/finality/mint/raw-decimal/slot validations; no fake currently live balances, current NAV or realized PnL. The read-only Dashboard loads optional `<control_root>/frank-inventory-snapshot.json` if manually present; otherwise source stays "SNAPSHOT_NOT_PRESENT"; invalid input is safely ignored.
- Watchlist UI now filters `样本余额非零` and `模型与链上有差异`, prioritizes known positive observations and shows source date/slot explicitly. Snapshot and model status never automatically generate Frank BUY alerts.
- `local-agent/mission_agent/mission_control/wallet_history.py`: read-only export of **every locally recognized** historical trade leg with signature, mint, side, original quote/raw units, route uncertainty and local-index classification. It preserves conflicting multi-leg transactions without false single price. Direct USDC observed inbound/outbound subtotals are labeled **unreconciled local cashflows, not PnL**; missing transfer cost, SOL fees, complete historical scan or routed trade decoding leave PnL `null`.
- `evidence_sync.py`: content-addressed Frank-history artifact with SHA256 chunking, remote Git content readback verification and failure-pending preservation on the dedicated evidence branch.
- `frank_evidence_bootstrap.py`: adds full sanitized local-history packet and optional `--inventory-evidence` to join the preserved 32-token finalized proof to the latest Mac local model without network read/restart/production modification. Its ZIP includes a new dated reconciliation artifact.

**Actual CI success:** [Run 38094380397](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38094380397), exact research head `4bcf7c32902dfd58f1c12b833776878b01536316`: **43 new exporter/watch/inventory/history tests passed + 80 existing Dashboard/Mission Control/Delivery tests passed**, Python syntax compilation and Node JS syntax checks passed. Earlier transient CI failures were fixed with source-correct scope labels and preserved exact USDC decimal formatting. This is real GitHub CI **not a Mac live deployment or independent AI review**.

**Remaining data blocker:** currently uploaded Mac ZIP contains only D0 latest-per-token normalized history, not full `forward.sqlite` trade ledger. Historical PnL and transaction-by-transaction confirmation need the **new sanitized one-shot history packet**. The script is prepared and test-gated; original production Frank remains unchanged. Full cross-platform GMGN parity, full wallet accounts (especially passive receipt-only mints), external CA narrative and independent AI review are still outstanding. `PR31_DRAFT=YES / PRODUCTION_DEPLOYMENT=NO / LIVE_EVIDENCE_AUTO_EXPORT=OFF / PRODUCTION_TRADING=NO_GO`.

## Acceptance and unresolved development

Passed (up to latest reported GitHub CI on research branch):
- isolated GitHub workflow compiles new Python code, validates JS syntax, runs exporter/watchlist tests plus 80 historical Dashboard/Control/Delivery regressions. The precise current HEAD and run outcome must be checked before claiming a new post-checkpoint result.
- selected actual chain owner balances checked by direct finalized RPC and preserved in source evidence JSON.

**Not done**: full Mac SQLite replay with newly deployed code, live Dashboard real screenshot, independent AI code review, full PnL and cost-basis reconstruction, all-mint complete chain balance/price discovery, manual favorites/notes persistence, passive-only observed mint inventory, complete historic wallet backfill, source parity against GMGN/FOMO/OKX for identical windows, and user-authorized rollout. The research-side watchlist is a meaningful **D1/D2 partial deliverable**, **not** finished GMGN parity.

No production file, monitored service, launchd, Gmail, wallet or live trading setting was altered by these Git commits. `PRODUCTION_TRADING=NO_GO`. Future continuous evidence syncing remains OFF unless separately reviewed/deployed and explicitly enabled.
