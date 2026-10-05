# PaperDAO / daos.world / Papertrade 发射与参与分析

Updated: 2026-10-05 Asia/Bangkok
Category: launchpad / community treasury / HyperEVM synthetic perps
State: WHITELIST LIVE / RAISE TERMS PARTIALLY UNRESOLVED / PAPERTRADE PREDEPOSIT OCT-08 / TRADING OCT-10

## Current conclusion

### CONFIRMED
- PaperDAO is an independent community treasury launched through daos.world. It is not Papertrade itself and states it is not affiliated with, endorsed by, or operated by Papertrade.
- PaperDAO's purpose is to pool capital, bridge/move treasury capital to HyperEVM, trade Papertrade from launch, accumulate/stake PAPER, and represent the treasury pro rata through PULP.
- Papertrade launch schedule published by Papertrade: predeposit opens 2026-10-08; frontend-only live trading starts 2026-10-10; later phases open direct contract access, builder codes and PAPER transferability.
- PAPER starts from zero supply and is minted by user losses/liquidations. PaperDAO describes the early flat region as 100 PAPER per USD 1 of loss basis while tracked LP is below roughly USD 2M, followed by decay. PAPER can be staked for protocol revenue; excess LP value above roughly USD 5M is intended to sweep to stakers under the published design.
- PaperDAO published PULP supply: 1.1B total, with 100M assigned to a locked Uniswap V3 pool. PULP is intended to be a pro-rata claim on treasury assets and later redeemable for PAPER once PAPER transfers are enabled.
- daos.world is a functioning DAO launchpad that began on Base in late 2024 and later expanded to other chains. Its older Base contract system is public in `azflin/daos-world-contracts`.
- daos.world's Base model gives the DAO manager broad treasury execution authority through the DAO contract. This is manager/custody risk, not a passive immutable index vault.
- daos.world founder AzFlin has a verifiable engineering history: TradFi development, Chainshot Solidity training, Genie lead-engineering history, then Uniswap after Genie acquisition, followed by independent crypto development and daos.world.
- Papertrade is an actual protocol under launch preparation, not just a token page. A HyperEVM mainnet testing deployment has existed; Papertrade publicly warned early users that test-contract deposits had no advantage and would be returned.
- Papertrade contracted Guardian Audits and later reported frontend/UX/servers largely complete with a small number of contract audit items remaining before launch-readiness work.
- Papertrade co-founder Colin Hong / `@izebel_eth` is publicly identifiable. Independent records confirm MIT, Morgan Stanley and Standard Crypto history; project materials also associate him with Millennium. Co-founder `@blurr` remains pseudonymous.
- No VC/seed PAPER allocation is part of the published fair-launch mechanism. PAPER has no initial team/VC premint under the published model.

### UNRESOLVED / CONFLICTING
- The exact PaperDAO raise contract/address was not published on the indexed PaperDAO page at the time of this review; PaperDAO says the contract will be published at the raise.
- daos.world homepage currently says `Raise live: whitelist`, while the dedicated PaperDAO launch page still says `Raise opens: Date to be announced`. Treat the homepage as evidence that whitelist activity is live, but do not invent the exact presale opening timestamp.
- Community/KOL posts currently report a 50 ETH hard cap and tier sizes around 0.025 / 0.1 / 0.25 ETH, with some posts claiming DAO/institution allocations up to 1 ETH. These terms were not found in the indexed first-party PaperDAO/daos.world page text and remain UNCONFIRMED until the live raise UI or a first-party announcement exposes them.
- PaperDAO manager identity, signer structure and treasury permissions for this specific raise are not yet independently reconstructed from the live raise contract.
- Papertrade's final production contracts and complete Guardian audit report should be rechecked when Oct-08 predeposit opens.

## daos.world launchpad background

daos.world allows managers to raise capital for an onchain treasury and issue a DAO token representing economic exposure to the treasury.

