# F0 D1 真实信任和受保护启动：可行性决策（DESIGN ONLY）

- 冻结批准父版：PR #183 SHA `4e12e4f43ca2cc466e6c20b79fcdbc23228dd28f`，Mac 独立 `APPROVE_OFFLINE_CODE — D1_INTEGRATED_FAKE_EXIT_BLOCKED_SCOPE_ONLY`，实际完整 **464/464**、D1 **103/103**、新增 **5/5**、零 SKIP，未发现新 P0/P1。
- 本增量仅冻结真实信任前置条件和 D1 的解阻路径：**无新源码发送器、无生产公私钥/真实 permit/nonce、无密钥生成或登记、无网络、无本地服务**。父代码不改动。
- 准确现状：`D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`。不能因离线 fake PASS、GitHub Actions PASS、同一操作者签署两套临时密钥或可编辑的 Git 文档而解除。

## 一、把“运行代码经审核”和“真实用户允许运行”严格拆开

| 对象 | 由谁掌控/事先证明 | 当前事实 | 未达成时的处理 |
|---|---|---|---|
| 不可随意修改的审核代码与源清单 | 固定 Git SHA，**独立认可**的代码和完整运行包 digest | F0 tracked tree 本地重算、PR183 Mac 检查已通过；**没有**完整可信闭包 | `G02_BLOCKED_SOURCE_PROVENANCE` |
| 用户身份公钥 | 用户在实际批准前经**独立渠道**确认其公钥指纹与有效用途 | **没有**已登记的生产 user 信任根 | `G04_BLOCKED_USER_IDENTITY` |
| 审核者身份公钥 | 与用户/执行者分离的审核主体，独立确认其公钥指纹及权限范围 | **没有**已登记的 production reviewer 根；“另一个 AI 跑了测试”不等于独立控制签名根 | `G04_BLOCKED_REVIEWER_IDENTITY` |
| 根信任来源 | 启动器预先信任、不同于运行工作区的授权公钥及版本，独立检查后固定 | 目前所有 test pins 都是调用方可传入参数 | `G02_G04_BLOCKED_ROOT_OF_TRUST` |
| 时间来源 | 可验证时间来源、容忍时钟回拨/跳跃并在最终发送边界重新判断 | fake UTC 是注入数据；Mac 本地 wall clock 可人为更改 | `G03_BLOCKED_TRUSTED_UTC` |
| 一次性消费状态 | 固定非 permit 指定的私有根，fsync/O_EXCL；失去历史状态时不能默许重新执行 | 临时测试根可通过；**未**与真实入口绑定 | `G05_G06_BLOCKED_FIXED_REGISTRY` |
| 传输、调度和证据原子边界 | 单一协调器持锁授权启动、每次发送前持久 RESERVE，RAW fsync 后 SETTLE | PR182 有具体 HTTPS 源码，PR183 只整合 **memory HTTPS**；未接真实 socket | `J02_J03_J06_BLOCKED_LIVE_LINK` |

**优先解决前三行的真实来源；最后几行尚不可进行真实调用测试。**

## 二、最小可信启动方案（候选设计，不是当前已配置）

1. **独立信任根先于可执行包存在。** 在后续另一次、单独审核的 release/启动器中，固定用户与审核者已核验的两个不同公钥/标识、允许的签名算法以及根版本；这组值来自受保护的带外审核过程，**不得由运行命令、测试配置、许可 JSON、同仓库可编辑文件或传入的 pins 覆盖**。密钥被替换、身份撤销或根版本变更时必须重新审核固定 SHA。GitHub 上显示 `Verified` 只能作为提交来源线索，不能单独认证真实批准者身份或同一个操作者的独立性。
2. **两类不同的签名对象。** （甲）不可变“发行物/源码及运行依赖清单”承诺：受审代码 SHA、入口文件、所有可执行模块、Python 解释器、stdlib/动态库、cryptography wheel 及传递依赖、实际启动参数、允许的运行目录及来源证明；（乙）单次实验 permit：固定 release digest、允许的 BSC endpoint/方法、受限 UTC 窗口、3 槽/250ms/预算及 grant ID、固定消费根的制度版本、证据根与严格只读目的。**不自动创建或签署任何实际 permit**，身份确认/代码批准也不能自动触发调用。
3. **完整软件闭包只能从独立制品基线校验。** 现有本地安装清单能读取 cryptography 46.0.4 文件，但有 **73 项 RECORD 条目不携带 RECORD 哈希**；本地 RECORD 与文件属于同一可变信任范围。下一实现须由独立审核者预先确认具体 Python 安装渠道及签名/校验依据、解释器二进制、stdlib、动态加载库、轮子原件及 SHA256、可复现环境锁定文件与 Git 入口清单，然后校对**实际**运行时模块解析与依赖载入路径。仅 `pip==version`、`--require-hashes` 或重新算本地摘要不能替代发行物可信来源。缺一项必须显式 `CLOSURE_INCOMPLETE`，不可直接设置 `complete_dependency_closure_attested=true`。
4. **可信运行时间需独立设计。** POST 前检查签署的 UTC 许可窗，使用 monotonic 控制最大执行期、队列和全局发送间隔；但注入测试时间或普通可调的系统时间**不是**可信时间源。需提出一个可验证的时钟来源及离线故障政策（离线时无法证明则拒绝）；允许访问时间来源的网络活动亦须以后单独获得认可，不得被本计划隐式激活。
5. **真正的固定注册根不可由操作者随手更换。** 注册和启动器绑定 release、许可 SHA、身份和 grant ID，不从单次输出路径重新派生；写入消耗记录并文件+目录 fsync 必须先于 **TLS connect**（连接本身就有真实网络活动）。工作区迁移、退出、SIGKILL、不同 evidence_root 不提供再试资格。目录状态丢失或可由同一操作者删除时必须 fail closed：单机可写目录不能承诺跨重装或恶意管理员的永久不可重放，若目标要求更强唯一性，需要带外不可重放审计或独立批准，不能臆造一个本地“永久安全”结论。
6. **完成上述可信启动后再做单次真实发送器绑定的 D1 离线验收。** 唯一协调器拥有所有 ID、3 槽、预算、HEAD TTL、真实 POST 尝试前 UTC 和时间间隔；已 fsync RESERVE 才能连接，RAW body 先于 SETTLE fsync，异常保留 UNKNOWN，绝不自动重试。PR182 中 `request()` 调用时点**不是物理首字节证据**；实际 socket 时序和绝对请求超时要独立采样审核，不能拿 mock 时间充数。
7. **将 D1/D2/D3 作为三个不能联动的事件。** D1：代码+可信启动方案独立审核；D2：用户明确批准一个**新的精确许可字节**、独立审核用户/审核者身份与许可；D3：用户再次明确批准一次严格限定的真实执行，消耗唯一 grant。过往 30 次许可已耗尽。任何一层失败都不执行下一层。

