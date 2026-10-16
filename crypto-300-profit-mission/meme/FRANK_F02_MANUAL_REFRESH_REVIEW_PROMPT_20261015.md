请独立复审 Frank F02 手动新来源会话，最终产品目标是来源可核验、仓位准确、界面可用，并按冻结计划推进整体功能；不要重开已批准 TTL P2，也不要扩大非阻塞 P3。

仓库：https://github.com/lxxlx2/ChatGPT_mission_record
Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/66
固定审核 HEAD：a20a9f972589e34d2eae435c2ee4696eb53bb1d7
固定比较 base：a59e423304cb2081aef359c0649245c7e1d05b48（已批准 #65）
只读 detached checkout；前后核对 PR remote head 与这两个 SHA，若漂移立即报告，不审旧版后声称审核当前版。

读取 design/frank-ca-multiperson-completion-plan-20261013 上最新 TODO、FRANK_CA_PR_REVIEW_INTEGRATION_GATE_20261014.md、FRANK_CA_DEVELOPMENT_AND_INDEPENDENT_REVIEW_RULES_20261015.md；代码分支的 FRANK_F02_MANUAL_SOURCE_REFRESH_20261015.md。此前 #64 的页面载入后跨 TTL 旧余额 P2 已由 #65 精确 SHA 修复、真实浏览器外审批准；本 PR 不修改 TTL JS，只检查关联行为保持。前一轮新增流程独立 AI 只读审查 a20a9f9 已给 APPROVE，89 专项、另行合成 socket probe PASS；不得将其当真实 RPC/Mac live 产品验收，也请独立复核而非照抄结论。报告归档于进度分支 codex/frank-f02-refresh-progress-20261015 的 meme/evidence/f02-manual-refresh/independent-review.md。

限定 diff 为 base..HEAD，关注新增 CLI、页面说明、工作流与测试。实测默认 PLAN_ONLY 不访问 RPC/创建目录，--serve 无 --execute 被拒，端口占用在 RPC/SQLite 前失败。明确执行恰好最多两次 finalized getTokenAccountsByOwner，第二程序最低 Slot 继承，完整原文双程序 replay 和冻结 32 Mint 对账在新私有 SQLite 写入之前完成。新数据库在 UUID 会话内，不覆盖旧库，不允许原文/数据库公开 HTTP。partial/超时/错误不能返回旧正余额或误当零，不能启动成功仓位服务。新来源保留真实采集时间，超过 300 秒遮罩；重新打开/导入不延长来源 TTL。测试精确数量、零与无账户/未知差异、SHA绑定和原文篡改拒绝。

独立运行命令（在 crypto-300-profit-mission/local-agent，Python 使用具备项目 dev 依赖的环境）：
python -B -m pytest -q -p no:cacheprovider tests/test_frank_f02_manual_refresh.py tests/test_frank_f02_r2_isolated_browser.py tests/test_frank_f02_r1_readonly_positions_api.py tests/test_frank_a05_r2_frozen32_offline.py tests/test_frank_a05_complete_rpc_receipts.py tests/test_frank_a05_f02_latest_inventory.py
node tests/frank_f02_r2_render.cjs
FRANK_EXPECT_REAL_GIT_REPLAY=1 python -B -m pytest -q -p no:cacheprovider tests
按真实 Git 回放要求获取历史 refs；依赖/refs 缺失保留原失败，不能改测试掩盖。

在独立临时树，以 main 8dec28571e41d3fc2e78cacffde682167145bc76 + 本 HEAD + C02 8898134a8a302e1187138f7fb3da87a554567e6d + F01 516e3335a134c608f477019b79027982f43af32a 做联合检查，尤其通用 CA 身份和 F01 机会接口；不修改已批准模块。初始 exact-head CI https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38688586451 SUCCESS：module 85/1640，combined 119/1692，Node PASS。开发方本地对应均 PASS，14 既有 warnings；CI临时联合 SHA ae6a31f9e3dac8bff1dd8ea6af15cbd062c48e1b，本地联合 SHA b772f459ff2b78cffc97b1ac16a53b8f46717480。合成来源 browser 实测仅证明可渲染/筛选/复制，不证明当天余额。

用你自建合成来源运行真实 localhost HTTP/浏览器，检查来源说明、新会话数量、搜索仅筛选32目标、复制精确CA、重新读取不请求RPC、跨TTL保持遮罩、拒绝 Host/其他wallet/私有原文路径。真实 RPC 或新 Sidecar 在用户私人目录的实际采集，必须另外明确授权；没有授权用临时合成 fixture 做测试，不能报告真实新持仓 PASS。

明确输出 APPROVE 或 REQUEST_CHANGES，按 P0/P1/P2/P3 分级，缺陷需实际复现、文件行号、业务影响与最小修复要求；区分静态推断、合成来源、真实HTTP、浏览器和用户Mac来源。说明未完成：全钱包持仓列表（本页只有32目标）、任意CA尽调集成、F02-R3、最终整体独立业务验收/发布。不要为P3要求无限延长阶段。

禁止改源码、自动真实RPC、重复导入旧Sidecar、生产SQLite写入、Gmail、交易、LaunchAgent、新自动化、合并或部署。保持 Draft/NO_MERGE/NO_DEPLOY。本复审不是生产授权。