Older Base documentation states:
- treasury funds live in a smart contract;
- the manager can execute arbitrary calls from the treasury;
- Uniswap V3 liquidity is locked until fund expiry;
- manager can extend fund expiry;
- platform charges a raise fee and takes part of trading fees;
- managers can receive carry on profits;
- whitelists are tiered and can be administered by project/platform operators.

This means daos.world should be treated as an actively managed crypto fund launchpad with a token wrapper. The token is not equivalent to a trustless vault share unless the specific launch contract constrains the manager more tightly.

### Founder / platform history

AzFlin publicly described:
- 7 years of TradFi Python/SQL/data work;
- Chainshot Solidity training in 2021;
- lead engineer at Genie;
- transition to Uniswap after Genie acquisition;
- independent crypto development after leaving Uniswap;
- creation of daos.world in Nov 2024 as a fork/evolution of daos.fun with another partner.

The public `azflin/daos-world-contracts` repository exists and contains the original Base DAO factory, treasury, token and LP-locker system. The public repository's latest visible commit is from 2025-02-19, so it is historical evidence of the platform's contract architecture but is not sufficient evidence for the current 2026 Robinhood/HyperEVM infrastructure rewrite.

## Historical launchpad experience

The platform has launched many DAO tokens, including FDREAM, ALCH, AISTR, AR, RWOK, YT and others. daos.world currently still lists live and expired DAOs.

Historical performance is highly dispersed:
- founder/community accounts state that several early launches reached 100x+ at peak;
- this is plausible for the 2024 Base mania but should not be treated as a repeatable expected return;
- long-run outcomes for some prior tokens are extremely poor. Example: ALCH's Base token later traded with only hundreds of dollars of liquidity and roughly low-thousands USD FDV in 2026, despite an early period where its market cap had been around seven figures.

Therefore the platform has real launch history and has produced extreme early winners, but it also has clear examples of severe long-run decay. Whitelist edge is a short-term launch phenomenon, not proof of durable treasury performance.

## Papertrade actual business

Papertrade is a synthetic perpetual venue on HyperEVM.

Mechanics:
- trades do not enter Hyperliquid's matching engine;
- Papertrade reads Hyperliquid BBO/mid pricing and settles synthetically against its own LP;
- LP starts at zero rather than with a conventional external liquidity seed;
- trader losses build LP and mint PAPER to the losing trader;
- profitable traders are paid from available LP; if LP is insufficient, profit claims can queue;
- no conventional funding rate and no ordinary orderbook slippage under the design;
- up to 1000x leverage is advertised;
- PAPER staking is designed to receive protocol/LP revenue.

Launch sequence published by Papertrade:
1. 2026-10-08: predeposit/account creation, trading paused.
2. 2026-10-10: frontend-only live trading through whitelisted relayers.
3. After congestion risk falls: direct smart-contract access.
4. Later: builder codes; builders/frontends can earn the frontend fee.
5. Later: PAPER transfers enabled.

The staged frontend-only phase means the initial launch is not fully permissionless despite the eventual architecture being onchain. Papertrade explicitly says this is intended to avoid launch MEV/race advantages.

## Papertrade team / financing

### Colin Hong / Jez (`@izebel_eth`)
Confirmed independent background:
- MIT graduate;
- four years at Morgan Stanley according to World Poker Tour profile;
- Standard Crypto Venture Partner / partner history;
- active angel investor.

Project/industry profiles also report a Millennium quantitative research role. Treat that detail as corroborated by multiple industry sources but not as strongly as the MIT/Morgan Stanley/Standard record.

### `@blurr`
- Papertrade co-founder.
- identity and CV not publicly disclosed.

### Financing
No conventional Papertrade token presale/VC PAPER allocation is part of the published design. The central claim is fair launch from zero supply. Do not translate Colin Hong's Standard Crypto affiliation into `Standard Crypto invested in Papertrade`; no such funding fact was verified.

## PaperDAO strategy

