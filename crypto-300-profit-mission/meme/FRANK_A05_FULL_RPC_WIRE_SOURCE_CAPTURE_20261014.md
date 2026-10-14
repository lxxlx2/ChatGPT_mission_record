# A05-R1 — complete Solana owner RPC source receipts (research-only)

Date: 2026-10-14 Asia/Bangkok
Status: `IMPLEMENTED_CODE / CI_AND_INDEPENDENT_MODULE_REVIEW_PENDING / REAL_FULL_RPC_SOURCE_UNVERIFIED / NO_MERGE / NO_DEPLOY`.

## Why this was needed

The previously used read-only connected Alchemy tool *successfully contacted* both Solana Token programs but truncated each long response to approximately 8 KB of visible text, preventing complete JSON parse, authoritative account counts, full Mint scope and archived raw source bytes. No full wallet source may be declared `BOTH_PROGRAMS_OBSERVED_NON_ATOMIC` from those partial outputs. See `FRANK_A05_F02_CHAIN_OWNER_SOURCE_PREFLIGHT_20261014.md`.

The current approved A05 normalizer `wallet_chain_capture.capture_owner` verifies parsed account data and produces hashed research snapshots; the earlier `frank_capture_owner_readonly.py` already has a 12 MB full-response transport, but did not archive the **original full RPC wire response bytes with each program's source slot** for independent offline audit. This module fills precisely that evidentiary gap, without replacing approved A05 source/normalizer/Sidecar code.

## New standalone module (Draft child of reviewed PR #58)

- `local-agent/mission_agent/mission_control/wallet_full_rpc_evidence.py`: bounded full original HTTP response bytes, explicit SHA-256 for each program's JSON-RPC receipt, strict JSON envelope/request id/result/context/slot/owner/Token program validation, finalized source rules and `minContextSlot` floor. Records full original bytes in isolated `0700` research directories with `0600` evidence files. Each program gets its own raw JSON; evidence manifest records source file/bytes/SHA/Program ID, finalized Slot, observed account count, UTC time, completeness/missing reason and `snapshot.capture_sha256`. No input RPC URL or key is written to disk; source directory inside public checkout is forbidden.
- `local-agent/scripts/frank_capture_owner_full_receipts.py`: default PLAN_ONLY (no network/write), explicit `--execute` for exactly two HTTPS `getTokenAccountsByOwner` requests with `jsonParsed/finalized`, bounded 12,000,000 bytes and request IDs, **complete raw** bytes archived locally. No CLI logs include a URL or secret. Full independently reconstructable source is the only condition under which `--import-sidecar` may write an **isolated research** `WalletEvidenceStore`; default execute does NOT import. `--replay-bundle` has **zero network calls** and rechecks original raw SHA/size, Program IDs, account owner, minimum slots, per-program counts and normalized capture SHA before any optional Sidecar import.
- Partial or corrupt reply, oversize transport, mismatched RPC ID, invalid JSON/truncated response, `error` RPC envelope or Slot below the requested floor → explicit `complete=false` manifest with program/reason and no eligible complete normalized snapshot. A valid response from one program never substitutes for a missing other program.
- `tests/test_frank_a05_complete_rpc_receipts.py`: synthetic original-wire-sized >8KB response (many real-format accounts), original byte-for-byte SHA/length and replay, partial/truncated/wrong-id/oversize source refusal, malformed or changed raw bytes, wrong wallet or program identity, deterministic same-source Sidecar re-import idempotence, no-write plan mode, context slot monotonicity, and protection against raw source files accidentally being written into public repository trees. Fixtures are synthetic; **they are not a 32-Mint live capture**.

## Manual isolated Mac/other approved RPC usage (zsh)

First plan-only from a checkout of the **reviewed** new branch, with the frozen Frank registry:

```bash
cd crypto-300-profit-mission/local-agent
python3 -m scripts.frank_capture_owner_full_receipts --person-id frank
```

Manual actual full-RPC capture after independent code review and authorized source collection; evidence saved outside Git checkout, without touching production SQLite:

```bash
python3 -m scripts.frank_capture_owner_full_receipts --person-id frank --execute --evidence-dir "$HOME/.local/share/frank-owner-full-rpc-evidence"
```

Manual offline replay/validation of the actual `evidence_bundle` path printed by that command (replace exact path, not guessed UUID):

```bash
python3 -m scripts.frank_capture_owner_full_receipts --person-id frank --replay-bundle "/actual/evidence_bundle/path"
```

Only with explicit research-only Sidecar import permission, after independent Review and source validation:

```bash
python3 -m scripts.frank_capture_owner_full_receipts --person-id frank --replay-bundle "/actual/evidence_bundle/path" --import-sidecar --sidecar "$HOME/Library/Application Support/FrankMeme/research-wallet-evidence.sqlite"
```

An RPC plan or synthetic CI fixture does **not** prove actual source. Fresh full RPC sources and an approved precise historical **32 Mint roster** must be compared separately in A05-R2. Current Token program accounts omit already-closed accounts; a present-day zero token balance is not chain-history sale evidence. Do not claim verified beneficial ownership, historical cost, BUY/SELL, PnL or USD NAV.

## Next gates

1. Exact-head module targeted/full tests + independent other-AI Review of this new A05-R1 module; fixes on child branch with new review, preserving approved PR #58 source SHA.
2. User-approved manual full-wire RPC capture, archived slot/UTC/raw SHA and program account count, inspect actual 32 historical target Mints without inventing manifest. A05-R2 own research reconciliation and independent Review.
3. F02 read-only actual observed positions from complete current source, no fabricated price/PNL, independent Review, actual Mac/real browser QA, separately independent combined F01/C02/A05/F02 Review, final overall independent Review after all modules, distinct explicit user deployment authorization.

NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / no protected Mac SQLite/LaunchAgent changes.
