# Current Portfolio / Capital Map

Updated: 2026-09-25 00:16 Asia/Bangkok

## Verification policy
Balances below are separated into: user-confirmed UI/screenshot, independently market-verified, and pending direct RPC verification. At this update Blockscout live wallet reads require a PRO API key and the connected Alchemy authorization is expired, so Base/Solana wallet balances cannot be falsely labeled direct-chain verified. Public Etherscan multichain indexing is stale/inconsistent with the user's current wallet state and is rejected as a balance source.

## Wallets
- EVM primary wallet: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

## Current user-confirmed liquid balances
- Solana: about 212 USDC available.
- Base: about 500 USDC available.
- Total active-strategy stablecoin liquidity: about 712 USDC.
- Separate low-risk capital bucket: 500 USD-equivalent. This bucket is NOT available for speculative Mission positions.
- PONS 50 USDT margin budget already exists separately on Binance; only the first 0.625 entry is filled, deeper orders remain open.

## Active non-stable positions
- SHARTCOIN: 44,982.986297 tokens, user intends to hold and has cancelled prior conditional/limit sell orders. Current market reference near this update about USD 0.00386, so indicative value about USD 174. Do not treat this reference as wallet valuation truth without live wallet/RPC.
- UNICRED CRED: 51.390151 CRED profit runner after principal recovery. Current public OpenSea token reference near USD 0.2393, indicative value about USD 12.3.
- UNICRED NFT #230: 7-day / 1x stake until 2026-10-01. Purchase cost 0.0105 ETH.
- Credits: Credit #23042 listed 0.25 ETH; Credit #23232 listed 0.40 ETH. No planned sale-price change at this update.
- PONSUSDT perpetual: first entry 0.625 filled; remaining 0.585 and 0.545 bids open; 3x isolated; hard stop 0.498 Mark Price.

## Active 712-USDC allocation map
- 150 USDC: hard opportunity reserve for short-window launches/memes/ICOs similar to SHARTCOIN. Prefer keeping this immediately deployable; do not consume it for ordinary averaging-down.
- JUMP/Legion: reserve 250 USDC now. If official Legion/Jumper sale terms confirm FDV <=75M, >=50% TGE unlock, sane initial circulation and no new adverse term, raise application ceiling to 300 USDC. If 75-100M FDV, max 250; 100-125M, max 150; >125M or severe unlock/float overhang, re-evaluate/skip rather than forcing participation.
- ETH: reserve up to 100 USDC, deployed only after the Sep-25 options-expiry review, in two bullets (50 + 50 confirmation/add-on).
- Remaining uncommitted stablecoin cash after a max 300 JUMP + 100 ETH + 150 opportunity reserve: about 162 USDC.
- PONS uses its existing separate 50-USDT margin budget; no increase.
- No fresh allocation to CRED, SHARTCOIN, Credits or UNICRED NFT at this state.

## Separate 500 low-risk bucket
Current action preference:
- 300 USDT: use the user's account-specific Binance 5-day ~25% APR offer only if the final subscription screen still shows the 300-USDT eligible tier and 5-day bonus.
- 200 USDC: Binance USDC Flexible while the current bonus tier remains available; public Binance campaign runs through 2026-09-30 23:59:59 UTC and gives 7% APR on the <=300 USDC tier, plus/minus live real-time APR differences shown in the user's account.
- Do not use this low-risk bucket for QQQ/stock-token LP, pPOLY LP, high-yield DeFi vaults, leveraged loops, depeg-sensitive structured products or new-protocol farms. They cannot satisfy the user's principal-preservation constraint.
- Re-evaluate the 500 bucket when the 5-day USDT offer expires and again at the end of the USDC promotion. Do not assume current promotional APR persists long-term.


## Alchemy RPC re-verification — 2026-09-25
A dedicated Alchemy app `ChatGPT Crypto Monitor` was created with Ethereum, Base, Solana, Unichain and Robinhood mainnets enabled and successfully tested.

