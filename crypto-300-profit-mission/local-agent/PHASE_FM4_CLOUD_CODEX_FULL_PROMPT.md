# PHASE_FM4 CLOUD CODEX — SELF-CONTAINED EXECUTION PROMPT

You are taking over the `$300-3000` crypto monitoring project in **Codex Cloud**.

This is a cloud development task. You are NOT running on the user's Mac.

Your job in this phase is to complete the repository-side implementation and tests for the Meme / tracked-person monitoring pipeline, while preserving the already-working Frank live runtime and preparing an exact local migration package for later execution on the user's Mac.

Do not create or modify ChatGPT Scheduled Tasks. Do not create a separate Codex automation for this project. The existing ChatGPT task is already named `$300-3000` and is managed outside Codex Cloud.

---

## 0. Repositories and branch

Primary repository:
- `lxxlx2/ChatGPT_mission_record`

Use branch:
- `codex/crypto-monitor-design-20260930`

Private runtime repository:
- `lxxlx2/crypto-monitor-runtime`

Use the private runtime repository only if this Codex Cloud environment actually has permission. If it does not, continue all repository-side work and report `PRIVATE_RUNTIME_REPO_UNAVAILABLE`; do not fabricate access or results.

Do not create another repository.
Do not rebase or force-push frozen history.
Do not overwrite historical FM1/FM2/FM3 evidence.

---

## 1. Read first — mandatory order

From branch `codex/crypto-monitor-design-20260930`, read completely:

1. `crypto-300-profit-mission/local-agent/CURRENT_MAINLINE_CHECKPOINT.md`
2. `crypto-300-profit-mission/local-agent/PHASE_FM3_FRANK_MONSTER_REPORT.md`
3. `crypto-300-profit-mission/local-agent/PHASE_FM4_MEME_SIGNAL_PIPELINE_PROMPT.md`
4. `crypto-300-profit-mission/local-agent/PHASE_FM4_CLOUD_CODEX_HANDOFF.md`
5. this file: `crypto-300-profit-mission/local-agent/PHASE_FM4_CLOUD_CODEX_FULL_PROMPT.md`

From `main`, read completely:

6. `crypto-300-profit-mission/STATUS_SCOPE_2026-10-03.md`
7. `crypto-300-profit-mission/meme/MEME_GPT_MONITOR_SPEC.md`
8. `crypto-300-profit-mission/portfolio/current.md` only for current accounting context; it is not an FM4 implementation dependency.

Then inspect all committed source/tests/config referenced by FM3. Search the repository for these exact identifiers if paths are unclear:

- `com.jerson.crypto-monitor-frank-shadow`
- `frank-forward-shadow`
- `FRANK_ACTIVE_E2E_PASS`
- `RAW_FRANK_CANDIDATE`
- `synthetic-local-v1`
- `frank-v7`
- `processing-v8`
- `monster_d1_v2`

Do not guess any uncommitted local file content.

---

## 2. Authoritative current state

Treat the following as current facts unless newer committed evidence supersedes them:

### Frank

