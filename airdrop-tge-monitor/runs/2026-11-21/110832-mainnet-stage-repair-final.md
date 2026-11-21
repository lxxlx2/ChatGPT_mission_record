# 2026-11-21 11:08 ICT manual TGE/Crypto project-stage regression audit

status: PARTIAL_REPAIR_RULES_UPDATED_UNATTENDED_NEXT_RUN_NOT_VALIDATED
authoritative_scope: existing TGE monitor 6a85fff710e0819190ffcf8c1145a170 only; original schedule HH:00, enabled, recipient unchanged
cause: user-reported Forecast mainnet activation around 2026-11-21 03:00 Bangkok did not produce TGE notification or substantive progress signal. 2026-11-21 05:03:46 and 09:04:08 Shard1 original scheduled finals included Forecast name/domain only, event-bound rights source 0, SOURCE_GAP, no Gmail. Official Forecast X original returns 403 and forecastprotocol.xyz/mainnet is not readable via web tool. Therefore independently verified precise mainnet announcement time, production deployment and first real trading are UNCONFIRMED. Do not upgrade the user's mainnet statement into onchain proof.
completed_deal_state: user confirmed actual 100 USDC principal refund on Base received; prior separate onchain research preserved in known-events (masked transfer 0xff0dee7e...0ad6a), original Forecast TGE explicitly USER_SUPPRESSED / CLOSED and removed from Registry Shard1. This conversation did NOT re-enable Forecast or send a completed-action notification.

root_causes:
  - stage_detection_missing: search only TGE/Claim and stale official home page, no systematic progress transition/mainnet/live-trades/withdraw check
  - primary_source_unavailable: X authenticated browser unavailable, official new product page not readable
  - misleading_scan_coverage: 14/14 names searched but 0/14 current rights proof; task marked completed despite run PARTIAL_ONLY
  - product_milestone_gate_too_narrow: product live can unlock a vault or participation before TGE

executed_rule_changes:
  - airdrop-tge-monitor/MONITOR_SPEC.md updated commit acb478570b588282c5f7bbdfdc92e2be46f1ee21
  - airdrop-tge-monitor/ACTION_GATE.md updated commit ee79fa4b9ef8f496398382cce373bf78eec37f4f
  - airdrop-tge-monitor/AUTOMATION_RUNTIME.md updated commit 18605eaa5c684849dbed40a01f1280961733e8e8
  - crypto-daily/COLLECTOR_SPEC.md updated commit 1da46c8d77a0d1feb0a91e909b713ec8ba9402ce
  - crypto-daily/REPORT_ACCEPTANCE.md CR-41 updated commit 807be9387fa27cb23133a8eaee18787fb020a1a6
  - original TGE automation prompt updated and verified enabled/schedule unchanged
  - original Crypto automation prompt updated and verified enabled/schedule unchanged

new_detection_contract: for ACTIVE registered project detect verified launch stage (predeposit -> testnet -> mainnet/trading live -> withdrawn/redeemed/claim/TGE/refund), use official issuer docs/help/blog/GitHub/chain evidence fallback to X403. Classify issuer claim vs real onchain live proof. Route real active-user rights/withdraw/claim milestone to existing Tier A/B gated one-time TGE Gmail. Route major non-action product stage to ordinary Crypto daily §6/§7. Keep existing fixed urgent5, four shard membership, subscriptions, no heartbeat or duplicate email. SOURCE_GAP cannot become false checked_no_update.

delivery: no TGE email for closed Forecast; not enough independent source to claim a newly actionable original rights event; no new task created, existing primary scan cadence unchanged.
remaining_blocker: actual authenticated issuer X/JS/chain documentation coverage, latest complete 4-shard original current-rights verification, and autonomous regression proof. last_verified_complete_at remains 2026-10-10T07:52:16+07:00 until actual source reads establish otherwise.
no_background_claim: no assumption that prompt update alone repairs unavailable official data sources.
