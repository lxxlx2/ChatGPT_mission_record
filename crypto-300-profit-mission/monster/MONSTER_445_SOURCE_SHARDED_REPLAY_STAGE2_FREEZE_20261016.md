# Monster 445官方分钟源分片缓存、全445唯一SQLite回放：代码前冻结（2026-10-16）

继[2026-02同一SQLite因果回放合同](MONSTER_SHARED_SPOT_CODEX_APPROVE_1154E97_AND_445_HIGHPRESSURE_EXECUTION_FREEZE_20261016.md)后，已从真实官方80份日ZIP/CHECKSUM复核得到字典序8币4 WATCH，其中2026-02-06 00:36Z恰有3币同刻信号，仍低于原生产D1的每轮8容量上限。新8币piloter固定`84a8d35e8f52c5c554886eeb926b2e66ec7a442d`源码尚未获新的独立review；**不许由于8币通过就把445或758宣称成功**。

本轮在任何实现前冻结以下工程协议和门禁：

1. 唯一研究日期 `2026-02-04T06:00Z`、原758历史尝试分母和313来源删失不变。全部`445`条源完整成员来自[原36Artifact双SHA派生的secondary freeze](evidence/monster_shared_spot_stage26_original758_secondary_freeze_20261016.json)，Git blob `8467bfc0db7cb888f805f30eaae301a812fbb20d`，名单本身二次冻结而非当年PIT；不能改信号核心、指标、筛选、费用、队列极限或手动挑选有信号的币。
2. 将原445名单**按字典序每16个一份固定分片**：0–27号，0–26各16个、27号13个（`27*16+13=445`）。每份必须包含 exact start/end roster、符号的`10`个官方Spot1m日ZIP/.CHECKSUM SHA256、每币原`12960`条UTC连续分钟行及符合原Stage26`read_complete_216h`的校验通过回执、最终每币实际source rows SHA256、producer Git固定SHA和研究源版本。离线打包为zip，只保留**原真实source生成的数据，不纳入生产数据库**，并存GitHub Action artifacts而非将几百MB原分钟数据commit到Git。可在Git存每分片的小SHA/规模清单。
3. 每份只用原Source strict reader`read_complete_216h`下载全部十天，禁止从旧Stage26的WATCH列表重建行情；分片所有成员有缺源时fail closed，标`SOURCE_RECHECK_FAILED`而不是把成员静默剔除变成441。官方.zip与.CHECKSUM来自同host，自洽不意味着独立签名；原8币源哈希是原先下载后归档，不能改称事前预承诺。
4. 首次真实分片**固定测试分片1（字典序序号16–31，共16币）**。这是来源资格名单的固定第二片，不按历史WATCH挑币。限制单Job worker≤2，且不启动全部28分片并行、不能重启Stage99、不能无约束429重试。记录下载失败码、运行时新鲜度/CI_SHA。
5. 分片合并器在所有28份出现前**必须严格不做“445共同D0/D1正式结果”**。它检查每片源生产代码指纹、预注册成员、manifest与ZIP文件唯一、每币归档sha重新计算、12960分钟时钟一致、10天SHA以及分片完整性；缺一份、duplicate、错身份、来源文件坏、未来分钟、假"FULL"一律阻断。合并全部分片后才构造一份统一SQLite并用旧审核过的`monster_v4_shared_spot_d0_d1_original_core.run_shared`做3360轮、每轮全445共同D0和D1 limit8的单池研究。分片可并行采源，**模型回放不准逐片各跑D1后将计数相加**。
6. 新CI先完成（a）Linux/macOS合成单测，（b）固定分片1官方160份日ZIP+CHECKSUM（16×10）真实采集+机器manifest SHA（c）来源artifact回读校验及相同GitSHA校验，归档只有轻量JSON入Git，保留下载的源ZIP为Actions artifact，用于未来28片重合。没有schedule，没有Gmail/Frank/交易/Mac权限。
7. **防工具伪验收**：真正可运行的`445`一库/完整原高压`98`同刻是否复现只能在28/28件全部真实来源重验且一次共同SQLite run_shared成功后标DONE。任一缺源只发布阻断报告，而不是假设“满445”。其余313老CENSORED永不填零。旧Stage28`91 LATE`属人工注入WATCH结果，不代表本次新共享D0结论，更不是盈利损失。
8. 新源码和固定CI后交另一AI对**新SHA**独立review，旧P2`1154e97... APPROVE`不覆盖新分片管道；保留`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`、Frank与Stage99不动。

声明：本协议是来源分片执行冻结，不是28/28已完成，也不是来源ZIP永久可访问保证。
