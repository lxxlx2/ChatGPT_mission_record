# TGE / Airdrop Known User State

Updated: 2026-10-15 Asia/Bangkok

Purpose: durable dedupe/state input for events already known, delivered, completed, refunded, explicitly closed, user-suppressed, or explicitly scheduled by the user within the existing rights monitor. This file is an input to ACTION_GATE.md.

Hard scope rule: do not create a new monitor/task/file for a user-specific future action. If the user explicitly gives a date/time for an action already within this existing rights-monitor scope, record it here as an unresolved known event so the existing monitor can act on it. No new monitoring scope may be added without explicit user authorization.

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
- issuer_original_social_text_readback: SOURCE_GAP
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
- reported_platform_announcement: DNA Binance Alpha on 2026-10-16; qualified Alpha Points users can claim after trading opens, subject to later detailed rules
- StandX_user_compensation_is_identical: FALSE, no relationship inferred between account Alpha Points and StandX-specific allocation
- user_eligibility/actual_Alpha_points: UNVERIFIED
- action_decision: do not deliver StandX-specific entitlement notice on generic Alpha announcement alone; retain a new material Crypto Daily news candidate and verify Alpha activity details before any action.
