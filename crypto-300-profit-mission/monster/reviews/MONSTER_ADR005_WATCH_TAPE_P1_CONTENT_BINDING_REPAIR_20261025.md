# Monster：真实原Core 53 WATCH 提取 API 来源绑定 P1 审核及修复记录

## 审核范围与结论

- **旧固定审核 SHA**：`6dc096e196ba0d9f4d3efca35b8764870abc06e1`。
- **用户转交的独立审核结论**：`REQUEST_CHANGES`，真实复现 **1项P1来源完整性缺陷**；该结论永久保留，不在原SHA上改称APPROVE。
- **审核主体**：Codex主代理（用户转交），底层具体模型型号`UNVERIFIED`；用户Mac macOS 27.0.1 arm64、Python3.14.7；独立detached只读、无原Core数据库修改、交易或部署。
- **审核实际执行**：旧SHA来源准入单测 `9/9 PASS`；实际下载GitHub Artifact ID`12557911034`，原ZIP 19,183字节、SHA256 `e395e610c0280a9ba53f6bf716b1711f93623d460d4f6dfae14bc5b3c3938568`、内部`paired-4088.json` SHA `453ee2e740578121b0734d61e6eb357be7bb34859b90878eb314f7d3dc1690f5`均匹配；loader在原文件导入`53`条WATCH、`39`不同币，按tick提取53个唯一event ID。加换行篡改字节与直接软链路径均拒绝。这些**仅针对旧固定SHA已实际测试**，不得冒称新SHA已获独立复审。
- **P1可复现漏洞**：旧`watches_at_tick()`只检查可由调用者填写的`schema`、`original_paired_json_sha256`、`original_watch_ledger_integrity_checked=True`和53个tuple长度，却未在提取处将tuple实际内容与固定真实53项身份指纹绑定。审核者用完全伪造53条`FAKEUSDT`或“真实loader返回后替换首条”的路径拿到伪事件，并实际以临时研究SQLite的`admit_original_watch()`接受该伪事件。**原ZIP字节SHA校验从未被攻破，漏洞位于已校验输出与使用方之间。**
- **影响/状态**：研究WATCH来源输入和后续episode分母有污染风险；原Core原WATCH/SETUP本身无变更。G0仍PARTIAL，原G2/G3新版本UNKNOWN、G4 UNKNOWN、G6 NO_GO。

## 最小修复与实际新代码测试

