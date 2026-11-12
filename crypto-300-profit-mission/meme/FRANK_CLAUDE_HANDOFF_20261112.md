# Frank Claude 交接核对与进度同步（2026-11-12）

结论：Claude 的四个新提交已在远端，源码工作树干净，未发现这些源码丢失。当前开发候选为`aad880991565d148aa6cc2f74fa0de1f5e6c27c7`（parent`d81f7fcbfb2f782f8528cb267e222950d24dfae7`），[PR252](https://github.com/lxxlx2/ChatGPT_mission_record/pull/252) Draft/Open，stack在[PR220](https://github.com/lxxlx2/ChatGPT_mission_record/pull/220)的`d43878828c86eacee5be9df8a17d16fc63a74bb6`上。PR220仍是基础版本，不能把它的HEAD说成当前安装源码。本轮只核对/同步，没有新RPC、CA POST、来源采集、重启、部署、交易或新PR。

[机器回执](./evidence/frank-claude-handoff-20261112.json)保留固定SHA、任务原件指纹、测试命令、边界和未完成项；原始报告、完整任务标识、SQLite及私人路径仅保留Git外。最新核对main为`5507e58e650f25e074f45bf9b426c1220a1e4f4f`，相对之前规则和Frank相关路径无增量。

## 已证实的进度

- 四提交`47d431c0cd5d37b6c3daf8f5e0f896a82ed12f71`、`c19dfd72632b851f167b7705ba1581f65f750e89`、`d81f7fcbfb2f782f8528cb267e222950d24dfae7`、`aad880991565d148aa6cc2f74fa0de1f5e6c27c7`，相对d438共15文件、892增/56删，已推送`codex/frank-gpa-binary-full-mint`。
- GPA改为固定166-byte `base64 dataSlice`，不是二分搜索。官方公共fallback使既有CA四次取得全账户枚举；这解除该样本的“完全拿不到排名”阻断，不代表Alchemy限额已修复、所有Mint可用或所有身份已证明。
- 无Mint authority且前后供给相等时，使用`NO_MINT_AUTHORITY_MONOTONIC_SUPPLY_BRACKET`。最新GPA slot468099092，供给前468099081/后468099321；`snapshot_consistent=false`。不是原子同slot读取。
- 最新全局Owner Top10为58.9540%，账户33872、非零账户7987、非零Owner7978。排除已核验池指标14.2998%，LP/特殊前缀策略指标亦14.2998%；`normalization_complete=false`。on-curve/System普通地址规则不能证明地址不是CEX、做市商或托管实体，不能宣称全表特殊身份完成。
- 最新报告已有Pump bonding curve/creator字段和Token-2022 metadata链上状态。Pump complete flag不单独证明迁移、creator不证明控制人、metadata URI不证明帖文作者认可。CEX配置实际新增12个地址、96行JSON（总地址1→13），不是96个地址。
- 当前账户历史标签确有新增输出：8个`CONFIRMED_ACCOUNT_COMPLETE`、1个`NO_MARKET_BUY_IN_COMPLETE_ACCOUNT_HISTORY`、1个未确认、10个未扫描；只覆盖已选当前token账户，不覆盖关闭账户/整个Owner。另有下面已复现的软件缺陷，不能据标签结案。

## 真实任务原件核对

以下是11月11日既有任务，不是11月12日重新采集。wire/cache为各自计数，不能简单相加当作逻辑读取总数。

| 脱敏任务 | 观察时间（曼谷） | 主wire / cache | 耗时 | 全局Owner Top10 | 排LP策略值 |
|---|---|---:|---:|---:|---|
| NOV11_RUN_1 | 2026-11-11T16:02:53.851630+07:00 | 281 / 725 | 193.474 秒 | 58.9106% | UNRESOLVED |
| NOV11_RUN_2 | 2026-11-11T16:30:29.702499+07:00 | 183 / 825 | 141.881 秒 | 58.9106% | UNRESOLVED |
| NOV11_RUN_3 | 2026-11-11T16:50:02.834290+07:00 | 186 / 825 | 120.842 秒 | 58.9106% | 14.2998 |
| NOV11_RUN_4 | 2026-11-11T18:05:50.499643+07:00 | 463 / 926 | 275.411 秒 | 58.9540% | 14.2998 |

四份raw报告均与独立DONE marker哈希匹配、各有相同字节的timestamped原档；4/4 checkpoint metadata SHA、seq、逐条body SHA/previous链及head/count通过，读取前后SQLite字节不变。4/4精确job的本地GET与原JSON相等，latest指向最后一次。最新报告SHA256`468b8c78e140b5e28827034c2360ffa83f0c882803353f9ac05d436255b44bec`。这证明观察到的本地档案一致性，不是外部来源认证、完整业务重放或所有历史任务的运行Git SHA证明。

最新独立PublicNode结果是`UNAVAILABLE / RPC_JOB_TIME_BUDGET_EXHAUSTED`，主任务1200wire/1800秒并未耗尽。不能写独立对账已完成。同源二进制重读仅10账户，`OBSERVED_SAMPLE_ONLY`、`full_positive_mass_reconciled=false`。仍有15个分页窗口PAGE_LIMIT；关闭账户未枚举；新增历史frontier选择为0。最新交易证据206（BUY162/SELL44），总体仍INCOMPLETE_EVIDENCE。

## Claude 的实际中断点和未完成软件项

1. **首买标签错误升级已复现。** `cluster.py`的getTransaction异常未记录holder phase，完整性判定仅筛holder phase；较早交易超时后碰到空页仍可升级“未见市场买入”，若另有较晚BUY则升级账户完整首买。[固定AAD离线复现器](./evidence/frank-first-buy-completeness-probe-20261112.py)两案均确认，未修源码。最新真实任务tx_errors=0，不据该反例倒推其8个具体BUY一定错误。
2. **叙事origin未接入checkpoint适配器。** 直接PublicNarrativeClient有collect_origin，生产CheckpointClient只有collect/token_snapshot/pool_snapshot；hasattr守卫因此跳过新路径。最新报告没有narrative.origin，earliest_origin及official_recognition仍UNVERIFIED。不能把已写JSON抓取函数称为真实源头链已读通。
3. **同slot措辞与供给夹逼矛盾。** 页面和holder_balances cause仍称same-slot，实际slot不同，需修正展示/证据原因。
4. **安装Git身份不干净。** 当前服务目录名称含AAD，但复制来的.git仍指向旧d438 worktree。171个tracked运行源码/配置文件逐字节匹配AAD、服务app.js也匹配；1个新测试缺失、2个测试不同。不能只凭目录名或该目录git HEAD宣称完整干净AAD安装。后续应准备独立固定SHA安装目录，禁止reset/clean当前运行树。

## 页面与测试核对

11月12日新打开真实Chrome原8766，发射/创建者及第二提供方卡片可见；原任务GET和刷新恢复通过，截图留Git外、页面留开。没有改代码或缓存设置。只能确认新页面可渲染，不能倒推出旧tab根因一定是缓存；服务app.js实际Cache-Control为no-store。

在独立AAD工作树实际执行：四文件`test_meme_holder_binary.py test_meme_launch_origin.py test_meme_holder_ranks.py test_meme_wallet_cluster_pagination.py`，专用Python -B、pytest禁cache、审计钩子拒绝全部socket.*，106 passed/0.23秒、socket事件0；node --check app.js通过。首买复现器两案确认、origin适配器静态探针确认。未在最新AAD发现GitHub workflow/check runs；Claude对较早阶段2300全量测试的陈述不自动迁移到本HEAD。未把旧d438的385/220/双CI或旧2x978回放当作AAD验证。

## 来源和预算变化

用户在Claude原会话明确允许“卡点找免费方案、本地调试部署、免review”；这与更早私有RPC-only边界不同，交接记录保留变化。本轮同步不再调用任何新来源。

- 官方public mainnet fallback默认开启，独立PublicNode checker默认启用；新增metadata/IPFS/fxtwitter路径。它们是新增免费来源，不能隐去。
- GPA账户上限5000→200000，响应8→64MiB；标准自适应历史4→8页、funding5→8页（候选120→240、60→96/目标）。
- 主RPC仍1200wire/1800秒，独立checker另有4wire/60秒，不计主wire；主墙钟仍持续并在发布前检查。不能声称所有provider严格共1200次，也不能声称全局时限1860秒。
- HTTP叙事最多旧HTML3次+metadata3次+post-chain4次，单次body256KiB；origin当前未通过生产适配器触发，这个上限是可用代码路径，不是本轮已发生10次新读取。
- 四次持久化主wire合计1113；此前记录2180加上它，得到可确认下界3293（原一次572单列）。零散诊断和独立checker未完整并入，不能宣称阶段精确总数。

当前完整CA验收仍PARTIAL，INVEST_NO_GO / TRADE_NO_GO保持。下一步最小工作是先修首买错误升级、origin checkpoint接线和供给夹逼措辞，并纠正安装身份，再验收独立来源和其他代表样本；不是继续增加无关工程。原10月故障归因按用户取消，不重新列为卡点。
