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
