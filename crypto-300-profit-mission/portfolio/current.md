# Current Portfolio / Capital Map

Updated: 2026-10-05 14:25 Asia/Bangkok
Timezone: Asia/Bangkok

## Accounting rule

- include only individual chain positions / NFTs with a reliable marked value of **>= $1.00** in the liquid marked subtotal;
- individual positions worth **< $1.00** are omitted from the displayed liquid portfolio;
- spam, claim-bait and unpriced unsolicited receipts are excluded;
- unpriced known inventory can remain as a note but does not enter marked totals;
- committed/pending allocation capital is tracked separately from liquid available balance;
- private/SPV/pre-TGE/points/NFT-rights inventory is tracked in a separate rights section and must not be added to liquid NAV without a reliable current mark;
- historical acquisition cost is not the same as current value;
- this is an asset-completeness snapshot, not Mission PnL.

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

## Fresh price references

Connected chain-data price snapshot around 2026-10-03 11:12 Asia/Bangkok:

- ETH: **$2,681.38**
- SOL: **$119.46**
- USDC: **$1.00013**

These prices are only for portfolio marking; they are not trading signals.

## Private / off-chain

### Binance — USER_CONFIRMED, not independently refreshed in this chain scan

Latest user-confirmed available balance:
- **$523.72**

### Legion / JUMP — USER_CONFIRMED

- submitted / reserved capital: **$1,000.00**
- state: **PENDING_ALLOCATION**
- final allocation: **not yet known**
- accounting: track the full $1,000 as pending capital until Legion publishes allocation/refund; do not treat it as liquid available balance or as a final token cost basis.

## Pre-TGE / private / points rights inventory

Purpose: preserve current unresolved user economic rights that are easy to miss in wallet-only accounting. These entries are **not** added to liquid NAV unless a reliable current market value and ownership state are independently verified.

### Confirmed capital / acquisition-cost exposures still unresolved

| Project | User right / position | Historical cost / committed capital | Current state | Accounting treatment |
|---|---|---:|---|---|
| Reya | CoinList token-sale allocation | **$5,000** | pre-TGE / unresolved distribution | cost basis only; exclude from liquid NAV |
| Makina | Legion / ICO token allocation | **$1,000** | pre-TGE | cost basis only; exclude from liquid NAV |
| JUMP / Jumper | Legion public-sale application | **$1,000 submitted/reserved** | **PENDING_ALLOCATION**; final allocation unknown | pending capital only; not final token cost basis |
| Block Stranding | presale / future token rights | **100 SOL** | pre-TGE | preserve native-unit cost; do not convert to current USD without explicit valuation refresh |
| Fortytwo | Echo seed / token-related rights | **$250** | pre-TGE / illiquid | cost basis only |
| OhBabyGames | Echo private / token-related rights | **$250** | unresolved liquidity / token event | cost basis only |
| 01.xyz / N1 | Echo investment rights plus legacy 01/N1 ecosystem rights | **$1,000** | 01 acquired by N1; final user-level conversion / liquidity not confirmed | cost basis only |
| ForecastFDN | private / token-related entitlement | **$100** | pre-TGE / unresolved | cost basis only |
| Crusoe | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only; not a TGE asset |
| Apptronik | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Aalo Atomics | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Thalassa | Echo private equity / SPV rights | **$500** | illiquid private-market right | cost basis only |
| Figure | Echo private equity / SPV rights | **$1,000** | illiquid private-market right | cost basis only |
| 1X | Echo private equity / SPV rights | **$2,000** | illiquid private-market right | cost basis only; separate from any 1X NEO consumer-order/refund history |
| RepublicX / rTTOK / ByteDance economic exposure | **5,000 RepublicX Contingent Payout Notes**, $1 principal each | **$5,000** | illiquid contractual note exposure; tokenization may represent the Notes if RepublicX elects to issue it | not direct ByteDance stock ownership; cost basis only |
| Surf Limited Edition NFT #691 | 1 NFT, pending delivery / airdrop | **$228** | not yet on-chain verified; expected by user to canonical main wallet on RB chain | historical acquisition cost only; exclude until delivered and reliably priced |

Known dollar-denominated historical acquisition cost / capital above, **excluding JUMP pending allocation** and excluding the 100 SOL Block Stranding cost: **$16,628**.

