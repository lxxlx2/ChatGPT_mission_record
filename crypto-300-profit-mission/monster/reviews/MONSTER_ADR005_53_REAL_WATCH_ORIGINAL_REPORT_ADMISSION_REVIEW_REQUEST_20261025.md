# Monster ADR-005 原Core真实53 WATCH的固定来源准入：独立审核请求

固定研究代码SHA：`6dc096e196ba0d9f4d3efca35b8764870abc06e1`
PR：`lxxlx2/ChatGPT_mission_record#30`（Draft，不merge不部署）

## 已知可复验输入

原离线真实历史回放 [GitHub Actions #40087231856](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40087231856) 的 Artifact ID **12557911034**，原包文件 `monster-spot511-4088-original-global-replay-20261024.zip`，外层 SHA256：

`e395e610c0280a9ba53f6bf716b1711f93623d460d4f6dfae14bc5b3c3938568`

解压后的原`paired-4088.json`的原始字节 SHA256：

`453ee2e740578121b0734d61e6eb357be7bb34859b90878eb314f7d3dc1690f5`

原 Core `fifo_watch_events` 与 `fair8_watch_events` **全字段完全相等，共53条、39个交易对**，其中包括同一币种在不同episode重新触发，不许按symbol去重；按原顺序 `symbol\tobserved_ms\tevent_id\n` 编码的 SHA256 为 `afeba23efc9e8b561ee7fa41d9e2267551d2a6b17c8f324df1e37e7f81042f9f`。原核心 full D0 tick=2919、censored tick=441、已验证原Publisher日档案=4088/4599。

## 本轮新增代码（仅只读source gate，非完整D1队列）

- `crypto-300-profit-mission/local-agent/scripts/monster_v4_spot511_verified_watch_tape.py`：`load_pinned_original_watch_tape(path)`只接收原字节SHA精确匹配的`paired-4088.json`，验证原53条FIFO/Fair8、511、3360轮、4088已完整验源、2919/441完整/删失时刻、每个WATCH的哈希/UTC 3m时钟/内容一致性、原事件顺序与全体指纹；出错必须fail closed，不开放调用方自由替换受信任SHA。输出一个按原tick提取WATCH的研究只读API，不负责改原DB。
- `crypto-300-profit-mission/monster/evidence/MONSTER_SPOT511_4088_REAL_ORIGINAL_CORE_53_WATCH_IDENTITIES_20261025.json`：由原完整Artifact抽取53条真实event_id/symbol/observed_ms及相应指纹、来源、未认证PIT的边界。该轻量文件本身**不是**原报告真实性凭证；正式导入仍必须按上述原报告完整原始字节SHA验收，不能仅凭event_key生成匹配哈希。
- `crypto-300-profit-mission/local-agent/tests/test_monster_v4_spot511_verified_watch_tape.py`：9项实际原53事件ID断言及反例，防伪report、lane漂移、来源分母漂移、重复symbol丢失、哈希/时钟/事件顺序错误。常规GitHub Actions [#40128789247](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40128789247) 在当前固定SHA实跑`177/177 PASS`；新组9/9 PASS，无网络调用。

源证据限制：Publisher 1m属于**回放后**获取的日档案，并非历史事件时刻实际收到的Spot快照与盘口；不能由Archive SHA证明原当时ticker/live listing/账户资格。原始G0仍PARTIAL。原研究候选的独立episode队列保持不变，`APPROVE @ 3d79beaa`只批准上一轮P1负例删失修复，不批准本轮来源鉴真新代码。

## 请提交给独立其他AI的审核范围

固定checkout `6dc096e196ba0d9f4d3efca35b8764870abc06e1`，先看Stage77冻结规则、ADR-004、ADR-005。检查上述三个新文件以及原`monster_v4_shadow.event_key`和`monster_v4_spot511_paired_sqlite.py`。优先证明没有“仅凭可伪造event_key即宣称原DB真实性”的路径；错误内容/错误SHA/被替换的FIFO或Fair8/错位或重复 event ID 是否必然拒绝；原53真实清单是否同源、不把39个symbol误当53个独立币种。检查输出是否可能绕开`load_pinned_original_watch_tape`构造伪`verified_tape`，如有P1/P2请指出实际影响。检查是否存在symlink、外部路径和未授权网络调用。研究队列只是离线输入通道，本次**不批准**其3m逐tick源回放、跨symbol排队行为、G1/G2/G3效果、真实交易G4或生产G6。

在可用的本地环境至少运行：

```zsh
PYTHONPATH=crypto-300-profit-mission/local-agent:crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p 'test_monster_v4_spot511_verified_watch_tape.py' -v
```

若能下载并验证原GitHub Artifact原`paired-4088.json`，还需实际调用`load_pinned_original_watch_tape`，确认53/53真实导入无缺失并禁止来源替换；若拿不到该文件，请把该部分标`NOT_TESTED`，不可拿合成9项测试冒充真原包测试。

必须输出`APPROVE / REQUEST_CHANGES / BLOCKED`、固定SHA、审核者身份/底层型号是否核验、运行命令与测试数量、P0/P1/P2复现步骤、未证明内容、是否改原Core以及G0–G6限制。严禁merge/deploy/trades/Gmail/automations。
