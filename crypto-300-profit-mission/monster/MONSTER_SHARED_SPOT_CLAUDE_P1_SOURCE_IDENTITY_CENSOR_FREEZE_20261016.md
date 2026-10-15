# Monster Shared Spot 独立Claude固定 0ffe44e 的 REQUEST_CHANGES：P1/P2 修复事前冻结

日期2026-10-16 Asia/Bangkok，原Draft PR #30。根据用户提供的独立Claude review（准确底层模型`UNVERIFIED`）：审核SHA `0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`，最终`REQUEST_CHANGES`，原D0单SQLite和因果结构大体正确；新3 P1（758缺源分母/称谓、使用方自封官方FULL认证、758原名单与事前类别/2 Unicode记录不完整），新P2（OHLC、源失败被计deferred、census缺负例、来源逐日SHA预存、Stage152遗留历史review表述、CI后续HEAD前移）。这不是另一AI当前版本批准。

## 严格修复选择：不要假装可重放没有行情的758币

原Stage26确认为758x6=4548个原历史试验组合，但原Stage26通过完整216h分钟来源仅2719，余1829缺源/不完整；2026-02-04有445完成，313不完成。若让未验证313个币进入`observe_snapshot`，需要捏造当时price/volume，会污染真实信号；所以**禁止此类合成填补**。现有全758原始分母必须出现在每日期输出的完整`coverage`与各币`CENSORED_SOURCE_MISSING_OR_INCOMPLETE`记录中；真实D0和D1只对**事前由已SHA锁定原Stage26/Stage28结果定义且已有官方发行者SHA的SOURCE_COMPLETE_SUBSET**尝试，不许当全758 Spot。任一声称`FULL_758_OFFICIAL_VERIFIED`的API路径在此阶段**明确fail-closed**（直至真实758全部源具备后另立新事前冻结），不可只靠调用方提供758名单/10个标志启用。

## 身份溯源：不能伪造2026-10-11之前的完整758成员预注册

原Stage26 Prereg原文只有`504 current`+`254 archive-only` =758个尝试标的，另记`2 unsupported Unicode archive symbols`，但没有当时单独758成员名单的预注册hash。**这是历史溯源的真实缺口，不能通过今天生成“追溯预注册”消除**。今后新完整名单以原36份SHA锁定历史Stage26 artifact派生且已由CI验证的758成员及sha作**“2026-10-16二次冻结”**；`504+254=758`，2 Unicode **不在这些ASCII 758已尝试symbol里**，本轮不映射、不加到760分母，也不冒称已查明原Unicode具体名字及当时归类。PIT listing未验证，真实市场全体不可宣称。这份二次冻结可保障**未来重算身份不漂移**，但不能回溯补齐旧文件不存在的事前完整名单。

## 来源真实性与显式边界

- 发出`source_origin_verified=true`不能依据公用`market_coverage_label`或调用方`verified_published_sha256=True`字段。通用`run_shared`只运行注入到缓存的历史/合成数据，**没有自己认证外部下载**, 返回`source_origin_verified=false`及对应来源级别。仅受控`run_official_subset`从原Stage26`read_complete_216h`真实取得10份发行者1m ZIP+CHECKSUM，核实连续性、每日SHA/日期、和真正返回的官网校验回执，才可标记`source_origin_verified=true`，同时明确是`SAME_HOST_PUBLISHER_CHECKSUM_AT_RUN_TIME`，尚无所有未来样本的事前逐日commit SHA。现有BTC/ETH 20天sha已在Git，冻结后可作为重复回归比对，不能说所有758分钟源都有首次下载前Sha。
- `prepare_symbol`必须逐分钟校验`low <= open,close <= high`，反例要测；D1读不到本应存在的闭合K线时不应被老核心简单当正常可重试deferred，回放须在进入`process_queue`前校验全部分钟/closed5m且异常源抛错并让整个历史研究失败，不能吞掉真实源断裂。不得修改生产`monster_v4_shadow.py`的错误处理。
- 增加census无真实archive时可运行的负测试：不同日期名单、缺一个原shard、total造假、SHA字节篡改（stage26原`load_zip`承担ZIP/内部JSON核对）；同时保留真实36原artifact GitHub CI。
- Stage152是否旧summary：本阶段不修改旧 Stage152 模型/已审SHA，审查文件间差异时严格保持其此前单独`APPROVE@71a041...`和来源级别，不擅自宣称新改旧版本已批准。
- CI写回源码 SHA核查，审查必须固定触发的源SHA，研究结果后续commit可以后移HEAD，只要模型/测试/workflow无漂移。NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE，Frank/Stage99不动，G4 UNKNOWN/G6 NO_GO。

## 验收顺序

先独立提交本冻结协议及原758成员来源的二次冻结json，才修改共享引擎/测试/CI；真实Ubuntu/macOS新单测、36件旧Stage26原ZIP+内JSON双SHA和20件BTC/ETH官方新minute数据验证，报告仍如实保留真实零信号控制；固定新SHA及CI机器证据后交其他AI复审。大规模445高压来源耗时/费用另标，用户不需Mac操作，不改原正式D0/D1或真实生产。
