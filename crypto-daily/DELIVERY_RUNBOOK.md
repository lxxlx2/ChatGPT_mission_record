# Crypto Daily Delivery Runbook

Updated: 2026-09-28 19:34 Asia/Bangkok
Timezone: Asia/Bangkok
> Active user-authorized schedule (2026-10-10): existing `Crypto 每日情报` at :20 Asia/Bangkok; 00:20/03:20/06:20/12:20/16:20/20:20 bounded collectors, 08:20 prebuild, 09:20 primary, 10:20/11:20 recovery. The old 09:00/10:00/11:00 and dedicated publisher text below is historical, not active. `COLLECTOR_SPEC.md` V2 + `REPORT_ACCEPTANCE.md` CR-20 govern discovery. No task or schedule change.


## Execution model

本 Runbook 由现有 `Crypto 每日情报` automation 在特定小时调用，不对应独立 scheduler。

- 09:00：主发布。
- 10:00：仅在当天日报不完整时恢复。
- 11:00：最后一次当日自动恢复。

其它小时不进入正式发布流程。

## Dedupe

每次发布/恢复前检查：
1. `crypto-daily/reports/daily/YYYY/YYYY-MM/YYYY-MM-DD.md`
2. Gmail Sent 中 subject = `Crypto Daily Brief｜YYYY-MM-DD`

若 official Gmail 已存在且 GitHub report 完整：
- 不重复发送；
- 当前小时继续按普通 collector 模式即可。

若 Gmail 已存在而 GitHub 缺失：
- 从 Gmail readback 恢复同一正文到 GitHub；
- 不重复发送 Gmail。

若 GitHub report 存在但 Gmail 不存在：
- 读取并 QA report；
- 合格后发送 Gmail；
- 回写 message_id。

## Delivery order

1. 聚合过去 24h research；若某小时 research 缺失但 final/final-retry 存在，也读取 final 中的 compact research payload / material candidates。
2. 建立 critical security carry-forward 清单，并逐项 fresh verification；任何需 revoke/patch/move/reclaim、>= $1M exposure/loss、或仍开放的钱包/approval/bridge/exchange漏洞不得静默丢失。
3. 对其余最高优先级事实做 fresh verification。
4. 生成 REPORT_SPEC 的固定 13 章。
5. QA。
6. **先发 Gmail**。
7. Gmail readback。
8. 写 GitHub official report。
9. GitHub readback。
10. finalize 当前小时 run audit，并记录 critical-security seen/included/omitted-with-reason。

GitHub archive 失败不得取消已经成功的 Gmail。

## Graceful degradation

非关键数据源失败时：
- 使用其余可靠英文/官方来源；
- 对缺失字段明确写“本轮未取得可靠数据”；
- 继续交付。

只有以下情况允许完全不发：
- 无法取得足够信息形成基本可靠报告；
- Gmail connector 不可用；
- QA 发现重大事实冲突且本轮无法消除。

## Recovery

09:00 失败后，10:00 自动检查当天是否缺报。
10:00 仍缺则重新尝试。
11:00 是最后一次当日自动恢复。

任何 recovery 都必须先 dedupe，正常情况下同一天只允许一封 official report。

## Success

- Gmail sent + Gmail readback + GitHub archive + GitHub readback = success。
- Gmail sent，但 GitHub archive 失败 = partial_success，日报视为已送达，后续只补 GitHub。
- Gmail failed = failed / partial_failure，后续 recovery 可重试。


## Dedicated fallback task — 2026-09-27

The existing `Crypto 09:00 日报发布` automation is the delivery fallback for the primary hourly task.

Schedule:
- 09:20
- 10:20
- 11:20
Asia/Bangkok.

It is delivery-only and idempotent.

Before any send:
- search Gmail Sent for exact subject `Crypto Daily Brief｜YYYY-MM-DD`;
- check the official GitHub report;
- check `crypto-daily/delivery-pending/YYYY-MM-DD.md`.

Recovery order:
- Gmail + GitHub both complete: silent exit.
- Gmail complete, GitHub missing: recover GitHub from Gmail readback.
- GitHub complete, Gmail missing: QA and send the archived body.
- both missing, pending body exists: send pending body, read back, archive official report.
- all three missing: reconstruct from the prior 24h research/final audits, create the pending body first, then send.

