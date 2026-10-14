# Monster 手动采集与研发节奏（跨对话长期有效，2026-10-14）

**用户最新明确指令：取消已经安装的 Stage99 自动定时采集；未来由用户在约定日期主动在聊天中提出采集请求，助手应当立即使用可用的 Binance 公开连接器/官方接口自主获取当前真实数据、分析并提交原 Mission Monster PR #30，无需再次让用户执行本地采集命令或重复确认公开只读数据获取。** 本文件是 Monster 模块的执行主入口，与 [MONSTER_MODULE_DEVELOPMENT_RULES.md](MONSTER_MODULE_DEVELOPMENT_RULES.md) 和 [AGENTS.md](AGENTS.md) 一起每次接手先读。

## 自动采集终止与当前事实

- 原已安装服务只涉及三个 `com.lxxlx2.monster.stage99.usdm.{20261014,20261028,20261111}` macOS LaunchAgent。2026-10-14 UTC 05:48:29 首次服务真实状态为 `SOURCE_FAILED_NO_BACKFILL`，报 `STAGE91_MARKET_SYMBOL_DUPLICATE_OR_INVALID`，后续已修复 Unicode 代码但**用户 Mac 上已安装旧版本未更新**。
- 用户在 2026-10-14 明确要求**停止全部三个 Stage99 自动任务**，未来无须为了实验再安装 launchd、cron、GitHub schedule、ChatGPT automation 或周期性 Gmail。助手提供准确 **限定标签的 zsh 停用命令**；随后用户于 2026-10-14 在当前对话提供真实 Mac zsh 终端截图，三行分别为 `20261014 STOPPED_AND_PLIST_REMOVED`、`20261028 STOPPED_AND_PLIST_REMOVED`、`20261111 STOPPED_AND_PLIST_REMOVED`，命令退出返回了 shell 提示符。因此按 **用户提供的实际终端输出** 记录 `STOPPED_THREE_LABELS_USER_TERMINAL_READBACK`。这是执行后本地检查的间接证据，不宣称助手远程登录 Mac，亦不能证明今后无其他程序重新注册。
- 停止时仅 bootout 精确三个 Stage99 labels、验证 `launchctl print/list` 该服务均不存在，再移除同名 LaunchAgents plist。不可使用 `launchctl remove` 通配、全量 `unload -w`、`killall`、删除孤立 repo/日志/证据、修改或停止 Frank/其他 LaunchAgents。原 Stage99 JSON 状态如仍为 `SCHEDULE_INSTALLED` 是历史记录，不能替代真实 launchctl readback。
- 原本 Stage99 一次性固定的三个时间仍为**历史实验设计记录**：2026-10-14、2026-10-28、2026-11-11 各 06:00 UTC（曼谷时间 13:00），原自动启动 05:48 UTC（曼谷 12:48）。在手动模式里，它们**只作为用户选择发起聊天采集的目标日期/参考时刻**，不再是实际运行中的 scheduler。
- 首个 2026-10-14 06:00 UTC Stage99 观察点保留 `SOURCE_FAILED_NO_BACKFILL`。本日已另外自主完成真实 Binance 新市场观察 `2026-10-14T09:48:24.840Z`（曼谷 16:48:24），归档 [Stage123 manifest](evidence/monster_stage123_20261014T094824Z_manifest.json)。**该新观察是新的起点，不是 06:00 旧快照补抓。**

## Mac 停用命令（用户执行；精准限定三个 Stage99 labels）

```zsh
for d in 20261014 20261028 20261111; do
  label="com.lxxlx2.monster.stage99.usdm.$d"
  service="gui/$(id -u)/$label"
  plist="$HOME/Library/LaunchAgents/$label.plist"
  if launchctl print "$service" >/dev/null 2>&1 || launchctl list "$label" >/dev/null 2>&1; then
    launchctl bootout "$service" || { echo "$d BOOTOUT_FAILED"; break; }
  fi
  if launchctl print "$service" >/dev/null 2>&1 || launchctl list "$label" >/dev/null 2>&1; then
    echo "$d STILL_REGISTERED"
    break
  fi
  rm -f -- "$plist"
  echo "$d STOPPED_AND_PLIST_REMOVED"
done
```

