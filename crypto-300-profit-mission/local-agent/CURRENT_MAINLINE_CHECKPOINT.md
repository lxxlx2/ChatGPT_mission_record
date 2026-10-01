# CURRENT MAINLINE CHECKPOINT — 2026-10-01

Status: **MAINLINE = FRANK + MONSTER**

This checkpoint records the actual state before the next Codex prompt is sent. It exists to prevent the project from drifting back into CORE PRICE V3 or other secondary work.

## Priority lock

1. **FRANK wallet monitor** — highest priority.
2. **MONSTER / 妖币 monitor** — highest priority.
3. Reuse existing SQLite / private GitHub / GPT consumer / delivery infrastructure only as needed for Frank and Monster.
4. CORE PRICE V3 remains paused.
5. NFT remains not started.
6. `$300 Crypto资产状态监控` remains disabled.
7. Production remains NO_GO.

Do not let CORE PRICE V3, generic BTC/ETH/SOL/BNB/HYPE price calibration, hidden-holdout work, or unrelated monitoring block Frank or Monster.

## Latest verified branch state

Working branch: `codex/crypto-monitor-design-20260930`

Latest verified remote HEAD before this checkpoint: `d9312c2a2a7db2efa76f9948d7af685058b925b2`

Latest completed phase: **PHASE_FM2 = PARTIAL**.

The latest FM2 report is:

`crypto-300-profit-mission/local-agent/PHASE_FM2_FRANK_MONSTER_REPORT.md`

Frozen historical provenance must be preserved. Because historical commit SHAs are part of acceptance/audit contracts, future synchronization with `main` should use merge, not rebase, unless explicitly authorized otherwise.

## FRANK — actual progress

Wallet:

`498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

Canonical Solana source remains only:

`https://api.mainnet.solana.com`

### Completed

- Official signature snapshot discovered **18,203 unique signatures**.
- Archival six-position probe: all 6 sampled transactions available.
- Canonical oldest sampled snapshot time resolved to **2025-09-04T00:06:20Z**. The earlier `02:46:20` handoff time was a transcription error; raw chain evidence was not changed.
- Final fixed 500-sample parsing completed with parser `frank-v7`, immutable output `processing-v8`.
- Final 500 classification:
  - ACTIVE = 45
  - PASSIVE = 374
  - UNKNOWN = 76
  - FAILED = 4
  - TRANSFER_OUT = 1
- Final 500 raw Frank candidates = **57**.
- Primary fixed manual review set: **50/50 reviewed** without resampling.
- Classification agreement: **48/50 = 96%**.
- Token delta agreement: **50/50 = 100%**.
- Signer / fee-payer agreement: **50/50 = 100%**.
- Authority agreement: **50/50 = 100%**.
- Original ACTIVE13 supplemental audit: **0 false positives**.
- Historical progress with current parser: **4,724 / 18,203** signatures durably normalized.
- Within available history observed:
  - 89 active mints
  - 67 observed round trips
  - 12 re-entries
  These are limited to available referenced accounts; they are not lifetime-PnL or lifetime-entry claims.
- Real forward collector ran continuously for **125.04 minutes** at 30-second polling.
- 4 distinct real new signatures were observed across the forward workflow:
  - PASSIVE = 1
  - UNKNOWN = 3
  - ACTIVE = 0
- Real restart / recovery tests included SIGTERM, SIGKILL, and ~320 seconds downtime.
- Verified recovery gap = 0 and candidate duplicate = 0 for observed recovery path.
- Real forward ACTIVE transaction has **not yet occurred**, therefore active-candidate forward E2E is still **NOT_OBSERVED**.
- Historical Frank private test transport passed for 57 v8 candidates with restart/hash/dedupe checks. Production runtime path was not used.

### Frank current status

`MANUAL_GATE = PASS`

`FORWARD_CAPTURE = PASS`

`ACTIVE_FORWARD_E2E = NOT_OBSERVED`

Frank is no longer blocked on parser/manual validation. The remaining important proof is a **real forward ACTIVE transaction** passing through:

Official RPC → raw cache → parser → mechanical ACTIVE → `RAW_FRANK_CANDIDATE` → SQLite queue → private test transport → exact readback/dedupe.

The next intended design is to keep a local **shadow-only Frank collector** running until a real ACTIVE event occurs, rather than repeatedly launching bounded two-hour manual sessions. No investment alert should be emitted during shadow validation.

## MONSTER / 妖币 — actual progress

The objective is abnormal Binance/Alpha/Futures “妖币” discovery, including old-shell reactivation and extreme 5X/10X/20X events. It is not a generic meme scanner and does not depend on CORE PRICE V3.

### Universe / coverage completed

FM1/FM2 established current and historical Binance universe inventory. FM2 V1 replay used a USDT union with:

- instruments in union: **1,724**
- instruments with usable historical data: **1,518**
  - Spot = 611
  - Futures = 907
- without bars = 206
- historical non-current instruments with bars = **279**
- completely absent from current inventory = **34**

The historical analysis period was nominally 2025-01-01 through 2026-09-30, with complete UTC archives through 2026-09-29.

### MONSTER GT V1

Ground-truth V1 was frozen before discovery at:

`3a4167ee9f9953de31c96f817dce318523d98a71`

It must remain preserved as a failed baseline.

Discovered V1 events:

- total frozen events = **1,542**
- exact 2X = **1,485**
- exact 3X = **41**
- exact 5X = **12**
- exact 10X = **2**
- exact 20X+ = **2**
- cumulative >=5X = **16**
- cumulative >=10X = **4**
- cumulative >=20X = **2**

