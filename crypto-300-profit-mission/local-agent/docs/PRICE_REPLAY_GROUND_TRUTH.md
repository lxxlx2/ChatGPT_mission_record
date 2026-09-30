# Frozen PRICE_GT_V1 — before first candidate replay, 2026-09-30

Labels are objective samples computed on the same closed canonical timeline but independent of candidate output. They are frozen before download/replay results. Each evaluable sample can have GT1–GT5; report both per-label and union recall. Incomplete input/warmup is reported unavailable, never counted as a negative label.

GT1: |rolling 1h return| >=4%. GT2: |rolling 4h return| >=7%. GT3: local15m reversal magnitude >=5%. GT4: >=1.5% outside causal prior24h extrema, same direction at three consecutive completed samples, each with its own causal reference. GT5: realized5m vol >=4*prior24h same-scale median, positive median, and |5m return|>=2.5%.

Hit: any raw candidate at the label's timestamp or in its preceding 15 minutes for the same asset. No future candidate credit. Lead = label time minus earliest qualifying candidate in that trailing15m window (nonnegative seconds); misses remain explicit. Report exact-sample recall additionally so a broad lead window is visible. Ground truth counts are evaluated only after canonical warmup; label unavailability counts are separate.

Evaluation gate frozen before results: NEEDS_CALIBRATION if union recall <90% with >=10 labelled samples, or median candidates/day >60 per asset, or p95/day >180 per asset, or combined complete-day candidates exceed960 (hourly input capacity40 ×24, before other sources). These are evaluation flags, not permission to retune PRICE_RULE_V1. Empty ground truth means recall N/A, not100%.

Daily bins are UTC dates. Rate/count summary uses the fixed30d evaluation period; partial first/last dates are reported separately from complete-day median/p95/max. Rule overlap counts every pair hit in one candidate. Clustering reports consecutive hit runs, candidates within15m, per-asset/day concentration. Noise review set is deterministic: earliest examples per rule plus samples from the maximum-count day, with feature evidence and no invented investment judgement. Missed moves list earliest samples per label. These are precision/noise proxies, not true trade-outcome precision.

If these frozen gates fail, report PRICE_RULE_V1=NEEDS_CALIBRATION, keep thresholds unchanged, stop escalation to further live/production work and await review. HYPE available-history metrics stay separate and always FORWARD_DATA_ACCUMULATING; full30d is not claimed.
