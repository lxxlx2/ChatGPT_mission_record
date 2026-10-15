# Monster Stage152 修复版固定 SHA 的完整其他AI独立复审提示词

请直接全文复制给其他独立Claude/Codex对话审核员。该提示词仅是review请求，不是APPROVE。

你是独立其他 AI 审核员。任务是判断 Monster Stage151 冻结历史策略经济研究的 Stage152 P1整改能否关闭前次 `REQUEST_CHANGES`，并验证本轮研究结果与仓库执行边界。**请从原始 Git 独立检出并尽量重算，严禁根据此提示词直接宣布APPROVE。**

仓库：[lxxlx2/ChatGPT_mission_record](https://github.com/lxxlx2/ChatGPT_mission_record)
Draft PR：[ #30 ](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)
唯一分支：`research/monster-v4-local-discovery-20261010`
**固定待审代码+测试+workflow SHA=`f12d6635c6f8a5e2ba8fbb2feeca29688583245b`**
前次独立Claude审核SHA `b309bf75a46a48cde1aa6b14c17d3e6b7c1b53c2`，结论 `REQUEST_CHANGES`、0 P0、3 P1；
Stage150独立Codex代码审核旧固定SHA `e569dddccddf12736051534f2bf0b56b0329ad62`，它不能为新Stage152代审。
Reviewer请填写实际模型/版本（不可核实写 `UNVERIFIED`）、平台/时间、代码git SHA。

**先核实仓库规范、冻结方案及真实输入**：
- `crypto-300-profit-mission/monster/AGENTS.md`
- `.../MONSTER_MODULE_DEVELOPMENT_RULES.md`
- `.../MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md`
- `.../MONSTER_STAGE151_FROZEN_POST_D1_PULLBACK_RECLAIM_ECONOMIC_RESEARCH_20261015.md`
- `.../MONSTER_STAGE152_FROZEN_STAGE151_CODEX_CLAUDE_P1_REMEDIATION_20261015.md`，冻结提交`58c5cd0a98869143d35ee8238a1c92f69d966e2c`，代码修改之前。
- `.../MONSTER_STAGE152_CLAUDE_P1_FIX_REAL305_SOURCE_PIN_CI_RESULTS_20261015.md`（本轮结果报告，**请独立查证而非采信自述**）。

**具体待审代码**：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage151_post_d1_pullback_reclaim.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage151_aggregate_post_d1_research.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage151_post_d1_pullback_reclaim.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage152_external_review_regressions.py`
- `.github/workflows/monster-stage151-original305-frozen-post-d1-economics.yml`

**原始历史 source lock**：Stage101→Stage88→Stage85冻结305原D1和519原D0；Stage88原出版者SHA认证全305原始证据Git blob `86e96b726f677a15f5a7c8d740e3caca5c83e3fc`；Stage85 as-of历史blob `622299fec16400e189cb8fa668ecbc8bc31ec630`；Stage83原519分母blob `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`。六个已曝光七日历史窗口：2025-01-30、2025-06-02、2025-08-01、2025-10-02、2026-06-21、2026-07-28。**不能把这305次历史回放叫独立OOS**。旧Stage116最初2026-10-14 06:00Z失败源仍 `SOURCE_FAILED_NO_BACKFILL`；Stage118/127 `REJECTED`、Stage132首次追涨收益负。

**一轮真实 CI 和文件身份**：
- [GitHub Actions #38731042245](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38731042245) 原代码SHA `f12d663...`，27/27 Jobs SUCCESS，其中Ubuntu24.04 job `116408600379`和macOS job `116408599900` 各18/18 unittests PASS，24个独立日期/分片真实publisher1m历史试验及最终聚合Git归档 job `116409060326` 成功。前序CI真实失败运行要保留（如 #38730751356/#38730840181），修复的是合成断言的错误schema/标签。
- 归档[新Stage152机器摘要](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/evidence/monster_stage152_original305_integrity_and_economics_summary.json) Git blob `f0dedc011d8518146f8c023ac61ebc5f7ff8b9a0` 和新[完整305行SHA/行情与经济证据](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/evidence/monster_stage152_original305_integrity_and_economics_rows.jsonl)；旧Stage151证据仍保留。
- 机器摘要 `trigger_commit_sha=f12d6635c6f8a5e2ba8fbb2feeca29688583245b`，核心源码SHA256 `cf1624048af1349266ceeae0171536c7c9dabc24c8300092caeb4c4c6ac11c10`，汇总源码SHA256 `80645d5b046393717e8017e91692ee9497bfc4cc2e199d28a71902c673cf0019`。PR HEAD在这之后仅可能多追加文档/证据，**凡非上述固定代码SHA，不要借旧审核结果代审**。

**请独立验证三项 P1 是否真正关闭**：

P1-1：完整305原D1/519原D0分母、原事件不变；全部样本与184确认样本、113无回撤、8回撤未恢复要都报告；同184直接D1入场毛24h中位−5.913%、新确认184中位−2.446%、mean+3.728%，同样本配对回报差中位+3.129个百分点**但不同退出时钟**，不宣称同钟alpha；正均值的最大5赢家MEMEFI/MYX/SYN/BLESS/AGLD合计约占184事件收益率求和的92.18%，去前5均值+0.300%。≥20%/≥100%正尾、≤−20%负尾、各六日期、DIRECT/REIGNITION、未确认和CENSORED要从完整行重新计算。原27个D1早5分钟2x历史评价只留下确认16个，不能隐藏漏报。至少校验一个故意删损/重复的305分母反例。

P1-2：原3%下降/1%恢复/120根已经冻结，不准调参数。每条确认的已闭合bar及预期模拟入场、退出1m市场quote/trade count应可追溯且不等于盘口深度；研究用市场成交额双边分钟同时 ≥0/10k/100k USDT样本数分别184/124/39，100k子样本24h中位+7.668% **不证明可成交**。额外0/1/3分钟延迟，24h毛中位约−2.446%/−1.871%/−2.010%，退出也随进场顺延，所以不是零延迟真实成交敏感性。直接查最大赢家的每分钟entry和exit报价活动、分钟时钟、交易数；不得假设用户下单USD30/100/300。

P1-3：每个shard的 `GITHUB_SHA` + 源码SHA256与汇总固定SHA一致；reconcile必须checkout `github.sha` 且Git rebase/push之前比较5个代码/测试/workflow blob没变；新报告冻结参数来自真实core常量。检查其workflow只有push/manual dispatch，没有任何`schedule`、Mac LaunchAgent、交易、邮件；每次成功CI仅归档本次研究输出到原PR分支，不是授权新后台采集。

**P2 请优先检验直接影响因果和诊断的项目**：日归档1439行与SHA篡改错误区分；分钟缺档、扫描缺档、缺退出bar需要准确fail-loud、不可冒充censored；决策只逐根消费已收盘且真实可观察的bar，确认后的未来坏bar不得逆向改变当时决策；该历史分片聚合缺少任何一个原始row必须拒绝；入口/出口价格OHLC与分钟UTC时刻严格一致。确认bar 0-trade的事实仅可单列，不能用成交数量造价格可执行概率。CI代码安全、交付边界和Frank隔离也必须核查。

**务必区分证据等级**：GitHub CI官方publisher重新读取305历史源是仓库自身run，尚不等于你独立联网从原始ZIP重算；若你无外网，说明是否只能交叉核对已归档的Stage83/85/88并把独立原始重算写`UNVERIFIED`。历史价格代理≠真实买卖盘口L2、费用、资金费率、滑点与成交净收益；不能升级业务模型为盈利、G1/G2/G3/G4或Mac Shadow/G6。

以固定结构返回：**`APPROVE | REQUEST_CHANGES | BLOCKED`**、准确审核SHA、底层模型版本、执行命令/测试及真实结果、P0/P1/P2问题的文件行号/复现/修复建议、上一Claude P1-1/1-2/1-3各是否闭合；说明是否影响D0 WATCH / D1或BUY / 发信、远端CI/源/样本外证明等级以及发布 `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE` 是否仍生效。当前这些门禁必须保持：G0 PARTIAL、G1 NOT_SCORABLE、G2/G3 NOT_PASSED、G4 UNKNOWN、G5_FULL_RELEASE NOT_PASSED、G6 NO_GO。
