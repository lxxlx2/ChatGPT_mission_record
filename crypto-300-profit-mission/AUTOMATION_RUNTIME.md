# $300 Crypto Automatic Runtime

Updated: 2026-09-26 15:10 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_TELEMETRY

Authority for the existing :29 scheduler.

## Append-only audit

At start create:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-start.md`

with only:
- run_time
- automation_id
- mode: FACTUAL_TELEMETRY
- run_status: started

Do not update the start file.

At end create:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-final.md`

with:
- run_time
- automation_id
- run_status
- wallet_reads
- threshold_checks
- discovery_checks
- alerts
- optional_cache_write_status
- source/tool errors

A run is complete only when the final file exists.

## Factual checks

Every hour:
- Ethereum USDC + native ETH
- Solana USDC + SOL + Token-2022 e/acc + PAID
- BNB Chain USDC + BNB + GSTOCK
- Robinhood Chain ETH + PONS
- read current PONS, XRP, ETH and JUMP state files only as needed to compare current facts with already stored thresholds
- read at most two newest Crypto Daily research files
- one bulk Binance futures universe screen for Monster V2.1, with at most 8 deep-check candidates
- launch/NFT/FOMO discovery only from recent research or a compact fallback if research is stale
- every 3 hours: UNICRED/Credits slow lane
- 19:29: Monster factual daily summary

Ink current factual context:
- Fresh INK commemorative NFT #372 already exists
- Tydro Ink Points are present
- the separately discussed target NFT remains pending until a new mint/transfer or user confirmation

## Notifications

Only for a new factual change under an already stored rule:
- stored threshold crossed
- changed WATCH
- Monster state transition
- wallet anomaly
- security/deadline event
- monitor health gap/lane failure
- 19:29 summary

No new trade plan, size, leverage, order change or capital allocation is generated automatically.

## Persistence

Append-only start/final audits are canonical for automatic runs.

Mutable files such as `portfolio/current.md`, `state/latest.md` and `health/current.md` are optional caches during automation. Do not require or repeatedly retry them. If a material wallet change is detected:
- record the new factual values in the final audit;
- attempt at most one cache update when appropriate;
- cache-write failure does not downgrade a completed factual run;
- never lose the final audit because a mutable-file update failed.

Temporary failures never disable/pause the task.
No Chinese-language websites as evidence.
