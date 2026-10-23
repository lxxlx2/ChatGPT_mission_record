# ADR-004 — Monster 妖币产品主线恢复、BSC 来源研究分离及下一交付顺序

- 日期：2026-10-23（Asia/Bangkok）
- 决策：**PRODUCT_MAINLINE_RESTORED / IMPLEMENTATION_PRIORITIES_APPROVED**，来自用户确认“我们不是做妖币模块吗”后“开始吧”的明确继续指令。
- PR：**仅** [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，分支 `research/monster-v4-local-discovery-20261010`；本次审计起点 HEAD `6876531c027778eaa3670ed73b15ca4a1249f4fa`。
- 性质：对**整体产品的范围与研发顺序**作治理纠偏；**不**改变已冻结 Stage77 G0–G6 量化验收、Stage163/166 的T0/未来窗口、旧样本或 BSC ADR-001~003/2026-11-02 P0 止损条件；没有新下单/费用/阈值/模型许可。
- 当前权限：`G0 PARTIAL / G1 NOT_PASSED / G2-G3 NOT_PASSED / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。Frank/其他模块及其生产进程不可更动。无后台/ChatGPT Automations/launchd/cron/GitHub schedule，新采集仅依用户显式聊天指令。

## 1. 纠偏依据：BSC 是数据源，不是 Monster 产品

**原始产品目标**是跨指定场所及时发现可能产生可实现净收益的少量异常代币，保留未触发、正常和失效候选，不漏原始WATCH，不将历史高点当真实收益。早期获批的**首版正式验收**见 [Stage77 标准](../MONSTER_STAGE77_CORE_MODEL_ACCEPTANCE_AND_BOUNDARY_FREEZE_20261013.md)：**Binance Spot + USD-M 两个明确分开的场所**先完成 D0 全市场发现 → D1 WATCH/SETUP 有效升级 → D2 同时点实际交易能力与经济风险 → 独立验证/Review → 经单独批准的投递与隔离Mac交付。

10月19日起的 [早期链上架构](../MONSTER_EARLY_ARCHITECTURE_CONTRACT_V1.md) 选择 **BSC 优先**是探索链上DEX真实新池/代币创建/税/双向交易来源的专项研究，**不是取代整个 Monster 的目标**，也不是使 Binance Spot/USD-M D0/D1 研发被 BSC 历史PIT未通过所禁止的总门禁。它的BSC源范围继续独立成立：2025-07-01冻结 V2 30、V3有界窗口、Four.meme 538历史状态等，不把这些源拼成全BSC，也不将BSC失败外推为Monster失败。Solana/其它DEX属于独立后续适配，未具真实源时一律 `NOT_IMPLEMENTED/NOT_COVERED`；不能宣称已覆盖全链或所有妖币。

本ADR**限制此前“BSC P0占用Monster所有主线开发”的资源排他性**，不倒改BSC实验合同、不混样本/成功率、不以Spot价格源替代DEX交易可达性。未来若改变具体 BSC 策略样本和费用/功效合同，仍须按照原架构单独履行ADR审批。

## 2. 实际远端代码和已审事实库存（2026-10-23，未重新执行原回放）

| 工作流 | 已有实现、已可复用部分 | 实际仍缺，不可写DONE或复活失败模型 |
| --- | --- | --- |
| **D0 全市场身份/发现** | `local-agent/scripts/monster_v4_shadow.py`原D0和独立SQLite；Stage163原始Spot官方T0 HTTPS ZIP SHA `b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b`，冻结**511活跃Spot USDT+214 BREAK**；Stage166 `monster_v4_stage166_spot511_official_1m_intake.py`已有独立Codex `APPROVE@30a87f0a`和真实CI验证的离线Source admission工具 | 10月17–24日真正完整Publisher日1m未曾在Stage166源报告中验收，动态中途上/下架、非加密身份/符号、无信号币和CEX时钟缺口不能凭静态T0删除；具体未核实的未来源数量不得猜测。G0仅PARTIAL |
| **D1 排队与升级** | 原 `monster_v4_shadow.py`候选队列、Stage153 lifecycle，Stage162同8槽FIFO/Fair8独立Codex `APPROVE@b85dee96`；冻结旧445真正全局A/B：有效首评172→199，原120 SETUP完全不变；Stage165独立 `APPROVE@dc9d09eb`查证新增27个全部因真实当时15m成交额比值低于1.5未变SETUP | 该445只有445/758源完整且同日回看，未见未来OOS增益；不重调已曝光27、不将早评改善包装成BUY或收益；真正新Spot窗口同场所FIFO/Fair8 paired回放及不漏候选分母仍需实际数据 |
| **D2 交易可执行性与损益** | `local-agent/scripts/monster_v4_stage90_d2_execution_proof.py`（真实双侧L2证据与滑点检查）、`monster_v4_stage120_exchangeinfo_execution_rules.py`（USD-M身份/过滤规则）、Stage163的Spot T0当时BBO原字节和静态报价研究 | 没有历史每个WATCH/SETUP发信后**对应时点**原始L2与退出盘口、真实gas/fee/tax/可成交量或用户指明研究名义金额；未知则只报告研究WATCH/SETUP和 `EXECUTION_UNKNOWN`，**不默认30U/300U、不制造BUY/净收益**。Stage132 首次动量入场毛价代理为负，不得用未来HIGH打翻 |
| **用户可读机会与通知** | 已有 `local-agent/scripts/monster_v4_opportunity_snapshot.py` 只读SQLite工具及19项原测试，能够说明source是否完整、历史WATCH/SETUP/过期及无BUY原因；原Shadow已含SQLite状态/通知研究接口 | 实际Mac产品未部署，无当前真实持续行情、端到端outbox投递readback或Frank隔离运行验收；只能在离线原SQLite上做源/状态回归。不得仅凭研究历史阅读器称实时产品DONE |
| **DEX链上来源适配** | `local-agent/mission_agent/early/` 的 V2 PIT、V3受限源、Four.meme index、asof等离线研究函数，既有2025-07-01冻结P0报告与ADR-003 D0设计 | 仍不能建立跨V3/launchpad完整BSC分母及2025 contemporaneous `available_at`、统一金额可卖性；与Spot/USD-M单独评估。**旧BSC P0截止2026-11-02不变**，未获授权不得在Mac/云端持续采集 |

证据入口： [模块开发规则](../MONSTER_MODULE_DEVELOPMENT_RULES.md)、[原V4架构](../MONSTER_V4_MODEL_AND_LOCAL_ARCHITECTURE.md)、[手动采集节奏](../MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md)、[Stage163真正Spot T0计划](../MONSTER_STAGE163_REAL_SPOT_T0_OFFICIAL_HTTP_AND_FORWARD_EVIDENCE_PLAN_20261018.md)、[Stage166来源接入及外审](../MONSTER_STAGE166_SPOT511_NINE_DAY_SOURCE_ADMISSION_IMPLEMENTATION_AND_REVIEW_20261019.md)。本次只是读取远端文件与旧CI/外审证据记录，**没有宣称重跑全仓/新 CI/新 other-AI Review**。

## 3. 唯一产品主线与相依次序（不增加Stage编号、不重写已APPROVE核心）

**工作包 A — G0: 源、身份、完整分母与真实T0。最高优先级。**
- 选择已有**独立Spot T0 511**为下一个可评的产品端到端样本，不把已曝光445的结果再当新OOS；USD-M已独立采集的T0另分场所对账、不和Spot合并成同一个分母。
- Spot冻结真实七日 `[2026-10-17T22:06:00Z, 2026-10-24T22:06:00Z)`（3360个3m轮次），在右端和发布方最后日级校验文件真正到齐**之后**，复用已APPROVE的Stage166而非另写下载/解析器；发现期 `2026-10-16..24`需511×9=4599次*来源准入条目*，不是已经下载文件数；如果采用信号后24小时固定退出代理，还需`2026-10-25`额外511条检查对象，总候选**5110**，无源仍 `CENSORED_SOURCE_MISSING`。10月25T22:06Z前不作全退出结果。动态Listing/退市的实际PIT未捕获必须另列UNKNOWN。
- 10月28/11月11的USD-M手工观察参考点仍必须**用户主动聊天请求**才能采集，不创建定时任务。本“开始吧”指恢复研发/整理主线，**不是**对后台扫描、官方大规模下载或Mac运行的常驻许可。

**工作包 B — G1/G2/G3: 同源同规则D0→D1。依赖A。**
- 已有 `monster_v4_shadow.py` 的原核心、既有 Stage162 Fair8，原源码按固定SHA锁定，从当时可获得的原始闭合1m数据重放整个3360个3m轮次，原FIFO与Fair8只在队列服务顺序处不同。要求原全部WATCH/队列ID保留、不静默drop、过期不可追认；按合法首次可见时间列时延和漏报。
- 硬性评估 **Stage77 G1（至少20个独立2×/至少3个窗口、严格提前≥90%/至少5m提前≥85%）**、**G2（原早5m机会中SETUP提前≥5m保留≥80%）**、**G3（日SETUP均值≤5、峰值≤12，D0全收不截断）**；本单独Spot 7d窗口即使结束也**不能**虚称达到3个独立时段。样本不足报`UNDERPOWERED`；不看新结果后现场改变规则。
- 关键判据不仅早评人数，还要净增/丢失真实SETUP、首次有效5m审核与FIFO占槽延迟、机会正常币负例、来源删失和真正新增收益信号；倘新队列仅救审核但0新增有效信号，要有明确`NO_PRODUCT_LIFT`结论，而非强行部署。

**工作包 C — G4: 真实执行、风险和退出。依赖A+B同一时间事实。**
- 复用既有Stage90/120，不造第四种执行引擎；Coin/合约单位、交易所Spot/USDM身份区分，数据时钟、可进价ask、可出价bid、多档深度、手续费及现存费率、退出失败与原始SHA逐项评级。
- **名义金额未指定则以参数 `UNKNOWN`**；不把历史固定30U/300U实验设为新用户订单限制。若真实时点L2不可补，最多给出`HISTORICAL_PRICE_PATH_PROXY`并明确不等于净可执行PnL。至少30个真正双侧有效观察才考虑Stage77 G4初步统计，但30不保证盈利。

**工作包 D — 用户可读机会与通知链。不得绕过A-C门禁。**
- 复用已有只读机会查询器和SQLite状态，不改Frank/生产；先用**已有测试和离线源**核对事件到达→队列→WATCH→SETUP→D2缺失原因→失效/过期→研究outbox去重/回放的完整一致性，输出真实队列积压、来源变差和延迟。研究出站`DRY_RUN_ONLY`且不得声称已送达。真实Gmail、Mac并行、发送readback严格等用户另行批准，且须先有G0-G5证据和独立Review。

**工作包 E — DEX连接器与BSC专项止损。非A-D的串行阻断。**
- 旧BSC P0保持隔离，只在有实际新合法免费来源能力时复核，不重复7笔买卖或反复扫描无效公共RPC。2026-11-02按历史既定来源门槛结项，未通过则BSC历史模型标`SOURCE_BLOCKED/INSUFFICIENT_COVERAGE`；**不会因此禁止CEX主线的离线工程、验证及相应的产品状态显示**。新链、Solana、NFT/其他市场若要生产级范围扩张，另需真实来源与用户批准，不能暗中号称全链覆盖。

## 4. 避免再次偏离的“下一次开发选择器”

每次接手 PR #30 必须先核 HEAD 与[Stage77](../MONSTER_STAGE77_CORE_MODEL_ACCEPTANCE_AND_BOUNDARY_FREEZE_20261013.md)、[Monster开发规则](../MONSTER_MODULE_DEVELOPMENT_RULES.md)、本ADR；按下表顺序决定有没有值得动的代码：

1. **源还没到**：只做可复用的离线源完整性/身份审计和下一批准入准备；**不要**重跑已批准的445回放、调27个旧阈值，或先开发新 BSC scanner。
2. **真实源已到**：优先按原Stage166与原Shadow/Fair8全场景因果重放；单次来源缺档就是删失，不删无WATCH或未上架候选。先看是否**真的**提升有效SETUP与可执行性，再决定写策略代码。
3. **D0/D1已可证但D2缺**：集中取得当时真实双侧盘口和合规身份；若无法恢复旧时点L2，明确G4 UNKNOWN、不增加会虚假放行的过滤器。
4. **研究指标通过但尚无工程通道/外审**：才处理原read-only operator、outbox、复审包和新资格安装，而不是继续扩数据源。
5. **同一事务没有新原数据、具体错误或可验证收益**：不要提交一个新Stage/重复报告。已有单点小修直接修改对应源码与测试；权限边界不变。

## 5. 验收、停工与交接输出模板

未来每次交付只需在PR既有相应报告/明确代码变更里报告**五件事**：`(1)固定SHA及来源时刻/完整分母；(2)新增真实功能与样本前后差别；(3)实际本机/CI/独立Review逐项证据；(4)G0–G6、真实净收益或UNKNOWN；(5)下一个唯一高价值缺口与权限界限`。类别为`DONE/PARTIAL/BLOCKED/REJECTED/NOT_DONE`，不从文档/CI存在推定部署成功。

立即验收本ADR：已有CEX D0/D1/D2脚本与来源锁存在、已有Spot未来样本具体成熟边界、BSC单链源独立止损、无触碰生产；**本ADR仅表示产品主线范围和交付顺序已经纠正，不是新模型、历史获利或前瞻回测已经通过**。


## 6. 2026-10-23 实际D0/D1工程进展：Spot 511分钟源到3m轮次的离线准入检查

- **已提交并逐字节读回**：`local-agent/scripts/monster_v4_spot511_replay_preflight.py`（Git blob `fde068908f53ae50d07b5a7d6cf78b4a88551d38`）与`local-agent/tests/test_monster_v4_spot511_replay_preflight.py`（Git blob `a0659dd9295bb1bf2f672cf6703186573dd7af5b`）。未修改此前已获独立审核的Stage163/Stage166/Stage162或原V4核心交易阈值。
- **新增实际能力**：离线读取Stage166的**完整**4599条尝试JSON，锁定511个原T0 symbol ×3360个三分钟轮次=1,716,960个symbol-tick；精确要求每个轮次`[T-24h,T)`全部已闭合分钟所属UTC日的1440根来源通过发行方SHA准入，累计`source_ready`与按原因`source_blocked`、每symbol删失数。00:00轮次不能误读当天尚未闭合的未来分钟。拒绝缺行、重复symbol+date、伪造VERIFIED状态、跨时钟未来可用性和错误聚合；未来价格标签不参与准入。
- **可用命令（仅在手动获取真实完整Stage166原报告后）**：`python3 crypto-300-profit-mission/local-agent/scripts/monster_v4_spot511_replay_preflight.py --stage166-report /path/to/stage166-full.json --out /path/to/spot511-preflight.json`。输出路径存在则拒绝覆盖，不做HTTP、监控、定时、发信或交易。该命令**不是**要求用户此时去下载未来Publisher ZIP或安装Mac服务。
- **实际验证**：同Git blob源的隔离Python 9/9 unittest PASS（合成511人口与档案状态、真实时间网格、CLI执行及拒绝覆盖），本轮没有触发新的仓库CI或其他AI独立审核。原Stage166长期Git机器JSON仅是**汇总文件**、不含4599条完整attempt，完整原attempt曾保存于指定旧Actions Artifact；所以**未把旧汇总文件冒充可供新工具直接消费的全部原证据**，本轮没有真实511新窗口已验收的publisher分钟档案。
- **严格含义**：此模块仅为`SOURCE_PREFLIGHT`，**不是**实际D0信号回放、源原字节重新校验、24h ticker与1m源数学等价证明，也没有历史动态上市身份PIT、单笔金额、盘口及真实净利润证据。即便输入全部标为已准入，仍固定`G0 PARTIAL / G1 NOT_SCORABLE / G2-G3 NOT_PASSED / G4 UNKNOWN / G6 NO_GO`。
- **下一唯一主线**：待2026-10-24T22:06Z七日窗和官方后续Publisher真实档案成熟，并有用户明确手动采集要求后，沿现有已审核Stage166生成完整来源attempt，再运行新检查器；只在实际可评价的分钟历史与动态上市缺失已公开记录后，对原D0/Stage162 Fair8做同源全市场因果paired回放。需要固定24h退出路径的研究还须独立等2026-10-25T22:06Z以后对应档案，不能先作真实ROI声明。不能以本次离线测试替代官方新源或真实OOS。



## 7. 2026-10-23：不等待正式七日结束的手动官方分钟源获取入口

当日（截至2026-10-23 UTC约14:08）10月16–22日为已结束UTC日，官方日级文件按Binance出版政策通常在次日上线；**具体每币文件是否成功取到/哈希是否匹配尚未通过当前网络实测**。10月23/24日尚未完成，不能伪造未来分钟。Binance官方说明：https://github.com/binance/binance-public-data 。

新增手动分批采集脚本 `local-agent/scripts/monster_spot511_manual_publisher_batch.py` Git blob `92b96c8abcb9542ccfe49219439330628fbf9f7a`，测试 `local-agent/tests/test_monster_spot511_manual_publisher_batch.py` Git blob `7182f027adfd8305542af2ba2203c9720ef71aed`。代码**不采用现时全市场交易所名单**，而是调用已审Stage166冻结的原Spot T0 511 symbol，只允许2026-10-16至24一个**已完整结束**的UTC日、一次最大64个symbol（可用start-index遍历）；默认`PLAN_ONLY`，仅显式`--download`才发到 `data.binance.vision` 的HTTPS，不递归重试、无无人值守服务。对每份ZIP先验官方相邻CHECKSUM、SHA，再调用原Stage166验证1440根1m/微秒时钟，成功后才持久化原ZIP和CHECKSUM。已有文件仅核验/跳过，不覆盖异常旧原字节；失败记录原因、保持未知而非零WATCH，止损网络响应字节数与重定向hostname。严格禁止跨HTTP站点源。

8项合成、无网络回归测试已经**提交到Git，当前尚无可核验的实际GitHub Actions运行结果/独立其他AI审查**，因此状态`CODE_COMMITTED / TEST_EXECUTION_UNVERIFIED`，不能声称新脚本已获外审。另已提交仅含`pull_request`和手动`workflow_dispatch`触发器、**无schedule和无市场HTTP的离线CI**：`.github/workflows/monster-spot511-manual-source-batch-ci.yml`。该CI本身不会采集真实档案，其`workflow_dispatch`若尚未登记在默认分支不应宣传为现成可单击云端下载入口。下一次真正网络采集需有可用被授权的一次性网络执行环境，再根据正确Git固定版本和官方源限制进行有界分批获取，不在用户高负载Mac上部署或长期运行。

**本轮实证限制**：当前容器及普通网页工具无法取得Binance ZIP/CHECKSUM真实字节（DNS错误/不支持二进制读取）；没有真实官方归档下载、没有真实511x9验收、没有D0/D1 paired replay、没有G4净收益。下一个最有价值动作是先对已结束日期做**一个真实来源受限批次验证**，确认云端能连通数据源及发布方SHA，同时保留所有失败样本；在数据通路成功之前不批量请求9×511，也不把准备工作当进度验收通过。G0 PARTIAL/G1 NOT_SCORABLE/G2-G3 NOT_PASSED/G4 UNKNOWN/G6 NO_GO，Frank/邮件/交易及Mac任务不动。

## 8. 2026-10-23 历史Spot分钟连接器可达性单币试验（REST_ONLY）

现有已连接Binance只读Spot历史K线接口，对**2026-10-22 UTC**、原511冻结T0中的`BONKUSDT`，以UTC毫秒`1792627200000`至`1792713599999`的完整单日窗口分2次请求（1000条+440条，源时间皆早于本次阅读），实际返回 **1440/1440 条**分钟K线，源分钟索引与收盘毫秒序列**0处缺口**，ohlc/12字段初步结构检测**0处错误**，首分钟开盘UTC毫秒`1792627200000`、最后一分钟收盘UTC毫秒`1792713599999`。这证明此时现有Binance连接器对该币、该日的**结构化历史Spot分钟数据可获取**，可用作D0/D1接入链路的一项真实活样，不是旧Stage历史汇总替代。此批未保留原HTTP body，没有Publisher ZIP/CHECKSUM SHA，不能标Stage166 `VERIFIED_FULL_DAY_1440`；分钟close不是买卖盘口，quoteVolume合计不是原时点24h ticker的等价回执，也不证明原T0以后该币每分钟真实买卖资格。不能凭这1币推到511全部或新上市币。

真实可复验来源请求：Binance Spot Klines连接器，`symbol=BONKUSDT, interval=1m, UTC first 1792627200000, UTC inclusive end 1792713599999, limits=[1000,500]`，只使用`structuredContent.result`核验，没有冒称Publisher字节或SHA。单币仅作通路验证，未来策略样本与G0–G6门槛不提升。

**同一轮采集入口安全性修复与验证状态（2026-10-23）**：针对刚新增的`monster_spot511_manual_publisher_batch.py`发现（1）原始写入使用`os.replace`可能在检查与提交间竞态覆盖另一执行方文件，且系统临时目录与目标目录可能分盘；（2）`zipfile.BadZipFile`未归入逐币失败，可能中断后续批次；（3）软链目标应拒绝跟随。本轮对应源码commit `afe9fb72aec3faf2368b9e34ad2cab7e53752b1b`、增加3个合成反例测试commit `195c36a64c3260cec140a487eb762d3284fce0b1`。修正使用目标目录内临时源文件和`os.link`独占提交，捕获损坏ZIP并显式阻止现存软链，失败保留缺失、不覆盖原有源。**已提交并Git blob读回；当前CI返回无可核验run，11项测试为已编写、未宣称运行PASS。**

## 9. 2026-10-23：Monster官方Spot511采集代码首次隔离运行验收（11/11）

**本轮新增真实执行证据，替换上一节旧时点“11项测试已写但未运行”的状态；不是回填到之前的CI/独立Review记录。** 从PR #30 HEAD `6dea402159a037289e6c2cc62bccf19429a11a7c` 按GitHub文件完整内容恢复以下固定Blob源码至隔离Linux工作区，分别使用Git原生对象算法 `sha1("blob "+len+"\\0"+原字节)` 读回与远端SHA一致，确认没有复制时改写测试代码：

- `local-agent/scripts/monster_spot511_manual_publisher_batch.py` = `64454bcc8a755f8d2932dc159c013b1b701623be`
- `local-agent/tests/test_monster_spot511_manual_publisher_batch.py` = `aa7162eb553a1b3035b719f2995f45966843a322`
- `local-agent/scripts/monster_v4_stage166_spot511_official_1m_intake.py` = `517fe5f06ac912230c8bb033798995b580f8332c`

运行环境 `Linux x86_64 / Python 3.13.5`；以原测试的显式合成511-roster代替未调用的Stage163历史T0档案加载依赖，**Stage166校验函数和新采集器源码均未替换**，并未把合成roster冒充原真实511名册。实际命令：

```sh
PYTHONPATH=scripts python -B -m unittest discover -s tests -p 'test_monster_spot511_manual_publisher_batch.py' -q
```

**原仓库11/11实际PASS，Ran 11 tests in 0.041s / OK；Python `py_compile` 对三份原文件全部通过。** 测试含默认不联网、已结束日期、有界来源、完整1440根、HASH不匹配、坏ZIP不阻断后续币、竞态拒绝覆盖、目标软链接拒绝、重复执行原文件SHA不改变，以及第三方重定向拒绝。所有源来自mock byte arrays，无真实Publisher HTTP交易和实际Binance完整数据。独立审查状态仍 `NOT_DONE`；GitHub Actions在本会话已能访问的接口中尚无相应可核验run/Job日志，故**不能把本地PASS写成GitHub CI PASS**。本轮没有修改新策略参数、Mac程序、后台、Gmail、Frank、交易或BSC。

本项源工具 `OFFLINE_CODE_TEST_PASS`，正式 `G0 PARTIAL/G1 NOT_SCORABLE/G4 UNKNOWN/G6 NO_GO` 不变。下一主线不是再扩同类坏包测试，而是把历史/正式原始Minute publisher完整来源实际纳入现有原D0与Fair8的同源因果回放，区分用户能得到的有效SETUP与只有更快审核的伪提升。

## 10. 2026-10-23：Spot511真实发布方分钟源→D0已闭合3分钟输入适配（离线）

落实ADR-004工作包A→B的**输入桥接**，而不是继续做旧BSC、改原D0/D1阈值或重复Fair8历史445的结论。

- 新增 `local-agent/scripts/monster_v4_spot511_closed_minute_feed.py`，Git blob `05b36b2e28cc88d4636dc865329e1f1cb0667586`；原 Stage166 校验器保持不变，针对冻结Spot T0名单中**每个单独symbol**读取 `2026-10-16..24` 官方日级ZIP + 原Publisher .CHECKSUM，逐日调用 Stage166 1440根/微秒/源SHA完整验证。避免载入整511个交易对的9天数据到内存，只处理单symbol的12960分钟。只接受已结束UTC日，未提供/损坏/未结束分别记录，不能把缺源当0个WATCH。
- 确定性计算3360个 `[2026-10-17T22:06Z,2026-10-24T22:06Z)` 三分钟tick；每个时刻 `T` 的价格只能取`T-1分钟`已经闭合K线的收盘价，24h成交额为`[T-24h,T)`恰好1440根已闭合1m `quoteVolume` 前缀和。**它与Binance 实际发在T的24h滚动ticker不是同一原始source，必须始终标`CLOSED_1M_SUM_1440_PROXY_NOT_LIVE_TICKER`**；不能把此代理直接当正式原V4因果实时行情，也不能在官方ZIP事后发布的情况下虚报原2026年T时网络`available_at`。
- 全3360个tick即使未来源也各有`CENSORED_SOURCE_MISSING_OR_REJECTED`占位和完整身份/时钟；`READY_RECONSTRUCTED_TICKER_PROXY`仅表示这一单币分钟源和历史计算在数学上有效，**不表示实时可见、完整511人口PIT、当时真正Spot资格、D1已复算、G1通过或收益**。
- 测试 `local-agent/tests/test_monster_v4_spot511_closed_minute_feed.py` Blob `e3331775aa168802f82699a4ed8f4557fa47f2ce`；隔离Linux/Python 3.13.5 使用不变的Stage166验证器、合成真实1440行发布方格式和对应ZIP SHA/ASCII CHECKSUM，实际 `5/5 OK` （正常连续两日首39个tick、前一分钟与未来分钟、SHA坏源、2026-10-18零点跨日单tick、未结束UTC日、全9日缺源、名单/时区拒绝）。没有联网、交易、部署和邮件。
- 已将新增源/测试接入既有 `monster-spot511-manual-source-batch-ci.yml` 纯离线工作流（仅push、PR及显式手动，无schedule），但**当前GitHub Actions运行回执没有取得**，因此本地 `5/5`不能写成GitHub CI PASS，也不能算其他AI独立review。
- **尚未开发/运行真正511币统一SQLite时间顺序D0→D1/Fair8回放**：需要全量资格过滤及发布方完整档案，同时明确上述24h代理与实际快照差异；原正式G0 PARTIAL / G1 NOT_SCORABLE / G2-G3 NOT_PASSED / G4 UNKNOWN / G6 NO_GO不变。下一可操作研发应以同一原模型状态机和原Stage162 Fair8恢复单一SQLite队列，从`READY`与`CENSORED`联合输入逐tick构造合法已闭合5m D1，不根据事后高价或已曝光赢家优化规则。
