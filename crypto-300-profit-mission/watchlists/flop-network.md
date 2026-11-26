# FLOP Network / $FLOP

Updated: 2026-11-26
State: WATCH / TESTNET_LIVE_UNSCORED
Scope: project analysis and participation research only. Close Call execution is delegated elsewhere.

## Current status override — 2026-11-25 Asia/Bangkok

State: WATCH / TESTNET_LIVE_UNSCORED. This dated section supersedes the historical pre-testnet status and schedule below; it does not change local agent execution authority.

- Official Testnet page and opening FAQ (2026-11-24) report public Testnet live with six founding validators, chain ID flop_testnet, public RPC wss://testnet.flop.network/ and published genesis 0x918abd58fb16306b30ef3886514cfaebffecb4de43e82b6f8ec4795c43cfd800. Explorer https://testnet.flopscan.io/ accessible as a public page; live block metrics not independently reproduced. Direct RPC attempt from research environment failed DNS resolution; no claim of independent chain verification.
- Opening is UNSCORED. Official FAQ says voucher earning requires a future finalized activation block following a runtime upgrade; no activation block/date announced, zero prior credit, no backfill. Voucher trading disabled.
- Generic faucet page independently inspected and still labeled Devnet; no verified public Testnet Self grant. Do not spend Devnet tokens expecting Testnet airdrop credit.
- Official operator hub identifies opening runtime 1014035; SDK 0.9.0 allowlist ends at 1014034. Keep compatibility checks enabled. Signed Testnet operator/miner packs pending per opening docs. Shared model API listing and Devnet MCP health do not prove Testnet settlement.
- First 50 validator seats open for registration; registration is not funding or active admission. Agent earnings require eligible settled compute in scored phase. No confirmed TGE date; Q1 2027 remains issuer planning, not commitment.
- User's local agent runtime, wallet funding and settlement not independently checked in this research environment. Do not modify local agent, monitoring, credentials or execution authorization based on this research record.
- PM scan 2026-11-25: Polymarket, Kalshi, Limitless and Predict.fun searched; no verifiable project-specific market found.
- Sources: https://flop.finance/testnet/ ; https://docs.flop.network/docs/network-testnet ; https://ask.flop.finance/networks/testnet ; https://faucet.flop.network/ ; https://github.com/flop-labs/network/releases

## Follow-up — 2026-11-25 06:09 Asia/Bangkok

- USER_CONFIRMED terminal RPC read: correct canonical genesis, Runtime 1014035, 19 peers, syncing false, two distinct finalized heads. Testnet connectivity verified from user's Mac; earlier research-environment DNS failure is not a network outage.
- Official CLI 0.8.2 release (2026-11-24) includes SDK 0.10.0 and admits Runtime 1014035; 0.8.1 can query network status but refuses incompatible chain commands. Source: https://github.com/flop-labs/network/commit/daaff43a0af4dbc1d5a392a885c0b4ee0bf7d101 . This supersedes the earlier SDK compatibility blocker for the new release, not for the installed 0.8.1.
- Official opening FAQ still describes unscored operation, no activation block or verified public Testnet Self faucet: https://docs.flop.network/docs/network-testnet . User's installed CLI 0.8.1 independently reports Testnet faucet fetch failure and expected-genesis match null; no wallet funding/settlement verified. Local tick reports 299 runs, interval 300 seconds, last exit 0; these do not prove successful inference or voucher credit. No execution changes made by research.

## Follow-up — 2026-11-26 00:18 Asia/Bangkok

- CONFIRMED via public HTTP GET https://faucet.flop.network/chain and /limits: faucet now serves canonical Testnet genesis, status open, signed agent lane 10 test FLOP per rolling 24h, prior spend required for rollover. Snapshot asOf 2026-11-25T17:03:43.592Z. Devnet faucet moved to https://faucet.devnet.flop.network. No actual wallet grant executed in this research.
- Official https://flop.network/llms.txt specifies signed POST /v1/testnet/agent-claims; no released CLI command for this lane according to guide. Testnet gateway, registered model/miner and inference unavailable per guide. Verified-human Self and chat claims not open. Faucet grants earn no voucher credit.
- Official FAQ https://docs.flop.network/docs/testnet-and-timeline recommends SDK >=0.11.0 / CLI >=0.8.3 with pinned genesis; package-reference page https://docs.flop.network/docs/sdk-references still lists 0.10.0 / 0.8.2. Registry availability of new versions not verified; do not equate docs recommendation with release publication.
- User terminal previously confirmed CLI 0.8.2 installed, old Technocore launchd jobs disabled and port 8765 released, FLOP services preserved. Current local wallet funding, dashboard bind and latest tick not independently verified. No local changes made.
- Voucher activation block/date still absent; no backfill, no scored inference. State remains WATCH / TESTNET_LIVE_UNSCORED.
- PM correction to prior no-market finding: project-specific https://polymarket.com/event/will-flop-launch-a-token-by exists and resolves using official @flop_labs evidence. Cached page read 2026-11-26 shows Dec 31 2026 displayed 15%, March 31 2027 45%, respective cumulative volumes $3,733 and $1,501; wide quoted spreads and non-monotonic later deadlines, not verified live probabilities; gamma API inaccessible. No direct matching market verified from search results for other named venues.

