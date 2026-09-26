# Crypto Project Analysis Framework

Updated: 2026-09-26
Scope: ICO / token sale / launchpad / testnet / mainnet / DeFi / perp DEX / infra / RWA / NFT / game / agent competition / early protocol.
Purpose: provide one reusable research process for future ChatGPT conversations so project analysis is consistent, evidence-driven and auditable.

This file governs **project analysis**, not transaction execution. Execution plans, wallet actions and live orders belong in the relevant `positions/` files and require separate authorization.

Related deep-dive authority:
- `token_trading_principles.md` for token/contract/holder/liquidity analysis.
- `watchlists/famous-token-launch-radar.md` for discovery.
- `MISSION_SPEC.md` for Mission-wide policy and execution boundaries.

## 1. Core research principles

Every project review starts by separating three layers:

1. **CONFIRMED**: official docs, official GitHub, official X, direct chain state, explorer data, audited contracts, signed launch records, regulator/company filings, first-party launchpad pages or other primary evidence.
2. **INFERRED**: conclusions supported by several independent facts but not explicitly confirmed by the project.
3. **SPECULATIVE**: valuation scenarios, adoption assumptions, future token probability, price path, market psychology and other forward-looking judgments.

Do not mix these layers.

A polished website, active X account, testnet, large transaction count or KOL support does not by itself prove commercial traction.

A low FDV does not by itself mean undervaluation.

A high TVL does not by itself mean sustainable revenue.

A project may be technically real and still be a poor token investment.

## 2. Source policy

Evidence order:

1. Direct chain / contract / transaction / wallet / LP / vesting data.
2. Official technical docs and official GitHub.
3. Official project, team, foundation and launchpad announcements.
4. Investor / exchange / partner first-party announcements.
5. Audits and legal/company filings.
6. High-quality market-data providers.
7. Prediction markets with real money and usable liquidity.
8. Independent technical researchers.
9. Reddit/community discussion.
10. KOL posts, screenshots and reposts.

Do not use Chinese-language websites as confirmation sources.

For material claims, return to the original source whenever possible.

When two sources conflict:
- prefer the newer primary source;
- preserve the conflict in the write-up;
- do not silently reconcile it;
- if unresolved, mark it UNRESOLVED.

## 3. Step 0: classify the project before researching

Identify the project type first because the relevant evidence differs.

Examples:
- ICO / public sale
- launchpad token
- pre-TGE points / airdrop
- testnet / L2 / L1
- perp DEX / spot DEX
- DeFi lending / vault
- RWA
- NFT / mint
- memecoin / creator token
- consumer app
- AI / compute / agent infrastructure
- game / competition
- protocol with existing token

Record:
- chain;
- canonical project name;
- official domain;
- official X;
- official GitHub/docs;
- canonical token or planned token identity;
- current stage;
- relevant deadline.

## 4. Step 1: establish canonical identity

Before discussing value, confirm exactly what is being analyzed.

Check:
- official domain and X;
- legal entity if available;
- canonical contract address / mint;
- current chain;
- old/migrated/fake contracts;
- official sale or mint URL;
- launchpad identity;
- whether the current token is the final economic asset;
- whether a future migration, bridge or mainnet swap exists.

If identity is unresolved, stop valuation and mark the project **IDENTITY_UNRESOLVED**.

## 5. Step 2: determine actual maturity

Use this stage ladder:

- Level 0: narrative only.
- Level 1: code / demo / docs.
- Level 2: public testnet.
- Level 3: production mainnet.
- Level 4: real users / volume / TVL / fees.
- Level 5: repeatable revenue / customers / real assets.
- Level 6: scaled network effects and durable growth.

Always state the current level.

For live competitions or protocols, distinguish:
- repository design assumptions;
- launch configuration;
- live runtime behavior.

Never extrapolate a simulation directly to live conditions without checking participant count, congestion, liquidity, latency and rule implementation.

## 6. Step 3: team and legal entity

Investigate:
- founders and core team;
- LinkedIn and prior employers;
- GitHub history;
- previous projects;
- prior successful exits or failures;
- company/legal entity and jurisdiction;
- team size;
- public technical contributors;
- whether deployer/team wallets can be linked to known entities.

