# Frank 历史分类缺口归因与Owner隔离修复（2026-11-13）

当前源码 `81bb338d967d09a9598894cb47976f4f1f994296`，parent/本轮基线 `9677da7d0b429a4a69fd270cd0097231e4713507`；原PR252继续开发，PR220固定d438仍是基础。原8766已直接安装干净detached checkout，503 tracked local-agent文件逐个Git blob核对。用户明确授权免费、本地调试/直接部署、免独立review；不宣称独立APPROVE，不合并、不启动Loop/盈利研究、不通知或交易。

## 原298条的实际归因

固定原报告SHA256 `2f1e663f8a47079609ffa1ad61c9dbe2359667aa48ead0706932390b4d8d4825`，属于Nov13曼谷11:24:34旧任务，不能把下面归因数当作后续新鲜查询计数。只读checkpoint与真实analyzer回放还原549次分类调用的实际Owner/账户/phase上下文，完整消费1529读取，不用“对每个签名随意尝试20个Owner”代替上下文。

298是观察记录，去重为271个Owner/签名组合、265个不同签名，涉及5个Owner；27条是相同Owner/签名重复观察。一个签名可出现在不同Owner上下文，不能混用分母。

| 实际原因 | 观察记录 | 去重Owner/签名 | 处理 |
|---|---:|---:|---|
| WALLET_NOT_SIGNER_AUTHORITY_UNPROVEN | 234 | 223 | 保留授权未证明，不把程序/委托流量强认作该Owner买入 |
| AMBIGUOUS_USER_EXCHANGE_ASSETS | 34 | 29 | 保留多资产交换歧义，不折成单目标精确成本 |
| WALLET_NOT_REFERENCED | 26 | 15 | 原分类器汇总为INCOMPLETE_CHAIN_METADATA；实际是Owner不在消息键中，非26次RPC失败或简单缺JSON，新增安全诊断但不伪造Owner签名/SOL数据 |
| INSUFFICIENT_MARKET_EXCHANGE_EVIDENCE | 4 | 4 | 保留未知，不以无充分证据写成没有买入 |

归因没有把上述未知强行改成交易或非市场取得。15个不能正常normalize的上下文，其目标余额变化在该分类证据中是UNAVAILABLE，不写成0。

## 发现并修复的真实问题

- 原完整性门槛对全部holder错误做全局any：一个Owner有缺口，其他已读完的Owner也被降级。现在在真实scan边界绑定owner/token_account，逐Owner判断；归属不明的legacy holder错误继续保守阻断。
- 对UNKNOWN保留固定分类原因和安全链元数据原因，不输出异常原文；共享分类器只增加诊断，不改变classification/trade或金额规则。新增coverage区分观察、去重上下文、不同签名和受影响Owner，页面不再把298条观察称作298笔读取失败。
- 独立复核在第4次失败后被预算异常覆盖具体source code。现有transport只新增安全last_wire_error_code（成功清空），报告另存last_source_error，与预算停止reason分开；无URL/body/全attempt日志，不增加来源/请求/预算。旧4次真实失败的具体原因仍UNKNOWN，不从新字段回填。

## 同一原件上的反事实验证

基线和候选各完整消费1529个checkpoint读取，全部socket拒绝、事件0、原SQLite hash不变。第二提供方原响应未录入，所以仅消费它已记录的primary读取并冻结原独立失败结果；不将此称为独立来源验证。比较仅归一化两个本机result_received_at和RPC endpoint标签，来源payload/slot/TTL/预算不改；基线业务字段与原报告一致。

候选相对基线仅改变transaction_errors归属/诊断、classification gap coverage、holder首买状态及关系组内同一首买状态投影；208交易、10资金、175归集、216边、指标和判断全相同。原9有界/3未知/8未扫变为5当前账户完整首买/2当前账户完整范围未见市场买入/4有界/1未知/8未扫，恢复7个未受该Owner缺口影响的账户覆盖声明。范围仍是选中当前token账户，不含关闭账户/全Owner历史；这不是新鲜链上结果，未改写生产旧报告。

## 216条边的范围内核对

