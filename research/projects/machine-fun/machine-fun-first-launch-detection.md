# Machine.fun 首批代币发行的提前发现与通知技术可行性

Updated: 2026-10-29 Asia/Bangkok  
Status: `RESEARCH_FEASIBLE / LIVE_DETECTOR_NOT_DEPLOYED / NO_NEW_MONITOR_AUTHORITY`  
Scope: Machine.fun 平台级新币发现；不优先绑定 Sixth Sense Labs / SXTH。  
Source baseline: Mission `main` commit `7ca9c2e4a98a9418b112341e08ca0b0622bbc0c8`; existing SXTH case `research/projects/sxth/sxth-sixth-sense-labs-machine-foundry.md`.  
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `MISSION_SPEC.md`, root `AGENTS.md` and `docs/DEVELOPMENT_RULES.md`.

## 1. Actual user objective and decision

The user wants to **discover and be notified of the first onchain token launches on Machine.fun as early as possible**, independently of whether SXTH is first or attractive. Priority is launch discovery, attribution, latency and notification; no buy/valuation decision in scope. Do not substitute SXTH tokenomics or an ICO report for the platform-discovery requirement.

**Feasibility decision: YES for targeted onchain issuance-event discovery under a known PlatformConfig; NO guarantee of the first officially endorsed / publicly accessible Machine.fun token or guaranteed sub-second delivery.** Real-time notification is **not currently deployed or tested**. No perpetual monitoring may be claimed from this interactive research.

## 2. Independently observed Solana anchors

Direct read-only Solana-mainnet Alchemy RPC on 2026-10-29 reconfirmed two current, 429-byte Raydium LaunchLab-owned `PoolState` accounts. Decoded using official `raydium-sdk-V2/src/raydium/launchpad/layout.ts` field order, at RPC slot 462574047:

| Record | Pool | Mint | Pool creator | PlatformConfig | Status at read |
| --- | --- | --- | --- | --- | --- |
| Earlier disputed launch | `Ehb92xLBJVAshcbwfMVYgWnQ8oeKJeeqdPR4HNFn6d9J` | `sYUJLvHEVQofSBehcUQiYLZA967BLqX8CZbUdCWMACH` | `7LJoZL5GHDmJoxczmM1P1hzrARCUWa7uyxVT5jBwsd9d` | `3hVbfgB77tL1qDKhtMQoe4Gv7qPN2dGmKpD2KxWP2sPb` | 2 |
| Later identified MACHINE | `3VV43iWWPUe7o9QAkBHzGdu8rezpcZGYGK3WyytqPdAt` | `3m4MAtoeJ1LA82peNBmzP3FGfbzpAxVqZj6ch5xtPcQc` | `8HVQQRJiHji5JwFDpFEtsPWD5M42yyiA4Tkh8Ggryw8s` | Same exact `3hVb...` | 0 |

The referenced PlatformConfig is a 944-byte LaunchLab-owned account, `3hVbfgB77tL1qDKhtMQoe4Gv7qPN2dGmKpD2KxWP2sPb`. First-party/corporate custody is not cryptographically established just by editable brand name and website. Previous documented exact onchain evidence:

- 2026-10-28 01:33:59 Bangkok: Squads execution signature `3icZstcFh86CCA2QebiAyJjtzJvwDtjXu2XpVYo8a7fq5KL6AdJNWLYrjKhxQATiYE67CCLGWWfuMgeuRLNThRJN`, `MACHX` CPI and Raydium CreatePlatformConfig. This was **18h44m20s before** the earlier disputed creation transaction.
- 2026-10-28 20:18:19 Bangkok: disputed launch signature `XSsPNb1TM8J7rEsWgr9ujus6TABVx45UhqaARaN454LWhr9qwM3aJg5qELDGzV9LNYimk1bShPpaeuKWLA2nmXE` on the same config; not a canonical SXTH mint and not proven formally endorsed Machine.fun production launch.
- 2026-10-28 22:34 Bangkok: `MACHX97ggsHjPyrZErp5mGr7uq5jVmqgCnN7Hd2213g` program-close transaction `4k7Hdv7diFSxAc9SUWT6NPnN2z5WCdLvirvBPLv66GFFrsf1H47vnL3Lcfub8JwsFh5bBwZKXsBriimBzJDzcLvL`. Do **not** use the closed custom program as the only future watcher.
- Latest successful transaction found in direct `getSignaturesForAddress` on this PlatformConfig, 2026-10-28 23:51:41 Bangkok, signature `3pcmk9tZvmv9af9TM2woCQRXgWiL2RsSK7PyNruWi3U2EFhj8br8PvE2nqjAZAQdoLcV32p6Q55aKRR6sSqKKZdr`, was a MACHINE swap, **not** proof the mint was first created at that time. Query was a bounded exact-address read, not exhaustive all-platform launch enumeration.

