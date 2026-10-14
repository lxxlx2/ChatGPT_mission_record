# C02 Claude independent review follow-up and integration gate (2026-10-14)

Status: **R-a / R-b PRODUCT FIXES SUBMITTED; exact-head CI and independent re-review REQUIRED; NO MERGE / NO DEPLOY.**

Scope: child of original Codex C02 [Draft PR #47](https://github.com/lxxlx2/ChatGPT_mission_record/pull/47), pinned original HEAD `c4073f699bff7744ca623f6adbbab8397a75b3ca`. The original PR remains unmodified to preserve its reported tests/review audit and is stacked on C01/C08 [Draft PR #46](https://github.com/lxxlx2/ChatGPT_mission_record/pull/46).

## What independent review established

- C02 latest SHA Actions `38499360445`: 13 focused, 1445 complete real Git regression PASS. Separate Claude review reproduced these numbers and found legitimate product risks R-a/R-b.
- Original first Gemini request returned UNAVAILABLE; independent response actually model `gemini-3.5-flash`, reviewed **product SHA `3ed4755e99a92983810e9ba27b844c80f795d1be`**, not final evidence-only SHA `c4073f69`. GitHub compare confirmed only report/evidence changed between these two. The C02 research file already records this correct nuance; do not report `gemini-3.7` or exact-final-SHA independent review as a fact.
- Original RED case 1 is a genuine self-quote acceptance behavior failure, case 2 is a KeyError for missing market_match_status, not proof that an existing direction field was wrong. Native screenshot evidence is isolated saved-case browser QA and `ca_identity_render.cjs` is Node VM/stub DOM, *not* a Mac production end-to-end user query.
- Original official evidence contains **three** separately verified Agency-name mints, including `H4UH4ypR3nTqDHJPJurYL2GsDWzotKzzU1Kmj3XiqFkj`. `7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump` and screenshot transcription `...VXPpump` are different, both structurally valid Solana keys; latter RPC returned null in saved result. User input truth remains exact CA, no name-based correction.
- The asserted 20 report chunks are summarized in an archived-provenance metadata field with a source branch/SHA. A complete twenty-chunk reproduction is **not packaged into the C02 PR**. Describe it as referenced archived provenance, not independent reproduction from PR files.
- C02 changes the shared `mission_control/server.py` and `static/app.js` import/render paths, even if Frank V1 frozen signal policy remains unchanged. It is *not deployed*; importing that shared Dashboard process changes behavior after a future deploy, so it needs joint regression with F01 (#44) and C01 (#46).

## Fixes on this child PR

- **R-a**: use the job's exact submitted Mint in BASE_READY progress and preview; UI progress shows mint prefix+suffix, while preview shows the full CA in escaped code. Existing final report continues full CA. No metadata/pair source is permitted to substitute the Mint. Same-name mint identity remains independently verified in the backend cache.
- **R-b**: use casefold-equivalent normalized labels for *source-conflict comparison* as already used for display de-duplication. Only letter case differences no longer generate a false conflict. Substantive name/symbol differences **continue to fail closed**; raw source records remain unmodified for audit.
- `identity_status=VERIFIED` and `conflict_status=TOKEN_IDENTITY_CONFLICT` denote independent facts (mint-bound chain metadata verified vs external label disagreement). This is not a claim that the cross-source identity is fully trusted. UI highlights conflict as an error; do not silently discard the chain proof to conceal a conflict.
- No fix for theoretical low-probability PDA curve edge R-c this round. Address when/if evidence or affected deterministic test exists. External Token-2022 interface still `UNCONFIRMED` and separate native Mac acceptance remains open.

## Regression and release constraints

New `tests/test_frank_ca_c02_claude_review_regression.py` covers case-only non-conflict, genuinely different source conflicts, two same-name mint BASE_READY payloads. Existing real `app.js` Node render test now requires full exact CA in preview and compact distinct CA in progress for each of six saved official examples.

Dedicated workflow executes focused tests, `node tests/ca_identity_render.cjs`, lint, syntax, complete local-agent real Git replay. **Must record its exact HEAD result** and get a second reviewer after this change. No merging into parent #47, no current-main integration, production deploy, Frank V1, Gmail, forward.sqlite, or LaunchAgent changes.

Required future integration gate: combine independent F01 (#44), C01/C08 (#46), C02 (#47+child), A02/A03/A04/A05 (#42/#43/#45/#48) on a disposable branch; replay all relevant tests and browser against the *combined* source. Individual green CI does not establish combined compatibility.
