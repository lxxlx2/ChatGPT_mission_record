# Frank historical MULTIPLE delivery E2E

**FRANK_HISTORICAL_MULTIPLE_DELIVERY_E2E_PASS**

## Selection

SELECTED_TOKEN = STONK. STONK historical ACCUMULATION = YES; STONK historical MULTIPLE = YES.

Selected the chronologically first valid STONK MULTIPLE in the existing frozen V1 replay. The preference was specified by the user; subsequent profit was not used as a predicate or selection override. No fallback or PnL ranking was needed. No profit number is inferred.

- Mint: `6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`
- Episode ID: `ed4e4398ce0f05b838084b443803aaeb7a7231873186cf9b6503ba1b0403d94c`
- Historical signal ID: `740649ef308021927eb1104113b63a8b0a33d66b9ee4f6c3c53b916d037fdb29`
- Delivery identity: `historical-test:740649ef308021927eb1104113b63a8b0a33d66b9ee4f6c3c53b916d037fdb29:delivery-e2e-v1`
- Frozen policy hash: `83ebab1fbb8ec7e03950626137c5597a38b81b8a4085d9150610018cc78cedab`

Existing sources: `v1-history-replay-final.json`, `v1-historical-signals.csv`, and `v1-history-replay-final.sqlite` in the private evidence root. The selected signal bodies in the JSON summary and durable ledger agree exactly.

## Deterministic reconstruction and provenance

Read the 29 existing classified ACTIVE_TRADE records for this mint, without fetching the entire 30D, reclassifying records, redefining episodes or changing IDs. Verified all 29 cached raw transaction hashes. Inserted those existing records into a separate reconstruction ledger and ran the unchanged V1 Engine in DRY_RUN_AUDIT. All generated STONK signal bodies, identities, timestamps and reason codes matched the existing source exactly. Reconstruction outbox remains DRY_RUN_AUDIT and is never drained.

Targeted finalized raw-chain reads of the selected episode first BUY, ACCUMULATION trigger and MULTIPLE trigger matched the original raw hashes, slots and signatures:

| Transaction | Slot | Result |
|---|---:|---|
| `5YHKqriQwjvN27yzoNyJmaEVRsJH4yGL8FRiCpt8PvTQgAbMLNJ9rS2hj1ptBLvb2sHAQgdnGL3FCC8Ym6LYGY6g` | 444679122 | raw hash / slot / signature PASS |
| `4p41QWdo2TmQZEVKBZH5PFcH93puVg79Pwb9FSek8BgaJkGfQnhGwX1fZBN67xGQaBe5nSqjBCLiLQEwrFizjuNu` | 444679309 | raw hash / slot / signature PASS |
| `4sTTVMgVS68TgiAXR2JFNCNxDSGyrXUcEnW1u9Eohk3c6tUtudBoNNcY8v9YdKNhnbKTh8A7PjJLfx1V7MYN9h36` | 444699970 | raw hash / slot / signature PASS |

## Every observed STONK episode

### `ed4e4398ce0f05b838084b443803aaeb7a7231873186cf9b6503ba1b0403d94c`

First ACTIVE BUY: 2026-09-06T09:28:31+07:00.
Final observed buy_count: 14; cumulative known raw USDC buys: 475194.926270.

- FRANK_ACCUMULATION_SIGNAL / PRECONFIRM: 2026-09-06T09:29:31+07:00
- Triggering signature: `4p41QWdo2TmQZEVKBZH5PFcH93puVg79Pwb9FSek8BgaJkGfQnhGwX1fZBN67xGQaBe5nSqjBCLiLQEwrFizjuNu`
- buy_count: 2; cumulative quote: {'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': '81956.017648'}
- Original signal ID: `f8efef0b7e2ccf92fa55ab10bd8b938b64ccb13a49d816ccf9618e5880c9d0ff`
- Reason codes: `PATH_C_REPEATED_ACTIVE_BUYS_GE_2`, `ROLLING_60M_USDC_QUOTE_GE_25000`, `PATH_C_SINGLE_LARGE_BUY_NOT_ACCUMULATION`

