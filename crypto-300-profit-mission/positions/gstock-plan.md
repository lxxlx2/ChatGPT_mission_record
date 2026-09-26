# GSTOCK BNB Chain Plan

Updated: 2026-09-26 14:12 Asia/Bangkok
Status: PLAN_NOT_FILLED

Canonical token:
- name: Gstock
- symbol: GSTOCK
- contract: `0xcAFdBCE93477261Db8250e42BdAe6E66733F9E20`
- network: BNB Chain

## Direct-chain state

Fresh Alchemy read:
- GSTOCK wallet balance: **0**
- BNB Chain USDC: **30.00474761**
- native BNB: **0.002684170274192202**
- current Alchemy GSTOCK reference price: **~0.024487 USD**

Therefore there is no direct-chain evidence of a GSTOCK fill at this snapshot.

The user confirms the BNB Chain funds are reserved for a GSTOCK pending-order plan. Wallet RPC cannot prove whether an off-chain / conditional order UI is currently active, so order state is USER_CONFIRMED / UNVERIFIED_BY_CHAIN until a fill or newer UI confirmation appears.

## Existing plan reference

Latest previously discussed ladder:
- 6 USD around 0.0250
- 10 USD around 0.0220
- 14 USD around 0.0185
- prior hard invalidation reference: 0.0158

These are stored plan references only. The automation must not create, replace, resize or submit any GSTOCK order.

## Monitoring

Factual monitor checks:
- canonical GSTOCK wallet balance
- BNB Chain USDC / BNB gas
- whether a direct-chain fill appears
- material security / liquidity / identity changes

No fill = PLAN_NOT_FILLED.
