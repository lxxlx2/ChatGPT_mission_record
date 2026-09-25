# UNICRED Position

Updated: 2026-09-24 18:21 Asia/Bangkok

## Canonical contracts
- Chain: Unichain, chain id 130.
- CRED ERC-20: `0x0FBc2Fc1366D5BA517E6ca5A304c10359F554E0D`.
- UNICRED NFT ERC-721: `0xf60de24F228dc7Ca6fF025958d2eE3A956ED88E5`.
- Both contracts were directly verified on Blockscout as non-proxy verified Solidity contracts during the 2026-09-24 review.

## User position
- NFT: UNICRED #230.
- NFT acquisition cost: 0.0105 ETH.
- OpenSea snapshot before staking: Common rarity trait, overall rarity rank about #425; highest offer about 0.0108 WETH; collection floor about 0.0068 ETH. #230 also had several relatively uncommon traits such as Mint background and Cyan/Yellow/Black layers.
- Staking: 7 days / 1x.
- Lock shown by official UI: until 2026-10-01.
- Contract behavior: after the 7-day lock ends, the NFT continues earning at the same 1x weight until the user actively unstakes.
- No early unstake is available.

## CRED execution
- User initially held about 205.560605 CRED.
- User reports selling enough CRED to recover the CRED principal.
- Wallet snapshot after this execution shows 51.390151 CRED remaining, about 25% of the original CRED amount.
- Snapshot price: about USD 0.13755/CRED, retained CRED value about USD 7.06.
- Treat the remaining 51.390151 CRED as a profit runner unless later user transactions supersede this state.
- Do not add new capital automatically.

## Staking live baseline
User-reported elapsed staking time: about 52 minutes.
Official UI snapshot around that time:
- Minted: 1,403 / 4,444.
- Epoch: 4 / 11.
- Current mint price: 0.008 ETH.
- Unicorns staked: 575.
- Total staking weight: 2,080.
- User share displayed: about 0.05%.
- Rent waiting snapshot: about 0.000794 ETH.
- User then showed a wallet confirmation of approximately +0.00087 ETH, about USD 2.30, from unicred.fun. Treat 0.00087 ETH after ~52 minutes as the first user-confirmed realized rent sample.
- Baseline realized pace from that sample: about 0.001004 ETH/hour.
- At a constant pace, 0.0105 ETH NFT acquisition cost would be recovered in about 10.5 hours, but this is NOT a forecast because staking weight, mint pace and epoch mint price all change rapidly.

## Verified protocol mechanics
From verified NFT contract source:
- MAX_SUPPLY = 4,444.
- Epoch size = 404.
- Mint price starts at 0.002 ETH and increases 0.002 ETH per epoch up to 0.022 ETH.
- Target pace is 10 seconds per unicorn, with dynamic difficulty.
- Mint revenue split: 65% to stakers, 25% to CRED buyback, 10% to builders.
- Stake terms: 7d = 1x, 14d = 2x, 30d = 4x.
- CRED trading opens after NFT #404.
- Burning an NFT mints CRED; current-epoch burn reward starts at 200 CRED and older epochs decay continuously/halve as later epochs progress.
- #230 is an old Epoch-1 NFT, so its burn value is much lower than 200 CRED and burn is not the preferred route at the current state.
- NFT royalty is 5%, routed to the buyback hook.
From verified CRED contract source:
- Initial supply = 1,000,000 CRED.
- Initial team allocation = 50,000 CRED, explicitly not vested in the source comment.
- 950,000 initial CRED to launch/pool.
- After launch, only the NFT contract can mint CRED via NFT burns.

## Monitoring / action rules
Hourly mission monitoring should check:
1. Minted / 4,444, current epoch, current mint price, mint pace.
2. Unicorns staked and total staking weight, because dilution changes the user's rent share.
3. User rent rate where observable. Compare realized/claimable rent to the ~0.001004 ETH/hour initial sample, but do not alert on ordinary dilution.
4. CRED price, liquidity, volume, current total supply, CRED bought-back/burned, NFTs burned, and major holder/liquidity changes.
5. Official unicred.fun / @Unicred0 rule changes, contract/admin changes, buyback changes, royalty changes, exploit/security reports.
6. NFT #230 / collection floor and offers when useful, especially near/after unlock.
7. Stake unlock on 2026-10-01. At unlock, decide whether to keep earning at 1x or unstake/sell based on remaining mint supply, ongoing rent, NFT secondary value and CRED/buyback health.

