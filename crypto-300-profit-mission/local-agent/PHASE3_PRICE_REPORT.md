# PHASE3_PRICE_REPORT — 2026-09-30

**PHASE_3 = FAIL; PRICE_RULE_V1 = NEEDS_CALIBRATION; PHASE_4 = NO_GO; PRODUCTION = NO_GO.**

The frozen evaluation gate failed for ETH: 28/48 labelled minute samples hit, 20 missed, 58.33% recall versus the pre-results 90% gate with >=10 labels. User section45 requires reporting and stopping before tuning or further live escalation. PRICE_RULE_V1 thresholds are unchanged. Remaining collector gates are NOT IMPLEMENTED / NOT RUN, not an environment inability to hold a two-hour session.

## Branch, sync and validation

Branch: `codex/crypto-monitor-design-20260930`. Rebased onto `bc4f73040473b230bad392bdccb55d372ecc531a` after fetching. The nine new main commits only changed six airdrop-tge-monitor run records; no local-agent, Mission specs, portfolio/state or runtime contracts changed. A final fetch found three additional main commits ending at `a327d90d5dc78f6edd90b02a2197ac893b7ce67c`, touching only three crypto-daily research/run records. They also do not modify protected module/spec/state/contracts. Final rebase includes them; no main write. Previous remote feature base: `7e20485b296201b4d279e1551d2e67265d117740`. Frozen specifications committed before first replay in `d697e22`. Final implementation/report commit is the commit containing this report, followed only by any explicitly recorded main-sync commit; final SHA and ahead/behind are reported after push.

Rebase baseline: original 150 passed, 0 failed, 0 skipped. Final Python3.14.6 suite: 214 passed in1.17s; Python3.12.14: 214 passed in1.29s. Original tests independently rerun: 150 passed in0.79s. All original150 preserved unchanged. compileall and dependency checks passed on both interpreters. Ordinary pytest performs no real network downloads. Final diff check and scoped credential-pattern scan passed (new/changed files only; heuristic scan, not proof of credential absence).

Implemented: canonical closed/provisional adapters, Decimal34 feature engine, frozen R1–R9, one raw candidate per asset/end/rule set, opt-in atomic price-schema migration, SQLite cursor/dedup/order persistence, immutable hash-verified gzip histories, explicit official probes/acquisition, cached batch and incremental replay, offline tests. The opt-in price migration uses a separate checksummed ledger to preserve the existing v1 foundation migration contract. `CANONICAL_STORED` is a storage status, not live health. Correction of already closed bars marks `CORRECTION_REPLAY_REQUIRED`; automatic downstream correction replay is not implemented. Source-state columns for reconnect/health are placeholders, not completed collector behavior.

## Source audit

See [PRICE_SOURCE_AUDIT.md](docs/PRICE_SOURCE_AUDIT.md) for official English URLs, checked_at, endpoints, protocols and limits. Successful probe checked_at: 2026-09-30T05:59:09.321707+00:00. Actual Binance market-only Spot `/stream` supports subscriptions and returned market frames; no derivative path migration was assumed. Binance:24 frames/23 market frames,18.417 seconds. Hyperliquid:30 frames/12 candle frames,13.813 seconds. These short probes are not live shadow or continuity/SLO acceptance.

Actual REST: `https://data-api.binance.vision/api/v3/klines` and POST `https://api.hyperliquid.xyz/info`. Actual WS: `wss://data-stream.binance.vision/stream` and `wss://api.hyperliquid.xyz/ws`. Binance assets are Spot USDT pairs; HYPE is Hyperliquid perpetual. Cross-venue relative features are mechanically defined, not investment comparisons.

## Historical completeness

| Asset | Evaluation expected/actual | Extra warmup | Missing before repair | Duplicates | Repair calls | Unresolved | Candidates |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTC | 43200/43200 | 1446 | 0 | 0 | 0 | 0 | 0 |
| ETH | 43200/43200 | 1446 | 0 | 0 | 0 | 0 | 23 |
| SOL | 43200/43200 | 1446 | 0 | 0 | 0 | 0 | 187 |
| BNB | 43200/43200 | 1446 | 0 | 0 | 0 | 0 | 0 |
| HYPE | 5041/5041 | 0 | 0 | 0 | 0 | 0 | 0 |

Four assets each have exactly43200 evaluation minutes (30d) plus1446 causal warmup bars,44646 total. Evaluation interval is [2026-08-31T05:57:00+00:00, 2026-09-30T05:57:00+00:00). Open-time uniqueness and continuity were checked, not inferred from API success.

HYPE:5041 available closed official bars,84.016667 hours /3.500694 days. Oldest open: 2026-09-26T17:56:00+00:00; newest open: 2026-09-30T05:56:00+00:00; exclusive close: 2026-09-30T05:57:00+00:00. First1445 samples cannot produce fully warmed features; available evaluation has3596 eligible samples. No external history. Status remains **FORWARD_DATA_ACCUMULATING** as the approved history-limitation state; continuous forward collection has NOT started due to the stop gate, so this does not claim an accumulating live process or full30d validation.