- Frank wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`
- `FRANK_SHADOW_READY = PASS`
- `FRANK_ACTIVE_E2E = PASS`
- real forward ACTIVE E2E has already been proven
- real path proven:
  official/finalized Solana evidence -> normalization -> candidate -> SQLite -> private transport -> exact readback
- FM3 report snapshot:
  - 5 real new forward signatures
  - 1 real ACTIVE
  - 2 real candidates from the same ACTIVE transaction / two mints
  - total first ACTIVE E2E = 47.297 s
  - detection = 27.010 s
  - normalization = 0.175 s
  - candidate = 0.203–0.206 s
  - transport = 19.907–19.910 s
  - RPC errors/429/timeouts/retries = 0
  - current gap = 0
  - unresolved gap = 0
  - candidate duplicate = 0
  - SQLite integrity = `ok`
  - post-ACTIVE restart/dedupe = PASS
  - historical parser progress at report snapshot = 6,105 / 18,203
- known local agent name before future migration:
  `com.jerson.crypto-monitor-frank-shadow`

### Monster

- `MONSTER_D1_V2_NEEDS_REDESIGN`
- 243 frozen TRAIN configs completed
- no config passed candidate ceiling
- winner = NONE
- minimum median entities/day = 148 > gate 100
- minimum p95/day = 215 > gate 150
- 2024 validation remains NOT_RUN
- D2 shortlist remains SKIPPED
- D3 remains NOT_STARTED

Do not reopen the same grid or loosen its gates in FM4.

### Mission scope

Current umbrella task/mission name:
- `$300-3000`

Current implementation priority:
- Meme / tracked-person signals = `ACTIVE_DEVELOPMENT_PRIORITY`

Deferred but NOT cancelled:
- Monster / 妖币 = `DEFERRED_NOT_CANCELLED`
- NFT opportunity/reminder monitoring = `DEFERRED_NOT_CANCELLED`
- CORE PRICE / broader market analysis = `DEFERRED_NOT_CANCELLED`

Do not delete their specs/history/tests/roadmap.
Do not describe them as abandoned.
Do not resume them in FM4.

Legacy old task:
- `$300 Crypto资产状态监控` = disabled legacy task

Existing ChatGPT monitoring task:
- `$300-3000`

Codex Cloud must NOT create, delete, rename, pause, resume or edit ChatGPT Scheduled Tasks.

Production trading:
- `NO_GO`
- no autonomous trades
- no wallet mutation
- no signing

---

## 3. Environment boundary — critical

You are in Codex Cloud.

You MAY directly:

- read/edit source in the connected repository;
- run tests in the cloud environment;
- install permitted dependencies;
- implement schemas, parsers, aggregation, state machines, renderer, outbox/dedupe and migration tooling;
- inspect committed reports/source/tests;
- commit and push to the existing branch;
- use the connected private runtime repo if actual permission exists.

You MUST NOT claim that cloud execution directly:

- inspected `/Users/jerson/...` local-only files that were never committed/provided;
- inspected the live Mac SQLite database unless an explicit sanitized snapshot exists in accessible storage;
- stopped/started/renamed the user's macOS LaunchAgent;
- inspected the user's live `launchctl` state;
- measured live Mac process CPU/RSS;
- proved Mac polling continuity across a real LaunchAgent migration;
- edited the ChatGPT `$300-3000` scheduled task;
- sent a real Gmail investment alert from Codex.

For every acceptance item that truly requires Mac execution, implement the script/check/tooling and mark the report field:

`LOCAL_EXECUTION_REQUIRED`

Never turn an unexecuted Mac-local check into PASS.

---

## 4. FM4 objective

Complete the repository-side implementation for:

1. Frank -> Meme system generalization;
2. Frank becomes one tracked `person_id` rather than the system identity;
3. support multiple verified wallets per person;
4. deterministic unique-person TOKEN_CONSENSUS aggregation;
5. deterministic PERSON_PATTERN feature handoff;
6. immutable candidate/run schema;
7. TTL/followability fields and provenance;
8. GPT handoff bundle;
9. current-run-only email renderer;
10. outbox/idempotency/dedupe/crash recovery/concurrency protection;
11. stale-content regression protection;
12. private Git handoff contract;
13. exact Mac-local migration/preflight/rollback package;
14. comprehensive automated tests;
15. FM4 acceptance report.

Do NOT perform Monster redesign in this phase.
Do NOT resume NFT work.
Do NOT resume Core Price work.
Do NOT create a Monster LaunchAgent.

---

## 5. Rename/generalize architecture: Frank -> Meme

System-level name target:
- `Meme`

Tracked person:
- `person_id = frank`
- display name = `Frank`

Minimum person registry representation:

```json
{
  "person_id": "frank",
  "display_name": "Frank",
  "wallets": [
    {
      "chain": "solana",
      "address": "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ",
      "verified": true
    }
  ],
  "person_pattern_state": "SIGNAL_ENABLED"
}
```

Rules:

- one person can own multiple verified wallets;
- consensus counts unique `person_id`, never wallet count;
- two Frank wallets buying the same token still count as one person;
- do not invent or automatically discover new people into live configuration;
- future people require explicit user approval;
- new approved people default to `OBSERVE_ONLY` for PERSON_PATTERN until separately historically validated;
- verified OBSERVE_ONLY people may contribute to TOKEN_CONSENSUS.

Preserve Frank durable history/state semantics. Refactoring names must not make historical Frank events replay as new live events.

---

## 6. Candidate schema v2

Create a stable, versioned immutable candidate schema.

Minimum fields:

- `schema_version`
- `candidate_id`
- `event_id`
- `run_id` or `source_batch_id`
- `signal_family_candidate`
  - `TOKEN_CONSENSUS`
  - `PERSON_PATTERN`
- `person_id` / `person_ids`
- source wallet(s)
- chain
- mint/token address
- transaction signature(s)
- finalized block/slot evidence
- event timestamp(s)
- `detected_at`
- `normalized_at`
- `candidate_created_at`
- deterministic buy amount(s)
- denominated asset
- USD estimate only when causally/deterministically supportable
- behavior type:
  - `first_entry`
  - `add`
  - `reentry`
  - `other`
- deterministic feature bundle
- source evidence hash(es)
- TTL provenance
- `expires_at`
- transport/content hash

Never store previous email prose as candidate input.
Never reconstruct missing chain facts from natural-language historical emails.

---

## 7. TOKEN_CONSENSUS

Purpose:

Detect when multiple independent tracked people buy the same token within a useful causal time window.

Deterministic code must establish:

- token/mint identity;
- unique `person_id` count;
- wallet -> person mapping;
- qualifying BUY events;
- transaction signatures;
- timestamps;
- deterministic amounts;
- each person's first qualifying buy;
- first_event_at;
- last_event_at;
- window_seconds;
- stable event/signal identity;
- TTL;
- dedupe.

Normally generate a GPT-review TOKEN_CONSENSUS candidate only when:

`unique_person_count >= 2`

Since only Frank is currently live-configured, real TOKEN_CONSENSUS must remain zero until user-approved additional people are actually configured.

Synthetic PersonA/PersonB are permitted only inside explicit test fixtures/namespaces.
Synthetic identities must never enter live manifest/runtime/email paths.

Do not assume consensus is automatically better. Build the data model so later validation can compare 1-person vs 2-person vs 3+-person performance by time window.

---

## 8. PERSON_PATTERN

Purpose:

Provide deterministic person-specific behavior/features to GPT, while GPT remains the final investment-value judgment layer.

For Frank, provide where reliably available:

- first entry / add / re-entry;
- current buy size;
- buy-size percentile relative to Frank history;
- prior Frank exposure to same mint;
- token age at entry;
- entry market cap/liquidity only if causally sourced;
- elapsed time since entry;
- price movement from Frank entry to candidate-ready time;
- historical pattern reason codes;
- followability timing fields;
- any deterministic quality/confidence flags.

Do NOT hard-code final investment SEND/NO_SEND in Codex.

Do NOT blindly apply Frank's person-specific pattern to future people.
Each future person must have separate replay/history validation before `SIGNAL_ENABLED`.

---

## 9. GPT remains final investment judgment

The architecture is intentionally hybrid.

Deterministic code owns:

- chain truth;
- identity;
- BUY/SELL facts;
- amounts;
- person/wallet mapping;
- first/add/reentry classification;
- aggregation;
- IDs;
- state;
- TTL;
- SQLite/outbox;
- dedupe;
- immutable run bundle;
- stale-content isolation.

The existing ChatGPT `$300-3000` task owns final investment judgment:

- `SEND` / `NO_SEND`;
- current followability;
- whether price has already overextended;
- current liquidity/market-cap/executability;
- project background;
- current official/X/on-chain/market context;
- reason codes;
- risks;
- confidence;
- user-readable email composition.

Codex must provide a machine-readable contract sufficient for GPT to return:

- `decision_id`
- `run_id`
- `signal_id`
- `signal_type`
- `person_ids`
- `mint`
- `decision`: SEND or NO_SEND
- `reason_codes[]`
- `evidence[]`
- `risks[]`
- `followable_now`
- `confidence`
- `decided_at`
- `candidate_age_seconds`

---

## 10. Followability and TTL

Core success metric is USER-FOLLOWABLE performance, not Frank's original wallet PnL.

Build replay/diagnostics based on realistic availability time.

Where committed historical data permits, measure outcomes using candidate/detection-ready time, including:

- +1m
- +2m
- +5m
- +10m
- +15m
- +30m
- +60m
- +1h
- +6h
- +24h

Where possible calculate:

- delayed-entry return;
- MFE;
- MAE;
- drawdown;
- liquidity;
- executable size;
- price extension from Frank fill to candidate-ready time;
- fraction already too extended at candidate-ready time.

Do not use future data as an online feature.

TTL must be explicit configuration with provenance.
Do not silently choose a permanent arbitrary TTL.

If history is insufficient, use:

`TEMPORARY_SHADOW_TTL`

and clearly report it as unvalidated temporary shadow logic.

Every candidate must have `expires_at`.
Expired candidates must never become live sendable alerts after recovery.

---

## 11. Immutable run contract

Each evaluation cycle must have an immutable run identity.

Renderer/delivery inputs must be tied to the current run only.

A new run must not mutate the prior run body.

Use stable concepts such as:

- `run_id`
- `candidate_id`
- `signal_id`
- `decision_id`
- `mail_run_id`
- `content_hash`

Published immutable run files must not later be silently rewritten as another logical run.

Identical republish should create zero semantic duplicate.

---

## 12. Email renderer — stale-content must be structurally impossible

Every email render starts from an empty document.

Renderer may read ONLY:

- current immutable run;
- current run decisions;
- current run enrichment.

Renderer must NOT read as template input:

- previous email body;
- previous email HTML;
- previous report prose;
- stale cached section fragments;
- prior run tokens/persons;
- prior run enrichment.

Possible sections:

1. `多人同币 / TOKEN_CONSENSUS`
2. `单人模式 / PERSON_PATTERN`

Rules:

- zero SEND signals in a section -> omit the entire section;
- both sections empty -> no sendable email artifact;
- same token qualifies TOKEN_CONSENSUS + PERSON_PATTERN -> exactly one full token block under consensus, with person-pattern reason attached;
- multiple distinct valid tokens -> retain all exactly once;
- never duplicate a full token block across sections.

---

## 13. Mandatory stale-content regression fixture

Create explicit tests:

RUN_A:

- TOKEN_CONSENSUS:
  Frank + PersonA -> TOKEN_X
- PERSON_PATTERN:
  Frank -> TOKEN_Y

Then immediately RUN_B:

- TOKEN_CONSENSUS: NONE
- PERSON_PATTERN:
  PersonA -> TOKEN_Z

Assertions for RUN_B:

- TOKEN_X occurrences = 0
- TOKEN_Y occurrences = 0
- old `Frank + PersonA` consensus phrase occurrences = 0
- TOKEN_Z = exactly one full signal block
- no empty TOKEN_CONSENSUS section

This must remain an automated regression test.

---

## 14. Outbox / dedupe / crash recovery

Implement deterministic idempotency.

Use SQLite UNIQUE constraints / atomic transitions where appropriate.

Must safely handle:

1. a mail run is prepared;
2. downstream Gmail accepts it;
3. process crashes before local SENT persistence;
4. restart occurs;
5. downstream reads/searches Gmail Sent using stable identity;
6. if already delivered, retry is suppressed.

Required stable fields/concepts:

- signal_id
- decision_id
- run_id
- mail_run_id
- content_hash
- outbox status
- Gmail message id/readback receipt fields

Codex must implement/test the deterministic infrastructure but must not send real Gmail.

---

## 15. Mandatory automated tests

At minimum test all of these:

1. prior run has consensus+person; current run person-only -> zero prior consensus content;
2. prior run has signals; current run none -> no email artifact;
3. same run processed twice -> one outbox/delivery identity;
4. simulated Gmail accepted but local SENT state missing -> readback suppresses resend;
5. same person owns two wallets and both buy token -> unique person count = 1;
6. Frank + second independent person -> unique person count = 2;
7. same token consensus + person-pattern -> one full block;
8. two distinct tokens -> both retained once;
9. GPT/enrichment failure -> no previous enrichment leakage;
10. crash during render -> deterministic clean rebuild;
11. expired candidate -> no sendable outbox;
12. concurrent workers -> one outbox result;
13. restart/cursor recovery -> no candidate loss/duplicate;
14. stale old HTML/cache/JSON deliberately planted -> current render unchanged;
15. synthetic test namespace cannot be consumed by live path;
16. old Frank historical candidates do not replay as new Meme live candidates;
17. schema/hash mismatch -> fail closed;
18. missing deterministic facts -> explicit unavailable/null, never fabricated.

---

## 16. Private runtime Git handoff

Preferred private repo:
- `lxxlx2/crypto-monitor-runtime`

Preferred live structure:

- `runtime-v2/meme/manifest/current.json`
- `runtime-v2/meme/runs/<run_id>/candidate-bundle.json`
- `runtime-v2/meme/runs/<run_id>/renderer-input.json`
- `runtime-v2/meme/runs/<run_id>/transport-receipt.json`

You may refine names only if needed, but document a single stable canonical contract.

Requirements:

- private repo only for runtime evidence;
- no private keys/API keys/secrets;
- immutable run files;
- atomic current manifest pointer;
- hashes/exact readback;
- identical republish -> zero semantic duplicate;
- restart-safe;
- bounded retention documented;
- do not delete audit evidence in FM4;
- test namespace strictly separated from live namespace;
- live path contains real forward candidates only.

If private repo is unavailable:

- implement publisher/reader schemas and tests in project repo;
- document exact target private paths;
- report `PRIVATE_RUNTIME_REPO_EXECUTION_REQUIRED`;
- do not fabricate remote readback PASS.

---

## 17. Mac-local migration package

Cloud Codex must prepare, but cannot claim to execute, the real Mac migration from:

`com.jerson.crypto-monitor-frank-shadow`

to:

`com.jerson.crypto-monitor-meme-shadow`

Create an exact, deterministic local migration package/scripts/checklist with:

1. preflight discovery of configured local paths;
2. SQLite integrity check;
3. cursor/state snapshot;
4. backup step;
5. record candidate counts before migration;
6. stop old Frank agent;
7. verify old process stopped;
8. install/start one Meme agent using same durable state;
9. verify exactly one Frank/Meme scanner process;
10. verify no double polling;
11. verify cursor monotonicity;
12. verify candidate count did not reset;
13. verify historical candidates were not replayed;
14. verify SQLite integrity again;
15. restart/recovery check;
16. gap/duplicate check;
17. rollback procedure to known-good Frank agent;
18. machine-readable local acceptance output.

Do not hard-code unknown `/Users/jerson/...` paths unless a committed config explicitly establishes them.
Unknown local paths should be CLI/config arguments.

All real results for this section remain:

`LOCAL_EXECUTION_REQUIRED`

until someone actually executes the package on the Mac and provides evidence.

---

## 18. Live runtime safety

Current Frank/Meme real-time polling has highest operational priority.

Repository-side work must not design an implementation that requires loading unbounded full history into the live process.

Preserve:

- durable cursor/state;
- restart safety;
- SQLite integrity;
- no gaps;
- no duplicate candidates;
- bounded memory;
- background historical work lower priority than real-time polling.

Do not silently replace official/finalized chain evidence with lower-quality sources.

---

## 19. Real Gmail test boundary

Codex Cloud must not send synthetic or real investment emails.

Codex acceptance responsibility:

- renderer isolation;
- stale-content tests;
- outbox/dedupe;
- crash recovery;
- concurrency;
- TTL expiry;
- simulated Gmail-accepted/local-state-lost behavior.

The existing ChatGPT `$300-3000` task owns the first real SEND:

- GPT final decision;
- Gmail send;
- Gmail Sent message id;
- readback;
- duplicate prevention;
- actual email body quality.

Until a real valid SEND candidate occurs and that external path is verified, report:

`REAL_GMAIL_E2E = NOT_YET_OBSERVED`

Synthetic data must never be mailed to the user merely to make this field PASS.

---

## 20. No ChatGPT task mutation from Codex

Important separation:

The user may be able to see Scheduled Tasks from the ChatGPT/Codex desktop UI, but this FM4 cloud coding task must not assume it owns or can safely mutate ChatGPT Scheduled Tasks.

Do NOT:

- create another `$300-3000` task;
- create a duplicate Meme task;
- rename the current ChatGPT task;
- alter its schedule;
- pause/resume it;
- enable old `$300 Crypto资产状态监控`;
- create Codex automation as a substitute.

Treat the ChatGPT task as an external downstream consumer with a documented interface.

---

## 21. Report

Create/update:

`crypto-300-profit-mission/local-agent/PHASE_FM4_MEME_SIGNAL_PIPELINE_REPORT.md`

Report actual evidence only.

Required fields:

1. cloud environment / repository access status
2. branch starting SHA
3. Frank/Meme source discovery result
4. person registry schema/result
5. candidate schema version
6. TOKEN_CONSENSUS implementation status
7. PERSON_PATTERN implementation status
8. wallets-per-person test
9. unique-person consensus test
10. real TOKEN_CONSENSUS count available from accessible real data
11. Frank feature bundle status
12. followability historical diagnostics
13. TTL state + provenance
14. immutable run schema
15. current-run renderer isolation
16. RUN_A/RUN_B contamination test
17. same-token dual-family dedupe test
18. no-signal/no-email-artifact test
19. duplicate-run/outbox test
20. concurrent worker race test
21. expired candidate test
22. simulated Gmail accepted/local SENT lost test
23. test/live namespace isolation
24. private runtime repo access status
25. private runtime publish/readback/hash status or explicit pending status
26. identical republish result
27. generated Mac migration package path(s)
28. Mac LaunchAgent migration = `LOCAL_EXECUTION_REQUIRED` unless truly executed outside cloud with evidence
29. live Mac SQLite check = `LOCAL_EXECUTION_REQUIRED` unless real evidence supplied
30. live Mac CPU/RSS = `LOCAL_EXECUTION_REQUIRED` unless real evidence supplied
31. real Gmail E2E = `NOT_YET_OBSERVED` unless independently verified after a real SEND
32. pytest results
33. compileall/static checks
34. dependency/pip checks as applicable
35. resource usage of cloud-side test/replay
36. no production trades/wallet mutation
37. Monster/NFT/Core Price changes = 0 except necessary documentation references
38. final branch SHA
39. push result
40. next gate

Never use `PASS` for something you did not actually execute or read back.

---

## 22. Stop conditions

Stop and report instead of loosening gates if any of these occur:

- required committed source for safe refactor is missing;
- refactor risks replaying old Frank candidates as new Meme signals;
- durable identity cannot be guaranteed;
- private Git run identity is mutable/ambiguous;
- renderer can leak stale content;
- outbox/dedupe fails crash recovery;
- concurrent workers can produce duplicate sendable output;
- test namespace can leak into live namespace;
- historical followability shows the current E2E delay makes the signal practically unusable;
- cloud environment lacks an essential dependency and there is no safe deterministic fallback.

Do not solve failure by weakening acceptance without explicit user approval.

---

## 23. Deferred components — preserve for later

Do not work on them in FM4, but preserve them:

### Monster / 妖币
- status: `DEFERRED_NOT_CANCELLED`
- technical state: `MONSTER_D1_V2_NEEDS_REDESIGN`
- later work requires a new D1 architecture/frozen grid, not reopening current failed result.

### NFT
- status: `DEFERRED_NOT_CANCELLED`
- prior research/requirements remain part of `$300-3000`.

### Core Price / broader market analysis
- status: `DEFERRED_NOT_CANCELLED`
- Core Price V3 remains paused, not deleted.

Do not create separate monitoring tasks for these components.

---

## 24. Completion rules

When repository-side FM4 work is complete:

1. run all relevant tests;
2. run compile/static/dependency checks;
3. inspect the final diff;
4. run credential/secret scan appropriate for changed files;
5. write the FM4 report;
6. commit only relevant changes;
7. push to `codex/crypto-monitor-design-20260930`;
8. verify remote HEAD matches the pushed commit;
9. report cloud worktree status;
10. return:
   - report path
   - final commit SHA
   - test summary
   - private runtime result
   - exact list of `LOCAL_EXECUTION_REQUIRED` items
   - exact next local command/package needed for Mac acceptance

Do NOT automatically start FM5.
Do NOT start Monster redesign.
Do NOT resume NFT/Core Price.
Do NOT create or edit ChatGPT/Codex automations.

Final vocabulary:

- MEME = `ACTIVE_DEVELOPMENT_PRIORITY`
- MONSTER = `DEFERRED_NOT_CANCELLED / NEEDS_REDESIGN`
- NFT = `DEFERRED_NOT_CANCELLED`
- CORE PRICE / broader market analysis = `DEFERRED_NOT_CANCELLED`
- old `$300 Crypto资产状态监控` = `DISABLED_LEGACY`
- ChatGPT task = `$300-3000`
- PRODUCTION TRADING = `NO_GO`
