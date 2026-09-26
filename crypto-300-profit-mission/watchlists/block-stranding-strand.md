# Block Stranding / $STRAND

Updated: 2026-09-26
State: ACTIVE (existing presale exposure; analysis only)
User exposure: 100 SOL presale deposit
Execution authority: NONE in this conversation

## Current conclusion

Block Stranding remains an active development project with independently verifiable technical work, but its presale governance and counterparty transparency are poor.

It is not currently proven to be a completed rug. The team still operates official channels, the game/technical demo has existed, Colosseum independently confirms a 4th-place Breakout Gaming Track result, MagicBlock-powered stress testing was independently reported, and the team repeatedly states that TGE will occur.

However, the presale has now been outstanding for roughly eleven months with no confirmed TGE date. The official explanation has repeatedly been market timing. For an already-funded sale, this is a material delivery failure even though the Terms reserve broad discretion to change TGE timing.

No new capital should be evaluated until TGE terms, canonical mint, launch liquidity, exchange venues and final circulating supply are known.

## Presale terms: CONFIRMED

Official presale page:
- displayed price: $0.009
- displayed deposited amount: 13,000.5 SOL
- displayed backers: 4,442
- 10% of token supply sold in presale
- max ticket: 200 SOL
- presale tokens: 100% unlocked at TGE
- tokenomics shown:
  - Ecosystem 45%
  - Liquidity provision 15%
  - Marketing / Airdrop 13%
  - Presale 10%
  - CEX listings 7%
  - Team 5%
  - Investors & early contributors 5%

Official Terms dated 2025-10-22:
- all onchain transactions final, no refunds;
- discretionary allocation model;
- allocations may be adjusted/reduced at team discretion;
- TGE timing, mechanics and parameters may be modified;
- tokens are claimable only after TGE;
- terms do not identify a clear legal corporation or conventional governing-law jurisdiction;
- disputes are described as confidential binding arbitration and class/collective proceedings waived.

These provisions explain the team's contractual defense but do not eliminate delivery/counterparty risk.

## Raise-size reconciliation: ONCHAIN CONFIRMED

The apparent 13,000.5 vs ~19,355 SOL conflict is now resolved from chain data.

Canonical presale collection wallet identified directly from the user's deposits:
`STRAnDNZFwxHHrVM54SgxsBCoFkZfajzAeVvckJvYhU`

The wallet currently holds approximately **13,000.503 SOL**, matching the current official presale page's "13,000.5 SOL" figure almost exactly.

Confirmed large post-sale outflows from that same presale wallet:
- 2026-06-22: 355.5 SOL
- 2026-06-22: 1,000 SOL
- 2026-06-26: 3,000 SOL
- 2026-07-06: 2,000 SOL
- total: **6,355.5 SOL**

Each large outflow first moved to a fresh/intermediate wallet. Each intermediate wallet then forwarded essentially the full amount within minutes to:
`6LY1JzAFVZsP2a2xKrtU6znQMQ5h4i7tocWdgrkZzkzF`

Solscan publicly labels `6LY1J...` as **Kraken Hot Wallet**.

Reconciliation:
- current presale wallet balance: ~13,000.503 SOL
- confirmed large outflows: 6,355.5 SOL
- sum: ~19,356.003 SOL
- there is also a confirmed 1 SOL post-sale inbound transfer plus small dust transfers
- removing those post-sale inflows reconciles the original presale gross to approximately **19,355 SOL**

Conclusion:
- ~19,355 SOL is the gross presale raise.
- 13,000.5 SOL is effectively the remaining balance after the later 6,355.5 SOL withdrawals, not the gross sale amount.
- Community claims that more than 6,000 SOL left the presale wallet and reached Kraken are substantially confirmed onchain.
- A Kraken deposit proves exchange deposit/custody. It does **not** by itself prove that the SOL was sold for fiat/stables or misappropriated.

## Presale FDV controversy

Public presale marketing circulated a 500M total supply and approximately $3M-$7M projected presale FDV.

