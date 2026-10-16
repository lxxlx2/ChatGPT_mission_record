# Monster 零quote V2 代码复审已通过；转入445源分片实采（2026-10-16）

## 复审裁定与固定范围

独立审核者 Codex；确切底层模型 `UNVERIFIED`。针对**唯一固定代码 SHA `ef30be7bc67588b39efe552b39ab240843253846`** 的 V2 研究模式修复，结论 **APPROVE**。前轮 `dfceade891909bf374ce3e790f3aef33746f2938` 的 **P1临时retry掩码SQLite异常持久化已CLOSED、P2已成功评价D1在恰好deadline遇真实zeroquote误分类已CLOSED**；本次限定范围内没有新增P0/P1/P2。初始review`REQUEST_CHANGES`的严格历史记录不回溯篡改。

独立审核已在detached checkout重跑实际单元测试11/11、源D1损坏负例、真实SQLite SQL trigger失败及历史reader异常后close/reopen、部分mask写入中断/恢复写入中断（**恢复失败时仍可能遗留mask，但必须阻断模型输出**）、deadline -1/0/+1ms × 先前是否成功D1评价 × 是否曾记录WAIT_ERROR的12边界测试，以及真实32币原GitHub Actions source Artifact SHA再验和3360tick实跑；[固定CI #38862965003](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38862965003)四Job成功。**Codex没重新向Binance下载所有320个daily ZIP，不得写成独立重下**。

真实32币历史32个source-complete成员结果为：共享D0自主WATCH29（与原Stage26同源逐币WATCH29、全部UTC相同），V2研究D1 EVALUATED27、SOURCE_UNSUPPORTED_D1_ZERO_QUOTE2（均ACAUSDT）、LATE0、SETUP13、INVALIDATED7、累计selected134/deferred105、重复zeroquote等待槽10；2026-02-06 00:36UTC 7币同时WATCH、真实最大同tick7。**尚未撞到每轮8预算，未观察完整445共同D0/D1容量竞争，亦非盈利证明。** V2测试是与旧production源码不同的源不可评价分类，不批准替换生产队列策略。G4 UNKNOWN、G6 NO_GO。

## 下一任务：实际补齐445完整来源的固定相邻分片

使用事前锁定[28份x16原分钟来源SHA证明+统一SQLite才可全445回放的协议](MONSTER_445_SOURCE_SHARDED_REPLAY_STAGE2_FREEZE_20261016.md)，历史观察分母758，2026-02-04当日source complete445、原CENSORED313；source full名单从原36份Stage26产物二次锁定，并非历史PIT上市证明。固定字典序28 shard（0–26每16、27尾13）；**shard00/01已真实源存档，剩余26片02–27合计413币**。

1. 在构建新可执行采集流程**之前**冻结一份可复用的**单次两片**工作流：本轮预选`02、03`，分别各16币，固定次序并**max parallel=1片、每片source workers<=2**，所以不会一次并发上千官方下载。每片10 UTC发行者原日Spot1m ZIP + 同host CHECKSUM、原连续12960 1m bars/coin，严格不补缺、不替换symbol、不从WATCH名单倒推。32币这轮=320份原官方日ZIP+校验文件，仅作为新源资格重取，不跑任何独立分片D1。
2. 工作流只`push`自身文件的首次创建或通过**显式手动workflow_dispatch**执行；参数`start_shard`只能选偶数2..26，自动固定相邻一对。绝对没有`schedule`或自动循环下一批；以后人工指定4/5、6/7……26/27。测试 Ubuntu/macOS 单测和py_compile，只读下载至GHA artifacts；每份source ZIP含真实分钟原行、manifest SHA和每币原source SHA，约定artifact保留60天，Git只保存轻量proof及具体triggerSHA。每片`source_origin_verified_at_collection`必须true且原`read_complete_216h`实际走官方下载，来源发行者CHECKSUM同host并非独立签名；SHA代码提交本身不是事前市场信号。
3. 两份original artifacts必须在归档Job用**同一GITHUB_RUN_ID和source SHA**回下载，再解包验 ZIP原SHA、manifest SHA、每币分钟JSON SHA、全部原本16 frozen members/每币10来源日、有且仅本次2片、最终proof写Git。若官方publisher返回404/429、未提供日文件、返回时间不一致、任何成员failed、若证明路径已存在（本次拒绝覆盖此前采集），整batch不能标成功；已有成功单片GHA Artifact可单独保留，但不能以半批成功发布两片完成证据。
4. 28片完整归档前**禁止宣称真正445共享回放**。此前已写的全445 oneSQLite组装器需要重新检查真实全部28份原始包、每成员SHA后才可能算，且原production旧核心在合法0quote会fail-closed；本V2源分类独立新实验，不得偷改旧`run_shared`或原模型。后续充分验证容量预算、实时告警送达、并单列研究盈亏/OOS/手续费滑点才有机会评估生产。
5. 独立APPROVE仅适用于上述固定V2源码，**不自动批准尚未独立审核的source shard pipeline、batch workflow、full445运行或merge/deploy**。新workflow代码必须按Mission开发规范验证和二审。保持 `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，`G0 PARTIAL/G1 NOT_SCORABLE/G2-G3 NOT_PASSED/G4 UNKNOWN/G5_RELEASE NOT_PASSED/G6 NO_GO`；Frank、Stage99、Mac生产SQLite均不触碰。

本文件先于新增可执行批量采集workflow提交，作为未来对话重复使用的source进度约束。
