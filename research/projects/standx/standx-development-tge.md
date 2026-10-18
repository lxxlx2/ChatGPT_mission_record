# StandX 官方开发进度、平台 Token TGE 与公开代码审计

Updated: 2026-10-18 Asia/Bangkok
State: **PLANNED_PLATFORM_TOKEN_CANCELED / FINAL_ONE_TIME_DUSD_AIRDROP / OPERATIONS_WIND_DOWN**
Source priority: official homepage notice -> official X October 15 2026 announcement, then independent contemporaneous news corroboration.
Historical research dated 2026-09-29 below is retained as archived TGE-prep view, **not current**.

## 2026-10-15 decisive update: StandX cancels token and winds down operations

### Evidence grade and primary notice

- StandX's official site https://standx.com/ currently displays notice "StandX is easing operations. Please read the announcement and withdraw your assets in time." The notice links DIRECTLY to official X post https://x.com/StandX_Official/status/2110613283967230232 .
- Direct official X text fetching returned 403 to research browser. Full procedural terms, dates and reward scope corroborated by contemporaneous independent outlets: https://defiprime.com/standx-sets-january-closure-and-dusd-exit-dates (2026-10-15; explicitly cites original official post), https://www.rootdata.com/news/790088 and https://www.tokenpost.com/news/business/32327 .
- Evidence label: **OFFICIAL_HOMEPAGE_LINK_CONFIRMED + OFFICIAL_X_POST_POINTER_CONFIRMED + SECONDARY_RECONSTRUCTION**. Do not claim full original X post independently retrieved verbatim. The earlier StandX SIP docs offering future platform token remain published but are **historical/stale relative to later October 15 decision**.

### New issuer plan and exact calendar

Issuer **announced** it is abandoning issuance of the planned platform token and shifting to a **one-time DUSD stablecoin airdrop, no lockup**. No actual TGE/vesting/tokenomics/centralized listing should be assumed going forward; any Polymarket token-FDV or launch-probability contracts need official settlement rules applied to **NO TGE** scenario (do not fabricate market outcome without instrument specifics). Distribution funded by protocol remaining revenue plus unspecified additional funds from team; total dollar pool and per-account payout not announced.

| Event | Original announced UTC | Bangkok UTC+7 |
|---|---|---|
| all DUSD yield / Position Yield / maker yield / referral commissions cease, new vault creation or additions stop | 2026-10-15 | 2026-10-15 |
| perps reduce-only; new users and DUSD mint close; new Block Trades / Block Options close | 2026-10-20 (no exact hour confirmed) | 2026-10-20 |
| **airdrop eligibility checker** | **2026-10-26 00:00 UTC** | **2026-10-26 07:00** |
| **DUSD airdrop claim starts** | **2026-11-01 00:00 UTC** | **2026-11-01 07:00** |
| **DUSD airdrop claim ends** | **2026-12-31 08:00 UTC** | **2026-12-31 15:00** |
| automatic settlement of outstanding open positions at Mark Price, vault close process | 2027-01-15 (hour not provided) | 2027-01-15 |
| **final DUSD redemption requests and platform withdrawals** | **2027-01-31 (hour not provided)** | **2027-01-31** |

Rewards assessment categories: **pre-deposits, Alpha participation, mainnet trading, active market-making, referrals**. All subject to **anti-Sybil / wash volume** adjustments; abnormal allocations may be cut or canceled. No authoritative weights, PP→DUSD ratio, user-specific total, compensation size or final pool balance published at check time => `UNCONFIRMED`. Eligibility and individual amount should be checked via the historical **BNB Chain / Solana address originally used on StandX** on October 26.

For user funds, differentiate two obligations:
1. Claim the **one-time discretionary DUSD allocation** in Nov 1–Dec 31; unclaimed rights **forfeited** after claim window.
2. Independently **close active derivatives and withdraw/redeem user-owned deposited assets** by Jan 31, 2027. Position close via mark price Jan 15, Perps Wallet → Cash Wallet → onchain DUSD withdrawal; stablecoin swap/redeem separately as needed. StandX redemption procedures say ~7 day waiting period, and users need to consider it; DUSD LP liquidity on PancakeSwap/Raydium to be withdrawn by StandX on Jan 31 per announcement. **Do not mix airdrop payout and refundable customer deposits**, and do not assume yield/APR continues.
Issuer's assertions that DUSD remains fully collateralized / no fund incidents are `ISSUER_CLAIMS`, not an audited current reserve solvency result.

