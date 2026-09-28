# Airdrop / TGE Canonical Registry

Updated: 2026-09-28

Grass 与 Backpack 明确排除。

## Always-hourly urgent set

每小时都检查：
- Concrete / @ConcreteXYZ
- MetaMask / @MetaMask
- Claynosaurz / @Claynosaurz
- HEEBOO / @HeebooOfficial
- Space / @intodotspace
- Solstice / @solsticefi — **ACTIVE RIGHTS INCIDENT**：Season 1 allocation 仍有 1,049.483713 SLX 权益争议，见下方专节
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
- Loopscale / @Loopscale
- Reflect / @reflectmoney
- Tydro / @tydrohq
- Theo / @Theo_Network
- Neutrl / @neutrl_labs
- Concrete / @ConcreteXYZ

## Shard 2
- Relay / @RelayProtocol
- Titan / @Titan_Exchange
- Abstract / @AbstractChain
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

## Solstice Season 1 rights incident

Canonical project:
- Solstice / @solsticefi
- domain: solstice.finance
- token: SLX
- chain: Solana
- SLX mint: `SLXdx4BUt2v9uJQNzWqSfzTJ9UKLUDsvxHFMEEdrfgq`
- user wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

Known user entitlement / incident state:
- Season 1 total allocation observed: 1,190.143139 SLX
- already received: 140.659426 SLX
- disputed/revoked vesting amount: 1,049.483713 SLX
- original vesting stream: `HJh9AWL5Z87n27Zq8gL3rNutSSeKg5DhViAFcHwcbeEB`
- original stream custody ATA: `BDuj2WsD1yTUuCXmZBoG6dQ5drUjf6Sgnrnmq8bHb2xx`
- vesting position NFT mint: `HnszSEkLMKzUNbkfErcDcPA7TXXmDKRoJWpNXGNfYDi7`
- project SLX vault ATA receiving the revoke: `9ibnEbGdYkyiX1QyZ8GxnEU94wut7M3cNk59gt5VEpks`
- vault owner: `3WWFtUpgKx8RDxxSayusmzWHy1HtC53fh2wnYMD22EuL`
- vesting program: `2sB4WkRwmkwNaidbRPFKzN2ZaV1enyajptupc4cMac4p`
- merkle distributor: `85F1bj5k85LZxzHM35epKtHD5E11HcYsxLpV8VbyT6od`
- user's stream was revoked by project-side Squads execution on 2026-09-11, tx `2GEN6SRCZruUNZVVnbmAUggGx3PVGyUZ6biupGRjsKRvQS17aSfsL1L4187ijWch3Z4UJYRyYuMA6nzzJxzRjMBA`
- original claim-status record remains relevant even though the old stream/custody were closed.

Hourly Solstice checks must be **delta-only** and focus on:
1. replacement stream / new claim route for the user's 1,049.483713 SLX;
2. claim page restoring the missing vesting allocation or showing a new unlock schedule;
3. official support / @solsticefi statement specifically addressing Season 1 vesting/claim remediation;
4. project vault `9ibn...` sending revoked SLX to a DEX, bridge, unlabeled intermediary, or known CEX/deposit cluster;
5. new project-side revoke/reissue transactions affecting similarly structured Season 1 streams;
6. material change to the user's vesting NFT / claim-status / replacement accounts.

Alert only on a confirmed material change. Ordinary Solstice marketing, Flares promotions, price moves, or unrelated protocol activity are NO_ACTION. A direct DEX swap or confirmed CEX deposit from the project vault is HIGH PRIORITY. A replacement stream or restored claim is ACTION.

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

## Closed / excluded deals

- humans& / @humansand — **CLOSED**. The user's Echo/Alpen Capital allocation was fully refunded on 2026-09-24. There is no remaining user entitlement or capital at risk in this deal. Exclude humans& and its Echo/Alpen deal channel from hourly shards, urgent checks and rights monitoring. Historical records remain for audit only. Reactivate only if the user explicitly enters a new humans& exposure or asks to monitor it again.
