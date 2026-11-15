# Frank 用户评审意见逐项核实与最小修复（2026-11-11）

结论：五项具体意见中，2项有可执行反例并已修复；3项所称守门穿透/全局精度泄露未复现，保留现有证据范围语义。固定新产品并已安装`d43878828c86eacee5be9df8a17d16fc63a74bb6`，parent`0b966ab459b775bc58c77427c1dbcb491f2d9bf8`，PR220 base`4fdf2238a4db2347975689913e49142b760dc091`。免独立review，不宣称独立APPROVE。完整CA需求仍PARTIAL，INVEST_NO_GO / TRADE_NO_GO保持。

[机器回执及完整实际命令](./evidence/frank-review-claims-resolution-20261111.json)保留输入文本hash、逐条判定、反例与分层证据。用户粘贴报告的运行描述本身不作为通过证据；本轮重新执行验证。代码与测试在原PR220，运维/回执在原PR242，均不合并。

| 评审意见 | 实际判定与处理 |
|---|---|
| 非列表批次引出第二个长度错误 | CONFIRMED_FIXED。保留缺失/非列表值；shape与length互斥。None、字典、字符串各自仅保留原始shape错误，真实空列表仍记长度不匹配。Token与Owner两阶段8例覆盖。该缺陷影响诊断精度，不将其夸大为已证明财务状态损坏。 |
| RAW优先preview属于守门穿透 | INTENDED。RAW是原始token账户金额比例，Owner解析缺失不应缩小已知原始Top10。显式Mint/同slot金额矛盾仍在最终门禁撤回全部比例。 |
| 无slot错误未传播导致全量假完成 | 嵌套COMPLETE观察可复现，但守门穿透未复现。真实缺program/未初始化/不可用profile在GPA前即拒绝；独立GPA已通过自身同slot供给/Top20对账时保留它自己的完整快照，同时Top20错误、最终比例撤回及总体INCOMPLETE_EVIDENCE保持。无slot不能擅自归属于独立证据的bank。 |
| 阅读时间被强迫晚于链上报告 | CONFIRMED_FIXED。允许真实阅读在报告前或后，保留publication≤capture≤now+60；任务/Mint/原报告hash/原引用URL/作者/文本hash边界不改，不重写真实时间。API和前端分别覆盖提前1/300/86400秒。 |
| KNOWN样本数值冒充排LP全局Top10 | INTENDED。明确标“已解析样本”，严格EX_LP/GLOBAL仍门禁。构造样本14.4%、真实全局15.2%的反例时，系统仅保留样本14.4%，严格值UNRESOLVED、总体INCOMPLETE_EVIDENCE。 |

关键修复源码：[批次上下文](https://github.com/lxxlx2/ChatGPT_mission_record/blob/d43878828c86eacee5be9df8a17d16fc63a74bb6/crypto-300-profit-mission/local-agent/mission_agent/meme/cluster.py#L972)、[浏览补证时间](https://github.com/lxxlx2/ChatGPT_mission_record/blob/d43878828c86eacee5be9df8a17d16fc63a74bb6/crypto-300-profit-mission/local-agent/mission_agent/mission_control/narrative_supplement.py#L99)、[前端边界](https://github.com/lxxlx2/ChatGPT_mission_record/blob/d43878828c86eacee5be9df8a17d16fc63a74bb6/crypto-300-profit-mission/local-agent/mission_agent/mission_control/static/app.js#L1645)。可独立运行的新增回归：[批次错误](https://github.com/lxxlx2/ChatGPT_mission_record/blob/d43878828c86eacee5be9df8a17d16fc63a74bb6/crypto-300-profit-mission/local-agent/tests/test_meme_top_account_context.py#L131)、[真实前置阅读](https://github.com/lxxlx2/ChatGPT_mission_record/blob/d43878828c86eacee5be9df8a17d16fc63a74bb6/crypto-300-profit-mission/local-agent/tests/test_narrative_supplement.py#L265)；前端回归在同提交test_frank_ca_report_render.mjs。

父版使用固定新测试及独立PYTHONPATH、`-c /dev/null`隔离pytest工程路径后，11例9失败/2通过；候选相同11例均通过。固定候选完整本机相关385 Python/220 Node通过。父版另外执行67现有排名/Top20测试、5新构造排名探针、5前端语义检查，以及47全量/Top20测试和4真实profile/holders/GPA路径探针，不替换收集函数制造不可能状态，无网络/监听。

既有Nov10捕获在新HEAD两次各978读取禁网回放，业务报告严格等值；752观察、20代表、732压缩、11身份与游标/去重核对不变。不是新鲜来源或真实重启续采。Push CI [42986392137](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/42986392137)及PR CI [42986401895](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/42986401895)各2264 Python/4skip、220 Node、42合成浏览器检查成功；PR生成合并测试SHA`7bd3bb675b9d46604976b2101335b5771d7f234e`，不代表执行Git合并，CI不是Mac实测。

固定执行器`9ae971f0252afe232c4df1a0d5c9e8d182066ae8`已发布/API读回，495旧源码、46报告、3 SQLite一致备份/integrity/FK、14保护哈希（前13加现有补证）及旧新实际Handler无监听预检后，仅重载Dashboard原8766。现有补证不改写，Scanner身份/代码不变且LIVE/无漂移/0错误，Loop未加载，回滚未实操。Chrome既有补证/原时间、原任务GET、刷新与有限样本/证据不完整提示通过并留页。提前阅读用例的实际证据层是单元/API及DOM/VM，没有真实“先读后新建链上任务”的来源样本；不把Chrome旧报告冒充该新场景。

第一份概览另须纠正：0条已核验金额匹配双边报价不等于752格已证明不可行；GPA429具体方法/路由门禁仍未知；hash绑定不等于官方认领或来源真实性证明；cluster.py实际在mission_agent/meme，现有RPC已有有界退避/冷却。本轮不做无反例的大范围格式重排或新增节点轮询。

本轮真实RPC/CA POST/通知/签名/交易0，不新增来源/端口/付费/key/监控自动任务。最近真实来源仍为Nov10任务，免费阶段2180不变、原一次572单列。全Mint、完整经济历史/首买、全部特殊身份、独立受控快照及代表样本缺口保持；原10月故障归因按用户取消。原始响应、截图及含私有路径日志留Git外。
