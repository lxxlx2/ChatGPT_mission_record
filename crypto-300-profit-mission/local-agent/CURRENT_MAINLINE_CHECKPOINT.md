# CURRENT MAINLINE CHECKPOINT — FM4 local acceptance 2026-10-03

**PHASE_FM4 = PASS for authorized shadow engineering; PRODUCTION_TRADING = NO_GO.**

Latest report: [PHASE_FM4_MEME_SIGNAL_PIPELINE_REPORT.md](PHASE_FM4_MEME_SIGNAL_PIPELINE_REPORT.md).

- Actual Mac LaunchAgent migration completed: `com.jerson.crypto-monitor-meme-shadow`, exactly one scanner, same durable SQLite/cursor, controlled restart PASS.
- Frank is the sole verified live person; multiple wallets count as one person. New people require user confirmation; new PERSON_PATTERN defaults OBSERVE_ONLY.
- Candidate V2 / consensus / person-pattern fact bundles / immutable private handoff / stateless renderer / transactional outbox tests PASS. Live V2 currently NO_CURRENT_SIGNALS; old Frank ACTIVE/candidates were not replayed.
- FM3 real ACTIVE E2E remains PRESERVED_PASS. New natural post-migration V2 ACTIVE and real external GPT/Gmail path remain unobserved.
- Historical executable-price coverage insufficient; TEMPORARY_SHADOW_TTL=900s, no strategy edge or production followability claim.
- ChatGPT task mutations=0; real Gmail sends=0; wallet/trades=0. `$300-3000` remains external decision/delivery owner.
- Monster DEFERRED_NOT_CANCELLED / NEEDS_REDESIGN; NFT and Core Price DEFERRED_NOT_CANCELLED. No logic/dataset/runtime changes to them.
- Stop for FM4 review. No automatic FM5, new persons, low-latency API integration, deferred-module work or trading.

The following retained FM3 snapshot is historical context; its process names, counters, portfolio and task authorization text are not a current FM4 runtime claim. The latest local request prohibits task mutations in this phase.

---

# CURRENT MAINLINE CHECKPOINT — 2026-10-03

Status: **FRANK ACTIVE E2E PASS → MEME GENERALIZATION NEXT; MONSTER REDESIGN BLOCKED PENDING LATER WORK**

This checkpoint supersedes the 2026-10-01 FM2 checkpoint.

## Latest verified development state

Working branch:
- `codex/crypto-monitor-design-20260930`

Latest completed report:
- `crypto-300-profit-mission/local-agent/PHASE_FM3_FRANK_MONSTER_REPORT.md`

FM3 report status:
- `PHASE_FM3 = PARTIAL`
- `FRANK_SHADOW_READY = PASS`
- `FRANK_ACTIVE_E2E = PASS`
- `MONSTER_D1_V2 = NEEDS_REDESIGN`
- `PRODUCTION = NO_GO`

User has explicitly chosen to finish the Frank/Meme path before resuming Monster redesign.

## FRANK — actual current result

