# Stage124 — reproducible manual full-market snapshot comparison (frozen before Oct28)

Date: 2026-10-14 Asia/Bangkok. User has selected only **chat-triggered public market data collection** for future Monster snapshots and requested all automatic Stage99 launchd tasks be stopped locally. Explicit manual cadence: [MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md](MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md).

## Problem solved

Stage123 already saved complete connected Binance data: a baseline at `2026-10-14T09:48:24.840Z`, 927 full exchangeInfo symbols, 525 active USDT perps, each of 525 had 24h/BBO/mark. Oct28/Nov11 user requests should immediately produce the same full artifacts and a **consistent market-wide, venue+symbol-aligned comparison**, not hand-picked top gainers or a manually overwritten spreadsheet. A future manual request may happen after 13:00 Bangkok; exact source times must always win over the calendar reference.

## Frozen implementation/acceptance

- Pure local stdlib, read-only offline CLI with `--manifest` and optional `--previous-manifest`. Never accesses Binance network, Mac LaunchAgents, scheduled jobs, real trading or Gmail.
- Read only the eight file paths listed in that manifest, under the exact Monster evidence directory. Preserve all five original segmented exchangeInfo parts, plus original complete ticker24h/BBO/mark source records. Assert exact batch UTC, symbol uniqueness and all population count identities; assert active `TRADING + PERPETUAL + USDT` set and source coverage. Do not infer that missing BBO is zero volume or that unknown symbols are losses.
- Keep exact Unicode venue symbols; never strip multipliers such as 1000/1000000. Distinguish price-change rolling24h and *later-to-earlier mark-price* change, plus funding and BBO spread data. No network-persisted value can be used as a later event before its actual source timestamp; report source event min/max and batch staleness if present.
- Full 525-bucket distribution for rolling24h price/turnover/spread, including negative and no-change; top movers are only descriptive. All market samples remain saved for independent audit.
- If a previous MANUAL snapshot is supplied: compute paired **same USD-M venue+exact symbol** mark-to-mark observed gross price proxy with true delta-hours between distinct capture batches, retained/newly-active/absent sets and missing-price/censor counts. A two-week change is NOT D0 predictive hit rate, realized profit, order-book liquidity or reliable as-of crypto identity.
- CI must verify original Stage123 actual full file population (927 and 525) on macOS and Ubuntu, and use a second **synthetic** snapshot to test pairing, new listings, missing quote, Unicode and no fabricated forward event. Generate original Stage123 machine summary with a Git commit, mark `NEW_OOS=NOT_DONE`, `REAL_NET=UNKNOWN`, `MONSTER_NO_GO`.
- This is core evidence processing so subsequent user-triggered sampling can proceed in a single conversation with actual Git outputs, independently of Stage99 and without waiting for fixed clock times.

`STRATEGY_STAGE118=REJECTED`; `REAL_USDM_G0_CRYPTO=PARTIAL`; `REAL_G4_NET=UNKNOWN`; `THREE_FROZEN_STAGE105_OOS=NOT_DONE`; `STAGE99_AUTOMATIC_COLLECTION=CANCEL_REQUESTED_NOT_YET_VERIFIED`; `NO_CHATGPT_AUTOMATION`.
