# Mission Meme current status — 2026-10-07

Timezone: Asia/Bangkok

Status: `MAIN_MERGED / LOCAL_RUNTIME_PENDING_REFRESH / LIVE_NOTIFICATION_EXISTING_STACK / PRODUCTION_TRADING_NO_GO`

This file is the current operational handoff for the Frank/Meme lane. It supersedes older review-only wording for current runtime state, while older reports remain historical evidence.

## 1. Current production shape

Frank production remains the deterministic source of chain facts and frozen V1 pattern state.

```text
Frank production
  health.json
  forward.sqlite [READ ONLY to Mission Control]
        |
        v
Mission Control
  FrankReader
  Jupiter official /swap/v1/quote
  FOLLOW_POLICY_V1
        |
        +--> mission-control.sqlite
        +--> localhost Dashboard
        +--> macOS local notification
        +--> Gmail
```

No wallet signing, swap construction, transaction sending, or automatic trading is authorized.

`PRODUCTION_TRADING = NO_GO`.

## 2. Current live functions

Implemented and in main:

1. Frank runtime health/read-only production DB checks.
2. Frank `ACCUMULATION` and `MULTIPLE` episode/position reading.
3. `REENTRY_WATCH`: a confirmed CLOSED -> REENTRY episode enters observation immediately, but remains WAIT-only until the frozen signal model independently reaches ACCUMULATION/MULTIPLE.
4. Jupiter executable quote check using the official quote endpoint, keyless or keyed.
5. Deterministic follow decisions: `BUY / SMALL_BUY / WAIT / NO_BUY`.
6. Chinese localhost Dashboard.
7. Full CA display + copy, Solscan links, readable Frank actions and decision reasons.
8. Closed positions leave the primary candidate area and appear only in recent-ended UI history.
9. Separate `mission-control.sqlite` audit DB.
10. 60-day `follow_observations` retention.
11. Durable decision snapshots/events/outbox and Gmail delivery receipts.
12. Live macOS + Gmail notifications for notification-eligible fresh Decision transitions.
13. Historical backlog suppression; enabling live delivery does not replay stale alerts.
14. Gmail Sent readback / ambiguity handling / dedupe.
15. macOS LaunchAgents for Mission Control loop and Dashboard.
16. Approved policy SHA256 pinning.
17. LaunchAgent runtime policy is copied to `~/Library/Application Support/FrankMeme/follow_policy_v1.approved.json` to avoid macOS Documents/TCC denial.
18. Existing Frank production LaunchAgent remains separate and is not modified by Mission Control.

### 2A. Meme local tooling v2 — merged to main, local runtime refresh pending

Merge commit:
`2f83be332e2c20270a3f534e333f1a19ea8b6bc5`

The following functionality is now in `main`:

- independent forward outcome tracking with executable Jupiter entry/exit quotes;
- fixed T+5m / T+15m / T+1h / T+6h / T+24h horizons;
- 5-minute sampled MFE / MAE / max drawdown plus monthly grouped statistics and Ex-Top robustness;
- live SOL-quoted Frank normalization in a separate sidecar DB, while keeping production Frank read-only and the frozen Frank evaluator unchanged;
- a free local Solana wallet-cluster engine and a tabbed `CA 链上查询` view inside the same Dashboard;
- Chinese trading-oriented Mission Control notification content.

Pre-merge review is complete (`738 passed` on feature code head `b6f26499`). The code is now merged to `main`, but the user's Mac is still running the previously installed local checkout/LaunchAgents until it is explicitly synchronized and restarted. Do not claim the new CA-query/outcome/SOL-sidecar code is live before that local acceptance.

## 3. Current approved follow policy

Runtime policy:
`config/follow_policy_v1.approved.json`

Required live gate:
- `status = FROZEN_APPROVED`
- `live_delivery_approved = true`
- runtime CLI `--live-delivery`
- exact approved policy SHA256 match

Approved policy SHA256 observed in the 2026-10-07 local acceptance run:

`355336f2959e674939210b51be97d2df1d6e66f4ee3cca8acfe041dabb9e3ae8`

Key current thresholds:
- quote size: 30 USDC
- latest Frank buy max age: 600s
- BUY: MULTIPLE + deviation <=8% + impact <=1.5%
- SMALL_BUY: ACCUMULATION/MULTIPLE + deviation <=20% + impact <=3%
- observation retention: 5,184,000s = 60 days

These values must not be silently changed from accumulated live results.

## 4. Local acceptance evidence

User-run acceptance on 2026-10-07 confirmed:

