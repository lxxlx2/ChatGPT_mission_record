# $300 Mission Three-Lane Baseline — 2026-09-29

Status: PRE-FIX BASELINE
Scope: Frank / Monster(meme) / NFT only

## Frank
Known failures:
- lane was added to runtime but multiple scheduled cycles persisted core success with `frank_lane_status: pending_after_core`;
- 12:33 returned `unavailable_source` even though direct Alchemy reads worked manually afterwards;
- live recovery later processed 30 signatures successfully, proving parser/source path can work;
- exhaustive 30D replay remains OPEN; current research file explicitly says first-pass/snapshot only.

Baseline:
- live cursor correctness: PARTIAL
- per-cycle mandatory completion: FAIL
- source fallback resilience: FAIL
- historical 30D recall proof: FAIL

## Monster / meme
Known failures:
- BTWUSDT was shortlisted, not deep-checked because max-3 budget was consumed, then disappeared because no durable deferred queue existed;
- anti-starvation queue was added later and BTW recorded as MISSED_ALERT control;
- current queue still contains old deferred candidates and the runtime budget clears them slowly;
- scans persist individual run artifacts, but there is no mandatory per-day coverage artifact proving full-universe screen -> shortlist -> deep-check -> deferred terminal accounting.

Baseline:
- full-universe bulk screen: PASS
- persistent setup state: PASS
- deferred fairness: PARTIAL
- silent-starvation prevention: PARTIAL
- daily coverage accounting: FAIL
- known BTW regression: historical FAIL / current rule patched but not fully regression-gated

## NFT
Known failures:
- watchlist says hourly discovery;
- Mission runtime places launch/NFT/FOMO in optional/slower enrichment after core final and only when upstream evidence already contains a plausible candidate;
- expected durable `radar/nft/YYYY/...` history does not exist;
- therefore zero NFT alerts cannot be interpreted as zero opportunities.

Baseline:
- hourly discovery execution proof: FAIL
- zero-candidate durable receipt: FAIL
- identity/security gate specification: PASS
- live current discovery proof: FAIL
- historical recall fixture suite: FAIL

## Overall
The prior runtime could report core success while one or more of these three priority opportunity lanes had not completed.

Pre-fix acceptance score:
- Frank: 2/6 effective controls pass
- Monster: 3/6 effective controls pass
- NFT: 1/7 effective controls pass

This file is baseline evidence only. It is not a live signal.
