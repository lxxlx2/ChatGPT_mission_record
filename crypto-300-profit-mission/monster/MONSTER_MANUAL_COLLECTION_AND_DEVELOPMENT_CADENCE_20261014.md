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

主线不依赖日期：继续研究信号在首次 D0 时的真实早报能力、独立底层 crypto/合约单位核验、信号时点盘口/标记价/手续费/滑点、源真实性、历史失败归因及模型样本外验证。用现有 Stage123 数据开发**可复现的全市场新旧手动快照对比**和 cohort coverage 诊断；不要在早已暴露的519个历史 D0 上不停重调参数。

**当前门禁**：`STAGE123_CURRENT_BASELINE=DONE`; `STAGE99_AUTOMATIC_FUTURE_CAPTURE=STOPPED_THREE_LABELS_USER_TERMINAL_READBACK_20261014`; `NEXT_MANUAL_CHECKPOINT=2026-10-28_13:00_ASIA_BANGKOK`; `STAGE118_STRATEGY=REJECTED`; `G0=PARTIAL`; `G4=UNKNOWN`; `NEW_VALID_OOS=NOT_DONE`; `OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `FRANK_UNCHANGED`.