- original live-notification acceptance baseline: `706 passed`
- independent review of feature head `fa01f7e`: `727 passed` (21 additional tests)
- independent re-review of remediation head `6c069ea`: `736 passed`; all nine previously reported issues were rechecked and no new blocker was found
- final independent review of feature head `b6f26499`: `738 passed`; report-age display, shared-infra localization and atomic report persistence verified; no new blocker found
- approved policy gate: PASS
- Gmail OAuth readiness: PASS
- recipient resolved successfully
- no test email was sent during preflight
- Mission Control health: `status = OK`
- `delivery_allowed = true`
- Dashboard HTTP: `200`
- LaunchAgent loop: `state = running`
- LaunchAgent dashboard: `state = running`
- runtime policy moved out of Documents to Application Support after the original macOS TCC failure
- production trading remained `NO_GO`

Observed PIDs are runtime evidence only and are not stable identifiers.

Important remaining runtime acceptance:
- the first post-enable real notification event has not yet been used to prove a real Gmail send + Sent readback in this new Mission Control path;
- reboot/login autostart is installed and running, but a physical Mac reboot/login recovery test is still pending.

## 5. Normal daily operation

No manual command is required while the Mac stays logged in and launchd is healthy.

Status check:

```bash
cd "/Users/jerson/Documents/ChatGPT/frank-meme-main/crypto-300-profit-mission/local-agent"
bash scripts/status_mission_meme_launchd.sh
```

Expected core state:
- loop `state = running`
- dashboard `state = running`
- Mission Control `status = OK`
- `delivery_allowed = true`
- Dashboard HTTP = 200

Dashboard:
`http://127.0.0.1:8766`

## 6. One-month acceptance plan

Target review window: approximately 30 days after live-notification enablement.

### A. Runtime reliability

PASS only if:
1. Frank production stayed healthy or outages are explicitly accounted for.
2. Mission Control loop recovered after normal process exits and, once tested, after Mac reboot/login.
3. Dashboard remained recoverable locally.
4. No recurring TCC/policy-path failure.
5. No unbounded Gmail ambiguity state.
6. No policy hash drift was silently accepted.

### B. Notification correctness

For every notification-eligible fresh Decision transition:
1. exactly one durable Decision event exists;
2. local notification has one delivery path;
3. Gmail has one durable delivery identity;
4. no duplicate Gmail exists for the same decision_id;
5. historical/stale episodes were not backfilled as fresh alerts;
6. BUY/SMALL_BUY invalidation transitions were not silently lost.

Record separately:
- eligible events;
- local delivered / failed;
- Gmail verified / pending / manual-review / failed;
- duplicate count;
- missed-notification count.

### C. Strategy usefulness

Separate engineering reliability from trading usefulness.

At minimum review:
- number of REENTRY_WATCH, ACCUMULATION and MULTIPLE episodes;
- number of BUY / SMALL_BUY / WAIT / NO_BUY decisions;
- fraction of Frank patterns that remained executable at 30 USDC;
- distribution of entry-price deviation and price impact;
- false-positive examples;
- missed followable opportunities;
- outcome concentration by token so one exceptional winner cannot dominate the conclusion.

Canonical followability horizons remain:
- T+5m
- T+15m
- T+1h
- T+6h
- T+24h

Do not call the strategy validated from raw Frank wallet PnL or one large winner.

### D. Main/live evaluation gap vs review-branch candidate

Current main/live Mission Control still has the historical gap described below: it stores 60-day observations plus immutable Decision transitions, but does not yet guarantee independent fixed-horizon capture after Frank exits.

`main` now contains the forward-only outcome tracker that records executable Jupiter entry inventory and T+5m/T+15m/T+1h/T+6h/T+24h exit observations, with `MISSED_WINDOW` instead of hindsight backfill.

Until the user's local checkout is synchronized to merge commit `2f83be33` (or a later main) and the Mission Meme LaunchAgents are restarted, the currently running local system must still be treated as having the old gap. Do not reconstruct missing horizon prices by guess.

## 7. Open validation items inside current Frank system

These are not blockers for normal notification use, but remain unclosed evidence gaps:

1. Real production SOL/WSOL-quoted Frank normalization remains unexercised. The review branch now has a live read-only sidecar candidate, but it still needs a real Frank SOL/WSOL trade acceptance before this gate is closed.
2. A real Jupiter `NO_ROUTE` fixture has not been observed; current no-route handling remains conservative.
3. Sustained Jupiter 429 handling still uses bounded blocking cooldown; a non-blocking cycle-level design remains preferable.
4. First real post-enable Mission Control Gmail send + Sent readback still needs live evidence.
5. Actual reboot/login recovery of both new LaunchAgents still needs one real reboot acceptance.

## 8. Deferred / unfinished Mission features

### P0 — needed for rigorous monthly Frank strategy review

**Post-signal outcome tracker / monthly evaluator — MERGED TO MAIN, LOCAL RUNTIME REFRESH PENDING**

Review-branch implementation:
- forward-only registration for fresh REENTRY_WATCH / ACCUMULATION / MULTIPLE stages;
- executable Jupiter 30 USDC -> token entry inventory;
- same raw token inventory -> USDC exit quotes;
- T+5m/T+15m/T+1h/T+6h/T+24h;
- 5-minute sampled MFE/MAE/max drawdown;
- win rate, statistical median, mean return, profit factor;
- grouping by pattern and Decision;
- Ex-Top1 / Ex-Top3 24h robustness;
- `MISSED_WINDOW` rather than late-price backfill.

