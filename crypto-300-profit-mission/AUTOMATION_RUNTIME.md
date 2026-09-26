# $300 Crypto Automatic Runtime

Updated: 2026-09-27 01:20 Asia/Bangkok
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
- while XRP Variational event position is active: read `watchlists/xrp-bitget-hacker-flow.md` and check the stored attacker-flow baselines/triggers
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

Required hourly, in this order:
1. PONS/XRP/ETH/BTC public market facts used by stored rules;
2. active XRP Bitget attacker-flow lane when the XRP event position is active;
3. recent Crypto Daily research;
4. one Binance USD-M bulk Monster screen plus bounded shortlist deep-check;
5. active-asset wallet telemetry only: Robinhood PONS, BNB GSTOCK, Solana active Token-2022/meme balances; other chain inventory is slower cadence;
6. persist final/final-retry immediately.

Do not run optional launch/NFT/FOMO fallback searches unless recent Crypto Daily research contains a plausible candidate.
Full Ethereum/Base/Unichain/Ink inventory reconciliation is 3-hour cadence or event-driven, not an hourly blocker.

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


## Notification behavior

Use `docs/MONITORING/NOTIFICATION_POLICY.md`.

Default is silent.

Monitoring/runtime/source/audit problems are GitHub-only and do not generate Gmail or ChatGPT alerts.

Send Gmail + ChatGPT only for substantive stored-rule events:
- stop/TP/event threshold crossing;
- qualified stored ETH setup;
- materially changed WATCH;
- Monster IGNITION / relevant EXHAUSTION;
- material real-asset wallet anomaly;
- material active-position security/deadline event;
- verified launch/NFT/TGE opportunity timing/eligibility change;
- scheduled 19:29 Monster factual daily summary;
- XRP Bitget ATTACKER_MAJOR_MOVE / ATTACKER_LIQUIDITY_RISK / BITGET_REPLENISHMENT / FLOW_REGIME_CHANGE from the dedicated watchlist.

When no substantive alert is required, return an empty user-visible response.


## Monster persistence and delivery

Read/write `state/monster-squeeze-v2.1-current.md`.

For a newly confirmed STRUCTURAL_CANDIDATE or PRESSURE candidate, persist:
- first_seen;
- setup_price;
- current_state;
- expiry at 7 days under frozen V2.1.

Do not retroactively invent setup_price.

Every Monster lane final must record:
- universe count;
- shortlist;
- structural_count;
- pressure_count;
- ignition_count;
- exhaustion_count;
- data gaps.

At 19:29 the daily summary must actually be delivered by Gmail + ChatGPT, subject:
`Crypto Mission｜Monster V2.1 日汇总｜YYYY-MM-DD`

Before sending, dedupe Gmail Sent by exact subject.
If the 19:29 run is missed, the first later successful run must send the missed summary once and record Gmail message_id/readback plus `monster_daily_summary_recovery: true`.
Generating a summary in the audit without sending it does not satisfy the daily-summary requirement.