**Identity boundary:** matching this exact PlatformConfig is strong onchain venue association but not standalone proof of platform legal ownership, first curated Foundry selection, issuer endorsement or no test launches. It is not safe to say that the first launch from this config must be the first officially endorsed project. Permissionless launches may include test, spoof or unrelated mints. Different config or separate platform backend is possible.

## 3. Website and API inspection (bounded)

- Directly read `https://machine.fun/` through connected user browser and current web lookup: Phase 1 Foundry applications and Phase 2 `LOADING`; no rendered token listing, live order list, authoritative issuer mint map, launch queue or visible authenticated purchase UI.
- `https://foundry.machine.fun/` is a founders' application form, not a launch-feed API. No public shortlisted first cohort / mint roster was returned.
- Attempted read-only public URL probes for `https://app.machine.fun/`, `https://api.machine.fun/`, `https://machine.fun/api/`, `https://machine.fun/api/launches`, `https://machine.fun/launch`, `https://machine.fun/robots`, `https://machine.fun/robots.txt`, `https://machine.fun/sitemap.xml`; the available web reader returned inaccessible/internal errors. **These are inconclusive.** They do not establish HTTP 404, absent DNS, lack of a private or unindexed backend, or availability of a working API. We did **not** capture browser network requests, download raw JS bundles, probe protected endpoints, or access private registration data.
- The official Raydium SDK and documentation **do** expose usable read surfaces independent of Machine.fun frontend: `https://launch-mint-v1.raydium.io` (indexed LaunchLab mint metadata and search), `https://launch-history-v1.raydium.io` (historical swaps), `https://api-v3.raydium.io` (pool/mint metadata). SDK source contains documented `GET /main/configs` on the launch-mint host. Endpoint response was **not live-tested in this pass** and indexed publication may lag the original chain slot. Treat as enrichment and backfill, not the primary earliest-signal trigger.
- Sources: https://github.com/raydium-io/raydium-sdk-V2/blob/master/src/api/api.ts ; https://github.com/raydium-io/raydium-docs-v1/blob/main/sdk-api/rest-api.mdx ; https://machine.fun/ ; https://foundry.machine.fun/ .

## 4. Actionable event detection design

**Primary exact-config listener (strongest current path):**

1. Once separately authorized to deploy, use the existing Alchemy Solana read-only connection's documented WebSocket PubSub `logsSubscribe` with `{"mentions":["3hVbfgB77tL1qDKhtMQoe4Gv7qPN2dGmKpD2KxWP2sPb"]}`, initial `confirmed` commitment for latency, not every program/ticker across Solana.
2. For each successful new signature, fetch `getTransaction`, including versioned account keys, loaded addresses and inner CPI. Require actual **Raydium LaunchLab** `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj` `InitializeV2` (`4399af27da102620`) or `InitializeWithToken2022` (`25be7ede2c9aab11`). Validate exact platform config account in the create call, new `PoolState.platformId`, base mint, quote mint, creator, status and success. Ignore mere swaps, failed 111 transactions, name matches or fee claims.
3. Persist a durable deduplicated (signature, pool, mint, slot) cursor. Reconcile confirmed events once finalized. After WS disconnect restart, backfill `getSignaturesForAddress` with bounded pagination + recorded last finalized cursor; persist uncovered interval as explicit **coverage gap** rather than silently treating zero notifications as zero launches.
4. Send an event-only `CHAIN_PLATFORM_CANDIDATE` alert containing mint, pool, creator, chain signature, local time, first observed slot and **unverified issuer/official-launch flag**. Later send a **separate substantive upgrade** to `OFFICIALLY_ENDORSED` only with authentic platform/issuer mint binding; do not repeatedly notify identical mints just to prove a loop is running.

**Secondary identity/config rotation safety net:**

