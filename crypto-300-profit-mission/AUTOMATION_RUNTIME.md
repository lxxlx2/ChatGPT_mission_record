# $300 Crypto Automatic Runtime

Updated: 2026-09-26 18:34 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_TELEMETRY

Authority for the existing :29 task.

## Audit
The append-only final audit is canonical.

At run start, make one best-effort attempt to create:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-start.md`.

If the start write is blocked by the runtime safety layer, record `start_audit_warning` and continue all factual lanes. A missing start marker alone must not abort or downgrade an otherwise complete run.

End by creating matching append-only `HHMMSS-final.md`.

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
