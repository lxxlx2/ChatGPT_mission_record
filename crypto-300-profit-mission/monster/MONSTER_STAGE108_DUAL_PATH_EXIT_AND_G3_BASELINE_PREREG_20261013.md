# Monster Stage108 — D1双路径持仓策略与G3负载同代码历史实验（事前冻结）

冻结：2026-10-13 Asia/Bangkok。原 [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。用户主线是**旧数据建模→效果验证→必要时改新策略**，不是等Stage99采集器。Stage99已由用户Mac独立安装，此文件和实验绝不调整其采集窗口/服务/源码，绝不触碰Frank、Gmail、自动化和交易。

## 源与前瞻边界

以 Stage101 原始305完整 Binance官方1m逐币回放退出档案 `crypto-300-profit-mission/monster/evidence/monster_stage101_all305_real1m_historic_exit_paths.jsonl` **Git blob `19dfc89ab10aaf23f068bee924cddc85d5bcc3e1`** 为唯一策略比较输入，所有305行`(date,symbol)`唯一、6个历史日期、164 DIRECT/141 REIGNITION、27旧2×提前5分钟。此前Stage101重新逐源校验每个日1m发布者SHA与Stage88，Stage101全原始完整档。禁止只抽右尾赢家。始终写`EXPOSED_RESEARCH_NOT_INDEPENDENT_OOS`，没有盘口、订单名义金额、滑点时`REAL_NET_PNL=UNKNOWN`。

## 策略冻结和验证

策略`STAGE108_PATH_EXIT_V1`只用D1当时已确定的路径类别，无训练阈值：
- `DIRECT_AT_FIRST_D0`：D1+1分钟开盘价格代理入场，原**24h**已完成分钟收盘价退出。
- `REIGNITION_AFTER_D0`：同一入场，原**12h**已完成分钟收盘价退出。
- 基准`ALL24H`：全部原24h出口；原`ALL12H`单列敏感性参照，禁止事后把更好看的6h或72h改成“策略”。
- **观察和D1升级保持原Stage79完全不变**，所以D1原始负载仍305/42日，平均7.26，峰值52；此实验**只能研究持仓路径，不能声称G3已改善**。不改原D0/WATCH，不因退出策略删币。所有同币不同日期仍当不同来源币日，所有原D1信号留下逐条证据。
- 额外仅给出单笔入场/出场各20bps、各100bps的**统一人工费用敏感性情景**：`100*((1+gross_return/100)*(1-fee)/(1+fee)-1)`。不称真实交易所fee、滑点、盘口净收益，绝不假设最高价实际成交。
- 同日期及六历史日期整体统计各策略：n、正毛价格比、毛中位、≤-20%风险、≥+50%、≥+100%、原已提前5分钟2×机会计数和日期桶42天信号负载；另外四个后序日期给出独立历史时间分组但它们**已经曝光，不能叫未见holdout/OOS**。
- 负例必须原样留存；主验收不能仅凭中位改善：路径策略全部305相较ALL24H，毛中位要**>0**、≥100%右尾须保留**至少80%（此处原5例至少4例）**；G3另外必须平均≤5/日且峰值≤12；原D1重大机会必须≥80%。任何失败均`REJECTED`，并指明是**退出策略还是关注层G3**失败；无任何真正执行净收益则不能部署。

## 本次工程与下一轮聚焦

先提交此合同，再编写 `monster_v4_stage108_path_exit_replay.py` 的原305完整实证、源码自测及跨系统GitHub CI；留存机器JSON和负例，不改变2026-10-14等未来冻结日期。若此候选因右尾损失和负毛收益被拒，**不要继续在相同305条历史数据上试不同12/6/24小时参数**。下一主要模型实验需要用D0观察→D1双路径，在更大519币池保持原事件，分别引入明确可观察、可因果复跑的确认/失效状态机，并依据失败归因而非事后赢家筛选；仍按Stage77 G2≥80%、G3≤5/日且≤12峰、G4可成交净收益，未经验证不部署。

## 预冻结禁止事项

不将旧Stage100 logistic 24h方向模型换标签补凑PASS，不事后按已知赢家改变时间退出，不把Stage99市场名单误认为连续七日价格源，严禁将采集器Codex审查APPROVE挪为Monster策略独立评审/部署批准。

状态：`D0_UNCHANGED`；`STAGE79_D1_UNCHANGED`；`STAGE108_RESEARCH_CONTRACT=FROZEN_BEFORE_CODE_AND_CI`；`STAGE108_RESULT=NOT_YET_EXECUTED`；`G3_ORIGINAL_REJECTED`；`REAL_EXECUTION_UNKNOWN`；`AUTOTRADE_NO_GO`。