After oversubscription, team lead n0rd publicly acknowledged:
- final FDV reached $36M;
- values would be recalculated pro rata according to final FDV;
- the decision was made by the team;
- refunds / oversubscription refunds were not planned;
- the team characterized the sale as a discretionary-cap model.

If total supply is 500M and final FDV is $36M:
- implied final token price = $0.072;
- 10% sale pool = 50M STRAND;
- presale pool value at final FDV = $3.6M.

The presale site's still-visible "$0.009" field therefore must not be treated as the user's effective final unit cost unless the actual allocation checker proves otherwise.

## User's 100 SOL presale deposit: ONCHAIN CONFIRMED

User wallet:
`BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

Three direct transfers to the canonical presale wallet were found:

1. **65 SOL**
   - time: 2025-10-22 20:47:58 UTC
   - tx: `3FxY6NQXyE2DgXAV4PCmpdPuXv5nfze27U3pJY6PWnuFRe4YCRjNpCihtkvAcSBMm51wgBjhR3UqhrRgPUyRrHpv`
   - destination: `STRAnDNZFwxHHrVM54SgxsBCoFkZfajzAeVvckJvYhU`
   - Binance SOLUSDT 1-minute candle around the transaction: ~$180.41 close

2. **15 SOL**
   - time: 2025-10-24 16:55:00 UTC
   - tx: `2JEqA6hL6V9zUyEFwLMxkJaHCPGhnU6E5JcEjrUBpeGNgU2RYXhCwArMrs51G3DCT2Nuc6YixJaM6yzbRZvUobhh`
   - destination: same presale wallet
   - Binance SOLUSDT 1-minute candle: ~$190.20 close

3. **20 SOL**
   - time: 2025-10-24 17:12:10 UTC
   - tx: `2MEmfs6JuUSug2vJvrNDGMfP8SfMrCXDviAAq21BUomNFWcF3SCVyvccTdWuoaKbpRzY5rogtmEzMbismZbxJXeV`
   - destination: same presale wallet
   - Binance SOLUSDT 1-minute candle: ~$190.65 close

Total: **100 SOL confirmed onchain**.

Historical USD-equivalent cost basis using the transaction-minute SOL prices:
- 65 × $180.41 ≈ $11,726.65
- 15 × $190.20 ≈ $2,853.00
- 20 × $190.65 ≈ $3,813.00
- total ≈ **$18,392.65**

Using the high/low ranges of those three one-minute candles gives approximately $18,384-$18,399, so $18.39K is a robust historical USD cost basis.

This historical cost basis is the primary PnL benchmark for the presale. Current value of 100 SOL is a separate opportunity-cost benchmark and must not replace the original cost basis.

## Estimated STRAND allocation

With the onchain-reconciled gross raise of approximately 19,355 SOL, a 500M total supply and 10% / 50M STRAND presale pool:

- base allocation per SOL ≈ 2,583.31 STRAND
- **100 SOL base allocation ≈ 258,331 STRAND**

Any WL / engagement / referral boost must be added separately after the official allocation checker is recovered.

At 258,331 STRAND:
- historical USD cost break-even token price ≈ **$0.07120**
- with 500M supply, historical-cost break-even FDV ≈ **$35.6M**
- at the team's stated $36M final FDV / $0.072 token price, the base allocation would be worth about **$18,600**, almost exactly the user's original ~$18.39K USD-equivalent contribution.

This strongly supports the interpretation that the final $36M presale FDV was the effective pro-rata sale valuation.

## Current TGE status: CONFIRMED

As of accessible indexed official posts in 2026:
- TGE date remains unconfirmed.
- July and August official replies repeatedly say the team is monitoring market conditions and waiting for a favorable time.
- June 29 official messaging says it would not launch into a high-fear / weak-SOL market and would give advance notice.
- Team explicitly says no refunds and promises STRAND distribution after TGE proportional to allocation.

The latest Sep 25-26 claims in the supplied Grok report about a major rebuild, PvP beta to ~100 wallets and a final farm season were not independently verified from an accessible primary source during this review. Keep them as SOURCE-REPORTED until a direct official post is archived.

## Product reality

CONFIRMED:
- Colosseum's official Breakout winners page lists Block Stranding as 4th in Gaming.
- Independent reporting documents a June 2025 MagicBlock-powered stress test with 120,000+ transactions in 20 minutes and >100 TPS using AI agents.
- MagicBlock publicly amplified Block Stranding gameplay.
- An independent hands-on review currently rates the project 5/10 overall, with strong infrastructure/technical novelty and weak gameplay depth; its April 2026 update confirms continued development and a Tower Defense single-player/mobile mode.
- The token is still not live; independent game review pages also report no confirmed TGE date.

INFERRED:
- The project is technologically real but remains closer to an onchain gaming technology showcase / early game than a mature MMORPG.

## Marketing / KOL quality

NFLUENCE publicly lists "Block Stranding — Presale Campaign":
- 19,300 SOL raised
- 837K impressions

NFLUENCE describes its own Web3 offering as KOL waves, creator campaigns, community pushes and paid distribution.

Therefore part of the presale reach was organized growth marketing. High social impressions around the sale should not be treated as purely organic product demand.

PRIMES also publicly described itself as having powered Block Stranding's social campaign.

## Team / counterparty and communication risk

Public-facing lead: n0rd / @nrdxhq.

Archived X snapshots show a material change:
- Around the presale period, his bio was **"Building @blockstranding"**.
- Current indexed profile snapshots show only **"Building"**.
- The newest visible original n0rd activity in the indexed profile is from approximately **2025-11-01**, shortly after the presale controversy.
- No later n0rd posts discussing the June-July 2026 presale-wallet withdrawals, Kraken deposits, TGE delay or treasury use were found.

This does not prove he left the project. It is, however, a meaningful counterparty/transparency risk because the public lead who personally defended the presale structure effectively stopped public communication while the project account continued posting.

Current concerns:
- pseudonymous / limited independently verifiable founder history;
- no full independently verified team roster;
- no clear legal counterparty identified in the Terms;
- no independently verified large institutional funding round for Block Stranding itself;
- public lead inactivity and removal of @blockstranding from the indexed bio.

MagicBlock's funding and reputation belong to MagicBlock, not Block Stranding. A technical partnership must not be reclassified as investment.

## Presale treasury / Kraken flow: ONCHAIN CONFIRMED

Canonical presale collection wallet:
`STRAnDNZFwxHHrVM54SgxsBCoFkZfajzAeVvckJvYhU`

The user's direct deposits prove this was the sale recipient.

Confirmed large withdrawals:
- 2026-06-22: **355.5 SOL**
- 2026-06-22: **1,000 SOL**
- 2026-06-26: **3,000 SOL**
- 2026-07-06: **2,000 SOL**
- total: **6,355.5 SOL**

Each withdrawal first went to a separate intermediate wallet and then, within minutes, essentially the full amount was forwarded to:
`6LY1JzAFVZsP2a2xKrtU6znQMQ5h4i7tocWdgrkZzkzF`

Solscan labels that destination as **Kraken Hot Wallet**.

Approximate SOL/USD at the transfer minutes (Binance SOLUSDT 1m):
- 355.5 SOL at ~$74.84 ≈ **$26.6K**
- 1,000 SOL at ~$73.59 ≈ **$73.6K**
- 3,000 SOL at ~$72.57 ≈ **$217.7K**
- 2,000 SOL at ~$81.56 ≈ **$163.1K**
- total transfer-time notional ≈ **$481K**

The presale wallet now holds ~13,000.503 SOL. Adding the 6,355.5 SOL of confirmed large withdrawals yields ~19,356 SOL; after accounting for a confirmed later 1 SOL inbound plus dust, this reconciles closely to the ~19,355 SOL gross presale raise.

Evidence boundary:
- CONFIRMED: presale wallet sent 6,355.5 SOL through intermediate wallets to Kraken.
- NOT CONFIRMED: what happened inside Kraken.
- Do not claim the SOL was sold, converted to fiat/stables, or personally misappropriated without offchain exchange records or an admission.

## Disclosure review around the withdrawals

A review of indexed official @blockstranding communications found **no public treasury disclosure explaining these four transfers** and no indexed official statement identifying the Kraken destination as market-making, CEX-listing, payroll, operational spending, custody, hedging or any other stated use.

The timing is notable:
- Jun 22: 355.5 + 1,000 SOL reached Kraken.
- Jun 26: another 3,000 SOL reached Kraken.
- Jun 29: official account said TGE was delayed because of poor market conditions / SOL under $70, rejected refund demands, and warned against "baseless FUD"; the post did not disclose the prior 4,355.5 SOL Kraken transfers.
- Jul 6: another 2,000 SOL reached Kraken.
- Jul 10: official replies again said the team was waiting for favorable market conditions; no treasury-transfer explanation was found.

Community users later publicly accused the project of transferring presale proceeds to Kraken. Indexed replies show the allegation being posted directly under/at the official account. No indexed substantive project response explaining the transfers was found during this review.

The presale Terms do not contain a use-of-proceeds section and contain no explicit commitments about treasury custody, liquidity deployment or CEX funding. They give the team broad discretion over allocations/TGE timing. The tokenomics page allocates token supply to categories such as liquidity provision (15%) and CEX listings (7%), but those percentages are token-supply allocations and do not explain how raised SOL proceeds may be used.

Assessment:
- The chain movement itself is legitimate to flag as a **material transparency issue**.
- The evidence supports saying **"6,355.5 SOL of presale proceeds was deposited to Kraken without a public explanation found in the reviewed official communications."**
- The evidence does not support saying **"the team definitely sold or stole the 6,355.5 SOL."**
- Given the long TGE delay and the public lead's prolonged inactivity, absence of treasury disclosure materially increases counterparty risk.


## Follow-up forensic review — 2026-09-26

### Exhaustive presale-wallet outbound scan

The canonical presale wallet has only **29 recorded signatures** from the sale period through this review. All 29 were inspected via Solana transaction data.

Confirmed direct SOL outflows where the presale wallet itself was the source:
- 355.5 SOL on 2026-06-22
- 1,000 SOL on 2026-06-22
- 3,000 SOL on 2026-06-26
- 2,000 SOL on 2026-07-06

No other direct SOL outflow from the presale wallet was found in the full address history available at the time of review.

Therefore **6,355.5 SOL is the complete confirmed direct withdrawal total**, not a partial sample.

All four intermediary wallets forwarded essentially the full amounts to the same Solscan-labelled Kraken Hot Wallet. No evidence was found that these four intermediary wallets retained meaningful balances.

### Public-lead activity / identity clues

The public X lead `@nrdxhq` has materially reduced public visibility:
- current indexed X bio: **"Building"**
- older snapshots: **"Building @blockstranding"**
- newest indexed original activity on the account remains clustered around the presale controversy / PRIMES period in late Oct to early Nov 2025;
- no indexed n0rd post explaining the June-July 2026 Kraken deposits was found;
- no verified later public project was found under the same handle in web or GitHub searches;
- the Telegram handle `@nrdxhq` remains reachable but provides no public activity history.

A useful identity clue exists in Superteam Earn: a MagicBlock Real-Time Hackathon submission lists **"Nick Nord @nrdxhq"**. Treat "Nick Nord" as a public platform identity attached to the same handle, not as independently verified legal identity. No reliable link was established from this profile to unrelated LinkedIn/music results sharing the same name.

GitHub searches found no repository/account clearly tied to `nrdxhq`.

### Team-change signal

An indexed Block Stranding official update in 2026 said the project had been slow with updates because of **"internal improvements happening within the team"**, while also saying TGE/pre-launch planning was delayed by market instability.

This is the only public evidence found that hints at an internal team transition. It does not identify who changed roles or confirm that n0rd left.

Combined evidence:
- n0rd stopped visible public communication;
- his indexed bio dropped `@blockstranding`;
- official account later referenced internal team improvements;
- the project account continued publishing without n0rd;
- 6,355.5 SOL of presale treasury later moved to Kraken with no public use-of-proceeds explanation found.

Assessment: **core-team continuity is UNRESOLVED and should be treated as a material counterparty risk.**


## Fake STRAND warning

Several unrelated / unofficial Solana tokens named STRAND or Block Stranding exist in search/indexers.

Until Block Stranding announces a canonical mint at TGE, none should be treated as the official token.

## TGE sell pressure

Presale allocation is explicitly 100% unlocked at TGE.

If final presale pool = 10%:
- 50M STRAND may become liquid immediately under the 500M-supply model.
- 4,400+ backers have waited about eleven months.
- community sentiment includes significant refund/TGE frustration.

Therefore presale-holder sell pressure is a major launch risk.

The final TGE circulation beyond the presale must be re-verified. Historical marketing references to 30% initial circulation are not sufficient for current valuation.

## Stage-matched TGE comparables

Historical launch references:
- Nyan Heroes: >$30M circulating market cap on TGE day; already a PC shooter on Epic Games Store and launched with Bybit support.
- Pixels: about $387M market cap in Feb 2024, with ~900K total players / 176K DAU and Binance Launchpool.
- Portal: about $425M circulating market cap on launch day, with Binance listing and $29M raised.

These show that gaming tokens can launch far above $36M FDV in strong conditions, but all had materially better distribution, team/product maturity or user scale than Block Stranding's currently verifiable state.

Therefore $36M should not be treated as a guaranteed floor merely because larger gaming tokens once launched above it.

## Working fair-value scenarios

These are ANALYST SCENARIOS, not confirmed market prices.

Current TGE FDV framework:
- Distressed / trust-discount launch: $5M-$10M
- Weak/base recovery: $12M-$25M
- Strong execution: $30M-$50M
- >$75M requires major exchange distribution, convincing PvP/product traction and restored community confidence.

Central working range: $15M-$25M FDV until stronger launch evidence appears.

Reasons for discount:
- ~11-month TGE delay;
- repeated "market conditions" explanation with no hard deadline;
- weak legal/counterparty transparency;
- large unlocked presale cohort;
- product still early;
- paid KOL/social distribution;
- no verified token launch liquidity or CEX list;
- no canonical mint;
- fund-use transparency unresolved.

Reasons value is not marked zero:
- real technical demo;
- independent Colosseum result;
- real MagicBlock integration;
- project communication continues;
- active product development has been independently observed.

## 100 SOL position scenarios

Use the historical contribution value of approximately **$18,393** as the primary cost basis.

Working base allocation: approximately **258,331 STRAND**.

If total supply remains 500M:

| TGE FDV | STRAND price | 258,331 STRAND value | vs historical cost |
|---:|---:|---:|---:|
| $5M | $0.010 | ~$2,583 | ~0.14x |
| $10M | $0.020 | ~$5,167 | ~0.28x |
| $15M | $0.030 | ~$7,750 | ~0.42x |
| $20M | $0.040 | ~$10,333 | ~0.56x |
| $25M | $0.050 | ~$12,917 | ~0.70x |
| $35.6M | $0.0712 | ~$18,393 | ~1.00x |
| $36M | $0.072 | ~$18,600 | ~1.01x |
| $50M | $0.100 | ~$25,833 | ~1.40x |
| $75M | $0.150 | ~$38,750 | ~2.11x |
| $100M | $0.200 | ~$51,666 | ~2.81x |

Historical-cost break-even is therefore approximately $35.6M FDV before slippage, fees and any boost.

A separate opportunity-cost analysis may compare the position to simply holding the original 100 SOL, but that is not the acquisition-cost PnL basis.


## Delivery / TGE-intent assessment — 2026-09-26

### What the team can demonstrably deliver

The team has demonstrated real technical execution:
- Colosseum Gaming Track placement;
- a functioning early onchain game;
- real MagicBlock integration;
- Tower Defense/mobile iteration;
- repeated live demos and stress-testing.

Therefore the technical difficulty of minting a Solana SPL token, publishing a claim page and seeding a market is below work they have already demonstrated.

The unresolved question is not whether a token can technically be created. It is whether the team is willing and able to execute a **credible liquid launch** while honoring old holders and absorbing the presale overhang.

### Current TGE-readiness checklist

As of this review, no verified evidence was found for:
- canonical STRAND mint;
- finalized public allocation checker;
- claim contract/page;
- fixed TGE date;
- finalized initial circulating supply;
- announced DEX pool;
- announced market maker;
- confirmed CEX listing from the exchange itself;
- disclosed launch liquidity;
- treasury / use-of-proceeds report;
- completion of the separately promised PRIMES pre-TGE airdrop.

Official site status:
- Season 2 is ended;
- leaderboard is paused/locked;
- no new live farm season is visible on the official Earn page.

Indexed official X activity currently ends at 2026-08-20 with:
- "first PvP version is almost here";
- TGE date still unconfirmed;
- team still waiting for the right market conditions.

The supplied Grok claim that a Sep 25-26 2026 rebuild/PvP beta/final farm season was launched could not be independently verified from the official site or currently indexed official X feed. Treat that claim as unverified until an original official URL is produced.

### Market-condition explanation is weakening

Official Jun 29 messaging cited high fear and SOL below ~$70 as a poor TGE environment.

Observed Binance SOLUSDT daily closes:
- Jun 29: ~$75.16
- Jul 10: ~$78.13
- Aug 20: ~$87.66
- Sep 25: ~$122.15
- current Sep 26 spot during review: ~$121.54

Despite a material market recovery, no fixed TGE date or launch infrastructure has been announced in accessible official evidence.

This does not prove unwillingness to launch. It does show that "market conditions" has functioned as a flexible delaying criterion rather than a published objective trigger.

### Treasury solvency hypothesis

The hypothesis that the team already spent all presale funds is **not supported** by the canonical wallet.

Visible remaining balance:
- ~13,000.503 SOL
- at ~$121.54/SOL ≈ **$1.58M**

Confirmed Kraken deposits:
- 6,355.5 SOL
- transfer-time notional ≈ **$481K**
- post-Kraken disposition unknown.

Gross raise:
- ~19,355 SOL.
- User's own presale fills imply SOL around ~$184 weighted average; using a similar sale-period price gives roughly ~$3.5M historical USD-equivalent gross, broadly consistent with PRIMES' "$4M raised" marketing claim.

Therefore the treasury's USD purchasing power has fallen materially because SOL fell after the sale. Even if the 6,355.5 SOL sent to Kraken was converted near transfer-time prices, visible remaining treasury + transfer-time notional is only roughly ~$2.06M today versus a rough ~$3.5M+ sale-time value.

This provides a plausible non-fraud explanation for why the team may have delayed: launching around a $36M FDV with fully unlocked presale holders and substantially reduced treasury purchasing power is hard.

It does not explain the absence of transparent treasury reporting.

### $36M launch-liquidity problem

Under the historical 500M supply / 10% presale model:
- presale unlock = 50M STRAND;
- $36M FDV => $0.072/STRAND;
- unlocked presale notional at launch = **$3.6M**.

If only:
- 10% of presale tokens sell => ~$360K gross sell flow;
- 20% => ~$720K;
- 30% => ~$1.08M.

With 4,400+ holders waiting roughly eleven months, meaningful launch selling is plausible.

Tokenomics assigns 15% / 75M STRAND to "liquidity provision". At $0.072, those tokens have a nominal value of $5.4M, but token inventory is not quote-asset liquidity. A balanced pool containing all 75M at that price would require roughly $5.4M of quote assets, far above the ~$1.58M still visible in the presale wallet.

A serious $36M-FDV launch therefore likely requires:
- external market-maker/CEX capital;
- much smaller token inventory deployed to LP;
- or acceptance of thin liquidity/high volatility.

No verified MM/CEX/liquidity plan has been found yet.

### Incentive to eventually TGE

There are real incentives for the team to issue STRAND:
- old presale and farming liabilities remain open until distribution;
- team/investor/ecosystem token allocations have little liquid value without TGE;
- project reputation cannot fully reset while 4,400+ buyers remain unpaid in tokens;
- official account continues to state that STRAND will be distributed after TGE.

This supports a meaningful probability of eventual token issuance.

There is much weaker evidence for a high-quality launch that sustains the original ~$36M valuation.

### Scenario assessment

ANALYST ESTIMATE, not a factual claim:

1. **Credible/serious TGE**: ~20-30%
   - fixed date;
   - allocation checker;
   - disclosed circulation;
   - credible DEX/CEX/MM/liquidity;
   - public PvP/product proof;
   - reasonable treasury explanation.

2. **Obligation-closing / low-quality TGE ("交代式 TGE")**: ~35-50%
   - token is eventually minted/distributed;
   - old obligations technically fulfilled;
   - weak liquidity and limited exchange support;
   - product remains shallow;
   - team reduces activity after launch;
   - severe unlocked-presale selling.

3. **Continued long delay / eventual abandonment without near-term TGE**: ~20-30%
   - "market conditions" continues as an undefined gate;
   - no claim/mint/listing infrastructure appears;
   - project social/development activity gradually decays.

4. **Fresh-money extraction before honoring STRAND**: currently ~5-15%
   - no verified new paid raise/farm/mint is live at this review;
   - ~13,000.5 SOL remains visibly in the presale wallet.
   - Probability rises sharply if the team asks users for new capital before distributing STRAND.

Ranges overlap because future paths can transition between categories. The central risk is currently an obligation-closing TGE, not proof of a second fundraising scam.

### "交代盘" warning pattern

Treat the following as a major escalation:
- renewed KOL campaign but still no mint/checker/date/liquidity disclosure;
- new paid NFT, presale, mint, farm or deposit campaign before old STRAND obligations are delivered;
- large new presale-wallet transfers to CEX without a simultaneous TGE/liquidity disclosure;
- sudden TGE announcement with only a few days' notice;
- no exact allocation checker before launch;
- launch with no credible market maker / CEX and shallow LP;
- tokenomics changed to increase team/marketing/unlocked circulation;
- PvP/rebuild remains private-demo only while token marketing restarts.

Evidence that would materially reduce the "交代式 TGE" risk:
- exact allocation checker including boost;
- canonical mint and authority configuration;
- fixed date with reasonable notice;
- final circulation/unlock table;
- verified exchange announcement or disclosed DEX/MM plan;
- launch-liquidity amount;
- public treasury accounting including the 6,355.5 SOL Kraken flow;
- genuinely public PvP build and active users;
- no new fundraising before old liabilities are settled.

### Working conclusion

The team has enough demonstrated engineering ability to technically issue STRAND and still has substantial visible treasury funds. The strongest current risk is **willingness/quality of launch**, especially whether management will accept a launch valuation below the old $36M anchor and provide enough liquidity for a heavily unlocked presale cohort.

Until concrete TGE infrastructure appears, treat public statements about "waiting for the right market" as intent signals only, not launch evidence.

## Decision state

ACTIVE because the user already has a material 100-SOL exposure.

Analysis posture:
- no new capital;
- no assumption of refund;
- no assumption of $36M launch floor;
- prioritize exact allocation verification, fund-flow reconstruction, canonical TGE terms and launch liquidity.

## Next evidence that changes the thesis

Positive:
- official fixed TGE date;
- canonical mint;
- final allocation checker;
- confirmed CEX/DEX launch venues and liquidity;
- final TGE circulating supply/unlocks;
- independently verifiable PvP/main-game traction;
- transparent presale treasury/accounting.

Negative:
- continued indefinite TGE delay;
- unexplained changes to allocation;
- project stops shipping/communicating;
- large presale fund outflows inconsistent with stated development/liquidity use;
- no executable liquidity plan;
- new tokenomics that increase TGE sell pressure.

## Next forensic task

If the user supplies the presale transaction signature or public sending address, reconstruct the exact 100 SOL deposit, identify the presale recipient and trace the fund flows. Never request seed phrases or private keys.
