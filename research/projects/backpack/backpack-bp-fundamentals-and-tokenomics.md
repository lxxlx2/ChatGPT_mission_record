# Backpack Exchange / BP: verified identity, actual issuance, equity rights, and supply research

Updated: 2026-10-09 Asia/Bangkok
Purpose: durable fundamental and tokenomics research for the Mission's six-asset non-Meme investment decision.
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `token_trading_principles.md`, `MISSION_SPEC.md`.
Research state: `TRADING_TOKEN_CONFIRMED / GROWTH_UNLOCKS_UNRESOLVED / NOT_A_CURRENT_POSITION`.
Trading: `PRODUCTION_TRADING=NO_GO`; no buy, staking, wallets, automation or existing production signal modified.

## Identity and team

- Issuer/brand: Backpack Exchange, founder Armani Ferrante, previously built Solana Anchor framework and Mad Lads NFT ecosystem.
- First-party official token page: https://backpack.exchange/bp
- First-party issuer announcement dated 2026-03-18: https://learn.backpack.exchange/blog/backpack-token-ticker-bp
- Launch: 2026-03-23 on **Solana** (issuer first-party; actual onchain supply independently read October 9).
- **Official SPL Mint**: `BPxxfRCXkUVhig4HS1Lh7kZqV6SPJhzfEk4x6fVBjPCy`. Beware of fake similarly named BP tokens.
- Exchange API docs: https://docs.backpack.exchange/
- Backpack issuer's corporate history reports February 2024 **$17m Series A, $120m company equity valuation**, led by Placeholder VC. Source: https://learn.backpack.exchange/blog/a-brief-history-of-backpack. **This is equity valuation, NOT private BP token purchase price; do not invent institutional BP cost.**
- Live products: centralized Backpack crypto exchange, wallet, tokenized equities functionality reported on official docs; actual users/revenue/net earnings/accounting are **UNVERIFIED** using independently accessible primary financial statements. Cumulative turnover or custody self-reports are issuer claims, not audited current revenue.

## Tokenomics: official issuer terms (not independent proof of enforceable lockups)

Issuer page https://backpack.exchange/bp :
- total supply: **1,000,000,000 BP** nominal;
- TGE circulation 25% = 250,000,000 BP: points holders 240,000,000 + Mad Lads 10,000,000;
- pre-IPO 37.5% = 375,000,000 BP: growth milestone unlocks allocated to users, **not fixed calendar release**; conditions include regulatory/product/market expansion;
- post-IPO 37.5% = 375,000,000 BP: corporate treasury, issuer states locked until one year after IPO;
- issuer states no separate team/venture investor allocation at token genesis;
- exact dates and tranche sizes of remaining growth unlocks **UNCONFIRMED**; do not trust third-party calendar `fully unlocked` if inconsistent with issuer documents.
- trading token `BP` and future company equity are **different legal/economic assets**.

## Equity-exchange program: conditional, no instant equity

First-party terms https://support.backpack.exchange/exchange/programs/backpack-participant-program :
- stake BP at least **one year** for the base program; continue staking until a qualified IPO or acquisition / equity liquidity event;
- the *right* to use tokens to purchase corporate equity from a reserved fixed share pool, subject to eligibility, minimum stake, geography/legal rules, forfeiture and program terms;
- at inception reserved equity pool was equivalent to **20% company shares** existing Feb. 23 / March 23, 2026. Fixed number of shares, **may be diluted** by future issuance. Not an unconditionally guaranteed 20% ownership of future company.
- Unstaking can reset accrued eligibility; issuer FAQ https://learn.backpack.exchange/articles/how-to-claim-bp says a seven-day unstaking period after launch grace; verify latest terms before any action.
- **No contractual guarantee that IPO/acquisition occurs on a target date or that sale price covers acquisition costs.** Do not market this as a risk-free dividend or a liquid 20% company ownership claim.

## Direct Solana finalized evidence

Observation: 2026-10-09, using Alchemy Solana mainnet finalized `getTokenSupply` and `getTokenLargestAccounts` against official Mint (not a third-party chart).
- actual mint supply `999,998,651.118185366 BP` at nine decimals.
- largest **token account** `2pWK2bHBah35yPDQdndtwTXry1JtR8LKF59tQrqgaU6s`: **750,000,000 BP (75%)**, consistent numerically with uncirculated 37.5%+37.5% official allocation pools; **account identity/vesting permissions not confirmed**. Treat this as one token account and not as a single liquid retail whale.
- second-largest token account `CBGt4r6n5KyPpV5D3XZaoFJReHGiNC1YbRqrY2zKKTaE`: **190,667,621.66160002 BP (~19.07%)**; account owner, staking/custody attribution and transfer conditions **UNRESOLVED**. Do not call it team/insider/central-exchange without additional evidence.
- these two token accounts together account for about **94.07% of total supply**, but this fact alone cannot establish available-for-sale float or economic ownership concentration; use account owner data and lockup program review for any conclusion.
- market-data aggregator CMC October 9 quoted circulating about 249,998,652 and about $1.248 BP; circulating-market-cap ~$312M and FDV ~$1.248B; 7-day ~-9.17%, 30-day ~+118.67%, 24h ~+20.32% at time of read. This is time-stamped research context, not a future live quote.
- issuer token dashboard showed substantial staking of 25% freely released tranche, but staking ratio fluctuates and dashboard does not prove next unlock date.

## Investment edge / risks / gating checks

Positive:
- externally verifiable running exchange/wallet business; disclosed founder background; actual fungible Solana token and official economics;
- distinct fee, USD yield, wallet benefits and long-term conditional equity exchange;
- demand for staking can reduce immediately active float, but also introduces liquidity/contract/legal constraints.

Risks:
- **large FDV versus current circulating MC**, up to 375m additional pre-IPO milestone BP allocations directly to users, unpredictable dates and potential subsequent selling;
- no independently reconciled current recurring revenue, custody assets, net profit or audited users;
- unusual conditional equity rights have material regulatory/jurisdiction, qualification, dilution and liquidity-event uncertainty;
- past 30-day appreciation of ~119% on read and current 24h +20% raises short-term chase risk;
- must inspect actual token mint/freeze authorities, named program-controlled wallets, transfer history, major pool depth and executable exit quotes before any trade thesis.
- short-horizon $300 Mission user wants liquid asymmetric upside; a 1-year BP stake/equity option is **not** a short-term liquid strategy.
- current research position: `WATCH / WAIT_FOR_UNLOCK_AND_VALUATION_REFRESH`; user explicitly included BP among six competing assets but has not ordered any BP trade. No target price invented as objective support.

Sources: issuer/backpack URL above; Solana finalized mint RPC; CMC read-only pricing.  Never infer minted supply = liquid circulating supply.
