# Monster Stage139 official instrument and saved contractInfo evidence: actual tests and limits

Date 2026-10-15 Asia/Bangkok. Existing Draft [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30). Pure offline evidence interpretation; no Stage133 live T0, live WebSocket, Binance real GET, scheduled capture, Gmail, trades or Frank changes.

## Official evidence actually researched

Binance USD-M exchangeInfo gives the observed contract's status, contract type, underlyingType, quote/base/margin assets, onboardDate and limits. Its snapshot was recorded shortly BEFORE the newly derived Stage133 future T0; that timestamp cannot prove the status was unchanged at the exact future start. The onboardDate field does not certify first executable fill. Official docs: https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data

Binance !contractInfo websocket broadcasts listing, contract changes and settlement, with event timestamp E, contract status cs, onboarding time ot and post-migration st=1 USD-M / st=2 COIN-M. Client receipt time, exchange event time, future OHLC first candle and executable orderbook are different evidence. A standalone manually saved event cannot prove seven-day continuous coverage. Official docs: https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market

Binance official public data is released as next-day daily and monthly OHLC ZIP archives with CHECKSUM. It is retrospective bar data, not a source of live-first-alert latency. Official repository: https://github.com/binance/binance-public-data

## Code, frozen contract and tested behavior

1. Pre-registered contract: [Stage139 frozen protocol](MONSTER_STAGE139_FROZEN_OFFICIAL_PIT_INSTRUMENT_AND_CONTRACTINFO_EVIDENCE_PROTOCOL_20261015.md), commit 92a8444506c6ab48c909b2e775b51ae8cc14bce9.
2. Source code: [Stage139 original T0 metadata and saved-event parser](../local-agent/scripts/monster_v4_stage139_official_t0_and_saved_contractinfo_evidence.py), commit a41b9481f8d5d301b79c572a14ab9e941576cb52. Runs Stage133 original three-raw-HTTP reconstruction plus Stage134 frozen all-symbol census and reports each original raw exchangeInfo symbol's underlyingType, status, contractType, quoteAsset, onboardDate and raw SHA. Explicit official COIN is labelled OFFICIAL_COIN_TYPED_ISSUER_UNVERIFIED. Other nonempty underlyingType (e.g. EQUITY) is labelled OFFICIAL_NOT_COIN_TYPED_AT_T0. Missing source type is UNKNOWN. No name-based inferred issuer or crypto-G1 PASS.
3. Optional previously SAVED raw contractInfo receipt JSON with SHA256 and received_ms is checked for event origin claim as recorded, event E before receipt, bounded recorded receive lag, USD-M st=1 USDT perpetual and trading status; a T0 existing active symbol is an update, not a newly listed opportunity. Duplicated identical frames deduplicate, conflicting same symbol and event clock reject. A new candidate's timestamp is rounded FORWARD from its claimed received time to a subsequent minute; an event clock or onboardDate cannot backdate a buyable live observation. It can output Stage134-compatible RAW_UNVERIFIED_CANDIDATE rows and always retains all original full-market venue attempts. One-shot event samples never attest complete seven-day census or third-party network authenticity.
4. Tests: [seven Stage139 tests](../local-agent/scripts/test_monster_v4_stage139_official_t0_and_saved_contractinfo_evidence.py) and [offline CI workflow](../../.github/workflows/monster-stage139-official-asof-contract-info-offline.yml). Only push/PR/manual CI; no schedule or actual Binance live data requests.

## Actual CI, failures and correction

Initial run [#38605468465](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38605468465) failed one test. The fixture incorrectly assigned a single symbol+exchange-event-timestamp two contradictory contract statuses. Code correctly raised STAGE139_SAME_EVENT_CLOCK_CONFLICT. The test was repaired to use another symbol, NOT the validation gate; fix commit 1c50db381e0a3de716ee756d5919151fde9ecad8.

Repaired run [#38605546607](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38605546607) at above fix SHA: completed / success:
- Ubuntu job 115995347716: Python compile PASS, 7/7 offline tests PASS, no T0/default-network or schedule checks PASS.
- macOS job 115995347971: Python compile PASS, 7/7 offline tests PASS, same no live source/scheduler checks PASS.

Synthetic example used only for validation: 3 T0 USD-M USDT initial venue attempts including an explicit EQUITY and two UNKNOWN types; 2 distinct saved unverified trading-state symbols can produce 5 full Stage134 attempts, no initial symbols dropped. This is NOT an observation of real 2026 exchange listings, issuer confirmation, real trading liquidity, returns, or early-delivery performance.

## Business conclusion and next real priority

Stage139 finally preserves official provenance of the ambiguous tradeable universe and avoids upgrading archive first-candle time to live first-trading-status observation. But genuine full seven-day instrument-event coverage **cannot** be established by scattered user-triggered one-shot snapshots. Any live contractInfo capture would be a separate authorization and a different operating mode; this iteration did not enable one. The original D0 old-core ASCII limitation and warmup for first-listed candidates remain real model coverage blockers. Stage137/138 currently class these separately rather than pretend NO_WATCH or G1 PASS.

Original 2026-10-14 06:00 UTC Stage116 failed source remains SOURCE_FAILED_NO_BACKFILL; Stage118/127 strategy REJECTED, Stage132 early momentum BUY fixed exits NEGATIVE, 3 independently observed full future windows NOT_DONE, original Stage77 gates unchanged. The user-notional G4 net entry+exit and independent other-AI review are not done, and no Monster production permission has been granted.

STAGE139_ENGINEERING_CI=PASS_BOTH_OS; STAGE139_LIVE_MARKET=NOT_COLLECTED; NEW_STAGE133_REAL_T0=NOT_DONE; G0=PARTIAL; G1=NOT_SCORABLE; G2_G3=NOT_PASSED; G4=UNKNOWN; G5_INDEPENDENT_AI=NOT_DONE; G6_MAC=NO_GO; FRANK=UNCHANGED; GMAIL=OFF; NO_NEW_AUTOMATION.
