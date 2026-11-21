# W08 持久风险与手动报价、W09 Mint 身份验收

固定源码 `0fd546b089b7526046308c5aa9ac60057e0100fd`，父提交 `49ecb750f533fcd1b46d7f88a82af3add46c056f`。原分支 PR #253。W08 本地功能通过，真实报价来源未实测。W09 本轮通过的是 Mint 身份和权限识别，W09 整体仍为 PARTIAL。

## W08 本地风险记录

- 支持读取指定 facts manifest。留空刷新会为本次请求固定当前本地索引。分析输出保留事实与分析截止时间、来源摘要、风险种类、上一条变化和所选证据。近期来源窗口、历史决定和执行资格独立显示。
- 重算只访问本地源。相同请求键读回既有运行。按来源时点拒绝倒退。SQLite 原子提交运行、去重状态和更新，中断可安全重试。GET 无写入。近期卖出和重新买入采用已有 F01 时间窗，已归档历史不变成新提醒。
- 记录行情过期及有效同币种参考价高于已核实买价的变化。减仓只使用有效余额快照，留作风险事实。无法确认的比较记录原因。运行和风险记录的通知权限均为 false。
- 用户必须填写输入和输出 Mint、原始整数金额及滑点。服务只调用已有 Jupiter GET 报价路径的免费免密钥方式。只返回绑定输入的路由和凭据，时效为 30 秒。HTTP 失败使用安全错误码。GET、页面打开和分析刷新均不询价。[Jupiter 报价合同](https://developers.jup.ag/docs/swap/v1/get-quote) · [Jupiter 免费访问](https://developers.jup.ag/)
- Chrome 选择 9,708 条实际本机事实的固定快照，分析 76 个 Mint。第一次产生 76 条证据缺口，同一输入重算新增为 0。HTTP 按每页 25 条读完 4 页，76 个更新 ID 唯一。实际数据中未观察到应触发新提醒的近期卖出，本轮没有真实通知。
- Chrome 在隔离报价传输中验证空输入、显式原始金额、路由、自然过期。合成传输调用一次。预览禁止所有外部 socket 连接。安装使用正式代码路径，合成传输仅存在于预览。

## W09 身份子项

- 缺失账户、普通代币账户、错误 owner、未初始化、非法权限地址或无有效槽位均返回未核实。Token-2022 元数据只使用单一、明确绑定同一 Mint 的扩展。相同名称的其他 Mint 元数据不能证明当前更新权限。
- 固定 SHA 离线重放 3 个已有 Token-2022 Mint 的缓存原件，三份结果均核对请求键、内容哈希、slot、供应量。另用普通 SPL 与各类反例夹具覆盖基本类型。原件重放不发起 CA 作业。
- 全量持有人、受益人角色、候选池集合及代表性协议矩阵仍属于 W09 后续验收。

## 命令与结果

在固定 SHA 的干净 detached checkout 进入 `crypto-300-profit-mission/local-agent`。Python 用 pytest 执行下列测试组，运行器预装 socket 审计钩子。

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
  tests/test_frank_v1.py \
  tests/test_frank_durable_risk_and_quote.py \
  tests/test_meme_wallet_cluster.py \
  tests/test_meme_global_pool_discovery.py \
  tests/test_meme_ca_completeness.py
node --test \
  tests/test_frank_ca_get_resume.mjs \
  tests/test_frank_ca_report_render.mjs \
  tests/test_frank_ca_rpc_budget_ui.mjs \
  tests/test_frank_d2_ingress_ui.mjs \
  tests/test_frank_evidence_manifests_ui.mjs \
  tests/test_frank_history_coverage_ui.mjs \
  tests/test_frank_research_ui.mjs \
  tests/test_frank_risk_and_quote_ui.mjs \
  tests/test_frank_wallet_cost_ui.mjs \
  tests/test_frank_watch_metadata_ui.mjs
```

**646 项 Python、248 项 Node 全部通过。** Python socket 事件为零。另运行 Node 的 frank 通配测试时，独立 CA 浏览器脚本因本机无 `playwright` 模块在初始化退出，其他 248 项通过。该脚本列为未验收，实际 Chrome 操作另有记录。

## 本地部署

原 8766 端口预览后实际恢复旧 Dashboard，验证上一轮 FIFO 快照仍可读取。随后安装候选，校对 648 个 Git 文件、静态资源和运行目录。安装后 Chrome 读取原分析运行和持久风险记录。Scanner PID、旧控制文件校验值及 Loop 状态均通过部署前后核对。真实报价、通知、交易、签名、CA 新作业和真实 RPC 次数均为零。生产保持 NO_GO。

