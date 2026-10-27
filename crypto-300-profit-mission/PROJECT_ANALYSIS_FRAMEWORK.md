# Crypto Project Analysis Framework

Updated: 2026-10-27
ICO execution-priority clarification: user is an experienced participant in MetaDAO and other ICOs; use the single project's measurable business and launch ROI as the default decision frame.
Scope: ICO / token sale / launchpad / testnet / mainnet / DeFi / perp DEX / infra / RWA / NFT / game / agent competition / early protocol.
Purpose: provide one reusable research process for future ChatGPT conversations so project analysis is consistent, evidence-driven and auditable.

This file governs **project analysis**, not transaction execution. Execution plans, wallet actions and live orders belong in the relevant `positions/` files and require separate authorization.

Related deep-dive authority:
- `token_trading_principles.md` for token/contract/holder/liquidity analysis.
- `watchlists/famous-token-launch-radar.md` for discovery.
- `MISSION_SPEC.md` for Mission-wide policy and execution boundaries.

## 0. User-confirmed ICO analysis priority (2026-10-27)

**Default objective for ICO / curated raise / public token sale research:** estimate the return from paying the public sale price and selling into actual post-TGE liquidity. Prioritize the issuer's verified business metrics, financing and cap, token float/unlocks, expected exit liquidity, market attention, prediction markets, and an evidence-grounded price/FDV and ROI range.

- The user is an experienced ICO participant (including MetaDAO). Skip introductory participation tutorials, KYC/geographic/legal risk screening, and generic explanations of common MetaDAO mechanics unless the user specifically asks. Real contract-enforced eligibility, allocation caps, refunds and irreversible transfer restrictions materially affecting a trade remain in scope.
- Do **not** treat tokenholder dividends, legal ownership, IP/equity claims, discretionary buybacks, governance rights or other ancillary benefits as required ICO valuation gates. Research any such item only if the user requests it or an **existing, verifiable mechanism materially affects token trading demand, cash flows, dilution or exit liquidity**. Do not presume a benefit exists.
- Do **not** compare the researched project to the user's previous ICOs, other unrelated projects, or launchpads by default. Keep analysis anchored to the requested project. Only use external peers, industry benchmarks or platform historical ROI when the user asks or when a specific quantitative comparison is essential and explicitly identified; never add comparisons for filler.
- Perform a **mandatory project-specific prediction-market scan**, including in short/fast-pass reports. If no live relevant market is found after an actual search, state **"未检索到可验证的项目专属 PM 市场（注明平台和检索日期）"**. Do not invent probabilities or import odds from unrelated projects.
- The central business data must distinguish **verified production metrics / issuer claims / missing data**. Metrics are insufficient if no credible independent source; state what is unverifiable. A speculative ICO ROI scenario is a forecast, never a fact.
- Existing Mission trading NO_GO, wallet/funding authorizations, and source-integrity rules remain unchanged. Project research does not authorize a trade or automation.

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

**This is the highest-priority substantive section for IPO/ICO initial research.** Start with real operations and revenue before polishing the token narrative. For all metrics record the observation period, source, unit, data grain, and independent verification status.

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
- growth by week/month;
- DAU/WAU/MAU, paying users and activation-to-paid conversion;
- revenue from paying customers and actually collected fees, separated from GMV/notional volume, incentives and deposits;
- weekly/monthly growth, retention cohorts, churn and repeat purchase/trade rate;
- gross margin, payouts/rewards, acquisition/referral expenses, cash burn and runway where observable;
- trading products: active real funded accounts, simulated versus executed notional, true paid desks, real payout count/USDC transferred, average fee per paying account, net platform revenue and payout-liability coverage.

If the project exposes only demo traffic, historical cumulative simulations, a waitlist, or self-reported user numbers, **do not promote these to paid production business metrics**. Present a compact `metric / period / value / first-party or chain evidence / verification status` table; leave unknown entries explicitly unverified.

For every metric, ask:
- production or testnet?
- organic or incentivized?
- unique users or sybil addresses?
- real economic value or free activity?
- gross volume or wash volume?
- current or cumulative?

Do not use cumulative volume as a substitute for current activity.

## 9. Step 6: tokenomics / float / insider costs / dilution

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
- buyback/burn mechanics **only when explicitly published and verifiably material to trading supply/demand**.

Then answer:
- what is the public buyer's effective cost basis and implied final FDV?
- what is the real public unlock and effective post-TGE free float?
- which insider, team, market-maker and early-bid tranches can sell, and when?
- how quickly can circulating supply expand and how large is the expected sell pressure?
- what verifiable market demand or catalyst can absorb selling?
- what exit price, liquidity and sell slippage are needed for the target ROI?

Do not create a default section about equity/dividend/IP/revenue entitlements; those are optional only under Section 0.

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
- **actual onchain sale eligibility and per-wallet cap**, when relevant to transaction execution;
- official link.

