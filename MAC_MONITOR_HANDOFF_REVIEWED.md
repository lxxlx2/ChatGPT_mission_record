# Mac Monitor Reviewed Handoff

Canonical detailed document:
`crypto-300-profit-mission/MAC_MONITOR_FEASIBILITY_HANDOFF.md`

Status: **CONDITIONAL_GO / NOT_IMPLEMENTATION_READY**

This root-level file exists so reviewers/tools that cannot automatically traverse the subdirectory can still read the reviewed product constraints.

## Confirmed constraints

1. Mac-side collection/ETL is feasible. Ordinary Mac CPU/RAM/storage are not the primary risk.
2. GPT remains the final investment/semantic decision maker.
3. Current free ChatGPT automation means GPT final judgement is hourly; <=5 minute GPT judgement is not feasible without a different trigger/API or a non-GPT factual alert.
4. Current repository `lxxlx2/ChatGPT_mission_record` is PUBLIC. Sensitive runtime ingest/health/decision/delivery state must not be written here. Preferred design is a separate PRIVATE runtime repository.
5. SQLite is the local source of truth. GitHub is transport/audit, not the primary queue/database.
6. Solana source requirement remains `https://api.mainnet.solana.com` only. Before Frank backfill, probe newest/median/oldest target signatures. If old transactions are unavailable, full historical replay is NOT FEASIBLE under the no-fallback constraint.
7. Gmail exactly-once cannot be strictly guaranteed by search-Sent -> send -> readback. Stable event_id, fencing/lease, cooldown and DELIVERY_UNCERTAIN state are required. Product owner must choose AT_LEAST_ONCE vs AT_MOST_ONCE bias.
8. Local watchdog cannot detect complete Mac sleep/power-off by itself. External consumer must reject stale health using generated_at + valid_until + seq.
9. Binance current USDⓈ-M WebSocket endpoint/path rules must be read from current official docs. Binance migrated WebSocket base URL/path handling in 2026 and retired the old URL on 2026-04-23.
10. NFT broad X/social discovery is best-effort. Only configured deterministic sources may be part of a hard availability gate.
11. Replay and live must use the same canonical features. 1m-candle replay cannot validate tick-only rules.
12. Runtime data must carry batch_id, payload_sha256, item_count, generated_at and valid_until; GPT receipts must echo the input batch/hash.
13. Mac/GPT writers should not push the same runtime branch. Preferred PRIVATE runtime branches: `mac-data` and `gpt-data`.
14. GitHub health commits should be every 10–15 minutes or on state change, not every minute.
15. Untrusted NFT/social free text must be structured/truncated and explicitly treated as untrusted input to reduce prompt-injection risk.

## Revised risk-first development order

1. Synthetic E2E first: Mac fake event -> private GitHub -> GPT dry decision -> Gmail canary -> readback -> receipt.
2. Test scheduler recovery, hash receipts, ambiguous-send handling and duplicate replay.
3. CORE PRICE live + 30-day replay + shadow.
4. Frank public-RPC archival probe -> 500 tx -> history/live split.
5. Health/watchdog/sleep/reboot/failure injection.
6. Monster lightweight collector + historical/forward-shadow evaluation.
7. NFT deterministic sources, then best-effort discovery.
8. >=48h full-stack shadow.
9. Only after all gates pass may the existing `$300 Crypto资产状态监控` be considered for re-enable.

## Revised GPT shadow acceptance

- shadow >=48h
- scheduled consumer success >=95%
- zero silently lost pending events
- missed runs recover on a later cycle
- oldest pending <=2 nominal cycles during normal availability
- synthetic full-load test: 40 normal candidates + urgent + backlog
- compact input <=100KB
- no connector truncation
- receipt echoes batch_id + payload_sha256
- backlog does not grow for >2 consecutive cycles

## Decisions required before implementation

1. Is worst-case ~1 hour GPT judgement latency acceptable?
2. ACTION email policy: AT_LEAST_ONCE or AT_MOST_ONCE?
3. Is a separate PRIVATE GitHub runtime repository acceptable?
4. Keep Solana public RPC as the only RPC even if old Frank history is unavailable?
5. Accept NFT scope as deterministic known sources + best-effort discovery?
6. Must monitoring restart before macOS user login, or is post-login LaunchAgent acceptable?
7. Maximum local disk budget?
8. Is 48h shadow with >=95% GPT consumer-cycle success sufficient for production?

Until answered: **do not start full implementation and do not re-enable $300/Frank automation.**
