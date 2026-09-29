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
