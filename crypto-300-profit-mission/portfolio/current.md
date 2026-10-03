# Current Portfolio / Capital Map

Updated: 2026-10-04
Timezone: Asia/Bangkok

## Accounting rule

- include only individual chain positions / NFTs with a reliable marked value of **>= $1.00** in the displayed subtotal;
- individual positions worth **< $1.00** are omitted from the displayed subtotal but may be noted as dust/gas;
- spam, claim-bait and unpriced unsolicited receipts are excluded;
- unpriced known inventory can remain as a note but does not enter marked totals;
- committed/pending allocation capital is tracked separately from liquid available balance;
- wallet balance changes are not PnL without transaction history and cost basis;
- this file is an asset-completeness snapshot, not Mission performance.

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Fresh mark references

Fresh connected price references around 2026-10-04 05:24 Asia/Bangkok:
- ETH: **$2,687.63**
- SOL: **$119.79**
- USDC: **$1.00014**

These references are used only to mark known balances, not as trading signals.

## Private / off-chain

### Binance — USER_CONFIRMED carry-forward

Latest stored user-confirmed available balance:
- **$523.72**

This was not independently refreshed in the 2026-10-04 chain scan.

### Legion / JUMP — USER_CONFIRMED carry-forward

- submitted / reserved capital: **$1,000.00**
- state: **PENDING_ALLOCATION**
- final allocation: not yet recorded as known in this Mission snapshot
- accounting: track the full $1,000 as pending/committed capital until allocation/refund is verified; do not treat it as liquid available balance.

## Fresh on-chain assets

### Solana — DIRECT_CHAIN finalized

Fresh slot range: approximately 453,066,884–453,066,912.

Native SOL:
- **0.003093645 SOL**
- mark: **~$0.37** -> below $1 display threshold.

Classic SPL Token Program:
- canonical USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`
- balance: **142.162136 USDC**
- mark: **~$142.18**

Other classic SPL token accounts returned in this read had zero token balance.

Coverage limitation:
- the enhanced Solana asset endpoint was temporarily unavailable;
- a full Token-2022 enumeration was not completed in this refresh;
- therefore do not claim exhaustive coverage of every possible Solana asset class.

### Ethereum — DIRECT_CHAIN

Native ETH:
- **0.000634360344095958 ETH**
- mark: **~$1.70**

Canonical USDC:
- **1.006555 USDC**
- mark: **~$1.01**

Credits contract `0x97630aA70AB14ed9883B41dAfccBc11349723043`:
- owned count: **0**
- verified at block **26,114,793** / **2026-10-03T22:26:23Z**.

Current Credits position: **0 / fully cleared**.

### Base — DIRECT_CHAIN

Native ETH:
- **0.000967183780184779 ETH**
- mark: **~$2.60**

No unknown/spam token receipt is included without verified identity and reliable value.

### Ink — DIRECT_CHAIN native balance

Native ETH:
- **0.011133212494942321 ETH**
- mark: **~$29.92**

Prior stored native balance was `0.010389022090321585 ETH`. The increase is recorded only as a balance delta; no source transaction or profit is inferred from balance alone.

Known prior inventory:
- **INK #372** remains prior-known inventory;
- no supported fresh Ink NFT ownership result was obtained in this refresh;
- no reliable current >=$1 mark is included.

### Unichain — DIRECT_CHAIN

Native ETH:
- **0.000020589846025254 ETH**
- mark: **~$0.06** -> below $1 display threshold.

UNICRED contract `0xf60de24F228dc7Ca6fF025958d2eE3A956ED88E5`:
- owned count: **0**
- verified at block **60,318,039** / **2026-10-03T22:26:38Z**.

Current UNICRED #230 position: **not owned / closed**.

### Other fresh EVM native balances

Fresh reads also returned small native balances on Arbitrum, Optimism, Linea, World Chain, MegaETH, Robinhood Chain and other supported networks. These remain below the display threshold or lack a reliable material mark and are not included in the displayed subtotal.

Known examples:
- Arbitrum ETH: **0.000003959328931033**
- Optimism ETH: **0.000065278581034767**
- Linea ETH: **0.000283128973717299**
- World Chain ETH: **0.000106736504323280**
- MegaETH native balance: **0.000082071511230598**
- Robinhood Chain ETH: **0.000080297765615110**

### Sui — USER_CONFIRMED, not freshly rescanned

Latest explicit user-confirmed state:
- **SUI = 0 / position fully cleared**

The connected generic portfolio method did not accept the canonical Sui address format, so no fresh Sui-native result was obtained. Do not relabel this as DIRECT_CHAIN.

## NFT / rights inventory

### Credits

- fresh Ethereum ownership: **0**
- all original Credits are now historical provenance rather than current inventory.

### UNICRED

- fresh Unichain ownership: **0**
- #230 is no longer current inventory.

### INK #372

- prior known inventory only;
- fresh Ink NFT ownership endpoint unavailable in this refresh;
- no reliable market mark included.

### Solstice rights dispute

The historical revoked/vesting SLX rights dispute remains separate research/accounting context and is not treated as liquid NAV without a current verified entitlement.

## Current marked asset reference

### Liquid / available

- Binance latest user-confirmed available balance: **$523.72**
- Solana USDC: **~$142.18**
- Ethereum USDC: **~$1.01**
- Ethereum ETH: **~$1.70**
- Base ETH: **~$2.60**
- Ink ETH: **~$29.92**

**Liquid / available subtotal: ~ $701.13**

### Pending / committed

- Legion / JUMP pending allocation: **$1,000.00**

### Marked NFT

- Credits: **$0 / fully cleared**
- UNICRED: **$0 current inventory / not owned**
- no other NFT has a reliable included mark in this refresh.

### Total tracked asset reference

Excluding sub-$1 dust and unpriced/unverified NFTs/tokens:

**~ $1,701.13**

This is not Mission PnL. The off-chain Binance and JUMP values are carried forward from the latest user-confirmed state and were not independently refreshed by the chain scan.

## Current state notes

- Solana USDC remains **142.162136** on a fresh finalized read.
- Ink native ETH is now **0.011133212494942321**.
- Credits ownership is freshly verified at **0**.
- UNICRED ownership is freshly verified at **0**.
- SUI remains **0** by latest user-confirmed state, without a fresh supported Sui-native scan.
- positions below $1 remain excluded from the displayed subtotal.
- unknown/spam assets remain excluded until identity/value is independently verified.

## Monitoring policy

Routine automatic wallet polling is not authorized.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

The umbrella `$300-3000` GPT task is paused as of 2026-10-04. Frank local signal monitoring remains separate and LIVE; this does not authorize routine portfolio polling.
