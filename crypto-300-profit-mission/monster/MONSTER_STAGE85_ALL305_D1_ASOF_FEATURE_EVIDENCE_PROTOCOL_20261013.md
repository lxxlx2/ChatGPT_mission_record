# Monster Stage85：全部305条D1当时可见量价特征调查预注册

日期：2026-10-13 Asia/Bangkok | 唯一Monster Draft PR #30 | `DATA_EVIDENCE_ONLY`。

## 为什么要做

[Stage83真实全519连续3m回放](MONSTER_STAGE84_FULL519_EXPOSED_D1_CONGESTION_AND_MISS_ATTRIBUTION_20261013.md)明确表明：27/28原D0提前2×获得D1提前5分钟确认，但305条D1、平均7.26/日、峰值52/日，G3失败。当前持续回放的Git工件只保存**D1时刻**，缺该时刻的quote15、trades15、ret60和归一化量比，因此不能据原D0时刻的老特征声称已评价了D1当时的拥挤筛选质量。固定配额先到先占已历史失败，禁止重复。先保留全部D0和D1，补可审计原始特征，再设计一套独立的新高优先级候选，避免用旧2×标签倒推参数。

## 冻结全量人群与资料来源

- 不筛赢家；`monster_stage83_all519_source_and_D1_result.jsonl` 的原519全部保留，Git blob `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`。其中应有305条`D1_FIRST_UTC`，164首次、141再点火；其余214个未升级的D0仍留在Stage83原始总表，不偷偷删掉。
- 同币首次D0的官方来源记录来自 `monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl`，Git blob `8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a`，用于原D0时间/第一次61分钟量价一致性核对。
- 按6个已曝光日期、每日期按币名排序后`index % 4`组成共24个日期分片，分片覆盖全部305条真实D1，无成功样本挑选。所有类别均保留，含3条已确认TradFi、15条乘数未验证以及501条暂缺加密身份凭据中的相关D1。D0时期身份不等于后验真实Crypto，类别来自已存Stage82，只做附注不做筛选。
- 对每条D1直接使用[Stage38 Binance USD-M官方1m ZIP + .CHECKSUM加载器](../local-agent/scripts/monster_v4_stage38_usdm_original_v4_1m_pilot.py)，精确取第一次D0之前最后一根已闭合分钟，以及D1之前完整61根已闭合1m bar所需自然日。对每个真实源文件校验官方发布方SHA，按Stage83保存的当日原SHA再次对账；来源矛盾失败，404则CENSORED、不按0或没有机会处理。
- 严格只用 `tD1-61min..tD1-1min` 以及 `tD0-1min` 可见数据。输出 `D1_ret60_pct, D1_quote15_USDT, D1_trade15, D1_quote15_normalized_prev45, D1_relative_first_D0_pct`，以Decimal精度记录，不填假设值。额外记录`D0_to_D1_delay_min`、首次/再点火入口和按`USD-M symbol`的原始币日身份。
- 对Stage79冻结资格重新校验：已有真实D1时刻的所有条件必须仍为TRUE；首次直接升级要求`D1 UTC==D0 UTC`；再点火要求`D1>D0`；首次61分钟实际资料与Stage64四项量价一致。禁止据后验2×/5×/10×标签做任何选择或排序。

## 技术与验收

建立一个导入原Stage80 `from_archived_closed_bars`、`gate`，原Stage38 `verified_1m_day` 的只读提取器。24个分片全部源验证及资料一致性PASS后，聚合全部305唯一D1行并保存到原PR；任何一个失败或删失必须如实标 `PARTIAL`。预期输出可分析后续D1当时的量价分布及真实拥挤日。

**此阶段绝不更动Stage79的8%/5%等阈值，不生成另一个策略参数，也不声称本批历史数据是OOS。真正新的策略必须在特征证据完备后单独前瞻冻结，且以2026-10-14/10-28/11-11预先锁定的未来时间窗验证；目前第一窗甚至尚未开始。**

`D0_UNCHANGED, D1_UNCHANGED, LABELS_RESEARCH_ONLY, USER_NOTIONAL_UNSPECIFIED, OOS_NOT_DONE, G3_REJECTED_EXPOSED, OTHER_AI_REVIEW_NOT_DONE, EXECUTABLE_PNL_UNKNOWN, DEPLOY_NO_GO, GMAIL_OFF, AUTOTRADE_NO_GO, FRANK_UNCHANGED`。
