# Mission Monster Stage153：固定SHA独立复审提示词

请由另一独立 Codex/Claude 做只读代码+源证据复审，不要仅复制作者CI结论或修改主工作区。

仓库 https://github.com/lxxlx2/ChatGPT_mission_record ，Draft PR #30 https://github.com/lxxlx2/ChatGPT_mission_record/pull/30。
唯一固定代码审核SHA：4553cb6b18c5aaf723072d17a39f9ad92f0629c9。旧Codex REQUEST_CHANGES SHA：80ebab9a6f3533103858de9e321f037384e86fde。PR HEAD已前移时仍固定checkout，不偷换版本。Stage152原独立APPROVE@71a04140保持原范围，不适用于Stage153。

事前修复协议先于源码commit 3304370785da2774e0ca6ac009fd35bd6a1da07f。请先阅读 Monster AGENTS、模块开发规则、长期开发节奏及 Stage27/28/153 原报告，然后diff本次仅改动的Stage153审计器与测试，工作流未改：
- crypto-300-profit-mission/local-agent/scripts/monster_v4_stage153_source_locked_d1_queue_lifecycle.py
- crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage153_source_locked_d1_queue_lifecycle.py
- .github/workflows/monster-v4-stage153-real-shared-d1-queue-lifecycle.yml

Codex先前发现1 P1及2 P2，新版须实测全部以下负例：
1. P1：实际使用隔离SQLite运行CLI --sqlite-readonly ... --asof-ms ... --out 同一路径、相对路径、symlink、hardlink、WAL/SHM/journal及这些sidecar的别名；必须拒绝而保留SQLite字节和PRAGMA integrity_check=ok，sidecar不变。普通新JSON输出可以写入，重复指定已存在out必须拒绝。请检查新的safe_new_json_output能否在路径竞争下仍被绕过。
2. P2 asof：构造98条PENDING但其first_seen_ms = asof + 1分钟，必须拒绝未来候选；已完成5m bar也不得来自未来；合法retry_after未来值仍是backoff。输出必须说明CURRENT_STORED_PENDING_ONLY_NOT_HISTORICAL_RECONSTRUCTION，不能假装能重构任意历史快照。
3. P2事件：candidate_queue.id单独唯一，LATE symbol+payload.first_seen_ms+payload.deadline_ms必须准确唯一对应已逾deadline的候选且只消费一次；拒绝同id不同symbol、LATE早于WATCH、两LATE用同一事件替换。SETUP必须有合法symbol/UTC、EVALUATED候选时间窗，禁止同symbol同UTC重复和对候选不可能的重复消费。

关键原始证据限制：旧Stage28的SETUP只保留symbol和utc，没有原候选ID，2025-11-09 08:21UTC MBLUSDT及2026-02历史另一个共2/828 SETUP落入两个合法已评价episode的重叠15m窗口。新版核实存在完整事件到候选的单射可行匹配，不声称唯一知道producer。请审查此实现是否严格、防止错配，并真实验重叠歧义标记与重复设置拒绝。

原Source-Pinned Actions #38789077966 https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38789077966，触发SHA正是4553cb6b18c5aaf723072d17a39f9ad92f0629c9，3/3 jobs SUCCESS；Ubuntu24.04和macOS各18/18单测和py_compile通过；另一Job重下旧Stage28 Actions #38146403662六份历史artifact ZIP，逐一ZIP SHA256、内层JSON SHA256与原Git proof匹配并重新核验全部1128行，再成功写回原Draft PR。
新摘要 Git blob e4ce8ad5d00b76d56b06616208a6b7dc11541cb0；新版审计脚本SHA256 d33c24160fde670ecde064ca29dc3a4a32860111dc2899037bdc0f889cd89636；行证据Git blob beb066d13ed1bf9656a1d9153f003c4363aa849c（与修复前逐字节相同）。请对比原旧摘要blob 0f24fb56b6cd9a3166f43ac7eed6ce9b3cc77e9a，除触发SHA/审计源码SHA和新增2个歧义标识外全部统计字段完全不变。
六日期全部1132 WATCH、1128 candidate、1005 EVALUATED、123 LATE、828 SETUP、3542 selections、2414 deferred，98同刻WATCH中91 LATE/7 EVALUATED。这里源是旧Stage28已下载过的Binance发行5m研究输出的双SHA锁定Artifacts；本轮没有重新核实1421个Binance 5m源，也没有真实全市场共用D0/Spot+Futures竞争、Gmail真实送达和实际净收益。不能推断91笔真实盈利机会漏失。

复审请给出审核身份及精确模型字符串（无法核实写UNVERIFIED）、唯一固定SHA、自己实际运行的测试/源核对和是否重下原artifact、原P1/P2关闭状态、新增P0/P1/P2及可复现行号，最终明确APPROVE/REQUEST_CHANGES/BLOCKED。APPROVE仅为代码修复审核，不代表业务盈利或合并授权。NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE，G4 UNKNOWN、G6 NO_GO，Frank/Stage99不变。
