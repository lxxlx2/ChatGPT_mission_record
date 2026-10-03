# FRANK_LOCAL_SIGNAL_V1 — canonical rule extraction

**Policy status: FROZEN. Runtime activation requires separate successful acceptance and cutover.**

DERIVED_FROM_EXISTING_FRANK_BEHAVIOR_MODEL
NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT

Canonical source: `crypto-300-profit-mission/state/frank-wallet-watch.md` at commit `f36432aec00c0d91078b120758556b7413775366`.
Source SHA256: `34a4e0038640d6a511c75599316ddb834b61431909fb7df5e03e52c109c57868`.

PRECONFIRM has Path S and Path C only. PRECONFIRM Path A/B do not exist. Persistence Path A/B belong to the later conviction stage.

Canonical Path C is mixed: single >=15,000 USD equivalent OR >=2 buys totaling >=25,000 USD equivalent in 60 minutes. The user explicitly selected only its repeated-buy branch for V1. PATH_C_SINGLE_LARGE_BUY = NOT_ACCUMULATION; provenance is preserved and no new user-visible signal is created.

## Extracted predicates

### ACTIVE_SWAP_PROOF

All stages require proven active market exchange; passive activity does not count.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| ACTIVE_SWAP_PROOF_44 | 44 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | Count only a transaction where the Frank wallet is the active swap participant and value is exchanged through a DEX/aggregator/pool. |
| ACTIVE_SWAP_PROOF_46 | 46 | OTHER | SOURCE_CONTEXT | Ignore: |
| ACTIVE_SWAP_PROOF_47 | 47 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - plain SPL/Token-2022 transfers; |
| ACTIVE_SWAP_PROOF_48 | 48 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - airdrops; |
| ACTIVE_SWAP_PROOF_49 | 49 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - creator-fee/reward receipts; |
| ACTIVE_SWAP_PROOF_50 | 50 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - token mint/creation; |
| ACTIVE_SWAP_PROOF_51 | 51 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - claim distributions; |
| ACTIVE_SWAP_PROOF_52 | 52 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - unsolicited deposits; |
| ACTIVE_SWAP_PROOF_53 | 53 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - LP bookkeeping that is not a directional token buy/sell. |
| ACTIVE_SWAP_PROOF_55 | 55 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | A token balance increase alone is never a BUY signal. |

### HFT_EXECUTION

Global old no-alert filter; quantitative and unquantified execution patterns are preserved separately.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| HFT_EXECUTION_59 | 59 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | Classify a mint as `HFT_EXECUTION` and do not alert when any strong execution pattern is present, including: |
| HFT_EXECUTION_60 | 60 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - >=3 active swaps in <=60 seconds for the same mint; |
| HFT_EXECUTION_61 | 61 | ONCHAIN_FRANK_BEHAVIOR, TIMING | UNQUANTIFIED_APPROXIMATE | - rapid buy/sell round trips that largely close inside ~20 minutes; |
| HFT_EXECUTION_62 | 62 | ONCHAIN_FRANK_BEHAVIOR | UNQUANTIFIED_PATTERN | - repeated routing/arbitrage across multiple pools where the wallet is cycling inventory rather than building a position. |

### WATCH

Silent research state. All listed criteria apply; not a new accumulation threshold.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| WATCH_71 | 71 | ONCHAIN_FRANK_BEHAVIOR, TIMING | PERSISTENCE_A_CONTEXT | - at least 2 distinct active BUY swaps occurred within the rolling 60 minutes; |
| WATCH_72 | 72 | ONCHAIN_FRANK_BEHAVIOR | PERSISTENCE_A_CONTEXT | - gross active buys are directionally larger than sells; |
| WATCH_73 | 73 | ONCHAIN_FRANK_BEHAVIOR | PERSISTENCE_A_CONTEXT | - the wallet still has positive exposure; |
| WATCH_74 | 74 | ONCHAIN_FRANK_BEHAVIOR | PERSISTENCE_A_CONTEXT | - the pattern is not HFT_EXECUTION. |

