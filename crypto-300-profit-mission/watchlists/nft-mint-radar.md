# NFT Mint Radar

Timezone: Asia/Bangkok

Purpose: discover newly announced or newly live NFT / digital-art mints with verified issuer provenance and an unusually favorable early opportunity profile. This radar is discovery-first and runs hourly. It must stay silent when no candidate passes the full gate.

## Discovery surfaces

Primary discovery surfaces:
- MintGo: https://mintgo.fun/ for Trending, New Mints, Upcoming Mints, market data, creator/contract context and mint-source discovery.
- Waypoint MintScan: https://waypoint.tools/mintscan/ for live mint activity, momentum and scam flags.
- MCT NFT minting / launch calendar: https://mct.xyz/nft/minting for block-level NFT mint discovery and upcoming projects.
- nftis.fun: https://nftis.fun/ for New Mints / Trending discovery.
- 985monitor: https://985monitor.xyz/wallet/ only as a read-only auxiliary EVM mint/activity surface. Never import a private key, seed phrase, or main wallet into this site for monitoring.
- English X/Twitter: official creator/project/platform accounts, known collectors, marketplaces and mint platforms.
- Reddit and other English-language public communities as sentiment / discovery evidence only.
- Official marketplaces and launch platforms such as OpenSea, Manifold, Foundation and Zora when applicable.
- Direct chain data and explorers for contract, mint progress, holder distribution, transfers and authority/security checks.

Never use Chinese-language websites as confirmation.

## Hard identity gate

A candidate can never be labeled high-potential until issuer/project provenance is confirmed.

Require:
1. Canonical issuer identity anchored by an official X account, official root domain, official launch page, or a direct link from one of those.
2. A verifiable project or creator history. This can be a public team identity, an established pseudonymous creator/project with a durable onchain/public history, or an established brand/platform. A copied name or a newly created account with no history fails.
3. Canonical mint page and/or canonical collection contract once live. If the contract is not live yet, the official issuer must explicitly announce the mint and official launch page.
4. No unresolved conflict among project name, account, domain, chain, contract, collection and payment destination.

If any identity conflict remains, record the candidate as rejected/pending and do not send an alert.

## High-potential gate

After the identity gate passes, require an actionable mint window now or within 24 hours and enough evidence to support at least two independent opportunity signals from the list below:

- Established creator/team/brand with a prior collection or product that reached meaningful organic demand.
- Social acceleration: rapid growth in views/reposts/replies, multiple independent known NFT/crypto accounts discussing it, or recognizable collectors interacting.
- Onchain acceleration: rising mint velocity, unique minters, low concentration, or meaningful participation from known wallets without obvious bundled-wallet manipulation.
- Supply/demand asymmetry: limited supply, short mint window, strong whitelist demand, or mint progress materially faster than comparable launches.
- Attractive primary terms relative to credible comps: free/low-cost mint, low implied primary valuation, or unusually favorable holder utility/claim structure.
- Secondary-market validation after launch: real sales, bids/offers, liquidity and volume from more than a few related wallets.
- Distribution/channel novelty with credible issuer backing, such as a major wallet, payments rail, large consumer platform, or recognized marketplace introducing a new issuance mechanic.

A single KOL post, raw follower count, paid promotion, wash trading, or a high mint count from a few wallets is insufficient.

## Mandatory risk checks

Before alerting, check as applicable:
- chain and canonical contract/collection
- mint price and payment asset
- supply and per-wallet limit
- public / allowlist phases
- exact start/end in Asia/Bangkok
- current minted / supply and mint velocity
- unique minters and concentration
- creator/team allocation
- royalties and marketplace restrictions
- contract ownership / admin / upgrade / pause permissions where relevant
- transfer restrictions or unusual approval flows
- phishing/domain mismatch
- whether the mint requires signing an unusual message or granting token/NFT approval
- secondary floor, top bid/offer, sales count, volume and listed ratio after launch
- creator's prior collections: mint price, peak floor/market cap when verifiable, time-to-peak and drawdown
- current X / Reddit sentiment, with social claims kept separate from verified facts

## Alert classes

