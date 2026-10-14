# Monster Stage130：首次一分钟新上市研究，31个完整官方Publisher SHA源的真实历史回放

日期：2026-10-14 Asia/Bangkok。原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。任务领域只限 Monster V4 妖币研究。**历史曝光回测、非未见过的前瞻、非交易盈利，模型不具备部署资格。**

## 1. 来源实际执行及事先冻结

- Stage77 既定模型验收闸门不变。原 Stage118 与 Stage127 为 **REJECTED**；任何替换参数、增加信号通道都不修改原模型失败。
- **在读取首次一分钟历史后的计算之前**，已冻结 [Stage130 完整31样本及因果协议](MONSTER_STAGE130_FROZEN_NEW_LISTING_31_OFFICIAL_1M_CAUSAL_RESEARCH_PROTOCOL_20261014.md)，预注册 commit `5b48e98c52b560925278fa244e7a3bfe70a11620`。本轮只用 Stage128 提前选出的31个 `IN_WINDOW_LATER_ONBOARD_NOT_HISTORICALLY_PROVEN` 合约日期及 Stage129 实际已归档第一小时，用于锁定当时尚未覆盖的原历史分钟来源；**不对未来涨幅做入选筛选**。
- 完成 [Stage130 独立1m源验证及闭合分钟时点研究程序](../local-agent/scripts/monster_v4_stage130_first_listed_minute_sha_replay.py)、[测试](../local-agent/scripts/test_monster_v4_stage130_first_listed_minute_sha_replay.py)、[macOS/Ubuntu离线测试与一次性官方源研究CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38566877450)。唯一1m真实采集来自 Binance 原始官方历史 Data Vision `futures/um/daily/klines/{SYMBOL}/1m` ZIP 及相应 `.CHECKSUM`，每一份 ZIP 都要求 **Publisher SHA256 实际一致**，不使用今天的24小时 ticker 冒充上市时源。
- 真实 GitHub Actions `#38566877450` 执行结果：macOS、Ubuntu 离线回归与独立 Ubuntu 1m publisher source job **SUCCESS**（被验证代码 SHA `ac4623af220d610a9c705cf9334d7b93e13bd35b`）。CI完整源 ZIP / 147份官方校验回执 / 完整逐31结果保存在 Artifact `monster-stage130-frozen31-original-publisher-minute-data`，artifact id `11896196549`，GitHub默认本工作流保留30天。不能将 CI artifact 当作永久 Git raw ZIP。
- 从CI下载真实 Artifact 并独立读取 `stage130_real31.json` + 全147个 ZIP/CHECKSUM，确认各档 ZIP 的当前 SHA256 均与 JSON 回执以及源文件内出版者 checksum 匹配，无一失败；本次提取的 `stage130_real31.json` SHA256 为 `a97037bff9d834f0f59fb3a0ae45942a9c28453dbfc0d01331fd78afa49b8f50`，Artifact ZIP SHA256 为 `e1a5931b64497214faa726831cbe1c64e2c93c3cbfd1c2e101af402da816372b`。不将这些文件误称新实时采集。
- 精简完整31条研究记录已永久提交至 [Stage130真实机器结果Git](evidence/monster_stage130_original31_publisher_sha1m_momentum_archived_summary_20261014.json)，包含合约、首根1m、首触发、首2×、所有31个的历史最高倍数及各合约官方文件数；原始147个每天 ZIP 的字节永久性由 Binance 发布站点和源校验负责，现时CI artifact保留可供独立复查。**精简Git记录仅保留全原始文件的摘要哈希，不宣称Git已保存全部原始147个ZIP。**

## 2. 真实全量31结果

| 冻结31个历史已曝光合约样本，来源与研究结果 | 实际值 |
| --- | ---: |
| 31个已冻结原 symbol/date，全保留 | **31/31** |
| Publisher SHA256通过的官方日1m ZIP/校验对 | **147/147** |
| 通过完整上市首分钟到原七日窗口结束且每分钟连续 | **31/31** |
| 合计有效原始1m candle | **159,675** |
| 相对**首次有效1m OPEN**，后续任何1m HIGH达到2× | **2/31** |
| 同口径后续触及5×、10× | **0** |
| 满足预冻独立新上市研究用动量条件的唯一合约/窗口 | **19/31** |
| 上述研究动量在首次HIGH跨2×**至少早5分钟** | **2/2**，仅历史曝光两个正例 |
| 动量研究触发但当窗口没有2× gross HIGH | **17/19** |
| 31个历史精选新上币的日触发峰值 | **2/日**（只计算此小样本，不能代表全市场G3） |
| 真正全市场 Crypto 未曝光未来OOS G1 | **NOT_SCORABLE** |
| 有实际盘口/交易费用/买入金额与平仓卖出证明的净盈利 | **UNKNOWN** |

