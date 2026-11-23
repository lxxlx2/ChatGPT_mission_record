# FLOP Network / Agent 路线经济收益、技术兑现与本地自动化尽调（2026-11-23）

Updated: 2026-11-23 Asia/Bangkok
Scope: single-project research; GitHub-first implementation is in agent/. This is research and read-only code, NOT permission to sign wallet, spend testnet coins, install launchd, trade or change the original monitoring tasks. Production NO_GO.

## 1. Current verdict

WATCH / EARLY_TESTNET_OPPORTUNITY / REWARD_AND_LIQUIDITY_UNVERIFIED.

The investment objective is **realizable cash earnings**, not a vanity count of requests, points, logins or online days. There is no official reliable US-dollar reward per task, FLOP market price, distribution per account, or credible ROI estimate. Do not call any testnet FLOP a dollar asset. Need actual eligible testnet spend, frozen cohort score formula, snapshot, eventual mainnet entitlement, unlock restrictions and executable trading liquidity.

Official Testnet opening is *targeted* 2026-11-24; as of 2026-11-23 there is no independently confirmed active Testnet genesis in this research. Devnet is accessible but earns no airdrop credit.

## 2. Identity and team

Official: https://flop.finance/ ; docs https://docs.flop.network/docs/official-links ; GitHub https://github.com/flop-labs .
The project claims founder/CEO Arthur Hayes and funding by Maelstrom, with more than two years runway at zero revenue. Treat these as **issuer statements** unless independent financing records establish investment flows. It says there is no equity raise or private token sale. It states team + foundation tokens are emitted over time, separate from its no-team-pre-mine claim. No third-party independent verification of runway was completed.

Source: https://docs.flop.network/docs/team-and-company and https://docs.flop.network/docs/tokenomics-and-supply .

## 3. Product and repository evidence

FLOP describes a Substrate-based proof-of-useful-inference network. Public Devnet RPC and gateway exist; live end-to-end demand, independent purchasers, revenue, retained activity, mainnet production throughput, real fees and competitor benchmarking were NOT fully audited in this pass.

Official GitHub flop-labs/network is **issues, public release notes and intake**, explicitly states core code lives elsewhere. Do not present an active commit in that repo as a live deployed release, and do not infer Testnet genesis from tagged CLI releases.

2026-11-23 official public release evidence:
- https://github.com/flop-labs/network/blob/main/releases/cli/v0.8.0.md : CLI 0.8.0 requires SDK 0.9.0, version compatibility and escrow/settlement fixes.
- https://github.com/flop-labs/network/blob/main/releases/cli/v0.7.0.md : faucet request telemetry, public catalog qualification.
- https://github.com/flop-labs/network/blob/main/releases/cli/v0.6.0.md : direct Hermes macOS/Linux, durable request recovery, bounded wallet-funded escrow. CLI docs explicitly say direct mode never automatically enrolls or calls faucet.
- https://github.com/flop-labs/yellowpaper : normative specifications, with conversion score caps/aggregation, genesis bridge and locked credit implementation still partial/open.

High-risk original developer issue: https://github.com/flop-labs/network/issues/229 documented absent publicly reachable direct Miner offers on Devnet. Another issue https://github.com/flop-labs/yellowpaper/issues/172 showed broker/gateway-paid channels opening under broker wallet; inference response for an enrolled user does NOT independently establish that user's wallet gets Era-T spend credit.

## 4. Genesis rewards and maximize-return rule

Source authority: https://flop.finance/whitepaper/ ; https://flop.finance/testnet/ ; https://flop.finance/intro/yellowpaper/ §8.2 R8.4, R8.5; https://docs.flop.network/docs/agent-onboarding ; https://docs.flop.network/docs/testnet-and-timeline .

Issuer design: 1.2 billion FLOP Agent cohort at genesis. Spec R8.4 requires scoring based on **settled compute-channel spending**, not completed job count or active days. Faucet grants, merely held balances and DID creation do not score. The complete conversion score formula, sublinear/cluster treatment and all rollout mechanics are NOT frozen. No evidence-based basis for 4 calls/day or 4, 40 or 400 calls/day maximum.

The rational objective is maximize **eligible spend attributed to the SAME user-controlled Agent address**, within actual per-identity Faucet quotas and network capacity, using genuine independent Miner demand with finality and no double charge. No multi-wallet bonus or self-controlled Agent/Miner circular paid activity. Testnet balances do not convert at a fixed ratio: the airdrop is computed from eligible verified work and snapshot inputs.

