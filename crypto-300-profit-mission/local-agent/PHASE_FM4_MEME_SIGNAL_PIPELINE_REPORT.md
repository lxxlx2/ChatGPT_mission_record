# PHASE_FM4 — Meme Signal Pipeline

Actual Mac-local acceptance, 2026-10-03 UTC. **PHASE_FM4 = PASS (authorized shadow engineering scope); production trading = NO_GO.**

Meme safely replaced Frank's system LaunchAgent using the existing durable state. Frank remains the sole live person. The existing real FM3 ACTIVE E2E is preserved; FM4 did not convert the old ACTIVE into a fresh signal. The live V2 handoff currently contains an empty `NO_CURRENT_SIGNALS` bundle. PERSON_PATTERN handoff infrastructure passes; a natural post-migration ACTIVE V2 handoff is not yet observed. No external GPT judgment or real Gmail delivery is claimed.

`MEME_SHADOW_READY=PASS`, `MEME_FRANK_SOURCE=PASS`, `FRANK_ACTIVE_E2E=PRESERVED_PASS`, `PERSON_REGISTRY=PASS`, `PERSON_PATTERN_HANDOFF=INFRA_PASS / REAL_FORWARD_PENDING`, `TOKEN_CONSENSUS_INFRA=PASS`, `REAL_TOKEN_CONSENSUS=0_EXPECTED`, `MAIL_RENDERER_CORRECTNESS=PASS`, `MAIL_DEDUPE_INFRA=PASS`, `PRIVATE_GPT_HANDOFF=PASS`, `REAL_GMAIL_E2E=NOT_YET_OBSERVED`.

Full private machine evidence: `/Users/jerson/Documents/ChatGPT/crypto-monitor-fm4-evidence-20261003`. Runtime remains at `/Users/jerson/Documents/ChatGPT/crypto-monitor-fm3-evidence-20261001/frank/shadow` intentionally to preserve SQLite, raw evidence and cursors. Private evidence is excluded from Git. Runtime contract: [MEME_FM4_RUNTIME_CONTRACT.md](docs/MEME_FM4_RUNTIME_CONTRACT.md).

