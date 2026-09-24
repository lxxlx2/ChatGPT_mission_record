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
