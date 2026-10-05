# Frozen PRICE_FEATURE_V1 — 2026-09-30, before first replay

Arithmetic uses Decimal precision 34, ROUND_HALF_EVEN. Input prices are decimal strings; no binary float threshold comparisons. Time is UTC integer milliseconds aligned to 60,000. A bar represents [open_time, open_time+60,000); close_time is exclusive end. Only closed bars enter features. Received/source timestamps are provenance, never return-window selectors.

return_N = close(t)/close(t-N)-1 for N=5,15,60,240,1440 minutes. Require N+1 consecutive closed bars, no skipped minutes. Gap resets the window; affected features unavailable until warmup. BTC relative returns require BTC features at exactly the same close time; absence means unavailable, never stale carry-forward.

high_24h/low_24h = max(high)/min(low) of 1440 prior bars [t-1440,t-1], excluding current. Distances = close/high-1 and close/low-1 respectively, unavailable until 1441 contiguous bars. reversal_15m = max((max(high[t-14:t])-close)/max(high[t-14:t]), (close-min(low[t-14:t]))/min(low[t-14:t])). This is a magnitude, not a directional judgement; requires 15 contiguous bars.

realized_vol_5m = sqrt(sum(ln(close_i/close_(i-1))^2)) for the five minute returns ending at t. Six contiguous closes required. trailing_24h_vol_median = median of 1440 prior minute-end realized_vol_5m values, excluding current. Every sample uses the same five-minute log-return formula. Requires 1446 contiguous bars (1440 valid prior samples plus the current sample). Zero median makes R7 unavailable; it does not imply an infinite expansion.

R6 requires current and immediately previous closed sample each to exceed its own causal prior-24h high by >=1%, or fall below its own causal prior low by >=1%. Reference windows move each minute and exclude the evaluated bar. Both samples must be contiguous; direction must match. This explicitly uses independent causal references, not future extrema or a retrospective fixed level.

PRICE_RULE_V1 thresholds remain exactly R1 |15m|>=.03, R2 |1h|>=.05, R3 |4h|>=.08, R4 |24h|>=.12, R5 reversal>=.04, R6 as above, R7 vol>=3*median and |5m|>=.02, R8 non-BTC |relative1h|>=.04, R9 non-BTC |relative4h|>=.06. Rule output is only raw evidence. Thresholds cannot be changed from replay findings.

One candidate per asset/closed end/rule set; subsequent bars retain new identities, including sustained hits. Canonical payload uses Decimal strings and causal bar-end timestamps. unavailable features are null. Only fully warmed, gap-free samples with aligned BTC features for non-BTC can emit a formal candidate; no provisional bar can emit one. This strict admission is independently measured by ground truth, including any warmup suppression.
