# Monster Spot511 真实69条 D1→D2 时间证据桥：Codex 微秒边界 P2 修复/独立复核请求（2026-10-25）

状态：**INTERNAL_FIXED_WITH_REAL_EVIDENCE / EXTERNAL_REVIEW_PENDING / G6_NO_GO**。不对原D0/D1规则、研究SQLite、阈值或生产配置做任何修改。

## 1. 外部独立复审意见与固定比较范围

用户带回的第三方审查主体为 **Codex 主代理**（底层具体型号 UNVERIFIED），用户Mac、Python3.14.7、隔离detached只读工作区。其审查固定SHA **`342fc476a49c25640e6c8c47302338b56c69316a`**、针对新D2时间证据桥返回 **`REQUEST_CHANGES`**。已亲自复算上轮新9项+旧Stage163 12项合计21 PASS；下载 #40193435581 真实Artifact12599195855，69/69 WATCH和47/47 D1研究SETUP的历史T0报价均STALE的来源结论可复现，未发现P0/P1，只有一项P2：

原`_millis(iso)`使用`int(timestamp.timestamp()*1000)`把真实HTTP收到时刻**向下截断至毫秒**。当WATCH `2026-10-18T10:40:00.000000Z`，真实完整回执 `2026-10-18T10:40:00.000001Z`，旧代码会把它当成`available_ms==signal_ms`而错误显示 `ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME`，实际应为`ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK`。此项不改变旧69笔严重过期的历史事实，却误标时间边界，故P2，需修复复核。

**本轮新固定待审核源码 SHA `c4a8f1e701b3a34d404db6f352d7b02591ce65c1`**（这是含两份代码文件和一次性验收workflow的完整源码/测试版）；本审核说明及后续ADR提交只是文档，不得替代它。审核增量：`342fc476a49c25640e6c8c47302338b56c69316a → c4a8f1e701b3a34d404db6f352d7b02591ce65c1`。

## 2. 有界源码修复

- `local-agent/scripts/monster_v4_spot511_d2_signal_receipt_coverage.py`：
  - 删除浮点`timestamp.timestamp()*1000`与截断；新`_micros(iso)`经已使用的Stage163 `s163.parse_utc()`，从UTC aware `datetime(1970,1,1)`以`delta.days/seconds/microseconds`生成**精确整数微秒**，不得舍掉最后1微秒。
  - `classify_receipt_time_us(signal_ms, available_us, max_age_ms)`把原3m/D1事件毫秒乘1000再进行整数微秒比较，**晚到1微秒即 NOT_YET**，超过180000ms年龄仅1微秒即STALE，年龄**恰等于阈值则未超时**。
  - 原`classify_receipt_time(signal_ms,available_ms)`仅做整数毫秒兼容调用，不再被原始ISO HTTP入口使用；主分析`analyze()`的WATCH/D1分类**全部使用精确微秒**。
  - 旧`archived_quote_available_at_client_receipt_ms`作为显示兼容字段，只允许**CEIL向上取整**，杜绝未来回执提前显示；新增`archived_quote_available_at_client_receipt_us_exact`、`watch_vs_archived_receipt_age_us_exact`、根级`archived_receipt_availability_us_exact`以及时钟精度声明。**报告Schema V1→V2**，原原始回执/JSON不会被覆盖。
  - 不改变历史的69个WATCH、47D1事件、Stage163原始Binance HTTP/ZIP/receipts SHA、180000ms工程诊断窗口、交易费、名义额或任何ADR005冻结策略参数。
- `local-agent/tests/test_monster_v4_spot511_d2_signal_receipt_coverage.py`：新增**4项完整analyze集成和ISO解析测试**；包含信号等时、+1us晚到、-1us提前、阈值=180000ms、±1us过期/未过期、真实D1 SETUP时刻+1us晚到，以及读取Stage163原原始回执`2026-10-17T22:04:46.929464Z`的精确微秒。
- 仅一次性GitHub Actions `.github/workflows/monster-spot511-real69-d2-microsecond-receipt-fix-once.yml`，push仅匹配该workflow路径，没有schedule/cron，未调用私有市场接口；下载**原**V2 69事件Artifact，不重新拟合模型。

## 3. 实际代码测试/真实原始来源复核

- [一次性Actions #40213575043](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40213575043) **SUCCESS**，Ubuntu Python3.11，新增D2测试13/13及原Stage163测试12/12，合计 **25 PASS**；读取Artifact `12597793739`、原Stage163 ZIP原SHA及请求回执，然后重新生成固定研究新报告Artifact **`12606896190`**。
- 真实生成JSON V2 SHA256：**`736eb55f43ae50b1d8b111b30edd1f08f5a863ec4c45b453d5b9c4f5f9d62f6e`**（V1原生成JSON `9bd81c0303d082885c79c8d282c53eb879e4eea712dbe1840be03001d708c077`）。
- 本会话通过GitHub接口实际下载旧Artifact12599195855和新Artifact12606896190，使用本地zipfile/json逐键逐事件独立比较：**69行全部信号身份、WATCH/D1时间、D1研究状态、盘口证据分类、全部G4/NO_GO字段不变**；`WATCH=69 STALE`，`D1=47 STALE + 22 NO_D1_RESEARCH_SETUP`，`G4=UNKNOWN/G6=NO_GO`、`executable_net_return=None`、`can_confirm_g4=False`始终保留。
- **与V1预期差异不伪称全字节相同**：增加准确us字段、schema V2；旧HTTP回执尾数`.929464`，过去向下显示`.929`，新兼容显示安全向上为`.930`，对应WATCH age展示整数毫秒少1；真正分类年龄改用精确us而非展示ms。上述显示调整恰为P2修复本意。

## 4. 下一轮独立审核精确要求

**固定审核SHA `c4a8f1e701b3a34d404db6f352d7b02591ce65c1`，状态只可为`APPROVE / REQUEST_CHANGES / BLOCKED`，对本D2微秒P2代码和案例审查，不把此前D1 V2 `d743acb...` 的独立APPROVE或上次D2 `REQUEST_CHANGES`混同。**

实际执行：
```sh
export PYTHONPATH=crypto-300-profit-mission/local-agent/scripts
python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_spot511_d2_signal_receipt_coverage.py -v
python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_stage163_spot_t0_quote_friction.py -v
```
独立构造完整`analyze()`路径，以真实微秒ISO回执而非预转换整数ms攻击边界；检查UTC offsets/float-free整数运算、负时间、日期/时区、D1时点、阈值±1us、ms展示不得提前、Schema V2/旧来源Hash、真实69条结果V1/V2分类一致，原报表不覆盖。阅读GitHub实际Actions日志及Artifact再下结论。仍需明示不具完整信号时两侧L2+之后退出报价+真实交易费，旧T0 source不是10月18–24实时盘口，0 G4证据≠ 0 可交易币。

最终报告应包含固定SHA、具体模型/环境、运行命令和测试计数、P0/P1/P2文件行号与复现、实际源覆盖/G0–G6；**NO_MERGE/NO_DEPLOY/NO_MAC/NO_AUTOMATIONS/NO_GMAIL/NO_TRADES/NO_NEW_RPC**继续成立。

**门禁声明：`G0 PARTIAL / G1 NOT_SCORABLE / G2 UNKNOWN / G3 EXPOSED_NOT_PASSED / G4 UNKNOWN / G5 NEW_D2_PATCH_REVIEW_PENDING / G6 NO_GO`**。无自动持续采集任务。
