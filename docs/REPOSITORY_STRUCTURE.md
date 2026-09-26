# Repository Structure and Naming Rules

Updated: 2026-09-26
Status: canonical repository organization rule

## Goal

Keep the repository readable for humans without breaking existing monitoring automations.

Every human-facing analysis file must make its purpose obvious from both:
1. its path / filename;
2. its first H1 title.

The H1 must answer: **what object is this about, and what is this file doing?**

Bad examples:
- `# Credits`
- `# JUMP`
- `# Strategy`
- `# Activity`
- `# Analysis`

Good examples:
- `# Jack / Visualize Value Credits NFT 持仓、稀有度与挂单记录`
- `# JUMP / Jumper Legion 公售参与计划与项目跟踪`
- `# PONS 二级市场、回购机制与合约持仓记录`
- `# GSTOCK Meme 基本面、链上结构与交易记录`
- `# Four Zero Two Ink NFT Mint 项目分析`

## Five top-level content classes

### 1. Monitoring / automation

Operational runtime stays in the existing task directories:
- `crypto-daily/`
- `airdrop-tge-monitor/`
- `crypto-300-profit-mission/`

Human-readable monitoring documentation lives in:
- `docs/MONITORING/`

This class contains schedules, runtimes, registries, alert rules, health/state pointers, delivery rules and immutable run audits.

Long-form project research should not be added here unless the automation itself requires a compact operational rule.

### 2. Project analysis and project records

Canonical human-facing location:
- `research/projects/`

Use for protocols, ICO/public sales, products, launchpads, early-stage projects and participation records.

Recommended per-project shape:
- `README.md`
- `due-diligence.md`
- `participation.md`
- `timeline.md`
- `updates.md`

Only create the files that are actually useful.

### 3. Token / secondary-market / derivatives analysis

Canonical human-facing location:
- `research/tokens/`

Use for tokenomics, valuation, market structure, spot/perpetuals, funding/OI, squeeze structure, buyback/burn, CEX/DEX liquidity and high-volatility token models.

Monster/squeeze analysis belongs here as token analysis unless it is a machine rule file required by a monitor.

### 4. Meme analysis

Canonical human-facing location:
- `research/memes/`

Use when the primary thesis is meme narrative, social propagation, launchpad flow, community attention, influencer flow or meme-style liquidity behavior.

Examples include ACC, PAID, KARDASHEV, GSTOCK and SHART.

### 5. NFT analysis

Canonical human-facing location:
- `research/nfts/`

Use for mint mechanics, creator background, collection structure, rarity, secondary market, whitelist/claim, listing and sale analysis.

Examples include Jack Credits, UNICRED, Fresh INK and Four Zero Two NFT.

## Operational files vs research files

Operational files answer:
- what is currently held;
- what threshold/order/event is already stored;
- what the automation should check;
- what the current factual state is.

Research files answer:
- what the project/token/NFT is;
- why it matters;
- what evidence supports the thesis;
- how the market/mechanism works;
- historical analysis and updates.

A project can therefore have both:
- a human-facing research record under `research/`;
- a compact operational state file under `crypto-300-profit-mission/positions/` or `watchlists/`.

Do not duplicate mutable facts unnecessarily. Operational current state remains authoritative for monitoring.

## Filename rule

Human-facing analysis:
`<entity>-<purpose>.md`

Use lower-case kebab-case.

Examples:
- `jack-credits-nft-position.md`
- `jump-legion-sale.md`
- `pons-buyback-mechanism.md`
- `saga-squeeze-cycle.md`

Automatic run audits keep machine-stable time naming.

## Run audit naming

Historical audit files are immutable by default and are not bulk-renamed.

Current automatic convention:
- mandatory completion record: `HHMMSS-final.md`
- older/best-effort start marker: `HHMMSS-start.md`

Older `HHMMSS.md` / `HHMMSS.json` files remain valid historical records.

Human/manual repair records may use:
- `HHMMSS-architecture-refresh.md`
- `HHMMSS-automation-repair.md`
- `HHMMSS-<topic>.md`

Do not rename hundreds of historical audits for cosmetic reasons.

## Repository Refactor Safety Rule

Monitoring continuity has higher priority than cosmetic cleanup.

1. Do not rename or move these task roots during ordinary cleanup:
   - `crypto-daily/`
   - `airdrop-tge-monitor/`
   - `crypto-300-profit-mission/`

2. Do not move these mutable pointers without an explicit migration:
   - `portfolio/current.md`
   - `performance/current.md`
   - `state/latest.md`
   - `health/current.md`

3. Before changing any path read by an automation, inspect references first.

4. For a required path migration:
   - create the new canonical file first;
   - update known references;
   - keep the old path as a compatibility alias during validation;
   - verify a real automatic run;
   - only then consider deleting the legacy alias.

5. Do not combine all of the following in one change:
   - large file moves;
   - automation prompt changes;
   - monitoring-rule changes.

6. Historical `runs/` content is immutable by default.

7. After a path-affecting refactor, verify the existing tasks only:
   - Crypto Daily at :00;
   - TGE at :14;
   - $300 Mission at :29.

8. No refactor creates a new automation unless the user explicitly requests a new automation.

## Migration state

The repository is migrating toward the five-category structure incrementally.

Current operational paths remain valid while human-facing research is organized under `research/`.
Legacy ambiguous filenames may remain temporarily as compatibility aliases until post-migration monitor validation.
