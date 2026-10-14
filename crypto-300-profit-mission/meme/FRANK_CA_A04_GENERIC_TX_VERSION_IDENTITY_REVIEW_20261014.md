# A04 generic TX immutable V2/V3 coexistence — Claude P2 review remediation

Date: 2026-10-14 Asia/Bangkok
Status: `CODE_IMPLEMENTED / FINAL_SHA_CI_AND_INDEPENDENT_REVIEW_GATED / NO_MERGE / NO_DEPLOY`

## Independent review that triggered this work

- User-provided independent Claude review examined [Draft PR #53](https://github.com/lxxlx2/ChatGPT_mission_record/pull/53) at **exact SHA `166bdaa133d7ed799870ca963d2dfa55f2736b17`** and returned **`REQUEST_CHANGES`** for a newly detected **P2**.
- Claude **passed** the exact-source PR #51/#52 frozen Sidecar migration and HistoryJournal V3 identities, immutable RAW_TX/V1/V2, repeat V3 reconstruction, correct V3 coverage, N1 gaps and original reviewed C02/F01 coexistence. Those former fixes are preserved unchanged in the new child branch.
- Remaining defect: the generic `WalletEvidenceStore.record_transaction(document)` was still writing any normalized transaction to kind=`TX`, identity=`solana:<signature>:<slot>` regardless of normalizer version. Previously saved actual V2 normalized `TX` conflicts with new V3 content at the same immutable identity, resulting in `IMMUTABLE_EVIDENCE_CONFLICT`. The HistoryJournal-specific `WALLET_TX_VIEW_V3` fix did **not** cover this public generic method.

## Version contract after this change

- `TX` legacy `SOL_TOKEN_VIEW_V2` / schema 2 retains the **original unversioned key** `solana:<signature>:<slot>` and its immutable document bytes and hash. No rewrite, migration, deletion or alias to V3.
- New `SOL_TOKEN_VIEW_V3` / schema 3 is a separate immutable `TX` identity `solana:<signature>:<slot>:v3`. `count("TX")` counts both, preserving existing consumer semantics; the key explicitly differentiates projection algorithms.
- Reimport of unchanged V2 or V3 returns false (idempotent). A second independently valid hash with changed content **within the same version** returns `IMMUTABLE_EVIDENCE_CONFLICT` and leaves both documents and source SHA unchanged.
- Mismatched or unsupported schema/normalizer pairs fail closed with `UNSUPPORTED_TRANSACTION_NORMALIZER_VERSION`; no arbitrary suffix, user-defined version string or automatic fallback to a legacy identity. A future V4 algorithm must explicitly introduce its own storage key rather than silently share a V3 identity.
- This change does not modify immutable `RAW_TX`, HistoryJournal `WALLET_TX_VIEW` / `WALLET_TX_VIEW_V2` / `WALLET_TX_VIEW_V3`, source cursor, Frank V1 follow decisions, production SQLite, Gmail, launchd, CA/C02 source or Dashboard UI.

## Reproducible tests and actual frozen-code regression

- New `tests/test_frank_a04_generic_tx_versions.py`: synthetic V2/V3 documents with same signature and slot inserted in *both* orders; per-version duplicate idempotence, distinct identity and exact hashes, same-version mutation collision cannot overwrite, read-only reopened count, six invalid or spoofed normalizer/schema pairs rejected. Synthetic tests are clearly marked; they are not original RPC receipts.
- More importantly, the GitHub workflow `frank-ca-a04-generic-tx-versioning-20261014.yml` checks out the actual **PR #52 SHA `e547203c6e4b00c80372c125785c9feb72fb8e87`** in a separate Git worktree, verifies that its Python normalizer was actually imported, then calls its original `WalletEvidenceStore.record_transaction` twice to produce the historic **unversioned V2 `TX`** in a real SQLite file. The current child source opens the *same database*, imports the V3 projection from the same receipt, repeats it, verifies both document keys, archived V2 content bytes and SHA, new V3 SHA and explicit rejection of contradictory within-V3 evidence.
- The second CI workflow temporarily merges the entire A04 branch stack with the separately independently approved [C02 #49](https://github.com/lxxlx2/ChatGPT_mission_record/pull/49) and F01 #44 on top of the currently fetched main; it runs full local-agent real-Git tests plus UI and joint A04/C02/F01 contracts. This does not push a merge commit to main or to production Mac.
- CI evidence and exact SHA must be appended after final commit is created. Prior green PR #53 CI is **not** re-used for this new versioning change.

## Acceptance bounds and next review

Independent another-AI review is required on this new exact HEAD, specifically covering legacy generic TX identity continuity, V3 identity separation, same-version fail-closed mutation, zero unapproved schema downgrade, frozen PR52 SQLite producer and combined HistoryJournal/F01/C02 regressions. Cross-SHA CI green is an engineering check, not independent approval or deployment authority.

Authentic failed parsed `getTransaction`, nonzero missing owner, ATA close, full 32-Mint/ATA history and economic PnL evidence and Mac dashboard business acceptance remain unresolved; no automated trading, Gmail or protected Mac production writes are performed. **Keep all related PRs DRAFT / NO_MERGE / NO_DEPLOY.**