Latest direct RPC balances:
- Solana wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
  - SOL: 0.063843747 SOL.
  - canonical USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`: 712.106982 USDC.
  - SHART mint actually held is `UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids`: 33,737.239723 SHART.
  - The alternate candidate mint `GKpNJz7yMuhZka9izamv6sDUxCsDr58pFMUaw1TQpump` returned zero balance for this wallet.
- EVM wallet `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
  - Base native ETH: 0.000791653069719195 ETH.
  - canonical Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`: 0.010429 USDC.
  - Unichain native ETH: 0.006739974356883644 ETH.
  - Unichain CRED: 25.69507573368924 CRED.

This supersedes the prior user-reported 212 Solana USDC + 500 Base USDC split for current wallet accounting. The current direct-chain state is ~712.107 USDC on Solana and ~0.0104 canonical USDC on Base. Do not infer whether the 500 was bridged/transferred without transaction-history verification.


## BTC tactical overlay
- Dedicated BTC allocation: 0 USDC at this update.
- BTC is monitored as a market-regime anchor under `strategy.md` and `watchlists/btc-regime-jasonleo.md`.
- Any fresh BTC long, short or hedge requires explicit user approval before capital is reassigned.
- Do not consume the 150 USDC hard opportunity reserve, JUMP reserve, ETH reserve or the separate 500 principal-preservation bucket automatically.
- If a BTC trade is later approved, source it only from then-current uncommitted speculative cash unless the user explicitly changes the capital map.


## Direct chain reconciliation — 2026-09-25 08:53 Asia/Bangkok

Alchemy app `ChatGPT Crypto Monitor` direct RPC snapshot:

### Solana wallet
Wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- SOL: 0.063596996 SOL.
- Canonical USDC (`EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`): 774.010034 USDC.
- SHARTCOIN canonical held mint (`UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids`): 8,434.309931 SHART.
These supersede prior Solana balance snapshots.

### Unichain wallet
Wallet: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Native ETH: 0.000134598028353274 ETH.
- USDC (`0x078d782b760474a361dda0af3839290b0ef57ad6`): 0.021286 USDC.
- CRED (`0x0FBc2Fc1366D5BA517E6ca5A304c10359F554E0D`): 0 CRED.
- UNICRED #230 remains staked in the protocol and is tracked separately from liquid wallet token balances.

Do not infer the causes of balance changes from prior snapshots without checking transaction history. Current Mission accounting should use the direct-chain balances above.


## JUMP reserve refresh — 2026-09-25
Latest direct-chain Solana USDC is ~782.385054.
Active speculative-capital reservation:
- 400 USDC conditional JUMP Legion application at 75M/50%-TGE/4mo terms.
- 150 USDC short-window launch/meme reserve.
- 100 USDC ETH trading reserve.
- ~132 USDC remains uncommitted.
Separate 500 low-risk bucket remains isolated.


## Authoritative live reconciliation — 2026-09-25 evening
This section supersedes all older balance/allocation snapshots above. `MISSION_SPEC.md` is the highest-priority authority.

Direct Alchemy reads:
- Ethereum mainnet: 400.308121 USDC; 0.001667063838788351 ETH.
- Solana: 390.866576 canonical USDC; 0.063112228 native SOL; approximately 0.033891318 WSOL across owned SPL token accounts; canonical SHART balance 0.
- Base: 0.252982 canonical USDC; 0.000790846510479134 ETH.
- Unichain: 0.021286 canonical USDC; 0.000231941590232335 ETH; CRED 0.
- Robinhood Chain: approximately 0.000081643478484768 native balance. Unknown/spam token balances are excluded until verified.
- Approx canonical on-chain stablecoin total: 791.448965 USDC.

User-confirmed off-chain / exchange state:
- PONS budget remains 50 USDT isolated; only the 0.6250 first entry is filled. The 0.5850 and 0.5450 orders remain pending. No budget increase.
- Separate 500 USD-equivalent low-risk bucket is currently earning interest and remains outside speculative Mission capital.

Current speculative allocation:
- 400 USDC JUMP conditional reserve is already on Ethereum mainnet.
- 150 USDC short-window launch / ICO / NFT opportunity reserve.
- 100 USDC ETH setup reserve.
- Approximately 141 USDC-equivalent remains uncommitted after those reservations, including Base/Unichain USDC dust.
- SHART is closed for exposure accounting because direct wallet balance is now 0.
- Liquid CRED is closed for exposure accounting because direct wallet balance is now 0.
- UNICRED #230 remains active as the staked NFT position; Credits #23042 and #23232 remain active listings.

Do not infer the reason for any balance change without transaction-history verification.


## WSOL auxiliary-account correction — 2026-09-25
Direct Solana RPC shows four wallet-owned native WSOL token accounts:
- `6FV88kiLJFmm5bprPfD4NitTHNFsfyUZZFn6wFNrLziE`: 0.019445574 WSOL + 0.002039280 SOL rent reserve = 0.021484854 SOL recoverable on close.
- `6LbxShFopPRf56AWJvdQP57CnTNW5G9nvw8rKQhfofi1`: 0.006972803 WSOL + 0.002039280 rent = 0.009012083 SOL recoverable.
- `8XszhZXZUKPiCLCkC7pbvhLyDwZqQQ8YV6BHHqY9X8TT`: 0.007191552 WSOL + 0.002039280 rent = 0.009230832 SOL recoverable.
- `FuC71ndKhDJ6ngtwGfoy7o44vEjuhacg2x2KwSJiSxW8`: 0.000281389 WSOL + 0.002039280 rent = 0.002320669 SOL recoverable.

Token amount total = 0.033891318 WSOL. Full lamports recoverable by closing all four native WSOL accounts = **0.042048438 SOL** before transaction fees. With current native wallet balance 0.063112228 SOL, post-close native SOL would be about **0.105160666 SOL** before transaction fees.

These accounts are auxiliary native-token accounts associated historically with Orca Whirlpool activity. Wallet swap UIs may fail to spend them because they are separate token accounts rather than a single default token account. For wrapped SOL, the protocol-level recovery operation is CloseAccount/unwrap, not a market swap. Do not treat 0.033891318 alone as the full recoverable amount because refundable rent is also present.