A prior automated claim of “already sent” is insufficient. Delivery proof requires an actual Gmail Sent message id and successful readback.


## Prebuild handoff

The 08:00 hourly collector prepares `delivery-pending/YYYY-MM-DD.md` but does not send.

The 09:00 publisher treats that pending file as the primary body:
- refresh only facts that are materially time-sensitive;
- preserve the body structure unless a correction is needed;
- Gmail delivery takes priority over broader research;
- target Gmail proof by 09:20.

If a valid pending body exists, recovery jobs must send it rather than rebuilding a new long report.


## Full-body resend rule — 2026-09-29

When the user requests a daily-report resend, correction, or reissue, recovery MUST NOT send a shortened digest as the replacement official report.

The resend must:
- contain all 13 REPORT_SPEC sections in the canonical order;
- meet the same factual and source-quality bar as the normal 09:00 report;
- include all material corrections discovered since the original report;
- use Gmail Sent + readback as delivery proof;
- write the identical body to the canonical GitHub daily-report path;
- read back GitHub and verify body equality;
- mark prior incomplete same-day editions as superseded.

An error-specific supplement may still be sent, but it never satisfies a request to resend the full formal daily report.


## Acceptance-gated delivery — 2026-09-29

Before any formal send or recovery send, read `REPORT_ACCEPTANCE.md`.

A formal send requires:
- current `delivery-manifest/YYYY-MM-DD.md`;
- `qa_status: PASS`;
- complete 13-section body;
- no unresolved CR hard-gate failure.

If manifest is missing/stale or QA is FAIL:
- do not send a digest;
- rebuild only the missing inputs/sections;
- rerun QA;
- then deliver.

The dedicated recovery automation must never invent a smaller replacement body. It may:
1. send the existing QA-PASS canonical body;
2. repair GitHub from Gmail readback;
3. rebuild missing coverage until the full body passes QA.

After send:
- read Gmail;
- archive the exact readback body;
- read GitHub;
- verify body equality;
- only then mark full delivery complete.

A short correction/supplement is supplemental only and cannot become the canonical daily body.

## 2026-10-16 delivery proof and suffix-aware deduplication

The 2026-10-16 primary 09:20 invocation persisted `runs/2026-10-16/092111-final.md` with `BLOCKED_WITH_REASON` from a Gmail safety gate, and had no 08:20 `delivery-pending/2026-10-16.md`. In an authorized same-day recovery, a complete 13-section email was actually sent and read back:
- report date: 2026-10-16
- Gmail Sent subject: `Crypto Daily Brief｜2026-10-16｜正式补发`
- Gmail Sent message ID: `1a1429397db803fe`
- canonical Git body: `crypto-daily/reports/daily/2026/2026-10/2026-10-16.md`
- Git archive SHA: `19438b9b738b211bdda7ace0d6fe674c95e4acbd`

**Recovery idempotency fix:** search Gmail Sent by the canonical date SUBJECT PREFIX `Crypto Daily Brief｜YYYY-MM-DD`, including `｜正式补发`, `｜历史漏发补送` and corrected subjects. Accept one matching authoritative, full-body, Sent-readback Gmail message plus canonical Git body equality as delivery proof. Never require the subject to equal the unsuffixed base string, and never resend because the approved recovery edition has a suffix.

At each existing 08:20 run, persist a durable QA-evidenced pending body and input manifest before optional deeper collection; if unable, persist a truthful reason in the terminal audit. At 09:20/10:20/11:20, lack of pending must trigger bounded reassembly and the unchanged full CR-01..CR-20 QA gate. Platform safety rejection remains BLOCKED_WITH_REASON and must not be bypassed; recover only via ordinary authorized calls. Gmail Sent/readback and canonical Git proof take precedence over any historical blocked attempt artifact. This fixes dedupe and records a reproducible prebuild gap; it does not assert that future platform safety blocking has been eliminated.