PaperDAO is effectively an outsourced PAPER farming vehicle:
- raise ETH through daos.world on Robinhood Chain;
- move treasury capital to HyperEVM before launch;
- predeposit into Papertrade;
- deliberately run strategies that generate early PAPER exposure while the emission curve is most favorable;
- retain PAPER, staking income and trading PnL in treasury;
- PULP holders own the treasury pro rata;
- later PULP is intended to redeem for PAPER once PAPER becomes transferable.

Important economic point:
PaperDAO cannot obtain PAPER without accepting trading loss/risk. The goal is not to "farm free PAPER". It is to make the expected value of early PAPER minted + later staking income + trading PnL exceed the capital intentionally lost / trading risk incurred.

## Participation opportunities

### 1. PaperDAO whitelist / raise
Current official status: whitelist is live on daos.world.

Potential advantages:
- pooled capital may obtain larger launch-throughput priority than a small individual account;
- removes the need to manually bridge/predeposit and trade during congestion;
- gives exposure to early PAPER farming without personally trying to get liquidated efficiently.

Risks:
- manager execution risk;
- treasury/cross-chain risk;
- PULP market/liquidity risk;
- Papertrade smart-contract/model risk;
- PAPER valuation is unknown and non-transferable initially;
- a bad strategy can destroy treasury capital even if PAPER is accumulated.

Do not size from community-advertised 50 ETH/tier numbers until first-party live UI confirms them.

### 2. Direct Papertrade participation
Most direct route:
- Oct 8: predeposit and create account;
- Oct 10: trade through official frontend;
- early losses/liquidations mint PAPER while emission rate is highest;
- stake PAPER for revenue if the protocol reaches the required LP scale.

Direct participation gives full control but requires execution during a congested launch and creates a strong temptation to intentionally over-leverage. Treat `lose money to mint PAPER` as an economic purchase of PAPER with uncertain implied price, not free mining.

### 3. daos.world DWL whitelist route
Historical daos.world system lets users earn DWL from staking supported DAO tokens. Documentation states 1M DWL can guarantee the lowest-tier whitelist slot, while smaller burns enter a weighted raffle. Check the live PaperDAO launch page before using this route because current Robinhood-chain launch mechanics may differ from the older Base flow.

### 4. Community whitelist giveaways
The screenshot/KOL post describes a giveaway of two whitelist spots and also links to official whitelist application. This is a valid low-cost attempt if no wallet asset approval/payment is requested, but it should not be treated as authoritative for allocation/tier terms.

## Preliminary decision

Research status: WATCH / PARTICIPATION-ELIGIBLE, not auto-buy.

Positive:
- real launchpad with historical launches;
- technically credible daos.world founder;
- technically/financially credible Papertrade founder;
- Papertrade product is substantially developed and launch schedule is concrete;
- PAPER fair-launch design creates genuine day-one scarcity/participation asymmetry;
- PaperDAO has a coherent reason to exist: pooled execution can reduce individual launch congestion and optimize early emission capture.

Negative:
- PaperDAO is an actively managed strategy wrapper, so manager quality is decisive;
- specific PaperDAO manager/signers and raise-contract permissions are not yet verified;
- exact live raise terms are not yet independently confirmed from first-party UI;
- PAPER has no market price at launch and starts non-transferable;
- the protocol can create delayed winner claims if LP capital is insufficient;
- 1000x leverage and intentional-loss farming make behavioral/execution risk extreme;
- historical daos.world token outcomes include both spectacular launch peaks and near-total long-run decay.

Before committing meaningful capital, require:
1. live PaperDAO raise contract/address;
2. exact whitelist tiers and hard cap from first-party UI;
3. manager/signer/treasury permission audit;
4. Oct-08 Papertrade production contract + Guardian audit verification;
5. clear PaperDAO execution policy: max loss budget, strategy classes, leverage limits, and how much treasury capital can be intentionally sacrificed to mint PAPER.