命令仅对明确列出的 Monster Stage99 标识工作；必须在用户 Mac 本地执行，所有远端 Git 研发提交都不会取消本地服务。完整成功输出应为三条 `STOPPED_AND_PLIST_REMOVED`；如显示失败，实际停止状态必须标 `PARTIAL_OR_UNVERIFIED`。不要删除 `$HOME/.local/share/monster-stage99-source-capture/` 的审计原始数据、状态和日志。

## 后续需执行的手动采集检查点（Asia/Bangkok）

| 目标日期 | 用户发起聊天的建议时间 | 相应 UTC 参考 | 采集模式 | 状态 |
| --- | --- | --- | --- | --- |
| 2026-10-14（已完成手动新基线） | 16:48:24 | 09:48:24 | 新市场数据完整基线 / Stage123 | `DONE_NEW_EXPLORATORY_BASELINE` |
| 2026-10-28 | **13:00** | 06:00 | **用户主动提问后立即公开接口采集**（无后台任务） | `WAIT_FOR_USER_REQUEST` |
| 2026-11-11 | **13:00** | 06:00 | **用户主动提问后立即公开接口采集**（无后台任务） | `WAIT_FOR_USER_REQUEST` |
| 其他任意日期 | 用户随时明确要求“采集妖币/Monster 数据” | 实际 API 观测时间 | **当次立即**，不必等固定日 | `ON_DEMAND` |

这不是日程提醒或任务计划，不会自行运行或主动通知用户。用户可能早于或晚于 13:00 发起；**使用真实 API 时间、真实 Git 提交时间作为本轮观测标签**，不得硬改成 06:00 UTC，也不要为了等到某一时刻才开始。当用户下次说“按之前计划继续采集”时，直接从本文件确定流程，不要求重发 Mac 信息。

## 收到采集消息后，直接完成的工作（无需反复确认）

1. 读取本文件、Monster 长期规则、原 PR #30 远端最新 HEAD 和上一份真实数据清单。**仅操作 Monster 妖币模块**，不要混入 Frank/BTC 价格预警/NFT/资产。
2. 并行调用可用的 Binance USD-M **实时**只读行情接口，至少：`exchangeInfo`（保留全量条目包括非活跃与其他合约）、所有合约滚动24h ticker、best bid/ask ticker、mark price/funding。能独立获取官方 `/fapi/v1/time` 和原始 HTTPS bytes 时记录它们；使用 Binance 连接器仅提供结构化 JSON 时必须显式标记 `CONNECTOR_STRUCTURED_NOT_RAW_HTTPS_STAGE97`，**不得制造 Stage97 原始 HTTPS SHA/时钟证明**。
3. 取 Binance 源提供的当前时间字段，保存每一源观测的时间范围，四源并非原子同一毫秒；检查记录数量/去重、市场全量分母、`TRADING + PERPETUAL + USDT` 活跃全集、完整 ticker/BBO/mark 覆盖、Unicode 名称、合约单位/分类未确认、旧数据时间与缺失项。全量原始结构化记录**分片存档**，不能仅保存榜单或删掉失败/非活跃币。
4. 分析实际业务价值：当前市场广度、过去24小时成交额分布、上涨/下跌比例、爆发币和正常币对照、BBO价差及其分布、过去观察点变化、真实币种身份/倍数和交易资格阻断，**WATCH != BUY**。没有日间逐分钟信号记录，不声称几天前就发现了 2x；只有价格/BBO 不能声称有真实可成交利润。
5. 为每次采集创建新的 UTC 批次文件名 `monster_stageNNN_YYYYMMDDTHHMMSSZ_...`，标注 `MANUAL_USER_REQUESTED`、UTC+曼谷时间、原始结构化 API 来源、采集覆盖、缺失/censor、Git SHA。在原分支 `research/monster-v4-local-discovery-20261010`（PR #30）提交**完整资料与简洁指标报告**，随后远端重新读取文件/CI 核对后汇报。不能只在聊天里给市场排行榜不更新 Git。
6. 运行 `../local-agent/scripts/monster_v4_stage124_manual_snapshot_comparison.py` 进行**每个真实批次独立全市场数据质量、分母和24h分布**核验；如存在两份完整实际批次，则用**预先冻结的唯一前瞻配对比较器** `../local-agent/scripts/monster_v4_stage124_manual_snapshot_forward_compare.py`（对应 [Stage124 原始 T0/T1 冻结方案](MONSTER_STAGE124_FROZEN_MANUAL_MARKET_TWO_SNAPSHOT_FORWARD_COMPARISON_PROTOCOL_20261014.md)）做 T0/T1 同合约严格因果比对。优先采用冻结比较器作为对外配对收益口径，严禁对两套输出挑有利数据。首次出现的币没有可比前值不得算 0% 或后验负收益。若要验证 D0 提前能力，需另行使用当时冻结的因果一分钟历史/前瞻证据与完整市场分母，**两张相距两周的快照不能验证 1m 早报率**。
7. 不自动开任务、发 Gmail、下交易单、安装 Mac 服务或修改 Frank。每次新的研究候选仍应按数据→方案冻结→实现→历史实验→独立其他 AI review→测试→独立前瞻验证→授权部署的原有顺序；失败策略如 Stage118 的 18/28 召回率保留为 `REJECTED`。

