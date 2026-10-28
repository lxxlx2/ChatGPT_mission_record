# Sixth Sense Labs / Sextus Sensus — SXTH candidate and machine.fun Foundry identity

Updated: 2026-10-28 Asia/Bangkok
Research category: embodied AI / physical-world robot training-data infrastructure; proposed Solana token launch.
Research status: `PROJECT_IDENTITY_IDENTIFIED / SXTH_OFFICIAL_TOKENOMICS_PUBLISHED / SXTH_MINT_AND_ICO_NOT_VERIFIED / USER_INTENDS_TO_PARTICIPATE`
Action: `WATCH`, `NO_BUY_UNTIL_OFFICIAL_LAUNCH_AND_LIQUIDITY_VERIFIED`.
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `token_trading_principles.md`.
Trading/monitoring: `PRODUCTION_TRADING=NO_GO`; no capital committed or monitoring task created by this note.

## 2026-10-29 chain-first superseding finding: verified Machine Launch program closure

**Supersedes prior statement that issuer "we are not live!" is strong counterevidence.** User insists issuer claims and denials are untrusted. Primary chain transactions, signers, logs and flows govern findings. Direct Solana mainnet read-only Alchemy RPC checks Oct29 2026 Asia/Bangkok.

### Verifiable timeline and identity link

