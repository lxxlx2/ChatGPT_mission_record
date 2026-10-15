# Monster Stage153：全市场D0→D1真实队列积压与失效的可核验研究冻结协议

冻结时点：2026-10-15 Asia/Bangkok；保留原 Monster Draft PR #30、Frank、Stage99、D0/D1生产阈值及 G0–G6。**本阶段只有历史源锁定原样队列事实＋完全只读的当前本机候选队列健康探针；不会直接改深查顺序、扩API并发、调旧305盈利阈值或启动Mac**。

## 原始证据和反例

Stage27已曝光六日期、758币/日、1132个WATCH，乐观首评单次模型表明2026-02-06 00:36 UTC同轮98 WATCH、每3min最多8条、15min TTL、至多6轮×8=48首评，至少50不能首评。Stage28用**真正单一SQLite原生产process_queue**但D0由Stage26每币独立WATCH时刻注入而非真实全市场observe_snapshot，真实生产共享D1子系统跑出1128队列记录、1005 EVALUATED、123 LATE、828 SETUP、累积3542次选取和2414次deferred；原98突发中91 LATE、7 EVALUATED。不能说因此丢失91件本可盈利的真实下单，也不能把Stage28称作已完整重放Spot+Futures全市场D0/真实通知。

**冻结且不重造来源**：Stage28 Git [六份真实研究原始发行者5m/production queue归档证据](evidence/monster_stage28_original_six_real_shared_sqlite_artifact_proof_20261011.json)，官方历史SHA原检验CI run [38146403662](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38146403662)，6份未过期GitHub Actions artifact，一份一日；其 `artifacts[].artifact_id` / `raw_json_sha256` 与 `date` 是**本次唯一允许输入**。从原run下载、读取每个解包后的 `monster_stage28_<date>_real_shared_sqlite.json`，对其原始字节计算sha256，逐个必须匹配保存在Git的六份原证据，强制6/6、数据结构、队列无重复及逐币状态事件交叉检验。旧Git proof的 `zip_sha256` 是GitHub上传封装包指纹，本次下载artifact会解压为原始json，不能把两者哈希误作一回事；只把实际验证过的 raw JSON 字节标 `SOURCE_LOCKED_STAGE28_JSON`，不是新下载官方K线。

## 可证伪交付范围和验收

1. **真实源锁定的全事件生命周期审计**：逐日期和总计从真实共享SQLite归档读取每个 `queue_final` 的 first_seen、deadline、last_evaluated_bar_ms、retry、status、attempts，真实WATCH event、SETUP event和LATE event匹配，严格校验 `sum(EVALUATED,LATE,...)=1128`，六日期全WATCH=1132、全SETUP=828、全LATE=123（其余与原CI一致）；按期末状态区分 `LATE_never_observed_completed_D1_bar`（`last_evaluated_bar_ms=None`）与 `LATE_after_at_least_one_observed_completed_D1_bar`；不以 `attempts>0`当做已成功评价。审计98个同源burst事件的准确队列身份、先后、到期、复评情况，对未知真实首次HTTP深查时刻和当时用户接收时刻标UNKNOWN。输出逐候选只读JSONL和小摘要Git证据，避免脱离原证据臆测。
2. **可用性导向队列压力只读探针**：为后续Monster本地状态提供单独`stage153_queue_pressure(db,asof_ms)`，从真实SQLite candidate_queue统计PENDING总数、从未成功完成D1 bar数量、已完成bar但还需重评数量、当前eligible、在重试backoff数量、已超过15min deadline仍PENDING、最早deadline余量、各3/6min到期数量、与默认8/3m/15min最多容量的下界风险**仅标假设和容量估算**，不读未来数据、不修改任何数据库、不连接真实市场、不启动调度或发送邮件。无需默认交易金额。若asof时出现大量同轮98候选，只能警示服务能力不足，不能发布BUY。
3. **单测与实际源报告**：构造SQLite 98同时间PENDING，验证所有候选都被统计且不被静默top3截断；分别有先评、未评、延期、超期、其他venue等状态；source六原JSON的删行、替换、时间错误和原始字节SHA变化必须拒绝；不写修改本地DB。Ubuntu/macOS两系统执行标准库unittest+py_compile；独立GitHub Actions专用工作流通过run-id `38146403662`下载六份artifact再跑真正Stage28历史源SHA核对，输出6日期完整表和存档。
4. **禁止过度承诺**：此audit只能定位拥堵不等于D1新策略，更不等于净盈利、已发邮件或完整同一全市场observe_snapshot；不重调原3%/1%/120m回撤模型；保留Stage152前轮独立Codex `APPROVE@71a041405352c9e2210d93dff9c2685149809e52`，新Stage153必须另一个AI独立固定SHA审查，不得借用。下一次可以根据本轮真实诊断确定是否实施正式调度重构，但不能未经新源实测盲提8→32限额。

**放行禁令**：`G0 PARTIAL / G1 NOT_SCORABLE / G2_G3 NOT_PASSED / G4 UNKNOWN / G5_FULL_RELEASE NOT_PASSED / G6 NO_GO`，`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，Frank unchanged，Stage99 stopped，no new schedule，所有自动采集只能用户以后聊天手动明确触发。