Actionable alerts:
- SOLD OUT / near sold out: if minting reaches 4,444 or remaining mints become very small, notify because new mint-rent generation is ending; give claim/unlock plan.
- SECURITY / MECHANISM: exploit, owner/admin change affecting user value, buyback/royalty/staking rule change, abnormal liquidity removal, or contract identity conflict.
- CRED EXIT/REDUCE: notify only when a major price/liquidity/supply move creates a clearly actionable profit-protection or exit decision; routine volatility stays silent.
- UNLOCK: on or after 2026-10-01, notify with exact recommendation to remain staked or unstake/list based on live economics.
- Do not send repetitive rent updates, routine mint progress, or ordinary CRED price noise. Those go to GitHub only.


## Mint-speed baseline — 2026-09-24

User observed the project felt slower. The available user snapshots provide a useful realized baseline:
- Earlier pre-stake snapshot: about 1,091 minted.
- Later snapshot after about 52 minutes of staking: about 1,403 minted.
- Increase: 312 mints in about 52 minutes.
- Realized average rate: about 6.0 mints/minute, approximately 1 mint every 10 seconds.

This matches the contract's target pace of about one unicorn every 10 seconds. Therefore, over that measured 52-minute window, minting had NOT materially slowed on average, even if the UI appeared visually stagnant for short intervals.

Monitoring rule:
- Calculate rolling mint pace whenever consecutive reliable minted/time snapshots are available.
- Flag a meaningful slowdown if the rolling pace falls below roughly 50% of target for >=30 minutes (slower than about 1 mint every 20 seconds), or if there is an idle period long enough to activate repeated difficulty halving.
- Flag a severe slowdown if pace is below roughly 25% of target for >=30 minutes (slower than about 1 mint every 40 seconds).
- Do not alert on short 5-10 minute pauses alone, because the PoW difficulty explicitly retargets and halves after idle intervals.


## Rent-end / breakeven model — 2026-09-24 18:46 Asia/Bangkok

Clarification of protocol economics:
- Staker rent is funded only by the 65% share of each NEW unicorn mint.
- Once unicorn #4,444 has been minted, no further mint-funded rent is created.
- Any rent already accrued but not yet claimed remains claimable after minting ends; sold-out does not erase accrued rent.
- Secondary-sale royalty does not fund stakers; it belongs to the project's separate royalty/buyback flow per the current official docs.

Observed mint-speed baseline:
- 1,091 -> 1,403 minted over about 52 minutes = 312 mints / 52 min = exactly about 6.0 mints/min, or 1 mint every 10 seconds.
- At the #1,403 snapshot, 3,041 remained. If the protocol target pace of 10 sec/mint held continuously, theoretical sold-out time from that snapshot is about 8.45 hours later, approximately 2026-09-25 02:48 Asia/Bangkok.
- This is a theoretical target-time estimate only; PoW difficulty and miner participation can make actual completion earlier/later.

User rent state:
- NFT acquisition cost: 0.0105 ETH.
- First confirmed claimed rent: about 0.00087 ETH after about 52 minutes.
- Pure-rent principal still unrecovered after that claim: about 0.00963 ETH.
- Initial realized sample pace: ~0.001004 ETH/hour.
- Current-state instantaneous model at 1,403 minted / total weight 2,080 / mint price 0.008 ETH / target 360 mints per hour gives ~0.00090 ETH/hour for a 1x stake.

