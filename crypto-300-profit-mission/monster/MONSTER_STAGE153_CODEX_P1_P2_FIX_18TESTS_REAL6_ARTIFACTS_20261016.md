# Monster Stage153：Codex 1 P1 + 2 P2 安全修复，真实六历史Artifact双SHA全量复核

2026-10-16 Asia/Bangkok。原 Draft PR [#30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)（不可合并）。本次修复输入是用户转述独立 Codex 针对固定 `80ebab9a6f3533103858de9e321f037384e86fde` 的 `REQUEST_CHANGES`，新3缺陷=1 P1/2 P2。Codex原审读原AGENTS/Monster开发准则，在其隔离mac临时SQLite复现P1导致完整数据库被输出JSON替换，还复现2个P2；并自己重新验证六份原 Stage28 GitHub Artifact ZIP及内部JSON SHA，全部通过，1,128历史队列事件逐件吻合。审核员真实底层精确模型ID `UNVERIFIED`。本次作者修复完成，不得伪称其已由另一AI `APPROVE`。

冻结修复协议**先于代码** Git SHA `3304370785da2774e0ca6ac009fd35bd6a1da07f`：
[MONSTER_STAGE153_CODEX_P1_P2_FROZEN_REMEDIATION_20261016.md](MONSTER_STAGE153_CODEX_P1_P2_FROZEN_REMEDIATION_20261016.md)。

## 新固定源码SHA与真实证据

**本次唯一固定代码/单测/未变更workflow审核 SHA：`4553cb6b18c5aaf723072d17a39f9ad92f0629c9`**。

[真实GitHub Actions #38789077966](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38789077966) 已核对运行exact触发SHA为上值：`completed/success`，**3/3 Jobs SUCCESS**，Ubuntu 24.04 / macOS Python 3.12 均分别 **18/18 unittest PASS**，py_compile PASS。第三个Job**实际重新下载**之前已归档的六份 Stage28 GitHub Artifacts（来自原CI #38146403662），每一份封装 ZIP SHA256 + 内层原研究JSON SHA256 与原保存 proof 精确一致；重新核对全部1128行，再成功推送新摘要进同一PR（原Stage153 workflow核查源/测试/workflow Git blob与触发SHA一致才允许写回）。`NO_NEW_SCHEDULE`，不采集当前新市场行情、改Mac SQLite或重启Frank。

本次新归档：
- [六原始双SHA验证 + 1128队列机器summary](evidence/monster_stage153_stage28_1128_queue_lifecycle_summary.json) **Git blob `e4ce8ad5d00b76d56b06616208a6b7dc11541cb0`**，触发SHA=`4553cb6b18c5aaf723072d17a39f9ad92f0629c9`，审计器SHA256=`d33c24160fde670ecde064ca29dc3a4a32860111dc2899037bdc0f889cd89636`。
- [1128条真实原队列行](evidence/monster_stage153_stage28_1128_queue_lifecycle_rows.jsonl) Git blob **`beb066d13ed1bf9656a1d9153f003c4363aa849c`**，与修复前**完整逐字节相同**（不是本次凭空重写的事件流）。
- 与修复前原summary Git blob `0f24fb56b6cd9a3166f43ac7eed6ce9b3cc77e9a` 比较，除了固定触发SHA、审计源码SHA256和**新增的明确SETUP归属歧义指标**，所有其他原summary字段（每日期和总体）**逐字段精确相同**。

## P1：真正阻断的SQLite源库覆写现已在实现和测试层修复

原 `--sqlite-readonly <db> --out <db>` 在只读查询后通过Path.write_text截断源数据库、exit 0。该P1本轮由 `safe_new_json_output(target, sqlite_input, result)` 阻断：
- 输出前把输入库 `Path.resolve(strict=True)` 固定成已存在真实路径，检查 `--out` 的实际规范路径、已有路径的 `os.path.samefile`，保护**源库、`-wal`、`-shm`、`-journal`**（包括相对路径、符号链接、硬链接）。
- **所有原本已存在的任意输出文件均禁止覆盖**；只用Python `Path.open("x")` 独占创建全新JSON输出文件（基于 `O_CREAT|O_EXCL`，不会追随竞态symlink去截断现存源），写入真实换行；不能按同一地址再次覆盖历史json。已经存在的旧结果需要使用新的输出路径。只读输入连接仍 `mode=ro / PRAGMA query_only=ON`，未进行DB schema改写。
- Ubuntu/macOS真实单测通过 **CLI与数据库同路径、相对路径、symlink、hardlink、模拟WAL/SHM/journal关联文件、WAL hardlink/symlink、普通新JSON生成及二次同路径拒绝**，拒绝后源字节完全相同且 SQLite `PRAGMA integrity_check=ok`。
- 本工具尚未在用户真实Mac生产数据库运行，本测试只属于隔离历史研发，不是新的正式运行授权。

## P2a：`asof_ms` 不能把未来98个pending当现时可用

`queue_pressure(db, asof_ms)` 对**当前保存的**PENDING表内每条候选核查 `first_seen_ms<=asof_ms`，且若存在已评价5m K线，必须满足 `last_evaluated_bar_ms+5min<=asof_ms`，任何未来候选/未来已完成bar立即 `STAGE153_ASOF_FUTURE_PENDING_OR_COMPLETED_BAR`，不能混入eligible/backoff/容量统计。新机器输出 `snapshot_scope=CURRENT_STORED_PENDING_ONLY_NOT_HISTORICAL_RECONSTRUCTION`，说明**只能检查当下SQLite快照，不能依靠当前队列最终状态重建任意历史时点PENDING全体**；未来retry_after是合法 backoff，不因大于asof被拒。合成98个候选在asof+1min首发的负例、未来bar负例、合法98 asof测试均PASS。

## P2b：修复候选/事件匹配，同时尊重真实Stage28档案信息损失

- 所有队列候选单独按SQLite主键 `id` 唯一，且 `(symbol,first_seen_ms,deadline_ms)` 作为episode不能重复，堵住原 `(id,symbol,time)` 元组允许重复ID的漏洞。
- `LATE_REVIEW` 必须唯一对应原队列一个 `status=LATE` 事件：精确`symbol + payload.first_seen_ms + payload.deadline_ms`，`observed_ms>deadline`，匹配后一次性消费，拒绝重复LATE覆盖另一候选及提前到WATCH之前的伪造时间。旧123/123 LATE仍完全相符。
- 原 Stage28 `setups` 数组历史只保留 `symbol` 与 `utc`，**不保留生成该SETUP的候选id**。初版企图强制按timestamp窗口唯一匹配，真实六份原始归档揭示 **2/828** SETUP与两条 `EVALUATED`候选15分钟窗口重叠（2025-11-04一个、2026-02-04一个；例如2025-11-09T08:21Z的 MBLUSDT）。强制唯一认领并不合理：**这不能证明原始K线篡改或D1重复下单**。本次在保留历史原文的前提下对每条SETUP检查有效UTC、已评价episode时窗存在、拒绝 `(symbol,UTC)` 重复，最后按每币执行注入匹配的**可行性检验**（必须存在一个不重复消费候选id的对应关系），对无法唯一认定的2个事件明确计入 `D1_SETUPS_with_multiple_plausible_EVALUATED_candidates` 并注明 `NOT_IN_ORIGINAL_STAGE28_REGISTER_MATCHING_EXISTS_ONLY`。不会编造具体映射的producer id；这是冻结方案面对原始证据限制后的有证据更新，而不是放过无效/重复SETUP。
- 测试独立构造旧P2的四类复现：相同队列主键不同币、无此symbol的SETUP、LATE先于WATCH、复制一条LATE覆盖另一条；另外新增有效重叠窗口必须明确报告归属歧义、完全重复SETUP必须拒绝、多个SETUP不可能注入不同episode必须拒绝。Ubuntu/macOS全18项PASS。

## 修复前后机器总量完全不变

| 统计 | 原Stage153审计 | 新固定SHA |
|---|---:|---:|
| Stage26 WATCH原始到达 |1132|1132|
| Stage28共享队列原候选 |1128|1128|
| 最终已评价 |1005|1005|
| 最终LATE |123|123|
| 真正SETUP |828|828|
| 生产累计选取 |3542|3542|
| 生产累计延期/重试 |2414|2414|
| 2026-02-06 00:36UTC同时WATCH |98|98|
| 该次最终LATE / EVALUATED |91/7|91/7|
| 原档案SETUP来源不唯一 |旧版未检查|**2/828，标注未知具体id**|

过去已发表的Stage28共享D1真实产物自身并没有因此新增错误，本轮是**新增审计器**的语义和安全修复。本轮没有重新下载原1421份Binance 5m/其CHECKSUM，不得声称独立官方源全量复核。真正同一共享D0 + Spot/Futures生命周期、真实首次HTTP、时效、Gmail、成交流动性、正净利润仍未证实。

## 代码审核和放行

本次新固定SHA需要**另一独立Claude/Codex复审**三项P1/P2是否关闭，尤其真实SQLite隔离恶意路径负向、源双SHA、两处真实重叠歧义；原旧 `REQUEST_CHANGES@80ebab9...` 不能迁移成APPROVE，Stage152 `APPROVE@71a041...` 仅其独立原范围。

状态仍 `G0 PARTIAL / G1 NOT_SCORABLE / G2_G3 NOT_PASSED / G4 UNKNOWN / G5_FULL_RELEASE NOT_PASSED / G6 NO_GO`，`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，Frank原状、Stage99停用、不创建新定时任务。本轮源修复及真实CI完成不等于模型盈利、Mac上线或者用户已授权交易。
