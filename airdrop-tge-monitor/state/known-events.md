# TGE / Airdrop Known User State

Updated: 2026-11-21 Asia/Bangkok, 28-project cross-asset lifecycle authority, user-known Galxe closure and original account stage separation.

Purpose: durable dedupe/state input for events already known, delivered, completed, refunded, explicitly closed, user-suppressed, or explicitly scheduled by the user within the existing rights monitor. This file is an input to ACTION_GATE.md.

Hard scope rule: do not create a new monitor/task/file for a user-specific future action. If the user explicitly gives a date/time for an action already within this existing rights-monitor scope, record it here as an unresolved known event so the existing monitor can act on it. No new monitoring scope may be added without explicit user authorization.

## LATEST 2026-11-21: event-driven progress + realization scope (supersedes older rights-only and token-only notes)

- user_scope: **KEEP all 28 preexisting project/issuer identities as approved**, including private investment and equity IPO/exit, crypto token TGE, investor allocations/settlement, tokenized RepublicX security payouts and relevant refunds. Distinct cash-out mechanisms need distinct original source routes, not separate autonomous monitors.
- original_automated_monitor: one existing hourly task, one rotating shard; fixed Urgent 0; four active shard counts **8/6/7/7 = 28**, current canonical project list in REGISTRY.md.
- user_01_points: 0; user_N1_points: 0. The user's **USD 1,000 original 01 Exchange investment through Echo** remains an exposure. Keep issuer identity **01 Exchange / N1**, with **Echo** merely its deal/hosting channel; do not list investment host as a separate project. Track both issuer milestone and mapped Echo investor-relevant distribution/refund/term changes, distinguishing original contract from independent points.
- equity_policy: Figure AI, Crusoe, Apptronik, Thalassa Robotics, 1X, Aalo Atomics and Republic's rTTOK are valid existing monitor entries. Their actual IPO/direct listing, M&A, major financing/valuation that affects asset realization, investor distribution, security-note liquidation or first trade may be a material NEW event. No unsupported inference that each company actually intends to IPO or that user holds identical shares.
- stage_dimensions: `issuer_stage`, `investment_type`, `tge_or_ipo_stage`, `liquidity_and_unlock`, `user_interest_source`, `eligibility`, `notice_sent`, `user_acknowledged`, `claim_attempted`, `claim_confirmed`, `investment_settled`, `excluded`, `last_verified_source_time`, `next_expected_milestone`.
- event_scope: original issuer or mapped actual investor platform, official filings/exchange notices and onchain evidence. Alert on verified investment-material progression, including firm launch/listing/IPO event, allocation/distribution, meaningful financing that alters valuation/liquidity outlook, deal cancellation/refund, new irreversible deadline, asset/security crisis or delisting, with prior-event dedupe. Generic PR, mere names or recycled old source do not qualify.
- proactive_rule: user discovering the news first is a monitoring **miss**, not a reason to start another watch. A user-provided screenshot/notification or attempted claim is `USER_AWARE_ASSUMED_HANDLED` for that event, not automatically `ONCHAIN_CLAIMED`; rectify prior missed one-time email only if it is genuinely needed and has no verified previous SENT. Do NOT add new project, urgent lane or platform-monitor scope without explicit consent.
- galxe_decision: issuer Nov9 platform closure was raised by the user Nov20 who already attempted to claim; treat user as having handled the alert. One corrected warning was previously emailed, Gmail Sent id `1a1f9a770fcb1c29`; `GALXE_USER_KNOWN / SUPPRESSED_CLOSED`. **Remove Galxe/Gravity completely from dynamic urgent, cross-shard special discovery, future notices and follow-on reward scans.** Never presume onchain payout from an attempted claim. Historical event and original Sent record remain.
- user_exclusions: Concrete, MetaMask, Claynosaurz, HEEBOO, Space (@intodotspace), StandX, Cambria, Forecast, Neutrl, Abstract, Grass, Backpack, Loopscale, humans& and completed UNICRED remain excluded per prior user direction. No dynamic reentry without explicit request.
- audit_standard: a single verified `issuer_stage` change requires dated first-party or mapped investor-host proof, comparison to last verified state, which user decision changes, and Sent+archive readback if emailed. An indexed homepage alone is `ATTEMPTED/SOURCE_GAP`, not `checked_no_update`; if no verified stage change then silent. Avoid false 0/28 completion claims.
- source_checkpoint_2026-11-21: OpenSea official FAQ confirms SEA postponed, not cancelled (https://support.opensea.io/en/articles/14324219-optional-fee-refund-faq); CoinList Reya sale terms TGE 50% / remaining 6 months but listing TBA (https://coinlist.co/reya); Crusoe Series F Sept17 valuation reported by issuer (https://www.crusoe.ai/resources/newsroom/crusoe-announces-series-f-funding); RepublicX rTTOK is contingent note tied to ByteDance qualifying liquidity event, no unconditional principal return (https://republic.com/rttok); Apptronik Nov17 GXO partnership issuer source https://apptronik.com/company/press-releases (general PR not independently an investor action); Base exploration remains noncommittal (https://www.base.org/blog/the-state-of-base-at-basecamp-2025); Polymarket Jun24 FAQ still says no token announced (https://help.polymarket.com/en/articles/13364250-does-polymarket-have-a-token). Remaining project original stage verification is PARTIAL/SOURCE_GAP until separately inspected; no new Gmail triggered by this reconciliation alone.
- authority: this top section and latest REGISTRY project lists supersede older paragraphs below that say `TGE_ONLY`, `Echo deal-rights only`, fixed urgent5 or Galxe dynamic urgent. Historical old notes remain archival evidence, not a current list.

## 2026-11-21 readback from original investment-platform emails (do not re-alert old correspondence)

### 01 Exchange / N1 investor equity and warrant
- last_direct_echo_support: 2026-10-29 UTC, original connected work Gmail message `1a18a194d58ed2fa`
- status: `INVESTMENT_OPEN_DOCUMENTATION_UNRESOLVED` according to last support reply, which merely promised to consult another team member
- original_issuer: `01XYZ CC Ltd` (legacy 01 Exchange; acquisition by N1 documented separately)
- user_original_subscription_amount: USD 1,000 (USER_CONFIRMED)
- initial_instruments: SAFE plus Token Warrant, user provided original terms in July correspondence; definitive issuer-conversion docs and liquidity not evidenced as completed
- user_01_points: 0; user_N1_points: 0
- old_support_on_2026-07-14: draft SAFE-holder documents not yet sent; transaction subject to final legal documentation at that date
- triggered_new_mail: NO; correspondence user already knows, no newer confirmed distribution, conversion, refund or listing
- next_delta: first official definitive SAFE/warrant conversion terms, verified equity/token deliverables, investor consent required, firm unlock/IPO/distribution, refund or liquidity

### Reya CoinList investor allocation
- verified_original_platform_reply: CoinList, 2026-11-06 UTC, connected life Gmail message `1a1b328b4a25111a`
- reported_successful_commitment: **5000 USDC**, successful participation and allocation preserved, per CoinList team
- reported_platform_migration: historical sale order/allocation not yet migrated into new self-service UI, so blank UI does not prove user allocation gone
- TGE_at_reply: NOT_OCCURRED
- distribution_date_at_reply: UNKNOWN; issuer confirmation still awaited
- original_sale_terms: https://coinlist.co/reya; price 0.01875 USDC/REYA, 50% released at TGE and 50% linear 6 months post TGE; reported user's EXACT unit amount NOT provided in support reply
- refund_if_never_delivered: UNCONFIRMED; platform support did not answer contractual remedies in the specific reply
- triggered_new_mail: NO; user previously received the original response and already discussed it, not a newly discovered event
- next_delta: issuer's definitive TGE date, first actual distribution, custody/wallet routing, complete contract terms, cancellation or legal recovery notice

### Pond reward-points legal qualification
- verified_issuer_terms: https://docs.joinpond.ai/docs/terms-of-use, effective 2026-08-27
- issuer_claim: bounty/task points are symbolic, have no monetary value, are nontransferable and do not confer future claim/redemption rights **unless issuer expressly declares otherwise in writing**
- monitored_status: existing Pond project remains in original 28 per user scope; points value or TGE entitlement NOT GUARANTEED
- next_delta: first dated issuer written token/value conversion terms or actual capital/exit milestone
- action: background legal qualification, not a fresh user-rights notice

## Latest user-directed exclusion: Neutrl (2026-11-21)

- project_id: neutrl
- canonical_official_handle: @neutrl_labs / @Neutrl; canonical current domain neutrl.finance (historical neutrl.fi was sunset after DNS incident)
- user_scope: **USER_SUPPRESSED_NO_TGE_ACTION / REMOVE_FROM_SHARD_1_AND_URGENT**
- issuer_fact: 2026-08-13 project paused minting and redemption due to reserve issues; 2026-08-28 explicitly said **not a contract exploit/hack/code vulnerability**, reported approximately USD 27M liquid reserves with additional illiquid positions, outcome unknown. Original issuer source https://x.com/Neutrl/status/2093390526582010348 ; official https://t.me/s/NeutrlOfficial
- issuer_fact: 2026-09-17 NUSD/sNUSD orderly redemptions opened at a **fixed reserve-dependent rate**, not full USD par; source https://x.com/Neutrl/status/2100614848241414280 , https://redeem.neutrl.finance
- loss_corrob: Nexus Mutual first-party insurance claim history https://docs.nexusmutual.io/overview/claims-history/neutrl-2026/ says redemption at roughly **51% of reference value, 49% shortfall**. No proof all holders were fully paid.
- current_claim_deadline: official account message dated 2026-11-16 extends redemption submission to **2026-12-13 23:59 UTC**; original X post exact status link UNVERIFIED in this pass, original-account text accessible through https://teapaw.org/Neutrl and cited public account reposts. Does NOT warrant notification to this user after explicit suppression.
- user_personal_NUSD_or_sNUSD_holdings: UNKNOWN; the user specifically asked to REMOVE this project from their TGE monitor. Do not invent a claimed refund or infer token allocations.
- status: **USER_DECISION_NO_TGE / PROJECT_COLLAPSED / TGE_CLOSED / NO_LAUNCH_WATCH / USER_SUPPRESSED**; issuer-level historical status remains RESERVE_IMPAIRMENT / CORE_OPERATIONS_PAUSED / PARTIAL_RECOVERY_REDEMPTION
- user_prior_decision: Already in Aug 2026, user explicitly judged Neutrl's reserve shortfall, aborted redemption, suspected liquidity withdrawal and impaired operational/funding capacity as effectively fatal to any credible TGE. This decision is final for TGE watch and supersedes assistant's previous 'unknown TGE' status.
- tge_monitor_disposition: **NO TGE; CLOSED FOR INVESTMENT MONITORING; DO NOT PUT BACK IN PENDING/UNKNOWN TGE.** This is USER-CONFIRMED ANALYTICAL CLASSIFICATION, separate from a formal first-party token cancellation statement, which was not independently evidenced.
- forensic_evidence_guard: Official issuer denied code/contract hack; user raised earlier liquidity-withdrawal / potential soft-rug concerns. Keep these as evidence/assessment with attribution, without certifying a proven onchain hack, legal wrongdoing or full investor reimbursement.
- monitor_action: **NO_PROJECT_SCAN / NO_DYNAMIC_URGENT / NO_EMAIL**; exclude before source-discovery and from project count. Other investors' redemption options are historical/research context only unless user explicitly reactivates
- configuration: former 8/7/7/7 active shard counts become **8/6/7/7 = 28 active entries**, permanent urgent zero
- provenance: user direction + independent issuer/social originals and Nexus Mutual claim evidence; existing historical notices remain immutable

## LATEST CANONICAL USER RIGHTS OVERRIDE, 2026-11-21 (takes precedence over all older entries below)

**User supplied the following personal entitlement facts directly.** These are `USER_CONFIRMED`, not independently proven by chain signatures. Legacy issuer TGE/claim announcements, old emails and older `SOURCE_GAP` investigations are archived history, and do NOT re-enable scanning of these projects.

### 01 / N1 points false-positive corrected; separate Echo investment OPEN
- entity: 01 Exchange / N1 acquisition; historical official issuer source https://www.nullstudios.com/blog/n1-01
- user_01_points: **0, USER_CONFIRMED**
- user_N1_points: **0, USER_CONFIRMED**
- points_monitoring: **SUPPRESSED**, no user eligibility/points balance, N1 token claim or points-to-token conversion may be inferred
- user_actual_investment_channel: **Echo**
- user_original_deal: **USD 1,000 invested in the original 01 Exchange deal, USER_CONFIRMED**
- paid_back_or_settlement_status: **UNKNOWN / NOT VERIFIED IN THIS TURN**; do not mark returned, distributed, converted into N1 or fulfilled without original deal evidence
- monitor_scope: `ECHO_01_DEAL_INVESTMENT_RIGHTS_ONLY`, single Shard-2 entry with Echo user-facing terms and issuer updates where directly connected to the user's deal
- material_events: Echo contract/issuer substitution, actual refund/partial refund, cancellation, redemption, token/warrant/equity deliverable, distribution deadline, investor action, allocation or fee change
- status: `OPEN_OUTCOME_UNVERIFIED`, not auto-urgent in absence of verified immediate deadline
- identity_guard: the N1 2026-07-08 app acquisition recognizes points for other legacy users; user has **none**. USD 1,000 Echo deal is independent unless contractual evidence proves otherwise.

### Explicit exclusion of all five former fixed Urgent projects
- project_ids: `concrete`, `metamask`, `claynosaurz` (including Clay Shares), `heeboo`, `space` (issuer @intodotspace, not Spacecoin)
- status_each: `USER_SUPPRESSED_NO_REMAINING_ACTION`
- confirmed_by: USER explicitly says **all five have no utility and must be removed**; prior user rights already handled or not eligible
- individual_claim_vs_ineligible_breakdown: UNKNOWN; do not assert each was claimed or paid onchain
- monitor_action: **REMOVE_FROM_FIXED_URGENT / REMOVE_FROM_ACTIVE_SHARDS / NO_DYNAMIC_REENTRY / NO_GMAIL** until user explicitly requests new monitoring
- note: past claims, rewards, send receipts and project history remain archived and cannot be treated as present unclaimed rights

### Additional old project rights closed by user
- project_ids: `standx`, `cambria`
- status_each: `USER_SUPPRESSED_NO_REMAINING_ACTION`
- original_project_lifecycle: StandX platform token TGE cancelled; Cambria RSGP TGE completed. Previous DUSD, RSGP, NeoSoul and old stake claim announcements are historical only, not user-owned unresolved claims.
- monitor_action: REMOVE_FROM_ACTIVE_SHARDS / REMOVE_FROM_DYNAMIC_URGENT / NO_GMAIL; preserve existing old alerts for audit
- claim_or_ineligibility_breakdown: UNKNOWN, only user's no-current-action assertion is confirmed

### Dynamic urgent eligibility rule after cleanup
- permanent_urgent_count: **0**
- active_shards: Shard0=8, Shard1=6 (Neutrl user-excluded), Shard2=7 (includes Echo 01 investment, excludes N1/01 points), Shard3=7; total=28
- dynamic_urgent: may be **0**; promote only a real existing eligible user right, confirmed current action and material urgency; never auto-reactivate suppressed/closed items because of project-wide news
- close_transition: notify only on genuinely NEW material actions; after user says CLAIMED / NO_ALLOCATION / INELIGIBLE / REFUNDED / CLOSED, reconcile the registry entry and known-events in the same authorized work turn, and suppress future checks. A SENT email is just `NOTIFIED`, **not** `CLAIMED`.
- evidence_protection: never rewrite historic mailed content, never call a user statement a chain receipt, never fabricate refund or closed balance proof

## 2026-11-21 historical issuer lifecycle reconciliation (superseded for above user rights) (canonical for future monitor runs)

**This section supersedes historical old-stage descriptions below where states conflict. Historical email IDs and earlier observations remain true for their original dates.** No email is authorized simply because this classification was repaired.

### N1 acquisition of 01 Exchange (independent 01 TGE monitoring closed)
- event_key: n1:acquisition_01_exchange:2026-07-08
- issuer_first_party: https://www.nullstudios.com/blog/n1-01 (published 2026-07-08; checked 2026-11-21)
- status: ACQUIRED_01 / LEGACY_APP_SUNSET / HISTORICAL_POINTS_RECOGNIZED_BY_N1
- previous_01_account: app.01.xyz retired as independent destination; official destination https://app.n1.xyz
- historical_01_points: N1 issuer explicitly says all previously earned 01 points recognized under N1; this is NOT a verified N1 token allocation, claim date or amount
- user_specific_points_balance_or_token_rights: UNKNOWN
- treatment: independent 01 Exchange entry removed from Shard 2; continue under existing N1 Shard-2 project identity, preserving separate Echo/SPV rights if present and separately evidenced
- notification: SUPPRESS acquisition as stale July news; send only new original rights/claim/compensation event passing source and dedupe gates

### Concrete CT token launched; original TGE is finished
- event_key: concrete:ct_tge_completed:2026-09-30
- official_exchange_listing: https://blog.kraken.com/product/asset-listings/ct-is-available-for-trading (dated 2026-10-02, states trading since 2026-09-30)
- status: TGE_COMPLETED / RIGHTS_CLAIM_ONLY
- tge_time: 2026-09-30 (calendar date confirmed)
- original_claim_open: already DELIVERED via event `concrete:ct_claim_open:2026-09-30`, Gmail `1a0fb623103c8948`; do not send duplicates
- individual_CT_claim_eligibility_or_balance: UNKNOWN
- claim_end_time: NOT_VERIFIED; must consult authentic issuer interface / first-party source; impersonating foundation domains exist and should not be linked without issuer verification
- unrelated_extra_USDC_claim: remains SOURCE_GAP, not silently dropped, verify separately
- treatment: Concrete remains fixed urgent-five and Shard-1 only for bounded unresolved CT/right claims or changed deadline, no another first TGE alert

### StandX platform token cancelled; wind-down DUSD/withdrawal rights remain
- event_key: standx:platform_tge_cancelled:2026-10-15
- official_issuer: https://x.com/StandX_Official/status/2110613283967230232 ; https://standx.com/
- status: PLATFORM_TGE_CANCELLED / WIND_DOWN / RIGHTS_ONLY
- issuer_milestones: DUSD claim window stated Nov2 UTC through 2026-12-31 08:00 UTC in official account posts reflected publicly; issuer's live claim UI and user eligibility remain to be separately verified before any personal action
- withdrawal_cutoff: 2027-01-31 (issuer announced; exact time not independently confirmed)
- final_positions_cutoff: 2027-01-15 (issuer announced)
- old_warning: standx:winddown_dusd_airdrop:2026-10-15 already emailed, Gmail `1a13e6930e07d0ae`
- personal_DUSD_allocation, remaining_positions, refund_amount: UNKNOWN
- treatment: retain existing Shard-0 as RIGHTS_ONLY and dynamic urgent if current user-entitlement deadline warrants; stop discovery of native StandX TGE; no repeat old warnings; distinct verified partner benefit and material claim delta may notify

### Cambria RSGP TGE complete; independent cross-chain rights remain
- event_key: cambria:rsgp_tge_completed:2026-10-29
- official_game_token: https://lobby.cambria.gg/genesis/ , Base RSGP contract `0x44B63aF715D5ef02CC3646a6CE96875e11d69E85`
- independent_first_party_listing: https://www.mexc.com/announcements/article/first-in-market-17827791539281 (trading 2026-10-29 15:00 UTC)
- status: RSGP_TGE_COMPLETED / RIGHTS_CLAIM_ONLY
- prior_notice: RSGP first launch Oct28 already emailed Gmail `1a1812a1f6802ecb`; never repeat unchanged TGE
- personal_RSGP_claim_wallet_eligibility_and_amount: UNKNOWN
- distinct_legacy_right: Blast/Abstract historical Duel Arena stake reclaim may still require issuer ticket; maintain separate existing event and no duplicates
- treatment: retain original Shard-3 only for issuer-verified new claim, allocation, claim deadline, escrow repayment or wallet migration change

### OnRe and Reflect are distinct; neither merger nor extra governance TGE proven
- event_key: onre_reflect:identity_separation:2026-11-21
- first_party_onre: https://www.onre.finance/resources/announcements , ONyc independently circulating and active
- first_party_reflect: https://reflect.money/insights , https://claims.reflect.money/ ; Reflect is independently operated and its USDC+ recovery portal is a separate rights family after Drift April 2026 exploit
- alleged_merger: **NOT_CONFIRMED**; Reflect's 'reUSD' Re Protocol underlying must not be mislabeled as OnRe reinsurance
- onre_new_governance_tge: NOT_CONFIRMED; existing ONyc is a yield-bearing product token, not proof of prospective governance TGE
- reflect_new_governance_tge: NOT_CONFIRMED
- previously_delivered_reflect_recovery: `reflect:recovery_claim_open:2026-09-12`, Gmail `1a09250f1088fcc6`; suppress unchanged claim notices
- user_USDC_plus_or_recovery_eligibility: UNKNOWN
- treatment: keep separate existing Shard-1 entries, rights-discovery only where verified and material, no manufactured merger or generic TGE claim

## Merger-resolved TGE scope — historical / no active independent TGE

### Loopscale / Orca / Formation
- event_key: formation:orca_loopscale_merger:2026-10-08
- project_ids: loopscale, orca, formation
- evidence: issuer-level merger announcement; combined entity is Formation; ORCA/xORCA remain the stated token network
- confirmed_first_party: https://www.prnewswire.com/news-releases/orca-and-loopscale-merge-to-build-capital-markets-for-ai-and-the-frontier-economy-302901726.html
- independent_loopscale_tge: NOT_CONFIRMED
- new_formation_token: NOT_ANNOUNCED
- orca_or_xorca_tge: ALREADY_EXISTING_TOKEN; NOT_NEW_TGE
- delivery_status: NO_TGE_ACTION; NO_GMAIL
- user_rights: no verified new entitlement/claim/airdrop from this merger; personal holdings/entitlements not established
- monitor_action: SUPPRESS_INDEPENDENT_TGE_DISCOVERY; remove Loopscale from Shard 1, do not add Orca or Formation. Maintain history for audit; do not create new automation. A separately proven new user right or fresh token launch requires new first-party evidence and explicit user direction.
- daily_lane: Crypto Daily Section 6 (merger + ORCA tokenholder governance), not TGE Section 7
- current_governance: proposal not proven passed; vote ends 2026-10-10 19:42 UTC, cooldown ends 2026-10-12 19:42 UTC; do not assert enactment

## Closed TGE scope after full principal refund (2026-11-21)

### Forecast / ForecastFDN
- project_id: forecast / forecastfdn
- event_key: forecast:founding_principal_full_refund:2026-11-21
- state: CLOSED_PRINCIPAL_REFUNDED / USER_SUPPRESSED_TGE
- original_deposit: 100.000000 USDC, Base, 2026-05-29 10:18:17 UTC
- actual_refund: 100.000000 USDC, Base, 2026-11-20 22:51:59 UTC (2026-11-21 05:51:59 Asia/Bangkok)
- payer: original Forecast Founding Safe (4-of-5), 0xf605…2378
- recipient: original depositor, masked 0x3df4…ea7c
- confirmed_tx: 0xff0dee7e…0ad6a (Base, native USDC, 100 USDC, success)
- source_type: user_report_confirmed + Alchemy Base RPC transfers and transaction receipt
- principal_unpaid: 0 USDC
- other_claim_or_reward_entitlement: NOT_EVALUATED; suppression is by user request, not a claim there can never be a token
- monitor_action: REMOVED_FROM_SHARD_1 / SUPPRESS_FORECAST_TGE_AIRDROP_REFUND_DISCOVERY / NO_DYNAMIC_URGENT / NO_FUTURE_ACTION until the user explicitly reactivates Forecast
- audit_evidence: research/projects/forecast/founding-deposit-custody-20261121.md (separate research branch, commit fac596425a55f11d3aba604624afa2460c128951)
- delivery_status: NO_GMAIL; no new task or change to schedule, fixed urgent5 or other projects. Retain all historical reports.

## CLOSED / no remaining rights

### humans&
- project_id: humansand
- state: CLOSED_FULLY_REFUNDED
- effective_date: 2026-09-24
- source_type: user_confirmed + stored deal history
- remaining_entitlement: none known
- monitor_action: suppress unless user explicitly re-enters a new exposure

## User-suppressed / excluded from active monitoring

### Abstract / ABS
- project_id: abstract
- state: USER_SUPPRESSED
- effective_date: 2026-10-07
- source_type: user_confirmed
- remaining_entitlement: not evaluated; user explicitly requested removal from TGE monitoring
- monitor_action: suppress Abstract / @AbstractChain / ABS from active discovery and notifications; reactivate only on explicit user request

## Completed / suppress

### UNICRED #230 unstake/unlock
- event_key: unicred:unstake_unlock:230:2026-10-01
- state: COMPLETED_NO_REMAINING_ACTION
- effective_date: 2026-10-01
- source_type: user_confirmed
- remaining_entitlement: no unresolved unstake/unlock action known
- monitor_action: suppress; do not send T-24h/T-2h/overdue or backfill reminders

## Delivered / known event keys

### Concrete CT claim-open
- event_key: concrete:ct_claim_open:2026-09-30
- delivery_status: delivered_once_late_discovery
- gmail_message_id: 1a0fb623103c8948
- user_policy: one notification is acceptable even if first discovery is late, provided Tier A/B confirms the action is still current/open and plausibly relevant
- repeat_policy: suppress unchanged CT claim-open reminders after this delivery; only a genuinely new Tier A/B material delta may re-alert

### HEEBOO claim open
- event_key: heeboo:claim_open:2026-09-10
- delivery_status: delivered
- gmail_message_id: 1a087e5f1a908034
- repeat_policy: suppress unchanged claim-open reminders

### Reflect USDC+ recovery claim
- event_key: reflect:recovery_claim_open:2026-09-12
- delivery_status: delivered
- gmail_message_id: 1a09250f1088fcc6
- repeat_policy: suppress unchanged recovery-portal reminders

### Surf Season 1 referral rewards claim
- event_key: surf:season1_referral_claim_open:2026-09-12
- delivery_status: delivered
- gmail_message_id: 1a09260ad0c0ca4
- repeat_policy: suppress unchanged claim reminders

### MetaMask Money Sweepstakes registration
- event_key: metamask:money_sweepstakes_registration:2026-09-17
- delivery_status: delivered
- gmail_message_id: 1a0b836c33c1039f
- note: two GitHub archives exist for the same Gmail message; this is one logical delivered event
- repeat_policy: suppress unchanged reminders; only deadline/eligibility/rules material delta may re-alert

### Cambria RSGP Genesis opt-in
- event_key: cambria:rsgp_genesis_opt_in:2026-09-30
- delivery_status: delivered_recovery
- gmail_message_id: 1a0e149fa6d9718a
- repeat_policy: suppress unchanged reminder; new official extension/reopen may alert once

### Space SPC public-sale claim dApp sunset — October 15
- event_key: space:spc_public_claim_dapp_sunset:2026-10-15
- project: Space @intodotspace, NOT Spacecoin @spacecoin
- source: https://t.me/intodotspace/919 (official channel, direct original checked in existing 2026-10-11 13:00 run)
- evidence_tier: A for public-sale claim dApp deadline; personal eligibility and precise closing hour unverified
- delivery_status: delivered_2026-10-11_manual_recovery
- gmail_message_id: 1a129b8b2ddd1607
- event_archive: airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-11/040407-space-spc-claim-dapp-sunset.md
- repeat_policy: permanently suppress this unchanged Oct 15 reminder; only new first-party deadline extension, eligibility/action/rights change may justify a fresh event

## Historical-only / no current ACTION baseline

### Crusoe Series F valuation
- event_key: crusoe:series_f_valuation:2026-09-17
- delivery_status: delivered_historical
- rights_effect_confirmed: false
- current_policy_reclassification: background_only_unless_mapped_spv_terms_change
- repeat_policy: suppress generic valuation/funding repeats

## 2026-10-15 late-discovery repairs: Surf and StandX

### SurfBoard member NFT claim opened (separate from prior referral Season 1)
- event_key: surf:surfboard_member_claim_open:2026-10-15
- project_id: surf
- verified_official_source: https://asksurf.ai/blog/en/surfboard-nft-launch
- official_open: 2026-10-15 03:00 UTC / 10:00 Asia/Bangkok
- official_claim_deadline: 2026-11-13, precise hour recheck issuer
- eligibility: annual Surf Pro/Max purchased before 2026-09-16, including lapsed; individual Surf subscription NFT number and claim status NOT independently confirmed
- delivery_status: DELIVERED_MANUAL_LATE_2026-10-15
- gmail_message_id: 1a13e676f3e4e04d
- event_archive: airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-15/1409-surf-surfboard-member-claim.md
- repeat_policy: suppress unchanged claim-open; only official reopened/deadline/eligibility change is fresh ACTION. Never conflate with previously delivered surf:season1_referral_claim_open:2026-09-12.

### StandX staged shutdown / one-time DUSD airdrop / user redemption
- event_key: standx:winddown_dusd_airdrop:2026-10-15
- project_id: standx (existing Registry Shard 0)
- official_account_posts: https://x.com/StandX_Official/status/2110613283967230232 ; https://x.com/StandX_Official/status/2110613379270185114
- official_full_text_direct_readback: SOURCE_GAP; third-party English translation exists, milestone times are PENDING_DIRECT_FIRST_PARTY_TEXT_VERIFY
- candidate_milestones_utc: 2026-10-15 new yield/deposits closure; 2026-10-20 perps reduce-only; 2026-10-26 00:00 eligibility check; 2026-11-01 00:00 through 2026-12-31 08:00 DUSD claim; 2027-01-15 position/vault settlement; 2027-01-31 redemption/withdrawal cutoff; recheck primary official announcements for exact timezone and content
- user_personal_rights: holdings/points/claimable DUSD, allocations and open positions NOT CONFIRMED
- delivery_status: DELIVERED_URGENT_RISK_2026-10-15
- gmail_message_id: 1a13e6930e07d0ae
- event_archive: airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-15/1410-standx-winddown-dusd-airdrop.md
- handling: keep StandX eligible for CURRENT existing dynamic urgent deadline/redemption checks until materially resolved, not as an additional project/watch task; suppress unchanged event recap emails; allow new verified material official deadline, open eligibility checker or claim window transition under a NEW stable material-delta event key only. Never suggest depositing to farm points.

## 2026-10-16 newly discovered missed cross-project StandX community benefit

### NeoSoul DNA proposed StandX contributor allocation
- event_key: neosoul:dna_standx_community_allocation:2026-10-15
- beneficiary_registry_project: standx / @StandX_Official (existing Shard 0)
- external_issuer: NeoSoul / DNA, not legacy NEO blockchain
- first_reported_at: 2026-10-15 (Binance News)
- secondary_attributed_source: https://www.binance.com/en/square/post/10-15-2026-neosoul-plans-dedicated-dna-airdrop-for-standx-community-377570746498100
- issuer_original_post_link: https://x.com/NeoSoulAI/status/2110722973703512113 (original handle/status ID discovered via cited independent source; direct X returned HTTP 403, content NOT independently readable)
- issuer_original_social_text_readback: SOURCE_GAP; cannot upgrade secondary quoted text to Tier A without direct original or equivalent canonical first-party readback
- reported_issuer_statement: NeoSoul / NS3.AI proposes dedicated DNA for long-term StandX contributors and eligibility/claim details after TGE.
- personal_snapshot_eligibility_allocation_claim: UNVERIFIED
- source_tier_for_STANDX_rights_ACTION: NOT_YET_A_OR_MAPPED_B
- state: HIGH_MATERIALITY_VERIFYING_PARTNER_RIGHTS, NO_GMAIL_PENDING_AUTHORITATIVE_RIGHTS_PROOF
- relationship_scope: existing StandX beneficiary check, no new independently monitored NeoSoul project
- prior_delivery_dedupe: distinct from standx:winddown_dusd_airdrop:2026-10-15; the original StandX shutdown alert cannot suppress this new potential rights event
- next_check: issuer first-party announcement/claim eligibility release after actual DNA TGE, with canonical account and exact evidence timestamp.

### NeoSoul DNA Binance Wallet Alpha release (separate event)
- event_key: neosoul:dna_binance_alpha_release:2026-10-16
- verified_platform_source: https://www.binance.com/en-IA/square/profile/binancewallet
- reported_platform_announcement: Binance Wallet official 2026-10-16 08:00 UTC DNA Alpha; initial threshold >=245 Alpha Points, first-come 400 DNA, cost 15 Alpha Points; threshold drops 5 points every five minutes IF rewards remain; users must confirm within 24 hours in Alpha Events (check actual user campaign countdown and pool).
- platform_official_detailed_source: https://www.binance.com/en/square/post/377812880382013
- first_party_checkpoint: 2026-10-17 ~08:00 UTC / 15:00 Asia/Bangkok is 24h from launch, not a guarantee of open stock at that time
- user_notification_accounting: DNA Alpha campaign described once in 2026-10-17 full Crypto Daily Gmail 1a14886106251842; no standalone NeoSoul project added to TGE Registry
- StandX_user_compensation_is_identical: FALSE, no relationship inferred between account Alpha Points and StandX-specific allocation
- user_eligibility/actual_Alpha_points: UNVERIFIED
- action_decision: do not deliver StandX-specific entitlement notice on generic Alpha announcement alone; retain a new material Crypto Daily news candidate and verify Alpha activity details before any action.

## 2026-10-18 targeted pending existing-scope rights verification (not delivered)

### Cambria Blast/Abstract gameplay transition (HIGH source-verification priority)
- event_key: cambria:blast_abstract_gameplay_migration:2026-10-19
- project_id: cambria (EXISTING Registry Shard 3; existing Genesis opt-in alert delivered Oct15; no new project/automation)
- multiple_english_secondary_sources: https://airdrops.io/cambria/ (updated Oct17 2026); https://blockchaingames.fun/latest-news/ (Oct16 announcement brief); https://t.me/s/airdrops_io?before=7954 (repeat of same secondary ecosystem)
- alleged_effective_at: 2026-10-19 11:00 US Eastern / 15:00 UTC / 22:00 Asia/Bangkok (October EDT), REQUIRES FIRST-PARTY CONFIRMATION
- reported_consequence: Cambria game disables Blast/Abstract support, game treasury/unclaimed Duel Arena stakes may move to Base/Ethereum; secondary guide says manual withdrawals before transition and Discord ticket route afterward, NOT authoritative advice for user action.
- issuer_original_source_text: SOURCE_GAP; no matching canonical Cambria official blog/docs/X announcement independently read at 2026-10-18 08:10 BKK
- personal_exposure: UNKNOWN; no evidence user's Cambria Duel Arena stakes on Blast/Abstract
- status: HIGH_MATERIALITY_VERIFYING_FIRST_PARTY; DO NOT SEND ACTION GMAIL until original issuer or mapped user-rights Tier A/B independently verifies actual current actionable user rights, appropriate route and deadline
- next_check: bounded time-sensitive official Cambria X/docs/blog and account-firstparty announcements before alleged 2026-10-19 22:00 BKK deadline, prioritizing this EXISTING shard event even when shard 3 is not scheduled; not a second full deep shard
- dedupe: NOT the same event as previously delivered Cambria Genesis Opt-in; a later independent material verified transition may have a new email exactly once.

### NeoSoul DNA generic issuer eligibility checker (separate from StandX-specific promise)
- generic_checker_official: https://airdrop.neosoul.ai/ (first-party issuer domain, checked Oct18)
- generic_checker_displayed_window: 2026-10-15 00:00 to 2026-10-23 00:00 UTC+8 (deadline 2026-10-22 16:00 UTC / 23:00 Asia/Bangkok)
- official_visible_action: wallet eligibility check and confirmation for Sybil-screened wallets; user's wallet inclusion NOT VERIFIED
- standx_contributor_specific_entitlement: UNVERIFIED; generic checker does not explicitly confirm a StandX beneficiary set. Cannot promote existing \`neosoul:dna_standx_community_allocation:2026-10-15\` into Tier A user-rights action based on this alone.
- relationship_scope: informational evidence for already-monitored StandX beneficiary check, not new full-watch NeoSoul project or independent urgent notification.

## 2026-10-23 verified StandX beneficiary action, delivered

### NeoSoul DNA Batch 1 StandX BNB wallet registration
- event_key: neosoul:dna_standx_batch1_wallet_registration:2026-10-20
- beneficiary_registry_project: standx / @StandX_Official (existing Shard 0 and dynamic urgent)
- external_issuer: NeoSoul / DNA / @NeoSoulAI (Gate 1B external issuer only; NOT new independent Registry member)
- issuer_first_party_rules: https://medium.com/@NeoSoul_AI/standx-community-dna-airdrop-batch-1-rules-and-how-to-register-2bc691665575 (issuer-authored Medium post, retrieved 2026-10-23)
- issuer_original_x: https://x.com/NeoSoulAI/status/2112503827702366328 (X direct 403; source URL and account match English mirrored post)
- identity_crosscheck: official @NeoSoulAI public X text links to the same @NeoSoul_AI Medium author profile; NeoSoul-curated Galxe credential https://app.galxe.com/quest/credential/668693055632572416 links to same Discord invite as issuer Medium article
- discord_link_from_issuer: https://discord.gg/neosoul (verified redirects to https://discord.com/invite/neosoul; actual private announcement/form JS-only)
- evidence_tier: A_ISSUER_MEDIUM_WITH_CANONICAL_IDENTITY_CROSSCHECK; external-issuer beneficiary rule ACTION_GATE Gate1B
- issuer_claim: registration OPEN for StandX community BNB Chain wallets, Oct14 23:59 UTC snapshot, closes 2026-11-03 15:59 UTC / 2026-11-03 22:59 Asia/Bangkok; unified distribution afterward
- user_eligibility: UNKNOWN; individual allocation, wallet inclusion and Discord form submission NOT VERIFIED
- rights_relevance: eligible existing StandX community users need to submit prior BNB Chain wallet; no key, seed or signature requested by issuer article
- prior_dedupe: prior StandX winddown and generic NeoSoul checker are distinct; Gmail Sent searched for NeoSoul StandX formal alert on 2026-10-23 and found NONE
- delivery_status: DELIVERED_2026-10-23_GMAIL_SENT_READBACK_ARCHIVED
- gmail_attempted: true (initial attempt FORBIDDEN; subsequent 20:04 BKK attempt SENT)
- initial_gmail_error: FORBIDDEN GmailApiError Failed to send email (historical first attempt only)
- gmail_sent_readback: VERIFIED; Gmail id 1a168dd4a732eab4, SENT label, recipient and complete body readback at 2026-10-23 20:04 BKK
- event_archive: airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-23/200501-standx-neosoul-dna-batch1-wallet-registration.md
- next_action: SUPPRESS_UNCHANGED_EVENT_PERMANENTLY; re-alert only on new material first-party change. Personal eligibility remains UNKNOWN; do not send repeated registration reminders.
- last_checked_at: 2026-10-23 18:58 Asia/Bangkok
- delivery_verified_at: 2026-10-23T20:04:00+07:00


## 2026-10-24 verified Cambria post-migration Duel Arena reclaim and login access

### Cambria Blast/Abstract Duel Arena old-stake claim and AGW login protection
- event_key: cambria:duel_arena_blast_abstract_post_sweep_claim_and_login:2026-10-19
- project_id: cambria (existing Registry Shard 3; bounded cross-shard material rights discovery)
- issuer_first_party_claim: https://docs.cambria.gg/archive/duel-arena/duel-arena-blast-and-abstract-wind-down
- issuer_first_party_login: https://docs.cambria.gg/dungeons/patch-notes/patch-v0.6.4
- verified_issuer_claim: on 2026-10-19 Cambria withdrew remaining unclaimed Blast/Abstract Duel Arena escrow stakes, recorded a wallet snapshot; affected users may still submit a Discord ticket, verify by original wallet message signature, and request ETH payout on Ethereum mainnet (issuer says within 30 business days after verification).
- related_login_access: issuer advises accounts relying only on Abstract Global Wallet + Privy to add an alternate wallet/social login before Abstract 2026-12-15 shutdown risk.
- actual_user_old_duel_stake_or_AGW_only_login: UNKNOWN; no personal allocation or eligibility was claimed in alert; check only if applicable.
- evidence_tier: A official Cambria docs, read 2026-10-24 Asia/Bangkok; docs explicitly describe an ongoing post-Oct19 ticket process, but exact document publication timestamp unverified.
- delivery_status: DELIVERED_2026-10-24_GMAIL_SENT_READBACK_ARCHIVED
- gmail_message_id: 1a16a27a9e5b557c
- event_archive: airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-24/020558-cambria-duel-arena-blast-abstract-reclaim.md
- stable_key_policy: suppress unchanged old-stake reclaim/login reminder; re-alert only for newly verified material deadline, route, eligibility or rights change.
- prior_cambria_rsgp_opt_in: separate event, already delivered; no duplicate.

## 2026-10-28 Cambria Base $RSGP TGE and My Cambria Journey — DELIVERED
- event_key: cambria:rsgp-base-tge-and-journey:2026-10-29
- project_id: cambria (EXISTING Shard 3; not a new Abstract/ABS watch entry)
- distinct_from: cambria:rsgp_genesis_opt_in:2026-09-30 AND old Blast/Abstract Duel Arena escrow reclaim/login events
- event_family: cambria:rsgp:base_tge_and_player_allocation_review
- evidence_tier: A project original https://docs.cambria.gg/genesis/usdrsgp and https://lobby.cambria.gg/token/
- expected_tge_utc: 2026-10-29T15:00:00Z
- expected_tge_bangkok: 2026-10-29T22:00:00+07:00
- launch_chain: Base
- issuer_token_ca: 0x44B63aF715D5ef02CC3646a6CE96875e11d69E85
- prior_user_participation: historical Cambria game, exact linked wallet and allocation UNVERIFIED
- allocation_amount: UNVERIFIED
- claim_open_transaction: UNVERIFIED
- delivery_status: DELIVERED_EMAIL_CONFIRMED
- gmail_message_id: 1a1812a1f6802ecb
- canonical_event_archive: airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-28/now-cambria-rsgp-base-tge.md
- repeated_alert_policy: unchanged Oct29 date, Base chain and My Cambria Journey visibility are ALREADY NOTIFIED. A new email only for a freshly issuer-verified actual claim opening, changed deadline, actual wallet-specific rights, contract migration/change, material postponement or other urgent user action, with distinct version and Gmail Sent dedupe.
- critical_negative_guard: user-suppressed independent Abstract/ABS token watch does not exclude Cambria-as-registered-project rights that were earned on Abstract but settle on Base.

## 2026-11-04 candidate — StandX $DUSD claim-window transition, original-post readback unresolved
- source_project: StandX (existing urgent Registry member, not new)
- event_family_key: `standx:dusd_claim_window_open:2026-11` (distinct from `standx:winddown_dusd_airdrop:2026-10-15` and distinct from NeoSoul's StandX community rights)
- historic_issuer_announcement: Oct15 original projected Nov1 claim start; Oct31 public-account report postponed because Binance withdrawals were closed.
- public_account_post_candidate: `https://x.com/StandX_Official/status/2117039675559026937` dated Nov1 2026 23:42 UTC, quoted by two independent X post mirrors `https://teapaw.org/StandX_Official/status/2117039675559026937` and `https://twiscan.com/en/x/StandX_Official/2117039675559026937`.
- mirror_text_claim: claim opens 2026-11-02 00:00 UTC, closes 2026-12-31 08:00 UTC, issuer-listed entry `https://standx.com/airdrop`. This is THIRD_PARTY_COPIED_ACCOUNT_TEXT, not directly readable original, as X direct returned HTTP403 and issuer's JS claim application was not readable on 2026-11-04 in this check.
- prior_sent_dedupe: Gmail search from Oct15 through Nov4 yielded Oct15 winddown alert ID `1a13e6930e07d0ae` and Oct23 NeoSoul alert ID `1a168dd4a732eab4` but NO separately sent DUSD Nov2 claim-open notice; old winddown notice DOES NOT suppress this material status transition once authoritative proof is obtained.
- user_claimable_allocation: UNVERIFIED; user-facing online claim interaction: UNVERIFIED; source tier for ACTION: `PENDING_DIRECT_FIRST_PARTY_OR_MAPPED_B`.
- action_status: `HIGH_PRIORITY_FIRST_PARTY_CLAIM_WINDOW_VERIFY`, `NO_GMAIL_YET`. Next existing urgent slot should read the original named account or canonical issuer endpoint and status, validate exact claim period and new user action, apply ACTION_GATE (including no duplicates), then send exactly one authorized Gmail with source and eligibility caveat iff proof passes; otherwise record source gap and remain silent.
- no extra task, no local cron, no assumption that current interactive X Home tab can be navigated by unattended schedule.

## 2026-11-08 historical reconciliation: revoked Space claim and duplicate HEEBOO timing
### Space / Spacecoin misattribution, original Sep14 alert (RETRACTED)
- false_alert_gmail_id: 1a09cc0fb4edb6f0
- correction_gmail_id: 1a0e149f1f9d03be (Gmail Sent, 2026-09-27)
- false_event_key: space:misattributed_spacecoin_final_claim:2026-09-14
- status: RETRACTED_DO_NOT_USE_AS_FACT_OR_ACTION
- canonical_archive: airdrop-tge-monitor/reports/events/2026/2026-09/2026-09-14/045127-space-final-claim-deadline.md (status: retracted, corrected mail recorded)
- original_claim_deadline_2026-09-14_09:00_bkk: FALSE_FOR_MONITORED_SPACE
- original_claim_link_chain: CROSS_PROJECT_EVIDENCE_CONFLATION
- scope: Space @intodotspace remains separate from Spacecoin @spacecoin and later independently verified SPC public-sale claim dApp sunset Oct15. The Oct15 reminder is a separate valid event family and has Gmail id 1a129b8b2ddd1607; neither historical date may replace the other.
- operational_rule: excluded from actionable opportunity/expiry metrics, 7-day novelty baselines, future private user TGE reminder and monthly rights summaries, except as incident/QA warning. Do not resend Sep14 error or Sep27 already-sent correction.

### HEEBOO Metaplex Aug24 explicit 9am ET notice: redundant emails
- family: heeboo:metaplex:tomorrow_9am_et:2026-08-24
- near_duplicate_sends: 1a03567f802748e5 and 1a0356976e78a590
- evidence: both Gmail Sent texts cite same exact Metaplex "Tomorrow. 9am ET. $HEEBOO." news, same Bangkok Aug25 20:00 and same unconfirmed stage. The later email adds explanation but no independent new event version or changed user action.
- classification: HISTORICAL_DUPLICATE_CONTENT_QUALITY_EXCEPTION
- separate_fact_families: earlier Aug24 tokenomics/allocation announcement 1a034f0f1a9a3f8a; launch pool mechanics/preflight 1a0344cdbb8d9b89, may overlap in timing but are distinct stage details, do not automatically label them identical.
- no_new_email: historical reminder already expired; no fresh actionable state. Future email gate must include event family and material version comparison before any new dispatch, never allow repetition solely because another official account repeats a schedule.
- past_sent_bodies: immutable Gmail evidence; don't delete/alter old messages or pretend duplicates were never sent.

### Galxe / Gravity legacy Quest shutdown and campaign reward claim cutoff — 2026-11-09
- project_id: galxe (legacy user-facing quest platform, specifically authorized to dynamic urgent lifecycle 2026-11-20; fixed urgent5 and four shards unchanged)
- event_key: galxe:legacy-quest-sunset:2026-11-09
- family_key: galxe:legacy-quest-sunset
- material_version: galxe-official-2026-11-09-deadlines-dec05-dec15
- canonical_issuer: Galxe / @Galxe / galxe.com; Gravity/G continues
- official_first_party: https://help.galxe.com/en/articles/18361711-galxe-is-integrating-into-gravity-what-you-need-to-know
- official_original_x: https://x.com/Galxe/status/2119681030609105175
- original_announced: 2026-11-09
- last_campaign_participation: 2026-12-05 (issuer-confirmed calendar day; precise hour not stated)
- last_earned_campaign_reward_claim: 2026-12-15 (issuer-confirmed calendar day; precise hour not stated)
- separate_asset_redemption: official Help Center says forthcoming for Smart Balance, unwithdrawn staked G and Gravity Alpha G; public https://app.galxe.com/claim-center displays distinct G-holder/staking/Latch panels, wallet-specific eligibility unverified; no general Dec15 assumption for asset redemption
- user_account_eligibility: UNKNOWN
- user_G_allocation_amount: UNKNOWN; third-party screenshot 85.0099298 G is NOT user's entitlement
- detection: MISSED original Nov9 announcement by existing Crypto Daily and TGE; first verified manual catch-up 2026-11-20
- alert_delivery: DELIVERED_MANUAL_CATCHUP (one conditional rights-preservation email, no duplicated future alert without material delta)
- gmail_sent_id: 1a1f9a770fcb1c29
- gmail_recipient: lxx.run688@gmail.com
- mail_sent_verified: SENT + full body readback + recipient verified 2026-11-20
- git_canonical: airdrop-tge-monitor/reports/events/2026/2026-11/2026-11-20/galxe-platform-sunset-legacy-rewards.md
- canonical_blob_sha: 87c842a94e1e6761f6abf2422eb10316a4807d81
- future_alert: only issuer-confirmed NEW separate asset claim route or deadline, material public rights change or verified account-specific entitlement; do not re-send unchanged Dec5/Dec15
- do_not_confuse: Gravity L1/G token remain running; platform Quest/ID/Passport services wind down; no private key needed