研究触发器按冻结合约：在 **UTC整3m、仅已闭合1m** 资料下，3分钟涨≥5%、15分钟涨≥8%、60分钟涨≥15% 任一，且截至当时从第一分钟累计的真实1m quote成交额≥100,000 USDT。**这并非原V4完整24h ticker条件**，属于上市初期 `PARTIAL_LISTING_QUOTE_CONTEXT` 的另一条 *未通过验收* 研究信号。不对原 Stage77 G1、G2、G3 过线做宣称，也没有任何 BUY/可交易身份。

### 两个真实 source-verifiable 历史高点例子

| 合约 | 首次有效1m | 首个研究动量信号 | 首次1m HIGH触及2× | 理论提前量 | 最高毛HIGH / 第一根1m OPEN |
| --- | --- | --- | --- | ---: | ---: |
| `VINEUSDT` | 2025-01-24 10:00 UTC | 2025-01-24 10:12 UTC | 2025-01-25 04:53 UTC | **1,121分钟** | **2.1571×** |
| `APRUSDT` | 2025-10-23 10:30 UTC | 2025-10-23 10:42 UTC | 2025-10-23 23:59 UTC | **797分钟** | **2.3962×** |

此前Stage129只有**小时**最高价，2×跨阈值的时间只能定到该1h；本轮官方分钟数据把首跨小时内的时间精确到 **04:53 UTC / 23:59 UTC**。两个样本的早报结论只用于已经被发现、后验已见上涨的 *小样本历史研究*，既不能声称具有预测统计显著性，也不能称首次信号价后用户实际可买且盈利。高点是未来1m HIGH，非真实卖出价。

## 3. 工程限制、结论及后续主线

- **技术取得**：真实市场开市未满24小时甚至不足60分钟时，原仅按整周完整/24h历史的研究会系统性删失候选。本次已证明 31条原本缺失整周历史的上市片段全部能用真实分钟源解释，两个历史2×案例若完整读取上市后的真实分钟并使用单独的观测机制可以在毛上涨前研究性触发。
- **策略尚不合格**：研究触发19个中只有2个达到该批次 gross HIGH 2×，其他17个未达；2个正例是已曝光赢家，无法在真正新的全市场中外推。无需为了“19个提醒过多”修改已知暴涨结果阈值，下一模型须先独立冻结并等待未曝光样本验证。
- **真实币种历史身份**：Stage123 的后验字段31个里20标 `COIN`、7标 `EQUITY`、4标 `HK_EQUITY`；其2025/2026历史时点发行方/对应现货资格与合约实际单位 **未独立确认**。保持原31完整审计，正式 G0 不能自动让非 Crypto 成负例，也不能拿后来的类型当历史时点证明。
- **交易**：没有真实买卖报价、订单深度、用户自定名义交易额或历史时间点双边可成交成本、退出订单及其结果。即使首次1m的HIGH达到2×，净收益依旧 UNKNOWN，G4未完成。
- **下一主线**：将已有的 Stage116 冻结完整窗口及原 Stage105 动态上市边界研究统一，事先冻结一套真正后续未曝光时段的**全市场全币+窗口内新上市**人口定义，保存合约第一分钟、源完整/删失、无 WATCH 的全部赢家分母；在截止窗口未来数据产生后再对照原 D0 与新增上市候选。原 Oct28 / Nov11 的市场快照仍严格仅在用户聊天发起时采集，没有恢复定时任务。真正 G0–G4 过线、其他 AI 真独立Review和用户明确批准前不部署、不发送 Monster 邮件、不交易；Frank保持原样。

`STAGE130_VERIFIED_31=31`; `STAGE130_PUBLISHER_SHA_ZIPS=147`; `STAGE130_CAUSAL_1M_SOURCE=159675`; `STAGE130_HISTORICAL_MOMENTUM_CANDIDATES=19`; `STAGE130_HISTORICAL_GROSS_2X_EARLY5=2_OF_2_ALREADY_EXPOSED`; `G0=PARTIAL`; `G1_NEW_OOS=NOT_SCORABLE`; `G2_G3=NOT_PASSED`; `G4=UNKNOWN`; `STAGE118=REJECTED`; `STAGE127=REJECTED`; `INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`; `NO_AUTO_CAPTURE`.
