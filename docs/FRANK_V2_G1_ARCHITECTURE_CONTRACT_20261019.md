# Frank V2 — G1 architecture and development contract (candidate)

Date: 2026-10-19 Asia/Bangkok  
Status: **DRAFT_FOR_USER_SIGNOFF / NOT_FROZEN / NO_PRODUCTION_CHANGE**  
Source base: `main` `4e2bf056438830cf69a171d30474fdf489dd93f0`  
Scope: Frank/Meme lane only. This document is the **G1 decision input**, not a claim that G0 backtesting, business acceptance, independent review, or a Mac rollout has passed.

Authority and precedence: preserve `crypto-300-profit-mission/MISSION_SPEC.md`, repository-wide engineering/security rules, the frozen Frank V1 runtime mapping, and immutable historical evidence. The user's 2026-10-19 explicit rejection of any fixed execution notional supersedes obsolete historical design references to an automatic $30 follow size. Do not rewrite original archived reports to conceal their original assumptions.

## 1. Product position and one-page PRD

**Product**: a local-only, read-only Solana wallet observation and human-decision aid, initially covering the known Frank wallet. Show what the wallet actually did, what remains observable, what a frozen signal judged, and the source/freshness/unknowns; allow CA research and existing authorized local/Gmail notices. No built-in order submission or signing, no automatic execution, no preset investment amount, no implicit buy permission.

**Two independent outcomes**:
- **Product GO/NO_GO**: a functioning Mac activity ledger, durable watchlist, source-factual and freshness-correct opportunity feed, reliable existing notifications, and CA lookup. Product usefulness does not depend on proving a profitable follow-trading strategy.
- **Strategy GO/NO_GO/NEED_MORE_DATA**: independently reproducible follower returns conditional on observation/delivery delay, credible price coverage, fees/impact bounds, outlier sensitivity and non-leaking validation. Historical Frank-wallet profits are **not** follower returns. Positive ROI claims require an adequate independent validation set; otherwise output NEED_MORE_DATA.

**Primary user journeys**: (1) inspect latest authenticated wallet activity with exact evidence links and unknowns; (2) inspect observed / exited / unresolved mint states without conflating model inventory with current onchain balances; (3) inspect current opportunities independently of archived decisions, noting F01 installation state; (4) paste a CA to obtain bounded source-based read-only research; (5) read signals/notifications without any system-chosen trading amount.

**Acceptance**: functional demonstration on the actual authorized Mac, bounded end-to-end latency evidence and quantitative research coverage; not PR count, screenshots, test count, review count or inferred account profit.

## 2. Five-layer architecture and ownership of truth

```text
A SOURCE/COLLECTOR: existing Frank Solana RPC/cursor/30s configured poll/health
  | raw immutable transaction evidence (slot, signature, source, fetch time)
  v
B FACTS: versioned signed transaction interpretation; passive/ATA/failed/unknown;
         wallet/token movement and dated holdings snapshot; source-qualified prices
   | immutable raw + auditable correction provenance; scoped read-only views
   +------------------------------+
   v                              v
C1 OFFLINE RESEARCH           C2 FROZEN ONLINE SIGNALS
  bounded replay, delay,         existing V1 ACC / MULT / HFT /
  coverage, performance          inventory predicates; signals/outbox
  research candidates            frozen hash and source trace
   |                               |
   | reviewed evidence, approved shadow profile only
   +------------------------------> future profile gate (not automatic)
                                   |
                                   v
D LOCAL UI + EXISTING NOTIFICATIONS: wallet ledger / watchlist /
  F01 current opportunities / C02 CA lookup / local and authorized Gmail
                                   |
                                   v
E HUMAN DECISION: whether/when/how/how much/when to exit; no automatic trades
```

**Physical deployment clarification**: “one local product” does **not** mean replacing currently authorized writer, Mission Control loop and Dashboard LaunchAgents with a new single process. Reuse existing isolation, locks, DBs, ports and delivery components; do not introduce an additional permanent service or impact crypto-daily/TGE/other Mission modules. An architecture drawing cannot itself authorize installation.

