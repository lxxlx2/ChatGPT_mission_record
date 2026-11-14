# Frank 免费手动 CA：完成来源采集、本机安装与 Chrome 验收

日期：2026-11-14，Asia/Bangkok。原 PR252 产品源码 **2471467e53cb772202abcc7415b17c1f33defd59**，parent **e7df038fa2bcc1a49add0019fb9a35718beed3a0**，PR base **d43878828c86eacee5be9df8a17d16fc63a74bb6**；本轮总基线 **81bb338d967d09a9598894cb47976f4f1f994296**。执行器及完整复放工具固定于原 PR242 **3a32996a0187b697755a25fda01edefbd30deede**。用户已授权免费、本地直接维护、免独立 review；不宣称第三方 APPROVE，不合并、不通知/签名/交易，不恢复 Loop 或盈利研究。

**分层结论：代码与离线回归 PASS；本次真实来源原件和关系引用校验 PASS；本机安装与真实 Chrome GET 验收 PASS；完整尽调仍 PARTIAL / INCOMPLETE_EVIDENCE。INVEST_NO_GO / TRADE_NO_GO 保持。** [完整机器回执](./evidence/frank-free-source-end-acceptance-20261114.json)记录实际参数、哈希和分母。前一份[运行中阶段记录](./FRANK_FREE_SOURCE_END_20261114.md)保留当时时点，本记录取代其“尚未 DONE／候选待安装”状态。

## 本次真实结果

真实查询的生产者是 **e7df038fa2bcc1a49add0019fb9a35718beed3a0**。本机 2026-11-14 04:58:09 开始，14:09:11 完成，**33062.185 秒（约 9 小时 11 分）**，DONE、error=null。安装247后只读取这份原报告，未把它改写成247的新实源查询。

- 主 RPC 保留尝试 **57354**，第二来源 **3362**；检查点 **61761** 条逻辑读取：主 RPC 58395、第二 RPC 3362、market 1、independent_market 1、narrative 2。主缓存命中1078，主transport恢复失败计数37已包含在wire尝试中；最终无逻辑来源错误。客户端逻辑观测数不是其内部全部HTTP请求数。额外来源诊断18wire与正式查询分列，旧c90中断原件继续保留。
- **35/35 历史窗口均 PROVIDER_EMPTY_PAGE**，没有 PAGE_LIMIT。目标账户19窗口、63页、412条签名；资金16窗口、6073页、48392条签名。最长单窗口2763页；分页重复签名0。标准查询 wire_limit / seconds_limit / deadline_at 均null。服务每次容量、逐请求超时、错误恢复和游标/磁盘/哈希保护保留。
- 20个Owner的当前来源账户均已选择，19个适用账户已扫描，1个链上核实协议池不适用个人首买。12个账户为 CONFIRMED_ACCOUNT_COMPLETE，2个账户为 NO_MARKET_BUY_IN_COMPLETE_ACCOUNT_HISTORY，4个 CONFIRMED_BOUNDED、1个 UNRESOLVED，另1个协议池 N/A。这些声明只覆盖相应账户窗口。
- 当前57条分类不明观察是57个Owner/签名组合、57签名、5个Owner：多资产歧义24、消息键不含Owner29、交换证据不足4。5个受影响Owner仍为有界/未确认，没有污染其他Owner或升级为完整首买。**不能把不同采集时点的原298减去57，称为修复了241条。**
- 281条关系边：直接代币239、直接SOL10、未确认共同归集10、公共基础设施21、未确认共同签名1。249条直接边由原始成功指令支持，32条派生边由各自多证据支持；重复边/无效引用0。284交易、14资金、88归集记录的成功状态、主签名、blockTime已核对；业务键重复0，14笔资金均有原始System转账指令支持。关系边不等于共同控制或现实身份认证。

原报告 SHA256 **1a94b9d6f31cd48498000a0ac178aa0ec142b36abd329b6982679e3ce81cbb79**；检查点1182298112字节，SHA256 **17a9d275966a2ad9e0143d93d42d648926a7cff2e2875d77797eada681f00daf**。DONE marker、原任务ID/CA、dated/latest两份、精确GET内容已核对；GET序列化字节与文件不同，JSON值相同，不混称同字节。原件/账户/私有路径/截图不上传公共Git；公开摘要与哈希不能替代获准访问的本机原件。

## 独立来源故障已经取得实证修复

真实100/50账户请求HTTP403 / JSON-RPC -32602，错误体明确免费每请求最多10账户；10账户HTTP200。错误体SHA256 **4a415486afd1b9c752f9aad108905ce24ec906291b655c0424d2e249765ac13c**。现以10分批覆盖全部输入，没有增加总配额、付费、注册key或换UA。生产原UA本来有效，不能把历史未保留错误体的403全部归为此原因。

正式3362次第二提供方读取均成功，覆盖**33615项＝Mint供给1＋主来源枚举token账户33614**。33613项非空比较字段一致，数值/Owner/Mint差异0；2个账户两源原始响应均null，未写为余额0或推断关闭原因；未尝试0。读取跨2223.589秒、多个slot，仍为 NEAR_TIME_DIFFERENCES。地址全集来自第一来源，这不是第二来源独立全表枚举，也不是同slot原子快照。

新报告来源枚举33614账户、7925个非零Owner；无增发权限的跨slot供给夹逼通过。全局Owner Top10为58.8555%，已核实池/前缀排除后16.7068%，全表特殊身份归一化仍false。其他提供方的匿名GPA要求个人token这项访问条件未绕过，未购买或注册；官方已有免费入口的GPA结果不是两个独立完整GPA都成功。

