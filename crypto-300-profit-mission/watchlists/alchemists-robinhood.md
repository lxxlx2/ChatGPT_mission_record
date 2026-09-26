# Alchemists / Robinhood Chain

Updated: 2026-09-26 16:44 Asia/Bangkok
State: WATCH
Type: on-chain PoW mining + crafting + NFT/Soul fee-stream game
Chain: Robinhood Chain mainnet, chainId 4663
Official code: simonborel617-cmyk/alchemists
Official site in repository: https://alchemist-mine.com

## Current judgment

Technically real and materially more complete than a typical narrative-only microgame, but the economic loop is not yet proven.

Do not classify it as a passive mining-yield product. A successful PoW find requires an ETH submit payment and produces game inventory whose external clearing price is currently unverified. Profitability becomes measurable only after there is reliable secondary-market price/volume or the Soul stream opens and actual claim yields can be observed.

Current Mission state is WATCH.

## Canonical v4 deployment

Deployment record timestamp: 2026-09-26T04:59:24.598Z.

- Materials: 0xf7a0D261d43ff2633eEb0d5b1cDD7B7A167b7285
- Keys: 0x560c97151984E719B6030DEAB9C4Fb1701e754e3
- Souls: 0x0AE508Db2798d17FD2B7cf1Fb90B210730A3b99D
- Stream: 0x13d0794A63933e0e00A2b20e59DF44dC7ab67e36
- Kettle: 0x06c3DcEec2152bFB40D40636bf138764b9074626
- Mine: 0x16de1dD77E741a80a9AF586dCB4D429A2b65B6f6
- Furnaces: 0xa1467f8B363F152120d5b418f443CC93c144E237
- Workshop: 0xB07453De23a6731021725Bc82092c81BFeB6328d
- Alchemists main-act contract: not deployed
- Timelock: none
- Treasury / governance Safe: 0x08Eb68ca02f6fDBCb2b335c67E14EC053166CC41
- Collection marketplace face: 0x5Ce8fb583fD3583E4cd7BF89f881e011B6ECfcD2

## Live on-chain snapshot

Read directly through Blockscout on 2026-09-26 around 16:44 Asia/Bangkok:

- Mine.currentPrice: 0.00002389152 ETH per successful submit.
- Initial price0: 0.00002 ETH.
- Current price / initial price: about 1.1946x.
- oreRemaining: 997,858 of 1,000,000.
- submittedTotal: 2,144.
- unlockedTier: 1, Common only at this snapshot.
- Materials.minedTotal: 2,137.
- Materials.burnedIngredients: 494.
- Souls.total: 11.
- Kettle.pot: 0.0011478168 ETH.

Mainnet tier unlock thresholds:
- Uncommon: 2,500 finds.
- Rare: 5,000.
- Epic: 10,000.
- Legendary: 15,000.

The season was only about 0.21% depleted at this snapshot. A rough straight-line extrapolation from the first few hours is not reliable because hashrate, retargeting, price pressure and demand are endogenous.

## Mining mechanics

Every minute:
- miners search SHA256(address || nonce || challenge);
- one address can submit at most one valid find per minute;
- a valid find is paid for during the following minute;
- reveal later rolls type and tier using a delayed parent-chain-block seed.

Mainnet mine parameters:
- floor 30 bits;
- ceiling 43 bits;
- target kPerHour 20,000;
- reserve 1,000,000;
- price0 0.00002 ETH;
- no price ceiling;
- mythic key probability per mined reveal 1 / 65,536;
- one-tier upgrade probability 1 / 16.

Standalone NVIDIA miner supports up to 32 addresses per card. Browser CPU and WebGPU mining are also implemented.

## Cauldron economics

Correct current flow:
1. Mine submit fees go to Kettle.
2. On hourly Kettle tick, 40% of fresh fees goes to the Safe.
3. 60% joins Kettle pot / steam.
4. Stream remains closed until 100 Souls exist.
5. Once open, about 4.17% (1/24) of the pot is poured into the Soul Stream each hour, with a 0.01 ETH minimum pour.
6. Soul holders claim by weight.

Therefore the common summary “60% is paid to Souls every hour” is inaccurate. Only a fraction of the accumulated 60% pot drips each hour after the 100-Soul gate is open.

## Soul supply and weights

Total cap: 5,555.

Quotas:
- Apprentice: 3,014
- Adept: 1,111
- Master: 833
- Magister: 555
- Archmage: 21
- named Souls: up to 21