## 研发在两次手动采集之间不能停

2026-10-14 本轮接手新增 [Stage125：Spot 与 USD-M 标的映射、时钟及可执行性缺口](MONSTER_STAGE125_CROSS_VENUE_EXACT_SYMBOL_AND_SOURCE_FRESHNESS_TRIAGE_20261014.md)，离线全量 cohort 映射代码和两个操作系统 CI 通过；本轮数据连接器源字段的时钟不同步，**没有升级为同一时点 Spot 买入证据**。继续用真实独立 source/issuer/单位和手续费深度数据解决 G0/G4，不能在已曝光的 519 个历史 D0 中继续选阈值。



2026-10-14 接续完成 [Stage126 原始525全市场真实 BBO 双边可见容量](MONSTER_STAGE126_REAL525_BBO_CAPACITY_MAINLINE_RESULTS_20261014.md)：使用 Stage123 原始八源，525/525 均有正挂单和合格源时钟，双边可见容量代理中位 **67.01877 USDT**，p25 **22.29402**，p75 **197.25257**；已由 macOS/Ubuntu [CI #38554960854](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38554960854) 实际 source-read 并核对全部输出相同，永久汇总保存 [Stage126 JSON](evidence/monster_stage126_20261014T094824Z_actual_full525_bbo_capacity_summary.json)。这仅说明本批 L1 挂单有多薄，不代表实际能成交、交易金额、后续卖出或正收益。最先要解决的仍是 D0 时点的 G0 身份/单位及 D2 多档深度和真实可交易净价，旧 Stage118 REJECTED 不变；不能用这批过去 24h 涨幅挑参数。

2026-10-14 Stage127 原 519 首次 D0 的六特征顺序前推优先模型完成：[冻结方案](MONSTER_STAGE127_FROZEN_FIRST_D0_CHRONOLOGICAL_PRIORITY_MODEL_PROTOCOL_20261014.md) → [真实双系统 CI #38556832716](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38556832716) → [最终实际否决报告](MONSTER_STAGE127_EXPOSED519_CHRONOLOGICAL_PRIORITY_REJECTED_REAL_RESULTS_20261014.md)。原 519 D0 完整保留，前 3 个窗口因训练样本不足冷启动未打分；后 3 个窗口重要早5分钟 2× 保留 **16/22=72.73%（<80%）**，日均 **6.857（>5）**，峰值 **18（>12）**，结论 **`REJECTED_EXPOSED_HISTORICAL`**，不能靠修改已曝光519上的阈值宣称成功；G0=PARTIAL，G4=UNKNOWN，完整新 OOS/外部独立 AI Review 均未完成。下一步把重点留给真正独立的全市场分钟级早报、D0/D1 时点交易身份/盘口深度和完整进出场证据；手动市场采集仍由用户另行在聊天触发，**不创建任何定时采集**。

2026-10-14 Stage128 全市场漏报分母主线：复查 **5,400 原始历史 symbol-date**，官方小时源 3,333 条完整、2,067 条不完整；再核对 Stage93 已有 3,283 条完整一分钟、51 条源完整 2× 和 **48 条 D0 提前≥5分钟**，但是其余 2,117 条有真实来源删失，48/51 不能升级正式 G1。将历史小时不完整与后来的 2026-10-14 Stage123 927 项交易规则比较，发现晚于整个七日窗口 1,869、后来的 onboardDate 落在窗口内 31、后来的 metadata 已不存在 167；另有 15 条小时历史完整却与现有 onboardDate 冲突。后来的上市字段**不证明旧历史当时可买，也不能直接修正分母**。 [Stage128 原始结果与后续重点](MONSTER_STAGE128_REAL5400_SOURCE_CENSOR_AND_IN_WINDOW_LISTING_AUDIT_20261014.md) 已保存 [46个需调查案例](evidence/monster_stage128_31_later_listings_and_15_historical_clock_conflicts.json)，[原始来源机器汇总](evidence/monster_stage128_original5400_later_metadata_censor_machine_summary.json) 和 macOS/Ubuntu [CI #38561158512](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38561158512) 成功证据。下一步**优先核实31个疑似窗口内新上市合约**的官方历史分钟级数据及上市身份，构造完整包含新上市和无 WATCH 的 G1 分母，继续原 G2/G3/G4 正向研究。Stage118/127 仍 REJECTED，Monster/实盘/Gmail 仍 NO_GO，无自动任务恢复。

2026-10-14 本轮续作 [Stage129 固定31个潜在窗口内新上市合约的真实历史小时行情](MONSTER_STAGE129_REAL31_LISTING_HOURLY_PRICE_SOURCE_AUDIT_20261014.md)：首先锁定Stage128全部31个候选，再读取 Binance USD-M 官方连接器的历史1h源并归档六个日期全量响应。**31/31**从初始可见小时到原窗口末尾连续，历史 VINEUSDT 首次1h OPEN 0.20194、最高 HIGH 0.43560（2.1571×），APRUSDT 初始0.313、最高0.750（2.3962×），另29例均未达两倍，没有5×；均为历史毛价 HIGH、非实际成交。后来的 Binance 类型分类31中20个 COIN、11个 EQUITY/HK_EQUITY，仅为交易所后验声明。代码及31源在 macOS/Ubuntu [CI #38562865049](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38562865049) 全部 PASS，[永久机器摘要](evidence/monster_stage129_fixed31_historical_hourly_exposed_source_machine_summary.json)。**两例不能并入 Stage93 原51个固定7日锚点OPEN→HIGH的2×，也不能称新 OOS 或净盈利。** 下一步为单独的早期新上市`D0_NEW_LISTING`因果一分钟数据与源证据，建立完整包含新上市及无 WATCH 的全市场G1，后续验证 G2/G3/G4；Stage118/127 失败仍保留，G0 PARTIAL、G4 UNKNOWN、Monster部署 NO_GO，不建立定时器/新服务。

2026-10-14 Stage130 实际完成 **首次一分钟新上市研究全31官方Publisher SHA逐源复算**：[预冻结合同](MONSTER_STAGE130_FROZEN_NEW_LISTING_31_OFFICIAL_1M_CAUSAL_RESEARCH_PROTOCOL_20261014.md) → 原31内147个官方 Binance Data Vision 1m日ZIP及其 `.CHECKSUM`，159,675真实分钟、31/31无分钟缺档 → [macOS/Ubuntu离线与实际官方源CI #38566877450](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38566877450) 全PASS → [Stage130 完整研究报告](MONSTER_STAGE130_FROZEN31_OFFICIAL_1M_CAUSAL_NEWLISTING_RESULTS_20261014.md) 与 [全31行永久Git摘要](evidence/monster_stage130_original31_publisher_sha1m_momentum_archived_summary_20261014.json)。独立二次解压CI原始Artifact，实际复核 **147/147** ZIP SHA 与Publisher回执一致，原ZIP与完整SHA清单在CI artifact保留30天，Git只永久保留精简31行与全原始结果SHA256，不虚称已将147个源ZIP写入Git。未调旧阈值的独立新上市研究候选19/31，历史本来已曝光 VINE/APR 两例 gross 2× 首分钟 HIGH 都提前>=5分钟，另17个触发未达该gross 2×；VINE提前1,121分钟，APR提前797分钟，明确 **已曝光历史研究，G1新OOS仍NOT_SCORABLE，G2/G3未过，G4 UNKNOWN**。下步优先将 Stage116 全市场 OOS 窗口与**窗口内新上市首分钟人口账本**统一并预先冻结，避免再被全168h准入漏掉真正上市后机会；不得用当前历史两赢家调整特征或认可实盘。原 Stage99 仍停用，手动市场采集只在用户聊天明确提出时进行；Frank、Gmail、交易和Mac部署状态不变。

2026-10-14 Stage131 完成 [全市场初始币+窗口内上市币分层、来源缺口及去重桥接](MONSTER_STAGE131_DYNAMIC_LISTING_G1_POPULATION_BRIDGE_ACTUAL_RESEARCH_AND_CI_20261014.md)：从旧 Stage130 官方SHA源永久摘要复算真实31个窗口内新上市案例、147个历史发布方ZIP校验、159,675个分钟、19个首次动量研究信号以及原2个已曝光2×早报；后来的COIN20、EQUITY7、HK_EQUITY4只作后验类别，绝不认证历史Crypto。读原完整Stage130源发现 **581次满足三分钟条件的扫描**，对31历史样本只有19个唯一最早触发，必须去重且不当作全市场G3通过。两OS [Stage131 CI #38572431172](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38572431172) macOS/Ubuntu 实际SUCCESS，源码/机器报告均在原PR30 [Stage131审计JSON](evidence/monster_stage131_dynamic_listing_original31_reconciliation_summary_20261014.json)。关键阻碍仍在：原Stage116 2026-10-14 06:00 UTC 首个冻结7日窗口`SOURCE_FAILED_NO_BACKFILL`，三原窗口不能硬补判 PASS；必须**另行预冻结新的完整真实前瞻验证方案**，特别确保用户手动发消息后取得的 as-of 原始市场来源确实早于新验证的开始时间，保留中途上新、退市、无WATCH、股票合约等分母。严禁启动定时任务或以离散市场快照声称一分钟实时报警。Stage118/127继续REJECTED、G0 PARTIAL、G1真实新OOS NOT_SCORABLE、G4 UNKNOWN、Monster/交易/Gmail均NO_GO、Frank不变。

2026-10-14 Stage132 经济代理检验完成：[固定先验协议](MONSTER_STAGE132_FROZEN_FIRST_SIGNAL_DELAYED_CLOSE_EXIT_PROXY_PROTOCOL_20261014.md) → [原31币价路径报告](MONSTER_STAGE132_ORIGINAL31_FIRST_SIGNAL_PRICE_PATH_NEGATIVE_HISTORICAL_RESULTS_20261014.md) → [实际双OS官方归档源复算CI #38578529492](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38578529492)（首轮路径错误的 [CI #38578392121](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38578392121) 失败保留）。真实复核原31/31、159675个分钟、147个Publisher ZIP+校验；19个首动量信号，在信号额外延迟1分钟后用下一根分钟 OPEN 入场，分别按15m/1h/6h/24h固定OPEN退出（0手续费/冲击，无法证实真实成交），有效数19/19/19/15，毛收益中位 **-2.5681%/-3.9260%/-4.8253%/-3.2593%**、简单均值 **-1.9012%/-3.3830%/-3.6554%/-4.3866%**，期内最大不利价格波动包含严重损失。由此原“新上市首次动量即买”仅可作D0发现研究，**BUY代理表现为NEGATIVE**，不能作为D1/D2或G4盈利证据；不准对已暴露31例优化阈值或选持有期来过关。永久机器结果 [Stage132 JSON](evidence/monster_stage132_original31_delayed_entry_fixed_horizon_machine_summary_20261014.json)，Stage118/127仍REJECTED，G0 PARTIAL，G1新OOS NOT_SCORABLE，G2/G3 NOT_PASSED，G4 UNKNOWN，NO_GO。下一主线：前瞻全市场含新上市完整真实分母、在真正未知区间按原规则统一评估D0/D1与当时交易资格/深度/费用，待独立Review与所有门禁通过后才讨论Mac；10/28、11/11市场数据仅聊天主动手动获取，无后台采集。

2026-10-14 Stage133 真实前瞻T0抗错过窗口方案与代码：[新独立协议](MONSTER_STAGE133_FROZEN_MANUAL_FORWARD_ACTUAL_T0_PROVENANCE_PROTOCOL_20261014.md) → [入口代码](../local-agent/scripts/monster_v4_stage133_manual_actual_t0_forward_proof.py) → macOS/Ubuntu [离线 CI #38587686275](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38587686275) 均SUCCESS → [实现/门禁及下一步报告](MONSTER_STAGE133_MANUAL_FORWARD_ACTUAL_T0_OFFLINE_GATE_AND_NEXT_OOS_PLAN_20261014.md)。本轮**没有发起新实时行情采集或启动新的OOS**。新代码只允许将来用户明确发消息要求手动采集时执行一次 Binance官方 /fapi/v1/time→/fapi/v1/exchangeInfo→/fapi/v1/time，独立验证原响应SHA、serverTime和UTC时钟、全量交易所合约原始数据/Unicode，再由最后一份官方time回应结束之后的确定性5至10分钟自动计算**新**未来七日开始时间，随后手动另行逐批累计至少三个真正未曝光完整不重叠窗口；不追补原Stage116 10/14 06:00失败且不能用一次性快照声称分钟级实时监控。所有Source、Issuer、Spot/衍生品量纲和G4仍须实证，数据源成功也不自动批准G1或通知。正式G0 PARTIAL、G1新OOS NOT_SCORABLE、G2/G3 NOT_PASSED、G4 UNKNOWN，Stage118/127旧REJECTED维持，Stage132首次动量买入经济代理NEGATIVE，部署NO_GO；原Stage99停止、Frank/Gmail/交易未改。到10/28和11/11用户主动发消息才采集，未额外设置任务。

主线不依赖日期：继续研究信号在首次 D0 时的真实早报能力、独立底层 crypto/合约单位核验、信号时点盘口/标记价/手续费/滑点、源真实性、历史失败归因及模型样本外验证。用现有 Stage123 数据开发**可复现的全市场新旧手动快照对比**和 cohort coverage 诊断；不要在早已暴露的519个历史 D0 上不停重调参数。

**当前门禁**：`STAGE123_CURRENT_BASELINE=DONE`; `STAGE99_AUTOMATIC_FUTURE_CAPTURE=STOPPED_THREE_LABELS_USER_TERMINAL_READBACK_20261014`; `NEXT_MANUAL_CHECKPOINT=2026-10-28_13:00_ASIA_BANGKOK`; `STAGE118_STRATEGY=REJECTED`; `G0=PARTIAL`; `G4=UNKNOWN`; `NEW_VALID_OOS=NOT_DONE`; `OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `FRANK_UNCHANGED`.
