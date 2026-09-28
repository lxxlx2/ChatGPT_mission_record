# FLOP Network / $FLOP

Updated: 2026-09-29
State: SETUP / ACTIVE-EARLY-PARTICIPATION
Scope: project analysis and participation research only. Close Call execution is delegated elsewhere.

## Project

Flop Labs is building FLOP Network, a proposed Substrate/FRAME blockchain for verified AI inference and agent-to-agent settlement.

Roles:
- agents buy inference;
- miners provide GPU inference;
- validators verify work / build blocks / provide data availability;
- FLOP is the settlement/staking asset.

Current official team:
- Arthur Hayes — CEO
- Sergey Vidyuk — CTO
- Shu Duan — CSO

The public protocol is still pre-testnet. The Yellow Paper is a draft and several implementation items remain planned/open.

## Latest official schedule

Official teaser:
- Testnet: Q4 2026
- testnet duration: roughly 90 days
- Mainnet: Q1 2027
- exact TGE date: not announced
- at testnet end, results are settled into genesis; bulk genesis pool expected to distribute at TGE.

Working interpretation:
- Q4 2026 is the earning/testnet phase.
- Mainnet-token TGE is most consistently expected around testnet completion / genesis in Q1 2027, but this is not a confirmed date.

## Tokenomics

Current official teaser / current parameter direction:
- year-10 cumulative supply: ~18.1B
- genesis pool: 4.4B
  - miners: up to 1.2B
  - agents: up to 1.2B
  - validators: 1.2B aggregate stake
  - ecosystem / growth reserve: 0.8B
- no presale
- no VC/investor allocation
- era-0 block reward: 96 FLOP
- block reward split currently described as:
  - 75% miners
  - 10% validators
  - 10% agents/brokers
  - 5% community stakers
- team/foundation still receive protocol emissions; "fair launch" should not be interpreted as zero team economics.

All figures remain provisional while the public specification is draft.

## Testnet airdrop mechanics

Miners:
- rewarded based on verified compute and inference served.
- around one quarter of miner airdrop is expected liquid at TGE; rest releases over opening mainnet months while compute continues.

Validators:
- top 1,000 testnet validators targeted for mainnet.
- genesis validator allocation acts as bonded validator stake, not a normal liquid airdrop.
- locked through first halving, then released over following 1,000 days under current teaser.

Agents:
- claim test tokens and spend them on inference.
- airdrop based largely on inference usage plus prizes.
- allocation arrives locked for inference/staking.
- current proposed unlock rule: every 3 FLOP spent on inference unlocks 1 airdropped FLOP.

Technocore:
- Flop Labs officially asked agents to create a unique DID and make a useful contribution spreading / improving Technocore, with reward during the FLOP airdrop.
- no official points formula, snapshot date or guaranteed allocation has been published.
- do not rely on unofficial faucet / daily-check-in guides unless official channels confirm them.

## Current official participation routes

1. Agent / Technocore
   - lowest-capital path
   - create persistent did:key identity
   - make useful verifiable contributions
   - later use Q4 testnet inference faucet/activity when open
   - user already has Technocore/DID and automation experience

2. Close Call
   - live agent trading competition
   - 1,000,000 FLOP prize pool for top three
   - execution is handled in another conversation

3. KOL / Creator application
   - official form is live
   - supports Chinese and Southeast Asia / Global audience
   - no public minimum follower threshold in the form
   - submission does not guarantee selection/reward

4. Miner interest application
   - official form is live
   - form lists NVIDIA datacenter GPUs and "Consumer GPU with at least 16GB VRAM"
   - public miner spec recommends 16GB+ VRAM per unit
   - ordinary SOFT GPU path is planned/ratified, but full end-to-end settlement is still being specified

5. Validator interest application
   - self-hosted and managed/hosted options
   - provisional recommended hardware: 8+ CPU cores, 64GB RAM, 2TB NVMe, 1Gbps redundant connection
   - validator airdrop is mainly bonded stake and therefore low-liquidity.

## User-fit assessment

Known user hardware:
- Apple M4 Max MacBook Pro
- 48GB unified memory
- ~1TB SSD
- no NVIDIA/CUDA GPU
- capable Python/Java/Linux/API/automation/local-LLM/agent workflows
- laptop/network setup is less suitable for reliable 24/7 validator operation.

Fit:
- Agent / Technocore: HIGH
- KOL/Creator: MEDIUM-HIGH if willing to publish useful Chinese technical/research content
- Miner on current Mac: UNCONFIRMED / LOW for now. No verified public Metal miner support; do not buy/rent GPU before testnet client and reward benchmarks exist.
- Self-hosted validator: LOW because current hardware/network is below provisional recommendations.
- Managed validator: technically possible but current economics/lockup do not justify spending before testnet details.

## Cost-effectiveness

Best current optionality:
- useful Technocore contribution + persistent DID: near-zero capital, official reward intent
- Q4 agent testnet participation: high fit, low direct capital cost
- KOL/creator application: free optionality, selection uncertain
- existing Close Call participation: low external capital, potentially large reward

Avoid for now:
- buying dedicated NVIDIA hardware solely for FLOP
- paying for cloud GPUs before conversion formula / testnet competition data
- paying for managed validator hosting before stake/airdrop economics are final.

## Technical / execution risks

- public Yellow Paper is still draft v0.5.0
- official pages explicitly mark several paths as planned/partly wired
- SOFT miner end-to-end settlement/dispute lane is still being specified
- validator active-set rule is only partly wired
- tokenomics parameters have changed repeatedly during August/September
- current project has no production inference-demand history
- actual economic demand for a dedicated FLOP settlement asset remains unproven
- supply grows materially from genesis to year 10, so valuation requires dilution discipline.

## Official channels

Verified:
- Website: https://flop.finance/
- X: https://x.com/flop_labs
- GitHub: https://github.com/flop-labs
- Technocore: https://technocore.chat
- Miner form: https://flop.finance/apply/miner
- Validator form: https://flop.finance/apply/validator
- KOL form: https://flop.finance/apply/kol

No verified public official FLOP Discord or Telegram invite was found on the official website, official X profile, GitHub or current docs as of 2026-09-29. Do not treat third-party Telegram/Discord groups as official.

## Next catalysts

Upgrade thesis when any of these occur:
- Q4 testnet opens
- official miner client and Apple/Metal support matrix appears
- agent faucet / participation rules and scoring formula published
- testnet-to-mainnet conversion ratio published
- exact TGE/genesis date announced
- public TGE circulating supply / claim schedule finalized
- official Discord/Telegram community link published
- real inference demand / performance benchmarks become reproducible.
