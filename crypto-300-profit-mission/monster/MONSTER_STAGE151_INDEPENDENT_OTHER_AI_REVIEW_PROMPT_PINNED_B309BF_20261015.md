# Monster Stage151 固定 SHA 独立其他 AI 审核提示词（可全文复制到 Claude / Codex）

你是独立 AI 审核员。请**独立 clone / checkout** 到指定固定 SHA，实际复现而非只信提交者声明。不要对我的代码先修改后自称审核通过。

目标仓库：https://github.com/lxxlx2/ChatGPT_mission_record
现有 Draft PR #30：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
分支：`research/monster-v4-local-discovery-20261010`
本轮固定代码/测试/CI SHA：`b309bf75a46a48cde1aa6b14c17d3e6b7c1b53c2`
上一阶段独立代码审核 APPROVE SHA：`e569dddccddf12736051534f2bf0b56b0329ad62`（仅Stage150，不自动覆盖Stage151）。
底层模型版本如果无法可靠取得，请写 `UNVERIFIED`。

## 原始研究目标与冻结顺序

Monster目标是：尽早全市场WATCH、从可获得数据因果升级/失效、提供有证据可跟踪并有真实净收益的机会，而非造大量报告。已验证 Stage110 连续确认106案例24h毛价中位-3.65%、G2 16/28、峰值16，Stage115原D0 +2.75%池化中位由2025-01-30一窗驱动，其余五窗中位负；Stage117/118/127失败。Stage150历史525原始过滤器完整不代表G4实际成交。

本轮Stage151在重新处理原305官方归档之前预先提交冻结单候选协议：
`crypto-300-profit-mission/monster/MONSTER_STAGE151_FROZEN_POST_D1_PULLBACK_RECLAIM_ECONOMIC_RESEARCH_20261015.md`，先冻结commit `8a7c2bf22ba563b20058e626453f1db1d7bb7be3`。