### D1 V1 result

D1 V1 used 48 frozen configurations and produced **no accepted winner**.

Diagnostic V1-47 only (not a deployable winner):

TRAIN:
- >=5X recall = 8/12 = 66.67%
- >=10X recall = 1/3 = 33.33%

VALIDATION:
- >=5X recall = 3/4 = 75%
- >=10X recall = 1/1 = 100%, but N=1 and therefore insufficient
- >=10X before-2X rate = 0/1 = 0%
- >=5X before-2X rate = 2/4 = 50%

Noise was unacceptable:

- median candidate symbols/day:
  - TRAIN = 60
  - VALIDATION = 78
  - AUDIT = 91
- p95 candidate symbols/day:
  - TRAIN = 82
  - VALIDATION = 96
  - AUDIT = 115
- non-2X candidate rate:
  - 24h = 99.22%
  - 72h = 97.89%
  - 168h = 95.98%

Largest known misses include:

- MMT Futures ~14.951X
- MMT Spot ~10.324X
- AVNT ~8.261X
- BTW ~7.744X in validation

D2 and D3 were **not started** because D1 V1 failed its acceptance gates.

### Important interpretation

MONSTER D1 V1 should stay frozen as a failed baseline. It should not be “fixed” by editing its old thresholds/results.

The next intended Monster architecture is:

- **D1 V2 = high-recall screen**
- **D2 = noise reduction / structure enrichment**
- **GPT = final investment judgment**

The V1 architecture over-constrained the first-stage screen with one AND expression while still producing excessive noise. The next design should use multiple independent causal pathways rather than forcing every candidate through the same conjunction.

Planned D1 V2 pathway families:

- MOMENTUM_BREAKOUT
- VOLUME_IGNITION
- OLD_SHELL_REACTIVATION
- NEW_LISTING_IGNITION
- RELATIVE_STRENGTH_ACCELERATION

Any one pathway may activate a D1 screen candidate. D2 is responsible for reducing the candidate set.

### Monster V2 historical expansion plan

Before downloading new older history, freeze a V2 spec and search space.

Proposed project-unexposed interval:

- TRAIN: 2021-01-01 → 2023-12-31
- VALIDATION: 2024-01-01 → 2024-12-31
- 2025-01-01 → 2026-09-30 remains exposed training/diagnostic data only

The goal is to increase the number of 10X/20X cases enough to make evaluation meaningful. This should be described as **project-unexposed-before-V2**, not globally unseen.

### Monster entity model

Future monitoring should distinguish:

- instrument events (e.g. Spot vs Futures)
- entity events (same underlying token when identity is unambiguous)

This is important because cases such as MMT Spot and MMT Futures should not necessarily create duplicate user alerts for the same underlying market episode.

### Resource issue to fix before expansion

FM2 historical replay observed approximately:

- peak CPU = 291%
- single-process RSS = ~4.31 GiB
- private evidence disk = ~2.13 GiB

Before expanding 2021–2024 history, replay must be changed to streaming/chunked processing. Target peak RSS is <1 GiB, preferably <500 MiB. Historical replay must not degrade Frank real-time polling.

## Latest next-step plan — NOT YET SENT TO CODEX

The latest proposed **PHASE_FM3_FRANK_SHADOW_MONSTER_V2** prompt has **not yet been sent to Codex** as of this checkpoint.

Its intended scope is:

### Frank

- authorize exactly one local shadow LaunchAgent, suggested identifier:
  `com.jerson.crypto-monitor-frank-shadow`
- keep official Solana RPC polling running locally
- no Gmail, ChatGPT calls, app alerts, trades, wallet actions, or production runtime writes
- real-time polling has priority over all historical work
- continue low-priority Frank history backfill toward 18,203 signatures
- wait for a **real ACTIVE** forward event and verify complete private-test E2E when it appears

### Monster

- preserve V1 forever as a failed baseline
- freeze MONSTER GT/D1 V2 before opening new old history
- expand historical data to 2021–2024 if official Binance archives are available
- build conservative instrument→entity mapping
- redesign D1 as multiple OR-style high-recall pathways
- move strict noise reduction into D2 instead of requiring D1 to do both jobs
- keep finite deterministic search space (target <=500 configurations)
- one-shot validation on 2024 after TRAIN-only selection
- allow D2 if V2 D1 has strong >=5X recall and candidate volume remains below a broad safety ceiling, even if >=10X N is still below 10
- D2 should audit real Binance official derivatives endpoints and distinguish historical-capable vs forward-only data
- D3, if reached, remains bounded manual shadow; no production notification

## Current hard boundaries

- CORE PRICE V3 = **PAUSED**
- NFT = **NOT STARTED**
- `$300 Crypto资产状态监控` = **DISABLED**
- Gmail investment sends = **0 / unauthorized**
- ChatGPT automation mutations = **unauthorized**
- Production `runtime-v2/` writes = **NO_GO**
- No trading / wallet mutation / portfolio mutation
- Frank and Monster remain the only development priorities

## Resume instruction

When work resumes, start from this checkpoint and `PHASE_FM2_FRANK_MONSTER_REPORT.md`.

Do **not** resume CORE PRICE V3.

Do **not** treat the latest FM3 prompt as already executed; it has not yet been sent to Codex.

Next implementation phase should be explicitly authorized from this checkpoint.