# Crypto Profit Mission Runbook

Updated: 2026-09-26 12:36 Asia/Bangkok
Timezone: Asia/Bangkok
Schedule: hourly at :29

Mode: FACTUAL_RULE_MONITOR

The scheduler gathers facts and evaluates stored rules. It does not originate new personalized trades.

## 0. Skeleton first

Before broad reads/searches:

1. get current Asia/Bangkok time;
2. create `runs/YYYY-MM-DD/HHMMSS.md`;
3. write:
   - run_time
   - automation_id
   - run_status: in_progress
   - mode: FACTUAL_RULE_MONITOR
   - phase: skeleton

If path collision occurs, retry once with a new second-level timestamp.

If skeleton creation fails, continue only far enough to attempt a compact health/error record. Never pause/disable the automation.

## 1. Minimal reads

After skeleton creation read:
- `MISSION_SPEC.md`
- `portfolio/current.md`
- `state/latest.md`
- `health/current.md`
- `positions/pons.md`
- `positions/xrp-variational.md`
- `positions/eth-conditional.md`
- `positions/jump.md`
- `watchlists/btc-regime-jasonleo.md`
- `watchlists/monster-squeeze-v2.1.md`

Read another file only when cadence/candidate requires it.

Do not bulk-read closed/history files.

## 2. Phase A: factual critical-risk checks

### Wallet / gas
Every hour:
- Ethereum canonical USDC + native ETH;
- Solana canonical USDC + native SOL;
- relevant known active liquid token balances.

Daily reconciliation adds Base, Unichain and Robinhood Chain.

Output only balance/current-state facts and material deltas.

### PONS
Read public Binance market data and compare it with stored PONS thresholds.

Allowed outputs:
- threshold not hit;
- stored threshold crossed;
- data unavailable.

Do not generate a new order, stop, target or size.

### XRP / Variational
Read public XRP price/derivatives/security data and compare with stored trigger rules.

Allowed outputs:
- stored TP/SL/event threshold crossed;
- rapid-move / OI / funding trigger crossed;
- relevant Bitget-event factual change;
- no trigger.

Do not infer private fill/PnL/order changes.

### ETH
Evaluate only the exact stored Setup A / Setup B / breakout conditions.

Output:
- qualified / not qualified / unavailable;
- which stored conditions passed/failed.

Do not invent a fresh ETH trade plan.

### BTC
Classify stored regime/risk conditions only.

### JUMP
Check:
- deadline proximity;
- authenticated term changes;
- reserve/gas readiness;
- predefined Sep-29 preflight when due.

No automated application or new allocation decision.

### Active-position security
Check material security/solvency/protocol events relevant to active positions.

After Phase A update the audit with factual lane status.

## 3. Phase B: bounded discovery

### Upstream input
Read at most the two newest `crypto-daily/research/` files from the previous 2 hours.

If no fresh research within ~90 minutes, do one compact fallback discovery pass.

### Monster V2.1
1. one bulk Binance USDⓈ-M universe snapshot;
2. Binance Alpha discovery when available;
3. merge carried candidates + SAGA;
4. shortlist at most 8 symbols;
5. detailed funding/OI/taker/top-trader/klines only for shortlist;
6. evaluate frozen V2.1;
7. record state transitions.

Automation output is classification only:
- STRUCTURAL_CANDIDATE
- PRESSURE
- IGNITION
- EXHAUSTION
- NO_STATE_CHANGE

No newly invented position size or trade instruction.

### Launch radar
Use upstream candidate first.
Deep-verify only actual candidates.
If one passes factual watch gates, emit:
`WATCH_CANDIDATE_REVIEW_REQUIRED`

Include facts, timing, identity, unresolved items and risk.
Do not include a new spend amount or buy instruction.

### NFT radar
Use:
- fresh upstream candidate;
- one primary discovery surface;
- fallback only if needed.

A qualified result is a factual WATCH for review, not an automated mint/buy recommendation.

### Robinhood/FOMO
Check current carried candidates / upstream evidence / calibration.

No candidate = checked_no_candidate.
No automatic entry recommendation.

## 4. Phase C: medium cadence

Only when Bangkok hour % 3 == 0, or a material event requires:
- UNICRED;
- Credits.

Otherwise:
`medium_lane: not_due`

## 5. Alert format

Send Gmail + ChatGPT only for a new factual trigger required by MISSION_SPEC.

Alert structure:
- trigger type;
- asset/project;
- current factual data;
- stored rule/threshold crossed;
- previous state -> current state;
- unconfirmed fields;
- invalidation/risk;
- `decision_status: REVIEW_REQUIRED` when user input is needed.

Do not include:
- newly invented buy/sell/short/long instruction;
- newly invented leverage;
- newly invented position size;
- automatic capital reallocation.

Existing user-set TP/SL/order levels may be quoted as stored facts.

Gmail failure does not stop audit finalization.

## 6. Current-state writes

Before updating mutable files, fetch latest SHA in the same run.

Update:
- `state/latest.md`
- `health/current.md`

Keep current files compact.

On SHA conflict:
- refetch;
- retry once;
- otherwise record failure and continue.

## 7. Always finalize

Best-effort finalize the same skeleton as:
- success
- partial_success
- partial_failure
- failed

Never intentionally leave `in_progress`.

Minimum final audit:
- Phase A lane statuses;
- wallet read status;
- upstream research freshness;
- Monster universe/shortlist/state counts;
- launch/NFT/FOMO status;
- medium lane status;
- alerts attempted/sent;
- state write;
- health write;
- exact tool/source errors.

If a discovery lane fails after critical checks completed, finalize partial rather than disappearing.

## 8. Health

- scheduler trigger without finalized audit = missing_audit;
- successful-run gap >90m = MONITOR_HEALTH_GAP on recovery;
- same mandatory lane unavailable twice consecutively = MONITOR_LANE_FAILURE;
- temporary failure never pauses/disables task.

## 9. Success

Success requires:
- skeleton created;
- each Phase A lane has checked/trigger/unavailable;
- Monster bulk screen has a status;
- launch/NFT/FOMO have status;
- state/health update completed;
- same audit finalized.

Scheduler metadata alone is never success.
