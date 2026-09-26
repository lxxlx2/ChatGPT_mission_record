# Crypto Hourly Collector Spec

Mode: FACTUAL_NEWS_COLLECTOR

Updated: 2026-09-27 01:20 Asia/Bangkok
Timezone: Asia/Bangkok

Goal: provide reliable rolling material for the daily report and Mission without making every hourly run an exhaustive internet crawl.

## Start / final audit

The automatic scheduler uses `AUTOMATION_RUNTIME.md`.

Each run is append-only:

Start:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS-start.md`
with `run_status: started`.

Final:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS-final.md`
with the completed status and lane results.

Do not update the start file. A final file is the proof of completion.

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

If the normal research write is blocked:
1. retry once at `HHMMSS-retry.md` using the compact schema;
2. if that also fails, embed a compact `research_payload` plus material candidates directly in the final/final-retry audit;
3. finalize partial_failure, but preserve enough content for the 09:00 report to recover the missed hour.

The 09:00 report reads both research files and final audits when a research gap exists.

## 09:00, 10:00, 11:00

The existing automation follows `REPORT_SPEC.md` and `DELIVERY_RUNBOOK.md`.

At 09:00 delivery is higher priority than new research.

At 10:00 and 11:00 missing-delivery recovery is higher priority than ordinary collection.

At other hours, do not read the full REPORT_SPEC unless required.

## Final audit

Create the append-only final file with:
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

Normal no-result/no-update is healthy.

Single source failure does not abort the run.

Temporary failure never disables or pauses the automation.

## Runtime-policy boundary

This hourly collector is factual research only.

It may:
- retrieve public market/news/official-source facts;
- calculate descriptive market statistics;
- save compact research/audit files;
- identify topics that deserve later human review.

It must not:
- recommend a personalized trade;
- invent entry/exit/stop/leverage/position size;
- tell the user to buy/sell/short/long;
- execute or prepare transactions;
- reallocate the user's capital.

Candidate labels in this collector mean research priority only. Investment/action decisions belong to interactive chat or a separately authorized rule monitor.

The first GitHub skeleton audit is intentionally content-neutral and must be attempted before reading other project files or starting external research.


## Success classification

Normal absence of news is not a source failure.

Examples that are healthy:
- no fresh authoritative security incident found
- no material candidate found
- a discovery category is not due in the current rotating shard
- X/Reddit/NFT fields are not_due outside their shard

Use `source_failures` / `tool_errors` only for actual request, access, parsing, provider or persistence errors.

If core scan + scheduled shard + research write + audit finalization all succeed and there is no real tool/access error, final status should be `success`, even when the factual result is "no update".
