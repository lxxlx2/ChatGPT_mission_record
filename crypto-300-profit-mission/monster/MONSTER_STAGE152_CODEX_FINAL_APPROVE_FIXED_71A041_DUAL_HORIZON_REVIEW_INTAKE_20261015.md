# Monster Stage152：Codex 独立最终 APPROVE@71a04140（只对聚合器P2修复）

本条为用户于2026-10-15提供的Codex独立复审报告的源限定归档，**不是假称GitHub原生review**，也不是作者自己的审查行为。Codex底层精确模型版本 `UNVERIFIED`。原PR [#30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30) 继续OPEN/DRAFT。

## 审核身份和结论

- 审核者用户声明：Codex；执行环境 Darwin / Python 3.14.7，detached HEAD `/tmp/monster152-review-71a04140`，真实工作区不改动。
- 唯一完整固定代码/测试 SHA：`71a041405352c9e2210d93dff9c2685149809e52`。
- 上轮 `REQUEST_CHANGES@f12d6635c6f8a5e2ba8fbb2feeca29688583245b`，3个原P1已按前次历史研究范围关闭，新增P2=6h/24h两组敏感性被后者覆盖。
- **本次独立审查：`APPROVE@71a041405352c9e2210d93dff9c2685149809e52`，该P2关闭，新增P0/P1/P2=0**。仅批准代码修复，不批准经济模型/交易/部署/合并。
- 需保留旧代码版本的 `REQUEST_CHANGES`，新提交不追溯修改旧结论。原Stage151 D0/D1规则 `DROP=.97 / RECLAIM=1.01 / MAX_BARS=120 / HORIZONS=360,1440 / FEE=.002 per side` 不变。

## 从Git直接可复核的证据

[真实源码SHA对应GitHub Actions #38734029751](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38734029751) `completed/success`，27/27 Jobs成功，Ubuntu24.04/macOS各20/20 unittest成功、24个官方出版者 SHA 锁定历史行情shard成功、全305结果聚合归档和 `STAGE152_ACTUAL_GIT_EVIDENCE_PUSH_CONFIRMED`。结果摘要 [Stage152完整机器输出](evidence/monster_stage152_original305_integrity_and_economics_summary.json)，源档案Git blob `518e7aa0d8db83fd1b818513ae7e72b165252806`；报告中 `trigger_commit_sha=71a041405352c9e2210d93dff9c2685149809e52`，core SHA256 `cf1624048af1349266ceeae0171536c7c9dabc24c8300092caeb4c4c6ac11c10`，aggregator SHA256 `eb9c51504e0d380716a06fe638fdfa80b94a27bd282a54470cf9c16da642aacf`。

**独立Reviewer此次真实执行的内容按用户提供的审查报告记录**：Python 3.14.7 本地两个测试集 `20/20 PASS`、py_compile；自行运行 `/tmp/review152_p2.py` 复验24 sharded artifact聚合与原Git summary逐字节一致 `24_SHARDS_REAGG_SUMMARY_EXACT True / ROWS_EXACT True / AGG_SHA_MATCH True`；另运行 `/tmp/review152_p2_mutation.py` 在旧聚合器上看到 **1 failure+1 error**，说明新增2个测试能确实杀死旧覆盖错误，而非装饰性单测。review临时探针脚本`/tmp/...`不在Git，不得声称仓库存放了本机复现文件。

新源码把两个对象分别变为 `market_1m_turnover_sensitivity_NOT_execution["360"|"1440"]` 及 `entry_delay_price_only_sensitivity_NOT_execution["360"|"1440"]`，读不读6h不改变24h；真实全305分类 `184/113/8`，0/10k/100k双边市场一分钟成交量门槛6h样本 `184/133/54`，24h样本 `184/124/39`。1/3分钟额外进入时延研究收益中位数：6h `-1.684256%/-1.720261%`，24h `-1.870766%/-2.010169%`。**9组**（overall/6日期/DIRECT+REIGNITION）逐组聚合、原始rows字节不变、除预期新两层结构及trigger/hashes外旧摘要其余指标无差异。

上轮独立Codex曾获取 **官方Binance 1220份日ZIP+CHECKSUM，1220/1220 SHA正确** 且全部305行独立原始分钟重放一致；本轮没有重新下载，核查了源核心SHA未变化和rows字节不变，故上轮对未改的输入及计算仍有相同适用范围。历史分钟source integrity可标 `PREVIOUS_INDEPENDENT_SOURCE_VERIFIED_UNCHANGED`，但真实时点深度、用户执行金额、实际成交和持仓/费用均仍`UNKNOWN`。

## 审核批准不改变真实业务NO_GO

这只是**原有曝光305条历史价格代理聚合器代码审核**。新184个价格信号6h毛价中位负、24h毛价中位−2.446%；24h均值+3.727669%主要受几笔极端赢家驱动，前五赢家贡献184条正负抵消后的收益率求和约92.18%（不是所有正收益之和的比例，后者约36.13%）。模型剔除原27个D1早5分钟2×标记中的11个，16/27=59.26%，且六历史日期24h毛中位仅1/6为正。上一轮曾独立复验的全部305事件不是未知日期OOS；无真实成对PIT完整L2可成交净收益案例、发信时间戳和实时买卖盈亏。**不会借此次局部APPROVE改写阶段业务模型REJECTED**。

门禁固定：`G0=PARTIAL`、`G1=NOT_SCORABLE`、`G2/G3=NOT_PASSED`、`G4=UNKNOWN`、`G5_FULL_RELEASE=NOT_PASSED`、`G6=NO_GO`、`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，`Frank=UNCHANGED`，Stage99 `STOPPED`、`NO_NEW_SCHEDULE`，用户手动行情采集参考日Oct28/Nov11，Stage140首次前瞻 publisher+48h buffer参考Oct24 01:00 Bangkok且需要用户明确聊天指令。

## 自本次批准后停止Stage151/152同类修补循环

用户真实目标是全市场早期WATCH正确、不遗漏、不过时，实盘前净利润真实可评估。完成Stage152代码闭环后应切回主线：
1. 冻结保存现有原D0、Stage80 D1、Stage137/138发布方因果回放及其完整旧窗口失败结论，**不改变现有入场模型或根据旧样本挑幸存阈值**。
2. 按 `MONSTER_V4_MODEL_AND_LOCAL_ARCHITECTURE.md` 回到真实全市场 D0 发现与持久化D1队列，优先核实原旧阶段中98个并发WATCH是否仅有每轮8次深查/15分钟TTL造成迟到，完整测出`WATCH_CREATED / QUEUED / ELIGIBLE / FETCHED / D1_EVALUATED / LATE / USER_DELIVERED` 的因果时钟和全分母。
3. 决策前留档实际重放证据、已发生的漏报，确定能否在**无额外API超限**及不减少WATCH覆盖下解决重大时效问题，不能无数据武断加大限额或改异动阈值；通过本地真实离线复验和其他AI review后再考虑Mac，不能把历史后验信号当未知向前证明。
4. 本地正式运行与邮件仍按安全关口顺序排队，禁创建GitHub schedule/ChatGPT Automation/launchd。

本报告随原PR同branch只增加文档，不使既有审核源码SHA失效。
