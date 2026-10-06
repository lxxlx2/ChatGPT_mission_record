# Current Portfolio / Capital Map

Updated: 2026-10-07 Asia/Bangkok
Timezone: Asia/Bangkok

## Accounting rule

- Include only individual on-chain positions with a reliable marked value of **>= $1.00** in the displayed chain subtotal.
- Positions worth **< $1.00**, spam, claim-bait and unpriced unsolicited receipts are excluded from marked totals.
- User-confirmed CEX balances are classified by purpose; living-expense/rent money is not investment capital.
- Historical/private/pre-TGE rights remain separate from liquid/investable NAV.
- This is an asset-completeness snapshot, not Mission PnL.

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Fresh reference prices

Connected market-data snapshot used only for marking current balances:

- ETH: **$2,692.98**
- SOL: **$87.00**
- USDC: **$0.999923**

These marks are not trading signals.

## Current on-chain assets >= $1

### Solana — DIRECT_CHAIN / finalized

- USDC: **531.094071 USDC** (~**$531.05**)
- native SOL: **0.039406389 SOL** (~**$3.43**)

Classic SPL token accounts other than USDC returned zero in the current read. Token-2022 accounts included non-transferable/unpriced or spam-like items with no reliable >=$1 mark; they are excluded from NAV.

### Ethereum — DIRECT_CHAIN

- native ETH: **0.000904693862403571 ETH** (~**$2.44**)
- canonical USDC: **0**

The prior JUMP/Legion 1,000 USDC sale deposit is no longer held in the sale position; see the JUMP section below.

### Ink — DIRECT_CHAIN

- native ETH: **0.010133156790964273 ETH** (~**$27.29**)

Known INK NFT inventory remains unpriced in this refresh and is excluded from marked NAV until a reliable >=$1 market value is available.

### Below-$1 chain balances — excluded

Fresh reads found the following native balances below the accounting threshold; they are deliberately omitted from the marked subtotal:

- Base: **0.000137238616283283 ETH** (~$0.37)
- Unichain: **0.000020589809992416 ETH** (~$0.06)
- Arbitrum: **0.000003959748317278 ETH** (~$0.01)
- Optimism: **0.000065278607595283 ETH** (~$0.18)
- Linea: **0.000283129977526624 ETH** (~$0.76)
- World Chain: **0.000106736523058181 ETH** (~$0.29)
- Robinhood Chain: **0.000080297791401733 ETH** (~$0.22)
- BNB Chain: **0.000006838175538195 BNB**, below $1
- Base canonical USDC: **0.000252 USDC**, below $1
- MegaETH native: **0**

Unpriced/spam token receipts on these networks are not promoted into holdings.

### Sui — USER_CONFIRMED

- **SUI chain assets = 0**

This is the latest explicit user-confirmed state. Do not carry forward any old SUI position.

## CEX / off-chain capital buckets

### Binance — USER_CONFIRMED / PARKED INVESTMENT RESERVE

Screenshot-confirmed balance:

- **600.866553 USDC**
- shown current earn APR: **2.11%**
- auto-subscribe enabled

Accounting / execution rule:

- This remains investment capital, currently parked in Binance Earn.
- Do **not** move it merely to increase activity.
- Redeploy only if a materially better risk/reward opportunity is identified and explicitly approved.

Current mark at the reference USDC price: ~**$600.82**.

### Bybit — USER_CONFIRMED / NON-INVESTMENT PERSONAL CASH

Only the USDC line is authoritative for this accounting snapshot:

- **403.020679 USDC** (~**$402.99** at the reference mark)

Purpose explicitly confirmed by user:

- living expenses;
- next month's rent.

Therefore:

`BYBIT_USDC = EXCLUDED_FROM_INVESTMENT_CAPITAL`

Do not include the Bybit account's displayed total asset value or other dust/token balances in Mission NAV.

## JUMP / Jumper Legion — REJECTED / REFUND COMPLETE

- application result: **UNSUCCESSFUL / REJECTED**
- final allocation: **0 JUMP / 0 USDC accepted**
- original deposit: **1,000 USDC**
- refund status: **COMPLETE ON-CHAIN**
- refund transaction: `0x3d3264417775aa9cf0bf5d83f69f00b2ada9e01852784bc52897264025c5e0b5`
- refund transfer timestamp: `2026-10-06T17:28:23Z`

Latest direct contract state read after refund:

