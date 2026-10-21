# Crypto Daily — Git-controlled monitoring and editorial contract

Version: 2026-10-21 (architecture P0)
Owner: the EXISTING ChatGPT `Crypto 每日情报` scheduled automation. No local Mac process, launchd, GitHub Actions cron, paid Arkham/GMGN API, extra scheduler or added monitored category.

## The design decision

The short ChatGPT task prompt is **a bootstrapper, not a news editor**. Git main holds the complete, versioned operating rules. The running automation reads the latest Git rules on every real invocation. Its own natural-language improvisation does not override the current Git control plane.

The fixed report is broad market intelligence, NOT a list of projects the user joined. Personal participation affects whether a project is worth detail and action in its OWN section, never whether it is among the biggest global stories.

**Authoritative order**:
1. `REPORT_SPEC.md` — scope, 13 section names, data/semantic requirements.
2. `EDITORIAL_RULESET.json` — machine-readable news classification, primary section, Top5 gating, domain coverage, source proof and no-padding behavior. In routing/Top5 disputes THIS JSON wins over older example prose.
3. `REPORT_ACCEPTANCE.md` — all remaining acceptance rules, high-materiality source discovery, safety; newer CR requirements apply unless contradicting the specific classification JSON.
4. `COLLECTOR_SPEC.md` and `SECURITY_SOURCE_POLICY.md` — where/what to discover, bounded scope and source receipts.
5. `DELIVERY_RUNBOOK.md` — idempotency, sent verification, Git records and provider blocks.
6. `scripts/editorial_gate.mjs` and `scripts/daily_event_gate.mjs` — executable checks WHEN the actual task runtime can execute them. Versioned tests are `tests/test_editorial_gate.mjs` etc. Merely storing a .mjs in Git does not cause scheduled ChatGPT to run it.

**Conflict resolution**: never use the historical :00/:10 scheduler examples in old docs to change the existing actual user-authorized :20 schedule. Preserve one original task, its current delivery windows, Gmail address, and the separate TGE alert monitor. If a true rule contradiction remains unresolved, log the conflicting filenames and fail editorial QA on the disputed item, not assert that the entire pipeline is correct.

## Routing truth table — one PRIMARY home, not several

| User-facing section | Its own purpose | Example | NOT for |
| --- | --- | --- | --- |
| 1. 今日最重要的5件事 | 0–5 brief highlights of *verified and material global* developments already fully covered in their home sections | systemic exploit or new major funds-access restriction | BALANCE because user placed a bid; filling the number 5 |
| 2. BTC/ETH/SOL及主要资产 | time-stamped core quotes/range/volume and other actual prices | BTC 24h range | whale deposits, long-term trend |
| 3. 二级市场剧烈波动与持续趋势 | independent multi-period/derivatives evidence and unusual moves | ZEC 24h surge supported by market data | repeat section 2 price list |
| 4. 监管与政策 | new legal/exchange/regulatory rules | new HTX funding path restrictions | no-delta historical restrictions |
| 5. 机构/基金/鲸鱼真实资金动作 | real ETF flows, exchange wallets, original onchain entity/tx | **Clifton Collins distinct fifth 500 BTC** | infer sold BTC from custody transfer |
| 6. 融资/基础设施/RWA/PM/公链 | new fundamental protocol/company infrastructure facts | JPMD new Ethereum institutional support | public token auction/ticket |
| 7. 空投/TGE/ICO/公售/解锁 | current executable eligibility, token sale, bids, claiming, settlement | **BALANCE live CCA bid/clear/refund/claim ONLY when a distinct current action** | general BALANCE project coverage; global Top5 just because user participated |
| 8. Early/Meme/NFT/艺术 | substantive early-project research, art/token design and verifiable social/market heat | **BALANCE project fundamentals and Jack Butcher Credits/Statements art** | same BALANCE auction settlement/claim copied from §7 |
| 9. 安全/黑客/漏洞 | new exploit, wallet drain, loss, repair or active threat | Qubic weak seed new issuer advisory | old issue summary with no new detail |
| 10. 全球局势/跨市场 | significant current macro and rates/equity/geopolitical news | newly completed US close, 10yr yields, oil | repeat same BTC quote |
| 11. 未来24–72小时催化 | future independently sourced dated event NOT already repeated | launch/earnings/deadline with new action | expired date or extra summary of same incident |
| 12. 持续趋势与机会观察 | multi-period evidence, falsifiable invalidation and next checkpoint | why a tracked trend persists or breaks | same section 2 24h data alone |
| 13. 今日行动与风险结论 | distinct actionable consequence, safety and invalidation | check actual transferable auction token after settle | rehash detailed story again |

