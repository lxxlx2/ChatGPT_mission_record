# Monster Stage124 — manual two-snapshot all-market observation (pre-result protocol)

Date: 2026-10-14 Asia/Bangkok. Original Monster Draft PR #30, user expressly prefers **NO automatic Stage99 scheduled captures** and will request a new data pull manually as needed. No new automation, cron, schedule, Gmail, Mac code replacement or Monster live deployment. The user has been given a local zsh command to disable all three existing Stage99 launchd jobs; **whether it actually ran remains UNKNOWN until user output**. Stage99 Oct14 original frozen 06:00 UTC failed with `SOURCE_FAILED_NO_BACKFILL`; Stage123's independent new real source baseline is legitimate research, NOT retroactively that missing archive.

## Input: actual finished new observation saved BEFORE any new follow-up outcomes

- Existing actual market data batch `monster/evidence/monster_stage123_20261014T094824Z_manifest.json` observed at 2026-10-14T09:48:24.840Z; its manifest lists **8 complete original connected Binance structured source files** from four Binance native read-only USD-M endpoints; 927 full exchangeInfo symbols, 525 active trading USDT PERPETUAL. Full 24h ticker 793, BBO 795, mark 930. All 525 active match each feed and all their quote/mark/24h timestamps lie 09:47:49.937 to 09:48:26.037 UTC. Five official exact Unicode market names retained.
- The connector provides structured data, not original byte-identical Stage97 official HTTPS raw receipt, and these four API responses are not perfectly simultaneous. The older 24h rolling price change field is *backward looking*, not post-observation profit. No user order amount was supplied or approved.
- Future actual manual request should use **the same four sources**, full market, real timestamp per symbol, and archive all source rows plus manifest to same PR30. User controls when another collection happens; no future date or time must be invented.

## Frozen single-model evaluation for the NEXT manual observation

1. An offline `monster_v4_stage124_manual_snapshot_forward_compare.py` consumes two manifest paths with no internet access. Resolve the exact 8 named files relative to the Mission root; enforce path containment under `monster/evidence`, stable source schema, exact count, active USD-M USDT PERPETUAL universe and unique exact symbol strings (Unicode supported); retain original instrument identities and unaltered strings. Disallow crossing quote venue or treating Spot as the same instrument. Reject malformed/stale timestamps, impossible best-bid>ask, nonfinite/nonpositive prices or malformed source file. Do not use metadata's nonauthoritative `exchangeInfo.serverTime` to define the snapshot clock.
2. T0 **full 525 denominator frozen**. Compare all T0 active USD-M symbols at later requested T1, with T1 omissions/delistings/contract-type changes classified `UNOBSERVED_OR_CHANGED` (NOT a loss or positive). Any newly listed active symbol T1 is reported separately and NEVER added retroactively to the T0 denominator.
3. T0 midquote=(bestBid+bestAsk)/2 and T1 midquote at time of each observed BBO. Endpoint forward marked price return = `(T1_mid/T0_mid-1)*100`. This is **gross price-proxy**, not realizable PnL: no entry fill, exit book depth, fees, funding, slippage, borrow or liquidation. T0->T1 mark price return may be recorded as *independent cross-reference*; Mark != tradable fill.
4. Price-only endpoint >=2x/5x/10x is **not** the time FIRST >=2x; a symbol can touch >=2x and retrace between manual observations, so full true early-2x recall, time-to-2x, D0 and D1 G1/G2/G3 remain **NOT_SCORABLE** without official 1m full-window replay. Missing T1 data => CENSORED; never write zero or use backwards 24h ticker growth as future return. Per-observation exact timestamps must be disclosed; no hidden simple average that drops negative or missing.
5. Preserve price-to-spread and market liquidity descriptors for **every** comparable instrument (current BBO spread bps, T0/T1 prior24h USD turnover, effective annualization NOT allowed). Summary includes full denominator, matched count, missing count/reasons, >=2x endpoint count, <=50% endpoint count, median/p10 etc for the matched but not falsely extrapolate to all.
6. Acceptance: selftest validates real Stage123 525 baseline WITHOUT supplying fake T1 and outputs only a `READINESS` artifact; a fully synthetic second batch may test code but must never be saved as actual Binance future results. Original old Stage118 `REJECTED` and original Stage99 failed window remain. Genuine future comparison only after the user's next manual data request.

`STAGE124_MANUAL_COMPARISON_PROTOCOL=FROZEN_BEFORE_T1`;
`STAGE123_T0_ACTUAL_SOURCE=ARCHIVED`;
`STAGE124_NEW_T1_REAL_BINANCE=NOT_YET_REQUESTED`;
`STAGE124_TWO_SNAPSHOT_FORWARD_RETURN=NOT_YET_AVAILABLE`;
`STAGE105_THREE_ORIGINAL_OOS_WINDOWS=UNCHANGED_NOT_COMPLETE`;
`G0_CRYPTO_IDENTITY=PARTIAL`;
`G1_G2_G3_TRUE_CAUSAL_EARLY_ALERT=NOT_SCORABLE_FROM_PAIR`;
`G4_EXECUTABLE_NET=UNKNOWN`;
`MONSTER_DEPLOYMENT=NO_GO`;
`FRANK_UNCHANGED`;
`STAGE99_USER_STOP_COMMAND_STATUS=UNVERIFIED_UNTIL_LOCAL_OUTPUT`;
`NO_AUTOMATIC_COLLECTION_OR_SCHEDULES`.
