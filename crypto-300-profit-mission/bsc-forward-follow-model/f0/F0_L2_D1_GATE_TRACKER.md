# F0 D1 执行型验收矩阵与未完成项（仅离线，Mac 审核待完成）

父D0批准：PR169 固定 SHA `29157cbc4aaf9165d4401ed695ec8902d4a0b7b7`，`DESIGN_APPROVED_ONLY`；本D1 PR170必须另行固定 SHA、Mac 独立代码复审。没有新的真实授权/nonce、没有实际 BSC 传输器、没有新 RPC。

## 代码范围

- `f0_l2_d1_grant.py`：Ed25519 user/reviewer 两角色签名验证（固定 cryptography 46.0.4 后端、固定角色、许可字节SHA256和代码 SHA）；规范化 Ed25519 raw 公钥去重、双进程 O_EXCL grant 登记、0600文件与fsync目录，固定注册根工厂 `FixedLocalGrantRegistry`。**真正的生产信任公钥仍为空（主动禁止真实授权）**，任何变更须新的单独许可与代码审核。
- `f0_l2_d1_coordinator.py`：只接受内存 `FakeSource`，真实3-worker、3共享槽、全部方法共用 ≥250ms 单调时钟假发送开头；唯一协调者分配请求 ID、预算、HEAD 和调度；0600 `RESERVE_UNKNOWN` 持久化后才允许发；原始假HTTP字节0600独占持久化后写 `SETTLE`；坏parent归属原请求ID；无重试，停止派发后结算在途，原始归档失败产生UNKNOWN。
- `tests/test_f0_l2_d1_grant.py`、`tests/test_f0_l2_d1_coordinator.py`：离线反例。临时测试用 Ed25519 私钥**只在测试进程内存生成，不落盘、不提交Git、不变成生产信任根**。

## 与D0的 G/J/M 矩阵逐项绑定（未达到的不能算 PASS）

