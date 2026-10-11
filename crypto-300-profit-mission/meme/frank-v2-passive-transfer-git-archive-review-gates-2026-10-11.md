# Frank V2 — Passive transfer evidence archival: research implementation and release gate

Updated: 2026-10-11 Asia/Bangkok
PR: https://github.com/lxxlx2/ChatGPT_mission_record/pull/31
Evidence branch: `evidence/frank-ca-local`
Status: `RESEARCH_CODE_IMPLEMENTED / UNIT_AND_INTEGRATION_CI_PASS / REAL_MAC_TRANSFER_CAPTURE_NOT_RUN / INDEPENDENT_AI_REVIEW_NOT_DONE / PRODUCTION_OFF`

## Purpose and prior proved chain facts

Frank's old full-history packet covered 78 locally recognized market trades across 33 mints, but did **not** export the `signatures.body.evidence.wallet_token_transfer_flows` and `token_balance_deltas` already recorded by the original normalized parser. Consequently, 12 mints had local SELLs but no locally recognized BUY; treating these sales as profit would be wrong.

Independent finalized Solana evidence found that the J7 mint's later sold **12,508,217.470763** units came from **three transfers signed by another wallet**. The incoming quantity exactly equalled the later local SELL token quantity. The sender's acquisition cost is still not verified. BPxx also had more than one million tokens before later large local sales; original basis is unknown. This feature preserves such passive-source evidence in reproducible Git artifacts without changing Frank's trading model.

Canonical real source report: `crypto-300-profit-mission/meme/frank-v2-full-history-source-audit-2026-10-11.md`.

## Code implemented in Draft PR #31

- `local-agent/mission_agent/mission_control/wallet_transfers.py`: existing *read-only* `forward.sqlite` signature-history export; local classification, signer/fee-payer status, transfer IN/OUT legs, wallet-owned token pre/post deltas, signature, block/slot and raw transaction evidence hash. Only explicit public fields; no raw signed transaction, endpoint credentials, email, API key or host path in selected output. `LOCAL_NORMALIZED_SIGNATURE_TRANSFER_EVIDENCE_NOT_FULL_CHAIN` is explicit; exporter does **not** establish sender's economic owner or acquisition price.
- `local-agent/mission_agent/mission_control/transfer_archive.py`: isolated durable spool under `git-evidence-spool/pending/frank-transfer-history{,-parts}`. Sanitized content receives a SHA-256 snapshot ID; each base64 part is independently hashed. The uploader verifies all local chunks and the complete reconstructed source before **any** PUT, uploads parts first, then the manifest. GitHub GET-after-PUT exact-byte match precedes deleting local pending content. A 404, offline Git, invalid record, bad part, oversized archive or server error retains pending files and sets a non-success status. The archive never writes to `main` or checks out the live repository.
- `scripts/frank_evidence_bootstrap.py`: adds the complete normalized transfer report to its safe ZIP and, with `--sync`, sends all existing CA/Frank evidence plus transfer archive to the existing dedicated Git branch. `SYNC_OK` now requires Frank scan, original trade history and transfer-history captures to succeed, all Git uploads to succeed, zero CA errors, a valid D0 audit, and a valid explicitly requested dated inventory comparison. A source-read failure cannot masquerade as successful capture.
- `mission_agent/mission_control/service.py`: uses **only the preexisting Mission Control background executor**, behind the existing `MISSION_EVIDENCE_EXPORT_ENABLED=1` opt-in. Every newly observed Frank Writer poll still gets a small scan checkpoint and the existing 15-minute evidence buckets. A full **cumulative** transfer snapshot is generated on first opt-in and at most hourly when new signatures have been observed; no new polling service or launchd job. This bounds Git volume and keeps source IO/network off the decision/Gmail thread. It is not a guaranteed per-event real-time transfer stream.
- Fixed the CI workflow's accidentally concatenated path filter so edits to `wallet_history.py`, `wallet_reconciliation.py`, `wallet_transfers.py`, `transfer_archive.py` and their tests actually trigger validation.

This is an additive optional research mechanism. Original Frank Writer/CA trading parser and static alert decision rules were **not** changed. A transfer archive finding must not automatically create a BUY, remove WATCH entries, assign PnL, send Gmail or place orders.

## Reproducible isolated CI evidence

[GitHub Actions run 38120104653](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38120104653) completed **SUCCESS** at research branch HEAD `de999dd2881266df27407020c44174b15d9a1ce2`.
- **59 new** safety/integration tests passed, including transfer chunks, whole-content hashes, manifest sequence/integrity, redaction, network failure, replay, worker isolation, Mac CLI ZIP source preservation, historical trade/inventory and 33-mint source-contract cases.
- **80 original** Dashboard/Mission Control/Delivery regressions passed.
- Python compilation and browser JavaScript syntax checks passed.
- Total tested subset: **139 passed**. This is NOT a full repository suite, independent second-model review, authenticated real Mac Git upload or deployed uptime test.

## Independent-AI review checklist — RELEASE BLOCKER

External reviewer should read the actual PR diff (not this status alone), including `wallet_transfers.py`, `transfer_archive.py`, `evidence_sync.py`, `frank_evidence_bootstrap.py`, `service.py` and tests. Require a report on:

1. Source signature identity and transfer-direction correctness, token account ownership, same-transaction inner/outer legs, signed vs passive receipts, duplicate/ambiguous normalized events.
2. Claim discipline: local observed != complete chain history; gross proceeds != profit; J7 sender's transfer != verified original acquisition cost; dated point-in-time token balances != live wallet NAV.
3. Data security and privacy: recursively sanitize nested public fields, forbid credentials, signer material, raw signed transactions, local filesystem metadata; examine symlink/permission/path and Git branch constraints.
4. Size/performance: SQLite read-only transaction consistency while production writer is active, 8 MB ceiling, snapshot re-export frequency, Git chunk count, branch/storage limits, no Dashboard/notification stalls.
5. Failure semantics: bad/missing chunk, bad snapshot hash, token expiry, 429/offline Git, CAS collision, worker exception, partial readback, retry idempotence, and truthful status/queues.
6. Real Mac acceptance: run one-shot, verify actual signature count and J7 passive transfer classification in generated ZIP, independently check remote Git manifest/full SHA256, observe no Frank/Gmail source fingerprint changes.
7. Full regression suite and real local UI acceptance, including watchlist history vs actual transfer-origin proof. Unsupported cases remain explicit `NOT_VERIFIED`, never fill unknowns with estimates.

**NO_GO gates:** `INDEPENDENT_AI_REVIEW=NOT_DONE`, `REAL_MAC_PASSIVE_TRANSFER_EXPORT=NOT_RUN`, `REAL_MAC_GITHUB_READBACK=NOT_VERIFIED_FOR_THIS_NEW_ARCHIVE`, `PRODUCTION_AUTO_EXPORT=OFF`, `MAC_NEW_DASHBOARD_DEPLOYMENT=NO`, `PRODUCTION_TRADING=NO_GO`. The prior 23-file CA and 78-trade Git upload successes do not validate this **new** transfer archive. No permission to deploy, merge or restart was exercised.
