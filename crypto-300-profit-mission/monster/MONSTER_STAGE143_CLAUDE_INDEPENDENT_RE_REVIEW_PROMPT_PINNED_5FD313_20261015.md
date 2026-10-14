# Monster Stage143 — 直接复制给 Claude 的独立复审提示词

请担任严格独立 AI 审核员，针对上轮你在旧 SHA 提交的 REQUEST_CHANGES 做**修复后复审**，只审核固定版本，给出新结论；不要只复述旧问题或仅信任 CI。

仓库：https://github.com/lxxlx2/ChatGPT_mission_record
原 Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
分支：research/monster-v4-local-discovery-20261010
**本轮复审固定新 SHA：5fd3138702a3caef69ce2d48696059bceeefd6f9**
旧被拒代码 SHA：ff711ebef8367635871004f27a98838f7aa8c4f3
最初冻结比对基准：50de0d8316c11ac4dcf7d736f397b9fdb16e0ce2
复审不得以浮动 HEAD 替代此固定新 SHA，后续只加 Markdown 不应认定为再次修改的 Python 代码。

## 请核对的规则/报告/代码

- crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md
- crypto-300-profit-mission/monster/MONSTER_STAGE143_FROZEN_CLAUDE_REQUEST_CHANGES_REMEDIATION_20261015.md
- crypto-300-profit-mission/monster/MONSTER_STAGE143_CLAUDE_EXTERNAL_REQUEST_CHANGES_REVIEW_INTAKE_20261015.md
- crypto-300-profit-mission/local-agent/scripts/monster_v4_stage134_t0_population_readiness_bridge.py
- crypto-300-profit-mission/local-agent/scripts/monster_v4_stage135_full_market_publisher_minute_coverage.py
- crypto-300-profit-mission/local-agent/scripts/monster_v4_stage136_manual_publisher_archive_acquisition.py
- crypto-300-profit-mission/local-agent/scripts/monster_v4_stage137_dynamic_t0_original_core_causal_replay.py
- crypto-300-profit-mission/local-agent/scripts/monster_v4_stage138_manual_evidence_scorecard.py
- 对应 Stage134/135/136/137/138 test_*.py 文件和 .github/workflows/monster-stage143-claude-p0-p1-remediation-integrated-offline.yml
- 冻结原 monster_v4_shadow.py D0（git blob bc958b3d90a8a52afa51515cb53f7e5fafaffaaa）以及 monster_v4_stage80_dual_entry_core.py D1 未修改。

## 核对你之前找到的真实缺陷，给出 PASS/REPRODUCED/OPEN

