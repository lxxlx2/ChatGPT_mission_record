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
