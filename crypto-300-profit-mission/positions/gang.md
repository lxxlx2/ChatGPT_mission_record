# GANG / The Syndicate — Backable ICO operational position

Updated: 2026-10-12 Asia/Bangkok (Complete and automatic claim/refund finalized; live GANG pools)
Network: Solana mainnet
Source standard: direct finalized Solana state + actual MetaDAO v0.7 contract + user participation statement.
State: `COMPLETE_ONCHAIN / RECEIVED_8008_208_GANG / REFUNDED_19_507520_USDC / LIVE_POOL`
Trading execution: `NO_GO` (research/read-only only; no standing automation or monitor authorized).

## 2026-10-12 finalized COMPLETE / automatic distribution / live pool evidence

Observed ~01:31-01:41 Asia/Bangkok on Solana mainnet **finalized** (independent account reads; changing AMM reserves are timestamped point-in-time observations).

### Actual settlement

- Launch PDA `EFUKEM6oaUMdCtVvgaqeV2E9baZ1ikkLng1kTakvjU7k`: **`state=Complete`**, approved total **600,000 USDC**, pledged total **631,770.75 USDC**. The planned 01:30 distribution has **actually executed**.
- User's FundingRecord `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot`: `committed=500 USDC`; `approved=480.492480 USDC`; `is_tokens_claimed=true`; `is_usdc_refunded=true` (read around finalized slot 455751011).
- User's Solana wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp` genuinely holds **8,008.208 GANG**, Token Account `5XBM2iEibBNAVBMjPYb9Deh8ibm4CCqZrbqk8n7TpGJo` (finalized slot 455750937, rechecked 455753009). Quantity = approved 480.49248 / 600000 × 10m. Actual cost basis **480.492480 USDC**, **$0.06 per GANG**; unused sale deposit **19.507520 USDC** refunded per contract `is_usdc_refunded=true`; user USDC account `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A` read as **85.102445 USDC** at slot ~455752xxx/455753009. Do not attribute *all* increase from October 10's 58.047629 to sale refund: unclassified external movements may exist.
- Personal claim/refund affected transaction in FundingRecord history: https://solscan.io/tx/u5TANZxqCbct3SNHd13F5wuabhLYein8ov4FSke6rFUKAEWcDZCLP2sTXkSstoX6vWu3F933Xn4r4qKLtcRNzAE (finalized 2026-10-11T18:30:18Z). Finalized decoded flags and wallet transfer provide primary evidence regardless of transaction detail API truncation.
- Mint supply **27,157,894 GANG**. `mintAuthority` changed from launch signer to DAO controller `59Km6UTvKMNmww5iwiVQ7iTKUy6Eoug1ytsMPhd36e8z`; freeze authority remains null. This authority is **not renounced**, so do not claim supply immutable.

### Live onchain pools: separate direct observations and simulations

- **Futarchy AMM live spot pool** account `7YktVLcciZ12HnsM2VektRZuxaPE9VRSyYhGBid47b2A` owned by `FUTARELBfJfQ8RDGhg1wdhddq1odMAJUePHFuBYfUxKq`, token vaults: GANG `6D61o3o82qCjFrLo5J9MVCU6iKuDP1ApjV8jDHPwwKqT`; USDC `HEedE6VTuuNAnQkuk2t8V9cHuYfuDvJ9vbUKrSomok1i`. Finalized snapshot slot 455753008: **2,099,533.808242 GANG** and **114,463.155810 USDC**. Mid reserve-ratio price (indicative, not router quote) **~0.05451837 USDC/GANG**, implies FDV **~$1,480,604.05**, and notional two-sided reserve TVL ~$228,926.31 if this spot ratio applied to GANG; both sides amount known. At this exact snapshot, *simplified* constant-product exact-input zero-fee full sale of 8008.208 GANG would yield ~434.94 USDC from this pool alone, plus 19.50752 refund => ~$454.44 total, ~-$45.56 vs 500; excludes real AMM, DEX/router, priority/gas fees and alternative pools. **Never claim this is an executable quote**.
- **Meteora DAMM v2** confirmed running; GANG token vault `7fugxJgmtgA3gL6DEWSuZmNK7qxGKEqvXJXg97XzSY55` owned by the program's canonical pool authority `HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC` (onchain). GANG vault around **900k tokens**, and `getSignaturesForAddress` returns successful fresh swaps, e.g. https://solscan.io/tx/2VCCjcPmKZifX5ZrXABQ7dJ5Gku58jB4y2ZFV5PUNjG71N1KXgQ3Zi1TdZ7hQNpXAYwos4o1DdygQ2tLJNmxccc6 . Canonical program `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG`. Program pool listing queries triggered Alchemy RPC 429 compute budget limit; matching USDC vault / full pool pubkey / current tick price / exact curve exit quote **UNVERIFIED**. Do not impute USDC reserves from the GANG side.
- Backable/Meteora complete code: https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/complete_launch.rs ; protocol docs https://github.com/MeteoraAg/docs/blob/main/developer-guides/damm-v2/index.mdx . No automatic production trade, monitor, or sell simulation executed on a live transaction.