## 三、现阶段能验证与无法验证的事实

**已经核验：** PR183 仅 memory-source 路径，测试 permit、参考 pins、一次性 marker、journal、RAW 审计离线连接正确；公开 live 入口始终拒绝。Git PR 和 CI 证据可继续用于独立代码审核。

**不能通过 GitHub 或本会话单方面完成：** 证明某个公钥确实归属于**用户本人**、另一个实际独立审核者的真实身份和独立密钥保管；确定用户实际 Mac 的 Python+动态依赖发行物来源、不可变 release 机制、可信时间来源或保护注册根的 OS 级边界。因此当前**不存在足以开启生产 D1 或申请 D2 的已认证信任根**。

没有可信来源时继续制造第二把临时 Ed25519 密钥、发布可编辑公钥 JSON、签署一份自称 complete 的本地 manifest，都属于**伪解阻**；严禁。

## 四、停止/继续决策及下一次最小外部输入

- **立即可做、无需 Mac 运行：** 冻结这份设计供独立审核；核对 PR183 approved SHA；更新仓库 handoff；准确记录尚未建立的信任来源、二角色授权与完全依赖闭包。不能接真实网络。
- **需要用户以后明确提供或核实的事实**（不要求把私钥放到聊天或 Git）：（1）哪个主体承担独立 reviewer 授权，其身份能否通过不同于操作者的渠道确认；（2）用户与该 reviewer 的公钥指纹如何在代码发布前带外验真；（3）Mac Python/cryptography 的实际官方发行物来源及依赖 hash/签名基线；（4）是否存在可审计的可信时钟及受保护的固定许可登记机制。以上缺失则保持阻断。
- **条件具备以后**：新单独 Draft PR 实现并独立审核真实信任根 bootstrap 与只读 release 校验，仍旧 `send_live` DENY；然后再按原 G/J/M 退出表接单一具体 sender/journal；只有新的完整 D1 approval 才能**讨论** D2。
- **条件不具备时**：正式停在 `D1_BLOCKED_AUTHORITY`，而不是用多个新 mock PR 继续“刷进度”。如果成本、安全门禁超出公开只读 F0 的实际研究价值，应提出 **原 D0 设计变更申请并要求用户批准**，而不是擅自削弱已批准的规则。

## 五、研究目标没有改变

F0 的真正下一决策是受单次新许可保护的免费 BSC **真实三路**同窗口 HEAD 来源增长与连续提交速度是否匹配；历史 serial 约 **1.045 block/s**、来源抽样约 **2.178 block/s**、fake 三路约 **1.740 block/s** 都不能证明真实持续追平。随后才可能讨论 24–48 h 的钱包签名 BUY/SELL 识别、普通 Router 实时对照、+60/+300/+900s 报价及独立分母。不得从“代码通过 464 次测试”推断 F0 完成百分比或交易盈利。

**当前结论：`TRUST_BOOTSTRAP_FEASIBILITY_BLOCKED_EXTERNAL_AUTHORITY / D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`。**

执行限制：`NO_NEW_RPC / NO_WS / NO_PERMIT_OR_SIGNATURE / NO_MERGE / NO_DEPLOY / NO_TRADES / NO_BACKGROUND`。本文件不生成密钥、公钥登记、nonce、运行命令或授权。