It still needs one final local full-suite rerun on merged `main`, LaunchAgent restart, and then real forward sampling.

### P1 — tracked-person expansion

**Reusable PERSON_PATTERN validation pipeline — NOT IMPLEMENTED**

Required flow:
wallet graph -> infrastructure exclusion -> raw finalized events -> market buy/sell/internal-transfer classification -> person-level ledger -> episodes -> causal signal time -> delayed replay -> robustness -> TRAIN/VALIDATION/HOLDOUT -> real FORWARD.

Current candidate states:
- Ethermonk: OBSERVE_ONLY / 0 validated patterns
- Point Farm: OBSERVE_ONLY / 0 validated patterns
- TheSolstice: OBSERVE_ONLY / 0 validated patterns

No production wallet registry or alerts are authorized for them yet.

### P1 — TOKEN_CONSENSUS

**Multi-person same-token consensus signal — DEFERRED**

The old design exists, but live authority is Frank-only. It requires at least two independently verified person_ids and must prove incremental edge over the one-person baseline before production use.

### P1 — wallet-cluster automation for CA research

**General wallet-cluster reconstruction engine — MERGED TO MAIN, LOCAL RUNTIME REFRESH PENDING**

Review-branch implementation:
- CA input in the same localhost Dashboard under `CA 链上查询`;
- Top20 token-account -> real owner resolution;
- bounded finalized Solana JSON-RPC history;
- direct target-token and SOL/USDC/WSOL relations;
- common funding / batch funding / common signer / consolidation evidence;
- synchronized buy/sell and distinctive-size behavior;
- public DEX/router/CEX/shared-infrastructure exclusion;
- confirmed relation vs probable control vs probable execution kept separate;
- strict concentration fields stay `UNRESOLVED` until special-address normalization is explicitly complete;
- persistent local reports + hashed RPC cache;
- quick / standard / deep presets;
- asynchronous single-worker execution to protect the free public RPC path.

The merged implementation still requires one real public-RPC CA acceptance run on the user's Mac before calling the feature locally accepted.

### P2 — MONSTER / 妖币 discovery

Status:
`RESEARCH_FROZEN / VALIDATION_NOT_PASSED`

- V3 TRAIN passed.
- Once-only 2024 validation failed ceiling / had insufficient target data.
- D2 blocked.
- D3 not started.
- No Monster LaunchAgent.
- No live Monster Gmail/scanner.
- No automatic V4 is authorized.

### P2 — NFT opportunity radar

Status:
`SPEC_PRESENT / RUNTIME_PAUSED`

Design is preserved, but no active Mission runtime/scheduler/Gmail currently provides NFT mint-opportunity coverage.

### P2 — CORE PRICE / overall-market trend monitor

Status:
`PAUSED`

BTC/ETH/SOL/HYPE/BNB price-abnormality / overall-market monitor is not running. Prior V2/V3 research remains historical; V3 is blocked by lack of a verifiably untouched hidden interval.

## 9. Intentionally excluded, not missing

The following are deliberate boundaries and should not be treated as unfinished bugs:

- automatic trading;
- wallet signing;
- swap construction/submission;
- GPT in Frank's real-time critical path;
- silent threshold tuning from live outcomes;
- new ChatGPT automation for this lane.

They require separate explicit authorization if ever reconsidered.


## 10. 2026-10-07 external review remediation on feature branch

Independent review of `fa01f7e` found three credibility-impacting defects plus several hardening issues. The branch now contains fixes for:

1. Public Jupiter/Raydium/PumpSwap/etc. DEX programs are recorded as `SHARED_INFRA`, not `SAME_EXECUTION_PROGRAM`; execution-only clusters no longer reduce unresolved material-holder share.
2. Funding-history `getTransaction = null` is recorded as unavailable evidence and skipped instead of aborting the CA job.
3. Even-sized outcome samples use the statistical midpoint median instead of the upper middle element.
4. Cluster POST body must be a JSON object.
5. Same CA is deduplicated only for the same scan preset; a requested deep scan is no longer silently replaced by an active quick scan.
6. Cluster POST requires `application/json` and rejects a non-loopback Origin while still allowing local CLI requests with no Origin.
7. Completed in-memory job metadata is bounded and full reports stay on disk; Dashboard reloads the last persisted CA report.
8. `DEV_LINKED_CLUSTER_PCT` includes wallets in a probable-control cluster containing a verified DEV/CREATOR/TREASURY wallet.
9. This status document now distinguishes current main/live authority from review-branch candidate functionality.

Independent review has now rerun the full local-agent suite on `b6f26499` with `738 passed` and found no new blocker. This is the accepted pre-merge feature-head evidence.


### Post-736 polish