**Boundary invariants**:
1. B exists independently of C2. A missing/failing signal cannot erase activity or watch states. Immutable **raw** payloads and provenance are never rewritten; derived classifications and views may be corrected by a new, traceable version/supersession, never silently altered or duplicated as facts. Existing production tables do not need immediate re-schema/rebuild.
2. C1 only reads authorized snapshots of B, with private/replay workspace and no production writer/outbox/config mutation. To introduce a novel profile: frozen research report -> independent review -> explicit user approval -> isolated shadow validation -> separately authorized production profile switch. Frozen V1 remains unchanged until that gate.
3. D presents B/C2 and verified server-side source outputs, with only non-semantic formatting/filtering/sorting. D must not silently generate new BUY/SELL decisions, repair missing facts, infer holdings from absence or fabricate financial metrics. Any calculated economic metric must carry source, timestamp, currency, method and unresolved dependencies and be implemented/tested in its proper data/service layer.
4. E is human-controlled. No fixed trade size (including $30), wallet signing, transaction building/sending or automatic trading. Missing amount means execution-dependent quote/impact is NOT_ASSESSED, **not** that a known source BUY disappears or the chain has no route. Existing signal and authorized notification semantics must be checked independently before changing policy.
5. Every layer differentiates true chain coverage from already-indexed local subset, event time from detection/availability/delivery time, and dated snapshot from present inventory. NO_GO on trading applies independently of product GO.

## 3. Minimal typed data contracts (logical, not an order to create tables)

| Object | Required logical fields / provenance | Rules |
|---|---|---|
| `wallet` | `wallet_id, person_id, chain, address, enabled, signal_profile_id` | Existing registry is wallet-aware but **only Frank person is currently enabled**. Future wallet/person activation needs separate ownership, cursor, profile and acceptance checks; not “one row and done”. |
| `raw_tx` | `wallet, signature, slot, block_time, observed_at, raw_hash, rpc_source, fetch_commitment, schema_version` | Unique by source wallet/signature; archive append-only. Preserve nullable block time and evidence gaps. |
| `event` | `event_id, wallet, signature, mint/asset, leg_id (where needed), classification, direction, token_raw_amount, quote_asset, quote_raw_amount, event_time, source_raw_hash, parser_version, evidence_status, supersedes_event_id (nullable), correction_reason (nullable)` | Classes: ACTIVE_BUY / ACTIVE_SELL / PASSIVE_IN / PASSIVE_OUT / FAILED / ATA / UNKNOWN. A single tx may contain multiple economic legs, so never use “one row per signature” as an unproved full ledger rule. UNKNOWN is neither zero nor BUY. Root-signed/active-swap proof is mandatory for active trades. A correction emits a new derived version linked to the superseded record; never overwrite the immutable raw transaction or silently replace a previously presented classification. |
| `position_snapshot` | `snapshot_id, wallet, mint, raw_amount or null, slot, captured_at, commitment, source, status, supersedes_snapshot_id (nullable), correction_reason (nullable)` | VERIFIED_NONZERO / VERIFIED_ZERO / UNKNOWN or equivalent explicit meaning. No missing RPC answer becomes ZERO; snapshots are dated, may be stale; model state != wallet balance. Later measurements are distinct dated snapshots; supersession applies only to an evidenced correction to an earlier derived snapshot, never to ordinary passage of time. |
| `price_sample` | `base_mint, quote_asset, price, price_time, observed_at, pool_or_pair, source, provenance, quote_kind, granularity, status` | Pool actual swaps / pool-price proxy / GeckoTerminal OHLCV / other provider / Frank's own fill / Coinbase SOL-USD rate are **different measurement kinds**. Coinbase SOL-USD is only a SOL conversion reference, not a direct meme USD series. No historical OHLCV is presumed an executable quote; missing=UNRESOLVED. |
| `signal` | `wallet, mint, type, profile_id/hash, triggered_at, triggering_signature, episode_id, reason_codes, source_event_ids` | Existing V1 contract retained, avoid duplicate signal authority. Preserve difference between chain event, hourly evaluation tick, signal creation and user notification. |
| `profile` | `id, hash, status, rules, validated_engine_version` | FROZEN / SHADOW / RETIRED life-cycle. Adding parameters supported by the engine can be config-only; new signal semantics require reviewed engine changes. |
| `research_run` | `frozen_spec_hash, exact_universe, sample_def, delay_ladder, clock_basis, price_priority, exit_assumption, thresholds, coverage_denominators, results, verdict, artifact_hashes` | Archive exact pre-run spec SHA. No fitting thresholds to the same evaluation outcomes and claiming that result is independent. |

`confidence` may be used as an **evidence-status category** (verified transaction, versioned reconstruction, proxy, inference, unresolved); do not invent numeric confidence probabilities. Schema is an incremental adapter contract; no immediate full migration of existing production tables is authorized.

## 4. Reuse and explicit scope decisions

