# $300 Crypto Automatic Runtime

Updated: 2026-09-26 20:35 Asia/Bangkok
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
- stored PONS/XRP/ETH threshold-state comparisons
- JUMP stored sale/deadline/gas state only; do not query a public JUMP market symbol
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


## Required vs optional lanes

Required hourly:
- PONS/XRP/ETH/BTC public market facts used by already stored rules;
- recent Crypto Daily research;
- Monster Binance Futures factual state;
- critical-wallet telemetry using fresh per-chain reads where supported;
- final audit persistence.

Optional enrichment:
- Binance Alpha availability;
- slow NFT/points enrichment outside its cadence;
- noncritical presentation/cache writes.

An unavailable optional enrichment is `optional_unavailable` and does not downgrade the run.

JUMP is a sale/project reserve, not a required public market symbol. Outside a known participation/deadline window, record `JUMP_check: not_due`. During a due window, check official sale/deadline/gas facts.

## Wallet fallback and classification

Read critical wallets per chain rather than one aggregate call.

Preferred:
- Alchemy/direct RPC for supported chains;
- Blockscout for supported EVM fallback;
- direct Solana RPC for SOL/SPL/Token-2022.

If one chain remains unavailable, record that chain only as unavailable.
If all wallet providers fail but the other required market/Monster lanes complete, use `partial_success`, not `partial_failure`.

## Final persistence fallback

At completion:
1. try `HHMMSS-final.md`;
2. if persistence fails, retry once using `HHMMSS-final-retry.md` with a compact audit.

Final persistence is attempted before optional cache updates.
