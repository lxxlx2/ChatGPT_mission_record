# JUMP / Jumper Legion — rejected allocation + 1,000 USDC refund closure

Updated: 2026-10-07 Asia/Bangkok

## Final state

- `APPLICATION_STATUS = UNSUCCESSFUL / REJECTED`
- `ACCEPTED_INVESTMENT = 0 USDC`
- `JUMP_ALLOCATION = 0`
- `ORIGINAL_DEPOSIT = 1,000 USDC`
- `AGREEMENT_SIGNATURE = VOIDED`
- `RECLAIM_STATUS = COMPLETE_ONCHAIN`

The earlier Legion UI `[E999]` reclaim failure is superseded by a confirmed successful on-chain refund.

## Original deposit evidence

Purchase transaction:

`0xab75877dae845838dc2a2c7904af37076dfc0408af31a23e84e601ffa4d5083b`

Confirmed facts:

- chain: Ethereum Mainnet
- status: success
- timestamp: `2026-09-29T13:48:23Z`
- participating wallet: `0x3Df4eBE3e5Bd012F459cD3392c90a2d8b576Ea7C`
- sale contract: `0x1324d9CA99b5AFfF6e8ceb4083EF744b3B6f4161`
- call: `invest(uint256,bytes)`
- invested amount: **1,000 USDC**
- USDC contract: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`

The sale contract is an EIP-1167 proxy to verified `LegionPreLiquidSaleV2` implementation `0x11077edDFc6dB5abFDB9E019A64172B5d8E81A3a`.

## Earlier reclaim incident

Immediately after the sale ended, the authenticated Legion UI showed:

- Application unsuccessful.
- Amount to claim: 1,000 USDC.
- Agreement Signature: VOIDED.
- Reclaim USDC button visible.
- `[E999] Something went wrong` when reclaim was attempted.

At the earlier chain read the position still showed 1,000 USDC invested and `hasRefunded=false`. The verified contract exposed a no-argument `refund()` path during the refund window.

## Successful refund evidence — CONFIRMED

Refund transaction:

`0x3d3264417775aa9cf0bf5d83f69f00b2ada9e01852784bc52897264025c5e0b5`

Confirmed ERC-20 transfer:

- from: sale contract `0x1324d9CA99b5AFfF6e8ceb4083EF744b3B6f4161`
- to: participating wallet `0x3Df4eBE3e5Bd012F459cD3392c90a2d8b576Ea7C`
- token: USDC
- amount: **1,000 USDC**
- timestamp: `2026-10-06T17:28:23Z`

Latest direct `investorPositionDetails()` state after refund:

- `investedCapital = 0`
- `hasSettled = false`
- `hasClaimedExcess = false`
- `hasRefunded = true`
- `vestingAddress = 0x0000000000000000000000000000000000000000`

This confirms that the full deposit was returned and the sale position was closed.

## Accounting conclusion

`JUMP_PUBLIC_SALE_POSITION = CLOSED_REJECTED_ZERO_ALLOCATION`

`JUMP_TOKEN_POSITION = 0`

`LEGION_PENDING_CAPITAL = 0`

Do not add the 1,000 USDC refund as a standalone asset on top of current wallet/CEX balances; subsequent current holdings already determine where that capital sits now.

## Historical refund-window reference

Previously confirmed sale configuration:

- sale end: `2026-10-06 23:54:59 Asia/Bangkok`
- refund window end: `2026-10-20 23:54:59 Asia/Bangkok`

The E999 issue occurred shortly after sale end. Because the chain refund later succeeded, no further recovery action is required unless a discrepancy appears in the receiving wallet history.