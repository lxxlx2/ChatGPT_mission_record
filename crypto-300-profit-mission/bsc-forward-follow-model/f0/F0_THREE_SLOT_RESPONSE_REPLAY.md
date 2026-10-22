# F0 三路请求与 JSON-RPC 响应协议离线回放

父版本 PR162 固定 SHA `39f12c716e061eb1e51bf4843737a5cd6cef5d8c`，用户报告独立 Mac 复审 **APPROVE_OFFLINE_CODE**：338/338 PASS、9/9专项，24组本机历史串行耗时模型，1500ms 等待在1×、1.5×有限窗口内较好，但全部连续提交速率低于先前来源 HEAD 增长 2.178 blocks/s。上轮30次真实授权已消耗。

本阶段为**离线响应格式和区块完整性门禁**：不改已审核调度器，复用其三槽位 250ms、32/24/6、4000ms TTL 和预算事件；把虚拟请求封装为真实 JSON-RPC 2.0 参数格式，在内存中用离线生成的 HTTP body bytes 调用原有 `parse_http_response` 和 `block_candidates`。独立统计收到完整区块、合法已尝试缺失、连续父哈希提交、HEAD次数、最后采样积压及错误证据。损坏ID、错误块高度、错误parentHash、HTTP503或丢失响应不能计入有效提交。

**严谨边界：** fake_frames 生成的 blockHash、parentHash 与 HEAD **全部是合成数据**，不是 BSC 节点的真实原始响应。Mac 的旧 journal 仅提供已验证的真实**串行请求时间**，并未重放旧22个真实区块数据。此层重放的是事先计算的派发轨迹，错误响应**不会动态反馈到调度器**，因此只能证明协议解析/账本核对，不能宣称闭环并发采集可用，更不能产生任何E2/E3跟单或收益。

Mac 上固定本 PR 的新 SHA 后，从仓库根目录执行以下绝对离线命令。原始文件留本地，不上传：

```zsh
umask 077
mkdir -m 700 "$HOME/Library/Application Support/MissionEvidence/20261022-f0-http-frame-replay"
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_three_slot_response_replay.py --journal "$HOME/Library/Application Support/MissionEvidence/20261021-adaptive-sampled-head/archive/journal.json" --expected-sha256 e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a --output-dir "$HOME/Library/Application Support/MissionEvidence/20261022-f0-http-frame-replay"
```

对照 checkpoint/1500ms × 1/1.5/2共六组结果，验证每组真实请求数为零、请求和响应身份正确、接收区块与连续提交区块一致、预算上限内无新鲜度越界。独立审核新SHA、Git blobs、全量测试和专项测试，检查不引入HTTP发送器、网络、permit、nonce、签名、交易和后台执行。若出现P0/P1，REQUEST_CHANGES；离线全部满足方可 APPROVE_OFFLINE_CODE。

**下一阶段尚未实施：** 闭环离线假发送器，将解析后的HEAD、成功/失败/超时实际反馈到未来调度决策，并对持续积压/缺块进行反例验证。然后独立设计真实三路传输和单次私有许可；只有新的明确用户授权才可调用真实RPC。F0_NOT_PASSED / PRODUCTION_NO_GO。
