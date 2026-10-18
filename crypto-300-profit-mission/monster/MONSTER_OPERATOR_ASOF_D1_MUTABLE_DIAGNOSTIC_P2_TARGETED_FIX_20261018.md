# Monster — Codex as-of 唯一残留 P2：D1未来错误泄露，定向修复与复审包（2026-10-18）

## 结论与明确门禁

**用户转交Codex的上轮独立审核：`REQUEST_CHANGES`，只剩P2=1（P0=0/P1=0）。** 上轮固定审核SHA `456111143f5ea1ac2e32103f71ea50dc5a27d078`，比较基线 `731a0dfad0a78e77c53d20dbea3e375aaa9e55e1`，审核者Codex，底层准确模型版本`UNVERIFIED`，本地独立隔离checkout `/tmp/monster-asof-review-45611114`。Codex验证原`LIMIT`后分类遮挡已修复；未来D2状态/费用、Source降级与恢复、未来LATE/INVALIDATED以及Futures事件/多回合隔离均在真实生产SQLite反例中通过。其指出唯一残留：`local-agent/scripts/monster_v4_opportunity_snapshot.py` 中 **`"d1_last_error": q["last_error"]` 没有时钟过滤**，以未来出现的`OSError:FUTURE_D1_FETCH_FAILURE`污染早420秒的历史JSON。