**BALANCE test**: BALANCE itself is an EARLY art/token experiment, so its primary *project story*, economics and verified valuation evidence are in §8. Only its independently distinct time-limited CCA bid/clear/claim/refund operations belong in §7; never duplicate the same facts in both. The user's personal stake never promotes it to global Top5. A large independent system-wide change would need explicit quantified external impact evidence, not popularity.

**Collins test**: a distinct new TXID and Arkham research qualify it for §5 once attribution is correctly caveated. It is a candidate for §1 ONLY if independently assessed as top-global significance, not simply because it exceeds a $10m *discovery threshold*. An exchange deposit is not a sale or proof of new police seizure.

**Security test**: major current loss or new exposure belongs §9. For a fresh extraordinary multi-user incident, a short §1 highlight may coexist. Do not mention Qubic/Cysic five more times in §6, §12 and §13 with no meaningful delta.

## Separation of source discovery from writing

**Phase A — source/discovery; no email**. In the original scheduled collector windows, inspect English primary official/market/onchain/Arkham/social/search sources within bounded cost, rotate existing deep shards fairly and record *actual* query, URL, checked_at, published_at, errors, candidate event_key/txid and exact material version. A full hourly attempt may be PARTIAL. Source `HTTP_403` is NOT `no_new_events`, and an old Arkham index is not comprehensive BTC-chain coverage. If a material candidate is missed by all available feeds, no downstream editorial linter can magically discover it; periodic retrospective source-lane recall must be independently reviewed.

**Phase B — candidate selection/classification**. At 08:20/09:20 read today's collector finals + previous 24h receipts and latest 48h urgent updates, seven days of REAL delivered Gmail/Git reports, the current `state/daily-event-ledger.json` and TGE known-events. Each new candidate has event_key, material_version/txid, actual delta, original date/url, source tier, confidence, affected users/scale, primary kind/section and include/watch/exclude reason. Rank severity *after* validating discovery. No global ranking by the projects the user holds.

**Phase C — write complete news**, 13 stable headings, market core/derivatives/capital flow/security/macro/forward risk/domain coverage actually checked; current quotes include as-of and precise source. No fixed item count and no repeated historical filler. If an area truly has no substantive new facts, include one `无高置信新增。` unnumbered line and an INTERNAL reason with concrete checked source receipts. A 13-heading/25-item report with multiple empty chapters, but no real checks or depth, is NOT complete just because headers exist. Never substitute a shortened correction for a normal broad-scope report.

**Phase D — machine/editorial QA**. Build *structured* `items[]`, `events[]`, `market_core[]`, `source_receipts[]`, `empty_section_reasons[]` manifest. Every numbered line is matched verbatim and has a real event key, kind and section. Reject wrong routing, BALANCE in global Top5, duplicates, missing new high candidate, absent BTC/ETH/SOL verified quotes, undocumented empty chapters, missing actual source receipts, stale dates, incorrect numbering and placeholders. Apply all other CR rules. When code execution is available in the automation environment, run the Git-hosted `editorial_gate.mjs` and existing `daily_event_gate.mjs`; otherwise mark `CODE_NOT_EXECUTED`, perform equivalent structured checks in the available tool environment and NEVER report a Node test run that did not happen. Git alone does not execute JavaScript.

