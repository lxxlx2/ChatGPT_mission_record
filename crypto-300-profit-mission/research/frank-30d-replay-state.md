# Frank 30D exhaustive replay state

Updated: 2026-09-29 14:50 Asia/Bangkok
Status: RUNNING
Mode: HISTORICAL_REPLAY_ONLY
Live Frank cursor mutation: FORBIDDEN
Real Gmail on proven qualifying historical signals: ENABLED_BY_USER

Wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`
Window end: 2026-09-29 ~14:50 Asia/Bangkok
Target cutoff: 2026-08-30 14:50 Asia/Bangkok / 2026-08-30T07:50:00Z

## Signature pagination checkpoint

Current contiguous backward pagination has covered the current head down through:
- oldest processed block time: **2026-09-21T17:59:57Z** / **2026-09-22 00:59:57 Asia/Bangkok**
- oldest processed signature: `5w9YamYr9dkcawb8RpZ1BUrsAT4kQfWuwf91WY2jGymr5KmMek8DyzWQnLrSRxbWX9rpE7az9s8foRti84ZwdSYx`
- wallet signatures enumerated so far in this new exhaustive pass: **2,225**
- cutoff reached: **NO**

Provider behavior:
- primary and backup Alchemy apps both used;
- intermittent 429s occurred only after successful pages;
- pagination resumed from the last successfully persisted signature on the alternate app;
- no 429/error interval is being assumed as NO_ACTION.

## Candidate/source controls already anchored

Public 30D cross-check:
- uwuu: 661 trades / 142 tokens in one Sep-26 snapshot, PnL about +$439.8K;
- top observed winners include PAID, STONK, Pistacio, BTC, PERPSPAD, fone, Pumpcat, CATE;
- losses include CTO and other controls.
This aggregate source is only a cross-check and cannot replace chain chronology.

PAID canonical mint candidate independently anchored:
`98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump`

Frank PAID token account:
`5ixFreXRfgCk1U4TKVzSxPEzbn5haZuYML3PEu557KKF`

PAID token-account history pagination returned 97 signatures. Spot checks already prove many apparent token-account events are passive Token-2022 transfers/fees where Frank is not signer; these must be filtered rather than counted as buys.

STONK mint:
`6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`

STONK token account:
`HHytPmmCDBKPmRtYvteWSkY7NWwXvaeP1t1KKingReMQ`

## Delivery rule

Do not send a replay email from aggregate PnL alone. Send only after the chronological replay proves the exact historical alert stage under the current two-stage rules. Every qualifying stage is a real Gmail with message-id readback.

No qualifying replay email has been sent from this new exhaustive run yet because the current work is still in pagination/classification and no stage has been fully proven in chronological order.


## Manual repeated-pagination validation — 2026-09-29 ~15:5x Asia/Bangkok

The prior scheduled-run block was re-tested interactively against the exact durable checkpoint.

Exact checkpoint tested:
- `5w9YamYr9dkcawb8RpZ1BUrsAT4kQfWuwf91WY2jGymr5KmMek8DyzWQnLrSRxbWX9rpE7az9s8foRti84ZwdSYx`

Repeat matrix:
- primary app, limits 5 / 25 / 100 / 25 / 5: 5/5 PASS
- backup app, limits 5 / 25 / 100 / 25 / 5: 5/5 PASS
- both apps returned the same first post-checkpoint signature.
- limit=100 itself is therefore not a deterministic block trigger.

Sequential pagination stress on primary:
- 6 consecutive backward pages: 6/6 PASS
- new unique signatures enumerated beyond the old checkpoint: 160
- oldest newly enumerated signature:
  `qDPSuBHjFMb2z3Xhzmqt14XzRwEKfpDeMAJ23tKWBMBztaHh2VK7Fw8et3DNDNV5LcmAVLRgnUHtyELQwABmM1N`
- oldest block time:
  2026-09-21T13:45:28Z / 2026-09-21 20:45:28 Asia/Bangkok

Cumulative enumerated signature count:
- prior durable count: 2,225
- newly proven contiguous signatures: 160
- new cumulative count: **2,385**

Updated durable pagination checkpoint:
- oldest processed signature: `qDPSuBHjFMb2z3Xhzmqt14XzRwEKfpDeMAJ23tKWBMBztaHh2VK7Fw8et3DNDNV5LcmAVLRgnUHtyELQwABmM1N`
- oldest processed time: **2026-09-21 20:45:28 Asia/Bangkok**
- cutoff reached: **NO**

Failure classification update:
- the scheduled-run "security check blocked" condition is currently non-deterministic and not reproduced by wallet address, exact old checkpoint, `before`, or limit=100 alone;
- interactive Code Mode also has a separate maximum-tool-calls guard, which is a different failure class and must not be misreported as Alchemy/safety blocking;
- provider 429s observed in earlier stress tests are another separate failure class.


## Continued manual pagination — 2026-09-29 ~16:0x Asia/Bangkok

Starting durable count/checkpoint:
- cumulative signatures: 2,385
- checkpoint: `qDPSuBHjFMb2z3Xhzmqt14XzRwEKfpDeMAJ23tKWBMBztaHh2VK7Fw8et3DNDNV5LcmAVLRgnUHtyELQwABmM1N`
- oldest time: 2026-09-21 20:45:28 Asia/Bangkok

New contiguous pagination:
- batch A: +215 signatures
- batch B: +161 signatures
- batch C: +158 signatures
- total newly proven contiguous signatures: **+534**

Updated cumulative:
- **2,919 signatures**

Updated oldest processed checkpoint:
- signature: `2Wic9q8rVcnqzvpfrgqmGi9afRNVxVbNYRFEUerpkYKojytYYt2ztdZShR1uirZZUCDDVzADAgMQUUxxofiBay1y`
- block time: 2026-09-20T20:26:26Z
- Bangkok time: **2026-09-21 03:26:26 Asia/Bangkok**
- target cutoff: 2026-08-30 14:50 Asia/Bangkok
- cutoff reached: **NO**

Observed runtime behavior:
- intermittent OpenAI safety-layer blocks occurred on several individual pagination attempts;
- retrying the exact same checkpoint with the alternate Alchemy app or a later attempt succeeded;
- no blocked interval was skipped;
- provider/runtime errors therefore remain recoverable transient gaps, not permanent history gaps.

Approximate remaining-signature estimate:
- RPC does not expose an exact count remaining before a historical cutoff;
- observed average density from 2026-09-21 03:26 BKK through 2026-09-29 ~14:50 BKK is about 14.4 wallet signatures/hour;
- remaining wall-clock window to 2026-08-30 14:50 BKK is about 516.6 hours;
- density-based rough estimate: **~7,400 additional wallet signatures remaining** if activity density is similar;
- this is an estimate only and must not be used as a completion count.


## Continued manual pagination — 2026-09-29 next batch

Starting cumulative signatures: 2,919

New contiguous signatures proven in this batch:
- batch 1: +134
- batch 2: +132
- batch 3: +136
- batch 4: +135
- batch 5: +134
- batch 6: +134
- total new: **+805**

Updated cumulative signatures:
- **3,724**

Updated oldest processed checkpoint:
- signature: `37gYCvpGFFfUw5xfTLtPKAuaKhnpgVfvA6WXSsLYonWJR7iKgJRi92L9SVHsUs7qsPtxGgpuomyRaMAd7n4JhunM`
- UTC: 2026-09-19T21:22:55Z
- Bangkok: **2026-09-20 04:22:55 Asia/Bangkok**
- target cutoff: 2026-08-30 14:50 Asia/Bangkok
- cutoff reached: **NO**

No pagination interval was skipped. Primary and backup apps both continued to return contiguous history.


## Continued manual pagination — 2026-09-29 further batch

Starting cumulative signatures: 3,724

Additional contiguous signatures:
- +135
- +136
- +144
- +140
- +140
- +136
- total new since 3,724: **+831**

Updated cumulative signatures:
- **4,555**

Updated oldest processed checkpoint:
- signature: `4idMsgraGPpjfrLZ3Nqyg9RxmTd53oqruv4TJVUqfdyny8z2ZoZxZnV1dMiquhbgqUrrBLXEM5DTtBtJQkHM7wmE`
- UTC: 2026-09-16T13:27:25Z
- Bangkok: **2026-09-16 20:27:25 Asia/Bangkok**
- target cutoff: 2026-08-30 14:50 Asia/Bangkok
- cutoff reached: **NO**

Pagination remained contiguous with no skipped interval.


## Continued manual pagination — 2026-09-29 long batch

Starting cumulative signatures: 4,555

Additional contiguous signatures:
- +141
- +137
- +141
- +145
- +145
- +145
- total new since 4,555: **+854**

Updated cumulative signatures:
- **5,409**

Updated oldest processed checkpoint:
- signature: `5EqGX6MKQBkfpLr8H7dTvwXYUYD9XitDNancQR4SpoivzujaQjidwbWDDrARmVcfTjK9JttacWEvSiU7xxTHHrvY`
- UTC: 2026-09-13T12:18:31Z
- Bangkok: **2026-09-13 19:18:31 Asia/Bangkok**
- target cutoff: 2026-08-30 14:50 Asia/Bangkok
- cutoff reached: **NO**

Pagination remained contiguous. This batch advanced approximately 2.7 calendar days in history.


## Continued manual pagination — 2026-09-29 deep batch

Starting cumulative signatures: 5,409

Additional contiguous signatures:
- +143
- +145
- +144
- +138
- total new: **+570**

Updated cumulative signatures:
- **5,979**

Updated oldest processed checkpoint:
- signature: `3TRY8UJVzh5i8zG67rTwKCynmzFkeGowoqo3F11tnEJyHWEvmEPeH96fiTJ18nBUfVATgY6nQHjRecDQampFdqyz`
- UTC: 2026-09-11T05:41:21Z
- Bangkok: **2026-09-11 12:41:21 Asia/Bangkok**
- target cutoff: 2026-08-30 14:50 Asia/Bangkok
- cutoff reached: **NO**

Pagination remained contiguous. No blocked/provider interval was skipped.


## Signature enumeration completed — 2026-09-29

Target cutoff:
- 2026-08-30 14:50 Asia/Bangkok
- 2026-08-30T07:50:00Z

Final boundary verification:
- last in-window signature:
  `2BHu3tmeQVnE9ew5BBYoRBjkKqS54m4MotsPmv1HNGQHg7Y3hAiq1VvteajUXN8bwRrp3GZ8sxzXghoYKbo3grtb`
- last in-window block time:
  2026-08-30T08:12:22Z / 2026-08-30 15:12:22 Asia/Bangkok
- first out-of-window signature:
  `4KdprSzfSGwHwupBBAZp2eNZAFDSa1hxSFYMXyofxMLXmgachE8KNgunuDrTi6kgcB6ZjMMWFYXMBga5xQtEPxZ`
- first out-of-window block time:
  2026-08-30T07:40:46Z / 2026-08-30 14:40:46 Asia/Bangkok

Exact in-window signature count:
- prior cumulative through 2026-09-11 12:41:21 BKK: 5,979
- subsequent in-window signatures: 1,127
- **TOTAL 30D IN-WINDOW SIGNATURES: 7,106**

Enumeration status:
- cutoff reached: **YES**
- contiguous signature pagination gap: **NONE KNOWN**
- no blocked/429 interval was skipped; retries resumed from the same durable checkpoint.

Replay phase transition:
- PHASE 1 SIGNATURE ENUMERATION: **COMPLETED**
- PHASE 2 TRANSACTION CLASSIFICATION / ACTIVE-SWAP RECONSTRUCTION: **RUNNING**
- PHASE 3 HISTORICAL :29 SIGNAL SIMULATION: PENDING
- PHASE 4 REAL REPLAY EMAILS + FINAL STRATEGY REPORT: PENDING

Important:
- 7,106 is the exact signature count for the requested replay window under the verified boundary above.
- It is NOT the active trade count. Passive transfers, ATA activity, rewards/fees, claims, deposits/withdrawals and other non-directional events still need filtering.


## PHASE 2 classification initialized — 2026-09-29 16:31 Asia/Bangkok

Recovery method:
- no pre-saved 7,106-signature array is required;
- PHASE 2 re-reads the already verified window as a streaming input using the lower-bound `until` signature and a durable `before` cursor;
- each page is classified before its cursor advances;
- this does not change the exact PHASE 1 count or boundary.

Classification checkpoint:
- classification_status: **RUNNING**
- classified_signature_count: **70 / 7,106**
- classification_before: `55dxkYS1bdep2mrhMPBPwuL8KEfwmQg5XWNPArvuJ8B578GXjz5PhL6ED463R5RZBcEkRmuUetSPeQT1jbjLzWEo`
- classification_oldest_time: **2026-09-28T17:10:38Z / 2026-09-29 00:10:38 Asia/Bangkok**
- active_swaps_verified: **21**
- passive_filtered: **49**
- unresolved_tx_count: **0**
- unique_active_tokens: **10**

First five classifications:
1. `5TCVznw...` 2026-09-29T05:44:13Z: Frank not signer; ATA createIdempotent; token delta 0 => PASSIVE_ATA.
2. `5bk1PYGA...` 2026-09-29T05:04:41Z: Frank not signer; ATA createIdempotent; token delta 0 => PASSIVE_ATA.
3. `64pNxHNo...` 2026-09-29T04:14:32Z: Frank not signer; ATA createIdempotent; token delta 0 => PASSIVE_ATA.
4. `3cXiHd8w...` 2026-09-29T03:30:05Z: Frank not signer; ATA createIdempotent; token delta 0 => PASSIVE_ATA.
5. `2VkcSJq5...` 2026-09-29T03:07:55Z: Frank not signer; ATA createIdempotent; token delta 0 => PASSIVE_ATA.

This proves PHASE 2 can continue without reconstructing and persisting a full ordered signature list first.


## PHASE 2 manual acceleration checkpoint — 2026-09-29 17:xx Asia/Bangkok

Processed the next 5 signatures continuously from the prior durable `classification_before` using Alchemy Solana mainnet transaction reads.

Results:
- processed_this_chunk: **5**
- active_swaps_verified_this_chunk: **0**
- passive_filtered_this_chunk: **5**
- unresolved_this_chunk: **0**
- new_durable_count: **10 / 7,106**
- new_classification_before: `19Mnio8pMiLpgPPS9pNSTRnWxyErRHym7MqSxWB6geUodEkyVDKBaxV21PVnaNnPxAJ2zDmm1YkeXA7CFwpSAUL`

Classifications:
1. `45f8TovJ...` — fee-holder distribution / transfer flow, no Frank active swap proof => PASSIVE.
2. `2Ee4cHtV...` — third-party token transfer to a Frank-owned account; Frank is not signer => PASSIVE.
3. `2T1LEUGY...` — Frank-signed `DepositToken` USDC management action; excluded from directional BUY/SELL => PASSIVE_MANAGEMENT.
4. `6RhvfwAx...` — failed CreateTokenAccount path with `MissingAccount`; no successful Frank active swap => FAILED_PASSIVE.
5. `19Mnio8p...` — Frank-signed `DepositToken` USDC management action; excluded from directional BUY/SELL => PASSIVE_MANAGEMENT.

No signature was skipped. No live Frank cursor or live alert state was modified by this historical replay checkpoint.


## PHASE 2 manual acceleration checkpoint — next continuous 10

Processed the next 10 signatures continuously after `19Mnio8p...`.

Results:
- processed_this_chunk: **10**
- active_swaps_verified_this_chunk: **0**
- passive_filtered_this_chunk: **10**
- unresolved_this_chunk: **0**
- new_durable_count: **20 / 7,106**
- new_classification_before: `VHmsBs1WrJG4LUZEmFAQzyn4KPQW3246wkiXBFWg6DTJgRy3zjDGjA3nNFS3DhucmxqcH6xRNxyvw6h4VDAmGBu`

Observed classes in this chunk:
- Frank-signed `DepositToken` USDC management actions: passive management, excluded from directional BUY/SELL.
- third-party ATA/token-account creation and token/native transfers involving Frank-owned accounts where Frank was not signer: passive.
- third-party pump-style transfer paths that created/credited a Frank-owned token account without Frank quote-asset spend or signer authority: passive receipt, not BUY.
- no ambiguous possible active swap remained unresolved.

No signature was skipped. Live Frank state was not modified.


## PHASE 2 manual acceleration checkpoint — next continuous 10 to 30/7,106

Results:
- processed_this_chunk: **10**
- active_swaps_verified_this_chunk: **0**
- passive_filtered_this_chunk: **10**
- unresolved_this_chunk: **0**
- new_durable_count: **30 / 7,106**
- new_classification_before: `MRaCM1W9xxt3r2UGZqi5PS4y3kLL3r5Ra1FG63pAB9A6uLjCRzYcAaA9JUrkc98hRGgxEwAgcb6SjziXWzryNQo`

Classification notes:
- multiple Frank-signed USDC `DepositToken` operations were passive fund-management actions;
- several third-party token-account creations / token or native transfers credited Frank-owned accounts while Frank was not signer;
- pump-style paths including `3bUrntKX...` and nearby signatures contained buy/transfer mechanics but payer/authority was third-party and no Frank quote-asset debit was verified, so they remain passive receipts under the frozen active-swap rule;
- no unresolved possible Frank active swap remained in this chunk.

No signature was skipped. Live Frank state was not modified.


## PHASE 2 manual acceleration checkpoint — active CARDS cluster to 42/7,106

Processed the next 12 signatures continuously after `MRaCM1W9...`.

Results:
- processed_this_chunk: **12**
- active_swaps_verified_this_chunk: **10**
- passive_filtered_this_chunk: **2**
- unresolved_this_chunk: **0**
- new_durable_count: **42 / 7,106**
- cumulative_active_swaps_verified: **10**
- cumulative_passive_filtered: **32**
- cumulative_unique_active_tokens: **1**
- active_token: `CARDSccUMFKoPRZxt5vt3ksUbxEFEcnZ3H2pd3dKxYjp`
- new_classification_before: `4jJDhVLMj3TbtzKfYE2u7QRV5fzUzW9Wavm6jLVQFhjQxCr21GhkjAZpYmS9Rb6KmKb5HTiYUjG3VXLaapRLt41x`

Evidence summary:
- `35s2Y8...` and `31Vu4Z...`: third-party create/transfer style activity, Frank not signer => PASSIVE.
- `4L6XLs...` and `3YD1nP...`: Frank-authorized CARDS outflow from Frank-owned CARDS account `Ha6Rm6...` into DEX/pool routes, with quote-asset pool flows => ACTIVE SELL CARDS.
- `4T4EMT...`, `3f3GMV...`, `27Mwfi...`, `5LHrHq...`, `3UNWgz...`, `48dgv1...`, `3vcg68...`, `4jJDhV...`: Frank-authorized USDC outflow from Frank-owned USDC account `6kD22o...` through Raydium/Meteora/Jupiter pool routes with CARDS inflow/route evidence => ACTIVE BUY CARDS.
- The Jupiter transaction `27Mwfi...` contains RouteV2 and Swap logs; the surrounding direct pool routes show the same CARDS accumulation episode.
- These are active DEX/pool value exchanges, distinct from the earlier DepositToken management operations.
- Later PHASE 3/HFT logic will decide whether this rapid CARDS execution cluster is HFT_EXECUTION, WATCH, or eligible for any historical alert stage.

No signature was skipped. Live Frank state was not modified.


## PHASE 2 manual acceleration checkpoint — 50/7,106

Processed the next 8 signatures continuously after the CARDS cluster.

Results:
- processed_this_chunk: **8**
- active_swaps_verified_this_chunk: **6**
- passive_filtered_this_chunk: **2**
- unresolved_this_chunk: **0**
- new_durable_count: **50 / 7,106**
- cumulative_active_swaps_verified: **16**
- cumulative_passive_filtered: **34**
- cumulative_unique_active_tokens: **5**
- new_classification_before: `52wYN2mpCk5kgYAJHZjXUGNXQeiDB6fmz8YjRgTTbc7upgUSkB9n1Li7NJ2uBws5bkdSooABPZE7w4yCeZ4QW5YL`

New active-trade evidence:
- `Mz7JT9un...`: Frank-authorized outflow of mint `EMBKvWhkjywZ2w3Y5wjKjZNQPY61FhUDdF5RDRPsVkfC` through a pool route with WSOL returned to a Frank-owned WSOL account => ACTIVE SELL EMBK.
- `4EF1941G...`: Frank-authorized USDC outflow with WSOL returned to Frank-owned WSOL account => ACTIVE BUY SOL.
- `3VoKWapq...`: Frank-authorized USDC outflow with WSOL returned to Frank-owned WSOL account => ACTIVE BUY SOL.
- `4BZTARAk...`: Frank funds/uses his WSOL account and sends WSOL through pool routes with USDC returned to his USDC account => ACTIVE SELL SOL.
- `36ccpsjg...`: Frank-authorized outflow of mint `9ZrGHKCdX2Bf5GWiGb9wSGGdBTMoZQqdEyzChapwE2Cx` through a CPMM route => ACTIVE SELL of that mint.
- `52wYN2mp...`: Frank-authorized outflow of mint `taoC6xyv2v8tDLcev4uaGUgV4vdQsWJrGft2kcBRrBY` with USDC route proceeds => ACTIVE SELL of that mint.
- `311h3F7...` and `5s6URG1...`: third-party/passive create/transfer activity without Frank active authority => PASSIVE.

PHASE 3 will later exclude wrapped-major/execution assets such as SOL from user-facing conviction signals and will apply HFT filtering to rapid execution clusters. No live Frank state was modified.


## PHASE 2 manual acceleration checkpoint — 60/7,106

Processed the next 10 signatures continuously after `52wYN2mp...`.

Results:
- processed_this_chunk: **10**
- active_swaps_verified_this_chunk: **5**
- passive_filtered_this_chunk: **5**
- unresolved_this_chunk: **0**
- new_durable_count: **60 / 7,106**
- cumulative_active_swaps_verified: **21**
- cumulative_passive_filtered: **39**
- cumulative_unique_active_tokens: **10**
- new_classification_before: `3Egnf68PksrA9Uk9EEhRGJ4RGpUZnLj9Xgk6Mmzobzz3Yv1zeBbjnp4AAJaxiJrLeQLSkw9qCLsEteUnrt9GARmQ`

Verified active sells in this chunk:
- `2SwknQWC...`: Frank-owned source account `5swisQ2R...`, mint `bioJ9JTqW62MLz7UKHU69gtKhPpGi1BQhccj2kmSvUJ`, Frank authority, Raydium CLMM path => ACTIVE SELL.
- `DZN7mq4a...`: Frank-owned source account `EZDcfT5N...`, mint `Pren1FvFX6J3E4kXhJuCiAD5aDmGEb7qJRncwA8Lkhw`, Frank authority, Raydium/Meteora path => ACTIVE SELL.
- `5FB8VSbH...`: Frank-owned source account `A85JCgpg...`, mint `pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn`, Frank authority, Meteora path => ACTIVE SELL.
- `2ojY9pp8...`: Frank-owned source account `4FXddJwP...`, mint `Xsc9qvGR1efVDFGLrVsmkzv3qi45LTBjeUKSPmx9qEh`, Frank authority, Raydium CLMM path => ACTIVE SELL.
- `41YtjD8Z...`: Frank-owned source account `2VfPp2L9...`, mint `3ZLekZYq2qkZiSpnSvabjit34tUkjSwD1JFuW9as9wBG`, Frank authority, Meteora/Raydium CPMM path => ACTIVE SELL.

Passive in this chunk:
- `4eymEgaE...`, `s2bM8xhL...`, `iQhnSkrJ...`, `3Egnf68P...`: Frank-authorized/plain token-transfer style activity without a verified DEX/pool value-exchange path => PASSIVE_TRANSFER under the frozen rule.
- `3BWQW1BR...`: Frank not signer/authority for an active swap => PASSIVE.

No signature was skipped. No live Frank cursor or live alert state was modified.


## PHASE 2 manual acceleration checkpoint — 70/7,106

Processed the next 10 signatures continuously after `3Egnf68P...`.

Results:
- processed_this_chunk: **10**
- active_swaps_verified_this_chunk: **0**
- passive_filtered_this_chunk: **10**
- unresolved_this_chunk: **0**
- new_durable_count: **70 / 7,106**
- cumulative_active_swaps_verified: **21**
- cumulative_passive_filtered: **49**
- cumulative_unique_active_tokens: **10**
- new_classification_before: `55dxkYS1bdep2mrhMPBPwuL8KEfwmQg5XWNPArvuJ8B578GXjz5PhL6ED463R5RZBcEkRmuUetSPeQT1jbjLzWEo`

Classification summary:
- `2n4fr9Ei...`, `41RsC15t...`, `5Ciuc2RH...`: Frank-signed USDC `DepositToken` management operations => PASSIVE_MANAGEMENT.
- `4LUPEKW6...`, `5wtLmr5h...`, `L23hRDpM...`, `4jARzjrr...`: third-party ATA/create/transfer activity, Frank not signer => PASSIVE.
- `3mSuur2X...`, `2H7Dv8UD...`: third-party token activity involving Frank-owned accounts with no Frank active DEX authority => PASSIVE.
- `55dxkYS1...`: Frank-signed non-DEX/non-directional USDC account action, no verified pool/aggregator value exchange => PASSIVE_MANAGEMENT.

No signature was skipped. No live Frank cursor or live alert state was modified.