After the `736 passed` review of `6c069ea`, three non-blocking polish items were implemented:

- persisted CA reports display exact observation time plus relative age after refresh, reducing the chance that an old holder snapshot is mistaken for current state;
- `SHARED_INFRA` / common-CEX evidence is localized in the Dashboard as public/shared infrastructure and explicitly says it does not imply common control;
- cluster report files, including `latest.json`, are written with temp-file + atomic replace semantics to avoid partial reads during same-CA refresh.

These commits were independently revalidated on `b6f26499`; the full local-agent suite passed `738` tests with no new blocker.


## 11. Merge record — 2026-10-07

Pull request #27 merged successfully into `main`.

- merge commit: `2f83be332e2c20270a3f534e333f1a19ea8b6bc5`
- accepted feature code head: `b6f26499`
- accepted feature full-suite result: `738 passed`
- final branch head before merge added acceptance/status documentation only
- production trading authority remains `NO_GO`

Main had advanced by 22 commits since the feature branch merge-base. Those commits touched airdrop/TGE, crypto-daily and US-stock-daily files and did not overlap the 23 Meme feature paths. GitHub reported PR #27 mergeable/clean and merged it normally.

### Required local post-merge acceptance

Before calling Meme local tooling v2 live on the user's Mac:

1. synchronize the local `frank-meme-main` checkout to current `origin/main`;
2. run the complete local-agent pytest suite on the merged main;
3. restart/reinstall the Mission Meme LaunchAgents so the loop and Dashboard load the merged code;
4. confirm policy gate, `delivery_allowed=true`, Dashboard HTTP 200 and both LaunchAgents running;
5. run one real CA query against Solana finalized RPC and verify Top20/coverage/cluster rendering;
6. confirm existing Frank signal view and Mac/Gmail notification path still remain healthy;
7. keep `PRODUCTION_TRADING = NO_GO`.

## 12. Local post-merge acceptance — 2026-10-07

User-local merged-main acceptance completed on `58a98faf`:

- local checkout synchronized to `origin/main` at `58a98faf`;
- complete local-agent suite: `738 passed` in 6.17s;
- policy gate: PASS;
- approved policy SHA256: `355336f2959e674939210b51be97d2df1d6e66f4ee3cca8acfe041dabb9e3ae8`;
- Gmail OAuth/config preflight: PASS, recipient `lxx.run688@gmail.com`, no email sent during preflight;
- Mission Meme loop LaunchAgent: running / active;
- Mission Meme dashboard LaunchAgent: running / active;
- Mission Control health: `status=OK`, `delivery_allowed=true`, `candidate_error_count=0`, `outcome_error_count=0`;
- SOL normalization sidecar: `status=OK`, with zero copied/resolved/unresolved rows in this acceptance cycle;
- Dashboard HTTP: 200 at localhost port 8766;
- AUTO-START: ON AFTER USER LOGIN;
- LIVE DELIVERY: policy-gated and enabled by approved policy;
- `PRODUCTION_TRADING = NO_GO`.

This closes the merged-main code/test/LaunchAgent startup acceptance gate.

Remaining runtime acceptance items:

1. run at least one real Solana CA through the new `CA 链上查询` page and verify Top20 owner / coverage / cluster rendering against live finalized RPC;
2. observe the first genuinely new forward outcome track and confirm T+5m/T+15m/T+1h/T+6h/T+24h persistence begins without historical backfill;
3. exercise a real SOL/WSOL-quoted Frank trade before declaring the SOL normalization path empirically exercised;
4. verify one actual Mission Control Gmail notification end-to-end, including Sent readback, when a real new eligible signal occurs;
5. after a future Mac reboot/login, verify both LaunchAgents automatically recover and Dashboard HTTP returns 200 without manual intervention.


## 13. CA research report v2 candidate — pending review

Branch:
`feature/meme-ca-report-v2-20261007`

Reason:
- first real CA acceptance attempt hit `HTTP_429` on the shared Solana public RPC;
- the first web UI exposed wallet-cluster mechanics but was too thin for the user's actual Meme investment workflow.

Candidate changes:
- explain quick / standard / deep scan budgets directly in the UI;
- remove the low-value CA hero description;
- pace and rotate across the free Solana mainnet endpoints listed in the Solana RPC directory, honor `Retry-After`, retain local cache, and expose RPC failure counts;
- never cache `getTransaction = null` as durable evidence;
- add finalized-chain token program / supply / mint authority / freeze authority / parsed metadata-update-authority status;
- add DexScreener secondary market snapshot (price, market cap, pair, liquidity, volume, buys/sells, price change);
- add a Jupiter $30 read-only executable quote and impact;
- expose bounded first confirmed market acquisition and pre-acquisition funding evidence for deep-scanned Top20 owners;
- render two explicit conclusion layers: chain/market-structure conclusion and full-investment conclusion;
- keep the full-investment conclusion pending when exact-CA narrative/official adoption, creator claim/buy/lock or treasury links are not verified;
- persist the richer report in both JSON and Markdown.

