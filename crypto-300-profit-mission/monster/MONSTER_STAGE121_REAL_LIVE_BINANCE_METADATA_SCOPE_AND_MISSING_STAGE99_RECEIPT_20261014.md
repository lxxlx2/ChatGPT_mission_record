# Monster Stage121 — first Stage99 as-of source missing; independently examined LIVE Binance exchangeInfo structure

Date checked: 2026-10-14 Asia/Bangkok. Original Draft PR #30. Purpose: deal with the real source blocker and exercise the full-market trade-rule structural assumptions without pretending to reconstruct a lost point-in-time snapshot or a profitable strategy.

## 1. Frozen Stage99 result — absence is a verified remote fact, cause is UNKNOWN

User-authorized macOS Stage99 source collector previously installed on 2026-10-13 (original real user terminal receipt `evidence/monster_stage107_user_mac_stage99_install_receipt_20261013.md`), first one-shot scheduled local Bangkok Oct 14 at 12:48, 06:00 UTC window. The original frozen remote evidence filename from the **actual reviewed Stage99 runtime code** is:

`crypto-300-profit-mission/monster/evidence/monster_stage97_point_in_time_usdm_2026-10-14_raw_https.json`

At this Stage121 remote inspection after the 06:00 UTC window started, the GitHub remote branch `research/monster-v4-local-discovery-20261010` **does not contain that exact file**. Directory was inspected directly, 316 entries, and GitHub commit search for original source archive reported no matching commit. Remote upload is therefore `NOT_VERIFIED`, but we cannot decide remotely between Mac slept/launchd skipped, script stopped before capture, Binance HTTPS failed, capture saved locally but Git push failed, or a later local auto-unload error. Do not claim a specific failure without the actual local state.

Original `monster_v4_stage99_mac_launchd_one_shot.py` has a tested read-only `status` subcommand, per-window JSON state and separate launchd stdout/stderr paths. Its **existing** `retry-push --window 2026-10-14T06:00:00Z` can re-upload original byte-identical saved evidence ONLY when state and SHA prove the capture exists. This must not be run blindly, and the authorization for a new capture at a past time DOES NOT exist. Read-only local status/log evidence is the **only** pending user Mac fact needed if no upload appears. Never replace it with today's exchangeInfo.

## 2. Real connected Binance native current exchangeInfo structure (NOT frozen 06:00 UTC snapshot)

Read-only source: connected Binance native public endpoint `get_futures_usds_exchange_information` (USD-M current exchange trading rules, corresponding official /fapi/v1/exchangeInfo). Native response `serverTime=1791968914198` (2026-10-14 09:08:34.198 UTC = 16:08:34.198 Bangkok). This native connector supplied normalized structured JSON, **not** the original Stage97 raw TLS body, two Binance /time receipts or source-byte SHA. Therefore it is a **current descriptive sanity check only**, not an archive acceptable for Stage105 frozen as-of capture, G0 pass or new OOS.

Actual read-only structural counts for that time:

| Exact structural category | Original current Binance response |
|---|---:|
| All exchangeInfo symbol entries including inactive/delivery/other quotes | 927 |
| TRADING + PERPETUAL + USDT quote | 525 |
| Within those, `underlyingType=COIN` (exchange label, **not independent token identity**) | 523 |
| Within those, `underlyingType=INDEX` | 2 |
| Two index symbols | `BTCDOMUSDT`, `ALLUSDT` |
| Active USDT perpetual symbols with `PRICE_FILTER`, `LOT_SIZE`, `MARKET_LOT_SIZE`, `MIN_NOTIONAL` | 525 / 525 |
| Active USDT perpetual symbols with `NOTIONAL` additionally | 0 / 525 (alternative expected contract) |
| Active symbols beginning literal `1000` or `1000000` | 11 |
| Active contracts with Binance `underlyingSubType` containing `Crypto` | 524 / 525 |
| Active contract without any exchange `underlyingSubType` values | 1: `CTUSDT` |

The 11 prefixed symbols include `1000SHIBUSDT`, `1000XECUSDT`, `1000LUNCUSDT`, `1000PEPEUSDT`, `1000FLOKIUSDT`, `1000BONKUSDT`, `1000SATSUSDT`, `1000RATSUSDT`, `1000CATUSDT`, `1000000MOGUSDT`, `1000CHEEMSUSDT`. Prefix is not independent contract unit proof. The two `INDEX` symbols both declare `underlyingSubType=["Index","Crypto"]`; `INDEX` does not imply TradFi by itself. The active `COIN` group is not independently issuer-verified merely due to Binance field.

Stage120 was extended at commit `b850a801ecf3fdda47826750d334454423b6d188` to retain the **exchange's own Crypto subtype assertion** as a distinct evidence grade from independent issuer confirmation. This avoids throwing away available exchange information without incorrectly upgrading a Binance category label to `G0_CRYPTO_CONFIRMED`.

Schema cross-check: Stage120 predeclared rules `LOT_SIZE`, `MARKET_LOT_SIZE`, `PRICE_FILTER`, and `MIN_NOTIONAL` match all 525 currently active USD-M USDT PERPETUAL instruments; no disabled/missing essential filters were detected in this particular **live** response. Do not extrapolate live current filters to old 2025–2026 original 519 cases or 2026-10-14 06:00 UTC frozen population.

## 3. Immediate business implication / research priorities

- A true current USD-M count **is not** a point-in-time crypto-only sample. Stage120 metadata format coverage is useful, but it does not repair G0's independent crypto issuer/multiplier/unit identity or a real at-signal book/mark/fee price.
- Stage118's frozen actual historical first D0 strategy remains `REJECTED`: 18/28 original early5 major GT2 opportunities; 183 events/42 days, 24h gross price-only median -3.919125% in 161 complete; no executable net evidence. Do not announce this current 525 USD-M list as a new profitable strategy.
- No daily first forward window analysis can be final until its full seven-day 1m source is available and all three frozen windows are checked. If a valid Oct14 Stage99 as-of source was never actually saved, **mark the first window unverified/censored**, do not silently move its date to Oct15 or use later snapshots.
- The next productive unblock action is to inspect ONLY existing Stage99 local state and original source-file SHA. If `GIT_UPLOAD_FAILED_RETRYABLE`, the existing reviewed `retry-push` mechanism preserves source authenticity. If `SOURCE_FAILED_NO_BACKFILL` or `MISSED_WINDOW_NO_BACKFILL`, preserve this negative original window and keep work on Stage116 replay/instrument identity without filling losses as zeros.

`STAGE121_REMOTE_OCT14_STAGE99_SNAPSHOT=NOT_FOUND`; `STAGE121_MISSING_CAUSE=UNKNOWN`; `STAGE121_LIVE_EXCHANGEINFO_RULE_COVERAGE=DESCRIPTIVE_VERIFIED_CURRENT`; `STAGE121_LIVE_DATA_AS_FROZEN_SOURCE=FORBIDDEN`; `STAGE118_STRATEGY=REJECTED`; `G0_CRYPTO_IDENTITY=PARTIAL`; `G4_TRUE_EXECUTABLE_NET=UNKNOWN`; `THREE_WINDOW_OOS=NOT_DONE`; `OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `FRANK=UNCHANGED`; `STAGE99_EXISTING_TASKS_UNCHANGED`; `GMAIL_AND_AUTOTRADE=OFF`.