## 实际运行的验证

产品247在固定源码上 **1044 Python passed /7.09秒，socket事件0；210 Node passed，failed/skipped均0；JS语法通过**。Python实际使用pytest.main，完整参数逐项保存在机器回执tests.python.args；没有把旧SHA测试迁移到247。实际Node命令为：

```sh
node --test tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs tests/test_frank_d2_ingress_ui.mjs tests/test_frank_ca_rpc_budget_ui.mjs
node --check mission_agent/mission_control/static/app.js
```

采集结束后，又分别用e7生产者和247候选从同一检查点**完整禁网复放61761条**，两者business_differences=[]、socket_events={}、secondary_verdict_frozen=false，原件哈希不变。没有冻结第二来源的结果来冒充复核。以下是实际命令参数，私有路径以变量代称；变量分别指向固定干净agent、原件目录和输出文件：

```sh
python -B crypto-300-profit-mission/meme/evidence/frank_source_end_capture_audit_20261114.py --agent "$FRANK_PRODUCER_AGENT" --expected-sha e7df038fa2bcc1a49add0019fb9a35718beed3a0 --capture "$FRANK_CAPTURE" --summary "$FRANK_PRODUCER_SUMMARY"
python -B crypto-300-profit-mission/meme/evidence/frank_source_end_capture_audit_20261114.py --agent "$FRANK_CANDIDATE_AGENT" --expected-sha 2471467e53cb772202abcc7415b17c1f33defd59 --capture "$FRANK_CAPTURE" --summary "$FRANK_CANDIDATE_SUMMARY"
python -B crypto-300-profit-mission/meme/evidence/frank_captured_edges_audit_20261113.py --agent "$FRANK_PRODUCER_AGENT" --expected-sha e7df038fa2bcc1a49add0019fb9a35718beed3a0 --capture "$FRANK_CAPTURE" --output "$FRANK_EDGE_SUMMARY"
```

初次全复放只因两个本机time.time()接收字段失败。已先发布工具修正并API读回，在严格枚举的本机接收时间路径内归一化，再完整重跑；不放行任何余额、slot、交易、身份、证据引用或判定差异。两次最终复放各2476个本机时间/间隔/端点标签路径不同，完整路径列表与原始失败日志留本机。工具的holder_binary时间语义为JOB_RECEIVED_RESULT_MAY_BE_CACHED_NOT_BLOCK_TIME，不能改写为链上as-of。

当前SHA的PR workflow列表为空。上述回归、全复放、本机Handler和Chrome分别记录，**CI没有冒充Mac或实源**。

## 本机安装和可见界面

最终安装247为真实干净detached release，507个tracked agent文件逐blob校验，原端口8766，Dashboard PID47976。更新前保留510个实际旧源文件、90个报告文件、3个SQLite一致备份及integrity/FK结果、14个保护哈希。旧备份/候选实际Handler无监听各读11个精确任务和1个绑定叙事补证，HTML/JS/CSS/D1/D2均通过；正式切换后再次HTTP读回11任务、静态字节、叙事补证、保护文件及Scanner状态。

仅Dashboard按已授权步骤重载；Scanner PID2268/code1f2c6afc28b9988eaacdc896562ff9a71b78f801仍LIVE、无漂移/连续错误0，Loop未加载。回滚分支未实操，不宣称已证明可回滚。部署和最终GET验收没有新RPC/CA查询，无新端口/监控/周期任务，无通知/邮件/签名/交易/合并或付费操作。

真实Mac Chrome强制刷新后，按原任务入口GET读回同一报告，任务编号和CA匹配；读取区间、33615项独立对照、20个Owner账户选择、35个来源结束窗口、分类缺口、首买状态和叙事均可见，标签页保留打开。浏览器调试器附着不可用时使用Chrome原生可访问性操作完成，未用fixture或另一浏览器替代。最终截图SHA256 **78f00d85d03afb2e123b5b0e978e2431877b1bae33b28ab86b7235385bcd7f74**；历史面板截图 **fb927400c378c8b91b7c94f70e095a507e62842da1714d880ac9728a28e16593**，私有保存。

## 剩余证据和使用限制

本轮来源采集、完整复放、候选安装和Chrome收尾均已完成，不再是“仍在等第18个Owner”或“独立来源完全不可用”。目前没有权限或review阻断。以下事实不足仍明确呈现，不把未知当失败，也不把运行结束当完整尽调：

1. 35个来源结束窗口不能证明已关闭账户全集、终身Owner归属或全钱包真实首买；57条经济分类歧义涉及5个Owner，继续保守。
2. 两源均null的2个账户、跨slot/37分钟对照、第二源未独立发现全集及池子原始储备的独立受控快照，仍不能写作全部通过。
3. 全部CEX/锁仓/金库/现实控制人身份、全表特殊身份及其他协议代表样本，没有被这个Token-2022/PumpSwap大账户样本穷尽验证。
4. 页面保留AI/模型训练、爬虫/智能体叙事、不可修改链上元数据、创建者链接帖子及引用链；exact CA认领、人物实际参与和全网最早起源仍UNVERIFIED。认领未证实不抹去有出处的叙事。
5. 约9小时11分钟的免费全量模式仍有明显时效限制。04:58行情不会因14:09完成而变成14:09行情；界面已明确读取区间，不能用本结果给出实时可交易或收益结论。

原10月故障已由用户取消，不重开。本轮关闭的是已授权的源码/真实捕获/本地维护验收范围，不恢复盈利研究、真实通知或Loop，也不为凑完整性继续新增来源、CA、监控、备用任务或无关PR。
