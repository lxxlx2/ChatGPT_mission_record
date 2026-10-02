# Current Portfolio / Capital Map

Updated: 2026-10-02 after Credit #23232 exit / Credits position fully cleared
Timezone: Asia/Bangkok

## Accounting rule

- include only individual chain positions / NFTs with a reliable marked value of **>= $1.00**;
- individual positions worth **< $1.00** are omitted from the displayed portfolio;
- spam, claim-bait and unpriced unsolicited receipts are excluded;
- unpriced known inventory can remain as a note but does not enter marked totals;
- committed/pending allocation capital is tracked separately from liquid available balance;
- cross-chain proceeds whose destination has not yet been independently mapped are tracked separately as reconciliation / in-transit value and are not double-counted as liquid;
- this is an asset-completeness snapshot, not Mission PnL.

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Private / off-chain

### Binance — USER_CONFIRMED

Latest available balance:
- **$523.72**

### Legion / JUMP — USER_CONFIRMED

- submitted / reserved capital: **$1,000.00**
- state: **PENDING_ALLOCATION**
- final allocation: **not yet known**
- accounting: track the full $1,000 as pending capital until Legion publishes the allocation/refund result; do not treat it as liquid available balance.

## Fresh / retained on-chain assets >= $1

### Solana

Latest retained verified balance from prior refresh:
- USDC: **108.626548**
- displayed mark: **~$108.66**

Native SOL remains below the $1 display threshold in the latest retained snapshot and is omitted.

### Ethereum USDC

Fresh Ethereum address scan 2026-10-02:
- USDC: **1.006555**
- marked value: **~$1.01**

### EVM native ETH-family positions

ETH reference from fresh Ethereum scan: **~$2,739.79**.

Fresh Ethereum native balance:
- Ethereum ETH: **0.000634360344095958 ETH** = **~$1.74**

Retained known balances on other chains, re-marked at the same ETH reference:
- Ink ETH: **0.010389022090321585 ETH** = **~$28.46**
- Base ETH: **0.000967183780184779 ETH** = **~$2.65**

Displayed ETH-family subtotal:
- **~$32.85**

Other individual native gas balances below $1 remain omitted.

### Sui

USER_CONFIRMED:
- **SUI balance for portfolio accounting: 0 / position fully cleared**

## Credits / Visualize Value — Ethereum

### Credit #23232 — SOLD / POSITION CLOSED

Contract:
- `0x97630aA70AB14ed9883B41dAfccBc11349723043`

Exit transaction:
- tx: `0xfec4cc0cf5618636afbd4d08e14d7175c3970bc7fc6fdd042f2a732f0cc4fb8a`
- time: **2026-10-02 15:09:35 Asia/Bangkok**
- NFT transferred out: **Credit #23232**
- seller wallet received: **0.0124 WETH**
- ETH reference at fresh scan: **~$2,739.79**
- sale proceeds reference: **~$33.97** before wallet gas
- sale transaction gas: **0.00005219278930425 ETH ≈ $0.14**

Original primary acquisition basis:
- Credit #23232 originated from one of the user's six **$8** Jack / X Money Credit payments.
- therefore direct acquisition basis for this Credit: **$8.00**

Approximate realized lifecycle result for Credit #23232:
- ~$33.97 seller proceeds
- less ~$8.00 original acquisition cost
- less ~$0.14 sale transaction gas
- **≈ +$25.83 realized profit** before any later bridge/withdrawal costs.

Important accounting distinction:
- the 2026-10-01 portfolio file carried Credit #23232 at a stale last-reliable mark of **~$65.37**;
- selling near ~$33.97 therefore reduces today's tracked NAV versus yesterday's marked reference even though the NFT itself was profitable versus its original $8 cost.

### Post-sale Relay movement

Immediately after the sale:
- tx: `0x5f2382d961c1474b34347e1525cb0c955c6071cb3cc529135ace35cb035e3be7`
- time: **2026-10-02 15:10:11 Asia/Bangkok**
- **0.012276 WETH** was transferred into the Relay flow and burned/unwrapped as part of the transaction path;
- reference value: **~$33.63**;
- transaction gas: **0.00003970961140206 ETH ≈ $0.11**;
- source-side contract is RelayDepository path; destination chain / final received asset has not yet been independently mapped in this refresh.

Accounting treatment:
- track **~$33.63** as `RELAY_RECONCILIATION / destination not yet mapped`;
- do not double-count it as Ethereum liquid balance;
- once the destination transaction is independently identified, move this value into the actual destination-chain asset line.

### Credits position state

- Credit #23232: sold 2026-10-02.
- Credit #23042: previously sold 2026-09-28.
- current canonical Credits position: **0 / fully cleared**.
- no Credits NFT value remains in current marked NFT holdings.

## Other NFT / rights inventory

- **UNICRED #230**: removed / no longer owned.
- INK #372 remains known Ink inventory, but there is no reliable current >=$1 market mark from the available connector, so it is excluded from marked totals.
- Solstice vesting-position NFT remains relevant only to the separate Season 1 rights dispute; revoked 1,049.483713 SLX is not treated as liquid NAV.
- other NFTs below $1 are omitted.

## Current marked asset reference

### Liquid / available

- Binance available balance: **$523.72**
- Solana USDC retained mark: **~$108.66**
- Ethereum USDC: **~$1.01**
- EVM ETH-family displayed positions: **~$32.85**

**Liquid / available subtotal: ~ $666.24**

### Pending / reconciliation

- Legion / JUMP pending allocation: **$1,000.00**
- Relay proceeds awaiting destination mapping: **~$33.63**

### Marked NFT

- Credits: **$0 / fully cleared**
- no other NFT currently has a reliable included mark in this snapshot.

### Total tracked asset reference

Including Relay reconciliation value but excluding sub-$1 dust and unpriced NFTs:

**~ $1,699.87**

Previous tracked asset reference (2026-10-01):
- **~$1,731.32**

Reference delta:
- **~ -$31.45**

This delta is primarily the mark-to-exit compression on Credit #23232: yesterday's portfolio used ~ $65.37 as a stale floor mark, while today's actual seller receipt was ~ $33.97. It is **not** the same as realized trade PnL. Relative to the original $8 acquisition basis, Credit #23232 itself closed profitably.

## Current state notes

- Credits: **fully cleared / 0**.
- SUI: **cleared / 0**.
- UNICRED #230: **removed from current holdings**.
- Legion / JUMP: **$1,000 pending allocation**.
- Binance: **$523.72 latest user-confirmed balance**.
- Relay: **~0.012276 ETH-equivalent / ~$33.63 pending destination reconciliation**.
- positions below $1 remain excluded by rule.

## Monitoring policy

No routine wallet polling.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

Do not add or modify monitoring/automation scope without an explicit user request.