**Phase E — Git prepare, actual Gmail, Git finalize**.
- Preferred normal path: save exactly ONE approved complete report candidate and its small QA/coverage manifest in the existing Git run/pending scheme. Read back SHA. Do not make repeated optional log writes prerequisite to email.
- First query Gmail Sent prefix for the target date (including corrected/resend), before any send. If Sent already exists, ONLY archive/repair. Do not send duplicate.
- If Git prepare fails due to provider controls, keep explicit `GIT_PREP_BLOCKED`. A *separately verified full/accurate* report can still attempt a normal Gmail send to prevent repeated missed mornings; this is a DEGRADED delivery, not false Git success, and must not bypass platform safety controls. An actual Gmail provider rejection is `BLOCKED_WITH_REASON` and cannot be overridden by Git.
- Send ONE complete `text/plain` report using existing authorized Gmail. Read actual Sent ID and entire body, revalidate sections and content, archive EXACT readback body in the canonical Git report (including original version supersession links if explicitly corrected). Read Git back; only then say `DELIVERED_AND_ARCHIVED`. If Gmail succeeded but Git failed: `SENT_ARCHIVE_PENDING`, NEVER resend.
- All process errors, source gaps and internal exclusions stay in Git run logs, not user-visible repeated numbered news. Silent if no separate Tier A/B TGE ACTION.

## GitHub-only executable check — no new scheduler

A checked-in JS gate is not self-executing on a ChatGPT task. To make the rules independent of prompt compliance, GitHub runs the **push-triggered**, **non-scheduled** workflow `.github/workflows/crypto-daily-editorial-qa.yml` when the existing monitor prepares a dated `crypto-daily/delivery-pending/YYYY-MM-DD.json` manifest. It uses a GitHub-hosted Node 22 runner, reads the current Git `EDITORIAL_RULESET.json`, runs the offline tests and machine gate, then writes SHA-bound `crypto-daily/delivery-qa/YYYY-MM-DD.json` on success. This is **not** another market monitor: it never scans external markets, never runs hourly and never accesses Gmail or wallets. It does not touch the user's Mac. Refer to `delivery-pending/README.md` for the exact schema.

The existing ChatGPT task must match Git SHA for the pending manifest, JSON rules and gate program against the CI receipt; a stale/missing receipt is `CI_NOT_PROVEN`, not a PASS. It should check Gmail Sent both BEFORE drafting and immediately BEFORE sending. When an already sent report exists, it skips even if CI triggered. A cloud provider failure cannot be worked around; any optional independently justified DEGRADED send stays accurately labeled and all provider blocks remain authoritative.

Cloud CI alone cannot guarantee a newly published Arkham story was discovered if no source scanner surfaced it. The full source-check receipt and candidate reconciliation are separately required. `_ci-selftest.json` is only proof the runner completed offline unit tests, never proof the report or mail reached the user.

## Non-goals and honest reliability boundary

- No Mac deployment or local background agent; no GitHub Actions schedule; no new monitor/scheduler; no change to existing reminder times.
- Git is the authoritative **configuration and evidence** store; existing ChatGPT automation is still the executor. This improves consistency/recoverability, but **does not guarantee** it can invoke Node, crawl every primary website, overcome X 403, or deliver through a platform-level Gmail safety block.
- The next scheduled run needs three observable independent passes: (A) genuine fresh primary source receipts / high-event recall, (B) actual routing/dedupe/coverage QA, and (C) Gmail Sent body readback + Git identical canonical. A code commit or chat resending manually never substitutes for (C).

## Rollout and rollback

P0: record this architecture and JSON classification authority on Git main, keep existing task/scope. P1: update original task's short bootstrap prompt to refer to Git instead of embedding the 13 chapters and all old examples; require rules version SHA and results in audit. P2: next actual scheduled run verify source receipts, section routing and Gmail/Git; do not claim healthy until verified. Rollback is a Git revert of this policy/version plus the existing task prompt, without touching Gmail historical Sent or historical report bodies.