### PRECONFIRM_PATH_S

((single >=5,000 USD) OR (rolling 60-minute aggregate >=10,000 USD)) AND first-party same-token call within prior 2 hours. Not authorized as the accumulation source.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| PRECONFIRM_PATH_S_277 | 277 | ONCHAIN_FRANK_BEHAVIOR, TIMING | NOT_MAPPED | - single active BUY >= 5,000 USD equivalent, OR active BUY aggregate >= 10,000 USD equivalent inside rolling 60 minutes; AND |
| PRECONFIRM_PATH_S_278 | 278 | SOCIAL, TIMING | REMOVED_NON_BEHAVIOR_AUTHORITY | - a first-party public Frank post/call on his own X/FOMO/public profile mentions the same token/ticker/CA within the prior 2 hours. |
| PRECONFIRM_PATH_S_280 | 280 | SOCIAL | REMOVED_NON_BEHAVIOR_AUTHORITY | Third-party reposts, replies from other accounts, and generic market posts do not satisfy the social condition. |

### PRECONFIRM_PATH_C

Social-unavailability fallback AND ((single active buy >=15,000 USD equivalent) OR (rolling 60-minute aggregate >=25,000 USD equivalent AND >=2 buys)). The single branch violates mandatory repeated-buy semantics.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| PRECONFIRM_PATH_C_283 | 283 | SOCIAL | REMOVED_NON_BEHAVIOR_AUTHORITY | - use only when first-party social source is unavailable, delayed, or not indexed; |
| PRECONFIRM_PATH_C_284 | 284 | ONCHAIN_FRANK_BEHAVIOR | PATH_C_SINGLE_LARGE_BUY_NOT_ACCUMULATION_USER_EXCLUDED | - single active BUY >= 15,000 USD equivalent; OR |
| PRECONFIRM_PATH_C_285 | 285 | ONCHAIN_FRANK_BEHAVIOR, TIMING | USER_SELECTED_REPEATED_BRANCH_USDC_DIRECT | - active BUY aggregate >= 25,000 USD equivalent inside rolling 60 minutes with >=2 BUY swaps. |

### PRECONFIRM_COMMON

Inherited preconfirm prerequisites and display rules, not additional buy thresholds.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| PRECONFIRM_COMMON_274 | 274 | ONCHAIN_FRANK_BEHAVIOR, TIMING | OLD_HOURLY_DELIVERY_SUPERSEDED_TARGET_LOCAL | Send Gmail PRECONFIRM at the first hourly scan that verifies active Frank buying and one of these paths. |
| PRECONFIRM_COMMON_292 | 292 | PRICE | NO_PRICE_VETO_ALREADY_IN_OLD_STAGE | Do not suppress PRECONFIRM solely because current price has moved above Frank VWAP. Show the deviation: |
| PRECONFIRM_COMMON_293 | 293 | PRICE | OPTIONAL_ENRICHMENT | - > +15%: `追价风险：高`; |
| PRECONFIRM_COMMON_294 | 294 | PRICE | OPTIONAL_ENRICHMENT | - > +25%: `仅观察，不建议追价`. |
| PRECONFIRM_COMMON_297 | 297 | OTHER | CANONICAL_TOKEN_IDENTITY_RETAIN | - exact mint/CA verified; |
| PRECONFIRM_COMMON_298 | 298 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - active swap confirmed, not transfer/airdrop/reward; |
| PRECONFIRM_COMMON_299 | 299 | LIQUIDITY | REMOVED_NON_BEHAVIOR_AUTHORITY | - basic liquidity exists; |
| PRECONFIRM_COMMON_300 | 300 | OTHER | NOT_FRANK_BEHAVIOR_EXCLUDED_FROM_TARGET_AUTHORITY | - no immediately visible hard honeypot / frozen-transfer condition. |

### MEANINGFUL_ACCUMULATION_T0

