# 可直接发送给 Codex / Claude：Monster 32币官方源共享D0、零quote D1 研究变体 V2 固定版独立审核

请遵循项目 [Monster AGENTS](AGENTS.md)、[模块研发规则](MONSTER_MODULE_DEVELOPMENT_RULES.md)、[长期开发节奏](MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md)、[研究变体事前冻结协议](MONSTER_SHARED_D1_GENUINE_ZERO_QUOTE_SEMANTIC_V2_PREREG_20261016.md)。请审**唯一源码+tests+CI固定SHA：`dfceade891909bf374ce3e790f3aef33746f2938`**，用独立detached checkout，严禁将后续自动归档推动的PR HEAD偷换成审核版。仓库 https://github.com/lxxlx2/ChatGPT_mission_record ，Draft PR #30 https://github.com/lxxlx2/ChatGPT_mission_record/pull/30 ，研究分支 `research/monster-v4-local-discovery-20261010`。准确底层模型版本如不能独立验证写`UNVERIFIED`。

**为什么新增该实验**：旧真实32币共享原生产D0/D1在`ACAUSDT 2026-02-08 04:42 UTC` source8根中2026-02-08 04:30–04:34:59真实5m报价成交额为`0E-8`，价格合法而原原生D1所有quote必须正数，所以整个原Core研究fail-closed。此为合法无报价成交的源不支持问题，不是来源恶意伪造，也不是可当作迟到的券；**之前Codex APPROVE@1154e97a25648dbf58c181be62076e4c1d406dde仅批准坏HIGH0应致命退出，不批准改原生产规则**。此实验单独V2文件，原`monster_v4_shadow.py`和`monster_v4_shared_spot_d0_d1_original_core.py`源码禁止改。首次实现版本`19e4335e...`在真正来源CI中暴露schema覆盖失败；中间`f0e45dc...`修掉旧逐候选原生产`limit1`同tick可能重复选择问题以及schema漂移，末尾`dfceade...`加2项关键负面FIFO回归，因此不能用较早SHA的绿CI冒充这次审查。

**要看源码**（固定SHA）：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_d1_zeroquote_research_v2.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_shared_d1_zeroquote_research_v2.py`
- `.github/workflows/monster-v4-445-first32-zeroquote-research-v2.yml`
- 对照原`crypto-300-profit-mission/local-agent/scripts/monster_v4_shadow.py`和旧独立获批共享`monster_v4_shared_spot_d0_d1_original_core.py`不改；及`monster_v4_shared_445_first32_real_comparison.py`对照旧Stage26已冻结全32原币源。

**必须自己动手检验或标UNVERIFIED**：
1. 在`crypto-300-profit-mission/local-agent/scripts`运行`python3 -m py_compile monster_v4_shared_d1_zeroquote_research_v2.py test_monster_v4_shared_d1_zeroquote_research_v2.py`、`python3 -m unittest -v test_monster_v4_shared_d1_zeroquote_research_v2.py`，应`7/7` PASS。不是仅看当前Git状态。
2. 官方源：2026-02原758历史成员只有445曾source-complete、另313继续CENSORED。本批固定字典序前32（不是按旧98爆发/赢家筛选），原官方16币×10天两个Publisher ZIP+CHECKSUM离线源包见Github Actions ID `12021352471`、`12021445690`；原生产真实3,360tick必须同份source比对Stage26每币WATCH时钟，没有手动从Stage28 98候选导入WATCH。Git摘要[机器真实原始D0+实验D1](evidence/monster_feb445_first32_zeroquote_D1_research_v2_actual.json)，机器 Git blob `d741cabce2784e9e9dd2e2b549ae9013f9dd9f38`、`trigger_commit_sha=dfceade...`；前置两个source SHA 与Zip/checksum属于此前官方来源CI下载后封存，检验真实性需自己下载并复算，不可未经下载声称独立原始官方fetch。
3. 真[GitHub CI #38855446302](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38855446302)，触发SHA准确一致，**4/4 jobs completed/success**；Ubuntu24.04/macOS各7 tests OK+编译；真实原两份旧GHA source artifacts重取解包校验全部32币JSON/ZIP SHA，原V4共享D0×3360轮 + 研究V2 D1，机器结果归档前检查原production/core/newsource/tests/workflow blob与触发源码相等。CI日志确认≠另一个AI已独立认可。
4. **本次真实结果核对**：29个原Stage26真实逐币WATCH与新的真正共享D0 WATCH=29，全部逐币UTC完全相等；2026-02-06 00:36 UTC **7个**同刻为1000SATS,1INCH,2Z,ACA,AIXBT,ALT,APE全部USDT；SETUP_ACTIVE=13，INVALIDATED=7，D1 EVALUATED=27，`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE=2`均ACAUSDT，累计不支持的处理槽10次（不是10币），真实D1 LATE=0，累计selected/deferred=134/105（不是独立候选数），最大同刻WATCH=7不达到limit8，无法断言原Stage28的98同刻91 late是否会在真正445回放中复现。
5. **重点找源码漏洞P0/P1/P2而非只看数字**：研究variant`experimental_queue_handler`通过在single SQLite上临时mask overflow，先固定原FIFO最老8个（是事实，非后验），正常非0数据原生产`process_queue`必须与原无变体完全等价；其中一个zero quote而同刻有9候选时，后第9个不能借走8个容量，或重新被错误处理两次；如第1个在源不支持下消耗一个3分钟处理槽，状态只得WAIT/最终SOURCE_UNSUPPORTED，不能伪造出SETUP或LATE。中间任何SQL/transaction异常可能在`with store`内持久化临时retry屏蔽，需要真实隔离探针检验源与队列没有半写。若候选先已做过有效D1评价再出现合法zero quote，必须按原截至语义区分已确认NO_SETUP和未成功评价unsupported，不能静默吞错误。非法HIGH=0/负quote/非有限时间/断K线仍必须整研究fail-closed，不允许被零quote分支吞掉。每轮真selection`<=8`，尝试数/延期数不能被当独立币。
6. 确认原Stage26 original source signer同host self-consistency，不是Binance私钥数字签名；旧Oct11 prereg只有504+254计数、另外2 Unicode未映射，不得把二次名单冒充2026-02真实PIT上市；只有32/445完整来源已跑、413未跑、313源缺，真全445统一queue未跑。无交易金额默认、真实盘口成交、成本/净收益/OOS、原正式模型盈利评价、Mac、通知发送；所有门禁保持，Frank/Stage99禁止触碰。
7. 新变体`run_v2`虽使用离线局部`unittest.mock.patch`替换一次 `production.process_queue`调用，但原生产文件源码始终未修改；应该检查并发线程/异常退出patch恢复以及报告`only_original_production_D0_and_D1_called=False`，不可以假报“完全原生产D1批准”。
8. 本次若建议以后全445来源下载或补审，请明确缺少真实28/28 Artifact持续可用、资金/订单和未来OOS，不可直接部署、邮件、交易。

交付请按照：审核者身份、底层型号是否可核验、唯一固定SHA `dfceade891909bf374ce3e790f3aef33746f2938`、实际检出的文件/行号与最小复现和P0/P1/P2、实际运行测试输出、源码SHA/source Artifact对账等级、固定实验判定与推荐修复、最终`APPROVE | REQUEST_CHANGES | BLOCKED`，并单列剩余 G0–G6。旧源Core P2的Codex局部APPROVE不为新V2背书。此次新V2也必须继续`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`。
