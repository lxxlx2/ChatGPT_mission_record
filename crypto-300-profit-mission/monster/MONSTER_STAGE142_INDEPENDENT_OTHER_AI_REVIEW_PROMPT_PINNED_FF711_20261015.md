# Monster Stage142 外部独立 AI 审核提示词（固定源码 SHA）

以下正文可直接复制到 Claude 网页对话或其他独立 AI。本文件的存在不代表已取得外部审核结论；本轮 G5=NOT_DONE。即使返回 APPROVE，也不授权合并、部署、邮件或交易。

---

请独立、严格审核 GitHub 仓库 lxxlx2/ChatGPT_mission_record，原 Monster Draft PR #30：
https://github.com/lxxlx2/ChatGPT_mission_record/pull/30

**本次唯一待审代码固定 SHA：ff711ebef8367635871004f27a98838f7aa8c4f3。**
分支：research/monster-v4-local-discovery-20261010
基准 SHA：50de0d8316c11ac4dcf7d736f397b9fdb16e0ce2。
不得以当前分支浮动 HEAD 替代固定 SHA，也不能把旧 PR / 旧 SHA 的 APPROVE 套用于本次修改。

项目目标是完整 USD-M USDT 永续妖币的尽早 WATCH/D1 发现及最终可实现正净收益，不是展示已经暴涨的榜单。Stage141 已在不修改冻结原 V4 D0/Stage80 D1 规则的条件下修复真实 525 个合约中 5 个 Unicode 币名的隔离回放。Stage142 新增了首次观察到的“窗口内新上市候选”冷启动重放：输入只包括 Stage133/134 记录的原始窗口和未经 PIT 独立验证的首次观察分钟，以及 Stage135 本地 ZIP+CHECKSUM 连续的延后公开 1m 数据；不许为新币伪造上市前的 24h 历史和 61 分钟 D1 特征。

请至少独立读取并复核这些文件在上述固定 SHA 的版本：
1. crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md
2. crypto-300-profit-mission/monster/MONSTER_STAGE142_FROZEN_LISTING_COLD_START_20261015.md
3. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage137_dynamic_t0_original_core_causal_replay.py
4. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage138_manual_evidence_scorecard.py
5. crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage137_dynamic_t0_original_core_causal_replay.py
6. crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage138_manual_evidence_scorecard.py
7. crypto-300-profit-mission/local-agent/scripts/monster_v4_shadow.py（冻结原 D0）
8. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage80_dual_entry_core.py（冻结原 D1）
9. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage135_full_market_publisher_minute_coverage.py
10. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage134_t0_population_readiness_bridge.py
11. crypto-300-profit-mission/monster/MONSTER_STAGE140_EXPLICIT_REAL_WWW_BINANCE_MIRROR_T0_SOURCE_CAPTURE_AND_FULL_POPULATION_READINESS_20261015.md
12. crypto-300-profit-mission/monster/MONSTER_STAGE141_REAL_525_SYMBOLS_UNICODE_D0_COVERAGE_FIX_TWO_OS_RESULTS_20261015.md

必须重点挑战，而非只作代码风格检查：
- ① Stage137 先审源、后因果 replay，首次观察分钟与真正首次可交易/可发警报事件能否被混淆？源来自延后归档还是实时数据？凌晨 T0 与真实事件 UTC 时间是否一致？
- ② 冷启动 D0 的 3m 绝对 UTC tick 是否恰好只读闭合1m，第一轮必须建立基线不能立即 WATCH；20%、15m、60m 等原信号设置是否被无意改动？滚动24h quote 是否只计算真实已观察到的区间，没有虚构前史？
- ③ 首个非整5分钟新币时刻（例如 06:21）如何产生全球自然边界上连续已完成的 5m 蜡烛？process_queue 是否可能拿到首分钟之前的 5m 或未来的 high？
- ④ Stage80 D1 首次 D0 出现而真实61根闭合1m不足时，features=None 和单独留存 D0 时点闭合价的 WatchState 修改是否忠于原逻辑；何时才能 61根后计算、是否可能过期后误触发、直接或再燃起路径是否一致？
- ⑤ Stage141 Unicode 内部 SHA256-ASCII surrogate 只进隔离 D0 SQLite；Stage80 与真实市场全部仍为原精确身份，是否有碰撞、错路由或通知/实盘误用的可能？
- ⑥ Stage138 是否正确保留 ALL original venue symbols 与新到名单、source CENSORED，不把未独立证明为加密币/首次交易的后验新 listing 加进 G1 原有币分母？gross HIGH×2 是否明显标记为未来事实、不是可成交价？
- ⑦ 根据真实 Stage140 数据：525 个初始 USDT 永续尝试、其中 COIN 523/INDEX 2；WWW FAPI exchangeInfo 内嵌 serverTime 约早8h44m，与独立官方 fapi 域名因地域451失败。是否仍必须 G0 PARTIAL？数据源 SHA 匹配是否只能证明本地一致，不代表 Binance 来源的外部证明？
- ⑧ 有无隐藏未来信息、竞态、巨大 SQLite 或 1m 文件性能问题、原 D0 队列首 WATCH / 冷却窗口错误、手动采集权限和 Frank/Gmail/定时任务越权？请指出最重要的少数真实功能性问题，避免为了审查数量制造低价值边界问题。

冻结验收原则：G1 至少3个真正独立完整七日前瞻窗口、至少20个已证实加密币毛2×，首 D0 严格提前≥90%、提前至少5分钟≥85%；G2 第一 D1 保留 D0 早5分钟成功≥80%；G3 平均 D1≤5/天、峰值≤12；G4 ≥30个独立有真实盘口深度、手续费、滑点、买卖退出和用户指定资金的净执行样本。G0 issuer/PIT/完整上市人群未过；G5独立审查尚未取得；G6生产部署未获授权。Stage116最初10月14日06:00源失败不可倒补；Stage118/127拒绝，Stage132 首追动量历史净收益代理为负，全部不得修改。

**真实 CI 证据（只代表合成 ZIP 源的工程测试）**：
Stage137 https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38615294004 ：macOS与Ubuntu各13/13 PASS。
Stage138 https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38615294086 ：macOS与Ubuntu各20/20 PASS。
CI PASS不是前瞻 G1 PASS，不是外部 Review，也没有实际 Mac 生产测试。

请自行拉取固定 SHA 后在 crypto-300-profit-mission/local-agent/scripts 执行：
python3 -m unittest -v test_monster_v4_stage137_dynamic_t0_original_core_causal_replay.py test_monster_v4_stage138_manual_evidence_scorecard.py
不要默认为测试资料是真实的2026年度独立前瞻收益证据。尽可能给出一个用真正已保存的原始历史源能够复现的问题案例，指出精确文件、行号、输入、预期/实际输出。

返回格式必须包括：审核固定 SHA、审查方模型身份、结论 APPROVE / REQUEST_CHANGES / BLOCKED、按P0/P1/P2的各问题清单、精确位置及复现步骤、对用户实际早报/可交易性/安全的影响、具体修复建议；如果仅工程源码 APPROVE，请明确它不是 G0-G4 模型通过，也不解除 NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE。没有实际检查的内容写 UNVERIFIED，绝不虚称独立 review 完成。

--- 