Official says early eligible contribution may benefit from lower competition, but NEVER infer exact $ROI from that. Testnet Faucet final quotas and window unknown as of this research. Devnet published 500 FLOP base, up to 2,000 per grant, 2,000 per rolling week, 24h cooldown for linked tier, **NOT Testnet terms**.

Mainnet Agent rewards are initially locked: specified spend-to-unlock principle is 3 FLOP of locked inference spending to release 1 FLOP, without time-based expiry. The exact production implementation and onchain rights are not yet audited. This means theoretical entitlement is not instantly liquid.

## 5. Economics, costs, and risk

- Mac M4 Max 48GB: enough for Agent HTTP client, scheduler, local dashboard and SQLite, no NVIDIA Miner GPU required.
- Local Python standard library, GitHub public API (subject to rate limits), and local dashboard: **no separate paid LLM API or external subscription required**.
- Real Agent inference is NOT free in FLOP units; on Testnet official faucet is planned to supply non-tradable test FLOP, with unknown future grant limits and network fees. Do NOT spend real USDC, SOL, ETH, mainnet FLOP or use an investor portfolio wallet.
- There is no confirmed FLOP spot-market price or listing, so $ income and break-even cannot be estimated. Mac power, developer time and reliability have opportunity costs.
- Community adapters or broker APIs can complete a chat turn without crediting the user's own wallet. A successful HTTP 200 or output is NOT a proved eligible contribution. Check channel payer/opening account, actual settled payable, finalized block and scoring inclusion.
- Case study risks: protocol release drift, unavailable Miner endpoint, testnet delays, faucet quota, wallet enrollment shared cap, direct sessions failing after channel opened, ambiguous refund/settlement, snapshots and concentration filters, unknown final token release rules.
- Mainnet tradability and crypto profit are a separate later decision. Do not infer support from token clones or unrelated project names.

## 6. Prediction-market scan

Checked project-specific FLOP token/TGE/price markets on Polymarket, Kalshi, Limitless and Predict.fun through public search on 2026-11-23. **未检索到可验证的项目专属 PM 市场**. A general Kalshi token launch market listing other projects is not evidence of FLOP-specific odds. No inferred odds.

## 7. Evidence-based first test gates

T0: offline agent + dashboard/read-only tests PASS in isolated execution; zero spend.
T1: confirm official Public Testnet is actually active; record chain genesis/hash, runtime spec and CLI/SDK version. Planned date is insufficient.
T2: private test wallet and DID, no key in Git; verify faucet real balance and current quota on Testnet, not Devnet.
T3: identify authenticated, public, registered, healthy independent Miner and compatible model, preflight real session quote and maximum amount.
T4: manually authorize ONE small Testnet direct session, capture signed output and channel, reconcile onchain finalized payer and payable, ensure own wallet is opener.
T5: independently verify the chain-score attribution policy, source and wallet-specific credit; only then promote to candidate for sustained operation.
T6: design dynamic allocation: actual faucet budget and remaining rate limit, eligible verified paid amount, quote/cost and successful finality, no arbitrary calls/day cap. Sequential single-wallet signing lane, persistent spend escrow, TTL/circuit breaker for unknown settlement, independent receipt reconciliation.
T7: local dashboard: source freshness, eligible settled spend, unverified receipts, Testnet quota/head, estimated volume capacity, unknown future payout, risk alerts. Monitor access only localhost.
T8: after user separately approves deployment and budget, schedule running through macOS launchd. No Gmail, trading, existing mission task changes, secondary wallets, proxy broker scoring assumptions or production signing without separate authorization.

Current state: T0 offline code/test only; T1 onward UNVERIFIED/NOT_EXECUTED. Draft branch/PR evidence is required before telling user code is delivered.

## 8. Review checklist before unlocking payment

1. Original GitHub/official documentation and exact network identity; immutable version tag.
2. First own-wallet direct settled channel on real Testnet.
3. Direct finality, payer and score ledger. Gateway channel != credit until proved.
4. Dynamic Faucet/grant and no self-trade policies.
5. No secret keys in public repo, local 0600 state only.
6. Independent QA + Mac real run before production scheduling.
