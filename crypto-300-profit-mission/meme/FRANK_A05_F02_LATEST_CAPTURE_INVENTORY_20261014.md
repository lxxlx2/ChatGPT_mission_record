# Frank A05 → F02 latest account evidence, before real Mac position display

Date: 2026-10-14 Asia/Bangkok
Stage: `RESEARCH_READ_ONLY_CODE / EXACT_SHA_CI_AND_EXTERNAL_REVIEW_PENDING / NO_LIVE_DISPLAY / NO_DEPLOY`

## Scope and problem

A05 already saves manually captured, independent finalized SPL Token and Token-2022 owner account inventories in a research-only immutable SQLite Sidecar. However, manually reading the previous Mint-specific provider does not establish the **latest** snapshot across both programs: a historical older snapshot can contain a positive quantity even when a newer capture is partial or no longer contains that Mint. F02 must never render such older evidence as a current balance.

This step implements a single-purpose **latest immutable-capture inventory projection**, not an RPC collector, production app update, price feed or trade classifier:

- `mission_agent/mission_control/wallet_inventory_snapshot.py`: input wallet, explicit list of 1–128 exact valid Solana Mints (32 accepted as specific target-size checkpoint), a trusted UTC `as_of_utc` and max source age; fetches the most recent captured account source by highest slot before resolving any Mint, validates archived snapshot SHA, and fails closed if a snapshot is future dated/malformed.
- `scripts/frank_research_latest_inventory.py`: explicitly read-only CLI; requires a Mint JSON file, existing Sidecar and wallet address. No RPC calls, raw signing, production SQLite connection, LaunchAgent or mail. Returns one JSON report with exact source SHA, finalized slot range, capture age, observed token account list, and all requested Mints (including unresolved).
- **Latest-source correctness:** a recent missing Mint in a *complete* both-program capture is `ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN`, reported with `observed_raw_amount=null` and sale proof false — never an assertion that old holdings were sold. A recent partial capture without a Mint is `UNKNOWN_MISSING_PROGRAM`, never 0. For a partial capture containing one program's amount, `PARTIAL_PROGRAM_OBSERVED_NOT_WHOLE_BALANCE` explicitly prevents claiming a complete wallet amount. Stale capture is `STALE_SNAPSHOT` and masks quantities.
- **Source truth:** two RPC program calls are *non-atomic* even when both succeeded. Slot min/max, non-atomic flag, wallet, source capture SHA and age remain explicit. Never claim `current_live_balance_verified`, person beneficial control, NAV, cost basis, BUY/SELL or PnL.
- **Evidence integrity:** archive payload SHA is independently recomputed on read; content mismatch is an error, not false confidence. Only saved research-sidecar captures are used; no zero-by-default or fallback to stale prior holdings.
- `tests/test_frank_a05_f02_latest_inventory.py` covers *older positive → newer complete absent*, *older positive → newer partial unknown*, multi-account same Mint, stale source, partial program with visible observed raw amount but no complete balance, missing capture, altered payload and 32 exact distinct user-supplied Mints.

## Business boundaries and acceptance still required

This is an A05→F02 **research bridging checkpoint**, not finished live F02 or complete 32-Mint acceptance. The exact 32 Mints have not been independently exported from the user's latest production Mac registry; no live production wallet snapshots are fabricated into tests. Observed balances are not a trade history or sale proof. No price means USD value stays null.

Before F02 can display balances on a production Dashboard:
1. Read the exact **user-approved 32-Mint roster** from latest Mac evidence (not hardcoded guesses).
2. Run one manual A05 owner capture with both finalized programs, record immutable source SHA and two slots; handle full owner-account scope or explicit `PARTIAL_SOURCE`.
3. Independently verify material non-ATA accounts, wallet owner semantics and any mint-specific discrepancies; compare source time to UI freshness budget and ensure no older snapshots are resurrected.
4. Independently review this new module code on **its final exact SHA**. Then integrate F02 under read-only Mac/real browser acceptance, independent cross-module review and eventual final whole-product review as mandated by `docs/DEVELOPMENT_REVIEW_POLICY.md` [Draft PR #55](https://github.com/lxxlx2/ChatGPT_mission_record/pull/55).
5. Preserve all previously reviewed A04 #54 code and C02 #49 code; no merging/deployment/user trade without separate approval.

**Known historical gaps unchanged:** full failed parsed transaction, genuine owner-missing nonzero, ATA close, full wallet and 32-Mint history, realized PnL and full CA holders/funding analysis.

## Explicit manual use (zsh, no background scheduling)

After separately capturing a research-only Sidecar and preparing a JSON array file containing the exact requested Mints:

```bash
cd crypto-300-profit-mission/local-agent
python3 -m scripts.frank_research_latest_inventory --wallet 498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ --mint-file /path/to/verified-32-mints.json --sidecar /path/to/research-wallet-evidence.sqlite --max-age-seconds 300
```

This only reads existing local data; the tool does not automatically obtain a new chain snapshot. A stale or missing source is not claimed current.
