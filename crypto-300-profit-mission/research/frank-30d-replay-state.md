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
- classified_signature_count: **30 / 7,106**
- classification_before: `MRaCM1W9xxt3r2UGZqi5PS4y3kLL3r5Ra1FG63pAB9A6uLjCRzYcAaA9JUrkc98hRGgxEwAgcb6SjziXWzryNQo`
- classification_oldest_time: **2026-09-28T21:37:09Z / 2026-09-29 04:37:09 Asia/Bangkok**
- active_swaps_verified: **0**
- passive_filtered: **30**
- unresolved_tx_count: **0**
- unique_active_tokens: **0**

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