Frank wallet:
- `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

FM3 established a real forward ACTIVE E2E, not a synthetic proof:

- real new forward signatures observed: 5
- real ACTIVE: 1
- real candidates: 2, from the same real ACTIVE transaction and two mints
- full path PASS:
  official/finalized chain evidence → normalization → candidate → SQLite → private transport → exact remote readback
- total measured first ACTIVE E2E: 47.297 s
  - detection 27.010 s
  - normalization 0.175 s
  - candidate 0.203–0.206 s
  - transport 19.907–19.910 s
- RPC errors / 429 / timeout / retry: 0
- current/unresolved gap: 0
- candidate duplicates: 0
- real-ACTIVE post-event restart/dedupe acceptance: PASS
- SQLite integrity: ok
- private transport exact readback/hash/identical-republish/restart dedupe: PASS
- historical parser progress at FM3 report snapshot: 6,105 / 18,203
- LaunchAgent remains one local shadow process: `com.jerson.crypto-monitor-frank-shadow`

Therefore the unresolved problem is no longer basic Frank chain collection. The next value-critical layer is:

`candidate → investment judgment → clean deduped Gmail alert → forward outcome audit`

## Naming / multi-person direction authorized by user

The system-level name should become **Meme**, because Frank is now only one tracked person/source.

Target entity model:

- system: `Meme`
- `person_id=frank`
- one person may own multiple verified wallets
- consensus counts unique people, not wallet addresses
- additional people will be selected by the user for Frank-like style and real followability

Do not add speculative people automatically. New people require explicit user-provided/approved identities and addresses.

## Two signal families

### 1. TOKEN_CONSENSUS

Multiple independent tracked people buy the same token in a useful causal time window.

Local deterministic layer must establish:
- unique `person_id` count;
- exact wallet/person mapping;
- buys, amounts, signatures, timestamps and mint identity;
- aggregation window;
- dedupe / event identity.

GPT performs final value judgment, including whether the consensus remains followable after elapsed time/price movement/liquidity/current context.

### 2. PERSON_PATTERN

One tracked person buys a token in a historically useful and followable pattern for that person.

Do not blindly apply Frank thresholds to other people. Each person's person-specific alert logic must be historically/replay evaluated before `SIGNAL_ENABLED`. New people default to `OBSERVE_ONLY` for PERSON_PATTERN, though verified people may participate in TOKEN_CONSENSUS.

## GPT remains the final investment-judgment layer

The architecture has NOT changed to deterministic investment decisions only.

Deterministic local/Codex layer owns facts and engineering correctness:
- transaction truth
- person/wallet mapping
- behavior features
- aggregation
- TTL fields
- IDs
- SQLite/outbox
- dedupe
- immutable run bundle
- stale-content isolation
- private transport

GPT task owns final investment-value judgment:
- SEND / NO_SEND
- whether the signal is still followable
- current project / liquidity / market / social / on-chain enrichment where reliable
- structured reasons / risks / evidence
- clean email composition

GPT must not own dedupe or reconstruct chain facts from prose.

Canonical task contract is now on main:
- `crypto-300-profit-mission/meme/MEME_GPT_MONITOR_SPEC.md`

## Email correctness is a first-class acceptance gate

User explicitly requires email testing, especially against stale-content contamination and duplicate delivery.

Renderer rule:
- every run starts from empty state;
- current email may read only current immutable run bundle + current run GPT decisions;
- never mutate/reuse prior email body;
- a section with zero SEND signals must be absent;
- if both signal families have zero SEND signals, send no email;
- same token qualifying both families gets one full block, not duplicate blocks.

Mandatory tests include:
- previous run consensus+person; current run person-only → zero previous consensus content;
- current run no signal → no email;
- same run twice → max one delivered email;
- Gmail accepted but local SENT state lost → readback prevents duplicate;
- same person with two wallets → still one person;
- consensus + person-pattern same token → one full token block;
- enrichment failure / renderer crash / stale caches → no previous-run leakage;
- expired candidate after outage → no late investment email;
- concurrent workers → one delivery path.

## Followability / strategy validity

The goal is user-followable PnL, not tracked-wallet PnL.

Backtest/replay must account for realistic system delay. Measure outcomes from realistic user-available time/price, not the tracked person's original fill.

Per signal/person where possible measure:
- T+5m / 15m / 1h / 6h / 24h
- MFE / MAE
- drawdown
- liquidity/executable-size constraints
- delayed-entry return
- precision / base rate / false-positive load
- TRAIN / VALIDATION / HOLDOUT / real FORWARD splits

For TOKEN_CONSENSUS, compare against the 1-person baseline. Do not assume 2+ people is better until data proves incremental edge.

## Newly authorized ChatGPT `$300` task

User explicitly authorizes exactly **one new `$300` task** for the Meme/GPT judgment path.

Old disabled `$300 Crypto资产状态监控` remains disabled and must not be re-enabled or repurposed.

No other new ChatGPT task is authorized.

Important product limitation:
- ChatGPT task cadence cannot exceed hourly.
- This may be too slow for 1–2 minute meme followability.
- The hourly task must honor TTL and silently discard expired candidates rather than send stale opportunities.
- Do not claim the hourly task is production-grade real-time follow trading.
- Any future lower-latency GPT/API trigger requires separate explicit authorization.

## Current portfolio refresh

Main canonical portfolio was freshly updated on 2026-10-03:
- `crypto-300-profit-mission/portfolio/current.md`

Key current chain state:
- Solana USDC: 142.162136
- Solana native SOL: 0.003093645 (<$1 display threshold)
- Ethereum USDC: 1.006555
- Ethereum ETH: 0.000634360344095958
- Base ETH: 0.000967183780184779
- Ink ETH: 0.010389022090321585
- Arbitrum / Optimism native balances below $1
- Credits contract ownership: 0 NFTs / fully cleared
- SUI remains 0 by latest explicit user-confirmed state; not relabeled as a fresh independent Sui scan
- prior Relay reconciliation is closed at balance level because Solana USDC increased by 33.535588, strongly consistent with the prior Relay-sized transfer; no double count

Off-chain latest known:
- Binance: $523.72 user-confirmed
- Legion/JUMP: $1,000 pending allocation

## MONSTER

FM3 V2 historical expansion and 243-config TRAIN completed, but every config exceeded candidate ceiling.

- eligible winner: NONE
- minimum median entities/day: 148 > gate 100
- minimum p95/day: 215 > gate 150
- 2024 validation: NOT_RUN
- D2 shortlist: SKIPPED
- D3: NOT_STARTED
- status: `MONSTER_D1_V2_NEEDS_REDESIGN`

Do not continue tuning the same grid or open 2024 holdout while Meme/Frank work is prioritized.

## Hard boundaries

- CORE PRICE V3 = PAUSED
- NFT = NOT STARTED
- old `$300 Crypto资产状态监控` = DISABLED
- exactly one new `$300` Meme/GPT task = AUTHORIZED
- Monster LaunchAgent = 0
- wallet mutation / trading = unauthorized
- production trading = NO_GO
- no rebase / force-push of frozen historical provenance

## Next implementation gate

Next Codex phase should be **FM4: Frank → Meme generalization + deterministic signal handoff + mail correctness infrastructure**, while keeping GPT as final investment-judgment layer.

Do not start Monster redesign in the same phase.
