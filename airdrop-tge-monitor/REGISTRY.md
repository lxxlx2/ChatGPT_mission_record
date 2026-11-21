# Airdrop / TGE Canonical Registry

Active scheduled minutes (2026-10-10 user-approved): hourly HH:00 Asia/Bangkok. Existing urgent set and hour % 4 shard mapping remain unchanged. Historic HH:50 logs are legitimate past records. ForecastFDN was removed on 2026-11-21 after full principal refund. The 2026-11-21 issuer-status reconciliation below removes the independent 01 Exchange Shard-2 entry, preserving its N1 rights mapping, and reclassifies four active entries to rights-only/claim-only without changing the original hourly task ID, time, urgent-five or shard rotation.

Updated: 2026-11-21 (reconciliation: 01/N1 acquisition; Concrete/Cambria TGE completed; StandX TGE cancelled; OnRe/Reflect distinct)

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
- StandX / @StandX_Official — **RIGHTS_ONLY, PLATFORM_TGE_CANCELLED**; check DUSD airdrop/redemption and verified partner beneficiary rights, not StandX native TGE
- Perena / @perena
- TurboFlow / @TurboFlow_xyz
- MetaMask / @MetaMask
- Makina / @makinafi
- Rho / @Rho_Labs

## Shard 1
- Surf
- Hylo / @hylo_so
- OnRe / @onrefinance — **INDEPENDENT_ACTIVE, ONyc already circulating**; no verified OnRe/Reflect merger or separate future governance TGE
- Reflect / @reflectmoney — **INDEPENDENT_ACTIVE, RECOVERY_RIGHTS_ONLY**; USDC+ / Drift-related recovery changes; no verified Reflect governance TGE
- Tydro / @tydrohq
- Theo / @Theo_Network
- Neutrl / @neutrl_labs
- Concrete / @ConcreteXYZ — **CT_TGE_COMPLETED, CLAIM_ONLY**; no second launch alert, check verified unclaimed rights/deadlines only

## Shard 2
- Relay / @RelayProtocol
- Titan / @Titan_Exchange
- Reya / @reya_xyz
- N1 / @N1Chain — **includes legacy 01 Exchange points and rights**, 01 separate app sunset 2026-07-08
- Figure AI / @Figure_robot
- Pond / JoinPond / @JoinPond
- OhBabyGames / @OhBabyGames
- Claynosaurz / @Claynosaurz
- HEEBOO / @HeebooOfficial

## Shard 3
- Cambria / @playcambria — **RSGP_TGE_COMPLETED, CLAIM_ONLY**; check legacy player claim and previously funded stake recovery, no second TGE alert
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

## 2026-11-21 canonical project lifecycle reconciliation

This is a correction of *existing* monitored projects, not an addition to scope, scheduled task, or alert stream. Keep historical email/run archives immutable. `TGE_COMPLETED` or `TGE_CANCELLED` stops fresh first-launch announcements; it does not automatically close still-valid user rights. Expired or previously delivered claim-open messages remain deduplicated under ACTION_GATE and state/known-events.md.