| Layer | Retain / use | Integration disposition |
|---|---|---|
| A | `scripts/frank_local_signal_service.py`, `mission_agent/frank/{collector,parser,rpc,store}`, existing scanner/registry and cursor | Reuse, **do not replace** or change V1 thresholds; 30s collector poll != guaranteed subminute end-to-end signal. |
| B | `signals/classifier.py`, frozen 6,874-signature history, M3/OOS, immutable source and A04 proven cursor/archival techniques | Reuse **facts and validated mechanisms**; defer wholesale A04/Sidecar dependency graph. Distinguish J0 634 ACTIVE including SELL from M3 653 recovered ACTIVE, and count BUY separately. |
| B | A05/F02 dated inventory, existing D2 #110 evidence | Use snapshot truth/unknown/zero contract; do not claim dated 32-mint verification covers every watch mint or current balances. Keep minimum proof and freshness semantics, not arbitrary complexity. |
| C1 | OOS scripts, six-lot signed wallet net-flow verification, GeckoTerminal 3-mint + TWEETCRAFT 1m/5m proxy experiments and actual historical price receipts | Reuse baseline/method and negative examples; none proves market-follow execution returns or pristine unseen OOS. |
| C2 | Frozen V1 ACC/MULT/HFT and policy hash | No production change. Measure hourly tick vs event-trigger paths and actual notification delay. |
| D: activity | **PR #111 as one wallet-ledger UI implementation candidate** | #111 read-only report/display is basis; #109 causal 2-BUY audit remains preserved as distinct diagnostic evidence, **not a parallel competing activity implementation**. No premature PR merge. |
| D: watch/CA/opportunity | Existing dashboard/delivery, #110 watchlist, minimal #49 C02 identity proof, F01 current-opportunity route | Minimal selected change extraction only. F01 missing on actual dated Mac was HTTP 404, not “0 opportunities”. Preserve #49 review and avoid importing its entire stacked ancestry. |
| D: authority | PR #112 remove non-user-authorized notional | **BLOCKED** for release until source signal vs amount-dependent decision/notification regression and high-impact reason wording are corrected and independently re-reviewed at exact SHA. Do not restore default sizing. |
| deferred | Entire old A04/A05/F02 chains, second person/multi-wallet activation, alternate chain, additional monitors, unused QA screenshot/503 harnesses | Keep archived branches/evidence intact. Classify 72 open PRs before any manual cleanup; no mass closure/merge. |

## 5. G0–G4 gates and outcome validity

| Gate | Required deliverable / exit | Stop condition |
|---|---|---|
| G0-A exploratory data audit (parallel with G1 draft) | Exact ACTIVE_BUY universe and direction counts, group definitions (all signed buys; frozen ACC/MULT; other explicitly identified candidates), price-source coverage, known gap list; propose an explicitly bounded API/RPC pilot with request cap, provider, expected expense and stop conditions, and run it **only after separate user authorization for that specific collection** | Previously viewed observations/pilots are exploratory, not independent validation. No automatic expansion of RPC quota, paid API, retries, wallet scope or coverage after the approved cap; no strategy GO from exploratory results. |
| G0-B preregistered evaluation | Freeze `frozen_spec_hash` and numerical decision thresholds **before** evaluating independent outcomes. The strategy statistics unit is one **episode** (same mint, same continuous accumulation/holding cycle); individual BUY transactions are counts/denominators for event and price coverage, **not independent observations for significance or sample-size thresholds**. Cluster by episode and examine repeated mints across episodes as dependent in uncertainty/sensitivity checks. Delay ladder e.g. 30/120/300/900/3600s; exits including realistic delayed Frank exit/fixed horizons; price source choice, fees/impact bound, interval estimates, worst/missing coverage, outlier exclusion, OOS plan. | Thresholds cannot be chosen from the same results that they later certify. If no genuinely independent historical holdout exists, verdict is NEED_MORE_DATA/RESEARCH_ONLY pending forward shadow data. |
| G1 architecture | This architecture + one-page PRD + file/module ownership + explicit not-do list + user signoff at exact git SHA | Without explicit signoff, status remains DRAFT, not frozen authority. Architecture reopening only for verified architectural blockers. |
| G2 implementation | One tangible user capability or reproducible quantified research result per main-based PR; no stacked PR chain. Work within declared module ownership. | Stop after bounded acceptance; avoid unrelated P3 and screenshot spirals. |
| G3 review and Mac release | Risk-graded independent review for A/B/C2 changes, material C1 ROI/backtest code, policy changes and integrated release; tests + fixed SHA; explicit user approval and rollback; Mac actual end-to-end and notification compatibility acceptance | CI or synthetic screenshot != Mac acceptance. No deployment without user approval. |
| G4 forward shadow | Predeclared signal->detection->notification timing and simulated delayed entry/exit with price evidence, coverage and independent evaluation | No live trades, no use of forward observations to retrospectively rewrite G0 thresholds. |

