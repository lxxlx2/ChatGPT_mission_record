# Current Portfolio / Capital Map

Updated: 2026-09-26 16:33 Asia/Bangkok
Timezone: Asia/Bangkok

## Data labels
- DIRECT_CHAIN: fresh connected chain/explorer data.
- USER_CONFIRMED: latest private venue screenshot / explicit user update.
- MARKET_ESTIMATE: current public market reference applied to a verified quantity.
- UNRESOLVED: excluded from strict NAV/PnL.

## Canonical direct-chain holdings

### Ethereum
- USDC: **400.308121**
- ETH: **0.001667063838788351**
- current ETH reference: ~2680.61 USD

### Solana
- USDC: **266.559188**
- SOL: **0.129098090**
- e/acc (Token-2022): **542.749359**
- PAID (Token-2022): **947.685473**
- SHART: **0**
- unidentified legacy SPL mint 2MU93...dZwQ: **1.745552**, UNRESOLVED

Change from 14:18 snapshot:
- USDC: +17.901827
- SOL: -0.004317397
- e/acc: -180.916452
- PAID: unchanged

A fresh finalized Solana transaction confirms an outgoing **180.916452 e/acc** transfer. Exact sale proceeds are not inferred from the wallet-level USDC delta because several recent transactions occurred and the full route has not yet been reconciled.

### BNB Chain
- canonical USDC: **0**
- BNB: **0.002567317179192202**
- GSTOCK: **1183.5967247073113**

The former 30.00474761-USDC reserve has filled:
- exact canonical-USDC outflow in the fill transaction: **30.00474761 USDC**
- GSTOCK received: **1183.5967247073113**
- effective token cost before BNB gas: **~0.0253504821 USD/GSTOCK**
- Alchemy market reference at ~16:31: **0.0241192634 USD**
- mark value: **~28.5475 USD**
- token unrealized PnL before gas: **~-1.4573 USD (-4.86%)**

### Robinhood Chain
- PONS: **54.799953441979625**
- ETH: **0.000825190918816326**
- PONS market reference at ~16:29: **0.6247626394 USD**
- spot mark value: **~34.2370 USD**
- verified spot acquisition cost: **35.291194 USDG**
- spot mark PnL: **~-1.0542 USD (-2.99%)**

Unpriced/non-canonical receipts such as JOLLY, HYPERCAT, familiars, RMB, 富贵, DIH and DGDY remain excluded from NAV.

### Ink
- ETH: **0.01113370814547789**
- Tydro Ink Points: **7.665136656205785948**
- Fresh INK commemorative NFT #372: **owned**
- separately discussed target Ink NFT: **still pending / no new mint evidence**

### Base
- USDC: **0.252982**
- ETH: **0.000790846510479134**

### Unichain
- USDC: **0.021286**
- ETH: **0.000231941590232335**
- CRED liquid balance: **0**
- UNICRED NFT #230: **owned**, fresh NFT inventory confirmed

### Arbitrum
- ETH: **0.000827194359305186**
- no canonical USDC position identified in the returned Blockscout token inventory
- multiple tokens named USDC use non-canonical contracts and are excluded as unverified/spoof receipts

## Direct-chain capital summary

Canonical stablecoins:
- Ethereum: 400.308121
- Solana: 266.559188
- BNB Chain: 0
- Base: 0.252982
- Unichain: 0.021286

**Total canonical stablecoins: 667.141577 USDC.**

Current native-gas mark value across Ethereum, Solana, BNB Chain, Robinhood Chain, Ink, Base, Unichain and Arbitrum is approximately **58.98 USD** using the latest connected ETH/SOL/BNB references.

Strict directly priced liquid NAV, excluding PAID/e/acc and unpriced NFTs/points/receipts:
- stablecoins: ~667.14
- native gas: ~58.98
- GSTOCK: ~28.55
- Robinhood PONS spot: ~34.24

**Strict directly priced on-chain NAV: ~788.91 USD.**

PAID and e/acc are held and tracked, but their public price feeds currently conflict materially. They remain outside strict NAV. Recent public PAID references imply roughly **9.9-18.0 USD** for the current balance; e/acc value is small but unresolved. Including those indicative ranges gives a rough direct-chain liquid range around **799-808 USD**, excluding NFTs/points/unpriced receipts.

## Private venue positions

### Binance PONSUSDT perpetual
Latest private USER_CONFIRMED state: 2026-09-26 13:45.
- LONG **64 PONS**
- entry **0.6250**
- isolated 3x
- TP triggers: 0.668 / 0.704 / 0.739
- hard stop: Mark <= 0.498

Current Binance public mark at ~16:32: **0.6256**.
No public Binance mark crossing of 0.668 or 0.498 was observed after the last private screenshot.
If the private position has not been manually changed:
- estimated unrealized PnL: **~+0.0384 USDT**
- screenshoted margin reference: **~13.20 USDT**

Private account state remains USER_CONFIRMED until a newer Binance account screenshot/source is available.

### Variational XRP perpetual
Latest private USER_CONFIRMED:
- LONG **77.12 XRP**
- entry **1.55589**
- isolated 3x
- TP **1.6280**
- SL **1.5140**

Current Binance public XRP mark at ~16:32: **1.53882547**.
Public mark history since the user screenshot did not cross either stored exit level.
If the private position remains unchanged:
- estimated unrealized PnL: **~-1.3160 USD**
- prior account equity at +0.97 uPnL was 50.87 USD; implied current venue equity is roughly **48.58 USD** using the public-mark estimate.

This is a market estimate, not a direct Variational account read.

## Non-fungible / non-priced holdings
- UNICRED NFT #230 on Unichain
- Credits #23042 and #23232 on Ethereum
- Fresh INK #372 on Ink
- Tydro Ink Points

These are excluded from strict liquid NAV until executable values are verified.

## Capital-sleeve note
The current tracked wallets contain later capital in addition to the original $300 mission sleeve. Current wallet NAV must not be compared directly with $300 to claim Mission profit.
The separate ~500 USD-equivalent low-risk interest bucket remains outside this speculative Mission accounting.
