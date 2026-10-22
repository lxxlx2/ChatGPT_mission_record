## 2026-10-23 PR167 P1：乱序缓冲父哈希故障归属的定向修正（等待独立复审）

独立 Mac 审核对原 SHA `e863e7ecf897c90a99bcb911fe5ee5fe139e62af` 给出 `REQUEST_CHANGES`：高度 1005 的假完整响应先于 1004 收到，随后 1004 正常到达并提交，但在检测缓冲的 1005 父哈希错误时错误地把 1004 请求标为 FAILED/缺失；正常的 1008、1012 在途请求又被重复污染。旧 SHA 的 360/360 测试通过不等于 P1 关闭。

本阶段只改变**已解析响应与链完整性事件的归属边界**：
- 乱序缓冲 `buffered[height] = (original_request_id, block_hash, parent_hash)`。
- 每次 RPC 响应先独立落盘 `SETTLE`。合法完整区块维持 `RPC_RESPONSE` 和已解析计数，之后检查可连续提交的缓存；遇到错误父哈希，另记一次 `CHAIN_INTEGRITY_FAULT`，`id` 和 `height` 都来自实际损坏的缓冲块，并单独报告 `invalid_parent_height`；不会反向修改触发本次检查的正常请求。
- `attempted_missing_heights` 此处表示缺失的**可用于连续提交的有效高度**，既包括 RPC 失败/超时，也包括父哈希验证失败的块；后者可能在 `block_responses_parsed_full` 中已经计数。完整解析不等于有效链成员。
- 故障发现后禁止新派发、停止跨缺口提交，并正常结算其他在途请求；同一坏块后续不重复记失败。历史父版本代码及所有预算、HEAD 新鲜度和发起间隔均不变。
- 新增由独立审核发现的精确组合反例：首块 2500ms、后续 300/400/350ms，`growth_bps=5`，`bad_parent_blocks=[1005]`，断言 1004 成功提交、1005 为**唯一父哈希完整性故障**、1008/1012 响应保持真实成功结算且无重试，并分别核对 JSONL、请求 ID、响应与连续提交数。

修正提交必须另行独立 Mac 固定 SHA 复审；旧 SHA 不追溯批准。原始 journal / permit / nonce 只留 Mac，不上传 GitHub，零新增 RPC/WS，保持 `F0_NOT_PASSED / PRODUCTION_NO_GO`。

---

## 本轮核心口径加固

- 收到合法完整区块但内部 parentHash 不匹配时，这条完整区块仍属于已解析响应，不属于连续有效提交。将指标正式命名为 `block_responses_parsed_full`，避免“收到”与“验证通过”混淆。
- 每笔连续内部父哈希通过的高度现在单独写入本机 `COMMIT_CONTIGUOUS` 事件；可以从私有 JSONL 审计是否跳过缺口、收到乱序时是否等待较低高度。
- 特意回归首块完成比后两块慢的真实乱序结构，并保留原 checkpoint 的 800ms 短 HEAD TTL 测试条件，不让 availability_wait 的最短间隔误限制原策略。新增要求不扩大网络请求范围，仍是绝对离线合成事件。

# F0 三路**闭环离线**假采集器 — F0_NOT_PASSED

前置：PR #163 SHA `0f6ed49b2675b04328be7adb7f1296622e1fccc2` 经 Mac 独立审核 `APPROVE_OFFLINE_CODE`，346/346 全部测试、8/8 新专项、6/6 真实保存历史串行耗时的合成回放、48 个损坏响应与6个重复结算反例通过；不代表真实三路网络吞吐。

## 本轮真正解决的主线问题

之前 #163 先生成全部虚拟请求/响应轨迹，后校验响应。因此即使某个 HEAD 或区块失败，也不会影响后续派发。这次引入独立 `f0_l1_closed_loop_fake.py`：真正的**单协调者、三路虚拟在途**事件循环，分别在提交前完成持久化预约、完成时通过原有 `parse_http_response` / `block_candidates` 校验内存假 HTTP 回包，并**在回包结算后决定下一次可派发什么**。因此模拟故障确实改变后续轨迹，失败/超时不会变成已收/已提交块；停止派发后仍完整结算已在途的旧任务。

主要不变条件：最多3个共享在途槽（HEAD也在内）、所有方法共用250ms起始间隔、总尝试不超过32（含 chainId/初始HEAD）、最多24个完整区块、6次刷新HEAD、虚拟派发期至多60秒、已完成HEAD必须未超过4000ms有效期、待取块高度不得超过已确认HEAD。仅 `availability_wait` 使用1500ms绝对刷新截止；默认策略为此阶段的对照，不自动更改已审核父版本。原始请求许可已消耗。

每次“假发送”仅为内存中安排完结事件，由 **`SyntheticBscOracle`** 根据事件完成时的虚拟时间生成假 JSON-RPC 响应。它没有 socket / url / HTTP sender / 注入真实post / WS / 用户账号 / nonce / 私有许可，不可能自行联网。日志为本机独占0600 JSONL，0700私有父目录，`RESERVE_UNKNOWN` fsync后才加入模拟完成队列；普通停止会结清在途，故障不会自动重试。

离线覆盖：HEAD请求失败/回退、单块HTTP503、超时、错误ID、JSON损坏、hash-only非完整交易、块高度错、父哈希不一致、较慢/较快响应、持续合成链头增长与有界刷新预算。区块按高度及内部相邻父哈希才连续提交，另计独立“收到完整块”和“连续提交块”；首个块无外部父锚。最后采样 HEAD 与最后提交高度差、已尝试但缺失、最后采样已知未尝试高度、合成**真值 oracle 链头**与提交差距均单列。合成 oracle 的实时链头不是实际区块链的独立观测。

**保守阻断选择：**任意一个 fake BLOCK RPC 错误会停止继续派发新区块，不会在有缺口情况下盲目继续；仍结清已在途、明确列出缺失和未提交缓冲。未来如果需要持续恢复必须单独设计和审核，不在本轮擅自加入重试或复用已经消耗的真实许可。

## Mac 私有 journal 离线验证

从本 PR **新固定 SHA** 的全新 checkout，在仓库根目录运行以下只读源日志+合成时延脚本；把旧的实际 JSONL 原始响应、permit/nonce留在 Mac，不要上传：

```zsh
umask 077
mkdir -m 700 "$HOME/Library/Application Support/MissionEvidence/20261023-f0-closed-loop-fake"
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_closed_loop_fake.py --journal "$HOME/Library/Application Support/MissionEvidence/20261021-adaptive-sampled-head/archive/journal.json" --expected-sha256 e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a --output-dir "$HOME/Library/Application Support/MissionEvidence/20261023-f0-closed-loop-fake"
```

检查源文件 SHA256、6组 checkpoint/wait1500 × 1/1.5/2x 私有历史请求耗时场景、故障改变轨迹、HEAD新鲜度、全局限速、UNKNOWNS没有被伪造成成功、账户预算、最后已采样HEAD及合成 oracle 最终链头差距。展示 commit rate 和 response rate；不能只按虚拟“收到”速度判定 F0 通过。禁止付费来源/新增RPC/交易/签名/部署/合并。

## 后续关口

完成新 SHA GitHub CI 与独立 Mac 审核后，才分析闭环离线合成结果是否为真实测试建立合理门槛。真实传输器的网络协议、权限、3槽并发全局串行 fsync、一次性许可、完整响应归档及独立 reviewer 批准必须在**另一阶段**完成；任何实际 BSC 请求须新的一次性用户授权，既有30次权限已经消耗。保留 `F0_NOT_PASSED / PRODUCTION_NO_GO`。
