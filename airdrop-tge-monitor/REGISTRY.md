# Airdrop / TGE Canonical Registry

Updated: 2026-10-08

Grass 与 Backpack 明确排除。

## Always-hourly urgent set

每小时都检查：
- Concrete / @ConcreteXYZ
- MetaMask / @MetaMask
- Claynosaurz / @Claynosaurz
- HEEBOO / @HeebooOfficial
- Space / @intodotspace
- 以及 state/current.md 中 deadline <= 7 days、已触发但未完成、KYC/claim/registration 正在开放的动态 urgent 项目。

Clay Shares 作为 Claynosaurz/HEEBOO 相关权益子项持续检查。

## Shard 0
- Block Stranding
- Base / @base
- OpenSea / @opensea
- Polymarket / @Polymarket
- StandX / @StandX_Official
- Perena / @perena
- TurboFlow / @TurboFlow_xyz
- MetaMask / @MetaMask
- Makina / @makinafi
- Rho / @Rho_Labs

## Shard 1
- Surf
- ForecastFDN / @ForecastFDN
- Hylo / @hylo_so
- OnRe / @onrefinance
- Reflect / @reflectmoney
- Tydro / @tydrohq
- Theo / @Theo_Network
- Neutrl / @neutrl_labs
- Concrete / @ConcreteXYZ

## Shard 2
- Relay / @RelayProtocol
- Titan / @Titan_Exchange
- Reya / @reya_xyz
- 01.xyz / 01 Exchange / @01Exchange
- N1 / @N1Chain
- Figure AI / @Figure_robot
- Pond / JoinPond / @JoinPond
- OhBabyGames / @OhBabyGames
- Claynosaurz / @Claynosaurz
- HEEBOO / @HeebooOfficial

## Shard 3
- Cambria / @playcambria
- Crusoe / @CrusoeAI
- Apptronik / @Apptronik
- Thalassa Robotics / Thalassa Inc.
- Fortytwo / @fortytwonetwork
- Space / @intodotspace
- 1X / @1x_tech
- Aalo Atomics / @AaloAtomics
- rTTOK / RepublicX / Republic / @joinrepublic

## Shard cadence

Asia/Bangkok hour modulo 4:
- hour % 4 == 0 → Shard 0
- hour % 4 == 1 → Shard 1
- hour % 4 == 2 → Shard 2
- hour % 4 == 3 → Shard 3

因此完整白名单最多约 4 小时刷新一次，urgent 项目每小时刷新。

## Identity

每个项目仍需 canonical identity tuple：
`project_id + canonical_name + official_x_handles + official_root_domains + known_tickers + known_chains + known_collision_names`

已知 hard-fail：Space (@intodotspace) 与 Spacecoin (@spacecoin) 永久分离。


## Deal-host / intermediary rights sources

For a project the user entered through a platform, SPV, syndicate or group lead, canonical project sources alone are insufficient.

Monitor both:
1. the underlying project;
2. the known user-facing deal host / SPV / syndicate / group lead.

Material rights events include:
- full or partial refund;
- deal cancellation / failed close;
- allocation increase/reduction;
- SPV or issuer substitution;
- SAFE/equity/token-warrant conversion changes;
- settlement/distribution;
- transfer or redemption window;
- material fee/valuation/term change.

A platform/intermediary notice can be a valid ACTION even when the underlying project posts nothing publicly.

Known mapping:
- 01.xyz / 01 Exchange -> preserve known Echo/intermediary deal-channel checks when user rights are affected.

Do not require a public project announcement to recognize a direct platform entitlement/refund notice.



## Formation / Orca / Loopscale TGE-scope resolution — 2026-10-08

- canonical_relationship: Orca (@orca_so) + Loopscale (@loopscale) combined into Formation (@formation_so) on 2026-10-08 Asia/Bangkok (announced 2026-10-07 19:00 ET).
- verified_token_network: existing ORCA and xORCA; no independently confirmed Formation token or separate Loopscale TGE from this announcement.
- scope_decision: remove independent Loopscale from Shard 1; Orca and Formation are NOT being added as new TGE watch entries. Treat the merger as a Crypto Daily protocol/governance event, not a TGE/action event.
- historical_state: retain past Loopscale monitoring/audit records. No claim, TGE, allocation, airdrop or new user entitlement is confirmed by this merger.
- user_instruction: no new automation/monitor. Do not continue independent TGE discovery of these two legacy names solely because of their merger; future user-specific rights/real token-launch scope needs separately verified first-party evidence and user authorization.
- relevant_existing_token_governance: Orca proposal published 2026-09-29 on fee split / treasury transfer / council changes; voting deadline 2026-10-10 19:42 UTC, cooldown until 2026-10-12 19:42 UTC. Proposal only, not yet proven passed/executed. Report via existing Crypto Daily governance lane, not TGE notification absent established user action.
- first_party_merger: https://www.prnewswire.com/news-releases/orca-and-loopscale-merge-to-build-capital-markets-for-ai-and-the-frontier-economy-302901726.html
- first_party_governance: https://forums.orca.so/t/tokenholder-proposal-resourcing-orca-for-its-next-phase/1281

## Closed / excluded deals

- Abstract / @AbstractChain — **USER_SUPPRESSED** on 2026-10-07. Remove Abstract/ABS from active TGE/airdrop monitoring, including hourly urgent checks, shard discovery and rights monitoring. Historical records remain for audit only. Reactivate only if the user explicitly asks to monitor Abstract/ABS again.

- humans& / @humansand — **CLOSED**. The user's Echo/Alpen Capital allocation was fully refunded on 2026-09-24. There is no remaining user entitlement or capital at risk in this deal. Exclude humans& and its Echo/Alpen deal channel from hourly shards, urgent checks and rights monitoring. Historical records remain for audit only. Reactivate only if the user explicitly enters a new humans& exposure or asks to monitor it again.


## Rights-source mapping requirement — 2026-09-29

Tier B user-rights evidence is valid only for an intermediary explicitly mapped in this registry.

A generic investor, news outlet, KOL, community moderator, aggregator, or unrelated platform is never a Tier B source.

When a deal is CLOSED/FULLY_REFUNDED, remove it from active discovery before network work where practical and persist the state in `state/known-events.md`.

Underlying-company financing/valuation announcements do not trigger a rights alert unless an explicitly mapped deal host/SPV/syndicate/group lead confirms a user-level allocation/term/fee/conversion/transfer/redemption/settlement/distribution impact.
