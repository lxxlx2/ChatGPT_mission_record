# Monster Stage105：Codex 独立审查 BLOCK 的 N-B2/N-B3 主线修复

记录日期：2026-10-13（Asia/Bangkok）。目标原 Draft [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。唯一受审采集器源 commit `2f25f2b921a97ab864ced7a0bc93aab1c9e85169`。**不授权Mac安装、launchd调度、ChatGPT automation、交易、邮件或修改Frank**。Monster历史数据模型研发持续独立进行，本研究证据采集不得阻塞研发。

## 真实独立审查证据

- 用户提交的 **Codex** 审查报告已原样按源语义归档 [Codex BLOCK：独立模型并非Claude、受审 SHA 8c318b6](evidence/monster_stage105_codex_independent_review_stage104_BLOCK_20261013.md)。原报告明确判断`BLOCK`，不得变为`Claude APPROVE`。
- 两项阻塞问题：**N-B2** 原Stage99顶层导入Stage91→Stage38→`monster_v4_shadow` / `monster_v4_historical_replay`，恶意未审历史模块可在门禁前执行；**N-B3** 第2窗口运行状态`store_status`模拟磁盘满后，在异常回滚期间持续写日志再失败，会中断其余已加载任务的`bootout`。
- 旧严格卸载确认 N-B1（`launchctl list`和`print`核对、无法证明卸载则保留plist）继续保留。本次的两个 BLOCK 与“CI本身绿”不矛盾；旧CI没有涵盖新复现。

## N-B2：真实减依赖，而非盲目添加路径

- 新 [Stage105零模型导入纯人口模块](../local-agent/scripts/monster_v4_stage105_capture_universe_core.py) 只用Python标准库提供三个冻结日期、Binance USD-M官方`exchangeInfo` endpoint、因果时间核对、完整符号人口及永续候选过滤。它没有任何`import Stage38/80/91/Shadow/HistoricalReplay`；没有网络I/O、调度或进程操作。
- [Stage97官方三段HTTPS采集](../local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py)和[Stage99本地一次性采集/ Git](../local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py)现在**只导入新纯模块**，不会再从研究模型侧加载Stage91或其递归依赖；Stage102审查凭证`REQUIRED_SOURCES`同时绑定Stage105在内的8个当前**真实执行与测试**Git blob。
- 原[Stage91历史回放](../local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py)仍保持原来的Stage38/80历史研究模块能力，但其冻结市场人口与验证函数直接复用 Stage105同一实现，避免双份不同筛选逻辑。Stage91变更不能自动修改已审核采集进程；Stage105变更一定让review blob失效并触发专项CI。
- 新[Stage105真正全新Python进程导入攻击回归](../local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py)把Stage38/80/91/Shadow/历史回放替换成“导入立即在磁盘写危险标记并抛错”的模拟模块，真实子进程导入Stage99/97/102成功，且危险标记未创建、危险模块未加载。另将本地真实Git未审修改测试从Stage91改为**实际采集依赖Stage105**，验证未审更改被门禁拒绝。上述都是本地无网络测试，不声称可抵御Python脚本自身被替换后的任意操作系统级执行。

## N-B3：磁盘满不阻止其他已加载服务的回滚

- [Stage99 `install()`](../local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py) 在安装任一步骤失败后维护**内存**的`rollback_failures`和`journal_failures`两个列表；每一窗口无论卸载成功/失败，都将状态记录封装进另一个独立try/except。即使`store_status`持续抛`OSError(ENOSPC)`，也继续对更早已成功bootstrap的任务调用`bootout`和退出确认。状态文件无法写时向stderr按原窗口输出`STAGE105_ROLLBACK_JOURNAL_FAILED`，最后统一抛出包含失败列表的非零异常，而不是冒充安装或清理成功。
- [单元测试](../local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py)覆盖“第二窗口已bootstrap但首次写`SCHEDULE_INSTALLED`磁盘满、其回滚状态文件仍磁盘满、第一窗口回滚状态文件也磁盘满”，核对`launchctl`有**两次bootstrap＋逆序两次bootout**；还覆盖“第二窗口bootout失败＋所有回滚journal都失败”，仍继续尝试卸载第一个窗口。未确认已卸载的任务保留plist，绝不标`ROLLBACK_SUCCESS`。
- N-B1后续`launchctl`确认仍是独立安全关口；本CI使用模拟系统命令，**并未**在用户真实Mac运行。未来真实Mac验收必须获得用户另行明确授权。

## 完整可信测试与事实边界

- [Monster Stage99/105 专项 CI #38383381420](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383381420) `head_sha=2f25f2b921a97ab864ced7a0bc93aab1c9e85169`，**macOS-latest与Ubuntu-latest各PASS**。
- 每个平台日志：**24个launchd/授权/故障mock测试、4个真实本地Git裸仓库/冲突/原始字节测试、1个全新Python进程恶意依赖导入检测**，加Stage91/97等离线selftest、源码编译；CI没有通过用户本机launchctl或真实Binance未来接口。
- [Monster V4 Research Baseline CI #38383499069](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383499069) **SUCCESS**：史料模型依旧可运行，且旧研究与采集已解耦。
- 另将独立审查来源门禁扩展为支持**用户真实转发Codex或者Claude聊天独立评审**，而非依赖Claude账户/本地CLI。**原Codex报告明确BLOCK，不可生成APPROVE回执，更不能作为用户安装授权。**任何真实独立review仅由用户交回文本，研发负责人不代拟人工批准。
- 原本三组未来日期 2026-10-14、10-28、11-11：只是可选证据采集窗口；若用户不批准本地安装或错过时点，则标`NOT_CAPTURED`，严禁补抓冒充时点证据；**无需采到新数据再推进Monster历史建模**。

## 下一状态

`STAGE105_CODE_CI=PASS_MAC_AND_UBUNTU`，`CODEX_PRIOR_REVIEW=BLOCK_ARCHIVED`，`INDEPENDENT_REVIEW_OF_NEW_SOURCE=NOT_DONE`，`USER_LOCAL_INSTALL_AUTHORIZATION=NOT_GIVEN`，`MAC_TASK_INSTALLED=NO`，`FUTURE_OFFICIAL_SNAPSHOT=NOT_DONE`，`MONSTER_MODEL_DEPLOYMENT=NO_GO`，`FRANK=UNCHANGED`，`GMAIL=OFF`，`AUTOTRADE=NO_GO`。
