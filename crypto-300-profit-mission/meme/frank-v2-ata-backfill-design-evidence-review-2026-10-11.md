# Frank V2 — Independent Solana ATA historical backfill, source reconciliation and release gates

Date: **2026-10-11**, Bangkok timezone.
State: **RESEARCH CODE AND CI PASS / SOME ACTUAL ON-CHAIN DATA VERIFIED / EXTERNAL AI REVIEW NOT RUN / MAC PRODUCTION UNCHANGED**.
PR: https://github.com/lxxlx2/ChatGPT_mission_record/pull/31
Evidence: `evidence/frank-ca-local` (user Mac original signatures/transfer archive); new public ATA source summary saved in PR #31.

## 1. Root cause: why Frank sold tokens invisible to its wallet-owner feed

The frozen original `local-agent/mission_agent/frank/rpc.py` uses Solana `getSignaturesForAddress` **only on the main owner address**. External payers may make SPL Token / Token-2022 transfers directly to an associated token account without the owner public key being present among transaction accounts.

The 2026-10-11 real normalized user Mac snapshot contains **1,720** owner-address indexed signatures: 1,393 passive, 78 active trade, 81 ATA create, 98 failed and 70 unknown. It exposes wallet-owned token deltas across **224** mints versus **33** trade/model mints. It does **not** supply parsed transfer source/destination arrays for any of its 1,720 records. Chain completeness therefore CANNOT be established from the wallet owner's signature stream alone. The 104 new passive-only Mint observations are not automatic BUY ideas, material market positions or verified USD holdings.

The `J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump` case demonstrates the defect concretely: direct chain evidence confirmed **three** passive transfers to Frank's J7 token account totaling **12,508,217.470763 J7**, while the archived owner stream contains only **one** of the three (2,846,838.050235 J7). The missing two arrived in finalized slots 454705824 and 454705939 and total **9,661,379.420528 J7**. A later local sell of the entire 12,508,217.470763 J7 quantity cannot have an attributed original acquisition cost based on the main-wallet local index.

## 2. Token-program correctness

Solana canonical ATA PDA derivation must include seeds `[owner, TOKEN_PROGRAM_ID, mint]` and use the associated-token program. The token program is **part of the address**. Both programs need coverage:

- SPL Token: `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`
- Token-2022: `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`

The real J7 mint is **Token-2022**, independently verified against the `programId` attached to finalized pre/post token-account balances. Its canonical Token-2022 ATA is `FjESMbdMaDapesMo889siXL1oQmgvQz8wsLTnHKeTNem` (PDA bump 255); using old SPL Token creates the *different* address `DbEAuRyJKJYcs6DS1TeLNph7snPDcXqwTqXVrmNyNhLe` (bump 253) and misses J7's actual receipts. For the earlier **12** sell-only-mint account addresses, pure canonical PDA verification found **8 Token-2022 and 4 legacy Token**. This does not discover noncanonical historical token accounts.

## 3. Real on-chain J7 ATA scan performed (not synthetic)

Alchemy Solana finalized `getSignaturesForAddress(FjES…TNem, limit=100)` returned **17 signatures**: **4 successful and 13 failed**. The four successful correspond to the three prior inbound transfers and later signed sale. The two owner-index-missing transfers were independently read using finalized `getTransaction` (raw `json`) and cross-checked:

| UTC date/time | Signature prefix | Received J7 | Finalized slot | Frank signed? |
|---|---|---:|---:|---|
| 2026-10-09 00:31:43 | `dveTCqqE…` | 5,000,000.000000 | 454705824 | No |
| 2026-10-09 00:32:14 | `4JMFca46…` | 4,661,379.420528 | 454705939 | No |

Both transactions were successful and signed by the external source wallet `VP4B4yj63FNP4BZLZdBJYRsTi1LqUuUENY8wfAdtSn8`. The exact before/after wallet token-unit differences match. **Neither transfer proves the source wallet's cost basis, a Frank market buy or realized PnL.**

