# Airdrop / TGE Canonical Registry

Updated: 2026-09-26

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
- humans& / @humansand
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
