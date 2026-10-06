# Project Analysis Evidence Workflow

Updated: 2026-10-06
Scope: crypto / Web3 project research, especially pre-TGE, airdrop, points, launchpad, L1/L2, DeFi and early token projects.
Purpose: define how to determine a project's **actual stage** from verifiable evidence rather than announcements, KOL interpretation or marketing language.

This file describes **research methodology only**. It does not authorize trading, wallet actions, monitoring, automation or production execution.

Related authority:
- `PROJECT_ANALYSIS_FRAMEWORK.md`
- `token_trading_principles.md`
- `MISSION_SPEC.md`

## 1. Default stance: claims are leads, not facts

Start from an adversarial assumption:

- project posts are leads;
- founder/KOL posts are leads;
- screenshots are leads;
- roadmap language is not execution evidence;
- an SDK interface is not a deployed contract;
- a contract ABI is not a live contract;
- a frontend button is not a successful claim;
- a token logo/name is not a canonical token;
- an unlock schedule is not proof that tokens were sold;
- a prediction-market price is not truth.

Upgrade a claim only after it is independently reproduced from stronger evidence.

For every material conclusion label it as:
- **CONFIRMED** — directly verified;
- **INFERRED** — several verified facts support it, but attribution/timing is incomplete;
- **SPECULATIVE** — forecast, scenario or interpretation.

## 2. Evidence hierarchy

Use this order whenever sources conflict:

1. Direct chain state / transaction / contract bytecode / logs / balances.
2. Canonical deployment configuration tied to the live network.
3. Official source repository and commit history.
4. Official SDK / ABI / technical docs.
5. Official website / X / Discord / team statements.
6. Exchange, investor, launchpad or partner first-party statements.
7. Independent market-data providers.
8. Prediction markets with real liquidity.
9. Independent researchers.
10. KOL posts, reposts and screenshots.

A lower-level source may generate a hypothesis, but it cannot override contradictory higher-level evidence without explanation.

Do not use Chinese-language websites as confirmation sources.

## 3. First establish canonical identity

Before judging progress, determine exactly what object is being researched:

- official project/foundation/entity;
- official website;
- official GitHub organization/repository;
- chain/network;
- canonical token contract/mint if one exists;
- deployment repository/configuration if applicable;
- relevant application/backend/SDK repository;
- current mainnet/testnet environment;
- whether a new token, existing ecosystem token or no token is expected.

Do not attribute a GitHub repository to a project merely because it contains the project name or token contract.

Third-party scanners, bots, analytics repos and forks are secondary evidence only.

If canonical identity is unresolved, use `IDENTITY_UNRESOLVED` and stop high-confidence attribution.

## 4. Git analysis: inspect time, ownership and meaning

A Git finding is useful only after answering three questions.

### 4.1 Is the repository actually attributable?

Confirm through one or more of:
- official organization ownership;
- official website links;
- known project contributors;
- organization/domain metadata;
- direct references from another canonical repository.

### 4.2 When was the relevant code introduced?

Always inspect commit history for material findings.

Do not describe an old feature as a new TGE signal merely because a researcher found it today.

Record:
- first commit containing the feature;
- latest modification date;
- whether it exists only on a branch or on the default/main branch;
- whether the commit was merged;
- whether it changes code, config, docs or only branding.

The date the market discovers evidence and the date the evidence was created are different facts.

### 4.3 What does the code actually prove?

Classify Git evidence into layers:

- **Interface only**: type, enum, ABI, schema, placeholder, TODO.
- **Client support**: SDK can query/call the feature.
- **Backend/indexer support**: server/API exposes data.
- **Deployment config**: live environment points to a non-zero real address.
- **Frontend integration**: user-facing path exists.
- **Runtime proof**: chain transactions/logs prove it is being used.

Do not skip layers.

Examples of invalid inference:
- ABI exists -> contract is deployed.
- `claim()` exists -> claim is live.
- `airdrop` API exists -> TGE is imminent.
- frontend mentions token -> canonical token is deployed.

## 5. Deployment configuration is a high-value truth source

