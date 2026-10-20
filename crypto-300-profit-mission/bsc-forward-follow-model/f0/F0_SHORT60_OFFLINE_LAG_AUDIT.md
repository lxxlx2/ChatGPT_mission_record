# F0 60/60 第一批真实样本：离线追头时差与候选质量复算

**状态：仅离线代码 / 尚未验证本次真实 Mac 原始归档 / 未获新 RPC 授权 / 不运行交易。**

基线：[PR #149](https://github.com/lxxlx2/ChatGPT_mission_record/pull/149) 固定归档 SHA `51b539dd5cb6185e9bc165da6a21f7ebf2e40fc4`。该归档报告一次用户授权、独立许可审核后的 BSC 免费 HTTP 运行：62/62 请求返回、60/60 连续未来完整区块（128716367–128716426）、5,940 笔交易、0 个 PRIMARY from 命中、40 个 Router-to 地址命中、20 个固定种子离线预选候选，退出 0。该许可已消耗。

以上统计已独立与**GitHub 提交的脱敏 JSON、日志、Git 祖先关系、实际成功的 257 项 CI** 做内部对账；**原始 62 份 HTTP 响应、journal、permit 和 Codex 审核全文只保留在用户 Mac 私有归档**，GitHub 评论审核者没有重新下载或复算这些原始字节。因此仍必须区分“操作者报告已从原始响应独立回放”和“GitHub 审核者亲自重放”。

## 为什么下一步不应直接申请 120 秒或 24 小时采集

BSC 官方文档描述主网目前约 `0.45s/block`，而本次的未来高度读取是按用户许可约 **1000ms/高度** 串行推进。虽然报告在所请求 **60 个高度中 60/60 收到块**，这只证明请求高度的覆盖；并未证明监控始终接近实时 head。若出块持续快于串行采集，落后量会增长，无法把本机 HTTP 响应时间或已落后区块识别时间直接解释为“可跟单首见”。官方依据：https://docs.bnbchain.org/bnb-smart-chain/introduction/ 。

下一个主线问题不是修更多同类安全边界，而是**用已有原始证据证伪/确认追头能力**：比较每个区块 `timestamp` 与接收时间（需注意 BSC header 秒级时间戳以及 Mac 钟差）、首尾区块生产时间跨度与本地接收跨度、候选浓度/路由 method selector 组成。若相对滞后增长明显，就先决定重新设计抓取节奏/并发与供应商免费吞吐能力，再单独申请新实验。

## 实现和证据口径

`f0_l1_saved_lag_audit.py` 是 **仅用 Python 标准库和仓库中已冻结的本地解析器的离线脚本**。它只接受本机 `journal.json`、`raw_responses/` 两个本地路径，从 Git HEAD 读取同一份 PR116 manifest + 两个 documentary Router registry。无 `urllib`、socket、传输注入、节点请求、自动采集、签名或私有数据上传。

逐行执行以下复算：

- 拒绝非 62 项原始完整观察、任何 UNKNOWN/FAILED 与隐藏跳号；按 `response_sha256` 逐份校验 **62 个本地原始 HTTP response 字节**，精确核对请求 ID、方法、chainId 56、单次链头、完整区块高度从 head+1 连续到 head+60；
- 每个完整区块使用原 `block_candidates` 解析，校验 **60 个连续高度的区块身份 + 59 条相邻父哈希链接**、内部交易 blockNumber/blockHash、重复交易、from/to 规范化，并重新累计全块交易与 PRIMARY-from / Router-to 地址命中。第一次 `eth_blockNumber` **只返回 head 的高度，不返回 head 的哈希**：首个保存区块的 parentHash **未锚定到 head 哈希**，报告必须写 `internal_parent_links_verified=59`、`first_saved_block_parent_anchored_to_observed_head=false`，不得使用“60 条父哈希都已验证”的表述；
- 只汇总 Router 地址命中的 EVM transaction `input` 前四字节选择器频次，不上传钱包地址、交易哈希、raw input 或路径；**selector 只表示交易发送到某地址的调用特征，绝不等于交易成功、实际 swap 或因果/独立对照**；
- 计算本机响应（UTC）与 BSC 区块头 `timestamp` 的差以及首尾 60 个块的 `[local receive span] - [header timestamp span]`。这是**追头滞后的间接指标**，不是独立实时节点的 head lag、传播首见、纯网络 RTT 或真实可成交延迟；
- 输出只有脱敏聚合 JSON，`network_requests_by_this_tool=0`，E2/E3/quotes/收益标记依旧为 false/0/UNVERIFIED。不会修改原归档任何文件。

用法（Mac 的固定且审过的离线分支、无下载脚本或散补丁）：

```zsh
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_saved_lag_audit.py --journal "/PATH/TO/private/journal.json" --raw-dir "/PATH/TO/private/raw_responses" --out "/PATH/TO/private/new-offline-lag-result.json"
```

其中 `--out` 必须是新文件，不覆盖原始归档。Mac 上的私有 Evidence 路径是否含直接的 `journal.json` 或是子目录，需要由有权限的本地 operator 实际核查；不应猜测路径，也不要让用户公开上传私人许可或 raw RPC 文件。

**测试与审核:** 新增 5 项纯本地假字节测试，覆盖完整 62 份成功、原始字节篡改、改写父哈希、错乱请求序号、区块时间戳缺失。历史 PR149 CI 确认 **257/257 PASS 零 SKIP**；本 PR 组合**预期 262**，须运行 GitHub Actions 完整 checkout 取得真实记录、独立固定 SHA 复审。完成前不能说真实采集延迟已经测出。

**下一阶段 Go/No-Go:** 如果有 60 份的 `block timestamp` 经过质检，离线结果给出首尾相对滞后是否增长以及候选组成；然后再考虑真正接近实时的动态 head 取块，必须另订预算与新授权。若 archive 缺少 timestamp 或原始 digest，不应对缺口作假设：输出 FAIL，保持无网络。

## 2026-10-20 独立审核 P1 的处理范围

PR #150 原始 SHA `65ef18be395fbbe9cc638199405bb67f7a22871f` 收到 REQUEST_CHANGES（首块父哈希无可核对的 head 哈希）。后续 PR #151 的真实离线归档已按 **59 条内部父哈希链接、首块未锚定**记录，不需要复采或改写结果。当前修复是将这个**已存在的实际证据边界**固化到离线解析器输出与测试，不引入网络和额外事件窗口。新增针对性测试构造“第一个区块父哈希不可信但所有后续 59 条连续”的响应，要求解析器只报告 59 条链内链接、`first_saved_block_parent_anchored_to_observed_head=false`，绝不伪造第 60 条外部链接。

此修复只改变声明/计数与回归，不声称首块此前的 head 哈希得到了新证实。审查者需对**新的固定 SHA**重新执行完整测试并审计改动；旧 PR #150 的 REQUEST_CHANGES 结论保持历史不变。其他 P2 中的时间戳整数秒误差已在分析结论中披露；selector 校验等不阻断主线，不因它们启动另一个长边界修复周期。
