# PONS Position

Updated: 2026-09-26 13:46 Asia/Bangkok

## Binance PONSUSDT perpetual — USER_CONFIRMED

Latest screenshots: 2026-09-26 13:45 Asia/Bangkok.

Position:
- LONG
- isolated 3x
- quantity: **64 PONS**
- entry: **0.6250**
- hard stop: **Mark Price <= 0.4980**
- stop order: market, reduce-only, **100% position**
- liquidation reference from prior 12:58 screenshot: **0.4293629**

The prior averaging bids are canceled:
- 0.5850: canceled
- 0.5450: canceled

### Current futures take-profit orders

All are market take-profit / reduce-only:

| Trigger mark | Quantity | Share of 64 PONS | Screenshot est. PnL |
| --- | ---: | ---: | ---: |
| 0.6680 | **25 PONS** | **39.0625%** | +1.07 USDT |
| 0.7040 | **22 PONS** | **34.3750%** | +1.73 USDT |
| 0.7390 | **16 PONS** | **25.0000%** | +1.82 USDT |

Total TP coverage: **63 PONS = 98.4375%**.

Important:
- **1 PONS (1.5625%) is not covered by the three TP orders.**
- the 0.4980 stop is still 100%, so it protects any residual that remains open.
- if the intent is to fully exit the futures position through take-profits, the last TP should eventually cover the remaining 17 PONS rather than 16 PONS, or the residual must be managed separately.
- automation must not modify the order automatically.

## Robinhood Chain spot sleeve — DIRECT_CHAIN + USER_CONFIRMED ORDERS

Canonical PONS contract:
`0x39dbed3a2bd333467115de45665cc57f813c4571`

Fresh Alchemy wallet read around 2026-09-26 13:46:
- wallet PONS balance: **54.799953441979625 PONS**
- native gas: **0.000825190918816326 ETH**
- no outgoing PONS transfer has occurred since the acquisition swap.

The PONS remains in the wallet while the OKX DEX conditional/limit orders are open; the order state itself is USER_CONFIRMED from screenshots.

Verified acquisition leg:
- 2026-09-26 12:58:38 Asia/Bangkok
- input: **35.291194 USDG**
- output: **54.799953441979625 PONS**
- token acquisition rate: **~0.64400044 USDG/PONS**

### Current spot take-profit orders — USER_CONFIRMED

| Trigger | PONS amount | Screenshot est. USDG received |
| --- | ---: | ---: |
| **0.668** | **11.0** | **7.30 USDG** |
| **0.704** | **16.4** | **11.48 USDG** |
| **0.739** | **16.4** | **12.06 USDG** |
| **0.845** | **11.0** | **9.25 USDG** |

Total TP quantity: **54.8 PONS**, effectively the full 54.79995344-PONS wallet balance subject to platform rounding.

Estimated total USDG if all four TP orders execute as shown: **~40.09 USDG**.

### Current spot downside trigger orders — USER_CONFIRMED

| Trigger | PONS amount | Screenshot est. USDG received |
| --- | ---: | ---: |
| **0.598** | **27.39** | **16.30 USDG** |
| **0.575** | **27.39** | **15.67 USDG** |

Together they cover **54.78 PONS**, effectively the whole current spot sleeve.

Operational caveat:
- these stop quantities are fixed amounts, while the TP orders also reference the same PONS balance;
- if one or more TP orders execute first and price later falls, the remaining stop quantities can exceed the then-current wallet balance;
- after any spot TP execution, the remaining downside trigger quantities should be reviewed/resized to the actual remaining PONS balance;
- do not treat an insufficient-balance failure of a later trigger as a new market signal.

If price falls directly before any TP fills, the two current downside triggers are internally consistent: roughly half at 0.598 and the other half at 0.575.

## PONS sleeve accounting

Original sleeve: about 50 USDT-equivalent.

Current structure:
- Binance futures: 64-PONS long, 3x isolated, entry 0.6250.
- Robinhood Chain spot: 54.799953441979625 PONS.
- Robinhood Chain gas: 0.000825190918816326 ETH.

Do not combine spot mark value and futures notional as profit. Exact sleeve PnL must account for:
- futures realized/unrealized PnL;
- funding/fees;
- spot USDG cost basis;
- spot execution fees/slippage;
- withdrawal/gas acquisition costs.

## Monitoring

FACTUAL_RULE_MONITOR should check:
1. futures mark against 0.668 / 0.704 / 0.739 TP triggers and 0.498 stop;
2. whether the futures position remains USER_CONFIRMED at 64 PONS until a newer private screenshot/source exists;
3. Robinhood PONS wallet balance and native ETH gas;
4. spot TP/downside trigger execution evidence through wallet balance/transfers plus user-confirmed order UI;
5. after any spot TP fill, flag `REVIEW_REQUIRED` because downside trigger quantities may need resizing;
6. PONS funding/OI/rapid-move/security/liquidity state.

No automatic order creation/modification/reallocation.

## 2026-09-26 16:33 factual refresh

DIRECT_CHAIN Robinhood:
- PONS balance remains **54.799953441979625**
- Alchemy market reference: **~0.6247626394 USD**
- mark value: **~34.2370 USD**
- verified cost remains 35.291194 USDG
- spot mark PnL: **~-1.0542 USD (-2.99%)**
- no balance reduction is visible, so there is no chain evidence that a spot TP/downside order executed.

Binance public market:
- PONSUSDT mark: **0.6256**
- latest private state remains USER_CONFIRMED LONG 64 @ 0.6250
- the public mark path after the latest screenshot did not reach 0.668 TP or 0.498 stop
- implied uPnL if the private position is unchanged: **~+0.0384 USDT**
- exact private position/account state still requires Binance account readback or a newer user screenshot.