OR of the two exact canonical paths; never anchor on an unqualified dust/probe.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| MEANINGFUL_ACCUMULATION_T0_190 | 190 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | Do not anchor latency to a dust/probe buy. |
| MEANINGFUL_ACCUMULATION_T0_193 | 193 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - Frank makes >=2 active BUY swaps in <=60 minutes with combined gross buy >=3,000 USD equivalent; or |
| MEANINGFUL_ACCUMULATION_T0_194 | 194 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - one active BUY >=5,000 USD is followed by at least one additional active BUY within 60 minutes. |
| MEANINGFUL_ACCUMULATION_T0_196 | 196 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CONVICTION_CANDIDATE | A single buy, regardless of PnL later, cannot by itself create FORMAL_ENTRY. |

### PERSISTENCE_PATH_A_B

A OR B. These are conviction persistence paths, not PRECONFIRM paths.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| PERSISTENCE_PATH_A_B_203 | 203 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE_PREVIOUS_HOURLY_WATCH | - Path A: the mint was WATCH in the previous hourly run and still satisfies the entry gates now; or |
| PERSISTENCE_PATH_A_B_204 | 204 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE_45_MINUTES_3_BUYS | - Path B: at the current run, the observed active BUY sequence already spans >=45 minutes from first to latest BUY, contains >=3 active BUY swaps, and the other FORMAL_ENTRY gates are satisfied. |

### FRESHNESS

Target latency is not itself a hard buy-count predicate. Beyond 3 hours, listed gates apply.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| FRESHNESS_211 | 211 | TIMING | TARGET_NOT_NEW_HARD_THRESHOLD | - target: **45 to 120 minutes**; |
| FRESHNESS_212 | 212 | TIMING | RETAIN_CANDIDATE | - >3 hours is considered late for a fresh new entry. |
| FRESHNESS_214 | 214 | TIMING | RETAIN_CANDIDATE | If `now - T0 > 3h`, a new FORMAL_ENTRY is allowed only when: |
| FRESHNESS_215 | 215 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - Frank made a fresh active BUY in the last 60 minutes; |
| FRESHNESS_216 | 216 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE_UNQUANTIFIED_MATERIALITY | - the position remains materially open; |
| FRESHNESS_217 | 217 | PRICE, EXECUTABILITY | REMOVED_NON_BEHAVIOR_AUTHORITY | - current executable price <= Frank VWAP * 1.05; |
| FRESHNESS_218 | 218 | OTHER, LIQUIDITY | REMOVE_NON_BEHAVIOR_COMPONENTS | - all normal safety/liquidity gates pass. |

### CONVICTION_BEHAVIOR_OVERRIDE

These latest inventory rules are referenced by SUSPECTED_CONVICTION; older 70% retention and 30% gross sell-value cap are superseded.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| CONVICTION_BEHAVIOR_OVERRIDE_225 | 225 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - persistence Path A or B above; |
| CONVICTION_BEHAVIOR_OVERRIDE_226 | 226 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - cumulative gross active buys in the episode >=10,000 USD equivalent; |
| CONVICTION_BEHAVIOR_OVERRIDE_227 | 227 | ONCHAIN_FRANK_BEHAVIOR | OLD_SELL_VALUE_VETO_EXPLICITLY_REMOVED | - do **not** use lifetime/gross sell-value ratio as a hard rejection gate: profitable conviction positions can recycle principal or trim while remaining materially exposed; |
| CONVICTION_BEHAVIOR_OVERRIDE_228 | 228 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE_50_PERCENT_OR_NET_BUYING | - current token-unit exposure should normally remain >=50% of the episode peak token-unit exposure; alternatively, Frank must have resumed net buying in the last 60 minutes and still hold a material open position; |
| CONVICTION_BEHAVIOR_OVERRIDE_229 | 229 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE_35_PERCENT_DISTRIBUTION | - if token-unit exposure fell >35% during the last 60 minutes with no fresh re-accumulation, suppress ENTRY as distribution/exit-risk; |
| CONVICTION_BEHAVIOR_OVERRIDE_230 | 230 | PRICE, EXECUTABILITY | REMOVED_NON_BEHAVIOR_AUTHORITY | - current executable price normally between Frank VWAP * 0.92 and * 1.10; |
| CONVICTION_BEHAVIOR_OVERRIDE_231 | 231 | LIQUIDITY | REMOVED_NON_BEHAVIOR_AUTHORITY | - liquidity / quote reserve sufficient and not collapsing; |
| CONVICTION_BEHAVIOR_OVERRIDE_232 | 232 | OTHER | NOT_FRANK_BEHAVIOR_EXCLUDED_FROM_TARGET_AUTHORITY | - bounded token-control / transfer restriction checks pass; |
| CONVICTION_BEHAVIOR_OVERRIDE_233 | 233 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - no HFT_EXECUTION; |
| CONVICTION_BEHAVIOR_OVERRIDE_234 | 234 | OTHER | ASSET_SCOPE_NOT_FRANK_BEHAVIOR | - stablecoins, wrapped majors and obvious execution/hedging instruments excluded. |

