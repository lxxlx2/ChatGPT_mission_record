> 2026-10-04 Frank authority override: `SUPERSEDED_FOR_FRANK_SIGNAL_AUTHORITY`. Current Frank system is `FRANK_ONLY` / `LOCAL_DETERMINISTIC_SIGNAL` under frozen `FRANK_LOCAL_SIGNAL_V1`, live since 00:29:01 Asia/Bangkok. GPT SEND/NO_SEND is not an alert authority. Private legacy manifest is superseded/expired; history below is preserved. Other persons and TOKEN_CONSENSUS are DEFERRED. See [FRANK_LOCAL_SIGNAL_REFACTOR.md](FRANK_LOCAL_SIGNAL_REFACTOR.md).

# MEME GPT MONITOR SPEC

Updated: 2026-10-03
Timezone: Asia/Bangkok
Status: AUTHORIZED_FOR_ONE_NEW_$300_TASK

## Purpose

This is the canonical contract for the single newly authorized `$300` Meme GPT monitoring task.

The task consumes deterministic on-chain candidates produced by the local Meme runtime, performs the final investment-value judgment, and sends at most one clean Gmail alert per processing run when an actionable signal exists.

It must NOT create additional ChatGPT tasks, local LaunchAgents, wallet actions, trades, or unrelated monitoring scope.

## Architecture boundary

Local Meme runtime / Codex-owned deterministic layer:

1. wallet polling / transaction discovery;
2. finalized-chain evidence;
3. person_id and wallets[] mapping;
4. BUY / SELL / first-entry / add / reduce / re-entry classification;
5. amount, mint, timestamps, transaction signatures;
6. multi-person aggregation by unique person_id, never by raw wallet count;
7. candidate/run IDs, TTL, SQLite state, dedupe and outbox;
8. immutable per-run candidate bundle;
9. private Git transport and exact readback;
10. renderer state isolation / stale-content prevention primitives.

GPT task:

1. read only valid current candidate bundles;
2. perform final value judgment;
3. enrich with current project/market/liquidity/social/on-chain context when evidence is available;
4. decide SEND / NO_SEND with structured reasons;
5. compose one clean email for the current run only;
6. send through Gmail only after all gates pass;
7. verify Gmail Sent/readback and persist the decision/delivery receipt.

GPT must NOT invent chain facts, wallet ownership, trade sizes or historical performance.

## Signal types

### TOKEN_CONSENSUS

Question: are multiple independent tracked people buying the same token in a genuinely useful time window?

Requirements before GPT review:

- at least 2 unique `person_id` values;
- multiple wallets belonging to one person count as one person;
- deterministic evidence for each person's buy;
- timestamps and buy amounts present;
- aggregation window explicit;
- token/mint identity explicit;
- no duplicate underlying event.

GPT then judges whether the apparent consensus remains actionable, considering at minimum current price move since first/last tracked entry, market cap/liquidity if available, elapsed time, concentration/risk, project legitimacy/context, and whether the signal is still realistically followable.

### PERSON_PATTERN

Question: did one tracked person make a buy that matches a historically useful, followable pattern for that person?

The local layer supplies deterministic behavioral features and reason candidates. GPT must not simply rubber-stamp a local score; it must judge whether current context invalidates the historical pattern.

A person may only have PERSON_PATTERN user alerts enabled after that person's historical/replay evaluation is accepted. New people default to OBSERVE_ONLY for person-specific alerts, but may participate in TOKEN_CONSENSUS once wallet identity is verified.

## Followability is mandatory

The objective is not to reproduce tracked-wallet PnL. The objective is user-followable opportunity after real system delay.

For every SEND decision, record:

- tracked person's event time;
- candidate creation time;
- GPT task observation time;
- current decision time;
- elapsed age;
- price move since tracked entry when reliably available;
- whether the opportunity is still reasonably followable.

Never use the tracked wallet's entry price as if the user could have received it.

## TTL / stale-signal rule

Each candidate bundle must carry `expires_at` from the deterministic local layer.

- If `now >= expires_at`, do not send an investment alert.
- Record `EXPIRED_NO_SEND`.
- Never resurrect an expired alert after a scheduler outage or Gmail recovery.
- The TTL must ultimately be calibrated from historical followability analysis; Codex must not silently pick an arbitrary permanent TTL and call it validated.

## GPT structured decision

Every reviewed signal must persist a machine-readable decision with at least:

- decision_id
- run_id
- signal_id
- signal_type
- person_ids
- mint/token identity
- `SEND` or `NO_SEND`
- reason_codes[]
- evidence[]
- risks[]
- followable_now: true/false
- confidence: HIGH/MEDIUM/LOW
- decided_at
- candidate_age_seconds
- model/task version if available

