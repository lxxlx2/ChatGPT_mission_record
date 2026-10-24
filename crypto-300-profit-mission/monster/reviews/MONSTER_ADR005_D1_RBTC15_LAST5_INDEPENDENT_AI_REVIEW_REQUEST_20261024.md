# Monster ADR-005 单一 D1 候选：独立其他 AI Review 请求

**待审核源码固定SHA**：`06aa72fceeb63c73375b556e7f8d44509452207a`
**仓库**：https://github.com/lxxlx2/ChatGPT_mission_record
**PR**：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
**分支**：`research/monster-v4-local-discovery-20261010`
**审核模式**：只读独立审核，不 merge、不部署、不下单、不发信、不创建自动化。文件本身的提交将使分支HEAD后移；**代码审核对象始终固定为上述不可变commit**，不要混用之后的HEAD。

以下提示词可直接复制到 Claude 网页对话：

---

你是 Monster 妖币主线的**独立第二AI代码及模型审核者**。请以 Git commit `06aa72fceeb63c73375b556e7f8d44509452207a` 独立checkout并核对PR #30，不信任先前助手声称的结论。目标不是代码风格，而是证伪新D1的因果性、研究设计和安全性。若无法访问仓库/真实源码和文件，必须返回 `BLOCKED`，绝不声称独立复核通过。

**先读冻结标准**：
- `crypto-300-profit-mission/monster/MONSTER_STAGE77_CORE_MODEL_ACCEPTANCE_AND_BOUNDARY_FREEZE_20261013.md`
- `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`
- `crypto-300-profit-mission/monster/adr/ADR-004-monster-product-mainline-scope-and-delivery-order-20261023.md`
- `crypto-300-profit-mission/monster/adr/ADR-005-spot-d1-btc-relative-confirmation-preregister-20261024.md`

**审核实际源码和测试**：
- 新研究比较器 `crypto-300-profit-mission/local-agent/scripts/monster_v4_d1_rbtc15_last5_research.py`
- 新回归 `crypto-300-profit-mission/local-agent/tests/test_monster_v4_d1_rbtc15_last5_research.py`
- 原D1只读对照 `crypto-300-profit-mission/local-agent/scripts/monster_v4_shadow.py`（必须确认没有修改此文件，原Core blob `bc958b3d90a8a52afa51515cb53f7e5fafaffaaa`）
- 原日期分钟源 `crypto-300-profit-mission/local-agent/scripts/monster_v4_spot511_d0_d1_tape.py`、`monster_v4_spot511_paired_sqlite.py`
- 当前官方T0/来源和原46条SETUP `crypto-300-profit-mission/monster/evidence/MONSTER_SPOT511_4088_REAL_GLOBAL_FIFO8_FAIR8_46_SETUP_EVENTS_20261024.json`
- 资产类型/验收 `crypto-300-profit-mission/monster/evidence/MONSTER_SPOT511_4088_G3_ALL46_PRE_EVENT_ASSET_CLASSIFIED_20261024.json`

**本轮真实测试证据**：GitHub Actions `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40093380416`，全9组测试`13+5+6+11+19+12+12+14+18=110/110 PASS`，新研究模块为18项，都是合成数据时钟/数据质量测试。**没有在三个预注册未来窗口做过真实数据验证，也没有 G1/G2/G3/G4 或收益 PASS**。原已曝光10月18–23 53 WATCH/46 SETUP，纯加密41、粉丝3、证券2，原D1六日已超过关注目标，Stage132毛价代理负、其他旧候选已被拒绝；不能拿已曝光46例拟合新阈值。

请独立审核并尽量实际运行：`PYTHONPATH=crypto-300-profit-mission/local-agent:crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p 'test_monster_v4_d1_rbtc15_last5_research.py' -v`。

**重点查错**：（1）最新六根UTC闭合5m与观察时钟的对齐、UTC 3m时钟、是否可能用到当前尚未闭合K线、买卖价/PIT伪装；（2）原D1 2/3步上涨+成交额比>=1.5+末>=第三根与新`coin[5]/coin[2]-btc[5]/btc[2]>=0`和末5m非下跌的数学/边界、一根BTC缺档应CENSORED而非负例；（3）比较器没有实际状态机/全市场集成，对原D0候选重试、15分钟deadline、8槽FIFO/Fair8和事件去重是否会造成不可预见G2损失，给出明确缺的集成测试；（4）G3真实通知注意力上限日均<=5和单日<=12，不得以Monitoring Tag/买入测验属于G4为由扣G3；（5）G1需20独立2×事件和>=3独立未看过窗口，>=90%严格提前和>=85%提前5m；G2保留>=80%，G4>=30个完整双侧可成交观察+自定义金额，G5真实其他AI审核/独立复算，G6仍NO_GO；（6）冻结日期2026-11-02..09、11-16..23、12-01..08 UTC是否有样本泄露、来源warmup/未来标签错误、选择偏差，且若源失效不能挑选有利日期替代；（7）不得影响Frank/Mac/Gmail、真实交易/后台定时任务。

**必须输出格式**：
`结论：APPROVE | REQUEST_CHANGES | BLOCKED`；
`审查固定SHA`；
`审核身份/模型及是否实际执行测试`；
`P0/P1/P2发现：准确路径:行号、复现步骤、影响WATCH/SETUP/G0–G6、建议修复`；
`源码数学与UTC/PIT因果验证`；
`缺失的真实数据/样本外回放/历史资格/盘口项`；
`NO_MERGE/NO_DEPLOY/NO_TRADES/NO_GMAIL是否保持（默认全部保持）`。
没有证据的项必须标UNKNOWN或BLOCKED，不能把CI通过当策略通过，不允许自行部署/改Git。

---

状态 `G5_OTHER_AI_REVIEW=NOT_DONE`；这份请求和后续用户转发给Claude都不自动构成外审结论。任何修改源码后的新SHA须重新pin和独立review。
