# Monster zero-quote V2：Codex 1 P1 + 1 P2 修复前冻结协议

日期2026-10-16。用户提供针对唯一固定 SHA `dfceade891909bf374ce3e790f3aef33746f2938` 的独立 Codex **REQUEST_CHANGES**，旧审核者精确底层模型版本`UNVERIFIED`。原真实源32币2个Stage26归档复验及历史结果吻合；原`monster_v4_shadow.py`和已批准共享`monster_v4_shared_spot_d0_d1_original_core.py`没有改。本轮只修隔离零quote实验变体及其tests/文档/CI，禁止改生产策略、交易、Gmail、Frank或Mac。

## 上轮独立阻断

- **P1**：原`experimental_queue_handler`把原FIFO前8之外和含quote=0者的`retry_after_ms`暂改为`now_ms+1`，在单个外层`with store`内调用原production `process_queue`，它的内层`with db`会提交临时掩码。若随后SQL trigger对正常BB候选UPDATE `RAISE(ABORT)`，`finally`恢复在外层因异常执行的rollback里消失，但前面mask已提交；实际关掉并重开SQLite后源AA掩码残留，错误来源以后研究时序。**不能声称SQLite内嵌context manager为嵌套事务。**
- **P2**：原`now_ms >= deadline_ms`的合法零quote分支，不区分`last_evaluated_bar_ms`非空的已经成功完成D1评价的候选，误把本已评价的候选标记`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`；`now>deadline`原production已正确标`EVALUATED/NO_SETUP_WITHIN_WINDOW`，要对`deadline-1/deadline/deadline+1`和`last_evaluated_bar_ms`空/非空做全矩阵负例。

## 实施合同

1. 用**单独的、明确提交的 mask+unmask 阶段**取代“外层with db + 内层with db”假嵌套。读取冻结FIFO前8以及所有其他eligible的原`retry_after_ms`，如需要掩码，在临时SQLite隔离研究连接写入并提交；再调用原production`process_queue`仅处理原被保留的有效候选（由它自己内部提交）；无论成功、读取异常或SQL`sqlite3.IntegrityError`，必须在错误逃离之前退出任何未完成事务并在**新的独立事务**准确恢复全部original retry，提交后READBACK校验全部掩码的原值，并确保关闭重开SQLite仍不残留。若恢复失败，主动抛`ZEROQUOTE_RESEARCH_MASK_RESTORE_FAILED`，不伪造研究成功。不要盲目回滚生产已经提交的真实候选处理；正常无零quote仍直接调用原冻结队列限8。
2. 只修实验V2的`last_evaluated_bar_ms`终态分类：到deadline/晚于deadline，若此前有已完成合法评价，应为`EVALUATED`、`last_error=NO_SETUP_WITHIN_WINDOW`并计`completed`，无SOURCE_UNSUPPORTED、无虚假`LATE_REVIEW`；只有未曾完成D1评价、真实quote0并在期限仍无法评分，才可终态`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`，明确不计成功评价。保持队列每3min最多8槽的FIFO/第9不借位、quote0先前未评不可被假写成成功。
3. 新真实SQLite（非mock原`process_queue`）SQL故障：AA零quote+BB正常+真实SQLite BEFORE/UPDATE触发`RAISE(ABORT)`，检查原抛出、**close/reopen** AA和第9号候选original retry字节一致；另加原历史source reader抛`RuntimeError`的after producer inner-commit恢复；无错误正常9币满8第9不提前处理。6格合法零quote而源reader故障时整个实验必须失败且不留下mask。
4. 新6-case deadline`-1/0/+1` × `last_evaluated_bar_ms is None/not None`，核验临界状态、SETUP和LATE事件计数，准确测试原生产已完成D1评价规则。额外必要的负面包括原`HIGH=0`损坏source仍fail-closed、无zeroquote原production事件/queue/execution counts逐项相同，真实32币publisher-sha历史输入二次重放摘要不应被局部代码修复无解释地漂移。
5. CI 只在本分支源码/tests push或手动触发：Linux/macOS全单测、py_compile、再从`12021352471/12021445690`真实Artifact核32×10份sha+3360tick研究变体，机器evidence与triggerSHA固定Git，最终新SHA交另一AI独立审查；**CI成功≠Codex独立APPROVE**。不因这两个代码bug调整价格、信号与模型阈值。
6. 延续758原历史分母/445 Stage26 source-complete/313删失不变。本实验32币真实WATCH29，D1 EVALUATED27/SOURCE_UNSUPPORTED2/LATE0，是前一版研究已验证的历史陈述，修复后若数字不同先分析，不为保数字而修行情。不宣称真正98并发或全445盈利；继续`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、G4 UNKNOWN/G6 NO_GO。

此文档在任何这轮可执行代码修复**之前**先提交 Git 保存，以防后续对话漏掉故障审查要求。
