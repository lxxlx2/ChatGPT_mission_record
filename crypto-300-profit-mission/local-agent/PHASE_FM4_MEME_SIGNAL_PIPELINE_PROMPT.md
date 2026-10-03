# PHASE_FM4 — FRANK → MEME GENERALIZATION + GPT HANDOFF + MAIL CORRECTNESS

You are continuing work in the existing local repo/branch used for FM1–FM3.

Do not create a new branch unless the current branch is unavailable. Do not rebase or force-push frozen history.

## Read first

1. `crypto-300-profit-mission/local-agent/CURRENT_MAINLINE_CHECKPOINT.md`
2. `crypto-300-profit-mission/local-agent/PHASE_FM3_FRANK_MONSTER_REPORT.md`
3. main-branch canonical `crypto-300-profit-mission/meme/MEME_GPT_MONITOR_SPEC.md`
4. all existing Frank shadow runtime, SQLite, transport and tests before editing.

FM3 facts are authoritative:
- `FRANK_SHADOW_READY = PASS`
- `FRANK_ACTIVE_E2E = PASS`
- real ACTIVE forward E2E already proven
- Monster remains `MONSTER_D1_V2_NEEDS_REDESIGN`
- user wants Frank/Meme finished first
- CORE PRICE V3 remains PAUSED
- NFT remains NOT STARTED
- production trading remains NO_GO

## Scope lock

This phase is only:

1. rename/generalize the Frank monitor architecture into **Meme**;
2. make Frank one `person_id` inside a multi-person registry;
3. support multiple verified wallets per person;
4. implement deterministic candidate-to-GPT handoff primitives for two signal families;
5. implement immutable-run / dedupe / outbox / stale-content isolation infrastructure;
6. build and test the email renderer contract locally without sending fabricated investment alerts;
7. publish a private Git handoff format that the authorized ChatGPT `$300` task can read;
8. preserve the existing working Frank real shadow collector and history.

Do NOT work on Monster redesign in this phase.
Do NOT add a Monster LaunchAgent.
Do NOT re-enable or modify old ChatGPT automations.
Do NOT create ChatGPT automations from Codex.
Do NOT perform wallet actions/trades.
Do NOT send real Gmail from Codex.

## 1. System rename / migration

