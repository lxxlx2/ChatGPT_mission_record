# Frank G0-B 2026-10-28 — one-shot, free, historical-price feasibility

**Authorization:** owner explicitly permits ONE execution of at most 50 public GeckoTerminal GET requests, no faster than 5 calls/minute, no credentials, no fees, no production reads/writes, no ongoing monitor, no live trading.

## Frozen inputs and preregistered selection

G0-A fixed approved PR117 source HEAD `817839b743752f76138c233786a509c0df9e9fd9`; public archived M3 study blob `a31a2bbcd1fe7c70951152f2a23edca6c934dc40` only. The manifest is assembled and SHA256-locked **before** any API call. Twelve distinct mints, one episode per mint. First 4 chronological episodes whose M3 frozen model emitted MULT (T0 = earliest ACC or MULT for that episode); first 4 chronological ACC-only; first 4 chronological unique recovered active BUY episodes from archived COMPLEX cases that never emitted an ACC/MULT signal. The control selection comes from a *recovered UNKNOWN trade subset* and is NOT statistically representative of all 166 no-signal episodes. No outcomes are used to select episodes.

| ID | Kind | T0 (UTC) | Mint |
|---|---|---|---|
| M1 | MULT | 2026-09-05 21:00:55 | MukLDtJ8Cx9DxLbeyLRSWPSposTMWuwHANbuaudpump |
| M2 | MULT | 2026-09-06 19:34:08 | HcRLc9VDgjLeK154xDawfb1dmVJ98DoSqcwTHGqiDeJR |
| M3 | MULT | 2026-09-12 16:37:15 | PerPsCe2SJ7Q25CN4R5TTX4fmBdmknE2hQmqCt96fHL |
| M4 | MULT | 2026-09-14 16:45:27 | Hg5Ja55T5wESq4vyFoiVCMeHXtGyVA69X2UHq8hgpump |
| A1 | ACC-only | 2026-09-06 02:28:38 | 6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx |
| A2 | ACC-only | 2026-09-08 02:42:17 | 8K5X85PAJHAAVSvYaAzgVPPAPsqqHmvx16ZyBiscYF8L |
| A3 | ACC-only | 2026-09-11 03:24:02 | E4Ap4icMLwKot8rkkTbq5JkS5kZxt5XCE3yfxbzYBjHx |
| A4 | ACC-only | 2026-09-11 20:56:02 | 4MMQY9bwkxxTtsK3W227Q5ABT6yFY8Pmn9Ze7wmAXKY8 |
| C1 | recovered no-signal | 2026-09-03 21:04:02 | Ax5dAamJPeuaLpFUzs9FdcpoUhHDcxyjPzxCJQidjups |
| C2 | recovered no-signal | 2026-09-07 18:40:48 | 3GXtoGmXaZHYEASkeDxejdrSWpeqqRWxCdzUVAagpump |
| C3 | recovered no-signal | 2026-09-08 17:18:20 | H1kXUqEPkQNNeNjGNN5tuHf3nsQK2vB1jUA9c4RggpUf |
| C4 | recovered no-signal | 2026-09-09 01:41:58 | 4ajeoXCv352quoiH26neS2JuKRgwv9mkDsM2o6Axpump |

## Guarded official API requests

Only `https://api.geckoterminal.com/api/v2/networks/solana/tokens/{mint}/pools?page=1` (max 12 attempts) and `https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}/ohlcv/minute` (max 24 normally, 1-min aggregation with bounded before_timestamp and limit). Strict total max 50 **attempts**; monotonic ≥12.5 seconds between them; no retries, redirects, paid API, user account, provider secrets or external RPC. First-page current pool ranking is a survivorship-biased sample: take the earliest created-before-T0 SOL/USDC pool found, with exact base/quote mint identity; never infer this was the historical best executable route.

Targets: delayed 30/120/300/900/3600 seconds from frozen T0 and 24-hour fixed-price horizon. First candle starting on/after target is a **future-known** 1-minute candle-close proxy; lookahead in seconds is reported. Missing/zero-volume candles are missing, never free fills. Illustrative 2% round-trip scenario is sensitivity, not verified actual fees. There is no order sizing or actual executable quote.

Stop on HTTP 429, permission/key/paywall, provider redirects, unexpected server errors, excess size, network failure, malformed response or 50 HTTP attempts. No re-execution without new approval.

## Reproducible code and output

- `g0b_gecko_one_shot.py` defaults to offline selection; only explicit `--execute --max-http 50` may make Gecko public GET requests.
- `test_g0b_gecko_one_shot.py` never uses the network.
- GitHub Actions workflow creation is the single run trigger: *only one path-filtered push event on this fixed research branch*. No schedule, no recurring dispatch.
- Output `g0b_public_receipts.json` in a GitHub Actions artifact and summary lines `G0B_RESEARCH_SUMMARY_JSON` / `G0B_EPISODE_JSON` in job logs; no private evidence, source database, local secrets, account signing or production changes.
- Feasibility threshold from PR117 comment: at least 6/8 signal and 3/4 control episodes with valid T0/1h/24h proxy coverage to consider expanding research; even if crossed, strategy verdict remains NEED_MORE_DATA until precommitted independent G0-B/G4 evidence exists.

**The run is not approval for a second scan, 30-day standing forward monitor, trading, delivery, F3/production changes or deployment.**
