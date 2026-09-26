# Crypto Hourly Collector Spec

Updated: 2026-09-26 12:05 Asia/Bangkok
Timezone: Asia/Bangkok

Goal: provide reliable rolling material for the daily report and Mission without making every hourly run an exhaustive internet crawl.

## Start heartbeat

First persistent action:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS.md`

Initial status:
`run_status: in_progress`

Create it before broad search. Path collision gets one retry with a new second-level timestamp.

Every run must later finalize the same audit.

## Core scan every hour

Always collect:
- BTC / ETH / SOL market state;
- high-volume / high-move crypto outliers using bulk market data;
- major exchange / security / protocol incident headlines;
- any deadline-sensitive event already carried from recent research.

Use concise paraphrase. Do not copy long source text or exploit instructions.

## Rotating discovery shard

To keep the hourly task reliable, run one discovery shard per hour while core risk scanning remains hourly.

Using Asia/Bangkok hour modulo 3:

### Shard 0: social / NFT
- English X discovery;
- Reddit discovery;
- NFT / digital art / open edition / mint / claim / drop.

### Shard 1: ecosystem / primary market
- TGE / ICO / public sale / unlock;
- chain/ecosystem launches;
- RWA / stablecoin / AI-Crypto / DePIN;
- prediction-market changes.

### Shard 2: flow / macro / security depth
- whale / exchange flow;
- derivatives / basis / liquidation anomalies;
- cross-chain / cross-platform spread candidates;
- regulation / macro / geopolitical crypto impact;
- deeper security follow-up.

Over any 3 consecutive successful hourly runs, all discovery categories are covered.

If a critical breaking event appears outside the current shard, follow it immediately.

## Candidate budget

Save at most 8 material candidates.

Prioritize:
1. security / solvency;
2. BTC/ETH/SOL and highly liquid market regime changes;
3. deadline-sensitive opportunities;
4. meaningful primary-market/TGE;
5. strong NFT/new-ecosystem candidates;
6. other research.

No material update is a valid successful result.

## Research file

Write:
`crypto-daily/research/YYYY-MM-DD/HHMMSS.md`

Keep it compact:
- topic
- why_it_matters
- confirmed_facts
- market_snapshot
- source_names/domains
- confidence
- unresolved
- discovery_shard

If a normal write is blocked, retry once using this compact schema.

If the compact write still fails:
- do not keep expanding/rephrasing indefinitely;
- record research_write_failed in the existing audit;
- finalize the run partial_failure;
- next hour continues independently.

## 09:00, 10:00, 11:00

The existing automation follows `REPORT_SPEC.md` and `DELIVERY_RUNBOOK.md`.

At 09:00 delivery is higher priority than new research.

At 10:00 and 11:00 missing-delivery recovery is higher priority than ordinary collection.

At other hours, do not read the full REPORT_SPEC unless required.

## Final audit

Finalize the skeleton with:
- run_status
- core_market_scan
- security_scan
- discovery_shard
- x_scanned / reddit_scanned / nft_scanned as applicable
- candidate_count
- research_path
- research_write
- source_failures
- tool_errors

Normal no-result/no-update is not a failure.

Single source failure does not abort the run.

Temporary failure never disables or pauses the automation.