Additional direct bounded ATA signature checks succeeded for five other sell-only accounts: `31k88G5…` 4 signatures (all succeeded), `5PiBn5J…` 2 (all succeeded), `6e8LLHk…` 3 (two succeeded, one failed), `7KEPApd…` 3 (all succeeded), `8dBnKHw…` 2 (all succeeded). The next address `8nnaeWC…` hit the provider's HTTP **429 rate limit**. No more accounts were claimed verified from that batch; there is no rate-limit circumvention, invented continuation or inferred token costs. Machine-readable source record: `meme/evidence/frank-v2-ata-j7-and-five-account-chain-verification-2026-10-11.json` on PR #31.

## 4. Independent research implementation in Draft PR #31

`local-agent/mission_agent/mission_control/ata_backfill.py`:

- Pure Python standard-library Ed25519 PDA/on-curve and base58 derivation for **both** Token Programs.
- Manual 1–12-mint scope, `getSignaturesForAddress` on each derived ATA rather than on the wallet owner; bounded 1–100 signatures per page, 1–4 pages per ATA and at most 120 unique transaction-detail requests per invocation.
- Solana `getTransaction(jsonParsed)` with finalized commitment; verifies Mint, token program, ATA pubkey, Frank ownership and exact raw pre/post token units before reporting a balance change.
- Distinguishes successful vs failed, absent vs partial balances, local-index-known vs genuinely new signature, both-token-program account coverage and bounded vs time-stopped pagination.
- Reports no current live wallet balance, no cost basis, no overall chain completeness, no follower signal and no realized profit. No transaction signing, wallets, market orders, original Frank Writer or Gmail modifications.

`local-agent/scripts/frank_ata_backfill.py`:

- **Explicit manual** read-only `--mint` and `--database` with `--output`; reads only original local signature IDs from existing SQLite, does not mutate the database or production services.
- Uses the existing bounded public Solana RPC client. All failed RPC/identity/required balances produce clear non-success rather than fake evidence.
- Writes local JSON as exclusive file creation (0600; refuses overwrite); optionally `--sync-git` to the **existing independent `evidence/frank-ca-local` branch**, content-addressed by SHA256 with exact Git remote readback using existing uploader. If Git upload fails, the local artifact is retained and command returns nonzero.
- No new launchd, scheduler, background monitor or production setting.

The current code only handles **canonical associated token accounts**, not arbitrary delegated, historically closed or unusual token accounts whose derivations cannot be established. Full 224-mint/account enumeration is a separate bounded archival/data-source milestone; no claim of GMGN parity.

## 5. Actual CI and independent review gates

Confirmed GitHub Actions:
- [Run 38124368713](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38124368713): **16 ATA unit/integration tests and entire local-agent suite 1,134 passed**.
- [Run 38124495963](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38124495963): **entire local-agent suite 1,135 passed** including a mandatory real-Git-archive regression that demonstrates the J7 derived Token-2022 ATA and two missing receipts against the 1,720-signature source. These counts are run-specific; later code must obtain new CI results before claiming validation.

**External second-AI review still REQUIRED and NOT DONE.** Reviewers must inspect the actual code/diff for PDA correctness against Solana SDK, retry and provider failures (including 429), read-only method constraints, identity proof, missing-pre/post guards, injected or duplicate signatures, cap-exhaustion semantics, readonly SQLite, Git secret redaction, host path metadata, source hashes and no production writer/Gmail/trade policy change. The independent reviewer must produce an identifiable report and list any release blockers. Local Mac one-shot and actual UI validation are separate later gates, not CI equivalences.

Hard release flags:
`ATA_READONLY_CODE=IMPLEMENTED`
`J7_MISSING_SIGNED_TRANSFERS=CHAIN_VERIFIED`
`ATA_BULK_ALL_12=NOT_COMPLETE_RATE_LIMIT`
`EXTERNAL_AI_REVIEW=NOT_DONE`
`USER_MAC_NEW_VERSION=NOT_DEPLOYED`
`PRODUCTION_AUTO_ATA_SCAN=OFF`
`PRODUCTION_TRADING=NO_GO`


## 6. 429 partial-save correction and duplicate signature protection

