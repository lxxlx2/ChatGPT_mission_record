# Crypto Mission Latest State

Market snapshot base: 2026-09-25 21:33 Asia/Bangkok
Wallet reconciliation: refreshed after the 21:33 run

Main status: NO_ACTION

## Capital / wallets
Direct Alchemy snapshot:
- Ethereum mainnet: 400.308121 USDC; 0.001667063838788351 ETH.
- Solana: 390.866576 canonical USDC; 0.063112228 native SOL; approximately 0.033891318 WSOL across owned token accounts; SHART canonical balance 0.
- Base: 0.252982 canonical USDC; 0.000790846510479134 ETH.
- Unichain: 0.021286 canonical USDC; 0.000231941590232335 ETH; CRED 0.
- Robinhood Chain: approximately 0.000081643478484768 native balance.
- Approx canonical on-chain stablecoin total: 791.448965 USDC.
- Separate 500 USD-equivalent low-risk bucket is user-confirmed as earning interest and remains outside the speculative Mission.

Current reserve map:
- 400 USDC JUMP conditional reserve, already on Ethereum mainnet.
- 150 USDC short-window opportunity reserve.
- 100 USDC ETH setup reserve.
- Approximately 141 USDC-equivalent currently uncommitted.
- PONS uses a separate 50-USDT margin budget.

## PONS
- User-confirmed execution state: only the 0.6250 entry is filled.
- 0.5850 and 0.5450 resting orders remain pending and must not be counted as filled exposure.
- Hard stop remains 0.4980 Mark Price.
- 50-USDT margin budget is unchanged and cannot be increased automatically.
- Latest formal market snapshot: mark 0.639780, index 0.639081, funding +0.031734%, OI 67.182M PONS, latest 4h top-trader position L/S 2.2987, broad-account L/S 1.3283, ADL risk HIGH.
- Funding is above +0.03% for the current interval but has not met the strategy's 24h persistence requirement. No new action.

## ETH
- No live Mission ETH position.
- Latest formal market snapshot: mark 2692.321, index 2693.227, funding +0.006550%, OI 2.289M ETH.
- Current post-expiry setup is not confirmed. Keep the 100-USDC reserve undeployed.

## JUMP / Legion
- 400.308121 USDC is already on Ethereum mainnet. Do not bridge the reserve again.
- Native Ethereum balance is 0.001667063838788351 ETH.
- Application target remains 400 USDC only if authenticated final terms remain approximately 75M FDV, 50% TGE unlock, remaining 50% linear over 4 months, with no material initial-float problem.
- >100M FDV => reduce target to 250 USDC.
- >125M FDV => re-evaluate / normally skip.
- First Mission run on Sep 29 at or after 19:00 Bangkok must perform the full TPA/Show Terms + gas preflight before the 20:00 opening.
- Gas buffer must cover at least 2x estimated approval + application cost; if an execution-grade estimate is unavailable and ETH remains below 0.003 ETH, warn to top up.

## SHARTCOIN
- Fresh direct Solana RPC: 0 SHART at the canonical mint.
- Mission exposure status: CLOSED.
- Hourly SHART price/liquidity monitoring is disabled unless a new position is opened or transaction-history reconciliation is requested.

## UNICRED
- Active exposure is UNICRED NFT #230 only.
- Liquid CRED balance is 0; standalone CRED position monitoring is disabled.
- Latest formal protocol snapshot: totalMinted 3,235 / 4,444; stakedCount 1,542; totalWeight 5,349; minting remains severely slower than target.
- Unlock remains 2026-10-01 17:28:04 Asia/Bangkok.
- First run at or after unlock must decide remain staked vs unstake+hold vs unstake+list/sell from live economics.

## Credits
- #23042 remains listed at 0.25 ETH.
- #23232 remains listed at 0.40 ETH.
- No new capital allocation.
- Full collection-market refresh moves to the medium lane unless a material Jack/Visualize Value event occurs.