### SUSPECTED_CONVICTION

Later-stage conjunction referencing persistence, T0 and latest inventory rules. Canonical says second Gmail; no numeric additional ADD count is specified.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| SUSPECTED_CONVICTION_310 | 310 | OTHER | OLD_STAGE_UPGRADE_CONTEXT | Send the second Gmail once later conviction conditions are satisfied: |
| SUSPECTED_CONVICTION_311 | 311 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - persistence Path A or B from the latency-aware override; |
| SUSPECTED_CONVICTION_312 | 312 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - meaningful accumulation T0 established; |
| SUSPECTED_CONVICTION_313 | 313 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - episode cumulative active BUY >=10,000 USD; |
| SUSPECTED_CONVICTION_314 | 314 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE_UNQUANTIFIED_MATERIALITY | - current token-unit inventory remains materially open under latest inventory-retention rules; |
| SUSPECTED_CONVICTION_315 | 315 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - no recent distribution invalidation; |
| SUSPECTED_CONVICTION_316 | 316 | PRICE, EXECUTABILITY | REMOVED_NON_BEHAVIOR_AUTHORITY | - current executable price normally inside Frank VWAP * 0.92 to * 1.10; |
| SUSPECTED_CONVICTION_317 | 317 | LIQUIDITY, OTHER | NOT_FRANK_BEHAVIOR_EXCLUDED_FROM_TARGET_AUTHORITY | - liquidity, token-control and transfer-restriction checks pass; |
| SUSPECTED_CONVICTION_318 | 318 | ONCHAIN_FRANK_BEHAVIOR | RETAIN_CANDIDATE | - no HFT_EXECUTION; |
| SUSPECTED_CONVICTION_319 | 319 | OTHER | ASSET_SCOPE_NOT_FRANK_BEHAVIOR | - not a stablecoin/wrapped major/obvious execution or hedging instrument. |

### RESET_CANCELLATION_EXIT

Source behaviors are preserved; V1 episode reset/dust rules are not invented.

