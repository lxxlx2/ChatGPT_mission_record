# JUMP / Jumper Legion — operational position

Human-facing historical research: `research/projects/jump/jump-legion-sale.md`
Current reclaim incident evidence: `research/projects/jump/jump-reclaim-2026-10-07.md`
Operational compatibility path retained for monitoring safety.

Updated: 2026-10-07 00:12 Asia/Bangkok

## Current authoritative state

- `APPLICATION_STATUS = UNSUCCESSFUL / REJECTED`
- `FINAL_ALLOCATION = 0`
- `JUMP_TOKEN_POSITION = 0`
- `DEPOSITED_CAPITAL = 1,000 USDC`
- `LEGION_UI_AMOUNT_TO_CLAIM = 1,000 USDC`
- `AGREEMENT_SIGNATURE = VOIDED`
- `RECLAIM_STATUS = PENDING / NOT COMPLETED`
- Current Legion UI error on **Reclaim USDC**: `[E999] Something went wrong. Please try again, or contact support if the issue persists.`
- `PRODUCTION_TRADING = NO_GO` remains unchanged.

The previous `IN_REVIEW_BY_PROJECT` state is superseded. Do not carry any JUMP allocation or JUMP token quantity forward from this sale.

## Confirmed purchase / deposit evidence

Ethereum Mainnet purchase transaction:

`0xab75877dae845838dc2a2c7904af37076dfc0408af31a23e84e601ffa4d5083b`

Confirmed on-chain:

- participating wallet: `0x3Df4eBE3e5Bd012F459cD3392c90a2d8b576Ea7C`
- sale contract: `0x1324d9CA99b5AFfF6e8ceb4083EF744b3B6f4161`
- transaction method: `invest(uint256,bytes)`
- deposited amount: **1,000 USDC**
- transaction status: success
- transaction timestamp: 2026-09-29 13:48:23 UTC

Sale contract is an EIP-1167 proxy to verified implementation:

`0x11077edDFc6dB5abFDB9E019A64172B5d8E81A3a` (`LegionPreLiquidSaleV2`)

Latest on-chain investor state read:

- `investedCapital = 1,000 USDC`
- `hasSettled = false`
- `hasClaimedExcess = false`
- `hasRefunded = false`
- `vestingAddress = 0x0000000000000000000000000000000000000000`

Therefore the 1,000 USDC has **not** yet been refunded on-chain. Do not count it as liquid capital until the refund transfer is confirmed.

## Refund timing

Confirmed on-chain sale configuration:

- sale end: **2026-10-06 23:54:59 Asia/Bangkok**
- refund window end: **2026-10-20 23:54:59 Asia/Bangkok**

The E999 failure was observed only minutes after the sale's on-chain end timestamp. A frontend/backend synchronization delay is plausible but not confirmed.

## Refund mechanism

Verified Legion contract source exposes `refund()` with no arguments. During an open refund window it returns the caller's full recorded `investedCapital`, subject to the contract's runtime guards (including not already refunded, sale state and pause state).

For this rejected application, the direct full-refund method is `refund()`; `withdrawExcessInvestedCapital(amount, proof)` is the separate partial-allocation excess-capital path and requires a Merkle proof.

Do not manually call a contract method blindly. Prefer the official Legion Reclaim flow; if direct interaction becomes necessary, first re-read/simulate current contract state and verify the exact sale address before signing.

## Recovery status / next action

1. Retry the official Legion **Reclaim USDC** flow using the same participating wallet on Ethereum Mainnet after the post-sale backend has synchronized.
2. If E999 persists, refresh/reconnect and determine whether the app ever produces a wallet transaction request.
3. If no transaction is produced, contact official Legion Support with the screenshot, E999, purchase transaction hash, wallet and sale contract.
4. If official UI/support remains blocked, use the verified `refund()` path only after a fresh simulation/read confirms it is callable.
5. After any refund attempt, require on-chain confirmation of the USDC transfer back and update this file to `RECLAIM_STATUS = COMPLETE`.

## Accounting rule

Until refund confirmation:

`1,000 USDC = LEGION_SALE_CONTRACT / RECLAIM_PENDING`

After confirmed refund:

`1,000 USDC = LIQUID USDC` at the returned chain/wallet location.

No JUMP position exists from this application.