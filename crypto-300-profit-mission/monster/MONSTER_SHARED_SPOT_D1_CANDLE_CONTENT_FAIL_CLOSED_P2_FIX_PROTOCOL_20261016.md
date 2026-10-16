# Monster shared Spot D0→D1：Codex P2 D1内容损坏后必须研究失败，固定源协议（2026-10-16）

本协议事前冻结于修复源代码之前。原独立Codex对唯一SHA `6e2897c4602ce554b57634fe05d25e7244068316` 报 `REQUEST_CHANGES`；3项P1审核范围内认可关闭，仅一项P2未关闭：`closed5m_source` 中只更改一根5m K线HIGH为 `"0"`、SQL主键与candle close_ms不变，原 `process_queue()` 接收到可解析但坏内容后抛出`ValueError:INVALID_HIGH`并被生产重试catch吞掉，最后将模型应原来评价成功的候选记为`LATE`。独立实测：原基线 D0 WATCH=1/D1 completed=1/LATE=0；破坏后D1 completed=0/LATE=1，研究仍然成功结束。此为**研究来源无法信任**，不是历史证据证明某个币原本真实LATE。必须修并加能够复现此精确缺陷的正负对照测试，不能仅以先前20/20为依据。

## 本轮固定允许修改和不可改范围

只允许修改新共享研究回放器`crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_d0_d1_original_core.py`、本模块同名`test_monster_v4_shared_spot_d0_d1_original_core.py`和必要研究证据、档案。**原`monster_v4_shadow.py`生产D0+D1、Stage26官方ZIP下载验证、原36 artifact、Stage152/153批准版及任何真实Mac生产状态禁止改动**。

在新共享引擎受控的`real_historical_closed_5m`回调返回给原生产`process_queue()` **之前**，完整校验要返回的8根已闭合5m：JSON为8元素数组；开/闭时间为预期UTC网格（5分钟，close=open+299999ms，8根不缺断、end<tick）；价格四项为正的有限十进制数，且low≤open,close≤high；已存栏位volume为有限非负数，quote为有限并且必须满足原生产D1已冻结`positive(CLOSED_QUOTE)`契约（如合法零交易quote发生，分类为`D1_EVALUATION_SOURCE_UNSUPPORTED`，研究fail closed，不能把其强行当作成功价）；所有无法解码JSON/不合法时间/数值/收益式特征因历史数据问题导致的异常转换成*不被原生产重试catch捕获*的明确研究`RuntimeError`，不改生产error catch。建议在返回前调用**未修改的**`production.evaluate_closed_5m(candles, tick)`进行预校验，能覆盖生产额外的特征及统计校验；每个真实D1评价会进行两次只读相同算法计算，不能执行交易或发送邮件。不得放过 `HIGH="0"`的等timestamp攻击路径。

测试必须同时使用**未mock的生产`process_queue()`**：原已确认WATCH=1的隔离合成1m数据跑出基线completed=1/LATE=0，然后只修改WATCH首次D1读取的缓存某根5m HIGH="0"、保持end_ms/SQL行数与时间戳不变，再用同一生产函数重跑，应`RuntimeError`退出且不存在返回的完整队列摘要。另添加合法完整8条、错误/非有限JSON、OHLC、quote、开放与收盘时钟变化的参数化负测。代码尽量最小修复，不增市场API、名单和多stage研究项目。

必须跑真实github.com仓库原PR分支对应源码SHA新的Ubuntu/macOS pytest/unittest/py_compile（全旧测试继续），并在真实36历史artifact双SHA及BTC ETH 20份官方minute ZIP+CHECKSUM原reader同结果复验真实CI。`5/5`Job全部success且trigger SHA精确匹配之后形成可交另一AI审核的固定SHA，归档后只允许JSON/doc差异。**本轮代码作者不可自称独立APPROVE**。真高压445币和全758原来源仍未完成，G4 UNKNOWN/G6 NO_GO。禁令NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE，不改Frank、Stage99、Mac及任何定时采集。