| 行 | 本 PR D1 证据（位置、测试名） | D1 状态 |
|---|---|---|
| G-01 | `grant.validate_live_trust_roots_not_enrolled`; `test_d1_has_no_enrolled_live_trust_roots`; fake协调器拒绝任意sender | OFFLINE_DENY_PASS；无真实执行入口 |
| G-02 | D0定义 Git fixedSHA全依赖门禁；现只有签名绑定 `approved_commit_sha` | **PENDING：真实入口的 checkout clean/blob SHA 核验未实现** |
| G-03 | `grant.validate_approvals_offline` 检查网络方法、端点、限额、字段类型、sha；相应签名反例 | PARTIAL；UTC窗口、真实启动合同未来D2 |
| G-04 | 固定 `cryptography==46.0.4` 的 `_verify_signature` / `_public_key_fingerprint`；`test_cryptographic_signatures_are_role_bound_and_cannot_swap`、`test_backend_missing_or_wrong_version_denies_not_skips`、`test_other_algorithm_and_corrupted_ed25519_key_denied`；不再调用 Mac LibreSSL，签名校验缺依赖即拒绝 | **CI_OFFLINE_PASS / MAC_REVIEW_PENDING**；真实身份信任根仍未登记、D2_BLOCKED |
| G-05 | `OfflineGrantRegistry.consume` / `FixedLocalGrantRegistry`、`test_two_processes_compete_and_only_one_consumes`、`test_fixed_registry_factory_ignores_operator_output_directory` | OFFLINE_PASS；真实固定入口未接入 |
| G-06 | O_EXCL/O_NOFOLLOW、目录FD/文件+目录 fsync、`test_registry_fsync_error_keeps_single_use_marker_consumed`、权限/symlink测试 | OFFLINE_PASS；人工删库/跨机器不作唯一性承诺 |
| J-01 | `run_fake_concurrent` 3-slot共享HEAD/BLOCK；`test_global_actual_fake_starts_share_250ms_and_slots_and_budget` | FAKE_PASS |
| J-02 | `GlobalStartGate.run` 单锁约束真实线程 fake sender 开始时间，monotonic 记录；全局250ms测试 | FAKE_PASS；真实HTTP sender开始时刻未验证 |
| J-03 | `ExclusiveEvidence.add` 在 executor.submit 前fsync；`test_presend_fsync_exception_never_invokes_fake_source` | FAKE_PASS |
| J-04 | HEAD 时间从 worker 真实响应完成起算；`test_global_gate_rejects_stale_head_at_actual_fake_send_time`、`test_slow_initial_head_archive_cannot_refresh_expired_head`（4.2秒归档）、`test_delayed_head_completion_queue_cannot_rejuvenate_old_sample`（4.1秒排队） | **CI_FAKE_PASS / MAC_REVIEW_PENDING** |
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
python3 -m venv "$TMPDIR/mission170-d1-ed25519-r2-venv"
"$TMPDIR/mission170-d1-ed25519-r2-venv/bin/python" -m pip install -r crypto-300-profit-mission/bsc-forward-follow-model/f0/requirements-d1-offline.txt
"$TMPDIR/mission170-d1-ed25519-r2-venv/bin/python" -c 'import cryptography; print(cryptography.__version__)'
"$TMPDIR/mission170-d1-ed25519-r2-venv/bin/python" -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py' -v
"$TMPDIR/mission170-d1-ed25519-r2-venv/bin/python" -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_f0_l2_d1_*.py' -v
```

没有真实网络、未注册生产用户或审核公钥、不调用原串行真实发送器；不要生成真实 permit 或任何运行批准文件。检查本 PR 文件Git blobs、CI、不覆盖PRIVATE Journal、不修改旧 PR169。独立审核结论需针对新固定SHA明确 `APPROVE_OFFLINE_CODE` / `REQUEST_CHANGES`；若某关键矩阵行未完成则明确说明 **D1_PARTIAL**，不能签发真实运行许可。

**下一门禁**：补齐 D1 的明确未完成项（真实传输源码、固定SHA全依赖校验和生产信任根通过独立方式预先登记的可验证绑定），重新独立复审；D2 用户明确给出**全新精确**运行许可后才可执行D3。原30请求授权耗尽，F0_NOT_PASSED / PRODUCTION_NO_GO。


## PR171 continuation: G/J delta and new offline tests

G-02 offline: verify_fixed_checkout_offline / test_exact_git_head_clean_files_and_symlink_denial; trusted full static manifest binding remains PENDING.
G-03 offline: validate_window_contract / test_utc_contract_exact_bounds_and_unknown_authority / test_utc_contract_resource_and_destination_fail_closed; signed approval and real-run UTC gate remain PENDING.
J-06 fake only: _exchange_with_factory / test_f0_l2_d1_https.py (7 focused tests); send_live unconditionally DENIED, no real origin access.
J-08 offline only: reconcile_saved_attempts / test_duplicate_settle_and_orphan_settle_rejected / test_parent_fault_owner_and_no_cross_gap. Real duplicate packets not tested.
J-10 offline only: test_crash_preserves_unknown_and_never_auto_retries / test_failed_rpc_settlement_is_not_valid_performance_sample / test_raw_mutation_and_truncated_jsonl_rejected. No OS interruption proof.
Every new statement requires independent Mac review of new child SHA; previously approved PR170 does not approve child PR171.

## PR173 addendum — source inventory & sealed memory-HTTPS coordinator

G-02: `tracked_f0_source_manifest_offline` enumerates every tracked F0 path; `installed_ed25519_distribution_inventory_offline` checks local cryptography RECORD/file bytes and Python executable checksum. **OFFLINE_INVENTORY_ONLY**: verified wheel-independent trusted SHA, interpreter, stdlib, imported dependency closure and role-attested manifest **NOT DONE**.

J-02/J-04/J-06: `SealedMemoryHTTPSSource.reply_over_memory_https` calls fixed in-memory HTTPS factory; `GlobalStartGate.run` gates the fake POST itself (after fake TLS setup), preserving 250ms shared start spacing and fresh HEAD. `test_f0_l2_d1_http_sealed_integration.py` covers normal, HTTP503, bad JSON, no live sender or mutable callback. Fake transport **PASS pending independent Mac**; actual socket starts **BLOCKED**.

J-08/J-10: hard in-flight failures override earlier budget-only stop labels, and existing recovery audit still checks pre-send reservation, raw-before-settle, original request ID and contiguous commit. No automatic grant retry; real crash proof **BLOCKED**.

G-03/G-04: `run_gated_fake_session` now admits exact sealed fake HTTPS class after ephemeral Ed25519, UTC budget and injected Git checksum checks. Strictly test-only; real identities, actual UTC send-time and trust root **BLOCKED**.

See `F0_L2_D1_SOURCE_HTTPS_GATE.md` for exact tests and claims. Mac approval for PR172 does not transfer to PR173.


## PR175 — D1 test-signed source/wheel inventory + test one-use fake gate (review pending)

G-02: `f0_l2_d1_inventory_gate.offline_inventory_statement` and `verify_test_inventory_attestation` bind complete **tracked F0 subtree** SHA inventory, installed wheel bytes, Python executable digest and exact raw permit SHA256 into independent ephemeral test-only role signatures; `test_signed_inventory_rejects_mutation_missing_or_extra_fields` etc. **TEST_INVENTORY_ONLY**: not source-independent provenance, no stdlib/import-closure signed proof, no production root.

G-03...G-06: `consume_then_run_fake_once` composes already approved signed UTC/checkout validation, independent test-only inventory commitment and **injected private disposable** OfflineGrantRegistry marker O_EXCL/fsync before FakeSource; `test_registry_consumes_once_before_memory_https_and_no_retry`, `test_consumed_marker_survives_fake_failure_and_new_output_root`, `test_bad_inputs_do_not_consume_or_start_fake`. **OFFLINE_TEST_ONLY**, not permanent production registry/real grant.

J-01..J-10: parent sealed **memory-only** HTTPS three-slot coordinator + response raw audit unchanged; no live socket/physical provider throughput. M-02/M-03 BLOCKED_REAL_DATA.


## PR176 — J-10 genuine OS SIGKILL at three OFFLINE fsync boundaries (Mac review pending)

Module `tests/test_f0_l2_d1_os_crash_survival.py` exercises isolated POSIX child-process SIGKILL after O_EXCL grant marker+dir fsync; after CHAIN `RESERVE_UNKNOWN` journal flush+fsync **before fake send**; and after BLOCK RAW body+dir fsync **before SETTLE**. Parent process verifies 0600 file/0700 directories, raw orphan vs UNKNOWN ID, invalid audit, zero retries and marker spent across output-root changes. Linux GitHub full CI 430/430 PASS. This upgrades J-10 **OS_PROCESS_SIGKILL_FAKE_ONLY**, not power loss and not real TLS provider crash recovery. No parent coordinator, registry or recovery source changed. Mac fixed-SHA independent audit required. See `F0_L2_D1_OS_CRASH_REVIEW.md`.


## PR179 — G-02 offline reviewer pins

PR176 Mac approved `OS_PROCESS_SIGKILL_FAKE_PASS` at `a1d33ab0fd7f68db01b67d3d7da6603af1fd6797` (430 full / 69 focused). PR179 independently supplied code, permit, inventory digests and user/reviewer fingerprints are checked against local signed files. External authenticity of the pins and complete runtime dependencies remain unverified. G-02 is PARTIAL and real permission/transport are BLOCKED. `F0_NOT_PASSED / PRODUCTION_NO_GO`.


## PR180 — UTC check at actual sealed fake POST after thread/TLS prep (Mac approval pending)

G-03/J-02/J-04: `OfflinePostUTCWindow` validates the exact signed TEST permit UTC bytes and candidate source SHA at the in-memory HTTPS POST start, after fake TLS preparation and pacing wait. The coordinator checks its monotonic start deadline and HEAD TTL at the same gate, records a failed settlement rather than fake start on UTC expiry, and drains previously reserved requests. Bundle and spent offline one-use registry can use this strict test-only sender clock. New tests in `tests/test_f0_l2_d1_post_utc.py`. This is **OFFLINE_FAKE_TIME_OF_USE_ONLY**, not trusted wall-clock or real TLS socket. Parent PR179 independently Mac approved: 436 full, 75 focused, and no P0/P1. D2/D3 remain prohibited. `F0_NOT_PASSED / PRODUCTION_NO_GO`.


## PR181 — J-06 HTTPS TLS-connect / POST call boundary (Mac review pending)

Frozen PR180 Mac APPROVE `e0af79fcf564aa3d5de826003e8ec0b5f6b49469`, 442 full, 81 focused. PR181 code `f0_l2_d1_tls_phases._exercise_tls_post_with_mock` and 7 tests separate `CONNECT_ATTEMPTED`, final fake pre-POST authorization and `POST_ATTEMPTED` before a single mock HTTPS request; invalid gate after TLS connect prevents mock POST but **does not undo network connection attempt**; a POST write exception leaves outcome failed/uncertain, never retryable. Raw 503 preserved, redirect/gzip/response cap rejected. No default live factory, no physical TLS peer, and `post_attempted_at_monotonic` is merely the call site, **not actual wire byte time**. Therefore J-06 status: `OFFLINE_PROTOCOL_BOUNDARY_CI_PASS`, NOT real TLS socket or actual send pacing. Main G-02/G-03..06, J-10 real and M-02/M-03 still blocked. `F0_NOT_PASSED / PRODUCTION_NO_GO`.


## PR182 — Concrete HTTPS connection source review and D1 exit convergence (Mac approval PENDING)

Approved parent PR181 `35e1cba6cc4b4e841ff6f096bf6ed0af22b2ac8d`, Mac full 449, focused 88, 7 new and no P0/P1. New `f0_l2_d1_concrete_https.py` concretely pins HTTPS host/443 and ssl CERT_REQUIRED+hostname verified, one strict JSON-RPC POST, bounded RAW capture, no retry/redirect/encoding fallback; new tests patch **the actual `http.client.HTTPSConnection` constructor** and assert zero network plus denial without internal test token. `send_live()` always DENIED. This is J-06 **CONCRETE_CODE_OFFLINE_REVIEW**, NOT J-06 live socket PASS: no independent TLS peer, actual physical send time or real durable-ledger binding. Real D1 exit also BLOCKED on G-02 runtime provenance, G-03/04 identity and trusted time, G-05/06 permanent grant integration, J-10 real send crash and M-02/03 source evidence. See `F0_L2_D1_CONCRETE_TRANSPORT_EXIT.md` for priority and exact next stage; no D2/D3 authority. `F0_NOT_PASSED / PRODUCTION_NO_GO`.


## PR183 — ONE D1 integrated offline exit and authority verdict (Mac review pending)

Approved PR182 exact `980121f75626df53508155b09d0776841b2c4f67` Mac 459/459 full and **98/98 focused**, new concrete source 10/10. PR183 `f0_l2_d1_integrated_exit.run_offline_integrated_fake_with_pins` now checks exact TEST pins+installed source/wheel/Python/signatures **before registry mutation**, then uses approved ephemeral signed UTC/budget, disposable O_EXCL/fsync single-use TEST marker, sealed-memory three-slot full ledger and recovery audit; no other worker type/callback or real HTTPS factory. New tests cover success, no consume on bad pins/permit/source, consumed grant across changed output dir, fake UTC expiry and always-denied production sender. `production_d1_exit_verdict` explicitly reports **`D1_BLOCKED_AUTHORITY`**: G02 complete independent code source + wheel/native closure, G03/04 independently identified human signers/trusted UTC, G05/06 production fixed registry coupled to entry, J02/03/06 real 3-slot transport and fsync/RAW, J10 real socket/OS/power conditions, M02/M03 independent same-window provider throughput all NOT COMPLETE. Not D1 production approval. Refer `F0_L2_D1_INTEGRATED_EXIT_GATE.md`. `F0_NOT_PASSED / PRODUCTION_NO_GO`.


## PR184 — Independent production-trust/bootstrap feasibility, DESIGN ONLY

Frozen PR183 Mac independently approved `4e12e4f43ca2cc466e6c20b79fcdbc23228dd28f`, **464/464 complete, 103/103 D1, 5/5 new**, scope only offline integrated fake; its `D1_BLOCKED_AUTHORITY` verdict remains authoritative. A separate design-only child documents actual trust-holder roles, independently authenticated and pinned signer fingerprints, full Python interpreter/stdlib/cryptography wheel/transitive dynamic dependency release provenance, trusted UTC, single-use fixed production registry, and physical-start HTTPS/journal coupling. None can be established solely from caller-provided keys/pins, mutable Git content or the current Mac test report. Current gate status: `TRUST_BOOTSTRAP_FEASIBILITY_BLOCKED_EXTERNAL_AUTHORITY`. See `F0_L2_D1_TRUST_BOOTSTRAP_DECISION.md` for acceptance/STOP criteria. No new RPC, real permit/nonce/signature, production roots, real HTTPS sender, merge, deploy or background job. `F0_NOT_PASSED / PRODUCTION_NO_GO`.


## PR185 — user as real F0 authorization source, Codex as independent code reviewer: D0 amendment PROPOSED ONLY

User confirmed authority roles: **user approves**, **Codex independently reviews exact-SHA code**. Third-party human signer/CA is not an intrinsic requirement for bounded public-only research; previous mandatory externally certified user and reviewer Ed25519 identities and complete system-library cryptographic provenance are now proposed for proportionate replacement with audited Mac source/runtime SHA, Codex clean-checkout review, explicit user chat-scoped *single trial* approval and fixed fsynced grant registry + hard request limits. Full comparison in `F0_D0_USER_CODEX_AUTHORITY_AMENDMENT.md`. This does **not** itself approve a new actual permit or D3 trial and does not change current code's `D1_BLOCKED_AUTHORITY`; no network authorized or D0 gate silently relaxed. Future change requires explicit review of this amendment and separate user approval of exact live parameters. `F0_NOT_PASSED / PRODUCTION_NO_GO`.


## PR186 — one D1 coordinator and concrete HTTPS CODE path, sealed offline Mac provenance (fixed SHA review pending)

- Frozen approved design parent PR185 SHA `a469019b596045d8d4cea9afe9a8393e40a10981`. The user grants trial permissions, Codex reviews exact SHA; **no third person/dual production-human PKI required for this bounded read-only research**, and old static blocker text was corrected. Design approval has NOT authorized actual calls.
- J02/J03/J06: new exact `SealedConcreteOfflineSource` executes the PR182 **specific standard library HTTPS lifecycle** inside the previously verified **single three-slot fake coordinator**, no callback or real socket. The coordinator still fsyncs `RESERVE_UNKNOWN` before worker submission/fake TLS, guards 250ms fake POST starts, signed test UTC/HEAD TTL, archives RAW before SETTLE, audits once grant identity. 503/expiry/late POST never gain a retry. Tests patch `http.client.HTTPSConnection` to detect accidental real usage. Code proves behavior only on sealed memory TLS, **not real peer, physical wire timing or absolute TCP/TLS timeout**.
- G02: new `review_loaded_runtime_offline()` measures ALL Git-tracked F0 bytes at pinned SHA, checks critical actually imported module paths against frozen Git paths, hashes Mac/CI `sys.executable` and cryptography wheel/RECORD; caller measurements do not prove external trusted source or attacker-resistant Mac execution. The lightweight protocol requires Codex to cross-check provenance.
- G03-G06: ephemeral pins/test permit/test registry are still testing input; protected actual Mac launch with user-approved exact run bytes and **fixed production one-use registry before TLS** is NOT joined. All live public entrypoints remain unconditional deny. J10 real socket crash and M02/M03 real source capacity remain unmeasured; D2/D3 not authorized. `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.