Trust boundary:
- finalized Solana RPC is authoritative for chain ownership/transactions/permissions;
- DexScreener is secondary market metadata only;
- Jupiter is executable quote evidence only;
- social/project adoption is not automatically inferred from name or link matching.

This branch is **not merged or live**. It requires a fresh full local-agent test run and external review before merge/reinstall.


## 14. CA research report v3 candidate — local validation required

Branch:
`feature/meme-ca-report-v3-20261007`

Built from the clean v2 candidate `18427693`, without modifying `main`.

Changes relative to v2:
- PublicNode added immediately after the configured/official Solana RPC in the fallback order;
- healthy requests stay on the configured/official primary rather than round-robin across providers;
- quick preset reduced to 6 owners / 8 target-token signatures / 4 funding signatures;
- standard preset changed to adaptive mode: 6 owners / 12 + 8 first, with only suspicious/material unresolved wallets deepened to 30 + 12;
- deep preset remains 20 owners / 100 + 50;
- Dashboard jobs expose progressive stages instead of a generic long-running spinner;
- per-CA conclusion history persists only material assessment changes and records new risks / removed uncertainty;
- missing `InvalidOperation` import in the v2 candidate was corrected;
- CA reports now include the existing read-only Frank state for that exact mint;
- Token-2022 sensitive extensions are surfaced as explicit chain-risk flags.

No main merge, LaunchAgent reinstall, notification-rule change, threshold change, wallet signing or production trading is authorized by this branch.

Required acceptance before merge:
1. full local-agent pytest on this exact branch head;
2. real CA query using the previously rate-limited test CA or another valid Solana CA;
3. verify base/Top20 progress appears before the final cluster report;
4. verify an RPC 429 can fail over without failing the entire report;
5. verify a repeat query with unchanged assessment does not append a fake conclusion-change event;
6. keep `PRODUCTION_TRADING = NO_GO`.


## 15. 2026-10-08 Frank classifier coverage remediation candidate

Status: `FEATURE_BRANCH_ONLY / LOCAL_VALIDATION_REQUIRED / PRODUCTION_UNCHANGED`.

A real RACE transaction exposed a classifier coverage gap already anticipated by the 2026-10-04 isolated trade-coverage study. The historical study had confirmed 19 active user trades that CURRENT classification missed; the shadow reconstruction changed one ACCUMULATION and one MULTIPLE on gross additions and also removed one existing MULTIPLE through the original sticky HFT rule. This means transaction-coverage repair can affect both positive and negative signal outcomes and must not be deployed without replay/acceptance.

Candidate remediation on `feature/meme-ca-report-v3-20261007` now:

1. adds officially documented Orca Whirlpools, Meteora DAMM v2 and Manifest market program IDs to the recognized market set; program identity still does not suffice without signer/authority, opposing owned flows and invocation-bound swap instruction evidence;
2. resolves parsed `programIdIndex` consistently instead of requiring a literal `programId` field in the second-stage swap check;
3. handles re-entrant program log stacks by closing the innermost matching invocation;
4. recognizes official Solana USDT as a quote identity, but keeps non-USDC amount predicates `UNDETERMINED`; no USDT=$1 assumption is introduced;
5. permits one target asset plus exactly one opposing primary quote even when additional quote refund/auxiliary legs exist; every quote leg is preserved, and composite quotes remain `UNDETERMINED` for the frozen USDC amount gate;
6. keeps multiple target assets, multiple opposing payment quotes, native-SOL reconciliation mismatches and unproven market programs fail-closed;
7. exposes existing `ACTIVE_SWAP_LIKE + UNKNOWN_NEEDS_REVIEW` records, plus signed successful opposing-flow cases with market proof still unresolved, in a read-only Dashboard `待复核链上行为` panel instead of making them appear absent;
8. keeps composite/auxiliary quote provenance out of both frozen USDC amount gates and Mission Control Frank reference-price math; a composite primary-USDC leg is not treated as the full Frank cost;
9. preserves the existing SOL-normalization sidecar semantics only for a simple non-USDC SOL quote with a verified causal previous-closed-minute reference; composite SOL legs remain `UNDETERMINED`;
10. resolves `programIdIndex` consistently for swap, token-transfer and native-transfer evidence and fixes re-entrant invocation-stack handling;
11. extends adaptive CA deepening to suspicious/material Top20 owners outside the first-six shallow prefix, including a relation counterpart discovered from a shallow owner;
12. makes the optional Frank per-CA snapshot non-fatal to the independent CA report if the read-only production DB is temporarily unavailable;
13. does not reclassify or backfill existing production history automatically and does not send historical notifications.

Frozen Frank thresholds are unchanged:
- ACCUMULATION still requires >=2 active buys within 60 minutes and >=25,000 direct-known USDC under the existing policy;
- non-USDC/composite quote amounts cannot satisfy the USDC amount threshold by themselves;
- production trading remains `NO_GO`.

