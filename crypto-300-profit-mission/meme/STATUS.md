# Frank STATUS（当前功能分支唯一状态入口）

## 当前重做主线

更新时间：2026-11-28 Asia/Bangkok。分支 `codex/frank-rebuild-spec-20261122`，本次复核基线 `544880ab71f1913290069a011b7537b2a8eec380`。**源码与隔离验收为 PARTIAL，8766 切换与生产发布为 NO_GO。** 本机 8766 提供的前端资源与旧安装 `fd06df4fbbc25721e0a87a3721571f0dc34cca75` 匹配。

- **准确性**：两日独立核对的 11 笔 Meme 买入均在新版历史。多目标独立买入的归属、追赶空态、新币资格补证与更广覆盖仍待完成。候选实际收件待验。
- **CA 查询**：摘要、分池行情、完整尽调和联合抽样已接通。首屏外语叙事、LP 锁／烧及闭户历史仍有能力缺口。多个新 CA 的全流程实源计时和独立持有人／池同槽待验。
- **迁移和扩展**：备份前置核查与隔离人物查询已实现。候选到目标服务器的恢复、单实例验收和回退，以及多人物采集与投递的隔离链路仍待验证。
- **交付**：三份草稿 PR 已存在。统一固定 SHA 验收入口目前只在草稿中。具体反例、当前证据与发布缺项见[重做反查](../../docs/frank-functional/FRANK_REBUILD_VALIDATION_20261125.md#2026-11-28-主线合同复核)。

## 2026-11-22 版本记录

以下保留 `codex/frank-functional-completion-20261115` 的 W14 历史状态。当前重做主线以本页上方为准。

更新时间：2026-11-22 Asia/Bangkok
更新者：Codex；免费/免review、本地研发及验收后部署授权持续

## 北极星答案（1 行）
**本机 CA 摘要、按需钱包明细和完整报告回读已交付。真实来源覆盖及 Scanner 独立逐笔对账仍为 PARTIAL，生产和交易保持 NO_GO。**

## 当前阶段与预算（最多 5 行）
阶段：W14 本机 Dashboard 安装与 Chrome 回读通过。GMGN、fomo 的关键查询能力及跨来源完整性仍待逐项验收。
分支：`codex/frank-functional-completion-20261115`，PR #253，当前本机 Dashboard 源码 `fd06df4fbbc25721e0a87a3721571f0dc34cca75`
来源：固定钱包事实、既有余额与行情、三个不同 CA 的隔离实测、已有归档和合成输入
费用/权限：使用既有免费来源。CA 实测在隔离环境执行，无真实通知、签名和交易
运行：Dashboard 沿用本机 8766，Scanner 保持 `1f2c6afc28b9988eaacdc896562ff9a71b78f801`，升级核对了进程和受保护台账摘要

## 本周唯一目标（1 行）
按[完整技术方案](../../docs/frank-functional/TECHNICAL_PLAN_20261115.md)与[59项实施映射](../../docs/frank-functional/implementation-plan-v1.json)推进。每个新真实 CA 场景使用此前未做过真实验收的 CA。先按[功能差距](../../docs/frank-functional/TECHNICAL_PLAN_20261115.md#134-gmgn-与-fomo-功能差距)补日常查询，Scanner 准确性独立使用钱包窗口逐笔核验。

## 长期主线

- 准确性优先。分支已纳入私有 RPC 接线和离线逐笔对账工具。真实钱包区间、补采恢复及链上事件到信号的实际时延仍待独立核实。
- 服务器可迁移交付和多候选人隔离依次展开。当前仍为单 Frank 运行，本地 W14 通过与真实来源验收分别记录。 [三个要求的实施与验收](../../docs/frank-functional/FRANK_ACCURACY_MIGRATION_EXTENSION_PLAN_20261119.md)

## 真实来源仍待验证

- [B] **W09/W12 来源与查询**。逐地址余额复核在相近时点一致，第二来源独立全 Mint 枚举返回 `HTTP_403`。同槽、全角色与代表协议矩阵仍缺。分池 K 线及近期逐笔成交未接入。
- [B] **W10/W11 代表样本**。完整尽调跑完本次地址窗口，耗时约 5 小时 51 分钟。已关闭账户全集、真实终身首买和真实官方认领仍缺证据。
- [B] **W13 真实送达**。Option3 完成隔离合成队列；真实渠道与收件延迟须按独立授权验收

## 等用户授权（最多 3 项）
当前无权限或review阻断。未启用的真实通知/签名/交易/Loop与已停止收益研究不由本地研发自动恢复；不新增批准步骤

## 本周已关闭（最多 5 行）
- [B] W10–W14 交付分散持有人历史、同槽首买歧义、可信叙事与认领、独立枚举、通知台账归档及合成恢复。原端口完成 Chrome 验收及本地发布。[主线验收与命令](../../docs/frank-functional/FRANK_MAINLINE_ACCEPTANCE_20261119.md)
- [B] W09 供给夹逼权限时间、Owner 批次恢复和多池分批。Chrome 验收 105 个合成池候选，并验证旧归档缺证时撤下全局 Top10。[W09 验收与命令](../../docs/frank-functional/W09_HOLDER_POOL_ACCEPTANCE_20261119.md)
- [B] W08 以 9,708 条固定事实生成 76 个分析条目和 76 条证据缺口。同输入重算新增为 0，安装后读取同一分析。合成报价验证显式输入、路由和自然过期。[W08/W09 验收与命令](../../docs/frank-functional/W08_W09_RISK_AND_IDENTITY_ACCEPTANCE_20261119.md)
- [B] W06/W07 归档全量核对和原币 FIFO 已验收。完整链史、未归属费用、公开平台对照和整仓估值保留证据边界。[W06/W07 验收](../../docs/frank-functional/W06_W07_FIFO_ACCEPTANCE_20261118.md)
- [B] W01–W05 已交付完整索引分页、来源合同、全钱包余额、参考行情、关注与备注。[余额与行情验收](../../docs/frank-functional/SOURCE_BALANCE_MARKET_ACCEPTANCE_20261117.md) · [W05 及快照基础验收](../../docs/frank-functional/WATCH_MANIFEST_ACCEPTANCE_20261117.md)

## 已知但故意不做（C 类清单）
- 原10月故障归因按用户取消。曾用于真实验收的 CA 只使用既有原件离线复算。
- 多人物/多钱包启用、多链、整套旧Sidecar与收益研究按G1延期，不批量合并旧分支
- 前端视觉/布局改版排除；仅补数据操作必要绑定、范围与来源说明
- 无币对/无价资产不填0；部分估值不当钱包净值；开放账户或本地历史快照不当终身完整历史

## 历史证据入口
[基线59项审计](../../docs/frank-functional/REQUIREMENTS_AND_GAPS_20261115.md)、[W01索引验收](../../docs/frank-functional/INDEXED_ACTIVITY_ACCEPTANCE_20261115.md)及[原运维固定状态15a782](https://github.com/lxxlx2/ChatGPT_mission_record/blob/15a782d841d2cf4d88cb27fa95654bdaefe2e4b9/crypto-300-profit-mission/meme/STATUS.md)保留旧时点，不覆盖当前事实
