# Frank P1 — CA 可用性与当前 owner 持仓验收主线（2026-10-25）

状态：PLAN/CODE-ONLY。没有执行任何生产 HTTP、链上 RPC、CA POST、部署、合并、端口/服务、通知或交易操作。

## 固定身份

- 当前正式 Dashboard 产品 SHA：914e9e47fed2e60bc24690fcb083413a64d4e681，运行于现有 127.0.0.1:8766；证据 [PR #178 生产报告](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6388948971)。完整候选 446 文件，manifest SHA256 9a06f5f29fce05ccade8caa2b90d6d6c0c4248d2e6ab4e45aa26fa9d3f401062。保留旧版 PR168 656ed2c96f4210d106d7b1129ec6cf8d7c4586f3 的回滚包。
- 原 PR178 Draft HEAD ea9a7715beb4d2a55ae956bf993828cbddcb50e5 **不是**已部署代码；不要错误引用它的 root-level D2 reader。
- D2 历史 JSON 已导入且只能作为 2026-10-23 14:46:32Z 两个不同 finalized slot 的历史证据：4148 Mint／3275非零、SPL 460482174，Token-2022 460482176；不能把页面显示说成当前持仓或已核实 PnL。
- Issue #165 两项原 P1 均保持 OPEN：[CA 深度分析掉线与实际持仓无法核实](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165)。

## P1-A：CA 当前真实用户流程

**核实的产品代码事实**

1. 已安装 app.js 的 pollClusterJob 支持最多 3 次 bounded GET-only 自动重试（1.5／3／6秒）、同 job ID 手动恢复、会话 pending ID，以及独立读取已保存同 Mint 报告的 GET /api/cluster-latest。对应前端修复随 PR168 上线，避免重复开发已有重试或新建另一个服务。
2. server.py::ClusterJobManager.jobs 是进程内存字典。2026-10-25 03:05 Dashboard 经授权 restart 后，之前进程的 job_id 再 GET /api/cluster-analysis 可能返回 404。此时已有 latest.json 仍可能存在，必须分别核对；不能把 404 猜作旧 worker/RPC 失败，也不能声称缓存一定对应旧 job。
3. server.py 的 CA POST 调用 submit 并可在后台新发 Solana RPC。任何 Quick／Standard／Deep 新扫描都属于需要单独明示授权的行动。单独读取旧报告的 GET 不会启动新 job。
4. [原 Mac D0 只读诊断](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6347259929) 找到旧页面对一条失败 poll GET 停止恢复的缺陷（现已代码修复），但没有证明底层 TCP 原因、原 job ID 和当前 Deep 全流程已无错误。生产 Chrome 的 5/5 PASS 只验证 CA 按钮可显示，未提交扫描。

**下一段 Mac 有界零 RPC 诊断，执行前须确认用户单独同意生产只读诊断**

- 验证当前 8766 实际代码、服务身份和端口；仅查看已有浏览器会话/已有历史报告。若页面没有完整可核对的 job ID，不得编造新 ID 或启动扫描。
- 最多一次对已知有效 job_id 的 GET /api/cluster-analysis；无有效 ID 时最多一次用户指定 Mint 的旧缓存 GET /api/cluster-latest。记录 HTTP code／耗时／阶段／是否缓存／报告观察时间、special normalization 与链上覆盖，不上传 ID、Mint、报告内容或真实原始端点凭据。
- 实际 Chrome 页面只测试「查看已有历史报告」或「继续读取原任务」这两种 read-only 功能，不点 Quick／Standard／Deep 提交按钮，不 POST，不触发 worker/RPC。验证失败是 transport、404 after restart、cache absent、report render 错误还是部分覆盖，不用「Failed to fetch」笼统定性上游 RPC。
- 成功仅标 GET_ONLY_CACHE_RECOVERY_PASS，绝不宣称 NEW_CA_QUICK_STANDARD_DEEP_VERIFIED。任何真正 Quick／Standard／Deep 完整分析必须另拟明确 RPC 数量／上限／时间／资金与停机条件、获取用户明确同意后才 POST。
- 不写 SQLite、不重启、不改策略、不发通知、不交易。保存脱敏日志、测试 SHA 和限制到 Issue165，不能泄露真实 job ID。

## P1-B：实际 owner 账户快照，独立于已有 D2 历史视图

**确定的缺口**

- 现有 Oct23 双程序快照只证明当时，不证明 Oct25 或未来的余额。已有 3 份历史归档在 PR60 下通过离线回放但全部 dated；不能跨时间或程序拼凑原子余额。
- 固定来源 PR60 e4529ba7069e5499d12323a7160ceac08c481fae 的 scripts/frank_capture_owner_full_receipts.py 支持默认无网络 PLAN_ONLY、单次 --execute 两个 getTokenAccountsByOwner HTTPS finalized owner 程序查询、--replay-bundle 纯离线校验。对每条调用有 wire bytes 上限、25 秒超时、HTTP framing 严格验证和拒绝 redirect 的保护。
- 在没有新 RPC 授权前只允许审代码、计划和现有历史；**绝不能运行 --execute、--import-sidecar、生产私有回执覆盖或重导旧 D2**。

**需要下一次另行批准的最小采集（本文件不是授权）**

- 从精确固定 SHA 的 PR60 干净离线 checkout、固定 Frank owner，使用现有被允许的 RPC provider（不得额外安装／换新 provider）发送恰好最多两次独立 finalized getTokenAccountsByOwner：SPL Token 与 Token-2022 各一次。不得失败重试、不得建立新常驻服务，不扫描历史交易或新 CA，不查询任意其它地址。
- **新发现必须修正的门禁：**固定 PR60 的 `wallet_full_rpc_evidence.py::collect_owner_full_receipts` 对第一条程序查询的异常使用 `continue`，所以直接运行 `frank_capture_owner_full_receipts.py --execute` 时，第一条失败后仍可能调用第二条。未来单次 RPC 授权必须采用经过独立代码审查的外层**逐条确认**执行器：第一条 HTTP 完整性、来源、program、owner、slot、原始回执保存与校验**全部成功**后才允许第二条；任何失败立即停止、不重试、不执行第二条、不补发、不以部分归档冒充完整覆盖。这只是研发设计门禁，绝不据此修改或执行当前 PR60 采集器；采集脚本实现与固定 SHA 必须先接受离线测试及独立复核。
- 仅保存本机私有 owner-only 0700目录中的 0600原始回执；校验响应 HTTP framing、大小、id/program/owner/account 唯一性、SHA256、客户端采集时间及两程序各自 finalized slot。若任一失败则整个新数据集标 SOURCE_INCOMPLETE，不混用旧证据。
- 只使用原 PR60 replay_owner_full_receipts 对两份原始回复离线 replay，禁止调用链上；单独记录收集时间、slot、owner 覆盖、结果非原子性，标明不含原生 SOL、其他 Token Program、美元估值与完整 PnL。
- 后续快照解释保留 NONZERO_AT_SLOT、ZERO_AT_SLOT、NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS、SOURCE_INCOMPLETE、SOURCE_STALE 和 UNSUPPORTED_PROGRAM；严格区分本地 BUY/SELL 与被动转入，不将非零账户误称主动买入/值得投资。
- 即使新采集顺利，新的 slot 余额也会随时间变旧，不得设计成「永远实时」。是否更换 Dashboard 历史数据、引入新页面或新主动采集须另立部署与私有数据授权，保留旧快照可核验，不默认新 cron/email/trade。

## 决策点、P1验收标准与边界

- CA P1 的真实完成标准是经授权的 Quick/Standard/Deep 新任务能产生真实 job、GET 最终状态/可靠恢复、报告来源/覆盖真实可信，既有缓存 GET 通过不算完成。
- 持仓 P1 的真实完成标准是新日期的完整 owner SPL/Token2022 各自 finalized slot 和全 Token Accounts 有原始来源、不可用时明示 UNKNOWN；它依然不是毫秒实时资产、可交易估值或跟单信号。
- 研发仅限新独立研究分支，不修改现有产品/正式 PR178，不改用户买入金额。**禁止在没有新授权前做 Mac 生产 GET、RPC、扫描、部署、重启、端口迁移、发通知、交易或定时任务。**
- 不再反复测试已经验收完成的 D2 私有导入、Chrome AF_UNIX/Seatbelt 沙箱或仅旧 CA 按钮存在性。

协调状态：CA_GET_RECOVERY_ALREADY_SHIPPED / CA_NEW_JOB_FLOW_UNVERIFIED / D2_HISTORICAL_DASHBOARD_LIVE / CURRENT_OWNER_SOURCE_NOT_YET_COLLECTED / NEED_BOUNDED_CA_DIAG_AUTH_AND_SEPARATE_TWO_RPC_AUTH / ISSUE165_OPEN。