Natural-language email text is secondary. The structured decision is canonical for later backtesting and auditing.

## Email contract

A run starts from an empty renderer state. Never edit/reuse the previous email body.

Renderer may read only the current immutable run bundle plus the current run's GPT decisions/enrichment. It must not read previous report bodies, previous HTML caches or stale section fragments.

Possible sections:

1. `多人同币 / TOKEN_CONSENSUS`
2. `单人模式 / PERSON_PATTERN`

Section rules:

- A section with zero SEND signals must be omitted entirely.
- If both sections are empty, send no email.
- If one token qualifies both as consensus and a person's pattern, describe it once in the consensus section and attach the person-pattern reason there; do not duplicate a full token block in both sections.
- Multiple distinct tokens may appear in the same email.
- Each token block must show CA/mint, who bought, when, approximate tracked amounts if deterministically available, why the signal passed, current risks, and the age of the signal.
- Never carry content from a previous run.

## Dedupe / delivery contract

Deterministic infrastructure owns idempotency.

Required concepts:

- stable `signal_id`;
- stable `run_id`;
- stable `mail_run_id`;
- content hash;
- SQLite UNIQUE constraints / atomic outbox state;
- Gmail Sent search/readback before any ambiguous retry.

A crash after Gmail accepts the message but before local SENT persistence must not produce a duplicate email after restart.

The same successful signal delivery must never be sent again unless a genuinely new underlying trade/material signal creates a new stable event identity.

## Mandatory regression tests before live Gmail

At minimum:

1. prior run has consensus + person signal; current run has only person signal -> no prior consensus/token text appears;
2. prior run has signals; current run has none -> no email;
3. same run executed twice -> maximum one delivered email;
4. Gmail accepted but local SENT write fails -> restart performs Sent readback and does not duplicate;
5. two wallets owned by same person buy one token -> unique-person count = 1;
6. same token is consensus + person-pattern -> one full token block only;
7. two different valid tokens -> neither is dropped;
8. GPT/enrichment failure -> no stale text from previous run;
9. crash during render -> rebuilt from current run only;
10. expired candidate after outage -> no late investment email;
11. concurrent workers on same event -> one outbox/delivery path;
12. restart/cursor recovery -> no lost or duplicated candidate;
13. old cache/HTML/JSON exists -> current email cannot reference it.

Explicit contamination fixture:

RUN_A:
- TOKEN_CONSENSUS: Frank + PersonA -> TOKEN_X
- PERSON_PATTERN: Frank -> TOKEN_Y

RUN_B:
- TOKEN_CONSENSUS: none
- PERSON_PATTERN: PersonA -> TOKEN_Z

RUN_B rendered body assertions:
- TOKEN_X occurrences = 0
- TOKEN_Y occurrences = 0
- `Frank + PersonA` prior consensus phrase occurrences = 0
- TOKEN_Z occurrences = exactly 1 full signal block

## Validation of judgment quality

Engineering PASS is not strategy PASS.

For each person and signal family, evaluate historical and forward results using user-followable timing:

- T+5m / 15m / 1h / 6h / 24h returns where meaningful;
- MFE / MAE;
- drawdown;
- liquidity / executable-size constraints;
- system-delayed hypothetical entry, not tracked-wallet entry;
- signal precision / base rate / false-positive burden;
- performance split by TRAIN / VALIDATION / HOLDOUT / real FORWARD.

For TOKEN_CONSENSUS, compare 1-person baseline against 2+ unique-person signals across multiple causal time windows. Do not assume consensus has value before evidence proves incremental edge.

## Current scheduling limitation

ChatGPT task scheduling supports at most one run per hour. This is slower than the intended 1–2 minute followability target for some meme trades.

Therefore:

- the authorized ChatGPT task may operate hourly as the current GPT judgment consumer;
- it must respect candidate TTL and may legitimately send nothing if a candidate has expired;
- do not claim this hourly path is production-grade real-time follow trading;
- Codex should preserve timestamps so we can measure how much edge is lost to the scheduler;
- a future lower-latency trigger/API design requires separate explicit authorization; do not create it implicitly.

## Current project gates

- FRANK collection/parsing/private transport: `FRANK_SHADOW_READY + FRANK_ACTIVE_E2E_PASS`
- system naming target: `Meme`; Frank becomes one `person_id`
- additional people: user-selected, preferably Frank-like and realistically followable
- MONSTER: `MONSTER_D1_V2_NEEDS_REDESIGN`
- CORE PRICE V3: PAUSED
- NFT: NOT STARTED
- old `$300 Crypto资产状态监控`: remains DISABLED
- exactly one newly authorized `$300` Meme GPT task: allowed
- trading / wallet mutation: unauthorized
- PRODUCTION trading: NO_GO
