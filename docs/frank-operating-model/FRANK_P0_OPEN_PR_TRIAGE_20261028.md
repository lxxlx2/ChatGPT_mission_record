# Frank P0 open Draft PR 冻结打标清单（2026-10-28）
**状态：DRAFT_RESEARCH_INDEX / NO_PR_CLOSED。** 快照由 GitHub REST `GET /pulls?state=open&per_page=100&page=1..3` 取得，采样时间为 2026-10-28 Asia/Bangkok。按 PR 的标题或 head 分支含 `frank`（忽略大小写）筛选；这是**可重现但非严格完备**的 Frank 模块候选定义，不能把未命中的 PR 推断为无依赖。

- 快照：全仓 OPEN PR **199**，全为 Draft；候选 Frank PR **103**（以前提案的 101 为旧时点数字），此快照包括 PR #241，**尚不包括新建 P0 PR**。
- 分类计数：**继续 10 / 冻结 85 / 待清理候选 8**；分类仅写入本清单，**并非调用 GitHub API 为每一条 PR 添加 label**，不改变任何旧 PR 状态、base、review 或评论。
- **继续 ≠ 允许合并/部署**；只是 P0/P1 的优先研究/冻结证据入口。**冻结 ≠ 过时或可删**，可能包含栈式父 PR、安全边界与未合并的源码。**待清理 ≠ 允许关闭**；仅说明标题显示有噪音嫌疑，须由 Codex 按 source/base/HEAD/依赖/安全/审查回执逐条复核，用户另外明确授权才可关闭。
- 优先级：P1 用 PR #117/#235/#238/#239 证据，以 7 天预算给 INVEST_GO/INVEST_NO_GO；旧产品开发与 F1–F3 复核冻结，但所有 S 类生产安全检查继续生效。不要把清理 103 条 PR 作为 P1 前置工作。
- 关键承接依赖：#232 的 base 包含 #220，#220 的 base 为 #205 相关栈，且 #239→#238→#235→#117 形成研究栈。因此冻结列表**不能**直接被批量关闭；如保留 #232/#239，必须尊重其父栈。此清单不展开跨链依赖代码审计。

