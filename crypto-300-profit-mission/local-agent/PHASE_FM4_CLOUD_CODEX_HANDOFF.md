# PHASE_FM4 CLOUD CODEX HANDOFF — MEME SIGNAL PIPELINE

This is the cloud-Codex entry point for FM4.

## 0. Environment boundary — read this first

You are expected to run in **cloud Codex**, not on the user's Mac.

Therefore you MUST distinguish repository work from Mac-local runtime work.

Cloud Codex CAN:
- read/edit/push the GitHub branch;
- implement schemas, parsers, signal aggregation, renderer, outbox/dedupe, tests and migration scripts;
- inspect committed FM1–FM3 reports/specs/source code;
- work with the connected private runtime repo if permission is available;
- create code/tests/docs needed for the later local migration.

Cloud Codex CANNOT truthfully claim it has directly:
- inspected `/Users/jerson/...` files that are not committed;
- read the user's live Mac SQLite database/cursor unless an explicitly sanitized snapshot has been committed/provided;
- stopped/started/renamed a macOS LaunchAgent;
- measured the currently running Mac process CPU/RSS;
- proved live polling continuity across a real Mac LaunchAgent migration;
- executed local Gmail/ChatGPT automation changes.

For every acceptance field requiring Mac-local execution, implement the migration/verification tooling and mark the result `LOCAL_EXECUTION_REQUIRED` until a real local run supplies evidence. Never fabricate PASS.

## 1. Repositories / branch

Primary project repo:
- `lxxlx2/ChatGPT_mission_record`
- branch: `codex/crypto-monitor-design-20260930`

Private runtime handoff repo:
- `lxxlx2/crypto-monitor-runtime`
- private
- use only if the cloud Codex session has actual permission; if unavailable, report `PRIVATE_RUNTIME_REPO_UNAVAILABLE` and continue all work that does not require it.

Do not create another repository.
Do not rebase or force-push frozen history.

## 2. Read these files in this order

From `lxxlx2/ChatGPT_mission_record` branch `codex/crypto-monitor-design-20260930`:

1. `crypto-300-profit-mission/local-agent/CURRENT_MAINLINE_CHECKPOINT.md`
2. `crypto-300-profit-mission/local-agent/PHASE_FM3_FRANK_MONSTER_REPORT.md`
3. `crypto-300-profit-mission/local-agent/PHASE_FM4_MEME_SIGNAL_PIPELINE_PROMPT.md`
4. this file: `crypto-300-profit-mission/local-agent/PHASE_FM4_CLOUD_CODEX_HANDOFF.md`

From `main`:

5. `crypto-300-profit-mission/meme/MEME_GPT_MONITOR_SPEC.md`
6. `crypto-300-profit-mission/portfolio/current.md` only for current accounting context; it is not an FM4 implementation dependency.

Then inspect all committed Frank shadow/runtime/parser/SQLite/transport/test source referenced by FM3. Search the repository by the exact identifiers below if paths are not obvious:
- `com.jerson.crypto-monitor-frank-shadow`
- `frank-forward-shadow`
- `FRANK_ACTIVE_E2E_PASS`
- `RAW_FRANK_CANDIDATE`
- `synthetic-local-v1`
- `monster_d1_v2`

Do not guess local-only file contents.

## 3. Authoritative current status