## BTC regime
- No dedicated BTC position or budget.
- Latest formal snapshot: BTC mark 83,816.16; funding -0.002050%; OI 95,795 BTC.
- 79k risk-off trigger and 98k-105k hedge candidate zone are not active.
- BTC remains a regime/risk overlay only.

## Opportunity / NFT radar
- Hourly short-window token-launch and NFT discovery stays active.
- Capital source is the 150-USDC opportunity reserve unless the user explicitly reallocates.
- Candidate must pass canonical issuer, official action-path, identity/domain/contract and expected-upside gates before alerting.

## Scope correction
- BSC smart-money cluster research is excluded from this Mission monitor and is handled in a separate workflow.
- Historical BSC research files remain audit-only.

## Monitoring architecture
- :00 broad Crypto research pipeline.
- :14 airdrop/TGE monitor.
- :29 action-oriented Crypto Mission monitor.
- Fast lane every Mission run: wallet delta, PONS, ETH/BTC, JUMP, launch radar, NFT radar, active-position security.
- Medium lane every 3 hours: UNICRED economics, Credits market, slower holder/liquidity data.
- First run after 00:00: full multichain reconciliation and file consistency check.

## Decision
NO_ACTION. The main change is accounting/monitoring cleanup: JUMP funding is already on Ethereum, SHART and liquid CRED are closed, PONS exposure is only the first fill, and the separate BSC research stream has been removed from this Mission's scope.


## WSOL auxiliary-account correction — 2026-09-25
Direct Solana RPC shows four wallet-owned native WSOL token accounts:
- `6FV88kiLJFmm5bprPfD4NitTHNFsfyUZZFn6wFNrLziE`: 0.019445574 WSOL + 0.002039280 SOL rent reserve = 0.021484854 SOL recoverable on close.
- `6LbxShFopPRf56AWJvdQP57CnTNW5G9nvw8rKQhfofi1`: 0.006972803 WSOL + 0.002039280 rent = 0.009012083 SOL recoverable.
- `8XszhZXZUKPiCLCkC7pbvhLyDwZqQQ8YV6BHHqY9X8TT`: 0.007191552 WSOL + 0.002039280 rent = 0.009230832 SOL recoverable.
- `FuC71ndKhDJ6ngtwGfoy7o44vEjuhacg2x2KwSJiSxW8`: 0.000281389 WSOL + 0.002039280 rent = 0.002320669 SOL recoverable.

Token amount total = 0.033891318 WSOL. Full lamports recoverable by closing all four native WSOL accounts = **0.042048438 SOL** before transaction fees. With current native wallet balance 0.063112228 SOL, post-close native SOL would be about **0.105160666 SOL** before transaction fees.

These accounts are auxiliary native-token accounts associated historically with Orca Whirlpool activity. Wallet swap UIs may fail to spend them because they are separate token accounts rather than a single default token account. For wrapped SOL, the protocol-level recovery operation is CloseAccount/unwrap, not a market swap. Do not treat 0.033891318 alone as the full recoverable amount because refundable rent is also present.


## User-confirmed XRP update — 2026-09-26 06:08 Asia/Bangkok
- Variational Omni XRP-PERP position is **FILLED LONG**.
- 77.12 XRP at 1.55589, isolated 3x.
- TP 1.6280; SL 1.5140; liquidation 1.24430.
- Screenshot mark 1.56844; unrealized +0.97 USD (+2.42%).
- Position value ~120.96 USD; margin ~40.99 USDC; Omni equity 50.87 USD; available 10.55 USD.
- Use `positions/xrp-variational.md` as the position authority.

## Direct-chain WSOL update — 2026-09-26
- Solana native balance now **0.105136682 SOL** by direct Alchemy RPC.
- The four previously tracked auxiliary native WSOL accounts are closed (all return null).
- WSOL recovery is complete and no further recovery alert is required.
