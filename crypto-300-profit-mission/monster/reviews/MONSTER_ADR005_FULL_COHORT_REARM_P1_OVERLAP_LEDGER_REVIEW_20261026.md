# Monster ADR-005：全T0事后代理回放 P1 — D0失效/重新WATCH与研究RBTC PENDING episode冲突修复与独立复审

**实现状态：`P1_CODE_FIXED_REAL_110_CI_PASS / INDEPENDENT_RE_REVIEW_PENDING / REAL_FORWARD_G6_NO_GO`。** 固定**待复审源码/测试/CI SHA：`519f5ddb10a904b9a9923557261d2e839693b9b9`**。用户提供的Codex `REQUEST_CHANGES` 固定旧SHA为 `e275b14f0421aa990b839d0a006c81a95a4e4094`。**后续文档HEAD不是复审代码SHA。**

## 1. 用户带回的独立审核反例及根因

Codex主代理（底层模型UNVERIFIED）在Mac macOS27.0.1 arm64、Python3.14.7的独立detached worktree针对旧固定SHA实测**106/106 PASS**，额外自建全T0两币AAAUSDT/BTCUSDT（quoteVolume均200,000）的四个合法原D0 tick：

| UTC 2026-11-02 | AAAUSDT | 原D0实际状态 |
|---|---:|---|
| 00:00 | 100 | baseline |
| 00:03 | 110 | WATCH_EARLY #1 |
| 00:06 | 90 | INVALIDATED #1 |
| 00:09 | 96 | WATCH_EARLY #2（D0可合法重新触发） |

原研究RBTC固定`admit_original_watch()`在同`venue,symbol`仅允许**一条PENDING**，第一条的固定deadline为00:18；旧桥在00:09无条件调用它，出现`ValueError: SECOND_ORIGINAL_WATCH_WHILE_RESEARCH_PENDING`，中止全七日回放，丢掉最终结果。**真正问题是两个原状态机的衔接，而非原D0或原研究episode独立代码错误。** 旧原始106 PASS及Artifact检查仍成立，但原全T0新增桥的G5结论**REQUEST_CHANGES**，当时有实际P1。用户还独立检查了11币同最后一tick触发10非BTC+1BTC、FIFO8前8服务后2 PENDING的正常路径；它未发现其他P0/P1/P2。

原始独立复现脚本 `/private/tmp/monster-e275b14f-probe.py` 和日志 `/private/tmp/monster-e275b14f-logs/reversal-probe.log`只在用户Mac，不能从当前Git仓库/新GitHub CI自动引用其字节。此记录以用户真实提供的审核结果为依据，不伪称在本会话亲自执行了其Mac脚本。

## 2. 修复：桥接**不改变**原研究episode的冻结生命周期

唯一修改的研究程序是本次新`local-agent/scripts/monster_v4_adr005_forward_spot_full_market_replay.py`，新Git Blob **`a0bd9205fb1ebee42451d31a4bece3bda9282699`**，Schema`MONSTER_ADR005_SPOT_FROZEN_COHORT_OFFLINE_SOURCE_PROXY_D0_RBTC_D1_SWEEP_V2`。对应新测试Blob **`db9e0f1f1f2814954d57bbae5089c97af227765d`**。

新增**独立桥接账本**`bridge_watch_disposition`（建在独立研究SQLite、不是原D0数据库），以原D0真实WATCH`original_watch_event_id`为主键记录每条非BTC WATCH的原venue/symbol/observed_ms及唯一处置：

- `ADMITTED_EPISODE`：研究队列该币无PENDING，严格调用**未修改**的`research.admit_original_watch()`，原SHA/原15分钟deadline/固定FIFO8保持原样。
- `OVERLAP_PENDING_UNSCORED`：已有同币PENDING，此事件不满足原研究`one_research_pending_per_spot_symbol`约束；**不调用会报错的admit，不吞掉原WATCH、不修改旧episode、不强终止、不改原D0 INVALIDATED、不伪造NO_SETUP或SETUP**；桥接账本持久记录其**原事件ID、准确触发时刻、阻断它的旧WATCH/episode ID**。该研究候选在本次回放中**明确标为重叠不可评分**，需要未来另有经批准的新生命周期策略才能扩大研究接纳率；严禁静默忽略或自作主张回填旧研究缺失的5m评审机会。
- 桥接记录的`blocking_episode_status_at_window_end`是左连接从未改的原研究episode表取出的最终状态。保存原D0全部WATCH及INVALIDATED的原`event_id`和时间，用于审计被阻断事件的因果链。输出新`proxy_research_D1_admitted_episode_count`、`proxy_research_D1_overlap_pending_unscored_watch_count`、`proxy_nonbtc_original_d0_watch_count`和逐条bridge表。**原完整分母恒等式变成**`nonbtc_original_WATCH = admitted_research_episode + overlap_pending_unscored`，并强制比对每条bridge账本、原D0全WATCH和研究状态数，任何无解释的遗漏或额外对象仍拒绝。
- BTC保留在原D0诊断并继续不作为RBTC研究目标。每一tick仍运行未修改的原D0及原研究poll`MAX_SERVICE=8`，原研究`PENDING/NO_SETUP/LATE_UNSCORED/SOURCE_UNSCORED/RESEARCH_SETUP`的deadline/闭合5m/错过机会语义**一行未改**；未来新WATCH只在已有episode真正成为原研究终态之后，才可建立下一条独立episode。
- 本轮作的是**源代理回放的保守研究分类**，并不是暗中确定“重叠WATCH一定不会达到2×”。所有重叠行是`UNSCORED`、不可成为G1/G2/G3有效样本或负例；如未来想延迟服务、并行episode、强制以D0失效终止研究episode，那将改变冻结研究策略，需要**单独明确审批**，不是本P1修复的默认副作用。

