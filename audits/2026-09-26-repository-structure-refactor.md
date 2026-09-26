# Repository Structure Refactor Audit

Date: 2026-09-26
Scope: Crypto repository organization
Automation creation: none

## Objective

Make the repository human-readable using five content classes while preserving the three existing Crypto monitoring tasks.

## Structural changes completed

Added:
- `docs/REPOSITORY_STRUCTURE.md`
- `docs/MONITORING/README.md`
- `research/README.md`
- `research/MIGRATION_MAP.md`
- `research/projects/README.md`
- `research/tokens/README.md`
- `research/memes/README.md`
- `research/nfts/README.md`
- `research/projects/jump/jump-legion-sale.md`
- `research/nfts/jack-credits/jack-credits-nft-position.md`
- `crypto-300-profit-mission/300-profit-mission-strategy.md`
- `crypto-300-profit-mission/positions/README.md`
- `crypto-300-profit-mission/watchlists/README.md`
- `crypto-300-profit-mission/runs/README.md`

Updated human-facing titles:
- `positions/credits.md`
- `positions/jump.md`
- `strategy.md`

Updated navigation/current architecture:
- root `README.md`
- `docs/ACTIVE_AUTOMATIONS.md`
- `docs/CRYPTO_AUTOMATION_ARCHITECTURE.md`
- `crypto-300-profit-mission/README.md`
- `crypto-300-profit-mission/MISSION_SPEC.md`

## Monitoring-safety controls

Intentionally unchanged:
- automation IDs
- automation count
- task root directories
- three `AUTOMATION_RUNTIME.md` paths
- `portfolio/current.md`
- `performance/current.md`
- `state/latest.md`
- `health/current.md`
- historical automatic audit filenames
- existing operational `positions/jump.md` path
- existing operational `positions/credits.md` path
- existing legacy `strategy.md` path

The new research copies do not replace operational monitor authorities yet.

No bulk run-history rename was performed.

## Compatibility stage

The repository is now in a staged migration:
- clearer human research paths exist;
- old operational paths remain valid;
- deletion of compatibility aliases is deferred until real automatic runs verify there are no hidden path dependencies.

## Required validation

Existing tasks only:
- Crypto Daily :00
- TGE :14
- $300 Mission :29

A path migration is not considered complete until relevant real automatic runs continue to produce final audits.
