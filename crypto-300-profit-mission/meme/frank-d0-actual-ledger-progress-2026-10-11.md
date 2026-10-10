# Frank D0 实际执行与数据账本重建进度（2026-10-11）

Status: `D0_REAL_CHAIN_SAMPLE_PASS / D0_LOCAL_INDEX_EXTRACTOR_TESTED_SYNTHETIC / FULL_RECONCILIATION_INCOMPLETE / D1_FULL_WALLET_LEDGER_NOT_BUILT / PRODUCTION_UNCHANGED`
Research branch: `research/frank-wallet-v2-d0-readonly-20261011`
Production authority: `PRODUCTION_TRADING=NO_GO`; original Frank Writer, current Dashboard, Gmail, launchd and frozen follow policy stay unchanged.

## 1. Actual data and sources, not mocked

Canonical Frank Solana wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`.

Read-only RPC: Alchemy `solana-mainnet`, finalized commitment, `getTokenAccountsByOwner({owner,mint})`, supplemented by `getSignatureStatuses(searchTransactionHistory=true)`.

The **exact structured actual result** is stored at:
`meme/evidence/frank-d0-six-mint-finalized-2026-10-11.json`.

Six historically audited selected trade cases, latest read:

| Mint | Current raw units | Decimals | Token quantity | Finalized slot | Direct-chain status |
| --- | ---: | ---: | ---: | ---: | --- |
| `MukLDtJ8Cx9DxLbeyLRSWPSposTMWuwHANbuaudpump` | 33586031 | 6 | 33.586031 | 455413478 | NONZERO |
| `8K5X85PAJHAAVSvYaAzgVPPAPsqqHmvx16ZyBiscYF8L` | 327203717034 | 9 | 327.203717034 | 455413479 | NONZERO |
| `E4Ap4icMLwKot8rkkTbq5JkS5kZxt5XCE3yfxbzYBjHx` | 0 | 9 | 0 | 455413478 | ZERO |
| `PerPsCe2SJ7Q25CN4R5TTX4fmBdmknE2hQmqCt96fHL` | 0 | 6 | 0 | 455413480 | ZERO |
| `4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta` | 0 | 6 | 0 | 455413479 | ZERO |
| `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy` | 0 | 6 | 0 | 455413480 | ZERO |

Important: prior Git research says these six selected **trade episodes** closed; their economic trade lots can close while the corresponding current wallet account retains positive residual inventory, including post-close transfers or incentives. Never auto-classify a nonzero remainder as a new Frank trade or a sizeable held investment. Conversely, never delete such owner balances just because the signal episode exited. USD prices were **not found** by a direct Alchemy Solana token-price lookup for the two nonzero records; both current USD valuations remain `UNPRICED`, not invented <$1 or $0.

### Actual additional verification for TWEETCRAFT

- Mint: `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy`.
- Historical original first buy tx `4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S` => `finalized`, `err=null`, slot **454400785**.
- Historical original sale tx `5wqKv5YuurRKUaJAK5fZtFrNg6GocVZuTTiAPWYrYDaswyUArwAZurpbZFU6WBjHp5z5Bt5bPCkLNKVQHfS6yigx` => `finalized`, `err=null`, slot **454718132**.
- Fresh token owner account `7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG` returned `0` raw at slot **455413480**.
- Prior independently researched full cash flow (reference `meme/FRANK_TWEETCRAFT_ROOT_SWAP_EVIDENCE_20261009.md`): spent `6715.734492` USDC, net returned `7031.556770` USDC, difference `+315.822278` USDC for **that selected round trip**, not whole wallet PnL.
- A new `getTransaction` call for the complex sell tx was **clipped after 8098 bytes** by the current tool response; do not claim its entire raw current read was parsed again. Fresh independent confirmation is **transaction finalization status and account quantity**; precise net flows retain prior proven source provenance.

### Historical 24h scope

The user screenshot is ~2026-10-11 04:48 BKK. Shown 2026-10-09 ~08:27 BKK transactions are ~44h old, so they cannot count in that screen's last-24h counters. `198` local signatures is not a count of confirmed active swaps. Still no full independent verification of all 24h buys/sells, since Alchemy pagination earlier hit RPC 429 after 132 sampled signatures.

## 2. Actual offline read-only extractor candidate

Files introduced on this **research branch only**:
- `local-agent/scripts/frank_wallet_d0_snapshot.py`
- `local-agent/tests/research/test_frank_wallet_d0_snapshot.py`

The script:
1. Requires an **existing** `forward.sqlite` (read-only `mode=ro` plus `query_only`); does not bootstrap a writable database.
2. Computes indexed signature classifications and recognized trade counts in one explicit 24h UTC window. It keeps scope `LOCAL_INDEX_NOT_FULL_CHAIN`, always `chain_completeness_verified=false`.
3. Extracts recognized historical trades (with exact original quote semantics as available) from local `trades` and joins `signatures`; deduplicates wallet/signature/mint/side/time.
4. Seeds research-only visible `watch_seed` from the union of local recognized trade mint history and all `v1_states` mints, **even if zero active follow candidates**. Never treats a model `OPEN` as chain-verified inventory.
5. Highlights rounded screenshot candidate quote matches `3300.00`, `2232.34`, `7031.56`, with status `LOCAL_INDEX_ONLY_NOT_INDEPENDENT_CHAIN_VERIFIED`, no backfilled fabricated signature.
6. Emits JSON to stdout or an explicitly provided output path; no read/write access to live policy, alerts, Gmail, wallet, trade execution or control state.

**Actual isolated test result:** `python -m unittest discover -s /mnt/data/frank_d0 -p 'test_*.py' -v` => **5 tests PASS** and standalone `py_compile` PASS. Synthetic fixtures check 44h history/24h-zero separation, watch retention, passive transfer not buy, trade dedupe, zero account balance/PnL never assumed from a local view, strict missing-db failure. These tests ran in the assistant's isolated container, **not** on the actual Mac `forward.sqlite` or against the installed checkout. The Git-uploaded test location imports the sibling `scripts/` module and is intended for the repository's normal test runner; the full repository suite/CI and independent AI review are **NOT_RUN** at this checkpoint.

## 3. Why this is not a finished ledger

Current D0 extractor is an **initial audit-only local-index universe**, not complete wallet transaction or holdings history. It does not include unclassified/passive-only token mints in watch_seed, does not independently fetch or price on-chain accounts, does not reconstruct FIFO PnL, and does not establish full historical source completeness. Its purpose is to reproduce the current UI filtering bug using the real local database when available without touching production.

To complete D0, obtain an explicit read-only snapshot of the actual Mac production DB and source-archive version, extract exact screenshot Oct 9 signature matches, replay and independently verify full 24h/7d source coverage, then show missing signatures, token account ownership and format assumptions. No invented counts before source readback.

D1 will extend the facts layer with passive receipt/transfer and delegated route distinctions, full token inventory reconciliation, bounded source-aware price coverage and persistent watch register. D2/UI begins only once representative D1 data invariants pass. Independent AI review and actual Mac acceptance are mandatory before any deployment; keep production isolated.

**No additional automation, local LaunchAgent, notification, order signing, account mutation or service restart.**
