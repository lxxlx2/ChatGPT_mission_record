# GANG / The Syndicate — Backable ICO operational position

Updated: 2026-10-08 Asia/Bangkok
Network: Solana mainnet
Source standard: direct finalized Solana state + actual MetaDAO v0.7 contract + user participation statement.
State: `COMMITTED_ONCHAIN / SALE_LIVE / ALLOCATION_PENDING`
Trading execution: `NO_GO` (record-only; no standing automation or monitor authorized).

## Canonical identity and contracts

- Project: The Syndicate
- Token: GANG
- Backable raise: https://backable.biz/raises/EFUKEM6oaUMdCtVvgaqeV2E9baZ1ikkLng1kTakvjU7k
- Raise account: `EFUKEM6oaUMdCtVvgaqeV2E9baZ1ikkLng1kTakvjU7k`
- **Canonical SPL mint (already created):** `syQqkspvb2PRr1meJ5pJDmhgxwc4hUou2TMjjrTmeta`
- Mint explorer: https://solscan.io/token/syQqkspvb2PRr1meJ5pJDmhgxwc4hUou2TMjjrTmeta
- On-chain owner/program: `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM` = MetaDAO Launchpad **v0.7** (not v0.8).
- Relevant source: https://github.com/metaDAOproject/programs/tree/develop/programs/v07_launchpad
- Token is **already minted into launch vault**; this is **NOT** a presently claimable liquid wallet token holding.
- Mint snapshot on 2026-10-08: 27,157,894 GANG (6 decimals), freeze authority null; mint authority `3bFdH9eitNJJnC2ocraqAFbnhC6GALNGowfY4otrXwi2` (launch signer pre-completion). Do not assume authority is permanently renounced.

## User-specific position — VERIFIED

- User's canonical Solana wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Individual FundingRecord PDA: `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot`.
- Deposit transaction (success, `Instruction: Fund`): `LLxbLZNJYKcWGchRt7QNwnx8UKs4gzu5rYC2CFbRWzm9FzjrCjFHaMbKeebKHZAc8gkcympJTqioHGp2f7ifYia`
- Solscan: https://solscan.io/tx/LLxbLZNJYKcWGchRt7QNwnx8UKs4gzu5rYC2CFbRWzm9FzjrCjFHaMbKeebKHZAc8gkcympJTqioHGp2f7ifYia
- Time: 2026-10-08 05:57:48 UTC = **2026-10-08 12:57:48 Bangkok**.
- USDC before: **531.094071**; after: **31.094071**.
- **Committed: 500 USDC**, transferred into sale escrow vault.
- FundingRecord direct chain state read 2026-10-08:
  - `committed_amount = 500 USDC`
  - `approved_amount = 0 USDC` (NOT YET FINAL; cannot infer rejection from this while launch Live)
  - `is_tokens_claimed = false`
  - `is_usdc_refunded = false`
- `GANG_ALLOCATED = UNKNOWN / PENDING_SETTLEMENT`
- `GANG_WALLET_BALANCE_FROM_ICO = 0 PENDING CLAIM` (no allocation should be counted as liquid or sold before claim).
- Current economically encumbered principal: **500 USDC** (not liquid wallet USDC).

## Sale schedule and on-chain launch parameters

Directly decoded from the v0.7 launch account:
- `started_at = 2026-10-07T17:30:01Z`
- `seconds_for_launch = 345600` (4 days).
- **Scheduled close: 2026-10-11T17:30:01Z = 2026-10-12 00:30:01 Asia/Bangkok.**
- `minimum_raise_amount = 250000 USDC`.
- 2026-10-08 finalized snapshot after user's deposit: `state = Live`, `total_committed_amount = 426936.09 USDC`, `total_approved_amount = 0` (not settled).
- Advertised up-to-$1M cap is an apparent project/platform allocation policy; a hard on-chain max-cap field was **not found** in v0.7 Launch state. Do not treat it as bytecode-enforced.
- Allocation: 10,000,000 GANG participants; 2,900,000 GANG liquidity; 12,900,000 GANG price-based team performance package; 1,357,894 GANG additional designated recipient.
- `months_until_insiders_can_unlock = 18` (team performance package, **not** ICO purchaser lock).
- GANG v0.7 investor `claim()` is a transfer from launch token vault to funder ATA once `LaunchState::Complete`; no additional buyer vesting constraint in the method.
- Additional recipient `53WKsoHAm2ztNF9xh68NC5dw8LWCroMsRt47x8JNvHTV` can claim 1,357,894 extra tokens after `Complete`, distinct from the team's 18-month performance lock.

## Post-close operational checklist — STATUS PENDING

1. **At or after 2026-10-12 00:30:01 Bangkok:** verify `LaunchState` moved from `Live` to `Closed` or `Refunding`. Time is a scheduled end, **not** a guarantee claim is live at that instant.
2. If `Closed`: inspect `FundingRecord.approved_amount`, `total_approved_amount`, and whether close/approval/complete transactions are finalized. v0.7 allows launch authority to record allocation approvals within two days after close.
3. If `Complete`: verify executable `claim()` for actual allocated GANG and independently available `refund()` amount = `committed_amount - approved_amount`.
4. If `Refunding`: verify `refund()` for full contributed 500 USDC.
5. The user must explicitly submit claim/refund using the original funding wallet. **No auto distribution, no guaranteed post-close clock time, no claim/refund deadline specified in provided terms.**
6. After actual confirmed receipts, record token balance, refund amount, final approved cost, first liquid-market availability, and transaction signatures; then update portfolio without double counting.
7. Do **not** execute claim/refund or create alerts/automations without separate explicit user authorization. This is a stored checklist, not an active monitor.

## Accounting treatment

- Transfer `500 USDC` from **liquid Solana USDC** to **pre-settlement restricted sale contribution at historical cost**, not a second $500 asset on top of prior USDC.
- As of deposit tx: wallet USDC = **31.094071**, escrowed sale commitment = **500 USDC**.
- Until approved and claimable: **GANG token quantity unspecified; liquid token NAV 0 from this sale; cost basis for future allocation not yet determined**.
- Distinguish USD historical deposited principal from its eventual recoverable amount and token's actual marked value.
- This position is **outside** any new task/automation creation. Manual updates only.

## Proof and source

- The funding transaction and FundingRecord contents are direct Solana finalized RPC observations.
- v0.7 claim code: https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/claim.rs
- v0.7 refund code: https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/refund.rs
- v0.7 approval: https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/set_funding_record_approval.rs
- Real claim/refund times must be evidenced with this raise's future state/transactions, not extrapolated from other raises.