During the first bounded real-provider batch Alchemy returned 429 after earlier successful ATA signature reads. Initial research code would have stopped on an RPC exception before emitting any of the earlier verified results. **This was identified and fixed before release**: the independent ATA scanner now catches network/RPC exceptions, records `scan_status=PARTIAL_RPC_INTERRUPTED`, `interruption_type`, all already independently validated signature and token-balance observations, and the number of canonical ATA addresses left unscanned. It then **stops** rather than immediately querying additional addresses against the rate-limited provider. The manual CLI retains the partial JSON as `0600`, and returns **nonzero exit status 3** even when prior evidence survived and optional Git publishing succeeded. A missing source is never called a complete successful scan.

An additional source-account deduplication guard now uses `(derived_token_account,signature)`, not only the RPC transaction cache, to avoid counting repeated Solana signatures from overlapping pages twice. Different ATA accounts in the same transaction remain distinguishable; known original Frank owner-stream signatures are marked but not claimed as new wallet activity.

Regression tests exercise the exact 429-after-J7 scenario, interruption with already-validated rows, independent observable `RPC_INTERRUPTED_PARTIAL` state, local packet retention, and duplicate signature removal. A provenance test independently derives **all 12** previously observed sell-only token accounts from their Mint and verified program IDs, checking the **8 Token-2022 / 4 Tokenkeg** classification. No production deployment or second-AI review has occurred.

## 7. 2026-10-11 latest 1,148-CI gate, actual BPxx 70-vs-1,720 replay, and independent review input

**Current reviewed-by-CI research code HEAD:** `87a0611bacbd46fc044aec79a941dbf9ec3c88e8` on Draft PR #31. **Actual Actions run [38145047270](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38145047270) SUCCESS**: ATA-focused **28 passed**, prior Frank V2 focus **65 passed**, existing Dashboard/Control/Delivery **80 passed**, **full local-agent suite 1,148 passed**. Focused tests are subsets, never to be summed. This proves CI acceptance of isolated code, not independent AI review or installation on the user's Mac.

### Actual source-account completeness discovery

New bounded live finalized Alchemy `getSignaturesForAddress` evidence in Draft PR #31:
- Six previously incomplete ATAs (8nnaeWC, BPxx, EFn88, GZw7, GoAD, wdys): 25 first-page signed transactions (21 successful, 4 failed); first-page source `meme/evidence/frank-v2-remaining-six-ata-first-page-signatures-2026-10-11.json` at `3e658f6ed3e7ff3caa4b70cc0bc1b202db812b47`.
- BPxx ATA `5WnoYgzTcSXVLfnGWNhYiZGYwSFk7PgBF6SUEHS1q6Qq`: seven actual read-only 10-entry pages returned **70 unique finalized signatures**, 69 success and 1 failure, then provider error halted pagination. All pages preserved under `meme/evidence/frank-v2-bpxx-ata-eight-page-bounded-signature-replay-2026-10-11.json` at `f82f812862ea9cf16fd0bef1891d3f749065a7ea`. **This does not imply only 70 lifetime transactions or 69 transfers.**
- Original user-Mac 1,720 signature transfer archive was reconstructed from **12 original Git evidence part files** on `evidence/frank-ca-local` with manifest snapshot `1cda7a289db31582f24d327c7dedd911c14475912346e1c4ff6e731a4f56a96a`. BPxx ATA intersection is **4 of 70**. Missing in the owner-index archive **66 of 70**. **63 predate** the documented local index start `2026-10-02T22:54:44Z`; the **3 in-window missing signatures include 1 failed tx and 2 successful tx**, **not 3 confirmed transfers**. The new mandatory real-Git-archive regression `tests/research/test_frank_git_real_transfer_replay.py` validates these numbers and part SHA256s on GitHub CI.
- Among the two successfully finalized in-window BPxx signatures missing from the owner-index archive, `3knjrZuSocitUtSunifVFy1V1mYyAzz7NLJUf96Kqg77T85x4wU8wkoHSWBxPKh22xhBAGpCewARmHksQJABGXVU` has independently re-fetched complete `getTransaction(encoding=json)` at slot **452919433**: exact requested primary signature; `meta.err=null`; Frank ATA Mint/program/owner match; balance before **1001346785078260**, after **1001347556621590**, decimals **9**, so passive inflow **+0.771543330 BPxx** with already held balance **1,001,346.785078260 BPxx**. Frank did **not** sign this tx. This does not establish how the previously held million BPxx were acquired. The other successful in-window BPxx transaction (`4Gxq6Un…`) returned connector-truncated transaction bodies, so its exact balance delta/source is **UNVERIFIED**.
- J7 two owner-index-missing Token-2022 ATA transfers were re-read again using actual `getTransaction(jsonParsed)`: both exact primary signature identities, external signer `VP4B4…`, Frank owner and Token-2022 program, pre/post raw changes (+5,000,000.000000 and +4,661,379.420528 J7) independently match earlier proof. **Neither is a verified Frank BUY nor economic cost.**
- Derived cross-source bounded report `meme/evidence/frank-v2-bpxx-1720-local-overlap-and-j7-real-tx-recheck-2026-10-11.json` under Draft PR #31 was Git GET-after-PUT verified (latest content update `5588729a36c5e7498d455450a5988027dc632a0c`).