Immutable raw/canonical gzip caches and SHA256/count manifests are private outside Git: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3-evidence-20260930/history`. Replay summary: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3-evidence-20260930/replay-summary.json`; SQLite: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3-evidence-20260930/replay-final.sqlite`. First replay summary/SQLite preserved separately before a Decimal serialization repair. The repair preserves all34 digits outside arithmetic context, with a regression test; final cached replay retains identical aggregate counts/recall. No thresholds changed.

## Rules, ground truth, distributions

See frozen PRICE_FEATURE_DEFINITIONS.md and PRICE_REPLAY_GROUND_TRUTH.md. GT1>=4%1h, GT2>=7%4h, GT3>=5% reversal, GT4>=1.5% causal breakout for3 samples, GT5>=4x median vol plus>=2.5%5m. Hit is same minute or an earlier candidate within15min, never future credit. Counts refer to minute samples, not independent market episodes. Full warmup admission excludes unavailable samples and reports them; it does not assert recall for excluded HYPE warmup.

| Asset | Candidates/day | Median/day | p95/day | Max/day | GT samples/hits/misses | Recall | Exact-minute recall | Longest consecutive run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | 0.000000 | 0.0 | 0 | 0 | 0/0/0 | N/A | N/A | 0 |
| ETH | 0.766667 | 0.0 | 5 | 18 | 48/28/20 | 58.33% | 27.08% | 17 |
| SOL | 6.233333 | 0.0 | 18 | 155 | 8/6/2 | 75.00% | 75.00% | 84 |
| BNB | 0.000000 | 0.0 | 0 | 0 | 0/0/0 | N/A | N/A | 0 |
| HYPE | 0.000000 | 0.0 | 0 | 0 | 0/0/0 | N/A | N/A | 0 |

Median/p95/max use wholly covered UTC calendar days including zero days; candidates/day uses full evaluated elapsed days. Empty labels give N/A, never100%. SOL recall75% is weak but has only8 labels, below the frozen10-sample decision minimum; this is not a rule PASS. No daily noise gate fired. Combined max over complete UTC days of the four full-history assets plus known available HYPE candidates: 155 (capacity gate960/day); HYPE before its available span is unavailable, not inferred zero. This is not a sustained live throughput benchmark.

| Asset | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | Clusters |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ETH | 16 | 5 | 0 | 0 | 6 | 0 | 11 | 0 | 0 | 4 |
| SOL | 6 | 0 | 0 | 173 | 0 | 0 | 9 | 0 | 0 | 22 |
| BNB | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| HYPE | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Full overlap matrix (ordered pairs; diagonals count per-rule samples):
- BTC: `{}`. Median first prior candidate lead_seconds: None. Labels/hits: `{"hits": {}, "labels": {}}`.
- ETH: `{"R1:R1": 16, "R1:R2": 3, "R1:R5": 6, "R1:R7": 6, "R2:R1": 3, "R2:R2": 5, "R2:R5": 2, "R2:R7": 1, "R5:R1": 6, "R5:R2": 2, "R5:R5": 6, "R5:R7": 2, "R7:R1": 6, "R7:R2": 1, "R7:R5": 2, "R7:R7": 11}`. Median first prior candidate lead_seconds: 900. Labels/hits: `{"hits": {"GT1": 23, "GT2": 1, "GT5": 5}, "labels": {"GT1": 43, "GT2": 1, "GT5": 5}}`.
- SOL: `{"R1:R1": 6, "R1:R7": 1, "R4:R4": 173, "R7:R1": 1, "R7:R7": 9}`. Median first prior candidate lead_seconds: 180. Labels/hits: `{"hits": {"GT1": 2, "GT5": 4}, "labels": {"GT1": 4, "GT5": 4}}`.
- BNB: `{}`. Median first prior candidate lead_seconds: None. Labels/hits: `{"hits": {}, "labels": {}}`.
- HYPE: `{}`. Median first prior candidate lead_seconds: None. Labels/hits: `{"hits": {}, "labels": {}}`.

## Missed moves and noise review set

Misses are frozen labels without any candidate in the trailing15min. Representative actual misses (UTC open time; window ends one minute later):
- ETH 2026-09-11T14:21:00+00:00 GT1; 1h return=0.04288494361232074779473927677019; 4h return=0.059721209174163222303266066942216.
- ETH 2026-09-11T14:22:00+00:00 GT1; 1h return=0.040823723885204437274700762781064; 4h return=0.058866912232501408153920341036644.
- ETH 2026-09-11T14:23:00+00:00 GT1; 1h return=0.042255710419647590085332461807645; 4h return=0.060008350256790663926485312060446.
- ETH 2026-09-11T14:24:00+00:00 GT1; 1h return=0.043123622113165123167634758827446; 4h return=0.060740824823347697945846897284237.
- ETH 2026-09-11T14:25:00+00:00 GT1; 1h return=0.045419178759960258717346112257153; 4h return=0.061922942859690506878075273785495.
- SOL 2026-09-21T08:42:00+00:00 GT1; 1h return=0.040384097639773849053217266445302; 4h return=0.039917473986365267312522425547183.
- SOL 2026-09-21T08:43:00+00:00 GT1; 1h return=0.041461006910167818361303060217177; 4h return=0.040993900251166128453534266236096.

Deterministic noise review samples are earliest hits per rule plus a sample from maximum-count day. These are review candidates, not confirmed false positives or measured precision:
- ETH 2026-09-04T12:31:00+00:00 R7; 24h return=0.018362102144107532310595557836276; reversal15m=0.02821645914043464009699037599567176.
- ETH 2026-09-04T12:44:00+00:00 R1; 24h return=0.015531848783013982392542723977214; reversal15m=0.031180216036330149043725025986807.
- ETH 2026-09-11T13:52:00+00:00 R1,R5,R7; 24h return=0.068303989742072298663510381220102; reversal15m=0.04039607606133255420230457352582139.
- ETH 2026-09-11T14:01:00+00:00 R1,R2,R5; 24h return=0.082916210598811968860301804183936; reversal15m=0.04529248594255143186143965684392968.
- ETH 2026-09-11T13:49:00+00:00 R1,R7; 24h return=0.062698595630484532178666095918603; reversal15m=0.03669960529855570590526362282121189.
- SOL 2026-09-04T12:30:00+00:00 R7; 24h return=0.0088994363690299614357757342035; reversal15m=0.02316898037338439444710387745332695.
- SOL 2026-09-11T13:59:00+00:00 R1; 24h return=0.051533988369761379586926007619812; reversal15m=0.03218187186300560968408621198700915.
- SOL 2026-09-18T19:13:00+00:00 R4; 24h return=0.120301497570167608846573440444312; reversal15m=0.007581839265007581839265007581839265.

SOL has187 candidates,173 R4 hits,155 on its maximum complete day and an84-minute sustained candidate run. This concentration needs review even though frozen median/p95 noise gates did not fire. ETH has23 candidates and20 missed labelled minutes. No cooldown or V2 tuning was introduced to improve these results.

## Equivalence and local persistence

All five assets: exact feature hash, rule hit counts, candidate set/identity hash match between batch replay and chronological incremental replay (BTC aligned first; provisional intermediate updates ignored). This is **offline live-style reconstruction**, not observed live WS/replay equality. Final SQLite integrity_check=ok;210 unique candidates, zero duplicate event IDs. All210 wrapped queue items fit existing2000-byte limit; size range1315–1386 bytes. These checks do not substitute for process SIGKILL recovery.

Offline faults covered: bounded REST429/timeout retries, duplicate and out-of-order canonical inserts, gap detection/manual real fixture fill, close-to-provisional regression protection, migration transaction failure/rollback, DB close/reopen cursor retention, corrupt cache/hash rejection, partial empty REST response, future-clock HYPE WS remains provisional. Not tested: real/reliable WS disconnect/server-close/resubscribe/rotation, clock-jump health behavior, SQLite temporary lock recovery, actual collector SIGKILL/restart. Gap detector reports missing timestamps; automatic source-state gap health updates and collector REST repair loop remain unimplemented.

## Live, health, transport and resources

Live shadow duration=0 seconds; live candidate count=N/A. Collector, health integration and source freshness/closed-commit latency benchmarks NOT IMPLEMENTED / NOT RUN after section45 stop. WS probe durations above are not counted toward2h. No environmental duration blocker is asserted. `PHASE_3_INCOMPLETE_LIVE_DURATION` applies to the unfulfilled duration gate within overall PHASE_3_FAIL. Reconnect/rotation, live gap repairs, kill/restart metrics=N/A, not0 successful tests. No overall HEALTHY claim.

Private GitHub Phase3 batch/readback NOT RUN after stop; raw SQLite queue and envelope size checks only. No real GPT decision. Production runtime-v2 writes=0; Gmail sends=0; third canary slot untouched; ChatGPT automation mutations=0; launchd/pmset/portfolio changes=0. No Frank/Monster/NFT work.

Historical replay process elapsed=45.688 seconds; peak RSS=334.11 MiB (macOS ru_maxrss bytes). This process evaluates all histories twice and is not a collector average-RSS/CPU benchmark. Historical REST response body RX=30068920 bytes; request body TX=111 bytes. Body counters exclude URL/headers/TLS/WS and are not wire traffic. Compressed cache bytes=15225893; final replay SQLite bytes=292544512. Collector CPU mean/p95, RSS, network, DB growth/hour and storage/day/30d=N/A; historical storage cannot establish a live storage rate.

## Decision and next review

**PRICE_RULE_V1 = NEEDS_CALIBRATION / FAIL. PHASE_3 = FAIL with incomplete collector gates. PHASE_4 = NO_GO.** Review ETH missed-label evidence, SOL sustained trigger noise, the frozen GT admission and thresholds before authorizing any V2. Do not infer investment opportunity or production readiness from historical completeness or passing unit tests. Implementation/report are committed and pushed only to the feature branch with force-with-lease following rebase; work stops after handoff.