PREMINT: verified issuer and official mint window within 24h, before contract activity is live.
LIVE_MINT: mint is live and passes the high-potential gate.
SECONDARY_BREAKOUT: newly minted collection shows real secondary demand and still has a plausible early entry window.
RISK_RETRACTION: a previously alerted candidate develops an identity/security/contract problem that materially changes the thesis.

## Email threshold and silence rule

Send Gmail to lxx.run688@gmail.com only when a new candidate passes the hard identity gate and high-potential gate, or when a previously alerted candidate has a material new action/risk update.

No qualifying candidate means complete silence: no Gmail and no ChatGPT notification.

Do not repeat the same candidate every hour. A follow-up alert requires a material change such as mint opening, contract becoming canonical, sellout acceleration, secondary market opening, major collector/official interaction, price/volume regime change, or a security/thesis failure.

## Alert payload

Subject:
`NFT Radar｜<project>｜<PREMINT|LIVE_MINT|SECONDARY_BREAKOUT|RISK_RETRACTION>`

Body:
- Project / creator
- Canonical official X and website
- Why the team/project provenance is considered verified
- Chain, collection/contract and official mint link
- Bangkok start/end time
- Mint price, supply, per-wallet limit and current progress
- Unique minters / concentration / mint velocity when available
- Secondary floor, best bid/offer, sales/volume/listed ratio when available
- Prior-project evidence and credible comparables
- Social/onchain heat with quantitative evidence
- Why this candidate passed the high-potential gate
- Main red flags and what would invalidate the thesis
- One concise action: WATCH, SMALL_TEST, or AVOID, with any suggested test size sourced only from the Mission general opportunity reserve
- Source links

Clearly label unknown data as unavailable. Never fabricate dynamic values.

## GitHub audit

Each hourly run should write or append an audit record under:
`crypto-300-profit-mission/radar/nft/YYYY/YYYY-MM/YYYY-MM-DD.md`

For each candidate record:
- discovery_time
- discovery_surface
- project
- official_identity_sources
- canonical_contract
- identity_gate
- opportunity_signals
- risk_checks
- social_heat
- onchain_heat
- primary_terms
- secondary_data
- accepted_or_rejected
- rejection_reason
- gmail_sent
- gmail_message_id

Actionable alerts should also create:
`crypto-300-profit-mission/signals/YYYY/YYYY-MM/YYYY-MM-DDTHHMM-nft-radar-<slug>.md`

Never store private keys, seed phrases, wallet secrets, or authentication tokens in GitHub.


## Source priority after live usability check — 2026-09-25

Use these discovery sources with different weights:

Tier 1:
- MintGo. Primary discovery feed because its public page exposes Trending, New Mints, Market, Upcoming Mints, time windows, search by collection/address, and project detail fields such as mint progress, creator, market data and contract analysis. Prefer it for early candidate generation across the chains it currently exposes.
- Direct chain / official issuer / official marketplace data. Always the final verification layer before an alert.

Tier 2:
- Waypoint MintScan. Strong signal design for live mint volume, percentage minted, wallet activity and momentum, and official docs describe real-time Ethereum mainnet scanning. Use when live/public data is retrievable, but do not rely on it as the only hourly source because the public page can block automated fetches and full Mint Scanner access may require Waypoint Red Premium.
- MCT FreeMint / Launch Calendar. Useful secondary discovery source because it exposes block/pending monitoring, short-window mint rankings and a launch calendar. Treat it as candidate generation, then verify externally.

Tier 3:
- nftis.fun. Lightweight backup for New Mints / Trending / Sold Out / Coming Soon. Low weight because the public page exposes little machine-readable detail and may remain in loading/waiting states.
- 985monitor. Optional read-only auxiliary heat scanner only. Never require it for coverage, never import a main-wallet private key/seed phrase, and never use its execution/batch-wallet capabilities as part of this Mission.

Source failure handling:
- A 403, loading state, empty dynamic page or inaccessible premium feature is not evidence that no NFT opportunity exists.
- Failure of one source must fall through to the remaining sources plus official X, marketplaces and direct chain data.
- Never alert based only on a scanner's ranking or scam/quality label.
