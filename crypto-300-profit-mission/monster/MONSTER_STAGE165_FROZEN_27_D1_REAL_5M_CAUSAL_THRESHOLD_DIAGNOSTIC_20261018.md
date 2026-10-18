# Monster Stage165 — 原27新增首评为何未产生 SETUP 的真实5m指标取证（先冻结、后代码）

日期：2026-10-18；研究分支：`research/monster-v4-local-discovery-20261010`，Draft PR #30。

## 唯一真实研究问题

Stage164已从原2026年2月445完整来源中冻结27个 `FIFO8 LATE -> Fair8 EVALUATED` 新首评，且27/27最终 `NO_SETUP_WITHIN_WINDOW`，SETUP新增0/保留旧120个。本轮新取证只问：**当这27个真实候选在原Stage162的哪些时间实际更新5m有效评价游标时，原 `monster_v4_shadow.evaluate_closed_5m()` 的具体三项指标数值是什么，哪几项不足以形成SETUP？** 不扩大或优化阈值，不重新采集当前币价，也不冒充前瞻市场。

## 原输入与严格来源门禁

1. 固定完整Stage162 A/B归档 [Actions #39068290868](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39068290868) 的 `monster162_actual_445_fair8_ab.json` 原字节SHA256 `c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`、原全27000? 实际269队列与每次753真实D1选槽记录，不使用后来写回的简表代替原始时间与queue ID。Stage164严格锁定27个唯一queue ID及事件 `evidence/monster_stage164_original445_fair8_new27_nonconversion_actual_v1.json`，Git blob`40aeb187320ea3efc3b8b6bd8a0a8ae1d4d10098`。
2. 历史5分钟价只从已归档的2026年2月原28个source shard ZIP/proof（18个真正生产Artifact分发），复用原已通过 `monster_v4_shared_445_archive_replay_runner.collect` 和 `monster_v4_shared_445_one_db_from_shards.verified_shard_paths` 的原来源证明。每个符号10天出版社SHA源、连续12,960个1m价量行，照原 `shared.prepare_symbol` 得到5m烛形；禁止另拉现在Binance历史端点来补缺或掩盖源归档漂移。对所有28份ZIP先验SHA封存；仅选择27个源符号构建指标分析库，但不得把这种单币取证称为另一次全市场策略重放（原全市场D0与SELECT时刻来自冻结Stage162全269）。
3. 原评估时间只能来自Stage162 `selected_slot_trace` 中属于27个独立queue ID、且真实 `valid_5m_evaluation_marker_advanced=true` 的tick；须核对各27首个推进时刻等于Stage164源中 `alternative_first_evaluation_ms`，不得遍历全部未来K线找“最接近成功”的时刻。若存在后续游标推进，单独报告每个实际推进时刻，且不能在原15m deadline之后制造新机会。

## 预冻结指标与可证伪结论

调用**同一份未修改的原生产`monster_v4_shadow.evaluate_closed_5m(candles,tick_ms)`**，源烛形由原生产规则`verified_closed_5m_for_original_d1`校验（禁止手造转化数据）。原6根已闭合5m bars的三个且条件：

- `positive_steps_last3 >= 2`
- `recent_vs_earlier_15m_quote_ratio >= 1.5`（须注意原函数内部原始Decimal阈值判断，**显示四位小数不可倒替该真实阈值**）
- `closes[-1] >= closes[2]`

每个D1真正推进的事件报告实际 `observed_ms`、queue episode ID、symbol、三个指标/通过与否、是否 `setup_candidate`、bar_last_open_ms 与是否<=原deadline；然后聚合首评失败组合、后续真实推进的所有失败组合、每个候选至少一次满足全部条件次数，不得把未选中/未实际评价的过去或将来时钟补充成候选实际看见的信息。所有27最终事件本应没有新增SETUP；若官方真实档案或D1函数复算出实际评价的`setup_candidate=True`但原SETUP=0，则**显式源/调度漂移FAIL**，不偷偷改结果。

## 预定义退出与边界

本轮只给出“原27具体为什么未转SETUP”的原特征事实及是否D1阈值组合阻断；**不得据此回头改三项冻结阈值、提高15m期限、选择事后上涨赢家、声称任何币现在可以买或对2026年10月前瞻胜率有证明**。原445/758删失313，非历史PIT交易身份，无信号与同刻L2/实际手续费/退出，因此G4 UNKNOWN、G6 NO_GO。缺少可读的原始publisher Artifact、核心源身份或完整严格烛形时**标BLOCKED并保留失败证据**，不能根据最终`NO_SETUP_WITHIN_WINDOW`推断指标失败。

只允许同一PR #30 源锁定 GitHub Actions 显式push单次离线研究；禁止GitHub schedule/ChatGPT Automation/launchd、Mac部署、Frank、Gmail、API交易。产出真实可复现脚本、测试、机器结果、简洁结论，**新增代码的其他AI独立审核未完成之前不能声称审核通过**。继续 `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