- FRANK_MULTIPLE_SIGNAL / SUSPECTED_CONVICTION: 2026-09-06T11:18:35+07:00
- Triggering signature: `4sTTVMgVS68TgiAXR2JFNCNxDSGyrXUcEnW1u9Eohk3c6tUtudBoNNcY8v9YdKNhnbKTh8A7PjJLfx1V7MYN9h36`
- buy_count: 6; cumulative quote: {'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': '207493.661298'}
- Original signal ID: `740649ef308021927eb1104113b63a8b0a33d66b9ee4f6c3c53b916d037fdb29`
- Reason codes: `ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED`, `MEANINGFUL_ACCUMULATION_T0_ESTABLISHED`, `EPISODE_USDC_QUOTE_GE_10000`, `PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M`, `OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING`, `NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION`, `NO_CONFIRMED_HFT_EXECUTION`, `FRESHNESS_BEHAVIOR_PASSED`, `NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT`

### `19a8e21dc0d4f2c9fc899cc5886a96f5762cd6101f458d80d55c84de31d17241`

First ACTIVE BUY: 2026-09-11T10:22:33+07:00.
Final observed buy_count: 1; cumulative known raw USDC buys: 5000.

ACCUMULATION = NO; MULTIPLE = NO. No triggering signature or signal ID exists for this episode. The first BUY has one buy and 5,000 USDC: accumulation buy-count and amount gates fail; prior accumulation, T0, cumulative amount and persistence fail. Later inventory becomes UNDETERMINED. No signal is fabricated.

## First triggers

ACCUMULATION first_trigger_at: **2026-09-06T09:29:31+07:00**, BUY #2.
Triggering signature: `4p41QWdo2TmQZEVKBZH5PFcH93puVg79Pwb9FSek8BgaJkGfQnhGwX1fZBN67xGQaBe5nSqjBCLiLQEwrFizjuNu`.

MULTIPLE first_trigger_at: **2026-09-06T11:18:35+07:00**, BUY #6.
Triggering signature: `4sTTVMgVS68TgiAXR2JFNCNxDSGyrXUcEnW1u9Eohk3c6tUtudBoNNcY8v9YdKNhnbKTh8A7PjJLfx1V7MYN9h36`.

The first BUY already exceeds 15,000 USDC but does not emit ACCUMULATION: the single-large Path C branch remains NOT_ACCUMULATION. BUY #2 establishes the repeated-buy Path C branch and T0. BUY #3–#5 fail persistence. BUY #6 spans 6,604 seconds from the first BUY, meets persistence B, and retains an already established ACCUMULATION stage. Its current rolling accumulation buy-count predicate is FAIL; MULTIPLE correctly uses the prior established stage rather than requiring a new ACCUMULATION event.

## Complete selected-episode chronology

