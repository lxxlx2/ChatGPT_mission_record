# Frank 通知顶部历史积压 + Gmail 实际收件对账（2026-10-22）

状态：`GMAIL_OBSERVED / LOCAL_DB_ROW_BY_ROW_NOT_YET_READ / UI_BROWSER_ACK_IMPLEMENTED_IN_DRAFT / PRODUCTION_CURRENT_SOURCE_UNCHANGED`。

## 问题及事实

Mac 正式 8766 页面右上角：`历史过期拦截 15（邮件 15，本地 0；数据库无发送尝试记录）`。此数字来自现有 `mission_control_health()` 的**只读** control SQLite 统计：

- `decision_outbox.status in ('MANUAL_REVIEW','SENDING','SENT_UNVERIFIED')`
- 关联 `gmail_delivery`、`local_delivery`，调用 `summarize_manual_reviews()` 分类。
- `gmail` 计入历史拦截：`outbox.status=MANUAL_REVIEW`、`last_error=GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND`、outbox attempts=0、Gmail attempt_count=0、gmail status MANUAL_REVIEW、没有 sent_at 和 gmail_message_id。
- 对 `local` 同理使用 `LOCAL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND`、attempts=0、无 delivered_at；不符合严格条件的仍进入 actionable 或 pending，不能借归档规避。
- 每 5 秒通过 `/api/control-health` 重算，**不会随着 Gmail 收到邮件而自动扣除**；该分类不代表 Gmail Sent 实际反向核查通过。不应解读为“总共有15封邮件都没发”。

## Gmail 2026-10-01 至 2026-10-22 已检索的相关真实邮件

通过用户已连接的 Gmail 搜索并读取各邮件正文与 `SENT/INBOX` 标签，排除 GitHub workflow 通知及日报：

| 来源类型 | Gmail 匹配 | 观察事项 |
| --- | --- | --- |
| 原 V1 多倍信号 | 两封正式 `[Frank 多倍信号]`：10-11（代币前缀 `2j5SaS7`）和 10-21 08:29（`nxPqZ4F7`）；另外有两封 `TEST/HISTORICAL TEST` 不计入正式邮件 | 与发布时 V1 `gmail_sent_verified=2` 数量一致，**不能只凭数量替代 sender message-id 回读核对** |
| MC 旧式决策邮件 | 八封 `[Meme提醒]`，时间 10-08、10-12、10-16、10-20、10-21（含多封）、10-22。包含 `WAIT/NO_FOLLOW/SMALL_BUY` 等建议 | **不同于**15条历史过期拦截，不能和它们互相抵扣；尚未按数据库 decision_id 逐条匹配 |
| 旧 MC 不符合当前用户要求 | 10-21 的 `nxPq` 邮件明示「小仓跟」，其他旧 MC 邮件出现「决策时 $30 报价」 | **P1 产品/通知范围风险：旧 MC Loop 仍在使用原有策略和运行程序，2026-10-22 Dashboard-only 切换没有修改该 Loop。不能因此宣称这些旧内容已停用** |

所有邮件存在 Gmail 中，此仓库**不写入** Gmail 邮箱、私人地址、完整 CA、私有内容、邮件 ID 或 token；不以这份脱敏汇总认定任意一条 `MANUAL_REVIEW` 已经邮件发送。Gmail 中 `SENT/INBOX` 是邮箱读取到的标签，不代表每条本地 outbox 的 deliverability 证明。

## 已提交的无写入收起功能（当前仅 Draft）

- `summarize_manual_reviews()` 额外计算 **严格符合历史过期且无尝试的 decision ID 集合 SHA256**，不暴露原 ID；缺少任一 ID 时不提供按钮（fail-closed）。
- Dashboard 顶部提供 `收起已过期历史` / `查看`，以 `localStorage` 保存当前这一批 fingerprint。刷新和重启浏览器仍可收起；**若集合改变而人数不变，也会重新展示**。
- 只是当前浏览器“已看过”的展示状态，不是跨设备/跨浏览器全局归档，不改变 SQLite/outbox 任何状态，**不增加发送权限**，也不触发重试，不等于清空 15 条数据库历史。
- `SENDING / SENT_UNVERIFIED / actionable` 分类保持醒目，任何未核送达的邮件不允许在此收起历史逻辑中被视为已清理。
- 当前生产 8766 仍在固定产品 SHA `31dd598df248ca15f731913a5cbf82e88b981874`；需要独立 SHA 审核、测试与单独 Dashboard-only 安装批准，新 Draft 功能不能自动进入生产。

## 真正“清理历史积压”的后续验收门禁

1. 在 Mac 本地只读读取完整 `decision_id + channel + status + attempts + last_error + gmail_attempt_count + sent_at + gmail_message_id + delivered_at + content_hash + decision_time` 的 15 行，**只本地**与真实 Gmail 邮件中的 `Mission-Decision-Identity/Message-Id` 进行匹配；不能把一封 V1/MC 成功邮件冒认为这15条中的任何一条。保留哈希/聚合审计。
2. 若结果仍证实 15 条仅在首发前过期、没有发送尝试，则设计**独立的历史归档索引**并改变 Dashboard 查询视图以区分 `未归档` 与 `已归档`。原 `decision_outbox`、`gmail_delivery`、`local_delivery` 中的事实与状态不得删除/重写；保留恢复、审计及查看入口。归档不得让 Loop 再次尝试发送。
3. 对本地源数据不完整、已投递记录或待核真实发送结果绝不能执行自动归档；保留 `PENDING/UNVERIFIED`。任何正式 ControlDB 写入和上线必须另行授权，先备份与 dry-run + 精确 diff + 第二 AI 审核。
4. 同时单独调查**旧 MC Loop 仍在产生带 $30 报价/小仓跟邮件**的路径，与用户“不要默认买入额”的原硬性要求对齐。只读调查可做；如需停止/切换 MC Loop 或关闭其 Gmail 通道，必须另行取得该特定生产操作授权，且不得重启 V1。

**不要**用本功能作为“P5 智能风险通知已上线”的证明。旧 V1 保留，P5 新智能提醒仍处于设计/假发送阶段。
