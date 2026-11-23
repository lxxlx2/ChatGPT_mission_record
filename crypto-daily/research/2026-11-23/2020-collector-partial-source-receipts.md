# 2026-11-23 20:20 collector source receipts (Asia/Bangkok)

Status: PARTIAL_SOURCE_GAPS; RESEARCH_ONLY; NOT_READY_FOR_SEND. This is a bounded collector pass after today's verified Gmail Sent, not a new daily edition.

## Delivery idempotency
Gmail Sent search (life account, in:sent after:2026/11/22 before:2026/11/25) returned 2026-11-23 Crypto Daily message 1a206fec44c5cfa7, to lxx.run688@gmail.com. No new mail sent. Canonical claimed by prior run: reports/daily/2026/2026-11/2026-11-23.md; canonical exact-body readback NOT independently repeated in this run. Monthly October previously delivered; no new monthly send.

## Current main rule blob SHA receipts
PIPELINE_CONTRACT.md 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9
REPORT_SPEC.md 2e70414c8fdb8d23a292cc3bf7797425a403e179
state/daily-event-ledger.json 0b4acf861b4a8a755759b5c6ab3d2cf5469609b1
Other six Git rule documents fetched in same call, but full source review and independent executable QA not proven. No CI claim.

## Market official Binance read at approx 2026-11-23 20:20 ICT
Source https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT and matching individual symbols via connected Binance public spot endpoint:
BTCUSDT 61249.56; ETHUSDT 1722.94; SOLUSDT 72.44; BNBUSDT 556.06; HYPEUSDT 64.11; USDCUSDT 1.00104. Timestamp: run window, endpoint responses do not include exchange server timestamp. Multi-symbol call failed HTTP 400 duplicate parameter; individual single-symbol calls succeeded.
Official futures source https://fapi.binance.com/fapi/v1/premiumIndex : BTC mark 61204.20, funding 0.00003327; ETH mark 1721.61117, funding -0.00004668; SOL mark 72.37030904, funding -0.00010893; exchange timestamp 1795439982000 ms UTC. Funding rates are not annualized.

## News discovery and source gaps
Checked 2026-11-23 ~20:20 ICT. https://www.binance.com/en/support/announcement returned current listing with November 20 notices; no independently validated November 23 high impact delta. https://github.com/laravel/framework/security/advisories lists Nov11 signed-URL advisories; no new Nov23 announcement proven. https://help.galxe.com/en/articles/18361711-galxe-is-integrating-into-gravity-what-you-need-to-know confirms already-delivered Nov9 Galxe exit and Dec5/Dec15 deadlines, SAME MATERIAL_VERSION, EXCLUDE duplicate. https://farside.co.uk/btc/ , https://farside.co.uk/eth/ , https://farside.co.uk/sol/ require direct final trading-day read; search results were conflicting/partial. Secondary https://mobee.com/en/mobee-academy/market-update/market-news-this-week reports 16-20 Nov BTC ETF -1.245bn and ETH -221.7m but not promoted to verified first-party Farside figures.
https://www.reuters.com/business/binance-says-it-has-court-order-get-back-crypto-frozen-after-63-billion-heist-2026-11-18/ reports Nov18 court freeze; prior event family and novelty not rechecked against seven full Sent bodies, EXCLUDE pending verification.
Official issuer checks for six security lanes, Arkham/Lookonchain raw TX, SEC/Fed, Tether/Circle reserves, ACTIVE projects and Anthropic venue IPO access were NOT exhaustively completed this pass; each is SOURCE_GAP_NOT_CHECKED rather than 'no news'. X browser session not checked, BROWSER_SESSION_UNAVAILABLE_NOT_PROVEN. No new material event has passed family novelty gate. No separate TGE or app notice.

## Execution
Only bounded partial research. No report QA, no Gmail send, no new task, timer, process or paid API. Retain source gaps for next normal collector/prebuild.
