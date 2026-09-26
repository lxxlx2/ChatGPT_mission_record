# Crypto Mission Performance Tracker

Updated: 2026-09-27 03:57 Asia/Bangkok
Timezone: Asia/Bangkok

## Core objective

Target: **3,000 USD-equivalent Mission net liquidation value**.

Starting asset set:
- **300 USD cash principal**
- **six Credits NFTs**: #21646, #21753, #22857, #23042, #23232, #23328

Current original-Credits state:
- held: **#23042, #23232**
- sold/transferred out: **#21646, #21753, #22857, #23328**
- gross matched sale/payment flows: **0.141165 ETH/WETH equivalent** before unresolved seller-side gas/fee reconciliation

The two remaining Credits are active Mission assets. Their 0.25 ETH and 0.40 ETH asks are not executable NAV.

## Performance rules

- External later deposits do not count as Mission profit.
- The 598 USD-equivalent Binance earn bucket is tracked as an off-chain asset bucket but stays outside speculative Mission performance unless provenance is explicitly reclassified.
- Internal bridge/venue transfers are not profit.
- Wallet balance alone is not PnL.
- Historical NFT proceeds are not added on top of current wallet balances.
- Private-venue state is USER_CONFIRMED.
- Unpriced NFTs/tokens stay outside strict liquid NAV.
- Mission target progress remains UNRESOLVED until capital provenance separates original Mission capital/proceeds from later additions.

## Current active-position marks

### GSTOCK / BNB Chain
DIRECT_CHAIN:
- quantity: **1183.5967247073113**
- verified USDC cost: **30.00474761**
- fresh price: **0.024642598080577366 USD**
- value: **~29.1669 USD**
- unrealized PnL: **~-0.8378 USD (-2.79%)**, before BNB gas
- status: **FILLED_ACTIVE**

### PONS / Robinhood spot
DIRECT_CHAIN:
- quantity: **54.799953441979625 PONS**
- verified cost: **35.291194 USDG**
- fresh price: **0.6268828643699188 USD**
- value: **~34.3532 USD**
- mark PnL: **~-0.9380 USD (-2.66%)**

No balance reduction is visible, so there is no direct-chain evidence that a stored spot TP/downside order executed.

### PONS / Binance futures
USER_CONFIRMED private position:
- LONG **64 PONS @ 0.6250**
- isolated 3x
- TP 0.668 / 0.704 / 0.739
- hard stop 0.498

Fresh public Binance mark: **0.62924862**.
If the private position is unchanged:
- estimated uPnL: **~+0.2719 USDT**
- exact margin/funding/fees remain unresolved without private account readback.

### PAID / Solana
DIRECT_CHAIN:
- **947.685473 PAID**

Connected price endpoint currently returns no price. Current value/PnL therefore remains **UNRESOLVED** rather than using a stale public range.

### Credits NFTs
DIRECT_CHAIN:
- **Credit #23042 owned**
- **Credit #23232 owned**

They are part of the Mission asset base. Current value is excluded from strict liquid NAV until an execution-grade bid/sale reference is obtained.

## Closed exposures

### XRP / Variational
- CLOSED after stored lower bound 1.5140 was hit.
- remaining venue funds were withdrawn to Solana.
- exact realized PnL remains UNRESOLVED until venue fees/funding/slippage are reconciled.

### e/acc
- DIRECT_CHAIN current balance: **0**
- fully exited.
- final realized PnL remains UNRESOLVED until all later sale legs are reconciled.

### KARDASHEV
- Token-2022 mint: `5wW9mhbwq1HTFh341iimpmrqBB4mfxdXiYhdYBL7hUnp`
- DIRECT_CHAIN current balance: **0**
- status: **CLOSED / FULLY EXITED ON-CHAIN**

The prior **4,103.186501 KARDASHEV** residual mark and **~+17.64 USD** marked total-position estimate are historical and must not appear in current active PnL. The final residual-sale proceeds still require reconstruction before final realized PnL is stated.

## Current liquid asset view

Fresh strict directly priced on-chain liquid NAV:
- canonical stablecoins: **728.600906 USD**
- native gas assets: **~62.8974 USD**
- GSTOCK: **~29.1669 USD**
- Robinhood PONS spot: **~34.3532 USD**

**Total: ~855.02 USD.**

This figure excludes PAID, Credits, UNICRED, Fresh INK, Tydro Points, pRCADE and unidentified/spam assets.

Binance off-chain inventory, USER_CONFIRMED:
- combined earn bucket: **598 USD-equivalent**
- PONS futures position only
- no other Binance assets/positions are tracked.

## Current partial active-trade PnL

Using only currently markable active positions:
- GSTOCK: ~-0.8378 USD
- PONS spot: ~-0.9380 USD
- PONS futures estimated uPnL: ~+0.2719 USDT

Comparable subtotal: **~ -1.50 USD**, before futures funding/fees and excluding PAID/NFTs.

This is not total Mission PnL.

## Goal progress

Status: **UNRESOLVED / provenance reconciliation required**.

Do not calculate “855 / 3000” or include the 598 earn bucket as progress until later capital additions are separated from the original 300 USD + six-Credits Mission capital and the four Credits sale proceeds are fully mapped.