Base weights:
- Apprentice 1
- Adept 4
- Master 16
- Magister 64
- Archmage 256
- named 512

From Adept upward, the first 100 of a rank receive a founder multiplier that starts at 2.0x for No.1 and tapers to 1.0x by No.100. Apprentices do not receive this early multiplier.

This creates a real early-position advantage only for higher-rank Souls, not for simply minting an early Apprentice.

## Main-act incompleteness

The v4 mainnet intentionally has:
- `withAlchemists: false`
- `Alchemists: null`

The current opening act includes mining, refining, reroll, ritual item crafting, Souls, Kettle and Stream infrastructure.

The final Alchemist summoning/main-act contract is still pending. This is an important execution risk because a major part of the long-run game loop is not live yet.

## Security and governance

No external audit has been completed.

Internal reviews found and fixed multiple serious issues immediately before launch, including:
- critical reveal reentrancy that could settle one find multiple times;
- high-severity Stream accounting/DoS issues;
- predictable randomness that could have enabled selective committing for rare outcomes / mythic keys;
- several lower-severity claim and receiver-hook problems.

The fixes and regression tests are positive evidence of engineering effort, but the fact that critical/high issues were found days before mainnet means residual smart-contract risk should be discounted heavily.

v4 governance is materially centralized:
- earlier v1-v3 used a 48-hour timelock;
- v4 has no timelock;
- the Safe directly owns/administers the game contracts and is guardian;
- parameter changes, pause/unpause and emergency rescue become effective immediately after Safe execution;
- the current mainnet Safe is documented as 2-of-2.

The collection owner wallet is mainly the marketplace face and cannot change token economics; the Safe is the meaningful governance authority.

## Secondary market

The contracts implement:
- ERC-7572 collection metadata;
- ERC-2981 5% creator royalties;
- an explicit collection-owner wallet intended as the OpenSea marketplace face.

Robinhood Chain NFT collections are supported/traded on OpenSea in general.

As of this review, no reliable indexed Alchemists collection floor, bid depth or completed-sale history was found. Marketplace compatibility must not be treated as proven liquidity.

## Team and development

Team identity remains weak. The public GitHub owner is `simonborel617-cmyk`; no independently verified founder/company track record was established in this review.

Code activity is materially stronger than social traction:
- substantial open-source contracts/dapp/miner/runbook/simulation/security-review code;
- Dawnscan recorded about 75 commits in the last 90 days;
- activity appears concentrated in one contributor.

Single-contributor dependency remains a major operational risk.

## Profitability status

Current mining expected value is UNRESOLVED.

Known cost:
- current paid submit price approximately 0.00002389152 ETH per successful find, plus gas and compute/electricity.

Unknown output value:
- no verified liquid clearing price for ordinary Materials;
- no verified active floor/bid depth for Souls;
- mythic key market value unknown;
- Soul stream is not yet open because only 11 Souls existed at the snapshot;
- final Alchemist main-act value is unknown.

Do not compute “days to breakeven” before these market/yield values exist.

## Promotion gates

Remain WATCH until several of these are satisfied:

1. At least 100 Souls and Stream opens.
2. Actual ETH claim rate per Soul weight can be measured.
3. Alchemists Materials / Souls obtain executable secondary-market bids and real sales.
4. Unique active miners / addresses and paid submit rate remain healthy after launch novelty.
5. Kettle/Safe fee flows reconcile cleanly on chain.
6. No security incident after the first days of production.
7. External audit is published, or enough live time and code review substantially reduce contract uncertainty.
8. Final Alchemists main-act contract is deployed with reviewed code.
9. Social/community growth begins to match on-chain usage.

Promotion to SETUP requires a measurable expected-value advantage after submit cost, gas, hardware/electricity, failed crafts and realistic NFT exit liquidity.

## Invalidation / downgrade

Downgrade to SKIP on:
- material exploit;
- Safe/governance compromise;
- unexplained treasury flow;
- significant rules change without transparent explanation;
- activity collapses before secondary liquidity forms;
- OpenSea/listing exists but bids/sales remain absent;
- developer disappears;
- main-act delivery stalls while mining payments continue.

## Key lesson

Alchemists is a useful example of a project where technical reality is ahead of market proof.

The correct analysis order is:
live contract state -> paid activity -> secondary liquidity -> Soul cash-flow -> main-act completion.

Do not infer profitability from GitHub quality, mining difficulty or the existence of an OpenSea-compatible NFT collection alone.
