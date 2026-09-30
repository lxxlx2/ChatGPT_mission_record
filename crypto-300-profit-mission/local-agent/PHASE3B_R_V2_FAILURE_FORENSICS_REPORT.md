# PHASE3B_R_V2_FAILURE_FORENSICS_REPORT — 2026-09-30

**PHASE_3B_R_DIAGNOSIS_COMPLETE. V2_VALIDATION_RESULT_PRESERVED. PHASE_3C=NO_GO; V3=NOT_AUTHORIZED; PRODUCTION=NO_GO.**

The five original SOL miss episodes reflect two forensic price sequences. Four early UP misses occur in a direction-fragmented reversal range where current candidate arbitration keeps choosing a still-active DOWN R1. The later08:38 DOWN miss has no raw candidate condition in the permitted hit window; its R3/R9 activation arrives5min late. This explains observed failure mechanisms without changing the original15/20=75% result or proving a replacement rule.

## Identity, sync and preservation

Branch: `codex/crypto-monitor-design-20260930`.
FORENSICS_FREEZE_COMMIT: `e30dd63c262d9575aec5be799de14fd6036eac09`. Plan committed and pushed before result generation.
V2_FREEZE_COMMIT: `15753ad1092cc2b1b9bd36270dd770916c50aec0`; V2_WINNER_COMMIT: `0b3d0cff2199c2bab42d07b42d4e5b8b9259e654`.
Starting feature SHA92634ee5b11a6555ddc74ff9d069f277ecab514b. Initial fetch found no new main commit; origin/main4d7dcfa7acaebf810a3a10461f164c803a2ec78b,feature ahead15/behind0. No rebase required and original freeze/winner identities remain reachable unchanged. Final SHA is the commit containing this report,reported after force-with-lease push.

88 original tracked local-agent artifacts checked byte-for-byte against the Phase3B final commit before and after analysis:zero changed. This includes all V1/V2 code,GT/rule/freeze docs,search JSON,calibration/winner/validation results,reports and original tests. Private baseline writes are blocked in the analysis process. No V2 correction/re-evaluation promotion or V3 config was written.

## Frozen inputs and evidence exports

Only immutable official CALIBRATION and exposed VALIDATION caches used;no new market download. P0 metrics exactly match every original per-asset calibration/validation metric;candidate state hashes match both and calibration feature hashes match the frozen result. Original five miss IDs reproduced. Runtime guard recorded zero audit reads,zero network calls,zero protected-file changes. Audit caches/manifests were not opened as diagnostic input. No HYPE diagnostic or future hidden dataset was opened.

All sample times below are exclusive bar CLOSE times,as in the original V2. For example05:14 is the bar opened05:13. Every row retains bar open/close UTC timestamps,OHLC,all frozen features and signed reversal components;all five GT-family details;GT before/after and finish reasons;all nine candidate rules/masks,latched state/events;P0–P4 diagnostic state. Full source/input hashes retained.

| Export | Inclusive UTC close-time interval | Actual/expected rows | File |
|---|---|---:|---|
|early-merged|2026-08-22 04:45 → 2026-08-22 06:00|76/76|`/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/early-merged.json`|
|late-merged|2026-08-22 08:00 → 2026-08-22 09:15|76/76|`/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/late-merged.json`|
|miss-1|2026-08-22 04:44 → 2026-08-22 05:44|61/61|`/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/miss-1.json`|
|miss-2|2026-08-22 04:46 → 2026-08-22 05:46|61/61|`/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/miss-2.json`|
|miss-3|2026-08-22 04:50 → 2026-08-22 05:50|61/61|`/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/miss-3.json`|
|miss-4|2026-08-22 04:54 → 2026-08-22 05:54|61/61|`/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/miss-4.json`|
|miss-5|2026-08-22 08:08 → 2026-08-22 09:08|61/61|`/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/miss-5.json`|