- `investedCapital = 0`
- `hasSettled = false`
- `hasClaimedExcess = false`
- `hasRefunded = true`
- `vestingAddress = 0x0000000000000000000000000000000000000000`

The sale contract transferred **1,000 USDC** back to the participating wallet. Do not carry a pending JUMP sale asset or JUMP token position forward, and do not add the refund as a separate asset on top of current wallet/CEX balances.

## Current marked capital reference

### On-chain material subtotal

- Solana USDC: ~$531.05
- Solana SOL: ~$3.43
- Ethereum ETH: ~$2.44
- Ink ETH: ~$27.29

**Material on-chain subtotal: ~ $564.21**

### Investable but parked CEX capital

- Binance Earn USDC: ~**$600.82**

### Current investable / Mission-addressable reference

**~ $1,165.03**

This includes the material on-chain subtotal plus Binance parked investment reserve. It excludes Bybit living/rent cash, sub-$1 dust, unpriced NFTs/tokens and private/pre-TGE rights.

### Personal cash excluded from investment

- Bybit USDC: ~**$402.99** — living expenses / next month's rent; excluded.

## Pre-TGE / private / points rights inventory

These entries preserve unresolved economic rights/cost bases and are not added to liquid NAV without a reliable current mark.

### Confirmed capital / acquisition-cost exposures still unresolved

| Project | User right / position | Historical cost / committed capital | Current state | Accounting treatment |
|---|---|---:|---|---|
| Reya | CoinList token-sale allocation | **$5,000** | pre-TGE / unresolved distribution | cost basis only; exclude from liquid NAV |
| Makina | Legion / ICO token allocation | **$1,000** | pre-TGE | cost basis only; exclude from liquid NAV |
| Block Stranding | presale / future token rights | **100 SOL** | pre-TGE | preserve native-unit cost; do not convert without explicit valuation refresh |
| Fortytwo | Echo seed / token-related rights | **$250** | pre-TGE / illiquid | cost basis only |
| OhBabyGames | Echo private / token-related rights | **$250** | unresolved liquidity / token event | cost basis only |
| 01.xyz / N1 | Echo investment rights plus legacy ecosystem rights | **$1,000** | final user-level conversion/liquidity unconfirmed | cost basis only |
| ForecastFDN | private / token-related entitlement | **$100** | pre-TGE / unresolved | cost basis only |
| Crusoe | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Apptronik | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Aalo Atomics | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Thalassa | Echo private equity / SPV rights | **$500** | illiquid private-market right | cost basis only |
| Figure | Echo private equity / SPV rights | **$1,000** | illiquid private-market right | cost basis only |
| 1X | Echo private equity / SPV rights | **$2,000** | illiquid private-market right | cost basis only |
| RepublicX / rTTOK / ByteDance economic exposure | 5,000 contingent payout notes, $1 principal each | **$5,000** | illiquid contractual note exposure | not direct ByteDance stock ownership; cost basis only |
| Surf Limited Edition NFT #691 | 1 NFT, pending delivery / airdrop | **$228** | delivery not independently verified | historical acquisition cost only |

Known dollar-denominated historical acquisition cost above: **$16,628**, plus **100 SOL** Block Stranding historical cost. JUMP is no longer included because the application was rejected and the 1,000 USDC deposit was refunded.

### Points / rewards / potential token rights

- StandX: **51,129.8 Final Points**
- Surf: **28,600 Points**
- Pond / JoinPond: **12,000 Points**
- TurboFlow: **12,000 Points; 2-account participation noted**
- MetaMask Rewards: **Season 1 Level 5**
- N1 / legacy 01, OpenSea, Polymarket, Base, Perena, Rho, Hylo, Tydro: historical participation/points rights exist; no current liquid value is assigned here.

## Explicit closed / excluded positions

- JUMP / Jumper Legion public sale: **rejected, 0 allocation, 1,000 USDC refunded**.
- humans& / Echo-Alpen: **CLOSED_FULLY_REFUNDED**.
- Credits / Visualize Value: fully cleared.
- UNICRED #230: no longer owned.
- SUI: 0 / fully cleared.
- PONS futures/spot: closed.
- XRP / Variational: closed.
- Assets below $1, spam, unknown/unpriced receipts: excluded under current rule.

## Monitoring policy

Routine wallet polling remains disabled.

Refresh this file only on explicit user request, after a material user-reported action, or when a verified event requires an ownership/balance check. Do not infer authorization for additional monitoring tasks.