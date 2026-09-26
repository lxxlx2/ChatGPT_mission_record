# Crypto Automation Architecture

Updated: 2026-09-26
Timezone: Asia/Bangkok

The system deliberately uses the three existing Crypto automations only. Repository cleanup, QA and repair do not create additional monitors unless explicitly requested.

Human-facing navigation:
- `docs/MONITORING/README.md`

Repository structure / migration safety:
- `docs/REPOSITORY_STRUCTURE.md`

## Schedule

- :00 `Crypto 每日情报`
- :14 `全项目空投与TGE监控`
- :29 `$300 Crypto资产状态监控`
- 19:29 same $300 task also performs Monster factual daily summary

The legacy standalone Monster and Crypto publisher tasks stay disabled.

## Audit model

Current automatic runs use append-only audit files:

- `HHMMSS-start.md`
- `HHMMSS-final.md`

The final audit is the canonical proof of completion.

Historical pure-time audits are preserved as immutable records.

Temporary tool/source/GitHub/Gmail failures must not automatically pause or disable an existing task.

## Crypto Daily

Operational root:
- `crypto-daily/`

Authority:
- `crypto-daily/AUTOMATION_RUNTIME.md`

Ordinary hours:
- core market/security scan;
- one rotating discovery shard;
- compact research write;
- final audit;
- no Gmail.

09:00:
- delivery first;
- use prior stored research plus small fresh verification;
- Gmail/readback;
- GitHub archive/readback;
- avoid duplicate delivery.

10:00 / 11:00:
- recovery only for the missing side;
- then ordinary collection if appropriate.

## TGE

Operational root:
- `airdrop-tge-monitor/`

Authority:
- `airdrop-tge-monitor/AUTOMATION_RUNTIME.md`

Every :14:
- urgent set;
- one registry shard;
- candidate verification only when needed;
- fallback source for initial source_unavailable where possible;
- ACTION only for verified user-action events;
- NO_ACTION silent;
- append-only final audit.

## $300 Mission

Operational root:
- `crypto-300-profit-mission/`

Authority:
- `crypto-300-profit-mission/AUTOMATION_RUNTIME.md`

Every :29:
- direct-chain wallet state;
- stored PONS/XRP/ETH/JUMP thresholds;
- Token-2022 Solana holdings;
- BNB GSTOCK;
- Robinhood PONS;
- recent Crypto Daily research;
- Monster V2.1 bounded screen;
- launch/NFT/FOMO factual candidate state;
- slower UNICRED/Credits lane on cadence.

The automation is factual telemetry. It does not originate a new trade or change orders.

## Human research layer

Long-form content is organized separately:
- `research/projects/`
- `research/tokens/`
- `research/memes/`
- `research/nfts/`

Operational `positions/` and `watchlists/` should gradually become compact machine authorities. Research migration must preserve compatibility paths until real automatic runs validate the change.

## Data truth

Fresh wallet/RPC reads outrank old snapshots.

Private venue state remains USER_CONFIRMED until directly connected or refreshed.

Unknown/spam assets remain outside NAV.

No successful alert/report may be claimed without the persistence/readback required by its runtime.