### Holder concentration and economics

- Largest GANG token account `4MgMwGb82egP7g5KoRwL6TSABjab9Bdm96SdCK1B5mFn` contains **12,900,000 GANG (47.5% supply)**; owner `7zvz5fPSYvk8nDhkM4osTZJpM71tqw7biVMMgjV6LAmN` is owned by price-based performance package program `pbPPQH7jyKoSLu8QYs3rSY3YkDRXEBojKbTgnUg7NDS`. Protocol launch records **18-month insider lock parameter**, but do not infer this entire package is released on a fixed calendar or freely salable.
- Futarchy AMM GANG ~2.10m (~7.73% of total), DAMM v2 GANG ~0.90m (~3.3%), both **contract-controlled trading liquidity**, not one retail whale.
- Old launch signer GANG Token Account `8TCjFJznaFcQhJmWCk9P1NXU5QAGKNLRh95oWRb3dLR9` retained about **1,357,902 GANG** at an earlier finalized snapshot, approximately the additional designated allocation; owner/withdrawable distribution needs further checking. Other top accounts include about 1,000,000; 974,302; 833,333; 833,333 GANG, but these are **unattributed wallet or pool accounts**, cannot label insiders or dumpers solely from balances.
- Under full-supply **FDV** convention, **break-even price=$0.06, break-even FDV=$1,629,473.64** before fees. If excluding only the 12.9m performance-package mint (14,257,894 residual) the *simplified circulating value at cost price* is $855,473.64, but real tradable float may differ and is **not independently audited**.
- PnL accounting after claim: original 500 USDC = **480.492480 USDC GANG cost + 19.507520 USDC refund**. No further escrow remains; **do not double-count old 500 USDC historical escrow**. The GANG is now an actual transferable wallet holding with non-guaranteed current resale value. Do not turn unrealized PnL into realized PnL.

### Historical sections below

Earlier `SALE_LIVE / Closed / payout_pending`, `wallet_GANG=0` and escrow statements are dated snapshots **SUPERSEDED** by this section. Preserve those observations for audit, but always take this latest finalized `Complete` read as current. There is no guaranteed standing alert; manual update performed because real state materially changed.


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

## 2026-10-12 post-window finalized on-chain milestone (SUPERSEDES pre-close operational snapshot)

Research type: `DIRECT_CHAIN / SOLANA_FINALIZED`. Observation slot ~455735427 to 455735691 on October 12 Bangkok, after scheduled 00:30:01 close. Independent finalized confirmation transaction: https://solscan.io/tx/3gPviEWwUaSvtWd2mKRFat1ar7aHBBW7LPAUTiujjwqdfrCGg4LNG5ooWVFRqAikhH7zVg7nrc4aGpStjN7wX1E9 . Program logs contain `Instruction: CloseLaunch` and finalized success; blockTime 2026-10-11T17:30:17Z = 2026-10-12 00:30:17 Bangkok.