All times below are Asia/Bangkok. Quote mint on every row is USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`. Amounts are original decoded raw quote quantities, with direct numeric comparisons; no USD conversion is inferred. Inventory quantities are observed token units, not a proven lifetime wallet position.

BUY #2 onward is an ADD to the open observed sequence. Stage before/after denotes already emitted stage milestones; it is not a claim that every later trade continues to qualify. After SELL #7 exceeds observed inventory, inventory remains UNDETERMINED and is not invented. No extra ADD/SELL notifications were dispatched.

For predicates: A=count/amount. MULTIPLE lists every non-PASS gate; omitted MULTIPLE gates are PASS. Its gates are prior_accumulation, t0, cumulative_amount, persistence, inventory, distribution, hft and freshness.

| Bangkok time | Side | Signature | Raw quote | Cumulative BUY USDC | buy_count | Observed STONK inventory / state | A count/amount | MULTIPLE predicate | Stage before → after |
|---|---|---|---:|---:|---:|---|---|---|---|
| 2026-09-06T09:28:31+07:00 | BUY #1 | `5YHKqriQwjvN27yzoNyJmaEVRsJH4yGL8FRiCpt8PvTQgAbMLNJ9rS2hj1ptBLvb2sHAQgdnGL3FCC8Ym6LYGY6g` | 47399.487446 USDC | 47399.487446 | 1 | 528876.951317789 / OPEN | FAIL/PASS | prior_accumulation=FAIL; t0=FAIL; persistence=FAIL | NONE → NONE |
| 2026-09-06T09:29:31+07:00 | BUY #2 / ADD | `4p41QWdo2TmQZEVKBZH5PFcH93puVg79Pwb9FSek8BgaJkGfQnhGwX1fZBN67xGQaBe5nSqjBCLiLQEwrFizjuNu` | 34556.530202 USDC | 81956.017648 | 2 | 911580.120522166 / OPEN | PASS/PASS | persistence=FAIL | NONE → ACCUMULATION |
| 2026-09-06T09:30:41+07:00 | BUY #3 / ADD | `2TqYpQUEtGe1TEx22aapNtZ9tLQaUb1iQ8o1UoMyAV2bDxFesjSbuxzA8MSEXrAvmoE3FRniMEKucMsma7wtXmrW` | 31101.579342 USDC | 113057.596990 | 3 | 1243768.206975849 / OPEN | PASS/PASS | persistence=FAIL | ACCUMULATION → ACCUMULATION |
| 2026-09-06T09:31:48+07:00 | BUY #4 / ADD | `eftFV6gJ2uEYmAF9V3VLgD7dPztr7hbahNewBXGDWKwo6dzdiQ5SHdUXxALVmYvJq3AoyXjUeLh2ttEXEH62Mis` | 25192.95979 USDC | 138250.556780 | 4 | 1504488.070751624 / OPEN | PASS/PASS | persistence=FAIL | ACCUMULATION → ACCUMULATION |
| 2026-09-06T09:47:52+07:00 | BUY #5 / ADD | `3AkMgUZ2TnksyrKTmr4fimhSRVTDWcG2NsqYsL7YrvAeRfE7iGKVXCbedGzVmagMrJUAv8BMyLcUnLJcBJ7nuEnP` | 44243.104518 USDC | 182493.661298 | 5 | 1939946.000037356 / OPEN | PASS/PASS | persistence=FAIL | ACCUMULATION → ACCUMULATION |
| 2026-09-06T11:18:35+07:00 | BUY #6 / ADD | `4sTTVMgVS68TgiAXR2JFNCNxDSGyrXUcEnW1u9Eohk3c6tUtudBoNNcY8v9YdKNhnbKTh8A7PjJLfx1V7MYN9h36` | 25000 USDC | 207493.661298 | 6 | 2179708.378284419 / OPEN | FAIL/PASS | ALL PASS | ACCUMULATION → MULTIPLE |
| 2026-09-06T11:26:22+07:00 | BUY #7 / ADD | `58jSLoDojkbUPHqreZEpP2wtRTnr7KwmNqjRVrK6GPp35HiKTUaEQhYaDSEsHR8zUdT1GzrTqKsTS8UjR7hPMHWo` | 52607.974907 USDC | 260101.636205 | 7 | 2655632.377849386 / OPEN | PASS/PASS | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-06T21:20:46+07:00 | BUY #8 / ADD | `21tXo53Pt62BCFThNJHNFkJosaQk88YEiCNTGmzeUT2vm5m7rmyDpb5ru2AiEMLLySWPmLWA1CT3uVtcPnEdoRuC` | 17500 USDC | 277601.636205 | 8 | 2781050.65412221 / OPEN | FAIL/FAIL | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-08T18:43:16+07:00 | BUY #9 / ADD | `3qzgMs47LeNR9Hppfu3sTsMTU7tQvtP4pPYj6CyBRzZZM3PuweRxWJoKd25ykBrxhzCPyrcVLqsiCw6UUgHqgUJ6` | 25000 USDC | 302601.636205 | 9 | 2961454.455058085 / OPEN | FAIL/PASS | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-09T04:27:22+07:00 | SELL #1 | `4sWqNysBZDFRKVgmAEtir39EHYyaHFJSrn1v8GtQR4m72YtgM1N5SyHbBxbYK9e7rfi5y2xiN1FHnAFWHFahnNBd` | 9884.946205 USDC | 302601.636205 | 9 | 2906226.062309094 / OPEN | FAIL/FAIL | freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-09T04:28:41+07:00 | SELL #2 | `2cLPRkgeXqL8M2hzfw6SVcRAWB6Y66qrdCdmbb8YyZVrpZMAVWiiEpmApBqJmkqr7nVj6woQV6PX2z3AENtTVNsY` | 19801.159743 USDC | 302601.636205 | 9 | 2795384.566041729 / OPEN | FAIL/FAIL | freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-10T02:44:52+07:00 | BUY #10 / ADD | `39DPuUCS1QULuoWMmDRuUC2cbUEgMGH8MFD5Lb5EBTwSxWDCHtQdmcEwv5U7Y89nAWfjk7MNkVmEi46C1WuzqcUk` | 24999.999999 USDC | 327601.636204 | 10 | 2928506.084176077 / OPEN | FAIL/FAIL | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-10T02:48:56+07:00 | BUY #11 / ADD | `5SypxNY1qiuL3iJE9RQby2J8KqdcsaicJF6pFdkV7ZxBthcZhNMzR4H1gukJKULddnxSXXhrWhsuX5qp521Yq7oU` | 49242.243989 USDC | 376843.880193 | 11 | 3198878.262077745 / OPEN | PASS/PASS | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-10T02:49:39+07:00 | BUY #12 / ADD | `Az1RC7SPQ7RMR3iDTK1Sobhy6H14JsA5uzuj8Q2kkX6m6bG6hKmGoxomgp9EYGcTtLzdkKUhtavurDiunRXZejt` | 48351.046077 USDC | 425194.926270 | 12 | 3454728.261664276 / OPEN | PASS/PASS | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-10T02:57:26+07:00 | BUY #13 / ADD | `5Xqwg4oTVeTFox9XPL2UpV6ktMLaUatrzZ5onjL62ehBeoE3g3cv7R1d4UmYBqtNDc35TNpZs5Qe7RjvqMDgHT5F` | 25000 USDC | 450194.926270 | 13 | 3579690.65451874 / OPEN | PASS/PASS | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-10T02:57:34+07:00 | BUY #14 / ADD | `3XbWQbPmsTLved4RjxqhaFVYmH6V3iL2rNrP8zXS19b8N4qFfLPTWbz74XGddoPBKP2TTmMK7C3AuTo4i3UbU5Ys` | 25000 USDC | 475194.926270 | 14 | 3703955.496767291 / OPEN | PASS/PASS | ALL PASS | MULTIPLE → MULTIPLE |
| 2026-09-10T04:24:36+07:00 | SELL #3 | `3bpwVSiqkUwY673rrFY8iiTuTxDgs9sTbDv2enkt5KLU9puymDqpF6aaPP5bFCZChAMyWns5qMBboKt6FN47ZNMA` | 76747.170992 USDC | 475194.926270 | 14 | 3269702.496767291 / OPEN | FAIL/FAIL | freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-10T04:24:47+07:00 | SELL #4 | `2v9EXfG1wzRBtaaqCZCaZrFV8B98Y8EBeeY55fxVJW9v2386ZRuRjC6ZNSUJX6B8NmUSHcbN1u35HrWsbgnRDYVF` | 85920.71789 USDC | 475194.926270 | 14 | 2769702.496767291 / OPEN | FAIL/FAIL | freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-10T04:24:55+07:00 | SELL #5 | `4sB5R4uoZVHy24jyRKBB2LVqFV2UkSdDdEM7rV1tBPdFkYSkgpGke9muA7FqnaJhKt1qr8r5vfaZMFsMd3F4jMvt` | 163233.853258 USDC | 475194.926270 | 14 | 1769702.496767291 / OPEN | FAIL/FAIL | inventory=FAIL; distribution=FAIL; hft=FAIL; freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-10T04:25:03+07:00 | SELL #6 | `7pnPj2EzYXhkJSat15eBP2kJXdYu11BV5htqvyNWoKjq4MHS59ushvH9pbfZsNkA8BLVTm5kJqHe99UFp2A6fqH` | 235938.440482 USDC | 475194.926270 | 14 | 269702.496767291 / OPEN | FAIL/FAIL | inventory=FAIL; distribution=FAIL; hft=FAIL; freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-10T04:25:10+07:00 | SELL #7 | `2kSodehDFmt8hBmCmrqHy91XCgNKaAThfTcrHzcRPNbcgRCJHpVSiaEWdkZVYcCdwqmfnBak6YixkobbrgbQd7H2` | 152187.274879 USDC | 475194.926270 | 14 | UNDETERMINED / INVENTORY_UNDETERMINED | FAIL/FAIL | inventory=UNDETERMINED; distribution=UNDETERMINED; hft=FAIL; freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-10T04:25:15+07:00 | SELL #8 | `3Z5h1desXzSAXWNZm5wRwvDYt49n5QxJudtYGeeibLSbQwAFZhu6XeD4RQEDP8NN1dJ9oXckv4WyzzCVpXg5UaM2` | 147627.516786 USDC | 475194.926270 | 14 | UNDETERMINED / INVENTORY_UNDETERMINED | FAIL/FAIL | inventory=UNDETERMINED; distribution=UNDETERMINED; hft=FAIL; freshness=FAIL | MULTIPLE → MULTIPLE |
| 2026-09-10T11:39:31+07:00 | SELL #9 | `2pUvQdkRmAbV3N1RNUiN5bRpQAxEKJGNgCxKGt89eFvUMf5fKi1wifBysvyLj2NhmZ2usC3adxGUJYxJEHw3ums3` | 0.131204 USDC | 475194.926270 | 14 | UNDETERMINED / INVENTORY_UNDETERMINED | FAIL/FAIL | inventory=UNDETERMINED; distribution=UNDETERMINED; hft=FAIL; freshness=FAIL | MULTIPLE → MULTIPLE |

## Actual local notifications

Two real AppKit notifications were dispatched. Both were subsequently found in macOS deliveredNotifications with exact title, full informativeText and independent historical identity. This verifies OS delivery records; it does not assert that a person read the banners.

- `[HISTORICAL TEST] Frank ACCUMULATION | STONK`: PASS; OS response `REQUEST_ACCEPTED`.
- Identity: `historical-test:f8efef0b7e2ccf92fa55ab10bd8b938b64ccb13a49d816ccf9618e5880c9d0ff:local-e2e-v1`.
- `[HISTORICAL TEST] Frank MULTIPLE | STONK`: PASS; OS response `REQUEST_ACCEPTED`.
- Identity: `historical-test:740649ef308021927eb1104113b63a8b0a33d66b9ee4f6c3c53b916d037fdb29:local-e2e-v1`.

Exactly two local historical TEST notifications were dispatched; subsequent CLI execution reused durable receipts. Historical ACCUMULATION sent no Gmail.

## Actual standalone Gmail

- Subject: `[HISTORICAL TEST][Frank 多倍信号] STONK | MULTIPLE | 2026-09-06T11:18:35+07:00`
- delivery_mode: `HISTORICAL_TEST`
- gmail_message_id: `1a103dc55e5aa123`
- gmail_thread_id: `1a103dc55e5aa123`
- sent_at: `2026-10-03T22:22:13+00:00`
- content_hash: `2a460b616fdcb49a90151de6e7ceb92871ed0e8b90c50d4acf112c2443acce50`
- readback_verified: true; durable state: `SENT_VERIFIED`
- Sent search: exactly one matching historical identity.
- Subject, X-Frank-Signal-ID, content hash, mode and full body: exact match; SENT label present.
- API readback: HTTP 200; Google error code/reason and exception class: none.
- Credential reused from private LOCAL_FILE backend; no OAuth flow or secrets printed.

The historical Gmail is not a live signal. Its first screen contains HISTORICAL REPLAY / DELIVERY E2E TEST and the three required Chinese disclaimers. The original historical signal remains immutable in DRY_RUN_AUDIT; the only sendable row is in a separate delivery ledger and a different identity namespace.

## Dedupe and real adapter crash recovery

- First execution send calls: 1; total durable attempt_count: 1.
- Second complete CLI execution send calls: 0.
- Second drain send calls: 0.
- TEST_DEDUPE = PASS.
- Simulated loss of SENT metadata only in the isolated historical-test ledger; closed and reopened the ledger and created a fresh real Gmail adapter.
- Recovered existing Gmail message ID: `1a103dc55e5aa123`.
- Recovery additional send calls: 0.
- CRASH_RECOVERY = PASS; DUPLICATE_SEND = 0.

## Live isolation

- PID before / after: 57287 / 57287.
- Last successful poll before: `2026-10-03T22:21:12.200930+00:00`.
- Last successful poll after: `2026-10-03T22:23:12.696423+00:00`.
- Processed signature before / after: `5Ez2fGTSf5VjHCEZFe1Ed1FDUBeENaHfJAUcHFyuyEfMiJTXpwnHAA55fMqnEcifi4gYfije5Cy18g5Th8shY4FH` / `5Ez2fGTSf5VjHCEZFe1Ed1FDUBeENaHfJAUcHFyuyEfMiJTXpwnHAA55fMqnEcifi4gYfije5Cy18g5Th8shY4FH`.
- pending raw before / after: 0 / 0; pending model before / after: 0 / 0.
- Finalized chain/local comparison, including the pre-test cursor anchor: missing=0; extra=0; latest head agrees.
- historical test rows inserted into live outbox = 0.
- live scanner interrupted = NO; no LaunchAgent operation or scanner restart.
- No new live signal appeared during the measured window. The independent test did not suppress or change the normal live delivery path.
- Policy, evaluator, engine, scanner, stage/store, local delivery and service script bytes exactly match deployed baseline `79bcf8646cb6e10897c7a6459434a7371cdfb643`.

## Current live status

```text
FRANK_LOCAL_SIGNAL_V1_LIVE
LOCAL_ACCUMULATION = LIVE
LOCAL_MULTIPLE = LIVE
MULTIPLE_GMAIL = LIVE
GPT_SIGNAL_AUTHORITY = REMOVED
PRODUCTION_TRADING = NO_GO
```

## Private evidence and reproducibility

Evidence directory: `/Users/jerson/Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/historical-delivery-e2e-v1`.

- selection.json: all selected signals, observed episodes and 23-row chronology.
- reconstruction.sqlite: unchanged Engine reconstruction; DRY_RUN_AUDIT only.
- targeted-chain-readback.json: three real finalized raw transaction comparisons.
- delivery.sqlite: isolated HISTORICAL_TEST Gmail ledger; no live signals or outbox rows.
- original-gmail-receipt.json and delivery-verification.json: send/readback/dedupe/crash recovery evidence.
- local-accumulation.json, local-multiple.json, local-os-readback.json: two notifications and OS full-content readback.
- live-before.json, live-isolation.json, frozen-bytes-verification.json: live boundary and byte checks.

Authorized one-time CLI: `python -m scripts.frank_historical_delivery_e2e --prepare`, then `--deliver`. Preparation is not repeated over an existing reconstruction. Delivery reruns keep the same stable identity; ambiguity never blindly resends. No merge to main.

Validation: 498 passed, 3 skipped (unrelated Monster tests require absent numpy). No credential material is included in this report.