For projects with public deployment manifests, always inspect the production/mainnet file.

Check:
- contract addresses;
- zero-address placeholders;
- network IDs;
- deployer;
- proxy/admin;
- token addresses;
- distributor/airdrop/staking addresses;
- version tags;
- start block;
- environment-specific differences.

A production deployment field equal to `0x000...000`, null, empty or a documented placeholder is strong evidence that the corresponding component is not currently connected to that deployment.

Conversely, a non-zero address is not enough by itself: inspect bytecode, creation transaction and runtime activity.

## 6. Chain analysis: verify deployment, funding and runtime behavior

Once an address is identified, move to direct chain verification.

For a pre-TGE or airdrop project, check in roughly this order:

1. token contract creation;
2. total supply / mint behavior;
3. owner/admin/proxy/mint authority;
4. treasury/foundation/distributor wallets;
5. airdrop/vesting/staking contracts;
6. initial funding of distributor contracts;
7. Merkle root / epoch / claim configuration;
8. approvals and role grants;
9. first real claims/transfers;
10. exchange/market-maker/liquidity preparation if relevant.

Distinguish:
- contract exists;
- contract is configured;
- contract is funded;
- contract is callable;
- contract has actually been used.

These are separate stages.

Never call a wallet `team`, `treasury`, `insider`, `distributor` or `market maker` without independent attribution.

Wallet clustering may support `COORDINATED_WALLET_CLUSTER`, but attribution stays unresolved until linked to an entity.

## 7. For TGE, use an evidence ladder instead of announcement counting

Recommended TGE readiness ladder:

### T0 — Narrative
Only discussion, branding, roadmap or social speculation.

### T1 — Token intent
Official product/brand/code clearly anticipates a token or allocation mechanism.

### T2 — Allocation/data layer
Eligibility, points conversion, allocation API, snapshots or Merkle data structures exist.

### T3 — Claim architecture
ABI/SDK/backend supports claim, vesting, staking or rewards logic.

### T4 — Mainnet deployment
Canonical token/distributor/claim contracts are deployed and production configuration points to real addresses.

### T5 — Funding/configuration
Supply is minted/allocated, distributor is funded, roots/epochs/roles are configured, and tokenomics or unlock data can be reconciled.

### T6 — User-facing readiness
Official eligibility/claim page, terms, claim instructions and supported wallets/networks are live.

### T7 — Market readiness
Exchange deposits/listing notices, market-maker/liquidity preparation or canonical pools appear.

### T8 — TGE live
Claim/trading/transfers are executing on-chain.

A project may be T2/T3 for months. Do not convert architecture readiness directly into a date prediction.

## 8. Separate product progress from token progress

A chain or application may be fully live while its token is not close to launch.

Evaluate separately:

- product maturity;
- user/TVL/revenue maturity;
- token design maturity;
- token deployment readiness;
- market/listing readiness.

Mainnet activity, TVL or user growth proves the product exists. It does not prove a new token has been deployed or is near TGE.

## 9. Frontend analysis: distinguish branding from functionality

Inspect official frontend repositories for:

- token name/symbol;
- eligibility;
- claim;
- allocation;
- vesting;
- tokenomics;
- wallet network checks;
- contract constants;
- exchange/bridge links;
- feature flags;
- environment variables;
- hidden routes/components.

Classify findings:

- visual/brand preparation;
- dormant code;
- disabled feature;
- active production route;
- runtime API/contract integration.

Brand assets and a token-themed redesign are useful signals of internal preparation, but they are weaker than live contract integration.

## 10. Prediction markets: use them as a pricing layer, not a fact layer

For TGE/date/FDV markets record:

- exact question;
- resolution criteria;
- current probability/price;
- volume;
- liquidity/depth/spread if available;
- observation time;
- whether the market moved after a new public signal.

Prefer larger/liquid venues. When multiple venues exist, compare them rather than defaulting to one platform.

Prediction markets answer:
`What is the market willing to pay for this outcome now?`

They do not answer:
`What is objectively true?`

Use them after Git/chain verification, not before.

