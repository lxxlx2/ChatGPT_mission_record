# Monster Stage72：独立审查 H01 / M01 / M02 修复验收；M03 尚未闭环

日期：2026-10-13 Asia/Bangkok。范围仅限 Monster 原 Draft PR #30 \`research/monster-v4-local-discovery-20261010\`。输入依据是由 **GPT-6 / Codex** 在 commit e9ff5d06d1ceb8470818255a7f084af2bacfc771 提交的 [Stage71 原始独立审查报告](MONSTER_STAGE71_INDEPENDENT_AI_REVIEW_STAGE65_70_20261013.md) 及源证据，不擅自声称本轮 Stage72 修改已经由另一AI重新独立复审。

## 基线和问题原始复现

- Stage71 原始审查 HEAD：dafc83bda50d1136e5bde98ffb244b6acf9069f8。其实际2700官方来源全量复核：2700/2700与原 Stage65/66 逐行一致；1497个完成官方1h+1m，1203因来源受限CENSORED，196个首次D0 WATCH，56个首次P1资格；P2 48条历史紧急，原P1 50条。所有历史事实及已存证材料完整保留，没有回写策略阈值。
- 审查 H01：P2 半日保留旧6日期 **20/28** 且丢 AIA 5×，历史整体策略 **REJECTED**。本轮绝不再调 P2 比例或“在5个已曝光2×赢家身上寻优”。
- 审查 M01：Stage66 \`frozen()\` 仅锁 Stage51、Stage38调用的shadow而未锁真实 Stage39等依赖；原审查隔离注入Stage39恶意wrapper后仍 \`frozen()==PASS\`。
- 审查 M02：Stage70 SQLite旧有完整937历史事件时第二次合法幂等导入新增0条，原CLI仍将 \`n==937\` 当成必须条件，错误抛 \`STAGE70_INPUT_EVENTS_OR_WATCH_DROPPED\`；数据库实际没有数据丢失。
- 审查 M03：未来分钟缺源先整币 CENSORED 才会丢弃该币早期可能可观测 WATCH。原冻结完整行情统计属于**源可评分子集**，不能代替当时可交易的真实全市场分母。**本轮未修复M03**。

## 本轮实际增量修复

1. **M02 Stage70 CLI修复**：commit \`8e3d867359b37eed441d47f439866a7a62c816c3\`。仍先依完整原937事件严格验证 SHA/唯一事件ID/冲突/恢复事务；把通过条件改成最终历史 journal=937、watch=715、P1=222和各stage计数准确，而不是本次新增数必须937。新增量按实际值 \`newly_ingested_this_invocation\` 只在CLI stdout输出；原规范化 JSON+JSONL研究证据始终对同一完整库字节一致，不因本次增量导致漂移。绝不因重跑而删除SQLite或强制清表。
2. **M01 执行依赖闭包修复**：
    - commit \`17efb53c1ca8cff3fb41bb777c5231e4b000b5c7\` 新增[真实导入模块的完整依赖manifest+SHA验证器](../local-agent/scripts/monster_v4_stage72_imported_dependency_integrity.py)，固定7个真正的历史规则和数据源依赖：Stage37、38、39、44、51、shadow、historical_replay；比对 Git blob SHA、实际import的 \`__file__\` 是否与仓库同目录严格一致，以及 Stage39→38、Stage51→38/39、Stage38 replay→shadow、Stage44→Stage37 身份一致性。拒绝路径影子文件或变异SHA。
    - commit \`b70c366b8bced369e952d37196a8d4a89d4ae282\`：Stage65新增helper SHA pin，执行前检查实际导入的 Stage44→Stage37 源代码闭包和事前日期、900名单。
    - commit \`6b4ae1726aa988f64b79354262d2a98914f1b6fa\`：Stage66新增 helper 与实际 Stage65 源代码SHA pin，Stage66 \`frozen()\` 调用 Stage65完整证据freeze和7模块依赖闭包校验；继续保留源始2700样本/旧P1时钟/原V4 shadow SHA和原所有来源SHA。没有更改决定WATCH、P1、时间或名额的任何业务阈值。
3. **真实回归和原Reviewer证明的追踪**：
    - commit \`d2f6f0dee922483203761e8f2a73e1972e5fec56\` 把原Stage71“一定复现CLI错误”的单测转为 Stage72 正确修复预期，连续运行两次且导出逐字节相同；**原Stage71审查报告和运行证据未修改**。
    - commit \`cc45de471c4ce156e3fd8c77602465d6c855202a\` 把原Stage71“篡改Stage39仍被错误接收”的单测转为预期拒绝；仍在临时隔离目录复制全部研究程序和Monster证据、注入返回空WATCH的Stage39 wrapper，要求Stage66进程明确失败并包含 \`STAGE72_MUTATED_IMPORTED_DEPENDENCY_SOURCE\`。
    - commit \`774b6b2d2c0e45609d405945d626ecc7ad91e6de\` 新增[七项专项独立回归](../local-agent/tests/test_monster_v4_stage72_review_remediation.py)：完整临时SQLite连续运行三次（第一次新增937，第二和第三次新增0）、导出两份文件字节完全一致；含合法252事件的partial SQLite继续导入剩余685事件；同event_id不同payload事务回滚；Stage65实际依赖、Stage66七模块依赖与每个alias的锁定；导入graph恶意swap及不同路径影子文件失败。
    - commit \`77655f7cf5de9ebe7ffde94f9f6a5e43571a6b4e\` 新增[Stage72 专项GitHub CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38289924423)；**SUCCESS**：语法检查PASS；原Stage70 SQLite ACID自测PASS、Stage65源锁定900名单自测PASS、Stage66原模型5条容量自测PASS；7项Stage72全通过；20项原Stage71回归在更新为“修复后应拒绝/CLI应成功”状态下全通过，专项合计27个测试项。
    
## 仍保留的技术与业务边界

- 本轮的历史依赖闭包只固定**当前实际历史回放**的本地Python源码和直接 import graph，并非正式的可复现Python环境lockfile、操作系统/解释器锁、运行中被猴子补丁修改的函数对象检测。Python 3.12 GitHub Runner的成功不等于所有环境已锁定；不可宣称百分百供应链安全。
- 新修复改变的是研究和复现工程安全及SQLite导入报告，**没有提高原Stage66的2×召回、Spot/Alpha/DEX同刻可买证据、可执行净利润或达到真正未曝光样本外验证要求**。Stage71既有20/28失败和丢AIA 5×原封保留。
- Stage70仍为研究只读SQLite投影；即使可以重复运行CLI和恢复相同数据库，也不是生产实时 ACID紧急预算/持久outbox/消息送达、也不代替Frank隔离实测。Gmail与实盘永远未启用。
- **M03源人口问题维持OPEN**。下一个数据主线需独立记录\`ASOF_WATCH_EVENT\`和\`FUTURE_LABEL_SCOREABILITY\`：从一个UTC06窗口首次WATCH之后已完成的分钟前缀判断早期发现是否存在，即使后续某日官方归档缺档，仍保留前缀发生时的可验证WATCH，后续2×标为 \`UNSCORED_SOURCE_MISSING\` 而不是无机会或无WATCH；同时按事前冻结的**当时上市／退市和可交易 venue**形成同日完整可尝试分母，USD-M期货名称不能外推成妖币现货/DEX CA。严禁回写Stage65–71任何冻结的数据、事后赢家或日期。这类架构和市场人口属于下轮**数据研究与技术合同**，新分母/前缀统计尚未取得，不能标完成。
- 新版容量调度仍需基于真实全市场拥挤度、信号年龄、成交证据，在未用未来日期冻结唯一可证伪规则，再独立other-AI review及回测；策略失败前绝不部署。

状态：\`M01=ENGINEERING_FIXED_CI_PASS\`、\`M02=ENGINEERING_FIXED_CI_PASS\`、\`M03=OPEN_SOURCE_POPULATION\`、\`H01_P2=REJECTED\`、\`FUTURE_HOLDOUT=NOT_TESTED\`、\`OTHER_AI_REVIEW_OF_FIX=NOT_DONE\`、\`REAL_SPOT_ENTRY_OR_NET_PROFIT=UNKNOWN\`、\`MONSTER_DEPLOYMENT=NO_GO\`、\`AUTOTRADE=NO_GO\`、\`GMAIL=OFF\`、\`ORDER_NOTIONAL=UNSPECIFIED\`。