另一个只读审计器从成功原交易的解析指令及pre/post账户Owner/Mint映射独立核对202目标币直接边、6报价直接边；4共同归集、3共享基础设施签名、1未确认共同签名均有对应多交易/签名证据。216/216引用成立、重复0、无效引用0；175归集原行同时逐条核对。登记标签只核与当时配置一致，不把登记当现实身份认证，也不把关系边当共同控制证明。审计器不以重跑_derive_pair_edges作为唯一证明。

## 测试和本地安装

新增Owner隔离/诊断反例父版6失败/1通过；三项UI反例均失败。候选573 Python通过（23文件、2.98秒、socket事件0），205 Node通过，node --check通过；相关共享classifier/Engine回归已包含。未用旧CI替代，本HEAD核对未发现workflow运行。

固定执行工具先在原PR242提交 `293b58219db8a5676fb99f06681160e42ebe4973` 并API读回。旧501文件完整字节备份，76报告/3 SQLite一致备份与integrity/FK、14保护哈希通过；旧新实际Handler无监听预检，各9精确任务/1绑定补证、D1/D2/静态文件通过，socket/POST0。仅原Dashboard重载，PID21841，Scanner2268/1f2c6af仍LIVE无漂移0错误、Loop未加载，回滚未实操。

## 本轮Chrome真实验收

本轮仅对同一既有CA/既有来源发起一次新查询，主1200wire/1800秒、独立4wire/60秒及HTTP上限不变。本次已DONE，数据时点2026-11-13T17:39:49.955598+07:00，183.689秒。主257wire/1153缓存（27次endpoint失败后恢复），独立另4wire，本次共261 RPC尝试；1387逻辑读取=1383 RPC逻辑读取+4客户端操作。新报告SHA256 `eaebeb1cac02e8df3859c40ddd849d6a2c36b27d7d65fcbe7241ad05d00483ff`；DONE身份/hash、原始与timestamped副本、1387条CP metadata/逐条链/head/count和精确job GET通过，源SQLite只读hash不变。

新时点为286条分类观察/258 Owner-签名/252签名/4 Owner；原因按去重上下文为223授权未证明、16多资产歧义、15Owner不在消息键、4交换证据不足。它与原298不是同一时点/采样，不能把数量变化归因于修复消除了12个问题。新报告5当前账户完整首买、2当前账户完整范围未见市场买入、3有界、1未知、9未扫；27窗口15封顶/12空页，关闭账户/全Owner历史仍缺。

独立PublicNode仍UNAVAILABLE/WIRE_BUDGET_EXHAUSTED，实际4次；新诊断保存最后来源错误HTTP_403，Chrome也明确显示。没有全attempt记录，因此只确认最后一次code，不宣称4次全部同因，也不据此推断必须付费、token或具体提供方规则；到限停止、未换源。

新全Mint33629账户/7942非零Owner，全局Top10 58.0139%、已核验池/前缀16.7068%，normalization_complete=false。供给前468895395/GPA468895405/后468895620为跨slot夹逼，不是原子same-slot；metadata+2帖仍读取，官方认领未核实。新增181边（174直接指令/7多证据派生）也完成同范围原始证据核对，重复/无效引用0；186交易真实分类器、9资金、166归集与原交易核对，业务键重复0。登记身份现实真伪和共同控制未因此验证。

原76文件75保持字节不变，仅latest预期更新；assessment-history因判断未变保持原字节。新增6文件后共82。13非缓存保护项不变，仅RPC cache预期变化；report/status/CP中未发现实际私有RPC URL/key。实际Chrome新分类面板、Owner各自完整性/有界状态、HTTP403明细及新job刷新恢复通过，截图留Git外、页面留开。

本轮代码/离线/安装/Chrome PASS；完整CA仍PARTIAL / INCOMPLETE_EVIDENCE。主RPC可确认下界4108、当前独立4另列、历史额外诊断未全计、原572单列。INVEST_NO_GO / TRADE_NO_GO保持，剩余是保留的分类歧义、完整/关闭账户历史、全身份/独立受控快照/其他代表样本；不发通知、不交易、不合并、不恢复盈利研究。详见[机器回执](./evidence/frank-classification-gaps-20261113.json)。
