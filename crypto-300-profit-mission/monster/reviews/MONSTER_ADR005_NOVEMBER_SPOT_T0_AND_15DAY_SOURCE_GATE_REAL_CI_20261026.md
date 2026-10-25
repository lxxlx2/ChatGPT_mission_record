# Monster ADR-005：11月冻结Spot T0与15天官方发行方源准入可执行交付（2026-10-26）

**完成级别：`OFFLINE_SOURCE_GATE_IMPLEMENTED_CI_PASS / INDEPENDENT_REVIEW_PENDING / G6_NO_GO`**。解决的是下一阶段工程上能否接入真实来源，不是提前产生尚未到来的11月数据、不代表预测模型/盈利通过。

## 1. 本轮解决的主线缺口

用户明确继续研发，不在已独立批准的D1 V2和D2微秒修复重复P2。原[ADR-005预注册](../adr/ADR-005-spot-d1-btc-relative-confirmation-preregister-20261024.md)要求三个**2026-11-02 / 11-16 / 12-01 UTC00**完整7日窗口的独立真实当时 T0 市场身份；每窗至少要先24h分钟源、整个7天D0/D1观察官方分钟、再7天后验2×目标标签分钟，不能把2026-10-17旧Spot511市场名单后填新日期。此前只有执行计划，没有可真正拒绝不合格原始输入的通用代码。

本轮固定**代码+测试审核SHA `48bf87fd0721071d8347f7f47df71253f2a835fc`**，此后文档提交不视为替代审核版本。保持原 Draft PR #30、不合并。

### A. T0真实HTTP归档准入

新增 `local-agent/scripts/monster_v4_adr005_forward_spot_t0_gate.py` (Git blob `b2512a393594254633c371a6e576dcec001aa009`)。复用现成Stage163 **6条公共Binance Spot原始HTTP响应体ZIP+逐请求source_receipts.json**。ZIP原字节SHA、ZIP内成员精确集合、内外manifest一致、每端点原body长度+SHA、官方endpoint URL及200状态逐一核对后，再在**UTC整数微秒**上验证所有请求顺序、server/client clock合理范围，所有请求需在T0前15分钟内开始并于T0时刻或之前完成。拒绝回执晚到**1微秒**、首请求早于15分钟**1微秒**、未来回执相对显式asof、错window、错URL、改hash、漏成员/符号、重复symbol及旧10月归档冒充11月T0。保留全交易所symbol原行与Spot/USDT候选行、BREAK与非交易行不静默删除。

此准入工具不会捕捉数据、也**不声称自报的HTTP回执具交易所签名或当时真正收到的外部独立见证**：成功只输出`T0_ARCHIVE_STRUCTURALLY_ADMITTED_ORIGIN_UNVERIFIED`、`source_authenticity=SELF_REPORTED_HTTP_RECEIPTS_NOT_EXCHANGE_SIGNED`和`G0 PARTIAL_NOT_FULL_DYNAMIC_PIT`，未来新Listing/历史Crypto身份/账户权限仍UNKNOWN。当前没有11月T0时分别展示`WAITING_FOR_PRESTART_SOURCE_WINDOW`、`T0_CAPTURE_WINDOW_NO_SOURCE_SUPPLIED`或`T0_MISSING_CANNOT_RETROACTIVELY_PASS_PIT`，**不**假装已有511或其他固定币数。

### B. 同窗口前1天+7天+7天源清单

新增 `local-agent/scripts/monster_v4_adr005_forward_spot_daily_gate.py` (Git blob `9250a815ab80bc3335800b8cc90d2f5097bae1fd`)。准确为每个冻结起点生成**15个UTC完整发行方每日分钟日期**：
- 首窗：`2026-11-01..11-15`，观察`11-02..11-08`，未来标签`11-09..11-15`；
- 第二窗：`2026-11-15..11-29`，观察`11-16..11-22`；
- 第三窗：`2026-11-30..12-14`，观察`12-01..12-07`。

有真正通过A的T0原始归档后，以其**完整当时Spot USDT候选名单**逐symbol×15日建立发行方来源attempt，不以10月511作分母。复用原已审Stage166 `daily_paths`和`validate_daily_zip`，逐天验证官方 .ZIP/.CHECKSUM 的真实发行方SHA、正确1m文件名、完整1440根2026年Spot微秒时间栅格、OHLC/VOL合法性。状态区分 `UTC_DAY_NOT_YET_ENDED`、`SOURCE_NOT_SUPPLIED`、`SOURCE_REJECTED_OR_INCOMPLETE`、`VERIFIED_1440_OFFICIAL_1M`；拒绝symlink，预存未来整日不能在未闭时读成成功，坏校验不能算没信号。**只有全部T0候选×15日逐条真实核验**才能标`verified_complete_all_15days=True`（仅来源完整，不等于G0/G1正式通过）；publisher历史真实`available_at`、中途上架/下架仍UNKNOWN；任何时候G6=NO_GO，不计算实际2×或未来真实收益。没T0时只生成三窗日历、无市场分母，`G0 POPULATION_UNKNOWN / G1 NOT_SCORABLE`。

