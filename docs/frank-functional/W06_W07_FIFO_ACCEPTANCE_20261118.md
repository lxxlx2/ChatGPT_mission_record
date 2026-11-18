# W06 钱包原件与 W07 原币 FIFO 验收

**W06 与 W07 的本地功能已通过。** 固定测试和安装源码为 `8575e78b726e4076233409fd565b65f9be2199d9`。本轮交易解析、核心账本和实际账本生成源码为 `0d4e74516aed814a0195321b1157798072ab0d08`。后续源码提交只改关户转回的展示及其前端回归，复用已固定的事实和账本。实施分支为 `codex/frank-functional-completion-20261115`，PR #253。目标范围是已有索引和已捕获来源可证明的本地结果。

## W06 原件、交易事实与恢复

- 明确接入机器上既有的旧归档。查找先用当前归档，文件缺失才尝试显式配置的旧归档。每笔均核对 SHA-256、首签名、slot、钱包和时间，既有索引记录中的文件路径不参与产品文件定位。
- 整个离线档案为 8,697 笔。全部逐笔核回原件，其中 35 笔来自旧归档，缺失或错配为零。每页 137 条，读完 64 页。换新版本重复固定相同输入，事实 ID 全部沿用。
- 区分钱包原币余额、网络费、账户初始注资、关闭时 SOL 转回与未分摊租金。8,697 笔中有 3,527 条付款人与指令可核实的 ATA 初始注资，5 笔关户余额满足独立核对。Token-2022 明示转账费分别保留毛额、扣费和净额。普通转账缺少费率证据时不推断金额。[Solana Transfer Fees](https://solana.com/docs/tokens/extensions/transfer-fees)
- 逐笔核对 5,487 条已执行代币转账和 1,413 条 SOL 转账，代币指令覆盖 300 个 Mint。180 条失败交易的转账尝试不进入已执行金额。168 笔按单标的和单报价资产的相反钱包流量核实，复杂路由仍保存原始指令及未决原因。
- 分页回补用隔离 SQLite 和测试传输复现重复页、原件短暂不可用及进程重启。故障后保留最后已入库游标。恢复后只补缺失签名，重复执行新增为零，outbox 为零。

## W07 成本、估值及分页

- 显式从不可变 facts manifest 重建，以输入快照和 FIFO 版本固定账本。创建同步返回 201。相同输入与版本复用账本。读接口按固定 run、Mint 和游标分页。
- FIFO 以原始整数和精确分数记账。钱包内部迁移保留成本，来源不明的转入进入未知成本批次。部分成交只计算已同时核实成本及同币种收入的那部分，网络费、初始注资和关闭退款单列。有效时点的参考价可产生范围内的估值与部分未实现盈亏，过期或缺价保留未知。
- 独立旧快照的账本包含 3,422 个 Mint。逐页核对末端批次数量，重算 28 个 Mint 的 47 笔卖出所覆盖的原币盈亏。227 个有正数索引余额的 Mint 在该离线价格缺失场景下保持未估值。捕获整个 W06 档案 13.387 秒，W07 重建 0.733 秒，均为本地工作量。
- 已运行跨币种、含未知入金的 FIFO、多次买卖和部分退出、内部账户迁移、同 slot 顺序未知、失败交易、重复写入、重启、固定游标、数据损坏、过期行情及缺价用例。

## 实际命令

在固定 SHA 的独立 checkout 中进入 `crypto-300-profit-mission/local-agent`。Python 执行器在调用 pytest 前禁用 socket。

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
  tests/test_frank_wallet_facts.py \
  tests/test_frank_archived_wallet_facts.py \
  tests/test_frank_wallet_cost_fifo.py \
  tests/test_frank_wallet_cost_store.py \
  tests/test_frank_local_signals.py \
  tests/test_frank_v1.py
node --test \
  tests/test_frank_ca_get_resume.mjs \
  tests/test_frank_ca_report_render.mjs \
  tests/test_frank_d2_ingress_ui.mjs \
  tests/test_frank_ca_rpc_budget_ui.mjs \
  tests/test_frank_research_ui.mjs \
  tests/test_frank_watch_metadata_ui.mjs \
  tests/test_frank_evidence_manifests_ui.mjs \
  tests/test_frank_history_coverage_ui.mjs \
  tests/test_frank_wallet_cost_ui.mjs
```

Python 543 项、Node 246 项全部通过，均无跳过。Python socket 事件为零。实际归档核查命令为 `python -B accept_w06_w07_fixed.py CHECKOUT INDEX_SQLITE CURRENT_ARCHIVE LEGACY_ARCHIVE`，输入和脚本在本机。索引 SHA-256 为 `98d27fe8d8cad983bf91fc6eaf4141efac7fa8659ca5c6cb1b8f8409cb7afb05`，运行前后相同。GitHub 当前无此提交的 CI 状态或 workflow 运行记录。

## Chrome 与本地 8766

- Chrome 基于上一版生成快照，共 **9,708** 条，全部找到原件、摘要相符，含 35 笔旧归档。页面显示 182 笔可核实钱包边界交换、5 笔已核实关闭退款。
- 同一界面复用快照创建 W07 账本。Chrome 两页各 25 个 Mint，无重叠。重复重建返回同一账本。分别用两种资产核对同币种已实现盈亏和未知转入成本的页面结果。
- 同一 Chrome 账本用本机 HTTP 分 24 页读取，**3,814 个 Mint** 全部可查。逐行检查未消费批次数量，并重算 29 个 Mint 的 52 笔可覆盖卖出。当前 234 个有余额的 Mint 无合格新鲜价格，显示未估值。浏览器读回重启前的账本 ID、首页和相同未估值数。
- 实际回滚并核对旧版能读取新版事实快照。最终安装时核对 642 个 Git 文件、端口和静态字节。最终 Chrome 重新读取账本，关户转回和租金退款分别展示。Scanner PID 与已保护的控制文件校验通过。Chrome 留在钱包成本页。

## 证据范围

以上覆盖已索引钱包历史和已有归档。钱包终身链史、全部协议内部归因、每笔纯租金、真实整仓价值、未实现总盈亏及公开平台同窗口对照尚无足够证据。测试覆盖新鲜与过期行情分支，Chrome 使用本机可读行情，当时无合格新鲜报价。W08–W14 继续按剩余任务清单。生产和交易状态保持 NO_GO。

