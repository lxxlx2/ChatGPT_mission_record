# Crypto Mission Performance Tracker

Updated: 2026-09-27 03:40 Asia/Bangkok
Timezone: Asia/Bangkok

## Accounting rules
- internal bridge / chain / venue movements are not PnL;
- realized PnL needs verified cost, proceeds and fees;
- private venue positions use latest USER_CONFIRMED state plus public marks only as an estimate;
- spoof/unpriced tokens and NFTs without executable value are excluded;
- the wallet contains later capital additions, so current NAV cannot be compared directly with the original $300 mission amount.

## Current active-position mark-to-market

### GSTOCK / BNB Chain
- cost: **30.00474761 USDC**, before BNB gas
- received: **1183.5967247073113 GSTOCK**
- average cost: **~0.0253504821**
- current Alchemy mark: **~0.0241192634**
- current value: **~28.5475 USD**
- unrealized PnL: **~-1.4573 USD (-4.86%)**, before BNB gas
- status: **FILLED / ACTIVE**

### PONS Robinhood spot
- quantity: **54.799953441979625 PONS**
- verified cost: **35.291194 USDG**
- current Alchemy mark: **~0.6247626394**
- current value: **~34.2370 USD**
- unrealized mark PnL: **~-1.0542 USD (-2.99%)**

Existing TP/downside orders remain USER_CONFIRMED. No outgoing PONS transfer is reflected in the fresh balance.

### PONS Binance futures
Latest USER_CONFIRMED private position:
- LONG 64 PONS @ **0.6250**
- isolated 3x
- TP 0.668 / 0.704 / 0.739
- stop 0.498

Current Binance public mark: **0.6256**.
Assuming no manual private-account change:
- estimated current uPnL: **~+0.0384 USDT**
- latest screenshoted realized PnL reference: **~-0.13 USDT**
- estimated trade-result subtotal using those two fields: **~-0.0916 USDT**, before any new funding/fees

No stored TP or stop was crossed in the public mark path after the latest private screenshot.

### XRP / Variational — CLOSED
USER_CONFIRMED:
- former LONG: 77.12 XRP @ **1.55589**
- stored stop/lower bound: **1.5140**
- lower bound was hit and the position closed
- remaining venue balance was withdrawn and converted back to Solana USDC

Gross reference if the full position closed exactly at 1.5140:
- **~-3.23 USDC** before funding, fees, spread and stop slippage

Exact realized venue PnL remains **UNRESOLVED** until execution/funding/fee data is available.
Status: **CLOSED / STOP_LOSS_TRIGGERED**.

### PAID / Solana
- DIRECT_CHAIN quantity: **947.685473 PAID**
- quantity unchanged from the verified purchase
- verified total purchase budget: **~50 USD-equivalent** including route cost from the prior execution record

Public PAID price references are currently inconsistent. Recent Pump results imply roughly **9.9-18.0 USD** for the current balance.
Indicative PAID mark PnL range: **~-40.1 to -32.0 USD**.
Keep this as MARKET_ESTIMATE until an execution-grade quote is reconciled.

### e/acc / Solana
- DIRECT_CHAIN current balance: **0 e/acc**
- another **180.916452 e/acc** has left the wallet since the 14:18 snapshot, confirmed by finalized chain data

Historical verified first-sale phase:
- original budget: about **40 USD**
- first major sale cash recovery: about **55.68 USD**
- recorded first-phase network/priority fees: about **0.57 USD**
- first-phase net cash recovery: about **55.11 USD**
- cash recovered above original budget at that stage: about **+15.11 USD**, while residual e/acc still remained

Fresh finalized RPC now shows the e/acc position fully exited (**0 balance**). Later sale legs are still not fully reconciled to exact proceeds/fees, so total e/acc realized PnL remains **UNRESOLVED** even though there is no residual token exposure.

### KARDASHEV / Solana
- DIRECT_CHAIN remaining: **4,103.186501 KARDASHEV**
- original capital: **20.00 USDC**
- total sold: **14,691.367277**
- gross routed exit proceeds observed: **~0.245051759 SOL**
- total listed network fees across entry + three exits: **~0.001318107 SOL**
- fresh PumpSwap reserves: **35,838,316.721083 KARDASHEV / 610.290341092 SOL**
- at SOL ~120.01, current pool-implied price: **~0.00204365 USD**
- remaining mark value: **~8.3855 USD**
- current total-position PnL reference: **~+17.64 USD**, after listed network fees
- status: **PRINCIPAL_RECOVERED / PROFIT_POSITION**

This mark uses current pool reserves and current SOL/USD reference. Chain quantities are authoritative; USD PnL remains a market-value estimate.
## Partial PnL view
- GSTOCK: ~-1.46
- PONS spot: ~-1.05
- PONS futures: ~-0.09 including latest screenshoted realized reference
- XRP Variational: **closed**, gross stop reference ~-3.23 before private venue fees/funding/slippage
- KARDASHEV: ~+17.64 current total-position estimate
- PAID: ~-40.1 to -32.0 indicative

The old active-position subtotal is superseded because XRP is now closed and Solana/e/acc state changed.

Using only the previous partial framework and replacing the prior XRP mark estimate (~-1.32) with the gross stop reference (~-3.23), the comparable partial reconciled range would shift by about **-1.91 USD**, to roughly **-13.2 to -5.1 USD**. This remains provisional because later e/acc proceeds and exact Variational fees/funding are not fully reconciled.

This is not the final Mission PnL. It excludes:
- later e/acc sale proceeds/fees;
- current residual e/acc executable value;
- historical SHART/CRED closed-sleeve reconciliation;
- UNICRED/Credits/Fresh INK executable values;
- exact current Binance/Variational funding and private account fees.

## Current capital distribution
- canonical on-chain stablecoins: **728.600906 USDC**
- strict directly priced on-chain liquid NAV: **~797.29 USD**, excluding PAID/e/acc and unpriced NFTs/points
- indicative direct-chain liquid NAV after adding PAID/e/acc public-reference ranges: roughly **807-816 USD**
- Binance PONS isolated margin reference: ~13.20 USDT plus current estimated uPnL

Prior all-tracked liquid-value range is stale after the Variational closeout and Solana USDC increase; recompute on the next full cross-chain mark refresh.

## Reserved / structural capital
- JUMP reserve: 400 USDC on Ethereum.
- ETH conditional reserve: 100 USDC accounting target; no live ETH Mission trade confirmed.
- opportunity capital is already distributed across Solana/BNB/Robinhood/private venues and must not be double-counted.
- separate ~500 USD-equivalent low-risk interest bucket remains outside speculative Mission accounting.


## Capital-location update — 2026-09-27 03:40

USER_CONFIRMED:
- apart from the Binance PONS perpetual and the combined earn bucket, tracked capital is on-chain;
- former 500 + 98 earn labels are consolidated to **598 USD-equivalent**;
- Variational XRP is closed and withdrawn;
- no active Variational derivative exposure remains.

Fresh DIRECT_CHAIN:
- Solana USDC: **328.018516**
- e/acc: **0**
- KARDASHEV: **0**
- PAID: **947.685473**
- total canonical on-chain stablecoins: **728.600906 USDC**

Fresh public Binance PONS mark: **0.63688970**.
If the latest user-confirmed 64-PONS long @ 0.6250 remains unchanged:
- estimated uPnL: **~+0.7609 USDT** before fresh funding/fees.

The **598 USD-equivalent earn bucket is capital, not PnL**, and is tracked as one combined off-chain balance.