### C. 实际GitHub执行与证据（非计划）

固定执行用两个**只对workflow自己文件改动触发的单次push**动作，均无schedule/cron、外部采集、Mac、订单、Gmail：

| 实际证据 | 结果 |
|---|---|
| [Actions #40215340393](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40215340393) | T0第一轮`12/12 PASS`；包括**真旧Stage163 10月官方ZIP/SHA对三个11月窗全部拒绝** |
| [Actions #40215653388](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40215653388) | 开发中有一次**失败**，10项每日源测试的“成功分类不存在时取零”断言导致`KeyError`；该错误已修复，不掩盖中间失败 |
| [Actions #40215810493](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40215810493) | 最终**SUCCESS，T0 14/14 + 15天官方源10/10 = 24/24 PASS**；覆盖15分钟边界±1微秒、旧十月真实原ZIP、合成有效完整请求、未来asof、篡改、3窗固定日历、模拟官方ZIP 1440根/坏CHECKSUM、未来日期和symlink |
| 最终 Artifact `12607271877` | `monster-adr005-3window-15day-no-source-preflight`，实际六份JSON（每窗T0+日历）。本会话另独立下载本地zip逐成员检查：**3份T0均`WAITING_FOR_PRESTART_SOURCE_WINDOW`，3份15天均为未来未闭日，无虚构ticker分母**，均G1 NOT_SCORABLE / G6 NO_GO。Artifact外包SHA256 `7bb2eda5b404ced221e2c495d56caaa2429af1ebdbf18443f2f4fea4c9c47e61` |

最后CI固定SHA `48bf87fd0721071d8347f7f47df71253f2a835fc`，两份新测试Git blob分别`a0cde6716a195483428919ac60bc151cb444455f`和`08c19234a80b3508fc3999d470a76dd355253305`。

**原已被Codex独立批准代码未变**：本轮直接比较Git Blob与各自独立审查固定SHA，D1`monster_v4_d1_rbtc15_episode_research.py` SHA `d7afa1053f82fb5c6b13b91ef41d0836e4ca8094` 与`d743acb...`一致；D2 `monster_v4_spot511_d2_signal_receipt_coverage.py` SHA`c80dc799074e63230d88ebaf81bf573a870b91e1`与`c4a8f1...`一致。

## 2. 不运行后台的可执行读源命令（用户有真实原始证据时）

从仓库根目录执行，输入必须是真正按Stage163格式已获得的原始HTTP ZIP和回执文件，不能把旧T0提供给新窗口。所有命令只读输入，输出为新的研究JSON路径（已存在则拒绝覆盖）。

```sh
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_adr005_forward_spot_t0_gate.py --window-start-utc 2026-11-02T00:00:00Z --asof-utc 2026-10-26T00:00:00Z
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_adr005_forward_spot_daily_gate.py --window-start-utc 2026-11-02T00:00:00Z --asof-utc 2026-10-26T00:00:00Z
```

**不在本轮自动执行新的交易所捕获或安排T0自动任务**。在不具实际对齐T0原始HTTP回执和真正可见时间时，后续即使ZIP全部有效也仅是离线历史研究，G0不可升级完整实时身份，G1/G2真正未来赢家的严格及时召回仍待来源成熟和正式评分。原ADR005第一个窗口曼谷时间**2026-11-02 07:00**；错过原窗口时间不能用事后下载补造T0或自动换一个表现有利的日期。

## 3. 建议其他AI固定增量审查范围

审查 **`48bf87fd0721071d8347f7f47df71253f2a835fc`**（相对本轮开发前`303162772801bc60fab61ca3b9c2c5527632ba51`），独立detached只读，执行上述两个`unittest discover`测试及CI源校验，复核T0时间±1us、真实旧10月ZIP拒绝、所有15日segment、未来ZIP未闭拒绝、官方SHA坏校验、无T0不造分母，检查原已获批D1/D2 Git Blob不变。重点审查：官方Stage163响应体只能证明来源包内部哈希一致，不能从中证明真正历史交易所身份或服务器签名；T0初始名单变化未知、发行方事后minute与当时`available_at`仍不能混同。未获得其他AI真实结果前**本新增A/B代码G5=REVIEW_PENDING**。

## 4. 门禁与权限

`G0 PARTIAL`（新三窗T0尚未取得，局部来源`POPULATION_UNKNOWN`）／`G1 NOT_SCORABLE`／`G2 UNKNOWN`／`G3 EXPOSED_NOT_PASSED`（2026-10研究，不得改历史阈值）／`G4 UNKNOWN`／`G5 NEW_T0_DAILY_GATE_REVIEW_PENDING`（旧D1 V2和D2 microsecond代码的限域批准保留）／**`G6 NO_GO`**。

**NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES / NO_NEW_RPC**；Frank独立模块不更动。
