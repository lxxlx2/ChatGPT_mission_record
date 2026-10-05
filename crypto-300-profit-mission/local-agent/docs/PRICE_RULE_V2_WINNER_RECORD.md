# Unique calibration winner — before first validation open

V2_FREEZE_COMMIT: 15753ad1092cc2b1b9bd36270dd770916c50aec0.

Only CALIBRATION was passed to the optimizer. 324 configs evaluated;108 passed all frozen gates. Deterministic winner config_id251: R1=.03,R2=.04,R3=.08,R4=.14,R7_multiplier=3,R7_move=.02. Fixed R5=.04,R6 causal1%,R8=.04,R9=.06 unchanged. No per-asset parameters or severity tiers.

Winner rank components: minimum recall over qualifying assets=1;aggregate recall=25/25=1;combined p95/day=5;total candidate episodes=33;threshold lexicographic descending tie break in frozen order. No manual choice from leaderboard. This is a calibration result, not validation or a claim of independent100% detection coverage. R2 and FAST_MOVE share a4% numerical threshold; the episode and multi-family contract, operational-load gates and subsequent chronological validation are required, and sparse labels limit conclusions.

BTC2/2,ETH10/10,SOL11/11,BNB2/2 episode hits;BTC/BNB insufficient for per-asset recall qualification. Events2,14,20,4 respectively. Final candidate config and calibration leaderboard/results are committed together here, before any held-out data evaluation. V2_WINNER_COMMIT is the original commit adding config/price_rule_v2_candidate.json, checked by the validation reader. Existing winner/config/result can never be overwritten by a subsequent validation/audit selection.

First calibration execution completed324 scores but failed canonical JSON serialization before writing artifacts because cluster-count keys were integers. They were converted to strings, with no contract or parameter changes. Identical cached calibration reran and produced this winner. Batch/sparse and minute-by-minute candidate state/event hashes matched for the winner. Validation has not yet opened at this commit.
