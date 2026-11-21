# Forecast Founding 100 USDC 存款收款合约、资金控制权和提现可行性核查（2026-11-21）

Status: **REFUND_CONFIRMED_ONCHAIN / PRINCIPAL_RETURNED_100_USDC / CLOSED**
Last checked: 2026-11-21 10:51+07:00 (Asia/Bangkok), live Base RPC read-only verification
Production: NO_GO; read-only analysis, no signing or transaction submission.
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `MISSION_SPEC.md`.
Privacy: user's original wallet and transaction hash are deliberately truncated in this public-facing repository record. Keep exact private linking material in user-held Founding receipt and own wallet history.

## Latest outcome (2026-11-21): FULL 100 USDC PRINCIPAL REFUND CONFIRMED

**FINAL STATE: CLOSED / REFUNDED / NO ACTION REQUIRED.**

- The participant reported receipt and the official Base network was checked independently using Alchemy `getAssetTransfers` in both directions, filtered by the **canonical Base native USDC** contract and by the original Founding Safe/recipient pair.
- Confirmed transaction `0xff0dee7e…0ad6a` from `0xf605…2378` (same 4/5 Safe that received the original deposit) to `0x3df4…ea7c` (same founding depositor).
- Exact ERC-20 transfer amount **100.000000 USDC**; onchain UTC timestamp **2026-11-20 22:51:59Z**, Bangkok local timestamp **2026-11-21 05:51:59+07:00**; Base block `0x3956a49`; transaction receipt reports success `status=0x1`.
- Historical original deposit **100.000000 USDC** on 2026-05-29, so the onchain return matched the original principal **100%**. No extra Founding proceeds/reward is claimed.
- Transaction was executed by the **existing Safe custodian**, consistent with earlier finding that ordinary depositors could not self-withdraw from its v1.3.0 4/5 multisig.
- At verification time, the original recipient wallet's **current** USDC `balanceOf` was `0`. This does **not** contradict receipt: ERC-20 incoming transfer history proves the 100 USDC reached the wallet; current spendable balance may subsequently have changed. No assumptions about subsequent wallet use are recorded here.
- Note that the September Founding receipt's old `returnedMicroUsdc=0` field is a **historical** pre-refund snapshot, not a present-day outstanding principal figure. Do not cite it as current truth.
- Prior snapshots and `REFUND_NOT_OBSERVED` wording below refer solely to the earlier audit moment; **superseded** for the refund status by this verified later event. No need to re-request refund, further deposit, trading or signature.
- Independent original data sources: Alchemy read-only Base RPC (`getAssetTransfers` both `toAddress=recipient` and `fromAddress=Safe,toAddress=recipient`) and transaction receipt. No transactions were initiated.

## Deposit proof and matching

- Base mainnet chainId 8453, native USDC contract `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`.
- User's Founding wallet masked: `0x3df4…ea7c`.
- Alchemy onchain asset transfer and `eth_getTransactionByHash` + receipt prove 100.000000 USDC successfully transferred at **2026-05-29 10:18:17 UTC**, tx `0x9b061608…a73eb`.
- Receiving address: **`0xf605767bb0636fe082b20b2999a6957e3c772378`**.
- Transaction is a direct call to the official USDC `transfer(address,uint256)`, selector `0xa9059cbb`, amount `100000000` base units, status `0x1`.
- User-held `forecast-founding-*.json` artifact `founding-1` status `finalized` observed 2026-09-19, `acceptedMicroUsdc=100000000`, `returnedMicroUsdc=0`, freeze 2026-09-13T17:04:12Z, `contributionMicroUsdcSeconds=926915500000000`.
- Calculation: `926915500000000 / 100000000 = 9269155` seconds; subtract from freeze time = **2026-05-29 10:18:17Z**, EXACTLY matches the USDC transfer timestamp. This is an exceptionally strong record-to-chain correlation.
- The new Forecast account page showed `Founding Accepted $100` / `Founding member Gold III`, but separate trading account `Total assets / Available = $0.00` on 2026-11-21. The trading `Withdraw` does not demonstrate Founding principal liquidity.

## Receiver contract source and live state