Anonymous or thin teams require a higher risk discount.

A named founder with no independently verifiable history remains weak evidence.

## 7. Step 4: financing, investors and partners

Keep these categories separate:
- investor;
- strategic investor;
- incubator / accelerator;
- launchpad;
- exchange/listing venue;
- market maker;
- auditor;
- RPC/infrastructure provider;
- ecosystem partner;
- ordinary integration.

For financing record:
- amount raised;
- round date;
- valuation if known;
- token/equity structure;
- token price if known;
- unlock/cliff/vesting;
- investor allocation.

Do not infer "investment" from a logo wall, integration, grant, launchpad listing or technical partnership.

## 8. Step 5: product reality and traction

Prefer measurable production evidence.

Depending on project type, collect:
- TVL;
- AUM;
- open interest;
- DEX/perp volume;
- fees;
- protocol revenue;
- active addresses;
- depositors;
- unique traders;
- transactions;
- contracts deployed;
- inventory value;
- real-world assets;
- paying customers;
- validator count;
- compute capacity;
- marketplace utilization;
- retention;
- growth by week/month.

For every metric, ask:
- production or testnet?
- organic or incentivized?
- unique users or sybil addresses?
- real economic value or free activity?
- gross volume or wash volume?
- current or cumulative?

Do not use cumulative volume as a substitute for current activity.

## 9. Step 6: tokenomics / ownership / value capture

Record:
- total supply;
- TGE supply;
- circulating supply;
- initial circulation percentage;
- ICO/public allocation;
- team;
- treasury;
- ecosystem;
- investors;
- market maker;
- airdrop;
- staking/mining;
- unlock schedule;
- vesting contract;
- emission schedule;
- burn/buyback/revenue-share mechanics.

Then answer:
- what creates demand for the token?
- what cash flow or protocol value reaches token holders?
- what part is narrative only?
- what can create sell pressure?
- how quickly can circulating supply expand?

For a chain or infrastructure project, check whether value accrues to:
- a new token;
- an existing ecosystem token;
- gas asset;
- sequencer/validator economics;
- another protocol token.

Do not assume every new product needs a new token.

## 10. Step 7: chain, contracts and security

For live assets inspect:
- deployer;
- proxy;
- admin/owner;
- mint/freeze/pause/blacklist rights;
- LP ownership and lock;
- vesting contracts;
- treasury;
- bridges;
- upgrade authority;
- audits;
- past exploits;
- compensation history;
- unresolved incidents.

For pre-token/testnet projects inspect:
- RPC;
- explorer;
- faucet;
- live contracts;
- block production;
- public code;
- audit status;
- production bridge readiness.

Security incidents must be included even if users were reimbursed.

## 11. Step 8: market and liquidity

For a live token collect:
- current price;
- circulating market cap;
- FDV;
- main pool;
- quote asset;
- liquidity;
- 24h / 7d / 30d volume;
- holder concentration;
- top 10/top 20 excluding LP/CEX where possible;
- buy/sell price impact;
- major CEX listings;
- derivatives/OI/funding if relevant.

Always distinguish paper market cap from executable exit liquidity.

## 12. Step 9: participation mechanics

For ICO, mint, testnet, points or competition, record exact mechanics:

- start/end;
- Bangkok-local deadline;
- minimum/maximum contribution;
- currency/chain;
- wallet requirements;
- KYC/geography;
- refund rules;
- soft cap;
- hard cap;
- final pricing formula;
- allocation formula;
- TGE unlock;
- vesting;
- claim process;
- gas requirements;
- lockup;
- referral effects;
- eligibility;
- official link.

If final ICO price depends on total commitments, do not treat the current implied price as locked.

If participation is free or near-free, quantify time/compute/opportunity cost anyway.

## 13. Step 10: launchpad/platform history

If a sale uses a launchpad, analyze the platform's prior launches separately.

For comparable past launches capture:
- sale date;
- raise;
- contributor count;
- ICO price;
- TGE/opening price;
- first-day market cap;
- initial FDV;
- first-week ATH;
- time to ATH;
- post-launch drawdown;
- liquidity;
- refunds/failures.