| Canonical project | Evidence-confirmed status | Existing monitor action / no-repeat rule |
|---|---|---|
| OnRe (@onrefinance) | Active independent reinsurance protocol with ONyc circulating; no verified merger with Reflect. Official https://www.onre.finance/resources/announcements | Keep independent identity. ONyc is a yield-bearing asset, not proof of a fresh future OnRe governance TGE. Alert only first-party rights change; no speculative token claims. |
| Reflect (@reflectmoney) | Separate active Solana yield/tranche platform; USDC+ recovery portal is active after Drift April 2026 incident. https://reflect.money/ ; https://claims.reflect.money/ | Keep independent rights status. Original recovery claim-open already emailed 2026-09-12; only new material first-party recovery/eligibility/deadline changes may be alerted. No merger with OnRe established; Reflect reUSD underlying is Re Protocol, not OnRe. |
| Concrete (@ConcreteXYZ) | CT **TGE_COMPLETED 2026-09-30**. Exchange first-party confirmation https://blog.kraken.com/product/asset-listings/ct-is-available-for-trading | **CLAIM_ONLY**: stop TGE / listing-preflight notices. Preserve unresolved wallet-specific CT claim and distinct additional USDC right only if independently proved, no repeat CT claim-open (already emailed). Do not link unverified lookalike Foundation websites; issuer root https://concrete.xyz . |
| N1 / legacy 01 | N1 developer publicly confirmed **ACQUIRED_01 2026-07-08**; https://www.nullstudios.com/blog/n1-01 . 01 separate app sunset; all 01-earned points recognized on N1. | Remove independent 01 Shard-2 entry; N1 is sole canonical project for linked points. Do not erase 01 points or conclude they became tokens/cash. Echo intermediary rights remain a separate mapped user-deal evidence question. |
| StandX (@StandX_Official) | **PLATFORM_TGE_CANCELLED 2026-10-15** and wind-down. Official https://x.com/StandX_Official/status/2110613283967230232 ; project shutdown notice https://standx.com . No native token TGE. | Keep original Shard-0 member **RIGHTS_ONLY** for DUSD airdrop (official Nov2 opening; claim cutoff 2026-12-31 08:00 UTC), positions 2027-01-15, DUSD redemption/withdrawal 2027-01-31 and independently verified distinct partner rights. Do not send another 'StandX token launching' alert. Same DUSD claim-open version requires prior Sent dedupe; personal allocation UNKNOWN. |
| Cambria (@playcambria) | **RSGP_TGE_COMPLETED 2026-10-29 15:00 UTC**, Base contract `0x44B63aF715D5ef02CC3646a6CE96875e11d69E85`, first-party https://lobby.cambria.gg/genesis/ and MEXC https://www.mexc.com/announcements/article/first-in-market-17827791539281 . | Retain Shard-3 **CLAIM_ONLY** for outstanding game-derived RSGP and old Blast/Abstract stake recovery. Already-notified TGE (Oct28 email) never re-emit; personal amount and remaining claim status UNKNOWN. |

**Scope guard:** fixed always-hourly urgent-five unchanged (Concrete retains urgent placement solely for unresolved rights, not future first TGE). Existing Shard 0=10, Shard 1=8, Shard 2=9 after 01 dedupe, Shard 3=9. No new automated tasks, no production trading or emails, no activation of already-closed Forecast/Loopscale/Abstract or completed unrelated deals.

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
- N1 / 01 Exchange legacy: N1 acquired 01 and absorbed the app and historical 01 points on 2026-07-08. Maintain any user 01 points under the N1 record. Preserve Echo/SPV rights checks only for any separately evidenced user capital commitment; do NOT assert that an Echo private deal was automatically converted into N1 token/points.

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

- Forecast / ForecastFDN / @ForecastFDN — **USER_SUPPRESSED / FOUNDING_PRINCIPAL_FULLY_REFUNDED** on 2026-11-21. The original 100 USDC Founding deposit was returned in full by the original Base Safe to the user's original wallet, verified onchain at 2026-11-20 22:51:59 UTC (2026-11-21 05:51:59 Bangkok), tx `0xff0dee7e…0ad6a`. Remove Forecast from Shard 1 and exclude it from independent TGE/airdrop scanning, dynamic urgent inclusion, refund/claim notifications, and deal-rights alerts. **Do not infer from principal refund that no separate token/rewards ever exist; suppression is the user's explicit request.** Preserve old audit records and the chain evidence in `research/projects/forecast/founding-deposit-custody-20261121.md` on the separate research branch; do not reactivate unless user explicitly requests it. All other project monitoring remains unchanged.

- Abstract / @AbstractChain — **USER_SUPPRESSED** on 2026-10-07. Remove Abstract/ABS from active TGE/airdrop monitoring, including hourly urgent checks, shard discovery and rights monitoring. Historical records remain for audit only. Reactivate only if the user explicitly asks to monitor Abstract/ABS again.

- humans& / @humansand — **CLOSED**. The user's Echo/Alpen Capital allocation was fully refunded on 2026-09-24. There is no remaining user entitlement or capital at risk in this deal. Exclude humans& and its Echo/Alpen deal channel from hourly shards, urgent checks and rights monitoring. Historical records remain for audit only. Reactivate only if the user explicitly enters a new humans& exposure or asks to monitor it again.


## Rights-source mapping requirement — 2026-09-29

