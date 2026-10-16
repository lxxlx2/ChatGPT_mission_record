# Monster Shared Spot Codex P2 APPROVE + 下一份445同库真实高压回放执行冻结（2026-10-16）

**独立审核事实**：用户传入Codex固定审查 SHA `1154e97a25648dbf58c181be62076e4c1d406dde`，对照旧`6e2897c4602ce554b57634fe05d25e7244068316`，最终 **APPROVE，仅关闭一项P2**“同timestamp缓存闭合5m HIGH=0 误当重试/deferred/LATE”。独立使用未经mock的原`monster_v4_shadow.process_queue()`，合成正常`WATCH=1/D1_completed=1/LATE=0`，只改一条close时钟不变的HIGH`"0"`，新程序抛`RuntimeError:SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE`、根因`HISTORICAL_D1_SOURCE_BAD_OHLC_OR_QUOTE`，没有成功返回报告，实际生产`LATE_EVENTS=0/DEFERRED=0`。审核身份`Codex`，底层准确型号`UNVERIFIED`。独立跑22/22、py_compile，通过已发布[CI #38835269851](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38835269851)固定触发5/5 jobs；**本次独立审查没有重新下载**36历史artifact与20天BTC/ETH ZIP，后者仅是CI任务证据。原生产`monster_v4_shadow.py`未改。Stage152/153各自固定 SHA APPROVE继续有效；不得扩大成本模型/全市场到此approval。

**本冻结文档不算完成445样本回放**，但规范下一段主线，用户先前已有研发授权。PR #30继续Open/Draft不merge/deploy。

## 固定分母及前瞻规则

- 原 `758`个历史2026-10-16**二次**冻结Spot ASCII成员来自36份Stage26双SHA锁定历史artifact；其原2026-10-11预注册只保存504 current+254 archive-only数目、不含每币完整名单Hash，还有2个不支持Unicode未映射。不得回填“当年逐名预注册”。
- 唯一高压日`2026-02-04 06:00 UTC`起，24h预热 + 168h激活 + 24h回退出场的共216h源，必须保留`758总尝试`、`445历史源完整`、`313原来源缺失`，仅**445完整来源子集**允许真正运行共享D0(once/3min)/D1(once/3min、limit8)；另外313永远不当0 WATCH、0收益或合成0量。真实现时Archive可能无法重新取得某些原来已完整的445，新增未取得情况单列`NEW_SOURCE_RECHECK_FAILED`，不偷换当期分母。
- 高压与普通对照日均为已公开使用的历史样本，不能称OOS；币种成员虽由Stage26历史完整源资格定义，不能按原88? /98个历史信号或未来盈亏再缩小候选。这是“来源完整子集”的回放，不是交易所当日完整listing/PIT。
- 每个币必须经原`monster_v4_stage26_continuous168h.read_complete_216h`取得 **10份对应日期** Binance官方Spot 1m ZIP+同host CHECKSUM，官方源原SHA256记录每币×日、10日UTC全分钟连续；实际2026-02-03至2026-02-12的10天，但样本来自`2026-02-04T06`至七天后。一次性全同一时间轴原`observe_snapshot`/原`process_queue`，引用已独立批准的`verified_closed_5m_for_original_d1`，无新规则、非法5m立即阻断。不要调用旧Stage26 WATCH列表生成新D0队列。
- 数据批量重取可用**少量固定分片**并行，无时钟混用、无实盘API交易、不使用付费GMGN。中间来源缓存SQLite严格独立离线、不可覆盖、分片姓名/sha和Git触发SHA绑定、机器完整性检查后才装入一份共同SQLite；所有来源齐备**才**跑全445。先固定并验证非机会挑选的pilot样本（从445按字典序/确定性算法选择，而非已知98 WATCH赢家），确认新程序、脚本和成本后才做全445，避免一次性4450笔网络请求没有防重复/限速就盲目触发。
- 除历史官方1m源，冻结D0的24h成交额context只是过去1m quote聚合代理，不是实际当年24h HTTP ticker或订单簿。曾经Stage28只注入Stage26已发现WATCH，仍需与**同一445成员**比较：Stage26独立原D0 WATCH出现时间、Stage28共享D1容量/迟到（源自注入）、新真正共享D0→D1实际WATCH/INVALIDATED/LATE/SETUP，一起报告首次评价时钟、最大单3分钟时点待处理数、queue backlog、队列15分钟失效数。不能把旧98币中91 LATE直接复制成新实测，不能把任何LATE称为盈亏损失。
- 有订单风险或审核漏洞：真实PIT listing、Spot/Futures共同资源争用、Gmail送达、真实可成交净利、OOS、Mac deployment一概保持`NOT_DONE/UNKNOWN`；G4 UNKNOWN、G6 NO_GO，`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，不启用Stage99定时器、Frank不动、不安排任何schedule。

## 具体开发准入和阶段

1. 本审核APPROVE先写长期节奏，保持审核SHA原样不可改。制定`445`严格来源inventory、分片计划以及校验与并发预算，核实本地冻结名单和已存的原source sha记录，记录实际原数据中的可再取得比例而不是假定100%。完成CI参数化文件及负向测试，先在固定非事后选币pilot内真实端到端检查，禁止虚称445已测。
2. 证据足够再完整445 Source-Complete一致性可复现全回放，必须同一次真实官方Source，与Stage26/Stage28同名成员对齐，严格保存事件级表现和延迟原因。
3. 另一AI独立审核新源SHA、测试和官方证据、来源完整性与实际同一SQLite，全绿色也不是默认策略通过；按用户原流程后置Mac。