| PR | 分类 | 标题 | 目标基分支 | 依据 / 限制 |
|---|---|---|---|---|
| [#241](https://github.com/lxxlx2/ChatGPT_mission_record/pull/241) | 继续 | docs(frank): Operating Model V1 — north-star question, one STATUS file, budgets, and forced answers on budget expiry | `main` | 运营模型已批准；待安全合并裁决 |
| [#240](https://github.com/lxxlx2/ChatGPT_mission_record/pull/240) | 继续 | docs(frank G4): preregister bounded ACC/MULT forward quoteability study protocol | `research/frank-g4-price-one-shot-20261028` | 前向报价协议，仅文档；待独立复核，不得开采 |
| [#239](https://github.com/lxxlx2/ChatGPT_mission_record/pull/239) | 继续 | research(frank G4): one-shot limited true-MULT and early-exit historical OHLCV probe | `research/frank-g4-acc-mult-causal-crosswalk-20261028` | 历史 G4 因果修复已研究批准，EXECUTE=NO |
| [#238](https://github.com/lxxlx2/ChatGPT_mission_record/pull/238) | 继续 | research(frank G4): ACC vs MULT exact causal signal clocks and root exit-horizon crosswalk | `research/frank-g0b-once-20261028` | ACC/MULT 因果时钟证据 |
| [#235](https://github.com/lxxlx2/ChatGPT_mission_record/pull/235) | 继续 | research(frank G0-B): real 36-GET free historical price feasibility — DATA_NOT_SCORABLE | `codex/frank-g0a-inventory-20261019` | 原 G0-B 历史价格试验，严格因果失效为0/30 |
| [#232](https://github.com/lxxlx2/ChatGPT_mission_record/pull/232) | 继续 | feat(frank F01): amount-free recent source observations and separate history, read-only | `feature/frank-p1a-ca-job-report-identity-20261026` | F01 来源只读展示，P1 决策前不发布 |
| [#226](https://github.com/lxxlx2/ChatGPT_mission_record/pull/226) | 冻结 | Frank F3: bind F2 to fresh readonly Mac runtime evidence | `codex/frank-f2-one-shot-mac-20261027` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#222](https://github.com/lxxlx2/ChatGPT_mission_record/pull/222) | 冻结 | Frank F2: Mac-validated one-shot adapter and recovery guards | `feature/frank-p1a-ca-job-report-identity-20261026` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#220](https://github.com/lxxlx2/ChatGPT_mission_record/pull/220) | 冻结 | Frank P1-A: bind completed CA report to real job ID and reject mismatched latest | `feature/frank-p1a-c1-job-rpc-budget-20261025` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#218](https://github.com/lxxlx2/ChatGPT_mission_record/pull/218) | 冻结 | Frank F1d: offline bounded bootstrap output observation and incomplete-evidence stop gate | `feature/frank-c2a-f1c-offline-release-supervisor-20261026` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#215](https://github.com/lxxlx2/ChatGPT_mission_record/pull/215) | 冻结 | Frank F1c: offline-only Dashboard release G0–G4 supervisor and protected rollback matrix | `feature/frank-c2a-f1b-offline-emergency-rollback-20261026` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#214](https://github.com/lxxlx2/ChatGPT_mission_record/pull/214) | 冻结 | Frank C2A F1b: synthetic independent recovery even if bootstrap evidence capture fails | `feature/frank-c2a-f1-offline-bootstrap-evidence-20261026` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#212](https://github.com/lxxlx2/ChatGPT_mission_record/pull/212) | 冻结 | Frank C2A F1: synthetic bootstrap failure evidence before mock rollback (OFFLINE ONLY) | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#210](https://github.com/lxxlx2/ChatGPT_mission_record/pull/210) | 待清理(仅候选) | docs(frank): C2A rollback bootstrap failure read-only evidence gate (PLAN_ONLY) | `main` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#208](https://github.com/lxxlx2/ChatGPT_mission_record/pull/208) | 待清理(仅候选) | docs(frank): C2 Dashboard-only rollout and one-Quick CA acceptance gate (PLAN_ONLY) | `main` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#205](https://github.com/lxxlx2/ChatGPT_mission_record/pull/205) | 冻结 | Frank P1-A C1: job-level RPC attempt/time failstop (CODE ONLY) | `research/frank-p1a-c1-installed-baseline-20261025` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#203](https://github.com/lxxlx2/ChatGPT_mission_record/pull/203) | 冻结 | docs(frank): P1-A CA real-flow diagnostic and hard RPC budget gate (PLAN_ONLY) | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#200](https://github.com/lxxlx2/ChatGPT_mission_record/pull/200) | 待清理(仅候选) | docs(frank): Oct25 verified D2 private source promotion gate (PLAN_ONLY) | `main` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#195](https://github.com/lxxlx2/ChatGPT_mission_record/pull/195) | 冻结 | Frank P1-B: stop after first failed owner RPC receipt (research only) | `fix/frank-a05-rpc-transport-integrity-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#178](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178) | 冻结 | feat(frank D2): opt-in private full-owner at-slot read-only Dashboard ingress | `feature/frank-d2-owner-at-slot-preview-20261023` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#174](https://github.com/lxxlx2/ChatGPT_mission_record/pull/174) | 冻结 | feat(frank D2): pinned full-owner source → private at-slot offline balance preview | `feature/frank-ca-get-resume-20261023` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#168](https://github.com/lxxlx2/ChatGPT_mission_record/pull/168) | 冻结 | fix(frank-ca): recover interrupted GET polling without repeating chain scans | `feature/frank-option3-activity-feed-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#166](https://github.com/lxxlx2/ChatGPT_mission_record/pull/166) | 冻结 | docs(frank): reconcile V3 redesign with frozen G1 and original V2/CA/mainline rules | `research/frank-v2-d1-mainline-20261019` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#164](https://github.com/lxxlx2/ChatGPT_mission_record/pull/164) | 冻结 | feat(frank): reversible expired-review banner acknowledgement (no outbox changes) | `feature/frank-option3-activity-feed-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#157](https://github.com/lxxlx2/ChatGPT_mission_record/pull/157) | 冻结 | feat(frank): source-backed wallet activity risk panel independent of current candidate signals | `feature/frank-amount-free-intelligence-p1p2-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#146](https://github.com/lxxlx2/ChatGPT_mission_record/pull/146) | 冻结 | feat(frank): source-grounded amount-free intelligence P1 inventory and P2 offline prototype | `release/frank-no-default-amount-policy-review-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#142](https://github.com/lxxlx2/ChatGPT_mission_record/pull/142) | 冻结 | docs(frank): Option 3 signal-preserving amount-free intelligence and risk-alert roadmap | `fix/frank-mc-loop-stop-readback-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#139](https://github.com/lxxlx2/ChatGPT_mission_record/pull/139) | 冻结 | fix(frank): verify MC Loop launchd and PID exit after safe-stop | `integration/frank-policy-handover-signed-approval-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#138](https://github.com/lxxlx2/ChatGPT_mission_record/pull/138) | 冻结 | feat(frank): jointly enforce source policy and signed user approval at notification delivery | `integration/frank-no-fixed-amount-g2-d1-d2-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#134](https://github.com/lxxlx2/ChatGPT_mission_record/pull/134) | 冻结 | fix(frank): require signed human policy approval and add MC-loop-only safe stop | `integration/frank-no-fixed-amount-g2-d1-d2-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#132](https://github.com/lxxlx2/ChatGPT_mission_record/pull/132) | 冻结 | fix(frank): quarantine cross-policy pending decision notifications at live resume | `integration/frank-no-fixed-amount-g2-d1-d2-20261020` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#128](https://github.com/lxxlx2/ChatGPT_mission_record/pull/128) | 冻结 | feat(frank): integrate user-controlled execution and G2 D1/D2 dashboard | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#126](https://github.com/lxxlx2/ChatGPT_mission_record/pull/126) | 待清理(仅候选) | docs(frank): PR112 live-policy authorization and Mac cutover preparation | `main` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#123](https://github.com/lxxlx2/ChatGPT_mission_record/pull/123) | 冻结 | docs: FRANK G2 D1/D2 Mac readonly acceptance evidence (no code) | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#119](https://github.com/lxxlx2/ChatGPT_mission_record/pull/119) | 冻结 | feat(frank G2): integrate D1 signed activity and dated D2 holdings into local Dashboard | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#117](https://github.com/lxxlx2/ChatGPT_mission_record/pull/117) | 继续 | research(frank): G0-A exploratory local inventory (no RPC, no strategy verdict) | `main` | G0-A 冻结样本，P1 直接利用 |
| [#115](https://github.com/lxxlx2/ChatGPT_mission_record/pull/115) | 冻结 | research(frank): D integration dependency map and source-to-notification timing audit | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#114](https://github.com/lxxlx2/ChatGPT_mission_record/pull/114) | 继续 | docs(frank): FROZEN user-approved G1 five-layer architecture contract | `main` | 已冻结 G1 架构基线 |
| [#112](https://github.com/lxxlx2/ChatGPT_mission_record/pull/112) | 继续 | fix(frank): remove unauthorized fixed $30 order assumption from policy, code, CA and UI | `main` | 删除未经授权默认金额的重要安全约束 |
| [#111](https://github.com/lxxlx2/ChatGPT_mission_record/pull/111) | 继续 | feat(frank D1): read-only signed activity ledger with corrected ATA scope facts | `main` | D1 来源签名活动基础 |
| [#110](https://github.com/lxxlx2/ChatGPT_mission_record/pull/110) | 冻结 | feat(frank D2): dated 32-mint verified inventory overlay in searchable local watchlist preview | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#109](https://github.com/lxxlx2/ChatGPT_mission_record/pull/109) | 冻结 | feat(frank D1): restore business-first V2 mainline and trace two indexed BUYs to source decisions | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#108](https://github.com/lxxlx2/ChatGPT_mission_record/pull/108) | 冻结 | ops(frank): aggregate-only real Mac local runtime, index coverage and F01 exclusion evidence | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#107](https://github.com/lxxlx2/ChatGPT_mission_record/pull/107) | 待清理(仅候选) | qa(frank): automatic real Mac Safari 503 fault-and-recovery screenshots for approved PR106 | `fix/frank-decisions-partial-refresh-20261019` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#106](https://github.com/lxxlx2/ChatGPT_mission_record/pull/106) | 冻结 | fix(frank): keep live dashboard usable if historical decisions GET returns 503 | `ops/frank-decisions-503-readonly-diagnostic-20261019` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#105](https://github.com/lxxlx2/ChatGPT_mission_record/pull/105) | 冻结 | diagnostic(frank): isolate /api/decisions 503 source versus preview GET proxy | `feat/frank-c02-local-archive-discovery-20261019` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#104](https://github.com/lxxlx2/ChatGPT_mission_record/pull/104) | 冻结 | fix(frank C02): auto-discover real saved report catalog before recent candidate mints | `feat/frank-c02-autocapture-zero-touch-20261018` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#103](https://github.com/lxxlx2/ChatGPT_mission_record/pull/103) | 冻结 | feat(frank): zero-touch Mac Safari C02 capture, automatic CA lookup and ZIP/Finder evidence | `ops/frank-pr101-safari-evidence-and-c02-archive-20261018` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#102](https://github.com/lxxlx2/ChatGPT_mission_record/pull/102) | 冻结 | ops(frank): Mac Safari evidence ZIP+Finder workflow and C02 cached CA read-only view | `feat/frank-f01-current-candidates-history-20261018` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#101](https://github.com/lxxlx2/ChatGPT_mission_record/pull/101) | 冻结 | feat(frank F01): show current opportunities separately from historical decisions | `fix/frank-pr93-executable-quote-binding-p2-20261018` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#96](https://github.com/lxxlx2/ChatGPT_mission_record/pull/96) | 待清理(仅候选) | qa(frank): isolated PR94 Mac/WebKit synthetic acceptance harness, fixed tree | `fix/frank-pr93-executable-quote-binding-p2-20261018` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#95](https://github.com/lxxlx2/ChatGPT_mission_record/pull/95) | 待清理(仅候选) | qa(frank): verify approved PR94 in real WebKit against native synthetic localhost Dashboard | `fix/frank-pr93-executable-quote-binding-p2-20261018` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#94](https://github.com/lxxlx2/ChatGPT_mission_record/pull/94) | 冻结 | fix(frank): pin executable $30 quote, impact and observation time across F01 snapshots | `fix/frank-pr92-mixed-f01-route-p1-20261017` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#93](https://github.com/lxxlx2/ChatGPT_mission_record/pull/93) | 冻结 | fix(frank): fail closed mixed BUY/WAIT candidates and restore actual F01 read-only route | `fix/frank-pr91-safe-primary-f01-and-gateway-20261017` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#92](https://github.com/lxxlx2/ChatGPT_mission_record/pull/92) | 冻结 | fix(frank): prevent recursive self-port gateway and expire stale primary BUY cards | `feat/frank-f01-source-context-pane-20261017` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#91](https://github.com/lxxlx2/ChatGPT_mission_record/pull/91) | 冻结 | feat(frank): mount A05 evidence and short-lived F01 source status in the formal Signals tab | `fix/frank-pr89-cross-source-review-p2-20261017` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#90](https://github.com/lxxlx2/ChatGPT_mission_record/pull/90) | 冻结 | fix(frank): preserve F01 vs archived A05 contradiction review indicator | `dev/frank-current-follow-context-a05-f02-20261017` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#89](https://github.com/lxxlx2/ChatGPT_mission_record/pull/89) | 冻结 | feat(frank): one-call current F01 opportunities with read-only A05 wallet context | `fix/frank-pr72-ignored-files-external-manifest-pin-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#88](https://github.com/lxxlx2/ChatGPT_mission_record/pull/88) | 冻结 | fix(frank QA): close PR87 startup leak, symlink escape, and failed-capture console loss | `qa/frank-pr85-approved-mac-safari-localhost-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#86](https://github.com/lxxlx2/ChatGPT_mission_record/pull/86) | 待清理(仅候选) | docs(frank): require one-command expanded full-page screenshot ZIP for Mac UI acceptance | `codex/frank-f02-refresh-progress-20261015` | 看标题疑似旧 UI/QA/发布文档；依赖和S类尚未复核，严禁自动关闭 |
| [#85](https://github.com/lxxlx2/ChatGPT_mission_record/pull/85) | 冻结 | test(frank): immutable PR83+PR84+F02 ephemeral triple-source combined Git and HTTP acceptance | `fix/frank-pr72-ignored-files-external-manifest-pin-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#84](https://github.com/lxxlx2/ChatGPT_mission_record/pull/84) | 冻结 | fix(Frank C02): distinguish absent RPC authority from explicit null in native verdict | `fix/frank-c02-pr80-backend-verdict-qa-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#83](https://github.com/lxxlx2/ChatGPT_mission_record/pull/83) | 冻结 | fix(Frank F01): align Decimal eligibility with browser Number and keep tiny prices nonzero | `fix/frank-f01-pr79-card-qa-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#82](https://github.com/lxxlx2/ChatGPT_mission_record/pull/82) | 冻结 | fix(C02): fail closed in native analyzer for uninitialized mint and redact unsafe provenance | `fix/frank-c02-pr78-verified-mint-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#81](https://github.com/lxxlx2/ChatGPT_mission_record/pull/81) | 冻结 | fix(F01): neutral invalid-quote BUY card and strict quote/DOM regression | `fix/frank-pr77-price-projection-slot-review-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#80](https://github.com/lxxlx2/ChatGPT_mission_record/pull/80) | 冻结 | fix(Frank C02): verified initialized mint safety proof and public audit redaction | `fix/frank-c02-unknown-risk-rpc-evidence-card-safari-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#79](https://github.com/lxxlx2/ChatGPT_mission_record/pull/79) | 冻结 | fix(Frank F01): reconcile decision quote with metrics and hide source slot | `fix/frank-f01-sold-excluded-badge-safari-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#78](https://github.com/lxxlx2/ChatGPT_mission_record/pull/78) | 冻结 | fix(Frank C02): Safari unknown permissions and phantom RPC counts; collapse source trace | `fix/frank-ca-c02-identity-preview-casefold-review-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#77](https://github.com/lxxlx2/ChatGPT_mission_record/pull/77) | 冻结 | fix(Frank F01): Safari SELL exclusion label and missing executable quote fail-closed | `dev/frank-ca-f01-actionable-view-20261013` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#76](https://github.com/lxxlx2/ChatGPT_mission_record/pull/76) | 冻结 | [Frank PR75 P2] Eliminate Git status/clean-filter execution from passive Mac preflight | `fix/frank-pr74-fsmonitor-home-isolation-20261016` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#75](https://github.com/lxxlx2/ChatGPT_mission_record/pull/75) | 冻结 | [Frank PR74 P2/P3] Disable Git fsmonitor helper in passive preflight and isolate test home | `dev/frank-mac-readonly-environment-preflight-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#74](https://github.com/lxxlx2/ChatGPT_mission_record/pull/74) | 冻结 | [Frank] Authorized Mac passive Git, historical-session existence and port preflight (no service) | `fix/frank-pr72-ignored-files-external-manifest-pin-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#73](https://github.com/lxxlx2/ChatGPT_mission_record/pull/73) | 冻结 | [Frank PR72 P1/P2] Preserve ignored research data and enforce external SHA256 provenance | `dev/frank-f01-c02-f02-pinned-isolated-workspace-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#71](https://github.com/lxxlx2/ChatGPT_mission_record/pull/71) | 冻结 | [Frank PR70 P2] Fail closed on truncated HTTP and incomplete F01 eligible source | `dev/frank-f01-c02-f02-http-readonly-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#70](https://github.com/lxxlx2/ChatGPT_mission_record/pull/70) | 冻结 | [Frank F01/C02/F02] Read-only localhost exact CA GET bridge over existing native APIs | `dev/frank-f01-c02-f02-joined-evidence-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#69](https://github.com/lxxlx2/ChatGPT_mission_record/pull/69) | 冻结 | [Frank F01/C02/F02] Exact-CA joint read-only source alignment and real synthetic-service integration | `dev/frank-f02-r3-offline-session-attestation-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#68](https://github.com/lxxlx2/ChatGPT_mission_record/pull/68) | 冻结 | [Frank F02-R3] Offline original-wire/Sidecar 32 Mint privacy-safe independent readback | `codex/frank-f02-manual-source-refresh-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#67](https://github.com/lxxlx2/ChatGPT_mission_record/pull/67) | 冻结 | docs(Frank): F02 手动新来源进度、证据与固定 SHA 审核输入 | `design/frank-ca-multiperson-completion-plan-20261013` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#66](https://github.com/lxxlx2/ChatGPT_mission_record/pull/66) | 冻结 | Frank F02: 手动核验新来源并打开隔离研究会话 | `fix/frank-f02-r2-ttl-live-expiry-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#65](https://github.com/lxxlx2/ChatGPT_mission_record/pull/65) | 冻结 | [Frank F02-R2] Expire cached open-page balances at TTL without new RPC | `dev/frank-f02-r2-isolated-browser-20261015` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#64](https://github.com/lxxlx2/ChatGPT_mission_record/pull/64) | 冻结 | [Frank F02-R2] Isolated localhost research holdings browser with verified-source masking | `fix/frank-f02-later-partial-lower-slot-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#63](https://github.com/lxxlx2/ChatGPT_mission_record/pull/63) | 冻结 | [Frank F02-R1] Block stale positions after later partial RPC attempt even at lower slot | `dev/frank-f02-r1-isolated-readonly-position-api-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#62](https://github.com/lxxlx2/ChatGPT_mission_record/pull/62) | 冻结 | [Frank F02-R1] Isolated source-pinned read-only positions HTTP API with stale masking | `dev/frank-a05-r2-frozen32-offline-reconciliation-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#61](https://github.com/lxxlx2/ChatGPT_mission_record/pull/61) | 冻结 | [Frank A05-R2] Offline reconcile complete owner RPC source against frozen historical 32 Mints | `fix/frank-a05-rpc-transport-integrity-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#60](https://github.com/lxxlx2/ChatGPT_mission_record/pull/60) | 冻结 | [Frank A05-R1 review P2] Fail closed on RPC HTTPS redirects and incomplete HTTP bodies | `dev/frank-a05-complete-owner-rpc-evidence-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#59](https://github.com/lxxlx2/ChatGPT_mission_record/pull/59) | 冻结 | [Frank A05-R1] Full Solana owner RPC wire receipts and offline source verification | `fix/frank-a05-f02-slotless-program-provenance-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#58](https://github.com/lxxlx2/ChatGPT_mission_record/pull/58) | 冻结 | [Frank A05/F02 Claude P2] Validate SPL + Token-2022 provenance of slotless failures | `fix/frank-a05-f02-full-slot-source-order-review-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#57](https://github.com/lxxlx2/ChatGPT_mission_record/pull/57) | 冻结 | [Frank A05/F02 Claude P2] Full-slot capture selection and safe no-slot RPC recovery | `dev/frank-a05-f02-latest-inventory-evidence-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#56](https://github.com/lxxlx2/ChatGPT_mission_record/pull/56) | 冻结 | [Frank A05/F02] Latest-owner-capture evidence inventory, no stale position resurrection | `fix/frank-ca-a04-versioned-generic-tx-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#54](https://github.com/lxxlx2/ChatGPT_mission_record/pull/54) | 冻结 | [Frank A04 Claude P2] Version generic immutable TX keys across V2 and V3 | `fix/frank-ca-a04-v3-immutable-view-upgrade-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#53](https://github.com/lxxlx2/ChatGPT_mission_record/pull/53) | 冻结 | [Frank A04 P2] Immutable normalizer V3 and genuine PR51/PR52 V2 Sidecar upgrade | `fix/frank-ca-a04-sol-native-gap-policy-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#52](https://github.com/lxxlx2/ChatGPT_mission_record/pull/52) | 冻结 | [Frank A04 Claude #4] Fee-only SOL truth, opt-in owner gap continuation and real ATA fixture | `fix/frank-ca-a04-claude-p2-p6-p4-coverage-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#51](https://github.com/lxxlx2/ChatGPT_mission_record/pull/51) | 冻结 | [Frank A04 Claude P2/P4/P6] Prevent silent missing owner, failed instructions and V2 replay gaps | `fix/frank-ca-a04-owner-gaps-source-replay-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#50](https://github.com/lxxlx2/ChatGPT_mission_record/pull/50) | 冻结 | [Frank A04 Claude review] Block false owner-less token deltas; replay immutable v2 views | `dev/frank-ca-a04-history-pagination-resume-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#49](https://github.com/lxxlx2/ChatGPT_mission_record/pull/49) | 冻结 | [Frank CA C02 review] Fix same-name mint preview ambiguity and case-only false conflicts | `codex/frank-ca-c02-token-identity-20261014` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#48](https://github.com/lxxlx2/ChatGPT_mission_record/pull/48) | 冻结 | [Frank A04] Crash-safe finalized Solana history pagination, source cursors and replay | `dev/frank-ca-a04-a05-readonly-chain-facts-20261013` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#47](https://github.com/lxxlx2/ChatGPT_mission_record/pull/47) | 冻结 | [Frank/CA C02] Exact-mint metadata identity and auditable source conflicts | `dev/frank-ca-c01-c08-unified-research-no-default-quote-20261013` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#46](https://github.com/lxxlx2/ChatGPT_mission_record/pull/46) | 冻结 | [Frank/CA C01+C08] One CA research entry and zero automatic $30 Jupiter quotes | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#45](https://github.com/lxxlx2/ChatGPT_mission_record/pull/45) | 冻结 | [Frank/CA A04-A05] Read-only dual-program wallet capture, economic evidence and sidecar | `dev/frank-ca-a03-research-wallet-facts-20261013` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#44](https://github.com/lxxlx2/ChatGPT_mission_record/pull/44) | 冻结 | [Frank/CA F01] Only current actionable follow opportunities; archive NO_BUY and stale decisions | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#43](https://github.com/lxxlx2/ChatGPT_mission_record/pull/43) | 冻结 | [Frank/CA A03] Read-only person-scoped wallet facts interface (stacked on PR #42) | `dev/frank-ca-registry-a00-a02-20261013` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#42](https://github.com/lxxlx2/ChatGPT_mission_record/pull/42) | 冻结 | [Frank/CA A00-A02] Research-only multi-person/multi-wallet registry and regression baseline | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |
| [#38](https://github.com/lxxlx2/ChatGPT_mission_record/pull/38) | 冻结 | [Frank Dashboard] Collapse long research watch pool and keep live follow opportunities prominent | `main` | 保留历史或潜在栈式依赖；未经复核不得关闭 |

**清理动作当前为 0。** 后续每批最多 10 条，先由独立 reviewer 验证真实依赖，用户授权后再做写入；如标题/分支变化需新快照，不得凭本旧快照推断可安全关闭。

## P0 第二轮：8 个“待清理候选”的真实依赖与文件范围核查（2026-10-29 01:48 Asia/Bangkok）

**结论：8/8 已完成最小只读分类复核；可**直接**关闭数 **0**。P0 文档分类工作到此结项，不展开新 C 类验收或新的清理工程。** 未关闭/合并/改 base/改 label 任何旧 PR；原有 10/85/8 分类是**2026-10-28 固定快照**，不把其“待清理”理解成“已判可删除”。

本次一手读取 8 个 PR 的 metadata、正文和 `GET /pulls/{id}/files` 真实文件清单；并将全仓所有 Open PR 的 `base.ref == 该 PR 的 head.ref` 作为**直接栈式子分支检查**，以及其他 Open PR 正文中 `#PR`／`pull/PR` 引用作为显式引用核查。这不等于完整 commit/文件级反向依赖审计：没有检测到直接子分支**不构成**“可以安全关闭”的正面证据。

| 候选 PR | 实际改动（不是标题推测） | 可追踪的直接依赖与风险 | P0 结果 |
|---|---|---|---|
| [#210](https://github.com/lxxlx2/ChatGPT_mission_record/pull/210) | 新增 1 份 C2A 发布失败取证文档 | 明确原 Dashboard `launchctl bootstrap` 失败根因 **UNRESOLVED**；该文档引用 #208 和 #205；服务恢复/回滚风险属于不可跳过的 S 类 | **保留冻结**；不能当普通过期文档关闭 |
| [#208](https://github.com/lxxlx2/ChatGPT_mission_record/pull/208) | 新增 1 份 Dashboard-only 发布与 Quick CA 许可文档 | **#210 的正文直接引用 #208**；涉及未来 Dashboard 8766 发布和单次 CA POST/RPC 授权 | **保留冻结**；有显式开放 PR 引用 |
| [#200](https://github.com/lxxlx2/ChatGPT_mission_record/pull/200) | 新增 1 份 D2 私有 source promotion 文档 | 描述私有 D2 文件更换、0600 备份、哈希及回滚；虽无直接子分支，也存在生产私有数据和服务安全约束 | **保留冻结**；不触碰 D2 数据 |
| [#126](https://github.com/lxxlx2/ChatGPT_mission_record/pull/126) | 新增 1 份 PR112 通知策略发布/迁移准备文档 | **#128 的正文直接引用 #126**；涉及撤销默认 $30、通知审批和不可用脚本的风险 | **保留冻结**；有显式开放 PR 引用 |
| [#107](https://github.com/lxxlx2/ChatGPT_mission_record/pull/107) | **新增 4 个代码/CI 文件**（Safari 503 QA 与工作流） | stacked base `fix/frank-decisions-partial-refresh-20261019`（#106）；原 503 故障与实际 Mac Safari 验收不可因标题写“QA”而视为已被替代 | **冻结保留**；不执行 Mac/QA |
| [#96](https://github.com/lxxlx2/ChatGPT_mission_record/pull/96) | **新增 4 个代码/CI 文件**（PR94 合成浏览器、Safari 辅助） | stacked base `fix/frank-pr93-executable-quote-binding-p2-20261018`（#94）；含可执行脚本，不是文档 PR；无证据证明所有源码/验证都已被后续结果取代 | **冻结保留** |
| [#95](https://github.com/lxxlx2/ChatGPT_mission_record/pull/95) | **改动 1 个 workflow + 新增 1 个测试脚本** | 同 #94 父栈，真实 Playwright WebKit ≠ Safari.app；保留现有历史 QA 证据，不重复运行 | **冻结保留** |
| [#86](https://github.com/lxxlx2/ChatGPT_mission_record/pull/86) | **改动 2 份审核/实施规则文档 + 新增 3 份运行手册** | stacked base `codex/frank-f02-refresh-progress-20261015`（#67）；实际包含审核规则修改，不是无影响的截图噪音 | **冻结保留**；未来如修改规则须按仓库正式规则审批 |

**实际依赖证据：** 这 8 个 PR 在查询时都是 OPEN/Draft；以它们作为 base.head 的**直接 Open 子 PR 为 0**，但公开 PR 正文存在 **#210→#208**、**#128→#126** 的显式引用。若有人以后建议关闭，必须新作最新 HEAD/base/代码重复性与生产安全检查并取得用户授权；**本次没有形成任何“可安全关闭”名单**。

**最新范围提示：** 2026-10-29 01:48 GitHub Open PR 已是 **201 个、全部 Draft**；按旧的“标题/分支包含 frank”字符串规则会匹配 **105 个**，其中新 [#243](https://github.com/lxxlx2/ChatGPT_mission_record/pull/243) 是 **Machine.fun 独立项目（标题仅写 Frank untouched）**，不得算入 Frank P0。排除该关键词误匹配后，Frank 语义候选为 **104 个**，比原固定 103 快照多 **#242** 本身。**不追溯改写原 199/103、10/85/8 归档快照**；数字随新 PR 创建而变化。Machine.fun 的新后台监控与 Frank 本轮 P0 无关，本轮绝不读取其生产资源、也不操作它。

**P0 本轮收尾：** 已完成 STATUS 入口、103 条固定快照分类、8 个清理候选的只读审查。没有额外盈利数据或可关闭 PR 的结论；P1 已于 2026-10-29 01:45 由用户批准提前 `INVEST_NO_GO` 结项。**不再以 P0 的名义扩展验收、增加子 PR 或等待 10 月 30 日才能算“完成”**。实际后续只保留已存在的钱包只读工具和严格的 S 类边界，任何代码发布/生产访问/PR 关闭仍需独立许可。
