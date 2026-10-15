# F02 手动新来源会话：功能目标与验收

日期：2026-10-15 Asia/Bangkok。开发基线：已批准 PR #65 `a59e423304cb2081aef359c0649245c7e1d05b48`。开发入口：设计分支 `design/frank-ca-multiperson-completion-plan-20261013` 的 TODO、跨 PR 门禁和正式开发规则。该分支最新进展指出 R2 Mac 旧档案 HTTP/视觉通过，但没有新持仓查询能力。

最终产品目标：来源可验证的真实钱包观察、准确候选与仓位、可用的界面；与通用任意 CA 尽调入口及 F01 候选在独立联合验收后集成。单个阶段代码通过不等于产品整体完成。

本轮只完成一个可审查的功能流程：手动请求完整双程序 owner RPC → 原文 replay → 冻结 32 Mint 对账 → 新建独立私有 Sidecar → 只读 F02 HTTP/页面。没有重复导入已验收的旧数据库。未改已批准 TTL 算法、F02-R1 API、生产 Dashboard。已批准的 TTL P2 不重开；账户明细 P3 不扩大范围。

## 操作

在 local-agent 目录，使用具有项目依赖的 Python：

```sh
python -m scripts.frank_f02_manual_refresh
```

默认 PLAN_ONLY，无网络、无新目录/数据库。明确授权两次只读 Solana RPC 及新研究会话后：

```sh
python -m scripts.frank_f02_manual_refresh --execute --serve
```

默认 HTTPS 公共 RPC。可在私有环境设 `FRANK_RESEARCH_SOLANA_RPC_URL`，不要将 URL/凭据写入 Git/日志。每次最多两次 finalized owner 查询，第二次沿用第一程序最低 Slot；不自动重试/自动采集。新页面地址默认 `http://127.0.0.1:18766/research/positions`，通过 Ctrl-C 关闭。端口已占用则在采集/数据库之前失败。浏览器仍必须保持原 300 秒 TTL，到期遮罩。

每次新会话保存到 `~/.local/share/frank-f02-research/manual-sessions/session-<uuid>/`：私有完整原文 bundle 和 `positions.sqlite`；没有覆盖旧路径、指向生产路径的选项。原文不进入公开 Git。失败只保存新失败来源，无仓位库/HTTP 服务，不回退旧档案。其他已开旧页面仍属于旧会话，必须打开终端输出的新会话 URL，旧页面依既有 TTL 遮罩。

执行但不加 --serve 只生成核验会话和受限 JSON 摘要。之后可使用既有 `frank_f02_readonly_positions_api --bundle <新bundle> --sidecar <新sidecar> --serve` 只读打开同一会话，不再访问 RPC；旧采集时间不因导入/重启变新。

## 功能范围

- 完整双程序扫描收集全钱包账户，页面仅投影冻结 32 个 Mint；摘要提供全钱包观察 Mint 数，不能称页面已列全部持仓。
- 精确整数/小数、多账户沿用审核过的上游；零账户余额与未观察到账户不同，未知不置零。
- 页面筛选只作用于已载入 32 Mint，刷新只读当前会话。页面明确说明手动采集入口及任意 CA 查询是另一条功能线；没有伪装成链上 CA 查询。
- 不推断 BUY/SELL、成本、USD、PnL、人物最终受益控制权，不接入跟单交易。

## 验证与门禁

本地新增 7 项工作流回归，真实原文 replay、SQLite、socket HTTP（合成来源），专项总 85 PASS；Node TTL/复制/过滤回归 PASS。完整及临时联合测试/远端 exact-SHA CI 另在最终交付记录。新鲜来源 fixture 是合成数据，不是实际 Frank 当天持仓。

代码独立审查、用户授权真实 RPC、新来源 Mac 浏览器交互、F02-R3 全功能和独立最终联合审核分别判定。没有取得这些证据前保持 PARTIAL，不勾选整个 F02 DONE。旧档案用户 Mac 视觉通过不替代新来源业务验收。

NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_AUTOMATION。新增来源真实执行按正式规范需明确授权；开发和合成测试不调用实际链 RPC。
