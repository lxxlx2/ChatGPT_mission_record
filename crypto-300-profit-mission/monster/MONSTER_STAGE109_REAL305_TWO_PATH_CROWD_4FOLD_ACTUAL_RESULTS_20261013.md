# Monster Stage109：真正新D1双路径模型，完整历史回测及失败证据

2026-10-13 Asia/Bangkok；原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。对用户的“先旧数据造模型，看效果，有问题再改”的实际进展。这里测试的是**D1高优先级过滤模型**，不是Stage99本地采集器，更不是正式Monster邮件/交易部署。

## 顺序与来源

- **先冻结**[Stage109两路径模型策略/技术合同](MONSTER_STAGE109_TWO_PATH_CAUSAL_CROWD_PRIORITY_MODEL_PREREG_20261013.md)，再完成[同一份实际代码](../local-agent/scripts/monster_v4_stage109_two_path_crowd_priority.py)，复用Stage100官方SHA钉住的Stage85当时特征305条/Stage88信号后价格路径305条。
- [实际跨平台CI #38412285041](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38412285041)：macOS-latest/Ubuntu-latest **2/2 SUCCESS**，GitHub Actions第三个job重新执行全部原样历史回放、保存完整模型与风险/漏报详情到[本次Git机器结果](evidence/monster_stage109_real305_two_path_causal_crowd_4fold.json)（真实Git blob `79a7c1a35fd9addd55aea469e76f302b2c73b907`）。CI PASS表示计算/回归闭合，**不代表策略PASS**。
- 纯当时信息：每条D1发生前**过去24小时全D1升级数量**（只计算本日期窗口中严格更早的D1，排除同分钟其他事件和未来时段）；加原始已闭合6项当时量价特征。DIRECT与REIGNITION用**不同**的固定L2 logistic模型，训练日期按4fold递进、训练期按路径分配预冻结4/UTC06日总关注预算；测试日期不根据结果调阈值，更不硬裁掉超过第5条后的WATCH。
- 原519 D0全部保留，原305 Stage79 D1全部保留；首两旧日期91 D1只作逐日期向前训练，后四旧日期214条完整测试；所有日期此前均**已经曝光**，绝不能称新OOS或未来预测能力。全305条拥挤度、全部214条测试分数、每折独立参数/训练阈值、未升级的亏损和暴涨案例完整保存。

## 实测：这是另一版必须拒绝的策略

| 指标 | Stage100已拒绝的单模型 | Stage109双路径+因果拥挤模型 | 原先冻结的正式目标 |
|---|---:|---:|---|
| 可评价后四日期D1 | 214 | 214 | 不删任何币 |
| PRIORITY个数 | 148 | **151** | 无固定个数，可因果降噪 |
| PRIORITY日均 | 5.2857 | **5.3929** | ≤5 |
| PRIORITY单日峰值 | 16 | **14** | ≤12 |
| 历史早报5m重大2×保留 | 20/27 = 74.07% | **20/27 = 74.07%** | ≥80% |
| 24h持有毛价格中位 | -4.3507% | **-4.7913%** | >0仅为实验标准 |
| 72h历史大涨≥100%保留 | 4/5 = 80% | **3/5 = 60%** | ≥80% |

全部实证指标来自[Stage109机器完整结果](evidence/monster_stage109_real305_two_path_causal_crowd_4fold.json)，不是推测。该策略对比Stage100并未改善真实核心门槛：**四项门槛全部失败**。尽管单日峰值从16降到14，仍高于12，且日均升高、24h价格中位恶化、漏掉7个早报2×以及2个72h大涨。

各测试窗口（不是独立未见验证集）：
- 2025-08-01：45 D1、33 PRIORITY、早报2×保留4/6，漏`MAGICUSDT`、`MEMEFIUSDT`，峰11。
- 2025-10-02：59 D1、48 PRIORITY、早报2×保留11/12，漏`BROCCOLI714USDT`，峰14。
- 2026-06-21：56 D1、40 PRIORITY、早报2×保留1/2，漏`VELVETUSDT`，峰14。
- 2026-07-28：54 D1、30 PRIORITY、早报2×保留4/7，漏`1000RATSUSDT`、`BEATUSDT`、`GIGGLEUSDT`，峰9。

**正式研究裁决**：`REJECTED_FROZEN_HISTORICAL_MODEL_GATES`，不是可部署策略；仍`G2_FAIL`、`G3_FAIL`、`G4_PRICE_MEDIAN_FAIL`、`HISTORICAL_RIGHT_TAIL_RETENTION_FAIL`。尽管历史模型开发完成、可重演，**新代码尚未获得独立其他AI审查**，不能把Stage105 Codex来源采集器APPROVE挪来批准该D1模型。

## 后续真正改变策略层，而非第N次调阈值

Stage100统一logistic和本阶段“拆DIRECT/REIGNITION并引入因果24h信号拥挤”都失败：这意味着当前305个D1时刻量价快照经24h涨跌标签学得的分数**不能稳定同时满足早报重大2×、右尾保留、关注负载和毛价格效益**。并不证明任何可能的模型都不行，但继续在这批已曝光数据上改LR、阈值或特征权重只会制造样本内优化幻觉。

下一技术主线应回到**真实D1事件的连续时间状态机**：D0全保留、D1先进入SETUP、观察其随后完成的1m/3m二次确认及否定条件、把大规模同市场再点火拥挤群组以可解释状态保存，重点计算“PRIORITY确认发生后”的真正入场时间/价格/滑点证据，而不是用已出信号那一分钟的价格当新模型的入场价格。重新执行全部519 D0源连续回放并严格区分D1已确认、过期和重大机会错失。真实分钟来源如现有Stage83/88分片已足够则复用并重验publisherSHA；缺未来新样本也能开发，未来日期只用于独立验收不阻挡研发。先冻结单一新状态机合同再编码，不在此历史已曝光集合调参直到过关。

## 安全/权限

Stage99 Mac已安装的三次市场名单快照独立运行，**本次没有改动任何Stage99代码或Mac服务**。不创建新定时任务、无Monster策略部署、无Frank变化、不发真实Monster Gmail、不下单，真实订单费率/盘口/名义金额不可证，因此`REAL_EXECUTABLE_NET_PNL=UNKNOWN`。

状态：`STAGE109_MODEL_CODE_AND_4FOLD_CI=DONE`、`STAGE109_STRATEGY=REJECTED`、`ORIGINAL_D0/D1=UNCHANGED`、`NEW_OOS=NOT_DONE`、`NEW_MODEL_EXTERNAL_AI_REVIEW=NOT_DONE`、`G3_PRODUCTION=REJECTED`、`DEPLOYMENT=NO_GO`。
