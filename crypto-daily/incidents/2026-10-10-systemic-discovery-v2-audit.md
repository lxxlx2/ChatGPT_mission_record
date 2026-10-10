# Crypto Daily systemic discovery incident and V2 remediation
Date: 2026-10-10 (Asia/Bangkok)
Scope: EXISTING Crypto Daily, not the separate user-rights TGE ACTION monitor or US stock morning report
Automation ID: 6a8600b9d12481919bc43ebc800c9916
Task name / schedule: unchanged
New tasks: none; new external alert stream: none

## Root cause: verified deterministic
Original crypto-daily/COLLECTOR_SPEC.md used Asia/Bangkok hour modulo three to choose a shard, while actual non-daily ordinary collector time slots were 00:10,03:10,06:10,15:10,19:10,23:10. Thus shard sequence was [0,0,0,0,1,2], rather than the claimed three-shard rolling cycle. Four out of six collectors deep-scanned social/NFT; only 19:10 handled ecosystem/TGE/RWA and only 23:10 handled macro/policy/flow/deep security. A failure in either single slot left disproportionate gaps. The specification's claim that any three successive collectors cover all shards was mathematically false.

## Compounding factors: observed/limited confidence
- Reports inherited partially empty research/final artifacts. Many Oct 9/10 ordinary runs were partial; Oct 10 19:10 had no durable terminal final on inspection. Missing artifact is not proof that zero research happened, but definitely prevents a coverage-complete claim.
- No independent bounded, cross-domain breaking-news discovery was guaranteed before drafting, so editorial QA could pass 13 formal headings while omitting whole events.
- Sources X/Reddit/issuer originals/specialist feeds were frequently unavailable; `no new verified event` was sometimes confused with `no new event was found in reachable sources`. Status/state verification can suppress unconfirmed claims prematurely.
- Separate Gmail action blocks caused full QA reports not to be delivered on some days. This is a delivery failure, distinct from discovery; changing prompts/research docs cannot prove the platform safety block fixed.
- Conflicting historical docs still referenced 09:00 and hourly-on-the-hour despite the current 09:10 actual task; precedence is now explicitly clarified.

## Four incident replays
1. Abstract L2 shutdown: existing ecosystem/chain security and forced migration; TGE user suppression must not hide the broad market event.
2. Ledger user wallet-drain cluster: user/researcher claims need discovery and investigation even before issuer confirms cause or total loss. Repetition of one source does not prove aggregate figures.
3. XRPL official disclosure Oct 9: severe hypothetical XRP overflow fixed Sept 25 and not known exploited. Official newly disclosed fix belongs in material security; absence of realized theft is not absence of news.
4. National blockchain network directive Oct 9/10: major policy and infrastructure item; English government/secondary corroboration may be needed, without claiming new permissionless token or legalized crypto trading.

## Changes implemented
- COLLECTOR_SPEC.md: every ordinary collector does one bounded cross-domain English headline sweep; deep shard selected from last two ACTUALLY completed and persisted shards, fallback [0,1,2,0,1,2]; separate unverified discovery, source receipt and material HIGH carry-forward.
- REPORT_ACCEPTANCE.md: CR-20 high-impact inclusion/disposition and discovery receipt gate. Top5 has maximum 5, not exactly 5; CR-18/19 unaffected.
- AUTOMATION_RUNTIME.md: latest V2 override; independent pre-send headline discovery and exact sent/archived delivery evidence.
- README.md, REPORT_SPEC.md and DELIVERY_RUNBOOK.md: actual schedule precedence over outdated historical 09:00/hourly instructions.
- tests/REGRESSION_CASES.md: V2-01 through V2-15, including the four concrete misses, source gaps, missing final and Gmail deduplication.
- Existing Crypto Daily automation prompt updated IN PLACE to read COLLECTOR_SPEC V2 and CR-20. No schedule change.

## Dry-run evidence and production acceptance
Pure selection simulation (NOT live news acquisition):
- Old actual hours [00,03,06,15,19,23] -> [0,0,0,0,1,2], demonstrated failure.
- New no-missing -> [0,1,2,0,1,2], all 3 shards twice. PASS.
- Missing 19 -> [0,1,2,0,MISSING,1], next completed shard recovers gap. PASS.
- Missing 03 -> [0,MISSING,2,1,0,2], next scheduled successful available slot recovers gap. PASS.
- Actual GitHub files above have been re-read after update. Existing enabled task update returned success and same Asia/Bangkok DTSTART/RRULE.
- PRODUCTION VERIFICATION PENDING: require at least three actual future ordinary collection finals with real cross-domain source receipts, last_two_complete_shards and high candidate dispositions when applicable. Also require a next complete official daily Gmail Sent+readback and identical Git archival readback. Until then status is CONFIG_UPDATED_TESTED_IN_SIMULATION, NOT FULLY_FIXED.
- Provider safety blocks and social-feed source availability remain external and unresolved. Suppress false claims of complete web coverage. Actual schedule remains sparse; this is not a real-time alert service.

No user-visible extra mail was sent for this engineering change.
