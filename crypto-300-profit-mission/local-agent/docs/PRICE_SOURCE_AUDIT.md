# Official source audit — 2026-09-30

English official documents read on implementation day. Successful connection probe checked_at: 2026-09-30T05:59:09.321707+00:00. Private raw frames and immutable histories are outside Git in the Phase 3 evidence directory.

## Binance Spot public market data

- Documentation: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams ; https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints ; https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md ; https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/CHANGELOG.md .
- Actual REST: `https://data-api.binance.vision/api/v3/klines`; public GET, symbols BTCUSDT/ETHUSDT/SOLUSDT/BNBUSDT, interval=1m, UTC, limit=1000, weight=2. Server time: `/api/v3/time`. No API key.
- Actual WS: `wss://data-stream.binance.vision/stream` on port 443. JSON `{"method":"SUBSCRIBE","params":["btcusdt@kline_1m","ethusdt@kline_1m","solusdt@kline_1m","bnbusdt@kline_1m"],"id":1}`. Combined envelope data.k; finality uses k.x. One-minute kline update cadence documented as 2 seconds.
- Connection lifetime 24 hours; server ping every 20 seconds; matching pong payload required within one minute. websockets library answers server control-frame ping automatically. Limits: 5 incoming client messages/sec including ping/pong/subscriptions; 1024 streams/connection; 300 connection attempts/IP/5min. REST limits must additionally respect current server headers and 429; no claim of unlimited capacity.
- Current Spot documentation still specifies `/ws/<stream>` and `/stream?streams=...`, and explicit SUBSCRIBE on `/stream`. The 2026 derivative-market path migrations must not be applied to these Spot symbols. This endpoint choice is verified by the actual successful connection, not an assumed historical endpoint.
- Actual probe: PASS; 24 received frames, 23 market frames, 18.417 seconds including connection/close overhead. Actual history: 45 REST requests/asset, no missing minutes in downloaded range.
- Required collector recovery remains UNIMPLEMENTED after frozen-rule stop: controlled reconnect/resubscribe, overlap dedup, REST continuity repair, rotation before 24h. Probe duration does not test rotation/reconnect or freshness SLO.

## Hyperliquid HYPE perpetual public market data

- Documentation: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint ; https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket ; https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions ; https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/timeouts-and-heartbeats ; https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits .
- Actual REST: POST `https://api.hyperliquid.xyz/info`, `{"type":"candleSnapshot","req":{"coin":"HYPE","interval":"1m","startTime":0,"endTime":1790747819999}}`. Only current recent approximately 5000 candles available; no external backfill.
- Actual WS: `wss://api.hyperliquid.xyz/ws`; subscriptions `{"method":"subscribe","subscription":{"type":"candle","coin":"HYPE","interval":"1m"}}` and trades subscription with type=trades, coin=HYPE. HYPE instrument is perpetual; the other four instruments are Binance Spot USDT. Venue/quote differences are retained as provenance.
- Candle messages lack a Binance-style closed flag. Adapter treats every WS candle as provisional; source candle T is interval boundary, not reliable wall-clock freshness. A future collector must finalize with an official completed REST candle and use trade event timestamps for source age.
- No documented fixed 24h lifetime used. Idle disconnect requires an application JSON `{"method":"ping"}` within 60 seconds without received messages; planned interval 25 seconds, not implemented by the short probe. WebSocket protocol ping alone is not claimed to satisfy this requirement.
- Published limits: REST 1200 weighted requests/min; candleSnapshot base weight20 plus per60 candles; 10 WS connections, 30 new connections/min, 1000 subscriptions, 2000 sent messages/min. Respect future server limit responses.
- Actual probe: PASS; 30 received frames, 12 candle market frames, candle/trades/subscriptionResponse channels, 13.813 seconds including overhead. Actual REST history: 5041 completed canonical bars, one historical request, no unresolved gaps.
- Reconnect, snapshot recovery, continuity repair and forward accumulation remain NOT RUN / UNIMPLEMENTED after frozen-rule stop. Successful subscription alone does not prove continuous data.

## Reproduction and boundaries

Run explicitly from local-agent with PYTHONPATH=.: `scripts/price_source_probe.py --root <private evidence root>`; `scripts/price_history.py --root <private evidence root>/history`; `scripts/price_replay.py --root <private evidence root>`. Ordinary pytest uses injected responses and synthetic unit fixtures, never official network downloads. No Gmail, investment judgement or production runtime write occurs in these scripts.
