# Frank 30D Full Replay Acceptance Spec

Status: OPEN / NOT YET COMPLETED
Date: 2026-09-29
Wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

## Why this file exists

The current file `research/frank-wallet-30d-replay-2026-09-29.md` is explicitly a first-pass snapshot analysis. It does not satisfy the user's requirement to run the complete 30-day transaction history.

This acceptance spec is the definition of done for that requirement.

## Definition of done

The replay is complete only when:
1. every wallet signature in the 30D window has been paginated and accounted for;
2. every active DEX/aggregator swap has been classified chronologically;
3. every traded token has a per-token event timeline;
4. the historical hourly :29 observer has been simulated without future information;
5. all WATCH / PRECONFIRM / SUSPECTED_CONVICTION / HFT / STALE / rejected outcomes are emitted;
6. every filtered/rejected token that later achieved >=3x is explicitly listed;
7. every entry-like signal has T0, alert time, latency, Frank buy/VWAP, alert price, forward returns, MFE, MAE and Frank later sell/exit timing where data exists;
8. the requested high-market-cap/high-liquidity subset is separately summarized;
9. a single aggregate report states total active tokens -> WATCH -> PRECONFIRM -> SUSPECTED_CONVICTION -> HFT -> STALE -> rejected -> later >=3x misses;
10. the full replay has no hidden pagination/provider gap. Any unavailable block is a test failure, not an assumed no-action period.

## Historical delivery behavior

Historical replay is audit-only:
- no Gmail per historical token;
- no live stage mutation;
- no live cursor mutation.

Only the final aggregate replay report is stored.

## Current status

OPEN.

Existing artifacts are methodology/positive controls only and MUST NOT be described as a completed exhaustive 30D backtest.


## User-requested real Gmail delivery override — 2026-09-29 14:50 Asia/Bangkok

The user explicitly requested that this exhaustive historical replay send **real Gmail** for every historical Frank signal that would have met the current live notification rules. This overrides the earlier audit-only/no-email clause for this replay only.

Recipient:
`lxx.run688@gmail.com`

Delivery granularity:
- one email per distinct token/episode/stage that historical replay proves would have triggered;
- stages: PRECONFIRM, SUSPECTED_CONVICTION, PRECONFIRM_CANCELLED, FORMAL_EXIT;
- deduplicate by deterministic event key + exact subject;
- historical WATCH / HFT / STALE / rejected remain silent;
- do not mutate the live Frank cursor or live stage state.

Subjects:
- `[300 Mission][回测][Frank][预确认] <TOKEN> | YYYY-MM-DD HH:mm BKK`
- `[300 Mission][回测][Frank][疑似] <TOKEN> | YYYY-MM-DD HH:mm BKK`
- `[300 Mission][回测][Frank][撤销] <TOKEN> | YYYY-MM-DD HH:mm BKK`
- `[300 Mission][回测][Frank][EXIT] <TOKEN> | YYYY-MM-DD HH:mm BKK`

The first screen of every email must be immediately readable and in this order:
1. `结论`: stage + historical replay;
2. `代币`: verified ticker/name;
3. `CA`: full Solana mint;
4. `Frank开始买入`: T0 Bangkok time;
5. `Frank本轮买入`: USD amount + BUY count;
6. `Frank卖出`: USD amount + SELL count up to alert;
7. `回测报警时间`: simulated next :29 observation / exact qualifying time;
8. `报警延迟`: T0 -> alert;
9. `Frank VWAP / 报警价 / 偏差`;
10. `分类原因`: concise pass/fail gates;
11. `当时策略动作`: PRECONFIRM uses 观察仓 0-15 USD; SUSPECTED uses 20-30 USD initial test under stored rules;
12. `禁追价格 / 失效条件`;
13. `后来结果`: 1h/3h/6h/24h/7d, MFE/MAE where available, clearly separated as hindsight;
14. relevant transaction hashes.

Do not bury CA, buy amount, time or classification below narrative text.

Every sent replay email requires Gmail message-id readback and persistence in the final replay report.