Including JUMP's currently submitted/reserved $1,000 as pending capital: **$17,628 + 100 SOL** of historical/committed exposure.

These figures are cost / commitment accounting only. They are not current fair value and must not be added to the liquid marked asset subtotal below.

### Points / rewards / potential token rights

| Project | Known user state | Token / liquidity status |
|---|---|---|
| StandX | **51,129.8 Final Points** | token/TGE not yet treated as realized |
| Surf | **28,600 Points** | pre-TGE / conversion not confirmed |
| Pond / JoinPond | **12,000 Points** | pre-TGE / conversion not confirmed |
| TurboFlow | **12,000 Points; 2-account participation noted** | no confirmed final token conversion in this portfolio record |
| MetaMask Rewards | **Season 1 Level 5** | rewards exist; token allocation/TGE not treated as confirmed |
| N1 / legacy 01 | legacy ecosystem points / rights exist; exact current quantity unresolved | conversion / token distribution unresolved |
| OpenSea | historical rewards / activity rights exist; exact current quantity unresolved | do not assign token amount without current official/user evidence |
| Polymarket | substantial historical user activity across prior accounts; no token amount recorded here | potential future rights only; do not value or assume token allocation |
| Base | historical ecosystem participation | no confirmed user token allocation in this record |
| Perena | points / activity rights recorded historically; exact quantity unresolved | pre-TGE / unresolved |
| Rho | points / activity rights recorded historically; exact quantity unresolved | pre-TGE / unresolved |
| Hylo | points / activity rights recorded historically; exact quantity unresolved | pre-TGE / unresolved |
| Tydro | points exist; exact current quantity unresolved | pre-TGE / unresolved |

### Explicit exclusions / closed positions

- **humans& / Echo-Alpen**: **CLOSED_FULLY_REFUNDED**; $1,000 returned on 2026-09-24; current economic exposure = **0**. Do not include in current holdings.
- Credits / Visualize Value: fully cleared.
- UNICRED #230: removed / no longer owned.
- SUI position: latest explicit user-confirmed state = 0 / fully cleared.
- Already-TGE assets are not included in this pre-TGE rights table merely because residual claim/dispute history exists.

## Fresh on-chain assets >= $1

### Solana — fresh finalized scan

Wallet native SOL:
- **0.003093645 SOL** ≈ **$0.37** → below $1 display threshold, omitted from marked subtotal.

