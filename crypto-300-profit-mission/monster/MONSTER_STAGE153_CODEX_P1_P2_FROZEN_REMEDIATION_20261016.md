# Monster Stage153 Codex 固定 SHA REQUEST_CHANGES：P1/P2 最小修复冻结协议（先于源码改动）
日期：2026-10-16 Asia/Bangkok。原 Draft PR #30 仍不合并/不部署。本次独立审核者报告为 Codex，底层精确模型UNVERIFIED。仅用户转述的审核内容，不是假称GitHub正式Review。

## 审核来源与不变事实

固定拒绝审核 SHA `80ebab9a6f3533103858de9e321f037384e86fde`，审核 `REQUEST_CHANGES`：0 P0、1 P1、2 P2。仍保留 Stage152 独立 Codex `APPROVE@71a041405352c9e2210d93dff9c2685149809e52` 原结论，不把另一SHA批准扩展到当前。审核员 independently 重新下载、验证6份原Stage28 GitHub Actions Artifact ZIP及内部JSON SHA256，全部与Git proof吻合；独立复算 1132 WATCH /1128队列行/1005 EVALUATED/123 LATE/828 SETUP/3542选取/2414延期；98同秒 WATCH 91 LATE/7 EVALUATED；机器summary与1128 rows逐字节吻合。旧数据归档原样保留，不改历史回测策略、D0/D1或真实现时结论。

## 精确三处修复与门禁

- **P1 文件丢失（最高优先）**：stage153只读CLI `--sqlite-readonly <db> --out <out.json>` 在 `out == db` 时曾成功退出并把输入SQLite覆写成JSON。输入数据库及 `-wal/-shm/-journal` companion不可被作为输出文件：在连接/写出前核对规范化真实路径、符号链接别名、硬链接 samefile/inode 别名及companion，防止未来尚不存在的companion路径被抢占。**CLI JSON输出采用安全创建（独占新文件 `x` 模式，不覆盖任何已有文件），拒绝既存输出**。所有危险路径拒绝时原SQLite、现有相关文件字节和可打开性必须不变；输入数据库查询仍sqlite readonly+query_only。新增CLI真正入口测试，直接同路径、相对路径、symlink、hardlink、WAL/SHM/journal和普通安全输出等负例，且普通输出文件不得覆盖已存在文件。任何修复不得借此修改用户Mac数据库。
- **P2 ASOF读未来**：`queue_pressure(db, asof_ms)` 针对**输入已保存的当前PENDING快照**，明确不重构指定时间的历史完整PENDING列表；若候选first_seen或last_evaluated_bar_ms时间晚于asof，则拒绝（不能误认未来98笔为当前eligible）。输出必须明确 `snapshot_scope=CURRENT_STORED_PENDING_ONLY_NOT_HISTORICAL_RECONSTRUCTION`。已见记录的 `retry_after_ms > asof` 是有效backoff，不误杀。
- **P2 候选与历史事件对账**：按 `candidate_queue.id` 独立唯一；LATE以 `symbol + payload.first_seen_ms + payload.deadline_ms` 精确映射唯一状态=LATE的原候选，`observed_ms > deadline`，一次一候选、不可重复消费、不可漏掉；SETUP源rows仅含 `symbol/utc`，按照原共享SQLite原候选EVALUATED `first_seen<=utc<=deadline` 且恰好一条进行一致性验证，不得拿原产物没有保存的全部D0原事件声称已验证。对不同symbol复用同候选ID、SETUP假symbol、过去的LATE时间、重复一条LATE遗漏另一条加回归测试。原6份SHA锁定原始JSON应全部通过严格验证，新的派生rows/summary除审计脚本SHA/触发SHA等source-tag变化外原总量及所有有效指标应保持不变。

## 验收顺序

1. 本冻结文档先入原Git分支后才能提交源码；仅改Stage153独立审计器、配套测试；冻结Stage153已有工作流只随源/测试push运行，源身份维持触发SHA绑定。
2. Ubuntu24.04/macOS单测真实运行，包括上述所有负探针、SQLite文件字节不变和shell入口安全输出；CI第三Job重新取得6份Stage28原始Artifact、双SHA并完整1128逐件重放、写回Git真实报告（若CI失败不得宣称PASS）。
3. 形成新的固定代码SHA、真实CI link及摘要Git blobs，发送给另一独立AI复审三项和防回归；不把作者自测或原Stage152局部APPROVE当新审核批准。
4. 不改变Frank、Stage99、原D0/D1、资金模型或参数，不恢复Mac服务、不发送Gmail、不交易、不合并、不创建新schedule。仍 `G0 PARTIAL / G1 NOT_SCORABLE / G2_G3 NOT_PASSED / G4 UNKNOWN / G5_FULL_RELEASE NOT_PASSED / G6 NO_GO`。