Dilution matters materially:
- From the earlier snapshot 1,091 minted / total weight 1,409 to 1,403 minted / total weight 2,080, weight increased 671 while 312 NFTs were minted, or about +2.15 staking-weight units per new mint during that interval.
- If that unusually fast recent dilution continued all the way to sold out, projected additional rent from #1,404 to #4,444 is only about 0.00589 ETH; total rent including the first 0.00087 claim would be about 0.00676 ETH, around 64% of the 0.0105 ETH NFT cost. Pure-rent breakeven would not occur before sold out.
- A more moderate base case of +1.3 weight per future mint projects about 0.00752 ETH additional rent and about 0.00839 ETH total including the first claim, around 80% of NFT cost. Pure-rent breakeven still would not occur before sold out.
- Mild dilution of only +0.5 weight per mint would allow pure-rent breakeven around mint #4,223, about 7.83 target-pace hours after the #1,403 snapshot.
- Zero further dilution is an unrealistic upper bound; it would reach pure-rent breakeven around mint #3,678, about 6.32 target-pace hours after #1,403.

Therefore the current reasonable base case is:
- RENT ALONE probably does NOT fully recover the 0.0105 ETH purchase cost before minting ends if staking dilution remains material.
- Economic breakeven can still occur because #230 remains an NFT after the 7-day lock. Under the +1.3 weight/mint base case, projected rent shortfall is about 0.00211 ETH, so a net NFT resale value above roughly 0.00211 ETH after unlock would cover the remaining purchase cost.
- Recompute this model hourly using actual minted progression, totalWeight, mint price and cumulative user rent rather than relying on the initial fixed assumptions.

