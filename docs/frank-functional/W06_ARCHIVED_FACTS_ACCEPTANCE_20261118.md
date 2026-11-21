# W06 钱包原始交易复核验收

**原件复核、跨版本读取和 Chrome 本地部署通过。W06 整体为 PARTIAL。** 安装源码为 `00f104dad26f5a2d232251f779b7cd6f255e548c`，分支为 `codex/frank-functional-completion-20261115`。上次已安装的 W06 源码为 `4ceeb23e96bc63bf5b7537e590b5e10238af90c6`。

## 功能与接口

“固定交易事实”逐笔在既有 Frank 归档目录中按签名查找原件，核对 SHA-256、首签名、slot、钱包和已知时间后重放。每笔保留原索引分类、独立重放分类、解析器与原文摘要，供逐笔对照。已核实的原始整数转账明细和开户注资分别记录。失败交易的转账保留为尝试，交易费用仍由原文记录的付款人承担。

快照元数据沿用 v2，扩展位于 `counts.archive_replay`。固定历史页提供快照统计和每笔 `transaction_fact.archived_replay`。归档根由本机已有 Frank 数据目录确定。路径查询只使用已校验的签名，目录和文件均拒绝符号链接。GET 读取已固定的私有工件，已有快照可以继续查询和引用。

## Mac 离线验证

在干净、独立的 detached checkout 中，从 `crypto-300-profit-mission/local-agent` 运行下列测试。Python 执行器直接调用 `pytest.main`，测试前装载 socket 审计钩子。

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
  tests/test_frank_archived_wallet_facts.py
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

Python 444 项、Node 239 项全部通过，均无跳过。Python socket 事件为零。针对性用例覆盖 SHA、slot、时间、钱包错配、不受信任的路径文本、文件与目录符号链接、失败交易、Token-2022、第三方开户、重复资金指令、旧快照引用和归档缺失后的固定版本读取。GitHub 当前返回该源码的状态与 workflow 记录均为空。

原始钱包数据在本地既有 SQLite 快照和 gzip 归档中。重放命令为 `python -B replay_w06_archive.py candidate-00f104d INDEX_SQLITE ARCHIVE_ROOT`，后两项使用本机私有资料的明确路径。脚本及机器证据保存在本机。SQLite SHA-256 为 `98d27fe8d8cad983bf91fc6eaf4141efac7fa8659ca5c6cb1b8f8409cb7afb05`。

- 8,697 条签名全部固定，64 页每页最多 137 条。复核通过 8,662 笔，35 笔存在于旧归档目录，在当前归档范围内标为缺失。摘要或身份不匹配为零。第二次对同一输入生成快照，8,697 个事实 ID 全部沿用。
- 对 8,662 笔原件重新核对摘要、钱包 SOL 前后余额、手续费及执行结果。输出中的每条转账核回原指令位置和金额。归档重放共 5,390 条已执行代币转账，涉及 296 个 Mint，另有 1,406 条已执行 SOL 转账。180 条转账尝试属于失败交易。原索引交易表含 76 个 Mint。
- 3,503 条关联代币账户初始注资复核通过，3,498 条由第三方付给 Frank 所有的账户，5 条由 Frank 钱包付出。2 笔原待核活动在当前解析器中达到主动交易条件。原索引分类在输出中保留。
- 本机全量固定耗时 9.993 秒，分页并逐笔从原件对账耗时 9.210 秒。源快照哈希未变，执行期间 socket 事件为零。该耗时属于本地重放。

## Chrome 实测和安装

- 在原 8766 端口打开候选页，选取先前 9,597 条事实的快照作为父版本。Chrome 固定 9,666 条，新增 69 条、修订 9,597 条。原件核实 9,631 笔，缺失 35 笔，失配与其他未核实均为零。页面读取连续两页各 25 条，签名无重叠，逐笔归档字段存在。
- 实际切回旧 Dashboard 的固定源码。旧版能列出新增的归档快照，并读出其首页 25 条。升级回新版后，用 Chrome 重新打开同一快照，快照哈希、首页各字段和 9,666 条总数一致。
- 从 Git 树核对 636 个安装文件并读取 8766 上的静态字节。本地维护仅涉及 Dashboard。Scanner 原 PID、源码和旧控制文件校验通过，Loop 未加载。Chrome 留在安装版快照页面。本轮真实 RPC 和 CA 查询均为零。

## 仍待完成

完整钱包链史、35 份旧目录原件接入、协议级交换配对、Token-2022 特殊转账指令、关闭账户退款和租金细分、路由费用归属及来源回填的游标验证仍待验收。无法归属的支出保留未知。W07 原币 FIFO 与部分 PnL、W08 持久风险、W09–W14 通用功能与统一验收均在实施清单中。