### Operational conclusion

- **Permanent project research state**: `NO_PLATFORM_TOKEN / FINAL_DUSD_COMPENSATION / WIND_DOWN`. Old TGE estimate and token-allocation ledger expectation now superseded.
- As of 2026-10-18, per planned schedule, **Oct 26 checker not yet available**, wallet-specific eligibility/allocated DUSD `UNVERIFIED`. Claim must not be described as already open or successfully executed.
- User has historically monitored/considered StandX and related NEO/DNA compensation; **do not conflate this StandX winddown DUSD distribution with any unrelated NeoSoul DNA airdrop**. No personal DUSD payout verified and no wallet claim, signatures, funding movements or trade performed.
- Record only; existing monitoring/automation/production configurations **untouched**. Any operational TGE alerts that may still expect a StandX token should not be treated as valid project state, but task changes require user permission.

---

## Historical 2026-09-29 research snapshot (superseded)


Updated: 2026-09-29 18:xx Asia/Bangkok
State at the time: PRODUCTION / SIP-5 PARTIAL ROLLOUT / PRE-TGE; **NO LONGER CURRENT**
Project: StandX
Official: https://standx.com
Docs: https://docs.standx.com
Official GitHub organization: https://github.com/standx-labs
Operational compatibility record: `crypto-300-profit-mission/watchlists/standx-tge.md`

## Current conclusion

CONFIRMED:
- StandX is already a production protocol. DUSD, Perps, API, Position Yield, Native Yield, Block Trade, Block Options, Community Maker Yield and Community Vault components are live or implemented.
- The large SIP-5 Universal Markets rollout is incomplete. The official SIP index currently marks SIP-5 as WIP, SIP-5A as Implemented, SIP-5B as Implemented and SIP-5C as Draft / "Cooooooking".
- SIP-5B's public specification is marked Implemented with release date 2026-07-18, while the team's July product update also described the feature as limited alpha testing before full rollout. Treat "implemented" as component implementation, not proof that full permissionless Universal Markets is complete.
- The official docs still explicitly state that the StandX platform token has not yet been issued.
- Maker Yield already maintains platform-token allocation entries and the live product UI exposes a Token Allocation field. This is a real pre-token accounting rail.
- No official token name/ticker, total supply, tokenomics, initial circulation, final points snapshot, eligibility checker, claim page, canonical platform-token mint/contract or exact TGE date was found in the current official public material.

INFERRED:
- StandX has built meaningful token utility hooks before TGE. SIP-5 permits the future platform token to act as a qualifying Sponsor staking asset, and Maker Yield already accrues token allocation.
- Product readiness is materially ahead of a typical points-only pre-TGE project, but launch readiness is behind the stage normally associated with an imminent TGE because the hard issuance artifacts are still absent.
- Full SIP-5 deployment is likely a more relevant product milestone than ordinary frontend feature shipping when assessing TGE proximity.

SPECULATIVE:
- Q4 2026 remains possible, but current public evidence does not support calling TGE imminent.
- If tokenomics, supply, checker/mint/claim or final snapshot still do not appear during mid-Q4, the 2027 scenario should gain weight.

## Official GitHub identity

The organization `standx-labs` is treated as official because its public `.github/profile/README.md` identifies "StandX Labs" and links directly to `https://standx.com`.

Public repositories found under the organization:

### Native StandX repositories
1. `standx-labs/stdc_assets`
   - created 2024-12-19;
   - last pushed 2025-04-07;
   - contains DUSD metadata/logo assets only;
   - no platform-token code or TGE artifact.

2. `standx-labs/stand_audit`
   - created 2025-03-12;
   - last pushed 2025-11-20;
   - contains six public audit PDFs for DUSD EVM/Solana and Highway EVM/SVM;
   - no Perps/SIP-5/platform-token source tree.

3. `standx-labs/.github`
   - organization profile only;
   - last pushed 2025-01-09.

### Forks / integration-support repositories
- `standx-labs/DefiLlama-Adapters` — fork.
- `standx-labs/defillama-dimension-adapters` — fork.
- `standx-labs/defillama-peggedassets-server` — fork used historically for DUSD listing/integration.
- `standx-labs/metamask-contract-metadata` — fork used historically for DUSD metadata.

