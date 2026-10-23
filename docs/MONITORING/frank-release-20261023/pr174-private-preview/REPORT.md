# PR #174 — MAC_D2_PRIVATE_OFFLINE_PREVIEW_PASS

真实Mac、真实已保存私有原始回执、零RPC离线预览验收。按[完整规则](https://github.com/lxxlx2/ChatGPT_mission_record/pull/174#issuecomment-6368741580)执行；[固定代码独立APPROVE](https://github.com/lxxlx2/ChatGPT_mission_record/pull/174#issuecomment-6368672240)。

## 固定环境与原始CLI

- 产品SHA：`a14846f16e68fd0899ab5506d8c2f0c91272df48`，开始/结束PR174 HEAD一致。
- 原始回放PR60 SHA：`e4529ba7069e5499d12323a7160ceac08c481fae`，实际PR60 HEAD一致。
- 两个独立clean detached checkout；完整local-agent Git字节核对分别441/457文件。各规范清单摘要见integrity-sanitized.json。未改产品、原始renderer、输入raw或approved replay代码。
- 使用10月23日既有原始bundle，manifest SHA256 `f06df53ccfb8b96e1b92f428620311cf62bd6bb44f9b83fd7e126f2ee5b1f88b`。没有重新采集或修补源。
- watchlist复用既有保存的原始GET响应：1355行，`READ_ONLY_FORWARD_SQLITE`，更新时间 `2026-10-23T10:15:57+00:00`。复制到本次私有目录后SHA一致、文件0600；这只是历史本地模型/活动观察，不是新余额证据。本轮连localhost Dashboard GET也为0，未直接读生产SQLite。
- 真实原始CLI `python3 -B scripts/frank_d2_owner_preview.py --pr60-checkout <固定独立PR60> --bundle <既有私有bundle> --watchlist-json <既有响应私有副本> --output <canonical Git外私有新文件>` 执行一次，**exit0**。真实隔离child调用原始PR60 `replay_owner_full_receipts`，不是合成fixture替代。

## 来源、余额和状态

|项目|实际结果|
|---|---|
|SPL Token|1875账户；finalized slot460482174|
|Token-2022|2273账户；finalized slot460482176|
|合计|4148账户、4148不同Mint|
|原始采集UTC|2026-10-23T14:46:32.787921+00:00|
|原始采集曼谷|2026-10-23T21:46:32.787921+07:00|
|渲染时年龄|3525秒，明确是生成页面时的年龄，不是持续更新时间|
|快照语义|两个独立finalized slot，same_slot_atomic=false；current balance verified=false|
|目标32|32/32均有账户；8非零、24零，与审核来源一致|
|汇总检查|全部4148个Mint的raw整数合计与各自所有Token Account行复算一致|
|真实多账户样本|本组0个Mint含多个账户；本次不能宣称真实样本覆盖该分支。既有合成多账户测试已独立审核，不重复跑来替代实机事实|
|观察池外Mint|2794（针对上述保存watchlist时点），不可当实时池外数量|
|默认200行|176 NONZERO_AT_SLOT、24 ZERO_AT_SLOT，含40个池外样本|

没有Token Account pubkey嵌入HTML，真实完整账户明细仍在私有源。独立用同一真实源和同一render-time复算projection/HTML，原始CLI产物逐字节相同；并检查所有USD/PnL均未核实、current_chain_balance_verified=false。

原始200行内有2行同时呈现非零点位余额与CLOSED或SELL本地历史列，列间未互相覆盖或推断清仓。真实保存watchlist另有1个Mint在完整program源中没有账户；它未进入按优先级截取的原200行，因此**没有虚报其实际浏览器行覆盖**。仅对同一真实源作内存投影核对：该Mint状态是NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS，raw/quantity均None、不是0；没有另生成/改写HTML。浏览器实际显示“不存在账户不等于零”的说明。

## Chrome真实验收

已有Google Chrome **155.0.8059.86** / Playwright，headful独立临时profile，仅打开真实私有HTML的`file://`页面，无HTTP fixture、无生产服务。页面原文件未修改。

|检查|结果|
|---|---|
|标题/真实渲染|PASS，Frank D2 本地余额证据预览|
|行数上限|PASS，实际200行|
|UTC/曼谷/生成时年龄|PASS|
|双slot/非原子/不是自动更新实时仓位|PASS|
|2794池外总量/40条池外样本|PASS|
|Mint精确搜索|PASS，本地查询匹配1行（不公开查询Mint）|
|NONZERO_AT_SLOT子串搜索|PASS，176行|
|无匹配/清空|PASS，0行/恢复200行|
|收益和市值|明确“未核实”，无虚构金额/收益|
|console/pageerror|均0|

**测试脚本一次有界纠正，原记录保留：** 首轮脚本误把ZERO_AT_SLOT查询假定为精确状态匹配；原始产品明确是textContent子串搜索，因此它也匹配NONZERO_AT_SLOT，共200行，导致测试AssertionError，浏览器本身无异常。没有修改产品、HTML或删去检查；纠正为验证实际子串语义，并增加NONZERO_AT_SLOT=176行检查后，一次浏览器补跑通过。原始CLI仅运行一次，原始HTML哈希始终不变。browser-initial-test-result.json保留首轮脚本结果；最终browser-sanitized.json是完整通过记录。该匹配行为不作为阻断缺陷扩大开发。

## 网络与私有输出保护

- 本轮**REAL_RPC=0 / PRODUCTION_REQUESTS=0 / PRODUCTION_DB_WRITES=0 / NEW_PRODUCTION_SERVICE=0 / REAL_NOTIFICATIONS=0 / REAL_TRADES=0**。
- CLI原始child禁用socket连接；CLI不自取watchlist，不调用RPC/DB/import。
- Chrome路由只放行唯一私有file GET，其余资源请求拒绝；外部域名DNS禁用，浏览器背景请求走本地deny-only代理，永不转发外网，不仅依赖CSP。
- 最终浏览器运行记录1次PRIVATE_LOCAL_HTML本地GET、10次背景意图被拒绝（1 HTTP、9 CONNECT）、外部转发0。首轮相同禁止机制；原始失败记录明确不是网络成功访问证据。未打开外部链接或提供商接口。
- HTML实际41642 bytes，SHA256 `ee938eb1fe6a3e526d51e0824a6c7fc259ab45efd813df840aa5b6b534a9facf`；新建Git外canonical目录0700、HTML0600，原CLI O_EXCL创建，未覆盖已有文件。未重跑已批准的文件系统负测试。
- 没有采集真实余额截图，不公开HTML、Mint列表、单Mint余额、Token Account明细、原始回执、私有绝对路径或凭据。公开的JSON仅含聚合/布尔断言、源码及原始文件SHA。

## 完整性、清理与结论

原始manifest/SPL/Token2022回执hash前后完全相同，见integrity-sanitized.json；真实HTML前后哈希相同；当前正式Dashboard已安装437个源文件前后均一致。未修改Dashboard/V1/MC Loop、通知策略、控制文件或生产数据库。

两次临时Chrome均关闭、profile删除、deny代理关闭且lsof读回无监听；没有fixture或其他后台服务。两个本轮detached源checkout在clean、无ignored/untracked文件后已移除。仅保留Git外私有HTML/输入副本，未Git-add私有文件。

结论 **MAC_D2_PRIVATE_OFFLINE_PREVIEW_PASS / D2_PRIVATE_SOURCE_PREVIEW_ACCEPTED**。这是固定源/代码下的离线私有预览通过，**不是生产Dashboard接入、Issue165关闭、实时持仓或完整钱包估值通过**。下一阶段仍需单独D2接入设计、审核与授权；本轮结束，不部署、不merge、不新增RPC。