### Source code changes actually committed and tested

1. `mission_control/ata_backfill.py` now requires the exact requested RPC signature to equal `transaction.signatures[0]` before verified ATA balance proof. Missing/mismatching transaction signature returns `TRANSACTION_SIGNATURE_UNVERIFIED`; no fabricated transfer.
2. Parsed `accountKeys` signer flags or valid raw-header signer counts are required before interpreting whether Frank signed; insufficient signer metadata records `wallet_signed=null` and `signer_identity_verified=false`, never fabricated `wallet_signed=false`.
3. Provider 429 still preserves previously verified rows. Additionally invalid/oversized signature page and invalid signature rows now preserve earlier proof and terminate as `PARTIAL_SOURCE_INVALID`. Transaction budget exhaustion or stalled pagination becomes `PARTIAL_BUDGET_OR_PAGINATION`; the manual CLI exits nonzero status 3 for any partial scan, and status 2 for Git upload failures. All research artifacts retain `complete_wallet_history=false`, `profit_usd=null`.
4. New regression tests cover missing/mismatching transaction signature, unknown signer flags, header fallback, exact archived BPxx 70/4/66 breakdown, invalid provider schema, preserving partial rows and nonzero CLI failure status.

### Mandatory independent second-AI review packet (REQUEST READY, OUTPUT NOT RECEIVED)

Reviewer must inspect **actual** Draft PR #31 at exact code HEAD `87a0611...` and real source files, and return a signed/attributed report with model identity, code SHA, PASS/FAIL findings, reproduction steps, and any concrete remediation:

- Primary-signature matching, Solana `getTransaction` json/jsonParsed accountKeys and signer/header fields, ATA PDA for Tokenkeg/Token-2022, accountIndex ownership/mint/program checks, raw-unit/decimals, failed transaction handling, and whether source-cost claims are prohibited.
- 429 and malformed RPC responses, 1–12 mint/pagination/tx budgets, dedupe across pages/accounts, temporary provider unavailability, partial scan statuses, nonzero exit codes, source-retention, `since_time` and missing `blockTime` handling, and cursor-stall proof.
- SQLite readonly invariants, public-provider method allowlist, no production Writer/threshold/Gmail/signing changes, Git branch allowlist, hashed immutable Git evidence GET-after-PUT, secret/local-path redaction and 0600 local files.
- Verify how `wallet_watch` and UI distinguish modeled BUY/SELL from raw ATA passive transfers; confirm that default follow signals still come solely from frozen V1. Test whether current `BOUNDED_COMPLETED` can still be mistaken for full chain completeness, and inspect outstanding closed/noncanonical token accounts.

**Hard gates not passed:** Independent second-AI review **NOT_RUN**; Mac new-head read-only execution **NOT_RUN**; complete BPxx and remaining ATA transaction/source/cost reconciliation **NOT_COMPLETE**; closed/noncanonical accounts **NOT_SCANNED**; new Dashboard v2 and CA accuracy feature **NOT_DEPLOYED**. Do **not** change existing live Frank V1, mission-control email, real Gmail, system LaunchAgents, or production trading. No new automation.