**P1源码修复**：[commit `bf64e7e150bef9c6e5adacd6949da97dac718416`](https://github.com/lxxlx2/ChatGPT_mission_record/commit/bf64e7e150bef9c6e5adacd6949da97dac718416)，只改`crypto-300-profit-mission/local-agent/scripts/monster_v4_spot511_verified_watch_tape.py`。新增`_verify_pinned_extraction_rows()`，在每次`watches_at_tick()`使用之前对**完整53项tuple**逐条验证：精确三元tuple结构、合法symbol、严格int+UTC3m时钟、原`event_key()`哈希、全体event ID不重复、(observed_ms,event_id)原顺序，最后固定全量canonical SHA256必须等于`afeba23efc9e8b561ee7fa41d9e2267551d2a6b17c8f324df1e37e7f81042f9f`。不信任布尔标记来替代内容验证，不接受调用方指定的信任摘要；任一异常**整个提取fail-closed**。原loader的完整原报告字节SHA校验仍是正式来源验收入口。

**新增8项回归**：[commit `73732fc647d588e9de33281d6aea8ac3e58763f4`](https://github.com/lxxlx2/ChatGPT_mission_record/commit/73732fc647d588e9de33281d6aea8ac3e58763f4)，追加`test_monster_v4_spot511_verified_watch_tape.py`：
1. 伪造完整公开来源标记，放入53份相同`FAKEUSDT`事件→拒绝重复ID；
2. 保持53条、首条换成正确重新计算event key的`FAKEUSDT`→拒绝固定指纹不一致；
3. 重复一条合法原ID→拒绝；
4. 交换合法原事件顺序→拒绝；
5. 原始事件移到另一个**合法3m tick**且正确重算ID→仍因固定摘要变化拒绝；
6. 非tuple记录/非整数时钟→拒绝；
7. 完全真实53个固定身份逐tick提取，53个ID且39个symbol全部保留；
8. 使用**单元测试本地构造的53条真实身份JSON**临时替换测试内原报告字节SHA，实际调用loader成功，再篡改返回字典第1条→提取拒绝。此fixture只在测试patch中接受，**绝不等同在新SHA以生产固定SHA重新下载真实原Artifact**。

**GitHub云端真实结果**：[Actions #40129464849](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40129464849)，固定commit `73732fc647d588e9de33281d6aea8ac3e58763f4`，Job `120977870279`，completed/**SUCCESS**，13组 `13+5+6+11+19+12+12+14+18+18+17+9+31=185/185 PASS`，新来源准入专项`17/17 PASS`，既有原shadow等回归不变。CI没有访问真实网络或买卖。

**P1 工程状态**：`PATCH_COMMITTED / REGRESSION_CI_PASS`；旧SHA`REQUEST_CHANGES`不变，**新固定SHA的独立其他AI复审还没有取得`APPROVE`**。

## 独立复审请求

请独立对PR #30的**固定代码SHA `73732fc647d588e9de33281d6aea8ac3e58763f4`**进行只读审核，不要按后续文档HEAD替换。上一轮 `REQUEST_CHANGES@6dc096e196ba0d9f4d3efca35b8764870abc06e1` 的唯一P1是“已验证的原53 WATCH字典可被篡改、`watches_at_tick`只信公开标记和长度”。

比较两项修复diff，检查新来源模块`_verify_pinned_extraction_rows`是否真正逐项重算哈希/唯一性/原序及全体canonical SHA，不受修改后字典标记或`FAKEUSDT`合法哈希欺骗；代码使用的SHA常量是否与原GitHub Artifact ID`12557911034`真实原paired JSON 53个身份一致。

先执行：
```zsh
PYTHONPATH=crypto-300-profit-mission/local-agent:crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p 'test_monster_v4_spot511_verified_watch_tape.py' -v
```

再在独立临时环境用真实原`paired-4088.json`调用`load_pinned_original_watch_tape`及所有WATCH原tick提取，确认53个ID无缺失；将返回dict的首条替换、完整伪造公开字段/全部53条伪ID、重复真实ID、换序和改3m tick后应全部拒绝。若无法重新取得真正的Artifact，应标记`REAL_ARTIFACT_PATH_NOT_TESTED`，不能仅凭合成17项冒充真实原包验收。

输出`APPROVE/REQUEST_CHANGES/BLOCKED`、精确SHA、审核模型如不明标`UNVERIFIED`、实际环境/数量、P0/P1/P2和复现及原P1是否CLOSED。**即使修复独立通过，也只批准来源提取内容绑定，不批准真实新D1 511币联动、历史行情PIT、G2/G3/G4盈利、G5全套或G6上线。** 维持 `NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES`。

## 独立复审结果：APPROVE @ `73732fc647d588e9de33281d6aea8ac3e58763f4`（用户转交）

- **正式结论及边界**：用户转交的 Codex 主代理对**固定代码SHA `73732fc647d588e9de33281d6aea8ac3e58763f4`**作出 `APPROVE`，**仅关闭上一轮WATCH提取API的P1来源内容绑定缺陷**。旧固定版本 `6dc096e196ba0d9f4d3efca35b8764870abc06e1` 的 `REQUEST_CHANGES`仍永久有效；不得把随后仅文档的HEAD当作审核源码。
- **实际环境**：用户Mac macOS 27.0.1 arm64 / Python3.14.7，独立 detached worktree，Codex 主代理；审核者底层模型 `UNVERIFIED`。本轮实际运行专项**17 PASS / 0 FAIL / 0 ERROR / 0 SKIP**，没有宣称 Mac 完整重跑云端185项。原 Mac 日志路径 `/private/tmp/monster-binding-73732-tests.log`仅属于审核方本地，不冒称已上传 Git。
- **真实来源二次实测**：重新下载GitHub Artifact `12557911034`，外层ZIP SHA256 `e395e610c0280a9ba53f6bf716b1711f93623d460d4f6dfae14bc5b3c3938568`、内部 `paired-4088.json` SHA256 `453ee2e740578121b0734d61e6eb357be7bb34859b90878eb314f7d3dc1690f5`、原53项canonical SHA256 `afeba23efc9e8b561ee7fa41d9e2267551d2a6b17c8f324df1e37e7f81042f9f`全部实际匹配。固定新源码 loader 成功，按原全部tick重取**53 WATCH、53唯一event ID、39交易对**。本次不含全部4,088份Publisher来源字节重验，不证明历史live报价PIT。
- **真实Artifact修改反例**：带全部公开trust标记的53条重复伪WATCH→`WATCH_TAPE_DUPLICATE_EVENT_ID`；真实loader后把首条替换成正确重算event key的`FAKEUSDT`→`WATCH_TAPE_CANONICAL_SHA_MISMATCH`；重复原ID→拒绝、真实事件换序→拒绝、改成另一个合法3m tick并重算event key→拒绝。审查者复核`bf64e7e`及`73732fc`两次差异，`_verify_pinned_extraction_rows()`在tick过滤前核验所有53条的结构、3m时间、event key、唯一性、原序和固定整体指纹；从此公开布尔标记不能代替内容绑定。新修复范围未发现P0/P1/P2，上一轮P1=`CLOSED`。
- **仍有审慎限制**：这些结果只证明提取内容与固定真实53事件指纹一致；Python dict不成为不可伪造的安全凭据，正式入口仍要执行原报告字节SHA验收。原 `monster_v4_shadow.py`、独立episode研究队列、RBTC15比较器、ADR-005预注册均未修改；完整真实511币与BTC同源时钟研究回放、G2/G3效果、历史动态上架和账户资格G0、真实bid/ask及成本G4、整体G5/G6**均不获得本次APPROVE授权**。
- **保持**：`G0 PARTIAL / G1 NOT_SCORABLE / G2/G3 NEW UNKNOWN / G4 UNKNOWN / G5 FULL INTEGRATION NOT_DONE / G6 NO_GO`；`NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES`。
