# Monster Stage135: complete population one-minute publisher source coverage engine and actual cross-OS tests

2026-10-14 Asia/Bangkok. Existing [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30). Research-only source engineering. No new real Stage133 T0 capture, no automatic collection, no production Monster/Frank/Gmail/order action.

## Objective and locked prior contract

Before Stage135 code or tests, committed [Stage135 frozen source protocol](MONSTER_STAGE135_FROZEN_FULL_MARKET_1M_PUBLISHER_SOURCE_COVERAGE_PROTOCOL_20261014.md) in `646d91bb396fa63d77dd9c968eeb333271311dab`. It retains Stage77 G0-G6 thresholds, Stage116 original first forward window `SOURCE_FAILED_NO_BACKFILL`, Stage118/127 `REJECTED`, Stage132 early-momentum BUY proxy `NEGATIVE` and Stage133 user-chat-only market capture. Stage134 T0->full-population offline CI was already PASS, including recorded first-run CI failures and fix.

## Actual delivered source code

- [Stage135 source census implementation](../local-agent/scripts/monster_v4_stage135_full_market_publisher_minute_coverage.py), commit `57b639b729fc63c13cc4b16e19bab10206955706`.
- [Seven offline regression/integration tests](../local-agent/scripts/test_monster_v4_stage135_full_market_publisher_minute_coverage.py), commit `e56306bbe1a2bd1a058ba6d5dfcf96d4547b565c`.
- [Push/PR/manual CI workflow, with no schedule](../../.github/workflows/monster-stage135-full-market-minute-source-offline.yml), commit `61a0a63cb96ef13eb744db831346f8436f6829f6`.

Stage135 **recomputes Stage133 raw T0 proof and Stage134 full frozen symbol denominator** before consuming only local ZIP+CHECKSUM bytes. It calls unchanged Stage130 original `verified_day` to validate ZIP/member, daily candle OHLC/quote volume/contiguity and exact SHA256/checksum agreement. Every active T0 symbol, no-watch candidate and optional separate in-window arrival candidate remains in its audit. Missing ZIP/checksum or partial minutes are explicitly **CENSORED**, never hidden or scored as a losing/no-watch opportunity; corrupt bytes/checksum fail the run rather than get silently ignored. T0 preexisting requires 24h warmup plus 168h and can cross 9 UTC publisher days; separately claimed in-window candidate requires contiguous bars from its candidate first minute to the end but retains unverified listing origin.

Output includes each symbol's exact required interval, expected/observed minute count, missing source days and SHA receipts. **Local ZIP + companion CHECKSUM consistency is not a cryptographically independent attestation that those files truly came from Binance**. No raw official historical source was downloaded or independently verified in this CI. The software does not compute BUY/profit, actual D0 real-time timing, real Binance spot eligibility, or G0/G1 PASS. User notional remains UNKNOWN.

## Actual GitHub Actions and reproducibility

[Stage135 CI #38594578684](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38594578684) for commit `61a0a63cb96ef13eb744db831346f8436f6829f6`, `event=push`, `completed`, **SUCCESS**:

- Ubuntu job `115957869998`: Python compile, **7 tests / 7 PASS** with synthetic local original-format publisher ZIP/checksum receipts; refusing default CLI lacking T0 and archive root `STAGE135_OFFLINE_ONLY_NO_CAPTURE_NO_SCHEDULE=PASS`.
- macOS job `115957870351`: Python compile, **7 tests / 7 PASS**, same fail-closed check `PASS`.
- Tests include full population counting with a synthetic contiguous nine-day archive for one T0 symbol and censored other symbols; exact ZIP parsing/SHA; missing checksum vs corrupt checksum; one-minute gap; separate unverified arrival; tampered T0 rejection; end-to-end offline CLI. These are synthetic **engineering tests only**, **not real Binance forward OOS**.

## Current mainline assessment

An actual Stage133 manually requested full three-endpoint Binance time/exchangeInfo/time T0 has **not yet** occurred. No three disjoint, complete, independently verifiable future seven-day crypto windows exist. Stage135 now provides a source-ready offline audit for future local publisher archives, but live user-facing timely discovery and the G1 crypto denominator remain unverified. Do not claim a two-week manual snapshot pair is 1m delay proof.

Immediate next core work: accumulate genuinely new complete original timestamped data for the entire market, with independent point-in-time spot/derivatives trade rules and issuer metadata, in-window introductions/halts, then run the frozen single-core D0/D1 G0-G3 scoring. G4 must have user specified trade notional, bid/ask depth, fees, conservative exit and >=30 independently sourced execution pairs. Other AI independent review and Mac/notification permission remain separate gates. Avoid further optimization of the exposed 31/519 events or inventing a fallback scheduled collector.

`STAGE135_SOURCE_ENGINE_CODE=DONE`; `STAGE135_MACOS_UBUNTU_CI=PASS`; `STAGE135_GENUINE_NEW_SOURCE_NOT_CAPTURED`; `STAGE133_LIVE_T0=NOT_DONE`; `G0=PARTIAL`; `G1=NOT_SCORABLE`; `G2_G3=NOT_PASSED`; `G4=UNKNOWN`; `G5_REVIEW=NOT_DONE`; `G6_DEPLOYMENT=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`; `NO_NEW_SCHEDULE`.