Target naming:
- system = `Meme`
- current tracked person = `frank`
- Frank wallet remains `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

Create a person registry with schema roughly equivalent to:

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

Important:
- one person may have multiple wallets;
- consensus counts unique `person_id`, never wallet count;
- unknown/new people are not invented automatically;
- future added people default to `OBSERVE_ONLY` for PERSON_PATTERN until separately validated.

Migration must preserve all durable Frank state/cursors/history. Do not reset the scanner and do not replay old candidates as new live signals.

### LaunchAgent migration

Current agent: `com.jerson.crypto-monitor-frank-shadow`.

Prepare and execute a safe in-place migration to exactly one Meme shadow agent only if all prerequisites pass:

1. snapshot current Frank cursor/SQLite/state;
2. stop/unload old Frank agent;
3. install/load `com.jerson.crypto-monitor-meme-shadow` using the same durable state;
4. verify exactly one Meme/Frank scanner process exists;
5. verify no double polling;
6. verify candidate counts/state did not reset;
7. verify SQLite integrity;
8. verify restart/recovery again.

If any migration check fails, roll back to the known-good Frank LaunchAgent. Never leave both agents polling simultaneously.

## 2. Candidate schema v2

Every deterministic candidate must have immutable identifiers and enough context for GPT without GPT reconstructing chain facts.

Required fields at minimum:
- schema_version
- candidate_id
- event_id
- run_id or source_batch_id
- signal_family_candidate (`TOKEN_CONSENSUS` or `PERSON_PATTERN`)
- person_id(s)
- source wallet(s)
- chain
- mint / token address
- transaction signature(s)
- finalized block/slot evidence
- event timestamp(s)
- detected_at
- normalized_at
- candidate_created_at
- buy amount(s), denominated token and USD estimate only when deterministically supportable
- behavior type: first_entry / add / reentry / other
- local deterministic feature bundle
- source evidence hashes
- `expires_at`
- transport hash

Do not store previous email prose inside the candidate.

## 3. TOKEN_CONSENSUS deterministic preprocessor

Implement aggregation by token + causal time window using **unique person_id**.

Must support future multiple people but only Frank exists now.

It should produce a GPT-review candidate only when the deterministic minimum is met (normally >=2 independent person_ids). Since only Frank currently exists, real TOKEN_CONSENSUS should remain zero until the user supplies additional approved people.

Do not create fake people just to exercise production state.

For tests, use synthetic fixtures clearly isolated from live candidate directories and forbidden from Gmail transport.

Candidate fields should include:
- unique_person_count
- sorted person_ids
- each person's first qualifying buy timestamp
- each person's deterministic buy amount
- first_event_at / last_event_at / window_seconds
- token identity
- current deterministic price/liquidity fields only if sourced reliably; otherwise explicit null + reason

## 4. PERSON_PATTERN deterministic handoff

For Frank, build a reproducible feature bundle from the already validated parser/history. Do NOT make the final investment SEND/NO_SEND decision locally.

The local layer should provide features such as where reliably available:
- first entry vs add vs re-entry
- buy size relative to Frank's historical distribution
- token age at entry
- liquidity/market-cap context if sourced causally
- prior Frank exposure to same mint
- elapsed time since entry
- price change since Frank entry
- historical pattern/reason codes
- followability-related timing fields

Do not claim a strategy is validated merely because a feature bundle exists.

## 5. TTL / followability

Do not silently hard-code a permanent arbitrary TTL.

Implement TTL as an explicit configuration field with provenance.

For FM4:
- derive candidate followability diagnostics from Frank historical examples if possible;
- report how often hypothetical signals remain usable at 1m / 2m / 5m / 10m / 15m / 30m / 60m after detected time;
- if data is insufficient, choose a conservative temporary SHADOW TTL and label it `TEMPORARY_SHADOW_TTL`, not validated production logic.

Every candidate must carry `expires_at`.

Expired candidates must never be promoted to a live Gmail alert by downstream consumers.

## 6. Immutable run / renderer isolation

Implement current-run-only rendering.

Hard rule:
- renderer starts from an empty document for every run;
- renderer input is exactly the immutable current run candidate/decision bundle;
- renderer cannot read or patch a previous email body;
- previous HTML/text/cache files may exist but cannot be inputs to the new render.

Sections:
1. `多人同币 / TOKEN_CONSENSUS`
2. `单人模式 / PERSON_PATTERN`

Rules:
- zero SEND signals in a section => section omitted;
- both sections empty => no mail artifact to send;
- same token qualifies consensus + person pattern => one full token block under consensus, with attached person-pattern reason; no duplicate full block;
- multiple distinct tokens => all retained once.

## 7. Dedupe / outbox / delivery handshake

Implement deterministic idempotency primitives even though Codex itself must not send Gmail.

Required stable concepts:
- `signal_id`
- `decision_id`
- `run_id`
- `mail_run_id`
- `content_hash`
- outbox status
- Gmail message-id/readback receipt fields for the downstream GPT task

Use SQLite UNIQUE constraints and atomic state transitions where appropriate.

Design for this failure case:
1. downstream Gmail accepts mail;
2. process crashes before local SENT persistence;
3. restart occurs;
4. downstream must search/read back Gmail Sent using stable identity before retry;
5. duplicate send must be prevented.

## 8. Mandatory contamination / duplicate tests

Add automated tests for all cases in `MEME_GPT_MONITOR_SPEC.md`.

Mandatory explicit fixture:

RUN_A:
- TOKEN_CONSENSUS: Frank + PersonA -> TOKEN_X
- PERSON_PATTERN: Frank -> TOKEN_Y

RUN_B:
- TOKEN_CONSENSUS: none
- PERSON_PATTERN: PersonA -> TOKEN_Z

Assert RUN_B rendered output contains:
- TOKEN_X = 0 occurrences
- TOKEN_Y = 0 occurrences
- prior `Frank + PersonA` consensus phrase = 0 occurrences
- TOKEN_Z = exactly one full signal block

Also test:
- same run executed twice -> one outbox item / one eventual delivery identity;
- Gmail-accepted-local-state-lost simulated receipt -> retry suppressed after readback simulation;
- same person two wallets -> consensus count one;
- same token consensus + person pattern -> one block;
- no signals -> no email artifact;
- enrichment failure -> no previous-run content;
- crash during render -> deterministic clean rebuild;
- expired candidate -> no sendable outbox item;
- concurrent worker race -> one outbox result;
- restart/cursor recovery -> no candidate loss/duplication;
- stale cache files deliberately planted -> current render unaffected.

## 9. Private Git GPT handoff

Use existing private repository:
- `lxxlx2/crypto-monitor-runtime`

Do not create another repository.

Create a clear, bounded path such as:
- `runtime-v2/meme/manifest/current.json`
- `runtime-v2/meme/runs/<run_id>/candidate-bundle.json`
- `runtime-v2/meme/runs/<run_id>/renderer-input.json`
- `runtime-v2/meme/runs/<run_id>/transport-receipt.json`

You may refine names, but document them clearly and keep them stable.

Requirements:
- private repo only;
- no secrets/private keys/API keys;
- immutable run files after publish;
- atomic current manifest pointer;
- hashes for exact readback;
- identical republish -> zero semantic change / no duplicate run;
- restart recovery;
- bounded retention policy documented, but do not delete audit evidence in FM4 unless already covered by existing policy.

Publish at least one **clearly marked synthetic test fixture** only if it is stored under a test namespace that the live GPT task is contractually forbidden to treat as a live candidate.

The live path must contain only real forward data.

## 10. GPT task interface contract

Codex does not execute GPT investment judgment.

It must provide enough deterministic data for the authorized ChatGPT `$300` task to output a machine-readable result:
- SEND / NO_SEND
- reason_codes[]
- evidence[]
- risks[]
- followable_now
- confidence
- decided_at
- candidate_age_seconds

Prepare a place in the private runtime structure for downstream decision/delivery receipts if writeback is technically available. If the ChatGPT connector cannot reliably write back to the private repo during task execution, document the limitation and keep the source bundle immutable; do not fake writeback.

## 11. Email integration test boundary

Codex itself has no permission to send Gmail.

Therefore FM4 email acceptance has two layers:

A. Codex must fully PASS local renderer/outbox/dedupe/contamination tests.

B. The newly authorized ChatGPT `$300` task owns real Gmail send + Sent/readback verification on the first real SEND candidate. Until that happens, label Gmail E2E as `NOT_YET_OBSERVED`, not PASS.

Do not send synthetic investment alerts to the user.

## 12. Followability validation

The key strategy metric is USER-FOLLOWABLE performance, not Frank's original PnL.

Build replay outputs allowing delayed-entry analysis at realistic observation times.

At minimum measure where data permits:
- T+1m / 2m / 5m / 10m / 15m / 30m / 60m from detected/candidate time;
- T+1h / 6h / 24h outcomes;
- MFE / MAE;
- liquidity/executable size;
- price change between Frank fill and candidate readiness;
- proportion of historical candidates already too extended by alert time.

Do not use future data as an online feature.

## 13. Resource / runtime safety

Frank/Meme real-time polling remains highest priority.

Target:
- no historical/replay task should starve real-time polling;
- keep RSS comfortably below existing FM3 gates;
- no unbounded in-memory history loads;
- preserve current working SQLite database and evidence.

## 14. Acceptance report

Create:
- `crypto-300-profit-mission/local-agent/PHASE_FM4_MEME_SIGNAL_PIPELINE_REPORT.md`

Report exact results, not aspirations.

Required fields:
1. old Frank LaunchAgent state before migration
2. new Meme LaunchAgent state after migration or rollback result
3. exact number of local scanner agents/processes
4. state/cursor migration proof
5. SQLite integrity
6. Frank live polling continuity
7. candidate counts before/after migration
8. person registry schema/result
9. wallets-per-person behavior test
10. consensus unique-person test
11. real TOKEN_CONSENSUS count (expected zero while only Frank exists)
12. Frank PERSON_PATTERN feature bundle status
13. historical followability diagnostics
14. TTL status and provenance
15. candidate schema version
16. immutable run schema
17. private runtime path
18. private exact readback/hash result
19. identical republish result
20. restart recovery result
21. renderer current-run isolation result
22. explicit RUN_A/RUN_B contamination fixture result
23. same-token dual-family dedupe result
24. no-signal no-email-artifact result
25. concurrent outbox race result
26. expired candidate result
27. simulated Gmail-accepted/local-state-lost dedupe result
28. pytest/compileall/pip check results
29. CPU/RSS/disk
30. real Gmail E2E status (`NOT_YET_OBSERVED` unless a real downstream task send actually occurs and is separately verified)
31. production writes/trades/wallet actions = 0
32. Monster changes = 0 except documentation references if necessary
33. branch/HEAD/worktree cleanliness
34. next gate

## 15. Stop conditions

Stop and report rather than silently weakening acceptance if:
- state migration risks replaying old candidates;
- both Frank and Meme LaunchAgents would run concurrently;
- current scanner loses durable cursor/state;
- private Git handoff cannot guarantee immutable per-run identity/readback;
- renderer tests reveal stale-run contamination;
- dedupe/outbox cannot survive crash/restart simulation;
- followability data contradicts the assumed value of the current alert latency.

Do not solve a failure by loosening a gate without explicit user approval.

## Final boundaries

- CORE PRICE V3 = PAUSED
- NFT = NOT STARTED
- MONSTER D1 V2 = NEEDS_REDESIGN but out of FM4 scope
- old `$300 Crypto资产状态监控` = DISABLED
- exactly one new ChatGPT `$300` Meme GPT task is authorized outside Codex
- no other task creation
- no trades/wallet mutation
- PRODUCTION TRADING = NO_GO

Push the completed FM4 report and code to the existing branch, verify local/remote HEAD match, verify worktree clean, and return the report path + final SHA.