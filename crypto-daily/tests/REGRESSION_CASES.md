# Crypto Daily Regression Cases

Updated: 2026-09-29

| ID | Fixture | Expected |
|---|---|---|
| CR-01 | Normal 24h input pool with all mandatory lanes | complete 13-section report |
| CR-02 | One hourly research artifact missing but final exists | manifest records gap and uses final compact payload where available |
| CR-03 | Several collector hours missing | report may proceed only with explicit manifest gaps and fresh verification; cannot infer no-event |
| CR-04 | Known material security event appears during prior 24h | Section 9 includes it or audit records explicit verified exclusion |
| CR-05 | X/specialist security source unavailable | mark source gap; use allowed fallback; never convert to checked_no_update |
| CR-06 | Known MEXC-style CEX account takeover appears in fresh English sources | security candidate must enter verification pipeline |
| CR-07 | Same security incident unchanged from prior day | dedupe; at most concise ongoing/no-material-change carry-forward if still critical |
| CR-08 | TGE event is old/refunded/completed/user-known | do not recycle it as new Section 7 item |
| CR-09 | Early/Meme/NFT lane did not run | Section 8 cannot claim “no opportunities”; manifest records unavailable/gap |
| CR-10 | ETF/whale/exchange-flow material change | Section 5 checked and included when decision-relevant |
| CR-11 | 09:00 send succeeds but GitHub archive fails | no resend; archive-only recovery |
| CR-12 | 09:00 send fails but QA-approved pending exists | recovery sends exact same complete 13-section body |
| CR-13 | Recovery/supplement is short patch only | cannot replace official report |
| CR-14 | Gmail body != GitHub canonical body | delivery not fully complete until Git repaired |
| CR-15 | Body/item count collapses below 70% trailing-5 median due to time pressure/provider error | QA_FAIL; recovery must rebuild missing coverage |
| CR-16 | Internal monitoring failure text dominates user report | QA_FAIL; plumbing stays in audit |
| CR-17 | Major market move has no single confirmed cause | report confirmed factors + uncertainty; no invented causal certainty |
| CR-18 | Prior same-day incomplete/incorrect edition exists | final full edition may supersede once; metadata keeps old message id |

Pass requirement: 18/18.

## V2 systemic discovery regression suite (2026-10-10)

Validation type: specification/rotation-contract dry-run, NOT a claim that a future scheduled collector or Gmail already ran successfully.

| ID | Scenario/input | Required V2 outcome | Dry-run status |
|---|---|---|---|
| V2-01 | Ordinary hours 00/03/06/15/19/23; old `hour % 3` | Old gives 0,0,0,0,1,2: detectable bias, never use | PASS |
| V2-02 | No missing ordinary runs | Deep shards 0,1,2,0,1,2; all categories twice/day | PASS |
| V2-03 | 19:10 slot has no persisted final | 23:10 catches missing shard 1 instead of silently calling it covered | PASS |
| V2-04 | 03:10 slot has no persisted final | 06:10 executes shard 2 and 15:10 catches shard 1; no false prior completion | PASS |
| V2-05 | All final/retry persistence fails | Run is UNHEALTHY, unknown coverage; cannot become success | Contract check only |
| V2-06 | Abstract L2 shutting down, user-specific TGE suppressed | Market-wide chain shutdown is still eligible in existing Section 6 or 9; TGE alert remains suppressed | Contract check only |
| V2-07 | Ledger multiple users report theft, researcher estimates >$86m | DISCOVERED/VERIFYING; no assertion of audited $86m, hardware exploit or actual loss | Contract check only |
| V2-08 | XRPL official critical flaw published Oct 9 after Sept 25 fix | Newly disclosed official critical security item must be considered for Section 9 even without a known public exploit | Contract check only |
| V2-09 | Oct 9/10 national blockchain policy with earlier 15th Five-Year planning | Section 4/6 material policy candidate; no invented public token or legalization | Contract check only |
| V2-10 | 23:00 news appears after normal day's report | Next existing collector plus next normal report; never backdate or duplicate prior Gmail | Contract check only |
| V2-11 | Two English outlets copy same unverified analyst | One research lead, not two independent fact confirmations | Contract check only |
| V2-12 | 3–4 major stories but report fixed heading contains '5' | Top5 has 3–4 verified items and no filler; CR-18 still applies | Contract check only |
| V2-13 | Collector discovery was skipped but writer has correct prices | Pre-send independent cross-domain headlines check required; missing attempt cannot be called QA_PASS | Contract check only |
| V2-14 | Gmail Sent exists while Git report missing | Archive from actual Gmail readback, no duplicate email | Contract check only |
| V2-15 | User-specific TGE has no verified ACTION | No Gmail; do not transform TGE into a daily mandatory email | Contract check only |

Dry-run executable rotation inputs: normal [0,3,6,15,19,23] -> [0,1,2,0,1,2]; missing 19 -> [0,1,2,0,missing,1]; missing 03 -> [0,missing,2,1,0,2]. The 'PASS' results above validate scheduling decisions only, not live discovery. Before declaring the fix VERIFIED IN PRODUCTION, inspect >=3 future *actual* ordinary collectors and at least one next complete Crypto Daily Gmail Sent/readback/Git body equality. Any missing final or key source receipt keeps status PARTIAL/UNHEALTHY.

Pass threshold for V2 claim: actual persisted finals report `cross_domain_receipts`, `last_two_complete_shards`, `executed_shard`, and `high_impact_candidate_dispositions` when applicable, plus distinct delivery proof. Missing test evidence is FAIL/NOT YET VERIFIED, never inferred PASS.
