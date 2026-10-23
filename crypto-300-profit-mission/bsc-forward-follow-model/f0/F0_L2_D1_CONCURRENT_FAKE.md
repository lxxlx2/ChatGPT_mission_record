# D1 三路共享调度 + 持久响应归档（真实线程，**假 HTTP 响应**）

入口 `run_fake_concurrent()` **只允许严格 `FakeSource` 类型**；它不含 HTTP/socket/urllib sender、不接受可执行网络 `post` 回调、不读取真实 permit/nonce，不能调用 BSC。三个 worker 使用 `ThreadPoolExecutor(max_workers=3)`，全局 `GlobalStartGate` 实际以 `time.monotonic()` 序列化**假发送开始**，约束跨方法 ≥250 ms；线程不分配请求ID和预算。

单协调者分配全局ID、HEAD与BLOCK共享3槽、最多32个RPC预算，其中块≤24、HEAD刷新≤6；首次链ID验证后才能读取HEAD，只有最新已完成HEAD有资格释放块高度，块发起前需满足4000ms TTL。START门禁也检查距最近确认HEAD的有效时刻，过期则已预留尝试记失败且不触发假发送。所有预留写到独占0600 `attempts.jsonl`，每行fsync后才把事件提交给线程。每份原始假HTTP响应先写0600文件并fsync目录，然后记录 `SETTLE`。完整解析成功与 `COMMIT_CONTIGUOUS` 分离；乱序缓冲保留原ID和父哈希，故障归属坏块。

**D1安全边界：** `FakeSource` 不具备网络功能，HEAD/区块完全合成。现在验证的250ms是**真实多线程假发送开始间隔**，不是实测公共RPC多线程间隔。下一阶段需要对独立真实 sender 和固定grant信任根再做代码审核。D1不存在真实许可、真实网络发送器、执行入口或签名授权。原真实30次许可不可再用。

独立审核应检查 fake sender 内部不接受callback、没有任何网络库，查看临时0700/0600日志的每个 RESERVE/SETTLE 顺序、3槽、全局≥250ms、32/24/6和HEAD门禁，注入HTTP503和损坏JSON，无自动重试。**特别注意**：有排队等待的 worker 在实际开始前也会再次检查旧HEAD TTL与窗口，不能仅凭预留时间判定发送合法。本阶段为 D1 OFFLINE，不代表真实源能追平。

**本轮 P1 时间修复：**HEAD 响应由工作线程在 `FakeSource.reply()` 实际返回瞬间用单调时钟保存 `completed_at`，即使后续响应等待协调者处理或归档/fsync 迟到，`head_completed` 仍以该早期时间计算 TTL。HEAD 的 `at_monotonic` 是实际 worker 完成时刻，`accepted_at_monotonic` 是归档之后的接受时刻；审核不能用后者重新赋予旧 HEAD 4000 ms 有效期。`test_slow_initial_head_archive_cannot_refresh_expired_head`（4.2秒）和 `test_delayed_head_completion_queue_cannot_rejuvenate_old_sample`（4.1秒）均必须 Mac 独立PASS；仍不能推断真实网络并发。
