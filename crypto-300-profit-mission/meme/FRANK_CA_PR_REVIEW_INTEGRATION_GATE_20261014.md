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

## 2026-10-14 actual combined code CI (not Mac acceptance)

- The second Claude reviewer returned **REQUEST_CHANGES** on C02 #49 `9c16829e` and A04 #48 `26c40912`/upstream #45 `92fbacbc`. Remediation is now PR #49 at `8898134a8a302e1187138f7fb3da87a554567e6d` with [CI #38503360215](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38503360215) 20 focus/1,452 whole PASS, and new child [PR #50](https://github.com/lxxlx2/ChatGPT_mission_record/pull/50) at `4cef47ac63d1a0a2beb9ec7924214a127c97e32f` with [CI #38503749827](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38503749827) 52 focus/1,534 whole PASS.
- **A real disposable multi-branch merge and joint code regression was run** in [Actions #38504090624](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38504090624) from current fetched origin/main at run time, merging in order: `origin/fix/frank-ca-a04-owner-gaps-source-replay-20261014` (includes #42/#43/#45/#48), `origin/fix/frank-ca-c02-identity-preview-casefold-review-20261014` (includes #46/#47), `origin/dev/frank-ca-f01-actionable-view-20261013` (#44). All three merge commits succeeded in isolated runner without conflicts; focused combined F01 + CA C01/C02 + A04 **48 PASS**, complete local-agent real Git suite **1,586 PASS**. No branch push, no main merge, no production changes.
- This removes the **known code-level merge/test blocker** in the listed versions, but does **not** replace new Claude independent review of fixed exact SHAs, live Mac browser + genuine RPC run, current inventory/32-Mint sidecar data, approval to deploy or post-deploy check. CI tested exactly current fetched versions at run time; newer changes require re-running this gate.
- Regulatorily important distinction: existing WALLET_TX_VIEW stored on an older v1 schema is historical evidence, not suddenly corrected. `WALLET_TX_VIEW_V2` must be derived explicitly from the immutable RAW_TX and its missing-owner evidence; no automatic sale/PnL inference.

## 2026-10-14 third Claude exact SHA review + P2/P4/P6 repair and new integrated CI

- **PR #49 `8898134a8a302e1187138f7fb3da87a554567e6d`: independent Claude `APPROVE`** on that exact SHA (full pytest 1,452; scoped 27; F01+CA real `app.js` VM render clean). Low/nonblocking Turkish dotted `İ` conservative mismatch and F01 shortened Mint/card copy. This is user-provided **external review**, not recorded GitHub formal review or Mac production acceptance. Source code in #49 unchanged.
- **PR #50 `4cef47ac63d1a0a2beb9ec7924214a127c97e32f`: independent Claude `REQUEST_CHANGES`**, High P2 unknown owner nonzero delta silently dropped, P6 V2 re-projection blocked only transiently with misleading CAPTURED state, P4 failed transaction parsed transfer incorrectly confirmed; Medium P5 SOL and P7 mixed V1/V2 kind. Do NOT merge #50 as-is.
- **New child [Draft PR #51](https://github.com/lxxlx2/ChatGPT_mission_record/pull/51)** fixes P2/P4/P5/P6/P7 at exact SHA `c2cf581196d19e61306148cdfb85ce4857d8f02f`: unknown owner nonzero always blocks and preserves pending reason; captured legacy signature missing/blocked V2 is persisted as error and reports `PARTIAL_ECONOMIC_EVIDENCE`; failed tx token instructions are NOT_EXECUTED; native SOL not observed counted separately; new views are immutable `WALLET_TX_VIEW_V2`, original RAW_TX and legacy V1 not overwritten.
- [Exact-head #51 test CI #38543947263](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543947263) **SUCCESS**: 57 scoped + 1,539 complete local-agent. [New disposable combined code tree #38543947345](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543947345) **SUCCESS**: current-at-run origin/main + A04 stack ending #51 + CA stack ending #49 + F01 #44 all merge clean, 53 combined scoped + **1,591 full real-Git PASS**. No main/PR merge, production SQLite, Gmail, Mac app or launchd changes.
- **Still BLOCKED for shipping**: independent another-AI review *of #51 final SHA* (old #50 review cannot be reused); actual owner-missing and failed parsed transfer fixture from Solana finalized raw `getTransaction`; real Mac 32-mint/ATA/inventory state and browser end-to-end; approved deployment. The connected RPC found an actual failed signature (slot 456780885), but raw getTransaction output was truncated by connector transport; no genuine failed parsed-instruction fixture has been committed. Two sampled successful transactions at slots 456789461/456789273 had complete parsed receipts and owner fields. Explicitly keep this as evidence gap, not test PASS.
- Long-term checkpoint: `FRANK_CA_A04_CLAUDE_P2_P4_P6_REMEDIATION_20261014.md` in PR #51, with exact source evidence. F02 and full market cost/PnL remain not done.

## 2026-10-14 fourth independent Claude review — newest unreviewed child #52

- User-provided fourth Claude report: **PR #51 exact SHA `c2cf581196d19e61306148cdfb85ce4857d8f02f`: REQUEST_CHANGES**. Confirmed earlier High P2/P4/P6 repairs by fixed RPC fixture before/after comparisons; **new Medium**: constant `NATIVE_SOL_FLOW_UNCLASSIFIED` even on fee-only Token tx makes AVAILABLE impossible, N1 unrelated missing-owner nonzero delta halts older pagination, missing automated old SQLite migration test. Full failed RPC instruction/actual owner-missing still unavailable. Independently approved **PR #49** stays untouched.
- **Draft [PR #52](https://github.com/lxxlx2/ChatGPT_mission_record/pull/52)** child of #51, no rewrite of parent reviewer SHA. Native SOL tracked account lamport deltas vs fee and relevant parsed System instruction, with **distinct missing-source state**; manual `--continue-on-owner-gaps` opt-in archives RAW_TX only, preserves V2 blocker and partial economic coverage so older source pages can continue; automated old-sidecar ALTER TABLE replay preserving RAW_TX/V1/cursor; first **genuine complete finalized Solana Token-2022 ATA creation transaction fixture** at Slot 456789461, signer rent payer ≠ Frank account owner, false native flow prevented. See `FRANK_CA_A04_CLAUDE_N1_SOL_AND_REAL_ATA_20261014.md` in PR #52.
- Still **independent Claude RE-REVIEW REQUIRED on #52 final code SHA**, not previously reviewed SHA. Exact-head full CI + true combined F01/C02 CI to be separately pinned. Real failed parsed `getTransaction` / nonzero owner-missing / ATA-close sample unavailable; full 32-Mint/ATA history, cost/PnL and Mac Dashboard end-to-end pending. No production release or import of uncertain research records into Frank V1.

## Review priority rather than endless edge chasing

**Immediate:** Review #48 journal and #45 sidecar together for loss/skip/duplicate and 429 retry; review #49 C02 R-a/R-b fix and the source provenance; review #44 F01 freshness boundary. **Then** joint frontend route integration and Mac QA. C02 low-probability PDA curve nuance R-c is recorded as non-blocking until a failing real or deterministic proof; do not divert business work from inventory accuracy. C02 external Token-2022 metadata interface remains UNCONFIRMED; status must be honest.

Source examples: PR #47 review+code and external Claude transcript provided in the conversation; GitHub #42–#49 snapshot and original CI artifacts. This document is an integration queue, not an assertion that Claude ran on #49 or that combined code exists.
