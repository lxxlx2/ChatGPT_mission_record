# Monster ADR-005：Codex 第二轮 P1 过期漏评修复与再复核门禁（2026-10-25）

当前状态：**修复/独立源码验收待复审；不予部署**。所有源码与 CI/研究更新继续在唯一 Draft [PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，research/monster-v4-local-discovery-20261010。未接触Mac、Frank、真实邮件、交易、后台或排程。禁止NO_MERGE解除。

## 1. 来自其他 AI 的真实固定源码第二轮审核

- 用户提供的原始审查主体：**Codex 主代理，底层具体型号 UNVERIFIED**；真实环境用户Mac、Python 3.14.7。审查方实际下载GitHub Action 40176833545固定离线包，校验SHA/Tree/SQLite，两批研究前后同69 WATCH与47 SETUP一致，运行22+13+8+6+7=56项定向测试，结果 `REQUEST_CHANGES`。
- 被拒绝代码固定 SHA `3fd5cab30324acd75c4f6f00f86bc264abdf943c`（与本轮待复核代码严格区分），P1 反例：WATCH `3240000`、deadline `4140000`，仅在 `3600000` 评估一次阴性，最后评估5m open `3300000`；错过截止前的最新有效5m open `3600000`；该尚未检查的截止bar可能 `RESEARCH_SETUP`，但旧过期代码仅因 `last_reviewed_open_ms is not None` 把下一轮 `NO_SETUP`。真实误把可漏掉的候选计入阴性，污染G2/G3历史基线。
- 外部审核同时确认：已曝光的真实8条旧`LATE→NO_SETUP`修正均确实评估过截止前最新5m open；新D1 47研究SETUP全部行字段未变；G3数值明确失败，官方预发类型Manifest固定对账40普通Crypto、2Chiliz、2bStocks、3未知；但Manifest公告原文链接只部分能独立取回。全4599官方原始ZIP字节对外审仍BLOCKED（包内只含12份），不能混淆该项和源码部分的拒绝。

## 2. 源码精确修复范围

- `crypto-300-profit-mission/local-agent/scripts/monster_v4_d1_rbtc15_episode_research.py`：
  - 引入一套过期判定`_negative_fully_reviewed_through_deadline(row)`及`_expiry_status(row)`，`expected_final_open = (deadline_ms // 300000) * 300000 - 300000`（与闭合5m规则一致）。
  - 截止后服务、以及截止恰逢`SAME_BAR`/WAIT/SOURCE_CENSORED，统一遵循：已有明确source-censor → SOURCE_UNSCORED；无source-censor且最后审查bar **等于最后允许的闭合5m bar** → NO_SETUP；否则 → LATE_UNSCORED。只曾经检查过早期bar不足以证明NO_SETUP。绝不在逾期后评估新资料或补发SETUP。
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_adr005_real53_original_sqlite_replay.py`：
  - 只有旧参照`LATE_UNSCORED`转`NO_SETUP`且row具有截止值、最后bar值、精确达到deadline允许的最后bar、0 censor，才标`SEMANTIC_DEADLINE_REPAIR_MATCH`；如缺字段、时间落后或有censor，直接 `DIFFERENCE_FAIL_CLOSED`，不把错误修复假装53/53“完全MATCH”。
- 专项测试：
  - `test_monster_v4_d1_rbtc15_episode_research.py`新增 **三种目标行为**：真实反例旧负评(3300000)→遗漏有潜在正信号最后bar(3600000)→逾期仅LATE；已有来源删失则SOURCE优先；截止当刻确实有效评估了最后bar且阴性才NO_SETUP。原正常8条保留验收。
  - `test_monster_v4_adr005_real53_original_sqlite_replay.py`修正合成fixture包含实际截止时钟，增加早期stale负评拒绝的严格断言，不能仅凭任意非null lastbar批准旧`LATE→NO_SETUP`。

固定源码提交序列：`4446c6918ade08d592ff985edcb1f0675c069691` → `f984196d5d9309ef88da733829c75448ce1911e0` → `8504d72332fdd158118ad46a4961deaaf05a7e28` → `b957a282839cf14e80b251573d22518371ef7c27` → `1add0d9af9c2cd1a8794a5c51b31e70a1388ea32` → `632299480825e87d1e36a61f1f26c48ee8932da2`。新增一份**仅路径触发、无schedule**的只读真实源码回放入口提交 `787219809b92fe2c60538f95476a7277ffa07e78`；**给其他AI固定审查此最终代码提交 SHA**。个别中间提交测试失败因新合成fixture缺`deadline_ms`/缺`last_reviewed_open_ms`，已新增缺字段拒绝路径并修复；**必须只根据最终固定SHA实际通过CI作结论**。

## 3. 最终代码实际 CI 与真实来源回放证据

| 证据 | 结果 |
|---|---|
| 最终代码回归 [Actions #40190452211](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40190452211) @ `632299480825e87d1e36a61f1f26c48ee8932da2`（`787219`只新增workflow入口，不修改模型/测试） | 实际从日志读取14组 `13/6/7/11/19/12/12/14/18/25/13/17/9/31`，**207/207 PASS**，Python 3.11，非仅摘要 |
| 真正完整研究回放 [Actions #40190516624](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40190516624) @ `787219809b92fe2c60538f95476a7277ffa07e78` | **SUCCESS**：精确读回42个历史Actions官方来源分片，再按原Stage166校验69个币日来源，原69 WATCH/3360轮SQLite，重跑同一份研究core |
| 真正研究输出 [Artifact `12596924379`](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40190516624) | 69 WATCH, 47 RESEARCH_SETUP, 18 NO_SETUP, 4 SOURCE_UNSCORED, 0 LATE_UNSCORED；已过最后closed bar覆盖检查（旧53更正6个） |
| 原对照Artifact `12592860133`（首次P1更正） | 69 WATCH/47 SETUP/18 NO_SETUP/4 SOURCE/0 LATE；需要独立核对事件ID、末bar时间，不可用计数一致代替全行复审 |

**未跨越的边界**：53条旧比对仍是暴露历史、无非SETUP完整终止时钟来源；原59条旧D1核心SETUP与47条新D1独立研究不可混同；固定511币是T0观察名单而非动态全市场上市资格；2026-10-16至24发行方历史原始档案的事后下载不能证明当时`available_at`；旧42个源Artifact只有原数据链归档，不等于Claude/Codex实际独立读取4599个源字节。

## 4. 下一次独立复审明确要求

新独立复审只针对 `3fd5cab30324acd75c4f6f00f86bc264abdf943c → 787219809b92fe2c60538f95476a7277ffa07e78` 的截止时间语义改动及其测试/真实回放；必须由另一个AI在**固定 SHA detached只读**环境亲自读取差异，不准用之前的`REQUEST_CHANGES`代替当前结果，也不能将本会话内部复核宣称外部APPROVE。

重点：
1. 逐条检查最后允许的5m bar计算、严格小于deadline已闭合、UTC5m与3m刻度（恰好5m边界和非5m边界）、期限外不计算正信号、SOURCE优先、旧8条最后bar精确覆盖；
2. 独立重演审查方提出的 `3240000/3600000/4140000` 反例，要求输出`LATE_UNSCORED`且**无SETUP**，截止同一bar已评估且负例才NO_SETUP，漏掉更新bar不能当阴性；
3. 确认`compare_exposed_exploration`的容许语义修复仅精确覆盖行并且拒绝缺字段/其他非状态漂移；
4. 独立读取新Artifact `12596924379`，复核真实69事件SHA、53历史身份、47 SETUP全部event+payload逐字段一致，8次旧更正每个对应最新bar、source-censored组不变。材料不可获取时逐项写BLOCKED，勿伪造全4599源复验；
5. 验证原ADR005预注册未来独立三段时窗不受影响，G0 PARTIAL / G1 NOT_SCORABLE / G2 UNKNOWN / G3 10月研究数值已失败 / G4 UNKNOWN / G5 本SHA新审查待完成 / G6 NO_GO。

**输出**：`APPROVE | REQUEST_CHANGES | BLOCKED`，精确审核SHA、审查模型和环境、P0/P1/P2文件行号/实际复现、源码行为和真实数据范围差异；结束时仍保持 `NO_MERGE/NO_DEPLOY/NO_MAC/NO_AUTOMATIONS/NO_GMAIL/NO_TRADES`。

**诚实的剩余方法限制**：最后bar覆盖是这轮审查方提出的**必要**否定条件；它自身未构成全窗口每一根闭合5m bar都逐条已评估的完整充分证明。若在更长的服务中断里中间bar被跳过、但最后bar恰被服务，仍可能存在未观察的机会；独立复审应评估这是否需要另设单独的数据可观测性门禁（不擅自调策略阈值）。本轮只修复已复现的截止前最后bar缺口，不夸称已证明每一潜在SETUP都被捕获。
