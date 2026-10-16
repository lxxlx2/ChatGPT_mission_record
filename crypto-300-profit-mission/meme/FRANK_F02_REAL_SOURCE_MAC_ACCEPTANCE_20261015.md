# F02 手动新来源：用户授权后的实际 Mac 验收

日期：2026-10-15 Asia/Bangkok。用户在 Claude 外审 APPROVE 后明确回复“授权”，范围为一次最多两次只读 Solana RPC、新私有研究会话和实际 Mac 浏览器验收。不是合并/部署/交易/自动化授权。

## 固定来源与执行

- PR #66 固定代码 SHA `a20a9f972589e34d2eae435c2ee4696eb53bb1d7`，工作区干净，外部 Claude APPROVE。未改源码，既有精确 HEAD CI 与联合测试结论沿用，不声称本轮重跑。
- 实际运行 `python -u -m scripts.frank_f02_manual_refresh --execute --serve`，一次采集、无重试。默认HTTPS公共Solana RPC，只有两份双程序 owner receipt；没有使用合成fixture。
- 采集 UTC `2026-10-15T06:10:01.348696+00:00`，Bangkok **13:10:01**。完整来源 SHA `a5964a093a1d6bffe7b2334480825c90af478d3c38d7336fc71cec767b81a25e`。
- SPL receipt：946,908 bytes、Slot457132317、SHA `f1fb230eb782a22a6954b8b93a87920d22afc6ccaad5b6a633e078d12a79fce6`；Token2022 receipt：872,204 bytes、Slot457132319、SHA `1b1ba3815a4cfc5f180c5b145ba0d769e18413d8a808e2f78a067b0db0c3fa37`。完整双程序、missing=[]，两次查询非原子快照。
- 新UUID私有研究会话在用户 `.local/share/frank-f02-research/manual-sessions/` 下；旧研究库未重复导入。完整原文、新Sidecar、逐Mint结果、原生浏览器截图保存在私有会话目录，不提交public Git。

## 实际功能结果

- 原文replay与冻结32目标对账通过：**9非零、23已观察零、0无开放账户**。全钱包观察3276个Mint，本页面只投影冻结32目标，不能说页面显示了全钱包所有持仓。
- 本机真实HTTP返回 `FRESH_VERIFIED_ARCHIVED_OBSERVATION`；采集摘要age1s，浏览器载入时age12s，独立本地HTTP核对时age68s，API selected SHA与原文replay SHA一致。
- Codex实际in-app浏览器（本机Mac上的浏览器，非Safari全面兼容认证）：32行数量和账户数逐行与原文replay核对通过；非零筛选9行，零筛选23行；精确CA筛选1行；复制后剪贴板字符串完全一致；Explorer href精确指向该Mint（未访问外部页面，不声称Solscan远端加载通过）。
- 点击“重新读取本地档案”只重读本机HTTP，采集时间/SHA保持不变；没有再次调用CLI或新链上采集。
- 浏览器自动化第一次按label选择余额状态未匹配，改用实际DOM已知id成功；这是选择器问题，没有代码修改。逐行核验最初按字符串比较碰到小数尾零格式差异，改用Decimal精确值比较通过，保留UI原格式，没有浮点近似。
- 自然时钟279秒本机API仍fresh；超过300秒、未重新加载页面的首次浏览器检查：来源已过期、32行数量和账户数全部遮罩，统计0非零/0零/32不可用；随后340秒API为STALE_ARCHIVED_SOURCE、32 SOURCE_UNAVAILABLE且数量和账户数均null。过期后精确Mint筛选及本地重读仍遮罩，无旧余额复活。未更改时钟/采集时间/TTL。
- 手动Ctrl-C实际输出F02_MANUAL_RESEARCH_LISTENER_STOPPED，进程退出0；socket确认18766端口不可连接，临时服务已关闭。浏览器截图只保留用户本机私有目录，Git仅归档受限摘要。

## 门禁

本轮验收仅针对F02手动真实来源→32目标研究页流程。F02-R3整体产品验收、F01/C02/研究页统一交互/任意CA入口、全钱包列表及独立最终业务复核仍需推进。不能从9/23推断出售、成本、PnL或跟单资格。NO_MERGE/NO_DEPLOY/NO_TRADES/NO_GMAIL/NO_PRODUCTION_SQLITE_WRITE/NO_NEW_AUTOMATION。
