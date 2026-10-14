# Frank / CA cross-PR independent review and integration gate

Checked: 2026-10-14 Asia/Bangkok
Status: `REVIEW_QUEUE_ACTIVE / CODE_CI_EVIDENCE / COMBINED_CI_NOT_RUN / MAC_NOT_DEPLOYED`.

## Review status, do not infer acceptance from a green workflow

| Line | PR stack, exact examined HEAD | Existing evidence | Mandatory pending before integration |
|---|---|---|---|
| Research persons/registry | #42 `22f7b8f7` → #43 `0010a7b8` → #45 `92fbacbc` → #48 `26c40912` | Corresponding GitHub CI green; #48: 43 focused and 1,525 whole local-agent PASS | Independent other-AI review **of current code stack and exact SHAs** focusing on registry authority, immutable Sidecar and A04 page/transaction atomicity; verified Mac ATA/32-mint data later |
| Live-follow UI presentation | #44 `516e3335` (independent from main) | F01 exact SHA CI #38418188923 PASS | Independent UI/data contract review, then combined Dashboard route and DOM tests with CA |
| General CA one-mode | #46 `e2fdb48e` | Exact SHA #38424959476 success | Independent other-AI review of CA/legacy Frank boundaries |
| Exact-mint C02 | #47 `c4073f69` (child of #46) | Exact SHA CI #38499360445 1,445 PASS. Gemini `gemini-3.5-flash` reviewed **product code** `3ed4755e` (later SHA only changed evidence/doc). Claude independently reproduced 13 C02 and 1,445 whole and identified R-a/R-b | Claude report constitutes **findings pending remediation**, not unconditional approved release; same-name preview CA and capitalization false-conflict resolved in separate #49; keep #47 original SHA immutable |
| C02 review follow-up | #49 child of #47, HEAD inspect live | Exact-head workflow `frank-ca-c02-claude-review-integration-20261014.yml` | On final exact SHA independently review R-a/R-b and code and verify full CI; preserve user source-case evidence |
| Current main | `f1dadb1a` when checked | Main head moved due unrelated runs/status updates | Re-read before **all** rebases/integration; do not overwrite live `state/latest.md`, positions or portfolio |

**GitHub PR metadata consistency:** normalized `get_pr_info` returned `mergeable=false` for #42 and #44 while raw GitHub REST PR reads returned **`mergeable=true, mergeable_state=clean`**; the raw state is higher fidelity and there is **no confirmed Git conflict** from these reads. This does not prove the separate code branches work together.

## Exact code overlap and the actual regression risk

- #44 (F01) changes `mission_control/server.py`, `static/app.js`, `static/index.html`.
- #46 (C01/C08) changes **all three** above.
- #47 (C02) changes `server.py` and `app.js` again, plus `meme/cluster.py` / `market.py` / `identity.py`.
- #49 changes C02 identity, `server.py` and `app.js` again. Tests on each branch **do not** show F01 and C02 simultaneously running.
- #42/#43/#45/#48 alter research registries, wallet-source/Sidecar/ledger/CLI; these must not be imported into Frank V1's frozen decisions without separately approved live authority.
- All PRs listed above remain Draft/unmerged at this checkpoint. No GitHub formal reviews were recorded for #47/#48 when read; external reports are not GitHub approvals.

## Non-negotiable staged integration gate before PR is marked ready

1. **Resolve current review findings on the owning child branch**; never rewrite already reviewed parent SHA. Independent reviewer returns `APPROVE / REQUEST_CHANGES` on **exact code SHA** and material findings, with a code-to-document-only SHA comparison for evidence-only commits. If code changes after review, review impacted code again.
2. **Merge order (disposable integration only, not production):** registry #42 → #43 → #45 → #48, then CA #46 → #47 → #49, then F01 #44 (adapt conflicts intentionally). Track exact parent SHA and file hashes; verify all independent tests in one combined checkout. Do not mistake a green standalone PR for joint compatibility.
3. **Business contract checks on the combined checkout:** old Frank V1 decision/output digest unchanged; no new Gmail/LaunchAgent/production SQLite; F01 only truly actionable, current signals; C01 one mint query, no implicit Jupiter $30; C02 exact mint and unique display at preview and final including same-name tokens; A04/5 no unknown-to-zero promotion, no tx double count, no false `HISTORY_COMPLETE`; all old APIs still parse, no broken shared import.
4. **Tests:** compileall/pyflakes/Node; complete local-agent tests with real Git replay; all focused A02/A03/A04/A05/F01/C01/C02; **actual browser using combined server response**, not Node-only stub, including saved Agency 3 same-name mints and unknown/conflict; a read-only local Mac preflight without changing runtime; rollback baseline, hash, test logs and gaps recorded.
5. **No release until** reviewed exact combined SHA, all high/medium findings addressed, user explicitly authorizes Mac deployment, and postdeploy checks verify existing Frank mail/Loop/SQLite untouched. `NO_MERGE / NO_DEPLOY` otherwise.

## Review priority rather than endless edge chasing

**Immediate:** Review #48 journal and #45 sidecar together for loss/skip/duplicate and 429 retry; review #49 C02 R-a/R-b fix and the source provenance; review #44 F01 freshness boundary. **Then** joint frontend route integration and Mac QA. C02 low-probability PDA curve nuance R-c is recorded as non-blocking until a failing real or deterministic proof; do not divert business work from inventory accuracy. C02 external Token-2022 metadata interface remains UNCONFIRMED; status must be honest.

Source examples: PR #47 review+code and external Claude transcript provided in the conversation; GitHub #42–#49 snapshot and original CI artifacts. This document is an integration queue, not an assertion that Claude ran on #49 or that combined code exists.
