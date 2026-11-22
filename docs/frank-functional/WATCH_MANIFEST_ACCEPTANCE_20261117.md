# W05 用户观察记录与 W06 不可变本地历史基础

结论：**W05本轮PASS并已在原8766部署；W06不可变历史基础PASS，W06整体及Frank整体PARTIAL。**
固定源码、独立测试与安装：`166f3abde36fd9d6f0a09b447169a00e2e3f7ab0`。后续仅证据／状态文档提交不改变local-agent字节。
本轮基线：`d3cd6f7b40fb9354d6c7ec2eb1d4a2a624d6859a`。
产品基线：`ee81a0f44c27eb539c3c874963d311d4e4d5761f`。仍在原分支与PR253。

## 实际行为

- W05新增持久收藏、4000字符纯文本备注、FOLLOW/HIDE/DEFAULT用户选择；与模型仓位、链上余额和源信号独立。
- 只在显式PATCH后写本机派生研究库。GET不建库、不访问RPC、不通知；修改当前行、before/after审计、幂等结果及全局revision在同一SQLite事务提交。
- 同键同body原样返回第一次结果；同键不同body及旧revision返回409。并发编辑保留一个成功结果，另一个明确冲突。重启后原记录及审计可读。
- 默认观察筛选接入FOLLOW/HIDE，收藏优先排序；全部／用户隐藏／收藏筛选仍可找回。索引之外的用户Mint标USER_ONLY，不填造买卖或仓位。
- 列表和审计按游标翻页，无总Mint或事件上限；游标绑定查询、库身份和元数据revision，期间更新时409要求从头读取。
- 页面保存前必须显式读取。冲突保留草稿，读取最新版本后才可保存；未确认的超时重试沿用同请求键。备注、审计和快照事实按文本显示。
- W06基础新增显式本地历史固定：只读一致SQLite源快照，完整保留源表及全部原始交易腿，固定当时规范活动投影，保存代码／解析器／来源绑定／计数／哈希。
- 后续源行纠错、回填、代码升级不会重新解释旧快照。固定活动API返回已物化规范行和未解释raw_trade_legs；读取核验工件hash，损坏时503，不回退当前来源。
- 同一内容的不同manifest拥有不同游标身份。创建失败不发布半成品；旧快照可读。源数据库仅mode=ro连接，派生工件写入独立私有目录。

## 合同调整

API30对本地activity/facts同步完成后返回201 COMPLETE；不额外增加202后台任务。positions/market manifest未实现，非法类型400。API10/11/27接线并新增只读API33审计查询；技术方案及机器合同已同步。

## 已运行离线验证

已从GitHub固定SHA建立独立detached checkout并确认clean，相关Python **408通过**、Node **233通过**，无失败／跳过；Python审计钩子禁止全部socket，记录为0。以下为实际测试参数（Mac隔离Python3.14虚拟环境；执行器再加`-ra`结果摘要参数）。GitHub statuses/workflow均无记录，未标CI通过。Chrome结果单独如下。

```sh
python -B -m pytest -q -p no:cacheprovider tests/test_frank_source_evidence.py tests/test_frank_wallet_refresh.py tests/test_frank_market_observations.py tests/test_frank_research_data.py tests/test_frank_activity_paging.py tests/test_frank_g2_d1_d2_dashboard.py tests/test_frank_wallet_watchlist_v2.py tests/test_frank_wallet_inventory_v2.py tests/test_frank_activity_watch_dashboard.py tests/test_frank_intelligence_dashboard_integration.py tests/test_frank_amount_free_intelligence.py tests/test_mission_control_dashboard.py tests/test_frank_d2_http_route.py tests/test_frank_d2_ingress.py tests/test_meme_market_and_rpc.py tests/test_frank_watch_metadata.py tests/test_frank_evidence_manifests.py
node --test tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs tests/test_frank_d2_ingress_ui.mjs tests/test_frank_ca_rpc_budget_ui.mjs tests/test_frank_research_ui.mjs tests/test_frank_watch_metadata_ui.mjs tests/test_frank_evidence_manifests_ui.mjs
```

反例包括：未建库读取、双线程首写、过期revision、同键变体、注入事务失败、全量138条元数据分页、12条审计分页、错误来源游标、HTML备注、多行备注、延迟响应、超时不明结果重试、重载只读、manifest源行纠错与回填、原始重复交易腿、未checkpoint的WAL、损坏工件和metadata、失败创建、manifest过滤游标和固定fence。

## 实际Mac／HTTP／Chrome与8766交付

- 已有一致本地快照SHA256 `98d27fe8d8cad983bf91fc6eaf4141efac7fa8659ca5c6cb1b8f8409cb7afb05`：8697签名、197条原始交易腿、76个交易Mint，137容量共64页；独立SQLite行身份和每条原始腿完全相等，源文件字节未变，socket0。捕获0.483秒、全部分页4.384秒；这是本地索引操作耗时，不能代表完整CA查询。
- Chrome显式POST固定当时实际本地索引：9520签名、211原始交易腿、76个交易Mint；HTTP全部70页（容量137）在5.842秒内与固定源工件独立逐行对账，无漏无重。它与上一条旧快照时间和分母不同，均不是本轮真实RPC采集。
- Google Chrome实际点击：读取／多行及HTML字面备注／收藏／FOLLOW／保存版本1；重载前后审计仍1条；第二HTTP客户端写版本2，旧页面保存409、草稿保留；读取最新2仍保留草稿；在Chrome恢复原值后保存3。备注、收藏与观察选择均恢复验收前值；3次变更审计有意保留。
- Chrome实际创建固定历史、读取第一页和下一页（第二页首index_rowid9495）；发布重启后，元数据3及原9520条manifest仍可读取／分页。浏览器留在原8766。截图服务不可用，验收依据原生Chrome可访问性观察及独立HTTP／SQLite记录，不虚构截图。
- 同端口候选预览通过后，实际启动旧9f版本并核对完整旧app.js字节，再发布166f版本并核对627个Git文件、进程release身份和静态字节。仅Dashboard维护；旧control／投递文件hash未变，Scanner PID及源码未变／LIVE无漂移，全部已加载label核对Loop未加载。
- [机器证据](watch-manifest-acceptance-20261117.json)区分独立离线、既有快照重放、实际本地索引、原生Chrome和本地部署。私有原件不提交公共仓库。

## 尚未关闭

W06整体仍PARTIAL：新复杂交易解释、每腿费用／租金归因、版本纠错supersedes及完整历史覆盖API仍未完成。固定已索引数据不证明完整钱包链史或终身首买。W07成本/FIFO/PnL、W08持久风险、后续CA矩阵与统一整体验收继续按原计划。

本轮没有真实RPC／行情／CA POST，不新增来源、Key、收费、端口、监控或自动任务，不发送通知、不签名或交易、不合并。INVEST_NO_GO／TRADE_NO_GO保持。
