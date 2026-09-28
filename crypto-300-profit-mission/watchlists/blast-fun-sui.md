# Blast.fun / Sui

Updated: 2026-09-29
State: WATCH
Type: Sui memecoin launchpad / bonding-curve launch platform
Official site: https://blast.fun
Official X: https://x.com/blastdotfun
Public code: https://github.com/interest-protocol/blast.fun
Builder org: Interest Labs / interest-protocol

## Current status

Blast.fun has entered a new early-access / reboot phase branded "Flight 001".

Current official website:
- shows "Blast · Flight 001";
- uses launch codes / invite access;
- displays "Mission Control is offline";
- no open public launch interface is exposed to unauthenticated users.

Official X was visibly rebooted:
- profile bio currently says "Clear for launch";
- public mirror currently shows one recent visible post: "Now recruiting. blast.fun";
- the post reached roughly 200K+ views and generated widespread invite-code distribution.

Community users are currently:
- entering invite codes;
- connecting X;
- completing social/profile tasks;
- generating / sharing Blast cards;
- receiving additional invite codes.

This is early-access onboarding, not evidence that the rebooted launchpad is fully public/live.

## Actual technical progress

Blast.fun is not a blank-slate project.

The underlying launchpad implementation already exists and has previously been used on Sui:
- Interest Protocol's Memez.fun contract system has a Blast.fun configuration;
- bonding-curve launches can migrate liquidity to Bluefin;
- Blast configuration currently documented with:
  - 0 SUI creation fee;
  - 0% meme-side swap fee;
  - 1.2% quote-side swap fee;
  - 5% migration fee;
  - 5% post-migration token allocation;
  - fee destinations include Blast treasury / LP manager and developer share;
- historical Blast.fun-launched tokens and Bluefin pools exist on mainnet.

Public frontend/database code contains:
- X/Twitter authentication;
- token creation records;
- creator wallet tracking;
- referral codes;
- token-protection settings;
- creator rewards;
- vesting;
- farms;
- airdrop/delegator flows;
- Sui wallet support;
- trading/token pages.

Therefore the project already has real launchpad infrastructure.

## Latest GitHub activity

Public repo remains active.

Recent main-branch commits:
- 2026-09-18: migrated remaining Sui reads/writes and transaction submission from deprecated JSON-RPC paths to Sui gRPC because public fullnodes stopped serving the old RPC methods;
- 2026-09-09: migrated creator reward claims to gRPC;
- 2026-08-02: farm stake flows migrated to Sui GraphQL;
- 2026-07-14: vesting/farm infrastructure migrated away from older Shinami/JSON-RPC paths.

Interpretation:
- the developers are actively maintaining compatibility with Sui infrastructure;
- these recent commits are mainly production-maintenance / plumbing work, not evidence of a large new product feature set;
- current Flight 001 / Mission Control invite layer is not present in the public main/staging branches, implying either closed-source deployment code, a separate repo, or an unreleased branch.

This limits how much of the reboot can be independently audited from GitHub.

## Current launch readiness

CONFIRMED:
- invite-based early access is live;
- official X has restarted promotion;
- site is reachable and branded Flight 001;
- card-generation / invite flow is being used by real users;
- underlying launchpad stack and Bluefin migration code already exist;
- repo received production compatibility fixes in September.

NOT YET CONFIRMED:
- date/time for open public launch;
- whether token creation/trading is enabled inside Flight 001 for invited users;
- new Season Zero economics;
- points / airdrop formula;
- platform token or tokenomics;
- investor/funding update;
- exact changes versus the old Blast.fun launchpad;
- public analytics for users, launches, bonding volume or fees from the reboot;
- whether current Flight 001 launch contracts differ from the historical Memez/Blast configuration.

## Social / ecosystem signals

Current attention is materially stronger than the previous quiet period:
- the official "Now recruiting" post reached roughly 200K+ views in public mirrors;
- Bluefin publicly posted "My helmet is coming on for @blastdotfun";
- multiple established Sui users/ecosystem accounts are distributing invite codes;
- Sui community discussion frames this as an OG launchpad returning / rebooting.

These are launch-attention signals, not proof of sustained trading demand.

## Assessment

Blast.fun is best understood as a **relaunch of an existing technical launchpad**, not a newly built launchpad starting from zero.

Current stage:
- underlying infrastructure: production-capable / historically used;
- reboot frontend/onboarding: early access;
- public market relaunch: not yet open;
- token/airdrop economics: unknown.

For the user's $300 Mission:
- keep in WATCH;
- early access is worth completing because cost is near zero;
- do not deploy meaningful SUI merely because an invite is obtained;
- highest-value event is the first public launch / first serious tokens / confirmed reward mechanism.

## Upgrade triggers

Move to SETUP when any of these appear:
1. official public launch date;
2. live token creation/trading under Flight 001;
3. first meaningful bonding/migration volume;
4. official points/airdrop/token incentive;
5. Blast/Bluefin launch-pool addresses and fee flows can be measured;
6. credible Sui ecosystem launches choose Blast.fun over competing pads.

Downgrade if:
- early access remains social-task-only for weeks;
- no actual launch date follows the current recruitment campaign;
- repo activity remains maintenance-only and reboot code stays opaque;
- first launches show negligible liquidity/volume;
- new token incentives require material capital with no clear expected value.
