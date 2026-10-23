# PR #178 — MAC_SYNTHETIC_CHROME_PASS

一次有界真实Mac隔离**合成源**Chrome验收，固定产品SHA `ea9a7715beb4d2a55ae956bf993828cbddcb50e5`。[独立APPROVE](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6371694115)；[验收合同](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6371753576)。用户在执行聊天明确确认开始。此报告不是原始私有余额验收或生产上线。

## 固定环境

- 开始/结束PR HEAD均为固定SHA；新detached checkout运行，原工作区未切换或修改。Git原始local-agent全部源文件字节匹配，清单摘要及静态三个文件SHA256见setup.json；测试前后静态哈希一致。
- 真实Mac，已有Chrome `155.0.8059.86`，独立临时profile；没有安装依赖，OS版本见browser-result.json。
- 127.0.0.1随机端口 **64103**，从未访问8766或8765。
- 未修改原始index.html/app.js/styles.css。fixture只为静态文件与其他无关API提供合成/不可用响应；D2通过原始 `Handler.do_GET`、原始同源/参数校验、`query_d2` 读取真实临时私有文件。
- 没有实例化DashboardState、FrankReader、ClusterJobManager、生产SQLite、scanner或loop。fixture进程socket outbound连接被拒绝；没有实际Alchemy/Solana RPC环境配置。
- 合成源由仓库 `test_frank_d2_owner_at_slot.source()` 与真实 `build_d2_document_from_verified_pr60_replay` 构造。扩展为213 Mint/214账户；其中一个Mint含两个合成账户，以超JS安全整数的raw检验小数展示。所有地址/数量均为fixture，不来自私有回执。
- 来源临时目录位于Git之外，0700；指定basename合成JSON0600。测试过程中只改fixture数据文件模拟未导入/拒绝状态，没有改产品函数、fetch或renderer。

## 实际8组PASS

|组|实际结果|
|---|---|
|初次加载|未读取；D2 GET=0。无自动加载、轮询或扫描。|
|来源不存在|显式点击后SOURCE_NOT_IMPORTED；未知、不能按零处理。|
|合法多账户与精度|100条首屏；双账户Mint精确显示`1234567890123456.789012345`枚，账户数2，本地CLOSED/SELL仍是独立历史列；API含UTC/曼谷时间与双slot460482174/460482176，页面明确按时点、非原子、美元/盈亏未核实、非自动持续核验。|
|分页|实际100/100/13，页码1/3→2/3→3/3；首尾及中间prev/next禁用状态正确；返回上一页成功。|
|精确查找/零与缺失|查询首100行外的完整合成Mint找到1条零余额；精确查询后分页按钮禁用。另一个不存在Mint显示无活跃账户且“不是余额0”。|
|输入/HTTP同源|无效UI Mint不发请求；非法page、Mint、组合query返回400；缺定制头、异Origin、cross-site头返回403。负向HTTP请求由测试执行器发往同一随机fixture，不是外网或生产；浏览器正常读取也确实发送原始定制头。|
|两项P2拒绝|重算自hash后夹带1000条coverage私有标记仍SOURCE_REJECTED，rows空且无coverage回显；全局和214不变但程序小计0/214与实际213/1冲突也拒绝。未改变自hash非认证的信任边界。|
|迟到响应|实际原始frankD2Read先发A，fixture延迟A；再发B并读到ZERO，释放A后观察200ms，B表格、状态、输入与按钮均未被旧NONZERO替换；服务器账本含两次合法返回。|

竞态测试边界：正常UI会禁用读取按钮来防止并发，故重叠请求通过Chrome内直接调用**原始frankD2Read函数**制造；不是声称两个禁用按钮可以真实点击并发，也没有替换原方法/DOM/fetch或改变产品行为。其余页面流程均实际fill/click。没有重复执行单元测试或原始钱包采集。

API分页之外没有全量账户清单回显；原始raw仍为字符串，没有转成JS浮点。每次读取显示的是响应时的数据年龄，不是永久实时余额。UI主要显示曼谷时间，UTC也在原始API返回中核实；没有声称UI同时列出了两种时间。

## 安全与请求账本

- 浏览器console warning/error及pageerror均 **0**。
- 最终Chrome记录12次背景连接意图（1 HTTP、11 CONNECT），全部被本地deny-only代理拒绝，没有外网转发。页面请求路由只允许fixture origin的GET/OPTIONS，其他请求被拦截。
- D2及其他API的脱敏HTTP状态/响应行数/coverage字段记录在http-ledger.json；浏览器请求另在browser-result.json。截图仅显示上述公开的合成fixture，无真实持仓数据。
- `REAL_RPC=0 / PRODUCTION_8766_REQUESTS=0 / REAL_CA_POST=0 / REAL_NOTIFICATIONS=0 / REAL_TRADES=0`。
- 没有读/导入真实Oct23私有raw或完整Mint列表，没有凭据、生产数据库/控制目录、真实后台服务或付费API访问。没有POST发出。未操作Dashboard/V1/MC Loop、launchd、通知策略、交易金额、merge或部署。

## 清理与结论

唯一fixture进程经过命令身份/UID核实后停止，64103的lsof监听读回为空；Chrome/context关闭、profile删除、deny代理关闭且端口无监听。合成source目录和文件已删除；本轮source checkout在clean、无ignored/untracked后清理。证据分支与产品固定SHA分开，仅提交脱敏报告/JSON/合成截图，没有永久harness加入PR178或新功能PR。

**MAC_SYNTHETIC_CHROME_PASS / D2_SYNTHETIC_BROWSER_ACCEPTED / PRIVATE_SOURCE_NOT_IMPORTED / PRODUCTION_UNCHANGED**。

固定SHA已完成此次合成源浏览器门禁；这不是实际余额导入/生产切换授权，不是Issue165全部结项、完整CA准确性或钱包估值证明。停止本轮；真实源导出/导入与正式Dashboard-only上线仍需单独授权。