## 3. 新增4个真实完整3360-tick集成回归

原全市场scanner 8项增加到**12项**，除原全T0完整人口、BTC缺失、D1准入、旧10月T0拒绝、数据库隔离等保留外：

1. **独立Codex固定P1原反例**：AAA100→110→90→96，实际完整扫描3360次、源代理6720条，原D0 WATCH两条`event_id`不等，INVALIDATED一条，桥接研究第一条ADMITTED、第二条OVERLAP_PENDING_UNSCORED且明确关联首条ID，原episode仍保留最终自然状态，整窗完成而不是异常退出；`G1 NOT_SCORABLE/G2 UNKNOWN/G6 NO_GO`不升级。
2. 第二条D0 WATCH延后至原研究episode固定deadline结束之后，仍可正常产生**第二条独立研究episode**（旧状态机天然允许），无重叠删失。
3. 同期另一个BBBUSDT触发WATCH，AAA重叠不能阻止BBBUSDT被独立接纳，也不能阻断完整3300+ tick扫描；3币×3360行全具备。
4. 同币连续两次`INVALIDATED→WATCH`重触发，三条不同原WATCH ID全部保留；旧首条研究episode不被强制终止，后两条都存有指向原阻断episode的明确重叠未评分关联，无凭空伪造SETUP/NO_SETUP。

测试明确使用合成价格与原未修改`observe_snapshot`和`research.poll_episodes`，**并非真实11月交易所行情、OOS提前2×验证或实时订单数据**。

## 4. 实际 GitHub CI 与三窗真实无源 Artifact

新一份只对自身workflow路径push触发的 GitHub Actions：
`.github/workflows/monster-adr005-p1-rearm-overlap-ledger-once.yml`，无`schedule`、无新RPC/实盘网络采集、无Mac部署。

[**真实最终 Actions #40273517695**](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40273517695) **SUCCESS**，固定SHA **`519f5ddb10a904b9a9923557261d2e839693b9b9`**，GitHub Ubuntu Python3.11实际原始日志**14 T0 + 10 daily + 20 score + 8 tape + 18 D1 pure + 28 queue + 12 full-market = 110 PASS**。新增4个具名测试在原始Actions日志均为`ok`；未跳过未发生错误。

GitHub Artifact **ID `12628199573`**，名`monster-adr005-p1-rearm-3window-no-source`。本会话**实际下载原ZIP并用Python验证CRC、外包SHA和全部3个JSON**。 ZIP SHA256：
`6d025e7c9087a1681a30a3b63fa321b4aab6d6a285096e6ead7df1f46eb0c182`。三份`2026-11-02/11-16/12-01.json`均为`WAITING_FOR_PRESTART_SOURCE_WINDOW`，原真实T0人口与BTC来源`null`、`G1 NOT_SCORABLE/G6 NO_GO`。**没有虚构真正未来全币WATCH/episode Artifact**；完整3360tick反例通过证据在GitHub原始测试日志中，文件未被冒充市场行情。

原冻结`research`队列Blob `d7afa1053f82fb5c6b13b91ef41d0836e4ca8094`、原`shadow` Blob `bc958b3d90a8a52afa51515cb53f7e5fafaffaaa`、11月分钟桥Blob `bd540a8656805f6d036dd84776d950fe1399758c` 本轮与被拒版逐Blob核对**完全未变**。其余已有独立批准T0/daily、BTC source score、D1 V2和D2微秒边界也继续保留。

## 5. 独立Codex复审范围（必须固定新SHA）

在用户Mac独立detached只读checkout审查**`519f5ddb10a904b9a9923557261d2e839693b9b9`**（比较拒绝版`e275b14f0421aa990b839d0a006c81a95a4e4094`）。只看新增scanner桥接处置、4测试及单次CI，不要用此文档HEAD代替代码；实际运行7组共110项，独立复现**原00:00→00:03→00:06→00:09**。特别检查两条WATCH的原ID、研究首条episode真实deadline/PENDING→自然终态、研究第二条**UNSCORED而非漏计或负例**、桥接数据库明确原父WATCH关联、全3360个tick不崩、其他币照常服务、BTC排除、FIFO8与窗口右边缘PENDING保持原冻结语义。验证其他源码Blob不变，实际读取Actions#40273517695与Artifact12628199573。

**核心审查决策**：在“不单独授权改变原研究episode终止/并行策略”的前提下，重叠WATCH保守分类`OVERLAP_PENDING_UNSCORED`并记录不可评分原由是否满足本次P1**全窗完整回放不崩溃且原事件不丢失**的工程要求？如果审核认为需要实现新策略，应提出**具体可重复的P0/P1/P2和所需独立策略授权**，不得擅自强制NO_SETUP、提前杀旧episode或悄悄补做遗漏的机会。新代码本次只获内部CI成功，**独立复审结论仍PENDING**，不得把旧106项或新110项测试通过当做已独立APPROVE。

## 6. 保留门禁和权限

G0 **PARTIAL**（11月真实T0/历史收包PIT未证明）；G1 **NOT_SCORABLE**；G2 **UNKNOWN**（重叠研究已明确UNSCORED）；G3 **十月EXPOSED_NOT_PASSED，十一月NOT_SCORABLE**；G4 **UNKNOWN**；G5 **新P1修复待独立复审**；G6 **NO_GO**。

**NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES / NO_NEW_RPC**，Frank未操作。