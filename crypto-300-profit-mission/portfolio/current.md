# Current Portfolio / Capital Map

Updated: 2026-09-29 02:28 Asia/Bangkok
Timezone: Asia/Bangkok

## Current allocation posture

User has intentionally reduced market risk:
- keep Ink ETH for future NFT participation;
- keep SUI for Sui launchpad participation;
- convert most other liquid crypto into USDC or move it to Binance earn;
- no active futures/perpetual position.

Current display/accounting threshold:
- include only individual chain positions / NFTs with a reliable marked value of **>= $1.00**;
- individual chain positions worth **< $1.00** are omitted even if a wallet UI aggregates them into a larger asset total;
- spam, claim-bait and unpriced unsolicited receipts are excluded;
- unpriced known inventory can remain as a note but does not enter marked totals;
- this threshold is for current portfolio presentation only, not historical provenance.

## Private / off-chain — USER_CONFIRMED

Binance Earn remains unchanged from the 2026-09-28 confirmed snapshot:
- estimated total: **682.40 USDT-equivalent**
- USDC position: **382.27204197 USDC** (displayed ~382.40 USDT)
- USDT position: **300 USDT**
- PONSUSDT perpetual: **CLOSED**
- no active Binance trading position

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Current wallet UI snapshot — USER_CONFIRMED

2026-09-29 02:28 Asia/Bangkok screenshot:
- wallet total shown: **$1,078.07**
- USDC aggregate: **919.75**
- SUI: **40.192929** = **$46.62**
- ETH aggregate across wallet-supported chains: **0.014307** = **$38.37**
- SOL: **0.015349** = **$1.82**

The UI aggregate is useful as a completeness cross-check. The canonical portfolio below applies the >=$1 rule per chain position, so it does not blindly carry the full aggregated ETH amount.

## Fresh liquid on-chain assets >= $1.00

### USDC

Fresh DIRECT_CHAIN reads:
- Solana USDC: **506.238655**
- Ethereum USDC: **400.308121**

Directly decomposed subtotal:
- **906.546776 USDC**

The current wallet UI shows aggregate USDC **919.75**, leaving approximately **13.203224 USDC** outside the two directly decomposed balances above. Current connector coverage does not cleanly attribute this residual to one canonical chain without risking inclusion of spam/lookalike tokens. For top-level portfolio completeness, the current wallet aggregate **919.75 USDC** is used; the known direct chain balances remain recorded separately.

Known tiny canonical USDC balances are below $1 and omitted, e.g. Base 0.000252 USDC, Arbitrum 0.000001 USDC, Unichain 0.021286 USDC.

### Sui

USER_CONFIRMED unchanged:
- SUI: **40.192929**
- wallet UI mark: **$46.62**

User explicitly confirmed the Sui position was not moved.

### Solana

DIRECT_CHAIN finalized:
- SOL: **0.015349154**
- current spot reference around **$118.88/SOL**
- value: **~$1.82**
- USDC: **506.238655**

Fresh SPL / Token-2022 reads found no additional fungible token position with a reliable value >= $1.00.

### EVM native ETH-family positions

User explicitly confirmed Ink was not moved.

Fresh DIRECT_CHAIN native balances:
- Ink ETH: **0.010389022090321585 ETH** = **~$27.85**
- Ethereum ETH: **0.000850479068623404 ETH** = **~$2.28**
- Base ETH: **0.000781411120038408 ETH** = **~$2.10**

Using ETH around $2,681, the directly confirmed >=$1 ETH-family subtotal is:
- **~$32.23**

Individual chain ETH balances below $1 are omitted per policy, including Linea ETH, Unichain ETH, World Chain ETH, MegaETH ETH, Robinhood Chain ETH, Optimism ETH and Arbitrum ETH.

The wallet UI aggregates all ETH-family balances as **0.014307 ETH / $38.37**; that full aggregate is not used in the filtered NAV because it includes sub-$1 chain positions and possibly chains not cleanly decomposed by the current connector.

Other native gas positions such as POL, BNB, AVAX, XPL, S and similar balances are also each below $1 and omitted.

## Material NFTs >= $1.00

### Credits — Ethereum

Fresh DIRECT_CHAIN ownership at 2026-09-29:
- **Credit #23232** — owned
- **Credit #23042** — sold / no longer owned

Fresh OpenSea collection reference:
- Credits floor: **$64.38**
- top offer: **$63.11**
- 24h volume: **$251.2K**

Conservative NAV:
- Credit #23232: **$64.38**
- no rarity premium is added to portfolio NAV.

### UNICRED #230 — Unichain

Fresh DIRECT_CHAIN ownership:
- **UNICRED #230** — owned

Fresh OpenSea Unichain reference:
- UNICRED floor: **$7.85**

Conservative NAV:
- UNICRED #230: **$7.85**

### Other NFT / position inventory

Previously marked Ethereum NFTs such as Survivor Dave #9347, Ten Years Of Ethereum #191404 and Adventure Cards #3052 remain below the $1 threshold and are omitted.

INK #372 remains known Ink inventory, but current tooling still lacks a reliable Ink NFT market/ownership endpoint and no reliable >=$1 mark is available in this refresh. It is excluded from marked totals.

The Solstice vesting-position NFT remains relevant to the separate Season 1 rights dispute. The revoked 1,049.483713 SLX is not a liquid wallet balance and is excluded from NAV.

## Current marked asset reference

Filtered liquid on-chain assets / positions >= $1:
- USDC aggregate completeness mark: **$919.75**
- SUI: **$46.62**
- SOL: **~$1.82**
- directly confirmed EVM ETH-family positions >=$1: **~$32.23**

**Filtered liquid subtotal: ~ $1,000.42**

Material NFTs:
- Credit #23232: **$64.38**
- UNICRED #230: **$7.85**

**Material NFT subtotal: ~ $72.23**

**Filtered on-chain + marked NFTs: ~ $1,072.65**

Wallet UI headline is **$1,078.07**; the roughly $5.4 gap is consistent with excluded sub-$1 chain dust / wallet-side marks and is intentionally not force-counted under the >=$1 rule.

Add unchanged USER_CONFIRMED Binance Earn:
- **$682.40**

**Total tracked asset reference under the >=$1 rule: ~ $1,755.05**

This is an asset-completeness snapshot, not Mission PnL. Capital provenance remains separated from performance accounting.

## Monitoring policy

No routine wallet polling.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

Do not add or modify monitoring/automation scope without an explicit user request.