## 11. Detect information-quality traps

Common traps:

### Discovery-time trap
A researcher discovers six-month-old code today and calls it a new development.

Fix: inspect commit introduction date.

### Interface/deployment trap
A claim method or ABI exists but the production address is zero/unset.

Fix: inspect production deployment config and chain bytecode.

### Branding/TGE trap
A token website, logo or copy exists.

Fix: look for canonical token deployment, allocation and distributor funding.

### Mainnet/token trap
The product mainnet is active, therefore the token is assumed imminent.

Fix: score product and token readiness separately.

### Wallet-attribution trap
Coordinated transfers are assumed to be team activity.

Fix: preserve attribution as unresolved until independently linked.

### Announcement-count trap
Several KOL/project posts repeat the same source and appear to be independent confirmation.

Fix: trace every claim back to its original evidence.

### Prediction-market anchoring
A market moves sharply after a rumor and the new price is treated as verification.

Fix: inspect the underlying evidence that caused repricing.

## 12. Internal consistency tests

Before assigning a stage, reconcile the evidence.

For TGE/airdrop research ask:

- Does the SDK expect a contract that production config leaves unset?
- Does the frontend expose a claim route but no contract address?
- Is there an allocation API but no funded distributor?
- Is token supply known but no canonical token contract exists?
- Is a vesting schedule published but no vesting contract can be found?
- Does a supposed launch window conflict with unresolved regulatory/technical dependencies?
- Do project statements claim readiness while Git still contains deployment TODOs/placeholders?
- Does a prediction-market move come from genuinely new evidence or rediscovery of old code?

Contradictions are findings. Do not silently smooth them over.

## 13. Timeline forecasting

Only forecast TGE timing after the readiness ladder is established.

A forecast should explain what remains between current state and launch.

Examples of milestone triggers that materially increase probability:
- zero-address deployment fields become canonical non-zero contracts;
- canonical token contract appears;
- total supply and allocation reconcile with tokenomics;
- distributor/vesting contracts receive inventory;
- Merkle roots/epochs are configured;
- official claim/eligibility frontend goes live;
- exchange deposit/listing infrastructure appears.

Do not increase probability merely because:
- community discussion increases;
- branding changes;
- an old SDK function is rediscovered;
- project staff say `soon`;
- a prediction market itself rises.

## 14. Required output format for progress checks

When the user asks for `实际进度`, return the answer in this order:

1. **Current actual stage** — one-line verdict.
2. **New hard evidence** — only what changed since the previous review.
3. **Git** — canonical repo, commit dates, exact meaning.
4. **Deployment/chain** — real addresses, bytecode, funding, runtime activity.
5. **Frontend/backend** — active versus dormant integration.
6. **Prediction markets** — probability, volume and whether repricing is justified.
7. **What is still missing** — explicit blockers.
8. **Updated probability/judgment** — clearly marked as analysis, not fact.

Do not lead with project marketing.

## 15. State changes require evidence

Do not upgrade a project solely because of more discussion.

Recommended state-change rule:

- `WATCH -> SETUP` requires at least one meaningful new primary-source or chain milestone and a defined participation/valuation edge.
- `TGE_SOON` should require deployment/configuration evidence, not just code architecture.
- `CONFIRMED_TGE` requires official timing or equivalent hard launch mechanics that can be independently verified.
- `TOKEN_DEPLOYED` requires canonical identity plus direct chain verification.
- `CLAIM_LIVE` requires a live official path plus successful chain execution.

If new evidence is insufficient, keep the previous state and say why.

## 16. Minimum standard before calling a pre-TGE project "close"

At minimum, look for several of the following together:

- canonical token contract or explicit token deployment;
- non-placeholder production airdrop/distributor address;
- funded distributor/vesting inventory;
- tokenomics and circulating supply;
- eligibility/allocation data;
- production claim integration;
- exchange/liquidity preparation;
- specific launch/claim timing.

One item alone is not enough.

The purpose of this workflow is to answer one question consistently:

**What has actually happened, what is merely prepared, and what still has to happen before the investment event becomes real?**
