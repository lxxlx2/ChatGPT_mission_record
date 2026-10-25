# Monster ADR-005：完整4599官方源与原生69 WATCH独立审查请求

- 项目：`lxxlx2/ChatGPT_mission_record`，仅 [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，分支 `research/monster-v4-local-discovery-20261010`。
- **固定待审代码 SHA：`cbce0ddef40ab23ba86ba27e31e3d93bfaa62362`**；审核前以该不可变SHA detached只读checkout，不用移动HEAD重算。历史基线原 paired-4088 JSON SHA256 `453ee2e740578121b0734d61e6eb357be7bb34859b90878eb314f7d3dc1690f5`；新版 original paired-4599 JSON SHA256 `bf8d1a1fd9916257fe39b0da1ae008fbe77e7ef35e09e1d61b24fe05641adbc1`。
- 范围：**只读独立外审，NO_MERGE / NO_DEPLOY / NO_MAC / NO_SCHEDULE / NO_GMAIL / NO_TRADES / Frank不动**。不要付费调用、启动运行服务、操作用户钱包或部署，不重拟合已曝光规则。无权限读取原GitHub Actions ZIP的审查者，应显式标记`RAW_ARTIFACT_INDEPENDENT_VERIFICATION_BLOCKED`。

## 审查的原始数据、运行与代码

1. 前511 frozen Spot T0身份来自Stage163官方archive，官方1m验收复用 `local-agent/scripts/monster_v4_stage166_spot511_official_1m_intake.py`；实际最后UTC2026-10-24新增 511/511 CSV完整1,440行、签名ZIP+CHECKSUM验证：[GitHub Actions #40171792607](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40171792607)，最后日报告 Artifact `12590422214`，每64个符号分片共八份官方源Artifact，仅push路径触发、无schedule。先验一个BTCUSDT源可用，再在八个分片有界获取；核实11月等未来数据完全没有混入。
2. 前4,088原始发行方日源对应 [原4,088回放 #40087231856](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40087231856)，Artifact `12557911034`；原53 WATCH原报告真实字节 SHA与canonical指纹已经有独立Code审查 `APPROVE@73732fc647d588e9de33281d6aea8ac3e58763f4`，仅限WATCH绑定P1，不代表当前全源回放的独立审核。
3. 新冻结4,599个 symbol-day ZIP/CHECKSUM 重新交叉并成功执行原 `local-agent/scripts/monster_v4_spot511_paired_sqlite.py` 的同一份不可变 FIFO8/Fair8 Shadow：[Actions #40172014267](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40172014267)，Artifact `12590697491`（`paired-4599.json`、`summary.json`）。固定七日3360/3360轮、511名单、全部4,599/4,599日源，旧53/46原 WATCH/SETUP事件零丢失，新69 WATCH、59 SETUP、增加16/13、FIFO/Fair8结果同一。原代码未作模型变更；源是历史后归档，实际2026-10-17..24的网络接收`available_at`未知；2026-10-25T00:00Z作为闭日asof门槛**不能**冒充出版社实时文件发布时刻。
4. 新研究适配 `local-agent/scripts/monster_v4_adr005_real69_original_sqlite_replay.py`、专项测试 `local-agent/tests/test_monster_v4_adr005_real69_original_sqlite_replay.py`，复用 `monster_v4_d1_rbtc15_episode_research.py`/ `monster_v4_d1_rbtc15_last5_research.py`，经完整69 WATCH固定 SHA256和69个精确币日来源做一次原生SQLite D1。 [Actions #40172786657](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40172786657)，真实Artifact `12591221330`（`real69.sqlite`、`real69.json`），6/6新专项CI PASS。上轮53完整研究同源码回放 [Actions #40170821372](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40170821372) Artifact `12589558700`；其探索参考Git Blob `4bb360a376223da1ba594c320f31ceccc335202a`，53/53行状态与触发时间重新匹配。
5. 新研究全69 WATCH状态：`RESEARCH_SETUP=47 / NO_SETUP=10 / SOURCE_UNSCORED=4 / LATE_UNSCORED=8`。前53为`37/7/3/6`，新增16为`10/3/1/2`。研究 SETUP 日期UTC10/18至10/24为`6/6/7/7/8/3/10`，日均6.71，峰值10。原D1 59 SETUP对应`8/7/7/9/11/4/13`，日均8.43，峰值13。先前新D1 37 SETUP有33普通加密、2 Chiliz fan、2 bStocks；新16产生10 SETUP中，已有本PR预先锁定Binance官方26币身份资料可证明7条普通加密：BMT1、EPIC2、AVA1、QUICK2、ERA1；其他TREE/LA/ANIME三条为分类未确认。新研究**至少40条**有积极的事前Crypto身份，已大于原Stage77七天35条注意力总限，不能称新G3通过。历史动态上市、当时账户交易资格/PIT不完整，勿将这40条升级为实际历史可下单资产。

## 必须由另一个AI重新验证的断言

A. 实际核查GitHub工作流与原始Artifact，而不仅阅读本摘要：源SHA链、4599互异官方归档、币日身份固定、必需来源不因`merge-multiple`/重复metadata冲突而被假替代，发行方校验失败是否严格以未知处理；审查`--asof`时间与真实发行方发布时间不匹配是否可能造成看未来。

B. 在同一冻结数据上独立重算至少随机抽取10条（含10/24新候选、重复symbol、新源删失）原事件ID、观察时钟、6根币/BTC闭合5m、原15分钟deadline、FIFO8/Fair8是否真正有区别。特别测试源曾删失而末次完整负样本应为`SOURCE_UNSCORED`、已到时点仍未评估应为`LATE_UNSCORED`，旧53不得被重新定价改写。

C. 原69研究使用已曝光10月窗口，不能作为三段预注册11/12月未来OOS；新的40条积极Crypto身份是「类型下界」并非动态交易资格或真正可执行净利；严格检查日均<=5、峰值<=12、G1 >=20个独立2×/3窗口、G2提前5m保留>=80%、G4至少30个可核实双侧成交及费用。确认原Stage132负收益代理及既有P1/P2拒绝策略没有被新代码默默推翻。

D. 审查不触碰Frank、网络后台、launchd/cron、GitHub schedule、Gmail、Mac、买卖路径、金额默认值；本批仅官方只读研究数据和GitHub源码/Artifact。检查仓库原Shadow、Stage166、Stage162未被修改，原门禁继续NO_GO。

**返回格式**：`APPROVE | REQUEST_CHANGES | BLOCKED`；精确待审SHA、实际审查AI与版本（不知道则UNKNOWN）、运行环境、真实命令与可核验日志/Artifact、各项P0/P1/P2文件+行号、可复现反例、是否改变既有WATCH/SETUP或生产授权；单列G0-G6和`NO_MERGE/NO_DEPLOY`。若某项资料不可读，不得写APPROVE全部证据，只能限定已验证范围。