Local validation checkpoint on `7387ca1dfa83861406020b08c6ed78f424025c36`:
- Python compile: PASS;
- targeted regression: `167 passed`;
- full local-agent suite: `769 passed`;
- RACE production raw hash: verified;
- old and candidate classifier at that checkpoint both returned `UNKNOWN_NEEDS_REVIEW / AMBIGUOUS_USER_EXCHANGE_ASSETS` because net balance evidence showed two positive non-quote assets: RARI `EFn88...gYwR` and RACE `RACEyW...9dLD`, with `5000 USDC` net outflow.

Follow-up chain inspection showed why net-only balance classification is insufficient for this case:
- the wallet's RACE Token-2022 ATA is created inside the transaction;
- RACE is received into that wallet-owned ATA and then spent again inside the same atomic transaction, leaving only a residual balance;
- the other positive target is RARI, whose principal pool is RARI/RACE;
- therefore the candidate parser now records ordered wallet-owned token transfer legs and may collapse a residual intermediate only when the chain flow proves receive-before-spend into exactly one downstream target. No dust/value threshold is used;
- parser evidence schema is bumped to `frank-v8`;
- a new isolated read-only classifier replay tool `scripts/frank_classifier_candidate_replay.py` compares stored production classification/state/signal behavior with current candidate code before any migration.

Current local validation checkpoint on `5d7c47f9151da75c20f7a2e695425d41386d531e`:
- targeted regression: `164 passed`;
- full local-agent suite: `772 passed`;
- real RACE raw transaction reclassified from `UNKNOWN_NEEDS_REVIEW / AMBIGUOUS_USER_EXCHANGE_ASSETS` to `ACTIVE_TRADE / SIGNED_DEX_SWAP_ROUTED_SINGLE_TARGET_WITH_RESIDUAL_INTERMEDIATE`;
- resolved final target mint: RARI `EFn88CiiFHhihqdr1Y11XBDxbbYarBf1ij92DsrigYwR`;
- RACE `RACEyWiM2ztEZcJx2AHXU2eWjhxU57x3vXn92b39dLD` is preserved as a routed residual intermediate with chain proof `CREATED_ZERO_PRE_RECEIVED_THEN_SPENT_CONSERVED_RESIDUAL`;
- aggregate USDC outflow is retained in the trade record, but `amount_predicate=UNDETERMINED`, `amount_predicate_reason=ROUTED_RESIDUAL_ASSETS`, and `route_amount_semantics=GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST`; therefore this event cannot satisfy the frozen >=25,000 direct-known-USDC amount gate by itself;
- isolated read-only production-history replay covered `970 / 970` stored signatures with `0` unreclassified rows;
- classifier changes: `72 ACTIVE_TRADE -> ACTIVE_TRADE` representation/provenance changes plus exactly `1 UNKNOWN_NEEDS_REVIEW -> ACTIVE_TRADE` (the RACE/RARI routed transaction);
- baseline signal parity against production: `true`;
- source/baseline/candidate signal counts: `3 / 3 / 3`;
- new signals: `0`;
- lost signals: `0`;
- candidate state deltas: `1`; exact delta remains a review item before any production-state migration;
- replay acceptance: `REVIEW_DELTAS`;
- production DB was opened read-only, no LaunchAgent changed, no production notification sent, and production trading remained `NO_GO`.

Independent review gate before any merge/runtime refresh:
- review the exact state delta and confirm it is the expected consequence of recognizing the routed RARI buy rather than an unrelated state change;
- review all 73 classifier transitions, especially the 72 `ACTIVE_TRADE -> ACTIVE_TRADE` representation/provenance changes, for amount-gate or follow-price regressions;
- verify routed residual reconstruction is fail-closed for true multi-target buys, reused/existing token accounts, multiple quote payers, incomplete transfer metadata and unrelated CPI transfers;
- verify `UNDETERMINED` routed/composite quote provenance cannot leak into frozen >=25k USDC gates, SOL normalization, Mission Control Frank reference-price math or historical notification replay;
- review adaptive Top20 deepening, Token-2022 extension semantics, assessment-history semantics and Frank read-only DB failure isolation from the CA v3 work;
- do not mutate existing production DB, backfill production state, replay historical notifications, merge main, reinstall LaunchAgents or enable production trading during review.


### Independent review FAIL and owner-fix candidate — 2026-10-08

Independent review of BASE `18427693ac53113f60243b6f9836a868ddbabc37` through review HEAD `4b3efc8b1c887f622f6a1eb13bced89f7414bc76` returned `FAIL`: 1 BLOCKING, 5 HIGH and 5 MEDIUM findings. The previous 772-pass checkpoint remains valid test evidence for that reviewed code, but it is not approval for real-CA acceptance, production migration or main merge.