- Track known Squads and operational administration addresses, `PlatformConfig` creation/update transactions and first-party Machine.fun/CodecFlow/peaq/Raydium platform deployment announcements in bounded, source-backed research. The historical `MACHX` was closed; it cannot serve as the only forward factory ID.
- For coverage of any **new unknown config**, bounded scan of LaunchLab initialize events by program with exact transaction decoding and platform admin / custody continuity is technically possible but may be far more expensive. Default to a limited research discovery lane, no unapproved network-wide subscription or upgraded Alchemy plan.
- A live web launch API, if later published, can enrich `OFFICIALLY_ENDORSED` status; do not wait for its index to send a marked candidate chain alert.

## 5. Latency, what is and is not guaranteed

- **Feasible**: a live, connected and authorized WS subscriber can trigger on the launch's confirmed transaction; the official LaunchLab initialize instructions **include** `platform_config` in the ordered account list. An exact-config subscription avoids discovering the CA in advance. Official docs: https://github.com/raydium-io/raydium-docs-v1/blob/main/products/launchlab/instructions.mdx ; https://www.alchemy.com/docs/reference/logs-subscribe .
- **Not demonstrated**: successful WS subscription on the user's Mac, actual delivery latency, notification readback, uninterrupted WS uptime, complete historical first-token enumeration, future new-config coverage or official issuer identity. No quantitative seconds guarantee without an actual end-to-end Mac acceptance test.
- **Inherent limits**: a reactive chain alert cannot precede bundled first-slot snipers already included in the same launch slot; a new platform config may not be observed beforehand; false assumptions about the selected official first project are unsafe.
- **Critical distinction**: an initial “we detected a real mint under a Machine-branded config” alert **can be earlier** than platform announcements, while “the official platform launch is authenticated” may follow later. State both explicitly rather than suppressing the earlier event.

## 6. Current authorization and required acceptance

Current state `RESEARCH_ONLY`. No new task, scheduler, LaunchAgent, external paid subscription, live notifier, Gmail change, wallet access, trading or Mac deployment was created or authorized by this document. Existing Mission production trading remains `NO_GO`.

Before claiming timely notifications: develop a minimal read-only listener within the repository according to GitHub-first rules; offline replay the two known historical pools and negative controls (failed swaps, unrelated platform config, duplicate signature, address spoof, network gap); freeze explicit alert rules; obtain independent fixed-SHA review; get **separate user authorization** for running an always-on process and any actual Gmail notification integration; perform real read-only Mac WS/notification tests with delivery readback. Do not use the existing hourly TGE job as if it guarantees first-slot latency.

**Decision:** `YES_KNOWN_CONFIG_FIRST_LAUNCH_DETECTION_TECHNICALLY_FEASIBLE / FIRST_OFFICIAL_COIN_NOT_GUARANTEED / MACHINE_WEBSITE_PUBLIC_LAUNCH_API_UNVERIFIED / LIVE_DELIVERY_NOT_ENABLED`. No token preference or investment decision asserted.

## 2026-10-29 explicit authorization update (supersedes section 6's install prohibition)

The user explicitly approved a **Machine.fun-only background process on their own Mac**, with Gmail alerts reusing Frank's pre-existing Google OAuth, and Alchemy Solana RPC reuse without reconfiguration where already available. This supersedes the prior research-only assumption **for a one-time local installation of this independent module only**. No authorization extends to Frank modifications, wallet/trades, broad market scans, unrelated monitors, Google scope expansion, or GitHub Actions schedules.

Implementation on PR #243 is in `research/projects/machine-fun/detector/`: isolated `install_machine_fun_background.sh`, `machine_fun_service.py`, `machine_fun_runtime.py`, `machine_launch_gmail.py`, tests and README. The first install is allowed to create exactly one user-level `~/Library/LaunchAgents/com.<username>.machine-fun-first-launch.plist`, with LaunchAgent `RunAtLoad` + nonzero-exit KeepAlive; no terminal must stay open. Installer checks existing credentials and runs 35 synthetic and loopback tests before loading service; a failed check leaves launchd unchanged. Gmail notifications are event-only for verified LaunchLab InitializeV2/Token2022 transactions associated with the known platform config and carry an explicit NOT OFFICIALLY ENDORSED label. Gmail OAuth source is read-only, secrets are never committed; the module uses its own SQLite and log directory. `uninstall` acts only on the exact Machine.fun service label.

**Deployment truth:** Git source is submitted in Draft PR but the user has not yet executed the Mac installation. No actual service, live Mac WS coverage, or Gmail SENT_VERIFIED can be claimed before user-side evidence. A sleeping or powered-off Mac is not a 24/7 availability guarantee. Unknown future Machine.fun PlatformConfigs remain a blind spot.
