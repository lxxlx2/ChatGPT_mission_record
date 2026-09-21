# 2026-09-21 Crypto Daily Quality Regression

Status: fixed at rules level
Date: 2026-09-21

## What failed

The report was technically formatted but had low decision value.

Observed failures:
- ZEC and HYPE were treated as one-off missing ticker entries instead of evidence that persistent-trend discovery was inadequate.
- The mover section was driven too heavily by 24h price changes and news availability.
- UNI was labeled without a sufficient cause explanation even though cross-chain and Robinhood Chain pricing/bridge mechanics were relevant investigation paths.
- Internal process text and QA/classification commentary leaked into the user-facing report.
- Empty Early/Meme/NFT and airdrop sections consumed space with workflow explanations.
- X/Twitter and Reddit were not systematically used as daily discovery inputs.
- public-chain ecosystem scanning was too shallow, missing areas such as Zcash inscriptions/NFT work, BNB Chain Genius.fun/GSTOCK and X Layer RWA/tokenized-stock expansion.
- large ZEC whale/hedge positioning was not elevated.
- crypto-relevant iOS/App Store security intelligence such as FomoPeek was missed.
- Polymarket token-vs-equity/Pre-Access structural signals were not elevated.

## Remediation

The Crypto Daily automation now:
- scans multi-period trends before writing
- adds a persistent trend and cross-market opportunity chapter
- performs cross-chain/CEX/DEX spread analysis
- mandates X and Reddit scans
- mandates public-chain ecosystem scans
- mandates whale and security feeds
- separates Polymarket token/TGE evidence from IPO/equity/SPV/Pre-Access evidence
- moves all QA/process details into run audit only
- sends one normal report per day

Canonical rules: crypto-daily/REPORT_SPEC.md