**Launch PDA `EFUKEM6oaUMdCtVvgaqeV2E9baZ1ikkLng1kTakvjU7k`, decoded using MetaDAO v0.7 Launch state source:**
- `state=Closed`, `unix_timestamp_closed=2026-10-11T17:30:17Z`.
- `total_committed_amount=631770.75 USDC` (**commitments escrowed, not actually approved/raised/company treasury**).
- `minimum_raise_amount=250000 USDC`, `total_approved_amount=0 USDC` at observation. Minimum commitments exceeded; funding outcome **not yet finalized**.
- `monthly_spending_limit=41666 USDC`, `months_until_insiders_can_unlock=18`.
- Official Backable deal page displays up-to-1M maximum for final approved raise, but `minRaise` is only fixed field in Launch; do not claim a signed on-chain hard-cap implementation.
- Backable primary docs: https://www.backable.biz/docs/committed-vs-raised / https://www.backable.biz/docs/whats-new . Early-fill boost, time weighting, Ownership Score and reserved Aligned Parties addresses can affect **individual approval**. Never estimate actual approved amount from headline total.

**User FundingRecord `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot`:**
- `committed_amount=500 USDC`
- `approved_amount=0 USDC` pending approval
- `is_tokens_claimed=false`
- `is_usdc_refunded=false`
- Claimable GANG amount **UNCONFIRMED / no tokens distributed**. Do not treat zero approval before finalization as final rejection.

**Mint & pool facts:**
- Mint `syQqkspvb2PRr1meJ5pJDmhgxwc4hUou2TMjjrTmeta`, total supply `27157894 GANG`, 6 decimals, `freezeAuthority=null`, `mintAuthority=3bFdH9eitNJJnC2ocraqAFbnhC6GALNGowfY4otrXwi2` (launch signer, not renounced).
- `getTokenLargestAccounts` shows **all 27,157,894 GANG** at `8TCjFJznaFcQhJmWCk9P1NXU5QAGKNLRh95oWRb3dLR9`; `getAccountInfo(jsonParsed)` confirms token-account owner `3bFdH9eitNJJnC2ocraqAFbnhC6GALNGowfY4otrXwi2` = launch signer. No transfer of supply into initial USDC/GANG pool or investor ATA at the snapshot. Wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp` has no GANG token account.
- `LaunchState::Complete` not reached: contract-required Meteora DAMM v2 + Futarchy AMM initialization not completed. **No verified pool address, LP USDC reserves, executable market price, volume or slippage**; do not use token aggregator 'buy' button as proof.
- CompleteLaunch source: https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/complete_launch.rs
- CloseLaunch source: https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/close_launch.rs
- `set_funding_record_approval.rs` permits launch authority to approve within 2 days *after actual CloseLaunch*. `claim.rs` requires Complete; `refund.rs` requires Complete or Refunding. A scheduled close is NOT equivalent to claim enabled.
- Project official X `https://x.com/SyndicateGameHQ`, platform official X `https://x.com/backabledotbiz`. Web direct reads of X returned 403, and no independently retrievable **post-close official announcement** establishing claim/TGE/trading time was found. `OFFICIAL_POST_CLOSE_ANNOUNCEMENT=UNVERIFIED`; do not invent a launch time or imply no statement exists anywhere.

**Scenario math ONLY (not allocation):** if approved total were 631770.75 USDC *and* user approved=500 USDC, expected `500/631770.75*10000000 ≈ 7914.26 GANG`, indicative sale price $0.063177; this is not proven. If approved total 1M and user approved 500, 5000 GANG; if user approved less, excess USDC refund required. Keep prior 7948 as historical pre-close scenario only.

**Next status gate:** finalized `Closed -> Complete` or `Closed -> Refunding`; personal `approved_amount` nonzero or final; actual `total_approved_amount`, LP/DAO accounts, liquidity depth, and confirmed claim/refund. Manual recheck on user request or meaningful authoritative event only. No monitor, signing, trade, claim or refund created or executed.