## 2026-10-21 publisher contract: discovery + dedupe + credible normal delivery
1. Sent-prefix check FIRST; same-day already-delivered formal/correction/resend is immutable and never silently duplicated. Reconcile only missing archive.
2. Consume current original English market/news source receipts and a bounded Arkham/Lookonchain/labelled BTC headline scan, plus seven-day real Sent/Git canonical history and existing TGE event ledger. Create an event/version decision matrix IN MEMORY; never pad 13 sections with historic safety, project-rights SOURCE_GAP, "no updates" or task-process statements. Account for each verified high materiality new item even if it has the same 500 BTC round value as old moves.
3. Construct one full final 13-section report. Before send perform semantic candidate accounting, no-delta suppression, ≤2 mentions per unique story, source/time/uncertainty checks and independent section-local 1..N numbering. When Node exists run \`node crypto-daily/scripts/daily_event_gate.mjs manifest.json\`; Node unavailable -> record gate not executed and run explicit equivalent in-memory checks (not a fake code PASS). The same report still must satisfy all preexisting CR gates.
4. Once real full QA passes, attempt Gmail normal delivery without optional repeat Git pending/attempt writes as a prerequisite. Provider Gmail safety block is real BLOCKED_WITH_REASON, never bypass; do not claim actual delivery. Successful Sent/readback followed by exact Gmail-body Git canonical archive; Git failure after Gmail is archive-only recovery, not resend. No user-visible health emails.
5. Store the compact per-event discovery/disposition in the single existing terminal final or optional pending metadata rather than creating an extra mutation per candidate. No separate new task, paid data subscription, credential or deployment.

## 2026-10-21 correction and real discovery source-receipt workflow
1. Check same-day Gmail Sent incl full corrected subject before ANY outgoing email. Oct21 corrected full Crypto email was sent as Gmail ID 1a15c6d25715d6ca and supersedes original 1a15c49e3ff24c51; do not resend either.
2. On each normal research round, gather truthful primary Arkham/Lookonchain BTC flow discovery receipts alongside original source lanes. Available on a real Node+network host: node crypto-daily/scripts/arkham_primary_discovery.mjs. Do not say code ran from a ChatGPT task unless it actually did; manual web discovery instead has its own real receipt status. Never equate reading Arkham homepage with complete blockchain coverage.
3. Use last seven successful Sent/Git daily reports plus state/daily-event-ledger.json to dedupe by exact event+material_version (txid, contract action, issuer update, market day). Existing fifth Collins transfer is already delivered in corrected edition. Old Qubic, Cysic, JPMD, HTX, Cambria, StandX, NeoSoul etc without new delta must not use numbered email space.
4. Check canonical 13 headings and each local 1..N numbering, cross-section unique-event maximum two mentions, all high-materiality candidates and source/uncertainty details. No need to pad an empty section. Keep operational metadata out of user email.
5. Send complete report only after true final QA, real Gmail Sent and full body readback, then archive actual readback body in Git. Provider safety block must be honestly marked and cannot be bypassed. A successful user-requested manual correction does not prove future autonomous delivery.

## 2026-10-21 Git control plane orchestration (current authoritative)

Use `PIPELINE_CONTRACT.md` + `EDITORIAL_RULESET.json` from Git main at START, record blob SHA/version. Collect source receipts and classify all candidates; create a full 13-heading report and editorial manifest, compare seven-day Sent/Git and ledger, check Top5 and primary sections BEFORE optional Git prepared write. Re-read rules SHA before send; a changed policy invalidates the old candidate QA until reconciled. Prefer one Git prepared artifact (full report+evidence) then one Gmail send then Git Sent-receipt canonical/archive. Do not make multiple optional attempts/temporary file updates block a fully validated legitimate send; platform Gmail block cannot be bypassed. Where Git ready file is unavailable, delivery is DEGRADED and must be independently QA-proven in memory, then Gmail readback and Git archive-only retry. Preserve Sent-prefix idempotency and explicit corrected-mail policy. User Mac is NOT a runtime. A Node script committed on GitHub does not self-run; when scheduled runtime cannot execute it, record CODE_NOT_EXECUTED, run explicit structured equivalent checks and do not claim the executable passed. All prior conflicting historic recipe paragraphs are deprecated by this section.

## 2026-11-05 P0: missing prebuild cannot terminate existing recovery windows
Confirmed: The 2026-11-05 09:19 audit `runs/2026-11-05/0919-incomplete.md` recorded no current-date pending manifest, QA or canonical report and did not send. Existing 10:20 recovery terminal `runs/2026-11-05/102056-final.md` repeated "no pending/QA" and did not reconstruct. No Crypto 11/05 was sent by the planned windows. The original 08:20 prebuild had left only a partial audit. This is a reproducible **handoff/branching failure**, not proof a Gmail provider rejected the send.
Use `scripts/daily_event_gate.mjs` exported `decideDailyRecovery` (or the EXACT same verified decision in a no-Node runtime) in all existing publisher/recovery slots:
A. Gmail Sent verified: archive exact Gmail readback if Git canonical absent, otherwise skip; NEVER resend.
B. Gmail not sent + QA-passed complete full report exists + full independent source/previous-seven-day review: recheck Sent then send once, readback and archive.
C. Gmail not sent + missing pending/QA or invalid draft: **IMMEDIATELY reconstruct the complete 13-section report** from last 24h research, scheduled terminal audits and fresh original English sources, perform independent source/novelty verification, build QA and send if valid within the existing delivery window. **Missing prebuild is a work trigger, not a success/final block reason.**
D. If an actual blocker remains, record exact missing evidence and `DELIVERY_PENDING_QA`; do not invent QA_PASS or send unverified content. In subsequent original 10:20/11:20 window retry reconstruction first instead of just re-reading missing files. No new automation, external cron or unscheduled fallback.
A valid full delivery is proven by Gmail Sent ID + recipient/body readback, even when pending Git/CI artifacts were unavailable and QA was independently completed with explicit `CI_NOT_PROVEN` (as existing degraded-delivery instructions allow). Git archive can follow asynchronously in the same invocation; failed Git after real Sent is `partial_success`, and recovery only repairs archive.
Fixed-date regression result: 2026-11-05 23:21 BKK manually rebuilt 13 chapters, independently checked actual official market sources, SignalPlus API warning, Reuters, Binance recovery #8, Circle SEC, Bitget rANT, Farside and BLS; sent `Crypto Daily Brief｜2026-11-05｜正式补发（SignalPlus API安全风险）`, Gmail ID `1a1ac87a1624ca68`, archived exact Gmail body at `crypto-daily/reports/daily/2026/2026-11/2026-11-05.md` Git commit `b53341f7af9a434ed7dbceb3daab57e786911e0d`. Do NOT resend this date, and do not claim that production autonomy or full original-X coverage passed.

## 2026-11-06 second consecutive unattended publisher regression: prepare before deadline
Critical evidence: on both 2026-11-05 and 2026-11-06 the original scheduled 09:20 publication had NO complete pending body/QA. Nov6 `runs/2026-11-06/092000-final.md` says `QA_FAIL_PENDING_RECOVERY`; Nov6 `runs/2026-11-06/1020-recovery-source-gap.md` repeats pending/QA 404 and no email, despite the Nov5 `decideDailyRecovery` source change and expanded automation prompt. This proves that writing the recovery helper and instruction alone did not repair real scheduled delivery. No Gmail provider rejection occurred in these audit records.
Execution priority without adding schedules:
1. Existing **00:20/03:20/06:20** research rounds write compact factual source receipts and candidate decision, no email; avoid optional large Git writes.
2. Existing **08:20 PREBUILD** is a genuine production prerequisite: assemble the FULL report using 24h receipts, verify missing highest-materiality original issuer items, draft the complete 13 chapters and 7-day material novelty, save one `delivery-pending/YYYY-MM-DD.md` and independently check structure/source/semantic quality. Merely writing a `PARTIAL` audit that no pending exists is a failure, not a completed prebuild. Do not make cloud CI receipt a necessary prebuild dependency if the authorized independent degraded QA can satisfy the existing gate.
3. Existing **09:20 PUBLISH** checks Gmail Sent first; if no pending report is found, immediately **use accumulated research and source receipts to rebuild**. Do not stop at file read errors. Perform independent QA, confirm 13 headings, top five new facts, seven-day event dedup and critical security source receipts; send Gmail once when verified, read back Sent and actual body, Git archive. If genuine content QA cannot be completed, state failure truthfully rather than fake pass.
4. Existing **10:20 / 11:20 RECOVERY** repeat this *same full rebuild* rather than another pure status audit. Missing pending / Git CI must be classified as `PREBUILD_MISSING_RECONSTRUCT_NOW`; never `NO_WORK_TO_DO`. Dedupe by actual Sent before any send, and already mailed days are Git-archive-only.
5. No optional diagnostic Git writes, prior incident backfill, monthly research or cumulative X troubleshooting should displace a verified complete overdue daily. Retain previous calendar month's monthly delivery check after daily (October already Sent `1a1a496a0bdc257d`). Preserve original content integrity and all source gaps clearly. If runtime can't finish, record actual blocker and use only existing recovery slots.
Observed manual recovery Nov6: Gmail Sent `1a1aefe6426bda13` to original account; 13 numbered chapters; exact Gmail readback archived `reports/daily/2026/2026-11/2026-11-06.md` commit `9a55d7731c22d1c29e4e9517205b1ac39bf0f928`. Never resend 2026-11-06. This does not prove automatic recovery fixed.

## 2026-11-08 canonical after a manual recovery and superseded draft
Canonical recovery rule: a successfully Sent/readback 13-chapter edition must live at the standard path `reports/daily/YYYY/YYYY-MM/YYYY-MM-DD.md` with its Gmail Sent ID/subject, not just a `delivery-pending/` draft or a separate corrected sidecar. If an old incomplete draft survives in `delivery-pending/YYYY-MM-DD.md`, mark it `SUPERSEDED_NO_SEND` with pointer to the canonical report and Gmail ID, so no automated retry can treat it as a new deliverable. Maintain one current authoritative daily edition, historic prebuild/final and Gmail logs as audit evidence; monthly dedupe counts each calendar date once. When a corrected email actually supplants an earlier Sent daily, first preserve the original in versioned audit history and update canonical with the exact corrected Sent body. Do not send from the pending copy when Gmail Sent already exists.
Nov7 2026 recovery: canonical `reports/daily/2026/2026-11/2026-11-07.md` holds Gmail Sent `1a1b71334aeb0615` exactly and remains `CLOUD_CI_NOT_PROVEN`, SOURCE_PARTIAL. The 08:20 `delivery-pending/2026-11-07.md` was an incomplete prebuild (prior to MEXC FinCEN official review) and is not a competing final. The already-Sent user-facing report contains a minor stale wording/typographical anomaly `北京时间?` in §2; because exact Gmail/canonical equality is required, don't silently edit the canonical body or send a third unsolicited edition for a nonmaterial copy typo. Any actual material factual contradiction warrants a separately audited formal correction.

## 2026-11-08 production handoff correction: four missed consecutive primary deliveries
Confirmed four consecutive dates 2026-11-04, 05, 06, 07 with 09:20 autonomous Crypto official email missing; manual user-requested full recovery successfully mailed all four, including Nov7 Gmail `1a1b71334aeb0615`. On 2026-11-07 08:20 the only `delivery-pending/2026-11-07.md` was a 3,050-character incomplete/QA-unverified scaffold (only three Top5 items, core HYPE missing, regulator blank despite FinCEN MEXC order); 10:20/11:20 were still QA blocked; collecting until 20:20 did not repair the morning. The root failure includes work not finished in bounded scheduled invocations, not merely a missing script or optional Git file. A scheduled automation "completed" status does not prove report sent.
Strict recovery decision:
(1) At 00/03/06:20 do bounded primary-source receipts, clear stale/no-evidence candidates and write actual inputs by original research/final path.
(2) At 08:20 **allocate the entire slot to prebuild** a real source-backed 13-section complete candidate, 5 truly distinct highlights, prices, original safety/regulator sources, TGE/Early coverage truth, and seven-day prior Sent material versions. If incomplete, save `QA_BLOCKER` details; this is not successful prebuild.
(3) At 09:20 check **actual Sent today first**, then use prebuild. If incomplete, reconstruct using prior 24h receipts before doing optional report-pipeline housekeeping. Do not merely record 404/QA_FAIL; attempt substantive recovery and send only if independent content gate passes.
(4) At 10/11:20 repeat full reconstruction from receipts if missing, otherwise archive-only from readback. Never invent test/CI pass or send an unverified daily. If the window's execution capacity is insufficient, persist blocked status and use next existing window; no new timer.
(5) First-of-month monthly delivery and missing previous-month catchup still required, but *after today's normal official daily*. No extra automations.
(6) Seven-day memory must read full delivered bodies or matching canonical Git history, not merely Sent subject headers; historical pending drafts and failed audit artifacts do not count as content delivered.
Nov7 Gmail readback `1a1b71334aeb0615`, Git canonical `crypto-daily/reports/daily/2026/2026-11/2026-11-07.md` commit `b30aba180be509a6387fb36f2dceec2786822a9f`. Nov4/5/6 and October monthly already sent; never resend these dates. Nov8 cross-date errata separately Sent `1a1b71acb668ad89`, archived `crypto-daily/reports/corrections/2026/2026-11/2026-11-08-two-week-errata.md`. Actual scheduled production recovery after this fix is still UNVERIFIED.

## 2026-11-09 P0 fifth unattended delivery failure, real Nov8/9 manual recovery
On Nov8 and Nov9, the original 09:20 normal daily still did not send. Nov8 `runs/2026-11-08/112234-final.md` states QA_FAIL_DELIVERY_PENDING; Nov9 `runs/2026-11-09/112255-final.md` states QA_FAIL_NO_SEND. Earlier Nov4–7 suffered identical failure, despite prior prompt/source fixes. **Fix type implemented today**: `COLLECTOR_SPEC.md` staged draft fragments across original 20:20 previous day + 00/03/06/08:20 windows; current `state/daily-event-ledger.json` updated to include materially versioned Nov4–9 official Sent history; no scheduler alteration or backup cron.
Verified manual recovery for Nov8: Gmail Sent `1a1bf42ad0c5d3c8`, full 13 sections, canonical `reports/daily/2026/2026-11/2026-11-08.md` commit `26f26e06fa89550ac620ccb65c9d73723feb4ae6`. Material previously missed: Binance CFO Kaiser Ng→Justin Yek (Reuters published Nov7 17:32 UTC), Nubank/Mercado Pago third-party crypto transfer interruptions (Reuters Nov6), Riyadh/Aramco office attack (Reuters Nov8), exact Binance Nov8 24 hourly candle history. Historical as-of data is explicitly differentiated from later coverage. Nov9: Gmail Sent `1a1bf46e14b36b3e`, canonical `reports/daily/2026/2026-11/2026-11-09.md` commit `196ab5418007078cd782c268bef1085e0de242ee`. Includes Binance original spot/perp as of 2026-11-09 14:38 BKK, Reuters crypto lows, AP Asian equity rebound, Riyadh next alert and last completed Nov6 Farside ETF issuer flows. Both actual Gmail bodies read back and archived verbatim, no premature CI_PASS. The unapproved Nov9 08:20 `delivery-pending/2026-11-09.md` was superseded with `SUPERSEDED_DELIVERED_DO_NOT_SEND` commit `af8fbeaddded1f2f7543bd61f5af49964a97461d`.
**Next genuinely autonomous primary Gmail delivery must be revalidated at its next real scheduled slot** before calling production fixed. Do not repeatedly send Nov8/9 or the already-resent Nov4–7. Current critical gaps remain NFT/ICO first-party discovery and original TGE X/wallet eligibility, and CI_NOT_PROVEN.


## 2026-11-14 P0: eliminate 08:20 missing prebuild and Binance HTTP 451 as recurring hard block

Observed primary evidence: the original **2026-11-14 09:20** `runs/2026-11-14/092359-final.md` records `QA_FAIL_NO_SEND`; **11:20** `runs/2026-11-14/1116-recovery-source-gap.md` again records `QA_FAIL_NO_SEND`. Both waited for `delivery-pending/2026-11-14.json` (404), and a raw Binance website/API request returned HTTP 451. The original 08:20 research handoff was explicitly `NOT_A_COMPLETE_13_SECTION_PREBUILD`. No live Sent existed at check time, despite automation executions marked `completed`. Merely updating a prompt has failed on other days and is NOT unattended acceptance.

**In-place existing single task, exact authorized :20 windows; no new task, scheduler or external runner:**

1. The 00:20/03:20/06:20 collectors must incrementally assemble source receipts and substantive report blocks, while leaving source failures explicit. Their research is not automatically a ready final.
2. **08:20 is a compulsory draft-production slot**, not just another research handoff. Consume existing evidence; fetch official market prices. The raw `api.binance.com` URL HTTP 451 is a provider access limitation, **not proof Binance market data is unavailable**. Prefer the existing connected official Binance market-data tools `get_spot_24hr_ticker_price_change_statistics({symbol})`, `get_futures_usds_open_interest({symbol})`, `get_futures_usds_funding_rate_history({symbol})`, subject to actually available connector actions. One-symbol requests are valid when multi-symbol request fails. Each API reading must carry exchange `closeTime`, requested symbol, 24h range, volume, and result status. If the connector is not available in the automation runtime, attempt public original Binance English quote/market page and verify timestamps; if those too are inaccessible, record `SOURCE_GAP`, do not invent quotes. **Persist a complete 13-heading provisional body and a compact structured source/dedupe manifest** at an existing `delivery-pending/YYYY-MM-DD.md` path. Reuse the same day rather than scattering unconnected drafts.
3. **09:20 must deliver a verified full 13-section report, not spend the entire slot rechecking a 404 pending file.** If pending is missing/failed, reconstruct from the last 24h existing research and current official market tools *within the same scheduled invocation*. Use Farside original BTC/ETH/SOL tables only for the last complete issuer rows; if some issuer rows are blank, label latest finalized previous trading day rather than claiming 0. Dedupe against latest **actual SENT** full bodies and family/version ledger; source-gapped sections are marked internally and kept neutral in the formal report rather than padded with old claims. Evaluate genuine high-impact security and local Thai SEC/other relevant policy source leads. The user-facing body must be the normal complete report, not process-only QA details or short error summary.
4. **10:20/11:20 recover the actual missing delivery, not repeat its earlier 404 blocker.** Read back any completed blocks, perform a bounded new primary-source check; if 08:20 stage never occurred, build the full report in the recovery window. An early raw API 451 or optional Git prewrite failure alone never excuses a capable but skipped alternative route. Preserve hard fact gates: if key prices, securities/rights terms or important safety claims cannot be independently verified by any original fallback, stay `QA_FAIL_NO_SEND` and record exactly why. Manual structural/source evaluation is `CODE_NOT_EXECUTED; MANUAL_EQUIVALENT_ONLY`, not fabricated CI_PASS.
5. Do one actual Gmail Sent prefix search before send; no duplicate. Send only to existing life account; read back `SENT`, recipient, **entire body**, then create/update exactly one canonical Git daily path from that readback and verify byte equality. If Git fails after Gmail Sent, `SENT_ARCHIVE_PENDING` and repair Git only. If Gmail fails, `NOT_DELIVERED` regardless of task `completed`.
6. At each real scheduled source/prebuild/publisher iteration record `stage_entered`, `data_source_fallback_attempted`, `draft_exists`, `qa_status`, `sent_id`, `exact_git_mail_equal`, or true unavailable reason. Silence all ordinary task output. Do not infer unattended success from a one-time manual email.

**November 14 recovery proof and limits:** authorized direct user-demand manual complete resend `Crypto Daily Brief｜2026-11-14` Gmail `1a1d8a65a1935ab7`, recipient `lxx.run688@gmail.com`, 13 sections, 6,764 characters; canonical `crypto-daily/reports/daily/2026/2026-11/2026-11-14.md`, commit `17871b07a5df3acf0f869374cdc11ff46553bfc3`; exact full readback confirmed Git blob `56dddbe53c6073e2e761a7f697c27d2757f7d9cb`. This was manual recovery **after** original scheduled failure, not proof that tomorrow's 09:20 unattended publication works. Market source is **connected official Binance** 2026-11-14 12:58:52 ICT, with Farside Nov13 revised BTC/ETH/SOL ETF and Thai SEC Nov12 draft. Editorial gate code was not executed and source coverage remains partial. Nov13 manual recovery Sent `1a1d785982ccbed1` is authoritative already and Telegram RCE research must not be recycled absent a new event version. Subsequent scheduled collectors should not send extra user-facing emails for this date.
