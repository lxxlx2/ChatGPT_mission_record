# Airdrop / TGE Monitor State (bounded materialized cache)
Last synchronized: 2026-11-06 18:04:09 Asia/Bangkok
Status: PARTIAL, verified_complete=false. This file is a compact convenience index, never completion evidence. Original append-only attempt/final records and state/known-events.md are authoritative. Last fully verified complete sweep remains **2026-10-10T07:52:16+07:00**; partial run must never advance it.

## Latest terminal
- authoritative_final: `airdrop-tge-monitor/runs/2026-11-06/180409-final.md`
- final_blob_sha: `1bade609b79f6b43b9a6b11f936a435262c60bb4`
- run_status: PARTIAL
- candidate_count: 1
- action_gate_pass: 0
- triggered_events: 0
- gmail_sent: false
- app_notification: false
- scheduled_shard: 2
- executed_shard: 2
- original_x_context: UNAVAILABLE
- completeness: Unverified original StandX DUSD issuer claim and user eligibility; other bounded-shard first-party source gaps remain

## Last meaningful per-shard attempts (PARTIAL_ONLY, not full coverage)
- shard0: 2026-11-06 16:04:42 Asia/Bangkok; `airdrop-tge-monitor/runs/2026-11-06/160442-final.md`; PARTIAL_ONLY
- shard1: 2026-11-06 13:59:54 Asia/Bangkok; `airdrop-tge-monitor/runs/2026-11-06/135954-final.md`; PARTIAL_ONLY
- shard2: 2026-11-06 18:04:09 Asia/Bangkok; `airdrop-tge-monitor/runs/2026-11-06/180409-final.md`; PARTIAL_ONLY
- shard3: 2026-11-06 15:00:36 Asia/Bangkok; `airdrop-tge-monitor/runs/2026-11-06/150036-final.md`; PARTIAL_ONLY

## Open urgent and eligibility state
- Always-hourly urgent5: Concrete, MetaMask, Claynosaurz, HEEBOO, Space @intodotspace. Dynamic Surf and StandX; full scope and four-shard groups remain defined by `REGISTRY.md`.
- `standx:dusd_claim_window_open:2026-11`: VERIFYING. Third-party archived copy of original social post alleges claim opened Nov2 00:00 UTC, closes Dec31 08:00 UTC; first-party post and wallet claim state remain SOURCE_GAP. Do not claim actionable user allocation or send before ACTION_GATE.
- Concrete additional USDC / private user claim: VERIFYING, issuer and user rights not independently confirmed; NO_ACTION.
- SurfBoard NFT claim through Nov13 and Cambria Base RSGP prior Oct29 were delivered previously; suppress unchanged. Other previous deliveries and lifecycle are in `state/known-events.md`.
- No verified new user-specific Tier A/B ACTION from latest terminal. No automatic Gmail should be generated solely because this cache is updated.
- Keep historical exclusions: user-suppressed Abstract; closed/refunded humans&; independent Grass, Backpack, Loopscale excluded per REGISTRY; no Space/Spacecoin or Theo/Autheo identity collision.

## History and runtime contract
- This file was compacted from former append-heavy cache with original blob SHA `be7fec5d2c130faeee0dca2b457c8d991bfefe24` (219658 UTF-8 characters); previous version remains retrievable from Git history. All per-hour source receipts and results remain in `airdrop-tge-monitor/runs/YYYY-MM-DD/HHMMSS-final.md` or `final-retry.md`. Do not synthesize prior completions from this index.
- Replace this cache in place with only latest verified terminal, last partial attempt per shard, unresolved user-rights candidates and stable dedupe pointers; DO NOT append each prior hourly terminal in full. Preserve Git historical blob on the next write and use optimistic sha compare-and-swap. The optional cache must never block actual ACTION verification, final write, or authorized Gmail.
- Task ID, schedule, scope, email-only rule and source evidence gates stay unchanged.