**新唯一待其他AI复审代码/测试SHA：`6dd74eb05af3b9055575a0996d00925b557bc09b`。** 与本次修复前实际分支HEAD **`c0c9e6ae3de6f3f06791adba824a276c785bf4a6`** 比较，实际只改**两份文件**：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`
- `crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`

其余原生产`monster_v4_shadow.py`、D0/D1/D2、SQLite schema、Frank、Mac、采集、Gmail、GitHub工作流、交易及Stage163已获批证据未修改。PR#30保持Draft，旧 `REQUEST_CHANGES` 不追溯改为通过。

### 为什么保守返回null，不假装关联 failures

真实`monster_v4_shadow.process_queue()`会在失败后的未来时点原地改写`candidate_queue.last_error`，无每次失败`observed_ms`，随后被未来状态覆盖。生产`failures`的实际字段为`(id, venue, observed_ms, stage, error)`，D1插入甚至只保存异常**类型**，不保存`candidate_queue.id`、`symbol`或原错误消息，**不能用venue+时间按猜测的顺序配对单个Episode**。因此真实存储不能可靠重构历史某个候选当时的`last_error`。正确修复是停止在asof JSON暴露无时间证明的可变队列字段：
- `d1_last_error: null`，**无论查询时间是多久都保持**，不给没有事实依据的“当前准确错误”特例；
- `d1_last_error_history_status: UNRECONSTRUCTABLE_FROM_MUTABLE_QUEUE_FIELD`，明确字段不可从历史记录还原；原真实`failures`仍在生产DB留作总体故障诊断，不能被误认为某个候选的历史故障。
- 不修改其他所有信号排序、深度信息或D2状态。它不是填充伪数据，也不是新生成SETUP的策略因子。

### 源级与真实SQLite/CLI回归

新增`test_d1_future_failure_is_not_leaked_into_same_past_asof_json_cli`，沿用生产`open_store/observe_snapshot/process_queue`并非自建假的表，用两个真实`3m`轮次形成Spot WATCH，先用子进程真实执行：
```zsh
python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py --db /path/to/your/test.sqlite --asof-ms 1800000180000 --format json
```
上面只是本测试调用形式，**不要将示例临时文件路径当作用户现存Mac生产DB路径或历史实盘时钟**。真实自动化测试内部用TemporaryDirectory，先在`BASE+180000`获得完整JSON；其后在`BASE+600000`（未来420秒）让原生产D1回调抛`OSError("FUTURE_D1_FETCH_FAILURE")`，实际验证生产`candidate_queue.last_error`现在含该错误、`failures(stage=D1).observed_ms=BASE+600000`；再用相同旧asof调用**真实CLI JSON**，整个JSON与错误发生之前**逐字段一致**，没有任何未来故障字符串。即使把查询时点移到未来失败已发生，也因为原事件无法按Episode精确还原而给D1历史字段`null`、保留来源说明。(测试采用合成时钟和合成OSError，不是实际交易行情)。

**实际GitHub [CI #39129122383](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39129122383)**：固定head`6dd74eb05af3b9055575a0996d00925b557bc09b`，工作流`monster-v4-research-baseline` job`historical-baseline`**SUCCESS，23/23实际步骤完成**；已独立读取GitHub原始Job日志，查询器`Ran 16 tests...OK`（原15+1真实CLI异步故障反例），原Shadow`Ran 31 tests...OK`，D2`Ran 12 tests...OK`。既有排序/历史D2时间/停机恢复/50k上限均持续回归；未向Binance或市场获取新数据。此前Codex对固定`456111...`的 15/15等成功CI不代表批准，其新P2因此保留到新版复审确认后才可CLOSED。

### 仅供局部复审的新任务：其他AI尚未完成

> 请定向**独立复审** Mission Monster PR#30`https://github.com/lxxlx2/ChatGPT_mission_record/pull/30`唯一代码与测试SHA **`6dd74eb05af3b9055575a0996d00925b557bc09b`**，比较基线`c0c9e6ae3de6f3f06791adba824a276c785bf4a6`。此前Codex在旧被拒固定SHA`456111143f5ea1ac2e32103f71ea50dc5a27d078`结论`REQUEST_CHANGES`，P0=0/P1=0/P2=1，唯一剩余是`--asof-ms`过去JSON读取当前`candidate_queue.last_error`造成未来420秒D1异常回填；上轮其余未来D2/Source/LATE/INVALIDATED等均由Codex独立确认修复，不必重新开启无关研究。请实际从Git取固定SHA，查看git diff，确认只改`crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`与`crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`。核对真正生产`monster_v4_shadow.py`写D1故障`candidate_queue.last_error`会原地覆写且没有历史时间；另`failures`只含venue/observed_ms/stage/error而无可靠谱对的候选Episode ID。查新代码`d1_last_error=null`并明确`d1_last_error_history_status=UNRECONSTRUCTABLE_FROM_MUTABLE_QUEUE_FIELD`，不能以venue时间相关性虚构历史错误。**独立实际用原生产open_store/observe_snapshot/process_queue和真实CLI --asof-ms JSON**重做WATCH前后、在晚420秒抛合成OSError D1失败、同一过去asof之前/之后整个输出不变且无未来错误，确认`candidate_queue`实际上存了未来错误且`failures`记录了正确未来时间；额外检查D1现在时诊断显式不可还原，不误升BUY。不改原D0/D1/D2策略、Frank、Mac、通知或钱包，不宣称完整市场PIT。真实执行`python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_opportunity_snapshot.py`和原Shadow/D2用例；GitHub [CI #39129122383](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39129122383)核验触发SHA、23/23 job steps、16/16查询器、31/31 Shadow、12/12 D2实际日志。给出Reviewer、精确模型版本(不明填UNVERIFIED)、固定SHA、`APPROVE/REQUEST_CHANGES/BLOCKED`、P0/P1/P2、实际反例、准确代码行号、无法核验的UNVERIFIED。**仅审这一D1残留及直接回归，旧时钟/经济/静态报价审核不要重新展开**。原门禁`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`保持。CI成功不能冒充独立外部审核批准。

**归档时状态**：`D1_MUTABLE_LAST_ERROR_P2_AUTHOR_FIXED=true`、`CI_16_31_12_PASS=true`、`OTHER_AI_INDEPENDENT_REVIEW=NOT_DONE`。无真实Mac投产，无新交易对实时行情、实盘买卖与净盈利验证。
