# Monster ADR-005：Claude Haiku 5.5 独立 REQUEST_CHANGES 与受限修复验收（2026-10-25）

## A. 外部审查身份与固定源码

- 来源：用户上传的 Claude Haiku 5.5 在 Anthropic 聊天环境、无网络 bash、Python 3.12.3、git 2.43.0 完成的**实际独立审查结果**，原文状态 `REQUEST_CHANGES`。此项是用户提供的审查证词，本仓库没有伪装成Claude本人新发的GitHub Review，也不得宣称其已经批准修复版。
- 审查的固定源码 SHA：`cbce0ddef40ab23ba86ba27e31e3d93bfaa62362`，Git tree `a116ca13732c442408aad72a8548b078e5cd77d8`，审查说明在原 `MONSTER_ADR005_FULL4599_REAL69_INDEPENDENT_REVIEW_REQUEST_20261025.md`；使用 [GitHub 原始离线审核包 #40174223421](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40174223421)。
- Claude在无网络环境中实际检查4011个Git跟踪文件、原69/53专项测试17/17、固定SHA和WATCH指纹、12个官方2026-10-24 ZIP/CHECKSUM；独立按原ZIP及自己实现重算Oct24新增16个WATCH价格/触发与D1，均16/16一致。它未能独立读取全部4599份原始ZIP、Oct18–23的37条源，也未实测原196 CI。对前版本认可的部分仅限上述范围。

## B. 用户反馈与本轮验证的实际修复

| 独立审查项 | 本轮处理 | 可审计证据 |
|---|---|---|
| P1-1：15m截止tick遇 `SAME_BAR` 后误标 `LATE_UNSCORED` | **已修复源码+真实回放**；源无缺口、先前有有效负评估 → `NO_SETUP`；先前source censored → `SOURCE_UNSCORED`；从未有效评估且无已报源缺口才是 `LATE_UNSCORED`，也覆盖“下次tick才被服务”的情形 | `local-agent/scripts/monster_v4_d1_rbtc15_episode_research.py`，提交 `f3a1454a035c774c94ba2ee9dc540f7adb803ec9`；真实GitHub Actions [#40176149293](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40176149293) **SUCCESS**、Artifact `12592860133` |
| P1-2：没有显式研究G3判断 | **已修复**，明确给出原47/7=6.71、峰10的曝光研究G3数值未过，别把G0/PIT/G4 UNKNOWN当作通过 | `local-agent/scripts/monster_v4_adr005_real69_original_sqlite_replay.py`，`research_G3_raw_setup_attention=EXPOSED_NOT_PASSED` |
| P1-3：“至少40条有Crypto身份依据不存在” | **经证据复核部分不成立**：早期ADR第245行是当时未完成身份分类的旧历史快照，不能覆盖后续冻结的**官方类型正面证据Manifest**。`MONSTER_SPOT511_PRE_EVENT_OFFICIAL_POSITIVE_CRYPTO_26_ASSETS_20261024.json` Git Blob `10661b150ecb5ad5e8a3b24ad023eea2b07269af` 与 `MONSTER_SPOT511_PRE_EVENT_REMAINING_7_TYPES_20261024.json` Git Blob `9b89569829d596c783903b101e15e3b6a7292421` 分别对应真实47条SETUP里36条和4条**已支持普通Crypto类型**。此结论只证明manifest内发行方公告/研究报告的事前类型证据，**不证明当时确有Spot可交易/个人账户有资格/可费后盈利**。 | 新报告`research_G3_positive_asset_identity`是强制按Git Blob SHA拒绝篡改的6字段分层，`CRYPTO_TYPE_POSITIVE=40 / CHILIZ_FAN_TOKEN_SEPARATE=2 / TOKENIZED_EQUITY_EXCLUDED=2 / UNRESOLVED_NOT_DEFAULT_CRYPTO=3`，后三个未知代币为TREE、LA、ANIME |
| P2-1/2：日期标签与静态53断言 | **已修复**：峰值标签改成曝光Oct完整窗，旧53由实查行数计算 | `monster_v4_adr005_real69_original_sqlite_replay.py` |
| P2-3/4：参考比较覆盖太窄、旧研究“独立” | **部分修复且诚实保留历史限制**：对旧53仍检查全ID、symbol、watch_ms、删失次数、SETUP触发时间；仅6个有有效评估/无删失的`LATE→NO_SETUP`转变可标 `SEMANTIC_DEADLINE_REPAIR_MATCH`，禁止对其他漂移报MATCH；旧研究无sqlite终止时间，输出`terminal_time_comparison=NOT_AVAILABLE_IN_LEGACY_SQLITE`，不能宣称非SETUP每个terminal_ms全字段一致。此前移植版仍是已曝光对照、绝非样本外或独立别的AI。 | `monster_v4_adr005_real53_original_sqlite_replay.py`、新差异测试13项 |
| P2-5：异常Decimal中断数据适配 | **已修复**：两份Spot分钟适配器捕获`decimal.InvalidOperation`，来源按拒绝/删失分类，不冒充零成交；增加2个验证器通过后发生坏CSV的负例测试 | `monster_v4_spot511_closed_minute_feed.py`、`monster_v4_spot511_d0_d1_tape.py`，最新常规云端CI [#40176372171](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40176372171) **204/204 PASS** |
| P2-6/7：发行方ZIP真正发布时间、T0名单/新增上市PIT | **不能靠历史补丁制造证据**：2026-10-24等官方档案均为后来读回；`UTC日结束`仅来源成熟度下界，不是实际文件公开时刻，T0 511仅是冻结研究分母，未证明新增上市/下架的全市场覆盖；G0仍PARTIAL、G1/G2不升级。 | 所有报告继续写PIT=UNKNOWN；无旧假设伪造live成交证据 |
| P2-8：42个旧Artifact来源链 | **已定位到精准run ID和分片数**：原GitHub只读归档 `40027484781×22`、`40006012284×1`、`40007027318×5`、`40086780992×6`、新Oct24官方 `40171792607×8`，共42个旧保存Artifact分片；真正合并源文件5372项，为原ZIP+CHECKSUM等，真正69个必要symbol-day再由Stage166逐一校验；并非5372个交易对。 | 固定GitHub工作流 `.github/workflows/monster-adr005-reviewed-deadline-p1-replay-once.yml` 文件自带42个确切Artifact名字和run ID；校验报告包含69个带来源SHA的实际样本日 |

## C. 完整真实新旧状态核销（绝不覆盖旧证据）

- 旧冻结基线 `cbce0dde...` 的完整69真实SQLite结果（Artifact `12591221330`）：`47 RESEARCH_SETUP / 10 NO_SETUP / 4 SOURCE_UNSCORED / 8 LATE_UNSCORED`，G3已曝光失败。
- **修复后的独立新SQLite**：[#40176149293](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40176149293) 在源码固定SHA `583fa952bbcc93d2bbbf19769887f2ee4c816df5`，完全重新从42个保存的真实官方源分片复算；`47 RESEARCH_SETUP / 18 NO_SETUP / 4 SOURCE_UNSCORED / 0 LATE_UNSCORED`。旧53纠正6个，新增16纠正2个；旧53原SETUP 37条/时间及新16研究SETUP10条/时间均原样保留。原始WATCH 69/69不变；更正仅作用于研究队列，不触碰原Shadow/真实盘口或历史源码归档。
- 最新代码另增加Decimal错误守卫并触发全套 source-batch 离线CI [#40176372171](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40176372171)，Ubuntu Python 3.11 下真实运行14组测试 **204/204 PASS**。实际已提交并测试的修复代码固定SHA **`3fd5cab30324acd75c4f6f00f86bc264abdf943c`**（这是当前本文件写入前最后一个仅源码/测试的提交），与此前受审SHA有差异，Claude的旧REQUEST_CHANGES**不构成新SHA的独立复审**。

## D. 继续门禁和后续动作

- **G0 PARTIAL**：固定511研究币日 ZIP完整（之前GitHub复算4599/4599），但历史真实当时PIT、全市场新增币、个人账户实时准入仍UNKNOWN；Claude只有12个原ZIP故只独立验证12个，不能写Claude全4599审核通过。
- **G1 NOT_SCORABLE / G2 UNKNOWN**：2×/5×/10×历史前瞻召回、提前量与逐账户执行路径依旧缺乏充分独立可用证据。
- **G3 EXPOSED_NOT_PASSED**：原始新D1研究47 SETUP/7天6.71 >5；官方正面身份普通Crypto类型40/7=5.71 >5；峰10 <=12。实际动态上市PIT不足，**不声明历史实际可交易的40个**，也不能把已曝光窗口等同未来预注册OOS。
- **G4 UNKNOWN / G5 NOT_DONE / G6 NO_GO**：即便Claude提出有效问题，本次修复版需新固定SHA的增量独立其他AI确认，才能关闭G5阻断；暂不进行部署。
- 限定：NO_MERGE / NO_DEPLOY / NO_MAC / NO_SCHEDULE / NO_GMAIL / NO_TRADES / NO_NEW_RPC。没有自动监控、没有继续做BSC边缘证明、没有修改Frank。

下一份外审请比对 `cbce0ddef40ab23ba86ba27e31e3d93bfaa62362 → 3fd5cab30324acd75c4f6f00f86bc264abdf943c` 的增量，只审修复、原P1逐项证据和新增P0/P1/P2，不重建全部历史研究；若不能独立读取旧ZIP，须保留该项BLOCKED，不得假装全源通过。