## 2026-10-12 official proposed settlement and chain-verified approvals

Evidence time: **2026-10-12 ~01:25-01:27 Asia/Bangkok**, finalized Solana slot **455749368** (newer than last `Closed` milestone). User screenshot of X `@backabledotbiz` (Backable account; **issuer/platform statement presented by user, original tweet URL not independently fetched**) says:
- "The Syndicate team has decided to accept $600,000."
- "The starting token price will be $0.06, corresponding to an FDV of $1,629,473."
- "Tokens and refunds will be processed on your behalf at 18:30 UTC." This corresponds to **2026-10-12 01:30 Asia/Bangkok** if posted on October 11 UTC; **announced planned action, not proof of completed transaction or exact execution deadline**.
- Final pledged/committed raised shown **$631,771** rounded; chain directly says **631,770.75 USDC**.

**Independently verified finalized on-chain, critical update:**
- Launch PDA `EFUKEM6oaUMdCtVvgaqeV2E9baZ1ikkLng1kTakvjU7k`: `LaunchState=Closed`, `total_committed_amount=631770.75 USDC`, **`total_approved_amount=600000 USDC`**, `seq_num=444`, `unix_timestamp_completed=None` in finalized slot ~455749368; 600k statement is **ONCHAIN_CONFIRMED**.
- User FundingRecord PDA `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot`: `committed_amount=500 USDC`, **`approved_amount=480.492480 USDC`**, `is_tokens_claimed=false`, `is_usdc_refunded=false`. This has actual chain evidence (not an allocation extrapolation). Approval transaction tied to user's FundingRecord: https://solscan.io/tx/35e3kcJKcNNnM38MMk9RLZ9fJ7ZMi2BaMb5H1Ycp7mBMtCnqjijCXKVHvoWJRAJPnobFgJKws6eHmDQrhUsZHaNi (2026-10-11T18:01:19Z). Some RPC transaction-detail responses truncated; FundingRecord current finalized bytes independently confirm the approved amount.
- **Conditional claimable token amount at `Complete`** under v0.7 claim.rs: `480.492480 / 600000 * 10000000 = 8008.208 GANG`, subject to any in-window authority amendments before Complete. This is now an **onchain-derived approval-based quote**, still **not received in wallet**.
- **Refund due once Complete**: `500 - 480.492480 = 19.507520 USDC`. Refund is **NOT YET PAID** according to live flags. Under `Refunding`, different logic would apply.
- Price math `600000/10000000=$0.06 GANG`. Using 27,157,894 total issuance, `FDV=1,629,473.64 USD` (post rounds to $1,629,473).
- `getTokenLargestAccounts` on official GANG mint `syQqkspvb2PRr1meJ5pJDmhgxwc4hUou2TMjjrTmeta` finalized slot ~455749292: **all 27,157,894 GANG still at launch vault** `8TCjFJznaFcQhJmWCk9P1NXU5QAGKNLRh95oWRb3dLR9`, wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp` has no GANG token account. **No token distribution, official seeded LP pool, actual market opening, tradeable price or executed refund verified at snapshot.**
- v0.7 source: https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/claim.rs ; https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/refund.rs ; https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/complete_launch.rs .
- The October 12 screenshot provides **OFFICIAL_STATEMENT** of intended 01:30 automated distribution. Even if processing is on behalf of participants, do not equate planned processing with success until finalized token account transfers, `Complete` state and wallet USDC/GANG readbacks are proven.
- This supersedes any pre-close `approved_amount=0` or $631770.75 pro-rata estimate as **latest durable allocation authority**, while keeping those earlier dated snapshots as historical evidence.
- No transaction signed/sent by ChatGPT; trading disabled; no new monitor/automation. **Next meaningful gate**: CompleteLaunch / Refunding and personal claim/refund confirmed, actual pool/LP liquidity and executable exit quotes. Only then update liquid portfolio balances and GANG mark.

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