Do not judge a launchpad only by anti-rug mechanics.

A structurally clean launch can still have poor secondary-market ROI.

## 14. Step 11: comparable valuation

Comparables must match the project's stage.

For projects that already launched, use:
- TGE day;
- first 24-48h;
- or earliest reliable public trading data.

Do not use today's mature market cap as the primary comparison for a new launch.

Control for:
- stage;
- circulating ratio;
- product maturity;
- revenue;
- users;
- TVL/AUM;
- liquidity;
- financing;
- exchange distribution;
- market regime.

For pre-TGE valuation build at least:
- downside case;
- conservative case;
- base case;
- strong-launch case.

Show both:
- circulating market cap;
- FDV;
- implied token price.

## 15. Step 12: TVL/revenue valuation discipline

Use TVL only when economically meaningful.

Check:
- is TVL productive or mercenary?
- does the protocol earn fees?
- what is annualized revenue?
- who captures revenue?
- how much is subsidized?
- is TVL concentrated in one whale or treasury?
- is the asset liquid?

Useful ratios may include:
- MC / TVL;
- FDV / TVL;
- MC / annualized revenue;
- FDV / annualized revenue;
- revenue yield to circulating market cap;
- buyback yield.

If no real mainnet TVL or revenue exists, say so and avoid fake precision.

## 16. Step 13: prediction markets

Search for:
- TGE timing;
- FDV;
- valuation thresholds;
- launch date;
- regulatory/event outcomes relevant to the project.

For every prediction market record:
- market;
- probability;
- volume;
- depth/spread when available;
- resolution criteria;
- observation time.

Thin prediction markets are signals, not truth.

Independent markets with overlapping questions can reveal disagreement or timeline uncertainty.

## 17. Step 14: social/KOL quality

Measure more than follower count.

Check:
- official account growth;
- post views;
- likes/replies/reposts;
- unique accounts discussing;
- known high-signal builders/traders;
- obvious referral links;
- coordinated posting;
- paid-looking copy;
- whether KOLs disclose ownership/incentives;
- Reddit/community sentiment;
- whether discussion is technical, product-driven or purely price-driven.

Separate:
- organic builder attention;
- launchpad/internal promotion;
- affiliate/referral promotion;
- paid KOL campaigns.

Low engagement around a supposedly huge raise or user count is a consistency warning.

## 18. Step 15: internal consistency checks

Before concluding, cross-check claims against each other.

Examples:
- claimed users vs active wallets;
- claimed volume vs liquidity;
- claimed TVL vs contract balances;
- claimed soft-cap status vs live launchpad commitments;
- claimed team size vs public contributors;
- claimed mainnet vs technical docs still saying testnet;
- claimed investor vs investor's own portfolio;
- claimed token lock vs ordinary EOA balances;
- claimed decentralization vs team-run validators.

Inconsistency is itself a risk factor.

## 19. Step 16: scenario valuation and payoff

For an ICO or early token, calculate:

- current/final token price;
- TGE supply;
- circulating market cap;
- FDV;
- liquidity at launch;
- amount of unlocked sale tokens;
- expected sell pressure;
- potential 2x/5x/10x valuation thresholds;
- required market cap for each multiple;
- whether those thresholds are plausible versus stage-matched peers.

For a prize/airdrop:
- estimate token value from plausible TGE market cap;
- apply unlock/claim timing;
- apply dilution;
- apply project-failure/time discount;
- distinguish gross prize pool from expected value per participant.

For points:
- explicitly state all unknown allocation assumptions.

## 20. Step 17: decision state

Use one of four project states:

### SKIP
Structural problem, unresolved identity, poor economics, excessive valuation, bad liquidity or unacceptable security.

### WATCH
Real project, but current edge is unclear or key evidence is still missing.

### SETUP
Evidence is sufficiently strong and there is a defined event/valuation/participation condition worth acting on after user review.

### ACTIVE
The user already has exposure or has explicitly delegated execution elsewhere.

