# Current Portfolio / Capital Map

Updated: 2026-09-27 12:46 Asia/Bangkok
Timezone: Asia/Bangkok

## Mission objective

Core target: grow the Mission starting asset set to **3,000 USD-equivalent net liquidation value**.

Starting asset set:
- **300 USD cash principal**
- original six Jack / Visualize Value Credits NFTs

Current original Credits:
- held: **#23042, #23232**
- sold/transferred out: **#21646, #21753, #22857, #23328**

## Fresh chain correction

This snapshot supersedes the earlier 12:41 reconciliation.

The earlier snapshot incorrectly carried forward old non-zero meme quantities on Solana, BNB Chain and Robinhood Chain. Fresh direct Alchemy reads now confirm the user has effectively cleared those meme positions.

Economically closed residual dust is not treated as an active position.

## Current on-chain holdings

### Ethereum
DIRECT_CHAIN:
- USDC: **400.308121**
- native ETH: **0.001667063838788351**
- WETH: **0.000038313**
- Credits NFTs: **#23042, #23232**
- small priced dust including ZRO/MORPHO/ZKP/ZAMA/USDT/cbBTC/HEX remains below active-position significance
- unsolicited/unpriced spam receipts excluded

### Solana
DIRECT_CHAIN finalized:
- canonical USDC: **420.472536**
- native SOL: **0.127067295**
- PAID mint `98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump`: **0.000473 PAID**
- KARDASHEV: **0**
- SHARTCOIN: **0**
- legacy unresolved SPL mint `2MU93nLHhDsHzgEYBKbVbwLDd2pi71ubGp8SkEv9dZwQ`: **1.745552**
- 1-unit/non-transferable Token-2022 receipts remain excluded

**PAID 0.000473 is residual dust. The PAID meme position is economically closed and is not an active holding for monitoring purposes.**

### BNB Chain
DIRECT_CHAIN:
- native BNB: **0.007878625902744041**
- canonical USDC: **0**
- GSTOCK: **0.096724707311314713**

GSTOCK decimals were independently confirmed as 18.

**GSTOCK 0.096724707311314713 is residual dust. The prior 1183.5967247073113-GSTOCK position has been cleared and is no longer active.**

The broad BNB token inventory contains many unsolicited/unverified token receipts. They are excluded from Mission NAV and position monitoring unless independently verified as user-acquired assets.

### Robinhood Chain
DIRECT_CHAIN:
- native ETH: **0.000815126815110326**
- PONS: **0.000953441979624353**

PONS decimals were independently confirmed as 18.

**PONS 0.000953441979624353 is residual dust. The prior 54.799953441979625-PONS Robinhood spot position has been cleared and is no longer active.**

Other Robinhood-chain token receipts visible in the wallet are unverified/unsolicited and are excluded from active Mission holdings unless provenance is established.

### Ink
DIRECT_CHAIN cross-chain balance endpoint:
- native ETH: **0.010389022090321585**
- Tydro Ink Points: **7.665136656205785948**
- Fresh INK commemorative NFT #372 remains tracked

### Base
DIRECT_CHAIN:
- canonical USDC: **0.252982**
- native ETH: **0.000790846510479134**
- tiny ERC-20 dust/spam excluded from core NAV

### Unichain
DIRECT_CHAIN:
- canonical USDC: **0.021286**
- native ETH: **0.000231941590232335**
- UNICRED NFT #230 remains tracked

### Arbitrum
DIRECT_CHAIN cross-chain balance endpoint:
- canonical USDC: **0.000001**
- native ETH: **0.000825005012848238**
- BONK: **0.00003** dust
- pRCADE and spoof/non-canonical USDC receipts excluded

## Canonical on-chain stablecoins

- Ethereum: 400.308121
- Solana: 420.472536
- Base: 0.252982
- Unichain: 0.021286
- Arbitrum: 0.000001
- BNB Chain: 0

**Total canonical on-chain stablecoins: 821.054926 USDC.**

## Strict directly priced liquid reference

Fresh public marks:
- ETH: **2704.28581395 USD**
- SOL: **121.10381149 USD**
- BNB: **774.24840623 USD**

Using the direct balances above:
- canonical stablecoins: **821.054926 USD**
- tracked native gas across Ethereum/Solana/BNB/Robinhood/Ink/Base/Unichain/Arbitrum: **~61.29 USD**
- WETH: **~0.10 USD**

**Strict directly priced on-chain liquid reference: ~882.45 USD.**

Excluded:
- meme residual dust PAID/GSTOCK/PONS;
- Credits #23042/#23232;
- UNICRED #230;
- Fresh INK #372;
- Tydro Ink Points;
- unresolved legacy SPL;
- unsolicited/spam receipts.

## Binance — USER_CONFIRMED

Current Binance inventory is exactly:
1. **598 USD-equivalent combined earn bucket**
2. **PONSUSDT perpetual**

No other Binance spot balance, derivative position or reserve bucket is carried forward.

### PONSUSDT perpetual
Latest private authority:
- LONG **64 PONS**
- entry **0.6250**
- isolated **3x**
- TP: 0.668 / 0.704 / 0.739
- hard stop: 0.498

Fresh public Binance mark:
- **0.61669610**
- latest funding: **0.00011652**

If private quantity is unchanged:
- estimated mark-to-entry uPnL: **~-0.5314 USDT**
- exact private margin, fees, realized PnL and order state remain USER_CONFIRMED-only.

## Current active asset interpretation

Position-specific active trading exposure:
- **Binance PONSUSDT perpetual only**

On-chain:
- stablecoins/native gas;
- Credits #23042/#23232;
- UNICRED #230;
- Fresh INK #372;
- Tydro Points;
- unresolved/minor dust.

Economically closed meme positions:
- Solana PAID: residual **0.000473**
- BNB GSTOCK: residual **0.096724707311314713**
- Robinhood PONS: residual **0.000953441979624353**
- SHARTCOIN: 0
- KARDASHEV: 0
- e/acc: previously verified 0

No dedicated meme-position monitoring should run for these closed/dust balances.
