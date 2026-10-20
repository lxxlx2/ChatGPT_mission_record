# Frank Option 3 — D2 钱包买卖与风险观察主线（2026-10-20）

## 当前已得到的实际 Mac 证据

- 用户对独立 QA 版本 `afe06caa93c284860ce01bb195e8a1bdef43f53f` 执行 `5/5` 定向标准库测试，`LOCAL_HTTP_SMOKE=PASS`，提供两个实际活动/旧信号页面截图及独立历史回放截图。**只证明隔离版本**；PR 正式集成代码尚未实机跑过。
- 来源：运行中的**旧 Frank 本地索引 8766**，启动时读取一次，`source_scope=LOCAL_INDEX_ONLY`，`source_chain_complete=false`；100 条不同签名、46 个币种；41 买类、59 卖类，其中 `SELL_POSITION_UNRESOLVED=25`。
- 原已审核 PR #146 智能分析仅从 `FrankReader.candidates()` 生成卡片，当前 Mac 共 5 条候选。上述 59 笔卖类中 **46 笔对应币种不在当前候选集合**。这是真实的覆盖缺口，不是“漏掉链上交易”，因为既有 `/api/trades` 已收录它们。
- 最近一次先源信号后同 episode 卖出核对：过去 60 天内找到 5 条真实生成的 V1 信号、0 条按现有本地严格规则能证明与其同轮次后续卖出；不得把任何普通卖出包装为“以前已通知的清仓”。

## 本轮用户价值目标与最小范围

在正式 Dashboard 的 Frank 智能分析附近加入一块**独立本地活动观察**，使用户直接看到其他币种已索引的卖出和不确定仓位，不必在旧买入候选里寻找。复用已有 `FrankReader.recent_trades(100)` 和 `candidates()`，不新增 DB schema、RPC、通知、规则、默认下单额或原 V1 信号扫描。

新增 `GET /api/frank-activity-watch` 和紧凑的筛选 UI，默认显示卖出类、每次最多 15 条，支持按卖出未定/买入/全部以及 CA/签名本地搜索；可从本机既有来源主动重新读取。显示：索引行为类型与时间、CA 复制、Solscan 签名链接、当前候选是否存在同 mint **仅供研究**。不能推断原买入提醒是否发出/送达、当前完整链仓位、退出后是否余额为零、利润、买入金额或能否跟单。

`SOURCE_UNAVAILABLE` 要显式展示不可用，不能写成 0 条交易。缓存和显示以接口当前读取为准，不声明“实时覆盖完整链”。PR #146 中原 ACCUMULATION/MULTIPLE/REENTRY_WATCH 提醒、`/api/frank-intelligence`、原跟单/CA 查询和传输程序保持不变。

## 交付条件与停止规则

1. 固定代码 SHA、确认新 PR 对 #146 是**最小四/五文件差异**，没有改 production policy、邮件、outbox、交易执行与旧扫描器。
2. 由 GitHub Actions/隔离环境运行新增源事实测试、原有 Dashboard 回归；按精确 SHA 进行一次独立代码审核。没有测试证据就标 `CI_UNVERIFIED`。
3. 在非生产的 Mac 隔离端口验收界面：确实显示“卖出类约 59，其中当前候选外约 46，仓位未知约 25”的事实。数字必须以来自实际新快照的输出为准，不对新环境预设这些为固定常量。原旧版本 Mac 结果不能冒充本产品 PR 的验证。
4. **停止**重复 P4 10 条回放与历史信号采样；只修对上述核心用户功能造成阻断的缺陷，非阻断 UI 微调以后处理。
5. PR 仅为 Draft、未合并，部署/切换/重启/新提醒/生产 DB 写入/交易等全部 `NO_GO`，需独立用户审批。

## 状态

`D2_READONLY_ACTIVITY_PRODUCT_INTEGRATION_IMPLEMENTING / MAC_NEW_PR_UNVERIFIED / ORIGINAL_V1_FROZEN / NO_DEPLOY`。
