# F0 D1 执行型验收矩阵与未完成项（仅离线，Mac 审核待完成）

父D0批准：PR169 固定 SHA `29157cbc4aaf9165d4401ed695ec8902d4a0b7b7`，`DESIGN_APPROVED_ONLY`；本D1 PR170必须另行固定 SHA、Mac 独立代码复审。没有新的真实授权/nonce、没有实际 BSC 传输器、没有新 RPC。

## 代码范围

- `f0_l2_d1_grant.py`：Ed25519 user/reviewer 两角色签名验证（OpenSSL，固定角色、许可字节SHA256和代码 SHA）；规范化 DER 公钥去重、双进程 O_EXCL grant 登记、0600文件与fsync目录，固定注册根工厂 `FixedLocalGrantRegistry`。**真正的生产信任公钥仍为空（主动禁止真实授权）**，任何变更须新的单独许可与代码审核。
- `f0_l2_d1_coordinator.py`：只接受内存 `FakeSource`，真实3-worker、3共享槽、全部方法共用 ≥250ms 单调时钟假发送开头；唯一协调者分配请求 ID、预算、HEAD 和调度；0600 `RESERVE_UNKNOWN` 持久化后才允许发；原始假HTTP字节0600独占持久化后写 `SETTLE`；坏parent归属原请求ID；无重试，停止派发后结算在途，原始归档失败产生UNKNOWN。
- `tests/test_f0_l2_d1_grant.py`、`tests/test_f0_l2_d1_coordinator.py`：离线反例。临时测试用 Ed25519 私钥**只在测试进程的临时目录生成，并不提交到Git或变成生产信任根**。

## 与D0的 G/J/M 矩阵逐项绑定（未达到的不能算 PASS）

| 行 | 本 PR D1 证据（位置、测试名） | D1 状态 |
|---|---|---|
| G-01 | `grant.validate_live_trust_roots_not_enrolled`; `test_d1_has_no_enrolled_live_trust_roots`; fake协调器拒绝任意sender | OFFLINE_DENY_PASS；无真实执行入口 |
| G-02 | D0定义 Git fixedSHA全依赖门禁；现只有签名绑定 `approved_commit_sha` | **PENDING：真实入口的 checkout clean/blob SHA 核验未实现** |
| G-03 | `grant.validate_approvals_offline` 检查网络方法、端点、限额、字段类型、sha；相应签名反例 | PARTIAL；UTC窗口、真实启动合同未来D2 |
| G-04 | `_verify_signature`、`_public_key_fingerprint`、`test_cryptographic_signatures_are_role_bound_and_cannot_swap`，真正区分两把钥匙且绑定许可hash和代码SHA | OFFLINE_PASS；**真实身份信任根未登记，D2_BLOCKED** |
| G-05 | `OfflineGrantRegistry.consume` / `FixedLocalGrantRegistry`、`test_two_processes_compete_and_only_one_consumes`、`test_fixed_registry_factory_ignores_operator_output_directory` | OFFLINE_PASS；真实固定入口未接入 |
| G-06 | O_EXCL/O_NOFOLLOW、目录FD/文件+目录 fsync、`test_registry_fsync_error_keeps_single_use_marker_consumed`、权限/symlink测试 | OFFLINE_PASS；人工删库/跨机器不作唯一性承诺 |
| J-01 | `run_fake_concurrent` 3-slot共享HEAD/BLOCK；`test_global_actual_fake_starts_share_250ms_and_slots_and_budget` | FAKE_PASS |
| J-02 | `GlobalStartGate.run` 单锁约束真实线程 fake sender 开始时间，monotonic 记录；全局250ms测试 | FAKE_PASS；真实HTTP sender开始时刻未验证 |
| J-03 | `ExclusiveEvidence.add` 在 executor.submit 前fsync；`test_presend_fsync_exception_never_invokes_fake_source` | FAKE_PASS |
| J-04 | reserve及 worker实际开始前对已完成HEAD加4000ms门禁；`test_global_gate_rejects_stale_head_at_actual_fake_send_time` | FAKE_PASS |
| J-05 | HEAD先核链ID、阻止越过最后成功HEAD；`test_initial_head_http_error_does_not_dispatch_blocks` | FAKE_PASS；真实来源独立锚未验证 |
| J-06 | 注入HTTP503、坏JSON、迟到超时帧，`test_http_503_stops_new_dispatch_and_charges_attempt`、`test_bad_json_denies_parse_without_false_commit`、`test_late_fake_frame_is_archived_but_not_accepted` | PARTIAL；真实TLS/代理/重定向/压缩需另审 |
| J-07 | `parsed_blocks[height]` 保存 `rid`；`test_out_of_order_parent_fault_owned_by_bad_buffered_response` | FAKE_PASS |
| J-08 | 别把完整响应等于连续提交；乱序故障专项测试 | PARTIAL；独立重复结算/恶意重放场景待增强 |
| J-09 | 最多32总请求/24区块/6HEAD刷新/3槽，统一单调间隔、短窗口 | FAKE_PASS；真实期限和网络发起需另审 |
| J-10 | 记录 `UNKNOWN`，未归档不能算成功；`test_archive_write_failure_never_claims_success_or_retries`、私有日志独占测试 | FAKE_PASS；真实系统崩溃/断电恢复审查待做 |
| M-01 | fake source增长与HEAD/连续提交差；已批准PR167有原私有Journal耗时六组 | PARTIAL；D1尚无私有Mac Journal并发HTTP实测 |
| M-02 | 真实同窗口连续提交速率与来源增长率比较 | BLOCKED_REAL_DATA |
| M-03 | 长期追平、外部父块锚、真实 first seen 和跟单可用性 | BLOCKED_REAL_DATA |

## 独立 Mac 审核任务与可执行命令

新隔离 checkout 固定在PR170最终SHA并核对原设计父SHA；不用分支名代替固定SHA。全套测试从 repo 根目录运行：

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py' -v
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_f0_l2_d1_*.py' -v
```

没有真实网络、未注册生产用户或审核公钥、不调用原串行真实发送器；不要生成真实 permit 或任何运行批准文件。检查本 PR 文件Git blobs、CI、不覆盖PRIVATE Journal、不修改旧 PR169。独立审核结论需针对新固定SHA明确 `APPROVE_OFFLINE_CODE` / `REQUEST_CHANGES`；若某关键矩阵行未完成则明确说明 **D1_PARTIAL**，不能签发真实运行许可。

**下一门禁**：补齐 D1 的明确未完成项（真实传输源码、固定SHA全依赖校验和生产信任根通过独立方式预先登记的可验证绑定），重新独立复审；D2 用户明确给出**全新精确**运行许可后才可执行D3。原30请求授权耗尽，F0_NOT_PASSED / PRODUCTION_NO_GO。