- `FRANK_SHADOW_READY = PASS`
- `FRANK_ACTIVE_E2E = PASS`
- real forward ACTIVE -> normalization -> candidate -> SQLite -> private transport -> exact readback has been proven in FM3
- Frank is becoming one person inside the generalized **Meme** monitor
- system name target: `Meme`
- tracked person now: `person_id=frank`
- Frank wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`
- GPT remains final investment-value judgment layer
- deterministic code owns chain facts, identities, aggregation, TTL, IDs, dedupe, outbox, current-run isolation
- current ChatGPT monitor name: `$300-3000`
- old `$300 Crypto资产状态监控` remains disabled
- production trading remains `NO_GO`

## 4. Deferred work is NOT cancelled

The following are deliberately **DEFERRED_NOT_CANCELLED** while Meme is completed first:

- CORE PRICE / broader market-price analysis
- NFT opportunity/reminder pipeline
- MONSTER / 妖币 monitor redesign and productionization

Do not delete their specifications, history, datasets, tests or future roadmap.
Do not describe them as abandoned, removed, permanently disabled or out of the `$300-3000` mission.

Current sequencing only:

1. Meme / tracked-person signal pipeline
2. then resume MONSTER redesign
3. then resume NFT alert work and broader price/market-analysis work according to later user prioritization

No new ChatGPT tasks are authorized for those deferred components now.

## 5. FM4 implementation objective

Implement the repository-side work for:

1. Frank -> Meme generalization;
2. person registry with multiple wallets per person;
3. unique-person TOKEN_CONSENSUS aggregation;
4. PERSON_PATTERN deterministic feature handoff;
5. immutable candidate/run schema;
6. explicit TTL / followability fields;
7. private Git handoff contract for GPT;
8. clean current-run-only email renderer contract;
9. outbox/dedupe/crash-recovery/concurrency protection;
10. automated stale-content and duplicate-delivery regression tests;
11. local migration scripts/checklists for the Mac LaunchAgent, but do not claim they ran in cloud.

Use `PHASE_FM4_MEME_SIGNAL_PIPELINE_PROMPT.md` and `MEME_GPT_MONITOR_SPEC.md` for the detailed acceptance rules. If this cloud handoff conflicts with assumptions that require local Mac access, this file wins for environment semantics: implement the tooling, then mark local execution as pending.

## 6. Person model

Minimum registry entry:

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
- one person may have multiple wallets;
- consensus counts unique `person_id`, never wallets;
- no speculative new people;
- future user-approved people default `OBSERVE_ONLY` for PERSON_PATTERN until their history is separately validated;
- verified OBSERVE_ONLY people may still contribute to TOKEN_CONSENSUS.

## 7. Signal families

### TOKEN_CONSENSUS

Deterministic code establishes:
- token identity;
- unique people;
- wallet/person mapping;
- qualifying BUYs;
- timestamps;
- amounts where deterministic;
- time window;
- stable event/signal identity;
- TTL and dedupe.

Normally require >=2 independent people before GPT review.
With only Frank configured, real live TOKEN_CONSENSUS should remain zero.
Synthetic fixtures must never enter live paths.

### PERSON_PATTERN

Deterministic code establishes Frank-specific facts/features, including where reliable:
- first entry / add / re-entry;
- size relative to Frank history;
- token age;
- prior Frank exposure;
- elapsed time;
- price movement since entry;
- liquidity/market-cap causal context;
- historical pattern reason codes;
- followability timings.

Do not make final SEND/NO_SEND investment judgment in Codex code. `$300-3000` GPT remains that layer.

## 8. Email correctness is mandatory

Every mail render starts from an empty document and reads only the current immutable run + current decisions/enrichment.
Never patch/reuse prior mail/HTML/cache.

Possible sections:
- `多人同币 / TOKEN_CONSENSUS`
- `单人模式 / PERSON_PATTERN`

No SEND signals in a section => omit the section.
Both empty => no mail artifact.
Same token qualifies both families => exactly one full token block, under consensus, with person-pattern reasons attached.

Mandatory regression fixture:

RUN_A:
- consensus: Frank + PersonA -> TOKEN_X
- person: Frank -> TOKEN_Y

RUN_B:
- consensus: none
- person: PersonA -> TOKEN_Z

RUN_B assertions:
- TOKEN_X = 0 occurrences
- TOKEN_Y = 0 occurrences
- old `Frank + PersonA` consensus phrase = 0
- TOKEN_Z = exactly one full signal block

Also test duplicate run, concurrent workers, crash during render, stale cache, expired candidate, same-person-two-wallets, same-token dual-family, no-signal/no-mail, and simulated Gmail-accepted/local-SENT-loss.

## 9. Followability

Optimize and evaluate for user-followable performance, not Frank's original fill PnL.

Where committed historical data permits, measure delayed-entry outcomes from candidate/detection availability at:
- 1m, 2m, 5m, 10m, 15m, 30m, 60m
- 1h, 6h, 24h

Include MFE/MAE, liquidity/executable-size context and price extension by alert-ready time.
Do not use future data as an online feature.
TTL must be explicit and provenance-tagged; if not validated use `TEMPORARY_SHADOW_TTL`.

## 10. Private runtime contract

Preferred live structure in `lxxlx2/crypto-monitor-runtime`:

- `runtime-v2/meme/manifest/current.json`
- `runtime-v2/meme/runs/<run_id>/candidate-bundle.json`
- `runtime-v2/meme/runs/<run_id>/renderer-input.json`
- `runtime-v2/meme/runs/<run_id>/transport-receipt.json`

Requirements:
- immutable run files;
- current manifest is an atomic pointer;
- hashes/exact readback;
- identical republish has zero semantic duplicate;
- no secrets;
- test namespace cannot be consumed by live `$300-3000`;
- live path contains only real forward candidates.

If private repo is unavailable to cloud Codex, implement the publisher/reader contract and tests in the project repo, document exact intended private paths, and mark remote publish/readback `PRIVATE_RUNTIME_REPO_EXECUTION_REQUIRED` rather than inventing success.

## 11. Mac-local handoff package required from cloud Codex

Because cloud Codex cannot mutate the Mac LaunchAgent, FM4 must produce a deterministic local handoff package containing:

1. a migration script or exact commands to move:
   `com.jerson.crypto-monitor-frank-shadow`
   -> `com.jerson.crypto-monitor-meme-shadow`;
2. preflight checks for current SQLite/cursor/state;
3. backup/snapshot step;
4. exactly-one-agent check;
5. no-double-polling check;
6. SQLite integrity check;
7. cursor monotonicity check;
8. candidate-count no-reset/no-replay check;
9. restart/recovery check;
10. rollback script/instructions;
11. machine-readable local acceptance output that can later be attached or committed.

Do NOT embed secrets or absolute assumptions that only worked on the original developer machine unless discovered from committed configuration. Where a local path is unknown, make it a required CLI/config argument.

## 12. Report semantics

Create/update:
- `crypto-300-profit-mission/local-agent/PHASE_FM4_MEME_SIGNAL_PIPELINE_REPORT.md`

For repository-side tests, report PASS/FAIL with evidence.
For Mac-only checks not actually executed by cloud Codex, report `LOCAL_EXECUTION_REQUIRED`.
For real Gmail E2E before any real SEND exists, report `NOT_YET_OBSERVED`.
Never convert either state to PASS just to complete the phase.

At minimum report:
- repository implementation results;
- test results;
- renderer contamination tests;
- outbox/dedupe/concurrency tests;
- person/wallet aggregation tests;
- followability diagnostics available from committed data;
- private runtime repo access/result;
- generated Mac migration tooling;
- which local acceptance checks remain pending;
- branch/HEAD/worktree state from the cloud checkout;
- next gate.

## 13. Stop conditions

Stop rather than weaken gates if:
- repository state needed for a safe migration is missing;
- old candidates could replay as new;
- immutable run identity cannot be guaranteed;
- renderer leaks stale-run content;
- outbox/dedupe fails crash/concurrency tests;
- test/live namespace isolation is not provable;
- historical followability contradicts usefulness at the current end-to-end latency.

## 14. Final status vocabulary

Use exactly this intent:

- MEME = ACTIVE DEVELOPMENT / PRIORITY
- MONSTER = DEFERRED_NOT_CANCELLED / NEEDS_REDESIGN
- NFT = DEFERRED_NOT_CANCELLED
- CORE PRICE / broader market analysis = DEFERRED_NOT_CANCELLED
- old `$300 Crypto资产状态监控` = DISABLED_LEGACY
- new ChatGPT monitor = `$300-3000`
- PRODUCTION TRADING = NO_GO

When finished, push only to the existing branch `codex/crypto-monitor-design-20260930`, return the report path and final SHA, and do not automatically start the deferred Monster/NFT/Core-Price phases.