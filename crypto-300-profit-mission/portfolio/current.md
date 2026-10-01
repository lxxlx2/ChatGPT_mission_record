# Current Portfolio / Capital Map

Updated: 2026-10-01 after REV exit
Timezone: Asia/Bangkok

## Accounting rule

- include only individual chain positions / NFTs with a reliable marked value of **>= $1.00**;
- individual positions worth **< $1.00** are omitted from the displayed portfolio;
- spam, claim-bait and unpriced unsolicited receipts are excluded;
- unpriced known inventory can remain as a note but does not enter marked totals;
- this is an asset-completeness snapshot, not Mission PnL.

## Private / off-chain — USER_CONFIRMED

Binance Earn unchanged:
- estimated total: **682.40 USDT-equivalent**
- USDC: **382.27204197**
- USDT: **300**
- no active Binance trading position

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Fresh liquid on-chain assets >= $1

### USDC

Fresh DIRECT_CHAIN:
- Solana USDC: **523.709901**
- Ethereum USDC: **400.308121**
- directly decomposed subtotal: **924.018022 USDC**

The latest wallet completeness snapshot had approximately **13.203224 USDC** outside the Ethereum + Solana balances. No non-Solana activity has been observed since that snapshot, so the inferred aggregate USDC completeness mark is:

- **~937.221246 USDC**

Known canonical USDC dust on Base / Arbitrum / Unichain etc. remains below $1 per chain and is omitted.

### Sui

USER_CONFIRMED unchanged:
- SUI: **40.192929**
- fresh SUIUSDT reference: **$1.1661**
- marked value: **~$46.87**

Current connector still lacks a usable direct Sui balance RPC; quantity therefore remains the latest user-confirmed canonical amount.

### Solana

DIRECT_CHAIN finalized:
- SOL: **0.023676412**
- SOLUSDT reference: **$119.10**
- marked value: **~$2.82**
- USDC: **523.709901**

The temporary meme position with mint
`C1mBfBoDkwWfd6uTFZp62ARHLjeVp3bDpCDMfMZtPngE`
is now **fully closed**:
- current balance: **0**
- previous residue: **2,845.330357**
- exit tx 1: `gi69QGEhAZ15ucUcUmKd5csq4EKT653b8EquhBgqDdSnqM6moj9dM3PKPKqErxNV2PTQEt6DVj413pgD45dh7Lh`
  - sold **1,422.665178**
  - swap leg produced **2.372119 USDC**
- exit tx 2: `2Yu4fXVCKvRMcwmDxmBonEKc45r2YgxWWHeNJNSgdz5XAAs1gGnLMvsdrs9tcnihziiZkcpsF6M3zwjS6HML8Ekp`
  - sold **1,422.665179**
  - swap leg produced **0.01271088 SOL**

Net wallet change versus the immediately preceding snapshot:
- Solana USDC: **521.349642 -> 523.709901** = **+2.360259**
- SOL: **0.011130612 -> 0.023676412** = **+0.012545800**
- meme token: **2,845.330357 -> 0**

The meme position is removed from current holdings.

- 2026-10-01: **REV temporary meme position: CLOSED**; finalized token balance **0**.

No other fungible SPL / Token-2022 position with a reliable value >= $1 was identified.

### EVM native ETH-family positions

No user-reported EVM movement since the prior refresh. Canonical balances remain:
- Ink ETH: **0.010389022090321585 ETH** = **~$27.94**
- Ethereum ETH: **0.000850479068623404 ETH** = **~$2.29**
- Base ETH: **0.000781411120038408 ETH** = **~$2.10**

ETH reference: **~$2,689.52**

Directly confirmed ETH-family subtotal above the $1-per-chain threshold:
- **~$32.33**

Linea ETH, Unichain ETH, World Chain ETH, Robinhood Chain ETH, Optimism ETH, Arbitrum ETH, BNB, AVAX, POL, HYPE, MON and other gas/dust positions remain individually below $1 and are omitted.

## Material NFTs >= $1

### Credits — Ethereum

Fresh DIRECT_CHAIN ownership:
- **Credit #23232** — owned
- **Credit #23042** — sold / no longer owned

Last reliable collection floor reference:
- **~$65.37**

Conservative NAV:
- Credit #23232: **~$65.37**
- no rarity premium added.

### UNICRED #230 — Unichain

Fresh DIRECT_CHAIN ownership:
- **UNICRED #230** — owned

Last reliable collection floor reference:
- **~$7.85**

Conservative NAV:
- UNICRED #230: **~$7.85**

### Other inventory

- INK #372 remains known Ink inventory, but there is no reliable current >=$1 market mark from the available connector, so it is excluded from marked totals.
- The Solstice vesting-position NFT remains relevant to the separate Season 1 rights dispute; revoked 1,049.483713 SLX is not treated as liquid NAV.
- Other Ethereum NFTs below $1 are omitted.

## Current marked asset reference

Filtered liquid on-chain positions >= $1:
- inferred aggregate USDC completeness mark: **~$937.22**
- SUI: **~$46.87**
- SOL: **~$2.82**
- EVM ETH-family positions >=$1: **~$32.33**
- temporary Solana meme: **$0 / CLOSED**

**Filtered liquid subtotal: ~ $1,019.24**

Material NFTs:
- Credit #23232: **~$65.37**
- UNICRED #230: **~$7.85**

**Material NFT subtotal: ~ $73.22**

**Filtered on-chain + marked NFTs: ~ $1,092.46**

Add unchanged Binance Earn:
- **$682.40**

**Total tracked asset reference: ~ $1,774.86**

## Monitoring policy

No routine wallet polling.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

Do not add or modify monitoring/automation scope without an explicit user request.
