# Frozen PHASE_3B_R failure forensics plan — 2026-09-30

Authorization: forensic diagnostics only, no new rule/GT release and no optimizer. PRICE_RULE_V1/V2 source, specs, results, winner, reports and private baseline evidence remain byte-identical. Preserve original V2_FREEZE_COMMIT15753ad1092cc2b1b9bd36270dd770916c50aec0 and V2_WINNER_COMMIT0b3d0cff2199c2bab42d07b42d4e5b8b9259e654. Commit/push this plan BEFORE generating forensic results. Snapshot protected hashes and verify before/after. Source is existing immutable official cache only; no market network, audit, HYPE, live, transport, Gmail, automation, launchd or portfolio work.

## Inputs and clocks

Only CALIBRATION [2026-06-02T05:57Z,2026-08-01T05:57Z) and VALIDATION [2026-08-01T05:57Z,2026-08-31T05:57Z), each with existing1476-bar warmup. Exact frozen winner thresholds, no alterations. Runtime I/O hook rejects audit subtree including manifests, future/hidden datasets and any V3 config output. File-loading capabilities admit only the two role/range/hash-bound partitions. Acquisition summary may be used only for storage/provenance, never audit cache values. Hashing already protected whole-evidence files is integrity-only, not diagnostic input; no audit cache open is needed for this phase.

Sample time is canonical bar exclusive CLOSE, consistent with V2 episode timestamps. Explicitly include bar open/close time so a05:14 onset is the bar opened05:13. Closed-time windows inclusive:
- Each of the five SOL misses05:14,05:16,05:20,05:24,08:38 UTC2026-08-22: onset±30min,61 rows each.
- Merged early window04:45–06:00,76 rows; late window08:00–09:15,76 rows. Union these and individual windows; store all required full traces, without extrapolating price or excluding intervening minutes.

## Expanded minute evidence

OHLC,all frozen features,drawup/drawdown15m,missing_data,raw/source input hash. Each GT family always emitted with active,direction,magnitude,threshold,normalized exceedance; inactive values still reported. Breakout normalization uses applicable distance/prior reference plus continuity condition; volatility normalized score=min(vol/(4*median),abs5m/.025), activation requires both. Families with missing data inactive/unknown, not fabricated.

Record raw material directions,selected GT direction/first-family reason,conflict flag,full active episode before/after,onset/finish flag and finish reason (opposite_material,inactive_reset,partition_censor). Full GT episodes include onset/end/last_material/types/peak/excursion/input hashes; graph ordered by onset and exact causative family at every flip.

Each R1–R9: raw condition active,direction,magnitude,threshold,normalized score and current eligibility; up/down/both masks,lowest active rule,selected candidate direction,latched direction/rule timestamps before/after,event/no-event/reason. R6 normalized score=distance/.01,with two-sample causal eligibility; R7 score=min(vol/(3*median),abs5m/.02); R5 uses signed drawup/drawdown. Candidate arbitration data includes all simultaneous raw rule directions, not only selected ones.

## Population counters and matching

CALIBRATION and VALIDATION per asset: observed evaluation minutes,GT conflict count/rate,switches at conflict minutes or immediately following a conflict (report same-step and lag1 separately),episode starts at/after conflict,selected family distribution; candidate mixed-direction minute count/rate,direction changes,flips with current lowest-number rule opposing previously latched direction while a previous-direction raw rule still exists,episode starts,reversal/rule-added counts. Specifically count R1/R2 arbitration over opposing R3–R9. Do not count warmup in rates; count only eligible closed minutes and give denominator.

Reconstruct P0 episodes/events and require per-asset frozen validation metrics,miss IDs,state hashes and event identity hashes to match, and calibration winner metrics to match. A mismatch is flagged before causal claims; do not update frozen artifacts to hide it. Family recall uses final episode type union and original onset hit window; a conflict-family episode has a conflict sample during its material lifetime. Single/multi-family counts and onset-family attribution reported separately. R2/FAST overlap:FAST-containing episode totals,main hits with R2 exact/pre-onset,only-other-rule hits,FAST misses,plus onset FAST active subset; final-type union and onset presence are not conflated.

## Suspicious fragmentation and price-path grouping

SUSPICIOUS_FRAGMENTATION: same asset/direction returns after previous same-direction episode end<=10min, with at least one intervening opposite episode, every intervening opposite episode duration<=5min. Pair consecutive same-direction episodes; include exact gap/intervening IDs,including direct negative/zero gap boundaries. This is a forensic flag, NOT new GT.

Stability per policy/asset:episode count,median/p95 duration,episodes<5min/<10min,direction flips/hour,same-direction reentry after previous end<=5/10/30min,fragmentation ratio(reentries<=30min divided by all episodes; denominator explicit),suspicious edges,count of reentry episodes. P4 has one envelope:single direction flips N/A; also report directional sub-signal on/off counts,not assign fake single-direction flips.

For five misses group via connected suspicious-fragmentation edges on original GT IDs (including intervening nodes) restricted to the contiguous early or late trace; integrity-verified minute continuity required. Report connected grouped price sequences separately from raw episode misses, retaining original75% validation. Price sanity:all onset closes,first onset close,window min/max close,net return,max positive/negative excursion relative to first onset; additionally clustered05:14–05:24. POSSIBLE_EPISODE_FRAGMENTATION if repeated direction flips in that10min cluster and max close/min close-1<4%(frozen FAST scale). This flags weak independence; it does not establish that all material reversals are economically false.

## Deterministic primary/secondary cause classification

