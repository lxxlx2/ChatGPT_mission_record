# JUMP / Jumper Legion — operational position

Human-facing historical research: `research/projects/jump/jump-legion-sale.md`
Refund incident evidence: `research/projects/jump/jump-reclaim-2026-10-07.md`
Operational compatibility path retained for monitoring safety.

Updated: 2026-10-07 Asia/Bangkok

## Current authoritative state

- `APPLICATION_STATUS = UNSUCCESSFUL / REJECTED`
- `FINAL_ALLOCATION = 0`
- `JUMP_TOKEN_POSITION = 0`
- `ORIGINAL_DEPOSIT = 1,000 USDC`
- `AGREEMENT_SIGNATURE = VOIDED`
- `RECLAIM_STATUS = COMPLETE_ONCHAIN`
- `PRODUCTION_TRADING = NO_GO`

The previous `IN_REVIEW_BY_PROJECT` and `RECLAIM_PENDING` states are superseded.

## Confirmed purchase / deposit

Ethereum Mainnet purchase transaction:

`0xab75877dae845838dc2a2c7904af37076dfc0408af31a23e84e601ffa4d5083b`

- participating wallet: `0x3Df4eBE3e5Bd012F459cD3392c90a2d8b576Ea7C`
- sale contract: `0x1324d9CA99b5AFfF6e8ceb4083EF744b3B6f4161`
- method: `invest(uint256,bytes)`
- deposited amount: **1,000 USDC**
- timestamp: `2026-09-29T13:48:23Z`

## Confirmed refund / closure

Refund transaction:

`0x3d3264417775aa9cf0bf5d83f69f00b2ada9e01852784bc52897264025c5e0b5`

Confirmed ERC-20 transfer:

- from: Jumper Legion sale contract `0x1324d9CA99b5AFfF6e8ceb4083EF744b3B6f4161`
- to: participating wallet `0x3Df4eBE3e5Bd012F459cD3392c90a2d8b576Ea7C`
- amount: **1,000 USDC**
- timestamp: `2026-10-06T17:28:23Z`

Latest direct contract-state read after refund:

- `investedCapital = 0`
- `hasSettled = false`
- `hasClaimedExcess = false`
- `hasRefunded = true`
- `vestingAddress = 0x0000000000000000000000000000000000000000`

Therefore the sale deposit is no longer locked in the Legion contract.

## Accounting rule

- JUMP allocation from this sale: **0**.
- Pending JUMP capital: **0**.
- Do not add the refunded 1,000 USDC as a separate current asset; it is already reflected wherever the user subsequently holds the returned funds.
- Any future JUMP exposure requires a new independently verified position.

## Incident note

The Legion page initially showed `E999` when reclaim was attempted immediately after sale end. The direct on-chain refund subsequently completed successfully, so the incident is closed from a capital-recovery perspective.