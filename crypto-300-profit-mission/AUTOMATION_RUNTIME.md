# $300 Crypto Automatic Runtime

Updated: 2026-09-27 12:25 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_TELEMETRY

Authority for the existing :29 task.

## Mission scope

Core Mission goal:
- starting asset set = **300 USD cash principal + original six Credits NFTs**
- target = **3,000 USD-equivalent Mission net liquidation value**

Current original Credits holdings:
- #23042
- #23232

The other four original Credits are historical sold assets/provenance.

Private Binance inventory authority:
- combined earn bucket = **598 USD-equivalent**
- PONSUSDT perpetual = the only tracked active Binance trading position
- do not invent or carry forward any other Binance spot/futures asset without a newer USER_CONFIRMED source.

The 598 earn bucket is tracked for asset completeness and remains outside speculative Mission performance unless provenance is explicitly reclassified.

## Audit

The mandatory automatic-run artifact is:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-final.md`

Fallback:
`HHMMSS-final-retry.md`

A scheduler trigger is not proof of success.

A manual reconciliation file is not automatic-run proof.

## Required hourly lanes

Run in this bounded order:

1. **Stored-rule market facts**
   - PONS public mark/funding
   - ETH stored setup facts
   - BTC stored regime facts

2. **Recent Crypto Daily input**
   - read newest two available research/final artifacts
   - no broad duplicate news scan

3. **Active wallet telemetry**
   - Robinhood PONS + native gas
   - BNB GSTOCK + native BNB
   - Solana USDC/SOL + Token-2022 active balances including PAID/e/acc/KARDASHEV

4. **Monster V2.1**
   - one Binance USD-M bulk screen
   - bounded shortlist
   - deep-check **maximum 3 symbols per hourly run**
   - if a deep source is unavailable, record the gap and continue; do not loop on fallbacks

5. **Persist final immediately**
   - write final/final-retry before any optional work

## Hard reliability guardrail

If any required lane has a tool/source error:
- record the affected lane as unavailable/partial;
- skip expensive fallback loops;
- do not start optional enrichment;
- immediately persist a compact final/final-retry with completed lanes, failed lanes, data gaps and alert state.

A partial factual run with honest unavailable fields is preferable to a missing audit.

No optional state/cache update may run before final persistence.

## Optional / slower work

Only after a final/final-retry exists:
- launch/NFT/FOMO enrichment when upstream evidence contains a plausible candidate;
- UNICRED / Credits market enrichment every 3 hours;
- full Ethereum/Base/Unichain/Ink/Arbitrum inventory reconciliation every 3 hours or event-driven;
- presentation/cache updates.

Optional failure never downgrades a completed final.

## Credits lane

Every full reconciliation must retain the two DIRECT_CHAIN Credits:
- #23042
- #23232

The original six remain Mission provenance:
- #21646, #21753, #22857, #23042, #23232, #23328

Do not value 0.25/0.40 ETH listing asks as executable NAV.

## JUMP

JUMP is a stored sale/project reserve, not a public market symbol.

Outside a known participation/deadline window:
- record `JUMP_check: not_due`.

During a due window:
- check official sale/deadline/gas facts.

No automatic application or transaction.

## Wallet fallback and classification

Preferred:
- Alchemy/direct RPC for supported chains;
- Blockscout for supported EVM fallback;
- direct Solana RPC for SPL + Token-2022.

Read critical chains independently.

If one chain is unavailable, mark only that chain unavailable.

If market/Monster lanes complete and a wallet provider fails, use `partial_success`, not a fabricated current balance.

Never reuse an old balance and label it current.

## Notifications

Default: silent.

Infrastructure/runtime/source/audit/health problems:
- GitHub audit only
- no Gmail
- no ChatGPT alert

User-visible Gmail + ChatGPT only for a new substantive stored-rule event:
- position stop/TP/event threshold crossing;
- stored ETH setup becomes qualified;
- materially changed WATCH;
- Monster IGNITION or relevant EXHAUSTION;
- material real-asset wallet anomaly;
- material security/solvency/deadline event affecting active capital;
- verified launch/NFT/TGE timing or eligibility change;
- scheduled 19:29 Monster factual daily summary.

No unchanged WATCH/NO_ACTION/ordinary volatility notification.

## Monster persistence

Authority:
`state/monster-squeeze-v2.1-current.md`

For newly confirmed STRUCTURAL_CANDIDATE/PRESSURE:
- first_seen
- setup_price
- current_state
- 7-day expiry

Do not retroactively invent setup_price.

Every automatic final records:
- universe_count
- shortlist
- structural_count
- pressure_count
- ignition_count
- exhaustion_count
- data_gaps

## 19:29 Monster summary

The 19:29 run must actually deliver the factual daily summary by Gmail + ChatGPT.

Subject:
`Crypto Mission｜Monster V2.1 日汇总｜YYYY-MM-DD`

Before sending:
- dedupe Gmail Sent by exact subject.

If missed:
- first later successful same-date run sends once;
- record `monster_daily_summary_recovery: true`;
- record Gmail message_id/readback.

## XRP / Variational

CLOSED.

Do not run XRP/Bitget attacker-flow, XRP TP/SL or Variational monitoring as a Mission hourly lane unless the user explicitly reactivates relevant exposure.


## Scheduler-survival override — 2026-09-27

Observed incident:
- automatic final/final-retry exists at 08:27;
- scheduler metadata later advanced through morning cycles;
- no 09:29, 10:29 or 11:29 completion audit was persisted.

Therefore the following rules override the earlier hourly ordering.

### Phase 0: attempt proof first

The first write action of every scheduled run is:
`crypto-300-profit-mission/runs/YYYY-MM-DD/HHMMSS-attempt.md`

Minimum fields:
- run_time
- automation_id
- status: started
- scheduled_cycle: :29

Only after this write should market/wallet/research tools be called.

The attempt file is diagnostic only. A final/final-retry remains completion proof.

### Phase 1: independent core lanes

Core lanes are independent. Failure in one lane must never cancel the remaining lanes.

Maximum critical work before final persistence:
1. PONS/BTC/ETH public facts, using bounded per-symbol calls;
2. active wallet telemetry for Robinhood PONS, BNB GSTOCK, Solana USDC/SOL + known active Token-2022 balances;
3. read one newest Crypto Daily research/final artifact.

For each lane:
- success -> record current data;
- tool/source error -> record `unavailable`;
- do not retry more than once;
- never reuse stale data as current.

After these three lanes, immediately create final/final-retry.

A complete audit with one or more unavailable lanes is `partial_success`.
Use `failed` only when no meaningful core lane completes or final persistence itself cannot be achieved.

### Phase 2: Monster and opportunity enrichment after core final

Hourly Monster scanning is enrichment and must not be able to erase core-run proof.

After the core final exists:
- every 3 hours, run one bounded Monster V2.1 universe screen;
- deep-check at most 3 candidates;
- persist Monster results separately to `state/monster-squeeze-v2.1-current.md` and/or a unique `HHMMSS-monster.md` audit;
- if IGNITION / relevant EXHAUSTION is confirmed, send the stored-rule alert.

At 19:29:
- Monster full screen + factual daily summary is required;
- if it cannot complete, the next successful run performs the existing missed-summary recovery.

On non-Monster hours:
- only refresh already persisted active Monster candidates when cheap;
- do not fetch the whole futures universe.

### Phase 3: slower enrichment

Only after core final:
- JUMP due-window checks;
- launch/NFT/FOMO;
- Credits/UNICRED;
- full cross-chain inventory;
- cache/state presentation updates.

No enrichment failure changes an already persisted core final.

### Final audit fields

Every core final/final-retry must contain:
- attempt_path
- market_lane
- wallet_lane
- crypto_daily_lane
- data_gaps
- substantive_event
- notification
- monster_due
- monster_status: pending_after_core / not_due / recovered_separately

This bounded architecture prioritizes durable monitoring proof while retaining Monster coverage on its own cadence.
