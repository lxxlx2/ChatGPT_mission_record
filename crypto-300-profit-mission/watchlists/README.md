# Machine Watchlists and Models

Updated: 2026-10-04
Timezone: Asia/Bangkok

This directory stores compact rules/models and preserved monitor specifications. Presence of a watchlist file does **not** mean its runtime is currently enabled.

Current runtime authority is defined by:
- `../MISSION_SPEC.md`
- `../STATUS_SCOPE_2026-10-04.md`

## Current watchlist/runtime status

- Frank/Meme: live authority is **not** a watchlist here; it is the local deterministic `FRANK_LOCAL_SIGNAL_V1` policy/runtime under `../meme/`.
- NFT mint radar: `nft-mint-radar.md` specification is preserved, but current runtime status is **PAUSED / NOT ACTIVE**.
- Monster: old `monster-squeeze-v2.1.md` remains historical/model provenance; current authority is the frozen V3 research result in `../local-agent/PHASE_MONSTER_D1_V3_REDESIGN_REPORT.md`. Current Monster runtime is **NOT ACTIVE**.
- CORE PRICE / overall-market trend: **PAUSED**; legacy `$300 Crypto资产状态监控` is disabled.
- Other watchlists in this directory remain preserved rules/research unless a newer current Mission status explicitly marks them active.

Do not infer hourly coverage, Gmail delivery, or active monitoring merely because an older watchlist text describes such a schedule.

## Organization rule

Appropriate files here include compact machine rules/models such as:
- BTC regime rules;
- launch radar rules;
- NFT mint radar rules;
- Monster/squeeze model provenance;
- Robinhood/FOMO execution-flow rules;
- token-specific squeeze rules retained for future authorized runtimes.

Long-form project/token/NFT research belongs under `research/`.

When a watchlist contains substantial historical research, migrate that research incrementally and keep operational rules here only after a real monitor validation. Historical model files should be preserved rather than rewritten to pretend they are current runtime authority.