Tier B user-rights evidence is valid only for an intermediary explicitly mapped in this registry.

A generic investor, news outlet, KOL, community moderator, aggregator, or unrelated platform is never a Tier B source.

When a deal is CLOSED/FULLY_REFUNDED, remove it from active discovery before network work where practical and persist the state in `state/known-events.md`.

Underlying-company financing/valuation announcements do not trigger a rights alert unless an explicitly mapped deal host/SPV/syndicate/group lead confirms a user-level allocation/term/fee/conversion/transfer/redemption/settlement/distribution impact.

## 2026-10-13 execution fairness override
The four existing shard membership lists above are unchanged. Scheduled shard continues Asia/Bangkok `hour % 4`. If primary source gaps persist across several days, the scheduler MUST NOT repeatedly choose the same group solely because it lacks a complete-success timestamp. Recovery picks the oldest actually attempted group once per four documented runs at most, and must rotate past it afterward; `partial` updates attempted clock only, NEVER full-coverage proof. A shard that has only inaccessible first-party pages stays SOURCE_GAP, not false success. Surf remains in Shard 1; any imminent official member claim/due date may enter the existing dynamic urgent set only after a fresh first-party source check, without altering membership or sending on a mere countdown. Latest AUTOMATION_RUNTIME.md controls fairness and terminal evidence.

## Official non-X source anchors and collision guard — 2026-10-16

The 2026-10-16 02:05 shard-2 terminal audit reported source gaps for Relay, Titan, N1, 01 Exchange, and JoinPond. The following first-party issuer/site locations were actually retrieved in English on 2026-10-16 and are usable as fallback discovery anchors when X is inaccessible. These are SOURCE ROUTES, not evidence of a new claim, TGE, allocation or distribution:
- **Relay / @RelayProtocol**: https://relay.link/blog/announcements and https://support.relay.link/en/articles/9261056-when-will-you-have-a-token . Relay's official FAQ is old (2024), so a static no-token statement cannot establish that today's token status has freshly changed or that a present-day negative finding is exhaustive. Verify current announcements before classification.
- **Titan / @Titan_Exchange (Solana aggregator)**: https://titan.exchange/ (currently redirects to https://titan.exchange/pro). Identity guard: `titanexchange.io` describes a separate Titan Trading/bot platform. Never mix it with the monitored `@Titan_Exchange` Solana aggregator.
- **Pond / @JoinPond**: https://joinpond.ai/blog and https://docs.joinpond.ai/docs/terms-of-use ; issuer site explicitly connects brand and platform. Do not mistake general AI-marketplace bounties, completed tasks, or company funding for a verified token/TGE entitlement.
- **N1 / @N1Chain**: official announcement channel https://t.me/s/n1announcements references original @N1Chain posts and https://docs.n1.xyz/learn/protocol/prime ; the docs original was unavailable at this check, so keep its direct-page status SOURCE_GAP unless actual first-party readback succeeds. Separate general trading-product releases from a rights event.
- **01 Exchange / @01Exchange**: historical independent identity only. SUPERSEDED by direct 2026-07-08 N1 issuer announcement https://www.nullstudios.com/blog/n1-01 : N1 acquired 01, retired independent app, and recognized prior 01 points on app.n1.xyz. No separate 01 token/TGE monitoring; check old user points through N1, with wallet-specific status UNKNOWN. Mapped Echo investment rights remain independent if separately evidenced.

At the next *existing* shard-2 rotation, attempt these bounded, canonical fallback anchors before declaring each domain inaccessible; record individual actual retrieval status, dated source content and source gaps. Never retroactively change the 2026-10-16 02:05 `PARTIAL` into success, invent a verified source observation, expand shard membership, or send a no-change email. All other source gaps, including Concrete additional USDC, Space extension and StandX original X full-text, remain open until equivalent valid first-party evidence is actually obtained.

## Existing StandX beneficiary relationship (not a new independent project watch) — 2026-10-16