Machine summary: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/summary.json`. Ordered graph: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/early-fragmentation-graph.json`. Signed range geometry: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3br-forensics-20260930/reversal-range-geometry.json`. Evidence stays outside Git;human tables below report selected observations.

## Five individual miss classifications

Primary precedence and evidence predicates were frozen before analysis;one primary per miss. Secondary causes retain overlapping mechanisms.

| Original onset UTC | Direction | Primary cause | Secondary causes | Evidence |
|---|---|---|---|---|
|2026-08-22 05:14|UP|B_GT_DIRECTION_CONFLICT_FRAGMENTATION|C_CANDIDATE_DIRECTION_CONFLICT|REVERSAL UP6.851% beats VOL DOWN by GT family order;R1 DOWN5.466% beats UP R5 by rule order;prior UP episode returns after4min DOWN episode.|
|2026-08-22 05:16|UP|C_CANDIDATE_DIRECTION_CONFLICT|none|R1 DOWN5.396% masks UP R5=7.319% and UP R7 move4.287%;the intervening REVERSAL DOWN→UP flip uses the same family,so frozen different-family B predicate is not assigned primary.|
|2026-08-22 05:20|UP|B_GT_DIRECTION_CONFLICT_FRAGMENTATION|C_CANDIDATE_DIRECTION_CONFLICT, E_HIT_WINDOW_TIMING|UP reentry after3min FAST_MOVE DOWN episode;R5 UP6.863% already true but R1 DOWN5.855% selected;first UP event05:25.|
|2026-08-22 05:24|UP|B_GT_DIRECTION_CONFLICT_FRAGMENTATION|C_CANDIDATE_DIRECTION_CONFLICT, E_HIT_WINDOW_TIMING|UP reentry after1min FAST_MOVE DOWN episode;R5 UP6.737% already true but R1 DOWN4.009% selected;first UP event05:25.|
|2026-08-22 08:38|DOWN|E_HIT_WINDOW_TIMING|A_TRUE_THRESHOLD_GAP|MEDIUM_MOVE DOWN7.212% is material;R3 requires8%,relative4h5.201% is below R9=6%;all candidate conditions absent in main hit window;R3/R9 arrive08:43.|

Primary totals:B=3,C=1,E=1. A_TRUE_THRESHOLD_GAP is supported secondary for08:38;four early misses are not missing candidate thresholds because same-direction R5 (and sometimes R7) were already active. D lifecycle-hysteresis alone is not selected for any of the five;the early candidate direction persists DOWN but the observed omission is arbitration,not merely a same-direction rule waiting to rearm. G implementation bug is not established by these traces.

## Exact early episode graph

Observed sequence: `04:38 UP → 05:10 DOWN → 05:14 UP → 05:15 DOWN → 05:16 UP → 05:17 DOWN → 05:20 UP → 05:23 DOWN → 05:24 UP → 05:31 DOWN`. Each immediate change is allowed by the frozen opposite-material rule;none needs30inactive minutes.

| Episode ID | Direction | Onset UTC | Last material UTC | End UTC | Final type set | Exact onset/flip family | Onset close |
|---|---|---|---|---|---|---|---:|
|`gt2e:SOL:1787373480000:UP`|UP|2026-08-22 04:38|2026-08-22 04:49|2026-08-22 05:10|FAST_MOVE,MEDIUM_MOVE|MEDIUM_MOVE|100.53|
|`gt2e:SOL:1787375400000:DOWN`|DOWN|2026-08-22 05:10|2026-08-22 05:13|2026-08-22 05:14|FAST_MOVE,REVERSAL,VOL_EXPANSION|VOL_EXPANSION|95.53|
|`gt2e:SOL:1787375640000:UP`|UP|2026-08-22 05:14|2026-08-22 05:14|2026-08-22 05:15|REVERSAL|REVERSAL|93.73|
|`gt2e:SOL:1787375700000:DOWN`|DOWN|2026-08-22 05:15|2026-08-22 05:15|2026-08-22 05:16|REVERSAL|REVERSAL|93.33|
|`gt2e:SOL:1787375760000:UP`|UP|2026-08-22 05:16|2026-08-22 05:16|2026-08-22 05:17|REVERSAL,VOL_EXPANSION|REVERSAL|94.14|
|`gt2e:SOL:1787375820000:DOWN`|DOWN|2026-08-22 05:17|2026-08-22 05:19|2026-08-22 05:20|FAST_MOVE,REVERSAL|FAST_MOVE|92.1|
|`gt2e:SOL:1787376000000:UP`|UP|2026-08-22 05:20|2026-08-22 05:22|2026-08-22 05:23|REVERSAL|REVERSAL|93.74|
|`gt2e:SOL:1787376180000:DOWN`|DOWN|2026-08-22 05:23|2026-08-22 05:23|2026-08-22 05:24|FAST_MOVE|FAST_MOVE|93.08|
|`gt2e:SOL:1787376240000:UP`|UP|2026-08-22 05:24|2026-08-22 05:26|2026-08-22 05:31|REVERSAL|REVERSAL|93.63|
|`gt2e:SOL:1787376660000:DOWN`|DOWN|2026-08-22 05:31|2026-08-22 06:08|2026-08-22 06:38|FAST_MOVE|FAST_MOVE|93.47|

05:15→05:16 is especially informative:the same REVERSAL family changes sign from whichever15m component is larger. This is additional model instability beyond the two simultaneously conflicted GT minutes. At05:23,REVERSAL can still support UP,but higher-priority FAST_MOVE selects DOWN. Temporal family substitution and within-family signed-range dominance both contribute;simultaneous conflict-minute counts alone understate fragmentation.

## Price-path sanity and signed-range geometry

| Window | First/last close | Min/max close | Net return | Max forward/reverse excursion vs first | Range max/min−1 |
|---|---|---|---|---|
|cluster_0514_0524|93.73/93.63|92.1/94.14|-0.1067%|0.4374%/-1.7390%|2.2150%|
|early_merged|102.21/94.23|90.27/102.21|-7.8075%|0.0000%/-11.6818%|13.2270%|
|late_merged|94.46/94.24|93.11/94.99|-0.2329%|0.5611%/-1.4292%|2.0191%|

The05:14–05:24 cluster has11 close samples,net−0.1067%,range2.2150%,and repeated directional episodes;it meets frozen **POSSIBLE_EPISODE_FRAGMENTATION**. The full04:45–06:00 path is not flat:net−7.8075%,max reverse excursion−11.6818%;this is a sharp selloff/rebound path with internal oscillation,not evidence that no material market move occurred. Four early miss onsets have closes93.73,94.14,93.74,93.63. The earlier04:38 episode onset close is100.53.

Local high/low refer to OHLC extrema,including wicks,not only closes. At05:14/05:15/05:16,the15m high99.98 and low87.72 are unchanged;small close changes alter which large retrospective component wins:

| Time | Close | Local high/low | Drawup15m | Drawdown15m | GT selection |
|---|---:|---|---|---|
|05:14|93.73|99.98/87.72|6.8513%|6.2513%|UP:REVERSAL|
|05:15|93.33|99.98/87.72|6.3953%|6.6513%|DOWN:REVERSAL|
|05:16|94.14|99.98/87.72|7.3187%|5.8412%|UP:REVERSAL|
|05:17|92.1|99.98/87.72|4.9932%|7.8816%|DOWN:FAST_MOVE|
|05:20|93.74|99.71/87.72|6.8627%|5.9874%|UP:REVERSAL|
|05:23|93.08|98.56/87.72|6.1104%|5.5601%|DOWN:FAST_MOVE|
|05:24|93.63|97.82/87.72|6.7373%|4.2834%|UP:REVERSAL|
|05:25|93.58|95.89/87.72|6.6803%|2.4090%|UP:REVERSAL|

Thus an UP label does not require a fresh5% rise from the prior episode close. The historical local low can continue to support a>5%drawup while local-high drawdown also exceeds5%. A single chosen sign plus immediate-opposite splitting can relabel a shared range as alternating independent events. This is a design concern,not proof that a particular directional sub-signal is economically invalid.

Grouped interpretation:original five miss episodes form **two forensic connected price sequences**:four early UP misses in one suspicious-fragmentation component,one08:38 DOWN miss in another. Original validation remainsfive misses/75%;grouping does not supply a corrected recall or new GT.

## GT conflicts and candidate arbitration population audit

Denominators exclude warmup:86400 eligible minutes per calibration asset,43200 per validation asset. Conflict means simultaneously active opposing raw directions,not every sequential reversal.

| Role | Asset | GT conflict minutes/rate | GT immediate switches | Switch at/after conflict | Starts at/after conflict | Candidate mixed minutes/rate | Candidate reversals | Lower-rule conflict switches | R1/R2 overriding opposite R3–R9 minutes |
|---|---|---|---:|---|---|---|---:|---:|---:|
|CALIBRATION|BNB|0/0.0000%|0|0/0|0/0|0/0.0000%|0|0|0|
|CALIBRATION|BTC|0/0.0000%|0|0/0|0/0|0/0.0000%|0|0|0|
|CALIBRATION|ETH|0/0.0000%|0|0/0|0/0|0/0.0000%|0|0|0|
|CALIBRATION|SOL|0/0.0000%|0|0/0|0/0|0/0.0000%|2|0|0|
|VALIDATION|BNB|0/0.0000%|0|0/0|0/0|0/0.0000%|0|0|0|
|VALIDATION|BTC|0/0.0000%|0|0/0|0/0|0/0.0000%|0|0|0|
|VALIDATION|ETH|1/0.0023%|0|0/0|0/0|1/0.0023%|2|0|1|
|VALIDATION|SOL|2/0.0046%|9|2/2|2/2|7/0.0162%|3|0|7|

Candidate lifecycle event distribution (episode starts = ACTIVATION+REVERSAL;RULE_ADDED stays within lifecycle):
- CALIBRATION BNB:ACTIVATION=4,REVERSAL=0,RULE_ADDED=0;starts=4.
- CALIBRATION BTC:ACTIVATION=2,REVERSAL=0,RULE_ADDED=0;starts=2.
- CALIBRATION ETH:ACTIVATION=12,REVERSAL=0,RULE_ADDED=2;starts=12.
- CALIBRATION SOL:ACTIVATION=13,REVERSAL=2,RULE_ADDED=5;starts=15.
- VALIDATION BNB:ACTIVATION=1,REVERSAL=0,RULE_ADDED=3;starts=1.
- VALIDATION BTC:ACTIVATION=2,REVERSAL=0,RULE_ADDED=0;starts=2.
- VALIDATION ETH:ACTIVATION=6,REVERSAL=2,RULE_ADDED=8;starts=8.
- VALIDATION SOL:ACTIVATION=7,REVERSAL=3,RULE_ADDED=11;starts=10.

Calibration haszero conflicting GT/rule minutes across all four assets. Validation hasone GT/rule conflict minute for ETH;SOL has2 GT conflict minutes but7 candidate mixed-rule minutes. All7 SOL mixed minutes occur at05:14,05:16,05:20,05:21,05:22,05:23,05:24,and R1 is lowest/selected DOWN. They suppress opposing R5/R7 evidence rather than cause candidate flips:lower-number conflict-caused reversal count iszero. Therefore arbitration is rare globally but concentrated exactly around these misses;do not describe R1/R2 as frequently overriding across the whole dataset.

GT family order and candidate rule number are explicit reproducibility priorities,but the frozen docs supply no market-calibrated justification for treating first family/lowest rule as stronger evidence. R1 DOWN can coexist with a rebound R5 UP because their windows/definitions differ. The order answers a software tie-break question,not a proven market-direction hierarchy.

## Family-level validation recall and R2 overlap

Family assignment uses final episode type union;families overlap,so totals are not independent counts. Onset-family presence is separately retained.

| Asset | FAST | MEDIUM | REVERSAL | BREAKOUT | VOL | Single/multi/conflict-family episodes |
|---|---|---|---|---|---|---|
|BNB|1/1 (100.0000%)|0/0 (N/A)|1/1 (100.0000%)|0/0 (N/A)|1/1 (100.0000%)|0/1/0|
|BTC|1/1 (100.0000%)|1/1 (100.0000%)|0/0 (N/A)|0/0 (N/A)|1/1 (100.0000%)|0/1/0|
|ETH|5/5 (100.0000%)|2/2 (100.0000%)|2/2 (100.0000%)|0/0 (N/A)|3/3 (100.0000%)|2/3/1|
|SOL|7/7 (100.0000%)|2/3 (66.6667%)|3/7 (42.8571%)|0/0 (N/A)|2/3 (66.6667%)|8/5/4|

Aggregate family recall:
- FAST_MOVE:14/14;recall=100.0000%.
- MEDIUM_MOVE:5/6;recall=83.3333%.
- REVERSAL:6/10;recall=60.0000%.
- BREAKOUT:0/0;recall=N/A.
- VOL_EXPANSION:7/8;recall=87.5000%.

R2/FAST_MOVE mechanical overlap:

| Asset | FAST-containing episodes | FAST active at onset | R2 exact-onset hit | R2 pre-onset hit | Only other-rule hit | FAST misses |
|---|---:|---:|---:|---:|---:|---:|
|BNB|1|0|0|0|1|0|
|BTC|1|1|1|0|0|0|
|ETH|5|3|3|0|2|0|
|SOL|7|5|3|2|2|0|

Across validation:14 FAST-containing episodes,9 FAST active at onset;7 R2 exact-onset hits,2 R2 pre-onset hits,5 only-other-rule hits,zero FAST misses. This quantifies strong mechanical overlap and shows aggregate misses came from other-family/onset semantics. No conclusion of independent100%FAST detector effectiveness follows from equal4%thresholds.

## Three late<=5min misses

| Miss onset | First same-direction event | Delay | Rules/reason | What changed |
|---|---|---:|---|---|
|05:20 UP|05:25 UP|300s|R5 / REVERSAL|R5 already active;opposing R1 stops being raw-active.|
|05:24 UP|05:25 UP|60s|R5 / REVERSAL|Same05:25 event;not a second independent alarm.|
|08:38 DOWN|08:43 DOWN|300s|R3,R9 / ACTIVATION|4h return and relative4h cross their fixed8%/6pp gates.|

At05:20,R1 return15m=−5.8552%,R5 drawup=6.8627%. At05:24,R1=−4.0086%,R5=6.7373%. At05:25,R1=−2.0412% (below3%abs),while R5 remains6.6803%;the removal of the lower-numbered opposing condition lets the candidate reverse and activate R5. No new UP threshold crossing is needed,so these are arbitration delays rather than R5 sensitivity gaps.

At08:38,GT MEDIUM return4h=−7.2118%,below candidateR3=8%;relative4h=−5.2008pp,belowR9=6pp. At08:43 these become−8.2825% and−6.2006pp. There were no candidate conditions in the original onset[-15min,0]main window;this is a genuine fixed-threshold timing gap under the chosen GT and hit-window definitions. It does not establish which threshold should replace V2 or that onset should be retimed.

05:14 and05:16 do not get<=5min late credit;their UP evidence is present but suppressed during the main windows. No late credit was added to original recall.

## P0–P4 diagnostics, not winner selection

All policies keep the same thresholds and exposure;they alter GT arbitration and candidate arbitration together,so both numerator and denominator change. These are correlated diagnostics on already exposed data,not new held-out validation,and no policy was selected as winner.

| Role | Policy | Episodes/hits/misses | Diagnostic recall | Candidate events/episodes | Combined p95/day | Suspicious reentries |
|---|---|---:|---:|---:|---:|---:|
|CALIBRATION|P0|25/25/0|100.0000%|40/33|5|0|
|CALIBRATION|P1|25/25/0|100.0000%|40/33|5|0|
|CALIBRATION|P2|25/25/0|100.0000%|40/33|5|0|
|CALIBRATION|P3|25/25/0|100.0000%|40/33|5|0|
|CALIBRATION|P4|25/25/0|100.0000%|40/31|5|0|
|VALIDATION|P0|20/15/5|75.0000%|43/21|15|7|
|VALIDATION|P1|16/13/3|81.2500%|43/21|15|2|
|VALIDATION|P2|16/15/1|93.7500%|45/23|15|2|
|VALIDATION|P3|16/15/1|93.7500%|45/23|15|2|
|VALIDATION|P4|11/10/1|90.9091%|41/16|16|0|

Per-asset policy counts and stability (direction flips count consecutive episode-direction changes,including episodes separated by inactivity;GT immediate-switch counters above are narrower):

| Role/policy | Asset | GT episodes/hits | Candidate events/episodes | Median/p95 duration seconds | <5m/<10m | Flips/hour | Reentry<=5/10/30m | Fragmentation ratio |
|---|---|---:|---:|---|---|---|---|---|
|CALIBRATION/P0|BNB|2/2|4/4|1890.0/1980|0/0|0|0/0/0|0|
|CALIBRATION/P0|BTC|2/2|2/2|2520.0/3180|0/0|0.0006944444444444444444444444444|0/0/0|0|
|CALIBRATION/P0|ETH|10/10|14/12|1920.0/4140|0/0|0.002777777777777777777777777778|0/0/0|0|
|CALIBRATION/P0|SOL|11/11|20/15|2520.0/3600|0/0|0.004861111111111111111111111111|0/0/0|0|
|CALIBRATION/P1|BNB|2/2|4/4|1890.0/1980|0/0|0|0/0/0|0|
|CALIBRATION/P1|BTC|2/2|2/2|2520.0/3180|0/0|0.0006944444444444444444444444444|0/0/0|0|
|CALIBRATION/P1|ETH|10/10|14/12|1920.0/4140|0/0|0.002777777777777777777777777778|0/0/0|0|
|CALIBRATION/P1|SOL|11/11|20/15|2520.0/3600|0/0|0.004861111111111111111111111111|0/0/0|0|
|CALIBRATION/P2|BNB|2/2|4/4|1890.0/1980|0/0|0|0/0/0|0|
|CALIBRATION/P2|BTC|2/2|2/2|2520.0/3180|0/0|0.0006944444444444444444444444444|0/0/0|0|
|CALIBRATION/P2|ETH|10/10|14/12|1920.0/4140|0/0|0.002777777777777777777777777778|0/0/0|0|
|CALIBRATION/P2|SOL|11/11|20/15|2520.0/3600|0/0|0.004861111111111111111111111111|0/0/0|0|
|CALIBRATION/P3|BNB|2/2|4/4|1890.0/1980|0/0|0|0/0/0|0|
|CALIBRATION/P3|BTC|2/2|2/2|2520.0/3180|0/0|0.0006944444444444444444444444444|0/0/0|0|
|CALIBRATION/P3|ETH|10/10|14/12|1920.0/4140|0/0|0.002777777777777777777777777778|0/0/0|0|
|CALIBRATION/P3|SOL|11/11|20/15|2520.0/3600|0/0|0.004861111111111111111111111111|0/0/0|0|
|CALIBRATION/P4|BNB|2/2|4/4|1890.0/1980|0/0|N/A|0/0/0|None|
|CALIBRATION/P4|BTC|2/2|2/2|2520.0/3180|0/0|N/A|0/0/0|None|
|CALIBRATION/P4|ETH|10/10|14/12|1920.0/4140|0/0|N/A|0/0/0|None|
|CALIBRATION/P4|SOL|11/11|20/13|2520.0/3600|0/0|N/A|0/0/0|None|
|VALIDATION/P0|BNB|1/1|4/1|5160.0/5160|0/0|0|0/0/0|0|
|VALIDATION/P0|BTC|1/1|2/2|3900.0/3900|0/0|0|0/0/0|0|
|VALIDATION/P0|ETH|5/5|16/8|1920.0/16020|0/0|0.001388888888888888888888888889|1/1/1|0.2|
|VALIDATION/P0|SOL|13/8|21/10|240.0/4440|7/8|0.0125|7/8/8|0.6153846153846153846153846154|
|VALIDATION/P1|BNB|1/1|4/1|5160.0/5160|0/0|0|0/0/0|0|
|VALIDATION/P1|BTC|1/1|2/2|3900.0/3900|0/0|0|0/0/0|0|
|VALIDATION/P1|ETH|5/5|16/8|1920.0/16020|0/0|0.001388888888888888888888888889|1/1/1|0.2|
|VALIDATION/P1|SOL|9/6|21/10|1920.0/4440|2/3|0.006944444444444444444444444444|2/3/4|0.4444444444444444444444444444|
|VALIDATION/P2|BNB|1/1|4/1|5160.0/5160|0/0|0|0/0/0|0|
|VALIDATION/P2|BTC|1/1|2/2|3900.0/3900|0/0|0|0/0/0|0|
|VALIDATION/P2|ETH|5/5|16/8|1920.0/16020|0/0|0.001388888888888888888888888889|1/1/1|0.2|
|VALIDATION/P2|SOL|9/8|23/12|1920.0/4440|2/3|0.006944444444444444444444444444|2/3/4|0.4444444444444444444444444444|
|VALIDATION/P3|BNB|1/1|4/1|5160.0/5160|0/0|0|0/0/0|0|
|VALIDATION/P3|BTC|1/1|2/2|3900.0/3900|0/0|0|0/0/0|0|
|VALIDATION/P3|ETH|5/5|16/8|1920.0/16020|0/0|0.001388888888888888888888888889|1/1/1|0.2|
|VALIDATION/P3|SOL|9/8|23/12|1920.0/4440|2/3|0.006944444444444444444444444444|2/3/4|0.4444444444444444444444444444|
|VALIDATION/P4|BNB|1/1|4/1|5160.0/5160|0/0|N/A|0/0/0|None|
|VALIDATION/P4|BTC|1/1|2/2|3900.0/3900|0/0|N/A|0/0/0|None|
|VALIDATION/P4|ETH|5/5|16/6|1920.0/16020|0/0|N/A|0/0/0|None|
|VALIDATION/P4|SOL|4/3|19/7|4200.0/7200|0/0|N/A|0/0/0|None|

P0 SOL median duration4min,p95=74min;7 episodes<5min and8<10min;8/13 same-direction reentries<=30min;7 suspicious fragmentation edges. P1–P3 SOL median32min with2 short<5min episodes and2 suspicious edges. P4 hasone market envelope per active price sequence:SOL4 envelopes,median70min,p95=120min;single-direction flips/fragmentation ratio are N/A. Its directional sub-signal transitions are28 including warmup;do not treat zero forced envelope flips as proof of directional stability.

Original five misses under each diagnostic:

| Original onset | P0 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|
|2026-08-22 05:14|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|DIRECTION_CHANGED_OR_ABSENT;mapped_hit=None;original_time_hit=False|DIRECTION_CHANGED_OR_ABSENT;mapped_hit=None;original_time_hit=False|DIRECTION_CHANGED_OR_ABSENT;mapped_hit=None;original_time_hit=False|MERGED_NO_NEW_ONSET;mapped_hit=True;original_time_hit=False|
|2026-08-22 05:16|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=True;original_time_hit=True|RETAINED_ONSET;mapped_hit=True;original_time_hit=True|MERGED_NO_NEW_ONSET;mapped_hit=True;original_time_hit=True|
|2026-08-22 05:20|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=True;original_time_hit=True|RETAINED_ONSET;mapped_hit=True;original_time_hit=True|MERGED_NO_NEW_ONSET;mapped_hit=True;original_time_hit=True|
|2026-08-22 05:24|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|MERGED_NO_NEW_ONSET;mapped_hit=False;original_time_hit=False|MERGED_NO_NEW_ONSET;mapped_hit=True;original_time_hit=True|MERGED_NO_NEW_ONSET;mapped_hit=True;original_time_hit=True|MERGED_NO_NEW_ONSET;mapped_hit=True;original_time_hit=True|
|2026-08-22 08:38|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|RETAINED_ONSET;mapped_hit=False;original_time_hit=False|

P1 removes some new UP onsets but leaves three diagnostic misses,showing inertia alone is not a detector fix. P2/P3 retain05:16 and05:20 as detected UP onsets and merge05:24 into the05:20 episode;08:38 still misses. P4 merges four early UP misses into an already-detected envelope,but at05:14 there is still no original-timestamp UP event;envelope recall can hide directional omissions. No policy comparison promotes original V2 FAIL to PASS.

## Statistical sensitivity

| Population | Original hits/episodes | Wilson95% interval | One/two more misses | One/two resolved misses | Max misses at90% |
|---|---:|---|---|---|---:|
|SOL|8/13|35.5229%–82.2903%|53.8462%/46.1538%|69.2308%/76.9231%|1|
|aggregate|15/20|53.1299%–88.8138%|70.0000%/65.0000%|80.0000%/85.0000%|2|

Aggregate one-miss sensitivity=5pp;SOL=7.6923pp. Unchanged90%gate requires>=18/20 aggregate and>=12/13SOL. Wilson intervals are conditional binomial explanations assuming sufficiently independent episodes;the observed clustered fragmentation undermines that assumption,so they do not quantify calibrated market-performance certainty. No threshold or90%gate was lowered.

## Implementation, design and threshold findings

No implementation violation was identified in the observed canonical reconstruction:all P0 metrics/state hashes and calibration feature hashes match;priority and lifecycle behavior reproduce frozen docs. This is scoped evidence,not proof that all V2 behavior is bug-free. Theoretical unobserved paths are outside this forensic conclusion.

**EVALUATION_MODEL_REDESIGN_REQUIRED:**first-family arbitration and immediate opposite splitting can turn shared retrospective high/low geometry into repeated directional episodes. Simultaneous conflict counts miss same-family sign dominance flips. Episode envelope/onset/family attribution and independent-sequence semantics need a new explicit version before another evaluation.

**CANDIDATE_DIRECTION_MODEL_REDESIGN_REQUIRED:**lowest-number arbitration masks already-active opposite R5/R7 at seven critical SOL minutes. The design has no supported general rule that short-window R1 should erase rebound evidence from R5/R7. A redesign may retain contradictory sub-signals or use an explicitly justified arbitration;these diagnostics do not choose it.

Threshold-related evidence:only08:38 is supported as a genuine raw-threshold gap in these five main windows (primaryE,secondaryA). The four early misses already have UP candidate conditions,so reducing thresholds indiscriminately cannot explain their failure and could increase load.

## What is not proven and next architecture options

No V3 effectiveness,unseen-policy generalization,investment correctness,production readiness or live reliability is proven. No AUDIT/HYPE/new history/hidden interval was used,no optimizer/grid expansion,no config/winner selection. Original75%validation remains unchanged. DiagnosticP2/P3 aggregate93.75%uses16label episodes and SOL8/9(<10);P4 uses11envelopes. Comparing these percentages as if all used the original20episodes would be wrong.

OPTION A — retain a single-direction episode and redesign arbitration. Benefit:smallest semantic surface and simpler consumer contract. Risk:still compresses multiscale contradictory evidence;normalized scores/votes can be unstable or dimensionally misleading. Refreeze direction precedence,ties,inertia,reset,reversal/onset and candidate event semantics. Reserve a genuinely unused official historical interval or prospective forward interval before evaluating;do not reuse August validation or this forensic data as hidden validation.

OPTION B — separate market episode envelope from directional sub-signals. Benefit:preserves selloff/rebound evidence without forcing each sign into an independent market episode. Risk:envelope recall may conceal missing directional response,as05:14 demonstrates;need separate direction-specific timeliness/coverage metrics and downstream lifecycle contract. Refreeze envelope admission/reset,sub-signal identity,timing/matching and directional score gates. New hidden interval and one-shot evaluation required;no future data opened here.

OPTION C — volatility/asset-normalized move architecture. Benefit:may align material scale and candidate sensitivity across assets. Risk:more degrees of freedom,causal normalization/warmup/leakage concerns,and it does not by itself fix direction arbitration. Refreeze normalization/reference windows,global versus asset parameters,GT independence,finite search/objective and onset contract. Use a new untouched historical or future interval;threshold normalization is not implemented or searched here.

No option was selected or implemented. Any future V3 must use a new interval that participated in none of V1,V2 or this forensic run;August01–31 is now exposed,latest AUDIT remains sealed for V2/V3 diagnostics,and future hidden data is not downloaded or opened in this phase.

## Tests, resources and external-action boundaries

Baseline255 tests passed before forensic on Python3.14/3.12.27 new forensic tests,total282;final full runs:282 passed in1.89s(Python3.14.6),282 passed in1.74s(Python3.12.14),zero failed/skipped. compileall,dependency checks,diff check and scoped credential-pattern scan passed. Original tests/source unchanged. Tests cover conflicting families/rules,UP→DOWN→UP,suspicious boundaries,deterministic taxonomy/policies,P4envelope/concurrent states,audit symlink access denial,V3/frozen-write/network denial,winner identity and Wilson sensitivity.

Forensic process wall=93.49912516599579s;CPU=93.308071s;peak RSS=388.23MiB. New evidence approximately5261823bytes;no new SQLite/history download. All protected88files unchanged after run,and original28private Phase3 evidence files hash-verified unchanged at final handoff. Real Gmail sends0;automation mutations0;private GitHub runtime writes0;market live WS0;launchd0;portfolio0. GitHub feature commits/pushes are the only authorized remote writes.

**PHASE_3B_R_DIAGNOSIS_COMPLETE; V3_NOT_AUTHORIZED; PHASE_3C_NO_GO; PRODUCTION_NO_GO.** Report/code commit and feature force-with-lease push complete this scope;stop awaiting review.
