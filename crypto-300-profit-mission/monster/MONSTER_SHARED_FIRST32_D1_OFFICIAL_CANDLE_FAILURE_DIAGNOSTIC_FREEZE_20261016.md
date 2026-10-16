# 32币真实源D1初次fail-closed定位：在不改已审生产规则前固定研究计划（2026-10-16）

已实现首445来源28份分片机制，shard01(16币/160官方日)真实源GHA #38840401636成功/Artifact ID 12021445690，shard00(另16币/160官方日)GHA #38841076844的来源采集Job独立成功，Artifact ID **12021352471**。新32币共享研究在`#38841076844`固定源码`c16c951b24639b90b07f7b944d5911ab8005b489`的real runner中，在`monster_v4_shared_spot_d0_d1_original_core.verified_closed_5m_for_original_d1`遇到`ValueError:HISTORICAL_D1_SOURCE_BAD_OHLC_OR_QUOTE`，向外正确`RuntimeError:SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE`，**未产出完整32币机器结果**；CI两OS基础门禁通过，官方两片320日Source ZIP来源核验通过，整个32币Job为failure。原Codex`APPROVE@1154e97...`只证明坏HIGH不会变为假LATE，**此研究阻断完全符合fail-closed设计，不能偷偷调原规则使CI变绿**。

## 本任务仅只读诊断，不修改原D0/D1核心

1. 固定从两份Artifact ID下载原zip/proof，按原source脚本实际验证raw ZIP SHA和每币分钟JSON SHA以及原758/445/313人口，不再浪费重复320天官方下载，也不信未经SHA匹配的本地文件。
2. 在新研究包装器外执行**观察层无副作用try/finally代理**，其唯一动作是调用未经修改的`verified_closed_5m_for_original_d1`，如抛`RuntimeError`则捕获第一处source failure的`symbol,venue,now_ms,8根源kline c[0]/c[6]/c[1:5]/volume/quote`及original异常根因；必须re-raise原异常，不改返回、不改变production.process_queue、原retry或信号规则。
3. 判断来源为真零成交/零quote、坏OHLC、非有限值、错开收盘时钟、还是其他源/原evaluator不可支持。不能把官方历史合法零成交直接谎称数据篡改；从之前同host .ZIP/.CHECKSUM reader得到的价格quote只证明发行者自洽，不是独立签名。
4. 顺带按同一实际32源旧Stage26逐币D0扫描记录真实WATCH UTC及02-06 00:36Z同刻数，但**由于新32共享研究在D1 source异常时整体FAIL，不能宣称这一时点32币新共享D0完整成功**；只能明确旧逐币参考与真正共队列范围的区别。
5. 仅作为`BLOCKED_OFFICIAL_D1_SOURCE_CONTRACT`机器诊断或已实际验证的有限成功; source层失败仍`NO_MODEL_REPORT`、`NO_LATE_SUMMARY`、`G4 UNKNOWN/G6 NO_GO`。真实CI只运行只读测试和对来源artifact处理，无schedule/邮件/实盘交易/Frank/Stage99。
6. 诊断后再根据真实证据选择后续业务研发：如果是官方零成交K线导致原D1 positive quote先验不支持，需要**另行事前冻结针对源实际覆盖率/严格NO_EVAL原因而不是随意变为deferred**的策略语义讨论与独立其他AI审查；如果损坏则先核对SHA/解码器。不得未经用户授权调整交易模型阈值。