- existing_project_id: standx (Shard 0)
- external_issuer_candidate: NeoSoul / DNA, official X https://x.com/NeoSoulAI , project https://neosoul.ai/
- canonical_relation: `NeoSoul issuer -> StandX community beneficiary`, NOT `StandX platform native token`
- candidate_event: `neosoul:dna_standx_community_allocation:2026-10-15`
- official_BINANCE_WALLET_Alpha_announcement: https://www.binance.com/en-IA/square/profile/binancewallet
- secondary_issuer_attributed_announcement: https://www.binance.com/en/square/post/10-15-2026-neosoul-plans-dedicated-dna-airdrop-for-standx-community-377570746498100
- current_issuer_primary_commitment_direct_readback: SOURCE_GAP
- beneficiary_entitlement, snapshot, claim_url, claim_time, user_allocation: UNVERIFIED
- status: HIGH_MATERIALITY_VERIFYING_PARTNER_RIGHTS, no separate project/full scan and no ACTION without authoritative proof
- reject_identity_collision: legacy NEO cryptocurrency/Neo blockchain is not NeoSoul DNA; Binance Alpha Points claim is separate from proposed StandX compensation.
- required_existing_lane: StandX Shard-0 RIGHTS_ONLY and applicable dynamic urgent rights deadlines, never a native StandX TGE watch; on issuer-verified new action apply ACTION_GATE and Gmail dedupe.

## Cambria cross-chain TGE rights mapping — 2026-10-28

Cambria / @playcambria is ALREADY registered in Shard 3. Monitor **the game's user entitlements over every actual reward distribution chain**, including Game activity on Abstract/Blast/Ronin with token delivery on Base, without adding Abstract/ABS as an independent monitored coin. Canonical official issuer https://cambria.gg/ , token docs https://docs.cambria.gg/genesis/usdrsgp , official token/season Journey https://lobby.cambria.gg/token/ , original X https://x.com/playcambria . Cambria $RSGP on Base is a distinct family from old Duel Arena stake/AGW migration and earlier Genesis opt-in.

The Base RSGP token launched on Oct29 15:00 UTC (22:00 BKK), independently confirmed by MEXC listing and Cambria's official token page; the TGE milestone was already email-delivered on Oct28, id `1a1812a1f6802ecb`. It MUST be present in `state/known-events.md`. Do not re-alert unchanged TGE date. New claim eligibility, user allocation, official claim-open or time/chain/contract change may be a distinct actionable version, subject to Tier A issuer evidence and ACTION_GATE. No personal wallet amount may be inferred without actual authenticated eligibility/wallet proof.

Scoping is *existing Cambria*; do not widen registry or change shard scheduling. A change of **settlement chain** never suppresses rights already earned in another supported game chain.

## Galxe legacy platform exception (2026-11-20)

User expressly requested monitoring Galxe platform exit and unclaimed historic rewards. Add only Galxe (@Galxe; root galxe.com; app.galxe.com; associated Gravity and G) to the existing *dynamic urgent entitlement lifecycle* until the announced claim deadlines and separate asset-redemption milestones resolve. This is not a new automation or a new scheduled shard entry; fixed urgent5 and all shard0-3 project denominators remain unchanged. This platform is historically user-relevant, but user's personal account activity, amount and wallet eligibility are UNKNOWN.

Verified Tier A: https://help.galxe.com/en/articles/18361711-galxe-is-integrating-into-gravity-what-you-need-to-know (issuer announcement Nov 9 2026); https://x.com/Galxe/status/2119681030609105175. Issuer-confirmed: Galxe Quest/ID/Passport are winding down; Gravity and G continue. Dec 5 2026 final campaign participation day; Dec 15 2026 last day to claim previously earned campaign rewards, thereafter Galxe site read-only. Official claim-center https://app.galxe.com/claim-center advertises account-linked G holder, G Staking and Latch asset claims; linked address and amount require authenticated check. The help center separately says a process for Smart Balance, unwithdrawn staked G and G on Gravity Alpha will be announced. DO NOT infer that campaign Dec 15 deadline applies to all these separate assets or that claim-center accessibility proves an individual's balance.

One issuer-confirmed public claim cutoff for a previously used platform justifies a CONDITIONAL, deduplicated email to preserve possible user rights, even if personal allocation is unverified. The screenshot showing about 85 G is a third party's balance, NEVER this user's allocated G. Watch material updated claim instructions, new deadlines or account eligibility independently. Do not convert this exception to a new comprehensive watch list for unrelated platforms or introduce new backup monitors. Existing exclusion and source-tier gates remain.
