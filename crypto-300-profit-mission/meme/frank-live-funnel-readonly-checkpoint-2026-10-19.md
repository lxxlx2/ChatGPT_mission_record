# Frank 现有 Mac 本地索引与候选资格：只读事实核查任务

Date: 2026-10-19 Asia/Bangkok
Status: **MAC_LIVE_GET_EVIDENCE_PENDING / NO_CHAIN_COMPLETENESS_CLAIM / NO_MERGE / NO_DEPLOY**

## 用户价值与判定标准

优先回答：Frank 是否在运行？最近 24 小时本地记录了多少链上签名与已识别买卖？候选为何无可跟项？运行环境实际提供独立 F01 资格接口吗？本地观察池有多少历史项目？

不根据已有的真实 Safari 页面截图直接推定全链覆盖，也不把历史 BUY、模型持仓、早前 Jupiter 报价当作当前可买交易。

## 当前仓库的真实差异

- 当前主线 `main` HEAD 在建分支时为 `b8330e55078e4e0a9243c31d3fa8346598a1628b`，它具有 `GET /api/runtime`、`/api/coverage`、`/api/candidates` 和 `/api/frank-observed-watchlist`，但没有 `/api/follow-opportunities`。
- PR #106 产品 HEAD `8a8b4fcc36242c0ba03b03170225f723d847fa53` 的独立 F01 接口已通过代码和离线测试，其历史判断 503 页面恢复功能已在实际 Mac Safari 验收通过。但 PR #106/#107 仍是 Draft/未合并/未部署，不能声称已进入主线或实际 Dashboard。
- 本轮比对 `main...PR106`：从共同祖先 PR106 超前 325 commits，main 自身超前 276 commits；开发分支显示约 141 个路径差异，属于大范围分叉，**禁止整串 PR 盲目合并**。

## 具体只读操作

新增脚本位于 `local-agent/scripts/frank_live_funnel_readonly.py`。它只向已存在的 Mac localhost 端口逐个 GET 六个已知路由：

`/api/runtime`、`/api/control-health`、`/api/coverage`、`/api/candidates`、`/api/frank-observed-watchlist`、`/api/follow-opportunities`。

默认两次采样，间隔 6 秒。每请求不超过 3 秒 socket 等待、2 MB JSON body 上限，拒绝 HTML、截断响应和未知端点。额外 F01 路由 404 表示**运行后端当前不提供该路由**，不能解读成 0 可买；若返回 200 则只统计服务声明的有效/排除项数及原因类别，不赋予交易权限。

ZIP 只含 `frank-live-funnel-summary.json`，无原始响应、CA、签名、钱包地址、原始错误详情、资金金额或生产路径；Finder 自动选中 ZIP。所有来源类别从固定白名单映射，无外部字段注入。报表明确标记 `production_backend_sha=UNVERIFIED`、`full_chain_coverage_verified=false`。

**不运行新 Solana RPC，不打开生产 SQLite、不重启、不开服务、不改现有文件、不发邮件、不交易。** 这是对现有索引与过滤器的表面诊断，不能证实全链完整性或已获利机会。

## 下一步

1. CI 和独立代码审核通过后，Mac 本机执行一次固定 SHA 命令，私下上传 Finder 选中的 JSON-only ZIP。
2. 用实际统计分清 `RUNTIME_OFFLINE`、`INDEX_SOURCE_UNKNOWN`、`NO_RECENT_INDEX`、`MODEL_NO_CURRENT_BUY`、`QUOTE_STALE`、`F01_ROUTE_MISSING` 等原因；未核实的链上缺口继续标记待核。
3. 仅对真实数据明确的功能缺口设计最小业务修改与可合并的主线集成，不绕过 F01 BUY 保护、不改已审过的 PR #106/#107 和其它监控。

**停止标准：获得两次可归因的真实只读证据并确定下一项实际阻塞；不要为了非阻断测试瑕疵启动新一轮截图与工具循环。**