## Follow-up — 2026-11-26 CLI 0.9.0 and faucet dependency verification

- USER_CONFIRMED npm registry CLI 0.9.0 and SDK 0.12.0. Temporary CLI 0.9.0 network status: profile live, expected genesis pinned, RPC matches_expected=true, runtime 1014035, faucet canonical host https://faucet.flop.network and matches_rpc=true. Global CLI remained 0.8.2 at preceding local check.
- USER_CONFIRMED faucet snapshot 2026-11-25T17:22:04.520Z: reachable but ready=false; /health HTTP 503, indexer_unavailable, signer and funding checks pass. Funding status open is not grant execution readiness. Signed agent lane remains 10 test FLOP per rolling 24h, rollover requires prior spend. No claim executed or verified.
- Local runtime previously returned HTTP_200_IDENTITY_VERIFIED, last scheduler tick 2026-11-25T17:15:30Z, 5 sent_verified mail records, sessions empty. UNVERIFIED_DOC_FORMAT / OFFICIAL_PROFILE_PLANNED reflects old document parser and old CLI; do not remove safety gates merely to obtain green status. Separate network identity/funding preparation from scored inference. No local code, task or signing changes made here.
- Official links updated 2026-11-25 explicitly say no Testnet inference gateway published, Devnet endpoints remain Devnet, scoring begins only at a publicly announced finalized activation block (no block or date confirmed), and earlier Q1 2027 estimate based on historical Nov 3 target is not a current launch commitment. TGE date UNCONFIRMED; historical estimate below is superseded. Sources: https://docs.flop.network/docs/official-links ; https://docs.flop.network/docs/testnet-and-timeline ; https://docs.flop.network/docs/network-testnet .

## Follow-up — 2026-11-26 08:01 Asia/Bangkok: Agent implementation gap

- Official https://flop.network/llms.txt explicitly opens signed POST /v1/testnet/agent-claims with address, decimal nonce, signature; identical nonce is the documented idempotent reconciliation path. Legacy POST /fund and signed GET closed on Testnet; TechnoCore room claims not yet open. Testnet gateway, registered miners/models and scoring activation still absent according to that guide. No backfill. https://docs.flop.network/docs/network-testnet confirms unscored phase.
- Faucet /limits observed 2026-11-26T00:43:50.007Z: open, remaining daily budget 196730 test FLOP, pendingGrants 110332. Health could not be retrieved in research environment; earlier user-observed indexer outage cannot be asserted current. No claim or settlement executed here.
- Inspected existing development branch research/flop-agent-local-dashboard-20261123: runtime.py blob 716117b1cb0e2d713ae277c15ada7cd27fc3f1ff relies on old document regex; faucet.py blob 111a7bd928e3d02ccb955d6373536fb1127fa1b7 calls legacy CLI faucet request and permanently blocks repeat after first attempt. Runtime's first-session path also blocks subsequent attempts, with independent settlement adapter not implemented. These are internal implementation gaps distinct from upstream service availability. README describes existing sr25519 wallet; verify actual local key type and signed lane compatibility before any signing; do not silently replace identity.
- Recommended repair in existing agent only: independently verify network identity, funding lane, idempotent nonce ledger/finalized grant, unscored trial vs scored execution, canonical miner/model discovery, independent settlement and prior spend eligibility. Preserve existing schedule, Bangkok reporting, credentials and NO_GO boundary. No implementation or deployment performed by this research review.

## Follow-up — 2026-11-26: recurring Agent deployment evidence

- USER_REPORTED Mac deployment of fixed SHA 801d8e2ac95de9e164c3d5be310bd383abed0c22 on research/flop-agent-local-dashboard-20261123, with 51/51 local offline unit tests PASS (0.180s), Node syntax and Python compilation passed, existing tick and dashboard PIDs present after restart. Remote branch HEAD independently read back at same SHA. This is deployment-command and offline-test evidence, not proof of completed live tick or sustained service health.
- Existing wallet balance query returned 10 free Test FLOP and zero reserved/frozen; previous first grant nonce result unresolved. No independently finalized grant transaction, direct inference settlement, rollover grant or new email delivery confirmed by this log. Do not classify this as full unattended participation success.
- Official guide https://flop.network/llms.txt and https://docs.flop.network/docs/network-testnet rechecked 2026-11-26: unscored phase, no activation block/date and no registered Testnet models/miners or usable inference gateway reported. User's earlier CLI 0.9.0 help and successful installation supersede guide's stale statement that no released signed-claim CLI command exists. Recurring execution adapter remains live-unverified. No new scheduler, wallet or deployment action performed by this verification.

## Project (historical background, 2026-09-29)

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
