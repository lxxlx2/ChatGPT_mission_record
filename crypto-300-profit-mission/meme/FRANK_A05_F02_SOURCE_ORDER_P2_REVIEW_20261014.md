# A05 / F02 — independent Claude P2 source ordering and no-slot recovery

Date: 2026-10-14 Asia/Bangkok
Scope: read-only owner-capture inventory research, not live F02 Dashboard positions.
Verdict on parent [Draft #56](https://github.com/lxxlx2/ChatGPT_mission_record/pull/56) exact `55b430608d9048360f922a453f77cced479ac810`: **external independent Claude REQUEST_CHANGES (two P2)**.

## Proven issues and impact

1. **P2, reappearing old positions:** `latest_inventory` read only `read_wallet_captures(wallet, limit=100)`; that legacy storage interface sorts by SQLite **rowid/import order**, not Solana chain slot. If a valid slot 1001 account capture was imported first, then 100 older balance-positive snapshots were archived afterward, the latest snapshot was excluded and the latest-slot projection could report old raw balance `2500000` as newly observed. Source age being inside TTL does not repair this selection defect.
2. **P2, failed source blocks healthy snapshot:** `capture_owner` legitimately stores an immutable `PARTIAL_SOURCE` document with `slot_max=null`, `slot_min=null`, both token program calls failed and `program_coverage=[]`. The former projection threw `OWNER_CAPTURE_SLOT_INVALID` on **any historical** such document, even when a later healthy finalized snapshot existed. Conversely, silently ignoring an actually later all-failed attempt would resurrect stale old positions.

## Engineering change

- Add a separate, read-only **streaming entire source set** iterator `WalletEvidenceStore.iter_wallet_captures(wallet)`, using `fetchmany(256)`. Existing bounded `read_wallet_captures(limit<=100)` remains unchanged for historical UI clients; it can no longer be used to decide a latest chain slot.
- Check every archived candidate's account owner/network identity, immutable original capture SHA and timezone-aware observed-at timestamp, excluding observations after the specified `as_of_utc`; choose **highest successful finalized slot** across the complete valid set before projecting any Mint. Out-of-order imported backfill never replaces a higher slot.
- Accept a **specifically valid double-RPC-failure capture** as a no-slot attempt rather than corrupt chain evidence. Compare observed attempt timestamps: old all-failed → later healthy means later healthy wins; old healthy → later all-failed means a **fresh unknown** `SOURCE_ATTEMPT_FAILED_NO_SLOT` record wins and masks all older balances; tie fails closed as unknown. Failure attempts with missing/contradictory required fields remain invalid. No token amount, cash, sale, entry, price or PnL is inferred from failed calls.
- Explicitly report `capture_candidates_examined`, `source_attempt_failed_no_slot`, `source_observation_status`, source hash, time/age and slot range (null when the newest source attempt has no confirmed slot). Persisted source records are not edited; no database schema migration is needed.
- Tests **reproduce original P2 counterexamples in real disposable SQLite** using `capture_owner` and `capture_wallet`: 121 valid captures, first newest slot 1001 with Mint absent and 120 older imported later with positive `2500000`; old failure → new healthy; healthy → newer double failure; healthy import → later imported older failure; stale latest failure. Prior no-stale, partial one-program, multi-account, 32-mint and sidecar read-only tests remain.

## QA, Review and downstream gates

- Exact final-HEAD CI must include targeted A05/F02 and all real-Git local-agent tests, plus a separate **disposable combined current-main + full A05 stack + C02 #49 + F01 #44** targeted/full regression; record the observed integration SHA and failures separately. Earlier PR #56 CI is not sufficient for modified code.
- **New independent other-AI module re-review is mandatory on this child PR's final exact head.** Reviewer must verify the two actual P2 reproductions, bounded reader backwards compatibility, no-slot attempt versus invalid source, timestamp/slot precedence, immutable raw evidence, provenance/freshness, consumer semantics and downstream F01/C02/Frank V1 behavior.
- A subsequent independent cross-module review and an additional independent entire-product review at completion are required by [development review policy Draft #55](https://github.com/lxxlx2/ChatGPT_mission_record/pull/55).
- Live Mac production 32 verified Mint roster, actual SPL+Token-2022 owner accounts, complete ATA historic closure, token price/PnL and real Dashboard user acceptance are **NOT** part of this successful research code patch. No approval to merge, deploy, trade or modify production Mac SQLite / Gmail / launchd.

Status: `CODE_FIX_IN_PROGRESS / CI_AND_INDEPENDENT_REVIEW_GATED / BUSINESS_ACCEPTANCE_PENDING / NO_MERGE / NO_DEPLOY`.
