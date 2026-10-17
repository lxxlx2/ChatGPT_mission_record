# 地址分析 / 通用 FIFO 单币账本 V1 离线验收（2026-10-18）

Status: `OFFLINE_REPLAY_PASS / REAL_CHAIN_RECONSTRUCTION_NOT_VERIFIED / NO_GO`
Base PR #97 HEAD: `3121265117e8212993e782c5ed87b71cda8ada41`
Scope: `crypto-300-profit-mission/address-analysis/` only. Do not merge or deploy.

## 本轮实际完成的代码

- 新工具 [`tools/transaction_ledger.py`](../tools/transaction_ledger.py) 读取标准化、事先有据可查的单币 BUY/SELL 事件，采用 Python 整数和 Fraction 进行 FIFO 实现成本、部分卖出、亏损、跨30天窗口与剩余库存计算。
- 严格对应冻结源449地址的行号、批次和钱包身份。开仓来源或全部 Token 收付不明、收据/代币净流/quote净流/Gas 核算声明不全、重复交易、同区块未聚合多笔成交、卖超现有库存、余额无法闭合时返回 `PNL_UNRESOLVED`，禁止形成部分的虚假收益合计。
- 在原生币作为 quote 时使用包含同币种 Gas/费用的净现金流。Gas 与 quote 不同时，需提供明确的执行时点兑换来源及费用换算断言；不计算缺少来源的美元价值。
- **所有 evidence/proof 布尔字段均为外部归一化数据提交者的声明**。这版 Python **不会主动访问 RPC 或检查 receipt**，所以合规通过后的输出名为 `CLAIM_REPLAY_ONLY`，不允许称为独立验证的链上盈亏，更不允许把单币结果升级为整钱包30天或长期收益。

## 实际测试记录

隔离执行环境：Python 3，标准库，未触碰生产，命令 `python3 -m unittest discover -s tests -v`（此记录对应只包含本轮 `test_transaction_ledger.py` 的独立测试目录）。

- 初始本轮测试真实失败：同一区块但 timestamp 不同的事件未被阻断。修复为同一 token 的规范化输入必须满足严格递增区块，否则退回未决队列（同区块多成交需上游核算并聚合）。
- 修改后 **20 tests passed，0 failed**，包括：真实保存的 sauce 002 数据回放、FIFO 多批成本、合成亏损、跨窗口、剩余持仓、超卖、重复哈希、Gas 汇率证据缺失、未知资产来源、钱包清单篡改、余额不匹配、审批伪装成交。
- **所有亏损测试均为合成数据**，未新增实链负收益闭环。
- 本轮手动 CLI 入口在测试隔离目录实际运行：固定 source row002 与已有 Git 源钱包匹配，但为了不传输其它隐私/无关地址，另外448行是仅供本地校验的**合成清单**。退出码 **0**；从历史证据中归一化的 2 BUY/1 SELL 回放结果为 **+156828105278687674 wei BNB**，精确与已有 sauce row002 证据一致。故意超卖反例返回 `PNL_UNRESOLVED`，退出码 **3**。此测试**不表示已对 Git 原始449地址清单完整执行该 CLI**。
- `tools/transaction_ledger.py` 的 Git blob 必须为 `5cebc2ef4b752a27bff64147e9c39bdb44dae112`；`tests/test_transaction_ledger.py` blob 为 `67aa8874fca77847f4863566646f9d1763d0debb`；`fixtures/batch001-row002-sauce-executions.json` blob 为 `24225421b04c4df6d01dae23b3e12f083200a1da`。这三个 SHA 与本地已实测文件逐字节一致。
- [既有 sauce 002 净额的输出与 CLI 执行环境限制](../evidence/ledger-v1-row002-source-replay.json)。

## 尚未完成的门禁

1. 原始 RPC / receipt / log / trace 的自动采集、成功状态与多链交易解码，验证上游 `proof=true` 的声明真实性。
2. 同一区块多路由、多 token 交互、跨钱包桥接、transfer tax、不同 gas 币种的独立准确换算。
3. 一个钱包全量跨链买卖、入金、转出、期初库存、盈利与亏损对账，完成可复核的月度和长期钱包 PnL。
4. Mac 实测及独立外部审核。
5. Batch007 原始121–140 的三链签名筛查继续保持 `NOT_STARTED`，不影响上述核心功能开发。

成果属于独立地址分析模块的研究性 FIFO 账本 V1。原始120/449覆盖、3个正收益单币闭环、0个真实完成亏损闭环、0/449完整钱包 PnL 均**保持不变**。不写 `final` 工件、不合并、不部署、不新建监控/自动化、不发送邮件、不交易。
