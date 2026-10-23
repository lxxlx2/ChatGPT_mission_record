# Frank D2 — offline full-owner at-slot balance preview (code-only)

Date: 2026-10-23 Asia/Bangkok

Scope: **CODE_ONLY / DRAFT / OFFLINE_PREVIEW / NO_NEW_RPC / NO_MAC_RUN / NO_PRODUCTION_DEPLOY / NO_TRADES**.

## Why this exists

The Mac's new approved 2026-10-23 21:46:32–34 +07 full-owner SPL Token and Token-2022 source was captured and independently replayed with PR #60 fixed SHA `e4529ba7069e5499d12323a7160ceac08c481fae`. [Issue #165 evidence](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6367661272) proves 1,875 + 2,273 token-account records at **two different finalized slots** 460482174 and 460482176. That is an authoritative pair of **dated point-in-time program reads**, **NOT** a single atomic or continually live portfolio value. The user has approved **D2 adapter/offline preview development only**, not live use of another RPC or production install.

The already deployed `wallet_inventory.py` accepts historical 32-mint-filtered records and labels them `DATED_POINT_IN_TIME_NOT_LIVE`; the full-owner PR60 snapshot has a **different source schema**. Converting it into the old status would conceal all-account provenance and invite dangerous false-live claims. Do not do that.

## New code and data contract

- `wallet_owner_at_slot.py`: pure in-memory adapter of an **original PR60 offline replayed** snapshot plus existing local observed watchlist and target Mint list. It checks the replay capture fingerprint, exact owner, both programs/finalized slots/account identity and counts, raw integer sums, mint decimals, duplicates and declared mint projections. No RPC, DB, price, notifications, signals or writes.
- `scripts/frank_d2_owner_preview.py`: manual CLI that refuses a nonmatching/dirty PR60 checkout, verifies pinned module bytes, invokes the original `replay_owner_full_receipts` inside a network-disabled Python child and generates only a private mode-0600 offline HTML file. It does not modify production Dashboard. The raw HTTP bodies remain exclusively in the existing private Mac evidence bundle.
- HTML is self-contained, no CDN or network. At most **200 visible Mint rows** by default, prioritizes target 32 and at-slot observed watchlist data, reserves a bounded sample of outside-watchlist Mint rows; search only covers this rendered subset. It **never embeds individual Token Account pubkeys or all 4,148 private account records**.
- States: `NONZERO_AT_SLOT`, `ZERO_AT_SLOT` **only when actual account rows are present**, and `NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS` otherwise. None imply purchased/sold, complete history, ever-held, cost, PnL or a present trade recommendation. Local model and signed last event are independent columns.
- Clear timestamps (UTC, Bangkok), age at preview creation, program slots/account counts, outside-watchlist Mint count and the fact that two calls are non-atomic. `current_chain_balance_verified=false` by design because this cannot remain real-time after capture.

## One manual Mac isolated preview, only after CI and independent source review

An operator may work only in isolated clean detached checkouts of this branch's exact reviewed SHA and **PR60** `e4529ba7069e5499d12323a7160ceac08c481fae`. First save the **already allowed GET-only** `/api/frank-observed-watchlist` response into a private local file (0700 parent / 0600 file). Do not let the CLI request it directly. Use the existing private October 23 owner raw archive and the repository October 11 32-Mint target roster.

Example invocation after filling in true local paths:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 crypto-300-profit-mission/local-agent/scripts/frank_d2_owner_preview.py --pr60-checkout "$PR60_CHECKOUT" --bundle "$PRIVATE_OWNER_BUNDLE" --watchlist-json "$PRIVATE_WATCHLIST_JSON" --output "$HOME/.local/share/frank-d2-preview/owner-at-slot.html"
```

The script requires `--pr60-checkout` and a private output directory, refuses existing output, and never prints per-Mint quantities/paths to stdout. **Any Git repository, its linked worktrees and its `.git` metadata are forbidden as preview output locations**, including a different clone from the code checkout. Output paths are lexically normalized before creating files; path components which are symlinks are rejected. On macOS, `/tmp` and `/var` are normally aliases into `/private`; use a resolved actual directory under `/private/…` or a canonical private `~/.local/share/…` directory instead. Git detection failures block output rather than making a guess. The output file is mode 0600 under a mode-0700 private parent. Optional `--targets-json` overrides the repository fixed Oct11 target file. The offline HTML is **sensitive wallet observation data** and should never be uploaded to the public GitHub repository. Never put RPC URLs/API keys in CLI arguments.

## Mandatory gates before any Dashboard UI/production integration

1. New PR exact SHA with targeted offline Node-free Python CI PASS, independent other-model review, source negative-path review and careful private file-output audit. CI uses **synthetic account fixtures only**, no private source.
2. Once approved, **one Mac isolated private offline replay + HTML open/read-only acceptance** on the exact same SHA, with byte hashes, fixed PR60 provenance and no network; submit only redacted assertions/hashes and no raw contents.
3. Only then design a **separate Dashboard read-only D2 ingestion/UX release**, with user approval required for local production import and Dashboard-only cutover. It cannot reuse the Oct11 filtered schema as if it were full-owner proof or silently mark perpetual current balance.
4. Preserve existing Frank V1/MC Loop, original notifications and frozen G1, no new local daemon, no new RPC, no Gmail/outbox, no trade, no merge/production action.

**Not supported**: native SOL, closed historical token accounts, same-slot atomic balances, indefinite live portfolio, priced token NAV, user PnL, sale event inference, partner/wallet beneficial ownership or all tokens outside the two official Solana Token programs.
