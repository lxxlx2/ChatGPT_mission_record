# Monster 445真共享D0/D1：提前冻结固定前32币两片复验（2026-10-16）

原分片第一轮[GitHub Actions #38840401636](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38840401636)已经证明固定 shard01 的16币160天官方Spot1m ZIP/CHECKSUM实际有效，source ZIP GitHub Artifact ID `12021445690`，保留60天，原内部档案ZIP SHA `9128f46b15361f72d88efb46c03bdd209f2ebdfdff419b1e0c08160eeac3df77`，Git[source SHA receipt](evidence/monster_feb445_shard01.proof.json)，CI 4/4 SUCCESS。

为进一步扩展真实队列压力而不是对成功8币重复试验，本轮**在新的32币共SQLite研究代码前事前固定**：
- 从冻结2026-02-04 `445`完整来源资格名单中按字典序取**分片0和1全部32币**，非按原WATCH或未来收益挑选；758原人口/313缺源仍保留，`445-32=413`个完整但尚未这轮共同回放。
- 分片1只能复用旧CI已SHA锁定Artifact `12021445690`，从GitHub原Artifact ZIP API下载并重新校验 ZIP与内部分钟原始每币SHA；绝不能简单信代码给出的`verified=true`。分片0实际经原Stage26 `read_complete_216h`新下载16币×10天=160份官方Spot1m日ZIP+同host CHECKSUM，保存内层源压缩包及真实 SHA 到GitHub Artifact，只有校验成功才允许汇总。
- 收集后的**32币原分钟数据经两个分片source manifest一一校验和同一SQLite连续3360轮**原V4生产`observe_snapshot(full32)`后紧随原生产`process_queue(limit8)`，不能分别跑每片的D1再拼总数。旧Stage26每币`scan_continuous`必须使用同一source，独立重做32币WATCH UTC匹配；重放时发生的实际并发、多次选择、backoff、候选LATE、SETUP、INVALIDATED以事实写入报告。
- 针对2026-02-06 00:36UTC原Stage28 98个同时WATCH，计算此次32币由**新共享D0自己产生**的同时WATCH数，以及真实共队列D1完成/迟到。低于8无需自行补旧Stage28事件。超8也不是全98复验，只报告32币子集。
- 数据不可验证、枚举非32、坏minute、错时钟、重复source、下载失败、旧核心drift、坏D1来源一律中止。本轮研究非OOS、非全445、非758/PIT、无真实净收益或订单许可。
- 分片0/1必须分别保存Archive ZIP SHA、每币10天原官方SHA。CI只在源码push/手动触发，不创建schedule；任何未来完整445另需28/28档案，不将两片冒称全445。原Mac/Frank/Stage99无操作。审批门槛依旧`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`，新增代码CI通过后再交另外AI固定SHA review。
