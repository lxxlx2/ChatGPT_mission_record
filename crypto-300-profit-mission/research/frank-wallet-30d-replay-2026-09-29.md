# Frank wallet 30D replay / notification test

Date: 2026-09-29 Asia/Bangkok
Wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

## Data caveat

This is a first-pass 30D replay using public wallet analytics snapshots plus direct-chain spot checks. It is not a full transaction-by-transaction historical simulator. Exact first-hour sell ratio, hourly VWAP drift and liquidity-at-alert require a deeper tick-level reconstruction.

Public 30D snapshot:
- realized PnL around +$439.8K
- ROI around +10.6%
- 661 trades
- win rate around 37.3%
- 142 tokens
- PAID best trade around +$290.4K
- CTO worst trade around -$33.6K

## Positive controls

### STONK
- lifetime snapshot around 4 days
- buys/sells 82 / 44
- bought around $808.75K at avg $0.028265
- sold around $1.07M at avg $0.033688
- realized around +$246.89K (+30.53%)
- classification: strong conviction-position positive control
- expected behavior under revised rules: WATCH on first qualifying hour, possible FORMAL_ENTRY only on the next hourly observation if still materially held/accumulating and price remains within -8%/+10% of Frank VWAP.

### CATE
- lifetime snapshot around 16 days
- buys/sells 70 / 14
- bought around $160.33K at avg $0.026404
- sold around $276.71K at avg $0.046297
- realized around +$117.78K (+73.46%)
- classification: strong conviction-position positive control
- expected behavior: same two-cycle persistence requirement as STONK.

### PAID
- public 30D wallet analytics records about +$290.39K from 12 trades
- classification: likely conviction candidate, but aggregate source does not expose the exact early accumulation path
- no claim that the exact historical FORMAL_ENTRY timestamp has been reconstructed yet.

## Negative / noise controls

### biketyson
- recent OKX snapshot showed about 7 buys / 8 sells in ~6 minutes
- classification: rapid round-trip / execution behavior
- expected result: HFT_EXECUTION, silent.

### Single-buy positions
Examples in recent snapshots include GJIMV2, RCPEPER, AIRDROP and RDLONG with one buy and no sell at the snapshot.
- expected result: no FORMAL_ENTRY even if later profitable
- rationale: one-off bets are deliberately outside the copied-conviction strategy.

### Wrapped majors / execution instruments
WBTC showed very high turnover (133 buys / 94 sells in roughly a day in one snapshot).
- expected result after revision: excluded from Frank formal alerts as a wrapped major / likely execution instrument.

## Potential false-positive controls

### CTO
- around 31 buys / 21 sells
- holding window shown around several hours
- final realized loss around -20%
- old rule could have been too permissive if early buys happened quickly.
- revision: require two consecutive hourly observations, retain >=70% of WATCH-cycle peak exposure, and current executable price must stay inside -8% / +10% of Frank VWAP.

### HYPE
- around 25 buys / 12 sells over ~2 days
- final loss was relatively small in the observed snapshot
- can still pass conviction logic if its early accumulation met all gates; this is acceptable because the filter reduces noise, it cannot guarantee profitable outcomes.

## Rule changes after replay

1. Removed the one-cycle fast path.
2. FORMAL_ENTRY now requires WATCH in one hourly run and persistence into the next hourly run.
3. Frank must retain >=70% of WATCH-cycle peak exposure or add more.
4. Current executable price must be within -8% / +10% of Frank VWAP.
5. Stablecoins, wrapped majors and obvious execution/hedging instruments are excluded.
6. Formal email must include why the signal passed, do-not-chase price and invalidation conditions.
7. WATCH/HFT/NO_ACTION remain silent.

## Gmail delivery test

User explicitly requested a one-off delivery test, overriding the normal no-test-email rule for this manual validation only.

Subject:
`[300 Mission][TEST][Frank] 30D历史回放 | STONK`

Gmail message id:
`1a0e9cef52df82b1`

Readback:
`PASS`

The message was found with SENT and INBOX labels and its full plain-text body was read back successfully.

Operational automation remains configured to send no test mail; only FORMAL_ENTRY / FORMAL_EXIT will email going forward.