| # | Acceptance field | Actual result |
|---|---|---|
| 1 | starting branch | codex/crypto-monitor-design-20260930 |
| 2 | starting SHA | 2fe359c0633ffd4452f53bb71cd0cc0916975e06 |
| 3 | starting worktree | CLEAN; nominal workspace untouched. Existing feature/main changes merged without rebase. |
| 4 | Frank LaunchAgent pre-state | RUNNING; com.jerson.crypto-monitor-frank-shadow; recorded 2026-10-03T05:12:07 UTC |
| 5 | Frank PID / process count | 69938 / exactly 1; uptime 6019.568 s |
| 6 | pre cursor | slot 452830645; signature SHA256 3a1a767c430614b96fdf955efa636d1767b31adc6c07a785723610f2c3b97129; full cursor private only |
| 7 | pre SQLite integrity | ok; forward.sqlite retained at original FM3 runtime path |
| 8 | pre candidate count | 2; observations 12; normalized transactions 513; batches 1 |
| 9 | pre poll count | 858 |
| 10 | pre private manifest | Existing FM3 ingest/current.json read from existing private repo; complete blob/hash binding in private pre-migration-state.json |
| 11 | backup / snapshot | PASS; consistent SQLite backup before stop and after stop, PRAGMA integrity_check=ok, hashed raw/detection/config/state copies; no credential backup |
| 12 | person registry | LIVE contains only user-confirmed Frank; verified Solana wallet; new persons default OBSERVE_ONLY; non-Frank enabling requires separately accepted history |
| 13 | multiple-wallet model | One person can own multiple verified wallets; independent source databases for additional wallets; no new live wallet/person added |
| 14 | Candidate Schema V2 | PASS: immutable IDs, person/wallet/mint/amount/decimals/signature/finalized slot/commitment/event+detected+normalized+created times/evidence hashes/TTL; missing facts null with reasons |
| 15 | TOKEN_CONSENSUS | PASS infrastructure: causal 900-second window; at least 2 unique persons, not wallets; verified OBSERVE_ONLY participants permitted |
| 16 | real consensus count | 0_EXPECTED: sole live person Frank |
| 17 | unique-person tests | PASS: Frank two wallets => 1 person; Frank + PersonA TEST => 2 people |
| 18 | PERSON_PATTERN | PASS infrastructure; Frank ACTIVE positive non-quote mint fact handoff; no local investment SEND decision |
| 19 | Frank feature bundle | Bounded preceding 500 causal observations; observed first-entry/add/reentry, amount/net debit facts and evidence; lifetime first-entry, USD, liquidity, market cap, price-change and percentile unavailable where not established |
| 20 | historical followability | INSUFFICIENT_EXECUTABLE_PRICE_HISTORY: 6482 available historical transactions; 591 ACTIVE classifications; 596 positive-mint observations; 12 real forward timing observations. 1/2/5/10/15/30/60m and 6/24h each N=0 executable returns. MFE/MAE/drawdown/precision/base rate/liquidity/executable size/overextension=null. No wallet-fill substitution or historical processing-time substitution. Strategy not validated; contradiction of value not proven. |
| 21 | TTL status / provenance | TEMPORARY_SHADOW_TTL; 900 seconds from FIRST_EVENT_AT; provenance config/meme_shadow_policy.json + historical price-coverage audit. Hourly consumer may discard every expired candidate; this is not a calibrated strategy TTL. |
| 22 | immutable run schema | PASS: stable run/candidate/signal/decision/mail IDs and content hash; resealed identity/fact tampering rejected |
| 23 | private runtime path | Existing private lxxlx2/crypto-monitor-runtime; LIVE runtime-v2/meme/{manifest/current.json,runs/<run_id>/{candidate-bundle.json,renderer-input.json,transport-receipt.json}}; TEST runtime-v2-test/meme/fm4-20261003 |
| 24 | exact publish / readback | PASS actual LIVE empty NO_CURRENT_SIGNALS run and actual TEST two-person fixture; immutable files exact-read before atomic current pointer; GPT consumer execution not claimed |
| 25 | hash verification | PASS canonical SHA256 and byte-exact remote readback; private receipts retained; no fabricated LIVE facts |
| 26 | identical republish | PASS actual LIVE repeat writes=0; actual TEST repeat PUTs=0; MemoryAPI partial-publish/restart/CAS rollback tests pass |
| 27 | old Frank agent stop | PASS actual bootout, worker drain, old plist archived then removed; old label disabled; no simultaneous polling |
| 28 | Meme agent install / start | PASS actual same durable runtime; com.jerson.crypto-monitor-meme-shadow installed and RUNNING |
| 29 | exact scanner process count | 1; launchd-managed Python Meme scanner, PID 23182 |
| 30 | cursor migration | PASS; pre/after/restart slot 452830645; identical signature retained (stable-no-new-tx); no reset or backward move |
| 31 | candidate count no-reset | PASS: legacy candidates 2 => 2; observations 12 => 12; transactions 513 => 513; batches 1 => 1 at migration/restart snapshots |
| 32 | old candidate no-replay | PASS: all 12 baseline observations BASELINE_EXCLUDED; old candidates retained but not converted; new Meme facts/signals 0 |
| 33 | polling continuity | 858 before => 860 after => 862 restart => 865 observed; 30-second polling; current RUNNING. Cumulative RPC errors/429=0/0; timeout/retry=1/1 already present before migration, no migration increase. |
| 34 | SQLite post integrity | ok; additive migration; same database; repeated migration and cursor-preserving backup tests PASS |
| 35 | restart result | PASS actual kickstart -k; PID changed 22523 => 23182; poll advanced, original cursor/counts preserved, exact current pointer preserved |
| 36 | gap | 0 current / 0 unresolved before, after and restart |
| 37 | duplicates | 0 candidate duplicates; one persisted source identity; restart tests PASS |
| 38 | renderer isolation | PASS pure current-run bundle/decisions/enrichment only; empty document each render; no previous files/cache input |
| 39 | RUN_A / RUN_B contamination | PASS permanent fixture: previous X/Y/Frank + PersonA absent; Z exactly one full block; consensus section absent; planted old HTML/JSON/cache ignored |
| 40 | dual-family dedupe | PASS same token in both families => one consensus block with pattern reasons; two tokens => each retained once |
| 41 | no-signal / no-mail | PASS both zero SEND => no sendable artifact; NO_SEND decisions can remain durable without mail |
| 42 | concurrent race | PASS 4 workers; one mail identity / one successful claim; SQLite UNIQUE + transaction |
| 43 | expired candidate | PASS no artifact or new send after TTL; pending state EXPIRED_NO_SEND; already accepted delivery can be reconciled after TTL |
| 44 | Gmail accepted / local SENT lost simulation | PASS TEST-only provider: accepted then crash before SENT; reopened SQLite + stable mail_run_id/content_hash Sent search/readback => SENT; accept count remains 1; uncertain/no-match never blindly retried |
| 45 | TEST / LIVE isolation | PASS synthetic bundle rejected before LIVE API; live source validator requires exact stored real post-cutoff observation and verified wallet; simulated mail provider TEST only |
| 46 | pytest | Python 3.14: 395 passed, 1 optional NumPy skip (3.55s); Python 3.12: 395 passed, 1 optional NumPy skip (3.32s); private Python 3.13 NumPy environment: 405 passed (4.75s). FM4 dedicated tests: 33 passed. Baseline 362 passed, 1 optional skip. |
| 47 | compileall | PASS: .venv312/bin/python -m compileall -q mission_agent scripts tests |
| 48 | pip / dependency check | PASS Python 3.12 and 3.14: No broken requirements found. Optional NumPy exercised separately, no mandatory test skipped. |
| 49 | CPU / RSS | Actual 60s / 13 samples; CPU mean 0.308% peak 3.300%; RSS mean 51.105 MiB peak 55.641 MiB. PID replacement during controlled restart recorded in samples; measurement did not pause polling. |
| 50 | disk | SQLite 4231168 bytes; FM4 evidence 8798208 bytes; FM3+FM4 2581798912 bytes; FM2+FM3+FM4 5020008448 bytes. Includes backups and existing evidence; no evidence deleted. |
| 51 | credential scan | PASS 16 implementation/test/config files: GitHub/OpenAI/AWS/private-key credential patterns zero hits; final report/checkpoint also scanned before push. Private raw signatures/mints/remote IDs remain outside Git. |
| 52 | real Gmail E2E | NOT_YET_OBSERVED; no real Gmail or synthetic investment email sent. External $300-3000 owns final investment decision and real delivery. |
| 53 | ChatGPT task mutations | 0; no task created/edited/enabled; legacy task remains untouched |
| 54 | wallet / trades | 0; no wallet mutation, order or trade |
| 55 | Monster changes | 0 logic/dataset/runtime changes; DEFERRED_NOT_CANCELLED / NEEDS_REDESIGN |
| 56 | NFT changes | 0; DEFERRED_NOT_CANCELLED |
| 57 | Core Price changes | 0; DEFERRED_NOT_CANCELLED |
| 58 | final branch | codex/crypto-monitor-design-20260930 |
| 59 | final SHA | Validated runtime implementation SHA: c12bb0a43c3c2ab04262de24aa383731d346bc6a. Delivery/report commit SHA is obtained after this report is committed; exact final SHA recorded in private final-delivery-verification.json and final response to avoid a self-referential Git commit hash. |
| 60 | remote HEAD | Delivery acceptance requires git rev-parse HEAD == git rev-parse origin/codex/crypto-monitor-design-20260930 after push; exact verified values retained in private final-delivery-verification.json and final response. |
| 61 | worktree cleanliness | Implementation commit clean before migration; final delivery gate requires git status --short empty after report/checkpoint commit and push, recorded separately. |
| 62 | next gate | STOP for FM4 review. Separately observe a natural post-migration real ACTIVE PERSON_PATTERN handoff and external GPT SEND/NO_SEND + genuine Gmail Sent readback/outcome audit. No FM5, new people, API triggering, Monster/NFT/Core Price or trading automatically. |

Followability remains a material limitation: no valid executable delayed-entry return series is available. The infrastructure PASS provides no evidence of investment edge. TTL expiry is enforced even if hourly downstream scheduling makes all signals stale. Real-time source polling remains active, with one scanner and bounded lower-priority history processing.

Provenance: starting clean local FM3 commit was merged with existing authorized feature documents (`9ab89bf7b77349457db76dd0d1ac4b749d076449`) and current main (`01f1e9e1079661c80bb53131c5a138dc18de7e3b`) without rebase/force push. The FM4 authored diff is compared to that merged baseline. FM3 reports, historical evidence and deferred modules are preserved. Rollback is implemented/tested, and the original known-good plist plus intact consistent snapshots remain available; actual migration succeeded, so rollback was not invoked.
