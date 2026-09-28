# Current Portfolio / Capital Map

Updated: 2026-09-28
Timezone: Asia/Bangkok

## Current allocation posture

User has intentionally reduced market risk:
- keep Ink ETH for future NFT participation;
- keep SUI for Sui launchpad participation;
- convert most other liquid crypto into USDC or move it to Binance earn;
- no active futures/perpetual position.

Current display/accounting threshold:
- include only individual liquid assets / NFTs with a reliable marked value of **>= $1.00**;
- assets worth **< $1.00** are omitted from the current displayed portfolio;
- spam, claim-bait and unpriced unsolicited receipts are excluded;
- unpriced known inventory can remain as a note but does not enter marked totals;
- this threshold is for current portfolio presentation only, not historical provenance.

## Private / off-chain — USER_CONFIRMED

Binance Earn screenshot, 2026-09-28:
- estimated total: **682.40 USDT-equivalent**
- USDC position: **382.27204197 USDC** (displayed ~382.40 USDT)
- USDT position: **300 USDT**
- PONSUSDT perpetual: **CLOSED**
- no active Binance trading position

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Fresh liquid on-chain assets >= $1.00

### Stablecoins

DIRECT_CHAIN:
- Ethereum USDC: **400.308121**
- Solana USDC: **506.238655**

Stablecoin subtotal:
- **906.546776 USD-equivalent**

The Solana amount is the exact finalized SPL balance. Under the new accounting rule, e.g. **506.238655 USDC is carried as $506.238655** rather than being rounded away or mixed with sub-$1 dust.

### Sui

Latest known wallet quantity:
- SUI: **40.192929**

Fresh market reference:
- SUIUSDT: **1.1571**
- marked value: **~$46.51**

The current connector still does not expose a usable Sui balance RPC in this session, so the quantity remains the latest user-confirmed/canonical quantity rather than a fresh DIRECT_CHAIN read. It is retained because its marked value is clearly above $1.

### Solana

DIRECT_CHAIN finalized:
- SOL: **0.015349154**
- SOLUSDT: **118.25**
- value: **~$1.82**
- USDC: **506.238655**

Fresh SPL and Token-2022 reads found no additional fungible token position with a reliable value >= $1.00.

### EVM native assets

Fresh multi-chain DIRECT_CHAIN scan was run across Ethereum, Base, Arbitrum, Optimism, Polygon, Linea, Ink, Unichain, World Chain, MegaETH, Robinhood Chain, BNB Chain, Avalanche, Blast, Scroll, Mantle, Berachain, zkSync, Monad and Hyperliquid.

ETH reference used for marking: **$2,657.17**.

Only native balances >= $1.00:
- Ink ETH: **0.010389022090321585 ETH** = **~$27.61**
- Ethereum ETH: **0.000850479068623404 ETH** = **~$2.26**
- Base ETH: **0.000790061852162197 ETH** = **~$2.10**

ETH-family/native subtotal above threshold:
- **~$31.96**

Examples now deliberately omitted from the displayed portfolio:
- Linea ETH **0.000283128973717299** (~$0.75)
- Unichain ETH **0.000231941590232335** (~$0.62)
- World Chain ETH, MegaETH ETH, Robinhood Chain ETH, Optimism ETH, Arbitrum ETH, POL, BNB, AVAX, HYPE and MON gas balances are each < $1 at current references.

Ethereum token spot-check:
- USDC: **400.308121**
- WETH: **0**
- USDT: **0.00917**, omitted under the $1 rule.

## Material NFTs >= $1.00

### Credits — Ethereum

DIRECT_CHAIN ownership:
- **Credit #23232** — still owned
- **Credit #23042** — sold / no longer owned

Credit #23042 disposal evidence:
- NFT transfer tx: `0x6de9f1830600200c8cdd38c682cdb031190d5a10c9f36be423fcda660413ac78`
- transfer time: 2026-09-28 14:41:35 UTC
- sale settlement into wallet: **0.0239 WETH**
- the wallet then unwrapped WETH and subsequently transferred **0.0232 ETH** out in the next sequence.

Current OpenSea collection floor reference:
- Credits floor: **~$65.37**

Conservative NAV:
- Credit #23232: **~$65.37**
- no rarity premium is added to portfolio NAV despite its stronger Rating/rank.

### UNICRED #230 — Unichain

DIRECT_CHAIN ownership reconfirmed:
- **UNICRED #230**

Fresh OpenSea collection floor reference:
- **~$7.85**

Conservative NAV:
- UNICRED #230: **~$7.85**

### Other NFT / position inventory

Previously marked Ethereum NFTs such as Survivor Dave #9347, Ten Years Of Ethereum #191404 and Adventure Cards #3052 are below the new $1 threshold and are omitted from displayed totals.

Fresh INK #372 remains known historical Ink inventory, but current tooling still lacks a reliable Ink NFT market/ownership endpoint and there is no reliable >=$1 mark in this refresh. It is excluded from marked totals.

The Solstice vesting-position NFT remains relevant to the separate Season 1 rights dispute, but the revoked 1,049.483713 SLX is not a liquid wallet balance and is not included in current NAV.

## Current marked asset reference

Liquid on-chain assets >= $1:
- stablecoins: **$906.55**
- SUI: **~$46.51**
- SOL: **~$1.82**
- qualifying EVM native balances: **~$31.96**

**Material on-chain liquid subtotal: ~ $986.83**

Material NFTs:
- Credit #23232: **~$65.37**
- UNICRED #230: **~$7.85**

**Material NFT subtotal: ~ $73.22**

**On-chain + marked NFTs: ~ $1,060.05**

Add USER_CONFIRMED Binance Earn:
- **$682.40**

**Total tracked asset reference: ~ $1,742.45**

This is an asset-completeness snapshot under the >=$1 presentation rule. It is not Mission PnL; capital provenance remains separated from performance accounting.

## Monitoring policy

No routine wallet polling.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

Do not add or modify monitoring/automation scope without an explicit user request.