SPL Token Program accounts:
- USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`
- balance: **142.162136 USDC**
- marked value: **~$142.18**

Other returned classic SPL accounts had zero token balance.

#### Relay reconciliation from 2026-10-02

Previous verified Solana USDC balance:
- **108.626548 USDC**

Current balance:
- **142.162136 USDC**

Increase:
- **+33.535588 USDC**

The increase is strongly consistent in size and timing with the prior Credit-sale Relay movement (~0.012276 ETH-equivalent / ~$33.63 source-side reference). The exact destination transaction has not been independently linked in this refresh, so this is recorded as **balance-level reconciliation**, not a proven transaction-level bridge mapping.

Accounting consequence:
- previous standalone `RELAY_RECONCILIATION` line is **closed**;
- the value now sits inside the actual Solana USDC balance;
- do not count the old ~$33.63 reconciliation value separately.

### Ethereum — fresh scan

Native ETH:
- **0.000634360344095958 ETH**
- mark: **~$1.70**

USDC:
- **1.006555 USDC**
- mark: **~$1.01**

Other returned ERC-20 balances with market data were below $1 individually or were spam/dust and are excluded under the accounting rule.

### Base — fresh native balance

- **0.000967183780184779 ETH**
- mark: **~$2.59**

No additional Base token is included without a reliable >=$1 mark; unsolicited/spam balances are excluded.

### Ink — fresh native balance

- **0.010389022090321585 ETH**
- mark: **~$27.86**

### Arbitrum / Optimism — fresh native balance, below threshold

- Arbitrum: **0.000003959328931033 ETH** ≈ **$0.01**
- Optimism: **0.000065278581034767 ETH** ≈ **$0.18**

Both are below the $1 display threshold and excluded from marked subtotal.

### Sui

Latest explicit user-confirmed accounting state remains:
- **SUI = 0 / position fully cleared**

No fresh Sui-native connector result was obtained in this refresh; do not relabel this line as independently rescanned.

## Credits / Visualize Value — CLOSED

Credit contract:
- `0x97630aA70AB14ed9883B41dAfccBc11349723043`

Fresh Ethereum NFT ownership query at block 26,109,344 / 2026-10-03T04:13:23Z:
- **owned NFTs from this contract: 0**

State:
- Credit #23042: previously sold 2026-09-28.
- Credit #23232: sold 2026-10-02.
- current Credits position: **0 / fully cleared**.

Credit #23232 realized lifecycle reference retained from the prior accounting entry:
- seller receipt: 0.0124 WETH (~$33.97 at then-current reference)
- direct acquisition basis: $8.00
- approximate realized profit after sale transaction gas: **~+$25.83**, before later bridge/withdrawal costs.

This realized result is distinct from the prior day-to-day NAV mark compression.

## Other NFT / rights inventory

- **UNICRED #230**: removed / no longer owned.
- **INK #372** remains known Ink inventory, but no reliable current >=$1 market mark is available in this refresh, so it is excluded from marked totals.
- **Surf Limited Edition NFT #691**: user-provided Surf subscription page shows purchase via DaimoPay for **$228.00** on **2025-08-31 13:38**. As of 2026-10-05 the page says the NFT is still in transit / pending airdrop to the account. User expects final delivery to the canonical main wallet on **RB chain**. Delivery/ownership is **not yet independently verified on-chain**. Record $228 as historical acquisition cost only; exclude from current marked totals until delivery and a reliable market value are confirmed.
- Solstice vesting-position NFT remains relevant only to the separate Season 1 rights dispute; revoked 1,049.483713 SLX is not treated as liquid NAV.
- other NFTs below $1 or without reliable value are omitted.

## Current marked asset reference

### Liquid / available

- Binance latest user-confirmed available balance: **$523.72**
- Solana USDC: **~$142.18**
- Ethereum USDC: **~$1.01**
- Ethereum ETH: **~$1.70**
- Base ETH: **~$2.59**
- Ink ETH: **~$27.86**

**Liquid / available subtotal: ~ $699.06**

### Pending / committed

- Legion / JUMP pending allocation: **$1,000.00**

### Marked NFT

- Credits: **$0 / fully cleared**
- Surf Limited Edition NFT #691: **pending delivery / unpriced**, excluded from marked subtotal; historical cost basis **$228.00**.
- no other NFT currently has a reliable included mark in this snapshot.

### Total tracked liquid + pending reference

Excluding sub-$1 dust, unpriced NFTs, and all private/pre-TGE/points rights without reliable current marks:

**~ $1,699.06**

Previous tracked asset reference from 2026-10-02:
- **~$1,699.87**

Reference change:
- **~ -$0.81**

Do not interpret this ~$0.81 change as trading PnL. The prior snapshot used different ETH/USDC marks and carried the Relay value as reconciliation; the current snapshot moves the Relay-sized value into actual Solana USDC and uses fresh prices.

## Current state notes

- Credits: **fully cleared / 0**, freshly rechecked on Ethereum.
- Solana USDC: **142.162136**, fresh finalized scan.
- Relay reconciliation: **closed at balance level**; no longer double-counted.
- SUI: **0 by latest explicit user-confirmed state**, not freshly rescanned here.
- UNICRED #230: **removed from current holdings**.
- Surf Limited Edition NFT #691: **$228 historical cost, pending airdrop; expected on main wallet RB chain; not yet on-chain verified**.
- Legion / JUMP: **$1,000 pending allocation**.
- Binance: **$523.72 latest user-confirmed balance**.
- pre-TGE/private/points rights are now preserved in a dedicated section and deliberately excluded from liquid NAV unless separately marked.
- humans& is fully refunded and excluded from current exposure.
- positions below $1 remain excluded by rule.

## Monitoring policy

No routine wallet polling unless explicitly authorized.

Refresh this file only:
- on explicit user request;
- after a user-reported material deposit/withdrawal/trade/claim/bridge/NFT action;
- when a verified event requires balance/ownership confirmation.

The newly authorized `$300` Meme/GPT monitoring task is separate from routine portfolio polling. Do not infer authorization for additional wallet-monitor automations.