The 2026 commits visible in the DefiLlama forks are upstream/general adapter work and must not be counted as StandX core development.

## Public GitHub development signal

The official public organization does not expose the current Perps engine, SIP-5 implementation, frontend, backend, matching engine, liquidation engine, token issuance code or platform-token contracts.

Organization-wide public code search on 2026-09-29 returned no matching TGE artifacts for:
- `TGE`
- `tokenomics`
- `platform token`
- `snapshot`
- `claim`
- `SIP-5`
- `utility token`
- `allocation`
- `governance token`

Therefore GitHub cannot be used as a direct current code-velocity meter for StandX core development. The core product is evidently developed outside the public repositories. Absence of public commits must not be interpreted as absence of private development.

The useful GitHub conclusion is narrower: there is currently no public pre-TGE code release, token-contract repository, tokenomics repository, claim/checker implementation or canonical platform-token contract artifact in the official organization.

## Actual product development state from first-party docs

### Completed / implemented
- SIP-1 Block Trade.
- SIP-2 Position Yield.
- SIP-3 DUSD Native Yield Expansion.
- SIP-4 Block Options.
- SIP-5A Community Maker Yield, release date 2026-07-05.
- SIP-5B Community Vaults, release date 2026-07-18.
- StandX Perps mainnet and programmatic REST/WebSocket API.
- DUSD on BNB Chain + Solana.
- Live Maker Yield accounting with DUSD Reward + Token Allocation fields.

### Still incomplete
- SIP-5 Universal Markets Listing: WIP.
- SIP-5C: Draft / "Cooooooking".
- Full permissionless market deployment: not demonstrated as complete in the current SIP status.
- Platform token issuance: not live.

This means StandX is in a late product-build phase around Universal Markets, while the token launch itself remains pre-hard-artifact.

## TGE hard-evidence audit

### Already present
- explicit first-party statement that a future platform token exists;
- token utility hook in SIP-5 Sponsor staking;
- Maker Yield platform-token allocation accounting;
- live user-facing Token Allocation field;
- historical/monthly and current/daily token allocation mechanics.

### Still missing
- official token name/ticker;
- total supply;
- distribution/tokenomics;
- TGE circulating supply;
- team/foundation allocation and vesting;
- points-to-token conversion;
- final points snapshot;
- eligibility checker;
- canonical mint/contract;
- claim page;
- exact TGE date;
- exchange listing announcement;
- public issuance/deployment code.

## TGE interpretation

The strongest new finding from the GitHub check is negative evidence with a clear boundary:

- there is no public token-launch code path in the official GitHub;
- the public GitHub is too sparse to measure current core engineering velocity;
- the official product docs show substantial live shipping, but the remaining SIP-5 roadmap is still incomplete;
- the token accounting rail exists, which shows preparation for eventual distribution;
- the usual final-stage launch artifacts have not surfaced.

Current classification:
- Project maturity: production / real usage.
- Product roadmap: SIP-5 partial rollout.
- Token readiness: PRE-TGE.
- TGE readiness: WATCH / TGE-PREP, not SETUP.

Do not upgrade to TGE-imminent based on GitHub activity alone.

## Prediction-market cross-check

Recent Polymarket snapshots in late September still assign a meaningful probability to a launch by 2026-12-31, but the timing market is thin relative to the FDV market and snapshots have moved materially. Use it as weak market sentiment, not launch evidence.

The FDV market has substantially more volume, but every year-end FDV threshold resolves NO if no token launches by 2026-12-31, so those prices mix launch timing and valuation.

## Upgrade triggers

Promote TGE readiness only when one or more hard artifacts appear, with two independent hard artifacts preferred before calling the launch close:
- tokenomics / total supply;
- final snapshot;
- points-to-token conversion;
- eligibility checker;
- canonical platform-token mint/contract;
- claim page;
- exact TGE date;
- initial circulating supply;
- exchange/DEX listing details;
- official public token deployment or audited issuance contract.

## Source hierarchy used

Primary:
- official StandX GitHub organization and repositories;
- official StandX SIP index and SIP-5/5A/5B documents;
- official StandX Maker Yield page and API docs.

Secondary/corroboration:
- Polymarket timing and FDV markets.

No Chinese-language website was used as confirmation evidence.