Owner-fix policy after review:
- keep the frozen Frank thresholds unchanged;
- treat any transaction with more than one positive non-quote wallet net balance as economically multi-target unless router/market-call level evidence actually binds the route;
- receive -> spend conservation alone is retained only as `residual_flow_candidates` review evidence with `route_binding=UNPROVEN`; it no longer promotes a transaction to `ACTIVE_TRADE`;
- therefore the real RACE/RARI transaction is expected to return to `UNKNOWN_NEEDS_REVIEW / AMBIGUOUS_USER_EXCHANGE_ASSETS` until stronger route binding is implemented. This intentionally removes the prior speculative RARI production-state delta.

Owner-fix candidate now addresses the review findings as follows:
1. migration replay report output is constrained to a brand-new isolated workspace, reserved DB names/existing paths are rejected, and final report creation uses exclusive/no-follow semantics;
2. missing/invalid raw hashes are migration-blocking rather than counted as verified reclassification;
3. migration replay compares full classifier bodies, full V1 state/evaluation/signal/email semantics and multiplicity-aware signal identities rather than only summary counts;
4. replay uses stored ACTIVE_TRADE evaluation clocks when available, the stored terminal model clock, and explicitly labels classified-at timing surrogates where historical poll clocks are unavailable;
5. routed/composite/otherwise uncertain SOL quotes cannot gain `SOL_EVENT_TIME_USDC_VERIFIED` authority merely because a valid SOLUSDC candle exists;
6. T0 large-buy establishment uses the same known-amount provenance rule as the other frozen USDC gates;
7. Engine/Ledger/signal/email presentation separates authoritative target cost from gross observed quote flow and preserves unknown-cost contributions;
8. every Frank Mission Control read, including exact-CA snapshot, candidate list, review activity and recent trades, is explicitly scoped to `person_id=frank` by the reader identity;
9. Token-2022 sensitive extension parsing preserves configuration and distinguishes `ACTIVE_RISK`, `INACTIVE` and `UNRESOLVED` rather than treating extension-name presence as active authority;
10. assessment history now includes extension/authority semantics and separately records scan coverage so coverage-only changes do not append fake chain-state conclusions;
11. unresolved residual-flow facts remain visible in the Dashboard review panel without becoming candidates/signals.

This owner-fix code has not yet been locally validated. Required next gate:
- compile + targeted regression + full local-agent suite on the exact owner-fix HEAD;
- reclassify the real RACE raw transaction and require fail-closed `UNKNOWN_NEEDS_REVIEW` with an unproven residual-flow candidate, not an `ACTIVE_TRADE`;
- run the new migration replay into a fresh workspace and review source->baseline parity plus every baseline->candidate semantic delta;
- only after these pass, perform an independent second review. No main merge, real-CA acceptance, production-state migration, historical backfill, LaunchAgent reinstall or production trading is authorized yet.


### Owner-fix validation after independent review — 2026-10-08

Validated code HEAD: `b487c78d2f4a5d8f1a323605b2c4be97f9f4072d`.

Local owner validation:
- targeted owner-fix regression: `234 passed`;
- full local-agent suite: `794 passed`;
- real RACE raw hash verified;
- real RACE remains deliberately fail-closed:
  `UNKNOWN_NEEDS_REVIEW / AMBIGUOUS_USER_EXCHANGE_ASSETS`, `trade=null`;
- RACE residual-flow evidence is retained as
  `CREATED_ZERO_PRE_RECEIVED_THEN_SPENT_CONSERVED_RESIDUAL_ONLY`
  with `route_binding=UNPROVEN`; it is not promoted to RARI or another final-target trade.

Migration replay v2 against the current read-only production ledger:
- signatures: `978 / 978` reclassified, `0` unavailable;
- source -> baseline signal identity parity: `true`;
- source -> baseline state parity: `true`;
- source -> baseline evaluation deltas: `0`;
- baseline -> candidate signal identity parity: `true`;
- candidate signal content deltas: `0`;
- candidate evaluation deltas: `0`;
- candidate email deltas: `0`;
- new/lost signal identities: `0 / 0`;
- top-level classifier transitions: `72 ACTIVE_TRADE -> ACTIVE_TRADE`, no UNKNOWN -> ACTIVE promotion;
- candidate state deltas: `18`.

The 18 candidate state deltas were reviewed field-by-field. Across all 18 state rows, every changed field is additive classifier/audit provenance only:
- `events[*].quote_legs[*].asset/decimals/raw_delta`;
- `events[*].route_amount_semantics`;
- `events[*].route_intermediate_assets`.

No candidate state delta changes policy/behavior fields such as:
`state`, `hft`, `t0`, `watch_at`, `current_raw`, episode identity,
buy/sell counts or amount predicates. Therefore historical state migration/backfill
is **not required and is not authorized**. The safer deployment model is
forward-only: preserve the current production ledger and `v1_seen`, deploy the
reviewed code only after second-review/acceptance gates, and let the new parser /
classifier provenance apply only to newly observed signatures.