| ID | Canonical source line | Categories | V1 treatment | Exact source predicate |
|---|---:|---|---|---|
| RESET_CANCELLATION_EXIT_106 | 106 | OTHER | OLD_DELIVERED_STAGE_PREREQUISITE | Only evaluate FORMAL_EXIT for a mint that previously generated a delivered FORMAL_ENTRY. |
| RESET_CANCELLATION_EXIT_109 | 109 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - Frank reduces the tracked position by >=35% in a rolling hour; |
| RESET_CANCELLATION_EXIT_110 | 110 | ONCHAIN_FRANK_BEHAVIOR | UNQUANTIFIED_EFFECTIVE_CLOSE | - Frank effectively closes the position; |
| RESET_CANCELLATION_EXIT_111 | 111 | ONCHAIN_FRANK_BEHAVIOR | UNQUANTIFIED_DISTRIBUTION | - repeated active sells clearly replace the prior accumulation regime; |
| RESET_CANCELLATION_EXIT_112 | 112 | OTHER, LIQUIDITY | REMOVED_NON_BEHAVIOR_AUTHORITY | - a hard token/liquidity invalidation emerges. |
| RESET_CANCELLATION_EXIT_330 | 330 | OTHER | OLD_DELIVERED_STAGE_PREREQUISITE | If PRECONFIRM was delivered but SUSPECTED_CONVICTION does not develop, send one `[撤销预确认]` follow-up only when a hard invalidation is observed: |
| RESET_CANCELLATION_EXIT_331 | 331 | ONCHAIN_FRANK_BEHAVIOR, TIMING | RETAIN_CANDIDATE | - token-unit inventory falls >35% in rolling 60 minutes with no re-accumulation; |
| RESET_CANCELLATION_EXIT_332 | 332 | ONCHAIN_FRANK_BEHAVIOR | UNQUANTIFIED_EFFECTIVE_CLOSE | - Frank effectively exits; |
| RESET_CANCELLATION_EXIT_333 | 333 | LIQUIDITY | REMOVED_NON_BEHAVIOR_AUTHORITY | - liquidity collapses materially; |
| RESET_CANCELLATION_EXIT_334 | 334 | OTHER | NOT_FRANK_BEHAVIOR_EXCLUDED_FROM_TARGET_AUTHORITY | - a hard token-control / transfer-restriction risk appears; |
| RESET_CANCELLATION_EXIT_335 | 335 | SOCIAL, ONCHAIN_FRANK_BEHAVIOR | SOCIAL_VETO_REMOVED_BEHAVIOR_UNQUANTIFIED | - original first-party social call is deleted/retracted and chain behavior also fails to confirm. |
| RESET_CANCELLATION_EXIT_337 | 337 | TIMING | QUIET_SCAN_NOT_RESET | Do not send cancellation merely because the next scan is quiet. |
| RESET_CANCELLATION_EXIT_347 | 347 | OTHER | RETAIN_ONCE_PER_MINT_EPISODE_STAGE | Each stage for a mint/episode is delivered at most once. |

## Exact numerical inventory

| Parameter | Canonical value | Status |
|---|---|---|
| Path S single / aggregate / social lookback | >=5,000 USD / >=10,000 USD in 60 min / prior 2 h | NOT_MAPPED |
| Path C single | >=15,000 USD equivalent | NOT_ACCUMULATION_PROVENANCE_ONLY |
| Path C repeated | >=2 buys AND >=25,000 USD equivalent in 60 min | USER_SELECTED_V1_USDC_DIRECT |
| T0 path 1 | >=2 buys AND >=3,000 USD equivalent in <=60 min | CONVICTION_CORE |
| T0 path 2 | >=5,000 USD buy followed by >=1 additional buy within 60 min | CONVICTION_CORE |
| Persistence A | previous hourly WATCH; no numeric extra ADD requirement | CONVICTION_CORE |
| Persistence B | >=3 buys spanning >=45 min | CONVICTION_CORE |
| Conviction cumulative buy | >=10,000 USD equivalent per episode | CONVICTION_CORE |
| Inventory retention | normally >=50% of episode peak; OR resumed net buying in last 60 min and material open position | CONVICTION_CORE |
| Distribution veto / preconfirm cancellation | >35% token inventory fall in 60 min without re-accumulation | CONVICTION_CORE |
| Old FORMAL_EXIT reduction | >=35% tracked position reduction in rolling hour | OLD_EXIT_SCOPE |
| HFT count | >=3 active swaps in <=60 s for same mint | BEHAVIOR_VETO |
| HFT round trip | largely close inside ~20 min | APPROXIMATE_NOT_EXACT_THRESHOLD |
| Freshness target / stale boundary / refreshed buying | 45–120 min / >3 h / active BUY within 60 min | TIMING |
| Deprecated executable price bounds | VWAP *0.92 to *1.10; stale-entry cap *1.05 | REMOVED_FROM_AUTHORITY |
| Old preconfirm display deviations | >15%, >25% above VWAP | ENRICHMENT_ONLY |
| Superseded base entry rules | two consecutive hourly observations; >=70% retention; sell value <=30% gross buys | SUPERSEDED_BY_OVERRIDES |
| Old suggested sizing | 10–30 USD base; 20–30 USD initial/add; 50–60 USD cap; 0–15 USD preconfirm; ~100 USD lane | NOT_SIGNAL_PREDICATES |
| Old runway scenarios | 3x and 5x implied capitalization | NOT_SIGNAL_PREDICATES_NO_GUARANTEE |
| Old scheduler / overlap | hourly :29; 0–59 min latency; 15 min signature overlap; 2 h social overlap | OLD_OPERATIONAL_NOT_NEW_BEHAVIOR_THRESHOLD |
| Relative-size / percentile / dust / extra ADD count | NOT_SPECIFIED | DO_NOT_INVENT |

