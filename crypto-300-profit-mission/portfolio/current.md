# Current Portfolio / Capital Map

Updated: 2026-09-29 03:44 Asia/Bangkok
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
- Solana USDC: **521.349642**
- Ethereum USDC: **400.308121**
- directly decomposed subtotal: **921.657763 USDC**

Last wallet UI completeness snapshot showed an additional **~13.203224 USDC** outside the Ethereum + Solana balances. Since the only wallet activity after that snapshot was the three Solana transactions listed below, the inferred aggregate USDC completeness mark is now:

- **~934.860987 USDC**

Known canonical USDC dust on Base / Arbitrum / Unichain etc. remains below $1 per chain and is omitted.

### Sui

USER_CONFIRMED unchanged:
- SUI: **40.192929**
- fresh SUIUSDT reference: **$1.1575**
- marked value: **~$46.52**

Current connector still lacks a usable direct Sui balance RPC; quantity therefore remains the latest user-confirmed canonical amount.

### Solana

DIRECT_CHAIN finalized:
- SOL: **0.011130612**
- SOLUSDT reference: **$118.79**
- marked value: **~$1.32**
- USDC: **521.349642**

New material SPL position:
- mint: `C1mBfBoDkwWfd6uTFZp62ARHLjeVp3bDpCDMfMZtPngE`
- balance: **2,845.330357**
- current Alchemy price feed has no quote for this mint.
- latest wallet execution sold **15,000 tokens** and, using the USDC wallet balance delta across the only three intervening Solana transactions, realized approximately **40.110987 USDC**, implying an execution-derived reference price of **~$0.002674/token**.
- residue marked at that execution-derived reference: **~$7.61**
- this is an execution-derived mark, not an independent market-price oracle.

Recent Solana sequence after the prior snapshot:
1. tx `44fD8WaGkPF6SMCpb1sD9rCMAw22Ch26R8FFj3SWXbK5n9Gn9yK4aAxhwM9zyDQCTR5X52WEd7HFWivQdwhot88d`
2. tx `98BUBWjGWLJKabUTq1mowhxRfLJeXRnic426jw4RWrUXeAoJ8bnbGD7TL3eRWXksiKMdLE7wiKeLx8UWvvdhj4B`
3. tx `3JMcPqQ1i4vn99nYMh1RiWmEX27sF7TZ7pAPjtidKkdw1RhxmTAzruHPrBVbwJ3RnN4jkd1BH9ebVtV7uiornsgB`

Relative to the 02:28 snapshot:
- Solana USDC: **506.238655 -> 521.349642** (**+15.110987**)
- SOL: **0.015349154 -> 0.011130612** (**-0.004218542**)
- C1m... token: **0 -> 2,845.330357** remaining after the trade sequence.

No other fungible SPL / Token-2022 balance with a reliable value >= $1 was identified.

### EVM native ETH-family positions

Fresh DIRECT_CHAIN:
- Ink ETH: **0.010389022090321585 ETH** = **~$27.85**
- Ethereum ETH: **0.000850479068623404 ETH** = **~$2.28**
- Base ETH: **0.000781411120038408 ETH** = **~$2.09**

ETH reference: **~$2,680.39**

Directly confirmed ETH-family subtotal above the $1-per-chain threshold:
- **~$32.22**

The following remain below $1 individually and are omitted: Linea ETH, Unichain ETH, World Chain ETH, Robinhood Chain ETH, Optimism ETH, Arbitrum ETH, BNB, AVAX, POL, HYPE, MON and other gas/dust positions.

## Material NFTs >= $1

### Credits — Ethereum

Fresh DIRECT_CHAIN ownership:
- **Credit #23232** — owned
- **Credit #23042** — sold / no longer owned

Fresh OpenSea collection floor:
- **~$65.37**

Conservative NAV:
- Credit #23232: **~$65.37**
- no rarity premium added.

### UNICRED #230 — Unichain

Fresh DIRECT_CHAIN ownership:
- **UNICRED #230** — owned

Fresh OpenSea collection floor:
- **~$7.85**

Conservative NAV:
- UNICRED #230: **~$7.85**

### Other inventory

- INK #372 remains known historical Ink inventory, but there is no reliable current >=$1 market mark from the available connector, so it is excluded from marked totals.
- The Solstice vesting-position NFT remains relevant to the separate Season 1 rights dispute; revoked 1,049.483713 SLX is not treated as liquid NAV.
- Other Ethereum NFTs below $1 are omitted.

## Current marked asset reference

Filtered liquid on-chain positions >= $1:
- inferred aggregate USDC completeness mark: **~$934.86**
- SUI: **~$46.52**
- SOL: **~$1.32**
- EVM ETH-family positions >=$1: **~$32.22**
- Solana `C1m...PngE` residue: **~$7.61**

**Filtered liquid subtotal: ~ $1,022.54**

Material NFTs:
- Credit #23232: **~$65.37**
- UNICRED #230: **~$7.85**

**Material NFT subtotal: ~ $73.22**

**Filtered on-chain + marked NFTs: ~ $1,095.76**

Add unchanged Binance Earn:
- **$682.40**

**Total tracked asset reference: ~ $1,778.16**

## Monitoring policy

No routine wallet polling.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

Do not add or modify monitoring/automation scope without an explicit user request.
