# Current Portfolio / Capital Map

Updated: 2026-10-01 after SUI exit, UNICRED exit and Legion JUMP funding
Timezone: Asia/Bangkok

## Accounting rule

- include only individual chain positions / NFTs with a reliable marked value of **>= $1.00**;
- individual positions worth **< $1.00** are omitted from the displayed portfolio;
- spam, claim-bait and unpriced unsolicited receipts are excluded;
- unpriced known inventory can remain as a note but does not enter marked totals;
- committed/pending allocation capital is tracked separately from liquid available balance;
- this is an asset-completeness snapshot, not Mission PnL.

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Private / off-chain

### Binance — USER_CONFIRMED

Latest available balance:
- **$523.72**

This replaces the previous Binance Earn reference of $682.40.

### Legion / JUMP — USER_CONFIRMED

- submitted / reserved capital: **$1,000.00**
- state: **PENDING_ALLOCATION**
- final allocation: **not yet known**
- accounting: track the full $1,000 as pending capital until Legion publishes the allocation/refund result; do not treat it as liquid available balance.

## Fresh liquid on-chain assets >= $1

Chain scan reference: 2026-10-01 around 13:45–13:50 UTC.

### Solana

DIRECT_CHAIN finalized:
- USDC: **108.626548**
- USDC reference: ~$1.0003
- marked value: **~$108.66**

Native SOL:
- SOL: **0.003093645**
- SOL reference: ~$117.92
- marked value: **~$0.36**
- omitted from displayed totals because it is below $1.

No other currently observed standard SPL balance with a reliable value >=$1 is included.

### Ethereum USDC

DIRECT_CHAIN:
- USDC: **1.006555**
- USDC reference: ~$1.0003
- marked value: **~$1.01**

Known Base / Arbitrum / Optimism / Unichain / Linea USDC balances checked in this refresh are each below $1 and are omitted.

### EVM native ETH-family positions

Fresh native balances:
- Ink ETH: **0.010389022090321585 ETH** = **~$27.97**
- Ethereum ETH: **0.000739940008393928 ETH** = **~$1.99**
- Base ETH: **0.000967183780184779 ETH** = **~$2.60**

ETH reference used for mark: **~$2,692.45**.

Directly confirmed ETH-family subtotal above the $1-per-chain threshold:
- **~$32.57**

Linea ETH, Unichain ETH, Optimism ETH, Arbitrum ETH, BNB, AVAX, POL and other native gas balances remain individually below $1 and are omitted.

### Sui

USER_CONFIRMED:
- **SUI balance for portfolio accounting: 0 / position fully cleared**
- removed from current marked holdings.

## Material NFTs >= $1

### Credits — Ethereum

Fresh DIRECT_CHAIN ownership check:
- **Credit #23232** — still owned by canonical EVM wallet

Last reliable collection floor reference remains:
- **~$65.37**

Current floor lookup was unavailable in this refresh, so this is a stale-but-last-reliable reference, not a new market quote.

Conservative marked value:
- Credit #23232: **~$65.37**

### Removed / no longer current

- **UNICRED #230**: removed from current portfolio. Fresh Unichain NFT ownership query returned no currently owned NFTs for the canonical EVM wallet after the user's completed operation.
- Credit #23042: previously sold / no longer owned.

### Other inventory

- INK #372 remains known Ink inventory, but there is no reliable current >=$1 market mark from the available connector, so it is excluded from marked totals.
- The Solstice vesting-position NFT remains relevant only to the separate Season 1 rights dispute; revoked 1,049.483713 SLX is not treated as liquid NAV.
- Other NFTs below $1 are omitted.

## Current marked asset reference

### Liquid / available

- Binance available balance: **$523.72**
- Solana USDC: **~$108.66**
- Ethereum USDC: **~$1.01**
- EVM ETH-family positions >=$1: **~$32.57**

**Liquid / available subtotal: ~ $665.95**

### Pending allocation capital

- Legion / JUMP pending allocation: **$1,000.00**

### Marked NFT

- Credit #23232: **~$65.37**

### Total tracked asset reference

**~ $1,731.32**

Previous tracked asset reference:
- **~$1,774.86**

Reference delta:
- **~ -$43.54**

User reported today's loss as approximately **$50**. The tracked-reference delta is broadly consistent, but it is not a precise realized-PnL calculation because Credit #23232 is still marked using the last reliable floor reference and some sub-$1 dust is intentionally excluded.

## Current state notes

- SUI: **cleared / 0**.
- UNICRED #230: **removed from current holdings**.
- Legion / JUMP: **$1,000 pending allocation; waiting for Legion allocation result**.
- Binance: **$523.72 latest user-confirmed balance**.
- Positions below $1 remain excluded by rule.

## Monitoring policy

No routine wallet polling.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

Do not add or modify monitoring/automation scope without an explicit user request.
