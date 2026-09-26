# $300 Crypto Automatic Runtime

Updated: 2026-09-26 19:55 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_TELEMETRY

Authority for the existing :29 task.

## Audit

The only mandatory persistence artifact is:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-final.md`.

Do not require or attempt a start file in the automatic path. Older start files remain valid historical artifacts.

The final audit is the canonical proof of completion.

## Hourly factual lanes
- Ethereum USDC + ETH
- Solana USDC + SOL + Token-2022 e/acc + PAID
- BNB USDC + BNB + GSTOCK
- Robinhood ETH + PONS
- stored PONS/XRP/ETH/JUMP threshold-state comparisons
- newest two Crypto Daily research files
- Monster V2.1 factual market-state screen
- launch/NFT/FOMO candidate state
- UNICRED/Credits slow lane every 3 hours
- Monster factual daily summary at 19:29

Current corrections:
- GSTOCK is FILLED_ACTIVE; read positions/gstock-plan.md.
- Solana scans must include Token-2022.
- existing Ink #372 is separate from the still-pending target Ink NFT.

## Alerts
Only new factual state changes already covered by stored rules: threshold crossing, changed WATCH, Monster state transition, wallet anomaly, security/deadline event, lane/health gap, or scheduled Monster summary.

No automatic account/action changes.

## Persistence
Append-only final audit is canonical.
Mutable portfolio/state/health files are optional caches.
A cache-write failure cannot erase or downgrade an otherwise completed factual run.
Temporary failure never disables/pauses the task.
No Chinese-language websites as evidence.


## Missed 19:29 recovery

The 19:29 run is responsible for the Monster factual daily summary.

If the 19:29 final audit is missing, the first later successful run on the same Bangkok date must:
- run the normal hourly factual lanes;
- generate the missed Monster factual daily summary once;
- mark `monster_daily_summary_recovery: true`;
- never duplicate the summary if an earlier final audit already records it.