1. **Oct28 20:18:19 Bangkok (13:18:19 UTC)**: Tx XSsPNb1TM8J7rEsWgr9ujus6TABVx45UhqaARaN454LWhr9qwM3aJg5qELDGzV9LNYimk1bShPpaeuKWLA2nmXE, slot 462490424, succeeded; created mint sYUJLvHEVQofSBehcUQiYLZA967BLqX8CZbUdCWMACH, decimals 6, called Raydium LaunchLab. Funding source 7LJoZL5GHDmJoxczmM1P1hzrARCUWa7uyxVT5jBwsd9d. Direct mint read as of RPC slot 462553659 showed 999,996,108.037488 tokens and both mint/freeze authorities null. This does not establish authorized front-end launch.
2. **Oct28 21:29 Bangkok**: @thetrenchfiles X allegation published (https://x.com/thetrenchfiles/status/2115450980804526090), used only as a date reference/hypothesis, not chain proof.
3. **Oct28 22:33:59 Bangkok (15:33:59 UTC)**: Same source address 7LJoZL5GHDmJoxczmM1P1hzrARCUWa7uyxVT5jBwsd9d is an actual signer of Squads v4 ProposalApprove tx 4wQq8LR5p1Qyy8L6jiXCn1RNhvgHLAtkiomF2geQzQEctVneWUU6Qq9fezYziC5PmCHdUc5kPk9ZozDCJxf1xjsy, slot 462528557; real multisig address GkvU4WqWVFz34pQnLfem3GqW57s2nEFGpqjkz4b3aTue, proposal account 2km41yhxW1Pa4SU7i4Dza5gJ9JZZLhy35gftBrTqBNZk.
4. **Oct28 22:34:00 Bangkok (15:34:00 UTC)**: Same signer executes successful Squads v4 VaultTransactionExecute tx 4k7Hdv7diFSxAc9SUWT6NPnN2z5WCdLvirvBPLv66GFFrsf1H47vnL3Lcfub8JwsFh5bBwZKXsBriimBzJDzcLvL, slot 462528562. Actual inner program logs:
   - Onchain Memo: "Machine Launch: permanently close config and program"
   - Calls executable program MACHX97ggsHjPyrZErp5mGr7uq5jVmqgCnN7Hd2213g, instruction CloseMachineConfig, success.
   - Calls BPFLoaderUpgradeab1e11111111111111111111111, parsed type close, programAccount MACHX97ggsHjPyrZErp5mGr7uq5jVmqgCnN7Hd2213g, ProgramData Ak3fwDLN8s7GgAvetccEiyLN2LSo6xUUbta2L2itgq1B, authority 2G5fgukpFZezPqMKW1S2hMvw4w8kqi1nK9hyzqr2cwPU, recipient FmoGkvumFhRo8jiJfuV9VgVhDL5gNQrzS9YaecaaDUhn. Runtime log: "Closed Program MACHX97ggsHjPyrZErp5mGr7uq5jVmqgCnN7Hd2213g". Direct program account shows executable flag and points to that ProgramData; after closure getAccountInfo(ProgramData) returned value null, consistent with close.
5. Program close took place **about 136 minutes after mint and 65 minutes after X accusation**. Sequence is confirmed, motive is unknown: do NOT assert the close was cover-up or was routine cleanup without evidence.

**Material reassessment:** The creator funding address approved and executed a multisig operation administrating a **self-labelled Machine Launch program**. This is substantially stronger than ordinary Squads interaction and raises concern about operational link to Machine-branded launch infrastructure. Independent proof of the program's corporate ownership by Machine.fun, actual human controller, three buyers' common controller, Jito Bundle member signatures, realized profits of $2300/$1500/$800, and alleged second Machine coin creation remains absent. Do not claim onchain issuer team attribution proven. Issuer denial or an unfinished website does not rebut the mint or program close.

**Status:** CHAIN_LAUNCH_VERIFIED / SQUADS_APPROVE_EXECUTE_VERIFIED / MACHINE_LAUNCH_CONFIG_AND_PROGRAM_CLOSED / REAL_WORLD_TEAM_ATTRIBUTION_UNVERIFIED / BUYER_BUNDLE_PNL_UNVERIFIED / SXTH_NO_GO. Research only: no new monitor, wallet activity or trade.

---

## 2026-10-28 23:xx The Trench Files allegation: official denial plus direct Solana RPC evidence

**Read-only evidence window:** Oct28 2026 ~23:00–24:00 Asia/Bangkok. Direct original full five-post X thread via user's authenticated shared browser `https://x.com/thetrenchfiles/status/2115450980804526090`, comments, and original `https://x.com/machinedotfun` profile. Solana mainnet queried with user's connected read-only Alchemy RPC. **Allegations ≠ verified attribution**.

### Full accusation and primary response

- Trench Files `@thetrenchfiles` Oct28 21:29 Bangkok thread `https://x.com/thetrenchfiles/status/2115450980804526090` claims machine.fun "went live"; a test token was created by alleged platform team, who approved/executed Squads multisig proposals, three fresh wallets were bundled to snipe launch through Jito, profits of roughly `$2300/$1500/$800`, and the same deployer next issued another `Machine` coin in an attempt to look official. References `https://x.com/thetrenchfiles/status/2115450983543365659`, `https://x.com/thetrenchfiles/status/2115450986672300100`, `https://x.com/thetrenchfiles/status/2115450988546924963`, `https://x.com/thetrenchfiles/status/2115450990967030085`, `https://x.com/thetrenchfiles/status/2115450993802371491`.
- **Strong direct counterevidence:** Machine.fun **official account** replied in the accusation thread `we are not live!` at `https://x.com/machinedotfun/status/2115464566880731430`. Issuer's original official website `https://machine.fun/` independently still displayed `Phase 2: FIND THE NEXT UNITREE — LOADING…` at lookup. Therefore original `platform already formally live` statement is **CONTRADICTED BY OFFICIAL ISSUER**. This is not proof no developer/test token or connected exploit occurred.
- **Solana tx is real**: `https://solscan.io/tx/XSsPNb1TM8J7rEsWgr9ujus6TABVx45UhqaARaN454LWhr9qwM3aJg5qELDGzV9LNYimk1bShPpaeuKWLA2nmXE`; Alchemy mainnet `getTransaction` returned Success (`meta.err=null`), slot `462490424`, `2026-10-28T13:18:19Z` (Bangkok 20:18:19). Parsed inner instructions create SPL mint `sYUJLvHEVQofSBehcUQiYLZA967BLqX8CZbUdCWMACH` with 6 decimals and call Raydium `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj` LaunchLab. New token and launch-program interaction are **ONCHAIN_VERIFIED**, not proof it was machine.fun website's production sanctioned first issuance.
- Mint `getAccountInfo` on Solana mainnet near slot `462553658`: supply `999996108037488` raw = `999,996,108.037488` UI; mint and freeze authority **null**, standard Token Program; not a verified `$SXTH` or official platform token.
- Fee-payer/source in transaction `7LJoZL5GHDmJoxczmM1P1hzrARCUWa7uyxVT5jBwsd9d`. Alchemy `getSignaturesForAddress` observed later signatures `4k7Hdv7diFSxAc9SUWT6NPnN2z5WCdLvirvBPLv66GFFrsf1H47vnL3Lcfub8JwsFh5bBwZKXsBriimBzJDzcLvL` and `4wQq8LR5p1Qyy8L6jiXCn1RNhvgHLAtkiomF2geQzQEctVneWUU6Qq9fezYziC5PmCHdUc5kPk9ZozDCJxf1xjsy`, both Success signed by same source and calling `SQDS4ep65T869zMMBKyuUq6aD6EgTu8psMjkvj52pCf` (**verified Squads Protocol v4 multisig program** per https://github.com/Squads-Protocol/v4). Therefore `some Squads interactions by the source account` is **ONCHAIN_VERIFIED**; **which multisig, approvals, role and its independently verified organizational ownership are not established**, so do not say "clearly machine team wallet".
- Three accused addresses `dCyMosm628KwGbBGy8vdwMWiCFEYfjXNAuies9XAnLG`, `3UA2JLNowMaWvVJDEPaWavmCoNzWAuG9rjosD1MpRkpX`, `FqmQi1RZ9gebJWKzGwMNxS154nJK8NabRz9VmDK7vgrt`: Alchemy `getTokenAccountsByOwner` found a valid owned token account for **the exact above mint** for each, **each current token account balance 0** when fetched near 2026-10-28 23:xx Bangkok. Creator's own token account also 0. This corroborates interaction with the same created mint and no remaining holdings in those accounts; **not independently verified Jito bundle membership, common controlling identity, 3 cash P&L figures, taxable realized profits, funding source or exact original buy size**.
- Accuser supplied Jito Explorer bundle ID `66860b72f77b93f94f8e0e49a8d76dbf71229851a1e4909599e7fff45d3533cb` at `https://explorer.jito.wtf/bundle/66860b72f77b93f94f8e0e49a8d76dbf71229851a1e4909599e7fff45d3533cb`, **public web fetch failed**, no successful direct `getBundleStatuses` membership proof. Keep `BUNDLE_NOT_VERIFIED`, not false.
- Secondary claim `same source created another token named Machine` from thread screenshots is **NOT independently chain reconciled**, so ticker/mint/issuer identity unconfirmed. A name `Machine` is not sufficient for issuer authorization.
- Major implication: **previous speculative SXTH-first launch narrative must remain explicitly unconfirmed**. Test/permissionless Raydium creation before a production app launch is possible; **neither automatic proof of developer misconduct nor proof of platform anti-sniping safety**. User should not trade same-name Machine/SXTH tokens without canonical issuer mint, genuine launch instance, authenticated custody & liquidity, validated deployer and feasible sell quotes.
- No position changes or scheduled monitoring; `MACHINE_PLATFORM_NOT_LIVE_PER_OFFICIAL_REPLY / LAUNCH_TX_VERIFIED / SQDS_V4_INTERACTION_VERIFIED / TOKEN_ACCOUNTS_CURRENT_ZERO / TEAM_ATTRIBUTION_UNVERIFIED / BUNDLE_PNL_UNVERIFIED / SXTH_NO_GO`.

---

## 2026-10-28 17:32 Telegram General now visible: owner did not confirm today launch

**Observation method**: User's recently reopened, authenticated Telegram Web `https://web.telegram.org/a/?utm_source=chatgpt.com#-1004432036138_1` read-only through connected Browser on Oct28 evening Bangkok. Unlike previous stale view, visible message region explicitly shows **Today** and Oct28 messages through approx **17:32**, followed by member-join events. This is not a full historical Telegram export. The previous "42 unread not inspected" limitation is now partially closed for the newly displayed slice.

**Launch date attribution:**
- At visible **16:37** member `O CA` asks Todd: `Wen launch todd`. The Owner does **not** answer with date/clock/CA in the currently rendered segment.
- At visible **17:32** member `Froze Tong` asks `hi, token launch today right ?`; member `O CA` responds **`Yes`** at 17:32. This is **NON-OWNER MEMBER-ONLY assertion**, not canonical issuer/machine.fun launch confirmation. Do not promote it to confirmed Oct28 TGE or official permission to snipe. Original issuer Telegram Owner's prior Oct27 endorsement `Wednesday Launch` was only a nonbinding target day.
- Machine.fun original X https://x.com/machinedotfun/status/2115110031754703022 (Oct27 15:55 UTC) remains a **platform** go-live within next 48h claim, literally through **Oct29 15:55 UTC / 22:55 Bangkok**. Its website https://machine.fun/ independently fetched Oct28 still shows `Phase 2: FIND THE NEXT UNITREE — LOADING…`. No platform first-listing roster or SXTH verified mint/curve initializer/timestamp located.
- Project's Oct28 **02:28** Telegram pinned https://x.com/Sextus_Sensus/status/2115163645114040782 is `Sixth Sense Labs Is Growing!` and welcomes community members. This is **community growth marketing**, NOT token deployment or distribution details.

**Separate possible future data-capture points and reward experiment**:
- At visible **01:38–01:50**, Telegram Owner Todd says `Quality over quantity right now!`, `We won’t make it a requirement for the global airdrop just will yield less points`, then **`Again this is all speculation we still have to build out a proper plan and document it all down but we have a vision and would love to ship it!`**. This concerns a *potential* hardware/data-capture quality weighting and future global airdrop and has **not been committed as an SXTH eligibility, PP conversion, claim or vesting rule**. Do not conflate planned Lumina points with an existing spot-launch $SXTH allocation. No verified reward payout, fixed multiplier or requirement.
- New social/group activity and several joins do not establish paid customers, launch or real trade volume. Do not treat the community member reply `Yes` as first-party proof.

**Evidence decision**: `TG_NEW_TODAY_READ_TO_17_32 / OWNER_OCT28_TOKEN_LAUNCH_TIME_UNCONFIRMED / MEMBER_YES_ONLY / PLANNED_GLOBAL_AIRDROP_SPECULATION / MACHINE_WEBSITE_LOADING / SXTH_MINT_UNCONFIRMED / NO_TRADE`. Verify on the canonical issuer and machine.fun first-party pages and actual Raydium LaunchLab creation transaction before any market action.

No account message, signature, transaction, monitoring or automation created.

---

## 2026-10-28 evening cross-source recheck: Machine peaq CodecFlow X, website, and Telegram limits

**Check time:** October 28 2026 around 19:20–20:00 Asia/Bangkok. Primary issuer X read through user-shared connected browser, official project sites via public web; user-authenticated Sixth Telegram General read-only; independent verbatim peaq representative interview of Oct13 as primary-speaker source. This update specifically answers cross-platform launch status and conflicts.

### Machine.fun issuer X and schedule

- Direct current connected X account `https://x.com/machinedotfun`: **4,721 followers**, overlay FrontRun **56 KOL follows** (plugin-defined and not independent buyers); latest top-level post Oct28 `https://x.com/machinedotfun/status/2115405990891758043` highlights **peaq support** and points to new peaq writeup; quotes @peaq saying `@solana as the home of robotics`, `Robots and machines running peaqOS`, `Access to projects from the very first day`. **This is PE AQ/Machine platform-wide launch support, not a source naming SXTH as the first coin.**
- Oct28 Machine `https://x.com/machinedotfun/status/2115353308785148064` quote-replied `Robots` to official @solana's generic `_____ should be on Solana.` It is **general ecosystem engagement, NOT issuer certification of SXTH.**
- Oct27 Machine explicit launch `https://x.com/machinedotfun/status/2115110031754703022` said `goes live within next 48 hours`. Twitter snowflake ID independently decodes original **2026-10-27 15:55:03 UTC** (Bangkok **2026-10-27 22:55**). A literal 48-hour upper bound would be **Oct29 15:55 UTC = Oct29 22:55 Bangkok**, **issuer's projected timeframe, not guaranteed trading timestamp**. Current official main website https://machine.fun/ directly still says `Phase 2: FIND THE NEXT UNITREE — LOADING…`; no visible live pool, issuer listing roster or contract. Foundry https://foundry.machine.fun/ remains hardware **application and incubator**, not a live token purchase list.
- Peer founder CodecFlow new original X statement mirrored in read-only `https://www.sotwe.com/Machinedotfun` and `https://teapawt.net/machinedotfun`: joined Machine.fun and peaq for a Solana robotics launchpad, integrated/collaborates with Solana, Raydium, Sunrise and peaq, onchain tradability possible from project day one and launches in 48h. **Not a Sixth-specific commitment, nor a guarantee which mint launches first.**

### Very high-value primary representative explanation: platform is permissionless, Foundry is selective

- **Martin El-Khouri of peaq** (first-person video interview dated **Oct13**) at `https://blockwest.co/interviews/building-the-machine-economy-peaqs-martin-el-khouri/` approximately 31:22: Machine.fun is a **fair-launch launchpad**, **any project can launch / they cannot really prevent it / you might see memes or random projects**; peaqOS/verification and Foundry can help **genuine machine builders show evidence**.
- This **distinguishes permissionless launch tokens from curated Foundry applicants**. Earlier SXTH Telegram community statement `every machine.fun token is thoroughly vetted before launch` is **INCONSISTENT WITH platform partner's explanation** if meant universally; a founder-only application vetting statement is plausible, but not blanket coin authentication. Protect from unknown first-created spoof or unreviewed token. The **first chronological token** may differ from a **first featured, successfully traded or Foundry-vetted token**.
- Do not imply Solana/Raydium/peaq endorsement of the SXTH token. Their direct confirmed partner target remains **Machine.fun platform and tech**.

### SXTH issuer and two-way engagement

- Connected official `https://x.com/Sextus_Sensus` tab remained showing **493 followers, 3 KOL overlay** and yesterday's posted `https://x.com/Sextus_Sensus/status/2115110356687151501` `See you on Launch Day!`, plus `https://x.com/Sextus_Sensus/status/2115125225486422255` Lumina 1.0 end-of-month/product incentive roadmap. User X tab may show cached age labels; **do not assert this is a complete fresh Oct28 timeline**.
- NEW correction to prior `one-way clout chasing` narrative: Machine.fun official account **did reply directly to @Sextus_Sensus** with `Can't wait!` in the first-party reply timeline, verifiable from `https://www.sotwe.com/Machinedotfun` near section with `@Sextus_Sensus`; **two-way engagement EXISTS**. This endorses excitement/awareness, **NOT formal first-in-line allocation, mint, price, launch time or signed partnership**. Previous `no official machine.fun direct interaction` claim is **superseded**; prior unverified first-listing **remains unverified**.
- Official SXTH tokenomics read `https://sixthsenselabs.xyz/Tokenomics`: **1bn proposed max SXTH**, liquidity 100m total of which 70m assumed DEX seed; marketing 22.5m nominal immediate release; monthly from month seven; LP planned locked to month twelve. Official RaaS `https://sixthsenselabs.xyz/RaaS` says Booster K1 rent via USDC, but booking returns `Failed to fetch` and no verified paid customer/payout; no onchain new genuine SXTH mint or LaunchLab initializer located in official site or retrieved platform feed. These remain **issuer docs/claims**, not verified deployed sale parameters.

### Telegram General currently NOT at newest messages

- Authenticated user browser `https://web.telegram.org/a/#-1004432036138_1`, Sixth Sense Labs Community General (chat interface shows **68 members** and `General 80 messages`); page content **only displays Yesterday Oct27 messages ending at 23:55** and a `Go to bottom` control / unread **42**, i.e. later messages **were not present in the read DOM**. Browser connector is **read-only** and cannot scroll or click in current chat mode.
- Latest actually read Owner Todd content remains Oct27 about RaaS backend test pending, 70 SOL promised LP, 6-month cliff/12-month vest, and marketing efforts, plus pinned Lumina 1.0. **Cannot claim to have read or ruled out any newly arrived Oct28 admin announcement**. Older chat screenshot mention of Wednesday launch was an Owner acknowledged weekday and not a chain-confirmed time. Platform X now offers clearer 48h bound.
- User can scroll Telegram chat to bottom so fresh messages become rendered; until then **TELEGRAM_NEWER_UNREAD_UNVERIFIED**. No automated TG export, messages, or account actions.

### Mandatory PM / execution gates

- The project-specific PM check previously recorded no verified SXTH direct market on Polymarket, Kalshi, Limitless, Predict.fun. Today's web index search `SXTH Sixth Sense Labs` Polymarket surfaced unrelated 'sixth Starship test' not an SXTH market; **no verified project-specific PM odds**, so no numeric probability.
- **STATUS:** `MACHINE_PLATFORM_GO_LIVE_48H_OFFICIAL_WINDOW / WEBSITE_PHASE2_NOT_LIVE / HARDWARE_COHORT_UNKNOWN / SXTH_PLATFORM_TWO_WAY_SOCIAL_CONTACT / SXTH_FIRST_LAUNCH_UNCONFIRMED / TG_UNREAD_42_NOT_REVIEWED / SXTH_MINT_UNKNOWN / WATCH`. The launchpad platform story is stronger than SXTH's independent launch eligibility/traction. Do not buy unverified name match, do not create automated monitor or unauthorized trades.

---

## 2026-10-28 platform-first launch thesis: watch actual machine.fun leaders, SXTH not guaranteed

**Trigger:** user explicitly compares platform attention to SXTH and asks whether first truly successful token deserves priority. This user-requested comparison is a one-off factual analysis, not a broad cross-ICO template. Verify with machine.fun first-party and user-connected X, 2026-10-28 Asia/Bangkok.

### Public evidence

- Direct read-only of connected `https://x.com/machinedotfun`: **4,377 X followers**, third-party FrontRun overlay **55 KOL follows** (methodology UNVERIFIED), and X native 2026-10-27 `within next 48 hours` platform announcement had around **8,187 views and 144 likes** at time of tab capture (not a constant or audited metric).
- Direct read-only of `https://x.com/Sextus_Sensus`: **493 X followers**, third-party overlay **3 KOL follows**, 2026-10-27 SXTH quote-post `See you on Launch Day!` around **357 views and 9 likes** at read time. Approx **8.9x** difference in account follower size. Compare as **dated surface social reach**, not independently verified active real traders, organic growth or identical post cohorts.
- Official `@solana` openly responded to `@machinedotfun` **2026-09-26** `machine time 👀`, subsequently quoted/reposted by machine.fun (platform account's own timeline archive https://twiscan.com/en/x/machinedotfun). First-party machine.fun partnership announced with `@Raydium` and its LaunchLab on 2026-09-29; `@codecopenflow` and `@peaq` appear as platform supporters on its official profile and its development history. These are **platform-specific signals**. No matching Solana/Raydium first-party SXTH endorsement was found in the inspected public results; absence from a partial search is NOT proof of absolutely zero interaction.
- Sixth Sense Labs has **one-sided public promotion**: SXTH official X quotes Machine.fun platform launch, owner Todd of linked official Telegram said `To our knowledge we will be the first!`. No matching `@machinedotfun` official first-launch named roster, first-launch mint, launch-specific accepted creator, or unique contract announcement found after targeted searches `site:x.com/machinedotfun "SXTH"` and `"Sixth"` through 2026-10-28. Hence **potential SXTH first place remains a nonbinding issuer claim**. Do not infer deliberate deception or nonexistent affiliation from asymmetric announcements.
- `https://machine.fun/` directly renders `Phase 2: FIND THE NEXT UNITREE — LOADING...`. `https://foundry.machine.fun/` defines hardware admission and Foundry support but **does not publish a specific selected listing order** at inspection.

### Refined trading thesis / confirmed separation

1. **Top-level event:** machine.fun platform actually live for permissionless token creation/trading, plus first-party vetted Foundry cohort identity (if released). Platform announcement doesn't guarantee SXTH first.
2. **Actual debut cohort:** discover real first onchain creator(s), exact quote mint, bonding-curve or Raydium LaunchLab identifier, creation slot and transaction; distinguish multiple simultaneous launch candidates, first timestamp, first traded asset and first graduated LP.
3. **First success / effective leader:** prioritize a first cohort token that shows **substantive organic unique buyers, independent order flow (exclude creator-linked/bundled wallets), buy/sell balance, 5m/30m/2h volume and holder concentration, depth/slippage, fee and price-impact behavior, and successful graduation or durable tradable liquidity**, rather than merely the first indexed mint or highest mark price. Realized investor ROI requires entry timing and exit quote; no automatic first-token 10x.
4. **SXTH remains a candidate only:** if it is indeed platform's first with independent demand and safer curve/holder conditions, it may be traded under prior conditional risk budget; if another project becomes the actual leader, do not force the SXTH thesis or silently swap analysis while claiming SXTH launch success. Reassess the actual project separately by the Mission research workflow before making a buy decision.
5. **Critical pitfalls:** platform endorsement of technology is NOT endorsement of any launched project. Launch order may be concurrent or front-run by a permissionless creator, bots may buy all early curve inventory, no first-launch return distribution is established for a brand-new platform. No reliable PM contract exists to quantify SXTH or actual first launch; no probability assigned.
6. **Status:** `MACHINE_PLATFORM_LAUNCH_PRIORITY / FIRST_SUCCESSFUL_COIN_UNVERIFIED / SXTH_FIRST_UNCONFIRMED / NO_GO`. This is a **research prioritization only**, NOT new monitoring, automation, push alert, wallet action or authorized trading setup.

---

## 2026-10-28 machine.fun platform identity and 48-hour launch interpretation

**Question resolved:** platform launchpad vs presale ICO, 48-hour message vs SXTH immediate launch, and independent official/community signals. First-party machine.fun sources + upstream Raydium official LaunchLab docs checked 2026-10-28 Asia/Bangkok. Latest prior direct user-connected X evidence of Oct27 machine.fun 48h and SXTH quote is in next section. **No trade, no automation.**

- Machine.fun's identity: **Solana hardware/robotics/Physical AI token launchpad + Foundry hardware accelerator**. Issuer https://machine.fun/ currently Phase 1 apply, Phase 2 `FIND THE NEXT UNITREE — LOADING`; https://foundry.machine.fun/ offers vetted applicants factory/operations support, free application and optional project tokenization. They are **not operating a MetaDAO-like fixed-window USDC ICO by default**.
- First-party @machinedotfun chronology independently retrievable in archived original posts https://twiscan.com/en/x/machinedotfun : **2026-09-29** official Raydium LaunchLab partnership announced; **Sep30** delayed initially intended platform opening, explicitly `Project registrations and trading open soon`; **Oct01 and Oct05** pledged at least **12 hours notice**, reworked fee config with onchain tests; **Oct27** says platform `goes live within the next 48 hours`, as preserved from SXTH quoted original first-party account. Hence reasonable to anticipate platform trading becoming available; **no evidence that SXTH mint must start exactly when web platform opens**, nor definite Bangkok clock time.
- **SXTH potential first:** actual SXTH Telegram group owner Todd @ Oct27 19:49 said `To our knowledge we will be the first!` and SXTH X posted `See you on Launch Day!` https://x.com/Sextus_Sensus/status/2115110356687151501 . Both are **issuer-side evidence**, no independent machine.fun SXTH-specific lineup/acceptance, signed token mint or listing timestamp found in the checked platform official X and machine.fun pages.
- Machine.fun mechanism per issuer Sep23: creator/platform **trading fee split**; capped founder buy at **same curve**, connected founder wallets disclosed; some platform fee used for market buys of CODEC and PEAQ. Optional `Ignition` places project tokens into higher-price sell orders with limited daily unlocked proceeds. Sep/Oct account documents multiple **quote mints**, including SOL, USDC, USDT, PEAQ, CODEC and specific equity-representation tokens. Quote mint must be read from actual project onchain instance; **do not assume SXTH/SOL**.
- Official Raydium actual primary docs https://github.com/raydium-io/raydium-docs-v1/blob/main/products/launchlab/overview.mdx , https://github.com/raydium-io/raydium-docs-v1/blob/main/products/launchlab/bonding-curve.mdx and https://github.com/raydium-io/raydium-docs-v1/blob/main/user-flows/creating-a-launchlab-token.mdx show: **create mint + launch curve → spot buy/sell on curve → raise threshold / graduate → CPMM pool**; supported curve choices are `constant-product`, `fixed-price`, `linear-price`. Initial 70 SOL owner-stated funding **cannot be simplistically divided by 70m SXTH as a guaranteed 50/50 pool**: possible cap/creator buy/other LP/launch reserve handling, currently unknown.
- Raydium official vesting https://github.com/raydium-io/raydium-docs-v1/blob/main/products/launchlab/vesting.mdx confirms vesting is **optional** and must be stored under the actual project initializer beneficiary records. Token launch project should inspect `LaunchState` supply, curve type, reserves/graduation threshold, founder buy, fees, quote token, vesting and actual source-verified token CA.
- Public discussion found: related **CodecFlow** prior posts describe first Foundry cohorts and fundraising plan (archived https://twiscan.com/en/x/codecopenflow), while peaq and Solana social activity signals **ecosystem interest**; some community/KOL relay machine.fun general platform narrative. **No substantiated independent SXTH-specific launch price, precise time, lineup confirmation, or deterministic ROI**; do not promote general robotics narrative to evidence that SXTH will launch at platform go-live.
- Archived first-party X exchange https://www.sotwe.com/Machinedotfun?lang=en quotes Machine.fun explicitly saying it will **not launch its own token**; platform revenue directed towards existing CODEC and PEAQ. This is a platform statement mirrored by third-party archive; no fresh signed contract inference. Do not assume invented `MACHINEFUN` token.
- **Decision gate unchanged:** `SXTH_WATCH`, proposed first-launch status `ISSUER_HINT_NOT_PLATFORM_CONFIRMED`, platform `LAUNCH_WITHIN_48H_ISSUER_CLAIM`, mint & config `UNVERIFIED`. Protect trading NO_GO; no automatic new tasks, no pre-purchase of similarly named token.

---

## 2026-10-28 00:12 investment gate re-evaluation and new machine.fun 48h signal

**Scope:** one-target SXTH speculative spot launch ROI/risk, under current `PROJECT_ANALYSIS_FRAMEWORK.md`; no generic KYC/geography/tokenholder-entitlement narratives, no peer-ICO cross-comparison. Research only; production NO_GO remains.

### New direct first-party launch and product statements

- **Machine.fun issuer launch imminence:** Read-only from authenticated user's original X tab https://x.com/Sextus_Sensus and latest quote around Bangkok 2026-10-28 00:12. Project account posted `See you on Launch Day!` https://x.com/Sextus_Sensus/status/2115110356687151501, quote of `@machinedotfun` saying `We've teased for long enough. MachineFun goes live within the next 48 hours.` This establishes an **official platform launch window claim** on Oct27, **not** a contract/clock-confirmed SXTH mint, exact trading time, minimum price, specific SXTH creator/mint or cash raise. The Oct27 Telegram Owner Wednesday endorsement remains a date lead. **Potential operational distinction**: machine.fun X 2026-10-05 had promised at least 12 hours' notice before live trading after September launch delays (source https://x.com/machinedotfun). As of this read, no separately verified 12-hour timestamp was found. LaunchLab protocol integration and exact anti-snipe restrictions must still be examined.
- **Lumina roadmap now more specific:** Project directly posted https://x.com/Sextus_Sensus/status/2115125225486422255 `Lumina 1.0 is slated for end of month`; proposed subsequent web3 upgrade: **Phantom sign-in, points toward future airdrop, partners fund real-world data capture campaigns**. Planned release ≠ production revenue, deliverable proof or an actual scheduled future airdrop. Do not equate this app `points` statement with guaranteed SXTH allocation; the future incentive campaign may use a separate mechanism.
- User's live Telegram General browser view updated through approx Oct27 23:55: group Owner Todd, in response to `whats the starting markercap?` around **23:18**, replied only **`Fair launch!`**, no opening cap or price. At **23:55**, Owner reposted/pinned the Lumina announcement. No official SXTH minted address, pool ID, bid contract, price, transaction receipt or binding sale window in read-only visible state.
- Machine.fun official https://machine.fun still showed Phase2 `LOADING` when queried; its Foundry https://foundry.machine.fun is hardware founder onboarding, not investor token ICO purchase page.
- Independent PM search in publicly indexed Polymarket, Kalshi, Limitless and Predict.fun using `SXTH`, `Sixth Sense Labs`, `Sextus Sensus` and `machine.fun` launch/FDV/raise returned **no matching verifiable project-specific active forecast market, probability, liquidity or settlement rules as of this research**. This does not prove one never exists; do not infer odds.

### Public-buyer exit risk and conditional hypothetical prices

- **Verified paid business metrics remain unknown:** no independent paid data-capture campaigns, true revenue, paid users, completed USDC RaaS rentals or paid dataset sales. RaaS backend and tests remain the Owner's unvalidated promises. Physical machine registration is not evidence of commercial sales.
- Group Owner's **70 SOL** seed capital and previous official tokenomics **70m SXTH DEX pool inventory, 1bn fully diluted supply** yield an **illustrative hypothetical simple 50:50 constant-product start price `0.000001 SOL/SXTH` and 1,000 SOL FDV**, only if *both specific amounts go into a regular initial pool at once*. This does **not** describe Raydium LaunchLab bonding-curve opening unless individually proven by actual transaction, reserves and current trading curve. A nominal 70 SOL reserve is shallow relative to speculative flow; users may buy at multiple times pool initial price and incur large reverse price impact on exit. Confirm **quote asset** too: machine.fun has discussed SOL, USDC/USDT and tokenized equity quotes; Owner has NOT committed to a SOL/SXTH pair.
- Marketing tranche initial availability and Group Owner `15% retained for hardware` statement remain unresolved against official 30/25/20/15/10 allocation. 6-month cliff vs full 18-month restriction messaging also inconsistent. Need actual lock/vesting/authority addresses; *LP locked* does not imply *marketing/community/team supply locked*.
- **Decision:** `WATCH / SPECULATIVE_ONLY_CONDITIONAL`. No unconditional opening snipe or initial large-size allocation. Candidate for a **fully-loss-tolerant, small spot-only discretionary test trade** after official issuer CA & machine.fun origin, first true AMM/LaunchLab price+route/reserve, holder/concentration/permissions/lock checks, accepted slippage quote and local budget cap. If price jumps before being executable, do not chase. A conservative possible planning bound could be **$50–$100 equivalent**, *only as hypothetical sizing guidance, not a commitment or a wallet balance claim*. No justified numerical fair FDV or payout probability without pool initialization and independent business data.
- Primary tokens shared through purported socials can be spoofed. The issuer had warned Oct20 about a **fake SXTH Raydium token** https://x.com/Sextus_Sensus/status/2112557952897077553 ; refuse any symbol-only substitute.

**Execution report:** inspected live read-only project official X and Telegram, official machine.fun site, public discovery of PM, current Git note. No live token mint/LP/ticker collision resolved onchain; no wallet action, automation, position update or signal registration.

---

## 2026-10-27 20:10-23:02 Telegram follow-up: 70 SOL LP and RaaS test scope

**Acquisition:** read-only context from user's connected authenticated Telegram Web chat `https://web.telegram.org/a/#-1004432036138`, `Sixth Sense Labs Community` → `General`, on 2026-10-27 approximately 23:08 Asia/Bangkok. Chronological conversation visible through 23:02; **not** proof entire historic chat was exported. `Todd | Sixth Sense Labs` visibly carried group `Owner` badge. Cross-check user’s open official `https://x.com/Sextus_Sensus` and `https://x.com/machinedotfun` tabs: no observed new SXTH canonical mint / deployment-specific launch post in loaded feed. Machine.fun homepage `https://machine.fun/` on 2026-10-27 continues `Phase 2: FIND THE NEXT UNITREE — LOADING`. All group-owner disclosures below are **ISSUER CLAIM / UNVERIFIED ONCHAIN**.

### Material liquidity and issuance statements

- At **20:17** a member asked whether the contract address would first be posted on X. Owner replied `Brother wait and find out please we’re avoiding snipers`, then `Will be posted on both official channels` and `We want to ensure the most fair launch`. **Do not assume an advance mint publication or a prelaunch buy route**; actual time, LP pool and canonical mint remain unverified. A separate member floated stealth launching, but Owner did not explicitly endorse that exact mechanism.
- **20:41–20:52:** a member questioned why about 90% supply looked project-controlled at launch. Owner replied `It’s all locked`; `We’re holding 15%` `At launch for hardware development`; `Other than that we hold nothing for 18 months`; `There is a six month cliff and than 12 month unlock with a major position going to community incentives`. When the 10% LP allocation was cited, Owner said `That’s locked`, `Our liquidity we will be locking and sharing at launch that it’s locked`, `It will be locked and visible upon launch`.
- **20:50** Owner said verbatim: `We’re putting up 70 SOL of our own cash to ensure stability during launch reducing sniping`. This is **promised SOL-side initial LP capital**, no transferred SOL, canonical vault, mint, LP lock authority/expiry, pool reserves or contract events verified. LP lock, even if later genuine, does not protect against concentrated sell flow or guarantee a profitable exit.
- **Material interpretation conflict:** official previously published `https://sixthsenselabs.xyz/Tokenomics` distribution was Treasury **30%**, Team **25%**, Community **20%**, Marketing **15%**, Liquidity **10%**; release plan mentions **6-month cliff then 12-month vest**, opening 22.5m marketing tokens, and target 70m SXTH in DEX LP. Owner's `we hold 15% at launch for hardware development` is **ambiguous as to wallet/control, locked versus liquid status and exact allocation**, and `hold nothing for 18 months` is **not unambiguously equivalent** to 6-month cliff followed by monthly releases months 7–18. Ask for final minted vesting contracts and effective unlocked treasury/marketing/community control; do not assert the ambiguity has been resolved.
- **Conditional math, NOT owner-confirmed exact reserves:** if precisely 70m SXTH are placed in a simple 50:50 constant-product LP against exactly 70 SOL, initial marginal spot price would be `0.000001 SOL/SXTH`; 1 billion max tokens times that price = `1000 SOL` hypothetical FDV. This is **illustrative only**. A launch curve/concentrated LP/antibot launch platform may produce wholly different auction pricing. A 70 SOL reserve against public market demand is shallow; quoted costs and sell-side market impact must be simulated against **actual runtime pool**.
- There was no new numeric opening market cap/FDV, validated official CA, firm UTC/Bangkok sale time, documented anti-sniper rules, public pre-sale cap, first transferable block, verified LP deposit or locked LP certificate in the examined messages.

### Business reality and marketing

- **22:18–22:19 Owner:** `RaaS back end is up and testing is about to begin`; describes intended end-to-end acceptance path `sign in, book, pay, robot run, results`, followed by temporary work environment deletion and delivery of customer-requested data. **Owner states testing has not yet passed**, and supplies no first successful paid booking, Solana USDC receipts, order cohort or customer revenue. Classify `RAAS_BACKEND_READY_CLAIM / E2E_TEST_PENDING / COMMERCIAL_TRACTION_UNVERIFIED`.
- **22:42** Owner said they would show progress via a stream. **22:45** Owner promised `building in public updates every Friday!`. These are promised demos/cadence, not successfully completed deployments or permitted scheduled monitoring.
- **20:36–21:02** Owner floated a potential collaboration with a YouTuber with `over 15 million subs`, then said `A potential hack smith collab is coming`, `Still have to further talk with James`, and hopes they will use smart glasses and smartphones to create a dataset. Owner specified the collaboration `Doesn’t involve crypto yet`; focus first on demonstrating tech before incentive campaigns. **Not a signed collaboration, marketing reach, paid customer or token listing confirmation.** Verify the creator's own first-party statement and a demo before incorporating into a valuation.
- **20:10** Owner complained of X distribution/shadow-ban changes and asked members to promote the account. Community member at **23:00** posted a promotional seven-tweet thread, which Owner acknowledged at 23:01. This activity is **community-led promotional engagement**, not evidence of organic paying traction. Avoid counting promoted views as product demand.

**Decision impact:** meaningful improvements to launch intelligence, initial LP estimate and proposed RaaS functional acceptance test; no reliable quantifiable revenue or actual execution-ready SXTH pool. `WATCH / NO_GO / MAINNET_MINT_UNVERIFIED / LAUNCH_TIME_UNVERIFIED / LP_70_SOL_ISSUER_CLAIM / RaaS_E2E_UNTESTED`. No trade, wallet signature, monitor, automation or live deployment performed.

---

## 2026-10-27 19:49-19:54 Telegram screenshots: possible first machine.fun launch and backend update

**Provenance:** Two screenshot images directly uploaded by the user from Telegram `Sixth Sense Labs Community` General on 2026-10-27 at around **20:03 Bangkok**, displaying messages around 19:49-19:54. Attempts to re-read user's browser tab in this turn returned `Browser access requires the originating browser context`; statements below are grounded in the screenshots only, without claiming a fresh DOM or complete history scan. Sender `Todd | Sixth Sense Labs` appears with Telegram **Owner** badge.

**Launch venue hint now updated:**
- In reply to the prior `do you guys plan on being the first launch on machine.fun?` question, **Todd (Owner)** explicitly said at 19:49, `To our knowledge we will be the first!`.
- **Classification: project owner claim of expectation/coordination, not a machine.fun signed listing or actual launch transaction.** It **supersedes the previous entry's `question unanswered` status**, but the launchpad itself has not independently confirmed SXTH first-listing exclusivity, fee model, swap curve, anti-bot rules, pool identity, or start time.
- Separately, community participants claimed every machine.fun issuer must undergo vetting and show hardware files/prototypes; Todd agreed (`Ofc` and subsequent positive transparency comments). This is **unverified procedural assertion/owner endorsement, not a formal third-party audit or real investor downside protection**. No public vetting report was cited.

**Actual product development update:**
- At 19:49, Todd said: `Massive update on the backend here for you guys we are close to being able to create full on data sets; using our capture apps!`
- The visible follow-up progress message states dataset creation is advancing with **dataset registration, metadata generation, version control, synchronization and automated validation**. Team is still **integrating/testing backend and dashboard** and promises updates after final validation.
- **Classification: issuer/Telegram participant-reported engineering work in progress, not independent code or production deployment confirmation**. Words `close to being able` and `testing` signal an incomplete end-to-end production acceptance. No public canonical commit, deployed backend, processed dataset file, paying customer, sale of a dataset, rental revenue, or verified cash receipt was supplied.
- User-investment implication: stronger evidence of a near-term planned **machine.fun fair launch** and identifiable implementation components, but **NO upgrade to verified paid business maturity** and no basis for inventing revenue, valuation, default initial cap or launch price. Launch before full data-product validation can create post-launch delivery risk. Potential first-launch visibility is promotional, not a quantifiable payout or ROI.

**Execution status remains:** `WATCH / OWNER_CLAIMS_FIRST_MACHINE_FUN_LISTING / ACTIVE_INTEGRATION_TESTS / CA_UNVERIFIED / TIME_UNVERIFIED / NO_GO`. Earlier group-owner acknowledgement of Wednesday remains attributed as a proposed weekday (UTC/Bangkok clock unconfirmed). No wallet actions, no new monitoring or alerts, no authorized trade.

---

## 2026-10-27 authenticated Telegram General: Wednesday launch acknowledged by group Owner

**Evidence:** read-only through the user's connected, already open Telegram Web at `https://web.telegram.org/a/#-1004432036138`, chat title `Sixth Sense Labs Community`. The visible group header says 58 members, with `General` and `Tech Talk`. Messages below were present under the UI's `Today` heading on **Tuesday 2026-10-27**. UI times are as displayed; the actual timezone of the announcement is not explicitly stated. Only currently rendered chat messages were inspected; this is **not exhaustive history**. The group was authenticated as the official community by issuer X post `https://x.com/Sextus_Sensus/status/2110735046340468988`. Telegram `Owner` badge is evidence of in-group authority, not independent cryptographic identity verification.

**Launch date attribution:**
- Around 01:38 displayed chat time, group member Benny Bear wrote `Confirmed for a Wednesday Launch!`; `Todd | Sixth Sense Labs` showed Telegram **Owner** role and replied **`Yessirrr`**. This is a strong **owner-endorsed plan for Wednesday** relative to Tuesday Oct27; nominal calendar day **Wednesday Oct28 2026**, but **no exact UTC/local launch clock or confirmation that Bangkok time is also Oct28**, and no issuer public primary post with timestamp or live contract. The earlier unrelated reply `29th 2 pm UTC?` on X is user speculation, not confirmed. Keep `LAUNCH_WEEKDAY_OWNER_ACKNOWLEDGED / UTC_TIME_UNVERIFIED`.
- About 01:40, Owner wrote `Snipers won’t be able to reap and farm liquidity either. This is a true fair launch with some serious tek behind it`. **Issuer's promise only**: the mechanism/launchpad, anti-sniper transaction rules, code/contract, price curve, tax, delay and routing are **UNVERIFIED**. Do not claim anti-MEV safety or execute a buy from marketing text.
- A member asked `Will CA be posted here or on X first?`; Owner answered around 01:42 `All official updates regarding will be posted on all official platforms`. No verified SXTH mint shown in these messages.
- A member asked `what mc is it launching at?` around 01:53; another member answered `Fair launch`; **Owner did not give a numeric opening MC/FDV or price in the visible exchange**. Thus price and accepted-cap remain unverified.
- Member `I heard that there will be two pools`; Owner around 02:38 replied `not immediately at launch!`, then `Before end of year`. This is **two-pool plan reported in conversation, not two verified live pools**. On being asked `So it’ll start with sol, yeah?`, Owner answered `You’ll find out soon enough!`; opening quote token/SOL pair still **unconfirmed**.
- Owner also pinned `Sorry for the slow week guys ... Will be powering up ahead of launch ...`, a promotional statement without contract/date or operating metrics.
- Group member asked `do you guys plan on being the first launch on machine.fun?`; at the time of this read the message was **unanswered in visible history**. `machine.fun launch` is therefore **UNCONFIRMED**, and the Telegram conversations describe a possible Solana spot **fair launch** rather than proven pre-funded public ICO.
- At this observation there was **no authenticated mint, sale contract, opening price, public allocation, committed USDC, swap quote, or onchain liquidity**. No investment position or monitor state should be upgraded to live.

**Decision impact:** SXTH token launch is now **IMMINENT CLAIMED, OWNER ACKNOWLEDGED**, a substantial upgrade from mere site tokenomics. Keep investment classification `WATCH / NO_GO` pending publicly linked canonical mint + verified pool/launch contract, true price/initial circulating supply, anti-sniper execution rules and actual liquidity. Consider short-window live spot purchase only after separate user decision and actual chain verification. Initial liquidity pool may be single rather than two; number of pools at TGE is unverified.

**Research disclosure:** No Telegram messages were sent, no bots/accounts contacted, no transactions signed, no new monitoring/automation created. Screenshot/DOM did not expose actual onchain launch contract; the research record keeps clear evidence provenance.

---

## 2026-10-27 verified official X announcements and Telegram access boundary

**Source method:** 2026-10-27 read-only of the user's **live, logged-in browser tab** on `https://x.com/Sextus_Sensus`, using the browser's rendered DOM, plus user-supplied Oct 27 screenshots. This is stronger than a web search snippet and confirms the displayed account posts, not any private Telegram messages.

- **Official Telegram link:** 2026-10-15 original issuer X post `https://x.com/Sextus_Sensus/status/2110735046340468988` explicitly: `After tons of requests our Telegram community is now open. This is the only and official telegram!` It links `https://t.co/p5eQhgys0t` with an X preview titled `Sixth Sense Labs Community`. **The shortlink could not be resolved by available public tools; group permalink, participant count and message history NOT_VERIFIED.** Do not falsely claim reading the chat, and do not fabricate Telegram quotes. The project source vouches for the link, subject to freshness.
- **Explicit fake SXTH warning:** On 2026-10-20 original first-party `https://x.com/Sextus_Sensus/status/2112557952897077553`, the issuer warned: `A fake $SXTH token has appeared on @Raydium claiming to be us. We have not launched any token. This is not legitimate. Do not buy or interact with it. We'll only ever announce an official launch from this account.` This **direct issuer announcement** is material to token canonical identity; confirmed official claim as of Oct20, but not proof that no later issuer deployment occurred.
- **Fresh 2026-10-27 teaser:** Official pinned `https://x.com/Sextus_Sensus/status/2114825308046340135`: `The Machines are coming!` with **11-second prerecorded countdown video**. User screenshot shows frame `T-41:49:54`, but the video is prerecorded, **not an anchored live block timestamp**. A public reply guessed `29th 2 pm UTC?` = October 29 **21:00 Bangkok** if correct, **unconfirmed by issuer**. Do not interpret countdown alone as token sale, fixed launch day or a guaranteed mint time.
- **Current sale outcome from checked public first-party sources remains** `TGE/ICO_DATE_UNCONFIRMED / OFFICIAL_SXTH_MINT_UNCONFIRMED / PUBLIC_PRICE_UNCONFIRMED`. Future issuer announcement must be verified on original X + canonical official mint/launch transaction before considering a trade. `machine.fun` may be partner/tag but an account tag does not verify an issuance date.
- **Telegram verification:** We located the official source post but did **not** actually access or review individual Telegram messages. Public search on `t.me` and Telegram directories produced no reliable indexed matching chat; the short URL was blocked in public web tools. If an authenticated group tab becomes accessible in the user's connected browser, read its on-screen messages read-only, separate admin statements versus participant claims, and then reassess.

This incremental record changes only fact provenance, fake-token risk and official-community discovery; it does not authorize new scheduled monitoring, wallet actions, token transfers, or production trades.

---

## 2026-10-27 official tokenomics, RaaS record and ICO/PM recheck

**Decision: WATCH; no officially verifiable live SXTH ICO/TGE, sale URL, launch date, allocation price, hard cap, accepted raise, mainnet SPL mint or DEX liquidity at time of review.** This dated observation supersedes the 2026-10-09 claim of unconfirmed *published* tokenomics, but does **not** upgrade a website-issued plan to a proven deployed onchain token.

### Official first-party tokenomics now published

- Primary https://sixthsenselabs.xyz/Tokenomics ; current issuer **proposal**: fixed hard cap 1,000,000,000 SXTH; treasury 300m (30%), team 250m (25%), community 200m (20%), marketing 150m (15%), liquidity/listing 100m (10%). These allocations now have first-party documentation; earlier Grok-derived percentages are corroborated as **issuer assertion**, not onchain-confirmed balances.
- Plan at TGE: marketing 22.5m released for circulation; liquidity 70m planned for DEX pool; 30m unused listing reserve subject to subsequent vesting. Total **potential unlocked/LP inventory is 92.5m (9.25% of fully diluted supply)**, but **70m LP inventory is not automatically seller-owned freely circulating supply**. Team/treasury/community have zero scheduled first-six-month releases; months 7–18 linear release, DEX LP unlock mentioned at month 12. Verify actual lock contracts once mint/LP exist.
- Site says monthly real product/fee revenue allocation: **50% buyback, 25% treasury, 15% marketing, 10% operations**. Of tokens actually bought, **70% burn / 30% bond**. This is a **program proposal**, not established cash revenue, actual onchain buybacks or minted burn events. Website's $100k/month revenue slider is an **illustrative what-if**, NOT achieved sales or claimed revenue.
- **Missing key buyer economics:** no stand-alone public-sale allocation in this five-bucket table, no sale contract, ICO token price, investor lockup or hard cap, and no primary documentation tying a live SXTH listing to machine.fun.

### Business reality: more evidence than Oct 09, but no paid sales confirmed

- Main project https://sixthsenselabs.xyz/ now links https://sixthsenselabs.xyz/RaaS ; RaaS currently advertises Booster K1 humanoid rentals by the hour against Solana USDC via Phantom, with operator-run and remote-view sessions; teleoperation "coming soon". The page's booking date/time widget displayed `Failed to fetch` in the read-only web response; no check-out test, wallet access or payment performed.
- Primary machine record https://machines.peaq.xyz/machine/72070072199752035588865179268289351973289970295321663729669764070389137395940 identifies Booster K1, machine DID `did:peaq:72070072199752035588865179268289351973289970295321663729669764070389137395940`, Solana owner `2xaFTukaVvsp3eyPbPFtm76HGC1dX4U5kjgWWrNpAphq`, Solana machine account `C3iHPJ1T7kJ9bitqcPN6u33ferq1mv1y6hbe9c5mitY5`, Basic bond 4.73 PEAQ, activation **2026-10-12**. The public peaq record exposes onboarding events and a Solana transaction: https://solscan.io/tx/4LtnoUVPKNwg2e3TiRHMVvgxnKumKVMcmH6aXLAofkkK4EfWzixTJmS2ju6VjXfQMEYGaNr4HC3Z3wZ1s6FPU2B2 . This corroborates **onchain machine registration/record existence only**, not real customer rental, operation hour count or business revenue.
- https://sixthsenselabs.xyz/Modulus describes a ceiling multi-camera/LiDAR capture instrument, with "book a capture cell" sales lead; neither installed customer units, bookings, revenues nor dataset sales verified.
- **Revenue, paid users, completed rentals, USDC transactions attributable to verified customer bookings, unit economics, DAU/retention, external financing, staff and audited audited operating cash flow = UNVERIFIED.** Keep operational-account registration separate from actual product income. Stage: multiple first-party working-looking product pages + onchain machine identity, **not proven commercial scale**.

### Token-sale / PM verification

- machine.fun main https://machine.fun/ still displays **Phase 1 hardware founder applications**, Phase 2 `FIND THE NEXT UNITREE — LOADING…`. Its https://foundry.machine.fun/ is a **free application for hardware founders** and physical manufacturing assistance, not a token-sale deposit or SXTH allocation. No current SXTH-specific listing on these pages.
- Checked 2026-10-27 public search of first-party issuer site, litepaper, machine.fun and indexed X; X full account feed was blocked in the available web reader. Could not independently confirm that some inaccessible newest social post had announced future sale, so do NOT assert there is definitively none.
- Mandatory project-specific PM searched by `SXTH`, `Sextus Sensus`, `Sixth Sense Labs`, launch, FDV, raise and IPO on publicly accessible/indexed **Polymarket, Kalshi, Limitless and Predict.fun**. **No verifiable SXTH-specific live contract, price, probability, resolution terms or liquidity located**. State `未检索到可验证的项目专属 PM 市场`; does not prove absence on unindexed/private venues or that there is zero market expectation.
- A separate DexScreener `gSense` pool named "Sixth Sense Labs" is **NOT issuer-verified SXTH mint** and must not be presented as official or usable sale access.

**Next material gate:** a first-party signed SXTH token sale URL and Solana mint, actual project-specific launch config and price/accepted cap, initial liquidity and lock proof, then verify real paid rentals/USDC inflows. No wallet transactions or new alerts/monitoring were created.

---

## Historical 2026-10-09 snapshot (superseded where updated above)

## Canonical identity and first-party sources

- Identified project: **Sixth Sense Labs**, also referenced as **Sextus Sensus**, website https://sixthsenselabs.xyz/ .
- Official-facing technical document: https://sixthsenselabs.xyz/LitePaper .
- Project's X account given by user: https://x.com/Sextus_Sensus .
- Proposed ticker according to user and prior Grok research: **SXTH**; canonical mint and official token-sale announcement **NOT VERIFIED**.
- Expected Solana token and machine.fun launch relationship: **LEAD / NOT VERIFIED AS A LIVE SXTH LISTING**. A common acronym match (`SXT` or `SXTH` from unrelated projects) is not evidence.
- Machine project entry given by user: https://machine.fun/ .
- Foundry program: https://foundry.machine.fun/zh-cn/ .

## Critical clarification: Foundry form is not an SXTH token ICO

Directly checked on 2026-10-09: https://foundry.machine.fun/zh-cn/ is an application form for **hardware/robotics founders** seeking a 5-day manufacturing/industry visit, potentially funding and commercialization help. Inputs include founder/company name, prototype stage, delivery schedule, team headcount, funding amount, deck/CAD/BOM and referral code. FAQ says applying is free and requires no equity transfer.

Its text says machine.fun may eventually facilitate project/machine tokenization. It does **not** show an SXTH launch listing, public allocation, ICO/IDO orders, investor sign-up, Solana token mint, tradeable bonding curve, launch time or sale price. A prospective SXTH token buyer should **not** complete the founder application as if it purchased or reserved SXTH; do not send SOL/USDC to any third-party presale wallet.

machine.fun front page https://machine.fun/ showed Phase 1 BUILDING PHYSICAL AI? APPLY TODAY and Phase 2 FIND THE NEXT UNITREE — LOADING as of checked date. This supports a future possibility, not proof of an SXTH token listing.

## Actual project stage / reality check

Confirmed first-party publication:
- Robot training data concept: synchronized first-person video (smart glasses/Quest/Vision Pro), LiDAR spatial capture (iPhone/iPad), calibration/sync and dataset export in HDF5, ROS Bag, RLDS and Open X-Embodiment formats.
- Website lists product architecture and supported hardware; lite paper provides a sample **illustrative** dataset schema and illustrative performance discussion.
- The site has a `Request access` path; no independently verified paying customers, revenue numbers, public datasets, successful actual recordings or attributable canonical SDK Git commits yet.
- Real-world ecosystem lead: Auki's public mentions and interactions with @Sextus_Sensus at robotics events (https://x.com/Auki). This supports attendance/interaction; it does not prove investment, distribution partnership or signed commercial sales.
- Product maturity: **Level 1 documentation/concept, potentially experimental development; independent executable production proof lacking.**
- Team/financing: named founders, legal entity, external investors, financing receipts, investment terms and historical exits **UNCONFIRMED**.

## SXTH token distribution claims are leads only

Prior Grok-derived claim supplied by user: proposed total 1,000,000,000 SXTH, treasury 30%, team 25%, community 20%, marketing 15%, liquidity 10%, 70% fees burned/30% bonds. **SOURCE_STATUS=UNVERIFIED THIRD-PARTY SUMMARY**. Project website and lite paper inspected 2026-10-09 do not independently establish signed tokenomics, issuer-controlled contract addresses, actual allocations, burn/bond implementation, initial circulation, vesting or token holder rights.

Do not repeat these as `CONFIRMED`; do not compute a launch FDV or an investment return from an unconfirmed issuance.

## Buyer checklist / participation path

1. Follow https://x.com/Sextus_Sensus and https://machine.fun/ for an issuer-authenticated SXTH listing and exact primary-sale URL. There is currently no independently verified SXTH ICO action to execute.
2. On an official launch listing, verify canonical Solana mint, issuer identity, launch authority, platform's actual smart contract, token supply, decimals, mint/freeze authorities, vesting, initial LP and treasury ownership.
3. Check whether issuance is a fixed-price ICO, standard bonding curve / Raydium LaunchLab, or other mechanism. The current Foundry page **does not establish** a Raydium LaunchLab sale.
4. Get exact TGE/launch clock, minimum deposit, wallet/geographic requirements, payment token/network, buy ceiling, fee and how USDC/SOL is refunded when participation fails. Check official docs and mainnet transactions.
5. At first actual open, assess active buys, real pool/reserves, executable $50/$100/$300 exit quotes and slippage, holder concentration and insider launch cost; do not FOMO into an unverified ticker.
6. If acceptable, user manually signs from a suitable wallet; only after confirmed allocation/purchase record position and capital in existing Mission authority paths.

## Status / value thesis

- User explicitly intends to participate if/when valid official issuance conditions exist, but amount not specified. No capital reserved automatically.
- A real embodied-AI robot dataset business is plausible; this project has not established measurable paying adoption or token value capture.
- Research continues interactively on user request. **No new automation/monitor or live trading.**