## Mapping and freeze decision

ACCUMULATION V1: >=2 distinct confirmed ACTIVE BUY signatures for the same person/mint observed sequence in an inclusive rolling 3,600-second window, whose raw USDC quote quantities total >=25,000. No single-buy branch. No social, price, liquidity, GPT or HFT veto is added to this explicitly selected accumulation branch.
MULTIPLE V1: prior/current ACCUMULATION stage; T0 established by >=2 buys totaling >=3,000 USDC in <=3,600 seconds OR a >=5,000 USDC buy followed by another buy within 3,600 seconds; episode cumulative known USDC buys >=10,000; persistence A (WATCH in the prior hourly :29 observation) OR B (>=3 buys spanning >=2,700 seconds); known observed-sequence position >0 and >=50% episode peak OR positive net token buying in the last 3,600 seconds; no >35% token-unit drop in the last 3,600 seconds without fresh re-accumulation; no >=3 active swaps in <=60 seconds HFT episode; no proven rapid round-trip close within the old approximate 20-minute reference. If T0 age >10,800 seconds, require fresh active BUY within 3,600 seconds and an open position. No numeric extra ADD count, percentile, or lifetime-zero-start requirement is invented.
Social availability/calls, price suitability/chase limits, liquidity, executability, non-Frank token-control suitability and GPT vetoes do not participate in V1 pass/fail. WATCH remains silent; :29 is only the provenance-preserving persistence-A observation clock, not a delivery dependency. Signals and delivery run locally immediately.
USER_AUTHORIZED_UNIT_UPDATE: USDC quote => direct numeric comparison. The existing 3,000 / 5,000 / 10,000 numbers are preserved; accumulation uses the user-selected 25,000 USDC branch. Non-USDC quote without reliable conversion => amount gate UNDETERMINED; active trade, position and every non-amount predicate remain recorded. No independent dollar valuation or SOL-to-USD rule is claimed. Known USDC totals are conservative lower bounds when an episode also contains unvalued quote assets.
Canonical source has no numeric additional-ADD requirement, numeric dust/close threshold, required zero lifetime starting balance, or buy-size percentile. Missing definitions remain null in JSON.
Retained behavior candidates include exact active swaps, amount/count/window conditions, conviction persistence, retention/distribution, HFT behavior and hard on-chain exit conditions. Unquantified predicates are not guessed.
Historical replay is DRY_RUN_ONLY. It never dispatches notifications/Gmail. Each stage is emitted once per policy/person/mint/observed episode. Same-stage ADD updates state without duplicate delivery. An observed active-trade inventory of exactly zero closes the observed sequence; unresolvable sells preserve unknown inventory rather than guessing EXIT. LIFETIME_POSITION_UNKNOWN does not erase CURRENT_ACCUMULATION_SEQUENCE_KNOWN.
Test results, historical replay and controlled cutover evidence are reported separately; freezing this policy does not certify the runtime as live.
PRODUCTION TRADING = NO_GO; OTHER PERSONS = DEFERRED; NEW AUTOMATION = NO.
