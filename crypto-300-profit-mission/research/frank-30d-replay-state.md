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
