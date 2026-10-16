请对 Frank F02 真实新来源 Mac 验收证据进行独立复核，保持主线为真实钱包来源、准确仓位、可用页面，不扩展已登记非阻塞 P3。

仓库 https://github.com/lxxlx2/ChatGPT_mission_record ，代码 Draft PR #66 https://github.com/lxxlx2/ChatGPT_mission_record/pull/66 ，固定HEAD a20a9f972589e34d2eae435c2ee4696eb53bb1d7 ，base a59e423304cb2081aef359c0649245c7e1d05b48。前后核对远端SHA。该SHA已有Claude外部代码APPROVE，exact CI https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38688586451 SUCCESS，module85/1640、joint119/1692；不冒充本轮重新执行。

阅读进度PR #67 https://github.com/lxxlx2/ChatGPT_mission_record/pull/67 中最新TODO、正式开发规则及 FRANK_F02_REAL_SOURCE_MAC_ACCEPTANCE_20261015.md、evidence/f02-manual-refresh/real-mac-source-acceptance.json。验证用户已明确授权一次两RPC和新研究会话，来源UTC 2026-10-15T06:10:01.348696+00:00、SHA a5964a093a1d6bffe7b2334480825c90af478d3c38d7336fc71cec767b81a25e，Slot457132317–457132319，完整双程序非原子。区分冻结32目标9非零/23零与全钱包3276观察Mint；不能推断SELL、PnL或跟单。核查32行原文重放精确值/账户数对照、真实本机HTTP/浏览器筛选复制、新鲜至自然300秒过期后遮罩，以及过程关闭证明；对比前一轮Claude只有HTTP/Node、无真实浏览器的限制，本轮是开发方Mac业务证据，不是Claude执行证明或独立最终整体验收。

需要复现时使用只读detached checkout，在local-agent运行 python -B -m pytest -q -p no:cacheprovider tests/test_frank_f02_manual_refresh.py tests/test_frank_f02_r2_isolated_browser.py tests/test_frank_f02_r1_readonly_positions_api.py 及 node tests/frank_f02_r2_render.cjs；需要全量时依项目dev/monster依赖和真实Git refs运行 FRANK_EXPECT_REAL_GIT_REPLAY=1 python -B -m pytest -q -p no:cacheprovider tests。可以自建合成来源做真实HTTP/浏览器TTL检查，但不能将其冒充此真实capture；私有原文/SQLite/截图未公开，远端审核无法自行读取就标记未独立重放。已授权单次采集已经用完，不得自动再次RPC或重导入旧库。

明确输出 APPROVE / REQUEST_CHANGES，实测和证据审读分开，P0–P3分级，阻塞项给具体复现及业务影响。保持Draft/NO_MERGE/NO_DEPLOY/NO_TRADES/NO_GMAIL/NO_PRODUCTION_SQLITE_WRITE/NO_NEW_AUTOMATION。整体F02-R3、F01/C02统一交互和最终独立产品验收尚需按计划推进，不把局部通过宣称整套完成。不修改代码，不删除私有证据。
