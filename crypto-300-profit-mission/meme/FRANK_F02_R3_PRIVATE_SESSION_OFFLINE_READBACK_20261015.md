# Frank F02-R3 private full-wire and research SQLite offline readback

Status: `CODE_UNDER_REVIEW / REAL_USER_MAC_EXECUTION_NOT_YET_DONE / NO_MERGE / NO_DEPLOY`. Base: independently reviewed F02 manual new source [PR #66](https://github.com/lxxlx2/ChatGPT_mission_record/pull/66), exact `a20a9f972589e34d2eae435c2ee4696eb53bb1d7`, user-authorized real private Mac data captured at 2026-10-15T06:10:01.348696+00:00. Separate [progress PR #67](https://github.com/lxxlx2/ChatGPT_mission_record/pull/67) evidence-only readback is `APPROVE` for bounded synthetic UI/code evidence, not independently verified private raw capture. Keep all old parent Draft PRs open/unmerged.

## Why this program is needed

The private user Mac session's original dual-program RPC bundle, 32 exact frozen roster, research-only Sidecar and native browser receipts are **not available in the public GitHub repo**. Reviewer of PR #67 independently reproduced the renderer with synthetic wire and real Chromium (15/15) but could not independently replay the user's private original bytes or confirm account-level source matching from public JSON booleans.

This deliberately minimal new **read-only local Mac audit**, run separately with user's existing private source under reviewed code SHA, reuses approved A05 wire `replay_owner_full_receipts`, `reconcile`, F02 Sidecar/read-only `ResearchPositions`. It adds no RPC, no new SQLite, no listener, no screenshots, no other APIs, no cross-wallet sale or PnL inference. It emits **aggregate only** and avoids raw owner wallets, full Mint roster and Token Accounts in public Git.

## Usage (local-agent working directory, once code reviewed)

```zsh
python3 -m scripts.frank_f02_r3_offline_attestation --capture-sha256 a5964a093a1d6bffe7b2334480825c90af478d3c38d7336fc71cec767b81a25e
```

The CLI finds exactly one matching existing private `~/.local/share/frank-f02-research/manual-sessions/session-*/wire/manifest.json`. It does not create or modify session files. The user must use the exact reviewed Git SHA in a separate checkout. Any missing, duplicate or tampered archive, hash mismatch, roster mismatch or normalized Sidecar contradiction returns `F02_R3_PRIVATE_SOURCE_ATTESTATION_FAILED` and exit 1, with no raw bytes printed.

On success, outputs only:

- Original source SHA/UTC, non-atomic two finalized slots.
- Whole wallet **observed token-account count** and separately **observed unique Mint count** (never subtract unlike units).
- Frozen **32** targets: nonzero / observed zero / missing; total target Token Accounts; frozen targets with **more than one** Token Account and maximum accounts within one Mint, without disclosing addresses.
- **All 32 exact raw quantities, decimal quantities, individual Token Account address/Program/state/raw quantity** are compared privately between replay and independently read-only Sidecar at a controlled historical `observed_at +1s` reference time; the program does not claim that historical number is current.
- API readiness at actual audit time and fail-closed 32 `SOURCE_UNAVAILABLE` for stale/failed/unverified source.
- Original research SQLite main file bytes unchanged, no real RPC, no production writes, no sell/PnL/cost or all-wallet UI claim.

The previous freeze list from 2026-10-11 had **10 nonzero / 22 zero**, unrelated to a later full owner snapshot's 9/23. The 2026-10-14 data listed 3233 observed accounts, while a later source in PR #67 declares **3276 observed unique Mints**: different measures; do not interpret their numerical difference as new tokens. This CLI emits both units for the *same* target capture.

Synthetic multi-account per-Mint and synthetic wire tamper/mismatched-source tests are required at the exact SHA in GitHub Actions before independent review. Their success does not prove this exact private Mac capture until user runs the CLI.

## Gate handling

- Expected next gate once CI passes: frozen exact SHA independent other-AI code audit, with copy-ready full reviewer prompt **in the same chat response** (Frank mandatory development rule).
- Next user-run Mac offline audit: 1 small sanitized stdout; no private original byte upload, no extra user authorization for RPC because **no new RPC is executed**.
- Then F02-R3 integration: actual F01 actionable-only/observation/exit contract + C01/C02 one-CA single-mode research and source-verified F02 holdings in a disposable **shared** integration checkout. Final independent product/UI review and separately authorized release remain pending.
- Keep existing P3s in backlog; don't sidetrack into changing approved TTL logic, all-history seller inference or low-level coin listing UI.

`NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_RPC / NO_NEW_AUTOMATION`.