The replay also reports three source -> baseline signal-content deltas. These are
not signal-identity or decision changes: two include the expected
`LIVE -> DRY_RUN_AUDIT` replay-mode difference, and all three add the new
presentation/provenance fields (`latest_quote_* provenance`,
`gross_quote_out_observed`, empty unknown-cost contribution list). Candidate
signal content is exactly equal to baseline signal content, so the classifier
owner-fix introduces no additional signal-body delta.

Current gate:
- code tests: PASS;
- RACE fail-closed regression: PASS;
- source -> baseline state/evaluation/signal-identity parity: PASS;
- candidate signal/evaluation/email behavior parity: PASS;
- production historical migration/backfill: NOT REQUIRED / NOT AUTHORIZED;
- production trading: NO_GO;
- main merge: still pending second review and isolated real-CA acceptance.


### FRANK-009/010/011 closure-fix local validation — 2026-10-08

Validated HEAD: `f110d247ab009d5eec4b793ed08ccb38d873a91a`.

Local validation:
- compile: PASS;
- focused FRANK-009/010/011 regression: `52 passed`;
- full local-agent suite: `798 passed`.

The validated fix scope remains intentionally narrow:
- FRANK-009: incomplete or invalid Token-2022 transfer-fee / transfer-hook configuration remains `UNRESOLVED`; only complete, valid, explicitly inactive configuration may become `INACTIVE`;
- FRANK-010: assessment-history semantic comparison excludes accounting-only raw extension config changes such as `withheldAmount`, while the current raw extension configuration remains available as audit context;
- FRANK-011: tests now cover the exact incomplete/malformed transfer-fee cases, missing transfer-hook program-id case, and accounting-only withheld-balance history regression reproduced by the second reviewer.

No policy thresholds, Frank historical state, production DB, `v1_seen`, LaunchAgents, notification history or production-trading state were changed.

Next gate is a closure-only independent review of exactly
`82d66fd0c1d0edf45e5334006cbb24dbf2f71db1..f110d247ab009d5eec4b793ed08ccb38d873a91a`,
limited to FRANK-009/010/011. FRANK-001..008 should not be reopened unless this
four-file diff directly regresses one of them.


### FRANK-009/010 final edge-fix local validation — 2026-10-08

Validated runtime/test HEAD: `e628c61a2c0566f2202d590d7ff8167e074d1f3c`.

Local validation:
- compile: PASS;
- focused FRANK-009/010 regression: `54 passed`;
- full local-agent suite: `800 passed`.

The two remaining closure-review reproductions are now covered:
- FRANK-009: a single `olderTransferFee` schedule containing duplicate aliases
  (`transferFeeBasisPoints` + `basisPoints`, `maximumFee` + `maxFee`)
  cannot satisfy the requirement for distinct `olderTransferFee` and
  `newerTransferFee` schedules; the result remains `UNRESOLVED /
  TRANSFER_FEE_CONFIG_INCOMPLETE`;
- FRANK-010: accounting-only config such as `withheldAmount` is excluded from
  semantic history comparison, while authority/program/older-newer fee
  parameters remain in the semantic snapshot; therefore `withheldAmount 0 -> 1`
  does not append history, but a newer transfer fee parameter change
  `25 -> 50 bps` does append a `CHAIN_PERMISSION_CHANGE`.

No other review findings, policy thresholds, historical state, production DB,
`v1_seen`, LaunchAgents, notification history or production-trading state were changed.

Next gate is a closure-only review of exactly
`56eb0b8dafcbcd372f1f01cf4a33a7a2d760790e..e628c61a2c0566f2202d590d7ff8167e074d1f3c`,
limited to FRANK-009 and FRANK-010.


### Independent closure review complete — 2026-10-08

Final closure review of
`56eb0b8dafcbcd372f1f01cf4a33a7a2d760790e..26af467c439d2dc08b8ba86e48056d4170348630`
reported:
- FRANK-009: `CLOSED`;
- FRANK-010: `CLOSED`;
- all previous FRANK-001..011 findings: `CLOSED`;
- `SAFE_FOR_ISOLATED_REAL_CA_ACCEPTANCE = YES`;
- `SAFE_FOR_PRODUCTION_STATE_MIGRATION = NO`;
- `SAFE_FOR_MAIN_MERGE = NO` until the isolated real-CA acceptance gate is completed.

The independently re-run closure suite reported `800 passed` on the validated
runtime/test code. Historical Frank state migration/backfill remains unnecessary
and unauthorized. Existing production `v1_seen`, historical notifications,
production DB contents and LaunchAgents must remain untouched during isolated
real-CA acceptance. Production trading remains `NO_GO`.

Next gate: localhost-only port `8877`, a fresh isolated control root, dashboard
server only (no Mission Meme loop / no delivery), read-only production Frank
snapshot access, and live Solana/Jupiter/DexScreener CA-report generation.