1. **P0 最近上市盲区**：在 synthetic T0=2026-10-28 06:20Z，原 exchangeInfo `onboardDate` 00:20Z，publisher 1m ZIP 首根为 00:20Z、之后每分钟连续。原先会因 T0-24h 缺档被整体 CENSORED；现在 Stage134 保留源声明、Stage135 严格只在 publisher 首 bar 与 onboarding 分钟一致时识别 pre-T0 最近上市冷启动，Stage136 只规划实际源日，Stage137 从新 T0 起以原 D0/D1 执行，无伪造上市前 24h。请实际复现原缺陷和新修复，额外质疑历史归档与 as-of onboard 的时效真实性（只应能给 UNVERIFIED，而不是已独立核实）。还要验证 00:25 首根不匹配 00:20 时确实 fail-closed，不能把 source missing 误判作 no-WATCH。
2. **P1 G3 全 cohort D1**：复现你前次 NEWUSDT 06:57 D0、07:24 D1。此次 Stage137 每个已存在、T0前最近上市、窗口内新上市的首次 D1 全部进入按 UTC 日的总负载，并另保存三组数组；Stage138 独立逐 symbol 重算，检查总计/分组与回放对账。请实际确认一个新币 D1 再也不会出现 total_daily 全0 的旧问题。若用户实际邮件仍未发生，报告只能称 retrospective potential notification count，不允许宣称已通过 G3 真实时效门禁。
3. **P1 G1 分母诚实性**：Stage138 原场所完整源旧币 complete-case 回顾式 2x/early5 与新上市、pre-T0 最近上市的 source-conditioned 2x 单列；缺档保留 CENSORED，全人口完整计数；已加“假设所有缺档均2x且未被发现”的悲观情景，必须检查它明确标为 hypothetical mixed venue NOT actual G1 recall。审核该情景是否误把 issuer UNKNOWN/INDEX 当可核实 crypto。
4. **P1 零发现延迟与 quote24 门槛**：是否将原 publisher 首根 open 与真实 websocket/交易所发现时刻明确分开？新增 1/3/5分钟延迟仅为 optimistic upper-bound 必要条件，不是真正迟到重新运行原 D0，请判断这种表述是否足够显著、真实策略是否依然可能更晚甚至漏报。原 quote24>=100000 USDT 不得调参；合成 quote 未达门槛但已 gross HIGH2x 时必须呈现结构性漏报诊断，不可生成 BUY。
5. **P2 首 poll 时序**：首次观察 O=06:22Z，第一个绝对 UTC3m poll 不能早于 O+3min，因此是 06:27Z；在 pre-T0 最近上市源中 earliest poll 不能早于 T0+3min。全部价格/quote/已闭合1m以及已闭合原5m不能出现任何未来信息，Stage80不足61根闭合1m必须保持数据未知。Unicode别名必须只存在于隔离 SQLite，绝不可污染真实合约symbol。
6. **授权/范围**：任何场景不得将用户仅授权研究理解为恢复 Stage99、创建 cron/launchd/ChatGPT task/GitHub schedule、执行真实 GET、发Gmail、碰 Frank或下单；D0/D1阈值、原 Stage116首窗失败、Stage118/127拒绝、Stage132负收益固定不变。

## 机器回归证据与复现

固定新 SHA 对应 GitHub Actions Stage143 集成：https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38646498839
Ubuntu job 116134533414：66/66 PASS；macOS job 116134533647：66/66 PASS。`Ran 66 tests`、`OK` 和不联网/不调度/不发信门禁皆经真实日志读回。请尽量在你的容器独立执行：

cd crypto-300-profit-mission/local-agent/scripts
python3 -m unittest -v test_monster_v4_stage134_t0_population_readiness_bridge.py test_monster_v4_stage135_full_market_publisher_minute_coverage.py test_monster_v4_stage136_manual_publisher_archive_acquisition.py test_monster_v4_stage137_dynamic_t0_original_core_causal_replay.py test_monster_v4_stage138_manual_evidence_scorecard.py

## 真实市场与放行事实

Stage140 2026-10-14T17:52:47Z 实际从 Binance WWW FAPI 备用主机保存 525 初始交易中的 USDT 永续（523 官方 COIN typed，2 INDEX），但标准 fapi 美国出口 HTTP451、镜像 exchangeInfo 内嵌 serverTime 约早8h44m，PIT crypto issuer/来源等价性未独立核验。**真实525初始名单中目前没有任何 onboardDate 落在该T0前24小时内**；P0 修复完全来自经过真实校验逻辑的合成归档测试，绝不可声称真实盈利验证。新7日全量 publisher 来源仍未取得；旧 Stage116 最初采集失败不可倒补。原 G1门槛仍要求 >=3独立前瞻7日窗口、>=20已核实 crypto 2x、首 D0 strict>=90% 和提前5min>=85%；G2 D1保留>=80%，G3平均<=5/day峰值<=12，G4>=30独立真实盘口/费用/滑点/退出成本样本。工程修复不能直接赋予 G0/G1/G2/G3/G4 PASS。

请返回审查的**精确固定 SHA**、模型身份、`APPROVE / REQUEST_CHANGES / BLOCKED` 的**代码审查**结果；逐一关闭/继续开启旧 P0/P1 发现项，并列新 P0/P1/P2（精确文件+行+复现输入/实际输出+核心业务影响+最小修复建议）。即使代码 APPROVE，也须保留 `G0 PARTIAL / G1 NOT_SCORABLE / G2_G3 NOT_PASSED / G4 UNKNOWN / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，并明确 G5 仅在本轮实际复审反馈处理完毕后才能作审核处理。未经核验写 UNVERIFIED，不要添加与妖币真实早报无关的低价值边界工作。