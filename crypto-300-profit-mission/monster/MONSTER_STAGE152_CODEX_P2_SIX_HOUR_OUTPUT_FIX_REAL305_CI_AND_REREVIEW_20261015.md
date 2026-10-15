# Monster Stage152：Codex 唯一 P2 的6h/24h敏感性覆盖修复、真实CI和新固定SHA独立复核

2026-10-15 Asia/Bangkok；原 Mission Monster [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。**独立审核状态：上一Code SHA的Codex = REQUEST_CHANGES；本次新SHA其他AI独立复核尚未返回**。禁止把完成GitHub CI当作另一个AI APPPROVE或业务模型收益通过。

## 上轮固定外审与原始数据身份

用户提交Codex对唯一SHA `f12d6635c6f8a5e2ba8fbb2feeca29688583245b` 复审结论：前三个P1（完整收益报告/代理成交活跃度和时延/CI来源SHA）均在历史研究范围内关闭；新唯一 P2 是 `monster_v4_stage151_aggregate_post_d1_research.py` 的 `groups()` 循环计算h=360和1440时，将 `market_1m_turnover_sensitivity_NOT_execution` 与 `entry_delay_price_only_sensitivity_NOT_execution` 两个顶层键用后一轮1440覆盖前360。Codex此次不止复算归档，还**独立取得官方 data.binance.vision 1,220日ZIP及每个CHECKSUM，1220/1220 ZIP SHA匹配，原305历史行与自写重放逻辑0差异**；验证分类184确认、113无回撤、8回撤后未确认，并指出这个P2只影响两套敏感性聚合的6h展示，不影响逐事件行、正式D0/D1、已审24h统计和原核心入场规则。此 `SOURCE_VERIFIED` 代表外部Codex已完成原始历史行情核实，**不**代表完整实时下单交易历史或净利润。

本轮先提交 [单一P2冻结修复协议](MONSTER_STAGE152_P2_HORIZON_SENSITIVITY_OUTPUT_FIX_PROTOCOL_20261015.md)，冻结commit `2af4b2fa6e8c11b3eba54a95d7ebdea47b832db8`，再分别提交最小源码改动和两项区分6h/24h的合成测试。

**新的代码固定审核 SHA：`71a041405352c9e2210d93dff9c2685149809e52`**。仅修改下面两个脚本：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage151_aggregate_post_d1_research.py`：两项敏感性顶层键改为 `{"360":..., "1440":...}`，每个原有 `tiers` / `delays` 只写入对应h，其他指标及参数不改。
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage152_external_review_regressions.py`：更新既有assert到 `["1440"]`，新增不同6h/24h成交量和不同延迟收益（h=360 quote=1 USDT，h=1440 quote=20,000 USDT；6h额外延迟1m=-50%，24h=+9%）的真实区分测试，另加6h为不支持价格代理、24h仍可用的状态隔离测试。

原Stage151核心 `3%/1%/120m/6h/24h`、原D0/D1、Stage90/120/137/138/150、工作流、原历史已曝光日期、旧Stage152研究阈值皆未变；没有新交易、用户下单金额或实际盘口假设。

## 真实GitHub Actions结果

[固定SHA对应的 GitHub Actions #38734029751](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38734029751) 经实际核对 `completed / success`，触发SHA精确为 `71a041405352c9e2210d93dff9c2685149809e52`：

- Ubuntu24.04 `20/20` 单测 PASS、macOS `20/20` 单测 PASS；原18项 + 区分持有期的2项。
- 6个已曝光原历史日期×4官方发行者SHA锁定的分钟归档shard，`24/24` 成功。
- `reconcile_real305_and_archive` 一项 SUCCESS，实际日志 `STAGE152_ACTUAL_GIT_EVIDENCE_PUSH_CONFIRMED`；全部 `27/27` jobs SUCCESS。
- [新的Stage152全305机器摘要](evidence/monster_stage152_original305_integrity_and_economics_summary.json) Git blob `518e7aa0d8db83fd1b818513ae7e72b165252806`，`trigger_commit_sha=71a041405352c9e2210d93dff9c2685149809e52`，聚合源码SHA256 `eb9c51504e0d380716a06fe638fdfa80b94a27bd282a54470cf9c16da642aacf`。原所有历史逐币行文件保持原blob，无需重写；前轮原始机器摘要Git blob `f0dedc011d8518146f8c023ac61ebc5f7ff8b9a0`仍可由旧commit复核。

**修复前后做了9个分组交叉验证**：overall + 六个日期 + DIRECT/REIGNITION 两条D1路径；逐组从两份真实Git摘要去掉两项改动的敏感性字段后，其他全部字段逐项一致；新 `["1440"]` 两项均与原被覆盖的顶层24h结果完全一致。历史305全人口分类184/113/8不变，已曝光旧策略仍不可当 OOS。

## 本次恢复的6h/24h聚合真值

| 持有期 | 双边分钟市场quote门槛（非订单额） | 样本量 | 24h或6h毛收益中位数 |
|---|---:|---:|---:|
| 6h | 0 USDT | 184 | -1.765975% |
| 6h | 10,000 USDT | 133 | +0.939199% |
| 6h | 100,000 USDT | 54 | +2.074312% |
| 24h | 0 USDT | 184 | -2.446284% |
| 24h | 10,000 USDT | 124 | +1.897110% |
| 24h | 100,000 USDT | 39 | +7.668440% |

额外0→1m、0→3m延迟后重新对齐持有期限，6h毛收益中位为 `-1.684256%`、`-1.720261%`；24h毛收益中位为 `-1.870766%`、`-2.010169%`。6h两套数据在旧摘要被覆盖，但原始305逐事件每个6h值一直存在，没有修改历史价格或反向优化阈值。

仍然 `STAGE152_P2_IMPLEMENTED_AND_27_CI_JOBS_SUCCESS`、`STAGE152_NEW_SHA_EXTERNAL_REVIEW=PENDING`。市场分钟总quote成交额不是当时已知的可执行L2价量，特别是**退出一分钟成交额是事后信息，不能作为入场因果条件**；亏损中位数、右尾赢家集中、G2早报漏失、市场状态严重依赖仍存在，真正G4净盈利路径UNKNOWN。新结果**不**允许提升正式D1、不许假设BUY、不能同日改为Shadow或自动交易。

**维持 `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，`G0=PARTIAL / G1=NOT_SCORABLE / G2_G3=NOT_PASSED / G4=UNKNOWN / G5_FULL_RELEASE=NOT_PASSED / G6=NO_GO`，Frank原状，Stage99保持停止，无调度或定时采集。**

## 请Codex/Claude独立复审（整段可复制）

仓库：https://github.com/lxxlx2/ChatGPT_mission_record ，原Draft PR #30；唯一固定新**源码/测试SHA `71a041405352c9e2210d93dff9c2685149809e52`**，旧请求修改固定SHA `f12d6635c6f8a5e2ba8fbb2feeca29688583245b`。请使用 detached worktree 只读review，不能用不断变化的PR HEAD偷偷替换pin。

请独立检查两次提交之间的源码差异，确认只有 `monster_v4_stage151_aggregate_post_d1_research.py` 的 `groups()` 敏感性输出拆为 `["360"]`、`["1440"]` 两组和 `test_monster_v4_stage152_external_review_regressions.py` 的相应测试更新。运行真实unit tests，特别确认合成反例：6h与24h退出的quote分别为1/20000 USDT时，门槛10000分组的6h n=0、24h n=1；额外延迟1m时6h毛收益-50%、24h +9%；6h退出无成交、24h退出有成交时不丢失另一个持有期的有效结果。

查看 [CI #38734029751](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38734029751) 真实 `27/27 PASS`（Ubuntu/macOS单测各20项、24个官方历史1m分片、全305归档），归档摘要 Git blob `518e7aa0d8db83fd1b818513ae7e72b165252806`。源SHA绑定 `71a041405352c9e2210d93dff9c2685149809e52`；核对完整305分母184/113/8、6h阈值0/10k/100k分别184/133/54、24h分别184/124/39、延迟1/3分钟两期中位；并独立检查旧摘要blob `f0dedc011d8518146f8c023ac61ebc5f7ff8b9a0` 的原24h两组与新 `["1440"]` 精确一致。不可拿已有Codex1,220份官方原始日ZIP验证结果当作自己亲自重下载；如无法独立重下请直接说明来源级别，既有外审官方源VERIFIED记录保持。

请报告固定SHA、审核身份/准确模型（无法验证写UNVERIFIED）、实际可复现测试、P2是否关闭、若发现P0/P1/P2给出最小文件行号/复现/建议、`APPROVE / REQUEST_CHANGES / BLOCKED` 的本次 **代码审核结论**。即使APPROVE，也不得宣称G4真实净利润、模型G1/G2过关、部署合并/邮件交易获批。NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE仍保持。