本轮新文件：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage151_post_d1_pullback_reclaim.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage151_post_d1_pullback_reclaim.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage151_aggregate_post_d1_research.py`
- `.github/workflows/monster-stage151-original305-frozen-post-d1-economics.yml`

依赖原始冻结且不允许改变：
- `monster_v4_stage101_exit_minute_backtest.py`
- `monster_v4_stage88_d1_24h72h_official_paths.py`
- `monster_v4_stage85_official_d1_asof_features.py`（如现仓库精确文件名不同，用原Stage101 frozen()依赖和Git记录确认）
- 原 `Stage88` 全305源 Git blob `86e96b726f677a15f5a7c8d740e3caca5c83e3fc`；
- 原D0共519、原D1共305、原D0-only共214；全六日期 `2025-01-30, 2025-06-02, 2025-08-01, 2025-10-02, 2026-06-21, 2026-07-28` 已被以前研究曝光，绝不是未知样本外。

单候选规则：首次原D1当时只能看到t-1m闭合价P0；接下去120根1m只有bar结束才读取CLOSE；第一次CLOSE≤0.97P0，随后首次CLOSE≥历史已闭合最低CLOSE×1.01且大于前根CLOSE，才得到模拟确认；确认时刻下一分钟OPEN作为未成交入场代理，固定360m/1440m后退出下一根OPEN。未出现回撤、未恢复、无实际成交活动或分钟归档缺失不得擅自填充正收益或零利润。20bps each side只是原理敏感性不是用户交易金额/真实费用。

## 请重点独立验证

1. 检查先冻结再编码，规则有无在实验后悄悄变阈值/换日期/选择赢家；原Stage110/118/127/132等失败是否保持原样。
2. 检查原305分母是否严实，无D1的214原D0只是原WATCH对照，不能把305买入实验虚报519全市场G1。
3. 检查每根1m数据的交易时间、CLOSE可见时点、首次pullback与reclaim是否存在同根OHLC偷看、确认时刻与下一分钟OPEN是否严格因果、120根边界是否有未来数据泄漏。
4. 检查 Stage101 Stage88固定原始官方publisher daily ZIP/CHECKSUM SHA与asof原信号/原D1 +1m entry/24h baseline是否逐币一致；任何市场源缺日、SHA不符、重复minute是否会FAIL，不许删除case保持成功。
5. 检查真实0成交量和0笔交易代理的拒绝、源断档/价格异常、价格缺失时`UNKNOWN` 与 `NOT_SCORABLE`。特别确认固定6h/24h并非已执行止盈止损。
6. 检查全305聚合24 shards×6 dates×4及全305去重/原始信号字段、按日期风险、24h价格代理中位/亏损与极端尾部，独立复算并尝试至少三个负向篡改（其中一个篡改SHA、一个漂移时间戳、一个砍掉某原D1）。
7. 检查测试/CI是否真在Ubuntu/macOS运行，真实305 publisher源全量历史能否取得并输出机器证据，不可以把工作流已创建当作真实CI通过。**本审核包提交时尚未取得可验证的新Stage151 CI run id / 完整实际历史结果，请审查者直接查当前工作流，并如不能重现，明确`BLOCKED`，不能根据预期自填数值。**
8. 检查新CI仅push/手动dispatch无schedule、不会修改Frank/Stage99、启用Mac daemon/自动Gmail/真实交易，也不可把模拟费率、未知真实L2和无notional默认成G4 PASS。
9. 真实核心业务结论：新的 D1 后二次确认是否只是减少样本数从而造成选择偏差？若历史部分日期有效、整体无效，应保持`REJECTED/UNVERIFIED`。成功CI不等于收益策略通过或允许部署。

本地基本命令（需在checkout后执行）：
```bash
cd crypto-300-profit-mission/local-agent/scripts
python -m py_compile monster_v4_stage151_post_d1_pullback_reclaim.py test_monster_v4_stage151_post_d1_pullback_reclaim.py monster_v4_stage151_aggregate_post_d1_research.py
python -m unittest -v test_monster_v4_stage151_post_d1_pullback_reclaim.py
```
真实305须逐shard沿工作流命令下载历史publisher原始ZIP+CHECKSUM，必须全部得到SOURCE_MATCH才能判通过。

必须返回：审核身份及准确版本（未知`UNVERIFIED`）、固定审核SHA、原始真实输入及结果证据、负向样本、P0/P1/P2实际缺陷的文件行号/复现/最小修复、`APPROVE | REQUEST_CHANGES | BLOCKED`结论。须明确是否影响WATCH或BUY以及 `NO_MERGE / NO_DEPLOY` 是否仍维持。

无论本轮代码审核是否通过，业务门禁仍：G0 PARTIAL, G1 NOT_SCORABLE, G2/G3 NOT_PASSED, G4 UNKNOWN, G5 FULL RELEASE NOT PASSED, G6 NO_GO；旧Stage116 2026-10-14 06:00Z SOURCE_FAILED_NO_BACKFILL，Stage118/127 REJECTED、Stage132 first buy price-only NEGATIVE；禁止恢复自动采集、Monster本机安装、自动交易或邮箱发信，Frank保持运行不变。


## 实际CI完成后的新增真实证据（不改变上述固定审核代码SHA）

先前提示词写入时CI未知，现已实际核实固定源码SHA `b309bf75a46a48cde1aa6b14c17d3e6b7c1b53c2` 对应 [Stage151 Actions #38724428671](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38724428671)：2026-10-15T11:01:50Z开始，11:03:21Z结束，27/27 jobs `SUCCESS`，其中 Ubuntu/macOS 各 `Ran 11 tests / OK`，24个 original305 官方历史publisher归档shards SUCCESS，最后全305校对/Git写入日志 `STAGE151_ACTUAL_GIT_EVIDENCE_PUSH_CONFIRMED`。远端真实已持久保存：

- `crypto-300-profit-mission/monster/evidence/monster_stage151_original305_preregistered_summary.json`（Git blob `f96354da4052c911a726954efdcc5bbd6`）
- `crypto-300-profit-mission/monster/evidence/monster_stage151_original305_preregistered_rows.jsonl`（Git blob `fcc8053f5bb1d672e8eaf907ee3d9ec64e911505`）

真实305事件：184先跌3%且恢复1%，113未回撤，8回撤未恢复；184完整24h毛收益中位 `-2.446284%`，示意双边20bps后中位 `-2.835720%`；6日期仅一个中位为正、四负、一个零，`STAGE151_EXPOSED_PRICE_MODEL=REJECTED`。请独立复算源和逐币统计，不要因为Actions成功就给业务G4通过。本报告是业务负结论，并不代替你的独立代码审核。审核代码SHA仍严格为 `b309bf75a46a48cde1aa6b14c17d3e6b7c1b53c2`，后续新增文档和机器结果并未修改待审源码。