Hourly rent monitoring requirements:
- Wallet: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`.
- NFT token id: #230.
- Track cumulative claimed rent plus current claimable/pending rent when chain data or the official app exposes it.
- RENT_BREAKEVEN is reached when cumulative claimed + claimable rent >= 0.0105 ETH. Send an immediate email/action notification at that point.
- Also calculate an economic-breakeven view when a credible executable OpenSea offer/floor is available: cumulative rent + estimated net executable NFT sale proceeds >= 0.0105 ETH.
- Every hourly run must write a UNICRED rent line to GitHub even if there is no alert: current minted, current epoch/mint price, staked count, total weight, observed mint pace, claimed rent known to Mission, claimable rent if available, latest hourly rent delta if available, projected rent-only breakeven status and projected sold-out time.
- If exact wallet-specific claimable rent is unavailable in a run, mark it unavailable rather than guessing. Continue to estimate protocol-level rent rate from mint price and totalWeight.


## Live update — 2026-09-25 00:16 Asia/Bangkok
User-provided official unicred.fun snapshot:
- Minted: 3,011 / 4,444.
- Epoch 8 / 11.
- Mint price: 0.016 ETH.
- Difficulty: 32.0 bits.
- Unicorns staked: 1,231.
- Total weight: 4,280.
- User share: about 0.02%.
- Current rent waiting after the latest claim: 0.000049 ETH.
- User reports the latest claim was about USD 7. This exact claim amount is not direct-chain verified in this update; treat it as approximate.

Observed mint-speed update:
- Prior reliable snapshot: 1,403 minted at about 2026-09-24 18:21 Asia/Bangkok.
- Current snapshot: 3,011 minted around 2026-09-25 00:16.
- +1,608 mints over about 355 minutes = about 4.53 mints/minute, roughly 1 mint every 13.25 seconds.
- This is moderately slower than the 10-second target but far above the monitor's meaningful-slowdown threshold of 20 seconds/mint.
- 1,433 mints remain. If the latest observed 13.25 sec/mint pace persists, theoretical sold-out is about 5.27 hours after the current snapshot, around 2026-09-25 05:32 Asia/Bangkok. At exact target pace it would be about 3.98 hours.

Rent economics update:
- First confirmed claim: ~0.00087 ETH (~USD 2.30 at the time).
- Latest user-reported claim: ~USD 7, approximately ~0.00260 ETH using ~USD 2,690/ETH only as an accounting estimate.
- Approx cumulative claimed: ~0.00347 ETH; plus current waiting 0.000049 ETH = ~0.00352 ETH known/estimated rent, about 33.5% of the 0.0105 ETH NFT purchase cost.
- Total weight rose from 2,080 at mint #1,403 to 4,280 at #3,011, +2,200 weight over 1,608 mints = about +1.37 weight per new mint. This validates the prior +1.3/mint base dilution model.
- Starting from #3,011 and weight 4,280, the remaining scheduled mint revenue through #4,444 is ~27.776 ETH; staker pool share is ~18.0544 ETH and CRED buyback budget is ~6.944 ETH before future rule changes.
- Under a +1.37 weight/mint dilution model, #230 is projected to earn only about another ~0.00343 ETH through sold-out. Estimated final rent including current claimed/waiting is about ~0.00695 ETH, roughly 66% of purchase cost.
- Therefore rent-only breakeven is now unlikely before sold-out. Whole-position breakeven remains plausible because #230 survives as an NFT. Under the current base case, the remaining cost gap after all projected rent is roughly 0.00355 ETH before sale fees/royalty. This is the minimum residual NFT value that matters economically.
- Do not add another UNICRED NFT or more CRED from Mission capital. Primary protocol buyback source is finite and minting is already in Epoch 8/11.

CRED market update:
- Public OpenSea token page near this update shows about USD 0.2393/CRED, FDV/market value about USD 223K, 24h volume about USD 371K, 612 holders, supply about 933.6K, ATH about USD 0.2784.
- Remaining 51.390151 CRED is therefore roughly USD 12.3 at that reference price.
- Because CRED is already near its young ATH, the remaining primary-mint buyback budget is finite (~6.944 ETH), and NFT burns can mint fresh CRED, there is no data-driven case to add fresh capital now. Continue as a principal-recovered profit runner.


## Direct Unichain RPC correction — 2026-09-25
Alchemy direct RPC confirms the primary EVM wallet currently holds:
- 0.006739974356883644 native ETH on Unichain.
- 25.69507573368924 CRED at `0x0FBc2Fc1366D5BA517E6ca5A304c10359F554E0D`.
This supersedes the older 51.390151 CRED wallet snapshot for current position accounting. Treat the CRED principal as already recovered; the remaining 25.69507573368924 CRED is the current profit-runner balance.


## Live chain update / unlock instruction — 2026-09-25 08:53 Asia/Bangkok

Direct Unichain contract reads for UNICRED #230:
- totalMinted: 3,188 / 4,444.
- Current mint price: 0.016 ETH.
- stakedCount: 1,486.
- totalWeight: 5,152.
- #230 current claimable rent: 0.000006060606060606 ETH.
- #230 on-chain unlockAt: Unix 1790850484 = 2026-10-01 10:28:04 UTC = **2026-10-01 17:28:04 Asia/Bangkok**.
- Contract lastMintTime at the snapshot: 2026-09-25 01:53:11 UTC = 08:53:11 Asia/Bangkok.

### Mint pace diagnosis
The user snapshot around 2026-09-25 00:16 Asia/Bangkok showed 3,011 minted. Current chain state is 3,188 at about 08:53, only +177 over about 8h37m:
- broad-window realized pace: about 1 mint every 2.9 minutes.
- This is roughly 17.5x slower than the protocol target of 1 mint every 10 seconds.

A more recent transaction sample from the contract shows 9 successful `mine` calls between 07:48:05 and 08:53:11 Asia/Bangkok, with one reverted attempt in the same page:
- recent successful pace is about 1 mint every 8.1 minutes.
- Therefore minting is **severely slower than target but not halted**. A successful mint occurred at 08:53:11.
- 1,256 NFTs remain. At the broad-window ~2.9 min/mint pace this is roughly 61 hours remaining; at the recent ~8.1 min/mint pace roughly 7.1 days. These are scenario estimates only because PoW difficulty and miner participation can change.

### Mandatory unlock alert
The existing `$300 Crypto盈利监控` must send an actionable Gmail alert at the first run at or after **2026-10-01 17:28:04 Asia/Bangkok**.
Alert should state that #230 is now legally/contractually unstakeable, read live minted/4444, mint pace, remaining mint-funded rent, current claimable rent, NFT floor/offer, and recommend one of:
- unstake + list/sell,
- unstake + hold,
- remain staked at 1x,
based on live economics.
Do not create a separate automation for this unlock.
