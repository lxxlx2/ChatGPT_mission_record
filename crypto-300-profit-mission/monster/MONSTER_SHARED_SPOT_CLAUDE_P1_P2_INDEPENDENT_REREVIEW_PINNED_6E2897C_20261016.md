# 给 Codex / Claude：Monster Shared Spot新固定 SHA P1/P2独立复审（只读）

原唯一仓库 https://github.com/lxxlx2/ChatGPT_mission_record ，Draft PR https://github.com/lxxlx2/ChatGPT_mission_record/pull/30 。

**本轮唯一待独立评审模型+测试+workflow固定SHA：`6e2897c4602ce554b57634fe05d25e7244068316`。** 上轮Claude `REQUEST_CHANGES@0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`，提出3 P1：源缺失758分母无CENSORED、任何调用者凭自造758名单+True布尔即可称FULL、原2026-10-11预登记只有504+254和额外2 Unicode数目但没有758币名单/hash。附多个P2：OHLC、D1来源异常当重试、source-census独立负例、没有下载之前的daily sha锚点等。Stage153另有Codex独立`APPROVE@4553cb6b18c5aaf723072d17a39f9ad92f0629c9`，仅上轮范围，不能自动批准本轮。

本轮修复必须按以下准确Git对象审核，**PR HEAD会随归档前移，不能用HEAD静默替代pin**：
- 事前约束 `crypto-300-profit-mission/monster/MONSTER_SHARED_SPOT_CLAUDE_P1_SOURCE_IDENTITY_CENSOR_FREEZE_20261016.md`（先于本轮代码提交）
- [Git二次冻结原758真实完整姓名和每日期complete名单](evidence/monster_shared_spot_stage26_original758_secondary_freeze_20261016.json)，Git blob `8467bfc0db7cb888f805f30eaae301a812fbb20d`，名单SHA256 `cea49caae4245dad910cc096bdaea953387bdfea64667a49916756d12297074a`
- [BTC/ETH20份官方SHA的二次固定](evidence/monster_shared_spot_BTC_ETH_20_publisher_daily_sha_secondary_pin_20261016.json) blob `08fdc8cf8054ad93089a93bcd1e3e6d26877367f`，它来自前一源码首次下载，**不能倒称已经在首次下载前预提交**
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_d0_d1_original_core.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_stage26_original_source_census.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_shared_spot_d0_d1_original_core.py`
- `.github/workflows/monster-v4-shared-spot-d0-global-d1-official.yml`
- [本次修复作者真实Git+CI详细报告](MONSTER_SHARED_SPOT_CLAUDE_P1_P2_REMEDIATION_REAL_CI_20261016.md)，不得仅信作者总结。

## 必须独立运行/核查

`cd crypto-300-profit-mission/local-agent/scripts`，执行`python3 -m py_compile monster_v4_shared_spot_d0_d1_original_core.py monster_v4_shared_spot_stage26_original_source_census.py test_monster_v4_shared_spot_d0_d1_original_core.py`和`python3 -m unittest -v test_monster_v4_shared_spot_d0_d1_original_core.py`，**新版应20/20 PASS**。真实[Actions #38812571412](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38812571412)触发SHA精确`6e2897c...`，五项Job全部Success：Ubuntu24.04/macOS各20测试、实际36份Stage26历史Artifact ZIP+内层JSON双SHA对账、BTC/ETH官方各十日1m ZIP+CHECKSUM真实下载+单SQLite原核心3360tick、源一致性归档Job实际打印`MONSTER_SHARED_SPOT_REAL_ORIGINAL_SOURCE_PROOFS_PINNED_GIT_PASS`。若无法自己获取原Artifact授权或官方数据，应明确区分已查看CI和独立下载验证 `UNVERIFIED`，不得从Git机器数字臆称自己跑过下载。

**新版机器证据**：
- [全4548源资格真实原36历史Artifact双SHA报告](evidence/monster_shared_spot_stage26_36_source_census.json)，Git blob `25d932d5e1ee72c4e6956f6fc3dfacf0df2dc43e`，每日期 `433/440/445/438/478/485` 个完整，`325/318/313/320/280/273`不完整；全2719完整、1829 CENSORED。仓库原758固定名单及六日期完整有效集合不是历史OOS/PIT。
- [真实BTC+ETH二币共享SQLite结果](evidence/monster_shared_spot_real_BTC_ETH_20260204.json)，Git blob `9f74c5a1144806c916cb6803b3eb00aad05e5145`，引擎源码SHA256 `d1fff2ee97b7375528e9de3e0d02ab3f4432838e3dc9f188c233e5b6063b50f3`，官方发行者同主机20份日SHA已再次与之前Git固定20相符，真实3360poll/2币均WATCH0且共享D1 0；原758分母中新增精确状态 `2已回放+443完整但未回放+313原缺源`。

**P1逐个独立验证**：
1. `run_shared`采用真实原生产D0+全局D1只调用一次的旧结构没变，但`FULL_758_OFFICIAL_VERIFIED`即使调用者提供自造758完整cache、同一自造`frozen_verified_roster`也直接报`SHARED_SPOT_FULL_758_NOT_VERIFIED_SOURCE_CENSORED`。不可让缺源313币被填0行情并悄悄参加原生产D0；后续真正全758必须新冻结与补足所有官方源。
2. 新`original_758_coverage`要求从SHA/硬锁Git blob的二次冻结中读到全部758实名，每币按day给出原来源完整/缺失及是否参与模型扫描。CACHE预载伪造True source SHA标记不能把`source_origin_verified`升级为真，更不能把perSymbol改成`OFFICIAL_VERIFIED`；只有`run_official_subset`通过受控`old.read_complete_216h`逐日1m真实官方ZIP+CHECKSUM才可标来源获得验证，严格是**官方同一个host的ZIP和CHECKSUM匹配，不是独立发行者签名**。BTC/ETH额外与之前Git20份日SHA二次锁定值匹配；其它尚无原始逐日预先固定，必须报告无先前pin。
3. 严查`504 current + 254 archive-only=758`，另两个Unicode不支持名称并未出现在原758 ASCII实测队列，不可说曾有760家同级可回放，不能将今日二次名单伪造成旧2026-10-11逐名预注册（旧prereg根本没有名单/hash）。如果认为仍不能历史确认PIT listing或旧类别对照，要明确是**不可补证事实限制**而非伪造“已验证”。
4. `prepare_symbol`OHLC异常、错误日期、时间缺口、quote/笔数、伪SHA拒绝，D1 8根闭合5m缺失或修改一根来源时`RuntimeError`必须逃离原`process_queue`的错误重试catch，不增加虚假的deferred；负向测试不能只断言20项数目，要自己做故障注入。Census独立测试应涵盖原分片丢失、不同日期名单漂移、总数篡改、原ZIP字节哈希错误；真实Stage26`load_zip`的ZIP/JSON双SHA逻辑需检查。
5. 剩余真实高压445个Source-complete 2026-02币种没有共SQLite共享原D0真实回放，旧98币WATCH/91 LATE仍只是Stage26 per-symbol后注入Stage28的结果；当前只读官方BTC/ETH零WATCH是对照，绝不宣称全758模型跑完或实际利润验证。
6. 对于Stage152新旧summary的审查，明确`APPROVE@71a04140...`只适用于该固定SHA，不能用Claude没完成的`f12d663...`自述覆盖后续Codex审批。本次 CI写回推动PR HEAD后移但模型SHA pinned且归档必须做Git源码/测试/workflow blob相等校验，任何漂移拒绝写回。

请提供审核者身份、真实可核验底层模型版本（否则`UNVERIFIED`）、唯一固定SHA、实际执行测试/独立源下载证据，P0/P1/P2新旧问题及行号/最小复现、最终 `APPROVE | REQUEST_CHANGES | BLOCKED`。即使APPROVE只属于这一修复及双币实际研究范围；`G0 PARTIAL, G1 NOT_SCORABLE, G2/G3 NOT_PASSED, G4 UNKNOWN, G5_RELEASE NOT_PASSED, G6 NO_GO`，`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`；Frank/Stage99不变。