For analysis-only conversations, ACTIVE means "track the thesis and facts"; it does not authorize execution.

## 21. Required final output

A serious project review should answer, in this order:

1. What exactly is the project?
2. What stage is it really at?
3. Who is the team and what have they done?
4. Who funded it and on what terms?
5. What is already working in production?
6. What are the real usage / TVL / revenue / user metrics?
7. What is the token or ownership model?
8. What is the current/final sale valuation?
9. What does initial circulating market cap look like?
10. What are stage-matched TGE comparables?
11. What is the current liquidity/exit risk?
12. What does the launchpad/platform's historical performance look like?
13. What do prediction markets say, if any?
14. What does social/KOL activity actually look like?
15. What security or governance risks exist?
16. What are the main upside catalysts?
17. What could permanently break the thesis?
18. What is the scenario valuation range?
19. What facts remain unknown?
20. Current state: SKIP / WATCH / SETUP / ACTIVE.

Avoid a generic conclusion such as "high risk, DYOR." Explain the actual mechanism producing the risk or opportunity.

## 22. Fast-pass workflow

When time is short:

### Pass A: 5-minute identity gate
- official website/X/GitHub;
- canonical token/sale URL;
- chain;
- deadline;
- obvious scam/conflict check.

### Pass B: 15-minute economic gate
- stage;
- team;
- raise;
- tokenomics;
- TGE circulation;
- current/final implied valuation;
- liquidity;
- real product metrics.

### Pass C: deep verification
Only if A and B remain interesting:
- onchain;
- holder clusters;
- launch transactions;
- security/admin;
- comparable TGE history;
- launchpad historical ROI;
- prediction markets;
- social graph/KOL;
- scenario valuation.

This keeps research effort proportional to potential value.

## 23. Reusable lessons from recent cases

### FLOP / Technocore Close Call
- Repository simulations are useful design evidence, but live participant count and runtime conditions can invalidate naive win-rate extrapolation.
- A signed/seeded launch configuration has more authority than a stale repository label.
- Live congestion, stale reference prices and sybil participation materially change strategy quality.
- Prize valuation requires TGE supply, initial circulation, claim timing and stage-matched launch comparables.
- For already-launched analogues, compare initial/TGE market cap, not present-day market cap.

### bye.fun / SagaPad
- Current implied ICO price may change if final price is a function of total commitments.
- Very low FDV can create asymmetric upside, but thin LP can make paper gains impossible to realize.
- Sale proceeds flowing to LP/inventory can improve backing while unlocked public-sale supply still creates sell pressure.
- Launchpad structural safeguards must be evaluated separately from historical investor ROI.
- A real adjacent market such as tokenized TCG validates category demand, but does not prove the small project can capture it.

### RISEx / Elysium
- Real trading volume, OI, fees and production usage are materially stronger evidence than roadmap claims.
- Security incidents remain relevant even after reimbursement.
- Points-campaign end dates must not be converted into assumed TGE dates.
- Infrastructure value capture may accrue to an existing token or gas asset, reducing the probability that a new token is required.
- Testnet transaction counts do not prove production demand.

## 24. Handoff rule for future conversations

When another conversation takes over a project:

1. Read `MISSION_SPEC.md`.
2. Read this file.
3. Read `token_trading_principles.md` if a token is involved.
4. Read the project's current position/watchlist/research file if one exists.
5. Prefer the newest GitHub state over older chat memory.
6. Re-verify time-sensitive facts before changing a conclusion.
7. Preserve CONFIRMED / INFERRED / SPECULATIVE labels.
8. Write material new findings back to the Mission repository.
9. Do not silently replace an earlier thesis; record what changed and why.
10. Keep analysis and execution separate unless the user explicitly delegates execution.

## 25. Final discipline

The reusable sequence is:

**identity -> stage -> team -> financing -> product reality -> token/value capture -> chain/security -> market/liquidity -> participation mechanics -> launchpad history -> TGE comparables -> prediction markets -> social quality -> consistency checks -> scenario valuation -> decision state.**

The goal is to find where the market's price differs from the project's verifiable reality, while avoiding false precision and narrative-only conclusions.