- `eth_getCode(0xf605…2378)` confirms a deployed proxy with `masterCopy()` selector `0xa619486e`.
- `eth_getStorageAt(slot=0)` and `eth_call(masterCopy())` both return **`0xfb1bffc9d739b8d520daf37df666da4c687191ea`**.
- This is the canonical **Gnosis SafeL2 v1.3.0** singleton. BaseScan verified ABI: https://basescan.org/address/0xfb1bffc9d739b8d520daf37df666da4c687191ea#code ; Safe source https://github.com/safe-global/safe-smart-account/blob/v1.3.0/contracts/GnosisSafe.sol ; docs https://docs.safe.global/reference-smart-account/transactions/execTransaction .
- `eth_call(VERSION())` = `1.3.0`.
- `eth_call(getOwners())` = 5 owners. `eth_call(getThreshold())` = **4** signatures required. Owner list exists in RPC but no need to replicate potentially identifiable third-party wallets in this report.
- `eth_call(isOwner(user))` = **false**.
- `eth_call(getModulesPaginated(sentinel,10))` = empty modules list, next = sentinel. No onchain module that could let external user withdraw is currently enabled.
- `eth_call` from the Founding wallet simulating a Safe `execTransaction` without valid owner signatures reverted **GS020** (signature bytes too short for threshold). No transaction was broadcast.
- `eth_call(USDC.balanceOf(Safe))` at time of check = **865,573.162890 USDC**.
- The Safe had historical successful outgoing USDC transfers to third-party addresses; last observed 2026-11-20 transfer `5,256.678730` USDC, another 2026-11-16 `70,000` USDC, etc. These are real wallet transfers, but recipient identity and economic use have NOT been established. Do not infer misappropriation or solvency from this alone.
- Alchemy `getAssetTransfers` with filters `fromAddress=Safe`, `toAddress=user`, `contractAddresses=[USDC]` returned **zero direct USDC refunds at the initial check**. This is historical only: the subsequent 100 USDC Safe-to-user refund on 2026-11-20 22:51:59Z is now independently confirmed above.

## Technical conclusion (historical access assessment before the later refund)

**This is a custodial Safe holding pooled USDC, not a user-withdrawable permissionless vault.** The customer's Founding receipt is a campaign/accounting record rather than a transferable onchain vault share, based on observed evidence. No verified Forecast-specific public core contract repository or direct self-service Founding refund function was found in this pass. This is narrower than claiming the project will never offer a refund interface in the future.

One user's wallet cannot force a withdrawal from this Safe; a valid standard Safe transfer requires signatures meeting the 4-of-5 threshold (or another future authorized action). The treasury has sufficient observed USDC to make a 100 USDC payment, but that does **not** establish an individual legally enforceable redemption right or operational readiness.

### Refund transaction SPEC for the controlling Safe signers (NOT submitted)

- Safe account: `0xf605767bb0636fe082b20b2999a6957e3c772378`
- Target contract: Base native USDC `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`
- Function: `transfer(address recipient,uint256 amount)`, `amount=100000000` base units (100 USDC), `ETH value=0`, `operation=CALL`.
- Recipient: user's original Founding wallet `0x3df4…ea7c` (exact value can be recovered from their own wallet and receipt, not duplicated here).
- Four of five Safe owner approvals required, following the multisig's existing guard/policy and sufficient remaining balance.
- No user approval, private key disclosure, additional top-up, protocol trading, or new deposit is technically required to process the Safe return. No authorization was provided to execute or simulate state changes outside read-only `eth_call`.

## Final classification

- Deposit: CONFIRMED ON CHAIN; corresponding principal repayment ALSO CONFIRMED ON CHAIN.
- Custody: CONFIRMED SAFE 4/5.
- Contract's user-controlled refund function: NO STANDARD SAFE PATH; NO MODULE ENABLED.
- Founding reimbursement by issuer: **CONFIRMED 100 USDC returned by the original multisig to the original depositor on Base at 2026-11-20T22:51:59Z**.
- Original trading-account withdraw button returning the Founding principal: NOT USED; original Safe made a direct 100 USDC repayment.
- Refund status: **CLOSED / PRINCIPAL REFUNDED IN FULL**. Historical optional Founding rewards or other entitlements were not investigated as part of this refund close-out.

No sensitive keys, credentials, monitor changes, onchain writes, production deployment, or wallet operations were undertaken.
