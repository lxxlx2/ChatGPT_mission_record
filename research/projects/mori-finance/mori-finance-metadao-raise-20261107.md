# Mori Finance / MetaDAO curated raise — evidence-first ICO diligence (2026-11-07)

## 2026-11-14 ~02:05 Bangkok: Mori Closed, finalized onchain allocation for user's 700 USDC commitment

**Direct finalized Solana RPC**, MetaDAO v0.7 launch program `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM`. This section supersedes older `Live` / `approved_amount=0` snapshots. No wallet action, claim, transfer, automation or monitoring performed.

- Launch PDA `BFVqq3Br9frUabrdgczu4obJ2TGNzKnys42j2pwrmXGZ` actual **`Closed`**, `unix_timestamp_closed=1794596431` = **2026-11-13 19:00:31 UTC / Nov 14 02:00:31 Bangkok**, **21 seconds after the hard-coded funding cutoff**. Successful closing [tx](https://solscan.io/tx/R2aG3LPTRNhNdbuw5h8mH2pcfVygFkFBjPjGQ1qfpk1kkekK8LwuHeCTsPutHMTSy7ejWgAtFHib5Zs3dxcm78k), slot **469035644**.
- **Final global gross commitments `7,700,010.170956 USDC`**, backed by `Launch.total_committed_amount` and exactly matching USDC escrow vault `9uaoJiwyJszXnP8iguE4XH4btcbz4F1BXeN4thAbhK2t`. Base vault `9ymW4Ya54jAhoRbRxW7HEUuUPanYvVfg3JcjCEPcN3JH` still held **25,800,000 MORI** in the closed snapshot.
- Final approval global `Launch.total_approved_amount=250,000 USDC` (observed at finalized slot **469036560**, while `state=Closed`, `unix_timestamp_completed=None`, `dao=None`). This is global accepted funding, not evidence of TGE completion or payout.
- User `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`, FundingRecord PDA `3z651WDFfQb7AzzYizSa8CdCaurP8TSHHTXugUhkWdki`: `committed_amount=700.000000 USDC`, **`approved_amount=17.650113 USDC`**, `is_tokens_claimed=false`, `is_usdc_refunded=false` at finalized slot **469036561**.
- Onchain approval successful [tx](https://solscan.io/tx/5MbHJQS7mPDbW8wZBipsRYWmCHAoJ1tsjoK47ZnGE2BHxqmNoVrm2YhTDCGRADyvQzx9Fu6zKVc4qtD4XXD9L8ev), **2026-11-13 19:03:08 UTC = Nov 14 02:03:08 Bangkok**, slot **469036369**, `meta.err=null`. Other approval txs appeared rapidly around 19:03 UTC. Approval is real, not a provisional allocation estimate.
- Under official v0.7 Claim formula **`approved_amount * 10,000,000 MORI / total_approved_amount`**, the user has **706.00452 MORI** redeemable after successful `CompleteLaunch`, and unused USDC **700 − 17.650113 = 682.349887 USDC** refundable after Complete. Integer micro-unit arithmetic yields exact 706.00452 MORI at 6 decimals. This beats previous simple-pro-rata baseline ~659 MORI; earlier 600–1300 scenario assumptions are no longer needed.
- User's MORI ATA `3EytgJ37GRWLV3VwbjtHBnGdGro4HBTRZqijyVj7T7LE` **exists but still has 0 MORI** at finalized slot **469036884**. User payout/USDC refund is **NOT DONE** as of this check. Do not confuse ATA creation with asset transfer.
- Official authenticated webpage `https://metadao.fi/companies/mori-finance` reported `Raise closed · Settling allocations`, **248 backers**, user #176, and `Claims and refunds open here when that’s done`. Public UI may lag onchain approval; funds are not claimable while Launch state remains `Closed`.
- **Timing:** do not invent a token trading/claim timestamp. `Claim` requires `LaunchState::Complete`, `Refund` requires `Complete` or `Refunding`. In previous completed MetaDAO v0.7 raises, closing-to-`Complete` varied ~1–2h, but this is historical, not a binding schedule. The 48-hour permissionless fallback after close is a separate condition and does not impose a mandatory wait for launch authority. In any case, the actual unlock is successful `CompleteLaunch` and subsequent token/refund transfers. The user does not need to send any new USDC or authorize an unknown claim site.

Links: [Mori Launch](https://solscan.io/account/BFVqq3Br9frUabrdgczu4obJ2TGNzKnys42j2pwrmXGZ) · [FundingRecord](https://solscan.io/account/3z651WDFfQb7AzzYizSa8CdCaurP8TSHHTXugUhkWdki) · [MORI mint](https://solscan.io/token/MoR1whCWjcLiUqAan4GHLRcn8wK4Jktk2DyDryNmeta) · [Official fundraiser](https://metadao.fi/companies/mori-finance) · [ICO rules](https://metadao.fi/docs/sale).

---


## 2026-11-11 ~17:35 Bangkok: confirmed Mori v0.7 live launch account, exact close, canonical base mint and user funding

**Source classification: direct finalized Solana RPC and MetaDAO user-authenticated official webpage**. Research-only update; this supersedes 2026-11-07 "MORI mint/address unverified" and "sale end unverified" statements. No trade, wallet signature, claim, alert or monitoring created.

### Timestamp, chain contract and escrow (direct RPC)

- **MetaDAO launch program**: `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM`. Mori Launch PDA: **`BFVqq3Br9frUabrdgczu4obJ2TGNzKnys42j2pwrmXGZ`**, deterministically derived with official v0.7 `seeds=[b"launch", base_mint]`; derivation method independently reproduced and checked against previously known SAT Launch PDA. Base mint embedded in Mori program state is **`MoR1whCWjcLiUqAan4GHLRcn8wK4Jktk2DyDryNmeta`**; exact mint also appears in Mori's MetaDAO fundraiser reporting ([MCG Signal primary founder interview](https://mcgsignal.com/feed/mcg-2026-11-09/MoR1whCWjcLiUqAan4GHLRcn8wK4Jktk2DyDryNmeta)).
- `state=Live`, `unix_timestamp_started=1794250810` (**2026-11-09 19:00:10 UTC / Nov 10 02:00:10 Bangkok**), `seconds_for_launch=345600` (**96 hours**), hence **hard coded scheduled close 1794596410 = Nov 13 19:00:10 UTC / Nov 14 02:00:10 Bangkok**. Actual `unix_timestamp_closed=null` until `CloseLaunch` is successfully executed, which may occur after the deadline; do not confuse scheduled end with confirmed closure. Official MetaDAO announced "4 days", independently corroborating the scheduled window.
- Snapshot around **Solana slot 468091790** (blockTime **1794393307 / Nov 11 ~17:35 Bangkok**): `minimum_raise_amount=250000 USDC`, `total_committed_amount=6708975.960956 USDC`, `total_approved_amount=0 USDC`, `dao=None`, `dao_vault=None`, `unix_timestamp_completed=None`, `seq_num=249`. State remains Live, no ICO settlement/TGE.
- Mori quote USDC vault `9uaoJiwyJszXnP8iguE4XH4btcbz4F1BXeN4thAbhK2t`: independent token-account balance `6,708,975.960956 USDC` at slot 468091936. Quote mint is canonical Solana USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`.
- Mori base MORI vault `9ymW4Ya54jAhoRbRxW7HEUuUPanYvVfg3JcjCEPcN3JH`: independent token-account balance `25,800,000 MORI` at slot 468091938. Base mint SPL Token program `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`, decimals 6, supply **25,800,000** at slot 468091247, mintAuthority `9hop857r4fh8ipL1dpUQxCXLe1aewmSqBhPwCzomP5eU` (matches Launch signer PDA), **freezeAuthority=None**. Current mint authority has not been disabled; no claim of immutable supply. Live total-supply 25.8M does **not** establish currently unlocked/tradable circulating supply, because 25.8M reside in Launch vault.
- `performance_package_token_amount=12,900,000` raw token units as a future allocation/contract config, `months_until_insiders_can_unlock=18`, `is_performance_package_initialized=false`, `additional_tokens_amount=0`, `has_bid_wall=false`. Performance-based release requires its separate conditions. MetaDAO own page lists 90-day average hurdle, lower bound 630 days etc. These are issuer terms before final launch, not a present team balance unlocked.

### User record (direct Solana RPC)

- FundingRecord PDA using official `seeds=[b"funding_record",launch,funder]`: **`3z651WDFfQb7AzzYizSa8CdCaurP8TSHHTXugUhkWdki`**, funder `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`, launch matches Mori PDA. `committed_amount = 700 USDC` onchain (stronger than previous UI-only evidence), `approved_amount=0` (Live stage default, **not** final zero allocation), `is_tokens_claimed=false`, `is_usdc_refunded=false`. Funding account was read at slot 468091787.
- Oversubscription on observed gross commitments = approx 26.836× minimum goal; final allocation could differ materially due to aligned allocations, ownership weighting, authority approvals, possible additional commitments, late exclusions etc. Do **not** invent accepted percentage or MORI token count from gross deposits.
- **Claim/TGE**: Not open at this observation. Official v0.7 `claim.rs` requires `LaunchState::Complete`, `refund.rs` requires `Complete` or `Refunding`. Scheduled fundraise close at Nov 14 02:00:10 Bangkok is not a confirmed spot-trading/claim time. Check `CloseLaunch`, approval and `CompleteLaunch` after that. Mint existing and all escrowed is normal.
- Verified official account on https://metadao.fi/companies/mori-finance , which shows user's 700 USDC commitment and funding call-to-action still open, $250k sale goal and intended $0.025 price / $645k FDV at goal. No user funding/trading action attempted in this check.

### Direct explorer links

- [MORI official launch PDA](https://solscan.io/account/BFVqq3Br9frUabrdgczu4obJ2TGNzKnys42j2pwrmXGZ)
- [MORI base mint](https://solscan.io/token/MoR1whCWjcLiUqAan4GHLRcn8wK4Jktk2DyDryNmeta)
- [MORI token vault](https://solscan.io/account/9ymW4Ya54jAhoRbRxW7HEUuUPanYvVfg3JcjCEPcN3JH)
- [MORI USDC escrow](https://solscan.io/account/9uaoJiwyJszXnP8iguE4XH4btcbz4F1BXeN4thAbhK2t)
- [User funding record](https://solscan.io/account/3z651WDFfQb7AzzYizSa8CdCaurP8TSHHTXugUhkWdki)
- [Official v0.7 Fund instruction and seeds](https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/v07_launchpad/src/instructions/fund.rs)

---


## 2026-11-10 participation update: 700 USDC committed on connected MetaDAO UI

**Evidence class: user-provided MetaDAO screenshot plus direct read of the user's connected MetaDAO browser tab; NOT independently verified via Solana RPC in this update.**

- The issuer's official page `https://metadao.fi/companies/mori-finance` displayed **"Committed $700 on Mori Finance"**, payment wallet **`BP7h…4dSp`** and **`Confirmed`**. This supersedes the 2026-11-07 research-era *planning assumption* of `0 USDC` / no user position. The user's actual participation is a **700 USDC gross commitment** according to the connected interface, not a final approved allocation or token distribution.
- The same screenshot displayed **$1,780,155 gross commitments** against a **$250,000 minimum objective** and the fundraiser still open. The subsequently inspected live connected browser page showed around **$1.9M** cumulative commitments and **75 wallets** at that separate observation. These are MetaDAO UI snapshots, not a verified accepted amount or Solana Escrow readback, and therefore must not be counted as the project's final raised capital.
- Issuer page still names the project risks: **Mori controls custody**, executes via a **single current institutional options market maker**; October **$1.7M notional** is issuer reported, still not independently proven revenue, active users, final real executions or profitability.
- **State: USER_COMMITMENT_700_USDC_UI_CONFIRMED / FUNDRAISE_OPEN / FINAL_APPROVAL_UNKNOWN / MORI_CLAIM_UNKNOWN / MAIN_RESEARCH_WATCH**. Do not infer an investment authorization to increase this position, and do not extrapolate a final token allocation from oversubscribed commitments. No signed transactions, wallet operations, recurring monitoring or automations were executed by this research update.

---


**Status:** `WATCH / RESEARCH_INCOMPLETE / NO_GO`. **No user allocation or trade authorized.** This is a single-project research record. Verified against Mission `PROJECT_ANALYSIS_FRAMEWORK.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `token_trading_principles.md`, and `MISSION_SPEC.md`. Independent operating metrics, mint address and launch config unresolved.

## Identity and official sources
- Canonical project: **Mori Finance**, Solana covered calls, official website https://mori.finance/ ; docs https://morifinance.gitbook.io/docs ; official X **@morifinance_**, *not* the unrelated 2023 Ethereum Mori Protocol at @Mori_Finance.
- MetaDAO's official upcoming curated raise: https://metadao.com/companies/mori-finance ; MetaDAO @MetaDAOProject announcement dated 2026-11-07. **Opens 2026-11-09 19:00 UTC = 2026-11-10 02:00 Asia/Bangkok (Nov 9 11am PST)**. Official page says **$250,000 raise goal** and **$MORI**, but as of this research **does not publish verified total supply, explicit token price, final accepted cap, investor/insider allocation, vesting or canonical mint address**. Opening is scheduled, not an already executed onchain deposit. Sale close/time and initial listing date are UNVERIFIED.
- Explicitly do not confuse with https://mori-finance.gitbook.io/mori-finance/mori-protocol , an unrelated 2023 Ethereum stable-asset project and old MORI ERC20. Same ticker cannot justify a canonical CA assertion.

## Product, stage and custody
- Working **public-facing options UI** https://mori.finance/calls/ and how-it-works https://mori.finance/how-it-works show SOL, cbBTC, PENGU, JitoSOL covered calls, selected strike/expiry and premium quotes. Does not alone prove settled executions.
- Mori issuer says October 2026 **$1.7 million option *notional volume***, PENGU options, Solana USDC payouts, and that trades route through **Mori's own OTC account** to **a single institutional market maker reportedly backed by Kraken**. These are **issuer/MetaDAO pitch claims, not independently reconstructed trades, paid users, counterparty identity or collected fees**. Kraken or market maker acknowledgement not independently found. Do NOT upgrade to verified partnership.
- **Important architecture**: despite "DeFi" positioning, current frontend is backed by **Mori-controlled custody and CeFi/OTC execution**; project itself acknowledges custody/counterparty and single-MM concentration risk. Previous GitBook alpha docs describe an institutional custodian and later planned smart contract migration. Production backend, custodian controls, solvency, withdrawals and audit not independently verified. Current `Level 1` UI confirmed; claimed production `Level 3-4` pending primary execution proof; independently verified paying users/revenue insufficient for confirmed Level 4/5.
- Core public GitHub identity not established: searched GitHub by exact project, `mori.finance`, `Morifinance`, Pavan Katepalli, options and Solana; no project-attributable open source program repo proven. Unrelated name-only `mori-finance/Mori-Finance-` is a generic Python financial analytics MVP and should **not** be attributed to this project.
- **Chain**: no canonical custody/settlement wallets, options contracts or $MORI mint publicly established by this check. Therefore no program/bytecode/signer/settlement/funder audit, and **no verified 1.7M notional**, TVL, holders, LP, claim readiness. Do not invent addresses or assume the old Ethereum MORI token is connected.

## Team, funding, historical record
- Founder named by MetaDAO: **Pavan Katepalli**; personal https://pavan.vc/about/ independently acknowledges founding Mori in 2026, former Trilogy senior executive and Yomi CEO.
- **Trilogy Education was truly acquired** by 2U in May 2019; SEC/2U 8-K and announcements: https://www.sec.gov/Archives/edgar/data/1459417/000110465919031103/a19-10494_1ex99d1.htm and https://www.sec.gov/Archives/edgar/data/1459417/000110465919020236/a19-7982_18k.htm ; transaction announced as $750M cash and stock. This verifies corporate sale, NOT that Pavan individually realized $750M, founded Trilogy or owned a particular fraction. His exact job title CTO/CLO remains a **personal/team statement pending independent employee record**.
- Pavan led **Yomi Games**, which issued 2022 primary funding press release announcing **$2M seed round** and investor names Hypersphere Ventures, Infinity Ventures Crypto, Sfermion, Cultur3 Capital, Maveron, Momentum 6, Taureon. Source: https://www.prnewswire.com/news-releases/yomi-games-raises-2m-to-build-out-casual-play-and-earn-ecosystem-301526937.html . This is **Yomi financing, not Mori financing**. Historical product success/users claimed by issuer, independently confirmed retention/revenue unavailable.
- Mori's own venture financing/valuation and any strategic investors remain UNVERIFIED beyond the upcoming MetaDAO $250k intended raise. The team GitBook also refers to co-founder Jason; current MetaDAO team panel lists only Pavan, so Jason's present role and identity require checking.

## Real financials and simple economic sensitivity
- Mori issuer claims **12% of gross option premiums** as its platform fee. Monthly notional **$1.7m** does NOT equal premium paid or revenue collected.
- **Explicit assumptions, never observed income:** 1% option premium-to-notional x 12% fee gives **$2,040/month**, $24,480/year; 3% yields **$6,120/month**, $73,440/year; 5% yields **$10,200/month**, $122,400/year. Assumes 100% fee applicability, no rebate, stable monthly volume for 12 months. Actual strike/term mix, transaction quality, referral shares, gross/net fee revenue, user counts, operating costs and runway NOT VERIFIED.
- Issuer target to win $10m–$20m/month notional from market maker and project its $2.8m/year fee income from Rysk-scale volume is **forecast**, not realized P&L. OTC counterparty concentration affects attainable spread, capacity and take rate.

## This sale, implied price and exit liquidity
- **Confirmed from MetaDAO Mori page:** upcoming *curated* raise for $250k, November 9 19UTC start, symbol $MORI; currently no confirmed specific total supply, token mint, total accepted money, sale end, private cost basis, performance package config, extra premine, exchange/LP.
- **MetaDAO generic documents, NOT Mori-specific confirmed terms:** https://metadao.com/docs/create ; https://metadao.com/docs/sale ; https://metadao.com/docs/whats-new ; describe **10,000,000 sale participant tokens + 2,900,000 liquidity tokens**, 20% accepted proceeds typically assigned to LP, optional up-to-12.9M founder performance package, time-weighted commitment/fill boost/Ownership Score, aligned-party reserved allocations and USDC refund for unused commitments. Do not automatically apply to Mori until its live deployment is onchain checked.
- **Conditional illustration only:** if Mori accepts exactly $250,000 in standard 10M participant issuance, **sale price = $0.025**; under such case 20% LP quote is **$50k** before any actual slippage or liquidity accounting. If a fully diluted 25.8M tokens existed, sale-price FDV **$645k**; if total supply differs, FDV changes linearly. **Neither supply nor price is verified Mori fact.** Even at low hypothetical FDV, $50k LP quote versus $250k sale token notional could limit realizable exit and price. No verified mint => no verified initial circulating MC, LP depth or actual quote.
- Relative ICO exit scenarios with hypothetical $0.025 sale price: $0.0125 (−50%), $0.020 (−20%), $0.025 (0%), $0.05 (+100%), $0.10 (+300%) before fees, slippage and unlock. Multipliers are illustrative, not forecasts or asserted tradeable prices.
- As-of review **no independently confirmed finalized claim, token CA, CEX listing, TGE, DEX pool, initial listing date or LP liquidity**.

## Mandatory project-specific PM and social scan — 2026-11-07 Asia/Bangkok
- Indexed venue/domain searches checked exact `Mori Finance`, `MORI MetaDAO`, `morifinance_` with **Polymarket, Kalshi, Limitless, Predict.fun** and MetaDAO company-specific decision pages. **未检索到可验证的项目专属 PM 市场**. Same-name `Mori` Peru election markets and 2023 Mori Protocol excluded. No numerical probability inferred. Venue-native complete unindexed coverage is not established.
- MetaDAO initial announcement has several thousand views/limited initial interactions, but these are platform distribution signals, not independent organic investor inflows. Real distinct participants, grassroots technical reviews and non-incentivized market depth unverified.
- No prior comparable ICO results used to set valuation, as per Mission project-specific preference.

## Risks and verification requirements
1. **Production custody model**: authority, segregation, proof of reserves, withdrawal and MM counterparty concentration unknown, plus no published audit matched to live backend.
2. **1.7m notional cannot be independently reproduced**, cannot infer recurring users, revenue or margin; buy-side options retail/treasury demand unverified.
3. **Mori total supply/private cost and future sell pressure not announced**; MetaDAO generic package is not immutable project config. No verified L2/chain contract addresses and attribution.
4. **Token exit liquidity**: accepted 250k is maximum *illustration*, and small early quote liquidity relative to public unlocked inventory may make headline multiples unrealizable.
5. **Historical team exit caveat**: 2019 2U acquired Trilogy, but amount is company valuation, not founder personal profit. Yomi seed amount applies only to Yomi.
6. **Identity collision**: unrelated Ethereum 2023 MORI must not be treated as official CA.
7. **PM**: no verified project-specific market found; no odds.

## Final assessment and state
- **Current project state `WATCH`**, not `SETUP`: potential attractive real-team + options distribution thesis, business data still issuer reported and sale economics/runtime unavailable.
- Before upgrade to `SETUP`: independently reconstruct real notional and USDC premium payout with canonical sender/receiver transactions and issuer reconciliations; verify custodian/OTC counterparty and recorded net fees, list live deploy and confirmed token mint + total supply/performance package/accepted $/public float/LP creation and slippage; recheck PM/source and real demand near opening; then compute sale-price-to-executable-TGE ROI in downside/base/strong cases.
- No sale participation planned, no wallets signed, no automated monitor, no position changes. `PRODUCTION_TRADING = NO_GO`.

## Source integrity
Official MetaDAO https://metadao.com/companies/mori-finance ; official platform sale mechanics https://metadao.com/docs/sale and https://metadao.com/docs/create ; Mori website https://mori.finance/ , product docs https://morifinance.gitbook.io/docs ; SEC and Yomi release above. This report intentionally leaves exact unknowns unknown. Research as-of 2026-11-07, not a live automated tracker.
