# Monster Spot511 D1→D2：Codex 独立 APPROVE — 微秒回执 P2 已关闭

**记录日期**：2026-10-25。**复审固定源码 SHA：`c4a8f1e701b3a34d404db6f352d7b02591ce65c1`**。范围仅限 D2 HTTP 回执时钟微秒比较修复；不是 Monster 全模型、交易可执行性或部署批准。

## 独立复审来源与核验主体

用户带回的独立审核主体为**Codex 主代理**，底层具体型号 **UNVERIFIED**，没有委托其他代理。实际执行环境：用户Mac，macOS 27.0.1 arm64，Python3.14.7，针对固定SHA独立detached只读工作区。本报告是用户带回的外部审核结论的忠实登记，不冒充Codex在GitHub签名评论或本助手在用户Mac运行。

对照被拒绝源码 `342fc476a49c25640e6c8c47302338b56c69316a` 的唯一P2：旧 D2 将 `2026-10-18T10:40:00.000001Z` 的真实来源回执向下截断到`10:40:00.000Z`，使其相对信号时间`10:40:00.000000Z`错误成为“已收到”而非NOT_YET_RECEIVED。

Codex 本轮独立确认新代码基于 UTC aware `datetime` 的 `delta.days/seconds/microseconds` 做**整数微秒**计算，无浮点`timestamp()`或过早ms截断；WATCH/D1的整数毫秒乘1000，回执实际微秒精度不丢失，180000ms工程时间阈值同比放大。现存`archived_quote_available_at_client_receipt_ms`仅展示向上取整(`CEIL_ONLY_DISPLAY`)，实际分类不读此显示字段。

### 真实独立测试范围

- 亲自运行D2桥13项及Stage163原12项，合计**25 PASS，0 FAIL/ERROR/SKIP**。
- 另**12项完整`analyze()`路径的独立时钟边界**：分别对WATCH/D1各测相等、回执晚到1us、早到1us、年龄恰等于180000ms、超过阈值1us、阈值内1us。全部符合预期。
- GitHub [#40213575043](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40213575043)原日志 13+12=25、SUCCESS、运行 SHA 与`c4a8f1e...`一致。
- 独立读取原研究V2 `real69.json` + Stage163原始ZIP/回执，调用本固定版本`run()`实际复算，JSON解析结果和新Artifact `12606896190`完全一致；与上版Artifact `12599195855`逐事件对账：69 WATCH的ID、symbol、时钟与分类完全一致，47 D1 SETUP的时钟/身份/类别一致；回执分类 **69 WATCH STALE、47 D1 STALE、22 NO_D1_RESEARCH_SETUP**；`can_confirm_g4=False`、无实际成交/退出/净收益。
- 真实Stage163的HTTP回执`2026-10-17T22:04:46.929464Z`对应精确整数微秒 `1792274686929464`；新安全显示毫秒`1792274686930`。V1/V2输出新增精度与schema字段，**字节应不同**。
- 本增量范围**未发现新可操作P0/P1/P2**，上轮微秒P2为**CLOSED**，结论 **`APPROVE @ c4a8f1e701b3a34d404db6f352d7b02591ce65c1`**。本次没改已获批的D1 V2或real53比较器，没读用户生产DB、没进行新采集、部署、发信或交易。

## G0–G6：受限批准，不升级整体门禁

- `G0 PARTIAL`：原单次来源/报告一致，不证明所有4,599发行方源的独立外审、动态Listing、历史账户交易资格或当时盘口完整。
- `G1 NOT_SCORABLE`、`G2 UNKNOWN`：未来三段真实前瞻窗口未成熟，旧十月历史不可重打OOS。
- `G3 EXPOSED_NOT_PASSED`：真实研究原47/7=6.71以及40/7=5.71普通crypto类型阳性都超过5/day上限。
- `G4 UNKNOWN`：历史T0旧L1书面BBO并非后面WATCH/D1当时的可用买卖深度和真正退出Bid；0充分证据≠0可交易币。
- `G5 D2_MICROSECOND_PATCH_APPROVED_ONLY`：本修复独立通过；与先前`d743acb...` D1 V2代码局部APPROVE分开登记，不能称Monster整体G5 PASS。
- `G6 NO_GO`：不合并、不部署、不创建自动化、无真实Monster Gmail/交易、无新RPC，不动Frank与Mac。

下一项有价值的工作是预注册ADR-005的**2026-11-02、11-16、12-01**三段独立UTC七日窗口的前瞻数据取得条件，而不是继续审核已经CLOSED的微秒补丁。来源真实当时T0证据不在场，须明确`G0_POPULATION_UNKNOWN / SOURCE_BLOCKED`，不能日后根据价格赢家反填市场清单。参见[ADR-005](../adr/ADR-005-spot-d1-btc-relative-confirmation-preregister-20261024.md)。
