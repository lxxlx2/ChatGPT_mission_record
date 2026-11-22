# W06 钱包历史覆盖与版本化交易事实验收

**本地钱包历史覆盖、逐笔事实固定和版本修订通过 Mac 与 Chrome 验收。W06 整体为 PARTIAL。** 安装源码为 `4ceeb23e96bc63bf5b7537e590b5e10238af90c6`，父提交为 `2f1fc730cfa65d7f670f4fc760ba0adea95147c6`。

## 从页面能核实什么

- 在 Frank 信号页展开“Frank 钱包历史覆盖”，可读取全部、24 小时、7 天、30 天四个时间窗。结果列出索引活动、类别、无区块时间的记录、待解析数及本窗口检测到但尚未入索引的数量。全链覆盖、早期缺口和回补独立显示。
- 在“固定历史证据快照”创建交易事实，可逐页读回原币整数、交易费用及钱包承担的份额、来源与解析器版本。重复生成相同事实沿用 ID，修订保留前身和原因。原始活动 v1 可继续读取。
- 当前逐笔事实取自已有的规范化索引。历史记录中未保存的指令、账户租金和路由费用归属均保留未知。

## 固定提交的离线回归

在固定提交的干净 detached checkout 中从 `crypto-300-profit-mission/local-agent` 运行。Python 直接调用 `pytest.main`，在执行前安装审计钩子禁止 `socket.*`。以下命令可在装有 pytest 的 Python 环境重跑同一组用例。

```sh
python -B -m pytest -ra -q -p no:cacheprovider \
  tests/test_frank_source_evidence.py \
  tests/test_frank_wallet_refresh.py \
  tests/test_frank_market_observations.py \
  tests/test_frank_research_data.py \
  tests/test_frank_activity_paging.py \
  tests/test_frank_g2_d1_d2_dashboard.py \
  tests/test_frank_wallet_watchlist_v2.py \
  tests/test_frank_wallet_inventory_v2.py \
  tests/test_frank_activity_watch_dashboard.py \
  tests/test_frank_intelligence_dashboard_integration.py \
  tests/test_frank_amount_free_intelligence.py \
  tests/test_mission_control_dashboard.py \
  tests/test_frank_d2_http_route.py \
  tests/test_frank_d2_ingress.py \
  tests/test_meme_market_and_rpc.py \
  tests/test_frank_watch_metadata.py \
  tests/test_frank_evidence_manifests.py \
  tests/test_frank_wallet_coverage.py \
  tests/test_frank_wallet_facts.py
node --test \
  tests/test_frank_ca_get_resume.mjs \
  tests/test_frank_ca_report_render.mjs \
  tests/test_frank_d2_ingress_ui.mjs \
  tests/test_frank_ca_rpc_budget_ui.mjs \
  tests/test_frank_research_ui.mjs \
  tests/test_frank_watch_metadata_ui.mjs \
  tests/test_frank_evidence_manifests_ui.mjs \
  tests/test_frank_history_coverage_ui.mjs
```

Python 430 项、Node 238 项全部通过，均无跳过；Python socket 事件为零。测试包含来源错配、无时间戳、陈旧前端响应、损坏工件、未识别的原始字段、失败交易、重复指令、费用付款人和快照修订。该源码在核查时没有 GitHub CI 状态或 workflow 运行记录。

## Mac 档案重放

本地命令为 `python -B replay_w06_facts.py candidate-4ceeb23`，后一个参数指定已核对源码的独立 checkout。执行脚本及私有原件保存在本机，仓库测试使用可分发夹具。

- 来源 SQLite SHA-256 为 `98d27fe8d8cad983bf91fc6eaf4141efac7fa8659ca5c6cb1b8f8409cb7afb05`。8,697 个签名、197 条索引交易腿、交易表内 76 个不同 Mint。按每页 137 条读完 64 页，核对全量签名、逐腿来源引用、唯一性，全部匹配。
- 固定讲求同一输入可复核。再次固定同一档案，8,697 个事实 ID 全部保留。原件抽样为主动 6 笔、被动 6 笔、待核 6 笔、ATA 3 笔、失败 3 笔。24 笔均核实原文哈希、钱包前后余额、实际手续费与成功状态。9 笔由钱包付费，15 笔由其他地址付费。
- 首次固定耗时 1.975 秒，读完固定快照耗时 5.895 秒。此耗时只对应该档案及本机。源文件哈希前后一致，socket 事件为零。

## Chrome 与安装版

| 实际操作 | 观察结果 |
| --- | --- |
| 在原端口 8766 切换四个窗口并手动读取 | 验收时全部 9,597 条、24 小时 326 条、7 天 2,315 条、30 天 6,081 条。全范围待核 517 条，已检测但未入索引为零，全链历史缺口未知。 |
| 创建事实快照，读第一页和下一页，以第一版为父再创建 | 两页各 25 条且不重叠，新版保留原有 9,597 个事实 ID，无新增或修改。 |
| 安装后重新打开 Chrome，读取部署前固定的版本 | 原快照仍有 9,597 条，首页 25 条，下一页可用。随后单独读取活动索引，截至 11 月 18 日 07:34:43（曼谷时间）已有 9,631 条，其中 518 条待核。 |
| 同端口恢复原版本并验证，再安装候选 | 安装 SHA 与 633 个 Git 文件匹配。Scanner 进程与源码未发生漂移，原控制文件校验匹配，Loop 未加载。 |

这一轮使用本机索引与已归档原件。CA 查询和新链上采集次数均为零。下一项是用可信原件重放复杂交易及账户生命周期、验证可归属的资金流，再为 W07 生成可用于 FIFO 的输入。所有钱包的完整链史、整仓成本与 PnL 仍待验证。

