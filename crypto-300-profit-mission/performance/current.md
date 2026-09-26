# Crypto Mission Performance Tracker

Updated: 2026-09-26 16:35 Asia/Bangkok
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

### XRP / Variational
Latest USER_CONFIRMED:
- LONG 77.12 XRP @ **1.55589**
- isolated 3x
- TP 1.6280
- SL 1.5140

Current Binance public XRP mark: **1.53882547**.
Assuming the Variational position remains unchanged:
- estimated current uPnL: **~-1.3160 USD**
- no public-mark crossing of 1.6280 or 1.5140 was observed after the latest private screenshot

Exact venue PnL remains private-source dependent.

### PAID / Solana
- DIRECT_CHAIN quantity: **947.685473 PAID**
- quantity unchanged from the verified purchase
- verified total purchase budget: **~50 USD-equivalent** including route cost from the prior execution record

Public PAID price references are currently inconsistent. Recent Pump results imply roughly **9.9-18.0 USD** for the current balance.
Indicative PAID mark PnL range: **~-40.1 to -32.0 USD**.
Keep this as MARKET_ESTIMATE until an execution-grade quote is reconciled.

### e/acc / Solana
- DIRECT_CHAIN current balance: **542.749359 e/acc**
- another **180.916452 e/acc** has left the wallet since the 14:18 snapshot, confirmed by finalized chain data

Historical verified first-sale phase:
- original budget: about **40 USD**
- first major sale cash recovery: about **55.68 USD**
- recorded first-phase network/priority fees: about **0.57 USD**
- first-phase net cash recovery: about **55.11 USD**
- cash recovered above original budget at that stage: about **+15.11 USD**, while residual e/acc still remained

Later e/acc reductions, including the latest 180.916452 outflow, are not yet fully reconciled to exact proceeds/fees. Current public e/acc price feeds conflict materially, so total e/acc realized + unrealized PnL remains **UNRESOLVED**.

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
- XRP Variational: ~-1.32 estimated from public mark
- KARDASHEV: ~+17.64 current total-position estimate
- PAID: ~-40.1 to -32.0 indicative

Active-position subtotal: approximately **-26.4 to -18.3 USD**, excluding e/acc, gas/funding not already captured, NFTs/points, and historical closed sleeves.

Adding only the already verified first-phase e/acc cash-recovery surplus of about +15.11 gives a **partial reconciled result around -11.3 to -3.2 USD**.

This is not the final Mission PnL. It excludes:
- later e/acc sale proceeds/fees;
- current residual e/acc executable value;
- historical SHART/CRED closed-sleeve reconciliation;
- UNICRED/Credits/Fresh INK executable values;
- exact current Binance/Variational funding and private account fees.

## Current capital distribution
- canonical stablecoins: **667.141577 USDC**
- strict directly priced on-chain liquid NAV: **~797.29 USD**, excluding PAID/e/acc and unpriced NFTs/points
- indicative direct-chain liquid NAV after adding PAID/e/acc public-reference ranges: roughly **807-816 USD**
- Binance PONS isolated margin reference: ~13.20 USDT plus current estimated uPnL
- Variational estimated current venue equity: ~48.58 USD from prior equity base plus current public-mark PnL estimate

Rough all-tracked liquid-value range: **~869-878 USD**, excluding NFTs/points/unpriced receipts and the separate low-risk interest bucket.

## Reserved / structural capital
- JUMP reserve: 400 USDC on Ethereum.
- ETH conditional reserve: 100 USDC accounting target; no live ETH Mission trade confirmed.
- opportunity capital is already distributed across Solana/BNB/Robinhood/private venues and must not be double-counted.
- separate ~500 USD-equivalent low-risk interest bucket remains outside speculative Mission accounting.
