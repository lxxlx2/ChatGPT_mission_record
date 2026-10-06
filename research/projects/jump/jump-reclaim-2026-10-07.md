# JUMP / Jumper Legion — allocation rejected + 1,000 USDC reclaim incident

Updated: 2026-10-07 00:12 Asia/Bangkok

## Current state

- `APPLICATION_STATUS = UNSUCCESSFUL / REJECTED`
- `ACCEPTED_INVESTMENT = 0 USDC` (user-confirmed Legion UI: no allocation was granted)
- `JUMP_ALLOCATION = 0`
- `DEPOSITED_CAPITAL = 1,000 USDC`
- `LEGION_UI_AMOUNT_TO_CLAIM = 1,000 USDC`
- `AGREEMENT_SIGNATURE = VOIDED`
- `RECLAIM_STATUS = NOT_COMPLETED`
- Current UI error after pressing **Reclaim USDC**: `[E999] Something went wrong. Please try again, or contact support if the issue persists.`
- Do **not** treat the 1,000 USDC as liquid / returned until an on-chain refund transaction and USDC transfer back to the participating wallet are confirmed.

## User evidence

Authenticated Legion sale UI screenshot supplied by the user on 2026-10-07 Asia/Bangkok shows:

- Application unsuccessful.
- Amount to claim: 1,000 USDC.
- Agreement Signature: VOIDED.
- Purchase network: Ethereum Mainnet.
- Investment Asset: USDC.
- Reclaim USDC button visible.
- E999 error appears when attempting reclaim.

## On-chain evidence — CONFIRMED

Purchase transaction:

`0xab75877dae845838dc2a2c7904af37076dfc0408af31a23e84e601ffa4d5083b`

Ethereum Mainnet transaction data:

- status: success
- timestamp: 2026-09-29 13:48:23 UTC
- participating wallet: `0x3Df4eBE3e5Bd012F459cD3392c90a2d8b576Ea7C`
- sale contract: `0x1324d9CA99b5AFfF6e8ceb4083EF744b3B6f4161`
- call: `invest(uint256,bytes)`
- invested amount: `1,000,000,000` USDC base units = **1,000 USDC**
- USDC contract: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`
- the 1,000 USDC transfer from the participating wallet to the sale contract is confirmed on-chain.

The sale address is a verified EIP-1167 proxy whose implementation is:

`0x11077edDFc6dB5abFDB9E019A64172B5d8E81A3a` (`LegionPreLiquidSaleV2`)

Latest on-chain `investorPositionDetails()` read for the participating wallet returned:

- `investedCapital = 1,000,000,000` = **1,000 USDC**
- `hasSettled = false`
- `hasClaimedExcess = false`
- `hasRefunded = false`
- `vestingAddress = 0x0000000000000000000000000000000000000000`

Therefore, at the time of the read, the original 1,000 USDC position is still recorded in the sale contract and no refund has been completed.

## Refund window — CONFIRMED ON-CHAIN

`saleConfiguration()` returned:

- startTime: `1790684831` = 2026-09-29 19:27:11 Asia/Bangkok
- endTime: `1791305699` = **2026-10-06 23:54:59 Asia/Bangkok**
- refundEndTime: `1792515299` = **2026-10-20 23:54:59 Asia/Bangkok**
- lockupEndTime: `1792515299`

The reclaim failure was observed only minutes after the on-chain sale end time, so a Legion frontend/backend synchronization delay is a plausible explanation for E999. This is an inference, not a confirmed Legion incident diagnosis.

## Verified contract refund path

Verified Legion source code exposes `refund()` with no arguments.

The public `refund()` function:

1. requires the refund period to still be open;
2. requires the sale not to be canceled;
3. requires the caller not to have already refunded;
4. reads `investorPositions[msg.sender].investedCapital`;
5. rejects zero refund amount;
6. sets the investor's invested capital to zero and `hasRefunded=true`;
7. transfers the full recorded bid-token amount back to `msg.sender`.

For this position, `investedCapital` is currently 1,000 USDC and `hasRefunded=false`.

Important distinction:

- `refund()` is the full-refund path during the refund window and does **not** require a Merkle proof.
- `withdrawExcessInvestedCapital(amount, proof)` is the excess-capital path for partial allocations and requires an accepted-capital Merkle proof. Do not use it blindly for this rejected application.

Before any manual direct-contract refund, re-check live contract state (`paused`, sale cancel state, position state) and simulate the call. Prefer the official Legion reclaim UI first.

## Official Legion workflow

Legion Help Center states:

- if an application is not accepted, the participant reclaims the full deposit;
- reclaim is performed from the sale page using the Reclaim button;
- refund/reclaim rights are available during the 14-day post-sale refund window;
- if the UI has errors or fails to update, verify the position on-chain and contact Legion Support if the issue persists.

Official references:

- https://help.legion.cc/en/articles/10335791-how-do-sales-work-on-legion
- https://help.legion.cc/en/articles/13222684-how-can-i-find-and-use-the-reclaim-button-in-the-legion-app
- https://help.legion.cc/en/articles/17139928-jumper-jump-public-sale-on-legion-everything-you-need-to-know

## Recovery plan

Priority order:

1. Retry the official Legion **Reclaim USDC** action after the post-sale backend has had time to synchronize; use the same participating wallet on Ethereum Mainnet.
2. If E999 persists, hard-refresh/reconnect the wallet and capture whether clicking Reclaim ever opens a wallet transaction request.
3. If the app still fails before a wallet transaction is produced, open Legion Support and provide the screenshot, E999, purchase transaction hash, participating wallet and sale contract. Never provide seed phrase/private key.
4. If official UI/support remains blocked, the verified contract has a direct `refund()` path. Only use direct contract interaction after a fresh read/simulation confirms it is still callable from the participating wallet. Verify the destination contract exactly before signing.
5. After refund, confirm both `CapitalRefunded` and the 1,000 USDC transfer back on-chain. Only then mark `RECLAIM_STATUS = COMPLETE` and restore the 1,000 USDC to liquid-capital accounting.

## Current operational conclusion

`JUMP_PUBLIC_SALE_POSITION = REJECTED / ZERO_ALLOCATION`

`1,000 USDC = RECLAIMABLE_SHOWN_BY_LEGION / ONCHAIN_NOT_YET_REFUNDED`

No JUMP token position should be carried forward from this sale.