G0-A data inventory and G1 drafting may proceed simultaneously. Read-only product utility can enter G2 when compatible with frozen C2 even if strategy remains research-only. Initial shadow measurement requires separate permission to instrument existing production and cannot silently add a new monitoring job.

**Research verdict discipline**: Strategy GO requires precommitted economic and reliability criteria met on independent observations; NO_GO when sufficiently covered evidence violates those criteria; NEED_MORE_DATA when source coverage, execution evidence, sample independence or statistical power are insufficient. Product GO/NO_GO is independent. Historical 6 selected lots and 3/18 priced mints do not authorize strategy GO.

## 6. Owners and conflict control

| Responsibility / directory zone | Primary writer | Independent review |
|---|---|---|
| C1 `local-agent/scripts` **specifically named historical-research scripts**; G0 research evidence/report | Claude | GPT or third party |
| A/C2 read-only timing/source-to-signal audit (no production edit unless approved) | GPT | Claude or third party |
| A/B production or adapter code changes (`collector`, `parser`, `classifier`, `signals/scanner`, facts/position adapters and persistence contracts) **when separately authorized in G2** | **GPT, sole writer for explicitly assigned paths** | Claude or third party |
| D integration (F01/C02/dashboard) and PR #112 fix/release audit | GPT-coordinated; original PR author fixes #112 | Claude or third party |
| #111 wallet ledger implementation | Current #111 author; single agreed owner | Other AI |
| G1 architectural contract, final gate and deployment permission | **User** | Reviewer evidence supporting user decision |

File ownership is **path-specific**, not a blanket exclusive lock on every `scripts/` file. Owner changes must be updated in this contract or a controlled `OWNERSHIP.md` addendum before simultaneous edits. Do not create a second D1 wallet activity implementation because #109 and #111 have different verified deliverables.

## 7. Explicit NOT NOW list

No additional person/wallet activation, multi-chain, new permanent monitor/LaunchAgent, wholesale sidecar rewrite, new automatic trade system, user-sized default or $30 resurrected, mandatory paid GMGN API, blind all-pool historical RPC download, unrelated PR/workflow/Safari mass deletion, forced single-process refactor, mail/notification behavior change without separate authorization, or production SQLite writes.

Historical workflow and QA evidence remain traceable until an approved dependency classification. Existing security, wallet identity, no-trade, local data privacy and rollback rules prevail over convenience.

## 8. Signoff, change discipline, and weekly output

**User signoff requested on this exact revision**:
1. #111 is the intended D1 activity UI foundation; #109 kept as causal forensic/audit evidence, not merged as a duplicate UI.
2. G0-A exploratory coverage/availability first; **numeric GO gates frozen for a separate independent G0-B validation before its evaluation**, not after seeing its results. No pristine holdout => no confirmed GO.
3. Multi-wallet deferred; support stays architectural only.
4. The corrected raw/derived evidence boundary, no UI signal invention, and single-host/multi-component deployment model are accepted.

**Exact signoff protocol:** the user (not an assistant acting on their behalf) posts a top-level comment on **PR #114** with the precise form `G1_APPROVED <40-character-current-PR-head-commit-SHA>`. The SHA must match the latest complete draft reviewed by the user; stale-SHA approval is not valid for a changed draft. **Only after verifying that comment and matching SHA** may the document header status be changed to `FROZEN / G1_APPROVED` in this same PR, recording the user-approved **pre-status-change SHA**, approval comment link/time and the new status-only commit SHA separately. The approval attests the unchanged architectural content of the pre-status-change SHA; the status-only metadata commit is not a license to modify substantive text. Any concurrent or subsequent substantive edit requires a newly reviewed SHA and renewed approval. Merely merging, CI passing or an AI recommendation does not grant user signoff. After freeze, hard-boundary revisions require a new PR identifying and evidencing an **architecture-level blocker** and explicit user reapproval.

Weekly product/research progress reports lead with only (i) backtest results **plus coverage and evidence grade**, (ii) measured chain event -> detection -> notification latency distribution and samples, and (iii) Mac functions actually accepted. All other CI/tests/PR count are supporting evidence only.
