# $300 Crypto Mission Operational Layer

This directory is the operational state and monitoring layer for the Crypto Mission.

Long-form human research is organized separately under:
- `research/projects/`
- `research/tokens/`
- `research/memes/`
- `research/nfts/`

Repository organization and migration safety:
- `docs/REPOSITORY_STRUCTURE.md`

## Scheduled authority

Existing task:
- `$300 Crypto资产状态监控`
- hourly at :29 Asia/Bangkok
- 19:29 same task also performs the Monster factual daily summary

Automatic runtime authority:
- `AUTOMATION_RUNTIME.md`

The scheduled task should not depend on human-facing research paths unless the runtime explicitly says so.

## Operational files

- `MISSION_SPEC.md`: global Mission policy and authority map
- `RUNBOOK.md`: richer manual/interactive execution reference
- `portfolio/current.md`: current capital distribution
- `performance/current.md`: PnL/accounting state
- `state/latest.md`: latest combined state
- `health/current.md`: monitor health
- `positions/`: active position/plan authorities
- `watchlists/`: compact machine watchlists/models
- `runs/`: immutable audit history
- `signals/`: stored factual signals
- `reports/`: Mission reports

Historical/background strategy:
- `300-profit-mission-strategy.md`
- `strategy.md` remains a temporary compatibility copy during migration validation

## Compatibility mappings

JUMP:
- human-facing research: `research/projects/jump/jump-legion-sale.md`
- operational compatibility authority: `positions/jump.md`

Jack / Visualize Value Credits:
- human-facing research: `research/nfts/jack-credits/jack-credits-nft-position.md`
- operational compatibility authority: `positions/credits.md`

Keeping those operational paths during the first migration stage protects existing monitor references.

## Audit naming

Current automatic convention:
- `runs/YYYY-MM-DD/HHMMSS-start.md`
- `runs/YYYY-MM-DD/HHMMSS-final.md`

Older `HHMMSS.md`/JSON records remain immutable.

A scheduler timestamp alone is not success. The final audit is the canonical proof of a completed automatic run.

## Scope rule

Mission operational files answer:
- what is held now;
- what stored threshold/order/deadline exists;
- what the monitor should check;
- what factual state changed.

Long-form explanation, due diligence and historical research should move toward the appropriate `research/` category.