Do not require routine jurisdiction/KYC/geographical investigation in the investment report. A verified transaction-level gate that directly changes whether an order can execute may be mentioned without a separate legal essay.

If final ICO price depends on total commitments, do not treat the current implied price as locked.

If participation is free or near-free, quantify time/compute/opportunity cost anyway.

## 13. Step 10: launchpad mechanics relevant to this sale

For experienced launchpad users, inspect **this specific sale's** currently effective rules: actual accepted commitment versus gross subscriptions, accepted cap, special allocations, time weights, claim, refund, first tradable liquidity and possible allocation concentration. Do not restate elementary platform mechanics or previous unrelated launch performance unless requested. Mark unavailable live configuration UNVERIFIED.

## 14. Step 11: standalone valuation of the researched project

Build scenarios from **this project's** observed operating performance, actual fundraising range, accepted commitments, complete token supply, expected initial float, listing liquidity and probable market demand. No automatic comparison with previous ICOs or unrelated tokens. External stage-matched benchmarks require a specific user request or an identified evidence need and must be labeled as optional context.

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

## 16. Step 13: mandatory prediction-market scan (PM)

**Required for EVERY project and EVERY initial ICO analysis, including fast-pass. Never omit without stating an actual search limitation.**

- Search project names, official domains, token symbols with disambiguation, raise title and issuer on **Polymarket, Kalshi, Limitless, Predict.fun, and other relevant active PM venues**. Also inspect any **actual project-specific MetaDAO decision-market** questions, when launched; do not mistake an unrelated token's futarchy/governance market for a forecast of the user's ICO ROI.
- Prioritize questions directly linked to public-sale profit: gross commitments (note distinct from accepted funds), accepted raise, implied FDV, TGE/listing timing, post-launch FDV or market cap thresholds, exchange listing, price above sale, and launch completion.
- For each VERIFIED matching PM: give exact question, immutable URL/market ID, venue, live versus resolved status, probability or priced threshold, volume, liquidity/depth/spread, last trade when possible, UTC and Bangkok observation time, resolution source, and any market-rule caveat.
- Separate `gross committed`, `net accepted`, `final price`, `FDV`, and `realizable exit`; a large subscription amount does not automatically mean a high final accepted valuation. Different thresholds must not be confused with each other.
- If search finds only another project or a token with the same ticker, exclude it. **If none verified: explicitly list checked venues and timestamp, write "未检索到可验证的项目专属 PM 市场", and do not fabricate a percentage.**
- Market prices are sentiment/liquidity signals, not verified TGE outcomes. Thin or stale odds require caution. Any assistant probability forecast must be explicitly separate from an observed PM price.

This section is a required independent evidence gate, not optional material to skip when results are empty.

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
- whether these valuations can be supported by this project's own actual business activity and executable exit liquidity.

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

A serious ICO/project review should answer, in this order:

1. Project identity, official links, specific sale stage, confirmed opening and closing time (Bangkok).
2. Actual currently working product and stage, with direct Git/contract/deployment evidence.
3. **Real business evidence**: period-scoped paying users, fee revenue, costs, payouts, volume quality, retention, growth and independent checks, distinctly labeling issuer claims.
4. Team, historical record, financing and actual investor terms/cost basis.
5. Sale mechanics: min/max/accepted raise, participant allocations and true final price formula.
6. Supply, insider allocations, lock/unlock, public float, new issuance and expected sell pressure.
7. Current or planned DEX/CEX trading venues, launch liquidity, depth and realistic exit slippage.
8. **Mandatory PM**: real project-specific prediction markets, implied probabilities, time, volume/liquidity and resolution conditions; or checked venues with explicit no-market finding.
9. Direct chain data, holder/fund movements, source-verified production security conditions and main risk to the capital.
10. Real social demand and market attention, separating independent interest from paid promotion.
11. Standalone downside/base/upside public-sale FDV, token price, sale cost, post-TGE exit potential, net ROI and conditions for each case.
12. Explicit verified gaps and current SKIP / WATCH / SETUP / ACTIVE decision.

Do not insert default separate sections on geographic/KYC/legal barriers, special tokenholder rights, comparative ICO histories, unrelated launchpads, or beginner MetaDAO tutorials. Refer to Section 0 for rare evidence-relevant exceptions.

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
- **verified paid business metrics, operating costs and real cash settlements**;
- **mandatory project-specific PM scan and explicit no-market result where appropriate**.

### Pass C: deep verification
Only if A and B remain interesting:
- onchain;
- holder clusters;
- launch transactions;
- security/admin;
- independent business metric verification;
- PM market rules, volume and liquidity recheck;
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

**identity -> verified paying business/production -> team/financing -> sale price and accepted raise -> insider basis/float/unlocks -> liquidity and executable ROI -> mandatory project-specific PM -> source/chain checks -> social-demand quality -> standalone scenarios -> decision state.**

The goal is to find where the market's price differs from the project's verifiable reality, while avoiding false precision and narrative-only conclusions.