Primary precedence (first satisfied), to avoid result-driven relabeling:
G IMPLEMENTATION_BUG:reproduced behavior violates frozen contract/invariant; identity/result mismatch first stops confirmation.
B GT_DIRECTION_CONFLICT_FRAGMENTATION:miss onset is a suspicious reentry node,local intervening GT direction flips originate from different/opposing material-family evidence; price sanity and raw conflicts included,not assumed from onset list.
C CANDIDATE_DIRECTION_CONFLICT:within main hit window a same-onset-direction raw rule is active but arbitration selects opposite direction at an event opportunity/current onset; no credited same-direction event.
D LIFECYCLE_HYSTERESIS_MISMATCH:same-direction raw rule active in main window,selected candidate direction agrees,but no credited event because it remains latched/no new activation; cite rule last-true and last prior event time.
E HIT_WINDOW_TIMING:first qualifying same-direction event occurs after onset and<=5min,unless higher-precedence evidence applies.
A TRUE_THRESHOLD_GAP:no same-direction raw candidate rule reaches threshold throughout main window,no higher-precedence cause; list closest normalized scores at onset/window and any later event.
F GT_EPISODE_MODEL_ARTIFACT:independence concerns outside family-conflict mechanism,with quantitative path/lifecycle evidence and no A–E/G explanation.
H OTHER:explicit quantitative evidence and explanation required; never silent unknown.

Secondary causes include every supported alternate C/D/E/A and price-fragmentation tag;never contradictory A if same-direction raw thresholds already active. Primary deterministic decision emits predicate evidence for review. A raw threshold criterion is stricter than absence of emitted candidate; do not call all misses threshold gaps. Family-priority causes can apply even if chosen family changes when the preceding family becomes inactive; distinguish simultaneous conflict from temporal family substitution.

Three late detections:first same-direction event in(onset,onset+5min],delay seconds,activated rules/reason;compare onset and event raw features/scores/latched state,which threshold/state/arbitration changed. Do not award late credit or retime GT onset.

## Fixed counterfactual diagnostics P0–P4

No parameter search,policy ranking,winner,V3 config or validation-PASS promotion. Both labels and candidate arbitration use each named policy with identical frozen thresholds/hysteresis;report they jointly change denominator and detector,not an isolated causal treatment. Match exactly frozen[-15min,0] main window.
P0 CURRENT_PRIORITY:call unchanged V2 GroundTruth/Activations; GT first active family, candidate lowest numbered rule.
P1 ACTIVE_DIRECTION_INERTIA:retain prior latched direction whenever at least one current raw same-direction signal exists;else use original priority. A latched direction with no current same-direction signal gets no inertia credit.
P2 MAX_NORMALIZED_EXCEEDANCE:choose direction of active family/rule with highest dimensionless score;exact ties use original family/rule priority. Both components of composite vol condition normalized with min;R6 eligible causal2-sample score;GT breakout eligible3-sample score.
P3 MULTI_SIGNAL_VOTE:one vote per active family/rule;majority direction;tie retain previous latched direction if it is represented among current signals,else use P2.
P4 TWO_SIDED_CONCURRENT:GT one market envelope starts when ANY material family active,ends after30inactive minutes,keeps raw directional sub-signals and onset_directions;does not split envelope on opposite signal. Candidate one envelope with independent UP/DOWN activation state machines,each fixed30min rearm;new opposite-side sub-signal emits its own activation rather than single-direction REVERSAL;same envelope counts once. An envelope hit requires event matching one of causal onset_directions,not future type/direction union. For each old P0 miss,report containing same-direction P4 sub-signal/envelope and whether envelope/onset detection or that original timestamp's detection differs;P4 is diagnostic complexity,not approved production semantic.

For P1–P3 derive independent diagnostic state from copied price/feature inputs in new forensics module;never monkeypatch or edit V2 classes. P0 full reconstruction must still match frozen stored validation. For each policy,report both partitions per-asset episodes/candidate events/candidate episodes/hits/recall,stability metrics,and five original miss mappings (retained,merged/no new onset,direction changed,mapped hit/miss). Do not select a winning policy. Record normalized ties and conflict policy precedence.

## Statistical interpretation and final deliverables

Wilson95% intervals z=1.959963984540054 for20 aggregate episodes15hits and13 SOL8hits. Report actual one/two additional/resolved miss sensitivity in percentage points,maximum allowed misses under unchanged90% gate (aggregate2,SOL1),and12/13 requirement. Statistics are explanations,not gate relaxation.

Outputs: PHASE3B_R_V2_FAILURE_FORENSICS_REPORT.md; private immutable machine-readable summary,seven trace exports,ordered fragmentation graph,all original P0 GT episodes/events,policy summary tables. Report protected artifact hashes,freeze/final commit,255+new tests both interpreters,CPU/RSS/wall/storage,forbidden external action counts0. COMPLETE only if all five primary classifications have reproducible evidence,exact61/76 rows,all required counters/families/stability/P0–P4 outputs,and frozen result preservation. Else DIAGNOSIS_INCOMPLETE with missing evidence. No root-cause-certainty claim beyond reproduction scope.

At most three architecture options:A single-direction with redesigned arbitration;B market envelope separated from directional sub-signals;C vol/asset-normalized architecture. For each explain benefit,risk,new contract to freeze,new genuinely unused historical or forward interval to reserve. Do not choose/implement,download or open future hidden data. V3 NOT_AUTHORIZED,PHASE_3C NO_GO,PRODUCTION NO_GO regardless of diagnosis completeness. Final commit/push feature only using force-with-lease,then stop.
